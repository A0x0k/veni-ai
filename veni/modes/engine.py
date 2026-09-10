"""
Mode Engine for Veni AI.

Manages HOW Veni communicates — verbosity, structure, and interaction style.
Modes are orthogonal to personas — any persona can use any mode.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Mode:
    """A single mode definition."""

    name: str
    description: str
    system_prompt_addition: str
    max_response_length: Optional[int] = None
    response_style: str = "default"
    best_for: List[str] = field(default_factory=list)
    icon: str = "💬"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt_addition": self.system_prompt_addition,
            "max_response_length": self.max_response_length,
            "response_style": self.response_style,
            "best_for": self.best_for,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mode":
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            system_prompt_addition=data.get("system_prompt_addition", ""),
            max_response_length=data.get("max_response_length"),
            response_style=data.get("response_style", "default"),
            best_for=data.get("best_for", []),
            icon=data.get("icon", "💬"),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "Mode":
        """Load mode from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class ModeEngine:
    """
    Manages mode selection and application.

    Usage:
        engine = ModeEngine()
        engine.set_mode("brief")
        prompt = engine.get_system_prompt_addition()
    """

    def __init__(self, modes_dir: Optional[Path] = None):
        self.builtins_dir = Path(__file__).parent / "builtins"
        self.custom_dir = Path.home() / ".veni-chatbot" / "modes"
        self.custom_dir.mkdir(parents=True, exist_ok=True)

        self._modes: Dict[str, Mode] = {}
        self._current: Optional[Mode] = None
        self._load_all()

    def _load_all(self):
        """Load all modes from builtins and custom directory."""
        self._modes.clear()
        for yaml_file in self.builtins_dir.glob("*.yaml"):
            try:
                mode = Mode.from_yaml(yaml_file)
                self._modes[mode.name.lower()] = mode
            except Exception as exc:
                logger.debug("Failed to load mode %s: %s", yaml_file.name, exc)

        for yaml_file in self.custom_dir.glob("*.yaml"):
            try:
                mode = Mode.from_yaml(yaml_file)
                self._modes[mode.name.lower()] = mode
            except Exception as exc:
                logger.warning("Failed to load custom mode %s: %s", yaml_file.name, exc)

    def list_modes(self) -> List[Mode]:
        """List all available modes."""
        return sorted(self._modes.values(), key=lambda m: m.name)

    def get_mode(self, name: str) -> Optional[Mode]:
        """Get a mode by name (case-insensitive)."""
        return self._modes.get(name.lower())

    def set_mode(self, name: str) -> bool:
        """Set the active mode."""
        mode = self.get_mode(name)
        if mode:
            self._current = mode
            return True
        return False

    def get_current(self) -> Optional[Mode]:
        """Get the active mode."""
        return self._current

    def get_system_prompt_addition(self) -> str:
        """Get the system prompt addition for the current mode."""
        if self._current:
            return self._current.system_prompt_addition
        return ""

    def get_max_response_length(self) -> Optional[int]:
        """Get max response length for the current mode."""
        if self._current:
            return self._current.max_response_length
        return None

    def clear_mode(self):
        """Remove the active mode (use default behavior)."""
        self._current = None

    def suggest_for_query(self, query: str) -> Optional[str]:
        """Suggest a mode based on the user's query using shared patterns."""
        # Use the shared detector patterns for consistency across all suggestion mechanisms
        from veni.detector import INTELLIGENCE_PATTERNS

        query_lower = query.lower()
        for pattern, mode_name in INTELLIGENCE_PATTERNS["mode_suggestions"]:
            if re.search(pattern, query_lower):
                return mode_name
        return None

    def export_config(self) -> Dict[str, Any]:
        """Export current mode state."""
        return {
            "current_mode": self._current.name if self._current else None,
        }

    def import_config(self, config: Dict[str, Any]):
        """Import mode state from config."""
        name = config.get("current_mode")
        if name:
            self.set_mode(name)
