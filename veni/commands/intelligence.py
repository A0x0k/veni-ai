from rich import box
"""
Intelligence commands for Veni AI.

/persona, /mode, /skill commands for managing personas, modes, and skills.
"""

from typing import List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from veni.commands.base import BaseCommand, console

# --- Persona Commands ---


class PersonaCommand(BaseCommand):
    """Set the active persona."""

    @property
    def name(self) -> str:
        return "/persona"

    @property
    def description(self) -> str:
        return "Set or manage the AI's persona."

    @property
    def usage(self) -> str:
        return "/persona [name | list | current | auto]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            return self._show_usage()

        action = args[0].lower()

        if action == "list":
            return self._list_personas()
        elif action == "current":
            return self._current_persona()
        elif action == "auto":
            return self._auto_persona(args[1:] if len(args) > 1 else [])
        else:
            return self._set_persona(action)

    def _set_persona(self, name: str) -> Optional[str]:
        if self.bot.persona_engine.set_persona(name):
            persona = self.bot.persona_engine.get_current()
            self.show_success(
                f"Persona set to: {persona.icon} {persona.name}\n{persona.description}"
            )
        else:
            self.show_error(
                f"Unknown persona: '{name}'. Use /persona list to see available."
            )
        return None

    def _list_personas(self) -> Optional[str]:
        personas = self.bot.persona_engine.list_personas()
        table = Table(
            title="Available Personas", box=box.ROUNDED, header_style="bold cyan"
        )
        table.add_column("Icon", style="white")
        table.add_column("Name", style="bold magenta")
        table.add_column("Description", style="white")
        table.add_column("Best For", style="dim")

        current = self.bot.persona_engine.get_current()
        for p in personas:
            active = " ◀ active" if current and current.name == p.name else ""
            table.add_row(
                p.icon,
                f"{p.name}{active}",
                p.description[:60],
                ", ".join(p.best_for[:3]),
            )

        console.print(table)
        return None

    def _current_persona(self) -> Optional[str]:
        current = self.bot.persona_engine.get_current()
        if current:
            console.print(
                Panel(
                    Text.assemble(
                        (f"{current.icon} {current.name}\n", "bold magenta"),
                        (f"{current.description}\n\n", "white"),
                        (f"Tone: {current.tone} | Depth: {current.depth}", "dim"),
                    ),
                    title="Current Persona",
                    border_style="magenta",
                )
            )
        else:
            console.print("[dim]No persona active (using base system prompt)[/dim]")
        return None

    def _auto_persona(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /persona auto <query>")
            return None

        query = " ".join(args)
        suggestion = self.bot.persona_engine.suggest_for_query(query)
        if suggestion:
            persona = self.bot.persona_engine.get_persona(suggestion)
            console.print(
                f"[dim]Based on '{query}', suggested persona:[/dim] "
                f"{persona.icon} {persona.name}"
            )
        else:
            console.print(f"[dim]No persona suggestion for '{query}'[/dim]")
        return None


# --- Mode Commands ---


class ModeCommand(BaseCommand):
    """Set the active interaction mode."""

    @property
    def name(self) -> str:
        return "/mode"

    @property
    def description(self) -> str:
        return "Set or manage the AI's interaction mode."

    @property
    def usage(self) -> str:
        return "/mode [name | list | current | auto]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            return self._show_usage()

        action = args[0].lower()

        if action == "list":
            return self._list_modes()
        elif action == "current":
            return self._current_mode()
        elif action == "auto":
            return self._auto_mode(args[1:] if len(args) > 1 else [])
        else:
            return self._set_mode(action)

    def _set_mode(self, name: str) -> Optional[str]:
        if self.bot.mode_engine.set_mode(name):
            mode = self.bot.mode_engine.get_current()
            self.show_success(
                f"Mode set to: {mode.icon} {mode.name}\n{mode.description}"
            )
        else:
            self.show_error(f"Unknown mode: '{name}'. Use /mode list to see available.")
        return None

    def _list_modes(self) -> Optional[str]:
        modes = self.bot.mode_engine.list_modes()
        table = Table(title="Available Modes", box=box.ROUNDED, header_style="bold cyan")
        table.add_column("Icon", style="white")
        table.add_column("Name", style="bold magenta")
        table.add_column("Description", style="white")

        current = self.bot.mode_engine.get_current()
        for m in modes:
            active = " ◀ active" if current and current.name == m.name else ""
            table.add_row(
                m.icon,
                f"{m.name}{active}",
                m.description[:70],
            )

        console.print(table)
        return None

    def _current_mode(self) -> Optional[str]:
        current = self.bot.mode_engine.get_current()
        if current:
            console.print(
                Panel(
                    Text.assemble(
                        (f"{current.icon} {current.name}\n", "bold magenta"),
                        (f"{current.description}\n\n", "white"),
                        (f"Style: {current.response_style}", "dim"),
                    ),
                    title="Current Mode",
                    border_style="magenta",
                )
            )
        else:
            console.print("[dim]No mode active (using default behavior)[/dim]")
        return None

    def _auto_mode(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /mode auto <query>")
            return None

        query = " ".join(args)
        suggestion = self.bot.mode_engine.suggest_for_query(query)
        if suggestion:
            mode = self.bot.mode_engine.get_mode(suggestion)
            console.print(
                f"[dim]Based on '{query}', suggested mode:[/dim] "
                f"{mode.icon} {mode.name}"
            )
        else:
            console.print(f"[dim]No mode suggestion for '{query}'[/dim]")
        return None


# --- Skill Commands ---


class SkillCommand(BaseCommand):
    """Manage active skills."""

    @property
    def name(self) -> str:
        return "/skill"

    @property
    def description(self) -> str:
        return "Enable, disable, or list skills."

    @property
    def usage(self) -> str:
        return "/skill [name | list | search <query> | status | enable <name> | disable <name> | auto <query>]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            return self._show_usage()

        action = args[0].lower()

        if action == "list":
            return self._list_skills()
        elif action == "search" and len(args) > 1:
            return self._search_skills(" ".join(args[1:]))
        elif action == "status":
            return self._skill_status()
        elif action == "enable" and len(args) > 1:
            return self._enable_skill(args[1])
        elif action == "disable" and len(args) > 1:
            return self._disable_skill(args[1])
        elif action == "auto" and len(args) > 1:
            return self._auto_detect(" ".join(args[1:]))
        else:
            return self._show_skill(args[0])

    def _list_skills(self) -> Optional[str]:
        skills = self.bot.skill_manager.list_skills()
        active = self.bot.skill_manager.get_active_skills()
        table = Table(title="Available Skills", box=box.ROUNDED, header_style="bold cyan")
        table.add_column("Name", style="bold magenta")
        table.add_column("Description", style="white")
        table.add_column("Source", style="dim")
        table.add_column("Active", style="green")

        for s in skills:
            is_active = s.name in active
            table.add_row(
                s.name,
                s.description[:50],
                s.source,
                "✅" if is_active else "—",
            )

        console.print(table)
        return None


    def _search_skills(self, query: str) -> Optional[str]:
        matches = self.bot.skill_manager.registry.match_triggers(query)
        if not matches:
            self.show_warning(f"No skills match '{query}'.")
            return None
        table = Table(
            title=f"Skills matching '{query}'",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Name", style="bold magenta")
        table.add_column("Description", style="white")
        table.add_column("Triggers", style="dim")
        active = self.bot.skill_manager.get_active_skills()
        for m in matches:
            is_active = "✅" if m.name in active else "—"
            table.add_row(
                f"{m.name} {is_active}",
                m.description[:50],
                ", ".join(m.triggers[:4]),
            )
        console.print(table)
        return None


    def _skill_status(self) -> Optional[str]:
        status = self.bot.skill_manager.get_status()
        parts = [
            "[bold]Skills Status[/bold]",
            f"Available: {status['available']}",
            f"Active: {', '.join(status['active']) if status['active'] else 'none'}",
        ]
        if status["auto_detected"]:
            parts.append(f"  Auto-detected: {', '.join(status['auto_detected'])}")
        if status["user_selected"]:
            parts.append(f"  User-selected: {', '.join(status['user_selected'])}")
        console.print("\n".join(parts))
        return None

    def _enable_skill(self, name: str) -> Optional[str]:
        if self.bot.skill_manager.enable_skill(name):
            self.show_success(f"Skill enabled: {name}")
        else:
            self.show_error(
                f"Unknown skill: '{name}'. Use /skill list to see available."
            )
        return None

    def _disable_skill(self, name: str) -> Optional[str]:
        self.bot.skill_manager.disable_skill(name)
        self.show_success(f"Skill disabled: {name}")
        return None

    def _show_skill(self, name: str) -> Optional[str]:
        skill = self.bot.skill_manager.get_skill(name)
        if skill:
            console.print(
                Panel(
                    Text.assemble(
                        (f"Skill: {skill.name}\n", "bold magenta"),
                        (f"{skill.metadata.description}\n\n", "white"),
                        (f"Triggers: {', '.join(skill.metadata.triggers[:5])}", "dim"),
                    ),
                    title="Skill Details",
                    border_style="magenta",
                )
            )
        else:
            self.show_error(f"Unknown skill: '{name}'")
        return None

    def _auto_detect(self, query: str) -> Optional[str]:
        detected = self.bot.skill_manager.auto_detect(query)
        if detected:
            console.print(
                f"[dim]Auto-detected skills for '{query}':[/dim] "
                f"{', '.join(detected)}"
            )
        else:
            console.print(f"[dim]No skills detected for '{query}'[/dim]")
        return None


class ApproveCommand(BaseCommand):
    """Toggle approval gate for tool execution."""

    @property
    def name(self) -> str:
        return "/approve"

    @property
    def description(self) -> str:
        return "Toggle approval gate for tool execution."

    @property
    def usage(self) -> str:
        return "/approve [on | off | status]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            current = self.bot.approval_gate.enabled
            self.bot.approval_gate.enabled = not current
            state = "enabled" if self.bot.approval_gate.enabled else "disabled"
            self.show_success(f"Approval gate {state}.")
            return None

        action = args[0].lower()

        if action in ("on", "enable", "yes", "y"):
            self.bot.approval_gate.enabled = True
            self.show_success("Approval gate enabled.")
        elif action in ("off", "disable", "no", "n"):
            self.bot.approval_gate.enabled = False
            self.show_success("Approval gate disabled.")
        elif action == "status":
            state = "enabled" if self.bot.approval_gate.enabled else "disabled"
            console.print(f"Approval gate: {state}")
        else:
            self.show_error("Usage: /approve [on | off | status]")

        return None


class DebugCommand(BaseCommand):
    """Analyze error output and debug issues."""

    @property
    def name(self) -> str:
        return "/debug"

    @property
    def description(self) -> str:
        return "Analyze error output and get debugging suggestions."

    @property
    def usage(self) -> str:
        return "/debug [error output or description]"

    def execute(self, args: list[str]) -> Optional[str]:
        if not args:
            if self.bot.last_error:
                return self._analyze(self.bot.last_error)
            self.show_error("Usage: /debug [error output or description]")
            return None

        error_text = " ".join(args)
        return self._analyze(error_text)

    def _analyze(self, error_text: str) -> Optional[str]:
        """Analyze error text using DebugMode."""
        response = self.bot.debug_mode.get_conversational_response(error_text)
        console.print(response)
        return None


class PlanCommand(BaseCommand):
    """Toggle autonomous planning mode."""

    @property
    def name(self) -> str:
        return "/plan"

    @property
    def description(self) -> str:
        return "Toggle autonomous planning mode. When active, the AI must output a PLAN.md before acting."

    @property
    def usage(self) -> str:
        return "/plan [on | off | status]"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            current = self.bot.planning_mode
            self.bot.planning_mode = not current
            state = "enabled" if self.bot.planning_mode else "disabled"
            self.show_success(f"Planning mode {state}.")
            return None

        action = args[0].lower()
        if action in ("on", "enable"):
            self.bot.planning_mode = True
            self.show_success("Planning mode enabled.")
        elif action in ("off", "disable"):
            self.bot.planning_mode = False
            self.show_success("Planning mode disabled.")
        elif action == "status":
            state = "enabled" if self.bot.planning_mode else "disabled"
            console.print(f"Planning mode: {state}")
        else:
            self.show_error("Usage: /plan [on | off | status]")
        return None
