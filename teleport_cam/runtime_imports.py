"""Keep unused optional audio backends out of the vision adapter's startup."""
from contextlib import contextmanager
import sys


@contextmanager
def without_optional_audio():
    # MediaPipe treats sounddevice as optional. Importing sounddevice itself
    # initializes PortAudio; this video-only app never needs that side effect.
    # Python documents None in sys.modules as an explicit import refusal.
    missing=object()
    previous=sys.modules.get('sounddevice',missing)
    sys.modules['sounddevice']=None
    try:
        yield
    finally:
        if previous is missing:
            sys.modules.pop('sounddevice',None)
        else:
            sys.modules['sounddevice']=previous
