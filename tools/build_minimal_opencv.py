"""Build reviewed Mac ARM64/Linux wheels in a separate pinned venv. No uploads."""
from pathlib import Path
from importlib import metadata
import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.opencv_profile import native_target, cmake_profile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_cmake_flags(flags, prefix, home):
    return {key: value.replace(prefix, '/usr/src/fora-de-cena').replace(
        home, '/usr/src/fora-de-cena-build-home') for key, value in flags.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args()
    target=native_target()
    if sys.version_info[:2]!=(3,14):
        raise RuntimeError('Use the dedicated native Python 3.14 build venv.')
    if target.startswith('linux') and platform.libc_ver()!=('glibc','2.35'):
        raise RuntimeError('Linux candidates must use the reviewed glibc 2.35 build base.')
    source=args.source.resolve(strict=True)
    if not source.is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Source must stay in project work/.')
    profile_path=ROOT/'packaging/opencv-minimal-profile.json'
    profile=json.loads(profile_path.read_text())
    source_info=profile['source_distribution']
    archive=source.parents[1]/source_info['filename']
    if digest(archive)!=source_info['sha256']:
        raise ValueError('Unverified source distribution')
    subprocess.run(['/usr/bin/git','apply','--reverse','--check',
                    '--directory='+source.relative_to(ROOT).as_posix(),
                    str(ROOT/'packaging/opencv-minimal-source.patch')],cwd=ROOT,check=True)
    # Do not substitute build tools implicitly or resolve a different NumPy ABI.
    versions={}
    for raw in (ROOT/'requirements-opencv-build.txt').read_text().splitlines():
        if not raw.strip() or raw.startswith('#'): continue
        name,version=raw.split('==')
        if metadata.version(name)!=version: raise ValueError('Build tool differs from pin: '+name)
        versions[name]=version
    flags=cmake_profile(profile,target)
    prefix=str(ROOT)
    home=str(Path.home())
    mapped_flags=shlex.join([f'-ffile-prefix-map={prefix}=/usr/src/fora-de-cena',
                            f'-ffile-prefix-map={home}=/usr/src/fora-de-cena-build-home'])
    flags.update(FDC_BUILD_PATH_PREFIX=prefix,FDC_BUILD_HOME_PREFIX=home,
        CMAKE_C_FLAGS=mapped_flags,CMAKE_CXX_FLAGS=mapped_flags)
    work=ROOT/'work/opencv-minimal'
    wheels=work/'wheels'
    wheels.mkdir(exist_ok=True)
    if list(wheels.glob('*.whl')):
        raise RuntimeError('Wheel directory must be empty; never reuse a wheel from another configuration.')
    environment=dict(os.environ)
    environment.update(profile['package_environment'])
    environment.update(CMAKE_ARGS=shlex.join(f'-D{k}={v}' for k,v in sorted(flags.items())),
        CMAKE_GENERATOR='Ninja',CMAKE_BUILD_PARALLEL_LEVEL='4',
        OPENCV_PYTHON_SKIP_GIT_COMMANDS='1',
        PATH=str(Path(sys.executable).parent)+':/usr/bin:/bin:/usr/sbin:/sbin',
        TMPDIR=str(ROOT/'work/test-temp'),PIP_DISABLE_PIP_VERSION_CHECK='1')
    if target=='macos-arm64':
        environment['MACOSX_DEPLOYMENT_TARGET']='15.0'
    else:
        environment.pop('MACOSX_DEPLOYMENT_TARGET',None)
    subprocess.run([sys.executable,'-m','pip','wheel','--no-build-isolation','--no-deps',
                    '--no-cache-dir','--wheel-dir',str(wheels),str(source)],
                   cwd=ROOT,env=environment,check=True)
    built=list(wheels.glob('*.whl'))
    if len(built)!=1: raise RuntimeError('Expected exactly one custom wheel')
    with zipfile.ZipFile(built[0]) as archive:
        native=[n for n in archive.namelist() if n.endswith(('.so','.dylib'))]
        if not native: raise RuntimeError('Missing native OpenCV bindings')
        private_prefixes=(b'/Users/',prefix.encode(),home.encode())
        if any(any(value in archive.read(n) for value in private_prefixes) for n in native):
            raise RuntimeError('Private build paths embedded in native wheel')
    downloaded=source/'opencv/.cache/kleidicv/b85a745bfe0e87e67e30be9533eb6b24-kleidicv-26.03.tar.gz'
    if target=='macos-arm64' and digest(downloaded)!='1bb4078fd215565f3906c33f76a00e7b843328965230d765afcd0d51141c434f':
        raise ValueError('KleidiCV download differs from reviewed source')
    record={'profile_id':profile['profile_id'] if target=='macos-arm64' else 'fdc-minimal-'+target+'-v1',
            'native_target':target,'custom_build':True,'distribution_ready':False,
            'source':source_info,'source_patch_sha256':digest(ROOT/'packaging/opencv-minimal-source.patch'),
            'profile_sha256':digest(profile_path),'build_tools':versions,
            'cmake':public_cmake_flags(flags,prefix,home),
            'wheel':{'filename':built[0].name,'sha256':digest(built[0]),'size':built[0].stat().st_size},
            'build_driver_sha256':digest(Path(__file__)),
            'downloaded_components':([{'component':'KleidiCV','version':'26.03',
                'url':'https://gitlab.arm.com/kleidi/kleidicv/-/archive/26.03/kleidicv-26.03.tar.gz',
                'sha256':digest(downloaded)}] if target=='macos-arm64' else []),
            'private_build_paths_remapped':True,'raw_logs_included':False}
    (work/'provenance.json').write_text(json.dumps(record,indent=2))
    print('Custom wheel:',built[0].name,'SHA256:',record['wheel']['sha256'])


if __name__=='__main__': main()
