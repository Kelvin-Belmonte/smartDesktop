# Session 06: T6 Feature: web playground

- **Date:** 2026-09-30
- **Mode:** 🛠️ SD Developer
- **Files edited:** `playground/{app.py,static/index.html,requirements.txt,tests/test_app.py,__init__.py}`, `render.yaml`
- **Accept command and result:** `python -m pytest playground/tests` → 30 passed

## What Bob did

- Built a FastAPI app with one module-level `CommandParser(dry_run=True)`. No request can change that flag.
- Added the endpoints `GET /api/commands`, `POST /api/parse`, `GET /health` and `GET /`.
- Wrote a single-file page with a Web Speech API mic button, a platform selector and a searchable catalog.
- Wrote 30 TestClient tests, including `TestNoSubprocessSpawned`, which proves that `Popen` and `run` are never called. Added `render.yaml` for the free Render tier.

## Prompt

```text
Task T6 from BOB_TASKS.md. Build a small web playground so judges can try smartDesktop in the browser.

Create playground/ with:
- app.py: a FastAPI app that imports the voice-assistant CommandParser and ALWAYS runs it with
  dry_run=True (it must be impossible to trigger a real OS action from the server). Endpoints:
  GET /api/commands (the catalog), POST /api/parse {"text": "..."} (the matched command and the planned
  action), GET /health, and GET / serving the static page.
- static/index.html: one self-contained page. Type a phrase (or use the browser's Web Speech API
  microphone button when available), see the matched command, the planned action as JSON, and a
  searchable command list. A platform selector (windows/macos/linux) shows how the action differs.
- requirements.txt (pinned), and tests in playground/tests/test_app.py using FastAPI's TestClient,
  including a test that proves no subprocess is ever spawned.
- render.yaml at the repo root to deploy it as a free Render web service.

Finish when `python -m pytest playground/tests` passes.
```

## Bob's session notes

Bob wrote these notes itself at the end of the task.

### What was built

#### Files created

| File | Purpose |
|---|---|
| `playground/app.py` | FastAPI application — always `dry_run=True` |
| `playground/static/index.html` | Self-contained browser UI with Web Speech API mic support |
| `playground/requirements.txt` | Pinned dependencies |
| `playground/tests/test_app.py` | 30 tests via `TestClient`, including no-subprocess proof |
| `playground/__init__.py` | Makes `playground` a Python package (for Render import path) |
| `playground/tests/__init__.py` | Pytest discovery |
| `render.yaml` | Free Render web service definition |

---

### Design decisions

#### Safety contract (`app.py:52–58`)
`CommandParser` is instantiated exactly once, at module load, with `dry_run=True` hardcoded.
There is no endpoint or parameter that accepts a `dry_run` flag — the parser's dry_run attribute
cannot be overridden by any HTTP request.

#### Hardware stub pattern (`app.py:23–47`)
`pvporcupine`, `pyaudio`, `faster_whisper`, `sounddevice`, `pyautogui`, and `pygetwindow` are
stubbed before the `commands` package is imported, mirroring the pattern in
`voice-assistant/tests/test_commands.py`. This means the playground works without any audio or
ML libraries installed.

#### `/api/parse` response shape
```json
{
  "input": "jarvis open chrome",
  "matched": "open chrome",
  "action": "open -a 'Google Chrome'",
  "platforms": {
    "windows": "start chrome",
    "macos": "open -a 'Google Chrome'",
    "linux": "google-chrome"
  },
  "dry_run": true
}
```
`_PARSER._strip_prefix()` and `_PARSER._match()` are called directly so the matched phrase is
available without executing the handler.

#### Platform notes (`app.py:77–100`)
A static dict maps the most common phrases to per-platform action strings.
Custom project/app commands not in the dict fall back to a sensible generated description.

#### UI (`static/index.html`)
- Single-file, no external CDN dependencies, dark GitHub-style theme.
- Platform selector (Windows / macOS / Linux) filters the catalog and the parse result.
- Web Speech API microphone button appears automatically when the browser supports it.
- Clicking any catalog entry fills the input and fires a parse immediately.

#### `render.yaml`
Free-tier Render web service; `uvicorn` binds to `$PORT` as required by Render.

---

### Test summary

```
30 passed in 0.17 s
```

| Test class | What it proves |
|---|---|
| `TestHealth` | `/health` → 200, `dry_run=true` in payload |
| `TestGetCommands` | Catalog non-empty, has `phrase`+`platforms` keys, contains `open chrome` and `git status` |
| `TestParseCommand` | Known, prefixed, unknown, 400 on empty, platforms present, substring match |
| `TestIndexPage` | Serves HTML with correct content-type and title |
| `TestNoSubprocessSpawned` | `subprocess.Popen` and `subprocess.run` never called across all command groups; `_PARSER.dry_run` is `True` |

---

### Accept command output

```
$ python -m pytest playground/tests -v
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1 ...
collected 30 items

playground/tests/test_app.py::TestHealth::test_health_dry_run_true PASSED
playground/tests/test_app.py::TestHealth::test_health_returns_200 PASSED
playground/tests/test_app.py::TestHealth::test_health_status_ok PASSED
playground/tests/test_app.py::TestGetCommands::test_catalog_nonempty PASSED
playground/tests/test_app.py::TestGetCommands::test_each_entry_has_phrase_and_platforms PASSED
playground/tests/test_app.py::TestGetCommands::test_git_status_present PASSED
playground/tests/test_app.py::TestGetCommands::test_open_chrome_present PASSED
playground/tests/test_app.py::TestGetCommands::test_returns_200 PASSED
playground/tests/test_app.py::TestGetCommands::test_returns_list PASSED
playground/tests/test_app.py::TestParseCommand::test_dry_run_always_true PASSED
playground/tests/test_app.py::TestParseCommand::test_empty_text_returns_400 PASSED
playground/tests/test_app.py::TestParseCommand::test_git_status_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_known_command_matches PASSED
playground/tests/test_app.py::TestParseCommand::test_minimise_window_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_platforms_contain_all_three PASSED
playground/tests/test_app.py::TestParseCommand::test_prefixed_phrase_stripped PASSED
playground/tests/test_app.py::TestParseCommand::test_response_has_input_field PASSED
playground/tests/test_app.py::TestParseCommand::test_response_has_platforms_field_when_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_substring_match PASSED
playground/tests/test_app.py::TestParseCommand::test_unknown_phrase_returns_none PASSED
playground/tests/test_app.py::TestParseCommand::test_whitespace_only_returns_400 PASSED
playground/tests/test_app.py::TestIndexPage::test_index_contains_title PASSED
playground/tests/test_app.py::TestIndexPage::test_index_is_html PASSED
playground/tests/test_app.py::TestIndexPage::test_index_returns_200 PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_app_commands_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_catalog_endpoint_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_parser_dry_run_flag_is_true PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_terminal_commands_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_unknown_phrase_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_window_commands_no_subprocess PASSED

============================== 30 passed in 0.17s ==============================
```

## Transcript

Exported from IBM Bob on 2026-10-01.

### 👤 User

## T6: Feature: web playground

- **Mode:** 🛠️ SD Developer
- **Edits:** `playground/**`, `render.yaml`, `voice-assistant/**` (only if the playground needs an import hook)
- **Accept:** `python -m pytest playground/tests`
- **Session file:** `docs/bob-sessions/06-playground.md`

**Prompt**
```text
Task T6 from BOB_TASKS.md. Build a small web playground so judges can try smartDesktop in the browser.

Create playground/ with:
- app.py: a FastAPI app that imports the voice-assistant CommandParser and ALWAYS runs it with
  dry_run=True (it must be impossible to trigger a real OS action from the server). Endpoints:
  GET /api/commands (the catalog), POST /api/parse {"text": "..."} (the matched command and the planned
  action), GET /health, and GET / serving the static page.
- static/index.html: one self-contained page. Type a phrase (or use the browser's Web Speech API
  microphone button when available), see the matched command, the planned action as JSON, and a
  searchable command list. A platform selector (windows/macos/linux) shows how the action differs.
- requirements.txt (pinned), and tests in playground/tests/test_app.py using FastAPI's TestClient,
  including a test that proves no subprocess is ever spawned.
- render.yaml at the repo root to deploy it as a free Render web service.

Finish when `python -m pytest playground/tests` passes.
```

---

### 🤖 Assistant

> 🔧 called: read_file, list_files

Let me start by reading the relevant files to understand the existing codebase.

> 🔧 **list_files** — voice-assistant

> 🔧 **read_file** — BOB_TASKS.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/main.py

> 🔧 **read_file** — voice-assistant/commands/__init__.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/commands/apps.py

> 🔧 **read_file** — voice-assistant/commands/terminal.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/commands/windows.py

> 🔧 **read_file** — voice-assistant/config.yaml

### 🤖 Assistant

> 🔧 called: read_file, list_files

Now let me look at the existing tests and dry_run implementation to understand the patterns:

> 🔧 **list_files** — voice-assistant/tests

> 🔧 **read_file** — voice-assistant/tests/test_dry_run.py

### 🤖 Assistant

> 🔧 called: glob, glob

Now I have a thorough understanding of the codebase. Let me also check if there's an existing `render.yaml` or `playground/` directory:

> 🔧 **glob** — render.yaml

> 🔧 **glob** — playground/**

### 🤖 Assistant

> 🔧 called: read_file

Good - neither exists yet. Now I understand the full picture. Let me also check what the `parse` endpoint needs to return — the dry_run returns `True` but the task asks for "matched command and the planned action as JSON". I need to understand what structured data the CommandParser can provide:

> 🔧 **read_file** — voice-assistant/tests/test_commands.py

### 🤖 Assistant

> 🔧 called: execute_command

Now I have everything I need. The task requires:
1. `playground/app.py` - FastAPI app with dry_run=True always
2. `playground/static/index.html` - self-contained UI page  
3. `playground/requirements.txt` - pinned deps
4. `playground/tests/test_app.py` - tests including no-subprocess check
5. `render.yaml` - at repo root

The key design choice: the `/api/parse` endpoint needs to return structured data about "the matched command and planned action". Looking at the code, `CommandParser` just returns `True/False` — I need to also return the matched phrase. I'll extend the app to use `_match` and `_strip_prefix` directly to get the matched phrase, then build the action description.

Let me now create all the files:

> 🔧 **execute_command** — mkdir -p playground/tests playground/static

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — playground/app.py

### 🤖 Assistant

> 🔧 called: write_file

Now create the static HTML page:

> 🔧 **write_file** — playground/static/index.html

### 🤖 Assistant

> 🔧 called: execute_command

Now let's check the latest stable versions of FastAPI, uvicorn, httpx, and pydantic:

> 🔧 **execute_command** — pip index versions fastapi 2>/dev/null | head -3; pip index versions uvicorn 2>/dev/null | head -3; pip index versions httpx 2>/dev/null | head -3; pip index versions pydantic 2>/dev/null | head -3; pip index versions python-multipart 2>/dev/null | head -3

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — pip install fastapi uvicorn httpx pydantic 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/pip install fastapi "uvicorn[standard]" httpx pydantic pyyaml 2>&1 | tail -10

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -c "import fastapi; print('fastapi', fastapi.__version__); import uvicorn; print('uvicorn', uvicorn.__version__); import httpx; print('httpx', httpx.__version__); import pydantic; print('pydantic', pydantic.__version__)"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/pip show starlette 2>&1 | grep Version; .venv/bin/pip show anyio 2>&1 | grep Version; .venv/bin/pip show pyyaml 2>&1 | grep Version

### 🤖 Assistant

> 🔧 called: write_file

Now create the pinned requirements.txt for the playground:

> 🔧 **write_file** — # SmartDesktop Playground — pinned dependencies
# Generated for Python 3.10+

fastapi==0.142.2
uvicorn[standard]==0.54.0
httpx==0.28.1
pydantic==2.13.5
pyyaml==6.0.2
starlette==1.7.0
anyio==4.15.1


### 🤖 Assistant

> 🔧 called: execute_command

Now I need to check pyyaml's exact installed version:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/pip show pyyaml | grep Version

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — playground/requirements.txt

### 🤖 Assistant

> 🔧 called: write_file

Now create the test file. The key test is "no subprocess is ever spawned". I'll use `TestClient` from FastAPI:

> 🔧 **write_file** — """
playground/tests/test_app.py

Tests for the SmartDesktop web playground (T6).

Uses FastAPI's TestClient (backed by httpx) — no real server is started.
Every test runs fully offline; no OS actions, no subprocesses.
"""

import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Make the playground package importable
# ---------------------------------------------------------------------------
_PLAYGROUND_ROOT = Path(__file__).resolve().parent.parent
_VA_ROOT = _PLAYGROUND_ROOT.parent / "voice-assistant"

if str(_PLAYGROUND_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLAYGROUND_ROOT))
if str(_VA_ROOT) not in sys.path:
    sys.path.insert(0, str(_VA_ROOT))

# ---------------------------------------------------------------------------
# Stub hardware-only libraries (identical pattern to voice-assistant tests)
# ---------------------------------------------------------------------------

def _stub(name):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return sys.modules[name]


_stub("pvporcupine")
_stub("pyaudio")
sys.modules["pyaudio"].paInt16 = 8        # type: ignore[attr-defined]
sys.modules["pyaudio"].PyAudio = object   # type: ignore[attr-defined]
_stub("faster_whisper").WhisperModel = MagicMock()  # type: ignore
_stub("pyautogui")
_stub("sounddevice")
gw = _stub("pygetwindow")
gw.getWindowsWithTitle = MagicMock(return_value=[])  # type: ignore
gw.getAllWindows = MagicMock(return_value=[])          # type: ignore
gw.getActiveWindow = MagicMock(return_value=None)     # type: ignore

# ---------------------------------------------------------------------------
# Import the app *after* stubs are in place
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient  # noqa: E402

import app as playground_app              # noqa: E402 — playground/app.py

client = TestClient(playground_app.app)


# ===========================================================================
# Health endpoint
# ===========================================================================

class TestHealth(unittest.TestCase):

    def test_health_returns_200(self):
        """GET /health must return HTTP 200."""
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_dry_run_true(self):
        """The health payload must confirm dry_run=True."""
        resp = client.get("/health")
        data = resp.json()
        self.assertTrue(data.get("dry_run"), "health must report dry_run=True")

    def test_health_status_ok(self):
        resp = client.get("/health")
        self.assertEqual(resp.json()["status"], "ok")


# ===========================================================================
# GET /api/commands
# ===========================================================================

class TestGetCommands(unittest.TestCase):

    def test_returns_200(self):
        resp = client.get("/api/commands")
        self.assertEqual(resp.status_code, 200)

    def test_returns_list(self):
        resp = client.get("/api/commands")
        self.assertIsInstance(resp.json(), list)

    def test_catalog_nonempty(self):
        resp = client.get("/api/commands")
        self.assertGreater(len(resp.json()), 5)

    def test_each_entry_has_phrase_and_platforms(self):
        resp = client.get("/api/commands")
        for entry in resp.json():
            self.assertIn("phrase", entry, f"Entry missing 'phrase': {entry}")
            self.assertIn("platforms", entry, f"Entry missing 'platforms': {entry}")

    def test_open_chrome_present(self):
        resp = client.get("/api/commands")
        phrases = [e["phrase"] for e in resp.json()]
        self.assertIn("open chrome", phrases)

    def test_git_status_present(self):
        resp = client.get("/api/commands")
        phrases = [e["phrase"] for e in resp.json()]
        self.assertIn("git status", phrases)


# ===========================================================================
# POST /api/parse
# ===========================================================================

class TestParseCommand(unittest.TestCase):

    def _parse(self, text: str) -> dict:
        resp = client.post("/api/parse", json={"text": text})
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()

    def test_known_command_matches(self):
        """'open chrome' must return a matched result."""
        data = self._parse("open chrome")
        self.assertEqual(data["matched"], "open chrome")

    def test_prefixed_phrase_stripped(self):
        """'jarvis open chrome' must also match 'open chrome'."""
        data = self._parse("jarvis open chrome")
        self.assertEqual(data["matched"], "open chrome")

    def test_unknown_phrase_returns_none(self):
        """An unrecognised phrase must return matched=None, not an error."""
        data = self._parse("xyzzy totally unknown phrase 99999")
        self.assertIsNone(data["matched"])

    def test_dry_run_always_true(self):
        """Every parse response must confirm dry_run=True."""
        for phrase in ["open chrome", "git status", "xyzzy unknown"]:
            data = self._parse(phrase)
            self.assertTrue(data.get("dry_run"), f"dry_run not True for '{phrase}'")

    def test_response_has_input_field(self):
        data = self._parse("open chrome")
        self.assertIn("input", data)

    def test_response_has_platforms_field_when_matched(self):
        data = self._parse("open chrome")
        self.assertIn("platforms", data)
        self.assertIsInstance(data["platforms"], dict)

    def test_platforms_contain_all_three(self):
        data = self._parse("open chrome")
        for plat in ("windows", "macos", "linux"):
            self.assertIn(plat, data["platforms"], f"Missing platform key '{plat}'")

    def test_empty_text_returns_400(self):
        resp = client.post("/api/parse", json={"text": ""})
        self.assertEqual(resp.status_code, 400)

    def test_whitespace_only_returns_400(self):
        resp = client.post("/api/parse", json={"text": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_git_status_matched(self):
        data = self._parse("git status")
        self.assertEqual(data["matched"], "git status")

    def test_minimise_window_matched(self):
        data = self._parse("minimise window")
        self.assertEqual(data["matched"], "minimise window")

    def test_substring_match(self):
        """A phrase containing a known command should still match."""
        data = self._parse("please open chrome for me")
        self.assertEqual(data["matched"], "open chrome")


# ===========================================================================
# GET /  (static index page)
# ===========================================================================

class TestIndexPage(unittest.TestCase):

    def test_index_returns_200(self):
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_is_html(self):
        resp = client.get("/")
        ct = resp.headers.get("content-type", "")
        self.assertIn("text/html", ct)

    def test_index_contains_title(self):
        resp = client.get("/")
        self.assertIn(b"SmartDesktop", resp.content)


# ===========================================================================
# Safety: no subprocess is ever spawned by the API handlers
# ===========================================================================

class TestNoSubprocessSpawned(unittest.TestCase):
    """
    Prove that the playground API handlers never spawn a subprocess,
    regardless of the command phrase sent.

    We patch subprocess.Popen and subprocess.run at the top level so any
    call — directly or via the command handlers — would be caught.
    """

    def _assert_no_popen(self, phrases):
        with patch("subprocess.Popen") as mock_popen, \
             patch("subprocess.run") as mock_run:
            for phrase in phrases:
                resp = client.post("/api/parse", json={"text": phrase})
                self.assertEqual(resp.status_code, 200, resp.text)
            mock_popen.assert_not_called()
            mock_run.assert_not_called()

    def test_app_commands_no_subprocess(self):
        self._assert_no_popen([
            "open chrome", "open firefox", "open terminal",
            "open vscode", "open spotify", "open discord", "open slack",
            "open calculator", "open file manager",
            "play liked songs",
        ])

    def test_terminal_commands_no_subprocess(self):
        self._assert_no_popen([
            "git status", "git pull", "run dev", "run tests",
            "npm start", "npm build", "run python",
        ])

    def test_window_commands_no_subprocess(self):
        self._assert_no_popen([
            "minimise window", "maximise window", "close window",
            "snap left", "snap right", "swap monitors",
        ])

    def test_unknown_phrase_no_subprocess(self):
        self._assert_no_popen(["xyzzy totally unknown phrase 12345"])

    def test_catalog_endpoint_no_subprocess(self):
        """GET /api/commands must also never spawn a process."""
        with patch("subprocess.Popen") as mock_popen, \
             patch("subprocess.run") as mock_run:
            resp = client.get("/api/commands")
            self.assertEqual(resp.status_code, 200)
            mock_popen.assert_not_called()
            mock_run.assert_not_called()

    def test_parser_dry_run_flag_is_true(self):
        """The global CommandParser instance inside the app must have dry_run=True."""
        self.assertTrue(
            playground_app._PARSER.dry_run,
            "CommandParser in playground must always have dry_run=True",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


### 🤖 Assistant

> 🔧 called: write_file

Now create the `render.yaml` at the repo root:

> 🔧 **write_file** — services:
  - type: web
    name: smartdesktop-playground
    runtime: python
    region: oregon
    plan: free
    rootDir: .
    buildCommand: pip install -r playground/requirements.txt
    startCommand: uvicorn playground.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"


### 🤖 Assistant

> 🔧 called: write_file, write_file

Now I need a `playground/tests/__init__.py` so pytest can discover the tests, and a `playground/__init__.py` so the playground is a package:

> 🔧 **write_file** — 

> 🔧 **write_file** — 

### 🤖 Assistant

> 🔧 called: execute_command

Now run the tests to see how they do:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

All 30 tests pass. There's one deprecation warning about `httpx` vs `httpx2` — let me check if that affects the tests or just styling, and fix it properly:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/pip show httpx2 2>&1 | head -3; .venv/bin/pip install httpx2 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v 2>&1

### 🤖 Assistant

> 🔧 called: apply_diff

All 30 tests pass with no warnings. Let me also update the `requirements.txt` to include `httpx2`:

> 🔧 **apply_diff** — playground/requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command

Also check the existing voice-assistant tests still pass (making sure we haven't broken anything):

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest voice-assistant/tests -v 2>&1 | tail -20

### 🤖 Assistant

> 🔧 called: write_file

All 76 existing tests still pass. Now let me write the session file:

> 🔧 **write_file** — # T6: Feature: web playground

**Mode:** 🛠️ SD Developer  
**Accept command:** `python -m pytest playground/tests`  
**Result:** ✅ 30 passed in 0.17 s

---

## What was built

### Files created

| File | Purpose |
|---|---|
| `playground/app.py` | FastAPI application — always `dry_run=True` |
| `playground/static/index.html` | Self-contained browser UI with Web Speech API mic support |
| `playground/requirements.txt` | Pinned dependencies |
| `playground/tests/test_app.py` | 30 tests via `TestClient`, including no-subprocess proof |
| `playground/__init__.py` | Makes `playground` a Python package (for Render import path) |
| `playground/tests/__init__.py` | Pytest discovery |
| `render.yaml` | Free Render web service definition |

---

## Design decisions

### Safety contract (`app.py:52–58`)
`CommandParser` is instantiated exactly once, at module load, with `dry_run=True` hardcoded.
There is no endpoint or parameter that accepts a `dry_run` flag — the parser's dry_run attribute
cannot be overridden by any HTTP request.

### Hardware stub pattern (`app.py:23–47`)
`pvporcupine`, `pyaudio`, `faster_whisper`, `sounddevice`, `pyautogui`, and `pygetwindow` are
stubbed before the `commands` package is imported, mirroring the pattern in
`voice-assistant/tests/test_commands.py`. This means the playground works without any audio or
ML libraries installed.

### `/api/parse` response shape
```json
{
  "input": "jarvis open chrome",
  "matched": "open chrome",
  "action": "open -a 'Google Chrome'",
  "platforms": {
    "windows": "start chrome",
    "macos": "open -a 'Google Chrome'",
    "linux": "google-chrome"
  },
  "dry_run": true
}
```
`_PARSER._strip_prefix()` and `_PARSER._match()` are called directly so the matched phrase is
available without executing the handler.

### Platform notes (`app.py:77–100`)
A static dict maps the most common phrases to per-platform action strings.
Custom project/app commands not in the dict fall back to a sensible generated description.

### UI (`static/index.html`)
- Single-file, no external CDN dependencies, dark GitHub-style theme.
- Platform selector (Windows / macOS / Linux) filters the catalog and the parse result.
- Web Speech API microphone button appears automatically when the browser supports it.
- Clicking any catalog entry fills the input and fires a parse immediately.

### `render.yaml`
Free-tier Render web service; `uvicorn` binds to `$PORT` as required by Render.

---

## Test summary

```
30 passed in 0.17 s
```

| Test class | What it proves |
|---|---|
| `TestHealth` | `/health` → 200, `dry_run=true` in payload |
| `TestGetCommands` | Catalog non-empty, has `phrase`+`platforms` keys, contains `open chrome` and `git status` |
| `TestParseCommand` | Known, prefixed, unknown, 400 on empty, platforms present, substring match |
| `TestIndexPage` | Serves HTML with correct content-type and title |
| `TestNoSubprocessSpawned` | `subprocess.Popen` and `subprocess.run` never called across all command groups; `_PARSER.dry_run` is `True` |

---

## Accept command output

```
$ python -m pytest playground/tests -v
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1 ...
collected 30 items

playground/tests/test_app.py::TestHealth::test_health_dry_run_true PASSED
playground/tests/test_app.py::TestHealth::test_health_returns_200 PASSED
playground/tests/test_app.py::TestHealth::test_health_status_ok PASSED
playground/tests/test_app.py::TestGetCommands::test_catalog_nonempty PASSED
playground/tests/test_app.py::TestGetCommands::test_each_entry_has_phrase_and_platforms PASSED
playground/tests/test_app.py::TestGetCommands::test_git_status_present PASSED
playground/tests/test_app.py::TestGetCommands::test_open_chrome_present PASSED
playground/tests/test_app.py::TestGetCommands::test_returns_200 PASSED
playground/tests/test_app.py::TestGetCommands::test_returns_list PASSED
playground/tests/test_app.py::TestParseCommand::test_dry_run_always_true PASSED
playground/tests/test_app.py::TestParseCommand::test_empty_text_returns_400 PASSED
playground/tests/test_app.py::TestParseCommand::test_git_status_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_known_command_matches PASSED
playground/tests/test_app.py::TestParseCommand::test_minimise_window_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_platforms_contain_all_three PASSED
playground/tests/test_app.py::TestParseCommand::test_prefixed_phrase_stripped PASSED
playground/tests/test_app.py::TestParseCommand::test_response_has_input_field PASSED
playground/tests/test_app.py::TestParseCommand::test_response_has_platforms_field_when_matched PASSED
playground/tests/test_app.py::TestParseCommand::test_substring_match PASSED
playground/tests/test_app.py::TestParseCommand::test_unknown_phrase_returns_none PASSED
playground/tests/test_app.py::TestParseCommand::test_whitespace_only_returns_400 PASSED
playground/tests/test_app.py::TestIndexPage::test_index_contains_title PASSED
playground/tests/test_app.py::TestIndexPage::test_index_is_html PASSED
playground/tests/test_app.py::TestIndexPage::test_index_returns_200 PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_app_commands_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_catalog_endpoint_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_parser_dry_run_flag_is_true PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_terminal_commands_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_unknown_phrase_no_subprocess PASSED
playground/tests/test_app.py::TestNoSubprocessSpawned::test_window_commands_no_subprocess PASSED

============================== 30 passed in 0.17s ==============================
```


### 🤖 Assistant

> 🔧 called: execute_command

All done. Let me do one final run of the accept command to confirm the clean pass:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python -m pytest playground/tests -v 2>&1

### 🤖 Assistant

**30 passed, 0 warnings.** T6 is done.

---

## What was built

### Files created

| File | Role |
|---|---|
| [`playground/app.py`](../../playground/app.py) | FastAPI app — `CommandParser` hardcoded to `dry_run=True` |
| [`playground/static/index.html`](../../playground/static/index.html) | Self-contained dark-theme UI: text input, 🎤 Web Speech API mic, platform selector, searchable catalog |
| [`playground/requirements.txt`](../../playground/requirements.txt) | Pinned: `fastapi==0.142.2`, `uvicorn==0.54.0`, `httpx==0.28.1`, `pydantic==2.13.5`, `pyyaml==6.0.3` |
| [`playground/tests/test_app.py`](../../playground/tests/test_app.py) | 30 tests via `TestClient` |
| [`render.yaml`](../../render.yaml) | Free Render web service, `uvicorn` on `$PORT` |
| [`docs/bob-sessions/06-playground.md`](../bob-sessions/06-playground.md) | Session notes |

### Safety contract

[`playground/app.py:58`](../../playground/app.py#L58) — `_PARSER = CommandParser(_CONFIG, dry_run=True)` is the only instantiation, hardcoded. No HTTP parameter can change it. `test_parser_dry_run_flag_is_true` asserts this at runtime; `test_app_commands_no_subprocess`, `test_terminal_commands_no_subprocess`, and `test_window_commands_no_subprocess` patch `subprocess.Popen` and `subprocess.run` and assert neither is ever called.

### Endpoints

| Method | Path | Returns |
|---|---|---|
| `GET` | `/health` | `{"status":"ok","dry_run":true}` |
| `GET` | `/api/commands` | Sorted catalog — each entry has `phrase` and `platforms` (windows/macos/linux) |
| `POST` | `/api/parse` | `{"input":…,"matched":…,"action":…,"platforms":{…},"dry_run":true}` |
| `GET` | `/` | Static `index.html` |
