from veni.core import TerminalChatbot
from veni.providers.factory import get_provider_name


class _FakeClient:
    def __init__(self):
        self.model = "fake"

    def chat(self, messages, stream=True):
        if False:
            yield ""
        return iter(())


def _make_bot():
    return TerminalChatbot(_FakeClient())


def test_extract_raw_content_from_fenced_block():
    from veni.tool_executor import _extract_raw_content
    text = "```python\nprint('hi')\n```"
    assert _extract_raw_content(text) == "print('hi')"


def test_extract_raw_content_from_plain_text():
    from veni.tool_executor import _extract_raw_content
    text = "  hello world  "
    assert _extract_raw_content(text) == "hello world"


def test_voice_lazy_init_failure(monkeypatch):
    bot = _make_bot()
    assert bot.voice_engine is None
    assert bot.voice_mode is False

    def _boom():
        raise RuntimeError("no mic")

    monkeypatch.setattr("veni.voice.VoiceEngine", _boom)
    bot.handle_command("/voice")
    assert bot.voice_engine is None
    assert bot.voice_mode is False


def test_unknown_provider_name_for_fake_client():
    assert get_provider_name(_FakeClient()) == "unknown"


def test_optional_integrations_start_disabled_by_default():
    bot = _make_bot()
    # Gateways are initialized but should stay opt-in.
    assert bot.telegram_gateway is not None
    assert bot.dashboard is not None
    assert bot.scheduler is not None
    assert not bot.scheduler.scheduler.running
    assert bot.memory_system.semantic_enabled is False
    assert "/evolve" not in bot.command_registry.commands
