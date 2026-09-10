"""Tests for the persona engine."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from veni.personas.engine import Persona, PersonaEngine


# ── Persona ────────────────────────────────────────────────────────────────


class TestPersona:
    def test_default_creation(self):
        persona = Persona(
            name="test", description="A test persona", system_prompt_addition=""
        )
        assert persona.name == "test"
        assert persona.description == "A test persona"
        assert persona.tone == "neutral"
        assert persona.depth == "adaptive"
        assert persona.best_for == []
        assert persona.icon == "🧠"

    def test_to_dict(self):
        persona = Persona(
            name="expert",
            description="Expert persona",
            system_prompt_addition="You are an expert.",
            tone="authoritative",
            depth="deep",
            best_for=["code review", "architecture"],
            icon="🎓",
        )
        data = persona.to_dict()
        assert data["name"] == "expert"
        assert data["tone"] == "authoritative"
        assert data["depth"] == "deep"

    def test_from_dict(self):
        data = {
            "name": "teacher",
            "description": "Teaching persona",
            "system_prompt_addition": "You are a teacher.",
            "tone": "patient",
            "depth": "step-by-step",
            "best_for": ["tutorials", "onboarding"],
            "icon": "👨‍🏫",
        }
        persona = Persona.from_dict(data)
        assert persona.name == "teacher"
        assert persona.tone == "patient"

    def test_from_dict_minimal(self):
        persona = Persona.from_dict({"name": "minimal"})
        assert persona.name == "minimal"
        assert persona.tone == "neutral"

    def test_from_yaml(self, tmp_path):
        yaml_file = tmp_path / "test_persona.yaml"
        data = {
            "name": "critic",
            "description": "Critical thinker",
            "tone": "analytical",
            "system_prompt_addition": "Challenge all assumptions.",
        }
        yaml_file.write_text(yaml.dump(data))
        persona = Persona.from_yaml(yaml_file)
        assert persona.name == "critic"
        assert persona.tone == "analytical"
        assert persona.system_prompt_addition == "Challenge all assumptions."


# ── PersonaEngine ──────────────────────────────────────────────────────────


class TestPersonaEngine:
    @pytest.fixture
    def engine(self, tmp_path):
        return PersonaEngine(personas_dir=tmp_path)

    def test_initialization(self, engine):
        assert engine._current is None
        assert isinstance(engine._personas, dict)

    def test_list_personas_empty(self, engine):
        personas = engine.list_personas()
        assert isinstance(personas, list)

    def test_get_nonexistent_persona(self, engine):
        persona = engine.get_persona("nonexistent")
        assert persona is None

    def test_set_persona_not_found(self, engine):
        result = engine.set_persona("nonexistent")
        assert result is False

    def test_get_current_when_none(self, engine):
        assert engine.get_current() is None

    def test_get_system_prompt_addition_when_none(self, engine):
        assert engine.get_system_prompt_addition() == ""

    def test_clear_persona(self, engine):
        engine._current = Persona(
            name="test", description="", system_prompt_addition=""
        )
        engine.clear_persona()
        assert engine._current is None

    def test_export_config_none(self, engine):
        config = engine.export_config()
        assert config["current_persona"] is None

    def test_import_config(self, engine):
        config = {"current_persona": "expert"}
        with patch.object(engine, "set_persona") as mock_set:
            engine.import_config(config)
            mock_set.assert_called_once_with("expert")

    def test_suggest_for_query(self, engine):
        detector_patcher = patch(
            "veni.detector.INTELLIGENCE_PATTERNS",
            {"persona_suggestions": [(r"teach|learn|explain", "teacher")]},
        )
        detector_patcher.start()
        try:
            suggestion = engine.suggest_for_query("Can you teach me Python?")
            assert suggestion == "teacher"
        finally:
            detector_patcher.stop()

    def test_suggest_for_query_no_match(self, engine):
        detector_patcher = patch(
            "veni.detector.INTELLIGENCE_PATTERNS",
            {"persona_suggestions": [(r"teach|learn|explain", "teacher")]},
        )
        detector_patcher.start()
        try:
            suggestion = engine.suggest_for_query("What is the weather?")
            assert suggestion is None
        finally:
            detector_patcher.stop()

    def test_load_builtins_and_custom(self, tmp_path):
        engine = PersonaEngine(personas_dir=tmp_path)
        assert isinstance(engine, PersonaEngine)
        assert engine.list_personas() is not None
