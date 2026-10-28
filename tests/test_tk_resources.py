from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import zipfile

from teleport_cam.tk_resources import verify_tk_data


class PackagedTkTests(unittest.TestCase):
    def test_external_scripts_are_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '_tk_data').mkdir()
            (root / '_tk_data/tk.tcl').write_text('# Tk resource')
            self.assertEqual(verify_tk_data(root), 'external-scripts')

    def test_embedded_tk9_scripts_do_not_require_a_fake_external_directory(self):
        for name in ('tcl9tk90.dll', 'libtcl9tk9.0.dylib', 'libtcl9tk9.0.so'):
            with self.subTest(library=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                payload = BytesIO()
                with zipfile.ZipFile(payload, 'w') as archive:
                    archive.writestr('tk_library/tk.tcl', '# Tk resource')
                (root / name).write_bytes(b'fixture native prefix' + payload.getvalue())
                self.assertEqual(verify_tk_data(root), 'embedded-library-zip')
                self.assertFalse((root / '_tk_data').exists())

    def test_framework_scripts_are_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / 'Tk.framework/Versions/9.1/Resources/Scripts/tk.tcl'
            script.parent.mkdir(parents=True)
            script.write_text('# Tk resource')
            self.assertEqual(verify_tk_data(root), 'framework-scripts')

    def test_macos_resources_symlink_is_allowed_only_inside_the_application(self):
        with tempfile.TemporaryDirectory() as folder:
            contents = Path(folder) / 'Example.app/Contents'
            root = contents / 'Frameworks'
            resources = contents / 'Resources/_tk_data'
            root.mkdir(parents=True)
            resources.mkdir(parents=True)
            (resources / 'tk.tcl').write_text('# bundled Tk resource')
            try:
                (root / '_tk_data').symlink_to(resources, target_is_directory=True)
            except OSError:
                self.skipTest('This Windows host restricts symlinks; native Unix CI covers the bundle layout.')
            self.assertEqual(verify_tk_data(root), 'external-scripts')
            (root / '_tk_data').unlink()
            outside = Path(folder) / 'outside'
            outside.mkdir()
            (outside / 'tk.tcl').write_text('# outside bundle')
            (root / '_tk_data').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(FileNotFoundError):
                verify_tk_data(root)

    def test_missing_tk_scripts_or_an_unrelated_zip_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with zipfile.ZipFile(root / 'unrelated.zip', 'w') as archive:
                archive.writestr('tk_library/tk.tcl', '# unrelated')
            with zipfile.ZipFile(root / 'tcl9tk90.dll', 'w') as archive:
                archive.writestr('other-file.txt', '# no Tk resource')
            with self.assertRaises(FileNotFoundError):
                verify_tk_data(root)
