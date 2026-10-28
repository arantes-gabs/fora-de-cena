"""Linux CI NumPy without external BLAS/Fortran; original version, no uploads.

Uses the reviewed source's blas/lapack/allow-noblas Meson options:
https://numpy.org/doc/stable/building/blas_lapack.html
"""
from __future__ import annotations

import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {'filename': 'numpy-2.5.4.tar.gz',
          'url': 'https://files.pythonhosted.org/packages/95/b0/c7453d0b6e2073c3264468b106ee1563750cecc910965e67357e3698c83e/numpy-2.5.4.tar.gz',
          'sha256': '9a94cf751c9ad8ebaa835bcd3d40dacf8534ad086b88c38029b65123c7999d2a'}
FORBIDDEN = ('openblas', 'gfortran', 'quadmath', 'libblas', 'liblapack')
SETTINGS = ('-Dblas=none', '-Dlapack=none', '-Dallow-noblas=true', '-Dbuildtype=release')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_artifact(wheel, provenance):
    record = json.loads(provenance.read_text(encoding='utf-8'))
    if (not record.get('custom_build') or record.get('source') != SOURCE or record.get('settings') != list(SETTINGS)
            or record.get('build_driver_sha256') != digest(Path(__file__))
            or record.get('build_requirements_sha256') != digest(ROOT/'requirements-numpy-build.txt')
            or record.get('wheel_sha256') != digest(wheel) or record.get('wheel_filename') != wheel.name
            or record.get('architecture') != platform.machine()
            or record.get('distribution_ready') is not False):
        raise ValueError('NumPy artifact differs from the reviewed native recipe.')
    distribution = metadata.distribution('numpy')
    direct = json.loads(distribution.read_text('direct_url.json') or '{}')
    if (distribution.version != '2.5.4' or
            direct.get('archive_info', {}).get('hashes', {}).get('sha256') != digest(wheel)):
        raise ValueError('Install the explicitly selected NumPy wheel before packaging.')
    with zipfile.ZipFile(wheel) as archive:
        natives = [name for name in archive.namelist() if name.endswith('.so')]
        if not natives:
            raise ValueError('NumPy wheel has no native extensions.')
        for name in natives:
            installed=Path(distribution.locate_file(name))
            if (not name.startswith('numpy/') or '..' in Path(name).parts or
                    not installed.resolve().is_relative_to(Path(distribution.locate_file('')).resolve())):
                raise ValueError('Unsafe NumPy native member.')
            if hashlib.sha256(archive.read(name)).hexdigest() != digest(installed):
                raise ValueError('Installed native NumPy differs from the selected wheel.')
    return record


def build():
    if (sys.platform != 'linux' or platform.machine() not in ('x86_64', 'aarch64')
            or os.environ.get('GITHUB_ACTIONS') != 'true' or sys.version_info[:2] != (3, 14)
            or platform.libc_ver() != ('glibc', '2.35')):
        raise RuntimeError('Use a clean Linux x64/ARM64 CI runner with Python 3.14 and glibc 2.35.')
    work = ROOT/'work/numpy-minimal'
    if work.exists() or not work.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Use a new, non-redirected NumPy work directory.')
    work.mkdir(parents=True)
    # The build interpreter/source stay in a private temporary runner directory,
    # avoiding personal profile or project paths in NumPy's generated config.
    with tempfile.TemporaryDirectory(prefix='fdc-numpy-', dir='/tmp') as folder:
        stage = Path(folder)
        home = stage/'home'; home.mkdir()
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'TMPDIR': str(stage),
               'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'PYTHONUTF8': '1',
               'LD_LIBRARY_PATH': str(Path(sys.base_prefix)/'lib'),
               'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'CC': '/usr/bin/gcc', 'CXX': '/usr/bin/g++',
               'CFLAGS': '-O2 -ffile-prefix-map='+str(stage)+'=/usr/src/numpy',
               'CXXFLAGS': '-O2 -ffile-prefix-map='+str(stage)+'=/usr/src/numpy'}
        venv = stage/'env'
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], env=env, check=True)
        python = venv/'bin/python'
        env['PATH'] = str(venv/'bin')+':/usr/bin:/bin'
        subprocess.run([str(python), '-m', 'pip', 'install', '--only-binary=:all:',
                        '-r', str(ROOT/'requirements-numpy-build.txt')], env=env, check=True)
        source_archive = stage/SOURCE['filename']
        with urllib.request.urlopen(SOURCE['url'], timeout=60) as response, source_archive.open('xb') as output:
            if not response.url.startswith('https://files.pythonhosted.org/'):
                raise ValueError('Unexpected source redirect.')
            count = 0
            while data := response.read(1024*1024):
                count += len(data)
                if count > 100*1024*1024:
                    raise ValueError('NumPy source exceeds download limit.')
                output.write(data)
        sys.path.insert(0, str(ROOT))
        from tools.prepare_minimal_opencv import extract_verified
        source = extract_verified(source_archive, stage/'source', SOURCE['sha256'], 'numpy-2.5.4')
        wheels = work/'wheels'; wheels.mkdir()
        command = [str(python), '-m', 'pip', 'wheel', '--no-build-isolation', '--no-deps',
                   '--no-cache-dir', '--wheel-dir', str(wheels), str(source)]
        command += ['-Csetup-args='+option for option in SETTINGS]
        command += ['-Ccompile-args=-j4']
        subprocess.run(command, cwd=stage, env=env, check=True, timeout=1800)
        built = list(wheels.glob('*.whl'))
        if len(built) != 1:
            raise ValueError('Expected one custom NumPy wheel.')
        with zipfile.ZipFile(built[0]) as archive:
            natives = [n for n in archive.namelist() if n.endswith('.so')]
            if not natives:
                raise ValueError('Missing NumPy native extensions.')
            for index, name in enumerate(natives):
                native = stage/('library-'+str(index)+'.so')
                data = archive.read(name)
                if str(ROOT).encode() in data or str(Path.home()).encode() in data:
                    raise ValueError('Private build paths in native NumPy.')
                native.write_bytes(data)
                needed = subprocess.check_output(['/usr/bin/readelf', '-d', str(native)], env=env, text=True)
                if any(value in needed.lower() for value in FORBIDDEN):
                    raise ValueError('Unexpected external BLAS/Fortran dependency.')
            for name in archive.namelist():
                if name.endswith(('.py', '.pc')):
                    data = archive.read(name)
                    if str(ROOT).encode() in data or str(Path.home()).encode() in data:
                        raise ValueError('Private build paths in generated NumPy configuration.')
        record = {'custom_build': True, 'source': SOURCE, 'settings': list(SETTINGS),
                  'build_driver_sha256': digest(Path(__file__)),
                  'build_requirements_sha256': digest(ROOT/'requirements-numpy-build.txt'),
                  'architecture': platform.machine(), 'wheel_sha256': digest(built[0]),
                  'wheel_filename': built[0].name, 'native_extensions': len(natives),
                  'external_blas_fortran': False, 'distribution_ready': False}
        (work/'provenance.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        print('Custom NumPy wheel verified:', built[0].name)


if __name__ == '__main__':
    build()
