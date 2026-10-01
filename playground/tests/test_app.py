"""
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


# ===========================================================================
# New tests: per-platform plans, macro steps, platform keys
# ===========================================================================

class TestParsePlatformPlans(unittest.TestCase):
    """Plans from /api/parse must have platform-specific targets from plan()."""

    def _parse(self, text: str) -> dict:
        resp = client.post("/api/parse", json={"text": text})
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()

    def test_open_chrome_platforms_have_plan_dicts(self):
        """platforms values must be plan dicts (with 'action' key), not plain strings."""
        data = self._parse("open chrome")
        for plat in ("windows", "macos", "linux"):
            plan = data["platforms"][plat]
            self.assertIsInstance(plan, dict, f"Platform '{plat}' plan is not a dict")
            self.assertIn("action", plan, f"Plan for '{plat}' missing 'action'")

    def test_open_chrome_windows_target(self):
        data = self._parse("open chrome")
        self.assertEqual(data["platforms"]["windows"]["target"], "start chrome")

    def test_open_chrome_macos_target(self):
        data = self._parse("open chrome")
        self.assertEqual(data["platforms"]["macos"]["target"], "Google Chrome")

    def test_open_chrome_linux_target(self):
        data = self._parse("open chrome")
        self.assertEqual(data["platforms"]["linux"]["target"], "google-chrome")

    def test_open_chrome_three_targets_all_different(self):
        """All three platform targets for 'open chrome' must be distinct."""
        data = self._parse("open chrome")
        targets = {plat: data["platforms"][plat]["target"]
                   for plat in ("windows", "macos", "linux")}
        self.assertEqual(len(set(targets.values())), 3,
                         f"Expected 3 distinct targets, got: {targets}")

    def test_platform_keys_are_lowercase(self):
        """'platform' field inside each plan dict must be lowercase."""
        data = self._parse("open chrome")
        for plat in ("windows", "macos", "linux"):
            plan = data["platforms"][plat]
            self.assertEqual(plan["platform"], plat,
                             f"plan['platform'] should be '{plat}', got {plan['platform']!r}")


class TestParseMacroStepsPlayground(unittest.TestCase):
    """Macros from config.yaml must surface as plan action=macro with steps."""

    def _parse(self, text: str) -> dict:
        resp = client.post("/api/parse", json={"text": text})
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()

    def test_start_dev_is_macro(self):
        data = self._parse("start dev")
        self.assertEqual(data["matched"], "start dev")
        for plat in ("windows", "macos", "linux"):
            plan = data["platforms"][plat]
            self.assertEqual(plan["action"], "macro",
                             f"start dev on {plat} should be macro, got {plan['action']!r}")

    def test_start_dev_has_two_steps(self):
        data = self._parse("start dev")
        for plat in ("windows", "macos", "linux"):
            steps = data["platforms"][plat]["steps"]
            self.assertEqual(len(steps), 2,
                             f"start dev on {plat} should have 2 steps, got {len(steps)}")

    def test_start_dev_step_run_npm_run_dev_has_known_action(self):
        """'run npm run dev' must resolve to action='terminal', not 'unknown'."""
        data = self._parse("start dev")
        for plat in ("windows", "macos", "linux"):
            steps = data["platforms"][plat]["steps"]
            run_step = next(
                (s for s in steps if "npm run dev" in s["phrase"]), None
            )
            self.assertIsNotNone(run_step,
                                 f"No 'run npm run dev' step in start dev on {plat}")
            self.assertEqual(run_step["action"], "terminal",
                             f"Step action should be 'terminal', got {run_step['action']!r}")

    def test_morning_routine_has_three_steps(self):
        data = self._parse("morning routine")
        self.assertEqual(data["matched"], "morning routine")
        for plat in ("windows", "macos", "linux"):
            steps = data["platforms"][plat]["steps"]
            self.assertEqual(len(steps), 3,
                             f"morning routine on {plat} should have 3 steps")

    def test_morning_routine_steps_all_launch(self):
        """All steps in morning routine are app launches."""
        data = self._parse("morning routine")
        for plat in ("windows", "macos", "linux"):
            for step in data["platforms"][plat]["steps"]:
                self.assertEqual(step["action"], "launch",
                                 f"Step '{step['phrase']}' on {plat} should be launch")

    def test_morning_routine_chrome_differs_per_platform(self):
        """Chrome target in morning routine steps must differ per platform."""
        data = self._parse("morning routine")
        chrome_targets = {}
        for plat in ("windows", "macos", "linux"):
            for step in data["platforms"][plat]["steps"]:
                if step["command"] == "open chrome":
                    chrome_targets[plat] = step["target"]
        self.assertEqual(len(set(chrome_targets.values())), 3,
                         f"Expected 3 distinct chrome targets, got: {chrome_targets}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
