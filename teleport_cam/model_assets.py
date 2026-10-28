"""Versioned official model URLs and pinned baseline SHA-256 digests."""
MODEL_ASSETS: dict[str, tuple[str, str]] = {
    'selfie_segmenter_landscape.tflite': (
        'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter_landscape/float16/1/selfie_segmenter_landscape.tflite',
        '490e9ea734313e0de10fa0cd9e3c6133e36ea4db2b7a49bde9ef019f72796b8e'),
    'hand_landmarker.task': (
        'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
        'fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1'),
    'face_detector.tflite': (
        'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
        'b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f'),
}


def active_model_assets(backend: str | None = None) -> dict[str, tuple[str, str]]:
    from .vision_backend import vision_backend
    backend = vision_backend() if backend is None else backend
    if backend == 'opencv-dnn':
        from .opencv_models import MODEL_ASSETS as opencv_assets
        return opencv_assets
    if backend != 'mediapipe':
        raise ValueError('Backend de visão desconhecido.')
    return MODEL_ASSETS
