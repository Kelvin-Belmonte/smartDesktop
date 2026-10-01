# Session 02: T2 Security and safety audit

- **Date:** 2026-09-30
- **Mode:** 🛡️ SD Auditor
- **Files edited:** `docs/baseline/security-audit.md`
- **Accept command and result:** `python scripts/check_docs.py --stage security` → OK

## What Bob did

- Ran bandit 1.9.4 (17 issues: 5 High, 12 Low) and pip-audit (no known CVEs), and mapped every result to a finding.
- S-01 (Critical): AppleScript injection through an unescaped command string (`commands/terminal.py:51`).
- S-02 (Critical): Windows `cmd` injection through `shell=True` with config and transcript values (`commands/terminal.py:44`).
- S-03 to S-05 (High): `shell=True` on app paths (`apps.py:52`), no confirmation before destructive commands (`windows.py:136`), full transcripts logged at INFO (`speech/__init__.py:232`).
- S-06 to S-09 (Medium): plain-text Porcupine key, unpinned dependencies, substring matching that triggers macros from misheard audio, and Linux `bash -c` injection.

## Prompt

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

## Transcript

Exported from IBM Bob on 2026-09-30.

### 👤 User

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

### 🤖 Assistant

> 🔧 called: read_file, read_file

I'll start by reading the relevant files to understand the codebase before auditing.

> 🔧 **read_file** — BOB_TASKS.md

> 🔧 **read_file** — docs/baseline/security-audit.md

### 🤖 Assistant

> 🔧 called: list_files, read_file



> 🔧 **read_file** — scripts/check_docs.py

> 🔧 **list_files** — voice-assistant

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me read all the source files I need to audit:

> 🔧 **read_file** — voice-assistant/config.yaml

> 🔧 **read_file** — voice-assistant/main.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — voice-assistant/commands/apps.py

> 🔧 **read_file** — voice-assistant/commands/__init__.py

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



> 🔧 **read_file** — voice-assistant/smartdesktop.log

> 🔧 **read_file** — voice-assistant/requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command

Now I have a thorough understanding of the code. Let me set up a virtual environment and run the security tools:

> 🔧 **execute_command** — python3 -m venv .venv && .venv/bin/pip install --quiet bandit pip-audit 2>&1 | tail -5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/bandit -r voice-assistant -x voice-assistant/tests 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/pip-audit -r voice-assistant/requirements.txt 2>&1

### 🤖 Assistant

> 🔧 called: write_file

Now I have all the evidence I need. Let me write the complete security audit document:

> 🔧 **write_file** — docs/baseline/security-audit.md

### 🤖 Assistant

> 🔧 called: execute_command

Now run the acceptance check:

> 🔧 **execute_command** — python scripts/check_docs.py --stage security

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python3 scripts/check_docs.py --stage security

### 🤖 Assistant

The check passes. Here is a summary of the complete audit.

---

## T2 Security Audit — Summary

`python scripts/check_docs.py --stage security`: **OK** ✅

---

### What was reviewed

All Python source files (`main.py`, `commands/`, `speech/`, `wakeword/`), `config.yaml`, `requirements.txt`, and the log file — traced against the full data-flow from wake-word detection through transcript → command match → OS action.

Two tools were run against the venv:
- **bandit 1.9.4**: 17 issues (5 High, 12 Low), all mapped to findings below
- **pip-audit**: No known CVEs in current dependency versions

---

### Findings (by severity)

| ID | Severity | Location | Title |
|----|----------|----------|-------|
| **S-01** | Critical | [`commands/terminal.py:51`](../../voice-assistant/commands/terminal.py#L51) | AppleScript injection via unescaped command string |
| **S-02** | Critical | [`commands/terminal.py:44-47`](../../voice-assistant/commands/terminal.py#L44) | Windows `cmd` injection via `shell=True` with config/transcript values |
| **S-03** | High | [`commands/apps.py:52`](../../voice-assistant/commands/apps.py#L52), [`:55`](../../voice-assistant/commands/apps.py#L55) | `shell=True` with config-controlled app paths (macOS/Linux) |
| **S-04** | High | [`commands/windows.py:136`](../../voice-assistant/commands/windows.py#L136) | No confirmation for destructive commands (`close window`, macros) |
| **S-05** | High | [`speech/__init__.py:232`](../../voice-assistant/speech/__init__.py#L232) | Full transcript logged to file at INFO level |
| **S-06** | Medium | [`config.yaml:15`](../../voice-assistant/config.yaml#L15) | Porcupine key stored as plain string in config.yaml |
| **S-07** | Medium | [`requirements.txt:1`](../../voice-assistant/requirements.txt#L1) | Unpinned `>=` dependency versions — no lock file |
| **S-08** | Medium | [`commands/__init__.py:136-141`](../../voice-assistant/commands/__init__.py#L136) | Substring match triggers macros from ambient / misheard audio |
| **S-09** | Medium | [`commands/terminal.py:57-60`](../../voice-assistant/commands/terminal.py#L57) | Linux `bash -c` injection via unescaped command argument |

**S-01 / S-02** are the most severe: the `_run_in_terminal()` function interpolates arbitrary strings directly into an AppleScript `do script "…"` body and a Windows `cmd /K "…"` string. Any macro step from `config.yaml` (or a sufficiently long Whisper mis-transcription that substring-matches a macro phrase) can break out and execute arbitrary code on the host.
