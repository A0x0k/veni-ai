"""
Base classes for Veni AI commands.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


class BaseCommand(ABC):
    """Abstract base class for all Veni AI commands."""

    def __init__(self, bot: Any):
        self.bot = bot
        self.colors = bot.COLORS

    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., '/help')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Command description for help text."""
        pass

    @property
    def usage(self) -> str:
        """Command usage instructions."""
        return self.name

    @property
    def examples(self) -> List[str]:
        """Example usages of the command."""
        return []

    @abstractmethod
    def execute(self, args: List[str]) -> Optional[str]:
        """
        Execute the command.

        Args:
            args: List of command arguments.

        Returns:
            Optional trigger (e.g., 'TRIGGER_CHAT', 'EXIT').
        """
        pass

    def show_error(self, message: str):
        """Show error feedback."""
        self.bot.show_error(message)

    def show_success(self, message: str):
        """Show success feedback."""
        self.bot.show_success(message)

    def show_warning(self, message: str):
        """Show warning feedback."""
        self.bot.show_warning(message)

    def _show_usage(self) -> None:
        """Print usage and examples for this command."""
        lines = [f"[bold]Usage:[/bold] {self.usage}"]
        if self.examples:
            lines.append("[bold]Examples:[/bold]")
            for ex in self.examples:
                lines.append(f"  {ex}")
        console.print("\n".join(lines))



class CommandRegistry:
    """Manages available commands for Veni AI."""

    def __init__(self, bot: Any):
        self.bot = bot
        self.commands: Dict[str, BaseCommand] = {}

    def register(self, command_cls: type):
        """Register a new command."""
        command = command_cls(self.bot)
        self.commands[command.name] = command

    def get(self, name: str) -> Optional[BaseCommand]:
        """Get a command by name."""
        return self.commands.get(name)

    def list_commands(self) -> List[BaseCommand]:
        """List all registered commands."""
        return sorted(self.commands.values(), key=lambda c: c.name)
