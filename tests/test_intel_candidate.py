import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from teleport_cam import __version__
from tools.stage_intel_candidate import stage, validate_reports


class IntelCandidateTests(unittest.TestCase):
    def reports(self):
        return {
            'candidate.json': {'target': 'macos-x86_64', 'version': __version__,
                'vision_backend': 'opencv-dnn', 'runtime_signature': 'fixture',
                'minimum_target': 'macOS 15.0', 'distribution_ready': False,
                'validation': {'ad_hoc_signature_verified': True, 'dependency_network_verified': False}},
            'native-self-test.json': {'ok': True, 'frozen': True, 'version': __version__,
                'runtime_signature': 'fixture', 'vision_backend': 'opencv-dnn',
                'camera_opened': False, 'dependency_network_verified': False},
            'native-gui-self-test.json': {'ok': True, 'frozen': True, 'version': __version__,
                'guide_images_rendered': 7, 'camera_opened': False, 'meet_bridge_opened': False},
            'macos-bundle-audit.json': {'architecture': 'x86_64', 'binaries': [{'path': 'Contents/MacOS/ForaDeCena'}]},
        }

    def write_reports(self, folder, reports):
        for name, report in reports.items():
            (folder / name).write_text(json.dumps(report), encoding='utf-8')

    def test_stage_requires_all_frozen_model_gui_architecture_and_signature_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            reports = self.reports()
            with patch('tools.stage_intel_candidate.runtime_signature', return_value='fixture'):
                self.write_reports(folder, reports)
                self.assertFalse(validate_reports(folder)['distribution_ready'])
                for file, key, value in (
                    ('candidate.json', 'distribution_ready', True),
                    ('candidate.json', 'runtime_signature', 'old'),
                    ('native-self-test.json', 'vision_backend', 'mediapipe'),
                    ('native-self-test.json', 'frozen', False),
                    ('native-self-test.json', 'camera_opened', True),
                    ('native-gui-self-test.json', 'guide_images_rendered', 0),
                    ('native-gui-self-test.json', 'meet_bridge_opened', True),
                    ('macos-bundle-audit.json', 'architecture', 'arm64'),
                ):
                    with self.subTest(file=file, key=key):
                        changed = copy.deepcopy(reports)
                        changed[file][key] = value
                        self.write_reports(folder, changed)
                        with self.assertRaises(ValueError):
                            validate_reports(folder)

    def test_staging_uses_allowlist_and_does_not_copy_raw_logs_or_private_report_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'dist/native/mac-test'
            folder.mkdir(parents=True)
            reports = self.reports()
            reports['candidate.json']['private_fixture'] = 'do-not-copy-this-value'
            self.write_reports(folder, reports)
            names = [f'ForaDeCena-{__version__}-macos-x86_64-experimental.dmg',
                     f'ForaDeCena-{__version__}-Fontes-Saida.zip', f'ForaDeCena-{__version__}-Licencas.zip',
                     'startup-error.log', 'candidate.json', 'native-self-test.json']
            for name in names[:4]:
                (folder / name).write_bytes(b'fixture')
            selected = [folder / name for name in names]
            with patch('tools.stage_intel_candidate.candidate_files', return_value=selected), \
                    patch('tools.stage_intel_candidate.runtime_signature', return_value='fixture'):
                destination = stage(root)
                self.assertEqual(len(list(destination.iterdir())), 6)
                self.assertFalse((destination / 'startup-error.log').exists())
                public = (destination / 'VALIDACAO.json').read_text(encoding='utf-8')
                self.assertNotIn('do-not-copy-this-value', public)
                self.assertEqual(len((destination / 'SHA256SUMS.txt').read_text().splitlines()), 5)
                with self.assertRaises(ValueError):
                    stage(root)


if __name__ == '__main__':
    unittest.main()
