"""Desktop entry point; diagnostics never open a webcam, window or Meet bridge."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import traceback

from . import __version__
from .paths import data_file, resource_root


def self_test() -> dict[str, object]:
    import cv2
    import numpy as np
    import customtkinter
    from PIL import Image, ImageFont
    import tkinter as tk
    from .app import App
    from .vision import Detector, Segmenter
    from .gesture_guides import GUIDES
    from .model_assets import MODEL_ASSETS
    from .effects import AnimeTeleportEffect, Silhouette
    from .tk_resources import verify_tk_data
    from setup_models import verify_model
    from .virtual_output import VirtualOutput, output_command, output_environment
    import subprocess
    import zlib

    root = resource_root()
    # Tcl() creates an interpreter without a window, camera or Meet bridge.
    tcl_version = tk.Tcl().eval('info patchlevel')
    font_root = Path(customtkinter.__file__).resolve().parent / 'assets' / 'fonts'
    for name in ('Roboto-Regular.ttf', 'Roboto-Medium.ttf'):
        ImageFont.truetype(str(font_root / 'Roboto' / name), 12)
    tk_data_layout = verify_tk_data(root) if getattr(sys, 'frozen', False) else 'development'
    for name, (_, digest) in MODEL_ASSETS.items():
        verify_model(root / 'models' / name, digest)
    for name in {guide.image for guide in GUIDES.values()}:
        with Image.open(root / 'assets' / 'gestures' / name) as image:
            image.verify()
    with Image.open(root / 'assets' / 'brand' / 'app-icon.ico') as icon:
        icon.verify()
    for name in ('GUIA_RAPIDO.html', 'meet_extension/manifest.json', 'LICENSE'):
        if not (root / name).is_file():
            raise FileNotFoundError(name)
    if getattr(sys, 'frozen', False):
        if not (root / 'customtkinter' / 'assets' / 'themes' / 'blue.json').is_file():
            raise FileNotFoundError('Tema da interface')
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    detector = Detector(root / 'models')
    try:
        detector.detect(frame, 1.0, 'anime')
    finally:
        detector.close()
    segmenter = Segmenter(root / 'models')
    try:
        result = segmenter.capture(frame, 1.0)
        if result.mask.shape != frame.shape[:2]:
            raise ValueError('Dimensões do recorte inválidas')
    finally:
        segmenter.close()
    # Exercise the packaged compositor, including the bounded macOS path.
    backdrop=np.full((720,1280,3),40,np.uint8)
    mask=np.zeros((720,1280),np.float32)
    mask[30:700,300:980]=1
    live=backdrop.copy()
    live[mask>0]=(80,140,210)
    effect=AnimeTeleportEffect(Silhouette(10.0,live,mask),True,10.0)
    composed=effect.render(live,backdrop,10.2)
    if composed.shape!=live.shape or np.array_equal(composed,live) or np.array_equal(composed,backdrop):
        raise RuntimeError('O compositor de teleporte não produziu um quadro intermediário.')
    worker = subprocess.run(output_command() + ['--self-test'], capture_output=True, timeout=30, check=True,
                            env=output_environment(), creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    worker_report = json.loads(worker.stdout)
    if not worker_report.get('ok') or worker_report.get('forbidden_imports'):
        raise RuntimeError('O diagnóstico do processo de saída não passou.')
    output = VirtualOutput(320, 240, 30, 'obs', dry_run=True)
    try:
        output.send(frame)
        if output.last_crc32 != zlib.crc32(frame):
            raise RuntimeError('O quadro mudou no canal de saída.')
    finally:
        output.close()
    if 'pyvirtualcam' in sys.modules:
        raise RuntimeError('PyVirtualCam carregado indevidamente no processo principal.')
    manifest_path = root / 'bundle-build.json'
    signature = json.loads(manifest_path.read_text(encoding='utf-8')).get('runtime_signature') if manifest_path.is_file() else None
    return {'ok': True, 'version': __version__, 'frozen': bool(getattr(sys, 'frozen', False)),
            'runtime_signature': signature,
            'tcl_version': tcl_version,
            'tk_data_layout': tk_data_layout,
            'checks': ['imports', 'tcl_runtime', 'tk_data', 'fonts', 'assets', 'model_hashes', 'hand_face_inference', 'segmentation', 'teleport_compositor', 'independent_output_process', 'rawvideo_fidelity'],
            'camera_opened': False, 'application_network_requests': False,
            'dependency_network_verified': False, 'virtual_output_tested': False}


def gui_self_test() -> dict[str, object]:
    """Render the real guide images through Tk/Pillow without camera or Meet."""
    import customtkinter as ctk
    from PIL import Image
    from .gesture_guides import GUIDES

    root = ctk.CTk()
    root.withdraw()
    names = sorted({guide.image for guide in GUIDES.values()})
    try:
        label = ctk.CTkLabel(root, text='')
        label.pack()
        for name in names:
            with Image.open(resource_root() / 'assets' / 'gestures' / name) as original:
                image = original.convert('RGBA')
            illustration = ctk.CTkImage(light_image=image, dark_image=image, size=(96, 96))
            label.configure(image=illustration)
            root.update_idletasks()
            photo = illustration.create_scaled_photo_image(1.0, 'light')
            if photo.width() != 96 or photo.height() != 96:
                raise RuntimeError('Guide image did not render through Pillow/Tk.')
        return {'ok': True, 'version': __version__, 'frozen': bool(getattr(sys, 'frozen', False)),
                'guide_images_rendered': len(names), 'camera_opened': False, 'meet_bridge_opened': False}
    finally:
        root.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description='Fora de Cena')
    diagnostics = parser.add_mutually_exclusive_group()
    diagnostics.add_argument('--self-test', action='store_true')
    diagnostics.add_argument('--gui-self-test', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.self_test or args.gui_self_test:
        try:
            report = gui_self_test() if args.gui_self_test else self_test()
        except Exception as error:
            report = {'ok': False, 'error': type(error).__name__, 'detail': str(error)}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        elif sys.stdout is not None:
            print(json.dumps(report, ensure_ascii=False))
        return 0 if report['ok'] else 1
    try:
        from .app import main as run_app
        run_app()
        return 0
    except Exception as error:
        # No video, preferences or pairing key is written to this startup log.
        try:
            data_file('startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        except OSError:
            pass
        if sys.platform != 'win32' and sys.stderr is not None:
            print('Fora de Cena não abriu (' + type(error).__name__ + '). '
                  'Consulte startup-error.log na pasta de dados do aplicativo; '
                  'remova dados pessoais antes de compartilhar o log.', file=sys.stderr)
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,
                'Não foi possível abrir o Fora de Cena. Reinstale o aplicativo. '
                'Detalhes técnicos ficam em %LOCALAPPDATA%\\ForaDeCena\\startup-error.log.',
                'Fora de Cena', 0x10)
        return 1
