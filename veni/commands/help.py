"""
Help command for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table

from veni.commands.base import BaseCommand, console


class HelpCommand(BaseCommand):
    """Shows help for all available commands."""

    @property
    def name(self) -> str:
        return "/help"

    @property
    def description(self) -> str:
        return "Shows available commands and their descriptions."

    @property
    def usage(self) -> str:
        return "/help [command]"

    @property
    def examples(self) -> List[str]:
        return ["/help", "/help /model", "/help /search"]

    def execute(self, args: List[str]) -> Optional[str]:
        if args:
            cmd_name = args[0].lower()
            if not cmd_name.startswith("/"):
                cmd_name = f"/{cmd_name}"

            cmd = self.bot.command_registry.get(cmd_name)
            if cmd:
                panel = Panel(
                    f"[bold cyan]Command:[/bold cyan] {cmd.usage}\n"
                    f"[bold]Description:[/bold] {cmd.description}\n\n"
                    f"[bold]Examples:[/bold]\n"
                    + "\n".join([f"  • {ex}" for ex in cmd.examples]),
                    title=f"Help: {cmd.name}",
                    border_style=self.colors["secondary"],
                    box=box.SIMPLE,
                )
                console.print(panel)
            else:
                self.show_warning(f"No detailed help available for {cmd_name}.")
            return None

        # Show all commands from the registry
        table = Table(
            title="Available Commands",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for cmd in self.bot.command_registry.list_commands():
            table.add_row(cmd.usage, cmd.description)

        # Add plugin commands if any
        if self.bot.plugin_help:
            table.add_section()
            for cmd, desc in self.bot.plugin_help.items():
                table.add_row(cmd, f"{desc} (plugin)")

        console.print(table)
        console.print(
            "\n[dim]Tip: Use /help <command> for detailed help on a specific command.[/dim]"
        )
        return None
