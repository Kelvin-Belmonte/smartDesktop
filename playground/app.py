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
import platform as _platform

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from commands import CommandParser, _resolve_os

# ---------------------------------------------------------------------------
# Build the parser — dry_run=True is HARDCODED and cannot be overridden
# ---------------------------------------------------------------------------
_CONFIG_PATH = _VA_ROOT / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as _fh:
    _CONFIG: dict = yaml.safe_load(_fh) or {}

# SAFETY: dry_run is always True — no OS action can ever be triggered.
_PARSER = CommandParser(_CONFIG, dry_run=True)

_PLATFORMS = ("windows", "macos", "linux")


def _plans_for(phrase: str) -> dict:
    """Return {windows: plan, macos: plan, linux: plan} for *phrase*."""
    return {plat: _PARSER.plan(phrase, platform=plat) for plat in _PLATFORMS}


def _build_catalog() -> list[dict]:
    """Return the full command catalog as a list of dicts."""
    return [
        {"phrase": phrase, "platforms": _plans_for(phrase)}
        for phrase in _PARSER.registered_commands
    ]


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
    _, matched = _PARSER._match(phrase_stripped)

    if matched is None:
        return JSONResponse(
            {
                "input": req.text,
                "matched": None,
                "action": None,
                "dry_run": True,
            }
        )

    # Build per-platform plans from the parser (single source of truth).
    platforms = _plans_for(req.text.strip())

    # "action" = the plan for the current server OS.
    current_platform = _resolve_os(None)  # returns "windows"/"macos"/"linux"
    action = platforms.get(current_platform)

    return JSONResponse(
        {
            "input": req.text,
            "matched": matched,
            "action": action,
            "platforms": platforms,
            "dry_run": True,
        }
    )


@app.get("/")
async def index() -> FileResponse:
    """Serve the static playground page."""
    return FileResponse(str(_STATIC_DIR / "index.html"))
