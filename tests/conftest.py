import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import pytest

# Ensure repo root is on sys.path for local imports in tests.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_TEMP_ROOT = Path.home() / ".codex" / "memories" / "veni_pytest_runtime"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["TMP"] = str(TEST_TEMP_ROOT)
os.environ["TEMP"] = str(TEST_TEMP_ROOT)
os.environ["TMPDIR"] = str(TEST_TEMP_ROOT)
tempfile.tempdir = str(TEST_TEMP_ROOT)


def _patch_pytest_tmpdir_cleanup_for_windows() -> None:
    """
    Work around WinError 448 during pytest tmpdir symlink cleanup.

    Some Windows environments treat tmpdir "current" links as untrusted mount points.
    Pytest resolves those links during session teardown and may crash the run.
    """
    try:
        import _pytest.pathlib as pytest_pathlib
        import _pytest.tmpdir as pytest_tmpdir
    except Exception:
        return

    def _wrap_cleanup(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        if getattr(func, "_veni_win448_patched", False):
            return func

        def _wrapped(path: Any) -> Any:
            try:
                return func(path)
            except OSError as exc:
                if getattr(exc, "winerror", None) in {5, 448}:
                    return None
                raise

        _wrapped._veni_win448_patched = True  # type: ignore[attr-defined]
        return _wrapped

    pytest_pathlib.cleanup_dead_symlinks = _wrap_cleanup(
        pytest_pathlib.cleanup_dead_symlinks
    )
    pytest_tmpdir.cleanup_dead_symlinks = _wrap_cleanup(pytest_tmpdir.cleanup_dead_symlinks)


_patch_pytest_tmpdir_cleanup_for_windows()


class _FakeClient:
    """Minimal fake AI client for testing."""

    def __init__(self):
        self.model = "fake"

    def chat(self, messages, stream=True, tools=None, **kwargs):
        if False:
            yield ""
        return iter(())


@pytest.fixture()
def bot():
    """Provide a TerminalChatbot with a fake client."""
    from veni.core import TerminalChatbot

    bot = TerminalChatbot(_FakeClient())
    # Disable approval gate in tests
    bot.approval_gate.enabled = False
    return bot


@pytest.fixture()
def tmp_path() -> Path:
    """Workspace-local tmp path that avoids Windows tempdir permission issues."""
    return Path(tempfile.mkdtemp(dir=TEST_TEMP_ROOT))
