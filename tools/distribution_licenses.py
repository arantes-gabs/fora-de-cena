"""Corresponding source and notice artifacts for the independently built output tool."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from importlib import metadata

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = 'dbac4732168c21f1337e30182957130f678aa058'
LIBYUV_COMMIT = '19bbedfd3e37329900d34e104021f04d7205ad78'
MODEL_CARDS = {
    'hand_landmarker.task': ('hands.pdf', 'https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Hand%20Tracking%20(Lite_Full)%20with%20Fairness%20Oct%202021.pdf'),
    'face_detector.tflite': ('face.pdf', 'https://storage.googleapis.com/mediapipe-assets/MediaPipe%20BlazeFace%20Model%20Card%20(Short%20Range).pdf'),
    'selfie_segmenter_landscape.tflite': ('segmentation.pdf', 'https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Selfie%20Segmentation.pdf'),
}
MODEL_CARD_HASHES = {'hands.pdf': '43127ff8a92e22717f0d8c30dab3efef4641a29cbf50b15ae3de001be94ab76b',
                    'face.pdf': 'cd335c06fc0de7807cd815a0777a697932598bcdb28fa98adaaabf847485f758',
                    'segmentation.pdf': 'ef2e8d350891ba71699ac1e079658e697fc8d48c0f9253922990e907ecdade60'}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_signature(root: Path = ROOT) -> str:
    paths = list((root / 'teleport_cam').glob('*.py'))
    paths += [root / 'main.py', root / 'camera_output' / 'main.py', root / 'camera_output' / 'worker.spec',
              root / 'packaging' / 'fora_de_cena.spec', root / 'requirements.lock.txt']
    for relative in ('packaging/fora_de_cena_unix.spec', 'tools/build_unix.py', 'tools/macos_bundle.py', 'requirements-build.txt',
                     'requirements-opencv-build.txt', 'tools/build_minimal_opencv.py', 'tools/opencv_profile.py',
                     'requirements-numpy-build.txt', 'tools/build_minimal_numpy.py',
                     'tools/distribution_licenses.py', 'tools/package_release.py',
                     'tools/opencv_artifact.py', 'packaging/opencv-minimal-profile.json',
                     'packaging/opencv-minimal-source.patch'):
        if (root / relative).is_file():
            paths.append(root / relative)
    paths.append(root / 'requirements-intel.lock.txt')
    paths += list((root / 'packaging/notices/opencv-zoo').glob('*'))
    for relative in ('tools/build_mediapipe_intel.py', 'tools/mediapipe_intel.py',
                     'packaging/mediapipe-intel-profile.json', 'packaging/mediapipe-intel-source.patch'):
        if (root / relative).is_file():
            paths.append(root / relative)
    paths += list((root / "packaging/notices/opencv-minimal").glob("*"))
    result = hashlib.sha256()
    # Path ordering is case-insensitive on Windows and case-sensitive on macOS.
    # Use the portable relative spelling so identical sources share one signature.
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        result.update(path.relative_to(root).as_posix().encode('utf-8'))
        result.update(path.read_bytes().replace(b'\r\n', b'\n'))
    return result.hexdigest()


def git(directory: Path, *arguments: str) -> bytes:
    return subprocess.run(['git', '-C', str(directory), *arguments], check=True,
                          capture_output=True).stdout


def upstream_files() -> list[tuple[Path, str]]:
    source = ROOT / 'work' / 'vendor' / 'pyvirtualcam-0.15.0'
    libyuv = source / 'external' / 'libyuv'
    result: list[tuple[Path, str]] = []
    for directory, expected in ((source, UPSTREAM_COMMIT), (libyuv, LIBYUV_COMMIT)):
        if git(directory, 'rev-parse', 'HEAD').decode().strip() != expected:
            raise ValueError('Fonte de terceiro diferente do commit revisado')
        if git(directory, 'status', '--porcelain').strip():
            raise ValueError('Fonte de terceiro alterado; revisar antes de distribuir')
        for name in git(directory, 'ls-files', '-z').decode('utf-8').split('\0'):
            if not name:
                continue
            path = directory / name
            if path.is_dir():
                continue  # The pinned submodule is collected in its own iteration.
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError('Caminho inválido nos fontes de terceiros')
            result.append((path, 'pyvirtualcam-0.15.0/' + path.relative_to(source).as_posix()))
    return result


def prepare_model_notices(destination: Path) -> None:
    from teleport_cam.vision_backend import vision_backend
    if vision_backend() == 'opencv-dnn':
        import shutil
        from teleport_cam.opencv_models import COMMIT, MODEL_ASSETS as assets
        rows = ['# Modelos OpenCV Zoo (Mac Intel)', '', f'Commit oficial: {COMMIT}', '',
                'Palm/Hand/PPHumanSeg: Apache-2.0. YuNet: MIT.',
                'Modelos sem alterações; adaptação de pré/pós-processamento própria.', '']
        for name, (url, checksum) in assets.items():
            rows += [f'## {name}', f'Origem: {url}', f'SHA256: {checksum}', '']
        (destination / 'MODELS.md').write_text('\n'.join(rows), encoding='utf-8')
        notice_folder = ROOT / 'packaging/notices/opencv-zoo'
        shutil.copytree(notice_folder, destination / 'opencv-zoo')
        shutil.copyfile(notice_folder / 'APACHE-2.0.txt', destination / 'APACHE-2.0.txt')
        # The independent output tool still needs its original libyuv notices below.
        prepare_libyuv_notices(destination)
        return
    from teleport_cam.model_assets import MODEL_ASSETS
    rows = ['# Modelos MediaPipe', '',
            'Google LLC. Licença: Apache-2.0. Cópias sem alteração, hashes fixados no aplicativo.',
            'As fichas oficiais de cada família declaram: "Apache License, Version 2.0".', '',
            'Fichas consultadas localmente; seus hashes permitem identificar a evidência revisada.', '']
    for name, (card, url) in MODEL_CARDS.items():
        evidence = ROOT / 'work' / 'compliance' / 'model-cards' / card
        if not evidence.is_file() or sha256(evidence) != MODEL_CARD_HASHES[card]:
            raise FileNotFoundError('Falta a ficha oficial revisada: ' + card)
        model_url, checksum = MODEL_ASSETS[name]
        rows.extend([f'## {name}', f'Modelo: {model_url}', f'SHA256: {checksum}',
                     f'Ficha: {url}', f'SHA256 da ficha: {sha256(evidence)}', ''])
    (destination / 'MODELS.md').write_text('\n'.join(rows), encoding='utf-8')
    prepare_libyuv_notices(destination)


def prepare_libyuv_notices(destination: Path) -> None:
    source = ROOT / 'work' / 'vendor' / 'pyvirtualcam-0.15.0' / 'external' / 'libyuv'
    for name in ('LICENSE', 'PATENTS', 'AUTHORS'):
        path = source / name
        if path.is_file():
            target = destination / 'libyuv'
            target.mkdir(exist_ok=True)
            (target / name).write_bytes(path.read_bytes())


def package_compliance(output: Path, version: str, notices: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    sources = output / f'ForaDeCena-{version}-Fontes-Saida.zip'
    entries = upstream_files()
    for name in ('main.py', 'LICENSE', 'README.md', 'worker.spec', 'requirements.txt', 'requirements-build.txt'):
        entries.append((ROOT / 'camera_output' / name, 'camera_output/' + name))
    manifest = {'video_output_license': 'GPL-2.0-only', 'pyvirtualcam_version': '0.15.0',
                'pyvirtualcam_commit': UPSTREAM_COMMIT, 'libyuv_commit': LIBYUV_COMMIT,
                'sources': [{'path': name, 'sha256': sha256(path)} for path, name in entries]}
    distribution = metadata.distribution('pyvirtualcam')
    manifest['unmodified_upstream_native_binaries'] = [
        {'path': str(item).replace('\\', '/'), 'sha256': sha256(Path(distribution.locate_file(item)))}
        for item in distribution.files or () if item.suffix in ('.pyd', '.so', '.dylib')]
    with zipfile.ZipFile(sources, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path, name in entries:
            archive.write(path, name)
        archive.writestr('SOURCE_MANIFEST.json', json.dumps(manifest, indent=2))
    licenses = output / f'ForaDeCena-{version}-Licencas.zip'
    with zipfile.ZipFile(licenses, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(notices.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(notices).as_posix())
        archive.write(ROOT / 'camera_output' / 'LICENSE', 'video-output/GPL-2.0.txt')
        archive.write(ROOT / 'camera_output' / 'README.md', 'video-output/README.md')
    for path in (sources, licenses):
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Pacote de conformidade inválido')
        path.with_name(path.name + '.sha256').write_text(f'{sha256(path)}  {path.name}\n', encoding='ascii')
    return [sources, licenses]
