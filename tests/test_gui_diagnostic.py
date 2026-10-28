import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from teleport_cam import __version__
from tools.build_unix import run_gui_diagnostic


class GuiDiagnosticTests(unittest.TestCase):
    def report(self):
        return {'ok': True, 'frozen': True, 'version': __version__, 'guide_images_rendered': 7,
                'camera_opened': False, 'meet_bridge_opened': False}

    def run_report(self, report, returncode=0, system='linux'):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            def execute(command, **kwargs):
                if system == 'linux':
                    self.assertEqual(command[0], '/usr/bin/xvfb-run')
                else:
                    self.assertEqual(command[0], str(folder / 'ForaDeCena'))
                self.assertIn('--gui-self-test', command)
                self.assertNotIn('GH_TOKEN', kwargs['env'])
                Path(command[-1]).write_text(json.dumps(report), encoding='utf-8')
                return Mock(returncode=returncode)
            with patch('tools.build_unix.sys.platform', system), \
                    patch('tools.build_unix.system_environment', return_value={}), \
                    patch('tools.build_unix.subprocess.run', side_effect=execute):
                return run_gui_diagnostic(folder / 'ForaDeCena', folder)

    def test_frozen_image_rendering_is_required(self):
        self.assertTrue(self.run_report(self.report())['ok'])
        invalid = [
            {**self.report(), 'ok': False, 'error': 'ModuleNotFoundError',
             'detail': "No module named 'PIL._tkinter_finder'"},
            {**self.report(), 'guide_images_rendered': 0},
            {**self.report(), 'frozen': False},
            {**self.report(), 'camera_opened': True},
            {**self.report(), 'meet_bridge_opened': True},
        ]
        for report in invalid:
            with self.subTest(report=report), self.assertRaises(RuntimeError):
                self.run_report(report)
        with self.assertRaises(RuntimeError):
            self.run_report(self.report(), returncode=1)

    def test_mac_gui_check_runs_the_executable_without_linux_xvfb(self):
        self.assertTrue(self.run_report(self.report(), system='darwin')['ok'])

    def test_linux_startup_error_is_visible_without_echoing_private_details(self):
        from teleport_cam.launcher import main
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'startup-error.log'
            output = io.StringIO()
            with patch.object(sys, 'argv', ['ForaDeCena']), \
                    patch.object(sys, 'platform', 'linux'), \
                    patch.dict(sys.modules, {'teleport_cam.app': Mock(main=Mock(side_effect=ModuleNotFoundError('fixture-private-detail')))}), \
                    patch('teleport_cam.launcher.data_file', return_value=log), \
                    patch.object(sys, 'stderr', output):
                self.assertEqual(main(), 1)
            self.assertIn('ModuleNotFoundError', output.getvalue())
            self.assertIn('startup-error.log', output.getvalue())
            self.assertNotIn('fixture-private-detail', output.getvalue())
            self.assertIn('fixture-private-detail', log.read_text(encoding='utf-8'))
