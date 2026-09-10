"""
Session management commands for Veni AI.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table

from veni.commands.base import BaseCommand, console


class QuitCommand(BaseCommand):
    """Exit the application."""

    @property
    def name(self) -> str:
        return "/quit"

    @property
    def description(self) -> str:
        return "Exit the Veni AI application."

    def execute(self, args: List[str]) -> Optional[str]:
        self.bot.running = False
        return "EXIT"


class ExitCommand(QuitCommand):
    """Exit the application alias."""

    @property
    def name(self) -> str:
        return "/exit"


class QCommand(QuitCommand):
    """Exit the application alias."""

    @property
    def name(self) -> str:
        return "/q"


class NewCommand(BaseCommand):
    """Start a new session."""

    @property
    def name(self) -> str:
        return "/new"

    @property
    def description(self) -> str:
        return "Clear the current conversation and start fresh."

    def execute(self, args: List[str]) -> Optional[str]:
        self.bot.history.clear()
        self.bot.current_images = []
        self.show_success("New session started")
        return None


class SaveCommand(BaseCommand):
    """Save the current session."""

    @property
    def name(self) -> str:
        return "/save"

    @property
    def description(self) -> str:
        return "Save the current conversation history to a file."

    @property
    def usage(self) -> str:
        return "/save [name]"

    def execute(self, args: List[str]) -> Optional[str]:
        name = args[0] if args else None
        path = self.bot.history.save(name)
        self.show_success(f"Session saved to {path.name}")
        return None


class LoadCommand(BaseCommand):
    """Load a saved session."""

    @property
    def name(self) -> str:
        return "/load"

    @property
    def description(self) -> str:
        return "Load a previously saved conversation history."

    @property
    def usage(self) -> str:
        return "/load <session_name>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /load <session_name>")
            return None
        if self.bot.history.load(args[0]):
            self.show_success(f"Loaded session: {args[0]}")
        else:
            self.show_error(f"Session not found: {args[0]}")
        return None


class HistoryCommand(BaseCommand):
    """List saved sessions."""

    @property
    def name(self) -> str:
        return "/history"

    @property
    def description(self) -> str:
        return "List all saved conversation sessions."

    def execute(self, args: List[str]) -> Optional[str]:
        sessions = self.bot.history.list_sessions()
        if sessions:
            table = Table(
                title="Recent Sessions", box=box.ROUNDED, header_style="bold magenta"
            )
            table.add_column("Name", style="cyan")
            table.add_column("Messages", style="white", justify="right")
            table.add_column("Modified", style="dim")

            for session_name in sessions[:10]:
                try:
                    session_path = self.bot.history.storage_dir / f"{session_name}.json"
                    stat = session_path.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    )

                    import json

                    with open(session_path, "r") as f:
                        data = json.load(f)
                        msg_count = len(data.get("messages", []))

                    table.add_row(session_name, str(msg_count), modified)
                except Exception:
                    table.add_row(session_name, "?", "?")

            console.print(table)
        else:
            self.show_warning("No saved sessions found.")
        return None


class ExportCommand(BaseCommand):
    """Export the session in different formats."""

    @property
    def name(self) -> str:
        return "/export"

    @property
    def description(self) -> str:
        return "Export the current session as Markdown, text, or JSON."

    @property
    def usage(self) -> str:
        return "/export <md|txt|json>"

    def execute(self, args: List[str]) -> Optional[str]:
        export_format = args[0].lower() if args else "md"
        if export_format not in {"md", "txt", "json"}:
            self.show_error("Usage: /export <md|txt|json>")
            return None

        from rich.prompt import Confirm

        export_dir = Path.home() / ".veni-chatbot" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        path = export_dir / name

        self.bot.history.export(export_format, path)

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            self.show_error(f"Export failed: {e}")
            return None

        preview_content = "\n".join(lines[:10])
        if len(lines) > 10:
            preview_content += f"\n... ({len(lines) - 10} more lines)"

        console.print(
            Panel(
                preview_content,
                title=f"Export Preview ({export_format.upper()})",
                border_style=self.colors["secondary"],
                box=box.SIMPLE,
            )
        )

        if not Confirm.ask("Keep this export?", default=True):
            path.unlink(missing_ok=True)
            self.show_warning("Export discarded.")
        else:
            self.show_success(f"Exported session to {path}")

        return None
        return None
