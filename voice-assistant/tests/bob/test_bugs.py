"""
B-xx baseline test suite: reproduction tests for all known bugs.
Written in Task T3 against commit 992e4dc. Failure markers removed in Task T4 after fixes.

These tests assert the CORRECT behaviour of the application code.
All OS interactions, GUI libraries, and hardware interfaces are mocked.
"""

import os
import platform
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ------------------------------------------------------------------
# Stub hardware / ML / GUI modules before importing project code
# ------------------------------------------------------------------

def _stub_module(name):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return sys.modules[name]

_stub_module("pvporcupine")
_stub_module("pyaudio")
pa_mod = sys.modules["pyaudio"]
pa_mod.paInt16 = 8
pa_mod.PyAudio = MagicMock()

fw_mod = _stub_module("faster_whisper")
fw_mod.WhisperModel = MagicMock()

_stub_module("pyautogui")

gw_mod = _stub_module("pygetwindow")
gw_mod.getWindowsWithTitle = MagicMock(return_value=[])
gw_mod.getAllWindows = MagicMock(return_value=[])
gw_mod.getActiveWindow = MagicMock(return_value=None)

_stub_module("sounddevice")
colorama_mod = _stub_module("colorama")
colorama_mod.Fore = MagicMock()
colorama_mod.Style = MagicMock()
colorama_mod.init = MagicMock()

# Ensure voice-assistant package root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commands import CommandParser
from commands.apps import _open_app, build_app_commands, open_terminal
from commands.terminal import build_terminal_commands
from commands.windows import _get_window, close_window, minimise_window
from speech import SpeechRecognizer
from wakeword import WakeWordDetector


# ==================================================================
# B-01: Macro execution
# ==================================================================

def test_b01_macro_executes_assistant_commands():
    """
    B-01: Macros defined in config.yaml with assistant commands (e.g. 'open chrome')
    should trigger assistant command handlers or be executed via the assistant parser,
    rather than launching a new OS terminal window with raw shell command 'open chrome'.
    """
    config = {
        "commands": {
            "prefix": "jarvis",
            "macros": {
                "morning routine": ["open chrome", "open spotify"],
            },
        }
    }
    parser = CommandParser(config)

    # When executing a macro containing voice assistant commands, the macro should
    # dispatch the assistant actions (e.g. call the registered handler for 'open chrome')
    # and should NOT invoke _run_in_terminal.
    chrome_called = []
    parser._commands["open chrome"] = lambda: chrome_called.append(True) or True

    with patch("commands.terminal._run_in_terminal") as mock_terminal:
        # Currently, build_terminal_commands binds macro steps directly to _run_in_terminal
        result = parser.execute("jarvis morning routine")
        # In correct behaviour, the assistant command 'open chrome' handler should be called,
        # and _run_in_terminal should not be called with 'open chrome'.
        assert len(chrome_called) == 1, "Macro step 'open chrome' did not invoke assistant handler"
        mock_terminal.assert_not_called()


# ==================================================================
# B-02: Window targeting active window
# ==================================================================

def test_b02_window_commands_target_active_window():
    """
    B-02: When no title is supplied to window commands (e.g. 'minimise window'),
    it should target the active window (pygetwindow.getActiveWindow()), not matches[0]
    from getWindowsWithTitle("").
    """
    active_win = MagicMock()
    active_win.title = "Focused Active Window"

    bg_win = MagicMock()
    bg_win.title = "Background Window 1"

    with patch("pygetwindow.getActiveWindow", return_value=active_win):
        with patch("pygetwindow.getWindowsWithTitle", return_value=[bg_win, active_win]):
            win = _get_window("")
            # Expected: when title is empty, it returns the active window.
            # Actual: it returns matches[0], which is bg_win.
            assert win == active_win, f"Expected active window, got {win.title if win else None}"


# ==================================================================
# B-03: Linux terminal fallback
# ==================================================================

def test_b03_open_terminal_linux_fallback_consistency():
    """
    B-03: On Linux, open_terminal() should check available terminal emulators
    (or use the same emulator discovery logic as commands/terminal.py) rather than
    blindly falling back to 'xterm' which may not be installed.
    """
    with patch("commands.apps._OS", "Linux"):
        with patch("commands.apps._open_app") as mock_open:
            # Suppose x-terminal-emulator is not installed, but gnome-terminal is.
            # apps.open_terminal() currently hardcodes 'paths.get(_OS, "xterm")' -> 'x-terminal-emulator',
            # but if fallback occurs or paths differs, it should use a robust emulator search.
            # Specifically, paths['Linux'] = 'x-terminal-emulator', and fallback is 'xterm'.
            # If x-terminal-emulator is not installed, it should try other common emulators like gnome-terminal.
            with patch("shutil.which", side_effect=lambda x: "/usr/bin/gnome-terminal" if x == "gnome-terminal" else None):
                open_terminal()
                mock_open.assert_called_with("gnome-terminal")


# ==================================================================
# B-04: macOS open_app with arguments or binary
# ==================================================================

def test_b04_macos_open_app_with_arguments_or_binary():
    """
    B-04: On macOS, _open_app('mytool --arg') should not call `open -a 'mytool --arg'`,
    because 'open -a' takes an application name, not command line arguments.
    """
    with patch("commands.apps._OS", "Darwin"):
        with patch("commands.apps.subprocess.Popen") as mock_popen:
            _open_app("mytool --arg")
            # Bug: "/" not in "mytool --arg" -> calls Popen(["open", "-a", "mytool --arg"])
            # Correct behavior: should not pass command-line arguments to open -a
            assert mock_popen.call_args[0][0] != ["open", "-a", "mytool --arg"]


# ==================================================================
# B-05: CUDA fallback forces CPU compute_type
# ==================================================================

def test_b05_cuda_fallback_forces_cpu_compute_type():
    """
    B-05: When initialized with device='cuda' and compute_type='float16',
    a CUDA failure at transcribe time should reload on CPU using 'int8' or 'float32',
    NOT re-use 'float16' which fails on most CPUs in Faster-Whisper.
    """
    import numpy as np

    with patch("speech.WhisperModel") as mock_wm_cls:
        mock_model = MagicMock()
        mock_wm_cls.return_value = mock_model
        recognizer = SpeechRecognizer(model_size="base", device="cuda", compute_type="float16")

        # Simulate CUDA error on iteration
        def _bad_iter():
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
            yield

        mock_model.transcribe.return_value = (_bad_iter(), MagicMock())

        with patch.object(recognizer, "_reload_on_cpu", wraps=recognizer._reload_on_cpu) as mock_reload:
            with patch("speech.WhisperModel") as mock_cpu_wm:
                cpu_model = MagicMock()
                cpu_model.transcribe.return_value = (iter([MagicMock(text="test")]), MagicMock(language="en", language_probability=0.99))
                mock_cpu_wm.return_value = cpu_model

                audio = np.zeros(16000, dtype=np.float32)
                recognizer._transcribe(audio)

                # Correct behaviour: compute_type must be int8 or float32 for CPU
                # Bug in speech/__init__.py:247 -> uses self._compute_type ('float16')
                mock_cpu_wm.assert_called_with("base", device="cpu", compute_type="int8")


# ==================================================================
# B-06: Wake-word loop survives runtime errors
# ==================================================================

def test_b06_wakeword_loop_survives_runtime_errors():
    """
    B-06: Non-OSError exceptions in WakeWordDetector._detection_loop (e.g. RuntimeError
    from Porcupine processing) must be caught and logged so the detection loop
    does not crash and terminate the thread.
    """
    detector = WakeWordDetector(access_key="dummy", keywords=["jarvis"])
    detector._porcupine = MagicMock()
    detector._porcupine.frame_length = 512
    detector._porcupine.sample_rate = 16000
    detector._audio_stream = MagicMock()
    detector._audio_stream.read.return_value = b"\x00" * 1024

    # Simulate Porcupine process raising a RuntimeError once, then normal
    call_count = [0]
    def fake_process(pcm):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("Porcupine internal processing error")
        detector._running = False
        return -1

    detector._porcupine.process.side_effect = fake_process
    detector._running = True

    # Current behaviour: unhandled RuntimeError escapes _detection_loop and crashes thread.
    # Expected behaviour: _detection_loop catches Exception, logs it, and continues.
    try:
        detector._detection_loop()
    except RuntimeError:
        pytest.fail("RuntimeError was not caught in WakeWordDetector._detection_loop")


# ==================================================================
# B-07: Config apps clobbering built-ins
# ==================================================================

def test_b07_config_apps_does_not_silently_override_builtins():
    """
    B-07: Configuring an app shortcut with the name of a core built-in command
    (e.g., 'terminal' or 'chrome') should not silently clobber the built-in launcher.
    """
    custom_apps = {"terminal": "C:/custom/term.exe"}
    cmds = build_app_commands(apps_config=custom_apps)

    # In correct behaviour, either the built-in handler remains protected or custom
    # apps are disambiguated/warned instead of silently overwriting built-in commands.
    # Here we assert that 'open terminal' preserves the built-in open_terminal handler.
    from commands.apps import open_terminal as builtin_open_terminal
    assert cmds["open terminal"] == builtin_open_terminal, "Built-in 'open terminal' was silently overwritten by custom app config"
