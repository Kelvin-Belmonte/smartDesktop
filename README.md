# smartDesktop

A local, offline voice automation assistant for developer workflows and desktop control — similar to Siri or Alexa but optimised for power users and developers.

## Overview

```
Microphone → Wake Word (Porcupine) → Speech-to-Text (Faster-Whisper) → Command Parser → Action Executor
```

The assistant runs permanently in the background, listens for a **wake word** (default: *"Jarvis"*), transcribes the following command entirely offline using Faster-Whisper, and executes the matching OS action.

## Features

- 🎙️ **Always-on wake word detection** — ultra-low CPU usage via Porcupine
- 🗣️ **Offline speech recognition** — Faster-Whisper, works without internet
- 🚀 **App launcher** — open Chrome, VS Code, Spotify, Discord, and custom apps (Windows, macOS, Linux)
- 🪟 **Window management** — minimise, maximise, restore, close (Windows ✅; macOS/Linux partial via pygetwindow); snap left/right and swap/extend monitors are **Windows-only**
- 💻 **Terminal automation** — run git, npm, pytest and custom shell commands (Windows, macOS, Linux)
- 📁 **Project navigation** — jump to any project directory and open it in VS Code
- 🔧 **Fully configurable** — all commands and shortcuts defined in `config.yaml`
- 🖥️ **Text mode** — `python main.py --text` reads commands from stdin; no microphone or audio library needed
- 🔍 **Dry-run mode** — `python main.py --text --dry-run` previews planned actions without touching the OS
- 🛡️ **Safety layer** — destructive commands require confirmation; AppleScript/shell injection defences; transcript redaction
- 🌐 **Web playground** — try commands in the browser at `/` (see `playground/`)

> **OS note:** App launch, terminal commands, and project navigation work on Windows, macOS, and
> Linux. Window snap, swap-monitors, and extend-displays are Windows-only in the current code.
> macOS and Linux window min/max/close rely on `pygetwindow`, which has limited support outside
> Windows.

## Quick Start

### 1. Prerequisites

- Python 3.9+
- A microphone (only needed for voice mode; `--text` mode has no audio dependency)
- A free [Picovoice account](https://console.picovoice.ai/) for a Porcupine access key (only needed for voice mode)

### 2. Install dependencies

```bash
cd voice-assistant
pip install -r requirements.txt
```

> **Note:** PyAudio requires `portaudio`. Install it first:
> - Windows: included in the PyAudio wheel
> - macOS: `brew install portaudio`
> - Linux: `sudo apt install portaudio19-dev`
>
> `--text` and `--dry-run` modes do **not** require PyAudio, pvporcupine, or faster-whisper.

### 3. Configure

Set your Porcupine access key as an environment variable (recommended — keeps the key out of version control):

```bash
export PORCUPINE_ACCESS_KEY="your-key-here"   # macOS / Linux
set PORCUPINE_ACCESS_KEY=your-key-here        # Windows cmd
$Env:PORCUPINE_ACCESS_KEY="your-key-here"     # Windows PowerShell
```

Alternatively, edit `voice-assistant/config.yaml` directly (not recommended for shared repos):

```yaml
wakeword:
  access_key: "${PORCUPINE_ACCESS_KEY}"   # expands the env var at startup
  keywords:
    - jarvis
  sensitivity: 0.5

commands:
  confirm_destructive: true   # require confirmation for close window, macros, shell commands
  apps:
    league: "C:/Riot Games/LeagueClient.exe"
  projects:
    myapp: "~/repos/myapp"
```

### 4. Run

**Voice mode** (requires microphone + Porcupine key):

```bash
cd voice-assistant
python main.py
```

**Text mode** (no microphone, no audio libraries required):

```bash
cd voice-assistant
python main.py --text
```

**Dry-run** — preview what *would* happen without executing anything:

```bash
cd voice-assistant
python main.py --text --dry-run
```

**List all registered commands:**

```bash
cd voice-assistant
python main.py --text --dry-run --list-commands
```

## Example Commands

| You say | What happens | OS |
|---|---|---|
| *Jarvis open chrome* | Opens Google Chrome | Win / macOS / Linux |
| *Jarvis open terminal* | Opens a terminal window | Win / macOS / Linux |
| *Jarvis open vscode* | Opens VS Code | Win / macOS / Linux |
| *Jarvis open spotify* | Opens Spotify | Win / macOS / Linux |
| *Jarvis go to littleguy* | `cd ~/repos/littleguy && code .` | Win / macOS / Linux |
| *Jarvis git status* | Runs `git status` in a terminal | Win / macOS / Linux |
| *Jarvis run dev* | Runs `npm run dev` in a terminal | Win / macOS / Linux |
| *Jarvis run tests* | Runs `pytest` in a terminal | Win / macOS / Linux |
| *Jarvis snap left* | Snaps active window to the left | **Windows only** |
| *Jarvis swap monitors* | Rotates all windows across monitors | **Windows only** |
| *Jarvis minimise window* | Minimises the active window | Windows ✅; macOS/Linux ⚠️ |

## Web Playground

A browser-based demo is available in `playground/`. It runs the `CommandParser` with
`dry_run=True` — **no OS action can be triggered from the server**.

```bash
cd playground
pip install -r requirements.txt
uvicorn app:app --reload
# open http://localhost:8000
```

Endpoints:
- `GET /` — self-contained browser UI (type a phrase or use the mic button)
- `GET /api/commands` — full command catalog with per-platform action descriptions
- `POST /api/parse` `{"text": "open chrome"}` — matched command + planned action
- `GET /health` — liveness check

The playground is deployable to [Render](https://render.com/) for free using `render.yaml` at the
repo root.

## Project Structure

```
voice-assistant/
├── main.py              # Entry point — orchestrates all components
├── config.yaml          # All configuration (wake word, commands, apps)
├── requirements.txt     # Python dependencies (all pinned with ==)
├── pytest.ini           # Test configuration
├── wakeword/
│   └── __init__.py      # Porcupine wake word detection
├── speech/
│   └── __init__.py      # Faster-Whisper speech-to-text
├── commands/
│   ├── __init__.py      # CommandParser — registry and dispatch
│   ├── apps.py          # App launcher commands
│   ├── windows.py       # Window management commands
│   └── terminal.py      # Terminal / shell commands
└── tests/
    ├── conftest.py      # Session-wide hardware stubs (no real OS calls)
    ├── bob/             # Bug regression tests (T3/T4)
    ├── test_commands.py # Command builder and parser tests
    ├── test_dry_run.py  # Dry-run and text-mode tests
    └── test_safety.py   # Security finding regression tests
playground/
├── app.py               # FastAPI app (always dry_run=True)
├── static/index.html    # Self-contained browser UI
├── requirements.txt     # Playground dependencies
└── tests/test_app.py    # 30 API + no-subprocess tests
```

## Configuration Reference

### `wakeword`

| Key | Description | Default |
|---|---|---|
| `access_key` | Picovoice API key — prefer `PORCUPINE_ACCESS_KEY` env var | *required* |
| `keywords` | Wake word list (built-in or custom) | `[jarvis]` |
| `sensitivity` | Detection sensitivity (0.0–1.0) | `0.5` |

### `speech`

| Key | Description | Default |
|---|---|---|
| `model_size` | Whisper model (`tiny`, `base`, `small`, `medium`, `large`) | `base` |
| `language` | Language code (`en`, `fr`, …) or `null` for auto | `en` |
| `device` | Inference device (`cpu`, `cuda`, `auto`) | `auto` |
| `compute_type` | Quantisation (`int8`, `float16`, `float32`) | `int8` |
| `max_record_seconds` | Max recording time per command | `10` |
| `silence_threshold` | RMS below which audio is silent | `500` |
| `silence_duration` | Seconds of silence to end recording | `1.5` |

### `commands`

| Key | Description |
|---|---|
| `prefix` | Wake word to strip from transcripts (`jarvis`) |
| `confirm_destructive` | If `true`, require confirmation for `close window`, macros, and shell commands (default: `true`) |
| `apps` | Custom app shortcuts (`name: path`) — built-in names are protected and cannot be overwritten |
| `projects` | Project directory shortcuts (`name: path`) |
| `macros` | Multi-step command sequences (each step is dispatched through the `CommandParser`) |

### `PORCUPINE_ACCESS_KEY` environment variable

The assistant reads `PORCUPINE_ACCESS_KEY` from the environment before falling back to
`config.yaml`. Set it in your shell profile or CI secrets — **never commit a real key** to version
control. The config ships with a placeholder (`"YOUR_PORCUPINE_ACCESS_KEY"`) that the assistant
will reject at startup with a clear error message.

## Running the tests

```bash
# Voice-assistant tests (no audio hardware required)
cd voice-assistant
python -m pytest tests -v

# Web playground tests
python -m pytest playground/tests -v
```

All tests mock OS-level side effects (`subprocess`, `os.startfile`, `pyautogui`, `pygetwindow`,
`ctypes`). No real application is launched, no window is moved, and no shell command is executed.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| Wake word | [Porcupine](https://github.com/Picovoice/porcupine) |
| Speech-to-text | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) |
| Audio capture | PyAudio |
| Desktop automation | PyAutoGUI |
| Window management | pygetwindow |
| Shell commands | subprocess |
| Configuration | PyYAML |
| Web playground | FastAPI + uvicorn |
