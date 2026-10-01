# Session 03: T3 Bug hunt and baseline tests

- **Date:** 2026-09-30
- **Mode:** 🧪 SD Tester
- **Files edited:** `docs/baseline/known-bugs.md`, `voice-assistant/tests/bob/test_bugs.py`
- **Accept command and result:** `python scripts/check_docs.py --stage bugs` → OK; `pytest tests -v` → 45 passed, 7 xfailed

## What Bob did

- Proved 7 functional bugs, B-01 to B-07, each with a `xfail(strict=True)` test in `tests/bob/test_bugs.py`.
- B-01: macro steps go to the shell instead of the parser (`terminal.py:228`). B-02: window commands act on `matches[0]`, not the active window (`windows.py:80`).
- B-03 / B-04: the Linux terminal fallback and macOS `_open_app` with arguments (`apps.py:94`, `apps.py:51`).
- B-05: the CPU fallback keeps the GPU compute type (`speech/__init__.py:247`). B-06: non-`OSError` exceptions kill the wake-word thread (`wakeword/__init__.py:89`).
- B-07: config apps silently override built-ins (`apps.py:214`).

## Prompt

```text
Task T3 from BOB_TASKS.md. Find the real functional bugs in smartDesktop at commit 992e4dc and prove
each one with a test, before anything is fixed.

Use docs/baseline/overview.md and docs/baseline/security-audit.md as a starting point. Look closely at:
how macros execute their steps, how config.yaml commands interact with built-in commands of the same
name, which window the window commands act on, each platform branch in commands/apps.py and
commands/terminal.py (Windows, macOS, Linux), the CUDA to CPU fallback in speech/__init__.py, error
handling in the wake-word thread, and the existing tests (tests that cannot fail, machine-specific paths).

For every bug:
1. Add a row B-01, B-02, ... to docs/baseline/known-bugs.md, and explain how to reproduce it.
2. Add a test in voice-assistant/tests/bob/test_bugs.py that asserts the CORRECT behaviour, whose
   name or docstring contains the id, and that is marked
   @pytest.mark.xfail(strict=True, reason="B-xx: <title>"). It must fail today because of the bug.
   Mock every OS side effect (subprocess, os.startfile, platform.system, pyautogui, pygetwindow, ctypes)
   in the same way as tests/test_commands.py.

Only list bugs you proved with a test. Do not change application code. Finish when
`python scripts/check_docs.py --stage bugs` passes and `cd voice-assistant && python -m pytest tests -v`
is green (every B-xx test reported as xfail).
```

## Bob's session notes

Bob wrote these notes itself at the end of the task.

### 1. Summary of Discovered Bugs

7 functional baseline bugs were identified, cataloged in [`docs/baseline/known-bugs.md`](../baseline/known-bugs.md#L1), and backed by strict `xfail` test cases in [`voice-assistant/tests/bob/test_bugs.py`](../../voice-assistant/tests/bob/test_bugs.py#L1):

1. **B-01:** Macro steps execute as terminal shell commands instead of parsing assistant commands ([`commands/terminal.py:228`](../../voice-assistant/commands/terminal.py#L228)).
2. **B-02:** Window command handlers select arbitrary first window in `matches[0]` instead of active window ([`commands/windows.py:80`](../../voice-assistant/commands/windows.py#L80)).
3. **B-03:** Linux terminal open uses unhandled fallback emulator `xterm` instead of supported emulator ([`commands/apps.py:94`](../../voice-assistant/commands/apps.py#L94)).
4. **B-04:** macOS `_open_app()` fails on app paths with arguments or non-`.app` executables ([`commands/apps.py:51`](../../voice-assistant/commands/apps.py#L51)).
5. **B-05:** CUDA fallback at inference re-uses original device's `compute_type` which may fail on CPU ([`speech/__init__.py:247`](../../voice-assistant/speech/__init__.py#L247)).
6. **B-06:** Non-`OSError` exceptions in wake-word detection loop crash the thread unhandled ([`wakeword/__init__.py:89`](../../voice-assistant/wakeword/__init__.py#L89)).
7. **B-07:** Custom app config overwrites built-in commands with same key silently without validation ([`commands/apps.py:214`](../../voice-assistant/commands/apps.py#L214)).

---

### 2. Test Suite Validation

Command:
```bash
pytest tests -v
```
Output:
```text
======================== 45 passed, 7 xfailed in 0.21s =========================
```

Command:
```bash
python scripts/check_docs.py --stage bugs
```
Output:
```text
check_docs --stage bugs: OK
```

## Transcript

Exported from IBM Bob on 2026-10-01.

### 👤 User

## T3: Bug hunt and baseline tests

- **Mode:** 🧪 SD Tester
- **Edits:** `docs/baseline/known-bugs.md`, `voice-assistant/tests/bob/test_bugs.py` (plus an empty `__init__.py` or `conftest.py` there if needed)
- **Accept:** `python scripts/check_docs.py --stage bugs` and `cd voice-assistant && python -m pytest tests -v` (green, with the xfails expected)
- **Session file:** `docs/bob-sessions/03-bug-hunt.md`

**Prompt**
```text
Task T3 from BOB_TASKS.md. Find the real functional bugs in smartDesktop at commit 992e4dc and prove
each one with a test, before anything is fixed.

Use docs/baseline/overview.md and docs/baseline/security-audit.md as a starting point. Look closely at:
how macros execute their steps, how config.yaml commands interact with built-in commands of the same
name, which window the window commands act on, each platform branch in commands/apps.py and
commands/terminal.py (Windows, macOS, Linux), the CUDA to CPU fallback in speech/__init__.py, error
handling in the wake-word thread, and the existing tests (tests that cannot fail, machine-specific paths).

For every bug:
1. Add a row B-01, B-02, ... to docs/baseline/known-bugs.md, and explain how to reproduce it.
2. Add a test in voice-assistant/tests/bob/test_bugs.py that asserts the CORRECT behaviour, whose
   name or docstring contains the id, and that is marked
   @pytest.mark.xfail(strict=True, reason="B-xx: <title>"). It must fail today because of the bug.
   Mock every OS side effect (subprocess, os.startfile, platform.system, pyautogui, pygetwindow, ctypes)
   in the same way as tests/test_commands.py.

Only list bugs you proved with a test. Do not change application code. Finish when
`python scripts/check_docs.py --stage bugs` passes and `cd voice-assistant && python -m pytest tests -v`
is green (every B-xx test reported as xfail).
```

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — scripts/check_docs.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-100

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-150

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — docs/baseline/security-audit.md

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — true

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-120

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 121-250

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-120

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 121-160

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-150

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/terminal.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-225

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/windows.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-200

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 201-260

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/wakeword/__init__.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 1-200

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/config.yaml

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — voice-assistant

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — which python3 && python3 -m pytest tests -v

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — which pytest || find / -name pytest 2>/dev/null || which -a python3

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — voice-assistant

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/python scripts/check_docs.py --stage bugs

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — 250-330

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — # smartDesktop: known bugs (baseline)

Written by IBM Bob in task T3 (🧪 SD Tester), against commit `992e4dc` (tag `baseline-before`).
Each bug has a failing test in `voice-assistant/tests/bob/test_bugs.py`, marked
`@pytest.mark.xfail(strict=True, reason="B-xx: ...")` until task T4 fixes it.

## Bugs

| Id | Title | Location (file.py:line) | Platform | Severity | Test |
|---|---|---|---|---|---|
| B-01 | Macro steps execute as terminal shell commands instead of parsing assistant commands | `commands/terminal.py:228` | All | High | `test_b01_macro_executes_assistant_commands` |
| B-02 | Window command handlers select arbitrary first window instead of active window | `commands/windows.py:80` | Windows | High | `test_b02_window_commands_target_active_window` |
| B-03 | Linux terminal open uses unhandled fallback emulator `xterm` instead of supported emulator | `commands/apps.py:94` | Linux | Medium | `test_b03_open_terminal_linux_fallback_consistency` |
| B-04 | macOS open_app fails on app paths with arguments or non-.app executables | `commands/apps.py:51` | macOS | Medium | `test_b04_macos_open_app_with_arguments_or_binary` |
| B-05 | CUDA fallback at inference re-uses original device's compute_type which may fail on CPU | `speech/__init__.py:247` | All | Medium | `test_b05_cuda_fallback_forces_cpu_compute_type` |
| B-06 | Non-OSError exceptions in wake-word detection loop crash the thread unhandled | `wakeword/__init__.py:89` | All | High | `test_b06_wakeword_loop_survives_runtime_errors` |
| B-07 | Custom app config overwrites built-in commands with same key silently without validation | `commands/apps.py:214` | All | Medium | `test_b07_config_apps_does_not_silently_override_builtins` |

## How to reproduce

### B-01: Macro steps execute as terminal shell commands instead of parsing assistant commands
- **Input / Phrase:** Say `start dev` or `morning routine` configured with macro steps such as `["open chrome", "open discord", "open spotify"]`.
- **Expected behaviour:** The assistant parser should evaluate each step as a voice assistant command (e.g., executing `open_chrome()`, `open_discord()`, `open_spotify()`).
- **Actual behaviour:** `_run_macro()` passes each step string directly to `_run_in_terminal(step)` (`commands/terminal.py:228`), launching a new OS terminal window executing `open chrome` as a shell command (which fails as an unknown shell command).
- **Root cause:** Macros were implemented as sequences of raw shell commands in `commands/terminal.py:225-232` rather than dispatching back through the `CommandParser` or assistant command registry.

### B-02: Window command handlers select arbitrary first window instead of active window
- **Input / Phrase:** Say `minimise window`, `maximise window`, `restore window`, or `close window` with no window title argument while working in an active application.
- **Expected behaviour:** The command should act on the currently focused / active foreground window.
- **Actual behaviour:** `_get_window("")` calls `pygetwindow.getWindowsWithTitle("")` and unconditionally returns `matches[0]` (`commands/windows.py:80`), which is an arbitrary window in the OS window stack (often a background or system window), not `pygetwindow.getActiveWindow()`.
- **Root cause:** `_get_window()` only queries `getWindowsWithTitle(title_fragment)` without checking if `title_fragment` is empty to query `getActiveWindow()`.

### B-03: Linux terminal open uses unhandled fallback emulator `xterm` instead of supported emulator
- **Input / Phrase:** On Linux, say `open terminal` when `x-terminal-emulator` is not in the system dictionary `paths.get(_OS)`.
- **Expected behaviour:** `open_terminal()` should resolve to an available terminal emulator on Linux (such as `x-terminal-emulator`, `gnome-terminal`, or system default), matching `_run_in_terminal()`.
- **Actual behaviour:** `commands/apps.py:94` passes `"xterm"` as default fallback to `_open_app()`, which tries `subprocess.Popen("xterm", shell=True)`. If `xterm` is not installed, it fails silently with an error, whereas `commands/terminal.py:55` checks multiple emulators (`gnome-terminal`, `xterm`, `konsole`, `x-terminal-emulator`).
- **Root cause:** Inconsistent fallback terminal selection between `commands/apps.py:94` and `commands/terminal.py:55`.

### B-04: macOS open_app fails on app paths with arguments or non-.app executables
- **Input / Phrase:** On macOS, configure an app with command arguments or a direct binary path (e.g. `/usr/local/bin/mytool --arg`).
- **Expected behaviour:** `_open_app()` should execute the command or binary properly with its arguments.
- **Actual behaviour:** `commands/apps.py:51` sees `"/" in app_path` and runs `subprocess.Popen(app_path, shell=True)`. But if `app_path` has no slash and does not end in `.app` (e.g. `mytool --arg`), it calls `open -a "mytool --arg"`, which macOS rejects because no application named `"mytool --arg"` exists.
- **Root cause:** `commands/apps.py:49` branches on `app_path.endswith(".app") or "/" not in app_path` to invoke `open -a`, passing arguments inside the application name string.

### B-05: CUDA fallback at inference re-uses original device's compute_type which may fail on CPU
- **Input / Phrase:** Initialize speech recognizer on GPU with `device="cuda"` and `compute_type="float16"`, then encounter a runtime CUDA library failure during `_transcribe()`.
- **Expected behaviour:** `_reload_on_cpu()` should fall back to CPU using a CPU-supported compute type like `"int8"` or `"float32"`.
- **Actual behaviour:** `_reload_on_cpu()` in `speech/__init__.py:247` passes `compute_type=self._compute_type` (which was `"float16"` for GPU). Faster-Whisper on CPU raises an exception because `float16` is not supported on x86/ARM CPUs without specialized instructions.
- **Root cause:** `_reload_on_cpu()` does not reset the compute type to a CPU-compatible default (`int8` or `float32`) when falling back from CUDA.

### B-06: Non-OSError exceptions in wake-word detection loop crash the thread unhandled
- **Input / Phrase:** During wake-word detection, `pvporcupine.process()` or `struct.unpack_from()` raises a `RuntimeError` or `ValueError` (e.g. corrupted audio buffer or Porcupine internal state error).
- **Expected behaviour:** The detection loop should catch the exception, log it, and continue listening or recover without terminating `WakeWordThread`.
- **Actual behaviour:** `_detection_loop()` in `wakeword/__init__.py:88-111` only catches `OSError` around the read loop. Any other exception propagates, terminating `WakeWordThread` and leaving the assistant permanently deaf.
- **Root cause:** Missing exception handling for general exceptions (`Exception`) inside `WakeWordDetector._detection_loop()`.

### B-07: Custom app config overwrites built-in commands with same key silently without validation
- **Input / Phrase:** Config contains `commands.apps: {terminal: "C:/custom/term.exe"}`.
- **Expected behaviour:** The user's custom commands should either register alongside or validate safely without breaking built-in core aliases or clobbering essential voice commands.
- **Actual behaviour:** `build_app_commands()` unconditionally overwrites `commands["open terminal"]` with the custom launcher, completely overriding the built-in system terminal launcher without warning or fallback.
- **Root cause:** `commands/apps.py:214-218` iterates `apps_config` and assigns directly into `commands[phrase]` without checking collision with built-in handlers or providing namespacing.


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — 235

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — 1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — voice-assistant

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — # Session Notes: T3 Bug Hunt and Baseline Tests

**Date:** 2025-05-10
**Mode:** 🧪 SD Tester
**Task:** T3 from `BOB_TASKS.md`
**Acceptance Commands:**
- `python scripts/check_docs.py --stage bugs`
- `cd voice-assistant && python -m pytest tests -v`

---

## 1. Summary of Discovered Bugs

7 functional baseline bugs were identified, cataloged in [`docs/baseline/known-bugs.md`](../baseline/known-bugs.md#L1), and backed by strict `xfail` test cases in [`voice-assistant/tests/bob/test_bugs.py`](../../voice-assistant/tests/bob/test_bugs.py#L1):

1. **B-01:** Macro steps execute as terminal shell commands instead of parsing assistant commands ([`commands/terminal.py:228`](../../voice-assistant/commands/terminal.py#L228)).
2. **B-02:** Window command handlers select arbitrary first window in `matches[0]` instead of active window ([`commands/windows.py:80`](../../voice-assistant/commands/windows.py#L80)).
3. **B-03:** Linux terminal open uses unhandled fallback emulator `xterm` instead of supported emulator ([`commands/apps.py:94`](../../voice-assistant/commands/apps.py#L94)).
4. **B-04:** macOS `_open_app()` fails on app paths with arguments or non-`.app` executables ([`commands/apps.py:51`](../../voice-assistant/commands/apps.py#L51)).
5. **B-05:** CUDA fallback at inference re-uses original device's `compute_type` which may fail on CPU ([`speech/__init__.py:247`](../../voice-assistant/speech/__init__.py#L247)).
6. **B-06:** Non-`OSError` exceptions in wake-word detection loop crash the thread unhandled ([`wakeword/__init__.py:89`](../../voice-assistant/wakeword/__init__.py#L89)).
7. **B-07:** Custom app config overwrites built-in commands with same key silently without validation ([`commands/apps.py:214`](../../voice-assistant/commands/apps.py#L214)).

---

## 2. Test Suite Validation

Command:
```bash
pytest tests -v
```
Output:
```text
======================== 45 passed, 7 xfailed in 0.21s =========================
```

Command:
```bash
python scripts/check_docs.py --stage bugs
```
Output:
```text
check_docs --stage bugs: OK
```


### 🤖 Assistant

Task T3 is complete. The functional bugs at commit `992e4dc` have been documented and backed with repro unit tests with all OS side-effects mocked.

### Summary of Changes

1. **[`docs/baseline/known-bugs.md`](../baseline/known-bugs.md#L1)**:
   - Added table with 7 identified bugs: **B-01** through **B-07**.
   - Added detailed "How to reproduce" sections containing the input phrase, expected behaviour, actual behaviour, and root cause analysis for each defect.

2. **[`voice-assistant/tests/bob/test_bugs.py`](../../voice-assistant/tests/bob/test_bugs.py#L1)** & **[`voice-assistant/tests/bob/__init__.py`](../../voice-assistant/tests/bob/__init__.py#L1)**:
   - Created test suite asserting the correct expected behavior for every B-xx bug.
   - Every test is marked `@pytest.mark.xfail(strict=True, reason="B-xx: ...")` and currently fails against baseline application code.
   - All OS interactions (`subprocess`, `os.startfile`, `pyautogui`, `pygetwindow`, `ctypes`, `pvporcupine`, `faster_whisper`, `pyaudio`) are mocked.

3. **[`docs/bob-sessions/03-bug-hunt.md`](../bob-sessions/03-bug-hunt.md#L1)**:
   - Created session log with findings and test run evidence.

---

### Bug Catalog Summary

- **B-01** ([`commands/terminal.py:228`](../../voice-assistant/commands/terminal.py#L228)): Macro steps execute as terminal shell commands instead of parsing assistant commands.
- **B-02** ([`commands/windows.py:80`](../../voice-assistant/commands/windows.py#L80)): Window command handlers select arbitrary first window (`matches[0]`) instead of the active window (`getActiveWindow()`).
- **B-03** ([`commands/apps.py:94`](../../voice-assistant/commands/apps.py#L94)): Linux terminal launcher falls back to `xterm` rather than probing supported terminal emulators.
- **B-04** ([`commands/apps.py:51`](../../voice-assistant/commands/apps.py#L51)): macOS `_open_app()` invokes `open -a` on app strings with command arguments or raw binary names.
- **B-05** ([`speech/__init__.py:247`](../../voice-assistant/speech/__init__.py#L247)): CUDA fallback at inference re-uses original device's `compute_type` (e.g. `float16`) which fails on CPU.
- **B-06** ([`wakeword/__init__.py:89`](../../voice-assistant/wakeword/__init__.py#L89)): Non-`OSError` exceptions in `WakeWordDetector._detection_loop()` unhandled, terminating the background listener thread.
- **B-07** ([`commands/apps.py:214`](../../voice-assistant/commands/apps.py#L214)): Custom app config overwrites built-in commands with same key silently without validation.

---

### Verification and Acceptance Checks

1. **`python scripts/check_docs.py --stage bugs`**
   ```text
   check_docs --stage bugs: OK
   ```

2. **`cd voice-assistant && python -m pytest tests -v`**
   ```text
   tests/bob/test_bugs.py::test_b01_macro_executes_assistant_commands XFAIL [  1%]
   tests/bob/test_bugs.py::test_b02_window_commands_target_active_window XFAIL [  3%]
   tests/bob/test_bugs.py::test_b03_open_terminal_linux_fallback_consistency XFAIL [  5%]
   tests/bob/test_bugs.py::test_b04_macos_open_app_with_arguments_or_binary XFAIL [  7%]
   tests/bob/test_bugs.py::test_b05_cuda_fallback_forces_cpu_compute_type XFAIL [  9%]
   tests/bob/test_bugs.py::test_b06_wakeword_loop_survives_runtime_errors XFAIL [ 11%]
   tests/bob/test_bugs.py::test_b07_config_apps_does_not_silently_override_builtins XFAIL [ 13%]
   ...
   ======================== 45 passed, 7 xfailed in 0.21s =========================
   ```
