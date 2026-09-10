"""
Core chatbot application logic.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from veni.approval import ApprovalGate
from veni.cache_sys import VeniCache
from veni.commands.ai import (
    MaxTokensCommand,
    ModelCommand,
    SetupCommand,
    StatusCommand,
    SystemCommand,
    TemperatureCommand,
    TemplateCommand,
    TopPCommand,
)
from veni.commands.base import CommandRegistry
from veni.commands.file import (
    CdCommand,
    EditCommand,
    LsCommand,
    PwdCommand,
    ReadCommand,
    TreeCommand,
)
from veni.commands.git import CommitCommand, DiffCommand, LogCommand
from veni.commands.help import HelpCommand
from veni.commands.intelligence import (
    ApproveCommand,
    DebugCommand,
    ModeCommand,
    PersonaCommand,
    PlanCommand,
    SkillCommand,
)
from veni.commands.message import (
    AliasCommand,
    PinCommand,
    PinsCommand,
    RetryCommand,
    SummaryCommand,
    UnpinCommand,
)
from veni.commands.session import (
    ExitCommand,
    ExportCommand,
    HistoryCommand,
    LoadCommand,
    NewCommand,
    QCommand,
    QuitCommand,
    SaveCommand,
)
from veni.commands.tools import (
    CopyCommand,
    ImageCommand,
    SearchCommand,
    StatsCommand,
    VoiceCommand,
)
from veni.commands.ui import (
    BannerCommand,
    ClearCommand,
    ColorsCommand,
    ContrastCommand,
    MenuCommand,
    NetworkCommand,
    RedactCommand,
    ThemeCommand,
    TipsCommand,
)
from veni.commands.web import PdfCommand, ScrapeCommand
from veni.commands.workflow import WorkflowCommand
from veni.commands.xref import XrefCommand
from veni.completer import VeniCompleter
from veni.config import config
from veni.context_switch import ContextSwitcher
from veni.plugin_loader import load_plugins
from veni.tool_executor import (
    check_and_execute_tools,
    execute_tool,
    execute_tool_with_dict,
)
from veni.chat_engine import (
    stream_response as _stream_response,
    update_system_prompt as _update_system_prompt,
)
from veni.startup import (
    maybe_resume_last_session,
    init_codebase_indexer,
    autosave_session,
)
from veni.session import (
    run as _session_run,
    _auto_detect_context,
    _suggest_intelligence,
    _record_memory,
    _check_response_errors,
)
import veni.ui as _ui
import veni.workspace as _workspace
from veni.crossref import CrossReferenceAnalyzer
from veni.debug import DebugMode
from veni.detector import ErrorDetector
from veni.gateways.telegram import TelegramGateway
from veni.git_ops import GitIntelligence
from veni.history import ChatHistory
from veni.indexer import CodebaseIndexer
from veni.mcp import MCPClient
from veni.memory import MemorySystem
from veni.modes.engine import ModeEngine
from veni.parallel import ParallelEngine
from veni.personas.engine import PersonaEngine
from veni.providers.base import AIClient
from veni.providers.factory import get_provider_name
from veni.providers.http import ping_provider
from veni.scheduler import VeniScheduler
from veni.server import VeniDashboard
from veni.sharing import SessionExporter
from veni.skill_manager import SkillManager
from veni.tools.base import ToolRegistry
from veni.tools.browser import BrowserTool
from veni.tools.doc_lookup import DocLookupTool
from veni.tools.files import FileReadTool, FileWriteTool
from veni.tools.image_gen import ImageGenTool
from veni.tools.intelligence import IntelligenceTool
from veni.tools.repo_map import RepoMapTool
from veni.tools.search import SearchTool
from veni.tools.shell import ShellExecTool
from veni.tools.vision import VisionTool
from veni.tools.voice import VoiceTool
from veni.tools.web_intelligence import WebIntelligenceTool
from veni.workflows import WorkflowEngine

console = Console()

if TYPE_CHECKING:
    from veni.voice import VoiceEngine


class TerminalChatbot:
    """Main terminal chatbot application."""

    COLORS = {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "accent": "#06b6d4",
        "user": "#22c55e",
        "assistant": "#3b82f6",
        "dim": "#475569",
        "error": "#ef4444",
        "success": "#10b981",
        "warning": "#f59e0b",
    }

    def __init__(self, ai_client: AIClient, context_tokens: Optional[int] = None):
        self.ai_client = ai_client
        self.config = config
        self.history = ChatHistory()
        self.voice_engine: Optional["VoiceEngine"] = None
        self.context_tokens = context_tokens or config.get("defaults", {}).get(
            "context_tokens", 4096
        )
        self.running = True
        self.voice_mode = False
        self.planning_mode = False
        self.last_response = ""
        self.current_images: List[str] = []
        self.cwd = Path.cwd().resolve()
        self.workspace_root = self.cwd
        self.codebase_indexer: Optional[CodebaseIndexer] = None

        # Initialize Tool Registry
        self.tool_registry = ToolRegistry(self)
        self.tool_registry.register(SearchTool(self))
        self.tool_registry.register(FileReadTool(self))
        self.tool_registry.register(FileWriteTool(self))
        self.tool_registry.register(ShellExecTool(self))
        self.tool_registry.register(RepoMapTool(self))
        self.tool_registry.register(VoiceTool(self))
        self.tool_registry.register(WebIntelligenceTool(self))
        self.tool_registry.register(DocLookupTool(self))
        self.tool_registry.register(IntelligenceTool(self))
        self.tool_registry.register(BrowserTool(self))
        self.tool_registry.register(VisionTool(self))
        self.tool_registry.register(ImageGenTool(self))

        # Approval gate for tool execution safety
        self.approval_gate = ApprovalGate()

        # Intelligence subsystems
        self.persona_engine = PersonaEngine()
        self.mode_engine = ModeEngine()
        self.skill_manager = SkillManager(self)
        self.memory_system = MemorySystem(
            enable_semantic=config.get("features.semantic_memory", False)
        )
        self.workflow_engine = WorkflowEngine(self)
        self.error_detector = ErrorDetector(self)
        self.crossref_analyzer = CrossReferenceAnalyzer(None)  # Set indexer after init
        self.session_exporter = SessionExporter(self.history, self.memory_system)
        self.git_intelligence = GitIntelligence(self)
        self.debug_mode = DebugMode(self)
        self.context_switcher = ContextSwitcher(self)
        self.veni_cache = VeniCache()
        self.parallel_engine = ParallelEngine(max_workers=4)
        self.scheduler = VeniScheduler(self)
        self.telegram_gateway = TelegramGateway(self)
        self.dashboard = VeniDashboard(self)

        # MCP clients for external tool servers
        self.mcp_clients: List[MCPClient] = []

        self.plugin_commands: Dict[str, Callable] = {}
        self.plugin_help: Dict[str, str] = {}
        self.generation_params: Dict[str, Optional[float]] = {
            "temperature": None,
            "top_p": None,
            "max_tokens": None,
        }
        self.ui_theme = config.get("ui_theme", {})
        self.quick_actions = config.get("quick_actions", [])
        self.ui_tips = config.get("ui_tips", [])
        self._compact_banner = config.get("compact_banner", False)

        # Input history for navigation
        self.input_history: List[str] = []
        self.history_index: int = -1

        # Error recovery
        self.last_error: Optional[str] = None
        self.last_failed_input: Optional[str] = None

        # Load theme colors from config
        theme_colors = config.get("theme_colors", {})
        if theme_colors:
            self.COLORS.update(theme_colors)

        # Initialize Command Registry
        self.command_registry = CommandRegistry(self)
        self.commands: Dict[
            str, Callable
        ] = {}  # Keep for compatibility with handle_command and plugins
        self._register_core_commands()

        self._load_plugins()

        # Update commands dict with registry commands for backwards compatibility
        for cmd_name, cmd in self.command_registry.commands.items():
            self.commands[cmd_name] = cmd.execute

    def _register_core_commands(self):
        """Register all core commands in the registry."""
        core_commands = [
            HelpCommand,
            QuitCommand,
            ExitCommand,
            QCommand,
            NewCommand,
            SaveCommand,
            LoadCommand,
            HistoryCommand,
            ExportCommand,
            SystemCommand,
            ModelCommand,
            TemperatureCommand,
            TopPCommand,
            MaxTokensCommand,
            TemplateCommand,
            StatusCommand,
            SetupCommand,
            PwdCommand,
            LsCommand,
            CdCommand,
            ReadCommand,
            EditCommand,
            TreeCommand,
            DiffCommand,
            CommitCommand,
            LogCommand,
            ClearCommand,
            ThemeCommand,
            ColorsCommand,
            ContrastCommand,
            MenuCommand,
            TipsCommand,
            PersonaCommand,
            ModeCommand,
            SkillCommand,
            ApproveCommand,
            DebugCommand,
            SearchCommand,
            VoiceCommand,
            ImageCommand,
            CopyCommand,
            StatsCommand,
            WorkflowCommand,
            ScrapeCommand,
            PdfCommand,
            XrefCommand,
            PinCommand,
            UnpinCommand,
            PinsCommand,
            RetryCommand,
            SummaryCommand,
            AliasCommand,
            RedactCommand,
            NetworkCommand,
            PlanCommand,
            BannerCommand,
        ]
        for cmd_cls in core_commands:
            self.command_registry.register(cmd_cls)
            # Legacy mapping for backwards compatibility in handle_command and existing plugins
            cmd = self.command_registry.get(cmd_cls(self).name)
            self.commands[cmd.name] = cmd.execute

    @property
    def provider_name(self) -> str:
        return get_provider_name(self.ai_client)

    @property
    def model_name(self) -> str:
        return getattr(self.ai_client, "model", "unknown")

    def print_header(self):
        """Print stylized Veni banner with gradients."""
        _ui.print_header(self)

    def format_user_message(self, content: str, images: List[str] = None):
        """Format user message with a side rail."""
        _ui.format_user_message(self, content, images)

    def stream_response(self, messages: List[Dict], max_tool_calls: int = 10) -> str:
        """Stream AI response with tool call support. See veni/chat_engine.py."""
        return _stream_response(self, messages, max_tool_calls)

    def _check_and_execute_tools(self, response: str) -> str | None:
        return check_and_execute_tools(self, response)

    def _execute_tool(self, tool_name: str, args_str: str) -> str | None:
        return execute_tool(self, tool_name, args_str)

    def _execute_tool_with_dict(self, tool_name: str, args: dict) -> str | None:
        return execute_tool_with_dict(self, tool_name, args)

    def handle_command(self, cmd_input: str) -> Optional[str]:
        """Route a command string to its handler via the registry."""
        parts = cmd_input.split()
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Primary: command registry (core commands + registered plugins)
        command = self.command_registry.get(cmd_name)
        if command:
            return command.execute(args)

        # Fallback: legacy plugin handlers (plugins that only populate self.commands)
        handler = self.commands.get(cmd_name)
        if handler:
            return handler(args)

        self.show_error(f"Unknown command: {cmd_name}")
        return None

    def show_onboarding(self):
        onboarding_marker = config.config_dir / ".onboarding_complete"
        if onboarding_marker.exists():
            return
        console.clear()
        welcome_panel = Panel(
            "[bold cyan]Welcome to VENI AI![/bold cyan]\n\nYour intelligent terminal assistant is ready.\n\n[bold]Key Features:[/bold]\n• Multi-provider AI support\n• Rich terminal UI\n• File & web search\n• Voice & image support\n\nPress Enter to continue...",
            title="Welcome to Veni AI",
            border_style=self.COLORS["primary"],
            box=box.DOUBLE,
            padding=(2, 4),
        )
        console.print(welcome_panel)
        input()
        onboarding_marker.touch()
        console.clear()

    def get_user_input(self) -> str:
        if self.voice_mode and self.voice_engine:
            return self.voice_engine.listen_once() or ""

        def get_toolbar():
            _, tokens, dropped = self.history.get_context_state(self.context_tokens)
            status = []
            if self.voice_mode:
                status.append("🎤 VOICE")
            if self.current_images:
                status.append(f"🖼️ {len(self.current_images)}")
            if dropped > 0:
                status.append(f"⚠️ PRUNED {dropped}")
            active_skills = self.skill_manager.get_active_skills()
            if active_skills:
                status.append(f"🛠 {', '.join(active_skills)}")
            bar_len = 10
            used = int(
                (min(tokens, self.context_tokens) / self.context_tokens) * bar_len
            )
            bar = "█" * used + "░" * (bar_len - used)
            return f" [ {bar} {tokens}/{self.context_tokens} ] " + " | ".join(status)

        def get_rprompt():
            return f"{self.provider_name.upper()} • {self.model_name} "

        bindings = KeyBindings()

        @bindings.add(Keys.ControlR)
        def _(event):
            """Start reverse history search (Ctrl+R)."""
            event.app.current_buffer.start_reverse_history_search()

        @bindings.add(Keys.ControlE)
        def _(event):
            """Toggle multi-line input with Ctrl+E."""
            from prompt_toolkit.application import run_in_terminal
            run_in_terminal(
                lambda: console.print("[dim]Enter multi-line (Ctrl+D to finish):[/dim]")
            )
            event.app.current_buffer.start_new_input()

        session = PromptSession(
            history=InMemoryHistory(),
            bottom_toolbar=get_toolbar,
            refresh_interval=0.5,
            key_bindings=bindings,
            multiline=False,
        )
        for hist in self.input_history:
            session.history.append_string(hist)
        completer = VeniCompleter(self)
        try:
            user_input = session.prompt(
                "❯ ",
                rprompt=get_rprompt,
                auto_suggest=AutoSuggestFromHistory(),
                completer=completer,
            )
        except (KeyboardInterrupt, EOFError):
            return ""
        if user_input.strip():
            self.input_history.append(user_input)
            self.history_index = len(self.input_history)
        if user_input.lower() in ["quit", "exit"]:
            self.running = False
            return "EXIT"
        return user_input

    def show_success(self, message: str):
        _ui.show_success(self, message)

    def show_error(self, message: str):
        _ui.show_error(self, message)

    def show_status(self, message: str):
        _ui.show_status(self, message)

    def show_warning(self, message: str):
        _ui.show_warning(self, message)

    def get_multi_line_input(self) -> str:
        console.print("[dim]Enter multi-line input (empty line to finish):[/dim]")
        lines = []
        while True:
            try:
                line = input().strip()
                if not line and lines:
                    break
                if line:
                    lines.append(line)
                elif not lines:
                    break
            except EOFError:
                break
        return "\n".join(lines)

    def run(self):
        _session_run(self)

    def _auto_detect_context(self):
        _auto_detect_context(self)

    def _suggest_intelligence(self, query: str):
        _suggest_intelligence(self, query)

    def _record_memory(self, query: str, response: str):
        _record_memory(self, query, response)

    def _check_response_errors(self, response: str):
        _check_response_errors(self, response)

    def _update_system_prompt(self, current_query: Optional[str] = None):
        _update_system_prompt(self, current_query)

    def _get_generation_params(self) -> Dict[str, Any]:
        return {k: v for k, v in self.generation_params.items() if v is not None}

    def _resolve_path(self, path_str: str) -> Path:
        return _workspace.resolve_path(self.cwd, path_str)

    def resolve_workspace_path(self, path_str: str) -> Path:
        return _workspace.resolve_workspace_path(
            self.cwd, self.workspace_root, path_str
        )

    def _is_within_workspace(self, path: Path) -> bool:
        return _workspace.is_within_workspace(path, self.workspace_root)

    def _load_plugins(self):
        cmds, help_map = load_plugins(self)
        self.plugin_commands.update(cmds)
        self.plugin_help.update(help_map)
        self.commands.update(cmds)

    def _show_model_presets(self):
        _ui.show_model_presets(self)

    def _autosave_session(self):
        autosave_session(self)

    def _maybe_resume_last_session(self):
        maybe_resume_last_session(self)

    def _init_codebase_indexer(self):
        init_codebase_indexer(self)

    def _ping_provider(self) -> str:
        base_url = getattr(self.ai_client, "base_url", None)
        if not base_url:
            return "n/a"
        return ping_provider(
            base_url,
            api_key=getattr(self.ai_client, "api_key", None),
            provider_name=self.provider_name,
        )
