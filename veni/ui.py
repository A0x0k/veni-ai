"""
UI/display helpers for Veni AI.

All Rich console output methods extracted from TerminalChatbot.
"""

from pathlib import Path
from typing import TYPE_CHECKING, List

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from rich.table import Table

from veni import __version__
from veni.config import config

if TYPE_CHECKING:
    from veni.core import TerminalChatbot

console = Console()


def print_header(bot: "TerminalChatbot") -> None:
    """Print stylized Veni banner with gradients."""
    from rich.align import Align
    from rich.rule import Rule

    # Check if compact mode is enabled
    if getattr(bot, "_compact_banner", False):
        info_text = Text.assemble(
            (" ⚡ VENI ", f"bold white on {bot.COLORS['primary']}"),
            (f" v{__version__} ", "bold white on #8b5cf6"),
            ("  ", ""),
            (f"{bot.provider_name.upper()}", "bold cyan"),
            (" • ", "dim"),
            (f"{bot.model_name}", "italic #94a3b8"),
        )
        console.print(info_text)
        console.print(Rule(style="#1e293b"))
        return

    logo = """
   ██╗   ██╗███████╗███╗   ██╗██╗
   ██║   ██║██╔════╝████╗  ██║██║
   ██║   ██║█████╗  ██╔██╗ ██║██║
   ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║
    ╚████╔╝ ███████╗██║ ╚████║██║
     ╚═══╝  ╚══════╝╚═╝  ╚═══╝╚═╝"""

    gradient_colors = ["#6366f1", "#8b5cf6", "#d946ef"]
    styled_logo = Text()
    for i, line in enumerate(logo.strip("\n").split("\n")):
        color = gradient_colors[min(i, len(gradient_colors) - 1)]
        styled_logo.append(line + "\n", style=color)

    info_text = Text.assemble(
        (f" v{__version__} ", "bold white on #8b5cf6"),
        ("  ", ""),
        (f"{bot.provider_name.upper()}", "bold cyan"),
        (" • ", "dim"),
        (f"{bot.model_name}", "italic #94a3b8"),
    )

    banner_panel = Panel(
        Align.center(styled_logo + "\n" + info_text),
        border_style="#475569",
        box=box.SIMPLE,
        padding=(1, 2),
    )
    console.print(banner_panel)
    console.print(Rule(style="#1e293b"))


def show_model_presets(bot: "TerminalChatbot") -> None:
    presets = config.get("model_presets", {})
    provider_name = bot.provider_name
    if provider_name == "unknown":
        provider_name = config.get("default_provider", "ollama")
    models = presets.get(provider_name, [])
    if not models:
        return
    table = Table(
        title=f"Model Presets ({provider_name})",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Model", style="white")
    for i, m in enumerate(models, 1):
        table.add_row(str(i), m)
    console.print(table)


def format_user_message(
    bot: "TerminalChatbot", content: str, images: List[str] = None
) -> None:
    """Format and print user message with a side rail."""
    user_content = Text()
    user_content.append(" 👤 YOU ", style="bold #10b981")
    user_content.append(" " + content, style="white")
    if images:
        for img in images:
            user_content.append(f"\n   📎 {Path(img).name}", style="dim italic")
    console.print(user_content)


def show_success(bot: "TerminalChatbot", message: str) -> None:
    console.print(f"[{bot.COLORS['success']}]✔ {message}[/{bot.COLORS['success']}]")


def show_status(bot: "TerminalChatbot", message: str) -> None:
    console.print(f"  [{bot.COLORS['dim']}]⚙ {message}[/{bot.COLORS['dim']}]")


def show_error(bot: "TerminalChatbot", message: str) -> None:
    console.print(f"[{bot.COLORS['error']}]✖ {message}[/{bot.COLORS['error']}]")


def show_warning(bot: "TerminalChatbot", message: str) -> None:
    console.print(f"[{bot.COLORS['warning']}]⚠ {message}[/{bot.COLORS['warning']}]")


def display_assistant_response(bot: "TerminalChatbot", response: str) -> None:
    """Render the final AI response in a styled panel."""
    console.print(
        Panel(
            Markdown(response),
            title=" VENI ",
            title_align="left",
            border_style=bot.COLORS["assistant"],
            box=box.SIMPLE,
            padding=(0, 2),
        )
    )
    console.print()
