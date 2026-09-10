"""
Example Veni AI Plugin: Weather lookup.

Drop this file into the `plugins/` directory and restart Veni.
Run `/weather <city>` inside a chat to get current weather info.

To create your own plugin:
1. Copy this file and rename it (e.g. `my_plugin.py`).
2. Edit PLUGIN_COMMANDS / PLUGIN_HELP, or implement `register(bot)`.
3. Add your command handlers that use `bot` to access history, tools, etc.
"""

from datetime import datetime
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Plugin metadata (optional — used by the built-in loader)
# ---------------------------------------------------------------------------
PLUGIN_NAME = "weather"
PLUGIN_VERSION = "0.1.0"

# Command → handler mapping (legacy style — still supported)
PLUGIN_COMMANDS: Dict[str, Any] = {}

# Help text shown by `/help`
PLUGIN_HELP: Dict[str, str] = {
    "/weather": "Get current weather for a city (example plugin).",
    "/plugin_info": "Show loaded plugin info.",
}

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _weather_handler(args):
    """Example weather command — returns mock data."""
    if not args:
        return "Usage: /weather <city>"
    city = " ".join(args)
    # Replace this with a real API call (e.g. OpenWeatherMap).
    now = datetime.now().strftime("%H:%M")
    return (
        f"**Weather for {city}**\n"
        f"- Temperature: 22°C / 72°F\n"
        f"- Conditions: Partly cloudy\n"
        f"- Updated: {now}\n"
        f"_This is example data — replace with a real API call._"
    )


def _plugin_info_handler(args):
    """Show basic plugin metadata."""
    return (
        f"**{PLUGIN_NAME}** v{PLUGIN_VERSION}\n"
        f"Commands: {', '.join(PLUGIN_HELP.keys())}"
    )


# Register command handlers
PLUGIN_COMMANDS["/weather"] = _weather_handler
PLUGIN_COMMANDS["/plugin_info"] = _plugin_info_handler

# ---------------------------------------------------------------------------
# Alternative: register() function (called by the built-in loader)
#
# def register(bot) -> Dict[str, Any]:
#     \"\"\"Return a dict of command_name → handler.\"\"\"
#     return {
#         "/weather": _weather_handler,
#         "/plugin_info": _plugin_info_handler,
#     }
# ---------------------------------------------------------------------------
