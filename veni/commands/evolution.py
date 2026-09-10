"""
Self-Evolution Command for Veni AI.

Allows the AI to generate and install its own plugins to expand its capabilities.
"""

from pathlib import Path
from typing import List, Optional

from rich.panel import Panel

from veni.commands.base import BaseCommand, console


class EvolveCommand(BaseCommand):
    """Command to trigger self-evolution."""

    @property
    def name(self) -> str:
        return "/evolve"

    @property
    def description(self) -> str:
        return "Command Veni to expand its capabilities by generating a new plugin."

    @property
    def usage(self) -> str:
        return "/evolve [description of the new capability]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Please describe what capability you want to add.")
            return None

        description = " ".join(args)
        self.show_warning(f"🧬 Starting evolution process for: {description}...")

        # System prompt for evolution
        evolution_prompt = (
            f"You are evolving yourself. Create a new Veni AI plugin in Python that implements "
            f"the following capability: {description}. \n\n"
            f"The plugin must follow this structure:\n"
            f"```python\n"
            f"PLUGIN_COMMANDS = {{\n"
            f"    '/command_name': lambda args: 'response',\n"
            f"}}\n"
            f"PLUGIN_HELP = {{\n"
            f"    '/command_name': 'Description',\n"
            f"}}\n"
            f"```\n"
            f"Or use a `register(bot)` function for more complex logic.\n"
            f"Respond ONLY with the Python code for the plugin file."
        )

        # We trigger a special chat turn
        try:
            messages = [{"role": "user", "content": evolution_prompt}]
            full_response = ""
            for chunk in self.bot.ai_client.chat(messages, stream=True):
                full_response += chunk

            # Extract code block
            import re
            code_match = re.search(r"```python\n([\s\S]*?)\n```", full_response)
            if not code_match:
                code_match = re.search(r"```\n([\s\S]*?)\n```", full_response)

            plugin_code = code_match.group(1) if code_match else full_response.strip()

            # Save to plugins directory
            plugins_dir = Path.cwd() / "plugins"
            plugins_dir.mkdir(exist_ok=True)

            # Generate a filename
            import hashlib
            filename = f"evolved_{hashlib.md5(description.encode()).hexdigest()[:8]}.py"
            plugin_path = plugins_dir / filename

            plugin_path.write_text(plugin_code, encoding="utf-8")

            self.show_success(f"Evolution complete! New plugin saved to plugins/{filename}")
            console.print(Panel("New capability added. Restart Veni or use /reload (if implemented) to activate.",
                               title="🧬 Evolution Result", border_style="green"))

            # Hot-reload plugins
            self.bot._load_plugins()
            self.show_success("Plugin hot-reloaded and active!")

        except Exception as e:
            self.show_error(f"Evolution failed: {e}")

        return None
