"""
Tool execution logic for Veni AI.

Handles parsing and dispatching tool calls from AI responses.
"""

import ast
import json
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from veni.core import TerminalChatbot


def extract_call_tool_request(response: str) -> tuple[str, dict[str, Any]] | None:
    """Parse CALL: tool_name(kwargs) syntax from AI response."""
    match = re.search(r"CALL:\s*(\w+)\s*\(", response, flags=re.DOTALL)
    if not match:
        return None

    tool_name = match.group(1)
    args_start = match.end() - 1
    depth = 0
    in_string = False
    string_quote = ""
    escaped = False

    for idx in range(args_start, len(response)):
        char = response[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == string_quote:
                in_string = False
            continue
        if char in {"'", '"'}:
            in_string = True
            string_quote = char
            continue
        if char == "(":
            depth += 1
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                args_str = response[args_start + 1 : idx]
                return tool_name, parse_tool_args(args_str)

    return None


def extract_json_tool_request(response: str) -> tuple[str, dict[str, Any]] | None:
    """Parse JSON {name, arguments} tool call from AI response."""
    decoder = json.JSONDecoder()
    raw = response.strip()
    candidates = [raw, _extract_raw_content(raw)]

    for candidate in candidates:
        for idx, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(candidate[idx:])
            except json.JSONDecodeError:
                continue
            if (
                isinstance(payload, dict)
                and isinstance(payload.get("name"), str)
                and isinstance(payload.get("arguments"), dict)
            ):
                return payload["name"], payload["arguments"]
    return None


def parse_tool_args(args_str: str) -> dict[str, Any]:
    """Parse keyword arguments string into a dict."""
    if not args_str.strip():
        return {}
    try:
        expr = ast.parse(f"_tool({args_str})", mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid tool arguments: {exc.msg}") from exc

    call = expr.body
    if not isinstance(call, ast.Call):
        raise ValueError("Invalid tool call syntax")
    if call.args:
        raise ValueError("Positional tool arguments are not supported")

    return {
        kw.arg: ast.literal_eval(kw.value)
        for kw in call.keywords
        if kw.arg is not None
    }


def _extract_raw_content(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 3:
            raw = "```".join(parts[1:-1])
    lines = raw.lstrip().splitlines()
    if (
        lines
        and len(lines[0]) <= 20
        and all(c.isalnum() or c in "-+_." for c in lines[0].strip())
    ):
        raw = "\n".join(lines[1:]).lstrip("\n")
    return raw.rstrip()


def check_and_execute_tools(bot: "TerminalChatbot", response: str) -> str | None:
    """
    Check for tool calls in response and execute them.
    Returns tool result string if a tool was called, None otherwise.
    """
    call = extract_call_tool_request(response)
    if call is not None:
        return execute_tool_with_dict(bot, *call)

    call = extract_json_tool_request(response)
    if call is not None:
        return execute_tool_with_dict(bot, *call)

    return None


def execute_tool_with_dict(
    bot: "TerminalChatbot", tool_name: str, args: dict
) -> str | None:
    """Execute a tool by name with a dict of arguments."""
    tool = bot.tool_registry.get(tool_name)
    if not tool:
        return None

    if not bot.approval_gate.check(tool_name, args):
        return (
            f"Execution of '{tool_name}' was blocked by the "
            f"approval gate. User declined to proceed."
        )

    bot.show_warning(f"🔧 Using tool: {tool_name}...")
    try:
        return str(tool.execute(**args))
    except Exception as e:
        bot.show_error(f"Tool failed: {e}")
        return f"Error executing {tool_name}: {e}"


def execute_tool(bot: "TerminalChatbot", tool_name: str, args_str: str) -> str | None:
    """Execute a tool from a raw argument string."""
    tool = bot.tool_registry.get(tool_name)
    if not tool:
        return None
    try:
        args = parse_tool_args(args_str)
    except ValueError as exc:
        bot.show_error(f"Tool failed: {exc}")
        return f"Error executing {tool_name}: {exc}"
    return execute_tool_with_dict(bot, tool_name, args)
