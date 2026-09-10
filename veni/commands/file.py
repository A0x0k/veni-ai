"""
File and directory management commands for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from veni.commands.base import BaseCommand, console
from veni.tool_executor import _extract_raw_content


class PwdCommand(BaseCommand):
    """Show current directory."""

    @property
    def name(self) -> str:
        return "/pwd"

    @property
    def description(self) -> str:
        return "Show the current working directory."

    def execute(self, args: List[str]) -> Optional[str]:
        console.print(str(self.bot.cwd))
        return None


class LsCommand(BaseCommand):
    """List directory contents."""

    @property
    def name(self) -> str:
        return "/ls"

    @property
    def description(self) -> str:
        return "List files and directories in the current or specified path."

    @property
    def usage(self) -> str:
        return "/ls [path]"

    def execute(self, args: List[str]) -> Optional[str]:
        try:
            target = (
                self.bot.cwd
                if not args
                else self.bot.resolve_workspace_path(" ".join(args))
            )
        except ValueError as exc:
            self.show_error(str(exc))
            return None
        if not target.exists():
            self.show_error(f"Not found: {target}")
            return None
        if target.is_file():
            console.print(str(target))
            return None
        table = Table(
            title=f"Listing: {target}", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Name", style="white")
        table.add_column("Type", style="dim")
        for p in sorted(target.iterdir()):
            p_type = "dir" if p.is_dir() else "file"
            table.add_row(p.name, p_type)
        console.print(table)
        return None


class CdCommand(BaseCommand):
    """Change directory."""

    @property
    def name(self) -> str:
        return "/cd"

    @property
    def description(self) -> str:
        return "Change the current working directory."

    @property
    def usage(self) -> str:
        return "/cd <path>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /cd <path>")
            return None
        try:
            target = self.bot.resolve_workspace_path(" ".join(args))
        except ValueError as exc:
            self.show_error(str(exc))
            return None
        if not target.exists() or not target.is_dir():
            self.show_error(f"Not a directory: {target}")
            return None
        self.bot.cwd = target
        self.show_success(f"Current directory: {self.bot.cwd}")
        return None


class ReadCommand(BaseCommand):
    """Read file into context."""

    @property
    def name(self) -> str:
        return "/read"

    @property
    def description(self) -> str:
        return "Read a file's content and add it to the conversation context."

    @property
    def usage(self) -> str:
        return "/read <file_path>"

    @property
    def examples(self) -> List[str]:
        return ["/read main.py", "/read configs/app.yaml"]

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /read <file_path>")
            return None
        try:
            path = self.bot.resolve_workspace_path(" ".join(args))
        except ValueError as exc:
            self.show_error(str(exc))
            return None
        if not path.exists():
            self.show_error(f"File not found: {path}")
        elif not path.is_file():
            self.show_error(f"Not a file: {path}")
        else:
            try:
                content = path.read_text(encoding="utf-8")
                self.bot.history.add_tool_message(
                    f"Context from file '{path.name}':\n\n{content}"
                )
                self.show_success(f"Added {path.name} to context")
            except Exception as e:
                self.show_error(f"Error reading file: {e}")
        return None


class EditCommand(BaseCommand):
    """Agentic file editing."""

    @property
    def name(self) -> str:
        return "/edit"

    @property
    def description(self) -> str:
        return "Request the AI to edit a file based on instructions."

    @property
    def usage(self) -> str:
        return "/edit <file_path> <instruction>"

    def execute(self, args: List[str]) -> Optional[str]:
        if len(args) < 2:
            self.show_error("Usage: /edit <file_path> <instruction>")
            return None
        try:
            file_path = self.bot.resolve_workspace_path(args[0])
        except ValueError as exc:
            self.show_error(str(exc))
            return None
        instruction = " ".join(args[1:])
        if not file_path.exists():
            self.show_error(f"File not found: {file_path}")
            return None
        try:
            original_content = file_path.read_text(encoding="utf-8")
            edit_prompt = (
                f"INSTRUCTION: {instruction}\n"
                f"FILE: {file_path.name}\n"
                f"CONTENT:\n{original_content}\n"
                f"Return ONLY updated content."
            )
            with Live(
                Text(
                    f" {self._spinner()} Generating edit for {file_path.name}...",
                    style=self.colors["warning"],
                ),
                transient=True,
            ):
                edit_messages = [
                    {"role": "system", "content": "Return ONLY raw file content."},
                    {"role": "user", "content": edit_prompt},
                ]
                new_content = "".join(
                    self.bot.ai_client.chat(edit_messages, stream=True)
                )
            new_content = _extract_raw_content(new_content)

            # Show unified diff preview
            diff = self._make_diff(file_path.name, original_content, new_content)
            console.print(
                Panel(
                    Syntax(diff, "diff", theme="monokai", line_numbers=False),
                    title=f" Diff: {file_path.name} ",
                    border_style=self.colors["accent"],
                )
            )

            if (
                Prompt.ask(
                    f"Apply changes to {file_path.name}?",
                    choices=["y", "n"],
                    default="n",
                )
                == "y"
            ):
                file_path.write_text(new_content, encoding="utf-8")
                self.show_success(f"Updated {file_path.name}")
        except Exception as e:
            self.show_error(f"Edit failed: {e}")
        return None

    @staticmethod
    def _make_diff(filename: str, old: str, new: str) -> str:
        """Generate a unified diff string using shared utility."""
        from veni.tools.diff import make_diff

        return make_diff(old, new, filepath=filename)

    @staticmethod
    def _spinner() -> str:
        return "🛠️"


class TreeCommand(BaseCommand):
    """Show visual conversation map."""

    @property
    def name(self) -> str:
        return "/tree"

    @property
    def description(self) -> str:
        return "Show a visual map of the current conversation structure."

    def execute(self, args: List[str]) -> Optional[str]:
        if not self.bot.history.messages:
            self.show_warning("No conversation yet.")
            return None

        tree = Table(
            title="Conversation Map", box=box.ROUNDED, header_style="bold magenta"
        )
        tree.add_column("#", style="cyan", justify="right")
        tree.add_column("Role", style="white")
        tree.add_column("Preview", style="dim")

        for i, msg in enumerate(self.bot.history.messages, 1):
            role_icon = (
                "👤"
                if msg.role == "user"
                else "🤖" if msg.role == "assistant" else "🔧"
            )
            preview = msg.content[:60].replace("\n", " ")
            if len(msg.content) > 60:
                preview += "..."
            if msg.pinned:
                preview = f"📌 {preview}"

            tree.add_row(str(i), f"{role_icon} {msg.role}", preview)

        console.print(tree)
        return None
