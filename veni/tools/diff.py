"""
Shared diff generation utility for Veni AI.

Used by EditCommand and FileWriteTool to produce consistent diffs.
"""

import difflib
from typing import List


def make_diff(
    old_content: str,
    new_content: str,
    filepath: str = "file",
    context_lines: int = 3,
) -> str:
    """
    Generate a unified diff between old and new content.

    Args:
        old_content: Original file content.
        new_content: New file content.
        filepath: Name of the file for diff header.
        context_lines: Number of context lines around changes.

    Returns:
        Unified diff string, or empty string if no changes.
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        n=context_lines,
    )

    return "".join(diff)


def make_diff_from_lists(
    old_lines: List[str],
    new_lines: List[str],
    filepath: str = "file",
    context_lines: int = 3,
) -> str:
    """
    Generate a unified diff from pre-split line lists.

    Args:
        old_lines: List of original lines (without newlines is fine).
        new_lines: List of new lines.
        filepath: Name of the file for diff header.
        context_lines: Number of context lines around changes.

    Returns:
        Unified diff string, or empty string if no changes.
    """
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        n=context_lines,
    )

    return "".join(diff)
