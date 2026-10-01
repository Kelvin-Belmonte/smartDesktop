# smartDesktop: security and safety audit (baseline)

Written by IBM Bob in task T2 (🛡️ SD Auditor), against commit `992e4dc` (tag `baseline-before`).

## Scope and method

**Files reviewed:** `voice-assistant/main.py`, `voice-assistant/config.yaml`,
`voice-assistant/commands/__init__.py`, `voice-assistant/commands/apps.py`,
`voice-assistant/commands/terminal.py`, `voice-assistant/commands/windows.py`,
`voice-assistant/speech/__init__.py`, `voice-assistant/wakeword/__init__.py`,
`voice-assistant/requirements.txt`, `voice-assistant/smartdesktop.log`.

**Threat model:**

1. *Proximity attacker* — anyone near the microphone (or an audio feed) can speak commands. There is
   no speaker verification, no PIN, and no confirmation prompt before any action is executed.
2. *Mishearing / adversarial transcription* — Whisper can transcribe ambient speech or background
   audio into a valid command string. Macro steps are arbitrary strings taken from `config.yaml`
   and executed verbatim.
3. *Config injection* — `config.yaml` is loaded without schema validation. An attacker who can
   write or substitute the config file controls values that flow directly into `subprocess` calls
   with `shell=True`, AppleScript bodies, and Windows `cmd /K` strings.
4. *Log exfiltration* — transcripts are written to a file (`smartdesktop.log`) at INFO level without
   redaction; anyone who can read that file learns what was spoken.
5. *Credential exposure* — the Porcupine access key is stored as a plain string in `config.yaml`,
   which may be committed to version control.

**Tools run:**

- `bandit -r voice-assistant -x voice-assistant/tests` (bandit 1.9.4, Python 3.14.7)
- `pip-audit -r voice-assistant/requirements.txt`

---

## Findings

### S-01: AppleScript injection via unescaped command string
- **Severity:** Critical
- **Location:** `commands/terminal.py:51`
- **Description:** The `_run_in_terminal()` helper builds an AppleScript `do script` command by
  directly f-string-interpolating the `command` argument into an AppleScript literal:
  ```python
  script = f'tell application "Terminal" to do script "{command}"'
  subprocess.Popen(["osascript", "-e", script], cwd=expanded_cwd)
  ```
  If `command` contains a double-quote or a backslash (e.g. a macro step such as
  `run echo "hello"` from `config.yaml`), the embedded character breaks out of the AppleScript
  string and arbitrary AppleScript — including shell execution via `do shell script` — can be
  injected. The `macros_config` entries are joined directly from the YAML file; any value there
  flows into this interpolation with no sanitisation.
- **Impact:** Arbitrary AppleScript / shell code execution on macOS. A crafted `config.yaml` macro
  or a Whisper mis-transcription that matches a registered macro step can run any command as the
  current user.
- **Recommendation:** Pass the command as an AppleScript variable rather than interpolating it into
  the script body. Escape at minimum `\` and `"` before interpolation, or use the `-e` argument
  multiple times to avoid the need for string quoting:
  ```python
  script = f"tell application \"Terminal\" to do script {shlex.quote(command)}"
  ```
  For full safety, pass the command string as a positional parameter and reference it via
  `$1` inside a shell heredoc: `osascript -e 'on run argv' -e 'tell app "Terminal" to do script (item 1 of argv)' -e 'end run' -- <cmd>`.

---

### S-02: Windows cmd injection via shell=True with unvalidated config / transcript values
- **Severity:** Critical
- **Location:** `commands/terminal.py:44-47`, `commands/terminal.py:91-97`
- **Description:** `_run_in_terminal()` on Windows builds:
  ```python
  subprocess.Popen(f'start cmd /K "{command}"', shell=True, ...)
  ```
  and `_run_background()` passes the command string directly to `subprocess.Popen(..., shell=True)`.
  The `command` value originates either from a hardcoded built-in (safe) or from a
  `macros_config` step read from `config.yaml` without any validation. A macro step such as
  `"git status" & cmd /c del /q /s C:\` exploits the shell metacharacters admitted by `shell=True`.
  Additionally, the macro steps are registered with `CommandParser` and dispatched when a
  transcript matches the macro phrase; a mis-transcribed phrase that happens to substring-match a
  macro name silently runs all its steps.
- **Impact:** Arbitrary shell command execution on Windows. Config tampering or a substring match
  in the `CommandParser` can trigger destructive operations with no confirmation.
- **Recommendation:** Avoid `shell=True` entirely. On Windows, use `subprocess.Popen(["cmd", "/K", command])`.
  Validate macro step values against an allowlist of recognised built-in command phrases before
  registering them. Add a confirmation step for any macro execution.

---

### S-03: shell=True with config-controlled app paths on macOS and Linux
- **Severity:** High
- **Location:** `commands/apps.py:52`, `commands/apps.py:55`
- **Description:** `_open_app()` falls back to `subprocess.Popen(app_path, shell=True)` when the
  path does not end in `.app` and contains a `/` on macOS, or on any Linux path. The `app_path`
  value is built from `config.yaml → commands.apps` via `os.path.expandvars` and
  `os.path.expanduser`, which themselves can introduce attacker-controlled data through environment
  variables. A config entry such as:
  ```yaml
  apps:
    discord: "C:/… --processStart Discord.exe; rm -rf ~"
  ```
  will be executed verbatim by the shell.
- **Impact:** Arbitrary command execution. An attacker who can edit `config.yaml`, or inject an
  environment variable that is referenced by a path, can run any shell command as the assistant's
  user.
- **Recommendation:** Replace `shell=True` with a list-form `Popen` after splitting the path with
  `shlex.split()`. Validate that paths read from config resolve to actual executables before use.
  On macOS, use `["open", "-a", app_path]` for all app names, not just `.app`-suffixed ones.

---

### S-04: No confirmation for destructive or high-impact commands
- **Severity:** High
- **Location:** `commands/windows.py:136`, `commands/__init__.py:65-96`, `commands/terminal.py:226-233`
- **Description:** Destructive or high-impact voice commands — `close window`, `swap monitors`,
  macro sequences that run shell commands — are executed immediately on transcript match with no
  confirmation step. The `CommandParser._match()` method uses a substring rule: if any registered
  phrase is a substring of the transcript, it fires. This means ambient speech such as
  "did I close window earlier?" matches `close window` and closes the active window.
- **Impact:** A casual comment, a misheard phrase, or a background radio broadcast can silently
  close application windows or run a multi-step macro (e.g. `start dev` → `open terminal` then
  `run npm run dev`). No undo mechanism exists.
- **Recommendation:** Introduce a confirmation flag (configurable in `config.yaml`) for commands
  tagged as destructive. In text mode, print "Confirm [command]? (y/n)". In voice mode, speak a
  confirmation prompt and require a second utterance. Skip confirmation in `dry_run` mode.

---

### S-05: Full transcript logged to a file at INFO level
- **Severity:** High
- **Location:** `speech/__init__.py:232`, `main.py:181`
- **Description:** Every transcribed utterance is logged at INFO level:
  - `speech/__init__.py:232`: `logger.info("Transcription: '%s'", transcript)`
  - `main.py:181`: `_info(f'You said: "{transcript}"')` (which also prints to stdout)

  `config.yaml` sets `logging.level: INFO` and `logging.file: "smartdesktop.log"`, so every spoken
  phrase is written verbatim to disk at runtime. If the user accidentally speaks a password, a
  credit-card number, or other sensitive information near the microphone, it is recorded in
  plaintext in the log file.
- **Impact:** Persistent plaintext capture of everything spoken near the device. The log file is
  written to the working directory with no access controls and no rotation.
- **Recommendation:** Log transcripts only at DEBUG level. Redact or truncate transcript text at
  INFO level (e.g., show the matched command rather than the raw transcript). Add a
  `logrotate`-compatible `maxBytes` / `backupCount` handler, and document that the log file
  contains spoken phrases.

---

### S-06: Porcupine access key stored as a plain string in config.yaml
- **Severity:** Medium
- **Location:** `config.yaml:15`, `main.py:136-138`
- **Description:** The config file ships with `access_key: "YOUR_PORCUPINE_ACCESS_KEY"` and the
  code comment encourages users to paste their real key directly into that field. The code does
  call `os.path.expandvars()` to support the `${PORCUPINE_ACCESS_KEY}` pattern, but this is
  optional and not the default. In practice, any user who follows the simplest path commits their
  API key to version control alongside `config.yaml`. The `.gitignore` in `voice-assistant/`
  does not exclude `config.yaml`.
- **Impact:** The Porcupine API key, once committed to a public or shared repository, is exposed
  indefinitely. The key can be used by third parties to exhaust the account's free quota or
  access associated Picovoice account data.
- **Recommendation:** Remove the plain-key option. Read the key exclusively from the
  `PORCUPINE_ACCESS_KEY` environment variable (already partially supported in `main.py:138`).
  Document this in `README.md` and add `config.yaml` to `.gitignore` (or ship only a
  `config.yaml.example` with a placeholder).

---

### S-07: Unpinned dependency versions in requirements.txt
- **Severity:** Medium
- **Location:** `requirements.txt:1-21`
- **Description:** Every dependency is specified with a `>=` lower-bound only, e.g.
  `faster-whisper>=1.0.0`, `pvporcupine>=3.0.0`. This means `pip install` will always fetch the
  newest available version, which could introduce breaking changes or newly-discovered
  vulnerabilities without any human review. There is no lock file (`pip freeze` output or
  `poetry.lock`).
- **Impact:** A compromised or newly-vulnerable release of any dependency (e.g. `pyaudio`,
  `faster-whisper`, `pyautogui`) is automatically pulled in on the next fresh install, potentially
  exposing the host machine to malicious code or exploitable bugs.
- **Recommendation:** Pin every dependency to an exact version (`==`) verified against a known-good
  build. Commit a `requirements.lock` generated by `pip-audit` or `pip freeze`. Re-evaluate pins
  when a security advisory is published.

---

### S-08: Misheard phrase can trigger arbitrary macro steps without warning
- **Severity:** Medium
- **Location:** `commands/__init__.py:136-141`, `commands/terminal.py:224-232`
- **Description:** The `CommandParser._match()` substring rule fires the longest registered phrase
  that appears *anywhere inside* the transcript — not just at the start. Macro phrases such as
  `"start dev"` and `"morning routine"` (from `config.yaml`) are registered as top-level
  commands. Because Whisper sometimes produces verbose transcriptions (e.g. "I'd like you to
  start dev please"), the substring rule will fire `start dev`, which runs two shell commands:
  `open terminal` then `run npm run dev`. There is no guard against recursive matching (a macro
  step that itself matches another macro).
- **Impact:** Background audio, filler phrases, or partial sentences spoken near the microphone
  can silently trigger multi-step shell-command macros. On the default config this opens a
  terminal and runs `npm run dev` in it.
- **Recommendation:** Require an exact match for macro phrases, or anchor matching to the
  beginning of the transcript after the prefix is stripped. Require user confirmation before
  running any macro. Log a visible warning whenever a substring match (rather than an exact match)
  fires a command.

---

### S-09: Linux terminal command injection via bash -c with unescaped argument
- **Severity:** Medium
- **Location:** `commands/terminal.py:57-60`
- **Description:** On Linux, `_run_in_terminal()` passes the command string to bash via:
  ```python
  subprocess.Popen([term, "--", "bash", "-c", f"{command}; exec bash"], ...)
  ```
  Because `command` is not quoted or escaped before concatenation into the `bash -c` string, any
  shell metacharacter in `command` (semicolons, pipes, backticks, `$(...)`) is interpreted by bash.
  A macro step of `echo hi; rm -rf ~/important` would be executed as two separate shell commands.
- **Impact:** Shell command injection on Linux. A crafted macro step or a command string
  containing shell metacharacters can run arbitrary commands as the current user.
- **Recommendation:** Pass `command` as a separate argument rather than embedding it in the
  `-c` string: `["bash", "-c", "$0; exec bash", "--", command]` so that `$0` is the command and
  no metacharacter expansion occurs. Alternatively, use `shlex.quote(command)` before embedding.

---

## Tool output

### bandit — `bandit -r voice-assistant -x voice-assistant/tests`

Run date: 2026-09-30. Total lines of code scanned: 1 178. Total issues: 17 (5 High, 12 Low).

| Bandit ID | Severity | Location | S-xx mapping |
|-----------|----------|----------|--------------|
| B602 | High | `commands/apps.py:46` | S-03 |
| B602 | High | `commands/apps.py:52` | S-03 |
| B602 | High | `commands/apps.py:55` | S-03 |
| B602 | High | `commands/terminal.py:46` | S-02 |
| B602 | High | `commands/terminal.py:93` | S-02 |
| B603 | Low | `commands/apps.py:50` | S-03 |
| B603 | Low | `commands/terminal.py:52` | S-01 |
| B603 | Low | `commands/terminal.py:57` | S-09 |
| B603 | Low | `commands/windows.py:261` | (informational — fixed args) |
| B404 | Low | `commands/apps.py:10` | S-02, S-03 |
| B404 | Low | `commands/terminal.py:15` | S-01, S-02 |
| B404 | Low | `commands/windows.py:16` | (informational) |
| B606 | Low | `commands/apps.py:41` | (informational — `os.startfile`) |
| B607 | Low | `commands/apps.py:50` | S-03 |
| B607 | Low | `commands/terminal.py:52` | S-01 |
| B607 | Low | `commands/windows.py:261` | (informational) |
| B110 | Low | `commands/windows.py:224` | (informational — silent except pass) |

Key patterns: 5 × B602 (`shell=True`) map directly to S-02 and S-03 (command injection).
B603 at `terminal.py:52` maps to S-01 (AppleScript injection — the subprocess call is safe, but
the script string it passes is not). B603 at `terminal.py:57` maps to S-09 (Linux bash injection).

---

### pip-audit — `pip-audit -r voice-assistant/requirements.txt`

Run date: 2026-09-30. Result: **No known vulnerabilities found** against the installed versions.

All packages resolved to current latest releases with no CVE matches in the OSV/PyPI advisory
database at the time of the scan. This does **not** reduce S-07: the packages are unpinned, so a
future `pip install` can pull in a vulnerable release without any change to `requirements.txt`.
