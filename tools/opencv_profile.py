"""Select explicit native OpenCV recipes; no host-dependent cross-compilation."""
import platform
import sys


def native_target(system=None, machine=None):
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if system == 'darwin' and machine == 'arm64':
        return 'macos-arm64'
    if system.startswith('linux') and machine in ('x86_64', 'aarch64', 'arm64'):
        return 'linux-x86_64' if machine == 'x86_64' else 'linux-arm64'
    raise RuntimeError('Minimal OpenCV requires a native Mac ARM64 or Linux x64/ARM64 build.')


def cmake_profile(profile, target):
    if target == 'macos-arm64':
        return {**profile['cmake_common_candidate'],
                **profile['cmake_platform_candidates']['darwin'], **profile['cmake_additions']}
    if target not in ('linux-x86_64', 'linux-arm64'):
        raise ValueError('Unsupported minimal OpenCV target')
    additions = {key: value for key, value in profile['cmake_additions'].items()
                 if not key.startswith('CMAKE_OSX_')}
    return {**profile['cmake_common_candidate'], **additions,
            **profile['cmake_platform_candidates']['linux'], **profile['cmake_linux_additions']}
