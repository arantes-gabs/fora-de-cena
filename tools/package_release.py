"""Package the public source tree using an explicit allowlist; never publish."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from teleport_cam import __version__ as VERSION
FILES = (
    '.gitignore', '.gitattributes', 'LICENSE', 'README.md', 'COMO_USAR.md',
    'GUIA_RAPIDO.html', 'PRIVACY.md', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md',
    'CONTRIBUTING.md', 'CHANGELOG.md', 'DESENVOLVIMENTO.md', 'DISTRIBUIR.md',
    'NOTAS_DA_VERSAO.md', 'MAC_LINUX.md', 'OPENCV_ENXUTO_MAC.md', 'main.py', 'setup_models.py', 'smoke_test.py',
    '.github/workflows/native-candidates.yml', '.github/workflows/release-candidates.yml',
    'requirements.txt', 'requirements.lock.txt', 'requirements-build.txt',
    'requirements-opencv-build.txt', 'requirements-numpy-build.txt', 'packaging/opencv-minimal-profile.json',
    'packaging/opencv-minimal-source.patch',
    'packaging/mediapipe-intel-profile.json', 'packaging/mediapipe-intel-source.patch', 'MAC_INTEL.md', 'MULTIPLATAFORMA.md',
    'INICIAR.bat', 'INSTALAR.bat', 'camera_output/LICENSE',
)
FOLDERS = {
    'teleport_cam': {'.py'}, 'camera_output': {'.py', '.md', '.spec', '.txt'},
    'tests': {'.py', '.mjs'}, 'meet_extension': {'.js', '.json', '.html', '.css'},
    'tools': {'.py'}, 'packaging': {'.spec', '.iss', '.txt', '.md'},
}
ASSETS = (
    'assets/README.md', 'assets/gestures/README.md',
    'assets/brand/readme-cover.png', 'assets/brand/app-icon.png', 'assets/brand/app-icon.ico',
    *(f'assets/gestures/{name}.png' for name in
      ('teleporte', 'selo-uma-mao', 'poeira', 'digital', 'palma', 'portal', 'manual')),
)
PRIVATE_NAMES = {'.meet_pairing_key', 'user_settings.json', 'startup-error.log'}


def release_files(root: Path = ROOT) -> list[Path]:
    paths = [root / name for name in (*FILES, *ASSETS)]
    for folder, suffixes in FOLDERS.items():
        paths.extend(path for path in (root / folder).rglob('*')
                     if path.is_file() and path.suffix in suffixes
                     and '__pycache__' not in path.parts
                     and path.name not in PRIVATE_NAMES
                     and not path.name.startswith('.env'))
    for path in paths:
        if (not path.is_file() or path.is_symlink()
                or not path.resolve().is_relative_to(root.resolve())):
            raise ValueError(f'Arquivo ausente ou fora do projeto: {path.name}')
    return sorted(set(paths))


def build(root: Path = ROOT, destination: Path | None = None) -> Path:
    destination = destination or root / 'dist'
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f'fora-de-cena-{VERSION}-source.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in release_files(root):
            name = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f'fora-de-cena-{VERSION}/{name}', date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None:
            raise ValueError('Arquivo compactado inválido.')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    print(f'Pacote de fontes: {archive.name} · {len(release_files(root))} arquivos · {archive.stat().st_size} bytes')
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(destination=args.output)
