"""
CLI Entry point for Veni AI.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

# Suppress TensorFlow/oneDNN logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.table import Table

from veni import __version__

from veni.config import config
from veni.logger import logger
from veni.providers.factory import create_ai_client
from veni.skill_registry import SkillRegistry

app = typer.Typer(help="⚡ Veni AI Chatbot - Your Intelligent Terminal")
console = Console()


def _version_callback(value: bool):
    if value:
        typer.echo(f"veni {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


# --- Skill CLI subcommands ---
skills_app = typer.Typer(help="Manage Veni AI skills")


@skills_app.command("list")
def skill_list(
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Filter by source (builtin, installed, custom)"
    ),
):
    """List all available skills."""
    registry = SkillRegistry()
    registry.scan()
    skills = registry.list_skills()

    if source:
        skills = [s for s in skills if s.source == source]

    if not skills:
        console.print("[dim]No skills found.[/dim]")
        raise typer.Exit()

    table = Table(title="Available Skills", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Name", style="bold magenta")
    table.add_column("Description", style="white")
    table.add_column("Source", style="dim")
    table.add_column("Triggers", style="dim")

    for s in skills:
        table.add_row(
            s.name,
            s.description[:55],
            s.source,
            ", ".join(s.triggers[:3]),
        )

    console.print(table)


@skills_app.command("search")
def skill_search(
    query: str = typer.Argument(..., help="Search query for skills"),
):
    """Search for skills by trigger keywords."""
    registry = SkillRegistry()
    registry.scan()
    matches = registry.match_triggers(query)

    if not matches:
        console.print(f"[dim]No skills match '{query}'.[/dim]")
        raise typer.Exit()

    table = Table(
        title=f"Skills matching '{query}'", box=box.ROUNDED, header_style="bold cyan"
    )
    table.add_column("Name", style="bold magenta")
    table.add_column("Description", style="white")
    table.add_column("Source", style="dim")

    for m in matches:
        table.add_row(m.name, m.description[:60], m.source)

    console.print(table)


@skills_app.command("install")
def skill_install(
    source: str = typer.Argument(
        ..., help="Skill source: name, GitHub URL, or local path"
    ),
):
    """Install a skill from registry, URL, or local path."""
    registry = SkillRegistry()
    registry.scan()

    # Check if it's a built-in skill name
    skill = registry.get_skill(source)
    if skill:
        console.print(f"[green]✓ Skill '{source}' is already built-in.[/green]")
        return

    # Check if it's a local path
    local_path = Path(source).expanduser().resolve()
    if local_path.exists() and (local_path / "SKILL.md").exists():
        dest = registry.installed_dir / local_path.name
        if dest.exists():
            console.print(f"[yellow]Skill already installed at {dest}[/yellow]")
            return
        shutil.copytree(local_path, dest)
        console.print(f"[green]✓ Installed skill from {local_path}[/green]")
        return

    # Check if it's a GitHub URL
    if source.startswith(("http://", "https://")):
        import subprocess

        # Extract skill name from URL
        skill_name = source.rstrip("/").split("/")[-1].replace(".git", "")
        dest = registry.installed_dir / skill_name
        if dest.exists():
            console.print(f"[yellow]Skill already installed at {dest}[/yellow]")
            return

        console.print(f"[dim]Cloning {source}...[/dim]")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", source, str(dest)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            console.print(f"[red]Clone failed: {result.stderr.strip()}[/red]")
            if dest.exists():
                shutil.rmtree(dest)
            raise typer.Exit(code=1)

        # Verify it's a valid skill
        if not (dest / "SKILL.md").exists():
            console.print(
                "[red]Cloned repo does not contain SKILL.md. Not a valid skill.[/red]"
            )
            shutil.rmtree(dest)
            raise typer.Exit(code=1)

        console.print(f"[green]✓ Installed skill: {skill_name}[/green]")
        return

    console.print(f"[red]Skill not found: '{source}'[/red]")
    console.print("Use 'veni skill list' to see available skills.")
    raise typer.Exit(code=1)


@skills_app.command("remove")
def skill_remove(
    name: str = typer.Argument(..., help="Name of the skill to remove"),
):
    """Remove an installed skill."""
    registry = SkillRegistry()
    registry.scan()

    skill_dir = registry.installed_dir / name
    if not skill_dir.exists():
        console.print(f"[red]Skill not found: '{name}'[/red]")
        raise typer.Exit(code=1)

    shutil.rmtree(skill_dir)
    console.print(f"[green]✓ Removed skill: {name}[/green]")


@skills_app.command("status")
def skill_status():
    """Show skill system status."""
    registry = SkillRegistry()
    registry.scan()
    skills = registry.list_skills()

    by_source = {}
    for s in skills:
        by_source[s.source] = by_source.get(s.source, 0) + 1

    console.print("[bold]Skill System Status[/bold]")
    console.print(f"Total skills: {len(skills)}")
    for source, count in sorted(by_source.items()):
        console.print(f"  {source}: {count}")
    console.print(f"Installed dir: {registry.installed_dir}")


app.add_typer(skills_app, name="skill")


@app.command()
def chat(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="AI provider (ollama, openai, gemini, anthropic, groq, deepseek, qwen, free)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Specific model name"
    ),
    api_key: Optional[str] = typer.Option(
        None, "--key", "-k", help="API Key if required"
    ),
    context_tokens: int = typer.Option(
        4096, "--context", "-c", help="Max context tokens"
    ),
):
    """
    Start an interactive chat session.
    """
    try:
        from veni.core import TerminalChatbot
        load_dotenv()
        client = create_ai_client(provider, model, api_key)

        if (provider or "").lower() == "free" or client.__class__.__name__ == "FreeAIClient":
            console.print(
                "[bold yellow]⚠ Free provider:[/bold yellow] Uses unofficial third-party "
                "endpoints (Pollinations). Reliability is not guaranteed — responses may "
                "fail or be rate-limited without warning. Tool use is not supported.\n"
                "For reliable free AI, install Ollama: [cyan]https://ollama.com[/cyan]\n"
            )

        logger.info(
            "Launching chat with %s/%s context=%d",
            client.__class__.__name__,
            client.model,
            context_tokens,
        )
        bot = TerminalChatbot(client, context_tokens=context_tokens)
        bot.run()
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def pipe(
    message: str = typer.Argument("", help="The message to send to the AI model"),
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="AI provider (ollama, openai, gemini, anthropic, groq, deepseek, qwen, free)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Specific model name"
    ),
    api_key: Optional[str] = typer.Option(
        None, "--key", "-k", help="API Key if required"
    ),
    context_tokens: int = typer.Option(
        4096, "--context", "-c", help="Max context tokens"
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Output raw text without Rich formatting"
    ),
):
    """
    Send a single message and print the AI response.

    Designed for CI/CD pipelines, IDE integration, and shell pipes.
    Reads from stdin if no message argument is provided.

    Examples:
        veni pipe "explain this error: TypeError: ..."
        echo "review this code" | veni pipe
        veni pipe "fix the bug in main.py" --provider openai --raw
    """
    # Read from stdin if no message provided
    if not message and not sys.stdin.isatty():
        message = sys.stdin.read().strip()

    if not message:
        console.print(
            "[bold red]Error:[/bold red] "
            "No message provided. Pass as argument or pipe via stdin."
        )
        raise typer.Exit(code=1)

    try:
        load_dotenv()
        client = create_ai_client(provider, model, api_key)
        bot = TerminalChatbot(client, context_tokens=context_tokens)
        bot._init_codebase_indexer()

        # Build messages
        messages = [{"role": "user", "content": message}]

        # Get response (non-streaming for pipe mode)
        response = "".join(
            client.chat(
                bot.history.get_context_messages(
                    context_tokens, model=bot.model_name, ai_client=client
                ),
                stream=True, 
                tools=bot.tool_registry.get_declarations()
            )
        )

        # Output
        if raw:
            # Plain text output — ideal for piping to other tools
            sys.stdout.write(response)
            sys.stdout.write("\n")
        else:
            console.print(response)

        logger.info("Pipe mode: %d chars in, %d chars out", len(message), len(response))
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def init():
    """
    Initialize configuration file.
    """
    config.save()
    console.print(f"[green]Configuration initialized at {config.config_path}[/green]")


