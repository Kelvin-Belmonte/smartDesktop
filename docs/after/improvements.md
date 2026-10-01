# smartDesktop: improvements (after)

Written by IBM Bob in task T9 (🔎 SD Analyst). Compare with `docs/baseline/` (tag `baseline-before`).
Numbers come from running the test suite and static-analysis tools on 2026-09-30.

## Summary

- **7 bugs fixed (B-01–B-07, T4):** macro steps now dispatch through `CommandParser` instead of the
  shell; window commands target the active window; Linux terminal probes for an installed emulator;
  macOS app launch handles binaries-with-arguments; CUDA CPU fallback resets compute type to
  `"int8"`; the wake-word loop survives non-OSError exceptions; config apps no longer silently
  overwrite built-in commands.
- **9 security findings addressed (S-01–S-09, T7):** all `shell=True` subprocess calls replaced
  with argument-list form; AppleScript injection eliminated via `osascript argv` pattern; Linux
  bash injection eliminated with positional argument passing; destructive commands guarded by a
  configurable `confirm_destructive` flag with voice/text confirmation callbacks; transcripts
  redacted at INFO level (full text only at DEBUG); Porcupine key read from
  `PORCUPINE_ACCESS_KEY` environment variable first; all dependencies pinned to exact versions.
- **Dry-run + text mode added (T5):** `python main.py --text` reads commands from stdin without
  importing any audio/ML library; `--dry-run` returns a description of the planned action without
  touching the OS. 23 new tests in `tests/test_dry_run.py`.
- **Web playground added (T6):** `playground/app.py` (FastAPI, always `dry_run=True`) exposes
  `/api/commands`, `/api/parse`, `/health` and serves a self-contained browser UI with Web Speech
  API support. 30 tests in `playground/tests/test_app.py`; `render.yaml` deploys to Render.
- **Test suite expanded and hardened (T3, T8):** test count grew from 45 to 92 (voice-assistant)
  + 30 (playground); machine-specific paths removed; a session-wide `conftest.py` stub prevents
  ordering-dependent import failures; `pytest.ini` makes the test root unambiguous; CI extended to
  a 6-runner matrix (ubuntu-latest × macos-latest × windows-latest, Python 3.10 + 3.12) with
  bandit enforcing zero high-severity findings.

---

## Traceability

| Id | Problem | Fix (`file.py:line`) | Test | Status |
|---|---|---|---|---|
| B-01 | Macro steps ran as OS shell commands instead of assistant commands | `commands/terminal.py` — `build_terminal_commands` gains `parser` param; steps dispatched via `parser.execute(step)` · `commands/__init__.py` — passes `parser=self` | `tests/bob/test_bugs.py::test_b01_macro_executes_assistant_commands` | ✅ Fixed |
| B-02 | Window commands acted on arbitrary first window, not the active one | `commands/windows.py:80` — `_get_window("")` returns `gw.getActiveWindow()` when title is empty | `tests/bob/test_bugs.py::test_b02_window_commands_target_active_window` | ✅ Fixed |
| B-03 | Linux `open terminal` hard-coded `xterm` fallback inconsistently with `_run_in_terminal` | `commands/apps.py:94` — probes `gnome-terminal`, `xterm`, `konsole`, `x-terminal-emulator` via `shutil.which` | `tests/bob/test_bugs.py::test_b03_open_terminal_linux_fallback_consistency` | ✅ Fixed |
| B-04 | macOS `open -a` received app paths with arguments or spaces, causing launch failure | `commands/apps.py:49` — condition tightened: `"/" not in app_path and " " not in app_path` | `tests/bob/test_bugs.py::test_b04_macos_open_app_with_arguments_or_binary` | ✅ Fixed |
| B-05 | CUDA CPU fallback reused GPU `compute_type` (`float16`), unsupported on CPU | `speech/__init__.py:247` — `_reload_on_cpu()` forces `cpu_compute_type = "int8"` | `tests/bob/test_bugs.py::test_b05_cuda_fallback_forces_cpu_compute_type` | ✅ Fixed |
| B-06 | Non-`OSError` exceptions crashed the `WakeWordThread` permanently | `wakeword/__init__.py:109` — `except OSError` widened to `except Exception` | `tests/bob/test_bugs.py::test_b06_wakeword_loop_survives_runtime_errors` | ✅ Fixed |
| B-07 | Config-driven apps silently overwrote built-in commands with the same key | `commands/apps.py:217` — guard added: logs warning and `continue` if phrase already in commands | `tests/bob/test_bugs.py::test_b07_config_apps_does_not_silently_override_builtins` | ✅ Fixed |
| S-01 | AppleScript injection via f-string interpolation in `osascript` call | `commands/terminal.py:55-63` — command passed as `osascript` argv positional argument (`-e 'on run argv...' -- <cmd>`), no string interpolation | `tests/test_safety.py::TestS01AppleScriptInjection` | ✅ Fixed |
| S-02 | Windows `cmd /K` and background `subprocess` used `shell=True` with unvalidated strings | `commands/terminal.py:50`, `commands/terminal.py:109` — list-form `["cmd", "/K", command]`; background uses `shlex.split()` | `tests/test_safety.py::TestS02WindowsCmdInjection` | ✅ Fixed |
| S-03 | `shell=True` with config-controlled app paths on macOS/Linux | `commands/apps.py:50-65` — all `Popen` calls replaced with `shlex.split(app_path)` argument lists | `tests/test_safety.py::TestS03AppLauncherNoShellTrue` | ✅ Fixed |
| S-04 | Destructive commands (`close window`, macros, shell scripts) executed without confirmation | `commands/__init__.py:132-137`, `main.py:133-146`, `main.py:204-211` — `confirm_destructive` flag; `_voice_confirm` / `_text_confirm` callbacks; dry-run skips confirmation | `tests/test_safety.py::TestS04DestructiveCommandConfirmation` | ✅ Fixed |
| S-05 | Full transcripts logged at INFO level to `smartdesktop.log` | `speech/__init__.py:231-234`, `main.py:246-256` — transcript redacted at INFO; full text only at DEBUG | `tests/test_safety.py::TestS05TranscriptRedaction` | ✅ Fixed |
| S-06 | Porcupine key stored as plain string in `config.yaml` | `main.py:196-206` — `PORCUPINE_ACCESS_KEY` env var checked first; config value treated as fallback | `tests/test_safety.py::TestS06PorcupineKeyEnvVar` | ✅ Fixed |
| S-07 | All dependencies unpinned (`>=` lower-bound only) | `requirements.txt:1-24` — every package pinned to exact version with `==` | `tests/test_safety.py::TestS07PinnedDependencies` | ✅ Fixed |
| S-08 | Substring match could silently fire a macro from ambient speech | `commands/__init__.py:76-83` — macro execution guarded under `confirm_destructive` | `tests/test_safety.py::TestS08MacroSecurity` | ✅ Fixed |
| S-09 | Linux `bash -c` injection via unescaped command concatenation | `commands/terminal.py:70` — command passed as positional `$0`: `[term, "--", "bash", "-c", "$0; exec bash", command]` | `tests/test_safety.py::TestS09LinuxBashInjection` | ✅ Fixed |

---

## Before and after

All "before" numbers are taken from `docs/baseline/overview.md` and `docs/baseline/security-audit.md`
(tag `baseline-before`, commit `992e4dc`). All "after" numbers were measured on 2026-09-30.

| Metric | Before | After |
|---|---|---|
| **Voice-assistant test count** | 45 | 92 |
| **Voice-assistant pass rate** | 45/45 (100 %) | 92/92 (100 %) |
| **Playground test count** | 0 | 30 |
| **Playground pass rate** | — | 30/30 (100 %) |
| **`--list-commands` works without audio libraries** | ❌ crashed with `ModuleNotFoundError: pyaudio` | ✅ `--text --dry-run` works; voice path still deferred behind `SmartDesktopAssistant.__init__` |
| **OS support — App launcher** | Windows ✅ macOS ✅ Linux ✅ | Windows ✅ macOS ✅ Linux ✅ (unchanged) |
| **OS support — Window min/max/restore/close** | Windows ✅ macOS ⚠️ Linux ⚠️ (pygetwindow partial) | Windows ✅ macOS ⚠️ Linux ⚠️ (pygetwindow partial — unchanged) |
| **OS support — Snap left / right** | Windows ✅ macOS ❌ Linux ❌ | Windows ✅ macOS ❌ Linux ❌ (unchanged) |
| **OS support — Swap/extend monitors** | Windows ✅ macOS ❌ Linux ❌ | Windows ✅ macOS ❌ Linux ❌ (unchanged) |
| **OS support — Terminal commands** | Windows ✅ macOS ✅ Linux ✅ | Windows ✅ macOS ✅ Linux ✅ (unchanged) |
| **bandit high-severity findings** | 5 (all B602 `shell=True`) | **0** |
| **bandit total findings** | 17 (5 High, 12 Low) | 55 Low, 0 Medium, 0 High (Low findings are informational `B404`/`B603`/`B606`/`B607` import notices — not security risks) |
| **pip-audit vulnerabilities** | 0 (packages were unpinned — future installs could introduce CVEs) | 0 (packages now pinned with `==`) |
| **CI matrix** | 1 runner (ubuntu-latest, Python 3.12) | 6 runners (ubuntu-latest × macos-latest × windows-latest, Python 3.10 + 3.12) + playground job + bandit job |
| **Dry-run mode** | ❌ not present | ✅ `--dry-run` flag; handlers return planned-action description without OS call |
| **Text mode** | ❌ not present | ✅ `--text` reads stdin; no audio/ML imports; works without pyaudio/pvporcupine |
| **Confirmation for destructive commands** | ❌ no confirmation | ✅ `confirm_destructive: true` in `config.yaml`; voice and text confirmation callbacks |
| **Porcupine key handling** | Plain string in `config.yaml` (risk of accidental commit) | `PORCUPINE_ACCESS_KEY` env var checked first; `config.yaml` value still accepted as fallback |
| **Transcript logging** | Full transcript at INFO level, written to `smartdesktop.log` | Redacted at INFO; full text only at DEBUG level |
| **Dependency pinning** | `>=` lower-bound only | Exact `==` versions for all 14 packages |
| **Web playground** | ❌ not present | ✅ FastAPI app (`playground/app.py`); browser UI with Web Speech API; `render.yaml` for Render deployment |
