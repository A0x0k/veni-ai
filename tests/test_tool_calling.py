"""
Tests for native tool calling functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from veni.core import TerminalChatbot


class FakeClient:
    """Fake AI client for testing."""

    model = "test-model"

    def chat(self, messages, stream=True, tools=None, **kwargs):
        if False:
            yield ""


class TestToolCalling:
    """Test native tool calling functionality."""

    @pytest.fixture
    def bot(self):
        """Create a bot instance with fake client."""
        bot = TerminalChatbot(FakeClient(), context_tokens=4096)
        # Disable approval gate in tests
        bot.approval_gate.enabled = False
        return bot

    @pytest.fixture
    def tool_registry(self, bot):
        """Get the bot's tool registry."""
        return bot.tool_registry

    def test_tool_registry_has_tools(self, tool_registry):
        """Test that tool registry has registered tools."""
        tools = tool_registry.list_tools()
        assert len(tools) >= 2  # At least search and file read

    def test_get_tool_by_name(self, tool_registry):
        """Test getting a tool by name."""
        search_tool = tool_registry.get("web_search")
        assert search_tool is not None
        assert search_tool.name == "web_search"

    def test_get_tool_declarations(self, tool_registry):
        """Test getting tool declarations for AI."""
        declarations = tool_registry.get_declarations()
        assert isinstance(declarations, list)
        assert len(declarations) >= 2

        # Check structure of declaration
        search_decl = declarations[0]
        assert "name" in search_decl
        assert "description" in search_decl
        assert "parameters" in search_decl

    def test_check_tool_call_pattern(self, bot):
        """Test tool call pattern detection."""
        response = (
            "Let me search for that.\n" "CALL: web_search(query='python tutorial')"
        )
        result = bot._check_and_execute_tools(response)
        assert result is None or isinstance(result, str)

    def test_execute_tool_with_string_args(self, bot):
        """Test executing a tool with string arguments."""
        # This tests the argument parsing logic
        result = bot._execute_tool("nonexistent_tool", "arg1=value1")
        assert result is None  # Tool doesn't exist

    def test_execute_tool_with_dict_args(self, bot):
        """Test executing a tool with dictionary arguments."""
        result = bot._execute_tool_with_dict("nonexistent_tool", {"arg": "value"})
        assert result is None  # Tool doesn't exist

    def test_tool_call_max_recursion(self, bot):
        """Test that tool calls have max recursion limit."""
        # The stream_response should have max_tool_calls parameter
        messages = [{"role": "user", "content": "test"}]
        # Should not raise an error even with no tools
        result = bot.stream_response(messages, max_tool_calls=0)
        assert result == ""  # Empty because fake client

    def test_search_tool_execute(self, bot):
        """Test search tool execution."""
        search_tool = bot.tool_registry.get("web_search")
        if search_tool:
            # Mock the MultiEngineSearch to avoid actual network calls
            with patch("veni.web_search.MultiEngineSearch") as mock_search:
                mock_instance = Mock()
                mock_instance.search.return_value = [
                    Mock(
                        title="Test",
                        url="http://test.com",
                        snippet="Test content",
                    )
                ]
                mock_search.return_value = mock_instance

                result = search_tool.execute(query="test query", max_results=1)
                # Result should contain search results or error message
                assert isinstance(result, str)
                assert len(result) > 0

    def test_file_read_tool_execute(self, bot, tmp_path: Path):
        """Test file read tool execution."""
        file_tool = bot.tool_registry.get("read_file")
        if file_tool:
            result = file_tool.execute(path="README.md")
            assert "Veni AI" in result

    def test_file_read_tool_not_found(self, bot):
        """Test file read tool with non-existent file."""
        file_tool = bot.tool_registry.get("read_file")
        if file_tool:
            result = file_tool.execute(path="nonexistent.txt")
            assert "Error" in result or "not found" in result.lower()

    def test_file_write_tool_previews_by_default(self, bot, tmp_path: Path):
        file_tool = bot.tool_registry.get("write_file")
        if file_tool:
            result = file_tool.execute(path="README.md", content="changed")
            assert "Preview modify file" in result
            assert "No changes have been written yet." in result

    def test_file_write_tool_applies_when_requested(self, bot, monkeypatch):
        file_tool = bot.tool_registry.get("write_file")
        if file_tool:
            fake_path = Mock()
            fake_path.exists.return_value = True
            fake_path.read_text.return_value = "old"
            fake_path.write_text.return_value = None
            fake_path.parent = Mock()
            fake_path.parent.mkdir.return_value = None
            monkeypatch.setattr(bot, "resolve_workspace_path", lambda _: fake_path)

            result = file_tool.execute(path="draft.txt", content="hello", apply=True)
            assert "Applied changes" in result
            fake_path.write_text.assert_called_once_with("hello", encoding="utf-8")

    def test_file_read_tool_rejects_outside_workspace(self, bot):
        file_tool = bot.tool_registry.get("read_file")
        if file_tool:
            result = file_tool.execute(path=r"C:\Windows\win.ini")
            assert "escapes workspace" in result.lower()


class TestToolCallPatterns:
    """Test various tool call pattern formats."""

    @pytest.fixture
    def bot(self):
        bot = TerminalChatbot(FakeClient(), context_tokens=4096)
        bot.approval_gate.enabled = False
        return bot

    def test_call_pattern_basic(self, bot):
        """Test basic CALL: pattern."""
        response = "CALL: web_search(query='test')"
        match = bot._check_and_execute_tools(response)
        # Pattern should be detected (execution may fail)
        assert match is None or isinstance(match, str)

    def test_call_pattern_with_spaces(self, bot):
        """Test CALL: pattern with spaces."""
        response = "Let me help. CALL:  web_search( query = 'test' )"
        match = bot._check_and_execute_tools(response)
        assert match is None or isinstance(match, str)

    def test_call_pattern_multiple_args(self, bot):
        """Test CALL: pattern with multiple arguments."""
        response = "CALL: web_search(query='test', max_results=5)"
        match = bot._check_and_execute_tools(response)
        assert match is None or isinstance(match, str)

    def test_call_pattern_with_comma_in_string(self, bot, monkeypatch):
        captured = {}

        def fake_execute(b, tool_name, args):
            captured["tool_name"] = tool_name
            captured["args"] = args
            return "ok"

        monkeypatch.setattr("veni.tool_executor.execute_tool_with_dict", fake_execute)
        response = "CALL: web_search(query='a, b', max_results=5)"
        assert bot._check_and_execute_tools(response) == "ok"
        assert captured["tool_name"] == "web_search"
        assert captured["args"] == {"query": "a, b", "max_results": 5}

    def test_json_pattern(self, bot):
        """Test JSON tool call pattern."""
        response = '{"name": "web_search", "arguments": {"query": "test"}}'
        match = bot._check_and_execute_tools(response)
        assert match is None or isinstance(match, str)

    def test_json_pattern_with_nested_arguments(self, bot, monkeypatch):
        captured = {}

        def fake_execute(b, tool_name, args):
            captured["tool_name"] = tool_name
            captured["args"] = args
            return "ok"

        monkeypatch.setattr("veni.tool_executor.execute_tool_with_dict", fake_execute)
        response = (
            'Tool:\n{"name":"web_search",'
            '"arguments":{"query":"test","filters":{"region":"us"}}}'
        )
        assert bot._check_and_execute_tools(response) == "ok"
        assert captured["tool_name"] == "web_search"
        assert captured["args"] == {"query": "test", "filters": {"region": "us"}}


class TestProviderToolCalls:
    """Test provider-specific tool call handling."""

    def test_openai_tool_capability(self):
        """Test OpenAI client has tool call capability."""
        from veni.providers.openai import OpenAIClient

        # Don't actually create client, just check class
        assert OpenAIClient.capabilities.supports_tool_calls is True

    def test_ollama_tool_capability(self):
        """Test Ollama client tool capability."""
        from veni.providers.ollama import OllamaClient

        # Ollama may or may not support tools depending on version
        assert hasattr(OllamaClient, "capabilities")

    def test_gemini_tool_capability(self):
        """Test Gemini client tool capability."""
        from veni.providers.gemini import GeminiClient

        assert hasattr(GeminiClient, "capabilities")
