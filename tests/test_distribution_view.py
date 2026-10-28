from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.prepare_distribution import ROOT, VERSION, prepare, repository_files


class DistributionViewTests(unittest.TestCase):
    def test_public_sources_include_runtime_tests_and_build_recipes(self):
        names = {path.relative_to(ROOT).as_posix() for path in repository_files()}
        self.assertTrue({
            'README.md', 'DESENVOLVIMENTO.md', 'DISTRIBUIR.md',
            'teleport_cam/engine.py', 'camera_output/main.py',
            'meet_extension/manifest.json', 'tests/test_meet.py',
            'packaging/fora_de_cena.spec', 'packaging/installer.iss',
            'tools/build_windows.py', 'requirements.lock.txt',
        }.issubset(names))
        for name in names:
            self.assertNotIn(Path(name).name, {
                'PROMPTS_GESTOS.md', 'AUDITORIA.md', 'DESIGN.md', 'PRODUCT.md',
                'PUBLICAR.md', 'user_settings.json', '.meet_pairing_key',
            })
            self.assertFalse(set(Path(name).parts) & {'models', 'work', 'build', '.venv'})
            self.assertNotIn(Path(name).suffix, {'.exe', '.task', '.tflite', '.mp4'})

    def test_missing_source_or_illustration_blocks_preparation(self):
        with patch.object(Path, 'is_file', return_value=False):
            with self.assertRaises(ValueError):
                repository_files()

    def test_unexpected_file_in_review_folder_is_not_silently_published(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.py'
            source.write_text('pass')
            destination = root / 'dist/source-review' / ('v'+VERSION) / 'repository'
            destination.mkdir(parents=True)
            private = destination / 'user_settings.json'
            private.write_text('private fixture')
            with patch('tools.prepare_distribution.repository_files', return_value=[source]):
                with self.assertRaises(ValueError):
                    prepare(root)
            self.assertEqual(private.read_text(), 'private fixture')
