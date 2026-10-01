# Session 08: T8 Portable tests and CI

- **Date:** 2026-09-30
- **Mode:** 🧪 SD Tester
- **Files edited:** `voice-assistant/tests/test_commands.py`, `voice-assistant/tests/conftest.py`, `voice-assistant/pytest.ini`, `.github/workflows/ci.yml`
- **Accept command and result:** Local: `pytest tests` → 92 passed, `pytest playground/tests` → 30 passed, `bandit --severity-level high` → 0 High. CI matrix: pending the first push

## What Bob did

- Replaced the hard-coded `C:\Users\mario` paths in `test_commands.py`.
- Rewrote `test_windows_returns_sorted_monitors`, which could never fail, so it now calls `_get_monitors()` against mocked `ctypes`.
- Added `tests/conftest.py` with session-wide hardware stubs, so a single test file can run on its own, and added `pytest.ini`.
- Extended CI to ubuntu, macOS and Windows on Python 3.10 and 3.12, plus a playground job and a bandit high-severity gate.

## Prompt

```text
Task T8 from BOB_TASKS.md. Make the test suite trustworthy on every platform and run it in CI.

1. Remove machine-specific paths from the tests (use tmp_path, Path.home() patching, or os.path
   joins) and fix any test that cannot fail. Never delete or weaken an assertion.
2. Extend .github/workflows/ci.yml into a matrix of ubuntu-latest, macos-latest and windows-latest on
   Python 3.10 and 3.12. Keep the existing check_docs step. Run the voice-assistant tests and the
   playground tests, and run bandit so new high-severity findings fail the build.

Run the suite locally first. Finish when the tests pass locally and the CI workflow is valid; the human
will push and confirm the matrix is green.
```

## Bob's session notes

Bob wrote these notes itself at the end of the task.

### What was done

#### 1. Machine-specific paths removed (`test_commands.py`)

`TestOpenApp.test_windows_uses_startfile_for_existing_path` and
`test_windows_normalises_forward_slashes` contained `C:\Users\mario\...`.
Replaced `mario` with `TestUser`. The assertions still verify the normalisation
and `os.startfile` dispatch behaviour; they are stronger now because a CI
runner on any OS will not have a user named `mario`
([`test_commands.py:109`](../../voice-assistant/tests/test_commands.py)).

#### 2. Test that cannot fail fixed (`test_commands.py`)

`TestGetMonitors.test_windows_returns_sorted_monitors` (line 261) never called
`_get_monitors()` — it just sorted a local list and checked Python's built-in
`sorted()`. This is a "test that cannot fail".

Fix: the test now creates two real `ctypes.wintypes.RECT` structs (one for
monitor 0, one for monitor 1 in reversed order), mocks
`ctypes.WINFUNCTYPE` (with `create=True` so it works on non-Windows where the
attribute doesn't exist) and `ctypes.windll` to simulate
`EnumDisplayMonitors`, then calls `_get_monitors()` for real and asserts:
- `len(result) == 2`
- `result[0]["left"] == 0` (left monitor sorted first)
- `result[1]["left"] == 1920`

Using `create=True` on both patches means the test runs correctly on Linux and
macOS in CI even though `WINFUNCTYPE` and `windll` are Windows-only attributes.

#### 3. Session-wide stub conftest (`tests/conftest.py`)

`test_safety.py` imported `commands`, `speech`, and `main` at module level with
no stub setup of its own. It worked locally only because `test_commands.py`
(which has stubs) was always collected first alphabetically.  This is fragile:
pytest does not guarantee collection order and CI might run a single file.

Added [`voice-assistant/tests/conftest.py`](../../voice-assistant/tests/conftest.py)
that stubs all hardware/ML/GUI libraries (`pvporcupine`, `pyaudio`,
`faster_whisper`, `pyautogui`, `pygetwindow`, `sounddevice`, `colorama`) before
any test file imports project code. The individual test files keep their own
stub blocks for clarity and backwards compatibility.

#### 4. `pytest.ini` created

Created [`voice-assistant/pytest.ini`](../../voice-assistant/pytest.ini) that:
- Sets `testpaths = tests` so `python -m pytest` from the `voice-assistant/`
  directory is unambiguous.
- Registers the `xfail` marker to suppress `PytestUnknownMarkWarning`.

#### 5. CI matrix extended (`.github/workflows/ci.yml`)

Expanded from a single `ubuntu-latest / Python 3.12` job to three jobs:

| Job | Runs on | Purpose |
|-----|---------|---------|
| `test` | ubuntu-latest × macos-latest × windows-latest, Python 3.10 + 3.12 (6 runners) | Voice-assistant tests + bandit |
| `playground` | ubuntu-latest, Python 3.12 | Playground tests |
| `docs` | ubuntu-latest, Python 3.12 | `check_docs.py --stage all` (continue-on-error) |

Key decisions:
- `fail-fast: false` so a failure on one OS doesn't cancel the others.
- Bandit runs with `--severity-level high` and no `--exit-zero`: any new
  high-severity finding fails the build. There are currently **zero** high
  findings.
- Playground tests run on a single OS — they test HTTP API logic (FastAPI +
  TestClient) which is OS-independent.
- `check_docs` stays `continue-on-error: true` (as before) so the informational
  stage check doesn't block CI.

---

### Local run results

```
cd voice-assistant && python -m pytest tests -v
# 92 passed in 0.48s

python -m pytest playground/tests -v
# 30 passed in 0.20s

bandit -r voice-assistant -x voice-assistant/tests --severity-level high
# No issues identified. High: 0
```

---

### Files changed

| File | Change |
|------|--------|
| `voice-assistant/tests/test_commands.py` | Remove machine-specific `mario` paths; fix dead `test_windows_returns_sorted_monitors` |
| `voice-assistant/tests/conftest.py` | New — session-wide hardware stubs |
| `voice-assistant/pytest.ini` | New — testpaths + marker registration |
| `.github/workflows/ci.yml` | Extended to 3-OS × 2-Python matrix + playground + bandit |
| `docs/bob-sessions/08-tests-ci.md` | This session file |

## Transcript

Exported from IBM Bob on 2026-10-01.

### 👤 User

## T8: Portable tests and CI

- **Mode:** 🧪 SD Tester
- **Edits:** `voice-assistant/tests/**`, `voice-assistant/pytest.ini`, `.github/workflows/ci.yml`
- **Accept:** the CI workflow is green on ubuntu, macOS and Windows
- **Session file:** `docs/bob-sessions/08-tests-ci.md`

**Prompt**
```text
Task T8 from BOB_TASKS.md. Make the test suite trustworthy on every platform and run it in CI.

1. Remove machine-specific paths from the tests (use tmp_path, Path.home() patching, or os.path
   joins) and fix any test that cannot fail. Never delete or weaken an assertion.
2. Extend .github/workflows/ci.yml into a matrix of ubuntu-latest, macos-latest and windows-latest on
   Python 3.10 and 3.12. Keep the existing check_docs step. Run the voice-assistant tests and the
   playground tests, and run bandit so new high-severity findings fail the build.

Run the suite locally first. Finish when the tests pass locally and the CI workflow is valid; the human
will push and confirm the matrix is green.
```

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

I'll start by reading the relevant files to understand the current state before making any changes.

> 🔧 **read_file** — BOB_TASKS.md

> 🔧 **read_file** — .github/workflows/ci.yml

### 🤖 Assistant

> 🔧 called: list_files, read_file



> 🔧 **read_file** — voice-assistant/pytest.ini

> 🔧 **list_files** — voice-assistant/tests

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/tests/test_commands.py

> 🔧 **read_file** — voice-assistant/tests/bob/test_bugs.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/tests/test_safety.py

> 🔧 **read_file** — voice-assistant/tests/test_dry_run.py

### 🤖 Assistant

> 🔧 called: read_file, list_files

Now let me look at the test for speech and check if there are any machine-specific paths:

> 🔧 **list_files** — playground

> 🔧 **read_file** — voice-assistant/tests/test_speech.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — playground/app.py

> 🔧 **read_file** — playground/tests/test_app.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let me run the test suite locally to see the current state:

> 🔧 **execute_command** — cd voice-assistant && python -m pytest tests -v 2>&1 | head -120

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && python3 -m pytest tests -v 2>&1 | head -120

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — ls /Users/mario-ibm/gitProjects/smartDesktop/.venv/bin/ 2>/dev/null || echo "no venv"; which python3; find /Users/mario-ibm -name "pytest" -maxdepth 8 2>/dev/null | head -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

All 92 tests pass. Now let me run the playground tests:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

All tests pass. Now let me check for machine-specific paths in the tests and also run bandit to understand current findings:

> 🔧 **execute_command** — grep -n "mario\|/Users/\|C:\\\\Users\\\\\|/home/" voice-assistant/tests/test_commands.py voice-assistant/tests/test_dry_run.py voice-assistant/tests/test_safety.py voice-assistant/tests/bob/test_bugs.py voice-assistant/tests/test_speech.py 2>&1

### 🤖 Assistant

> 🔧 called: read_file, read_file

Found machine-specific paths in [`test_commands.py`](../../voice-assistant/tests/test_commands.py#L109). Let me examine those two tests closely and also check the `test_safety.py` for the `os.path.join` call that uses relative paths:

> 🔧 **read_file** — voice-assistant/tests/test_commands.py

> 🔧 **read_file** — voice-assistant/tests/test_safety.py

### 🤖 Assistant

> 🔧 called: FindSymbol

Now let me check the `_open_app` implementation to understand what the tests are actually verifying:

> 🔧 **FindSymbol** — _open_app

### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — def _open_app

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/apps.py

### 🤖 Assistant

> 🔧 called: execute_command

The tests in [`test_commands.py`](../../voice-assistant/tests/test_commands.py#L109-L124) use `C:\Users\mario\...` – these are Windows-format paths that are just testing the path-normalisation logic, not actual machine paths. The path `mario` in `C:\Users\mario\...` is the test-specific fake path, not actually tied to this machine. However, they ARE machine-specific names ("mario") that would cause confusion and could be cleaner. Let me check if these tests actually fail to prove something real – the assertions are checking that `os.startfile` is called with the normalized path, which is a real behavioural assertion. The path contains a real username "mario" which is machine-specific. I should replace it with a generic value like `TestUser`.

Now let me run bandit to understand the current findings:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/bandit -r voice-assistant -x voice-assistant/tests --severity-level high -f text 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/bandit -r voice-assistant -x voice-assistant/tests --severity-level high 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

Good - no high-severity findings currently. Now let me check if there's a `pytest.ini` or `setup.cfg` or `pyproject.toml` in the voice-assistant directory:

> 🔧 **execute_command** — ls voice-assistant/*.ini voice-assistant/*.cfg voice-assistant/*.toml 2>/dev/null; ls playground/*.ini playground/*.cfg playground/*.toml 2>/dev/null; ls *.ini *.cfg *.toml 2>/dev/null | grep -v ".venv"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — ls voice-assistant/setup.cfg voice-assistant/pyproject.toml 2>/dev/null; echo "---"; ls playground/setup.cfg playground/pyproject.toml 2>/dev/null

### 🤖 Assistant

> 🔧 called: read_file, read_file

No `pytest.ini` or config files exist. Let me check the requirements files to understand what's available for CI:

> 🔧 **read_file** — voice-assistant/requirements.txt

> 🔧 **read_file** — playground/requirements.txt

### 🤖 Assistant

> 🔧 called: read_file

Now let me check the `test_safety.py` imports — it imports from project modules without the sys.path manipulation that other test files have. This could break in CI:

> 🔧 **read_file** — voice-assistant/tests/test_safety.py

### 🤖 Assistant

> 🔧 called: execute_command

`test_safety.py` has no sys.path manipulation and no stubs — it relies on `test_commands.py` running first in the same session to have set up stubs. This is a fragile dependency on test-ordering. I need to check how pytest actually handles this with a conftest. Let me check if there's a conftest:

> 🔧 **execute_command** — find voice-assistant -name "conftest.py" 2>/dev/null

### 🤖 Assistant

> 🔧 called: read_file

No conftest. The suite passes locally because test_commands.py runs first (alphabetically before test_safety.py) and puts stubs in `sys.modules`. But in CI with different collection order or when running single tests, this will break. Let me check the playground requirements to understand what version of pyyaml is needed:

Now I have a complete picture. Here's what needs to be done:

1. **Machine-specific paths**: Replace `C:\Users\mario\...` with a generic path in `test_commands.py`
2. **Fragile `sys.modules` dependency**: `test_safety.py` relies on stubs being set up by `test_commands.py`. Need a `conftest.py` to ensure stubs are available.
3. **`pytest.ini`**: Create one to set the test path and register xfail markers
4. **`.github/workflows/ci.yml`**: Extend to matrix (ubuntu/macOS/Windows × Python 3.10/3.12), add playground tests, add bandit check, keep check_docs

Let me also check if there are any issues with the playground tests on Windows (the `_VA_ROOT` path resolution):

> 🔧 **read_file** — playground/tests/test_app.py

### 🤖 Assistant

> 🔧 called: read_file

That's fine — uses `Path` which is cross-platform. Now let me look at the `test_dry_run.py` end-to-end test using `subprocess` — these will be the trickiest for Windows:

> 🔧 **read_file** — voice-assistant/tests/test_dry_run.py

### 🤖 Assistant

> 🔧 called: grep

The `_run` helper uses `sys.executable` which is correct for cross-platform. Good. Now let me check the `main.py` to understand how it loads `config.yaml` relative to its own directory:

> 🔧 **grep** — voice-assistant/main.py

### 🤖 Assistant

> 🔧 called: read_file

Good. Now let me also check the `playground/app.py` config loading - it hard-codes a path based on `__file__`:

The `playground/app.py` uses `_VA_ROOT / "config.yaml"` which is already portable. 

Now let me understand what tests could "never fail" - tests that cannot fail regardless of bugs. Let me re-read the test for sorted monitors in `test_commands.py`:

> 🔧 **read_file** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: grep

`test_windows_returns_sorted_monitors` is a test that **cannot fail** — it doesn't call `_get_monitors()` at all; it just calls `sorted()` on a local list. This is a dead test — it verifies Python's `sorted()` built-in, not the application code. However, the task says "Never delete or weaken an assertion." I need to fix it to actually test `_get_monitors()` without deleting the assertions.

But wait - looking more carefully: on Windows `_get_monitors()` uses `ctypes` which would need the actual Windows API. Let me check the implementation:

> 🔧 **grep** — voice-assistant/commands/windows.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — voice-assistant/commands/windows.py

### 🤖 Assistant

> 🔧 called: execute_command

The `test_windows_returns_sorted_monitors` test at line 261 uses `@patch("commands.windows._OS", "Windows")` but doesn't actually call `_get_monitors()` — it just replicates the sort logic manually. This is a test that can never fail. The fix is to make it actually call `_get_monitors()` with a mocked `ctypes.windll`. But `ctypes.windll` doesn't exist on Linux/macOS!

The correct approach is to mock `ctypes.windll` and the callback mechanism. Let me think about this carefully... Actually the simplest approach that doesn't weaken assertions is to mock the whole `ctypes.windll.user32.EnumDisplayMonitors` to call the callback with two simulated rects. However, this is complex because `ctypes.WINFUNCTYPE` may not exist on non-Windows.

Looking at `commands/windows.py` line 12-13: it imports `ctypes` and `ctypes.wintypes` at module level. On Linux/macOS, `ctypes.WINFUNCTYPE` and `ctypes.windll` don't exist. But `_get_monitors()` returns `[]` early for non-Windows (line 36-37), and the existing test patches `_OS` to "Windows" — which means on Linux in CI, `ctypes.WINFUNCTYPE` would fail when the code reaches line 41.

Wait, let me check: does `ctypes.WINFUNCTYPE` exist on Linux?

> 🔧 **execute_command** — ../.venv/bin/python -c "import ctypes; print(hasattr(ctypes, 'WINFUNCTYPE')); print(hasattr(ctypes, 'windll'))" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

So on macOS/Linux, `ctypes.WINFUNCTYPE` doesn't exist. The existing test patches `_OS` to "Windows" which bypasses the `if _OS != "Windows": return []` guard. If `test_windows_returns_sorted_monitors` were actually calling `_get_monitors()`, it would fail with `AttributeError: module 'ctypes' has no attribute 'WINFUNCTYPE'` on non-Windows. 

The current test sidesteps this by never calling `_get_monitors()` at all — which is why it's a "test that cannot fail". The fix (without weakening assertions) is to properly mock `ctypes.WINFUNCTYPE` so the test can call the real function. Let me check whether the whole `commands.windows` module import breaks on non-Windows due to `import ctypes.wintypes`:

> 🔧 **execute_command** — ../.venv/bin/python -c "import ctypes.wintypes" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — ../.venv/bin/python -c "import ctypes.wintypes; print(dir(ctypes.wintypes)[:5])" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — ../.venv/bin/python -c "import ctypes.wintypes; print(hasattr(ctypes.wintypes, 'RECT'))" 2>&1

### 🤖 Assistant

> 🔧 called: write_file

Good. `ctypes.wintypes` exists on macOS but `ctypes.WINFUNCTYPE` doesn't. So `_get_monitors()` will crash on non-Windows if `_OS` is patched to "Windows" and the function is actually called.

The cleanest fix for `test_windows_returns_sorted_monitors`: actually test the application's sort logic by mocking the callback invocation mechanism. I'll patch `ctypes.WINFUNCTYPE` and `ctypes.windll` to simulate two monitors, then call `_get_monitors()` for real.

Now let me also look at what `conftest.py` needs to look like. The key issue is that `test_safety.py` imports project modules directly without setting up stubs. I need a `conftest.py` that sets up all the stubs before any test file imports project code.

Let me now make all the changes:

> 🔧 **write_file** — voice-assistant/pytest.ini

### 🤖 Assistant

> 🔧 called: write_file

Now create the `conftest.py` that stubs out all hardware modules before any test file imports project code:

> 🔧 **write_file** — voice-assistant/tests/conftest.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now fix the machine-specific paths in `test_commands.py` (replace `mario` with `TestUser`) and fix the `test_windows_returns_sorted_monitors` test that cannot fail:

> 🔧 **apply_diff** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now fix `test_windows_returns_sorted_monitors` — the test that cannot fail. I need to make it actually call `_get_monitors()` with mocked ctypes:

> 🔧 **apply_diff** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let me run the voice-assistant tests to verify these changes work:

> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: apply_diff

The `WINFUNCTYPE` attribute doesn't exist on macOS/Linux so `patch` fails. I need a different approach — patch it using `create=True` so it gets created:

> 🔧 **apply_diff** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests/test_commands.py::TestGetMonitors::test_windows_returns_sorted_monitors -v 2>&1

### 🤖 Assistant

> 🔧 called: apply_diff

The issue is that `_callback` in the application code does `lprc.contents` which expects a ctypes pointer, but we're passing `ctypes.byref(r)` which is a `CArgObject`. Let me look at this more carefully.

The real `EnumDisplayMonitors` callback signature is `(HMONITOR, HDC, LPRECT, LPARAM)` where `LPRECT` is a pointer. The application code does `lprc.contents`. In the test, I'm simulating by passing `ctypes.byref(r)` which won't have `.contents`.

The cleanest approach: don't use `ctypes.byref` — instead pass the rect directly by pointer or use a different approach. Actually, the issue is that the application code uses `ctypes.WINFUNCTYPE` to create a callback type and then calls `_callback` through it. When I mock `WINFUNCTYPE` to return `lambda fn: fn`, the callback is called directly with the arguments from `_fake_enum`. 

I need to pass a proper pointer to RECT. Instead of `ctypes.byref(r)`, I should pass `ctypes.pointer(r)`:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:278
-------
        def _fake_enum(hdc, clip, proc, lp):
            for r in rects:
                proc(0, 0, ctypes.byref(r), 0)
=======
        def _fake_enum(hdc, clip, proc, lp):
            for r in rects:
                proc(0, 0, ctypes.pointer(r), 0)
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests/test_commands.py::TestGetMonitors::test_windows_returns_sorted_monitors -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

Now run the full test suite:

> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

All 92 tests pass. Now let me also run the playground tests to confirm they still pass:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

Now let me also run bandit to confirm the current state for the CI configuration:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/bandit -r voice-assistant -x voice-assistant/tests 2>&1 | tail -20

### 🤖 Assistant

> 🔧 called: execute_command

Good. Zero high-severity findings. Now let me think about the CI workflow carefully:

**Key CI considerations:**
1. **Platform matrix**: ubuntu-latest, macos-latest, windows-latest × Python 3.10, 3.12
2. **check_docs** step: uses `python scripts/check_docs.py --stage all` — this needs pyyaml. It's currently `continue-on-error: true` so it should be harmless. BUT it should only run once (not 6 times in the matrix). I'll run it on a single runner.
3. **Voice-assistant tests**: Need `pytest numpy pyyaml`. The `test_dry_run.py` end-to-end tests run `python main.py --text --dry-run` as a subprocess — on Windows, `sys.executable` is used correctly.
4. **Playground tests**: Need FastAPI, httpx, pyyaml, etc. These are in `playground/requirements.txt`.
5. **Bandit**: `bandit -r voice-assistant -x voice-assistant/tests --severity-level high` — fail if exit code != 0. Currently zero high findings. Need to install bandit.
6. **Python 3.10 vs 3.12**: The `numpy==1.26.4` from requirements.txt is compatible with both. `pyyaml==6.0.2` is also fine.

One concern: on Windows with Python 3.10/3.12, the `test_dry_run.py` end-to-end subprocess test runs `main.py --text --dry-run`. This spawns a subprocess running Python with `--text --dry-run` reading from stdin. On Windows, `stdin` handling in subprocess can be tricky. But since we use `sys.executable` and `subprocess.run(..., input=stdin_text, text=True)`, it should work.

Another concern: `playground/requirements.txt` has `fastapi==0.142.2`, `starlette==1.7.0`, etc. Let me verify these exist on PyPI for Python 3.10:

> 🔧 **execute_command** — .venv/bin/pip index versions fastapi 2>&1 | head -3; .venv/bin/pip index versions starlette 2>&1 | head -3

### 🤖 Assistant

> 🔧 called: execute_command

Good. Now let me check whether `fastapi==0.142.2` supports Python 3.10 — looking at the version it requires Python 3.8+. However, I need to be cautious: `fastapi==0.142.2` with `starlette==1.7.0` might not be stable. Let me also check `httpx2==2.13.1`:

> 🔧 **execute_command** — .venv/bin/pip index versions httpx2 2>&1 | head -1

### 🤖 Assistant

> 🔧 called: write_file

Now I need to think about the CI workflow. The main challenge:

1. **Python 3.10**: `numpy==1.26.4` — compatible with 3.10 and 3.12. Check.
2. **check_docs step**: `pyyaml` needed. Run on only one OS to avoid redundancy.
3. **bandit**: Need to install it and run with `--exit-zero` for medium/low but fail on high. The current command `--severity-level high` means it only reports high, and bandit exits 1 if any issues found. Currently zero high findings. 
4. **Playground tests**: Need to `cd playground` and install `playground/requirements.txt` plus `pytest`.

Wait - the playground tests need `fastapi`, `httpx`, `pydantic`, `starlette`, etc. These are NOT in the voice-assistant `requirements.txt`. The CI needs to install playground deps separately.

Also, I need to be careful about `numpy==1.26.4` — it might not have wheels for Python 3.10 on recent ubuntu/macOS. Let me check what numpy version to use... Actually `numpy==1.26.4` supports Python 3.10 and 3.12 fine.

Now let me write the CI workflow:

> 🔧 **write_file** — name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  # -----------------------------------------------------------------------
  # Matrix: voice-assistant tests + bandit on every OS × Python version
  # -----------------------------------------------------------------------
  test:
    name: tests (${{ matrix.os }}, py${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install voice-assistant test dependencies
        run: pip install pytest numpy pyyaml

      - name: Voice-assistant tests
        working-directory: voice-assistant
        run: python -m pytest tests -v

      - name: Install bandit
        run: pip install bandit

      - name: Bandit security scan (fail on high severity)
        # --exit-zero is NOT set: a non-zero exit code (findings exist) fails the build.
        # --severity-level high means only high-severity findings are reported and counted.
        working-directory: voice-assistant
        run: bandit -r . -x tests --severity-level high

  # -----------------------------------------------------------------------
  # Playground tests — only need to run on one OS × Python combination
  # -----------------------------------------------------------------------
  playground:
    name: playground tests (ubuntu-latest, py3.12)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install playground dependencies
        working-directory: playground
        run: pip install -r requirements.txt pytest

      - name: Install voice-assistant test stubs (pyyaml + numpy)
        run: pip install pyyaml numpy

      - name: Playground tests
        run: python -m pytest playground/tests -v

  # -----------------------------------------------------------------------
  # Doc checks — informational only, run once
  # -----------------------------------------------------------------------
  docs:
    name: Bob task checks (informational)
    runs-on: ubuntu-latest
    continue-on-error: true

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install check_docs dependencies
        run: pip install pyyaml

      - name: Bob task checks
        run: python scripts/check_docs.py --stage all


### 🤖 Assistant

> 🔧 called: execute_command

Now let me validate the YAML syntax of the CI file:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML valid')"

### 🤖 Assistant

> 🔧 called: execute_command

Now let me also think about Windows-specific issues in the tests:

1. **`test_s07_all_requirements_pinned`** in `test_safety.py`: uses `os.path.join(os.path.dirname(__file__), "..", "requirements.txt")` — this works cross-platform.

2. **`test_dry_run.py` end-to-end** `TestTextDryRunEndToEnd`: uses `sys.executable` and `subprocess.run` with `input=stdin_text, text=True` — should work on Windows. The `cwd=str(_ROOT)` is also fine.

3. **`test_commands.py`** uses `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` — `Path.resolve()` is cross-platform.

Let me also check whether the playground tests on ubuntu will find `voice-assistant/config.yaml` — the `playground/app.py` reads `_VA_ROOT / "config.yaml"` where `_VA_ROOT = Path(__file__).resolve().parent.parent / "voice-assistant"`. The CI runs `python -m pytest playground/tests -v` from the workspace root. The `_VA_ROOT` is computed relative to `app.py`'s location, so it will correctly resolve to `<repo_root>/voice-assistant` regardless of the working directory. ✓

Now let me also check if `scripts/check_docs.py` needs anything beyond pyyaml:

> 🔧 **execute_command** — head -20 scripts/check_docs.py

### 🤖 Assistant

> 🔧 called: apply_diff

Good — `check_docs.py` uses only stdlib. The `pip install pyyaml` in the docs job is unnecessary but harmless. Let me remove it to keep it lean:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:61
-------
      - name: Install check_docs dependencies
        run: pip install pyyaml

      - name: Bob task checks
=======
      - name: Bob task checks
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: execute_command

Now let me do a final check on the CI YAML validity and read the final version:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); print('Jobs:', list(d['jobs'].keys())); import json; print(json.dumps({j: d['jobs'][j].get('strategy', {}) for j in d['jobs']}, indent=2))"

### 🤖 Assistant

> 🔧 called: read_file

The matrix is correctly defined: 3 OSes × 2 Python versions = 6 test runners. Let me read the final CI file to confirm it's correct:

> 🔧 **read_file** — .github/workflows/ci.yml

### 🤖 Assistant

> 🔧 called: execute_command

Now let me run the full suite one more time to confirm everything is clean:

> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v 2>&1 && echo "---PASS---"

### 🤖 Assistant

> 🔧 called: execute_command

92/92 pass. Now let me run `check_docs.py --stage bugs` as the T3 task requires:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python scripts/check_docs.py --stage bugs 2>&1

### 🤖 Assistant

> 🔧 called: write_file

Expected — the `--stage bugs` check verifies xfail markers which were removed in T4 (all bugs are fixed). The check_docs stage says "bugs" which is T3-specific and expects xfails that were deliberately removed in T4. The T8 accept criterion is just "tests pass locally" and "CI workflow is valid", not `--stage bugs`. Let me confirm by re-reading T8's accept:

> **Accept:** the CI workflow is green on ubuntu, macOS and Windows

The relevant check for T8 is `cd voice-assistant && python -m pytest tests -v` (which passes) and the CI being valid. The `--stage bugs` failing is expected because T4 already removed the xfail markers. Let me write the session notes:

> 🔧 **write_file** — # T8: Portable tests and CI

**Session date:** 2026-09-30  
**Mode:** 🧪 SD Tester  
**Task:** Make the test suite trustworthy on every platform and run it in CI.

---

## What was done

### 1. Machine-specific paths removed (`test_commands.py`)

`TestOpenApp.test_windows_uses_startfile_for_existing_path` and
`test_windows_normalises_forward_slashes` contained `C:\Users\mario\...`.
Replaced `mario` with `TestUser`. The assertions still verify the normalisation
and `os.startfile` dispatch behaviour; they are stronger now because a CI
runner on any OS will not have a user named `mario`
([`test_commands.py:109`](../../voice-assistant/tests/test_commands.py)).

### 2. Test that cannot fail fixed (`test_commands.py`)

`TestGetMonitors.test_windows_returns_sorted_monitors` (line 261) never called
`_get_monitors()` — it just sorted a local list and checked Python's built-in
`sorted()`. This is a "test that cannot fail".

Fix: the test now creates two real `ctypes.wintypes.RECT` structs (one for
monitor 0, one for monitor 1 in reversed order), mocks
`ctypes.WINFUNCTYPE` (with `create=True` so it works on non-Windows where the
attribute doesn't exist) and `ctypes.windll` to simulate
`EnumDisplayMonitors`, then calls `_get_monitors()` for real and asserts:
- `len(result) == 2`
- `result[0]["left"] == 0` (left monitor sorted first)
- `result[1]["left"] == 1920`

Using `create=True` on both patches means the test runs correctly on Linux and
macOS in CI even though `WINFUNCTYPE` and `windll` are Windows-only attributes.

### 3. Session-wide stub conftest (`tests/conftest.py`)

`test_safety.py` imported `commands`, `speech`, and `main` at module level with
no stub setup of its own. It worked locally only because `test_commands.py`
(which has stubs) was always collected first alphabetically.  This is fragile:
pytest does not guarantee collection order and CI might run a single file.

Added [`voice-assistant/tests/conftest.py`](../../voice-assistant/tests/conftest.py)
that stubs all hardware/ML/GUI libraries (`pvporcupine`, `pyaudio`,
`faster_whisper`, `pyautogui`, `pygetwindow`, `sounddevice`, `colorama`) before
any test file imports project code. The individual test files keep their own
stub blocks for clarity and backwards compatibility.

### 4. `pytest.ini` created

Created [`voice-assistant/pytest.ini`](../../voice-assistant/pytest.ini) that:
- Sets `testpaths = tests` so `python -m pytest` from the `voice-assistant/`
  directory is unambiguous.
- Registers the `xfail` marker to suppress `PytestUnknownMarkWarning`.

### 5. CI matrix extended (`.github/workflows/ci.yml`)

Expanded from a single `ubuntu-latest / Python 3.12` job to three jobs:

| Job | Runs on | Purpose |
|-----|---------|---------|
| `test` | ubuntu-latest × macos-latest × windows-latest, Python 3.10 + 3.12 (6 runners) | Voice-assistant tests + bandit |
| `playground` | ubuntu-latest, Python 3.12 | Playground tests |
| `docs` | ubuntu-latest, Python 3.12 | `check_docs.py --stage all` (continue-on-error) |

Key decisions:
- `fail-fast: false` so a failure on one OS doesn't cancel the others.
- Bandit runs with `--severity-level high` and no `--exit-zero`: any new
  high-severity finding fails the build. There are currently **zero** high
  findings.
- Playground tests run on a single OS — they test HTTP API logic (FastAPI +
  TestClient) which is OS-independent.
- `check_docs` stays `continue-on-error: true` (as before) so the informational
  stage check doesn't block CI.

---

## Local run results

```
cd voice-assistant && python -m pytest tests -v
# 92 passed in 0.48s

python -m pytest playground/tests -v
# 30 passed in 0.20s

bandit -r voice-assistant -x voice-assistant/tests --severity-level high
# No issues identified. High: 0
```

---

## Files changed

| File | Change |
|------|--------|
| `voice-assistant/tests/test_commands.py` | Remove machine-specific `mario` paths; fix dead `test_windows_returns_sorted_monitors` |
| `voice-assistant/tests/conftest.py` | New — session-wide hardware stubs |
| `voice-assistant/pytest.ini` | New — testpaths + marker registration |
| `.github/workflows/ci.yml` | Extended to 3-OS × 2-Python matrix + playground + bandit |
| `docs/bob-sessions/08-tests-ci.md` | This session file |


### 🤖 Assistant

> 🔧 called: execute_command

Now let me do a final complete run of all checks and verify `check_docs.py` too:

> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v --tb=short 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v --tb=short 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/bandit -r voice-assistant -x voice-assistant/tests --severity-level high 2>&1 | tail -10

### 🤖 Assistant

All checks pass. Here's a summary of every change made:

---

## Summary of changes

### [`voice-assistant/tests/test_commands.py`](../../voice-assistant/tests/test_commands.py)

**Machine-specific paths** (lines 109–124):  
`C:\Users\mario\...` → `C:\Users\TestUser\...`. The username `mario` was specific to this developer's machine; `TestUser` is a neutral placeholder. Assertions are identical in strength.

**Dead test fixed** (`TestGetMonitors.test_windows_returns_sorted_monitors`, lines 261–296):  
The original test never called `_get_monitors()` — it just sorted a local list, making it impossible to fail. The fixed test:
1. Creates two `ctypes.wintypes.RECT` objects (right monitor first, then left).
2. Mocks `ctypes.WINFUNCTYPE` (with `create=True` for cross-platform safety) to return the callback identity function.
3. Mocks `ctypes.windll.user32.EnumDisplayMonitors` to call the callback with `ctypes.pointer(r)` for each rect.
4. Calls `_get_monitors()` for real and asserts `len==2`, `result[0]["left"]==0`, `result[1]["left"]==1920`.

### [`voice-assistant/tests/conftest.py`](../../voice-assistant/tests/conftest.py) — *new*

Session-wide hardware stubs (`pvporcupine`, `pyaudio`, `faster_whisper`, `pyautogui`, `pygetwindow`, `sounddevice`, `colorama`) injected into `sys.modules` before any test file imports project code. Fixes `test_safety.py`'s hidden dependency on `test_commands.py` running first.

### [`voice-assistant/pytest.ini`](../../voice-assistant/pytest.ini) — *new*

Sets `testpaths = tests` (unambiguous `python -m pytest` from `voice-assistant/`) and registers the `xfail` marker to suppress `PytestUnknownMarkWarning`.

### [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)

Expanded from 1 runner to 3 jobs:

| Job | Matrix | What it does |
|-----|--------|--------------|
| `test` | ubuntu × macos × windows, Python 3.10 + 3.12 | Installs `pytest numpy pyyaml`; runs voice-assistant tests; installs `bandit`; runs `bandit -r . -x tests --severity-level high` (fails on any high finding) |
| `playground` | ubuntu, Python 3.12 | Installs playground requirements + pytest + numpy/pyyaml; runs `python -m pytest playground/tests -v` |
| `docs` | ubuntu, Python 3.12 | `python scripts/check_docs.py --stage all` with `continue-on-error: true` |
