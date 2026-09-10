"""
Chat engine for Veni AI.

Handles streaming AI responses, tool call loops, and system prompt assembly.
"""

import concurrent.futures
import re
import time
from typing import TYPE_CHECKING, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from veni.tool_executor import check_and_execute_tools
import veni.ui as _ui

if TYPE_CHECKING:
    from veni.core import TerminalChatbot

console = Console(soft_wrap=True)

# Language map for syntax highlighting during stream
_CODE_LANG_MAP = {
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "bash": "bash", "sh": "bash", "shell": "bash", "zsh": "bash",
    "json": "json",
    "yaml": "yaml", "yml": "yaml",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "rust": "rust", "rs": "rust",
    "go": "go", "golang": "go",
    "java": "java",
    "c": "c",
    "cpp": "cpp", "c++": "cpp",
    "ruby": "ruby", "rb": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "diff": "diff",
    "markdown": "markdown", "md": "markdown",
}


def _render_streaming_content(text: str):
    """Render text with basic syntax highlighting during streaming."""
    # Check if we're inside a code block
    code_block_match = re.search(r"```(\w*)\n(.*?)(?:```|$)", text, re.DOTALL)
    if code_block_match:
        lang = code_block_match.group(1)
        code = code_block_match.group(2)
        if lang and code.strip():
            lexer = _CODE_LANG_MAP.get(lang.lower(), "text")
            try:
                return Syntax(code, lexer, theme="monokai", line_numbers=False, word_wrap=True)
            except Exception:
                pass
    return Markdown(text)

_TOOL_TIMEOUT = 30          # seconds before a tool call is considered hung
_STREAM_MAX_RETRIES = 2     # retry attempts on transient provider errors
_STREAM_RETRY_BACKOFF = 1.5 # seconds; doubles each attempt

# Error substrings that indicate a transient (retryable) failure
_TRANSIENT_KEYWORDS = ("rate limit", "429", "503", "connection", "timeout", "overloaded")


def stream_response(
    bot: "TerminalChatbot",
    messages: List[Dict],
    max_tool_calls: int = 10,
) -> str:
    """
    Stream AI response with tool call support and transient-error retry.

    Retries up to _STREAM_MAX_RETRIES times when the provider returns a
    transient error (rate-limit, connection reset, 503). Each retry waits
    with exponential backoff.
    """
    for attempt in range(_STREAM_MAX_RETRIES + 1):
        result = _stream_once(bot, messages, max_tool_calls)
        if result is not None:
            return result
        if attempt < _STREAM_MAX_RETRIES:
            delay = _STREAM_RETRY_BACKOFF * (2 ** attempt)
            bot.show_warning(
                f"Provider error — retrying in {delay:.0f}s "
                f"(attempt {attempt + 1}/{_STREAM_MAX_RETRIES})…"
            )
            time.sleep(delay)
    bot.show_error("Provider failed after all retries. Please try again.")
    return ""


def _stream_once(
    bot: "TerminalChatbot",
    messages: List[Dict],
    max_tool_calls: int,
) -> str | None:
    """
    Single streaming attempt.

    Streams tokens directly into the final response panel so the user sees
    text accumulate in place — no spinner-then-swap.

    Returns the response string on success, or None to signal a transient
    error that should be retried by stream_response().
    """
    full_response = ""
    loading_steps = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    frame_count = 0

    # Spinner lives in the title, not mixed with content
    live_panel = Panel(
        Text("…", style="dim"),
        title=" VENI ",
        title_align="left",
        border_style=bot.COLORS["assistant"],
        box=box.SIMPLE,
        padding=(0, 2),
    )

    with Live(live_panel, auto_refresh=False, vertical_overflow="visible") as live:
        try:
            params = bot._get_generation_params()
            for chunk in bot.ai_client.chat(
                messages,
                stream=True,
                tools=bot.tool_registry.get_declarations(),
                **params,
            ):
                if chunk.startswith("Error:"):
                    bot.last_error = chunk
                    live_panel.border_style = "red"
                    live_panel.renderable = Text(chunk)
                    live.update(live_panel)
                    live.refresh()
                    if any(kw in chunk.lower() for kw in _TRANSIENT_KEYWORDS):
                        return None
                    return ""
                full_response += chunk
                spinner = loading_steps[frame_count % len(loading_steps)]
                # Put spinner in title; body stays clean
                live_panel.title = f" VENI  {spinner} "
                live_panel.renderable = _render_streaming_content(full_response)
                live.update(live_panel)
                frame_count += 1
                live.refresh()

            # Streaming done — render final markdown in place
            live_panel.title = " VENI "
            live_panel.renderable = Markdown(full_response)
            live.update(live_panel)
            live.refresh()

        except KeyboardInterrupt:
            live_panel.renderable = Markdown(full_response) if full_response else Text("[Interrupted]", style="dim")
            live_panel.title = " VENI "
            live.update(live_panel)
            live.refresh()
            return full_response
        except Exception as exc:
            live_panel.border_style = "red"
            live_panel.renderable = Text(f"⚠ {exc}")
            live_panel.title = " ERROR "
            live.update(live_panel)
            live.refresh()
            return None

    console.print()  # breathing room after the panel

    # Tool call loop with timeout and recursion cap
    if max_tool_calls > 0:
        bot.show_status("Running tool calls...")
        tool_result = _execute_tools_with_timeout(bot, full_response)
        if tool_result is not None:
            bot.history.add_message("assistant", full_response)
            bot.history.add_tool_message(f"[Tool Result]\n{tool_result}")
            return stream_response(
                bot,
                bot.history.get_context_messages(bot.context_tokens, model=bot.model_name),
                max_tool_calls=max_tool_calls - 1,
            )
    elif _has_tool_call(full_response):
        bot.show_warning("Tool call limit reached. Returning response as-is.")

    bot.last_response = full_response
    return full_response


def _has_tool_call(response: str) -> bool:
    """Quick check whether a response contains any tool call syntax."""
    return bool(re.search(r"CALL:\s*\w+\s*\(", response)) or (
        "{" in response and '"name"' in response and '"arguments"' in response
    )


def _execute_tools_with_timeout(bot: "TerminalChatbot", response: str) -> Optional[str]:
    """Run tool detection + execution with a hard timeout."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(check_and_execute_tools, bot, response)
        try:
            return future.result(timeout=_TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            bot.show_error(f"Tool call timed out after {_TOOL_TIMEOUT}s. Skipping.")
            return f"Error: tool execution timed out after {_TOOL_TIMEOUT} seconds."


def update_system_prompt(
    bot: "TerminalChatbot", current_query: Optional[str] = None
) -> None:
    """Build and apply the unified system prompt from all active sources."""
    parts = [bot.history.system_prompt]

    persona_prompt = bot.persona_engine.get_system_prompt_addition()
    if persona_prompt:
        parts.append(f"\n## Current Persona\n{persona_prompt}")

    mode_prompt = bot.mode_engine.get_system_prompt_addition()
    if mode_prompt:
        parts.append(f"\n## Current Mode\n{mode_prompt}")

    skills_prompt = bot.skill_manager.get_system_prompt()
    if skills_prompt:
        parts.append(f"\n## Active Skills\n{skills_prompt}")

    memory_prompt = bot.memory_system.get_context_prompt(current_query)
    if memory_prompt:
        parts.append(f"\n## User Memory\n{memory_prompt}")

    ctx = getattr(bot, "_current_context", None)
    if ctx and ctx.prompt_addition:
        parts.append(
            f"\n## Project Context\n"
            f"Type: {ctx.project_type} ({ctx.language})\n"
            f"{ctx.prompt_addition}"
        )

    bot.history.system_prompt = "\n\n".join(parts)
