"""
SmartDesktop Voice Assistant - Main Entry Point

Orchestrates:
  1. Configuration loading
  2. Wake word detection (Porcupine)
  3. Speech recognition (Faster-Whisper)
  4. Command parsing & execution

Architecture:
    Microphone → Wake Word Engine (Porcupine)
                      │
                      ▼
              Speech Recognition (Faster-Whisper)
                      │
                      ▼
              Command Parser
                      │
                      ▼
              Action Executor
              ┌────────────────┬──────────────┬──────────────┐
              │  OS automation │  open apps   │  terminal    │
              └────────────────┴──────────────┴──────────────┘

Usage:
    python main.py [--config path/to/config.yaml]
    python main.py --text                      # read commands from stdin
    python main.py --text --dry-run            # preview only, no OS actions
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

# colorama is only used for coloured console output; keep the import eager so
# the colours work everywhere but wrap it in a try/except for minimal envs.
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:  # pragma: no cover
    class _Noop:
        def __getattr__(self, _):
            return ""
    Fore = Style = _Noop()

_DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmartDesktop — local voice automation assistant"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="Path to config.yaml (default: ./config.yaml)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level from config.",
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="Print all registered commands and exit.",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help=(
            "Read commands from stdin line by line instead of using the "
            "microphone. No wake word, Porcupine, or Whisper is needed."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the planned action for each command instead of executing "
            "it. No OS action is performed. Implies --text when combined with it."
        ),
    )
    return parser.parse_args()


def _setup_logging(config: dict, override_level: str = None) -> None:
    log_cfg = config.get("logging", {})
    level_name = override_level or log_cfg.get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    log_file = log_cfg.get("file")

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(
            f"{Fore.RED}Config file not found: {config_path}{Style.RESET_ALL}"
        )
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Text-mode loop (no audio / ML imports)
# ---------------------------------------------------------------------------

def _run_text_mode(config: dict, dry_run: bool) -> None:
    """
    Read command phrases from stdin, one per line, and execute them.

    When *dry_run* is True the commands are parsed but no OS action is taken.
    """
    # Audio/ML imports are intentionally NOT done here — text mode must work
    # without pyaudio, pvporcupine, or faster-whisper installed.
    from commands import CommandParser

    def _text_confirm(command: str) -> bool:
        sys.stdout.write(f"Confirm '{command}'? (y/n): ")
        sys.stdout.flush()
        try:
            line = sys.stdin.readline()
            if not line:
                return False
            return line.strip().lower() in ("y", "yes")
        except Exception:
            return False

    parser = CommandParser(
        config,
        dry_run=dry_run,
        confirm_callback=_text_confirm if not dry_run else None,
    )

    mode_label = "(dry-run)" if dry_run else ""
    _info(f"SmartDesktop text mode {mode_label}. Type a command and press Enter. Ctrl-D / Ctrl-Z to quit.")

    try:
        for line in sys.stdin:
            phrase = line.strip()
            if not phrase:
                continue
            _info(f"Command: \"{phrase}\"")
            result = parser.execute(phrase)
            if not result:
                _warn(f"Command not recognised: \"{phrase}\"")
    except KeyboardInterrupt:
        pass

    _info("SmartDesktop text mode exiting.")


# ---------------------------------------------------------------------------
# Assistant orchestration (voice mode — lazy audio/ML imports)
# ---------------------------------------------------------------------------

class SmartDesktopAssistant:
    """
    Top-level controller that wires together wake word, STT, and command execution.
    """

    def __init__(self, config: dict, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run

        import threading
        import time
        self._threading = threading
        self._time = time
        self._ready_event = threading.Event()
        self._shutdown_event = threading.Event()

        # Deferred imports so modules are only loaded when actually needed.
        # This keeps --text mode free of pyaudio / pvporcupine / faster-whisper.
        from commands import CommandParser
        from speech import SpeechRecognizer

        speech_cfg = config.get("speech", {})
        self._recognizer = SpeechRecognizer(
            model_size=speech_cfg.get("model_size", "base"),
            language=speech_cfg.get("language", "en") or None,
            device=speech_cfg.get("device", "auto"),
            compute_type=speech_cfg.get("compute_type", "int8"),
            max_record_seconds=float(speech_cfg.get("max_record_seconds", 10)),
            silence_threshold=int(speech_cfg.get("silence_threshold", 500)),
            silence_duration=float(speech_cfg.get("silence_duration", 1.5)),
        )

        def _voice_confirm(command: str) -> bool:
            _info(f"High-impact command '{command}' detected. Please say 'yes' or 'confirm' to proceed.")
            confirmation = self._recognizer.listen()
            if confirmation and any(w in confirmation for w in ["yes", "confirm", "proceed", "sure"]):
                _info(f"Confirmation received for '{command}'.")
                return True
            _warn(f"Action '{command}' cancelled or not confirmed.")
            return False

        self._parser = CommandParser(
            config,
            dry_run=dry_run,
            confirm_callback=_voice_confirm if not dry_run else None,
        )

    def run(self) -> None:
        """Start the assistant and block until interrupted."""
        from wakeword import WakeWordDetector

        ww_cfg = self.config.get("wakeword", {})
        # S-06: Read Porcupine key from PORCUPINE_ACCESS_KEY environment variable first,
        # with fallback to config.yaml if non-default.
        access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "").strip()
        if not access_key:
            raw_key = ww_cfg.get("access_key", "")
            expanded_key = os.path.expandvars(raw_key).strip()
            if expanded_key and expanded_key != "YOUR_PORCUPINE_ACCESS_KEY":
                access_key = expanded_key

        if not access_key or access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            _warn(
                "Porcupine access key not configured.\n"
                "  1. Sign up at https://console.picovoice.ai/ (free tier available).\n"
                "  2. Set the PORCUPINE_ACCESS_KEY environment variable."
            )
            sys.exit(1)

        keywords = ww_cfg.get("keywords", ["jarvis"])
        sensitivity = float(ww_cfg.get("sensitivity", 0.5))

        detector = WakeWordDetector(
            access_key=access_key,
            keywords=keywords,
            sensitivity=sensitivity,
            on_detected=self._on_wake_word,
        )

        _info(
            f"SmartDesktop is ready. Say one of {keywords} to activate."
        )

        with detector:
            try:
                while not self._shutdown_event.is_set():
                    self._time.sleep(0.1)
            except KeyboardInterrupt:
                _info("Shutting down SmartDesktop...")

    def _on_wake_word(self, keyword: str) -> None:
        """
        Called on the WakeWord thread when the wake word is detected.
        Records and processes a command synchronously on the same thread.
        """
        _info(f"Wake word '{keyword}' detected! Listening for command...")
        transcript = self._recognizer.listen()

        if not transcript:
            _warn("No command detected.")
            return

        logger = logging.getLogger(__name__)
        if logger.isEnabledFor(logging.DEBUG):
            _info(f"You said: \"{transcript}\"")
        else:
            _info("Voice command received.")
        success = self._parser.execute(transcript)
        if not success:
            if logger.isEnabledFor(logging.DEBUG):
                _warn(f"Command not recognised: \"{transcript}\"")
            else:
                _warn("Command not recognised.")

    def list_commands(self) -> None:
        """Print all registered commands to stdout."""
        print(f"\n{Fore.CYAN}Registered commands:{Style.RESET_ALL}")
        for cmd in self._parser.registered_commands:
            print(f"  • {cmd}")
        print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _info(message: str) -> None:
    print(f"{Fore.GREEN}[SmartDesktop]{Style.RESET_ALL} {message}")


def _warn(message: str) -> None:
    print(f"{Fore.YELLOW}[SmartDesktop]{Style.RESET_ALL} {message}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    _setup_logging(config, args.log_level)

    # Text mode: no audio/ML imports needed
    if args.text:
        _run_text_mode(config, dry_run=args.dry_run)
        return

    # --dry-run without --text: build the parser in dry-run mode but still
    # use voice input (wake word + whisper).
    assistant = SmartDesktopAssistant(config, dry_run=args.dry_run)

    if args.list_commands:
        assistant.list_commands()
        return

    assistant.run()


if __name__ == "__main__":
    main()
