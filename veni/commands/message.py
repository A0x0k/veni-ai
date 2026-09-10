"""
Message and history management commands for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table

from veni.commands.base import BaseCommand, console
from veni.config import config
from veni.providers.factory import create_ai_client


class PinCommand(BaseCommand):
    """Pin a message."""

    @property
    def name(self) -> str:
        return "/pin"

    @property
    def description(self) -> str:
        return "Pin a message to keep it in the conversation context."

    @property
    def usage(self) -> str:
        return "/pin [index_from_last]"

    def execute(self, args: List[str]) -> Optional[str]:
        index = 1
        if args:
            try:
                index = int(args[0])
            except ValueError:
                self.show_error("Usage: /pin [index_from_last]")
                return None
        msg = self.bot.history.pin_message(index)
        if not msg:
            self.show_error("Nothing to pin at that index.")
            return None
        preview = (msg.content[:80] + "...") if len(msg.content) > 80 else msg.content
        self.show_success(f"Pinned ({msg.role}): {preview}")
        return None


class UnpinCommand(BaseCommand):
    """Unpin a message."""

    @property
    def name(self) -> str:
        return "/unpin"

    @property
    def description(self) -> str:
        return "Unpin a message to allow it to be pruned."

    @property
    def usage(self) -> str:
        return "/unpin [index_from_last]"

    def execute(self, args: List[str]) -> Optional[str]:
        index = 1
        if args:
            try:
                index = int(args[0])
            except ValueError:
                self.show_error("Usage: /unpin [index_from_last]")
                return None
        msg = self.bot.history.unpin_message(index)
        if not msg:
            self.show_error("Nothing to unpin at that index.")
            return None
        preview = (msg.content[:80] + "...") if len(msg.content) > 80 else msg.content
        self.show_success(f"Unpinned ({msg.role}): {preview}")
        return None


class PinsCommand(BaseCommand):
    """List pinned messages."""

    @property
    def name(self) -> str:
        return "/pins"

    @property
    def description(self) -> str:
        return "List all currently pinned messages."

    def execute(self, args: List[str]) -> Optional[str]:
        pins = self.bot.history.list_pins()
        if not pins:
            self.show_warning("No pinned messages.")
            return None
        table = Table(
            title="Pinned Messages", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Index", style="cyan", justify="right")
        table.add_column("Role", style="white")
        table.add_column("Preview", style="white")
        for i, msg in enumerate(pins, 1):
            preview = (
                (msg.content[:80] + "...") if len(msg.content) > 80 else msg.content
            )
            table.add_row(str(i), msg.role, preview)
        console.print(table)
        return None


class RetryCommand(BaseCommand):
    """Retry last request."""

    @property
    def name(self) -> str:
        return "/retry"

    @property
    def description(self) -> str:
        return "Retry the last failed AI request."

    def execute(self, args: List[str]) -> Optional[str]:
        if self.bot.last_error:
            if self.bot.last_failed_input:
                self.bot.history.add_message("user", self.bot.last_failed_input)
                return "TRIGGER_CHAT"
        else:
            self.show_warning("No failed request to retry.")
        return None


class SummaryCommand(BaseCommand):
    """Generate summary."""

    @property
    def name(self) -> str:
        return "/summary"

    @property
    def description(self) -> str:
        return "Generate an AI summary of the current conversation."

    def execute(self, args: List[str]) -> Optional[str]:
        if not self.bot.history.messages:
            self.show_warning("No conversation to summarize.")
            return None
        conversation_text = ""
        for msg in self.bot.history.messages:
            if msg.role in ["user", "assistant"]:
                conversation_text += f"{msg.role}: {msg.content}\n\n"
        summary_prompt = (
            f"Summarize this conversation in 3-5 bullet points:\n\n{conversation_text}"
        )
        try:
            summary_client = create_ai_client(
                provider=config.get("default_provider", "ollama"),
                model=config.get("default_model", "llama3.2"),
            )
            summary = "".join(
                summary_client.chat(
                    [{"role": "user", "content": summary_prompt}], stream=False
                )
            )
            console.print(
                Panel(
                    summary,
                    title="Conversation Summary",
                    border_style=self.colors["accent"],
                    box=box.SIMPLE,
                )
            )
        except Exception as e:
            self.show_error(f"Could not generate summary: {e}")
        return None


class AliasCommand(BaseCommand):
    """Create command alias."""

    @property
    def name(self) -> str:
        return "/alias"

    @property
    def description(self) -> str:
        return "Create a shortcut for an existing command."

    @property
    def usage(self) -> str:
        return "/alias <new_name> <original_command>"

    def execute(self, args: List[str]) -> Optional[str]:
        if len(args) < 2:
            self.show_error("Usage: /alias <new_name> <original_command>")
            return None
        alias_name = args[0]
        original_cmd = " ".join(args[1:])
        if not original_cmd.startswith("/"):
            self.show_error("Original command must start with /")
            return None
        if alias_name in self.bot.commands:
            self.show_error(f"Cannot create alias: '{alias_name}' is already a command")
            return None
        handler = self.bot.commands.get(original_cmd)
        if not handler:
            self.show_error(f"Original command '{original_cmd}' not found")
            return None
        self.bot.commands[f"/{alias_name}"] = handler
        self.bot.plugin_help[f"/{alias_name}"] = f"Alias for {original_cmd}"
        self.show_success(f"Created alias /{alias_name} -> {original_cmd}")
        return None
