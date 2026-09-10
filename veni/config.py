"""
Configuration management for Veni AI Chatbot.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

DEFAULT_CONFIG = {
    "default_provider": "ollama",
    "default_model": "llama3.2",
    "default_context_size": 10,
    "theme": "dark",
    "theme_colors": {
        "primary": "#00d4ff",  # Bright cyan for logo
        "secondary": "#7b68ee",  # Medium purple for accents
        "accent": "#00ff88",  # Mint green for success
        "user": "#ff6b6b",  # Coral for user messages
        "assistant": "#4ecdc4",  # Teal for AI responses
        "dim": "#6b7280",  # Gray for secondary info
        "error": "#ff4757",  # Bright red for errors
        "success": "#2ed573",  # Green for success
        "warning": "#ffa502",  # Orange for warnings
    },
    "ui_theme": {
        "background": "#030712",
        "rail_bg": "#0a0f1a",
        "panel_alt": "#111827",
        "badge": "#38bdf8",
        "input_bg": "#1f2937",
        "input_border": "#334155",
        "tip_bg": "#0f172a",
        "tip_text": "#f8fafc",
    },
    "model_presets": {
        "openai": ["gpt-4o", "gpt-4o-mini"],
        "anthropic": ["claude-3-5-sonnet-20240620"],
        "gemini": ["gemini-2.0-flash"],
        "ollama": ["llama3.2", "llama3.1", "qwen2.5"],
        "deepseek": ["deepseek-chat"],
        "groq": ["llama-3.1-70b-versatile"],
        "qwen": ["qwen-max"],
        "free": ["openai"],
    },
    "prompt_templates": {
        "default": "You are Veni, a professional and helpful terminal-based AI assistant. You can use search and edit files. Keep responses concise and focused.",
        "concise": "You are Veni. Keep responses brief and direct. Use bullet points when helpful.",
        "coding": "You are Veni, a senior software engineer. Provide clear, practical code suggestions and highlight tradeoffs.",
    },
    "quick_actions": ["/new", "/read", "/search", "/template", "/pin"],
    # System defaults — configurable constants used across Veni
    "defaults": {
        "context_tokens": 4096,
        "max_tool_calls": 3,
        "max_index_files": 2000,
        "max_tool_output": 8000,
        "cache_ttl_seconds": 3600,
        "cache_max_entries": 1000,
        "cache_max_size_mb": 50,
        "parallel_workers": 4,
        "search_max_results": 5,
        "api_timeout_seconds": 30,
        "api_max_retries": 3,
        "api_rate_limit_delay": 0.5,
    },
    "ui_tips": [
        "Pin critical responses to keep them out of pruning.",
        "Use /read to inject docs or configs before asking for fixes.",
        "Templates keep system prompts consistent—consider naming them.",
        "Search results auto-inject; revisit the search panel after edits.",
        "Enable voice for hands-free “explain” requests when multitasking.",
    ],
    "features": {
        "semantic_memory": False,
        "proactive_scheduler": False,
        "telegram_gateway": False,
        "dashboard": False,
        "project_plugins": False,
    },
    "security": {
        "dashboard_token": "",
    },
    "api_keys": {
        "openai": "",
        "gemini": "",
        "huggingface": "",
        "anthropic": "",
        "groq": "",
        "deepseek": "",
        "mistral": "",
        "qwen": "",
    },
}


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".veni-chatbot"
        self.config_path = self.config_dir / "config.yaml"
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()

        # Ensure config dir exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load config if exists
        self.load()

    def load(self):
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                    # Deep merge with default config
                    self._update_dict(self._config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")

    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        keys = key.split(".")
        target = self._config
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        self.save()

    def _update_dict(self, target: dict, source: dict):
        """Recursively update dictionary."""
        for k, v in source.items():
            if k in target and isinstance(target[k], dict) and isinstance(v, dict):
                self._update_dict(target[k], v)
            else:
                target[k] = v


# Global config instance
config = ConfigManager()
