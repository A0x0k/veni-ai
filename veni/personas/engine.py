"""
Persona Engine for Veni AI.

Manages WHO Veni is — expertise domain, perspective, and priorities.
Personas change the system prompt, tone, and behavior.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    """A single persona definition."""

    name: str
    description: str
    system_prompt_addition: str
    tone: str = "neutral"
    depth: str = "adaptive"
    best_for: List[str] = field(default_factory=list)
    icon: str = "🧠"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt_addition": self.system_prompt_addition,
            "tone": self.tone,
            "depth": self.depth,
            "best_for": self.best_for,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        return cls(
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            system_prompt_addition=data.get("system_prompt_addition", ""),
            tone=data.get("tone", "neutral"),
            depth=data.get("depth", "adaptive"),
            best_for=data.get("best_for", []),
            icon=data.get("icon", "🧠"),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "Persona":
        """Load persona from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class PersonaEngine:
    """
    Manages persona selection and application.

    Usage:
        engine = PersonaEngine()
        engine.set_persona("teacher")
        prompt = engine.get_system_prompt_addition()
    """

    def __init__(self, personas_dir: Optional[Path] = None):
        self.builtins_dir = Path(__file__).parent / "builtins"
        self.custom_dir = Path.home() / ".veni-chatbot" / "personas"
        self.custom_dir.mkdir(parents=True, exist_ok=True)

        self._personas: Dict[str, Persona] = {}
        self._current: Optional[Persona] = None
        self._load_all()

    def _load_all(self):
        """Load all personas from builtins and custom directory."""
        self._personas.clear()
        for yaml_file in self.builtins_dir.glob("*.yaml"):
            try:
                persona = Persona.from_yaml(yaml_file)
                self._personas[persona.name.lower()] = persona
            except Exception as exc:
                logger.debug("Failed to load persona %s: %s", yaml_file.name, exc)

        for yaml_file in self.custom_dir.glob("*.yaml"):
            try:
                persona = Persona.from_yaml(yaml_file)
                self._personas[persona.name.lower()] = persona
            except Exception as exc:
                logger.warning("Failed to load custom persona %s: %s", yaml_file.name, exc)

    def list_personas(self) -> List[Persona]:
        """List all available personas."""
        return sorted(self._personas.values(), key=lambda p: p.name)

    def get_persona(self, name: str) -> Optional[Persona]:
        """Get a persona by name (case-insensitive)."""
        return self._personas.get(name.lower())

    def set_persona(self, name: str) -> bool:
        """Set the active persona."""
        persona = self.get_persona(name)
        if persona:
            self._current = persona
            return True
        return False

    def get_current(self) -> Optional[Persona]:
        """Get the active persona."""
        return self._current

    def get_system_prompt_addition(self) -> str:
        """Get the system prompt addition for the current persona."""
        if self._current:
            return self._current.system_prompt_addition
        return ""

    def clear_persona(self):
        """Remove the active persona (use base system prompt only)."""
        self._current = None

    def suggest_for_query(self, query: str) -> Optional[str]:
        """Suggest a persona based on the user's query using shared patterns."""
        # Use the shared detector patterns for consistency across all suggestion mechanisms
        from veni.detector import INTELLIGENCE_PATTERNS

        query_lower = query.lower()
        for pattern, persona_name in INTELLIGENCE_PATTERNS["persona_suggestions"]:
            if re.search(pattern, query_lower):
                return persona_name
        return None

    def export_config(self) -> Dict[str, Any]:
        """Export current persona state."""
        return {
            "current_persona": self._current.name if self._current else None,
        }

    def import_config(self, config: Dict[str, Any]):
        """Import persona state from config."""
        name = config.get("current_persona")
        if name:
            self.set_persona(name)
