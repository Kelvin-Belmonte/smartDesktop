"""
SmartDesktop Voice Assistant - Application Launcher Commands

Handles voice commands that open applications.
"""

import logging
import os
import platform
import shlex
import shutil
import subprocess
import sys
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Detect the current operating system
_OS = platform.system()  # "Windows", "Darwin" (macOS), or "Linux"

# ---------------------------------------------------------------------------
# Platform-keyed target data (single source of truth for both execution and plan)
# ---------------------------------------------------------------------------

# Maps platform.system() key → app target string used by _open_app.
# "Linux" entries use the first candidate from the emulator list; plan() uses the same.
_APP_TARGETS: Dict[str, Dict[str, str]] = {
    "open chrome": {
        "Windows": "start chrome",
        "Darwin": "Google Chrome",
        "Linux": "google-chrome",
    },
    "open firefox": {
        "Windows": "start firefox",
        "Darwin": "Firefox",
        "Linux": "firefox",
    },
    "open terminal": {
        "Windows": "start cmd",
        "Darwin": "Terminal",
        "Linux": "gnome-terminal",  # first candidate; runtime falls back if absent
    },
    "open vscode": {
        "Windows": "code",
        "Darwin": "code",
        "Linux": "code",
    },
    "open file manager": {
        "Windows": "explorer",
        "Darwin": "Finder",
        "Linux": "xdg-open .",
    },
    "open calculator": {
        "Windows": "calc",
        "Darwin": "Calculator",
        "Linux": "gnome-calculator",
    },
    "open spotify": {
        "Windows": "start spotify",   # plan uses fallback; runtime tries known paths first
        "Darwin": "Spotify",
        "Linux": "spotify",
    },
    "play liked songs": {
        "Windows": "start spotify:collection",
        "Darwin": "open spotify:collection",
        "Linux": "xdg-open spotify:collection",
    },
    "open discord": {
        "Windows": "start discord",
        "Darwin": "Discord",
        "Linux": "discord",
    },
    "open slack": {
        "Windows": "start slack",
        "Darwin": "Slack",
        "Linux": "slack",
    },
    "open new window": {  # alias for chrome
        "Windows": "start chrome",
        "Darwin": "Google Chrome",
        "Linux": "google-chrome",
    },
}
# Aliases that share target data with another entry
_APP_ALIASES: Dict[str, str] = {
    "open vs code":        "open vscode",
    "open code":           "open vscode",
    "open explorer":       "open file manager",
    "play my liked songs": "play liked songs",
    "spotify liked songs": "play liked songs",
    "open liked songs":    "play liked songs",
}


# Maps canonical lowercase os key → _APP_TARGETS key
_OS_TO_TARGETS_KEY = {"windows": "Windows", "macos": "Darwin", "linux": "Linux"}


def _app_target(phrase: str, os_name: str) -> str:
    """Return the launch target for *phrase* on *os_name* (lowercase: windows/macos/linux)."""
    canonical = _APP_ALIASES.get(phrase, phrase)
    targets = _APP_TARGETS.get(canonical, {})
    sys_key = _OS_TO_TARGETS_KEY.get(os_name, "Linux")
    return targets.get(sys_key, targets.get("Linux", ""))


def plan_app_command(phrase: str, os_name: str) -> Optional[dict]:
    """
    Return a plan dict for *phrase* as an app-launch command on *os_name*.

    *os_name* is the canonical lowercase key: ``"windows"``, ``"macos"``, or ``"linux"``.
    Returns None if *phrase* is not a known app command.
    """
    canonical = _APP_ALIASES.get(phrase, phrase)
    if canonical not in _APP_TARGETS:
        return None
    target = _app_target(phrase, os_name)
    return {
        "action": "launch",
        "target": target,
        "platform": os_name,
    }


def _open_app(app_path: str, dry_run: bool = False) -> bool:
    """
    Launch an application using the most appropriate method for the current OS.

    Args:
        app_path: Executable path, application name, or shell command string.
        dry_run:  If True, log the intended action but perform no OS operation.

    Returns:
        True if the process was started successfully (or dry_run is True), False otherwise.
    """
    if dry_run:
        logger.info("[dry-run] Would launch application: %s", app_path)
        return True

    try:
        if _OS == "Windows":
            # Normalise forward slashes so Windows can find the file.
            normalized = app_path.replace("/", "\\")
            if os.path.isfile(normalized):
                # Use os.startfile (ShellExecuteEx) so Windows sets the
                # working directory to the app's own folder and resolves
                # DLL / resource paths correctly – identical to double-clicking
                # the file in Explorer.  Any OSError (e.g. if the file
                # disappears between the isfile check and the launch) is
                # caught by the outer except block below.
                os.startfile(normalized)
            else:
                # Parse into arguments to avoid shell=True
                args = shlex.split(app_path, posix=False)
                subprocess.Popen(args)
        elif _OS == "Darwin":
            # macOS: use 'open -a' only for bare application names (no slashes,
            # no spaces/arguments) or explicit .app bundles without a path.
            # Anything else (paths, commands with arguments) runs as argument list without shell=True.
            bare_name = "/" not in app_path and " " not in app_path
            if app_path.endswith(".app") or bare_name:
                subprocess.Popen(["open", "-a", app_path])
            else:
                args = shlex.split(app_path)
                subprocess.Popen(args)
        else:
            # Linux / other POSIX: split arguments without shell=True
            args = shlex.split(app_path)
            subprocess.Popen(args)
        logger.info("Launched application: %s", app_path)
        return True
    except (OSError, ValueError) as exc:
        logger.error("Failed to launch '%s': %s", app_path, exc)
        return False


# ---------------------------------------------------------------------------
# Built-in command handlers
# ---------------------------------------------------------------------------

def open_chrome(dry_run: bool = False) -> bool:
    """Open Google Chrome."""
    paths = _APP_TARGETS["open chrome"]
    return _open_app(paths.get(_OS, "chrome"), dry_run=dry_run)


def open_firefox(dry_run: bool = False) -> bool:
    """Open Mozilla Firefox."""
    paths = _APP_TARGETS["open firefox"]
    return _open_app(paths.get(_OS, "firefox"), dry_run=dry_run)


def open_terminal(dry_run: bool = False) -> bool:
    """Open the system terminal / command prompt."""
    if _OS == "Linux":
        # Try emulators in the same order as _run_in_terminal so the choice
        # is consistent.  Fall back to xterm only when nothing else is found.
        for term in ["gnome-terminal", "xterm", "konsole", "x-terminal-emulator"]:
            if shutil.which(term):
                return _open_app(term) if not dry_run else _open_app(term, dry_run=True)
        return _open_app("xterm") if not dry_run else _open_app("xterm", dry_run=True)
    paths = _APP_TARGETS["open terminal"]
    target = paths.get(_OS, "xterm")
    return _open_app(target) if not dry_run else _open_app(target, dry_run=True)


def open_vscode(dry_run: bool = False) -> bool:
    """Open Visual Studio Code."""
    return _open_app("code", dry_run=dry_run)


def open_file_manager(dry_run: bool = False) -> bool:
    """Open the system file manager."""
    paths = _APP_TARGETS["open file manager"]
    return _open_app(paths.get(_OS, "xdg-open ."), dry_run=dry_run)


def open_calculator(dry_run: bool = False) -> bool:
    """Open the system calculator."""
    paths = _APP_TARGETS["open calculator"]
    return _open_app(paths.get(_OS, "gnome-calculator"), dry_run=dry_run)


def open_spotify(dry_run: bool = False) -> bool:
    """Open Spotify, trying known install locations before falling back to the
    'start' shell command so the app reliably launches on Windows regardless
    of whether Spotify was installed from the web or the Microsoft Store."""
    if _OS == "Windows":
        candidates = [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return _open_app(candidate, dry_run=dry_run)
        # Fall back: works when Spotify is registered as a URI handler or is
        # findable on PATH.
        return _open_app("start spotify", dry_run=dry_run)
    paths = _APP_TARGETS["open spotify"]
    return _open_app(paths.get(_OS, "spotify"), dry_run=dry_run)


def play_spotify_liked_songs(dry_run: bool = False) -> bool:
    """Open Spotify and navigate to the liked-songs collection."""
    uris = _APP_TARGETS["play liked songs"]
    return _open_app(uris.get(_OS, "xdg-open spotify:collection"), dry_run=dry_run)


def open_discord(dry_run: bool = False) -> bool:
    """Open Discord."""
    paths = _APP_TARGETS["open discord"]
    return _open_app(paths.get(_OS, "discord"), dry_run=dry_run)


def open_slack(dry_run: bool = False) -> bool:
    """Open Slack."""
    paths = _APP_TARGETS["open slack"]
    return _open_app(paths.get(_OS, "slack"), dry_run=dry_run)


# ---------------------------------------------------------------------------
# Factory: build command map from config
# ---------------------------------------------------------------------------

def build_app_commands(
    apps_config: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, callable]:
    """
    Return a mapping of command phrases to callable handlers.

    Built-in commands are always included. If ``apps_config`` is provided
    (from config.yaml), custom app entries are added dynamically.

    Args:
        apps_config: Dict of {phrase: path/command} from the YAML config.
        dry_run:     If True, all handlers will perform no OS action.

    Returns:
        Dict mapping lowercase command phrase → callable that launches the app.
    """
    if dry_run:
        commands: Dict[str, callable] = {
            "open chrome":       (lambda: open_chrome(dry_run=True)),
            "open firefox":      (lambda: open_firefox(dry_run=True)),
            "open terminal":     (lambda: open_terminal(dry_run=True)),
            "open vscode":       (lambda: open_vscode(dry_run=True)),
            "open vs code":      (lambda: open_vscode(dry_run=True)),
            "open code":         (lambda: open_vscode(dry_run=True)),
            "open file manager": (lambda: open_file_manager(dry_run=True)),
            "open explorer":     (lambda: open_file_manager(dry_run=True)),
            "open calculator":   (lambda: open_calculator(dry_run=True)),
            "open spotify":      (lambda: open_spotify(dry_run=True)),
            "open discord":      (lambda: open_discord(dry_run=True)),
            "open slack":        (lambda: open_slack(dry_run=True)),
            "open new window":   (lambda: open_chrome(dry_run=True)),
            "play liked songs":        (lambda: play_spotify_liked_songs(dry_run=True)),
            "play my liked songs":     (lambda: play_spotify_liked_songs(dry_run=True)),
            "spotify liked songs":     (lambda: play_spotify_liked_songs(dry_run=True)),
            "open liked songs":        (lambda: play_spotify_liked_songs(dry_run=True)),
        }
    else:
        commands = {
            "open chrome":       open_chrome,
            "open firefox":      open_firefox,
            "open terminal":     open_terminal,
            "open vscode":       open_vscode,
            "open vs code":      open_vscode,
            "open code":         open_vscode,
            "open file manager": open_file_manager,
            "open explorer":     open_file_manager,
            "open calculator":   open_calculator,
            "open spotify":      open_spotify,
            "open discord":      open_discord,
            "open slack":        open_slack,
            "open new window":   open_chrome,
            "play liked songs":        play_spotify_liked_songs,
            "play my liked songs":     play_spotify_liked_songs,
            "spotify liked songs":     play_spotify_liked_songs,
            "open liked songs":        play_spotify_liked_songs,
        }

    # Inject custom app shortcuts from config.yaml.
    # Built-in commands are protected: if a custom entry would overwrite a
    # built-in phrase, log a warning and skip it.
    if apps_config:
        for keyword, path in apps_config.items():
            phrase = f"open {keyword.lower()}"
            if phrase in commands:
                logger.warning(
                    "Custom app '%s' conflicts with built-in command '%s'; skipping.",
                    keyword,
                    phrase,
                )
                continue
            app_path = os.path.expandvars(os.path.expanduser(path))
            # Create a closure that captures app_path and dry_run correctly
            commands[phrase] = (lambda p, dr=dry_run: lambda: _open_app(p, dry_run=dr))(app_path)
            logger.debug("Registered custom app command: '%s' → %s", phrase, app_path)

    return commands
