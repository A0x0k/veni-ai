"""
Tests for veni/tools/shell.py, veni/tools/files.py, and provider key validation.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bot(tmp_path: Path):
    bot = MagicMock()
    bot.cwd = tmp_path
    bot.workspace_root = tmp_path

    def resolve(p):
        resolved = (tmp_path / p).resolve()
        if not str(resolved).startswith(str(tmp_path)):
            raise ValueError(f"Path escapes workspace: {resolved}")
        return resolved

    bot.resolve_workspace_path.side_effect = resolve
    return bot


# ---------------------------------------------------------------------------
# ShellExecTool._check_blocked
# ---------------------------------------------------------------------------

class TestCheckBlocked:
    def setup_method(self):
        from veni.tools.shell import ShellExecTool
        self.tool = ShellExecTool(MagicMock())

    def test_allows_safe_command(self):
        assert self.tool._check_blocked("pytest tests/") == ""

    def test_allows_ls(self):
        assert self.tool._check_blocked("ls -la") == ""

    def test_blocks_rm_rf(self):
        assert self.tool._check_blocked("rm -rf /") != ""

    def test_blocks_rm_fr(self):
        assert self.tool._check_blocked("rm -fr .") != ""

    def test_blocks_rm_r(self):
        assert self.tool._check_blocked("rm -r somedir") != ""

    def test_blocks_powershell_remove_item_recurse(self):
        assert self.tool._check_blocked("Remove-Item -Recurse -Force .") != ""

    def test_blocks_powershell_ri_recurse(self):
        assert self.tool._check_blocked("ri -recurse .") != ""

    def test_blocks_del_s(self):
        assert self.tool._check_blocked("del /s /q C:\\temp") != ""

    def test_blocks_rmdir_s(self):
        assert self.tool._check_blocked("rmdir /s /q build") != ""

    def test_blocks_fork_bomb(self):
        assert self.tool._check_blocked(":(){:|:&};:") != ""

    def test_blocks_dd(self):
        assert self.tool._check_blocked("dd if=/dev/zero of=/dev/sda") != ""

    def test_case_insensitive(self):
        assert self.tool._check_blocked("RM -RF /") != ""

    def test_allows_grep(self):
        assert self.tool._check_blocked("grep -r 'error' .") == ""

    def test_allows_find(self):
        assert self.tool._check_blocked("find . -name '*.py'") == ""


# ---------------------------------------------------------------------------
# FileReadTool
# ---------------------------------------------------------------------------

class TestFileReadTool:
    def test_reads_existing_file(self, tmp_path):
        from veni.tools.files import FileReadTool
        (tmp_path / "hello.txt").write_text("hello world", encoding="utf-8")
        tool = FileReadTool(_make_bot(tmp_path))
        result = tool.execute(path="hello.txt")
        assert "hello world" in result

    def test_missing_file_returns_error(self, tmp_path):
        from veni.tools.files import FileReadTool
        tool = FileReadTool(_make_bot(tmp_path))
        result = tool.execute(path="nonexistent.txt")
        assert "Error" in result

    def test_missing_path_arg_returns_error(self, tmp_path):
        from veni.tools.files import FileReadTool
        tool = FileReadTool(_make_bot(tmp_path))
        result = tool.execute()
        assert "Error" in result

    def test_path_escape_blocked(self, tmp_path):
        from veni.tools.files import FileReadTool
        tool = FileReadTool(_make_bot(tmp_path))
        result = tool.execute(path="../../etc/passwd")
        assert "Error" in result


# ---------------------------------------------------------------------------
# FileWriteTool
# ---------------------------------------------------------------------------

class TestFileWriteTool:
    def test_preview_does_not_write(self, tmp_path):
        from veni.tools.files import FileWriteTool
        tool = FileWriteTool(_make_bot(tmp_path))
        tool.execute(path="out.txt", content="hello", apply=False)
        assert not (tmp_path / "out.txt").exists()

    def test_apply_writes_file(self, tmp_path):
        from veni.tools.files import FileWriteTool
        tool = FileWriteTool(_make_bot(tmp_path))
        tool.execute(path="out.txt", content="hello", apply=True)
        assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "hello"

    def test_apply_creates_parent_dirs(self, tmp_path):
        from veni.tools.files import FileWriteTool
        tool = FileWriteTool(_make_bot(tmp_path))
        tool.execute(path="subdir/nested/out.txt", content="data", apply=True)
        assert (tmp_path / "subdir" / "nested" / "out.txt").exists()

    def test_missing_path_returns_error(self, tmp_path):
        from veni.tools.files import FileWriteTool
        tool = FileWriteTool(_make_bot(tmp_path))
        result = tool.execute(content="hello")
        assert "Error" in result

    def test_path_escape_blocked(self, tmp_path):
        from veni.tools.files import FileWriteTool
        tool = FileWriteTool(_make_bot(tmp_path))
        result = tool.execute(path="../../evil.txt", content="x", apply=True)
        assert "Error" in result


# ---------------------------------------------------------------------------
# Provider missing-key ValueError
# ---------------------------------------------------------------------------

class TestProviderKeyValidation:
    def _no_env(self, monkeypatch):
        """Strip all provider API key env vars."""
        for var in (
            "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
            "GROQ_API_KEY", "DEEPSEEK_API_KEY", "QWEN_API_KEY",
            "OPENROUTER_API_KEY", "MISTRAL_API_KEY", "PERPLEXITY_API_KEY",
        ):
            monkeypatch.delenv(var, raising=False)

    def _no_config(self, monkeypatch):
        """Patch config.get to return None for api_keys.*"""
        import veni.providers.factory as factory_mod
        original_config = factory_mod.config
        mock_cfg = MagicMock()
        mock_cfg.get.return_value = None
        monkeypatch.setattr(factory_mod, "config", mock_cfg)

    @pytest.mark.parametrize("provider", [
        "openai", "gemini", "anthropic", "groq", "deepseek",
    ])
    def test_raises_value_error_without_key(self, provider, monkeypatch):
        self._no_env(monkeypatch)
        self._no_config(monkeypatch)
        from veni.providers.factory import create_ai_client
        with pytest.raises(ValueError, match="API Key"):
            create_ai_client(provider=provider)

    def test_ollama_needs_no_key(self):
        from veni.providers.factory import create_ai_client
        client = create_ai_client(provider="ollama")
        assert client is not None

    def test_free_needs_no_key(self):
        from veni.providers.factory import create_ai_client
        client = create_ai_client(provider="free")
        assert client is not None
