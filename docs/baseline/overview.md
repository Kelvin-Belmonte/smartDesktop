# smartDesktop: current state (baseline)

Written by IBM Bob in task T1 (🔎 SD Analyst), against commit `992e4dc` (tag `baseline-before`).
See [SOURCE.md](SOURCE.md). Every claim cites the source as `file.py:line`.

## Architecture

TODO(bob): describe the runtime pipeline (wake word → recording → transcription → parsing → action),
the threads involved, and how `config.yaml` is loaded. Include a Mermaid flowchart:

```mermaid
flowchart LR
  A["TODO(bob)"] --> B["TODO(bob)"]
```

## Command catalog

TODO(bob): a table of every built-in phrase and every config-driven phrase:
| Phrase | Module | Handler (file.py:line) | What it does | Config key |

## OS support matrix

TODO(bob): a table | Command group | Windows | macOS | Linux | Notes |. Use ✅ / ⚠️ / ❌ and base
each cell on the code, not the README.

## Does it run?

TODO(bob): the exact commands you ran and their output, summarized:
- `cd voice-assistant && python -m pytest tests -v` (pass / fail / error counts)
- `python main.py --list-commands`
- what is needed to run the real assistant (keys, models, hardware) and what fails without it.
