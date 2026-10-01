"""
SmartDesktop Voice Assistant - Terminal / Shell Commands

Handles voice commands that run terminal operations:
  - Opening a terminal
  - Navigating to project directories
  - Running common developer commands (npm, git, python, etc.)
  - Custom macro sequences
"""

import logging
import os
import platform
import shlex
import subprocess
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_OS = platform.system()


# ---------------------------------------------------------------------------
# Low-level helper
# ---------------------------------------------------------------------------

def _run_in_terminal(command: str, cwd: Optional[str] = None, dry_run: bool = False) -> bool:
    """
    Run ``command`` in a new visible terminal window.

    On Windows, opens a new cmd window. On macOS, opens Terminal.app.
    On Linux, tries common terminal emulators.

    Args:
        command:  Shell command string to execute.
        cwd:      Optional working directory for the command.
        dry_run:  If True, log the intended action but perform no OS operation.

    Returns:
        True if the terminal process was started (or dry_run is True), False otherwise.
    """
    expanded_cwd = os.path.expanduser(cwd) if cwd else None

    if dry_run:
        logger.info("[dry-run] Would run in terminal: %s (cwd=%s)", command, expanded_cwd)
        return True

    try:
        if _OS == "Windows":
            subprocess.Popen(
                ["cmd", "/K", command],
                cwd=expanded_cwd,
            )
        elif _OS == "Darwin":
            # Pass command safely as argument to AppleScript to prevent injection
            subprocess.Popen(
                [
                    "osascript",
                    "-e",
                    "on run argv\ntell application \"Terminal\" to do script (item 1 of argv)\nend run",
                    "--",
                    command,
                ],
                cwd=expanded_cwd,
            )
        else:
            # Linux: try common terminal emulators in order
            for term in ["gnome-terminal", "xterm", "konsole", "x-terminal-emulator"]:
                if _which(term):
                    subprocess.Popen(
                        [term, "--", "bash", "-c", "$0; exec bash", command],
                        cwd=expanded_cwd,
                    )
                    break
            else:
                logger.error("No supported terminal emulator found.")
                return False
        logger.info("Ran in terminal: %s (cwd=%s)", command, expanded_cwd)
        return True
    except (OSError, ValueError) as exc:
        logger.error("Failed to run terminal command '%s': %s", command, exc)
        return False


def _which(program: str) -> Optional[str]:
    """Return the full path of ``program`` if it exists on PATH, else None."""
    import shutil
    return shutil.which(program)


def _run_background(command: str, cwd: Optional[str] = None, dry_run: bool = False) -> bool:
    """
    Run ``command`` silently in the background (no new terminal window).

    Args:
        command:  Shell command string.
        cwd:      Optional working directory.
        dry_run:  If True, log the intended action but perform no OS operation.

    Returns:
        True if the process was started (or dry_run is True), False otherwise.
    """
    expanded_cwd = os.path.expanduser(cwd) if cwd else None

    if dry_run:
        logger.info("[dry-run] Would run in background: %s (cwd=%s)", command, expanded_cwd)
        return True

    try:
        args = shlex.split(command, posix=(_OS != "Windows")) if isinstance(command, str) else command
        subprocess.Popen(
            args,
            cwd=expanded_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Background command started: %s", command)
        return True
    except (OSError, ValueError) as exc:
        logger.error("Failed to run background command '%s': %s", command, exc)
        return False


# ---------------------------------------------------------------------------
# Built-in terminal command handlers
# ---------------------------------------------------------------------------

def open_terminal_here(dry_run: bool = False) -> bool:
    """Open a terminal in the current working directory."""
    return _run_in_terminal("echo Terminal ready", dry_run=dry_run)


def git_status(dry_run: bool = False) -> bool:
    """Run 'git status' in a new terminal window."""
    return _run_in_terminal("git status", dry_run=dry_run)


def git_pull(dry_run: bool = False) -> bool:
    """Run 'git pull' in a new terminal window."""
    return _run_in_terminal("git pull", dry_run=dry_run)


def run_npm_start(dry_run: bool = False) -> bool:
    """Run 'npm start' in a new terminal window."""
    return _run_in_terminal("npm start", dry_run=dry_run)


def run_npm_dev(dry_run: bool = False) -> bool:
    """Run 'npm run dev' in a new terminal window."""
    return _run_in_terminal("npm run dev", dry_run=dry_run)


def run_npm_test(dry_run: bool = False) -> bool:
    """Run 'npm test' in a new terminal window."""
    return _run_in_terminal("npm test", dry_run=dry_run)


def run_npm_build(dry_run: bool = False) -> bool:
    """Run 'npm run build' in a new terminal window."""
    return _run_in_terminal("npm run build", dry_run=dry_run)


def run_python_main(dry_run: bool = False) -> bool:
    """Run 'python main.py' in a new terminal window."""
    return _run_in_terminal("python main.py", dry_run=dry_run)


def run_tests(dry_run: bool = False) -> bool:
    """Run pytest in a new terminal window."""
    return _run_in_terminal("pytest", dry_run=dry_run)


# ---------------------------------------------------------------------------
# Project navigation
# ---------------------------------------------------------------------------

def go_to_project(path: str, dry_run: bool = False) -> bool:
    """
    Open a terminal navigated to ``path`` and launch VS Code there.

    Args:
        path:     Filesystem path (may contain ~ or environment variables).
        dry_run:  If True, log the intended action but perform no OS operation.

    Returns:
        True if the terminal was opened successfully.
    """
    expanded = os.path.expandvars(os.path.expanduser(path))
    return _run_in_terminal(
        f"cd {shlex.quote(expanded)} && code .", cwd=expanded, dry_run=dry_run
    )


# ---------------------------------------------------------------------------
# Factory: build command map from config
# ---------------------------------------------------------------------------

def build_terminal_commands(
    projects_config: Optional[Dict[str, str]] = None,
    macros_config: Optional[Dict[str, List[str]]] = None,
    parser=None,
    dry_run: bool = False,
) -> Dict[str, callable]:
    """
    Return a mapping of command phrases to terminal command handlers.

    Args:
        projects_config: Dict of {name: path} from config.yaml.
        macros_config:   Dict of {phrase: [command, ...]} from config.yaml.
        parser:          Optional CommandParser instance; if provided, macro steps are
                         dispatched through it instead of run as shell commands.
        dry_run:         If True, all handlers will perform no OS action.

    Returns:
        Dict mapping lowercase command phrase → callable.
    """
    if dry_run:
        commands: Dict[str, callable] = {
            # Git
            "git status":    (lambda: git_status(dry_run=True)),
            "git pull":      (lambda: git_pull(dry_run=True)),
            "show git status": (lambda: git_status(dry_run=True)),
            "pull latest":   (lambda: git_pull(dry_run=True)),
            # npm
            "run start":     (lambda: run_npm_start(dry_run=True)),
            "start server":  (lambda: run_npm_start(dry_run=True)),
            "run dev":       (lambda: run_npm_dev(dry_run=True)),
            "start dev":     (lambda: run_npm_dev(dry_run=True)),
            "run tests":     (lambda: run_tests(dry_run=True)),
            "run test":      (lambda: run_tests(dry_run=True)),
            "npm test":      (lambda: run_npm_test(dry_run=True)),
            "npm start":     (lambda: run_npm_start(dry_run=True)),
            "npm dev":       (lambda: run_npm_dev(dry_run=True)),
            "npm build":     (lambda: run_npm_build(dry_run=True)),
            "run build":     (lambda: run_npm_build(dry_run=True)),
            # Python
            "run python":    (lambda: run_python_main(dry_run=True)),
            "run main":      (lambda: run_python_main(dry_run=True)),
            # Pytest
            "run pytest":    (lambda: run_tests(dry_run=True)),
        }
    else:
        commands = {
            # Git
            "git status":    git_status,
            "git pull":      git_pull,
            "show git status": git_status,
            "pull latest":   git_pull,
            # npm
            "run start":     run_npm_start,
            "start server":  run_npm_start,
            "run dev":       run_npm_dev,
            "start dev":     run_npm_dev,
            "run tests":     run_tests,
            "run test":      run_tests,
            "npm test":      run_npm_test,
            "npm start":     run_npm_start,
            "npm dev":       run_npm_dev,
            "npm build":     run_npm_build,
            "run build":     run_npm_build,
            # Python
            "run python":    run_python_main,
            "run main":      run_python_main,
            # Pytest
            "run pytest":    run_tests,
        }

    # Project shortcuts — "go to <name>"
    if projects_config:
        for name, path in projects_config.items():
            phrase = f"go to {name.lower()}"
            commands[phrase] = (lambda p, dr=dry_run: lambda: go_to_project(p, dry_run=dr))(path)
            logger.debug("Registered project command: '%s' → %s", phrase, path)

    # Macro sequences — dispatch each step through the assistant parser when
    # available, otherwise fall back to running the step as a shell command.
    if macros_config:
        for phrase, steps in macros_config.items():
            def _make_macro(step_list: List[str], _parser=parser, _dry_run=dry_run) -> callable:
                def _run_macro() -> bool:
                    success = True
                    for step in step_list:
                        if _parser is not None:
                            success = _parser.execute(step) and success
                        else:
                            success = _run_in_terminal(step, dry_run=_dry_run) and success
                    return success
                return _run_macro
            commands[phrase.lower()] = _make_macro(steps)
            logger.debug("Registered macro: '%s' (%d steps)", phrase, len(steps))

    return commands
