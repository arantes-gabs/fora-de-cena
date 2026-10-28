"""Build local experimental macOS/Linux candidates. No commits, uploads or installers."""
from __future__ import annotations
import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from teleport_cam import __version__
from teleport_cam.model_assets import MODEL_ASSETS
from teleport_cam.platform_support import system_environment
from setup_models import verify_model
from tools.build_windows import collect_notices, digest
from tools.distribution_licenses import package_compliance, runtime_signature, upstream_files
from tools.build_diagnostics import public_error

TARGETS = ('macos-arm64', 'macos-x86_64', 'linux-x86_64', 'linux-arm64')
PRIVATE_NAMES = {'.git', '.venv', '.ssh', '.aws', '.env', '.meet_pairing_key',
                 'user_settings.json', 'startup-error.log', '__pycache__'}
UNREVIEWED_NATIVE_PREFIXES = ('libavcodec', 'libavformat', 'libavutil', 'libswscale',
    'libswresample', 'libx264', 'libx265', 'libqt', 'libglib', 'libgobject', 'libgio',
    'libreadline', 'libquadmath', 'libgfortran', 'libscipy_openblas', 'libopenblas')


def check_native_license_scope(paths):
    """Reject unused/unreviewed codec, GUI and Fortran libraries; don't delete them."""
    for path in paths:
        if path.name.lower().startswith(UNREVIEWED_NATIVE_PREFIXES):
            raise ValueError('Native library outside the reviewed candidate profile: '+path.name)


def native_target(system: str | None = None, machine: str | None = None) -> str:
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if system == 'darwin' and machine in ('arm64', 'aarch64'):
        return 'macos-arm64'
    if system == 'darwin' and machine in ('x86_64', 'amd64'):
        return 'macos-x86_64'
    if system.startswith('linux') and machine in ('x86_64', 'amd64', 'arm64', 'aarch64'):
        return 'linux-arm64' if machine in ('arm64', 'aarch64') else 'linux-x86_64'
    raise RuntimeError('Compile no próprio Mac ou Linux 64 bits. Windows não gera estes pacotes.')


def build_plan(target: str) -> dict[str, object]:
    if target not in TARGETS:
        raise ValueError('Alvo sem suporte de build.')
    return {'target': target, 'format': 'dmg' if target.startswith('macos') else 'tar.gz',
            'experimental': True, 'distribution_ready': False,
            'python': '3.14', 'automatic_upload': False,
            'minimum_target': 'macOS 15 (profile); actual bundle audited' if target == 'macos-x86_64' else 'macOS 13 (actual bundle audited)' if target.startswith('macos') else 'glibc 2.35 (build base)',
            'custom_mediapipe_required': target == 'macos-x86_64',
            'pending': ['native-build-and-self-test', 'native-library-license-and-source-review',
                        'dependency-network-verification', 'real-camera-and-call-validation', 'owner-publication-approval']}


def checked_directory(path: Path, parent: Path) -> Path:
    if (not parent.resolve().is_relative_to(ROOT.resolve()) or
            not path.resolve().is_relative_to(parent.resolve()) or path.is_symlink()):
        raise ValueError('Diretório de build redirecionado ou fora do destino previsto.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def inventory(folder: Path) -> list[Path]:
    """Preserve required Unix symlinks, but reject links outside the application."""
    base = folder.resolve()
    result = []
    for path in sorted(folder.rglob('*')):
        relative = path.relative_to(folder)
        if any(part.lower() in PRIVATE_NAMES or part.lower().startswith('.env.') for part in relative.parts):
            raise ValueError('Estado privado dentro do pacote: ' + relative.as_posix())
        if path.suffix.lower() in ('.p12', '.pfx', '.key'):
            raise ValueError('Arquivo de credencial dentro do pacote: ' + relative.as_posix())
        if not path.resolve().is_relative_to(base) or not path.exists():
            raise ValueError('Link externo ou ausente no pacote: ' + relative.as_posix())
        if path.is_file() and path.suffix.lower() == '.pem' and b'PRIVATE KEY' in path.read_bytes():
            raise ValueError('Chave privada dentro do pacote.')
        if path.is_symlink() or path.is_file():
            result.append(path)
    if not result:
        raise ValueError('Pacote vazio.')
    return result


def create_tarball(payload: Path, destination: Path) -> None:
    inventory(payload)
    with tarfile.open(destination, 'w:gz', dereference=False) as archive:
        # Adding entries explicitly also preserves empty directories and symlinks.
        for path in [payload, *sorted(payload.rglob('*'))]:
            info = archive.gettarinfo(str(path), arcname='ForaDeCena/' + path.relative_to(payload).as_posix())
            info.uid = info.gid = 0
            info.uname = info.gname = ''  # Never expose the build machine's account name.
            if info.isfile():
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
            else:
                archive.addfile(info)


def run_diagnostic(executable: Path, work: Path) -> dict[str, object]:
    report_path = work / 'native-self-test.json'
    environment = system_environment()
    environment['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
    environment['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    completed = subprocess.run([str(executable), '--self-test', '--report', str(report_path)],
                               cwd=work, env=environment, timeout=180, check=False)
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if completed.returncode or not report.get('ok') or not report.get('frozen') or report.get('camera_opened'):
        detail = public_error(str(report.get('error', 'RuntimeError')) + ': ' + str(report.get('detail', 'invalid frozen test result')))
        raise RuntimeError('O autoteste nativo não passou: ' + detail)
    return report


def build(python_license: Path | None = None, opencv_wheel: Path | None = None,
          opencv_provenance: Path | None = None, mediapipe_wheel: Path | None = None,
          mediapipe_provenance: Path | None = None) -> Path:
    target = native_target()
    mediapipe_build = None
    if target == 'macos-x86_64':
        if mediapipe_wheel is None or mediapipe_provenance is None:
            raise ValueError('Mac Intel requires an explicitly built/validated MediaPipe wheel and provenance. No automatic downgrade.')
        from tools.mediapipe_intel import validate_artifact
        mediapipe_build = validate_artifact(mediapipe_wheel, mediapipe_provenance)
    elif mediapipe_wheel is not None or mediapipe_provenance is not None:
        raise ValueError('Custom Intel MediaPipe inputs are only valid for Mac Intel.')
    if bool(opencv_wheel) != bool(opencv_provenance):
        raise ValueError('Supply both --opencv-wheel and --opencv-provenance.')
    opencv_build=None
    if opencv_wheel is not None:
        from tools.opencv_artifact import validate_artifact
        opencv_build=validate_artifact(opencv_wheel,opencv_provenance)
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError('Use Python 3.14 com os requirements fixados do projeto.')
    if sys.platform == 'darwin' and int(platform.mac_ver()[0].split('.')[0]) < (15 if target == 'macos-x86_64' else 13):
        raise RuntimeError('O macOS deste build é inferior ao perfil selecionado.')
    if sys.platform.startswith('linux'):
        libc, version = platform.libc_ver()
        if libc != 'glibc' or tuple(map(int, version.split('.')[:2])) != (2, 35):
            raise RuntimeError('Para este candidato, compile em glibc 2.35 (Ubuntu 22.04). Não use uma base mais nova.')
    # Fail before creating deliverable artifacts when required inputs are missing.
    for name, (_, checksum) in MODEL_ASSETS.items():
        verify_model(ROOT / 'models' / name, checksum)
    upstream_files()
    work_base = checked_directory(ROOT / 'work' / 'native', ROOT / 'work')
    build_base = checked_directory(ROOT / 'build' / 'native', ROOT / 'build')
    output_base = checked_directory(ROOT / 'dist' / 'native', ROOT / 'dist')
    work = Path(tempfile.mkdtemp(prefix=target + '-', dir=work_base))
    build_root = Path(tempfile.mkdtemp(prefix=target + '-', dir=build_base))
    versions = collect_notices(work / 'notices', python_license)
    if sys.platform=='linux':
        from tools.build_minimal_numpy import validate_artifact
        wheels=list((ROOT/'work/numpy-minimal/wheels').glob('*.whl'))
        if len(wheels)!=1:
            raise ValueError('Linux candidates require the explicit no-BLAS NumPy wheel/provenance.')
        numpy_build=validate_artifact(wheels[0],ROOT/'work/numpy-minimal/provenance.json')
        (work/'notices/NUMPY-CUSTOM-BUILD.json').write_text(json.dumps(numpy_build,indent=2),encoding='utf-8')
    if mediapipe_build is not None:
        (work / 'notices' / 'MEDIAPIPE-INTEL-CUSTOM-BUILD.json').write_text(
            json.dumps(mediapipe_build, indent=2), encoding='utf-8')
    if opencv_build is not None:
        (work / 'notices' / 'OPENCV-CUSTOM-BUILD.json').write_text(json.dumps(opencv_build,indent=2),encoding='utf-8')
        native_notices=ROOT/'packaging/notices/opencv-minimal'
        if not native_notices.is_dir():
            raise FileNotFoundError('Missing custom OpenCV native notices')
        shutil.copytree(native_notices,work/'notices'/'opencv-minimal')
    if sys.platform == 'darwin':
        from PIL import Image
        with Image.open(ROOT / 'assets' / 'brand' / 'app-icon.png') as original:
            image = original.convert('RGBA')
            bounds = image.getchannel('A').point(lambda alpha: 255 if alpha >= 8 else 0).getbbox()
            if bounds is None:
                raise ValueError('Ícone vazio.')
            symbol = image.crop(bounds)
            symbol.thumbnail((960, 960), Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', (1024, 1024))
            canvas.alpha_composite(symbol, ((1024-symbol.width)//2, (1024-symbol.height)//2))
            canvas.save(work / 'app-icon.icns', format='ICNS')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(build_root / 'helper'), '--workpath', str(build_root / 'helper-work'),
                    str(ROOT / 'camera_output' / 'worker.spec')], cwd=ROOT, check=True)
    helper = build_root / 'helper' / 'ForaDeCenaVideoOutput'
    manifest = build_plan(target)
    manifest.update({'product': 'Fora de Cena', 'version': __version__, 'packages': versions,
                     'runtime_signature': runtime_signature(),
                     'programs': {'application': 'MIT', 'independent-video-output': 'GPL-2.0-only'},
                     'pyinstaller': metadata.version('pyinstaller'), 'developer_id_signed': False})
    if opencv_build is not None:
        manifest['opencv_build']=opencv_build
    if mediapipe_build is not None:
        manifest['mediapipe_intel_build'] = mediapipe_build
    (work / 'bundle-build.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    environment = dict(os.environ, FDC_UNIX_WORK=str(work), FDC_UNIX_HELPER=str(helper))
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(build_root / 'application'), '--workpath', str(build_root / 'application-work'),
                    str(ROOT / 'packaging' / 'fora_de_cena_unix.spec')], cwd=ROOT, env=environment, check=True)
    manifest = json.loads((work / 'bundle-build.json').read_text(encoding='utf-8'))
    payload = build_root / 'application' / ('Fora de Cena.app' if sys.platform == 'darwin' else 'ForaDeCena')
    files = inventory(payload)
    check_native_license_scope(files)
    native_libraries = [{'path': path.relative_to(payload).as_posix(), 'sha256': digest(path)}
                        for path in files if path.suffix in ('.so', '.dylib') or '.so.' in path.name]
    (work / 'native-libraries.json').write_text(json.dumps(native_libraries, indent=2), encoding='utf-8')
    print('Candidate native library basenames:', json.dumps(sorted({Path(row['path']).name for row in native_libraries})))
    executable = payload / 'Contents' / 'MacOS' / 'ForaDeCena' if sys.platform == 'darwin' else payload / 'ForaDeCena'
    if sys.platform == 'darwin':
        from tools.macos_bundle import audit_bundle
        audit = audit_bundle(payload, 'x86_64' if target == 'macos-x86_64' else 'arm64')
        manifest['minimum_target'] = 'macOS ' + audit['minimum_macos']
        (work / 'macos-bundle-audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    diagnostic = run_diagnostic(executable, work)
    if sys.platform == 'darwin':
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(payload)], check=True)
    manifest['validation'] = {'native_self_test': diagnostic['ok'], 'frozen': diagnostic['frozen'],
                              'camera_opened': diagnostic['camera_opened'],
                              'dependency_network_verified': False, 'real_camera_and_calls_tested': False,
                              'ad_hoc_signature_verified': sys.platform == 'darwin'}
    manifest['pending'].remove('native-build-and-self-test')
    output = Path(tempfile.mkdtemp(prefix=target + '-', dir=output_base))
    package_compliance(output, __version__, work / 'notices')
    artifact_name = f'ForaDeCena-{__version__}-{target}-experimental'
    if sys.platform == 'darwin':
        artifact = output / (artifact_name + '.dmg')
        with tempfile.TemporaryDirectory(prefix='dmg-stage-', dir=build_root) as staging:
            shutil.copytree(payload, Path(staging) / payload.name, symlinks=True)
            subprocess.run(['/usr/bin/hdiutil', 'create', '-volname', 'Fora de Cena', '-srcfolder', staging,
                            '-format', 'UDZO', str(artifact)], check=True)
    else:
        artifact = output / (artifact_name + '.tar.gz')
        create_tarball(payload, artifact)
    shutil.copyfile(work / 'native-self-test.json', output / 'native-self-test.json')
    # Integrity reports contain only relative package paths, never local user paths.
    shutil.copyfile(work / 'native-libraries.json', output / 'native-libraries.json')
    if sys.platform == 'darwin':
        shutil.copyfile(work / 'macos-bundle-audit.json', output / 'macos-bundle-audit.json')
    (output / 'candidate.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for path in sorted(output.iterdir()):
        if path.is_file() and not path.name.endswith('.sha256'):
            path.with_name(path.name + '.sha256').write_text(f'{digest(path)}  {path.name}\n', encoding='ascii')
    print(f'Candidato experimental gerado: {artifact.name}. Sem publicação; revisão de licenças nativas e testes reais pendentes.')
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', choices=TARGETS, help='Print the build plan without generating a package')
    parser.add_argument('--python-license', type=Path, help='License supplied with the Python distribution used for the build')
    parser.add_argument('--opencv-wheel',type=Path,help='Explicit selected custom OpenCV wheel')
    parser.add_argument('--opencv-provenance',type=Path,help='Provenance bound to the selected custom wheel')
    parser.add_argument('--mediapipe-wheel', type=Path, help='Explicit experimental Intel MediaPipe wheel')
    parser.add_argument('--mediapipe-provenance', type=Path, help='Provenance bound to the Intel MediaPipe wheel')
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(build_plan(args.plan), ensure_ascii=False, indent=2))
    else:
        build(args.python_license,args.opencv_wheel,args.opencv_provenance,
              args.mediapipe_wheel,args.mediapipe_provenance)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
