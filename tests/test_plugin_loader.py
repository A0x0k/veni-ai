"""
Tests for veni/plugin_loader.py
"""

from unittest.mock import MagicMock

from veni.plugin_loader import _load_single_plugin, load_plugins


def _make_bot():
    bot = MagicMock()
    bot.show_warning = MagicMock()
    return bot


# ---------------------------------------------------------------------------
# load_plugins — no plugins dir
# ---------------------------------------------------------------------------


def test_load_plugins_no_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    bot = _make_bot()
    cmds, help_map = load_plugins(bot)
    assert cmds == {}
    assert help_map == {}


def test_load_plugins_disabled_by_default(monkeypatch, tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    plugin_file = plugins_dir / "greet.py"
    plugin_file.write_text('PLUGIN_COMMANDS = {"/greet": lambda args: "hello"}\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VENI_ENABLE_PROJECT_PLUGINS", raising=False)

    bot = _make_bot()
    cmds, help_map = load_plugins(bot)

    assert cmds == {}
    assert help_map == {}
    bot.show_warning.assert_called_once()


# ---------------------------------------------------------------------------
# load_plugins — PLUGIN_COMMANDS style
# ---------------------------------------------------------------------------


def test_load_plugins_plugin_commands(monkeypatch, tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    plugin_file = plugins_dir / "greet.py"
    plugin_file.write_text(
        'PLUGIN_COMMANDS = {"/greet": lambda args: "hello"}\n'
        'PLUGIN_HELP = {"/greet": "Say hello"}\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VENI_ENABLE_PROJECT_PLUGINS", "1")

    bot = _make_bot()
    cmds, help_map = load_plugins(bot)

    assert "/greet" in cmds
    assert cmds["/greet"](["world"]) == "hello"
    assert help_map["/greet"] == "Say hello"


# ---------------------------------------------------------------------------
# load_plugins — register() style
# ---------------------------------------------------------------------------


def test_load_plugins_register_style(monkeypatch, tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    plugin_file = plugins_dir / "reg_plugin.py"
    plugin_file.write_text(
        "def register(bot):\n" '    return {"/ping": lambda args: "pong"}\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VENI_ENABLE_PROJECT_PLUGINS", "1")

    bot = _make_bot()
    cmds, _ = load_plugins(bot)

    assert "/ping" in cmds
    assert cmds["/ping"]([]) == "pong"


# ---------------------------------------------------------------------------
# load_plugins — command name normalisation (no leading slash)
# ---------------------------------------------------------------------------


def test_load_plugins_normalises_slash(monkeypatch, tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    plugin_file = plugins_dir / "noslash.py"
    plugin_file.write_text('PLUGIN_COMMANDS = {"hello": lambda args: "hi"}\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VENI_ENABLE_PROJECT_PLUGINS", "1")

    bot = _make_bot()
    cmds, _ = load_plugins(bot)

    assert "/hello" in cmds
    assert "hello" not in cmds


# ---------------------------------------------------------------------------
# _load_single_plugin — broken plugin doesn't crash loader
# ---------------------------------------------------------------------------


def test_load_single_plugin_syntax_error(tmp_path):
    bad_plugin = tmp_path / "bad.py"
    bad_plugin.write_text("def register(bot):\n    return {{{")

    bot = _make_bot()
    cmds, help_map = _load_single_plugin(bot, bad_plugin)

    assert cmds == {}
    assert help_map == {}
    bot.show_warning.assert_called_once()


# ---------------------------------------------------------------------------
# _load_single_plugin — missing spec (non-.py path edge case)
# ---------------------------------------------------------------------------


def test_load_single_plugin_empty_file(tmp_path):
    empty = tmp_path / "empty.py"
    empty.write_text("")

    bot = _make_bot()
    cmds, help_map = _load_single_plugin(bot, empty)
    assert cmds == {}
    assert help_map == {}
