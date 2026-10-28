from pathlib import Path
import unittest

from tools.package_release import ROOT,VERSION,release_files
from teleport_cam import __version__


class SourceReleaseTests(unittest.TestCase):
    def test_release_version_matches_application(self):
        self.assertEqual(VERSION,__version__)

    def test_windows_installer_and_executable_metadata_match_the_candidate(self):
        from teleport_cam import __windows_version__
        numeric=','.join(map(str,__windows_version__))
        info=(ROOT/'packaging/version_info.txt').read_text()
        self.assertIn('filevers=('+numeric+')',info)
        self.assertIn("StringStruct('ProductVersion', '"+__version__+"')",info)
        installer=(ROOT/'packaging/installer.iss').read_text()
        self.assertIn('#define AppVersion "'+__version__+'"',installer)
        self.assertIn('#define AppNumericVersion "'+'.'.join(map(str,__windows_version__))+'"',installer)

    def test_source_release_excludes_private_and_downloaded_files(self):
        paths=release_files()
        names={path.relative_to(ROOT).as_posix() for path in paths}
        self.assertIn('LICENSE',names)
        self.assertIn('teleport_cam/model_assets.py',names)
        self.assertIn('meet_extension/manifest.json',names)
        self.assertIn('requirements.lock.txt',names)
        for name in names:
            self.assertNotIn(name,{'user_settings.json','.meet_pairing_key','PROMPTS_GESTOS.md','AUDITORIA.md','DESIGN.md','PRODUCT.md','PUBLICAR.md'})
            self.assertFalse(any(part in Path(name).parts for part in ('work','.venv','dist','models','.git','.impeccable')))
            self.assertNotIn(Path(name).suffix,{'.jpg','.task','.tflite','.mp4','.exe'})
            if Path(name).suffix=='.png': self.assertTrue(name.startswith(('assets/gestures/','assets/brand/')))

    def test_nested_session_files_are_excluded_from_sources_and_zip(self):
        import shutil
        import tempfile
        import zipfile
        from uuid import uuid4
        from tools.package_release import build
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for source in release_files():
                destination = root / source.relative_to(ROOT)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            session_value, env_value, prompt_value = (uuid4().hex for _ in range(3))
            (root / 'meet_extension' / 'user_settings.json').write_text(session_value)
            (root / 'meet_extension' / '.env.local').write_text(env_value)
            (root / 'PROMPTS_GESTOS.md').write_text(prompt_value)
            archive = build(root)
            with zipfile.ZipFile(archive) as package:
                for name in package.namelist():
                    self.assertNotIn(Path(name).name, {'user_settings.json', '.env.local', 'PROMPTS_GESTOS.md'})
                    for value in (session_value, env_value, prompt_value):
                        self.assertNotIn(value.encode(), package.read(name))
