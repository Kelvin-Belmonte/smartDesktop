# Session 07: T7 Safety layer

- **Date:** 2026-09-30
- **Mode:** 🛠️ SD Developer
- **Files edited:** `voice-assistant/commands/*.py`, `voice-assistant/main.py`, `voice-assistant/speech/__init__.py`, `voice-assistant/config.yaml`, `voice-assistant/requirements.txt`, `voice-assistant/tests/test_safety.py`
- **Accept command and result:** `pytest tests -v` → 92 passed

## What Bob did

- S-01 / S-09: AppleScript and Linux `bash -c` now receive the command as an argument (argv / `$0`), not by interpolation.
- S-02 / S-03: removed `shell=True` everywhere and switched to argument lists (`shlex.split`).
- S-04 / S-08: added `confirm_destructive` in `config.yaml`, with voice and text confirmation; dry-run skips it.
- S-05 / S-06 / S-07: transcripts are redacted unless the log level is DEBUG, the key is read from `PORCUPINE_ACCESS_KEY`, and the requirements are pinned with `==`.
- Added `tests/test_safety.py`, with one test class per S-xx.

## Prompt

```text
Task T7 from BOB_TASKS.md. Fix the security findings in docs/baseline/security-audit.md that task T4
did not already fix, starting with the highest severity.

At minimum: destructive or high-impact commands (closing windows, running shell commands, macros that
run commands) need a confirmation step, configurable in config.yaml, that works in voice and text mode
and is skipped in dry-run; strings interpolated into AppleScript or shell commands are escaped or
passed as argument lists instead of shell=True; transcripts are redacted from logs unless the log level
is DEBUG; the Porcupine key is read from the PORCUPINE_ACCESS_KEY environment variable; and the
dependencies in requirements.txt are pinned.

Add tests for each fix in voice-assistant/tests/test_safety.py, naming the S-xx id in each test.
Finish when `cd voice-assistant && python -m pytest tests -v` passes.
```

## Bob's session notes

Bob wrote these notes itself at the end of the task.

### Findings addressed

| ID | Severity | File & line | Description & Resolution |
|---|---|---|---|
| **S-01** | Critical | `commands/terminal.py:55-63` | **AppleScript injection**: Fixed by passing the command safely as a positional argument via argv (`osascript -e 'on run argv...' -- <command>`), preventing string escaping attacks. |
| **S-02** | Critical | `commands/terminal.py:50`, `commands/terminal.py:109` | **Windows cmd & background injection via `shell=True`**: Eliminated `shell=True`. On Windows, `cmd /K` now uses list form `["cmd", "/K", command]`. Background processes use `shlex.split()`. |
| **S-03** | High | `commands/apps.py:50-65` | **`shell=True` on app launch**: Replaced `shell=True` fallback on all platforms with safe `shlex.split(app_path)` argument list execution. |
| **S-04** | High | `commands/__init__.py:132-137`, `main.py:133-146`, `main.py:204-211` | **Missing confirmation for destructive commands**: Added `confirm_destructive` config option. High-impact commands (`close window`, shell/dev scripts, macros) require confirmation in voice (`_voice_confirm`) and text (`_text_confirm`) mode, and are skipped in dry-run mode. |
| **S-05** | High | `speech/__init__.py:231-234`, `main.py:246-256` | **Plaintext transcript logging**: Redacted transcripts at `INFO` level. Full transcripts are now only logged if log level is `DEBUG`. |
| **S-06** | Medium | `main.py:196-206` | **Porcupine key plain string in config**: Prioritized reading `PORCUPINE_ACCESS_KEY` environment variable. |
| **S-07** | Medium | `requirements.txt:1-24` | **Unpinned dependencies**: Pinned all packages to exact versions (`==`) across `voice-assistant/requirements.txt`. |
| **S-08** | Medium | `commands/__init__.py:76-83` | **Macro step security**: Guarded macros under `confirm_destructive` checks and ensured macro execution cannot trigger unconfirmed destructive side-effects. |
| **S-09** | Medium | `commands/terminal.py:70` | **Linux terminal command injection**: Passed command as positional parameter `$0` to `bash -c` (`[term, "--", "bash", "-c", "$0; exec bash", command]`). |

---

### Test coverage

Created `voice-assistant/tests/test_safety.py` covering:
- `TestS01AppleScriptInjection`: Verifies AppleScript parameterization and absence of raw interpolation.
- `TestS02WindowsCmdInjection`: Verifies `shell=True` elimination in Windows terminal and background runners.
- `TestS03AppLauncherNoShellTrue`: Verifies argument list execution for application launching across Linux, macOS, and Windows.
- `TestS04DestructiveCommandConfirmation`: Tests confirmation flows for `close window`, macro steps, and dry-run bypass.
- `TestS05TranscriptRedaction`: Tests redaction of transcript at `INFO` level and visibility at `DEBUG` level.
- `TestS06PorcupineKeyEnvVar`: Tests `PORCUPINE_ACCESS_KEY` environment variable handling.
- `TestS07PinnedDependencies`: Tests that all dependencies in `requirements.txt` are pinned with `==`.
- `TestS08MacroSecurity`: Tests macro protection under `confirm_destructive`.
- `TestS09LinuxBashInjection`: Tests safe positional parameterization for Linux terminal commands.

## Transcript

Exported from IBM Bob on 2026-10-01.

### 👤 User

## T7: Safety layer

- **Mode:** 🛠️ SD Developer
- **Edits:** `voice-assistant/**`
- **Accept:** `cd voice-assistant && python -m pytest tests -v`
- **Session file:** `docs/bob-sessions/07-safety-layer.md`

**Prompt**
```text
Task T7 from BOB_TASKS.md. Fix the security findings in docs/baseline/security-audit.md that task T4
did not already fix, starting with the highest severity.

At minimum: destructive or high-impact commands (closing windows, running shell commands, macros that
run commands) need a confirmation step, configurable in config.yaml, that works in voice and text mode
and is skipped in dry-run; strings interpolated into AppleScript or shell commands are escaped or
passed as argument lists instead of shell=True; transcripts are redacted from logs unless the log level
is DEBUG; the Porcupine key is read from the PORCUPINE_ACCESS_KEY environment variable; and the
dependencies in requirements.txt are pinned.

Add tests for each fix in voice-assistant/tests/test_safety.py, naming the S-xx id in each test.
Finish when `cd voice-assistant && python -m pytest tests -v` passes.
```

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — docs/baseline/security-audit.md

### 🤖 Assistant

> 🔧 called: glob



> 🔧 **glob** — **/*

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && python -m pytest tests -v

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — which python3 || which python || find / -name pytest 2>/dev/null

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && python3 -m pytest tests -v

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — which -a python3; which -a python; which -a pytest; find ~/.pyenv ~/.local /opt/homebrew ~/.venv -name pytest 2>/dev/null

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — echo $PATH; find /Users/mario-ibm -name "pytest" -maxdepth 5 2>/dev/null

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python -m pytest voice-assistant/tests -v

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — BOB_TASKS.md

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — BOB_TASKS.md

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/requirements.txt

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — playground/requirements.txt

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/terminal.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/apps.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/windows.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/__init__.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/main.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/speech/__init__.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/wakeword/__init__.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/config.yaml

### 🤖 Assistant

> 🔧 called: search_and_replace



> 🔧 **search_and_replace** — # Speech recognition
faster-whisper>=1.0.0

# Wake word detection
pvporcupine>=3.0.0

# Audio capture
pyaudio>=0.2.13
sounddevice>=0.4.6
numpy>=1.24.0

# Desktop automation
pyautogui>=0.9.54
pygetwindow>=0.0.9

# Configuration
pyyaml>=6.0

# NLP (optional, for advanced command parsing)
# spacy>=3.7.0

# Utilities
colorama>=0.4.6

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/requirements.txt

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/requirements.txt

### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — voice-assistant/tests

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/tests/bob/test_bugs.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/commands/terminal.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:101
-------
    try:
        subprocess.Popen(
            command,
            shell=True,
            cwd=expanded_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Background command started: %s", command)
        return True
=======
    try:
        args = shlex.split(command, posix=(_OS != "Windows")) if isinstance(command, str) else command
        subprocess.Popen(
            args,
            cwd=expanded_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Background command started: %s", command)
        return True
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/commands/apps.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/speech/__init__.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:194
-------
        ww_cfg = self.config.get("wakeword", {})
        access_key = ww_cfg.get("access_key", "")
        # Support environment variable expansion (e.g. "${PORCUPINE_ACCESS_KEY}")
        access_key = os.path.expandvars(access_key)

        if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            _warn(
                "Porcupine access key not configured.\n"
                "  1. Sign up at https://console.picovoice.ai/ (free tier available).\n"
                "  2. Copy your access key into config.yaml → wakeword.access_key"
            )
            sys.exit(1)
=======
        # S-06: Read Porcupine key from PORCUPINE_ACCESS_KEY environment variable first,
        # with fallback to config.yaml if non-default.
        access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "").strip()
        if not access_key:
            ww_cfg = self.config.get("wakeword", {})
            raw_key = ww_cfg.get("access_key", "")
            expanded_key = os.path.expandvars(raw_key).strip()
            if expanded_key and expanded_key != "YOUR_PORCUPINE_ACCESS_KEY":
                access_key = expanded_key

        if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            _warn(
                "Porcupine access key not configured.\n"
                "  1. Sign up at https://console.picovoice.ai/ (free tier available).\n"
                "  2. Set the PORCUPINE_ACCESS_KEY environment variable."
            )
            sys.exit(1)
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:240
-------
        _info(f"You said: \"{transcript}\"")
        success = self._parser.execute(transcript)
        if not success:
            _warn(f"Command not recognised: \"{transcript}\"")
=======
        logger = logging.getLogger(__name__)
        if logger.isEnabledFor(logging.DEBUG):
            _info(f"You said: \"{transcript}\"")
        else:
            _info("Voice command received.")
        success = self._parser.execute(transcript)
        if not success:
            if logger.isEnabledFor(logging.DEBUG):
                _warn(f"Command not recognised: \"{transcript}\"")
            else:
                _warn("Command not recognised.")
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/config.yaml

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/commands/__init__.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:94
-------
        handler, matched = self._match(phrase)
        if handler is None:
            logger.warning("No command matched for: '%s'", phrase)
            return False

        logger.info("Executing command '%s'...", matched)
=======
        handler, matched = self._match(phrase)
        if handler is None:
            logger.warning("No command matched for: '%s'", phrase)
            return False

        if self.is_destructive(matched) and not self.dry_run and self.confirm_destructive:
            confirmed = self._confirm_action(matched)
            if not confirmed:
                logger.info("Command '%s' cancelled by user.", matched)
                return False

        logger.info("Executing command '%s'...", matched)
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:115
-------
    @property
    def registered_commands(self) -> list:
        """Return a sorted list of all registered command phrases."""
        return sorted(self._commands.keys())
=======
    def is_destructive(self, command: str) -> bool:
        """Return True if ``command`` is classified as destructive or high-impact."""
        return command.lower() in self._destructive_commands

    @property
    def registered_commands(self) -> list:
        """Return a sorted list of all registered command phrases."""
        return sorted(self._commands.keys())

    def _confirm_action(self, command: str) -> bool:
        """Prompt for confirmation before executing a destructive action."""
        if self.confirm_callback is not None:
            return self.confirm_callback(command)
        return True
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/main.py

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
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


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python -m pytest voice-assistant/tests -v

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:192
-------
    def run(self) -> None:
        """Start the assistant and block until interrupted."""
        from wakeword import WakeWordDetector

        # S-06: Read Porcupine key from PORCUPINE_ACCESS_KEY environment variable first,
        # with fallback to config.yaml if non-default.
        access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "").strip()
        if not access_key:
            ww_cfg = self.config.get("wakeword", {})
            raw_key = ww_cfg.get("access_key", "")
            expanded_key = os.path.expandvars(raw_key).strip()
            if expanded_key and expanded_key != "YOUR_PORCUPINE_ACCESS_KEY":
                access_key = expanded_key

        if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            _warn(
                "Porcupine access key not configured.\n"
                "  1. Sign up at https://console.picovoice.ai/ (free tier available).\n"
                "  2. Set the PORCUPINE_ACCESS_KEY environment variable."
            )
            sys.exit(1)

        keywords = ww_cfg.get("keywords", ["jarvis"])
        sensitivity = float(ww_cfg.get("sensitivity", 0.5))
=======
    def run(self) -> None:
        """Start the assistant and block until interrupted."""
        from wakeword import WakeWordDetector

        ww_cfg = self.config.get("wakeword", {})
        # S-06: Read Porcupine key from PORCUPINE_ACCESS_KEY environment variable first,
        # with fallback to config.yaml if non-default.
        access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "").strip()
        if not access_key:
            raw_key = ww_cfg.get("access_key", "")
            expanded_key = os.path.expandvars(raw_key).strip()
            if expanded_key and expanded_key != "YOUR_PORCUPINE_ACCESS_KEY":
                access_key = expanded_key

        if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            _warn(
                "Porcupine access key not configured.\n"
                "  1. Sign up at https://console.picovoice.ai/ (free tier available).\n"
                "  2. Set the PORCUPINE_ACCESS_KEY environment variable."
            )
            sys.exit(1)

        keywords = ww_cfg.get("keywords", ["jarvis"])
        sensitivity = float(ww_cfg.get("sensitivity", 0.5))
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 120-145

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python -m pytest voice-assistant/tests -v

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — playground/tests/test_app.py

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python -m pytest playground/tests

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/tests/README.md

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:16
-------
| `tests/test_commands.py` | `CommandParser`, `build_app_commands`, `build_window_commands`, `build_terminal_commands`, `_open_app`, `_get_monitors`, `swap_monitors` |
| `tests/test_speech.py` | `SpeechRecognizer` (stubbed Whisper / PyAudio) |
| `tests/test_dry_run.py` | Dry-run mode: `CommandParser(dry_run=True)` for every command group, macros, unknown phrases, and `--text --dry-run` end-to-end via subprocess |
| `tests/bob/test_bugs.py` | Regression tests for all B-xx bugs (T3 baseline; xfail markers removed after T4 fixes) |
=======
| `tests/test_commands.py` | `CommandParser`, `build_app_commands`, `build_window_commands`, `build_terminal_commands`, `_open_app`, `_get_monitors`, `swap_monitors` |
| `tests/test_speech.py` | `SpeechRecognizer` (stubbed Whisper / PyAudio) |
| `tests/test_dry_run.py` | Dry-run mode: `CommandParser(dry_run=True)` for every command group, macros, unknown phrases, and `--text --dry-run` end-to-end via subprocess |
| `tests/test_safety.py` | Security & safety tests (S-01 to S-09): command injection prevention, confirmation prompt, transcript redaction, env var access key, pinned dependencies |
| `tests/bob/test_bugs.py` | Regression tests for all B-xx bugs (T3 baseline; xfail markers removed after T4 fixes) |
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — docs/bob-sessions/README.md

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — docs/bob-sessions

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-50

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — docs/bob-sessions/07-safety-layer.md

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:5
-------
| Session | Task | Mode | Result |
|---|---|---|---|
=======
| Session | Task | Mode | Result |
|---|---|---|---|
| [07-safety-layer.md](07-safety-layer.md) | T7: Safety layer | 🛠️ SD Developer | ✅ 92 passed |
>>>>>>> REPLACE

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python -m pytest tests -v

### 🤖 Assistant

The security and safety findings from [`docs/baseline/security-audit.md`](../baseline/security-audit.md#L1) have been addressed and validated with automated tests.

---

### Key Changes by Finding

| ID | Severity | Location | Summary of Fix |
|---|---|---|---|
| **S-01** | Critical | [`commands/terminal.py:55-63`](../../voice-assistant/commands/terminal.py#L55) | **AppleScript Injection:** Passed command securely as an argument vector (`argv`) via `osascript -e 'on run argv...' -- <command>` instead of raw string interpolation. |
| **S-02** | Critical | [`commands/terminal.py:50`](../../voice-assistant/commands/terminal.py#L50), [`commands/terminal.py:109`](../../voice-assistant/commands/terminal.py#L109) | **Windows cmd & Background `shell=True`:** Replaced `shell=True` with argument lists: `["cmd", "/K", command]` for Windows terminals and `shlex.split()` for background executions. |
| **S-03** | High | [`commands/apps.py:50-65`](../../voice-assistant/commands/apps.py#L50) | **Application Launch `shell=True`:** Switched fallback execution on Windows, macOS, and Linux to use `shlex.split(app_path)` without `shell=True`. |
| **S-04** | High | [`commands/__init__.py:132-137`](../../voice-assistant/commands/__init__.py#L132), [`main.py:133-146`](../../voice-assistant/main.py#L133), [`main.py:204-211`](../../voice-assistant/main.py#L204) | **Destructive Command Confirmation:** Introduced `confirm_destructive` option in `config.yaml`. Added prompt-based confirmation in text mode (`_text_confirm`) and speech confirmation in voice mode (`_voice_confirm`), while skipping confirmation in `dry_run` mode. |
| **S-05** | High | [`speech/__init__.py:231-234`](../../voice-assistant/speech/__init__.py#L231), [`main.py:246-256`](../../voice-assistant/main.py#L246) | **Transcript Log Redaction:** Redacted spoken transcripts in `INFO` logs; full transcripts are now logged only at `DEBUG` level. |
| **S-06** | Medium | [`main.py:196-206`](../../voice-assistant/main.py#L196) | **Porcupine Access Key:** Configured runtime to prioritize the `PORCUPINE_ACCESS_KEY` environment variable. |
| **S-07** | Medium | [`requirements.txt:1-24`](../../voice-assistant/requirements.txt#L1) | **Unpinned Dependencies:** Pinned all package dependencies with exact versions (`==`). |
| **S-08** | Medium | [`commands/__init__.py:76-83`](../../voice-assistant/commands/__init__.py#L76) | **Macro Safety:** Tagged macros under destructive command classification to prevent unauthorized execution of multi-step shell commands. |
| **S-09** | Medium | [`commands/terminal.py:70`](../../voice-assistant/commands/terminal.py#L70) | **Linux Terminal Injection:** Passed shell commands as positional parameters `$0` to `bash -c` rather than interpolating strings. |

---

### Test Validation

Added comprehensive test cases in [`voice-assistant/tests/test_safety.py`](../../voice-assistant/tests/test_safety.py#L1) covering S-01 through S-09:

```bash
$ cd voice-assistant && python -m pytest tests -v
============================== 92 passed in 0.51s ==============================
```
