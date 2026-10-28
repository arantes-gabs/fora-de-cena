import json
from pathlib import Path
import platform
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from tools import build_minimal_numpy as recipe


class MinimalNumPyTests(unittest.TestCase):
    def test_build_is_refused_outside_clean_linux_ci_before_downloading(self):
        with patch.dict('os.environ', {}, clear=True), self.assertRaisesRegex(RuntimeError, 'clean Linux'):
            recipe.build()

    def test_identical_package_version_does_not_allow_another_native_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            native=base/'numpy/native.so';native.parent.mkdir();native.write_bytes(b'changed installed file')
            wheel=base/'numpy-selected.whl'
            with zipfile.ZipFile(wheel,'w') as archive:
                archive.writestr('numpy/native.so',b'selected native file')
            record={'custom_build':True,'source':recipe.SOURCE,'settings':list(recipe.SETTINGS),
                    'build_driver_sha256':recipe.digest(Path(recipe.__file__)),
                    'build_requirements_sha256':recipe.digest(recipe.ROOT/'requirements-numpy-build.txt'),
                    'wheel_sha256':recipe.digest(wheel),'wheel_filename':wheel.name,
                    'architecture':platform.machine(),'distribution_ready':False}
            provenance=base/'provenance.json';provenance.write_text(json.dumps(record))
            distribution=SimpleNamespace(version='2.5.4',
                read_text=lambda _:json.dumps({'archive_info':{'hashes':{'sha256':recipe.digest(wheel)}}}),
                locate_file=lambda name:base/name)
            with patch('tools.build_minimal_numpy.metadata.distribution',return_value=distribution), \
                    self.assertRaisesRegex(ValueError,'Installed native NumPy differs'):
                recipe.validate_artifact(wheel,provenance)
