"""
Skill Manager for Veni AI.

Manages skill loading, stacking, enabling/disabling, and conflict resolution.
Built on top of SkillRegistry for AgentSkills-standard skill management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from veni.skill_registry import Skill, SkillMetadata, SkillRegistry


@dataclass
class SkillStack:
    """A composed stack of active skills."""

    auto_detected: List[str] = field(default_factory=list)
    user_selected: List[str] = field(default_factory=list)

    def all_skills(self) -> List[str]:
        """Return all active skill names (deduplicated, normalized)."""
        seen: Set[str] = set()
        result = []
        for name in self.auto_detected + self.user_selected:
            key = name.lower()
            if key not in seen:
                seen.add(key)
                result.append(name)
        return result

    def enable(self, name: str, source: str = "user"):
        """Enable a skill (normalized to lowercase to prevent duplicates)."""
        normalized = name.lower()
        if source == "auto":
            if normalized not in [s.lower() for s in self.auto_detected]:
                self.auto_detected.append(normalized)
        else:
            if normalized not in [s.lower() for s in self.user_selected]:
                self.user_selected.append(normalized)

    def disable(self, name: str):
        """Disable a skill (case-insensitive)."""
        normalized = name.lower()
        if normalized in self.auto_detected:
            self.auto_detected.remove(normalized)
        if normalized in self.user_selected:
            self.user_selected.remove(normalized)

    def clear(self):
        """Clear all skills."""
        self.auto_detected.clear()
        self.user_selected.clear()


class SkillManager:
    """
    High-level skill management for Veni AI.

    Handles:
    - Skill stacking (multiple active skills)
    - Auto-detection integration
    - User enable/disable
    - System prompt assembly
    """

    def __init__(self, bot: Any = None):
        self.bot = bot
        self.registry = SkillRegistry()
        self.stack = SkillStack()
        self.registry.scan()
        # Enable all builtin skills by default so they're available immediately
        for metadata in self.registry.list_skills():
            if metadata.source == "builtin":
                self.stack.enable(metadata.name.lower(), source="auto")

    def rescan(self) -> None:
        """Rescan skill directories."""
        self.registry.scan()

    def list_skills(self) -> List[SkillMetadata]:
        """List all available skills."""
        return self.registry.list_skills()

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a full skill by name."""
        return self.registry.get_skill(name)

    def enable_skill(self, name: str, source: str = "user") -> bool:
        """Enable a skill (uses canonical name from metadata)."""
        metadata = self.registry._metadata.get(name.lower())
        if metadata:
            # Use the canonical name from metadata, not user input
            canonical = metadata.name.lower()
            self.stack.enable(canonical, source)
            return True
        return False

    def disable_skill(self, name: str) -> None:
        """Disable a skill (case-insensitive)."""
        self.stack.disable(name)

    def get_active_skills(self) -> List[str]:
        """Get all active skill names."""
        return self.stack.all_skills()

    def auto_detect(self, query: str) -> List[str]:
        """Auto-detect skills from a query (normalized names)."""
        matches = self.registry.match_triggers(query)
        detected = []
        for m in matches:
            normalized = m.name.lower()
            self.stack.enable(normalized, source="auto")
            detected.append(normalized)
        return detected

    def get_system_prompt(self) -> str:
        """Build system prompt contributions from all active skills."""
        active = self.get_active_skills()
        if not active:
            return ""
        return self.registry.get_system_prompt_contributions(active)

    def get_summary(self) -> str:
        """Get human-readable summary of loaded skills."""
        return self.registry.get_skill_summary()

    def get_status(self) -> Dict[str, Any]:
        """Get current skill status."""
        return {
            "available": len(self.registry.list_skills()),
            "active": self.get_active_skills(),
            "auto_detected": list(self.stack.auto_detected),
            "user_selected": list(self.stack.user_selected),
        }
