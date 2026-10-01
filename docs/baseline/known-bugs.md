# smartDesktop: known bugs (baseline)

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
