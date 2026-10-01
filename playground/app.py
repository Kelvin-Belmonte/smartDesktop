"""
SmartDesktop Web Playground — FastAPI application.

SAFETY CONTRACT: CommandParser is ALWAYS instantiated with dry_run=True.
There is no code path in this module that can trigger a real OS action.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the voice-assistant package importable regardless of where uvicorn
# is launched from.  The playground/ dir sits next to voice-assistant/.
# ---------------------------------------------------------------------------
_VA_ROOT = Path(__file__).resolve().parent.parent / "voice-assistant"
if str(_VA_ROOT) not in sys.path:
    sys.path.insert(0, str(_VA_ROOT))

# Stub heavy/hardware-only libraries so the playground works without a
# microphone, GPU, or native audio drivers installed.
import types as _types


def _ensure_stub(name: str) -> None:
    """Insert a lightweight stub for *name* if it is not already importable."""
    if name in sys.modules:
        return
    mod = _types.ModuleType(name)
    sys.modules[name] = mod


_ensure_stub("pvporcupine")
_ensure_stub("pyaudio")
sys.modules["pyaudio"].paInt16 = 8  # type: ignore[attr-defined]
sys.modules["pyaudio"].PyAudio = object  # type: ignore[attr-defined]
_ensure_stub("faster_whisper")
_ensure_stub("pyautogui")
_ensure_stub("sounddevice")

_gw = _ensure_stub("pygetwindow") or sys.modules["pygetwindow"]
import unittest.mock as _mock

sys.modules["pygetwindow"].getWindowsWithTitle = _mock.MagicMock(return_value=[])  # type: ignore
sys.modules["pygetwindow"].getAllWindows = _mock.MagicMock(return_value=[])  # type: ignore
sys.modules["pygetwindow"].getActiveWindow = _mock.MagicMock(return_value=None)  # type: ignore

# ---------------------------------------------------------------------------
# Now import the project code and FastAPI
# ---------------------------------------------------------------------------
import platform

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from commands import CommandParser

# ---------------------------------------------------------------------------
# Build the parser — dry_run=True is HARDCODED and cannot be overridden
# ---------------------------------------------------------------------------
_CONFIG_PATH = _VA_ROOT / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as _fh:
    _CONFIG: dict = yaml.safe_load(_fh) or {}

# SAFETY: dry_run is always True — no OS action can ever be triggered.
_PARSER = CommandParser(_CONFIG, dry_run=True)

# ---------------------------------------------------------------------------
# Command catalog helper
# ---------------------------------------------------------------------------
_OS_NAME = platform.system()  # "Windows" | "Darwin" | "Linux"

# Map of phrase → what the action does on each platform (informational only).
_PLATFORM_NOTES: dict[str, dict[str, str]] = {
    "open chrome":       {"windows": "start chrome", "macos": "open -a 'Google Chrome'", "linux": "google-chrome"},
    "open firefox":      {"windows": "start firefox", "macos": "open -a Firefox", "linux": "firefox"},
    "open terminal":     {"windows": "start cmd", "macos": "open -a Terminal", "linux": "gnome-terminal / xterm"},
    "open vscode":       {"windows": "code", "macos": "code", "linux": "code"},
    "open file manager": {"windows": "explorer", "macos": "open -a Finder", "linux": "xdg-open ."},
    "open calculator":   {"windows": "calc", "macos": "open -a Calculator", "linux": "gnome-calculator"},
    "open spotify":      {"windows": "Spotify.exe / start spotify", "macos": "open -a Spotify", "linux": "spotify"},
    "open discord":      {"windows": "start discord", "macos": "open -a Discord", "linux": "discord"},
    "open slack":        {"windows": "start slack", "macos": "open -a Slack", "linux": "slack"},
    "play liked songs":  {"windows": "start spotify:collection", "macos": "open spotify:collection", "linux": "xdg-open spotify:collection"},
    "git status":        {"windows": "cmd /K git status", "macos": "Terminal: git status", "linux": "bash -c git status"},
    "git pull":          {"windows": "cmd /K git pull", "macos": "Terminal: git pull", "linux": "bash -c git pull"},
    "run dev":           {"windows": "cmd /K npm run dev", "macos": "Terminal: npm run dev", "linux": "bash -c npm run dev"},
    "run tests":         {"windows": "cmd /K pytest", "macos": "Terminal: pytest", "linux": "bash -c pytest"},
    "minimise window":   {"windows": "pygetwindow minimize()", "macos": "pygetwindow minimize()", "linux": "pygetwindow minimize()"},
    "snap left":         {"windows": "Win+Left hotkey", "macos": "not supported", "linux": "not supported"},
    "snap right":        {"windows": "Win+Right hotkey", "macos": "not supported", "linux": "not supported"},
    "swap monitors":     {"windows": "rotate windows across monitors", "macos": "not supported", "linux": "not supported"},
}


def _describe_command(phrase: str) -> dict:
    """Return a dict describing what *phrase* does, per platform."""
    notes = _PLATFORM_NOTES.get(phrase, {})
    # Infer a generic description if no per-platform note is registered
    if not notes:
        if phrase.startswith("go to "):
            project = phrase[len("go to "):]
            cmd = f"cd <{project}> && code ."
            notes = {"windows": cmd, "macos": cmd, "linux": cmd}
        elif phrase.startswith("open "):
            app = phrase[len("open "):]
            notes = {"windows": f"launch {app}", "macos": f"open -a {app}", "linux": app}
        else:
            notes = {"windows": phrase, "macos": phrase, "linux": phrase}
    return notes


def _build_catalog() -> list[dict]:
    """Return the full command catalog as a list of dicts."""
    catalog = []
    for phrase in _PARSER.registered_commands:
        catalog.append({
            "phrase": phrase,
            "platforms": _describe_command(phrase),
        })
    return catalog


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SmartDesktop Playground",
    description="Try SmartDesktop voice commands in the browser (always dry-run).",
    version="1.0.0",
)

_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness probe."""
    return JSONResponse({"status": "ok", "dry_run": True})


@app.get("/api/commands")
async def get_commands() -> JSONResponse:
    """Return the full command catalog."""
    return JSONResponse(_build_catalog())


class ParseRequest(BaseModel):
    text: str


@app.post("/api/parse")
async def parse_command(req: ParseRequest) -> JSONResponse:
    """
    Parse a text phrase and return the matched command + planned action.

    SAFETY: the parser always runs with dry_run=True — no OS action occurs.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    phrase_stripped = _PARSER._strip_prefix(req.text.strip())
    handler, matched = _PARSER._match(phrase_stripped)

    if matched is None:
        return JSONResponse(
            {
                "input": req.text,
                "matched": None,
                "action": None,
                "dry_run": True,
            }
        )

    platforms = _describe_command(matched)
    current_platform = {
        "Windows": "windows",
        "Darwin": "macos",
        "Linux": "linux",
    }.get(_OS_NAME, _OS_NAME.lower())

    return JSONResponse(
        {
            "input": req.text,
            "matched": matched,
            "action": platforms.get(current_platform, matched),
            "platforms": platforms,
            "dry_run": True,
        }
    )


@app.get("/")
async def index() -> FileResponse:
    """Serve the static playground page."""
    return FileResponse(str(_STATIC_DIR / "index.html"))
