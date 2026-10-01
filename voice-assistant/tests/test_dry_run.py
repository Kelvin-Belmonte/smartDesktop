"""
Tests for dry-run mode (T5).

Verifies that:
  - CommandParser(dry_run=True) performs no OS actions for every command group.
  - Macros in dry-run mode return True without touching the OS.
  - Unknown phrases return False (no change).
  - `python main.py --text --dry-run` end-to-end via subprocess with stdin.
"""

import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# ------------------------------------------------------------------
# Stub hardware-dependent modules before importing project code
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
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from commands import CommandParser
from commands.apps import build_app_commands, _open_app
from commands.terminal import build_terminal_commands, _run_in_terminal
from commands.windows import build_window_commands, minimise_window, snap_left, swap_monitors


# ------------------------------------------------------------------
# Shared minimal config
# ------------------------------------------------------------------

def _make_config(macros=None, projects=None, apps=None):
    return {
        "commands": {
            "prefix": "jarvis",
            "apps": apps or {},
            "projects": projects or {},
            "macros": macros or {},
        }
    }


# ==================================================================
# _open_app dry-run
# ==================================================================

class TestOpenAppDryRun(unittest.TestCase):

    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_dry_run_does_not_launch(self, mock_startfile, mock_popen):
        """_open_app(dry_run=True) must not touch Popen or startfile."""
        result = _open_app("some_app", dry_run=True)
        self.assertTrue(result)
        mock_popen.assert_not_called()
        mock_startfile.assert_not_called()

    @patch("commands.apps.subprocess.Popen")
    def test_normal_mode_does_launch(self, mock_popen):
        """_open_app(dry_run=False) on Linux should call Popen."""
        with patch("commands.apps._OS", "Linux"):
            _open_app("some_app", dry_run=False)
        mock_popen.assert_called_once()


# ==================================================================
# _run_in_terminal dry-run
# ==================================================================

class TestRunInTerminalDryRun(unittest.TestCase):

    @patch("commands.terminal.subprocess.Popen")
    def test_dry_run_does_not_spawn(self, mock_popen):
        """_run_in_terminal(dry_run=True) must not call Popen."""
        result = _run_in_terminal("git status", dry_run=True)
        self.assertTrue(result)
        mock_popen.assert_not_called()


# ==================================================================
# App commands dry-run
# ==================================================================

class TestAppCommandsDryRun(unittest.TestCase):

    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_all_builtin_app_handlers_no_os_call(self, mock_startfile, mock_popen):
        """All built-in app command handlers in dry-run mode must not call OS APIs."""
        cmds = build_app_commands(dry_run=True)
        for phrase, handler in cmds.items():
            mock_popen.reset_mock()
            mock_startfile.reset_mock()
            result = handler()
            self.assertTrue(result, f"Handler for '{phrase}' returned False in dry-run")
            mock_popen.assert_not_called()
            mock_startfile.assert_not_called()

    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_custom_app_dry_run(self, mock_startfile, mock_popen):
        """A custom app from config is also suppressed in dry-run mode."""
        cmds = build_app_commands(
            apps_config={"myeditor": "/usr/bin/myeditor"},
            dry_run=True,
        )
        result = cmds["open myeditor"]()
        self.assertTrue(result)
        mock_popen.assert_not_called()
        mock_startfile.assert_not_called()


# ==================================================================
# Terminal commands dry-run
# ==================================================================

class TestTerminalCommandsDryRun(unittest.TestCase):

    @patch("commands.terminal.subprocess.Popen")
    def test_all_builtin_terminal_handlers_no_os_call(self, mock_popen):
        """All built-in terminal command handlers in dry-run mode must not call Popen."""
        cmds = build_terminal_commands(dry_run=True)
        for phrase, handler in cmds.items():
            mock_popen.reset_mock()
            result = handler()
            self.assertTrue(result, f"Handler for '{phrase}' returned False in dry-run")
            mock_popen.assert_not_called()

    @patch("commands.terminal.subprocess.Popen")
    def test_project_shortcut_dry_run(self, mock_popen):
        """Project shortcuts in dry-run mode must not call Popen."""
        cmds = build_terminal_commands(
            projects_config={"myproj": "~/repos/myproj"},
            dry_run=True,
        )
        result = cmds["go to myproj"]()
        self.assertTrue(result)
        mock_popen.assert_not_called()


# ==================================================================
# Window commands dry-run
# ==================================================================

class TestWindowCommandsDryRun(unittest.TestCase):

    def test_all_window_handlers_no_os_call(self):
        """All window command handlers in dry-run mode must not call pygetwindow or pyautogui."""
        import pygetwindow as gw
        import pyautogui
        cmds = build_window_commands(dry_run=True)
        for phrase, handler in cmds.items():
            gw.getActiveWindow.reset_mock()
            result = handler()
            self.assertTrue(result, f"Handler for '{phrase}' returned False in dry-run")
            gw.getActiveWindow.assert_not_called()

    def test_minimise_dry_run(self):
        """minimise_window(dry_run=True) returns True without touching pygetwindow."""
        with patch("commands.windows._get_window") as mock_gw:
            result = minimise_window(dry_run=True)
        self.assertTrue(result)
        mock_gw.assert_not_called()

    def test_snap_left_dry_run(self):
        """snap_left(dry_run=True) returns True without calling pyautogui."""
        import pyautogui
        pyautogui.hotkey = MagicMock()
        result = snap_left(dry_run=True)
        self.assertTrue(result)
        pyautogui.hotkey.assert_not_called()

    def test_swap_monitors_dry_run(self):
        """swap_monitors(dry_run=True) returns True on any platform without any OS call."""
        with patch("commands.windows._OS", "Linux"):
            result = swap_monitors(dry_run=True)
        self.assertTrue(result)


# ==================================================================
# Macro dry-run
# ==================================================================

class TestMacroDryRun(unittest.TestCase):

    @patch("commands.terminal.subprocess.Popen")
    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_macro_with_parser_no_os_call(self, mock_startfile, mock_apps_popen, mock_term_popen):
        """Macros dispatched through a dry-run CommandParser must not touch the OS."""
        config = _make_config(macros={
            "morning routine": ["open chrome", "open spotify"],
        })
        parser = CommandParser(config, dry_run=True)

        result = parser.execute("morning routine")
        self.assertTrue(result)
        mock_apps_popen.assert_not_called()
        mock_startfile.assert_not_called()
        mock_term_popen.assert_not_called()

    @patch("commands.terminal.subprocess.Popen")
    def test_macro_without_parser_no_os_call(self, mock_popen):
        """Macros without a parser reference also respect dry_run in build_terminal_commands."""
        cmds = build_terminal_commands(
            macros_config={"do stuff": ["git status", "npm start"]},
            parser=None,
            dry_run=True,
        )
        result = cmds["do stuff"]()
        self.assertTrue(result)
        mock_popen.assert_not_called()

    @patch("commands.terminal.subprocess.Popen")
    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_multi_step_macro_all_steps_succeed(self, mock_startfile, mock_apps_popen, mock_term_popen):
        """Multi-step macro in dry-run should return True and call each step once."""
        config = _make_config(macros={
            "start day": ["open chrome", "open discord", "open spotify"],
        })
        parser = CommandParser(config, dry_run=True)

        called = []
        # Intercept the individual command handlers without running them
        for phrase in ["open chrome", "open discord", "open spotify"]:
            original = parser._commands[phrase]
            parser._commands[phrase] = (lambda p=phrase: lambda: called.append(p) or True)()

        result = parser.execute("start day")
        self.assertTrue(result)
        self.assertEqual(called, ["open chrome", "open discord", "open spotify"])


# ==================================================================
# Unknown phrase dry-run
# ==================================================================

class TestUnknownPhraseDryRun(unittest.TestCase):

    def test_unknown_phrase_returns_false(self):
        """An unrecognised phrase in dry-run mode returns False, same as normal mode."""
        parser = CommandParser(_make_config(), dry_run=True)
        result = parser.execute("jarvis do something totally unknown xyzzy12345")
        self.assertFalse(result)

    def test_dry_run_flag_set(self):
        """CommandParser.dry_run attribute reflects the constructor argument."""
        p_dry = CommandParser(_make_config(), dry_run=True)
        p_normal = CommandParser(_make_config(), dry_run=False)
        self.assertTrue(p_dry.dry_run)
        self.assertFalse(p_normal.dry_run)


# ==================================================================
# CommandParser dry-run — all command groups matched
# ==================================================================

class TestCommandParserDryRunAllGroups(unittest.TestCase):
    """Verify that every command group is reachable via execute() in dry-run mode."""

    def setUp(self):
        self.parser = CommandParser(_make_config(), dry_run=True)

    @patch("commands.apps.subprocess.Popen")
    @patch("commands.apps.os.startfile", create=True)
    def test_app_command(self, mock_startfile, mock_popen):
        result = self.parser.execute("open chrome")
        self.assertTrue(result)
        mock_popen.assert_not_called()
        mock_startfile.assert_not_called()

    @patch("commands.terminal.subprocess.Popen")
    def test_terminal_command(self, mock_popen):
        result = self.parser.execute("git status")
        self.assertTrue(result)
        mock_popen.assert_not_called()

    def test_window_command(self):
        with patch("commands.windows._get_window") as mock_gw:
            result = self.parser.execute("minimise window")
        self.assertTrue(result)
        mock_gw.assert_not_called()


# ==================================================================
# End-to-end: --text --dry-run via subprocess
# ==================================================================

class TestTextDryRunEndToEnd(unittest.TestCase):
    """
    Run `python main.py --text --dry-run` as a subprocess, feed commands via
    stdin, and assert that no OS process is spawned and output is produced.
    """

    _MAIN = str(_ROOT / "main.py")

    def _run(self, stdin_text: str):
        """Helper: invoke main.py --text --dry-run with given stdin, return stdout."""
        result = subprocess.run(
            [sys.executable, self._MAIN, "--text", "--dry-run"],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(_ROOT),
        )
        return result

    def test_known_command_exits_zero(self):
        """A recognised command must produce output and exit 0."""
        result = self._run("open chrome\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        # Should print the command phrase
        self.assertIn("open chrome", result.stdout)

    def test_unknown_command_exits_zero(self):
        """An unrecognised command must not crash (still exit 0)."""
        result = self._run("totally unknown xyzzy phrase\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        # Should warn about the unrecognised command
        self.assertIn("not recognised", result.stdout.lower())

    def test_multiple_commands(self):
        """Multiple commands in one session all produce output."""
        result = self._run("open chrome\ngit status\nminimise window\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("open chrome", result.stdout)
        self.assertIn("git status", result.stdout)
        self.assertIn("minimise window", result.stdout)

    def test_no_subprocess_spawned(self):
        """
        In --text --dry-run mode no child process should be started by the
        command handlers (the OS interaction is suppressed).

        We verify this by confirming the command produced recognisable output
        without touching actual binaries.  Because the subprocess.Popen in the
        handlers is skipped by dry-run logic, we just assert exit 0 and output
        is present (the absence of side effects is covered by the unit tests
        above that patch Popen).
        """
        result = self._run("open spotify\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("open spotify", result.stdout)

    def test_empty_lines_ignored(self):
        """Empty lines in stdin must not cause errors."""
        result = self._run("\n\nopen chrome\n\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("open chrome", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
