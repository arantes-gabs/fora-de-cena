"""Small native CI helpers. No credentials, camera, publishing or driver installation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_diagnostics import public_error
PYTHON_VERSION = '3.14.7'
PYTHON_LICENSE_SHA256 = 'b0e25a78cffb43f4d92de8b61ccfa1f1f98ecbc22330b54b5251e7b6ba010231'


def diagnose(target: str | None) -> int:
    from teleport_cam.launcher import self_test
    try:
        report = self_test()
    except Exception as error:
        report = {'ok': False, 'error': type(error).__name__, 'detail': public_error(str(error))}
    name = 'intel-source-self-test.json' if target == 'macos-x86_64' else 'source-self-test.json'
    path = ROOT / 'work' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if not report['ok']:
        print('Source diagnostic failed:', report.get('error'), report.get('detail'))
        return 1
    print('Source diagnostic passed. No camera opened; dependency network verification remains pending.')
    return 0


def intel_compatibility() -> None:
    report=json.loads((ROOT/'work/wheels.json').read_text(encoding='utf-8'))
    allowed='mediapipe: no compatible non-yanked wheel'
    errors=report.get('errors')
    if (report.get('target')!='macos-x86_64' or not isinstance(errors,list) or
            any(error!=allowed for error in errors)):
        raise ValueError('Intel compatibility check has issues beyond the reviewed MediaPipe source build.')
    print('Intel dependency check accepted only the explicit MediaPipe source-build exception.')


def build() -> None:
    """Use only the native builder and the license matching the CI Python pin."""
    if sys.version.split()[0] != PYTHON_VERSION:
        raise RuntimeError('CI Python differs from the reviewed version')
    if sys.platform == 'win32':
        compiler = shutil.which('ISCC.exe')
        if compiler is None:
            compiler = str(Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) /
                           'Inno Setup 6/ISCC.exe')
        if not Path(compiler).is_file():
            raise FileNotFoundError('The Windows runner must provide Inno Setup; no automatic installation is performed.')
        subprocess.run([sys.executable, 'tools/build_windows.py', '--single-file'], cwd=ROOT, check=True)
        subprocess.run([sys.executable, 'tools/build_windows.py', '--iscc', compiler], cwd=ROOT, check=True)
        return
    else:
        url = f'https://raw.githubusercontent.com/python/cpython/v{PYTHON_VERSION}/LICENSE'
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.url != url:
                raise ValueError('Unexpected Python license redirect')
            license_bytes = response.read(1024 * 1024)
        if hashlib.sha256(license_bytes).hexdigest() != PYTHON_LICENSE_SHA256:
            raise ValueError('Python license differs from reviewed source')
        license_path = ROOT / 'work/ci-python-LICENSE.txt'
        if not license_path.parent.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('Redirected CI license destination')
        license_path.parent.mkdir(parents=True, exist_ok=True)
        with license_path.open('xb') as output:
            output.write(license_bytes)
        command = [sys.executable, 'tools/build_unix.py', '--python-license', str(license_path)]
        if sys.platform in ('darwin', 'linux'):
            folder = 'opencv-minimal'
            wheels = list((ROOT / 'work' / folder / 'wheels').glob('*.whl'))
            if len(wheels) != 1:
                raise ValueError('Expected one explicit custom wheel for the native target')
            prefix = '--opencv'
            command += [prefix + '-wheel', str(wheels[0]), prefix + '-provenance',
                        str(ROOT / 'work' / folder / 'provenance.json')]
        if sys.platform=='linux':
            from tools.build_minimal_numpy import validate_artifact
            wheels=list((ROOT/'work/numpy-minimal/wheels').glob('*.whl'))
            if len(wheels)!=1:
                raise ValueError('Expected one explicit NumPy wheel for the Linux target')
            validate_artifact(wheels[0], ROOT/'work/numpy-minimal/provenance.json')
    subprocess.run(command, cwd=ROOT, check=True)


def summarize(target: str) -> None:
    """Only fixed labels and aggregate counts go to the public Actions summary."""
    from tools.check_platform_wheels import TARGETS
    if target not in TARGETS:
        raise ValueError('Unknown CI target')
    wheels_path = ROOT / 'work/wheels.json'
    if wheels_path.is_file():
        report = json.loads(wheels_path.read_text(encoding='utf-8'))
        errors = report.get('errors', [])
        state = f"{len(errors)} dependency compatibility issue(s)" if errors else 'Pinned binary dependencies available'
    else:
        state = 'Dependency check did not complete; inspect failed steps'
    if target == 'macos-x86_64':
        selected_backend = report.get('vision_backend') if wheels_path.is_file() else None
        state += ('. Intel OpenCV DNN profile selected; complete app/camera validation is still required.'
                  if selected_backend == 'opencv-dnn' else
                  '. Legacy MediaPipe wheel check; it does not certify the Intel OpenCV DNN candidate.')
        state += ' No support certification.'
        diagnostic = ROOT / 'work/intel-source-self-test.json'
        if diagnostic.is_file() and json.loads(diagnostic.read_text(encoding='utf-8')).get('ok'):
            state += ' Intel source inference/self-test passed; inspect the separate DMG/frozen test outcome.'
    network=ROOT/'work/dependency-network-sample.json'
    if network.is_file():
        observed=json.loads(network.read_text(encoding='utf-8')).get('sample_network_syscalls_observed')
        state += (' Network sample observed calls requiring review.' if observed else ' No network syscalls observed in this bounded sample.')
        state += ' Dependency network verification is still pending; no offline certification.'
    text = (f'### {target}\n\n{state}\n\n'
            'See job/step results for test and build outcomes. No webcam or call tested. '
            '`distribution_ready=false`. No Release or stored binary artifact.\n')
    destination = os.environ.get('GITHUB_STEP_SUMMARY')
    if destination:
        with Path(destination).open('a', encoding='utf-8') as summary:
            summary.write(text)
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'summary', 'diagnose', 'intel-compatibility'))
    parser.add_argument('--target')
    args = parser.parse_args()
    if args.action == 'diagnose':
        raise SystemExit(diagnose(args.target))
    elif args.action == 'build':
        build()
    elif args.action=='intel-compatibility':
        intel_compatibility()
    else:
        summarize(args.target)


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
