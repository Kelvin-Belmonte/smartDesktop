# SmartDesktop — Tests

Run the test suite from the `voice-assistant/` directory:

```bash
cd voice-assistant
python -m pytest tests/ -v
```

No microphone, GPU, or API key is required — hardware dependencies are mocked.

## Test files

| File | What it covers |
|---|---|
| `tests/test_commands.py` | `CommandParser`, `build_app_commands`, `build_window_commands`, `build_terminal_commands`, `_open_app`, `_get_monitors`, `swap_monitors` |
| `tests/test_speech.py` | `SpeechRecognizer` (stubbed Whisper / PyAudio) |
| `tests/test_dry_run.py` | Dry-run mode: `CommandParser(dry_run=True)` for every command group, macros, unknown phrases, and `--text --dry-run` end-to-end via subprocess |
| `tests/test_safety.py` | Security & safety tests (S-01 to S-09): command injection prevention, confirmation prompt, transcript redaction, env var access key, pinned dependencies |
| `tests/bob/test_bugs.py` | Regression tests for all B-xx bugs (T3 baseline; xfail markers removed after T4 fixes) |

## Dry-run and text mode (T5)

`CommandParser` accepts a `dry_run=True` flag. When set, every handler returns `True` without
performing any OS action. The builders (`build_app_commands`, `build_window_commands`,
`build_terminal_commands`) propagate the flag to each handler closure.

`python main.py --text` reads commands from stdin line by line; `--dry-run` suppresses all OS
actions. Audio and ML libraries are not imported in text mode, so it works without `pyaudio`,
`pvporcupine`, or `faster-whisper` installed.
