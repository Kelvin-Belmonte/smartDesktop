# Hackathon submission

## Project

- **Name:** smartDesktop
- **Team:** Kelvin-Belmonte
- **Theme / track:** Theme 1: Explore, Fix, and Build
- **Repository:** https://github.com/Kelvin-Belmonte/smartDesktop
- **Live playground:** https://smartdesktop-playground.onrender.com
- **Pitch deck:** [`docs/pitch-deck.pdf`](pitch-deck.pdf) ([`.pptx`](pitch-deck.pptx))
- **Video:** (YouTube URL)

## Description (≤100 words)

smartDesktop is an offline voice assistant that turns speech into OS actions: it launches apps,
manages windows and runs git and npm. It had never been audited. IBM Bob explored it, audited it and
proved 7 bugs with failing tests before fixing them. It then removed 9 security risks, such as
AppleScript injection, and built a dry-run/text mode and a browser playground. Four custom
Bob modes, each limited to its own files, did the work in 9 tasks, each gated by a
check. Tests went from 45 to 163, and CI from 1 job to 8 on three operating systems.

## Tech stack

Python 3.10–3.14, Porcupine (wake word), Faster-Whisper (speech-to-text), PyAutoGUI / PyGetWindow,
FastAPI + Uvicorn (playground), Web Speech API, pytest, bandit, pip-audit, GitHub Actions,
Render, and **IBM Bob** (four custom modes, project rules, `BOB_TASKS.md` playbook).

## How IBM Bob was used

The playbook is [`BOB_TASKS.md`](../BOB_TASKS.md): 9 tasks, each with a mode, an edit scope, a
prompt and an accept command. The modes are defined in
[`.bob/custom_modes.yaml`](../.bob/custom_modes.yaml), and their `fileRegex` stops a mode from
editing files outside its task. [`.bob/rules`](../.bob/rules) and [`AGENTS.md`](../AGENTS.md)
forbid weakening tests, running real OS actions, editing the baseline after T3, and committing.
[`scripts/check_docs.py`](../scripts/check_docs.py) checks each documentation stage.

| Mode | Tasks | Output | Accept |
|---|---|---|---|
| 🔎 SD Analyst | T1, T9 | [`overview.md`](baseline/overview.md) (architecture with a Mermaid diagram, command catalog with `file:line`, OS matrix, "does it run?"); [`improvements.md`](after/improvements.md) and the corrected README | `check_docs --stage baseline` / `after` |
| 🛡️ SD Auditor | T2 | [`security-audit.md`](baseline/security-audit.md): S-01 to S-09 by severity, mapped to bandit and pip-audit output | `check_docs --stage security` |
| 🧪 SD Tester | T3, T8 | [`known-bugs.md`](baseline/known-bugs.md) and `tests/bob/test_bugs.py`, with every bug proven by an `xfail(strict=True)` test; portable tests, `conftest.py`, and the 3-OS × 2-Python CI matrix | `check_docs --stage bugs`, pytest, CI |
| 🛠️ SD Developer | T4–T7 | Fixes for B-01 to B-07; `--text` / `--dry-run` and `CommandParser.plan()`; the FastAPI playground with `render.yaml`; the safety layer for S-01 to S-09 | pytest, `check_docs --stage fixes` |

**Depth:** 12 prompts (9 tasks + 3 follow-ups), 436 Bob tool calls (168 `read_file`,
133 `execute_command`, 63 `apply_diff`, 40 `write_file`), about 11,000 lines of exported
transcript. Every session is in [`docs/bob-sessions/`](bob-sessions/README.md).

**Where Bob needed correcting.** All three corrections are recorded in the T5 session:
1. The first T5 attempt logged planned actions but did not return them. A follow-up added
   `CommandParser.plan()`.
2. In that follow-up, Bob's `glob playground/**` came back empty. It concluded T6 hadn't been
   done, rebuilt the playground and deleted 29 of its 30 tests. The review caught this
   (`AGENTS.md`: "never delete a test"). Bob restored the playground from git, kept all 30 tests
   and added 12 more.
3. CI on Python 3.10/3.12 failed on a missing `Optional` import, which Python 3.14's lazy
   annotations had hidden locally. Bob fixed it and ran pyflakes to confirm no other undefined
   names.

**Who did what.** IBM Bob wrote every analysis document, test, fix and feature. Claude Code built
the scaffolding (playbook, modes, rules, `check_docs.py`, templates, baseline CI), reviewed Bob's
output between tasks, and packaged the submission (this file, the README pitch, the deck). The
human ran Bob, exported the transcripts and committed.

## Improvements (before → after)

Full traceability (each B-xx and S-xx mapped to a fix, a test and a status) is in
[`docs/after/improvements.md`](after/improvements.md).

| | Before (`baseline-before`, `992e4dc`) | After (`main`) |
|---|---|---|
| Functional bugs | 7, undocumented | 7 fixed (B-01 to B-07), each with a regression test |
| Security findings | 9, including 2 critical injections | 9 addressed (S-01 to S-09) |
| bandit | 5 High, 12 Low | 0 High, 18 Low (informational subprocess notices) |
| pip-audit | 0 CVEs, but unpinned `>=` versions | 0 CVEs, exact `==` pins |
| Tests | 45 (1 could never fail, machine-specific paths) | 121 voice-assistant + 42 playground = 163 |
| CI | 1 job, Ubuntu, Python 3.12 | 8 jobs: Ubuntu/macOS/Windows × 3.10/3.12, playground, docs |
| Without a microphone | `--list-commands` crashed (eager PyAudio import) | `--text`, `--dry-run` with JSON action plans, web playground |
| Destructive commands | Ran immediately | `confirm_destructive`, with voice and text confirmation |
| Transcripts in logs | Full text at INFO | Redacted unless the log level is DEBUG |
| Porcupine key | Plain text in `config.yaml` | `PORCUPINE_ACCESS_KEY` environment variable |

Key fixes:
- **B-01:** macro steps ("open terminal", "run npm run dev") were sent to the shell as
  literal commands. They now go through the parser.
- **B-02:** window commands acted on an arbitrary window. They now act on the active one.
- **S-01:** a config or misheard string could break out of an AppleScript `do script "…"`. It is
  now passed as `argv`.
- **S-02 / S-03 / S-09:** every `shell=True` is replaced with argument lists.

## Pitch deck outline

[`docs/pitch-deck.pdf`](pitch-deck.pdf), 7 slides:

1. **Title:** smartDesktop × IBM Bob, Theme 1, team, live link
2. **The problem:** a voice assistant that runs shell commands, never audited
3. **The Bob workflow:** 4 modes → 9 tasks → accept checks, with guardrails
4. **What Bob found:** 7 bugs and 9 security findings (2 critical), proven before fixing
5. **Before → after:** the numbers
6. **What Bob built:** dry-run plans, text mode, the playground, the safety layer
7. **Honest record and roadmap:** where Bob was corrected, and what's next

## Video script (≤3 min)

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:15 | Title slide, then the live playground | "smartDesktop is an offline voice assistant: say 'Jarvis, start dev' and it opens a terminal and runs your dev server. That also means it turns speech into shell commands, and nobody had ever audited it. We gave it to IBM Bob." |
| 0:15–0:40 | `BOB_TASKS.md`, then `.bob/custom_modes.yaml` | "We didn't just say 'fix it'. We wrote a playbook of nine tasks. Each runs in a custom Bob mode that can edit only its own files and has to pass a check before it's done. The analyst documents, the auditor audits, the tester proves bugs, and the developer fixes them." |
| 0:40–1:05 | `docs/baseline/overview.md` (Mermaid diagram), then `security-audit.md` | "First Bob explored the code: the architecture, every command with its file and line, and what really works on each OS. The README claimed more than the code did. Then the audit found nine findings. Two were critical: a misheard phrase or a config value could inject AppleScript or cmd commands." |
| 1:05–1:30 | `test_bugs.py` with the xfail markers, pytest showing `7 xfailed` | "Before fixing anything, Bob proved seven bugs with tests that fail. For example, a macro sent the phrase 'open terminal' straight to the shell. Only then did the developer mode fix them, one at a time, removing each xfail without touching a single assertion." |
| 1:30–2:05 | Terminal: `printf 'start dev\n' \| python main.py --text --dry-run`, then the playground with the platform selector | "Bob then built what the project was missing: a text mode and a dry-run mode that return a structured plan instead of acting. That powers this playground, which shows exactly what each phrase would do on Windows, macOS and Linux. It's always dry-run, and a test proves no process is ever started." |
| 2:05–2:30 | The GitHub Actions matrix, all green; the before/after table | "The tests went from 45 to 163, and CI from one job to eight, across three operating systems. The two critical injections are gone, along with every high-severity bandit finding." |
| 2:30–2:50 | `05-dry-run-text-mode.md`, at the follow-ups | "Bob wasn't perfect, and that's on the record too. Once it rebuilt the playground and dropped tests. The guardrails caught it and Bob restored them. CI caught an import that only broke on older Python. Every transcript is in the repo." |
| 2:50–3:00 | README with the live link | "smartDesktop, explored, fixed and built with IBM Bob. Try it at the link below." |
