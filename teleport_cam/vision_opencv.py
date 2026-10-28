"""Intel vision adapter. CPU only; no MediaPipe/ONNX Runtime or network imports.

Model conventions follow OpenCV Zoo at the commit pinned in opencv_models.
The gesture state machine and video compositor remain shared across platforms.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .effects import Silhouette
from .gesture import Face, Point
from .opencv_models import FACE, HAND, PALM, PERSON, verified_path
from .recognition import GestureRecognizer
from .scene import Frame


def cpu_net(folder: Path, name: str) -> cv2.dnn.Net:
    net = cv2.dnn.readNetFromONNX(str(verified_path(folder, name)))
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


def palm_anchors() -> np.ndarray:
    # The model has two anchors per 24x24 cell and six per 12x12 cell.
    return np.asarray([(float(x + .5) / size, float(y + .5) / size)
                       for size, repeats in ((24, 2), (12, 6))
                       for y in range(size) for x in range(size)
                       for _ in range(repeats)], dtype=np.float32)


ANCHORS = palm_anchors()


def palm_input(frame: Frame) -> tuple[np.ndarray, float, tuple[int, int]]:
    h, w = frame.shape[:2]
    scale = 192 / max(h, w)
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    small = cv2.resize(frame, size)
    left, top = (192 - size[0]) // 2, (192 - size[1]) // 2
    padded = cv2.copyMakeBorder(small, top, 192-size[1]-top,
                               left, 192-size[0]-left, cv2.BORDER_CONSTANT, value=0)
    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    return rgb[np.newaxis].astype(np.float32) / 255, scale, (left, top)


def decode_palms(boxes: np.ndarray, logits: np.ndarray, scale: float,
                 padding: tuple[int, int]) -> np.ndarray:
    if boxes.shape != (1, 2016, 18) or logits.shape != (1, 2016, 1):
        raise ValueError('Saída inválida do detector de mãos.')
    if not np.isfinite(boxes).all() or not np.isfinite(logits).all():
        raise ValueError('Coordenadas de mão inválidas.')
    scores = 1 / (1 + np.exp(-np.clip(logits[0, :, 0], -80, 80)))
    indices = np.flatnonzero(scores >= .65)
    if not len(indices):
        return np.empty((0, 19), dtype=np.float32)
    raw = boxes[0, indices]
    center = (raw[:, :2] + ANCHORS[indices] * 192 - padding) / scale
    size = raw[:, 2:4] / scale
    valid = (size > 1).all(axis=1)
    center, size, raw, indices = center[valid], size[valid], raw[valid], indices[valid]
    if not len(indices):
        return np.empty((0, 19), dtype=np.float32)
    xywh = np.c_[center-size/2, size]
    # NMSBoxes expects x/y/width/height, not x1/y1/x2/y2.
    keep = np.asarray(cv2.dnn.NMSBoxes(xywh.tolist(), scores[indices].tolist(),
                                      .65, .3, top_k=64), dtype=np.intp).reshape(-1)[:2]
    landmarks = (raw[:, 4:].reshape(-1, 7, 2) + ANCHORS[indices, None] * 192 - padding) / scale
    return np.c_[xywh[keep, :2], (center+size/2)[keep],
                 landmarks[keep].reshape(-1, 14), scores[indices[keep]]].astype(np.float32)


def hand_transform(palm: np.ndarray) -> np.ndarray:
    landmarks = palm[4:18].reshape(7, 2)
    wrist, middle_base = landmarks[0], landmarks[2]
    direction = middle_base - wrist
    if np.linalg.norm(direction) < 1 or not np.isfinite(palm).all():
        raise ValueError('Região da mão degenerada.')
    angle = np.degrees(np.pi/2 - np.arctan2(-direction[1], direction[0]))
    rotation = cv2.getRotationMatrix2D(tuple(map(float, (palm[:2]+palm[2:4])/2)), float(angle), 1)
    rotated = cv2.transform(landmarks[None].astype(np.float64), rotation)[0]
    low, high = rotated.min(axis=0), rotated.max(axis=0)
    center = (low+high)/2 + np.array([0, -.4]) * (high-low)
    side = float(max(high-low) * 3)
    if side < 2:
        raise ValueError('Região da mão muito pequena.')
    transform = rotation * (224 / side)
    transform[:, 2] += 112 - center * (224 / side)
    return transform


def hand_input(frame: Frame, palm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    transform = hand_transform(palm)
    crop = cv2.warpAffine(frame, transform, (224, 224), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    return rgb[np.newaxis].astype(np.float32) / 255, transform


def decode_hand(outputs: tuple[np.ndarray, ...], transform: np.ndarray) -> list[Point]:
    if len(outputs) != 4 or outputs[0].shape != (1, 63) or outputs[1].size != 1:
        raise ValueError('Saída inválida do modelo de pontos da mão.')
    if not all(np.isfinite(item).all() for item in outputs):
        raise ValueError('Pontos da mão inválidos.')
    if float(outputs[1].reshape(-1)[0]) < .75:
        return []
    xy = outputs[0].reshape(21, 3)[:, :2]
    mapped = cv2.transform(xy[None], cv2.invertAffineTransform(transform))[0]
    return [Point(float(x), float(y)) for x, y in mapped]


class Detector:
    def __init__(self, folder: Path) -> None:
        # Leave CPU time for capture, composition and Tk instead of oversubscribing.
        cv2.setNumThreads(2)
        self.palm = cpu_net(folder, PALM)
        self.hand = cpu_net(folder, HAND)
        self.face = cv2.FaceDetectorYN.create(str(verified_path(folder, FACE)), '', (320, 320),
                    score_threshold=.75, nms_threshold=.3, top_k=64,
                    backend_id=cv2.dnn.DNN_BACKEND_OPENCV, target_id=cv2.dnn.DNN_TARGET_CPU)
        self.recognizer = GestureRecognizer()
        self.progress = 0.0
        self.hint = 'Mostre o rosto e uma mão.'

    def validate_models(self) -> None:
        """Exercise both hand nets even when the diagnostic image has no face."""
        self.palm.setInput(np.zeros((1, 192, 192, 3), np.float32))
        boxes, scores = self.palm.forward(self.palm.getUnconnectedOutLayersNames())
        decode_palms(boxes, scores, 1, (0, 0))
        self.hand.setInput(np.zeros((1, 224, 224, 3), np.float32))
        decode_hand(self.hand.forward(self.hand.getUnconnectedOutLayersNames()),
                    np.array([[1., 0., 0.], [0., 1., 0.]]))

    def detect(self, frame: Frame, captured_at: float, effect: str = 'anime') -> tuple[bool, int]:
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (640, max(1, round(h * 640 / w))))
        _, faces = self.face.detect(cv2.resize(small, (320, 320)))
        count = 0 if faces is None else len(faces)
        if count != 1:
            self.recognizer.reset()
            self.progress = 0.0
            self.hint = ('Mostre o rosto de frente para a câmera.' if not count
                         else 'Mantenha somente seu rosto no enquadramento.')
            return False, count
        sh, sw = small.shape[:2]
        x, y, fw, fh = faces[0, :4]
        face = Face(float(x*sw/320), float(y*sh/320), float(fw*sw/320), float(fh*sh/320))
        blob, scale, padding = palm_input(small)
        self.palm.setInput(blob)
        boxes, scores = self.palm.forward(self.palm.getUnconnectedOutLayersNames())
        palms = decode_palms(boxes, scores, scale, padding)
        hands: list[list[Point]] = []
        for palm in palms:
            try:
                blob, transform = hand_input(small, palm)
            except ValueError:
                # A noisy/degenerate candidate is not a fatal model failure.
                continue
            self.hand.setInput(blob)
            points = decode_hand(self.hand.forward(self.hand.getUnconnectedOutLayersNames()), transform)
            if points:
                hands.append(points)
        # Every update uses this frame's points. No cached landmarks can hold a gesture.
        result = self.recognizer.update(hands, face, captured_at, effect)
        self.hint, self.progress = result.hint, result.progress
        return result.matched, 1

    def close(self) -> None:
        self.recognizer.reset()
        self.palm = self.hand = self.face = None


class Segmenter:
    def __init__(self, folder: Path) -> None:
        self.net = cpu_net(folder, PERSON)

    def capture(self, frame: Frame, captured_at: float) -> Silhouette:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(cv2.resize(frame, (192, 192)), cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32)/255 - .5)/.5
        self.net.setInput(cv2.dnn.blobFromImage(normalized))
        result = self.net.forward()
        if result.shape != (1, 2, 192, 192) or not np.isfinite(result).all():
            raise ValueError('Modelo não retornou um recorte válido.')
        mask = cv2.resize(result[0, 1], (w, h), interpolation=cv2.INTER_LINEAR)
        return Silhouette(captured_at, frame.copy(), np.clip(mask, 0, 1).astype(np.float32))

    def close(self) -> None:
        self.net = None
