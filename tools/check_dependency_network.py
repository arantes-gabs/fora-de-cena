"""Linux CI-only network syscall counts; never capture packets or user traffic.

Uses strace -f -c -e trace=%network (summary only), following its official manual:
https://github.com/strace/strace/blob/v5.16/doc/strace.1.in
This bounded synthetic sample does not certify absence of future telemetry.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def parse_counts(summary: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in summary.splitlines():
        fields = line.split()
        if not fields or fields[0] == '%' or set(line.strip()) <= {'-', ' '}:
            continue
        if (len(fields) not in (5, 6) or not fields[3].isdigit()
                or not re.fullmatch(r'[a-z][a-z0-9_]*', fields[-1])):
            raise ValueError('Unexpected strace summary format; do not assume zero activity.')
        if fields[-1] != 'total':
            if fields[-1] in counts:
                raise ValueError('Duplicate syscall in strace summary.')
            counts[fields[-1]] = int(fields[3])
    return counts


def trace(mode: str, folder: Path, tracer: str) -> dict[str, int]:
    summary = folder / (mode + '.counts')
    home = folder / (mode + '-home')
    home.mkdir()
    # No GitHub credentials, proxy settings or personal profile/config are inherited.
    environment = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(home),
                   'TMPDIR': str(folder), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
                   'MPLBACKEND': 'Agg', 'PYTHONUTF8': '1',
                   'FDC_NETWORK_DIAGNOSTIC_CHILD': '1',
                   'XDG_CONFIG_HOME': str(home), 'XDG_CACHE_HOME': str(home),
                   # setup-python requires its own shared libpython on Linux.
                   'LD_LIBRARY_PATH': str(Path(sys.base_prefix) / 'lib')}
    command = [tracer, '-f', '-qq', '-c', '-e', 'trace=%network', '-o', str(summary),
               sys.executable, str(Path(__file__).resolve()), '--workload', mode]
    result = subprocess.run(command, cwd=ROOT, env=environment, timeout=180,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode or not summary.is_file():
        raise RuntimeError('Traced workload failed; no network conclusion is available.')
    return parse_counts(summary.read_text(encoding='utf-8'))


def workload(mode: str) -> None:
    if os.environ.get('FDC_NETWORK_DIAGNOSTIC_CHILD')!='1':
        raise RuntimeError('Synthetic workloads are internal to the isolated CI check.')
    if mode == 'canary':
        # Deliberate loopback attempt, no payload. Proves child syscall tracing works.
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(1)
            probe.connect_ex(('127.0.0.1', 9))
        return
    if mode=='audio-control':
        # Clean runner only: imports the optional backend without recording.
        import sounddevice
        return
    sys.path.insert(0, str(ROOT))
    from teleport_cam.launcher import self_test
    if not self_test().get('ok'):
        raise RuntimeError('Synthetic application self-test failed.')
    time.sleep(5)  # Observe a short idle period and normal process shutdown too.


def audit() -> int:
    if not sys.platform.startswith('linux') or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('This check runs only on a clean Linux GitHub runner, not your computer.')
    tracer = shutil.which('strace')
    if not tracer:
        raise RuntimeError('strace is required; do not silently skip network observation.')
    work = ROOT / 'work'
    if not work.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Redirected CI work directory.')
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='network-counts-', dir=work) as temporary:
        folder = Path(temporary)
        canary = trace('canary', folder, tracer)
        if canary.get('socket', 0) < 1 or canary.get('connect', 0) < 1:
            raise RuntimeError('Network tracing canary failed; no conclusion is available.')
        counts = trace('synthetic', folder, tracer)
        try:
            audio_counts = trace('audio-control', folder, tracer)
        except RuntimeError:
            audio_counts = None  # Optional comparison, never the application gate.
    report = {'scope': 'Linux source self-test, 5-second idle and process shutdown',
              'camera_opened': False, 'packet_payload_captured': False,
              'canary_verified': True, 'network_syscall_counts': counts,
              'optional_audio_control_counts': audio_counts,
              'sample_network_syscalls_observed': any(counts.values()),
              'dependency_network_verified': False, 'distribution_ready': False}
    (work / 'dependency-network-sample.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    # Activity is not automatically labelled telemetry; investigate before approval.
    return 1 if any(counts.values()) else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workload', choices=('canary', 'synthetic', 'audio-control'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.workload:
        workload(args.workload)
    else:
        raise SystemExit(audit())
