"""Official OpenCV Zoo assets; build/setup downloads only, never runtime downloads."""
from __future__ import annotations

import hashlib
from pathlib import Path

COMMIT = '48b10fa505aeb51fbd127fc60a5c660040e823b7'
BASE_URL = f'https://media.githubusercontent.com/media/opencv/opencv_zoo/{COMMIT}/models'
PALM = 'palm_detection_mediapipe_2023feb.onnx'
HAND = 'handpose_estimation_mediapipe_2023feb.onnx'
PERSON = 'human_segmentation_pphumanseg_2023mar.onnx'
FACE = 'face_detection_yunet_2023mar.onnx'
MODEL_ASSETS: dict[str, tuple[str, str]] = {
    PALM: (f'{BASE_URL}/palm_detection_mediapipe/{PALM}',
           '78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c'),
    HAND: (f'{BASE_URL}/handpose_estimation_mediapipe/{HAND}',
           'db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c'),
    PERSON: (f'{BASE_URL}/human_segmentation_pphumanseg/{PERSON}',
             '552d8a984054e59b5d773d24b9b12022b22046ceb2bbc4c9aaeaceb36a9ddf24'),
    FACE: (f'{BASE_URL}/face_detection_yunet/{FACE}',
           '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),
}


def verified_path(folder: Path, name: str) -> Path:
    path = folder / name
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Modelo excedeu o limite permitido.')
    if hashlib.sha256(path.read_bytes()).hexdigest() != MODEL_ASSETS[name][1]:
        raise ValueError(f'Modelo alterado: {name}. Reinstale o app ou repare os modelos nos fontes.')
    return path
