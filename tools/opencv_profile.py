"""Select explicit native OpenCV recipes; no host-dependent cross-compilation."""
import platform
import sys


def native_target(system=None, machine=None):
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if system == 'darwin' and machine == 'arm64':
        return 'macos-arm64'
    if system == 'darwin' and machine == 'x86_64':
        return 'macos-x86_64'
    if system.startswith('linux') and machine in ('x86_64', 'aarch64', 'arm64'):
        return 'linux-x86_64' if machine == 'x86_64' else 'linux-arm64'
    raise RuntimeError('Minimal OpenCV requires a native Mac or Linux 64-bit build.')


def cmake_profile(profile, target):
    if target == 'macos-arm64':
        return {**profile['cmake_common_candidate'],
                **profile['cmake_platform_candidates']['darwin'], **profile['cmake_additions']}
    if target == 'macos-x86_64':
        return {**profile['cmake_common_candidate'],
                **profile['cmake_platform_candidates']['darwin'], **profile['cmake_additions'],
                'CMAKE_OSX_ARCHITECTURES': 'x86_64',
                'BUILD_LIST': 'core,imgproc,imgcodecs,videoio,python3,dnn,objdetect',
                'WITH_PROTOBUF': 'ON', 'BUILD_PROTOBUF': 'ON', 'PROTOBUF_UPDATE_FILES': 'OFF',
                'WITH_IPP': 'OFF', 'WITH_KLEIDICV': 'OFF'}
    if target not in ('linux-x86_64', 'linux-arm64'):
        raise ValueError('Unsupported minimal OpenCV target')
    additions = {key: value for key, value in profile['cmake_additions'].items()
                 if not key.startswith('CMAKE_OSX_')}
    return {**profile['cmake_common_candidate'], **additions,
            **profile['cmake_platform_candidates']['linux'], **profile['cmake_linux_additions']}
