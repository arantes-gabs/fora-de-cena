"""Platform selection shared by runtime, model preparation and native packaging."""
from __future__ import annotations

import platform
import sys


def vision_backend(system: str | None = None, machine: str | None = None) -> str:
    system = sys.platform if system is None else system
    machine = platform.machine() if machine is None else machine
    return 'opencv-dnn' if system == 'darwin' and machine.lower() in ('x86_64', 'amd64') else 'mediapipe'


def requirements_file(backend: str) -> str:
    if backend not in ('opencv-dnn', 'mediapipe'):
        raise ValueError('Backend de visão desconhecido.')
    return 'requirements-intel.lock.txt' if backend == 'opencv-dnn' else 'requirements.lock.txt'
