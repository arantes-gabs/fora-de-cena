"""Bind a native candidate to a selected custom wheel, not just a version string."""
from importlib import metadata
from pathlib import Path
import ast
import hashlib
import json
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def used_symbols(root=ROOT):
    symbols=set()
    for path in (root/'teleport_cam').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='cv2':
                symbols.add(node.attr)
    return sorted(symbols)


def inspect_runtime(cv2, system=None):
    missing=[s for s in used_symbols() if not hasattr(cv2,s)]
    if missing: raise ValueError('OpenCV missing application symbols: '+', '.join(missing))
    info=cv2.getBuildInformation()
    modules=re.search(r'To be built:\s+([^\n]+)',info)
    if not modules or 'highgui' in modules.group(1).split():
        raise ValueError('HighGUI must be absent from the custom build')
    system=system or sys.platform
    if system not in ('darwin','linux'):
        raise ValueError('Custom OpenCV runtime is only validated on macOS/Linux')
    backend=cv2.CAP_AVFOUNDATION if system=='darwin' else cv2.CAP_V4L2
    if not cv2.videoio_registry.hasBackend(backend):
        raise ValueError('Required native capture backend missing')
    if cv2.videoio_registry.hasBackend(cv2.CAP_FFMPEG) or cv2.videoio_registry.hasBackend(cv2.CAP_GSTREAMER):
        raise ValueError('Forbidden video backend enabled')
    if not re.search(r'JPEG:\s+(?!NO\b)\S+',info):
        raise ValueError('JPEG support missing')
    return {'application_symbols':used_symbols(),'avfoundation':system=='darwin',
            'v4l2':system=='linux','ffmpeg':False,
            'gstreamer':False,'highgui':False,'jpeg':True,'camera_opened':False,
            'modules':modules.group(1).split()}


def validate_artifact(wheel: Path, provenance: Path):
    record=json.loads(provenance.read_text(encoding='utf-8'))
    if not record.get('custom_build') or record.get('distribution_ready'):
        raise ValueError('Expected an experimental custom-build provenance record')
    checksum=digest(wheel)
    if record['wheel']['sha256']!=checksum or record['wheel']['filename']!=wheel.name:
        raise ValueError('Selected wheel differs from provenance')
    profile_path=ROOT/'packaging/opencv-minimal-profile.json'
    profile=json.loads(profile_path.read_text(encoding='utf-8'))
    if (record.get('profile_sha256')!=digest(profile_path) or
            record.get('source_patch_sha256')!=digest(ROOT/'packaging/opencv-minimal-source.patch') or
            record.get('source')!=profile['source_distribution']):
        raise ValueError('Selected build recipe differs from provenance')
    providers=[d.metadata['Name'].lower().replace('_','-') for d in metadata.distributions()
               if d.metadata['Name'].lower().replace('_','-') in
               ('opencv-python','opencv-contrib-python','opencv-python-headless','opencv-contrib-python-headless')]
    if providers!=['opencv-contrib-python']:
        raise ValueError('Expected exactly one cv2 provider: '+repr(providers))
    from tools.opencv_profile import native_target
    target=native_target()
    if record.get('native_target', 'macos-arm64')!=target:
        raise ValueError('Selected OpenCV wheel belongs to a different native target')
    distribution=metadata.distribution('opencv-contrib-python')
    if distribution.version!=record['source']['version']:
        raise ValueError('Installed OpenCV version differs from selected source')
    direct=json.loads(distribution.read_text('direct_url.json') or '{}')
    installed_hash=direct.get('archive_info',{}).get('hashes',{}).get('sha256')
    if installed_hash!=checksum:
        raise ValueError('Test venv must install the selected local wheel explicitly')
    with zipfile.ZipFile(wheel) as archive:
        native=[n for n in archive.namelist() if n.endswith(('.so','.dylib'))]
        if not native: raise ValueError('Wheel has no native bindings')
        for name in native:
            installed=Path(distribution.locate_file(name))
            if hashlib.sha256(archive.read(name)).hexdigest()!=digest(installed):
                raise ValueError('Installed native file differs from wheel: '+name)
    import cv2
    record['runtime_validation']=inspect_runtime(cv2)
    return record
