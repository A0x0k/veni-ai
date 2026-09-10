"""
Plugin loading logic for Veni AI.

Discovers and loads drop-in Python plugins from the plugins/ directory.
"""

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from veni.config import config

if TYPE_CHECKING:
    from veni.core import TerminalChatbot


def project_plugins_enabled() -> bool:
    """Return whether plugins from the current project may be executed."""
    env_value = os.getenv("VENI_ENABLE_PROJECT_PLUGINS", "").strip().lower()
    if env_value in {"1", "true", "yes", "on"}:
        return True
    if env_value in {"0", "false", "no", "off"}:
        return False
    return bool(config.get("features.project_plugins", False))


def load_plugins(bot: "TerminalChatbot") -> tuple[dict[str, Callable], dict[str, str]]:
    """
    Load all plugins from the plugins/ directory.

    Returns (commands, help_map) dicts to be merged into the bot.
    """
    plugin_commands: dict[str, Callable] = {}
    plugin_help: dict[str, str] = {}

    plugins_dir = Path.cwd() / "plugins"
    if not plugins_dir.exists():
        return plugin_commands, plugin_help
    if not project_plugins_enabled():
        bot.show_warning(
            "Project plugins are disabled. Set features.project_plugins=true "
            "or VENI_ENABLE_PROJECT_PLUGINS=1 to load trusted plugins."
        )
        return plugin_commands, plugin_help

    for plugin_path in plugins_dir.glob("*.py"):
        cmds, help_map = _load_single_plugin(bot, plugin_path)
        plugin_commands.update(cmds)
        plugin_help.update(help_map)

    return plugin_commands, plugin_help


def _load_single_plugin(
    bot: "TerminalChatbot", plugin_path: Path
) -> tuple[dict[str, Callable], dict[str, str]]:
    commands: dict[str, Callable] = {}
    help_map: dict[str, str] = {}

    try:
        mod_name = f"veni_plugin_{plugin_path.stem}"
        spec = spec_from_file_location(mod_name, plugin_path)
        if not spec or not spec.loader:
            return commands, help_map

        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "register"):
            result = module.register(bot)
            if isinstance(result, dict):
                commands.update(result)

        if hasattr(module, "PLUGIN_COMMANDS") and isinstance(
            module.PLUGIN_COMMANDS, dict
        ):
            commands.update(module.PLUGIN_COMMANDS)

        if hasattr(module, "PLUGIN_HELP") and isinstance(module.PLUGIN_HELP, dict):
            help_map.update(module.PLUGIN_HELP)

        # Normalize command names to start with /
        normalized: dict[str, Callable] = {}
        for cmd, handler in commands.items():
            key = cmd if cmd.startswith("/") else f"/{cmd}"
            normalized[key] = handler
        commands = normalized

    except Exception as e:
        bot.show_warning(f"Plugin load failed: {plugin_path.name} ({e})")

    return commands, help_map
