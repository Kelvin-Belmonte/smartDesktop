"""
SmartDesktop Voice Assistant - Command Registry

The ``CommandParser`` aggregates all command handlers (apps, windows, terminal)
and maps transcribed phrases to the appropriate action.

Command matching strategy (in priority order):
  1. Exact match after stripping the wake word prefix.
  2. Prefix / fuzzy substring match — the longest registered phrase that
     appears as a substring of the transcript wins.
  3. Unknown command → user-friendly feedback.
"""

import logging
import platform
from typing import Callable, Dict, Optional, Tuple

from commands.apps import build_app_commands, plan_app_command, _APP_TARGETS, _APP_ALIASES
from commands.terminal import build_terminal_commands, plan_terminal_command
from commands.windows import build_window_commands, plan_window_command

logger = logging.getLogger(__name__)

# Type alias
CommandMap = Dict[str, Callable[[], bool]]


# Default destructive phrases that require user confirmation when confirm_destructive is True
DESTRUCTIVE_COMMANDS = {
    "close window",
    "git pull",
    "pull latest",
    "run start",
    "start server",
    "run dev",
    "start dev",
    "run tests",
    "run test",
    "npm test",
    "npm start",
    "npm dev",
    "npm build",
    "run build",
    "run python",
    "run main",
    "run pytest",
}


# Maps plan() platform argument → canonical lowercase key used in plan dicts.
# Also maps platform.system() raw values so callers can pass either form.
_PLATFORM_MAP = {
    "windows": "windows",
    "darwin":  "macos",
    "macos":   "macos",
    "linux":   "linux",
}

# Maps canonical lowercase key → platform.system() string for the module-level _OS lookups
_OS_KEY_MAP = {
    "windows": "Windows",
    "macos":   "Darwin",
    "linux":   "Linux",
}


def _resolve_os(platform_arg: Optional[str]) -> str:
    """
    Convert a plan() ``platform`` argument to the canonical lowercase key
    ``"windows"``, ``"macos"``, or ``"linux"``.

    Accepts ``"windows"``, ``"macos"``, ``"linux"`` (case-insensitive),
    or the raw ``platform.system()`` values (``"Windows"``, ``"Darwin"``,
    ``"Linux"``). Falls back to the current OS.
    """
    if platform_arg is None:
        raw = platform.system()
        return _PLATFORM_MAP.get(raw.lower(), "linux")
    return _PLATFORM_MAP.get(platform_arg.lower(), "linux")


class CommandParser:
    """
    Parses a raw transcript and dispatches it to the correct action handler.

    Usage::

        parser = CommandParser(config)
        success = parser.execute("open chrome")

        # Dry-run: no OS action; execute() still returns True when matched.
        parser = CommandParser(config, dry_run=True)
        success = parser.execute("open chrome")
    """

    def __init__(
        self,
        config: dict,
        dry_run: bool = False,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ):
        """
        Build the command registry from the given configuration.

        Args:
            config:           Parsed ``config.yaml`` dict (full document).
            dry_run:          If True, no OS action is performed; handlers still return True.
            confirm_callback: Optional callable(prompt_str) -> bool to confirm destructive actions.
        """
        self.dry_run: bool = dry_run
        self.confirm_callback = confirm_callback
        cmd_cfg = config.get("commands", {})
        self._cmd_cfg = cmd_cfg  # retained for plan()
        self.prefix: str = cmd_cfg.get("prefix", "jarvis").lower()
        self.confirm_destructive: bool = bool(cmd_cfg.get("confirm_destructive", False))

        # Identify destructive commands including macros and project commands
        self._destructive_commands = set(DESTRUCTIVE_COMMANDS)
        macros_cfg = cmd_cfg.get("macros") or {}
        for macro_phrase in macros_cfg:
            self._destructive_commands.add(macro_phrase.lower())
        projects_cfg = cmd_cfg.get("projects") or {}
        for proj_name in projects_cfg:
            self._destructive_commands.add(f"go to {proj_name.lower()}")

        # Track custom app paths for plan() (apps_config entries not in _APP_TARGETS)
        self._custom_app_paths: Dict[str, str] = {}
        apps_config = cmd_cfg.get("apps") or {}
        import os as _os
        for keyword, path in apps_config.items():
            phrase_key = f"open {keyword.lower()}"
            if phrase_key not in _APP_TARGETS and phrase_key not in _APP_ALIASES:
                expanded = _os.path.expandvars(_os.path.expanduser(path))
                self._custom_app_paths[phrase_key] = expanded

        self._commands: CommandMap = {}
        self._commands.update(build_app_commands(cmd_cfg.get("apps"), dry_run=dry_run))
        self._commands.update(build_window_commands(dry_run=dry_run))
        self._commands.update(
            build_terminal_commands(
                projects_config=cmd_cfg.get("projects"),
                macros_config=cmd_cfg.get("macros"),
                parser=self,
                dry_run=dry_run,
            )
        )

        logger.info(
            "CommandParser initialised with %d commands (dry_run=%s).",
            len(self._commands),
            dry_run,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, transcript: str) -> bool:
        """
        Parse *transcript* and execute the matching command.

        Args:
            transcript: Raw transcription from the speech recogniser
                        (lowercase, stripped).

        Returns:
            True if a command was matched and executed successfully.
        """
        phrase = self._strip_prefix(transcript)
        logger.debug("Parsed phrase: '%s'", phrase)

        handler, matched = self._match(phrase)
        if handler is None:
            logger.warning("No command matched for: '%s'", phrase)
            return False

        if self.is_destructive(matched) and not self.dry_run and self.confirm_destructive:
            confirmed = self._confirm_action(matched)
            if not confirmed:
                logger.info("Command '%s' cancelled by user.", matched)
                return False

        logger.info("Executing command '%s'...", matched)
        try:
            result = handler()
            if result:
                logger.info("Command '%s' completed successfully.", matched)
            else:
                logger.warning("Command '%s' returned failure.", matched)
            return bool(result)
        except Exception as exc:
            logger.error(
                "Error executing command '%s': %s", matched, exc, exc_info=True
            )
            return False

    def is_destructive(self, command: str) -> bool:
        """Return True if ``command`` is classified as destructive or high-impact."""
        return command.lower() in self._destructive_commands

    def plan(self, transcript: str, platform: Optional[str] = None) -> Optional[dict]:
        """
        Return a structured description of what *transcript* would do, without
        performing any OS action.

        Args:
            transcript: Raw phrase or transcript (wake-word prefix is stripped).
            platform:   One of ``"windows"``, ``"macos"``, or ``"linux"``.
                        Defaults to the current OS when None.

        Returns:
            A dict with keys ``phrase``, ``command``, ``action``, ``target``,
            ``platform``.  Macros additionally have a ``steps`` key with a list
            of per-step plan dicts.  Returns ``None`` for an unknown phrase.
        """
        # Normalise platform to platform.system() keys
        os_name = _resolve_os(platform)
        phrase = self._strip_prefix(transcript)
        _, matched = self._match(phrase)
        if matched is None:
            return None

        detail = self._plan_matched(matched, os_name)
        return {
            "phrase": phrase,
            "command": matched,
            **detail,
        }

    def _plan_matched(self, matched: str, os_name: str) -> dict:
        """
        Return the action/target detail for an already-matched command phrase.
        Never touches the OS.

        Priority mirrors the command-map override order:
          macros > projects > app > terminal > window
        """
        cmd_cfg = self._cmd_cfg

        # 1. Macros override everything (same as build_terminal_commands behaviour)
        macros_cfg = cmd_cfg.get("macros") or {}
        for phrase_key, steps in macros_cfg.items():
            if phrase_key.lower() == matched:
                step_plans = []
                for step in steps:
                    # Use the same substring matching that execute() uses so that
                    # e.g. "run npm run dev" resolves to "run dev" (npm run dev),
                    # not "unknown".
                    step_stripped = self._strip_prefix(step)
                    _, step_matched = self._match(step_stripped)
                    if step_matched is not None:
                        step_detail = self._plan_matched(step_matched, os_name)
                        step_command = step_matched
                    else:
                        # Fall back to literal step as unknown
                        step_detail = {"action": "unknown", "target": step_stripped,
                                       "platform": os_name}
                        step_command = step_stripped
                    step_plans.append({
                        "phrase": step,
                        "command": step_command,
                        **step_detail,
                    })
                return {
                    "action": "macro",
                    "target": matched,
                    "platform": os_name,
                    "steps": step_plans,
                }

        # 2. Project shortcuts ("go to <name>")
        if matched.startswith("go to "):
            proj_name = matched[len("go to "):]
            path = (cmd_cfg.get("projects") or {}).get(proj_name, proj_name)
            import os as _os
            expanded = _os.path.expandvars(_os.path.expanduser(path))
            return {
                "action": "project",
                "target": expanded,
                "platform": os_name,
            }

        # 3. App commands
        app_plan = plan_app_command(matched, os_name)
        if app_plan is not None:
            return app_plan

        # 4. Terminal built-ins
        term_plan = plan_terminal_command(matched, os_name)
        if term_plan is not None:
            return term_plan

        # 5. Window commands
        win_plan = plan_window_command(matched, os_name)
        if win_plan is not None:
            return win_plan

        # 6. Custom apps (not in _APP_TARGETS — registered from apps_config)
        if matched in self._custom_app_paths:
            return {
                "action": "launch",
                "target": self._custom_app_paths[matched],
                "platform": os_name,
            }

        # Fallback
        return {
            "action": "unknown",
            "target": matched,
            "platform": os_name,
        }

    @property
    def registered_commands(self) -> list:
        """Return a sorted list of all registered command phrases."""
        return sorted(self._commands.keys())

    def _confirm_action(self, command: str) -> bool:
        """Prompt for confirmation before executing a destructive action."""
        if self.confirm_callback is not None:
            return self.confirm_callback(command)
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _strip_prefix(self, transcript: str) -> str:
        """
        Remove the wake word prefix from the beginning of *transcript*.

        Example:
            prefix = "jarvis", transcript = "jarvis open chrome"
            → "open chrome"
        """
        transcript = transcript.strip().lower()
        if transcript.startswith(self.prefix):
            transcript = transcript[len(self.prefix):].strip()
        return transcript

    def _match(self, phrase: str) -> Tuple[Optional[Callable], Optional[str]]:
        """
        Find the best command handler for *phrase*.

        Matching order:
          1. Exact match.
          2. Longest registered phrase that is a substring of *phrase*.

        Returns:
            (handler, matched_phrase) or (None, None) if no match.
        """
        # 1. Exact match
        if phrase in self._commands:
            return self._commands[phrase], phrase

        # 2. Substring match — prefer longer (more specific) matches
        candidates = [
            cmd for cmd in self._commands if cmd in phrase
        ]
        if candidates:
            best = max(candidates, key=len)
            return self._commands[best], best

        return None, None
