"""
Git integration commands for Veni AI.

Unified to use GitIntelligence for all git operations.
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


class DiffCommand(BaseCommand):
    """Show git diff."""

    @property
    def name(self) -> str:
        return "/diff"

    @property
    def description(self) -> str:
        return "Show the current git diff of the project."

    def execute(self, args: List[str]) -> Optional[str]:
        diff = self.bot.git_intelligence.get_diff()
        if diff.strip():
            console.print(
                Panel(
                    Syntax(diff, "diff", theme="monokai", line_numbers=True, word_wrap=True),
                    title="Git Diff",
                    border_style=self.colors["accent"],
                    box=box.SIMPLE,
                )
            )
        else:
            console.print("[dim]No changes.[/dim]")
        return None


class CommitCommand(BaseCommand):
    """Generate commit message and commit using GitIntelligence."""

    @property
    def name(self) -> str:
        return "/commit"

    @property
    def description(self) -> str:
        return "Generate an AI commit message and commit changes."

    @property
    def usage(self) -> str:
        return "/commit [--review]"

    def execute(self, args: List[str]) -> Optional[str]:
        review = "--review" in args

        # Get diff
        diff = self.bot.git_intelligence.get_diff()
        if not diff.strip():
            diff = self.bot.git_intelligence.get_diff(staged=True)

        if not diff.strip():
            self.show_warning("Nothing to commit.")
            return None

        # Generate commit message using GitIntelligence
        with Live(
            Text(" 📝 Generating commit message...", style=self.colors["accent"]),
            transient=True,
        ):
            msg = self.bot.git_intelligence.generate_commit_message()

        # Optionally show code review
        if review:
            review_comments = self.bot.git_intelligence.review_code(diff)
            if review_comments:
                table = Table(title="Code Review", box="ROUNDED")
                table.add_column("Severity", style="white")
                table.add_column("Comment", style="yellow")
                for c in review_comments:
                    severity_color = {
                        "suggestion": "blue",
                        "warning": "yellow",
                        "issue": "red",
                    }.get(c.severity, "white")
                    table.add_row(
                        f"[{severity_color}]{c.severity}[/{severity_color}]",
                        c.comment,
                    )
                console.print(table)

        # Show proposed commit message
        console.print(
            Panel(
                msg,
                title="Proposed Commit Message",
                border_style=self.colors["success"],
            )
        )

        if Prompt.ask("Commit?", choices=["y", "n"], default="y") == "y":
            import subprocess

            subprocess.run(["git", "add", "."], capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-m", msg],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.show_success("Committed changes")
            else:
                self.show_error(f"Commit failed: {result.stderr}")
        return None


class LogCommand(BaseCommand):
    """Show recent git history."""

    @property
    def name(self) -> str:
        return "/log"

    @property
    def description(self) -> str:
        return "Show recent git commit history."

    @property
    def usage(self) -> str:
        return "/log [count]"

    def execute(self, args: List[str]) -> Optional[str]:
        count = 10
        if args and args[0].isdigit():
            count = int(args[0])

        commits = self.bot.git_intelligence.get_log(count)
        if not commits:
            console.print("[dim]No git history found.[/dim]")
            return None

        table = Table(title="Recent Commits", box="ROUNDED")
        table.add_column("Hash", style="cyan")
        table.add_column("Message", style="white")
        table.add_column("Author", style="dim")
        table.add_column("Date", style="dim")

        for c in commits:
            table.add_row(c["hash"][:7], c["message"], c["author"], c["date"])

        console.print(table)
        return None
