"""
Intelligence Management Tool for Veni AI.

Allows the AI to autonomously manage personas, modes, and skills.
"""

from typing import Any, Dict

from veni.tools.base import AITool


class IntelligenceTool(AITool):
    """
    Tool for managing the AI's own intelligence configuration.

    The AI can use this to:
    - Set its persona (who it is)
    - Set its mode (how it communicates)
    - Enable/disable skills (what it knows)
    - Get current configuration status
    - Auto-detect and suggest appropriate settings
    """

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "intelligence_config"

    @property
    def description(self) -> str:
        return (
            "Manage the AI's persona, mode, and skills. "
            "Use this to change how you respond, your expertise domain, "
            "and what knowledge you have access to. "
            "Actions: set_persona, set_mode, enable_skill, disable_skill, "
            "get_status, auto_detect"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "set_persona",
                        "set_mode",
                        "enable_skill",
                        "disable_skill",
                        "get_status",
                        "auto_detect",
                        "list_personas",
                        "list_modes",
                        "list_skills",
                        "create_workflow",
                        "list_workflows",
                    ],
                    "description": "The action to perform.",
                },
                "name": {
                    "type": "string",
                    "description": (
                        "Persona, mode, or skill name "
                        "(required for set/enable/disable actions)."
                    ),
                },
                "query": {
                    "type": "string",
                    "description": "Query for auto-detection.",
                },
                "description": {
                    "type": "string",
                    "description": "Description for workflow creation.",
                },
            },
            "required": ["action"],
        }

    def execute(
        self,
        action: str,
        name: str = "",
        query: str = "",
        description: str = "",
        **kwargs: Any,
    ) -> str:
        """Execute an intelligence management action."""
        if action == "set_persona":
            return self._set_persona(name)
        elif action == "set_mode":
            return self._set_mode(name)
        elif action == "enable_skill":
            return self._enable_skill(name)
        elif action == "disable_skill":
            return self._disable_skill(name)
        elif action == "get_status":
            return self._get_status()
        elif action == "auto_detect":
            return self._auto_detect(query)
        elif action == "list_personas":
            return self._list_personas()
        elif action == "list_modes":
            return self._list_modes()
        elif action == "list_skills":
            return self._list_skills()
        elif action == "create_workflow":
            return self._create_workflow(name, description)
        elif action == "list_workflows":
            return self._list_workflows()
        elif action == "semantic_code_search":
            return self._semantic_code_search(query)
        else:
            return f"Unknown action: {action}"

    def _semantic_code_search(self, query: str) -> str:
        """Search the codebase semantically."""
        if not query:
            return "Error: 'query' is required for semantic_code_search."

        # Search in code symbols and files
        results = self.bot.memory_system.recall(query, limit=10, category="code_symbol")
        file_results = self.bot.memory_system.recall(query, limit=5, category="code_file")
        
        all_results = results + file_results
        if not all_results:
            return f"No semantic matches found for '{query}'"

        parts = [f"## Semantic Search Results for '{query}'\n"]
        for i, res in enumerate(all_results, 1):
            parts.append(f"{i}. {res}")
            
        return "\n".join(parts)

    def _set_persona(self, name: str) -> str:
        """Set the active persona."""
        if not name:
            return "Error: 'name' is required for set_persona."

        if self.bot.persona_engine.set_persona(name):
            persona = self.bot.persona_engine.get_current()
            return (
                f"Persona set to: {persona.icon} {persona.name}\n"
                f"System prompt updated: {persona.description}"
            )
        else:
            available = [p.name for p in self.bot.persona_engine.list_personas()]
            return f"Unknown persona: '{name}'. " f"Available: {', '.join(available)}"

    def _set_mode(self, name: str) -> str:
        """Set the active mode."""
        if not name:
            return "Error: 'name' is required for set_mode."

        if self.bot.mode_engine.set_mode(name):
            mode = self.bot.mode_engine.get_current()
            return (
                f"Mode set to: {mode.icon} {mode.name}\n"
                f"Response style updated: {mode.description}"
            )
        else:
            available = [m.name for m in self.bot.mode_engine.list_modes()]
            return f"Unknown mode: '{name}'. " f"Available: {', '.join(available)}"

    def _enable_skill(self, name: str) -> str:
        """Enable a skill."""
        if not name:
            return "Error: 'name' is required for enable_skill."

        if self.bot.skill_manager.enable_skill(name):
            active = self.bot.skill_manager.get_active_skills()
            return (
                f"Skill enabled: {name}\n"
                f"Active skills: {', '.join(active) if active else 'none'}"
            )
        else:
            available = [s.name for s in self.bot.skill_manager.list_skills()]
            return f"Unknown skill: '{name}'. " f"Available: {', '.join(available)}"

    def _disable_skill(self, name: str) -> str:
        """Disable a skill."""
        if not name:
            return "Error: 'name' is required for disable_skill."

        self.bot.skill_manager.disable_skill(name)
        active = self.bot.skill_manager.get_active_skills()
        return (
            f"Skill disabled: {name}\n"
            f"Active skills: {', '.join(active) if active else 'none'}"
        )

    def _get_status(self) -> str:
        """Get current intelligence configuration."""
        persona = self.bot.persona_engine.get_current()
        mode = self.bot.mode_engine.get_current()
        skills = self.bot.skill_manager.get_active_skills()

        parts = ["## Current Intelligence Configuration\n"]
        parts.append(
            f"**Persona:** {persona.icon if persona else ''} {persona.name if persona else 'None (default)'}"
        )
        parts.append(
            f"**Mode:** {mode.icon if mode else ''} {mode.name if mode else 'None (default)'}"
        )
        parts.append(f"**Skills:** {', '.join(skills) if skills else 'None'}")

        skill_status = self.bot.skill_manager.get_status()
        if skill_status.get("auto_detected"):
            parts.append(f"  Auto-detected: {', '.join(skill_status['auto_detected'])}")
        if skill_status.get("user_selected"):
            parts.append(f"  User-selected: {', '.join(skill_status['user_selected'])}")

        return "\n".join(parts)

    def _auto_detect(self, query: str) -> str:
        """Auto-detect appropriate persona, mode, and skills."""
        if not query:
            return "Error: 'query' is required for auto_detect."

        results = []

        # Persona suggestion
        persona_suggestion = self.bot.persona_engine.suggest_for_query(query)
        if persona_suggestion:
            results.append(f"Suggested persona: {persona_suggestion}")

        # Mode suggestion
        mode_suggestion = self.bot.mode_engine.suggest_for_query(query)
        if mode_suggestion:
            results.append(f"Suggested mode: {mode_suggestion}")

        # Skill detection
        detected_skills = self.bot.skill_manager.auto_detect(query)
        if detected_skills:
            results.append(f"Detected skills: {', '.join(detected_skills)}")

        if results:
            return f"Auto-detection for '{query}':\n" + "\n".join(results)
        else:
            return f"No intelligence suggestions for '{query}'"

    def _list_personas(self) -> str:
        """List available personas."""
        personas = self.bot.persona_engine.list_personas()
        if not personas:
            return "No personas available."

        parts = ["## Available Personas\n"]
        current = self.bot.persona_engine.get_current()
        for p in personas:
            active = " (active)" if current and current.name == p.name else ""
            parts.append(f"- {p.icon} **{p.name}**{active} — {p.description}")
        return "\n".join(parts)

    def _list_modes(self) -> str:
        """List available modes."""
        modes = self.bot.mode_engine.list_modes()
        if not modes:
            return "No modes available."

        parts = ["## Available Modes\n"]
        current = self.bot.mode_engine.get_current()
        for m in modes:
            active = " (active)" if current and current.name == m.name else ""
            parts.append(f"- {m.icon} **{m.name}**{active} — {m.description}")
        return "\n".join(parts)

    def _list_skills(self) -> str:
        """List available skills."""
        skills = self.bot.skill_manager.list_skills()
        if not skills:
            return "No skills available."

        active = self.bot.skill_manager.get_active_skills()
        parts = ["## Available Skills\n"]
        for s in skills:
            is_active = s.name in active
            status = " ✅" if is_active else ""
            parts.append(
                f"- **{s.name}**{status} — {s.description}\n"
                f"  Triggers: {', '.join(s.triggers[:5])}"
            )
        return "\n".join(parts)

    def _create_workflow(self, name: str, description: str) -> str:
        """Create a new workflow."""
        if not name:
            return "Error: 'name' is required for create_workflow."

        self.bot.workflow_engine.create_workflow(name, description, [])
        return f"Workflow created: {name}\nDescription: {description or name}"

    def _list_workflows(self) -> str:
        """List available workflows."""
        workflows = self.bot.workflow_engine.list_workflows()
        if not workflows:
            return "No workflows defined. Use create_workflow to define one."

        parts = ["## Available Workflows\n"]
        for name, wf in workflows.items():
            steps = len(wf.steps)
            parts.append(f"- **{name}** — {wf.description} ({steps} steps)")
        return "\n".join(parts)
