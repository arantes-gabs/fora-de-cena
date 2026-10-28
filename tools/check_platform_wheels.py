"""Verify pinned wheel availability and dependency closure using public PyPI metadata.

No packages are installed or executed. This is not a native runtime test.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import urllib.request
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import Tag, compatible_tags, cpython_tags, mac_platforms
from packaging.utils import canonicalize_name, parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TARGETS = ('windows-x64', 'macos-arm64', 'macos-x86_64', 'linux-x86_64', 'linux-arm64')


def target_environment(target: str) -> dict[str, str]:
    if target not in TARGETS:
        raise ValueError('Unsupported target')
    mac = target.startswith('macos-')
    windows = target == 'windows-x64'
    machine = 'AMD64' if windows else 'arm64' if target == 'macos-arm64' else 'aarch64' if target == 'linux-arm64' else 'x86_64'
    return dict(default_environment(), sys_platform='win32' if windows else 'darwin' if mac else 'linux',
                platform_system='Windows' if windows else 'Darwin' if mac else 'Linux',
                os_name='nt' if windows else 'posix', platform_machine=machine,
                python_version='3.14', python_full_version='3.14.7', implementation_name='cpython',
                platform_python_implementation='CPython', implementation_version='3.14.7',
                platform_release='', platform_version='', extra='')


def supported_tags(target: str) -> set[Tag]:
    target_environment(target)
    if target.startswith('macos-'):
        platforms = list(mac_platforms((15, 0), 'arm64' if target.endswith('arm64') else 'x86_64'))
    elif target == 'windows-x64':
        platforms = ['win_amd64']
    else:
        arch = 'aarch64' if target.endswith('arm64') else 'x86_64'
        platforms = [f'manylinux_2_{minor}_{arch}' for minor in range(35, 16, -1)]
        platforms.append('manylinux2014_' + arch)
        if arch == 'x86_64':
            platforms.extend(['manylinux2010_x86_64', 'manylinux1_x86_64'])
    return set(cpython_tags((3, 14), ['cp314'], platforms)) | set(compatible_tags((3, 14), 'cp314', platforms))


def pinned_requirements(root: Path, environment: dict[str, str]) -> dict[str, Requirement]:
    from teleport_cam.vision_backend import requirements_file, vision_backend
    result: dict[str, Requirement] = {}
    backend = vision_backend(environment['sys_platform'], environment['platform_machine'])
    for name in (requirements_file(backend), 'requirements-build.txt'):
        for line in (root / name).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            requirement = Requirement(line)
            if requirement.marker and not requirement.marker.evaluate(environment):
                continue
            pins = list(requirement.specifier)
            if len(pins) != 1 or pins[0].operator != '==':
                raise ValueError('Expected an exact pin: ' + requirement.name)
            result[canonicalize_name(requirement.name)] = requirement
    return result


def fetch_metadata(item: tuple[str, Requirement]) -> tuple[str, dict]:
    name, requirement = item
    version = next(iter(requirement.specifier)).version
    url = f'https://pypi.org/pypi/{name}/{version}/json'
    with urllib.request.urlopen(url, timeout=30) as response:
        if not response.url.startswith('https://pypi.org/'):
            raise ValueError('Unexpected metadata redirect')
        payload = response.read(8 * 1024 * 1024 + 1)
    if len(payload) > 8 * 1024 * 1024:
        raise ValueError('Metadata exceeds limit')
    return name, json.loads(payload)


def check(target: str) -> dict[str, object]:
    environment = target_environment(target)
    requirements = pinned_requirements(ROOT, environment)
    tags = supported_tags(target)
    with ThreadPoolExecutor(max_workers=4) as pool:
        packages = dict(pool.map(fetch_metadata, requirements.items()))
    rows = []
    errors: list[str] = []
    for name, package in packages.items():
        python_constraint = package['info'].get('requires_python')
        if python_constraint and '3.14.7' not in SpecifierSet(python_constraint):
            errors.append(name + ': incompatible Python requirement: ' + python_constraint)
        wheels = []
        for entry in package['urls']:
            if entry['packagetype'] != 'bdist_wheel' or entry.get('yanked'):
                continue
            if parse_wheel_filename(entry['filename'])[3] & tags:
                wheels.append(entry['filename'])
        if not wheels:
            errors.append(name + ': no compatible non-yanked wheel')
        rows.append({'name': name, 'version': package['info']['version'], 'compatible_wheels': wheels})
        for raw in package['info'].get('requires_dist') or ():
            dependency = Requirement(raw)
            if dependency.marker and not dependency.marker.evaluate(environment):
                continue
            dependency_name = canonicalize_name(dependency.name)
            pin = requirements.get(dependency_name)
            if pin is None:
                errors.append(name + ': dependency not pinned: ' + str(dependency))
            elif next(iter(pin.specifier)).version not in dependency.specifier:
                errors.append(name + ': incompatible dependency pin: ' + str(dependency))
    from teleport_cam.vision_backend import vision_backend
    return {'target': target, 'python': '3.14', 'ok': not errors,
            'vision_backend': vision_backend(environment['sys_platform'], environment['platform_machine']),
            'native_runtime_tested': False, 'packages': rows, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=TARGETS)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = check(args.target)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"{args.target}: {len(report['packages'])} pinned packages; {len(report['errors'])} issues. Native runtime untested.")
    for error in report['errors']:
        print(error)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
