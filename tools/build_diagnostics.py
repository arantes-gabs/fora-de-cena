"""Bounded build-error messages without credentials or local profile paths."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def public_error(detail: str) -> str:
    for prefix in sorted({str(ROOT), ROOT.as_posix(), str(Path.home()),
                          Path.home().as_posix(), sys.base_prefix, Path(sys.base_prefix).as_posix()},
                         key=len, reverse=True):
        detail = detail.replace(prefix, '[build-path]')
    detail = re.sub(r'(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]+', '[redacted]', detail)
    detail = re.sub(r'(?i)\b(password|secret|token|authorization)\s*[:=]\s*\S+', r'\1=[redacted]', detail)
    return detail[:1600]
