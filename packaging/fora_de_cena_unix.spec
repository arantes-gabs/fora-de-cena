"""Native, experimental macOS/Linux bundle. Never cross-compile or publish."""
import os
import json
import platform
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

root = Path(SPECPATH).parent
from teleport_cam import __version__, __windows_version__
if sys.platform not in ('darwin', 'linux'):
    raise RuntimeError('Run this recipe on macOS or Linux.')
work = Path(os.environ['FDC_UNIX_WORK']).resolve()
helper = Path(os.environ['FDC_UNIX_HELPER']).resolve()
if not work.is_relative_to((root / 'work').resolve()) or not helper.is_relative_to((root / 'build').resolve()):
    raise ValueError('Build input outside project build directories')
datas = [(str(work / 'notices'), 'notices'), (str(work / 'bundle-build.json'), '.'),
         (str(helper), 'video_output')]
for name in ('app-icon.png', 'app-icon.ico'):
    datas.append((str(root / 'assets' / 'brand' / name), 'assets/brand'))
for name in ('teleporte.png', 'selo-uma-mao.png', 'poeira.png', 'digital.png', 'palma.png', 'portal.png', 'manual.png'):
    datas.append((str(root / 'assets' / 'gestures' / name), 'assets/gestures'))
for name in ('manifest.json', 'package.json', 'background.js', 'heartbeat.js', 'protocol.js', 'popup.js', 'popup.html', 'popup.css'):
    datas.append((str(root / 'meet_extension' / name), 'meet_extension'))
for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'GUIA_RAPIDO.html', 'MAC_LINUX.md', 'MAC_INTEL.md', 'OPENCV_ENXUTO_MAC.md'):
    datas.append((str(root / name), '.'))
for name in ('hand_landmarker.task', 'face_detector.tflite', 'selfie_segmenter_landscape.tflite'):
    datas.append((str(root / 'models' / name), 'models'))
datas += collect_data_files('customtkinter') + collect_data_files('mediapipe')
a = Analysis([str(root / 'main.py')], pathex=[str(root)],
    binaries=collect_dynamic_libs('mediapipe'), datas=datas,
    # Pillow's native Tk bridge imports the finder dynamically on Linux.
    hiddenimports=['mediapipe.tasks.c', 'PIL._tkinter_finder', 'PIL._imagingtk'],
    hooksconfig={'matplotlib': {'backends': ['Agg']}},
    excludes=['IPython', 'jupyter', 'pytest', 'readline', 'sounddevice', 'pyvirtualcam', 'camera_output'], noarchive=False)
a.datas = [entry for entry in a.datas if Path(entry[0]).name != 'direct_url.json']
# Unix OpenCV may link FFmpeg directly: do not remove its libraries and break loading.
# The native codec/GUI libraries still need a corresponding-source/license review.
if any(name == 'pyvirtualcam' or name.startswith('pyvirtualcam.') for name, source, kind in a.pure):
    raise ValueError('Output library imported in the application process')
if sys.platform == 'darwin':
    from tools.macos_bundle import minimum_macos
    macos_architecture = platform.machine().lower()
    deployment_target = minimum_macos((source for name, source, kind in a.binaries), macos_architecture)
    manifest_path = work / 'bundle-build.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['minimum_target'] = 'macOS ' + deployment_target
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ForaDeCena',
          console=False, upx=False, strip=False, argv_emulation=False)
coll = COLLECT(exe, a.binaries, a.datas, name='ForaDeCena', upx=False, strip=False)
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Fora de Cena.app', icon=str(work / 'app-icon.icns'),
        bundle_identifier='app.foradecena.desktop', info_plist={
            'CFBundleDisplayName': 'Fora de Cena', 'LSMinimumSystemVersion': deployment_target,
            'CFBundleShortVersionString': '.'.join(map(str,__windows_version__[:3])),
            'CFBundleVersion': str(__windows_version__[-1]),
            'CFBundleGetInfoString': 'Fora de Cena '+__version__,
            'NSCameraUsageDescription': 'A câmera é usada para aplicar os efeitos locais escolhidos por você.',
            'NSHighResolutionCapable': True,
        })
