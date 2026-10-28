from __future__ import annotations
from contextlib import ExitStack
from pathlib import Path
import hashlib
import cv2
from .runtime_imports import without_optional_audio
with without_optional_audio():
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
from .gesture import Face, Point
from .recognition import GestureRecognizer
from .scene import Frame
from .effects import Silhouette
from .model_assets import MODEL_ASSETS


def model_options(folder: Path, name: str) -> python.BaseOptions:
    # The native Windows file loader fails on accented paths. Python reads Unicode
    # paths correctly; pass the exact verified bytes rather than reopening by path.
    model = (folder / name).read_bytes()
    if hashlib.sha256(model).hexdigest() != MODEL_ASSETS[name][1]:
        raise ValueError(f'Modelo alterado: {name}. Reinstale o app ou repare os modelos nos fontes.')
    return python.BaseOptions(model_asset_buffer=model)


class Detector:
    def __init__(self, folder: Path) -> None:
        self.resources = ExitStack()
        try:
            self.hand = self.resources.enter_context(vision.HandLandmarker.create_from_options(
                vision.HandLandmarkerOptions(
                    base_options=model_options(folder, 'hand_landmarker.task'),
                    running_mode=vision.RunningMode.VIDEO, num_hands=2,
                    min_hand_detection_confidence=0.65, min_hand_presence_confidence=0.65,
                    min_tracking_confidence=0.65)))
            self.face = self.resources.enter_context(vision.FaceDetector.create_from_options(
                vision.FaceDetectorOptions(
                    base_options=model_options(folder, 'face_detector.tflite'),
                    running_mode=vision.RunningMode.VIDEO, min_detection_confidence=0.65)))
        except Exception:
            self.resources.close()
            raise
        self.timestamp = -1
        self.recognizer = GestureRecognizer()
        self.progress = 0.0
        self.hint = 'Mostre o rosto e uma mão.'

    def detect(self, frame: Frame, captured_at: float, effect: str = 'anime') -> tuple[bool, int]:
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (640, max(1, round(h * 640 / w))))
        image = mp.Image(image_format=mp.ImageFormat.SRGB,
                         data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        self.timestamp = max(self.timestamp + 1, int(captured_at * 1000))
        faces = self.face.detect_for_video(image, self.timestamp).detections
        hands = self.hand.detect_for_video(image, self.timestamp).hand_landmarks
        if len(faces) != 1:
            self.recognizer.reset()
            self.progress = 0.0
            self.hint = 'Mostre o rosto de frente para a câmera.' if not faces else 'Mantenha somente seu rosto no enquadramento.'
            return False, len(faces)
        box = faces[0].bounding_box
        face = Face(box.origin_x, box.origin_y, box.width, box.height)
        sh, sw = small.shape[:2]
        points = [[Point(p.x * sw, p.y * sh) for p in hand] for hand in hands]
        result = self.recognizer.update(points, face, captured_at, effect)
        self.hint = result.hint
        self.progress = result.progress
        return result.matched, 1

    def close(self) -> None:
        self.resources.close()


class Segmenter:
    def __init__(self, folder: Path) -> None:
        name = 'selfie_segmenter_landscape.tflite'
        self.task = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=model_options(folder, name),
            running_mode=vision.RunningMode.VIDEO,
            output_confidence_masks=True, output_category_mask=False))
        self.timestamp = -1

    def capture(self, frame: Frame, captured_at: float) -> Silhouette:
        import numpy as np
        h,w=frame.shape[:2]
        small=cv2.resize(frame,(512,max(1,round(h*512/w))))
        image=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(small,cv2.COLOR_BGR2RGB))
        self.timestamp=max(self.timestamp+1,int(captured_at*1000))
        result=self.task.segment_for_video(image,self.timestamp)
        if not result.confidence_masks:
            raise ValueError('Modelo não retornou recorte.')
        # The binary landscape model has one foreground confidence channel.
        raw=result.confidence_masks[0].numpy_view().copy()
        mask=cv2.resize(raw,(w,h),interpolation=cv2.INTER_LINEAR)
        mask=np.clip((mask-0.15)/0.7,0,1).astype(np.float32)
        return Silhouette(captured_at,frame.copy(),mask)

    def close(self) -> None:
        self.task.close()
