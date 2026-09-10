"""
AI tools and interaction commands for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.live import Live
from rich.table import Table
from rich.text import Text

from veni.commands.base import BaseCommand, console


class SearchCommand(BaseCommand):
    """Web search command."""

    @property
    def name(self) -> str:
        return "/search"

    @property
    def description(self) -> str:
        return "Search the web and inject findings into the conversation."

    @property
    def usage(self) -> str:
        return "/search <query>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /search <query>")
            return None
        query = " ".join(args)
        with Live(
            Text(f" 🔍 Searching: {query}...", style=self.colors["accent"]),
            transient=True,
        ):
            search_tool = self.bot.tool_registry.get("web_search")
            if not search_tool:
                self.show_error("Search tool not available")
                return None
            context = search_tool.execute(query=query)
        self.bot.history.add_tool_message(context)
        return "TRIGGER_CHAT"


class VoiceCommand(BaseCommand):
    """Toggle voice mode."""

    @property
    def name(self) -> str:
        return "/voice"

    @property
    def description(self) -> str:
        return "Toggle voice-to-text and text-to-speech mode."

    def execute(self, args: List[str]) -> Optional[str]:
        from veni.voice import VoiceEngine

        if not self.bot.voice_mode:
            if self.bot.voice_engine is None:
                try:
                    self.bot.voice_engine = VoiceEngine()
                except Exception as e:
                    self.show_error(f"Voice init failed: {e}")
                    return None
        self.bot.voice_mode = not self.bot.voice_mode
        status = "enabled" if self.bot.voice_mode else "disabled"
        self.show_success(f"Voice mode {status}")
        if self.bot.voice_mode and self.bot.voice_engine:
            self.bot.voice_engine.speak(f"Voice {status}")
        return None


class ImageCommand(BaseCommand):
    """Attach image."""

    @property
    def name(self) -> str:
        return "/image"

    @property
    def description(self) -> str:
        return "Attach an image to the next message for multimodal analysis."

    @property
    def usage(self) -> str:
        return "/image <file_path>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /image <file_path>")
            return None
        try:
            path = self.bot.resolve_workspace_path(" ".join(args))
        except ValueError:
            self.show_error("Image path must be within the workspace.")
            return None
        if path.exists():
            self.bot.current_images.append(str(path.absolute()))
            self.show_success(f"Image attached: {path.name}")
        else:
            self.show_error(f"Image not found: {path}")
        return None


class CopyCommand(BaseCommand):
    """Copy last response."""

    @property
    def name(self) -> str:
        return "/copy"

    @property
    def description(self) -> str:
        return "Copy the last AI response to the clipboard."

    def execute(self, args: List[str]) -> Optional[str]:
        import pyperclip

        if self.bot.last_response:
            try:
                pyperclip.copy(self.bot.last_response)
                self.show_success("Copied to clipboard")
            except Exception as e:
                self.show_error(f"Failed to copy: {e}")
        else:
            self.show_warning("Nothing to copy yet.")
        return None


class StatsCommand(BaseCommand):
    """Show session statistics."""

    @property
    def name(self) -> str:
        return "/stats"

    @property
    def description(self) -> str:
        return "Show detailed statistics about the current session and token usage."

    def execute(self, args: List[str]) -> Optional[str]:
        from datetime import timedelta

        total_messages = len(self.bot.history.messages)
        user_messages = sum(1 for m in self.bot.history.messages if m.role == "user")
        assistant_messages = sum(
            1 for m in self.bot.history.messages if m.role == "assistant"
        )

        _, token_count, dropped = self.bot.history.get_context_state(
            self.bot.context_tokens
        )
        token_usage_percent = (token_count / self.bot.context_tokens) * 100

        if self.bot.history.messages:
            first_time = min(m.timestamp for m in self.bot.history.messages)
            last_time = max(m.timestamp for m in self.bot.history.messages)
            session_duration = timedelta(seconds=last_time - first_time)
            duration_str = str(session_duration).split(".")[0]
        else:
            duration_str = "0s"

        stats_table = Table(
            title="Session Statistics", box=box.ROUNDED, header_style="bold magenta"
        )
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Messages", str(total_messages))
        stats_table.add_row("User messages", str(user_messages))
        stats_table.add_row("Assistant messages", str(assistant_messages))
        stats_table.add_row(
            "Tokens used",
            f"{token_count}/{self.bot.context_tokens} ({token_usage_percent:.1f}%)",
        )
        stats_table.add_row("Messages pruned", str(dropped))
        stats_table.add_row("Session duration", duration_str)
        stats_table.add_row("Provider", self.bot.provider_name)
        stats_table.add_row("Model", self.bot.model_name)

        console.print(stats_table)
        return None
