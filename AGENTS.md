# AGENTS.md: rules for AI agents (IBM Bob) in this repository

smartDesktop is an offline Python voice assistant: Porcupine wake word ("jarvis") → Faster-Whisper
speech-to-text → a substring `CommandParser` → OS actions (apps, windows, terminals, macros).
The code lives in `voice-assistant/`.

This fork is an IBM Bob hackathon entry (Theme 1: Explore, Fix, and Build). **IBM Bob does the
analysis, the audit, the fixes and the features**, one task at a time, from
[`BOB_TASKS.md`](BOB_TASKS.md), each in the project mode it names. Claude Code only built the
guardrails and scaffolding (this file, `.bob/`, `scripts/check_docs.py`, the doc templates, CI).

## What you may edit (enforced by the modes in `.bob/custom_modes.yaml`)

| Mode | Tasks | Files it may edit |
|---|---|---|
| 🔎 SD Analyst (`sd-analyst`) | T1, T9 | `docs/baseline/overview.md`, `docs/after/*.md`, `README.md` |
| 🛡️ SD Auditor (`sd-auditor`) | T2 | `docs/baseline/security-audit.md` |
| 🧪 SD Tester (`sd-tester`) | T3, T8 | `docs/baseline/known-bugs.md`, `voice-assistant/tests/**/*.py`, `voice-assistant/pytest.ini`, `.github/workflows/ci.yml` |
| 🛠️ SD Developer (`sd-developer`) | T4–T7 | `voice-assistant/**`, `playground/**`, `render.yaml` |

Every mode may also write its own notes in `docs/bob-sessions/`.

## Never

- Never edit `docs/baseline/` after T3 is committed, or `docs/baseline/SOURCE.md` at all.
- Never edit `AGENTS.md`, `BOB_TASKS.md`, `.bob/`, or `scripts/`.
- Never weaken, skip, or delete a test to make a check pass. Never change an assertion in
  `voice-assistant/tests/bob/test_bugs.py`; in T4 only remove the `xfail` marker of a fixed bug.
- Never perform real OS actions in tests, or run the real assistant while working (see `.bob/rules`).
- Never commit, push, or rewrite git history. The human commits after each task.
- Never commit secrets (the Porcupine access key stays a placeholder).

## Checks

| Command | Used by |
|---|---|
| `python scripts/check_docs.py --stage baseline` | T1 |
| `python scripts/check_docs.py --stage security` | T2 |
| `python scripts/check_docs.py --stage bugs` | T3 |
| `python scripts/check_docs.py --stage fixes` | T4 |
| `python scripts/check_docs.py --stage after` | T9 |
| `cd voice-assistant && python -m pytest tests -v` | T3–T8 |
| `python -m pytest playground/tests` | T6 |

Test dependencies: `pip install pytest numpy pyyaml` (the tests stub the audio, ML and GUI libraries).
