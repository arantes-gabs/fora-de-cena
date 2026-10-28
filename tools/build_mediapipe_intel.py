"""Attempt a native Intel build of MediaPipe 1.1.1. Experimental; never publish."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMPILE_TIMEOUT_SECONDS = 150 * 60
sys.path.insert(0, str(ROOT))
from tools.mediapipe_intel import PROFILE, digest, load_profile, make_wheel


def download(url: str, destination: Path, expected: str) -> None:
    with urllib.request.urlopen(url, timeout=60) as response, destination.open('xb') as output:
        if not response.url.startswith(('https://github.com/', 'https://release-assets.githubusercontent.com/',
                                        'https://files.pythonhosted.org/')):
            raise ValueError('Unexpected build input redirect')
        count = 0
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if count > 150 * 1024 * 1024:
                raise ValueError('Build input exceeds download limit')
            output.write(chunk)
    if digest(destination) != expected:
        raise ValueError('Build input SHA256 mismatch: ' + destination.name)


def compile_native(command: list[str], source: Path, environment: dict[str, str]) -> None:
    try:
        subprocess.run(command, cwd=source, env=environment, check=True,
                       timeout=COMPILE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise RuntimeError('Intel C++ compilation exceeded 150 minutes. No verified wheel was produced; '
                           'inspect the last compiler action before retrying.') from None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true', help='Inspect the experimental profile without downloading or compiling')
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(load_profile(), indent=2))
        return
    if sys.platform != 'darwin' or platform.machine().lower() != 'x86_64':
        raise RuntimeError('Run this experimental compiler on a Mac Intel x86_64 runner.')
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError('Use Python 3.14; do not downgrade the runtime lock.')
    profile = load_profile()
    work = ROOT / 'work/mediapipe-intel'
    if (work.exists() or not (ROOT / 'work').resolve().is_relative_to(ROOT.resolve())
            or not work.resolve().is_relative_to((ROOT / 'work').resolve())):
        raise ValueError('Use a new, non-redirected work/mediapipe-intel directory.')
    work.mkdir(parents=True)
    bazel = work / 'bazel'
    download(profile['bazel']['url'], bazel, profile['bazel']['sha256'])
    bazel.chmod(0o755)
    template = work / profile['python_template']['filename']
    download(profile['python_template']['url'], template, profile['python_template']['sha256'])
    source = work / 'source'
    # The source is public. Never prompt for or inject account credentials.
    build_home = work / 'home'
    build_home.mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if key in {'PATH', 'TMPDIR', 'LANG', 'LC_ALL', 'DEVELOPER_DIR', 'SDKROOT', 'JAVA_HOME'}}
    environment.update(HOME=str(build_home), GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1')
    subprocess.run(['/usr/bin/git', '-c', 'credential.helper=', 'clone', '--depth=1', '--single-branch',
                    '--branch', profile['source_tag'], profile['source_repository'], str(source)],
                   env=environment, check=True)
    head = subprocess.check_output(['/usr/bin/git', '-C', str(source), 'rev-parse', 'HEAD'],
                                   text=True, env=environment).strip()
    if head != profile['source_commit']:
        raise ValueError('MediaPipe checkout differs from reviewed commit')
    if subprocess.check_output(['/usr/bin/git', '-C', str(source), 'status', '--porcelain'], env=environment).strip():
        raise ValueError('MediaPipe checkout is not clean')
    patch_path = ROOT / 'packaging/mediapipe-intel-source.patch'
    if (digest(patch_path) != profile['source_patch_sha256'] or
            digest(source / 'third_party/BUILD') != profile['source_build_file_sha256'] or
            digest(source / 'WORKSPACE') != profile['source_workspace_sha256'] or
            digest(source / 'mediapipe/tasks/c/mediapipe_tasks_c_shared_library.bzl') != profile['source_shared_library_sha256']):
        raise ValueError('Intel source patch or upstream OpenCV rule differs from reviewed inputs')
    subprocess.run(['/usr/bin/git', '-C', str(source), 'apply', '--check', str(patch_path)],
                   env=environment, check=True)
    subprocess.run(['/usr/bin/git', '-C', str(source), 'apply', str(patch_path)],
                   env=environment, check=True)
    sdk = Path(subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'],
                                      text=True, env=environment).strip()).resolve(strict=True)
    sdk_version = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-version'],
                                          text=True, env=environment).strip()
    if not (sdk / 'usr/lib/libz.tbd').is_file() or not (sdk / 'usr/include/zlib.h').is_file():
        raise ValueError('The selected macOS SDK must provide system zlib headers and linker stub.')
    build_file = source / 'third_party/BUILD'
    configured = build_file.read_text(encoding='utf-8')
    for suffix in ('usr/lib/libz.tbd', 'usr/include'):
        placeholder = json.dumps('__FDC_MACOS_SDKROOT__/' + suffix)
        if configured.count(placeholder) != 1:
            raise ValueError('Unexpected SDK substitution in the reviewed source patch')
        configured = configured.replace(placeholder, json.dumps(str(sdk / suffix)))
    build_file.write_text(configured, encoding='utf-8')
    # Compile the C API directly; setup.py forces ARM. The reviewed source patch
    # keeps its private OpenCV static and omits external codecs/GUI dependencies.
    command = [str(bazel), '--batch', '--nosystem_rc', '--nohome_rc',
               '--output_user_root=' + str(work / 'bazel-root'), 'build',
               '--config=darwin_x86_64', '--compilation_mode=opt', '--jobs=3',
               '--local_ram_resources=HOST_RAM*0.6', '--macos_minimum_os=15.0',
               '--define=MEDIAPIPE_DISABLE_GPU=1', '--define=OPENCV=source',
               '--copt=-DNDEBUG', '--copt=-DLITERT_DISABLE_NPU', '--apple_generate_dsym=false',
               '--copt=-ffile-prefix-map=' + str(ROOT) + '=/usr/src/fora-de-cena',
               '--cxxopt=-ffile-prefix-map=' + str(ROOT) + '=/usr/src/fora-de-cena',
               '--copt=-ffile-prefix-map=' + str(Path.home()) + '=/usr/src/fora-de-cena-build-home',
               '--cxxopt=-ffile-prefix-map=' + str(Path.home()) + '=/usr/src/fora-de-cena-build-home',
               profile['build_target']]
    compile_native(command, source, environment)
    native = work / 'libmediapipe.dylib'
    shutil.copyfile(source / profile['native_output'], native)
    subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(native)], check=True)
    wheel = make_wheel(template, native, work / 'wheels', profile)
    record = {'custom_build': True, 'experimental': True, 'distribution_ready': False,
              'architecture': 'x86_64', 'profile_sha256': digest(PROFILE),
              'source_commit': head, 'python_template_sha256': digest(template),
              'source_patch_sha256': digest(patch_path),
              'macos_sdk_version': sdk_version, 'system_zlib_from_sdk': True,
              'bazel_sha256': digest(bazel), 'native_sha256': digest(native),
              'build_driver_sha256': digest(Path(__file__)),
              'wheel': {'filename': wheel.name, 'sha256': digest(wheel)},
              'pending': ['native-source-and-frozen-self-tests', 'real-intel-camera-and-calls',
                          'complete-native-license-and-source-review', 'dependency-network-verification'],
              'raw_logs_included': False, 'official_intel_wheel': False}
    (work / 'provenance.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print('Experimental Intel wheel built:', wheel.name, record['wheel']['sha256'])


if __name__ == '__main__':
    main()
