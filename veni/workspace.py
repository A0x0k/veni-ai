"""
Workspace path resolution and safety utilities for Veni AI.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from veni.core import TerminalChatbot


def resolve_path(cwd: Path, path_str: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = cwd / p
    return p.resolve(strict=False)


def is_within_workspace(path: Path, workspace_root: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
        return resolved == workspace_root or _is_relative_to(resolved, workspace_root)
    except OSError:
        return False


def resolve_workspace_path(cwd: Path, workspace_root: Path, path_str: str) -> Path:
    path = resolve_path(cwd, path_str)
    if not is_within_workspace(path, workspace_root):
        raise ValueError(f"Path escapes workspace: {path}")
    return path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
