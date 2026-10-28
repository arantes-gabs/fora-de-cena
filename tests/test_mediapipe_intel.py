from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile

from tools.mediapipe_intel import digest, load_profile, make_wheel, validate_artifact


class IntelWheelTests(unittest.TestCase):
    def test_native_compile_has_a_finite_budget_and_preserves_build_failures(self):
        from tools.build_mediapipe_intel import compile_native
        source=Path('fixture-source')
        environment={'HOME':'fixture-isolated-home'}
        with patch('tools.build_mediapipe_intel.subprocess.run') as run:
            compile_native(['fixture-bazel','build'],source,environment)
        run.assert_called_once_with(['fixture-bazel','build'],cwd=source,env=environment,
                                    check=True,timeout=9000)
        with patch('tools.build_mediapipe_intel.subprocess.run',
                   side_effect=subprocess.CalledProcessError(1,['fixture-bazel'])), \
                self.assertRaises(subprocess.CalledProcessError):
            compile_native(['fixture-bazel'],source,environment)

    def test_native_timeout_does_not_echo_command_paths_or_environment(self):
        from tools.build_mediapipe_intel import compile_native
        with patch('tools.build_mediapipe_intel.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(['fixture-private-path'],9000)), \
                self.assertRaises(RuntimeError) as error:
            compile_native(['fixture-private-path'],Path('fixture'),{'HOME':'fixture-private-home'})
        self.assertIn('150 minutes',str(error.exception))
        self.assertNotIn('fixture',str(error.exception))
        self.assertTrue(error.exception.__suppress_context__)

    def test_build_plan_can_be_reviewed_on_windows_without_executing_or_downloading(self):
        from tools.build_mediapipe_intel import main
        with patch.object(sys, 'argv', ['build_mediapipe_intel.py', '--plan']), \
                patch.object(sys, 'platform', 'win32'), patch('tools.build_mediapipe_intel.download') as download, \
                patch('tools.build_mediapipe_intel.subprocess.run') as run, patch('builtins.print') as output:
            main()
        download.assert_not_called()
        run.assert_not_called()
        self.assertFalse(json.loads(output.call_args.args[0])['distribution_ready'])

    def template(self, root: Path, extra_native: bool = False) -> tuple[Path, Path, dict]:
        profile = load_profile()
        template = root / 'upstream.whl'
        native = root / 'intel.dylib'
        native.write_bytes(b'fixture compiled Intel library')
        info = 'mediapipe-1.1.1.dist-info/'
        with zipfile.ZipFile(template, 'w') as output:
            output.writestr(profile['native_member'], b'fixture original ARM library')
            output.writestr('mediapipe/__init__.py', '# upstream Python, unchanged\n')
            output.writestr(info + 'METADATA', 'Name: mediapipe\nVersion: 1.1.1\n')
            output.writestr(info + 'LICENSE', 'upstream license notice, unchanged')
            output.writestr(info + 'WHEEL', 'Tag: py3-none-macosx_11_0_arm64\n')
            output.writestr(info + 'RECORD', 'old hashes')
            if extra_native:
                output.writestr('mediapipe/unexpected-arm.so', b'another ARM binary')
        profile['python_template']['sha256'] = digest(template)
        return template, native, profile

    def test_python_and_license_preserved_native_replaced_and_record_verifies_every_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template, native, profile = self.template(root)
            with patch('tools.macos_bundle.inspect_macho', return_value={'minimum': (15, 0, 0)}):
                wheel = make_wheel(template, native, root / 'wheels', profile)
            with zipfile.ZipFile(wheel) as output:
                self.assertEqual(output.read(profile['native_member']), native.read_bytes())
                self.assertEqual(output.read('mediapipe/__init__.py'), b'# upstream Python, unchanged\n')
                self.assertEqual(output.read('mediapipe-1.1.1.dist-info/LICENSE'), b'upstream license notice, unchanged')
                self.assertIn(b'x86_64', output.read('mediapipe-1.1.1.dist-info/WHEEL'))
                rows = list(csv.reader(io.StringIO(output.read('mediapipe-1.1.1.dist-info/RECORD').decode())))
                self.assertEqual(len(rows), len(output.namelist()))
                for name, checksum, size in rows:
                    if not checksum:
                        self.assertTrue(name.endswith('/RECORD'))
                        continue
                    content = output.read(name)
                    expected = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b'=').decode()
                    self.assertEqual(checksum, 'sha256=' + expected)
                    self.assertEqual(int(size), len(content))

    def test_unverified_template_fails_before_reading_native_code(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template, native, profile = self.template(root)
            template.write_bytes(b'tampered upstream download')
            with patch('tools.macos_bundle.inspect_macho') as inspect:
                with self.assertRaisesRegex(ValueError, 'Unverified'):
                    make_wheel(template, native, root / 'wheels', profile)
                inspect.assert_not_called()

    def test_an_arm_binary_cannot_be_relabelled_as_an_intel_wheel(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template, native, profile = self.template(root)
            with patch('tools.macos_bundle.inspect_macho', side_effect=ValueError('Mach-O sem X86_64')) as inspect:
                with self.assertRaisesRegex(ValueError, 'X86_64'):
                    make_wheel(template, native, root / 'wheels', profile)
                inspect.assert_called_once_with(native, 'x86_64')
            self.assertFalse((root / 'wheels').exists())

    def test_extra_arm_libraries_and_a_false_macos_minimum_block_wheel_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            template, native, profile = self.template(root, extra_native=True)
            with patch('tools.macos_bundle.inspect_macho', return_value={'minimum': (15, 0, 0)}):
                with self.assertRaisesRegex(ValueError, 'Unexpected native'):
                    make_wheel(template, native, root / 'wheels', profile)
            with patch('tools.macos_bundle.inspect_macho', return_value={'minimum': (16, 0, 0)}):
                with self.assertRaisesRegex(ValueError, 'newer macOS'):
                    make_wheel(template, native, root / 'wheels', profile)

    def test_source_recipe_provenance_cannot_be_replaced_with_arbitrary_wheel_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wheel = root / 'unverified.whl'
            wheel.write_bytes(b'unverified')
            provenance = root / 'provenance.json'
            provenance.write_text(json.dumps({'custom_build': True, 'distribution_ready': False,
                                               'architecture': 'x86_64', 'source_commit': 'unreviewed'}))
            with patch('tools.mediapipe_intel.metadata.distribution') as installed:
                with self.assertRaisesRegex(ValueError, 'provenance differs'):
                    validate_artifact(wheel, provenance)
                installed.assert_not_called()


if __name__ == '__main__':
    unittest.main()
