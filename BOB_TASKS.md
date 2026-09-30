# BOB_TASKS.md: the IBM Bob playbook

smartDesktop was taken as-is from [Qrytics/smartDesktop](https://github.com/Qrytics/smartDesktop) at
commit `992e4dc` (tag `baseline-before`). These 9 tasks are the part IBM Bob does: explore the code,
audit it, prove its bugs, fix them, and build new features. Claude Code only built the scaffolding
(this file, `AGENTS.md`, `.bob/`, `scripts/check_docs.py`, the doc templates and the baseline CI).

**How to run a task**
1. In Bob, switch to the **mode** the task names (Bob loads the project modes from `.bob/custom_modes.yaml`).
2. Paste the **prompt**.
3. Let Bob work until the **accept** command passes. Bob runs it itself, and you can run it too.
4. Save the conversation (export or copy) to the **session file**, starting from
   `docs/bob-sessions/TEMPLATE.md`, and add a row to `docs/bob-sessions/README.md`.
5. Commit: `git add -A && git commit -m "T<n>: <title>"`.

Setup once: `python -m venv .venv && . .venv/bin/activate && pip install pytest numpy pyyaml`.

If Bob wanders outside its task: stop it, run `git status`, restore anything outside the task's
**Edits** with `git checkout -- <file>`, and start the task again.

---

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

## T2: Security and safety audit

- **Mode:** 🛡️ SD Auditor
- **Edits:** `docs/baseline/security-audit.md`
- **Accept:** `python scripts/check_docs.py --stage security`
- **Session file:** `docs/bob-sessions/02-security-audit.md`

**Prompt**
```text
Task T2 from BOB_TASKS.md. Audit smartDesktop at commit 992e4dc for security and safety risks, and
write the results in docs/baseline/security-audit.md.

Threat model: anyone near the microphone can speak commands, the transcription can mishear, and
config.yaml values reach subprocess calls. Review in particular: every subprocess call and shell=True
use, strings interpolated into AppleScript, PowerShell or shell commands, how config values and
transcripts flow into them, destructive commands and whether they need confirmation, what is logged,
how the Porcupine key is handled, and the dependency pins.

Run `bandit -r voice-assistant -x voice-assistant/tests` and
`pip-audit -r voice-assistant/requirements.txt` (install them into the virtual environment) and
summarize the output under "Tool output", mapping each result to a finding.

Number the findings S-01, S-02, ... by severity. Each has a severity, a file.py:line location, a
description, the impact and a concrete recommendation. Do not change any code. Finish when
`python scripts/check_docs.py --stage security` passes.
```

---

## T3: Bug hunt and baseline tests

- **Mode:** 🧪 SD Tester
- **Edits:** `docs/baseline/known-bugs.md`, `voice-assistant/tests/bob/test_bugs.py` (plus an empty `__init__.py` or `conftest.py` there if needed)
- **Accept:** `python scripts/check_docs.py --stage bugs` and `cd voice-assistant && python -m pytest tests -v` (green, with the xfails expected)
- **Session file:** `docs/bob-sessions/03-bug-hunt.md`

**Prompt**
```text
Task T3 from BOB_TASKS.md. Find the real functional bugs in smartDesktop at commit 992e4dc and prove
each one with a test, before anything is fixed.

Use docs/baseline/overview.md and docs/baseline/security-audit.md as a starting point. Look closely at:
how macros execute their steps, how config.yaml commands interact with built-in commands of the same
name, which window the window commands act on, each platform branch in commands/apps.py and
commands/terminal.py (Windows, macOS, Linux), the CUDA to CPU fallback in speech/__init__.py, error
handling in the wake-word thread, and the existing tests (tests that cannot fail, machine-specific paths).

For every bug:
1. Add a row B-01, B-02, ... to docs/baseline/known-bugs.md, and explain how to reproduce it.
2. Add a test in voice-assistant/tests/bob/test_bugs.py that asserts the CORRECT behaviour, whose
   name or docstring contains the id, and that is marked
   @pytest.mark.xfail(strict=True, reason="B-xx: <title>"). It must fail today because of the bug.
   Mock every OS side effect (subprocess, os.startfile, platform.system, pyautogui, pygetwindow, ctypes)
   in the same way as tests/test_commands.py.

Only list bugs you proved with a test. Do not change application code. Finish when
`python scripts/check_docs.py --stage bugs` passes and `cd voice-assistant && python -m pytest tests -v`
is green (every B-xx test reported as xfail).
```

---

## T4: Fix the bugs

- **Mode:** 🛠️ SD Developer
- **Edits:** `voice-assistant/**` (in `tests/bob/test_bugs.py`, only removing the xfail markers)
- **Accept:** `cd voice-assistant && python -m pytest tests -v` and `python scripts/check_docs.py --stage fixes`
- **Session file:** `docs/bob-sessions/04-fix-bugs.md`

**Prompt**
```text
Task T4 from BOB_TASKS.md. Fix every bug listed in docs/baseline/known-bugs.md, one at a time.

For each B-xx: read its test in voice-assistant/tests/bob/test_bugs.py, fix the root cause in the
application code with the smallest correct change, remove that test's xfail marker, and run the full
suite. Do not change any assertion in test_bugs.py and do not edit docs/baseline/. Keep the existing
tests passing. Explain each fix with its B-xx id and file.py:line.

Finish when `cd voice-assistant && python -m pytest tests -v` passes with no xfail left and
`python scripts/check_docs.py --stage fixes` passes.
```

---

## T5: Feature: dry-run and text mode

- **Mode:** 🛠️ SD Developer
- **Edits:** `voice-assistant/**`
- **Accept:** `cd voice-assistant && python -m pytest tests -v` (including the new tests)
- **Session file:** `docs/bob-sessions/05-dry-run-text-mode.md`

**Prompt**
```text
Task T5 from BOB_TASKS.md. Add a dry-run mode and a text mode to smartDesktop, so it can be used and
demonstrated without a microphone, and without touching the machine.

1. Dry-run: CommandParser (and the handlers it calls) can run with dry_run=True. In that mode no OS
   action happens; instead the parser returns a structured description of the planned action, e.g.
   {"phrase": ..., "command": ..., "action": "launch", "target": ..., "platform": ...}. Macros return the
   list of their steps' actions.
2. Text mode: `python main.py --text` reads commands from stdin line by line (no wake word, no Whisper,
   no audio libraries imported) and executes them; `python main.py --text --dry-run` only prints the
   planned actions. Audio and ML imports must stay lazy so --text works without pyaudio, pvporcupine or
   faster-whisper installed.

Add tests in voice-assistant/tests/test_dry_run.py covering dry-run for every command group, macros,
unknown phrases, and --text --dry-run end to end via subprocess with stdin. Update
voice-assistant/tests/README.md. Finish when `cd voice-assistant && python -m pytest tests -v` passes.
```

---

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

## T7: Safety layer

- **Mode:** 🛠️ SD Developer
- **Edits:** `voice-assistant/**`
- **Accept:** `cd voice-assistant && python -m pytest tests -v`
- **Session file:** `docs/bob-sessions/07-safety-layer.md`

**Prompt**
```text
Task T7 from BOB_TASKS.md. Fix the security findings in docs/baseline/security-audit.md that task T4
did not already fix, starting with the highest severity.

At minimum: destructive or high-impact commands (closing windows, running shell commands, macros that
run commands) need a confirmation step, configurable in config.yaml, that works in voice and text mode
and is skipped in dry-run; strings interpolated into AppleScript or shell commands are escaped or
passed as argument lists instead of shell=True; transcripts are redacted from logs unless the log level
is DEBUG; the Porcupine key is read from the PORCUPINE_ACCESS_KEY environment variable; and the
dependencies in requirements.txt are pinned.

Add tests for each fix in voice-assistant/tests/test_safety.py, naming the S-xx id in each test.
Finish when `cd voice-assistant && python -m pytest tests -v` passes.
```

---

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

## T9: After docs

- **Mode:** 🔎 SD Analyst
- **Edits:** `docs/after/improvements.md`, `README.md`
- **Accept:** `python scripts/check_docs.py --stage after`
- **Session file:** `docs/bob-sessions/09-after-docs.md`

**Prompt**
```text
Task T9 from BOB_TASKS.md. Document what changed between tag baseline-before and now.

1. docs/after/improvements.md: a summary; a traceability table with one row for every B-xx in
   docs/baseline/known-bugs.md and every S-xx in docs/baseline/security-audit.md (problem, fix with
   file.py:line, test, status); and a before/after table (test count and pass rate, OS support,
   bandit and pip-audit results, CI, new features). Re-run the tools and tests to get the "after"
   numbers; take the "before" numbers from docs/baseline/.
2. README.md: correct the OS support claims to match the code and CI, and document --text,
   --dry-run, the confirmation settings, PORCUPINE_ACCESS_KEY and the playground.

Use `git diff baseline-before --stat` and the session notes in docs/bob-sessions/. Finish when
`python scripts/check_docs.py --stage after` passes.
```
