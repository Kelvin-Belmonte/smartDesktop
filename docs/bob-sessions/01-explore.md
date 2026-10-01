# Session 01: T1 Explore and document the current state

- **Date:** 2026-09-30
- **Mode:** 🔎 SD Analyst
- **Files edited:** `docs/baseline/overview.md`
- **Accept command and result:** `python scripts/check_docs.py --stage baseline` → OK

## What Bob did

- Mapped the runtime: the main thread idles in a loop (`main.py:164`) and the wake-word callback runs on `WakeWordThread` itself (`wakeword/__init__.py:100`), so recording, transcription and execution block detection.
- Found that `speech/__init__.py:16` imports `pyaudio` and `faster_whisper` at module level, so `python main.py --list-commands` crashes with `ModuleNotFoundError: No module named 'pyaudio'` (`main.py:115`).
- Catalogued 17 app, 12 window and 18 terminal phrases, and found two silent overrides: `open discord` from config (`commands/__init__.py:48`) and the `start dev` macro over the built-in (`terminal.py:232`).
- OS matrix: snap left/right, swap monitors and extend displays are Windows-only although the README says cross-platform (`windows.py:166`, `:198`, `:257`); `go to project` is broken on Windows (`terminal.py:169`).
- Ran the suite: 45 passed.

## Prompt

```text
Task T1 from BOB_TASKS.md. You are new to this repository. Explore it and document how smartDesktop
works today, at commit 992e4dc, in docs/baseline/overview.md.

Read voice-assistant/main.py, config.yaml, commands/{__init__,apps,terminal,windows}.py,
speech/__init__.py, wakeword/__init__.py, the tests and the README.

1. Architecture: the runtime pipeline from wake word to OS action, the threads, how config.yaml is
   loaded and merged, and a Mermaid flowchart of it.
2. Command catalog: every built-in phrase and every phrase generated from config.yaml (apps,
   projects, macros), with its handler as file.py:line.
3. OS support matrix: for each command group, what really works on Windows, macOS and Linux
   according to the code. Where the README claims more than the code does, say so.
4. Does it run?: run `cd voice-assistant && python -m pytest tests -v` and
   `python main.py --list-commands`, and report the real results. Explain what the real assistant
   needs (keys, models, audio hardware) and what fails without it. Do not run the assistant itself.

Replace every TODO(bob) marker and keep the four headings. Cite file.py:line for every claim. Do not
change any code. Finish when `python scripts/check_docs.py --stage baseline` passes.
```

## Transcript

Exported from IBM Bob on 2026-09-30.

### 👤 User

## T1: Explore and document the current state

- **Mode:** 🔎 SD Analyst
- **Edits:** `docs/baseline/overview.md`
- **Accept:** `python scripts/check_docs.py --stage baseline`
- **Session file:** `docs/bob-sessions/01-explore.md`

**Prompt**
```text
Task T1 from BOB_TASKS.md. You are new to this repository. Explore it and document how smartDesktop
works today, at commit 992e4dc, in docs/baseline/overview.md.

Read voice-assistant/main.py, config.yaml, commands/{__init__,apps,terminal,windows}.py,
speech/__init__.py, wakeword/__init__.py, the tests and the README.

1. Architecture: the runtime pipeline from wake word to OS action, the threads, how config.yaml is
   loaded and merged, and a Mermaid flowchart of it.
2. Command catalog: every built-in phrase and every phrase generated from config.yaml (apps,
   projects, macros), with its handler as file.py:line.
3. OS support matrix: for each command group, what really works on Windows, macOS and Linux
   according to the code. Where the README claims more than the code does, say so.
4. Does it run?: run `cd voice-assistant && python -m pytest tests -v` and
   `python main.py --list-commands`, and report the real results. Explain what the real assistant
   needs (keys, models, audio hardware) and what fails without it. Do not run the assistant itself.

Replace every TODO(bob) marker and keep the four headings. Cite file.py:line for every claim. Do not
change any code. Finish when `python scripts/check_docs.py --stage baseline` passes.
```

---

### 🤖 Assistant

> 🔧 called: read_file, list_files

I'll start by exploring the repository structure to understand what we're working with.

> 🔧 **list_files** — .

> 🔧 **read_file** — BOB_TASKS.md

### 🤖 Assistant

> 🔧 called: list_files, read_file



> 🔧 **list_files** — voice-assistant

> 🔧 **read_file** — docs/baseline/overview.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/config.yaml

> 🔧 **read_file** — voice-assistant/main.py

### 🤖 Assistant

> 🔧 called: list_files, list_files



> 🔧 **list_files** — voice-assistant/tests

> 🔧 **list_files** — voice-assistant/commands

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/commands/__init__.py

> 🔧 **read_file** — voice-assistant/commands/apps.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/commands/terminal.py

> 🔧 **read_file** — voice-assistant/commands/windows.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/wakeword/__init__.py

> 🔧 **read_file** — voice-assistant/speech/__init__.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/tests/test_commands.py

> 🔧 **read_file** — voice-assistant/tests/test_speech.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — README.md

> 🔧 **read_file** — voice-assistant/tests/README.md

### 🤖 Assistant

> 🔧 called: execute_command

Now let me run the tests and the `--list-commands` command:

> 🔧 **execute_command** — cd voice-assistant && python -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && python3 -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python -m pytest tests -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python main.py --list-commands 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/pip install colorama pyyaml faster-whisper numpy pyaudio 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/pip install colorama pyyaml 2>&1 | tail -3

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd voice-assistant && ../.venv/bin/python main.py --list-commands 2>&1

### 🤖 Assistant

> 🔧 called: read_file, read_file

The `--list-commands` flag requires instantiating `SmartDesktopAssistant` which imports `pyaudio` unconditionally. Let me check the requirements file and then read the check_docs script to understand what the baseline check requires:

> 🔧 **read_file** — scripts/check_docs.py

> 🔧 **read_file** — voice-assistant/requirements.txt

### 🤖 Assistant

> 🔧 called: glob, list_files

Now I have a complete picture of the codebase. Let me also check the `pytest.ini` and check for any existing docs templates:

> 🔧 **list_files** — docs

> 🔧 **glob** — voice-assistant/pytest.ini

### 🤖 Assistant

> 🔧 called: write_file

Now I have everything I need. Let me write the complete `docs/baseline/overview.md`:

> 🔧 **write_file** — docs/baseline/overview.md

### 🤖 Assistant

> 🔧 called: execute_command

Now run the acceptance check:

> 🔧 **execute_command** — cd /Users/mario-ibm/gitProjects/smartDesktop && .venv/bin/python scripts/check_docs.py --stage baseline 2>&1

### 🤖 Assistant

The check passes. Here is a summary of what was done and why.

---

## What was written and why

### Architecture (`## Architecture`)

- **Two-thread model**: the main thread sleeps in a `while` loop ([`main.py:164`](../../voice-assistant/main.py#L164)); the daemon `WakeWordThread` reads Porcupine frames and fires `on_detected`. Critically, the callback is called **on the WakeWordThread itself** ([`wakeword/__init__.py:100`](../../voice-assistant/wakeword/__init__.py#L100)), so recording + transcription + execution all block the detection loop.
- **Eager imports**: [`speech/__init__.py:16`](../../voice-assistant/speech/__init__.py#L16) top-level imports `pyaudio` and `faster_whisper`, so even `--list-commands` fails without PortAudio installed.
- **Config loading**: [`main.py:90`](../../voice-assistant/main.py#L90) calls `yaml.safe_load()` with no validation or merging. The only special handling is `os.path.expandvars` for the Porcupine key ([`main.py:138`](../../voice-assistant/main.py#L138)).
- **Mermaid diagram** shows the full mic-to-action pipeline with module:line citations.

### Command catalog (`## Command catalog`)

All 17 built-in app phrases, 12 window phrases, and 18 terminal phrases sourced directly from the `build_*` factory functions. Two important overwrite bugs documented:
1. `open discord` config entry overwrites the built-in at [`commands/__init__.py:48`](../../voice-assistant/commands/__init__.py#L48).
2. `start dev` macro overwrites the `run_npm_dev` built-in alias at [`terminal.py:232`](../../voice-assistant/commands/terminal.py#L232). Macro steps are **not** dispatched through `CommandParser` — they go directly to `_run_in_terminal()`.

### OS support matrix (`## OS support matrix`)

Three Windows-only gaps the README omits: `snap left/right` ([`windows.py:166–185`](../../voice-assistant/commands/windows.py#L166)), `swap_monitors` ([`windows.py:198`](../../voice-assistant/commands/windows.py#L198)), and `extend_displays` ([`windows.py:257`](../../voice-assistant/commands/windows.py#L257)). Also noted: the `shlex.quote` POSIX path in `go_to_project` ([`terminal.py:169`](../../voice-assistant/commands/terminal.py#L169)) is incompatible with `cmd.exe`, so project navigation is broken on Windows.

### Does it run? (`## Does it run?`)

- **Tests**: 45 passed, 0 failed — confirmed by running the suite.
- **`--list-commands`**: crashes with `ModuleNotFoundError: No module named 'pyaudio'` because `SmartDesktopAssistant.__init__()` ([`main.py:115`](../../voice-assistant/main.py#L115)) imports `SpeechRecognizer` unconditionally before the `--list-commands` branch is reached at [`main.py:217`](../../voice-assistant/main.py#L217). Expected command list derived from the code is provided.
