"""
Tests for security and safety fixes (Task T7 / S-01 .. S-09).
"""

import logging
import os
import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

from commands import CommandParser
from commands.apps import _open_app, build_app_commands
from commands.terminal import _run_background, _run_in_terminal, build_terminal_commands
from speech import SpeechRecognizer


# ===========================================================================
# S-01: AppleScript injection prevention on macOS
# ===========================================================================
class TestS01AppleScriptInjection:
    """S-01: AppleScript commands must not interpolate arbitrary unescaped strings."""

    @patch("commands.terminal._OS", "Darwin")
    @patch("commands.terminal.subprocess.Popen")
    def test_s01_applescript_injection_prevention(self, mock_popen):
        malicious_command = 'echo "hello" && do shell script "rm -rf /"'
        _run_in_terminal(malicious_command)

        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        # Must be passed as arguments with argv rather than interpolated into do script string
        assert args[0] == "osascript"
        assert args[-1] == malicious_command
        # Should not directly interpolate dangerous quote into -e string without parameterization
        assert f'do script "{malicious_command}"' not in args[2]


# ===========================================================================
# S-02: Windows cmd injection prevention (avoid shell=True)
# ===========================================================================
class TestS02WindowsCmdInjection:
    """S-02: Windows terminal and background runners avoid shell=True."""

    @patch("commands.terminal._OS", "Windows")
    @patch("commands.terminal.subprocess.Popen")
    def test_s02_run_in_terminal_avoids_shell_true(self, mock_popen):
        command = 'echo test & calc.exe'
        _run_in_terminal(command)

        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["cmd", "/K", command]
        assert "shell" not in kwargs or kwargs["shell"] is False

    @patch("commands.terminal._OS", "Windows")
    @patch("commands.terminal.subprocess.Popen")
    def test_s02_run_background_avoids_shell_true(self, mock_popen):
        command = "python script.py --arg 123"
        _run_background(command)

        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["python", "script.py", "--arg", "123"]
        assert "shell" not in kwargs or kwargs["shell"] is False


# ===========================================================================
# S-03: shell=True avoided for app launcher on macOS, Linux, and Windows
# ===========================================================================
class TestS03AppLauncherNoShellTrue:
    """S-03: _open_app does not pass shell=True when launching executables."""

    @patch("commands.apps._OS", "Linux")
    @patch("commands.apps.subprocess.Popen")
    def test_s03_linux_open_app_no_shell_true(self, mock_popen):
        _open_app("my-app --flag value")
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["my-app", "--flag", "value"]
        assert "shell" not in kwargs or kwargs["shell"] is False

    @patch("commands.apps._OS", "Darwin")
    @patch("commands.apps.subprocess.Popen")
    def test_s03_macos_open_app_no_shell_true(self, mock_popen):
        _open_app("/usr/local/bin/custom-app --arg 1")
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["/usr/local/bin/custom-app", "--arg", "1"]
        assert "shell" not in kwargs or kwargs["shell"] is False

    @patch("commands.apps._OS", "Windows")
    @patch("os.path.isfile", return_value=False)
    @patch("commands.apps.subprocess.Popen")
    def test_s03_windows_open_app_fallback_no_shell_true(self, mock_popen, _):
        _open_app("calc.exe")
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["calc.exe"]
        assert "shell" not in kwargs or kwargs["shell"] is False


# ===========================================================================
# S-04: Confirmation for destructive / high-impact commands
# ===========================================================================
class TestS04DestructiveCommandConfirmation:
    """S-04: Destructive commands require confirmation when confirm_destructive is enabled."""

    def test_s04_close_window_rejected_when_not_confirmed(self):
        config = {
            "commands": {
                "confirm_destructive": True,
            }
        }
        confirm_callback = MagicMock(return_value=False)
        parser = CommandParser(config, confirm_callback=confirm_callback)

        with patch("commands.windows.close_window") as mock_close:
            result = parser.execute("close window")
            confirm_callback.assert_called_once_with("close window")
            mock_close.assert_not_called()
            assert result is False

    def test_s04_close_window_executed_when_confirmed(self):
        config = {
            "commands": {
                "confirm_destructive": True,
            }
        }
        confirm_callback = MagicMock(return_value=True)
        parser = CommandParser(config, confirm_callback=confirm_callback)

        with patch("commands.windows._get_window") as mock_gw:
            mock_win = MagicMock()
            mock_gw.return_value = mock_win
            result = parser.execute("close window")
            confirm_callback.assert_called_once_with("close window")
            mock_win.close.assert_called_once()
            assert result is True

    def test_s04_destructive_macro_requires_confirmation(self):
        config = {
            "commands": {
                "confirm_destructive": True,
                "macros": {
                    "start dev": ["open terminal", "run npm run dev"]
                }
            }
        }
        confirm_callback = MagicMock(return_value=False)
        parser = CommandParser(config, confirm_callback=confirm_callback)

        with patch("commands.terminal._run_in_terminal") as mock_run:
            result = parser.execute("start dev")
            confirm_callback.assert_called_once_with("start dev")
            mock_run.assert_not_called()
            assert result is False

    def test_s04_dry_run_skips_confirmation(self):
        config = {
            "commands": {
                "confirm_destructive": True,
            }
        }
        confirm_callback = MagicMock(return_value=False)
        parser = CommandParser(config, dry_run=True, confirm_callback=confirm_callback)

        result = parser.execute("close window")
        # In dry run, confirmation is skipped and action is planned
        confirm_callback.assert_not_called()
        assert result is True


# ===========================================================================
# S-05: Redaction of transcripts in logs unless DEBUG
# ===========================================================================
class TestS05TranscriptRedaction:
    """S-05: Full transcripts are redacted from logs unless DEBUG is enabled."""

    def test_s05_transcript_redacted_at_info_level(self, caplog):
        with caplog.at_level(logging.INFO, logger="speech"):
            with patch("speech.WhisperModel") as mock_wm_cls:
                mock_model = MagicMock()
                mock_segment = MagicMock()
                mock_segment.text = "my secret password is 12345"
                mock_model.transcribe.return_value = ([mock_segment], MagicMock())
                mock_wm_cls.return_value = mock_model

                recognizer = SpeechRecognizer(model_size="base")
                import numpy as np
                transcript = recognizer._transcribe(np.zeros(16000, dtype=np.float32))

                assert transcript == "my secret password is 12345"
                # Transcript text must NOT appear in INFO logs
                assert "my secret password" not in caplog.text
                assert "redacted" in caplog.text

    def test_s05_transcript_logged_at_debug_level(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="speech"):
            with patch("speech.WhisperModel") as mock_wm_cls:
                mock_model = MagicMock()
                mock_segment = MagicMock()
                mock_segment.text = "my secret password is 12345"
                mock_model.transcribe.return_value = ([mock_segment], MagicMock())
                mock_wm_cls.return_value = mock_model

                recognizer = SpeechRecognizer(model_size="base")
                import numpy as np
                transcript = recognizer._transcribe(np.zeros(16000, dtype=np.float32))

                assert transcript == "my secret password is 12345"
                # At DEBUG level, it should be logged for debugging
                assert "my secret password is 12345" in caplog.text


# ===========================================================================
# S-06: Porcupine access key read from environment variable
# ===========================================================================
class TestS06PorcupineKeyEnvVar:
    """S-06: Porcupine key is read from PORCUPINE_ACCESS_KEY env variable."""

    def test_s06_porcupine_key_from_env_var(self):
        from main import SmartDesktopAssistant

        config = {
            "wakeword": {
                "access_key": "YOUR_PORCUPINE_ACCESS_KEY",
                "keywords": ["jarvis"],
            }
        }

        with patch.dict(os.environ, {"PORCUPINE_ACCESS_KEY": "valid_env_key_12345"}):
            with patch("wakeword.WakeWordDetector") as mock_ww:
                mock_detector = MagicMock()
                mock_ww.return_value = mock_detector
                mock_detector.__enter__.return_value = mock_detector

                assistant = SmartDesktopAssistant(config, dry_run=True)
                assistant._shutdown_event.set()
                assistant.run()

                mock_ww.assert_called_once()
                assert mock_ww.call_args[1]["access_key"] == "valid_env_key_12345"


# ===========================================================================
# S-07: Pinned dependencies in requirements.txt
# ===========================================================================
class TestS07PinnedDependencies:
    """S-07: All dependencies in voice-assistant/requirements.txt must be pinned with =="""

    def test_s07_all_requirements_pinned(self):
        req_file = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        with open(req_file, "r", encoding="utf-8") as fh:
            lines = [line.strip() for line in fh if line.strip() and not line.strip().startswith("#")]

        assert len(lines) > 0
        for line in lines:
            assert "==" in line, f"Requirement '{line}' is not pinned with '=='"
            assert ">=" not in line, f"Requirement '{line}' contains '>='"


# ===========================================================================
# S-08: Macro phrases and command boundaries
# ===========================================================================
class TestS08MacroSecurity:
    """S-08: Macros are identified as destructive and can be confirmed or cancelled."""

    def test_s08_macro_execution_guarded(self):
        config = {
            "commands": {
                "confirm_destructive": True,
                "macros": {
                    "morning routine": ["open chrome", "open spotify"]
                }
            }
        }
        confirm_callback = MagicMock(return_value=False)
        parser = CommandParser(config, confirm_callback=confirm_callback)

        assert parser.is_destructive("morning routine")
        assert not parser.execute("morning routine")
        confirm_callback.assert_called_once_with("morning routine")


# ===========================================================================
# S-09: Linux bash -c command injection prevention
# ===========================================================================
class TestS09LinuxBashInjection:
    """S-09: Linux terminal commands pass arguments separately to avoid injection."""

    @patch("commands.terminal._OS", "Linux")
    @patch("commands.terminal._which", return_value="/usr/bin/gnome-terminal")
    @patch("commands.terminal.subprocess.Popen")
    def test_s09_linux_terminal_argument_passing(self, mock_popen, _):
        command = "echo hi; rm -rf /"
        _run_in_terminal(command)

        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "gnome-terminal"
        # Should be passed as positional argument $0 to bash -c
        assert args == ["gnome-terminal", "--", "bash", "-c", "$0; exec bash", command]
