"""Create a local Windows test candidate. Never upload or install the product."""
from __future__ import annotations
import argparse
import hashlib
from importlib import metadata
from packaging.requirements import Requirement
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from teleport_cam import __version__, __windows_version__
from teleport_cam.model_assets import MODEL_ASSETS
from teleport_cam.vision_backend import vision_backend, requirements_file
from setup_models import verify_model
from tools.distribution_licenses import prepare_model_notices, package_compliance, upstream_files, runtime_signature
from tools.build_diagnostics import public_error

PRIVATE_NAMES = {'.meet_pairing_key', 'user_settings.json', '.env', 'startup-error.log'}


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def check_inventory(folder: Path) -> list[Path]:
    paths = sorted(path for path in folder.rglob('*') if path.is_file())
    if not paths:
        raise ValueError('Pacote vazio')
    for path in paths:
        relative = path.relative_to(folder)
        if (path.is_symlink() or not path.resolve().is_relative_to(folder.resolve())
                or any(part.lower() in PRIVATE_NAMES | {'.git', '.venv', 'work', '__pycache__'}
                       or part.lower().startswith('.env.')
                       for part in relative.parts)):
            raise ValueError(f'Arquivo não permitido: {relative}')
    return paths


def collect_notices(destination: Path, python_license: Path | None = None) -> dict[str, str]:
    """Collect installed notices, without pretending that notices resolve GPL compatibility."""
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'MODELS.txt').unlink(missing_ok=True)  # Superseded pre-review note.
    versions: dict[str, str] = {}
    for line in (ROOT / requirements_file(vision_backend())).read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = requirement.name
        pins = list(requirement.specifier)
        if len(pins) != 1 or pins[0].operator != '==':
            raise ValueError('O lock exige versões exatas: ' + name)
        expected = pins[0].version
        distribution = metadata.distribution(name)
        if distribution.version != expected:
            raise ValueError(f'Versão diferente do lock: {name}')
        versions[name] = distribution.version
        target = destination / name
        target.mkdir(exist_ok=True)
        (target / 'METADATA.txt').write_text(distribution.read_text('METADATA') or '', encoding='utf-8')
        for item in distribution.files or ():
            if '.dist-info' not in str(item):
                continue
            if not ('licenses' in item.parts or item.name.lower().startswith(('license', 'copying', 'notice', 'authors'))):
                continue
            source = Path(distribution.locate_file(item))
            if source.is_file():
                # Preserve subdirectories within each distribution's dist-info.
                index = next(i for i, part in enumerate(item.parts) if part.endswith('.dist-info'))
                output = target.joinpath(*item.parts[index + 1:])
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
    python_license = python_license or Path(sys.base_prefix) / 'LICENSE.txt'
    if not python_license.is_file():
        raise FileNotFoundError('Licença do Python não encontrada. No build Unix, informe --python-license com a licença da distribuição Python usada.')
    shutil.copyfile(python_license, destination / 'PYTHON-LICENSE.txt')
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'packaging/TESTE_LOCAL.txt'):
        shutil.copyfile(ROOT / name, destination / Path(name).name)
    for path in (ROOT / 'packaging' / 'notices').glob('*.txt'):
        shutil.copyfile(path, destination / path.name)
    installer_distribution = metadata.distribution('pyinstaller')
    for item in installer_distribution.files or ():
        if item.name == 'COPYING.txt':
            shutil.copyfile(Path(installer_distribution.locate_file(item)), destination / 'PYINSTALLER-COPYING.txt')
    (destination / 'ROBOTO.txt').write_text(
        'Roboto-Regular.ttf / Roboto-Medium.ttf\nCopyright 2011 Google Inc. All Rights Reserved.\n'
        'Licensed under the Apache License, Version 2.0.\n'
        'License text: APACHE-2.0.txt for the Intel profile; mediapipe/licenses/LICENSE otherwise.\n'
        'Original copyright/license metadata is retained in both font files.\n', encoding='utf-8')
    prepare_model_notices(destination)
    return versions


def write_checksum(path: Path) -> None:
    path.with_name(path.name + '.sha256').write_text(f'{digest(path)}  {path.name}\n', encoding='ascii')


def run_diagnostic(executable: Path, cwd: Path, report_path: Path, temp_root: Path | None = None) -> None:
    report_path.unlink(missing_ok=True)
    environment = {key: value for key, value in os.environ.items()
                   if key not in ('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV')}
    environment['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
    if temp_root is not None:
        environment['TEMP'] = str(temp_root)
        environment['TMP'] = str(temp_root)
    result = subprocess.run([str(executable), '--self-test', '--report', str(report_path)],
                            cwd=cwd, env=environment, timeout=120,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if result.returncode or not report.get('ok') or not report.get('frozen') or report.get('camera_opened'):
        raise RuntimeError('O diagnóstico do executável não passou: ' + public_error(str(report)))


def verify_portable(archive_path: Path, work: Path) -> None:
    # Keep the Unicode regression check in every build, not just this machine's QA.
    with tempfile.TemporaryDirectory(prefix='validação portátil-', dir=work) as temporary:
        extracted = Path(temporary).resolve()
        if not extracted.is_relative_to(work.resolve()):
            raise ValueError('Pasta temporária fora do projeto')
        with zipfile.ZipFile(archive_path) as archive:
            for entry in archive.infolist():
                if not (extracted / entry.filename).resolve().is_relative_to(extracted):
                    raise ValueError('Caminho inválido no ZIP')
            archive.extractall(extracted)
        payload = extracted / 'ForaDeCena'
        for line in (payload / 'bundle-files.sha256').read_text(encoding='utf-8').splitlines():
            expected, relative = line.split('  ', 1)
            path = (payload / relative).resolve()
            if not path.is_relative_to(payload.resolve()) or digest(path) != expected:
                raise ValueError(f'Inventário extraído inválido: {relative}')
        run_diagnostic(payload / 'ForaDeCena.exe', extracted, work / 'extracted-self-test.json')


def verify_single_file(executable: Path, work: Path) -> None:
    with tempfile.TemporaryDirectory(prefix='executável único-', dir=work) as temporary:
        folder = Path(temporary).resolve()
        if not folder.is_relative_to(work.resolve()):
            raise ValueError('Pasta temporária fora do projeto')
        copy = folder / 'Fora de Cena.exe'
        shutil.copyfile(executable, copy)
        # No adjacent resources, and force the bootloader's extraction path to Unicode.
        run_diagnostic(copy, folder, work / 'single-file-self-test.json', temp_root=folder)
        if list(folder.glob('_MEI*')):
            raise RuntimeError('A extração temporária não foi removida após fechar o executável.')


def build(iscc: Path, portable_only: bool = False, single_file: bool = False) -> list[Path]:
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('Compile em Windows x64 com Python x64.')
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError('Use o ambiente Python 3.14 do projeto.')
    if not portable_only and not single_file and not iscc.is_file():
        raise FileNotFoundError('Instale o compilador Inno Setup oficial e informe --iscc.')
    for name, (_, expected) in MODEL_ASSETS.items():
        verify_model(ROOT / 'models' / name, expected)
    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    versions = collect_notices(work / 'bundle-notices')
    # Fail before producing binaries if corresponding third-party sources changed.
    upstream_files()
    helper_root = ROOT / 'build' / 'video-output'
    if not helper_root.resolve().is_relative_to((ROOT / 'build').resolve()) or not (helper_root / 'ForaDeCenaVideoOutput').resolve().is_relative_to((ROOT / 'build').resolve()):
        raise ValueError('Destino do componente fora da pasta prevista')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(helper_root), '--workpath', str(ROOT / 'build' / 'pyinstaller-output'),
                    str(ROOT / 'camera_output' / 'worker.spec')], cwd=ROOT, check=True)
    manifest = {
        'product': 'Fora de Cena', 'version': __version__, 'platform': 'windows-x64',
        'candidate': 'owner-review', 'distribution_ready': False, 'signed': False,
        'format': 'single-file' if single_file else 'one-folder',
        'pending': ['owner-publication-approval', 'real-camera-and-call-validation'],
        'programs': {'application': 'MIT', 'independent-video-output': 'GPL-2.0-only'},
        'runtime_signature': runtime_signature(),
        'interface': 'standard raw BGR24 video over local anonymous pipes',
        'excluded_from_main_process': ['pyvirtualcam', 'opencv-videoio-ffmpeg'],
        'python': platform.python_version(), 'pyinstaller': metadata.version('pyinstaller'),
        'packages': versions,
    }
    (work / 'bundle-build.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    mode = 'onefile' if single_file else 'onedir'
    build_root = ROOT / 'build' / ('windows-single-file' if single_file else 'windows')
    # PyInstaller may replace its previous output. Refuse redirected/junction paths.
    allowed_build = (ROOT / 'build').resolve()
    if not build_root.resolve().is_relative_to(allowed_build) or not (build_root / 'ForaDeCena').resolve().is_relative_to(allowed_build):
        raise ValueError('Destino de build fora da pasta prevista')
    environment = dict(os.environ, FDC_BUILD_MODE=mode)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(build_root), '--workpath', str(ROOT / 'build' / f'pyinstaller-{mode}'),
                    str(ROOT / 'packaging' / 'fora_de_cena.spec')], cwd=ROOT, env=environment, check=True)
    output = ROOT / 'dist' / 'windows'
    output.mkdir(parents=True, exist_ok=True)
    package_compliance(output, __version__, work / 'bundle-notices')
    if single_file:
        verify_single_file(build_root / 'ForaDeCena.exe', work)
        artifact = output / f'ForaDeCena-{__version__}-Portatil.exe'
        shutil.copyfile(build_root / 'ForaDeCena.exe', artifact)
        write_checksum(artifact)
        print(f'{artifact.name}: {artifact.stat().st_size / 1024 / 1024:.1f} MiB · executável único, sem instalador')
        return [artifact]
    payload = build_root / 'ForaDeCena'
    packaged_names = [path.relative_to(payload).as_posix().lower() for path in check_inventory(payload)]
    if any('opencv_videoio_ffmpeg' in name for name in packaged_names):
        raise ValueError('Plugin FFmpeg não deve ser distribuído')
    if any('pyvirtualcam' in name and not ('video_output/' in name or '/notices/' in name) for name in packaged_names):
        raise ValueError('PyVirtualCam fora do programa independente')
    # Run the compiled executable, in an unrelated CWD and with no Python environment.
    run_diagnostic(payload / 'ForaDeCena.exe', work, work / 'frozen-self-test.json')
    shutil.copyfile(ROOT / 'packaging' / 'TESTE_LOCAL.txt', payload / 'LEIA-ME.txt')
    files = check_inventory(payload)
    (payload / 'bundle-files.sha256').write_text(
        ''.join(f'{digest(path)}  {path.relative_to(payload).as_posix()}\n' for path in files), encoding='utf-8')
    files = check_inventory(payload)
    portable = output / f'ForaDeCena-{__version__}-Windows-x64-teste.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, 'ForaDeCena/' + path.relative_to(payload).as_posix())
    with zipfile.ZipFile(portable) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP inválido')
    verify_portable(portable, work)
    artifacts = [portable]
    if not portable_only:
        subprocess.run([str(iscc), f'/DAppVersion={__version__}',
                        '/DAppNumericVersion='+'.'.join(map(str,__windows_version__)), f'/DPayloadDir={payload}',
                        f'/DOutputDir={output}', str(ROOT / 'packaging' / 'installer.iss')],
                       cwd=ROOT, check=True)
        installer = output / f'ForaDeCena-{__version__}-Setup.exe'
        if not installer.is_file():
            raise FileNotFoundError('Instalador não foi gerado')
        artifacts.append(installer)
    for artifact in artifacts:
        write_checksum(artifact)
        print(f'{artifact.name}: {artifact.stat().st_size / 1024 / 1024:.1f} MiB')
    print('Candidato local validado. Publicação e instalação não foram executadas.')
    return artifacts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iscc', type=Path, default=ROOT / 'work' / 'inno-setup' / 'ISCC.exe')
    mode_options = parser.add_mutually_exclusive_group()
    mode_options.add_argument('--portable-only', action='store_true')
    mode_options.add_argument('--single-file', action='store_true')
    options = parser.parse_args()
    build(options.iscc, options.portable_only, options.single_file)
