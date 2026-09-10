"""
Startup and teardown logic for Veni AI.

Handles session resume, codebase indexing, MCP server init, and autosave.
"""

from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt

if TYPE_CHECKING:
    from veni.core import TerminalChatbot

console = Console()


def maybe_resume_last_session(bot: "TerminalChatbot") -> None:
    """Offer to resume the last autosaved session."""
    autosave = bot.history.storage_dir / "autosave_last.json"
    if not autosave.exists():
        return
    try:
        choice = Prompt.ask(
            "Resume last session from autosave?", choices=["y", "n"], default="y"
        )
        if choice == "y" and bot.history.load("autosave_last"):
            console.print(
                f"[{bot.COLORS['success']}]✔ Resumed last session"
                f"[/{bot.COLORS['success']}]"
            )
    except Exception:
        pass


def init_codebase_indexer(bot: "TerminalChatbot") -> None:
    """Build a codebase index for repo awareness, then init MCP servers."""
    from veni.indexer import CodebaseIndexer

    try:
        console.print("[dim]Indexing codebase...[/dim]", end="")
        bot.codebase_indexer = CodebaseIndexer(bot.workspace_root)
        file_count = bot.codebase_indexer.scan()
        if file_count > 0:
            console.print(f"\r[dim]Indexed {file_count} files in {bot.workspace_root.name}[/dim]")
        else:
            console.print("\r[dim]No files to index[/dim]")
        if bot.crossref_analyzer:
            bot.crossref_analyzer.indexer = bot.codebase_indexer

        if hasattr(bot, "parallel_engine"):
            try:
                bot.parallel_engine.run_parallel(
                    [
                        ("count_lines", bot._count_total_lines),
                        ("find_todos", bot._find_todos),
                    ]
                )
            except Exception:
                pass
    except Exception:
        pass

    _init_mcp_servers(bot)


def _init_mcp_servers(bot: "TerminalChatbot") -> None:
    """Load and connect to MCP servers from mcp_servers.json."""
    import os
    from veni.mcp import MCPClient, load_mcp_config

    mcp_config = os.path.join(bot.workspace_root, "mcp_servers.json")
    if not os.path.exists(mcp_config):
        return

    clients = load_mcp_config(mcp_config)
    if not clients:
        return

    console.print(f"[dim]Connecting to {len(clients)} MCP server(s)...[/dim]")
    connected = 0
    for client in clients:
        if client.connect():
            for tool in client.get_tools(bot):
                bot.tool_registry.register(tool)
            bot.mcp_clients.append(client)
            connected += len(client.get_tools(bot))

    if connected > 0:
        console.print(
            f"[dim]Connected to {len(clients)} MCP server(s), "
            f"{connected} MCP tools loaded[/dim]"
        )


def autosave_session(bot: "TerminalChatbot") -> None:
    """Save session state and shut down background services."""
    if bot.history.messages:
        try:
            bot.history.save("autosave_last")
        except Exception:
            pass

    if hasattr(bot, "scheduler"):
        bot.scheduler.stop()
    if hasattr(bot, "telegram_gateway"):
        bot.telegram_gateway.stop()

    for client in getattr(bot, "mcp_clients", []):
        try:
            client.disconnect()
        except Exception:
            pass
