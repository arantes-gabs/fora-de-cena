from __future__ import annotations
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch
import cv2
import numpy as np

from teleport_cam.devices import CameraDevice, capture_backends, list_cameras
from teleport_cam.engine import Engine, Settings
from teleport_cam.hotkey import RestoreHotkey
from teleport_cam.meet import pairing_token
from teleport_cam.paths import data_file, data_root
from teleport_cam.platform_support import output_choices, open_local_path, system_environment
from teleport_cam.virtual_output import VirtualOutput, output_command, output_environment
from tools.build_unix import build, build_plan, checked_directory, create_tarball, inventory, native_target
from tools.build_unix import check_native_license_scope
from tools.check_platform_wheels import check, supported_tags
from packaging.requirements import Requirement
from packaging.utils import parse_wheel_filename


class DesktopAdapterTests(unittest.TestCase):
    def test_devices_keep_their_backend_index_and_path(self):
        for platform_name, backend in (('win32', cv2.CAP_DSHOW), ('darwin', cv2.CAP_AVFOUNDATION), ('linux', cv2.CAP_V4L2)):
            with self.subTest(platform=platform_name), patch.object(sys, 'platform', platform_name), \
                    patch('teleport_cam.devices.enumerate_cameras') as enumerate_devices, \
                    patch('teleport_cam.devices.linux_output_devices', return_value=[]):
                enumerate_devices.return_value = [Mock(index=4, name='USB Camera', path='device-path', backend=backend)]
                # Mock's constructor name is not a device's name attribute.
                enumerate_devices.return_value[0].name = 'USB Camera'
                devices = list_cameras()
                enumerate_devices.assert_called_once_with(backend)
                self.assertEqual(devices, [CameraDevice(4, 'USB Camera', 'device-path', backend)])

    def test_output_only_loopbacks_are_visible_before_streaming_and_not_duplicated(self):
        loopback = CameraDevice(17, 'Fora de Cena', '/dev/video17', cv2.CAP_V4L2)
        with patch.object(sys, 'platform', 'linux'), patch('teleport_cam.devices.enumerate_cameras', return_value=[]), \
                patch('teleport_cam.devices.linux_output_devices', return_value=[loopback]):
            self.assertEqual(list_cameras(), [loopback])
        with patch.object(sys, 'platform', 'linux'), patch('teleport_cam.devices.enumerate_cameras', return_value=[loopback]), \
                patch('teleport_cam.devices.linux_output_devices', return_value=[loopback]):
            self.assertEqual(list_cameras(), [loopback])

    def test_interface_passes_distinct_linux_capture_and_output_devices(self):
        from teleport_cam.app import App
        app = Mock()
        app.engine = None
        app.inputs = []
        camera = CameraDevice(4, 'USB Camera', '/dev/video4', cv2.CAP_V4L2)
        app.devices = [camera]
        app.camera.get.return_value = camera.label
        app.resolution.get.return_value = '1280 × 720'
        app.backend.get.return_value = 'Câmera virtual Linux'
        app.virtual_device.get.return_value = '/dev/video17'
        app.hold.get.return_value = '1.0'
        app.effect.get.return_value = 'Teleporte anime'
        app.dynamic.get.return_value = False
        with patch.object(sys, 'platform', 'linux'), patch('teleport_cam.app.Engine') as factory, \
                patch('teleport_cam.app.save_preferences'):
            App.start(app)
        settings = factory.call_args.args[0]
        self.assertEqual(settings.camera_path, '/dev/video4')
        self.assertEqual(settings.virtual_device, '/dev/video17')
        self.assertEqual(settings.virtual, 'v4l2loopback')
        self.assertFalse(settings.dynamic_background)

    def test_mac_capture_does_not_request_mjpeg_or_use_windows_backends(self):
        engine = Engine.__new__(Engine)
        engine.settings = Settings(camera=3)
        capture = Mock()
        capture.isOpened.return_value = True
        with patch.object(sys, 'platform', 'darwin'), patch('teleport_cam.engine.cv2.VideoCapture', return_value=capture) as factory:
            self.assertIs(engine._open_capture(), capture)
        factory.assert_called_once_with(3, cv2.CAP_AVFOUNDATION)
        self.assertNotIn(cv2.CAP_PROP_FOURCC, [call.args[0] for call in capture.set.call_args_list])

    def test_capture_never_reuses_an_enumerated_index_in_another_backend(self):
        engine = Engine.__new__(Engine)
        engine.settings = Settings(camera=5, camera_backend=cv2.CAP_DSHOW)
        capture = Mock()
        capture.isOpened.return_value = False
        with patch('teleport_cam.engine.cv2.VideoCapture', return_value=capture) as factory:
            with self.assertRaises(RuntimeError):
                engine._open_capture()
        factory.assert_called_once_with(5, cv2.CAP_DSHOW)
        capture.release.assert_called_once()

    def test_linux_capture_uses_explicit_device_and_prevents_video_feedback(self):
        engine = Engine.__new__(Engine)
        engine.settings = Settings(camera=8, camera_path='/dev/video8', virtual='v4l2loopback')
        capture = Mock()
        capture.isOpened.return_value = True
        with patch.object(sys, 'platform', 'linux'), patch('teleport_cam.engine.linux_loopback_device', return_value=False), \
                patch('teleport_cam.engine.cv2.VideoCapture', return_value=capture) as factory:
            engine._open_capture()
        factory.assert_called_once_with('/dev/video8', cv2.CAP_V4L2)
        with patch.object(sys, 'platform', 'linux'), patch('teleport_cam.engine.linux_loopback_device', return_value=True), \
                patch('teleport_cam.engine.cv2.VideoCapture') as factory:
            with self.assertRaises(ValueError):
                engine._open_capture()
            factory.assert_not_called()

    def test_unix_hotkey_falls_back_without_a_windows_thread(self):
        for system in ('darwin', 'linux'):
            with self.subTest(system=system), patch.object(sys, 'platform', system), patch('teleport_cam.hotkey.Thread') as thread:
                shortcut = RestoreHotkey()
                shortcut.close()
                thread.assert_not_called()
                self.assertTrue(shortcut.ready.is_set())
                self.assertFalse(shortcut.registered)

    def test_backend_choices_do_not_offer_windows_drivers_on_unix(self):
        with patch.object(sys, 'platform', 'linux'):
            self.assertEqual(set(output_choices().values()), {'off', 'v4l2loopback'})
        with patch.object(sys, 'platform', 'darwin'):
            self.assertEqual(set(output_choices().values()), {'off', 'obs'})

    def test_frozen_auxiliary_has_a_platform_specific_filename(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, '_MEIPASS', folder, create=True):
            for system, suffix in (('win32', '.exe'), ('darwin', ''), ('linux', '')):
                with self.subTest(system=system), patch.object(sys, 'platform', system):
                    self.assertEqual(output_command(), [str(Path(folder) / 'video_output' / ('ForaDeCenaVideoOutput' + suffix))])

    def test_private_user_data_is_outside_the_bundle_on_unix(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(sys, 'frozen', True, create=True), \
                patch('pathlib.Path.home', return_value=Path(folder)):
            base = Path(folder)
            with patch.object(sys, 'platform', 'darwin'):
                self.assertEqual(data_root(), base / 'Library/Application Support/ForaDeCena')
            with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_DATA_HOME': str(base / 'data')}):
                self.assertEqual(data_root(), base / 'data/fora-de-cena')
            with patch.object(sys, 'platform', 'linux'), patch.dict(os.environ, {'XDG_DATA_HOME': 'invalid-relative'}):
                self.assertEqual(data_root(), base / '.local/share/fora-de-cena')
                file = data_file('test.txt')
                self.assertTrue(file.parent.is_dir())
                if os.name != 'nt':
                    self.assertEqual(stat.S_IMODE(file.parent.stat().st_mode), 0o700)

    def test_system_opener_gets_an_absolute_argument_and_clean_loader_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(sys, 'platform', 'darwin'), patch('teleport_cam.platform_support.subprocess.Popen') as launch, \
                    patch.object(Path, 'is_file', return_value=True), \
                    patch.dict(os.environ, {'LD_LIBRARY_PATH': '/bundle', 'LD_LIBRARY_PATH_ORIG': '/system',
                                           'PYTHONPATH': 'injected', 'DYLD_INSERT_LIBRARIES': 'injected'}, clear=True):
                open_local_path(Path(folder))
                self.assertEqual(launch.call_args.args[0], [str(Path('/usr/bin/open')), str(Path(folder).resolve())])
                environment = launch.call_args.kwargs['env']
                self.assertEqual(environment['LD_LIBRARY_PATH'], '/system')
                self.assertNotIn('PYTHONPATH', environment)
                self.assertNotIn('DYLD_INSERT_LIBRARIES', environment)
                self.assertNotIn('shell', launch.call_args.kwargs)
                self.assertEqual(os.environ['LD_LIBRARY_PATH'], '/bundle')

    def test_meet_key_is_persistent_and_private_on_posix(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'pairing'
            first = pairing_token(path)
            self.assertEqual(pairing_token(path), first)
            if os.name != 'nt':
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_output_helper_receives_no_unrelated_environment_credentials(self):
        with patch.dict(os.environ, {'AWS_SECRET_ACCESS_KEY': 'fixture-not-a-real-key',
                                    'GITHUB_TOKEN': 'fixture-not-a-real-token', 'PYTHONPATH': 'injected'}, clear=False):
            environment = output_environment()
            self.assertNotIn('AWS_SECRET_ACCESS_KEY', environment)
            self.assertNotIn('GITHUB_TOKEN', environment)
            self.assertNotIn('PYTHONPATH', environment)
            self.assertEqual(environment['PYINSTALLER_RESET_ENVIRONMENT'], '1')

    def test_main_report_creates_its_parent_without_starting_the_application(self):
        from teleport_cam.launcher import main
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / 'nested/report.json'
            with patch.object(sys, 'argv', ['main.py', '--self-test', '--report', str(report)]), \
                    patch('teleport_cam.launcher.self_test', return_value={'ok': True}):
                self.assertEqual(main(), 0)
            self.assertTrue(json.loads(report.read_text())['ok'])

    def test_linux_output_stream_preserves_frames_with_explicit_device_in_dry_run(self):
        output = VirtualOutput(16, 16, 30, 'v4l2loopback', device='/dev/video17', dry_run=True)
        try:
            frame = np.zeros((16, 16, 3), dtype=np.uint8)
            output.send(frame)
            self.assertEqual(output.index, 1)
        finally:
            output.close()
        self.assertIsNotNone(output.process.poll())

    def test_invalid_output_paths_and_foreign_backends_fail_before_spawning(self):
        with patch('teleport_cam.virtual_output.subprocess.Popen') as launch:
            for device in ('/dev/video0/../etc/passwd', '/dev/video0;id', 'https://example.com', '/tmp/video0'):
                with self.subTest(device=device), self.assertRaises(ValueError):
                    VirtualOutput(16, 16, 30, 'v4l2loopback', device=device, dry_run=True)
            with patch.object(sys, 'platform', 'darwin'), self.assertRaises(ValueError):
                VirtualOutput(16, 16, 30, 'unitycapture')
            launch.assert_not_called()


class NativePackageTests(unittest.TestCase):
    def test_wheel_validation_rejects_a_newer_glibc_and_foreign_mac_architecture(self):
        self.assertFalse(parse_wheel_filename('example-1.0-py3-none-manylinux_2_36_x86_64.whl')[3] & supported_tags('linux-x86_64'))
        self.assertFalse(parse_wheel_filename('example-1.0-py3-none-macosx_13_0_x86_64.whl')[3] & supported_tags('macos-arm64'))

    def test_dependency_check_reports_an_unpinned_transitive_requirement(self):
        package = {'info': {'version': '1.0', 'requires_dist': ['missing>=2'], 'requires_python': '>=3.10'},
                   'urls': [{'filename': 'example-1.0-py3-none-any.whl', 'packagetype': 'bdist_wheel'}]}
        with patch('tools.check_platform_wheels.pinned_requirements', return_value={'example': Requirement('example==1.0')}), \
                patch('tools.check_platform_wheels.fetch_metadata', return_value=('example', package)):
            report = check('macos-arm64')
        self.assertFalse(report['ok'])
        self.assertIn('dependency not pinned', report['errors'][0])

    def test_native_targets_and_intel_require_explicit_custom_mediapipe(self):
        self.assertEqual(native_target('darwin', 'arm64'), 'macos-arm64')
        self.assertEqual(native_target('darwin', 'x86_64'), 'macos-x86_64')
        self.assertEqual(native_target('linux', 'x86_64'), 'linux-x86_64')
        with self.assertRaises(RuntimeError):
            native_target('win32', 'AMD64')
        with patch('tools.build_unix.native_target', return_value='macos-x86_64'), \
                self.assertRaisesRegex(ValueError, 'explicitly built/validated'):
            build()
        self.assertFalse(build_plan('macos-arm64')['distribution_ready'])
        self.assertTrue(build_plan('macos-x86_64')['custom_mediapipe_required'])

    def test_archives_do_not_include_the_build_user_name_and_keep_executable_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            payload = base / 'payload'
            payload.mkdir()
            executable = payload / 'ForaDeCena'
            executable.write_bytes(b'fake executable')
            executable.chmod(0o755)
            archive = base / 'candidate.tar.gz'
            create_tarball(payload, archive)
            with tarfile.open(archive) as package:
                for entry in package.getmembers():
                    self.assertEqual((entry.uid, entry.gid, entry.uname, entry.gname), (0, 0, '', ''))
                    self.assertFalse(entry.name.startswith('/'))
                if os.name != 'nt':
                    self.assertEqual(package.getmember('ForaDeCena/ForaDeCena').mode & 0o111, 0o111)

    def test_private_files_block_native_packaging(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = Path(folder)
            for name in ('.meet_pairing_key', '.env.local', 'certificate.p12', 'private.pem'):
                with self.subTest(name=name):
                    path = payload / name
                    path.write_bytes(b'-----BEGIN PRIVATE KEY-----')
                    with self.assertRaises(ValueError):
                        inventory(payload)
                    path.unlink()

    def test_unused_codec_gui_and_fortran_binaries_block_instead_of_being_deleted(self):
        for name in ('libavcodec.so.62', 'libQt5Core.so.5', 'libquadmath-abc.so.0', 'libreadline.so.8'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError,'reviewed candidate profile'):
                check_native_license_scope([Path(name)])
        check_native_license_scope([Path('cv2.abi3.so'),Path('libmediapipe.dylib'),Path('libstdc++.so.6')])

    def test_symlinks_must_stay_inside_the_bundle_and_survive_tar_archiving(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            payload = base / 'payload'
            payload.mkdir()
            (payload / 'library.so.1').write_bytes(b'library')
            link = payload / 'library.so'
            try:
                link.symlink_to('library.so.1')
            except OSError:
                self.skipTest('This host does not permit unprivileged symlinks; native Unix CI covers this case.')
            archive = base / 'candidate.tar.gz'
            create_tarball(payload, archive)
            with tarfile.open(archive) as package:
                self.assertTrue(package.getmember('ForaDeCena/library.so').issym())
            link.unlink()
            link.symlink_to(base / 'outside')
            with self.assertRaises(ValueError):
                inventory(payload)

    def test_redirected_build_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('tools.build_unix.ROOT', root / 'project'):
                with self.assertRaises(ValueError):
                    checked_directory(root / 'outside/build', root / 'outside')


if __name__ == '__main__':
    unittest.main()
