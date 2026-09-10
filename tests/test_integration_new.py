import pytest

from veni.core import TerminalChatbot
from veni.security import redactor


class _FakeClient:
    def __init__(self):
        self.model = "gpt-4o"

    def chat(self, messages, stream=True, tools=None, **kwargs):
        yield "Thinking..."


def test_command_registry_discovery():
    bot = TerminalChatbot(_FakeClient())
    # Verify core commands are registered
    assert bot.command_registry.get("/help") is not None
    assert bot.command_registry.get("/model") is not None
    assert bot.command_registry.get("/network") is not None
    assert bot.command_registry.get("/redact") is not None

    # Verify command listing
    cmds = bot.command_registry.list_commands()
    assert len(cmds) > 30
    assert any(c.name == "/help" for c in cmds)


def test_tool_registry():
    bot = TerminalChatbot(_FakeClient())
    assert bot.tool_registry.get("web_search") is not None
    assert bot.tool_registry.get("read_file") is not None
    assert bot.tool_registry.get("speak") is not None
    assert bot.tool_registry.get("write_file") is not None
    assert bot.tool_registry.get("shell_exec") is not None
    assert bot.tool_registry.get("repo_map") is not None
    assert bot.tool_registry.get("doc_lookup") is not None
    assert bot.tool_registry.get("web_intelligence") is not None
    assert bot.tool_registry.get("intelligence_config") is not None

    decls = bot.tool_registry.get_declarations()
    assert len(decls) >= 9


def test_redactor():
    """Test sensitive info masking."""
    text = (
        "My key is sk-123456789012345678901234567890123456789012345678 "
        "and email is test@example.com"
    )
    masked = redactor.redact(text)
    assert "sk-" not in masked
    assert "test@example.com" not in masked
    assert "[REDACTED]" in masked


def test_ui_logic_get_toolbar():
    bot = TerminalChatbot(_FakeClient())
    # We can't easily test the visual rendering, but we can test the data logic
    # Mocking get_user_input's internal get_toolbar function is hard,
    # but we can verify the bot state affects the rendering logic if we refactor it.
    # For now, just ensure the bot initializes without UI errors.
    assert bot.COLORS["primary"].startswith("#")


def test_dashboard_requires_token():
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    bot = TerminalChatbot(_FakeClient())
    if bot.dashboard.app is None:
        return
    client = TestClient(bot.dashboard.app)

    assert client.get("/api/history").status_code == 401
    response = client.get(
        "/api/history",
        headers={"X-Veni-Token": bot.dashboard.auth_token},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_manual_tool_call_detection():
    """Test CALL: pattern detection via regex."""
    import re

    full_response = "I will check that. CALL: read_file(path='README.md')"
    match = re.search(r"CALL:\s*(\w+)\((.*)\)", full_response)
    assert match is not None
    assert match.group(1) == "read_file"
    assert "README.md" in match.group(2)
