from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import sys
import unittest
from unittest.mock import patch

from packaging.utils import parse_wheel_filename
from tools.check_platform_wheels import supported_tags, target_environment
from tools.ci_native import build, summarize, public_error
from tools.prepare_minimal_opencv import extract_verified


class NativeCITests(unittest.TestCase):
    def test_ci_failure_messages_hide_home_paths_and_credential_values(self):
        with patch('tools.ci_native.Path.home', return_value=Path('/fixture-home')):
            text = public_error('/fixture-home/private/library.so; password=fixture-value token=fixture-token github_pat_example')
        for value in ('/fixture-home', 'fixture-value', 'fixture-token', 'github_pat_example'):
            self.assertNotIn(value, text)
        self.assertIn('library.so', text)

    def test_windows_ci_builds_both_portable_and_installer_without_installing_tools(self):
        with patch.object(sys, 'platform', 'win32'), patch.object(sys, 'version', '3.14.7 (fixture)'), \
                patch('tools.ci_native.shutil.which', return_value='ISCC.exe'), \
                patch.object(Path, 'is_file', return_value=True), patch('tools.ci_native.subprocess.run') as run:
            build()
        self.assertEqual(len(run.call_args_list), 2)
        self.assertIn('--single-file', run.call_args_list[0].args[0])
        self.assertIn('--iscc', run.call_args_list[1].args[0])

    def test_cross_platform_markers_and_native_architecture_do_not_leak_from_host(self):
        self.assertEqual(target_environment('windows-x64')['os_name'], 'nt')
        self.assertEqual(target_environment('macos-x86_64')['platform_machine'], 'x86_64')
        self.assertEqual(target_environment('linux-arm64')['platform_machine'], 'aarch64')
        intel = supported_tags('macos-x86_64')
        self.assertFalse(parse_wheel_filename('example-1-py3-none-macosx_11_0_arm64.whl')[3] & intel)
        self.assertTrue(parse_wheel_filename('example-1-cp314-cp314-win_amd64.whl')[3] & supported_tags('windows-x64'))

    def make_archive(self, path: Path, name: str, link: bool = False) -> str:
        with tarfile.open(path, 'w:gz') as output:
            entry = tarfile.TarInfo(name)
            if link:
                entry.type = tarfile.SYMTYPE
                entry.linkname = '/etc/passwd'
                output.addfile(entry)
            else:
                entry.size = 4
                output.addfile(entry, io.BytesIO(b'test'))
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_source_hash_is_required_before_extracting_or_running_build_scripts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'source.tar.gz'
            self.make_archive(archive, 'source/setup.py')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                extract_verified(archive, root / 'extracted', '0' * 64, 'source')
            self.assertFalse((root / 'extracted').exists())

    def test_source_extraction_refuses_traversal_links_and_an_unexpected_root(self):
        for name, link in (('source/../../escaped', False), ('source/link', True), ('other/setup.py', False)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                archive = root / 'source.tar.gz'
                checksum = self.make_archive(archive, name, link)
                with self.assertRaises(ValueError):
                    extract_verified(archive, root / 'extracted', checksum, 'source')
                self.assertFalse((root / 'extracted').exists())

    def test_reviewed_source_extracts_and_cannot_overwrite_an_existing_tree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'source.tar.gz'
            checksum = self.make_archive(archive, 'source/setup.py')
            source = extract_verified(archive, root / 'extracted', checksum, 'source')
            self.assertEqual((source / 'setup.py').read_bytes(), b'test')
            with self.assertRaises(ValueError):
                extract_verified(archive, root / 'extracted', checksum, 'source')

    def test_public_summary_uses_counts_and_fixed_labels_without_dumping_report_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'work').mkdir()
            (root / 'work/wheels.json').write_text(json.dumps({'errors': ['fixture-private-path-or-token']}))
            summary = root / 'summary.md'
            with patch('tools.ci_native.ROOT', root), patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': str(summary)}):
                summarize('macos-x86_64')
            text = summary.read_text(encoding='utf-8')
            self.assertIn('1 dependency compatibility issue', text)
            self.assertIn('No support certification', text)
            self.assertNotIn('fixture-private-path-or-token', text)


if __name__ == '__main__':
    unittest.main()
