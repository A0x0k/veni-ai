"""
UI and appearance commands for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table

from veni.commands.base import BaseCommand, console
from veni.config import config


class ClearCommand(BaseCommand):
    """Clear terminal screen."""

    @property
    def name(self) -> str:
        return "/clear"

    @property
    def description(self) -> str:
        return "Clear the terminal screen and reset the header."

    def execute(self, args: List[str]) -> Optional[str]:
        console.clear()
        self.bot.print_header()
        self.bot.current_images = []
        return None


class ThemeCommand(BaseCommand):
    """Switch themes."""

    @property
    def name(self) -> str:
        return "/theme"

    @property
    def description(self) -> str:
        return "Switch between predefined visual themes."

    @property
    def usage(self) -> str:
        return "/theme [theme_name]"

    def execute(self, args: List[str]) -> Optional[str]:
        themes = {
            "cyberpunk": {"primary": "#00d4ff", "secondary": "#7b68ee"},
            "minimal": {"primary": "#ffffff", "secondary": "#888888"},
            "retro": {"primary": "#00ff00", "secondary": "#003300"},
            "professional": {"primary": "#3498db", "secondary": "#2c3e50"},
            "dark": {"primary": "#9b59b6", "secondary": "#8e44ad"},
        }

        if args and args[0] in themes:
            theme_name = args[0]
            theme_colors = themes[theme_name]
            self.bot.COLORS.update(theme_colors)
            config.set("theme_colors", self.bot.COLORS)
            self.show_success(f"Theme switched to {theme_name}")
            return None

        table = Table(
            title="Available Themes", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Name", style="cyan")
        table.add_column("Preview", style="white")
        for name, colors in themes.items():
            preview = f"Primary: {colors['primary']} | Secondary: {colors['secondary']}"
            table.add_row(name, preview)
        console.print(table)
        console.print("\n[dim]Use /theme <name> to switch themes[/dim]")
        return None


class ColorsCommand(BaseCommand):
    """Show current colors."""

    @property
    def name(self) -> str:
        return "/colors"

    @property
    def description(self) -> str:
        return "Display the currently active color scheme."

    def execute(self, args: List[str]) -> Optional[str]:
        table = Table(
            title="Current Colors", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Color", style="cyan")
        table.add_column("Hex Value", style="white")
        table.add_column("Preview", style="white")
        for color_name, hex_value in self.bot.COLORS.items():
            preview = f"[{hex_value}]████[/{hex_value}]"
            table.add_row(color_name, hex_value, preview)
        console.print(table)
        return None


class ContrastCommand(BaseCommand):
    """Toggle high contrast mode."""

    @property
    def name(self) -> str:
        return "/contrast"

    @property
    def description(self) -> str:
        return "Toggle between high contrast and normal color modes."

    def execute(self, args: List[str]) -> Optional[str]:
        high_contrast_colors = {
            "primary": "#ffffff",
            "secondary": "#ffff00",
            "accent": "#00ffff",
            "user": "#00ff00",
            "assistant": "#00ffff",
            "dim": "#cccccc",
            "error": "#ff0000",
            "success": "#00ff00",
            "warning": "#ffff00",
        }
        current_primary = self.bot.COLORS.get("primary", "#00d4ff")
        if current_primary == "#ffffff":
            theme_colors = config.get("theme_colors", {})
            self.bot.COLORS.update(theme_colors)
            self.show_success("Switched to normal contrast mode")
        else:
            self.bot.COLORS.update(high_contrast_colors)
            self.show_success("Switched to high contrast mode")
        return None


class MenuCommand(BaseCommand):
    """Show quick actions menu."""

    @property
    def name(self) -> str:
        return "/menu"

    @property
    def description(self) -> str:
        return "Display a quick access menu for common actions."

    def execute(self, args: List[str]) -> Optional[str]:
        table = Table(
            title="Quick Actions",
            box=box.SIMPLE,
            header_style="bold cyan",
            show_header=False,
        )
        table.add_column("Command", style="bold yellow")
        table.add_column("Action", style="white")
        table.add_row("/new", "Start a new conversation")
        table.add_row("/save", "Save current session")
        table.add_row("/load", "Load a saved session")
        table.add_row("/help", "Show help")
        table.add_row("/model", "Switch AI model/provider")
        table.add_row("/clear", "Clear screen")
        table.add_row("/theme", "Switch visual theme")
        table.add_row("/quit", "Exit Veni AI")
        console.print(table)
        return None


class TipsCommand(BaseCommand):
    """Show daily tips."""

    @property
    def name(self) -> str:
        return "/tips"

    @property
    def description(self) -> str:
        return "Show a random helpful tip for using Veni AI."

    def execute(self, args: List[str]) -> Optional[str]:
        import random

        tips = [
            "Use /help <command> for detailed help on specific commands",
            "Type /menu to see quick actions menu",
            "Use /stats to see detailed session statistics",
            "Use /tree to visualize your conversation",
            "Press Ctrl+E to enter multi-line input mode",
            "Press Ctrl+R to search command history",
            "Use /theme to switch between different visual themes",
            "Press Ctrl+C to cancel current input",
            "Use /colors to see current color scheme",
            "Type /export md to export your session as Markdown",
            "Use /banner to toggle compact header mode",
        ]
        tip = random.choice(tips)
        panel = Panel(
            tip, title="Daily Tip", border_style=self.colors["accent"], box=box.SIMPLE
        )
        console.print(panel)
        return None


class RedactCommand(BaseCommand):
    """Toggle redaction mode."""

    @property
    def name(self) -> str:
        return "/redact"

    @property
    def description(self) -> str:
        return "Toggle automatic redaction of sensitive information (API keys, etc.)."

    def execute(self, args: List[str]) -> Optional[str]:
        from veni.security import redactor

        redactor.enabled = not redactor.enabled
        status = "enabled" if redactor.enabled else "disabled"
        self.show_success(f"Automatic redaction {status}")
        return None


class BannerCommand(BaseCommand):
    """Toggle compact banner."""

    @property
    def name(self) -> str:
        return "/banner"

    @property
    def description(self) -> str:
        return "Toggle between full ASCII art banner and compact one-line header."

    def execute(self, args: List[str]) -> Optional[str]:
        self.bot._compact_banner = not self.bot._compact_banner
        config.set("compact_banner", self.bot._compact_banner)
        mode = "compact" if self.bot._compact_banner else "full"
        self.show_success(f"Switched to {mode} banner mode")
        return None


class NetworkCommand(BaseCommand):
    """Check network status."""

    @property
    def name(self) -> str:
        return "/network"

    @property
    def description(self) -> str:
        return "Check connectivity to the internet and the AI provider."

    def execute(self, args: List[str]) -> Optional[str]:
        import requests

        try:
            requests.get("https://www.google.com", timeout=3)
            internet = "[green]ONLINE[/green]"
        except Exception:
            internet = "[red]OFFLINE[/red]"

        provider_ping = self.bot._ping_provider()

        table = Table(
            title="Network Status", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_row("Internet", internet)
        table.add_row(f"Provider ({self.bot.provider_name})", provider_ping)
        console.print(table)
        return None
