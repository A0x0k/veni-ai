"""
Session loop and intelligence helpers for Veni AI.

Contains the main run() loop and per-turn helpers extracted from core.py.
"""

from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from veni.core import TerminalChatbot

console = Console()


def run(bot: "TerminalChatbot") -> None:
    """Main interactive session loop."""
    from veni.scheduler import setup_default_tasks

    bot.show_onboarding()
    bot.print_header()
    bot._maybe_resume_last_session()
    bot._init_codebase_indexer()
    _auto_detect_context(bot)

    if bot.config.get("features.proactive_scheduler", False):
        setup_default_tasks(bot.scheduler, bot)
        bot.scheduler.start()

    if bot.config.get("features.telegram_gateway", False):
        bot.telegram_gateway.start()

    if bot.config.get("features.dashboard", False):
        bot.dashboard.start()

    while bot.running:
        try:
            user_input = bot.get_user_input()
            if not user_input.strip() and not bot.current_images:
                continue
            if user_input.startswith("/"):
                res = bot.handle_command(user_input)
                if res == "EXIT":
                    break
                if res != "TRIGGER_CHAT":
                    continue
            else:
                bot.last_failed_input = user_input
                bot.format_user_message(user_input, bot.current_images)
                bot.history.add_message("user", user_input, images=bot.current_images)
                _suggest_intelligence(bot, user_input)
            bot.current_images = []
            bot._update_system_prompt(
                user_input if not user_input.startswith("/") else None
            )
            response = bot.stream_response(
                bot.history.get_context_messages(
                    bot.context_tokens, model=bot.model_name
                )
            )
            if response:
                bot.last_error = None
                bot.history.add_message("assistant", response)
                _record_memory(bot, user_input, response)
                _check_response_errors(bot, response)
                if bot.voice_mode and bot.voice_engine:
                    bot.voice_engine.speak(response)
        except KeyboardInterrupt:
            break

    bot._autosave_session()
    console.print(
        f"\n[bold {bot.COLORS['primary']}]Veni out. See ya! 👋"
        f"[/bold {bot.COLORS['primary']}]"
    )


def _auto_detect_context(bot: "TerminalChatbot") -> None:
    """Auto-detect project type and enable matching skills."""
    if bot.context_switcher:
        ctx = bot.context_switcher.detect()
        if ctx.prompt_addition:
            console.print(
                f"[dim]Detected {ctx.project_type} project ({ctx.language})[/dim]"
            )
        bot._current_context = ctx
    if bot.skill_manager:
        detected = bot.skill_manager.auto_detect(str(bot.workspace_root.name))
        if detected:
            console.print(f"[dim]Auto-enabled skills: {', '.join(detected)}[/dim]")


def _suggest_intelligence(bot: "TerminalChatbot", query: str) -> None:
    """Print persona/mode suggestions based on the user query."""
    from veni.detector import suggest_intelligence

    suggestion = suggest_intelligence(query)
    suggestions = []

    if suggestion.get("persona"):
        name = suggestion["persona"]
        current = bot.persona_engine.get_current()
        if not current or current.name.lower() != name:
            persona = bot.persona_engine.get_persona(name)
            if persona:
                suggestions.append(
                    f"[dim]💡 Suggested persona: {persona.icon} {persona.name}[/dim]"
                )

    if suggestion.get("mode"):
        name = suggestion["mode"]
        current = bot.mode_engine.get_current()
        if not current or current.name.lower() != name:
            mode = bot.mode_engine.get_mode(name)
            if mode:
                suggestions.append(
                    f"[dim]💡 Suggested mode: {mode.icon} {mode.name}[/dim]"
                )

    for s in suggestions:
        console.print(s)


def _record_memory(bot: "TerminalChatbot", query: str, response: str) -> None:
    """Persist interaction notes and corrections to memory."""
    if any(
        w in query.lower()
        for w in ["no,", "wrong", "incorrect", "not that", "don't", "do not"]
    ):
        bot.memory_system.record_correction(query)

    topic = query[:80].strip()
    if topic:
        bot.memory_system.remember(
            category="interaction",
            content=f"User asked about: {topic}",
            weight=0.1,
        )


def _check_response_errors(bot: "TerminalChatbot", response: str) -> None:
    """Log and surface potential issues found in the AI response."""
    if response.startswith("Error:") or "Error:" in response[:100]:
        bot.last_error = response[:200]
    if bot.error_detector:
        issues = bot.error_detector.analyze_test_results(response)
        if issues:
            console.print(
                f"[dim]🔍 Found {len(issues)} potential issue(s) in response[/dim]"
            )
