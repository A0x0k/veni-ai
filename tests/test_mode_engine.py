"""Tests for the mode engine."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from veni.modes.engine import Mode, ModeEngine


# ── Mode ───────────────────────────────────────────────────────────────────


class TestMode:
    def test_default_creation(self):
        mode = Mode(name="test", description="A test mode", system_prompt_addition="")
        assert mode.name == "test"
        assert mode.description == "A test mode"
        assert mode.max_response_length is None
        assert mode.response_style == "default"
        assert mode.best_for == []
        assert mode.icon == "💬"

    def test_to_dict(self):
        mode = Mode(
            name="concise",
            description="Short responses",
            system_prompt_addition="Be brief.",
            max_response_length=100,
            response_style="brief",
            best_for=["quick answers", "status checks"],
            icon="⚡",
        )
        data = mode.to_dict()
        assert data["name"] == "concise"
        assert data["max_response_length"] == 100
        assert data["response_style"] == "brief"

    def test_from_dict(self):
        data = {
            "name": "detailed",
            "description": "Thorough responses",
            "system_prompt_addition": "Be thorough.",
            "max_response_length": 2000,
            "response_style": "comprehensive",
            "best_for": ["research", "analysis"],
            "icon": "📚",
        }
        mode = Mode.from_dict(data)
        assert mode.name == "detailed"
        assert mode.max_response_length == 2000

    def test_from_dict_minimal(self):
        persona = Mode.from_dict({"name": "minimal"})
        assert persona.name == "minimal"
        assert persona.response_style == "default"

    def test_from_yaml(self, tmp_path):
        yaml_file = tmp_path / "test_mode.yaml"
        data = {
            "name": "socratic",
            "description": "Question-based learning",
            "system_prompt_addition": "Guide user through questions.",
            "response_style": "interactive",
        }
        yaml_file.write_text(yaml.dump(data))
        mode = Mode.from_yaml(yaml_file)
        assert mode.name == "socratic"
        assert mode.response_style == "interactive"
        assert "questions" in mode.system_prompt_addition


# ── ModeEngine ─────────────────────────────────────────────────────────────


class TestModeEngine:
    @pytest.fixture
    def engine(self):
        return ModeEngine()

    def test_initialization(self, engine):
        assert engine._current is None
        assert isinstance(engine._modes, dict)

    def test_list_modes(self, engine):
        modes = engine.list_modes()
        assert isinstance(modes, list)

    def test_get_nonexistent_mode(self, engine):
        mode = engine.get_mode("nonexistent")
        assert mode is None

    def test_set_mode_not_found(self, engine):
        result = engine.set_mode("nonexistent")
        assert result is False

    def test_get_current_when_none(self, engine):
        assert engine.get_current() is None

    def test_get_system_prompt_addition_when_none(self, engine):
        assert engine.get_system_prompt_addition() == ""

    def test_get_max_response_length_when_none(self, engine):
        assert engine.get_max_response_length() is None

    def test_clear_mode(self, engine):
        engine._current = Mode(name="test", description="", system_prompt_addition="")
        engine.clear_mode()
        assert engine._current is None

    def test_export_config_none(self, engine):
        config = engine.export_config()
        assert config["current_mode"] is None

    def test_import_config(self, engine):
        config = {"current_mode": "concise"}
        with patch.object(engine, "set_mode") as mock_set:
            engine.import_config(config)
            mock_set.assert_called_once_with("concise")

    def test_suggest_for_query(self, engine):
        detector_patcher = patch(
            "veni.detector.INTELLIGENCE_PATTERNS",
            {"mode_suggestions": [(r"step by step|guide|walk me through", "step_by_step")]},
        )
        detector_patcher.start()
        try:
            suggestion = engine.suggest_for_query("Walk me through this step by step")
            assert suggestion == "step_by_step"
        finally:
            detector_patcher.stop()

    def test_suggest_for_query_no_match(self, engine):
        detector_patcher = patch(
            "veni.detector.INTELLIGENCE_PATTERNS",
            {"mode_suggestions": [(r"step by step|guide", "step_by_step")]},
        )
        detector_patcher.start()
        try:
            suggestion = engine.suggest_for_query("What time is it?")
            assert suggestion is None
        finally:
            detector_patcher.stop()

    def test_set_mode_success(self, engine):
        mode = Mode(name="concise", description="Brief", system_prompt_addition="")
        engine._modes["concise"] = mode
        result = engine.set_mode("concise")
        assert result is True
        assert engine.get_current() is mode
