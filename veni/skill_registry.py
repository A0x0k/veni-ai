"""
Skill Registry for Veni AI.

Parses and manages AgentSkills-standard skill definitions.
SKILL.md format: YAML frontmatter + markdown content + optional scripts/references.
Compatible with Claude Code, OpenHands, Cursor, and other AgentSkills adopters.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class SkillMetadata:
    """Lightweight skill metadata (always loaded for matching)."""

    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "unknown"
    source: str = ""  # "builtin", "installed", "custom"
    directory: Path = field(default_factory=Path)

    def matches_query(self, query: str) -> bool:
        """Check if a query matches this skill's triggers (word-boundary aware)."""
        import re
        query_lower = query.lower()
        for trigger in self.triggers:
            # Escape the trigger and require word boundaries so "test" doesn't
            # match inside "latest", "contest", etc.
            pattern = r"\b" + re.escape(trigger.lower()) + r"\b"
            if re.search(pattern, query_lower):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "triggers": self.triggers,
            "version": self.version,
            "author": self.author,
            "source": self.source,
        }


@dataclass
class Skill:
    """Full skill definition with content (loaded on demand)."""

    metadata: SkillMetadata
    instructions: str = ""  # Full markdown content
    has_scripts: bool = False
    has_references: bool = False
    scripts_dir: Optional[Path] = None
    references_dir: Optional[Path] = None

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def system_prompt_addition(self) -> str:
        """Extract instructions for system prompt."""
        return self.instructions

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.metadata.to_dict(),
            "instructions": self.instructions[:500],  # Truncated
            "has_scripts": self.has_scripts,
            "has_references": self.has_references,
        }


class SkillRegistry:
    """
    Registry for AgentSkills-standard skills.

    Follows the AgentSkills specification (agentskills.io):
    - SKILL.md with YAML frontmatter
    - Progressive disclosure (metadata always, full on trigger)
    - Compatible with Claude Code, OpenHands, Cursor, etc.

    Usage:
        registry = SkillRegistry()
        registry.scan()
        skills = registry.match_triggers("django orm patterns")
    """

    def __init__(self):
        self.builtins_dir = Path(__file__).parent / "skills" / "builtins"
        self.installed_dir = Path.home() / ".veni-chatbot" / "skills"
        self.project_dir = Path.cwd() / ".veni" / "skills"
        self.installed_dir.mkdir(parents=True, exist_ok=True)

        self._metadata: Dict[str, SkillMetadata] = {}
        self._loaded: Dict[str, Skill] = {}

    def scan(self):
        """Scan all skill directories and load metadata."""
        self._metadata.clear()
        self._loaded.clear()

        # Scan builtins
        if self.builtins_dir.exists():
            self._scan_directory(self.builtins_dir, "builtin")

        # Scan installed
        if self.installed_dir.exists():
            self._scan_directory(self.installed_dir, "installed")

        # Scan project-specific
        if self.project_dir.exists():
            self._scan_directory(self.project_dir, "custom")

    def _scan_directory(self, directory: Path, source: str):
        """Scan a directory for SKILL.md files."""
        for skill_dir in directory.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                metadata = self._parse_metadata(skill_md, source, skill_dir)
                self._metadata[metadata.name.lower()] = metadata
            except Exception:
                pass

    def _parse_metadata(
        self, path: Path, source: str, directory: Path
    ) -> SkillMetadata:
        """Parse YAML frontmatter from SKILL.md."""
        content = path.read_text(encoding="utf-8")
        frontmatter = self._extract_frontmatter(content)

        return SkillMetadata(
            name=frontmatter.get("name", directory.name),
            description=frontmatter.get("description", ""),
            triggers=frontmatter.get("triggers", []),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", "unknown"),
            source=source,
            directory=directory,
        )

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from SKILL.md."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1)) or {}
        return {}

    def _extract_body(self, content: str) -> str:
        """Extract markdown body after frontmatter."""
        match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
        if match:
            return content[match.end() :].strip()
        return content.strip()

    # --- Public API ---

    def list_skills(self) -> List[SkillMetadata]:
        """List all available skills (metadata only)."""
        return sorted(self._metadata.values(), key=lambda s: s.name)

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a full skill by name (loads content on demand)."""
        key = name.lower()
        if key in self._loaded:
            return self._loaded[key]

        metadata = self._metadata.get(key)
        if not metadata:
            return None

        # Load full content
        skill_md = metadata.directory / "SKILL.md"
        if not skill_md.exists():
            return None

        content = skill_md.read_text(encoding="utf-8")
        instructions = self._extract_body(content)

        scripts_dir = metadata.directory / "scripts"
        references_dir = metadata.directory / "references"

        skill = Skill(
            metadata=metadata,
            instructions=instructions,
            has_scripts=scripts_dir.exists(),
            has_references=references_dir.exists(),
            scripts_dir=scripts_dir if scripts_dir.exists() else None,
            references_dir=(references_dir if references_dir.exists() else None),
        )

        self._loaded[key] = skill
        return skill

    def match_triggers(self, query: str) -> List[SkillMetadata]:
        """Find skills whose triggers match a query."""
        return [m for m in self._metadata.values() if m.matches_query(query)]

    def get_system_prompt_contributions(self, skill_names: List[str]) -> str:
        """Get combined system prompt additions for loaded skills."""
        parts = []
        for name in skill_names:
            skill = self.get_skill(name)
            if skill and skill.instructions:
                parts.append(f"## Skill: {skill.name}\n{skill.instructions}")
        return "\n\n".join(parts) if parts else ""

    def get_skill_summary(self) -> str:
        """Get a human-readable summary of all skills."""
        if not self._metadata:
            return "No skills loaded."

        lines = ["## Available Skills\n"]
        for m in self.list_skills():
            lines.append(f"- **{m.name}** ({m.source}) — {m.description}")
            if m.triggers:
                lines.append(f"  Triggers: {', '.join(m.triggers[:5])}")
        return "\n".join(lines)
