"""
Tests for veni/tool_executor.py
"""

import pytest
from unittest.mock import MagicMock

from veni.tool_executor import (
    parse_tool_args,
    extract_call_tool_request,
    extract_json_tool_request,
    check_and_execute_tools,
    execute_tool_with_dict,
)


# ---------------------------------------------------------------------------
# parse_tool_args
# ---------------------------------------------------------------------------

def test_parse_tool_args_empty():
    assert parse_tool_args("") == {}


def test_parse_tool_args_single_kwarg():
    assert parse_tool_args('path="foo.py"') == {"path": "foo.py"}


def test_parse_tool_args_multiple_kwargs():
    result = parse_tool_args('path="a.py", content="hello"')
    assert result == {"path": "a.py", "content": "hello"}


def test_parse_tool_args_rejects_positional():
    with pytest.raises(ValueError, match="Positional"):
        parse_tool_args('"positional"')


def test_parse_tool_args_invalid_syntax():
    with pytest.raises(ValueError):
        parse_tool_args("path=")


# ---------------------------------------------------------------------------
# extract_call_tool_request
# ---------------------------------------------------------------------------

def test_extract_call_tool_request_basic():
    response = 'CALL: read_file(path="main.py")'
    result = extract_call_tool_request(response)
    assert result is not None
    name, args = result
    assert name == "read_file"
    assert args == {"path": "main.py"}


def test_extract_call_tool_request_no_match():
    assert extract_call_tool_request("just a normal response") is None


def test_extract_call_tool_request_no_args():
    result = extract_call_tool_request("CALL: list_tools()")
    assert result is not None
    assert result[0] == "list_tools"
    assert result[1] == {}


# ---------------------------------------------------------------------------
# extract_json_tool_request
# ---------------------------------------------------------------------------

def test_extract_json_tool_request_basic():
    response = '{"name": "web_search", "arguments": {"query": "python"}}'
    result = extract_json_tool_request(response)
    assert result is not None
    name, args = result
    assert name == "web_search"
    assert args == {"query": "python"}


def test_extract_json_tool_request_embedded_in_text():
    response = 'Let me search: {"name": "web_search", "arguments": {"query": "test"}} done.'
    result = extract_json_tool_request(response)
    assert result is not None
    assert result[0] == "web_search"


def test_extract_json_tool_request_no_match():
    assert extract_json_tool_request("no json here") is None


def test_extract_json_tool_request_wrong_shape():
    assert extract_json_tool_request('{"foo": "bar"}') is None


# ---------------------------------------------------------------------------
# check_and_execute_tools / execute_tool_with_dict
# ---------------------------------------------------------------------------

def _make_bot(tool_result="ok"):
    """Build a minimal mock bot."""
    bot = MagicMock()
    bot.approval_gate.check.return_value = True
    tool = MagicMock()
    tool.execute.return_value = tool_result
    bot.tool_registry.get.return_value = tool
    return bot


def test_execute_tool_with_dict_success():
    bot = _make_bot("file contents")
    result = execute_tool_with_dict(bot, "read_file", {"path": "x.py"})
    assert result == "file contents"
    bot.tool_registry.get.assert_called_once_with("read_file")


def test_execute_tool_with_dict_blocked_by_gate():
    bot = _make_bot()
    bot.approval_gate.check.return_value = False
    result = execute_tool_with_dict(bot, "shell_exec", {"command": "rm -rf /"})
    assert "blocked" in result.lower()
    bot.tool_registry.get.return_value.execute.assert_not_called()


def test_execute_tool_with_dict_unknown_tool():
    bot = _make_bot()
    bot.tool_registry.get.return_value = None
    result = execute_tool_with_dict(bot, "nonexistent", {})
    assert result is None


def test_execute_tool_with_dict_exception():
    bot = _make_bot()
    bot.tool_registry.get.return_value.execute.side_effect = RuntimeError("boom")
    result = execute_tool_with_dict(bot, "read_file", {"path": "x.py"})
    assert "Error" in result


def test_check_and_execute_tools_call_syntax():
    bot = _make_bot("search result")
    response = 'CALL: web_search(query="veni ai")'
    result = check_and_execute_tools(bot, response)
    assert result == "search result"


def test_check_and_execute_tools_json_syntax():
    bot = _make_bot("json result")
    response = '{"name": "web_search", "arguments": {"query": "test"}}'
    result = check_and_execute_tools(bot, response)
    assert result == "json result"


def test_check_and_execute_tools_no_call():
    bot = _make_bot()
    result = check_and_execute_tools(bot, "just a plain response")
    assert result is None
