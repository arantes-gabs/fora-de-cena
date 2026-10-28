import importlib
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from teleport_cam.runtime_imports import without_optional_audio


class OptionalAudioTests(unittest.TestCase):
    def test_optional_audio_import_is_refused_and_existing_module_is_restored(self):
        original=ModuleType('sounddevice')
        with patch.dict(sys.modules,{'sounddevice':original}):
            with without_optional_audio(),self.assertRaises(ModuleNotFoundError):
                importlib.import_module('sounddevice')
            self.assertIs(sys.modules['sounddevice'],original)

    def test_failed_vision_initialization_does_not_leave_global_import_state_changed(self):
        previous=sys.modules.pop('sounddevice',None)
        try:
            with self.assertRaises(RuntimeError):
                with without_optional_audio():
                    raise RuntimeError('fixture initialization failure')
            self.assertNotIn('sounddevice',sys.modules)
        finally:
            if previous is not None:
                sys.modules['sounddevice']=previous
