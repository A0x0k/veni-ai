"""
AI configuration and control commands for Veni AI.
"""

from typing import List, Optional

from rich import box
from rich.prompt import Prompt
from rich.table import Table

from veni.commands.base import BaseCommand, console
from veni.config import config
from veni.providers.factory import create_ai_client


class SystemCommand(BaseCommand):
    """Set the system prompt."""

    @property
    def name(self) -> str:
        return "/system"

    @property
    def description(self) -> str:
        return "Set the AI's system prompt or persona."

    @property
    def usage(self) -> str:
        return "/system <text>"

    def execute(self, args: List[str]) -> Optional[str]:
        if args:
            self.bot.history.system_prompt = " ".join(args)
            self.show_success("System Prompt updated")
        else:
            console.print(
                f"[dim]Current System Prompt: {self.bot.history.system_prompt}[/dim]"
            )
        return None


class ModelCommand(BaseCommand):
    """Switch models or providers."""

    @property
    def name(self) -> str:
        return "/model"

    @property
    def description(self) -> str:
        return "Switch the AI model or provider."

    @property
    def usage(self) -> str:
        return "/model [model_name | --list]"

    def execute(self, args: List[str]) -> Optional[str]:
        if args and args[0] in ["--list", "list"]:
            self.bot._show_model_presets()
            return None

        if args and args[0] == "--set":
            if len(args) < 2:
                self.show_error("Usage: /model --set <model_name>")
                return None
            args = [args[1]]

        if args:
            self.bot.ai_client.model = args[0]
            self.show_success(f"Model switched to: {args[0]}")
            return None

        presets = config.get("model_presets", {})
        available_models = presets.get(self.bot.provider_name, [])
        table = Table(
            title=f"Models ({self.bot.provider_name})",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Model", style="white")
        table.add_column("Status", style="dim")

        for i, m in enumerate(available_models, 1):
            status = (
                "[bold green]current[/bold green]"
                if m == self.bot.model_name
                else "suggested"
            )
            table.add_row(str(i), m, status)

        if available_models:
            console.print(table)
            choices = [
                str(i) for i in range(1, len(available_models) + 1)
            ] + available_models
            choice = Prompt.ask(
                "Select model ID or name", choices=choices, default=self.bot.model_name
            )
            selected = available_models[int(choice) - 1] if choice.isdigit() else choice
        else:
            selected = Prompt.ask("Enter model name", default=self.bot.model_name)

        # Smart Provider Detection
        new_provider = None
        s_lower = selected.lower()
        if "gemini" in s_lower:
            new_provider = "gemini"
        elif "gpt" in s_lower or "openai" in s_lower:
            new_provider = "openai"
        elif "claude" in s_lower or "anthropic" in s_lower:
            new_provider = "anthropic"
        elif "deepseek" in s_lower:
            new_provider = "deepseek"
        elif "llama" in s_lower or "qwen" in s_lower:
            new_provider = "ollama"

        if new_provider and new_provider != self.bot.provider_name:
            try:
                self.bot.ai_client = create_ai_client(new_provider, selected)
                self.show_success(
                    f"Switched to Provider: {new_provider} | Model: {selected}"
                )
            except Exception as e:
                self.show_error(f"Failed to switch provider: {e}")
        else:
            self.bot.ai_client.model = selected
            self.show_success(f"Switched to model: {selected}")
        return None


class TemperatureCommand(BaseCommand):
    """Set generation temperature."""

    @property
    def name(self) -> str:
        return "/temperature"

    @property
    def description(self) -> str:
        return "Set the sampling temperature (0.0 to 1.0)."

    @property
    def usage(self) -> str:
        return "/temperature <value>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            console.print(
                f"[dim]Temperature: {self.bot.generation_params['temperature']}[/dim]"
            )
            return None
        try:
            value = float(args[0])
            self.bot.generation_params["temperature"] = value
            self.show_success(f"Temperature set to {value}")
        except ValueError:
            self.show_error("Usage: /temperature <number>")
        return None


class TopPCommand(BaseCommand):
    """Set nucleus sampling top_p."""

    @property
    def name(self) -> str:
        return "/top_p"

    @property
    def description(self) -> str:
        return "Set the nucleus sampling (top_p) value."

    @property
    def usage(self) -> str:
        return "/top_p <value>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            console.print(f"[dim]Top_p: {self.bot.generation_params['top_p']}[/dim]")
            return None
        try:
            value = float(args[0])
            self.bot.generation_params["top_p"] = value
            self.show_success(f"Top_p set to {value}")
        except ValueError:
            self.show_error("Usage: /top_p <number>")
        return None


class MaxTokensCommand(BaseCommand):
    """Set max output tokens."""

    @property
    def name(self) -> str:
        return "/max_tokens"

    @property
    def description(self) -> str:
        return "Set the maximum number of output tokens."

    @property
    def usage(self) -> str:
        return "/max_tokens <value>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            console.print(
                f"[dim]Max tokens: {self.bot.generation_params['max_tokens']}[/dim]"
            )
            return None
        try:
            value = int(args[0])
            self.bot.generation_params["max_tokens"] = value
            self.show_success(f"Max tokens set to {value}")
        except ValueError:
            self.show_error("Usage: /max_tokens <integer>")
        return None


class TemplateCommand(BaseCommand):
    """List or apply prompt templates."""

    @property
    def name(self) -> str:
        return "/template"

    @property
    def description(self) -> str:
        return "List or apply a predefined prompt template."

    @property
    def usage(self) -> str:
        return "/template [name]"

    def execute(self, args: List[str]) -> Optional[str]:
        templates = config.get("prompt_templates", {})
        if not args or args[0] in ["--list", "list"]:
            table = Table(
                title="Prompt Templates", box=box.ROUNDED, header_style="bold magenta"
            )
            table.add_column("Name", style="cyan")
            table.add_column("Preview", style="white")
            for name, text in templates.items():
                preview = (text[:60] + "...") if len(text) > 60 else text
                table.add_row(name, preview)
            console.print(table)
            return None
        name = args[0]
        if name not in templates:
            self.show_error(f"Template not found: {name}")
            return None
        self.bot.history.system_prompt = templates[name]
        self.show_success(f"System prompt set to template: {name}")
        return None


class StatusCommand(BaseCommand):
    """Show provider status."""

    @property
    def name(self) -> str:
        return "/status"

    @property
    def description(self) -> str:
        return "Check the status and connectivity of the current AI provider."

    @property
    def usage(self) -> str:
        return "/status [--ping]"

    def execute(self, args: List[str]) -> Optional[str]:
        ping = "--ping" in args or self.bot.provider_name == "ollama"
        key = getattr(self.bot.ai_client, "api_key", None)
        base_url = getattr(self.bot.ai_client, "base_url", None)

        key_status = "n/a"
        if key is not None:
            key_status = "set" if key else "missing"

        reachable = "not checked"
        if ping and base_url:
            reachable = self.bot._ping_provider()

        table = Table(
            title="Provider Status", box=box.ROUNDED, header_style="bold magenta"
        )
        table.add_column("Provider", style="cyan")
        table.add_column("Model", style="white")
        table.add_column("Key", style="white")
        table.add_column("Endpoint", style="dim")
        table.add_column("Reachable", style="white")

        table.add_row(
            self.bot.provider_name,
            self.bot.model_name,
            key_status,
            base_url or "n/a",
            reachable,
        )
        console.print(table)
        return None


class SetupCommand(BaseCommand):
    """Interactive wizard to setup providers and API keys."""

    @property
    def name(self) -> str:
        return "/setup"

    @property
    def description(self) -> str:
        return "Interactive wizard to configure AI providers and API keys."

    def execute(self, args: List[str]) -> Optional[str]:
        console.print("\n[bold cyan]⚡ Veni AI Setup Wizard[/bold cyan]")
        console.print("[dim]------------------------------------[/dim]")

        # 1. Choose Provider
        providers = ["gemini", "openai", "anthropic", "openrouter", "mistral", "perplexity", "ollama", "deepseek", "groq", "free"]
        table = Table(title="Available Providers", box=box.ROUNDED)
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Provider", style="white")
        for i, p in enumerate(providers, 1):
            table.add_row(str(i), p)
        console.print(table)

        p_choice = Prompt.ask("Choose a provider (ID or name)", choices=[str(i) for i in range(1, len(providers)+1)] + providers, default="1")
        provider = providers[int(p_choice)-1] if p_choice.isdigit() else p_choice

        # 2. Choose Login Method
        method = "manual"
        if provider not in ["free", "ollama"]:
            method = Prompt.ask("Choose login method", choices=["manual", "browser"], default="manual")

        api_key = None
        if method == "manual":
            if provider not in ["free", "ollama"]:
                current_key = config.get(f"api_keys.{provider}", "")
                key_prompt = f"Enter your {provider.upper()} API Key"
                if current_key:
                    key_prompt += " (leave empty to keep current)"

                api_key = Prompt.ask(key_prompt, password=True)
                if not api_key and current_key:
                    api_key = current_key
        else:
            # Browser-based login flow
            urls = {
                "gemini": "https://aistudio.google.com/app/apikey",
                "openai": "https://platform.openai.com/api-keys",
                "anthropic": "https://console.anthropic.com/settings/keys",
                "openrouter": "https://openrouter.ai/keys",
                "mistral": "https://console.mistral.ai/api-keys/",
                "perplexity": "https://www.perplexity.ai/settings/api",
            }
            if provider in urls:
                self.show_warning(f"🚀 Opening {provider.upper()} login page in a visible browser...")
                # We need to access the tool directly
                browser_tool = self.bot.tool_registry.get("browser_automation")
                if browser_tool:
                    browser_tool.execute(action="navigate", url=urls[provider], visible=True)
                    console.print("\n[bold yellow]Step 1:[/bold yellow] Log in to your account in the browser window.")
                    console.print("[bold yellow]Step 2:[/bold yellow] Copy your API Key from the page.")
                    console.print("[bold yellow]Step 3:[/bold yellow] Come back here and paste it.")

                    api_key = Prompt.ask(f"Paste the {provider.upper()} API Key here", password=True)
                    browser_tool.cleanup()
                else:
                    self.show_error("Browser tool not available.")
            else:
                self.show_error(f"Browser login not yet supported for {provider}. Switching to manual.")
                api_key = Prompt.ask(f"Enter your {provider.upper()} API Key", password=True)

        # 3. Save to config
        if api_key:
            config.set(f"api_keys.{provider}", api_key)
        config.set("default_provider", provider)

        # 4. Switch current client
        try:
            self.bot.ai_client = create_ai_client(provider, api_key=api_key)
            self.show_success(f"Successfully configured and switched to {provider}!")

            # Offer to help find the key using browser if missing
            if not api_key and provider not in ["free", "ollama"]:
                if Prompt.ask("Would you like me to help you find your API key in the browser?", choices=["y", "n"], default="y") == "y":
                    urls = {
                        "gemini": "https://aistudio.google.com/app/apikey",
                        "openai": "https://platform.openai.com/api-keys",
                        "anthropic": "https://console.anthropic.com/settings/keys",
                        "openrouter": "https://openrouter.ai/keys",
                        "mistral": "https://console.mistral.ai/api-keys/",
                        "perplexity": "https://www.perplexity.ai/settings/api",
                    }
                    if provider in urls:
                        self.bot.handle_command(f"browser_automation navigate url='{urls[provider]}'")
                        self.show_warning("I've opened the API key page for you. Copy the key and run /setup again.")

        except Exception as e:
            self.show_error(f"Failed to switch provider: {e}")

        return None
