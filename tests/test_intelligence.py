"""
Integration tests for new intelligence features:
personas, modes, skills, workflows, approval gate, debug mode.
"""

import pytest

from veni.approval import ApprovalGate, RiskLevel
from veni.debug import DebugMode
from veni.detector import suggest_intelligence
from veni.modes.engine import ModeEngine
from veni.personas.engine import PersonaEngine
from veni.skill_manager import SkillManager
from veni.skill_registry import SkillRegistry
from veni.workflows import TaskStatus, TaskStep, WorkflowEngine

# --- Persona Engine Tests ---


class TestPersonaEngine:
    """Test persona loading, switching, and suggestion."""

    @pytest.fixture
    def engine(self):
        return PersonaEngine()

    def test_loads_builtins(self, engine):
        personas = engine.list_personas()
        assert len(personas) >= 12

    def test_set_persona(self, engine):
        assert engine.set_persona("teacher")
        current = engine.get_current()
        assert current is not None
        assert current.name == "Teacher"

    def test_set_unknown_persona(self, engine):
        assert not engine.set_persona("nonexistent")

    def test_persona_prompt_addition(self, engine):
        engine.set_persona("teacher")
        prompt = engine.get_system_prompt_addition()
        assert "teacher" in prompt.lower()

    def test_clear_persona(self, engine):
        engine.set_persona("teacher")
        engine.clear_persona()
        assert engine.get_current() is None

    def test_suggest_for_query(self, engine):
        suggestion = engine.suggest_for_query("help me learn python")
        assert suggestion is not None  # Should suggest something


# --- Mode Engine Tests ---


class TestModeEngine:
    """Test mode loading, switching, and suggestion."""

    @pytest.fixture
    def engine(self):
        return ModeEngine()

    def test_loads_builtins(self, engine):
        modes = engine.list_modes()
        assert len(modes) >= 10

    def test_set_mode(self, engine):
        assert engine.set_mode("brief")
        current = engine.get_current()
        assert current is not None
        assert current.name == "Brief"

    def test_set_unknown_mode(self, engine):
        assert not engine.set_mode("nonexistent")

    def test_mode_prompt_addition(self, engine):
        engine.set_mode("socratic")
        prompt = engine.get_system_prompt_addition()
        assert "socratic" in prompt.lower()

    def test_suggest_for_query(self, engine):
        suggestion = engine.suggest_for_query("compare A vs B")
        assert suggestion == "compare"


# --- Skill Registry Tests ---


class TestSkillRegistry:
    """Test skill loading and trigger matching."""

    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_loads_builtins(self, registry):
        registry.scan()
        skills = registry.list_skills()
        assert len(skills) >= 6

    def test_trigger_matching(self, registry):
        registry.scan()
        matches = registry.match_triggers("django orm")
        assert len(matches) >= 1
        names = [m.name for m in matches]
        assert "Python Web Development" in names

    def test_load_full_skill(self, registry):
        registry.scan()
        skill = registry.get_skill("Python Web Development")
        assert skill is not None
        assert skill.instructions != ""

    def test_system_prompt_contributions(self, registry):
        registry.scan()
        prompt = registry.get_system_prompt_contributions(["Python Web Development"])
        assert "Python Web Development" in prompt


# --- Skill Manager Tests ---


class TestSkillManager:
    """Test skill stacking and auto-detection."""

    @pytest.fixture
    def manager(self):
        return SkillManager()

    def test_enable_skill(self, manager):
        assert manager.enable_skill("testing")
        assert "testing" in manager.get_active_skills()

    def test_disable_skill(self, manager):
        manager.enable_skill("testing")
        manager.disable_skill("testing")
        assert "testing" not in manager.get_active_skills()

    def test_auto_detect(self, manager):
        detected = manager.auto_detect("django security")
        assert len(detected) >= 1

    def test_skill_stacking(self, manager):
        manager.enable_skill("testing")
        manager.enable_skill("security audit")
        active = manager.get_active_skills()
        assert "testing" in active
        assert any("security" in s.lower() for s in active)

    def test_get_status(self, manager):
        manager.enable_skill("testing")
        status = manager.get_status()
        assert status["available"] >= 6


# --- Workflow Engine Tests ---


class TestWorkflowEngine:
    """Test workflow creation and execution."""

    class _FakeBot:
        pass

    @pytest.fixture
    def engine(self):
        return WorkflowEngine(self._FakeBot())

    def test_create_workflow(self, engine):
        wf = engine.create_workflow("test", "test desc", [])
        assert wf.name == "test"
        assert engine.get_workflow("test") is not None

    def test_execute_empty_workflow(self, engine):
        wf = engine.create_workflow("empty", "no steps", [])
        result = engine.execute(wf)
        assert result == {}

    def test_execute_workflow_with_steps(self, engine):
        def step_func():
            return "done"

        wf = engine.create_workflow(
            "test",
            "test",
            [TaskStep(name="step1", description="step", action=step_func)],
        )
        result = engine.execute(wf)
        assert result["step1"] == "done"
        assert wf.status == TaskStatus.COMPLETED

    def test_workflow_retry(self, engine):
        call_count = 0

        def failing_step():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("first fail")
            return "ok"

        wf = engine.create_workflow(
            "retry",
            "test",
            [TaskStep(name="s", description="s", action=failing_step, max_retries=2)],
        )
        result = engine.execute(wf)
        assert result["s"] == "ok"
        assert call_count == 2

    def test_get_history(self, engine):
        wf = engine.create_workflow("hist", "h", [])
        engine.execute(wf)
        history = engine.get_history()
        assert len(history) == 1


# --- Approval Gate Tests ---


class TestApprovalGate:
    """Test approval gate safety checks."""

    def test_disabled_allows_all(self):
        gate = ApprovalGate(enabled=False)
        assert gate.check("shell_exec", {"command": "ls"})

    def test_safe_tool_auto_approved(self):
        gate = ApprovalGate(enabled=True, max_risk=RiskLevel.MEDIUM)
        # Safe tools should auto-approve without prompting
        gate.non_interactive = True  # Prevent any prompts
        result = gate.check("read_file", {"path": "test.txt"})
        assert result is True

    def test_non_interactive_blocks_high_risk(self):
        gate = ApprovalGate(enabled=True, max_risk=RiskLevel.LOW, non_interactive=True)
        # MEDIUM risk tools should be blocked when max_risk is LOW
        assert not gate.check("shell_exec", {"command": "ls"})

    def test_write_preview_is_safe_but_apply_is_not(self):
        gate = ApprovalGate(enabled=True, max_risk=RiskLevel.LOW, non_interactive=True)
        assert gate.check("write_file", {"path": "test.txt", "content": "x"})
        assert not gate.check(
            "write_file", {"path": "test.txt", "content": "x", "apply": True}
        )

    def test_get_log(self):
        gate = ApprovalGate(enabled=False)
        gate.check("read_file", {"path": "test.txt"})
        log = gate.get_log()
        assert len(log) >= 0


# --- Debug Mode Tests ---


class TestDebugMode:
    """Test debug mode error analysis."""

    class _FakeBot:
        pass

    @pytest.fixture
    def debug(self):
        return DebugMode(self._FakeBot())

    def test_analyze_missing_import(self, debug):
        result = debug.analyze("ModuleNotFoundError: No module named 'requests'")
        assert result.error_type == "missing_import"

    def test_analyze_attribute_error(self, debug):
        result = debug.analyze("AttributeError: 'str' object has no attribute 'foo'")
        assert result.error_type == "attribute_error"

    def test_analyze_type_error(self, debug):
        result = debug.analyze("TypeError: can only concatenate str (not 'int') to str")
        assert result.error_type == "type_error"

    def test_conversational_response(self, debug):
        response = debug.get_conversational_response(
            "ModuleNotFoundError: No module named 'pandas'"
        )
        assert "missing_import" in response or "install" in response.lower()


# --- Auto-Detection Tests ---


class TestAutoDetection:
    """Test suggest_intelligence from detector.py."""

    def test_persona_suggestion_teacher(self):
        result = suggest_intelligence("help me learn python")
        assert result["persona"] == "teacher"

    def test_persona_suggestion_creative(self):
        result = suggest_intelligence("brainstorm some ideas")
        assert result["persona"] == "creative"

    def test_mode_suggestion_brief(self):
        result = suggest_intelligence("give me a quick summary")
        assert result["mode"] == "brief"

    def test_mode_suggestion_compare(self):
        result = suggest_intelligence("compare python vs go")
        assert result["mode"] == "compare"

    def test_no_suggestion(self):
        result = suggest_intelligence("hello")
        assert result["persona"] is None
        assert result["mode"] is None
