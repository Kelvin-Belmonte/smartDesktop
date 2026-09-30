#!/usr/bin/env python3
"""Acceptance checks for the IBM Bob tasks in BOB_TASKS.md (stdlib only).

Usage: python scripts/check_docs.py --stage {baseline,security,bugs,fixes,after,all}
Exit code 0 means the stage passes. Every failure is printed with the file it is about.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "docs" / "baseline"
AFTER = ROOT / "docs" / "after"
BUG_TESTS = ROOT / "voice-assistant" / "tests" / "bob" / "test_bugs.py"

TODO = "TODO(bob)"
S_ID = re.compile(r"\bS-\d{2}\b")
B_ID = re.compile(r"\bB-\d{2}\b")
FILE_LINE = re.compile(r"[\w/.-]+\.py:\d+")


def _read(path: Path, errors: list) -> str:
    if not path.is_file():
        errors.append(f"{_rel(path)}: file is missing")
        return ""
    return path.read_text(encoding="utf-8")


def _ids(pattern: re.Pattern, text: str) -> set:
    """Ids in text, ignoring template lines that still carry a TODO(bob) marker."""
    done = "\n".join(line for line in text.splitlines() if TODO not in line)
    return set(pattern.findall(done))


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _common(path: Path, headings: list, errors: list) -> str:
    text = _read(path, errors)
    if not text:
        return text
    todos = text.count(TODO)
    if todos:
        errors.append(f"{_rel(path)}: {todos} {TODO} marker(s) left")
    for h in headings:
        if not re.search(rf"^{re.escape(h)}\s*$", text, re.MULTILINE):
            errors.append(f"{_rel(path)}: required heading missing: {h!r}")
    return text


def check_baseline(errors: list) -> None:
    path = BASELINE / "overview.md"
    text = _common(
        path,
        ["## Architecture", "## Command catalog", "## OS support matrix", "## Does it run?"],
        errors,
    )
    if text and "```mermaid" not in text:
        errors.append(f"{_rel(path)}: needs a ```mermaid pipeline diagram under Architecture")
    if text and len(FILE_LINE.findall(text)) < 5:
        errors.append(f"{_rel(path)}: cite at least 5 source locations as file.py:line")
    if text and "--list-commands" not in text:
        errors.append(f"{_rel(path)}: 'Does it run?' must include the `--list-commands` result")


def check_security(errors: list) -> None:
    path = BASELINE / "security-audit.md"
    text = _common(path, ["## Scope and method", "## Findings", "## Tool output"], errors)
    if not text:
        return
    ids = _ids(S_ID, text)
    if len(ids) < 3:
        errors.append(f"{_rel(path)}: expected at least 3 findings with ids S-01, S-02, ...")
    for tool in ("bandit", "pip-audit"):
        if tool not in text:
            errors.append(f"{_rel(path)}: Tool output must include {tool} results")
    if len(FILE_LINE.findall(text)) < len(ids):
        errors.append(f"{_rel(path)}: every finding needs at least one file.py:line citation")


def _bug_ids(errors: list) -> set:
    path = BASELINE / "known-bugs.md"
    text = _common(path, ["## Bugs", "## How to reproduce"], errors)
    ids = _ids(B_ID, text)
    if text and len(ids) < 3:
        errors.append(f"{_rel(path)}: expected at least 3 bugs with ids B-01, B-02, ...")
    return ids


def check_bugs(errors: list) -> None:
    ids = _bug_ids(errors)
    tests = _read(BUG_TESTS, errors)
    if not tests:
        return
    for bug in sorted(ids):
        if bug not in tests:
            errors.append(f"{_rel(BUG_TESTS)}: no test references {bug}")
    xfails = len(re.findall(r"xfail\(\s*strict\s*=\s*True", tests))
    if xfails < len(ids):
        errors.append(
            f"{_rel(BUG_TESTS)}: {len(ids)} bugs but only {xfails} xfail(strict=True) markers"
        )


def check_fixes(errors: list) -> None:
    ids = _bug_ids(errors)
    tests = _read(BUG_TESTS, errors)
    if not tests:
        return
    if "xfail" in tests:
        errors.append(f"{_rel(BUG_TESTS)}: xfail marker(s) still present; fix the bug, then remove them")
    for bug in sorted(ids):
        if bug not in tests:
            errors.append(f"{_rel(BUG_TESTS)}: test for {bug} was removed")


def check_after(errors: list) -> None:
    path = AFTER / "improvements.md"
    text = _common(path, ["## Summary", "## Traceability", "## Before and after"], errors)
    if not text:
        return
    audit = (BASELINE / "security-audit.md").read_text(encoding="utf-8") if (BASELINE / "security-audit.md").is_file() else ""
    bugs = (BASELINE / "known-bugs.md").read_text(encoding="utf-8") if (BASELINE / "known-bugs.md").is_file() else ""
    for finding in sorted(_ids(S_ID, audit) | _ids(B_ID, bugs)):
        if finding not in text:
            errors.append(f"{_rel(path)}: {finding} is not in the traceability table")


STAGES = {
    "baseline": [check_baseline],
    "security": [check_security],
    "bugs": [check_bugs],
    "fixes": [check_fixes],
    "after": [check_after],
}
STAGES["all"] = [c for s in ("baseline", "security", "fixes", "after") for c in STAGES[s]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", required=True, choices=sorted(STAGES))
    args = parser.parse_args()

    errors: list = []
    for check in STAGES[args.stage]:
        check(errors)

    if errors:
        print(f"check_docs --stage {args.stage}: FAIL ({len(errors)} problem(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"check_docs --stage {args.stage}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
