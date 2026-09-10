"""
Dynamic completion for Veni AI CLI.
"""

from pathlib import Path
from typing import Iterable

from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document

from veni.config import config


class VeniCompleter(Completer):
    """Smart completer for Veni AI commands and arguments."""

    def __init__(self, bot):
        self.bot = bot
        self.commands = list(bot.commands.keys())
        self.command_completer = WordCompleter(self.commands, ignore_case=True)

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # If no space, complete commands
        if " " not in text:
            yield from self.command_completer.get_completions(document, complete_event)
            return

        # If space exists, we are in argument mode
        parts = text.split()
        cmd = parts[0].lower()
        arg_text = parts[-1] if len(parts) > 1 and not text.endswith(" ") else ""

        # /read path completion
        if cmd == "/read" or cmd == "/image" or cmd == "/cd":
            yield from self._complete_paths(arg_text)

        # /model preset completion
        elif cmd == "/model":
            provider_name = self.bot.provider_name
            if provider_name == "unknown":
                provider_name = config.get("default_provider", "ollama")
            presets = config.get("model_presets", {}).get(provider_name, [])
            for p in presets:
                if p.startswith(arg_text):
                    yield Completion(p, start_position=-len(arg_text))

        # /load session completion
        elif cmd == "/load":
            sessions = self.bot.history.list_sessions()
            for s in sessions:
                if s.startswith(arg_text):
                    yield Completion(s, start_position=-len(arg_text))

        # /theme completion
        elif cmd == "/theme":
            themes = ["cyberpunk", "minimal", "retro", "professional", "dark"]
            for t in themes:
                if t.startswith(arg_text):
                    yield Completion(t, start_position=-len(arg_text))

    def _complete_paths(self, text: str) -> Iterable[Completion]:
        """Complete local file system paths."""
        try:
            path = Path(text)
            if text.endswith("/") or text.endswith("\\") or not text:
                search_dir = self.bot.cwd / path if not path.is_absolute() else path
                prefix = ""
            else:
                search_dir = (
                    self.bot.cwd / path.parent
                    if not path.is_absolute()
                    else path.parent
                )
                prefix = path.name

            if search_dir.exists() and search_dir.is_dir():
                for p in search_dir.iterdir():
                    if p.name.startswith(prefix):
                        display_name = p.name + ("/" if p.is_dir() else "")
                        yield Completion(display_name, start_position=-len(prefix))
        except Exception as exc:
            logger.debug("Path completion failed: %s", exc)
