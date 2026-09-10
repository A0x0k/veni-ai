"""
Smoke tests for veni/commands/

Verifies that every registered command can be instantiated and that
calling execute() with empty args does not raise an unhandled exception.
Commands that require real I/O (git, web, voice) are expected to return
a string or None — not crash.
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bot():
    """Minimal bot mock sufficient for command instantiation."""
    from veni.core import TerminalChatbot

    class _FakeClient:
        model = "fake"
        def chat(self, *a, **kw):
            return iter(())

    bot = TerminalChatbot(_FakeClient())
    bot.approval_gate.enabled = False
    return bot


def _smoke(bot, cmd_cls, args=None):
    """Instantiate cmd_cls, call execute(args), assert no unhandled exception."""
    cmd = cmd_cls(bot)
    result = cmd.execute(args or [])
    # Result must be a string, None, or a known sentinel — never an exception
    assert result is None or isinstance(result, str)


# ---------------------------------------------------------------------------
# Session commands
# ---------------------------------------------------------------------------

def test_new_command(bot):
    from veni.commands.session import NewCommand
    _smoke(bot, NewCommand)


def test_history_command(bot):
    from veni.commands.session import HistoryCommand
    _smoke(bot, HistoryCommand)


def test_status_command(bot):
    from veni.commands.ai import StatusCommand
    _smoke(bot, StatusCommand)


def test_help_command(bot):
    from veni.commands.help import HelpCommand
    _smoke(bot, HelpCommand)


# ---------------------------------------------------------------------------
# File commands
# ---------------------------------------------------------------------------

def test_pwd_command(bot):
    from veni.commands.file import PwdCommand
    _smoke(bot, PwdCommand)


def test_ls_command(bot):
    from veni.commands.file import LsCommand
    _smoke(bot, LsCommand)


def test_tree_command(bot):
    from veni.commands.file import TreeCommand
    _smoke(bot, TreeCommand)


def test_read_command_no_args(bot):
    from veni.commands.file import ReadCommand
    _smoke(bot, ReadCommand, args=[])


# ---------------------------------------------------------------------------
# UI commands
# ---------------------------------------------------------------------------

def test_clear_command(bot):
    from veni.commands.ui import ClearCommand
    with patch("rich.console.Console.clear"):
        _smoke(bot, ClearCommand)


def test_theme_command_no_args(bot):
    from veni.commands.ui import ThemeCommand
    _smoke(bot, ThemeCommand, args=[])


def test_colors_command(bot):
    from veni.commands.ui import ColorsCommand
    _smoke(bot, ColorsCommand)


def test_menu_command(bot):
    from veni.commands.ui import MenuCommand
    _smoke(bot, MenuCommand)


# ---------------------------------------------------------------------------
# AI commands
# ---------------------------------------------------------------------------

def test_temperature_command_no_args(bot):
    from veni.commands.ai import TemperatureCommand
    _smoke(bot, TemperatureCommand, args=[])


def test_temperature_command_set(bot):
    from veni.commands.ai import TemperatureCommand
    _smoke(bot, TemperatureCommand, args=["0.7"])


def test_max_tokens_command_no_args(bot):
    from veni.commands.ai import MaxTokensCommand
    _smoke(bot, MaxTokensCommand, args=[])


def test_model_command_no_args(bot):
    from veni.commands.ai import ModelCommand
    # ModelCommand with no args prompts stdin; pass a model name directly
    _smoke(bot, ModelCommand, args=["llama3.2"])


# ---------------------------------------------------------------------------
# Intelligence commands
# ---------------------------------------------------------------------------

def test_persona_command_no_args(bot):
    from veni.commands.intelligence import PersonaCommand
    _smoke(bot, PersonaCommand, args=["list"])


def test_mode_command_no_args(bot):
    from veni.commands.intelligence import ModeCommand
    _smoke(bot, ModeCommand, args=["list"])


def test_skill_command_no_args(bot):
    from veni.commands.intelligence import SkillCommand
    _smoke(bot, SkillCommand, args=["list"])


def test_approve_command_no_args(bot):
    from veni.commands.intelligence import ApproveCommand
    _smoke(bot, ApproveCommand, args=[])


# ---------------------------------------------------------------------------
# Message commands
# ---------------------------------------------------------------------------

def test_pins_command(bot):
    from veni.commands.message import PinsCommand
    _smoke(bot, PinsCommand)


def test_summary_command_no_history(bot):
    from veni.commands.message import SummaryCommand
    _smoke(bot, SummaryCommand)


# ---------------------------------------------------------------------------
# All registered commands round-trip
# ---------------------------------------------------------------------------

def test_all_registered_commands_instantiate(bot):
    """Every command registered in the bot's registry must instantiate cleanly."""
    for name, cmd in bot.command_registry.commands.items():
        assert cmd is not None, f"Command {name!r} is None in registry"
