"""Tests for the skill manager and skill registry systems."""

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import yaml

from veni.skill_manager import SkillManager, SkillStack
from veni.skill_registry import Skill, SkillMetadata, SkillRegistry


# ── SkillStack ─────────────────────────────────────────────────────────────


class TestSkillStack:
    def test_empty_stack(self):
        stack = SkillStack()
        assert stack.all_skills() == []

    def test_enable_auto_skill(self):
        stack = SkillStack()
        stack.enable("code-review", source="auto")
        assert "code-review" in stack.all_skills()
        assert "code-review" in stack.auto_detected

    def test_enable_user_skill(self):
        stack = SkillStack()
        stack.enable("debugging", source="user")
        assert "debugging" in stack.all_skills()
        assert "debugging" in stack.user_selected

    def test_disable_skill(self):
        stack = SkillStack()
        stack.enable("testing", source="auto")
        stack.disable("testing")
        assert "testing" not in stack.all_skills()

    def test_dedup_skills(self):
        stack = SkillStack()
        stack.enable("skill1", source="auto")
        stack.enable("skill1", source="user")
        assert len(stack.all_skills()) == 1

    def test_clear_skills(self):
        stack = SkillStack()
        stack.enable("skill1", source="auto")
        stack.enable("skill2", source="user")
        stack.clear()
        assert stack.all_skills() == []

    def test_case_insensitive_disable(self):
        stack = SkillStack()
        stack.enable("Code-Review", source="auto")
        stack.disable("code-review")
        assert stack.all_skills() == []


# ── SkillRegistry ──────────────────────────────────────────────────────────


class TestSkillRegistry:
    @pytest.fixture
    def registry(self):
        reg = SkillRegistry()
        # Override dirs to avoid needing real files
        reg.builtins_dir = Path("nonexistent_builtins")
        reg.installed_dir = Path("nonexistent_installed")
        reg.project_dir = Path("nonexistent_project")
        return reg

    def test_initial_state(self, registry):
        assert registry.list_skills() == []

    def test_scan_empty_dirs(self, registry):
        registry.scan()
        assert registry.list_skills() == []

    def test_scan_with_skill(self, tmp_path, registry):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: test-skill\ndescription: A test skill\ntriggers: [test]\n---\n\nTest instructions"
        )
        registry.builtins_dir = tmp_path
        registry.scan()
        skills = registry.list_skills()
        assert len(skills) == 1
        assert skills[0].name == "test-skill"

    def test_get_skill(self, tmp_path, registry):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: test-skill\ndescription: A test skill\ntriggers: [test]\n---\n\nTest instructions"
        )
        registry.builtins_dir = tmp_path
        registry.scan()
        found = registry.get_skill("test-skill")
        assert found is not None
        assert found.metadata.name == "test-skill"
        assert "Test instructions" in found.instructions

    def test_get_nonexistent_skill(self, registry):
        assert registry.get_skill("nonexistent") is None

    def test_match_triggers(self, tmp_path, registry):
        skill_dir = tmp_path / "python-dev"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: python-dev\ndescription: Python dev\ntriggers: [python, django, flask]\n---\n\nPython skill"
        )
        registry.builtins_dir = tmp_path
        registry.scan()
        matches = registry.match_triggers("How do I write a Django view?")
        assert len(matches) == 1
        assert matches[0].name == "python-dev"

    def test_match_triggers_no_match(self, tmp_path, registry):
        skill_dir = tmp_path / "python-dev"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: python-dev\ndescription: Python dev\ntriggers: [python, django]\n---\n\nPython skill"
        )
        registry.builtins_dir = tmp_path
        registry.scan()
        matches = registry.match_triggers("How do I write a Rust function?")
        assert len(matches) == 0

    def test_get_system_prompt_contributions(self, tmp_path, registry):
        for name in ["skill1", "skill2"]:
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                f"---\nname: {name}\ndescription: {name}\ntriggers: []\n---\n\nPrompt {name}"
            )
        registry.builtins_dir = tmp_path
        registry.scan()
        result = registry.get_system_prompt_contributions(["skill1", "skill2"])
        assert "Prompt skill1" in result
        assert "Prompt skill2" in result

    def test_get_skill_summary(self, tmp_path, registry):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: test-skill\ndescription: A test skill\ntriggers: [test]\n---\n\nTest instructions"
        )
        registry.builtins_dir = tmp_path
        registry.scan()
        summary = registry.get_skill_summary()
        assert "test-skill" in summary


# ── SkillManager ───────────────────────────────────────────────────────────


class TestSkillManager:
    @pytest.fixture
    def mock_bot(self):
        bot = MagicMock()
        bot.skill_manager = None
        return bot

    @pytest.fixture
    def manager(self, mock_bot):
        with patch.object(SkillRegistry, "scan"):
            mgr = SkillManager(mock_bot)
            return mgr

    def test_initialization(self, manager):
        assert manager.bot is not None
        assert manager.registry is not None
        assert manager.stack is not None

    def test_list_skills(self, manager):
        with patch.object(manager.registry, "list_skills", return_value=[]):
            skills = manager.list_skills()
            assert isinstance(skills, list)

    def test_enable_skill(self, manager):
        metadata = SkillMetadata(
            name="test-skill", description="Test", triggers=[], source="builtin"
        )
        manager.registry._metadata["test-skill"] = metadata
        result = manager.enable_skill("test-skill")
        assert result is True

    def test_enable_nonexistent_skill(self, manager):
        result = manager.enable_skill("nonexistent")
        assert result is False

    def test_disable_skill(self, manager):
        manager.stack.enable("test-skill", source="user")
        manager.disable_skill("test-skill")
        assert "test-skill" not in manager.get_active_skills()

    def test_get_active_skills(self, manager):
        manager.stack.enable("skill-a", source="auto")
        manager.stack.enable("skill-b", source="user")
        active = manager.get_active_skills()
        assert "skill-a" in active
        assert "skill-b" in active

    def test_auto_detect(self, manager):
        metadata = SkillMetadata(
            name="python-dev",
            description="Python development",
            triggers=["python"],
            source="builtin",
        )
        manager.registry._metadata["python-dev"] = metadata
        detected = manager.auto_detect("I need help with Python")
        assert "python-dev" in detected

    def test_get_system_prompt_empty(self, manager):
        prompt = manager.get_system_prompt()
        assert prompt == ""

    def test_get_system_prompt_with_skills(self, tmp_path, manager):
        skill_dir = tmp_path / "test"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: test\ndescription: Test\ntriggers: []\n---\n\nTest prompt"
        )
        manager.registry.builtins_dir = tmp_path
        manager.registry.scan()
        manager.stack.enable("test", source="auto")
        prompt = manager.get_system_prompt()
        assert "Test prompt" in prompt

    def test_get_status(self, manager):
        status = manager.get_status()
        assert "available" in status
        assert "active" in status
        assert "auto_detected" in status
        assert "user_selected" in status
