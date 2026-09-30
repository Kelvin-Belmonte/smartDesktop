# smartDesktop guardrails (all modes)

1. Do ONLY the current task in `BOB_TASKS.md`, in the mode it names. Do not start the next task unless asked.
2. `docs/baseline/` records the code at tag `baseline-before`. Once T3 is committed, never edit it again:
   results from later tasks go in `docs/after/`.
3. Never weaken, skip, or delete a test to make a check pass. The only allowed change to
   `voice-assistant/tests/bob/test_bugs.py` in T4 is removing the `xfail` marker of a bug you fixed.
4. Tests must never perform real OS actions: no launching apps, moving windows, opening terminals,
   or running shell commands. Mock `subprocess`, `os.startfile`, `pyautogui`, `pygetwindow` and `ctypes`.
5. Never run the real assistant (`python main.py` without `--list-commands`, `--text --dry-run`, or `--help`)
   while you work: it can open apps and run commands on this machine.
6. Edit only the files your mode allows. Do not use the terminal to change any other file.
   Never commit, push, or change git history.
7. Never commit secrets. The Porcupine key stays a placeholder in `config.yaml`.
8. Cite evidence as `file.py:line` and quote the commands you ran and their output.
9. After each change, run the task's Accept command. A task is finished only when it passes.
10. Explain what you changed and why, citing the B-xx / S-xx ids. This transcript is shown to the judges.
