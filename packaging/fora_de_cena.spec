"""Windows x64: one-folder and single-executable candidates share one recipe."""
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

root = Path(SPECPATH).parent
single_file = os.environ.get('FDC_BUILD_MODE') == 'onefile'
datas = [
    (str(root / 'assets' / 'brand' / 'app-icon.ico'), 'assets/brand'),
    (str(root / 'assets' / 'brand' / 'app-icon.png'), 'assets/brand'),
    (str(root / 'work' / 'bundle-notices'), 'notices'),
    (str(root / 'work' / 'bundle-build.json'), '.'),
    (str(root / 'build' / 'video-output' / 'ForaDeCenaVideoOutput'), 'video_output'),
]
for name in ('manifest.json', 'package.json', 'background.js', 'heartbeat.js', 'protocol.js', 'popup.js', 'popup.html', 'popup.css'):
    datas.append((str(root / 'meet_extension' / name), 'meet_extension'))
for name in ('teleporte.png', 'selo-uma-mao.png', 'poeira.png', 'digital.png', 'palma.png', 'portal.png', 'manual.png'):
    datas.append((str(root / 'assets' / 'gestures' / name), 'assets/gestures'))
for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'GUIA_RAPIDO.html'):
    datas.append((str(root / name), '.'))
for name in ('hand_landmarker.task', 'face_detector.tflite', 'selfie_segmenter_landscape.tflite'):
    datas.append((str(root / 'models' / name), 'models'))
datas += collect_data_files('customtkinter')
datas += collect_data_files('mediapipe')
binaries = collect_dynamic_libs('mediapipe')

a = Analysis(
    [str(root / 'main.py')], pathex=[str(root)], binaries=binaries, datas=datas,
    hiddenimports=['mediapipe.tasks.c'],
    # MediaPipe imports drawing_utils eagerly, which requires matplotlib.
    # Include its noninteractive backend only; never open plots or audio devices.
    hooksconfig={'matplotlib': {'backends': ['Agg']}},
    excludes=['IPython', 'jupyter', 'pytest', 'readline', 'sounddevice', 'pyvirtualcam', 'camera_output'],
    noarchive=False,
)
# File-video codecs are unused: capture always explicitly uses DirectShow/MSMF.
# Exclude the FFmpeg plugin (LGPL) instead of redistributing unused video codecs.
a.binaries = [entry for entry in a.binaries if 'opencv_videoio_ffmpeg' not in entry[0].lower()]
a.datas = [entry for entry in a.datas if 'opencv_videoio_ffmpeg' not in entry[0].lower()]
a.datas = [entry for entry in a.datas if Path(entry[0]).name != 'direct_url.json']
if any(name == 'pyvirtualcam' or name.startswith('pyvirtualcam.') for name, source, kind in a.pure):
    raise ValueError('PyVirtualCam must not be imported by the graphical application')
pyz = PYZ(a.pure)
payload = [a.binaries, a.datas] if single_file else [[]]
exe = EXE(
    pyz, a.scripts, *payload, exclude_binaries=not single_file, name='ForaDeCena',
    debug=False, strip=False, upx=False, console=False,
    icon=str(root / 'assets' / 'brand' / 'app-icon.ico'),
    version=str(root / 'packaging' / 'version_info.txt'),
)
if not single_file:
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ForaDeCena')
