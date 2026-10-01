"""
conftest.py — session-wide stubs for hardware/ML/GUI libraries.

Inserted into sys.modules before pytest collects any test file so that
every test module that imports project code (commands, speech, wakeword,
main) gets the same lightweight fakes regardless of collection order.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Ensure the voice-assistant package root is on sys.path
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _stub(name: str):
    """Return the existing stub or create a new one."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return sys.modules[name]


# --- audio ---
_stub("pvporcupine")
_stub("pyaudio")
pa = sys.modules["pyaudio"]
pa.paInt16 = 8
pa.PyAudio = MagicMock()

# --- speech ---
_stub("faster_whisper").WhisperModel = MagicMock()

# --- GUI ---
_stub("pyautogui")

gw = _stub("pygetwindow")
gw.getWindowsWithTitle = MagicMock(return_value=[])
gw.getAllWindows = MagicMock(return_value=[])
gw.getActiveWindow = MagicMock(return_value=None)

# --- misc ---
_stub("sounddevice")
colorama = _stub("colorama")
colorama.Fore = MagicMock()
colorama.Style = MagicMock()
colorama.init = MagicMock()
