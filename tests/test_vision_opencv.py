import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from teleport_cam.model_assets import MODEL_ASSETS, active_model_assets
from teleport_cam.opencv_models import verified_path
from teleport_cam.vision_backend import requirements_file, vision_backend
from teleport_cam.vision_opencv import (ANCHORS, Detector, Segmenter, decode_hand,
                                       decode_palms, hand_input, hand_transform, palm_input)


class BackendTests(unittest.TestCase):
    def test_only_mac_intel_selects_dnn(self):
        for system, machine in [('win32', 'AMD64'), ('linux', 'x86_64'),
                                ('linux', 'aarch64'), ('darwin', 'arm64')]:
            self.assertEqual(vision_backend(system, machine), 'mediapipe')
        self.assertEqual(vision_backend('darwin', 'x86_64'), 'opencv-dnn')
        self.assertIs(active_model_assets('mediapipe'), MODEL_ASSETS)
        self.assertEqual(len(active_model_assets('opencv-dnn')), 4)
        self.assertEqual(requirements_file('opencv-dnn'), 'requirements-intel.lock.txt')
        with self.assertRaises(ValueError):
            active_model_assets('unknown')

    def test_corrupt_model_is_rejected_before_native_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / 'test.onnx').write_bytes(b'changed')
            assets = {'test.onnx': ('https://example.invalid', hashlib.sha256(b'valid').hexdigest())}
            with patch('teleport_cam.opencv_models.MODEL_ASSETS', assets):
                with self.assertRaisesRegex(ValueError, 'Modelo alterado'):
                    verified_path(path, 'test.onnx')


def sample_palm() -> np.ndarray:
    return np.array([70, 80, 130, 140, 100, 140, 80, 100, 100, 80,
                     115, 90, 130, 100, 90, 130, 80, 120, .9], np.float32)


class GeometryTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(cv2, 'dnn'), 'DNN is intentionally absent from other minimal profiles')
    def test_letterbox_and_palm_decode_restore_wide_frame_coordinates(self):
        blob, scale, padding = palm_input(np.zeros((240, 640, 3), np.uint8))
        self.assertEqual(blob.shape, (1, 192, 192, 3))
        self.assertEqual(blob.dtype, np.float32)
        boxes = np.zeros((1, 2016, 18), np.float32)
        scores = np.full((1, 2016, 1), -20, np.float32)
        index = 100
        center = np.array([320, 120])
        boxes[0, index, :2] = center * scale + padding - ANCHORS[index] * 192
        boxes[0, index, 2:4] = [60*scale, 80*scale]
        boxes[0, index, 4:] = np.tile(center*scale+padding-ANCHORS[index]*192, 7)
        scores[0, index, 0] = 10
        result = decode_palms(boxes, scores, scale, padding)
        self.assertEqual(result.shape, (1, 19))
        np.testing.assert_allclose(result[0, :4], [290, 80, 350, 160], atol=.001)
        np.testing.assert_allclose(result[0, 4:18].reshape(7, 2), np.tile(center, (7, 1)), atol=.001)

    @unittest.skipUnless(hasattr(cv2, 'dnn'), 'DNN is intentionally absent from other minimal profiles')
    def test_nms_receives_width_height_and_keeps_two_distinct_hands(self):
        boxes = np.zeros((1, 2016, 18), np.float32)
        scores = np.full((1, 2016, 1), -20, np.float32)
        for index, center in ((0, [40, 80]), (1, [41, 81]), (2, [150, 80])):
            boxes[0, index, :2] = center - ANCHORS[index]*192
            boxes[0, index, 2:4] = [30, 30]
            scores[0, index, 0] = 10-index
        result = decode_palms(boxes, scores, 1, (0, 0))
        self.assertEqual(len(result), 2)
        self.assertGreater(abs(result[0, 0] - result[1, 0]), 80)

    def test_rotated_hand_landmarks_round_trip_to_camera_coordinates(self):
        frame = np.zeros((240, 320, 3), np.uint8)
        for angle in (0, 50, -80):
            palm = sample_palm()
            rotation = cv2.getRotationMatrix2D((100, 110), angle, 1)
            palm[4:18] = cv2.transform(palm[4:18].reshape(1, 7, 2), rotation).reshape(-1)
            blob, transform = hand_input(frame, palm)
            self.assertEqual(blob.shape, (1, 224, 224, 3))
            original = np.tile(palm[4:6], (21, 1)).astype(np.float32)
            xy = cv2.transform(original[None], transform)[0]
            landmarks = np.c_[xy, np.zeros(21)].astype(np.float32).reshape(1, 63)
            points = decode_hand((landmarks, np.array([[.9]]), np.array([[1.]]), landmarks), transform)
            np.testing.assert_allclose([[p.x, p.y] for p in points], original, atol=.001)

    def test_uncertain_nonfinite_or_degenerate_hands_do_not_trigger(self):
        landmarks = np.zeros((1, 63), np.float32)
        outputs = (landmarks, np.array([[.1]]), np.zeros((1, 1)), landmarks)
        self.assertEqual(decode_hand(outputs, hand_transform(sample_palm())), [])
        with self.assertRaises(ValueError):
            hand_transform(np.zeros(19, np.float32))
        landmarks[0, 0] = np.nan
        with self.assertRaises(ValueError):
            decode_hand(outputs, np.eye(2, 3))


class AdapterTests(unittest.TestCase):
    def test_no_face_or_multiple_faces_reset_gesture_progress(self):
        detector = Detector.__new__(Detector)
        detector.face, detector.recognizer = Mock(), Mock()
        frame = np.zeros((240, 320, 3), np.uint8)
        for faces, count in ((None, 0), (np.zeros((2, 15)), 2)):
            detector.progress = .8
            detector.face.detect.return_value = (None, faces)
            self.assertEqual(detector.detect(frame, 10), (False, count))
            self.assertEqual(detector.progress, 0)
        self.assertEqual(detector.recognizer.reset.call_count, 2)

    def test_missing_hands_send_empty_current_frame_instead_of_cached_points(self):
        detector = Detector.__new__(Detector)
        detector.face, detector.palm, detector.hand, detector.recognizer = (Mock() for _ in range(4))
        detector.face.detect.return_value = (None, np.array([[60, 60, 120, 120]], np.float32))
        detector.palm.forward.return_value = (np.zeros((1, 2016, 18), np.float32),
                                               np.full((1, 2016, 1), -20, np.float32))
        detector.recognizer.update.return_value = Mock(matched=False, progress=0, hint='Mostre a mão.')
        detector.detect(np.zeros((240, 320, 3), np.uint8), 10)
        self.assertEqual(detector.recognizer.update.call_args.args[0], [])
        detector.hand.forward.assert_not_called()

    def test_segmentation_preserves_frame_and_foreground_channel(self):
        segmenter = Segmenter.__new__(Segmenter)
        segmenter.net = Mock()
        segmenter.net.forward.return_value = np.stack([np.full((192, 192), .8),
                                                       np.full((192, 192), .2)])[None].astype(np.float32)
        frame = np.zeros((240, 320, 3), np.uint8)
        result = segmenter.capture(frame, 12.5)
        np.testing.assert_allclose(result.mask, .2)
        self.assertEqual(result.mask.shape, (240, 320))
        self.assertFalse(np.shares_memory(result.frame, frame))
        normalized = segmenter.net.setInput.call_args.args[0]
        self.assertEqual(normalized.shape, (1, 3, 192, 192))
        np.testing.assert_allclose(normalized, -1)
        segmenter.net.forward.return_value[0, 1, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            segmenter.capture(frame, 13)

    def test_degenerate_palm_candidate_does_not_disable_recognition(self):
        detector = Detector.__new__(Detector)
        detector.face, detector.palm, detector.hand, detector.recognizer = (Mock() for _ in range(4))
        detector.face.detect.return_value = (None, np.array([[60, 60, 120, 120]], np.float32))
        detector.palm.forward.return_value = (None, None)
        detector.recognizer.update.return_value = Mock(matched=False, progress=0, hint='Mostre a mão.')
        degenerate = np.array([[10, 10, 40, 40, *([20, 20]*7), .8]], np.float32)
        with patch('teleport_cam.vision_opencv.decode_palms', return_value=degenerate):
            self.assertEqual(detector.detect(np.zeros((240, 320, 3), np.uint8), 10), (False, 1))
        self.assertEqual(detector.recognizer.update.call_args.args[0], [])
        detector.hand.forward.assert_not_called()


if __name__ == '__main__':
    unittest.main()
