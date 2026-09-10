#!/usr/bin/env python3
"""
scripts/update_changelog.py

Prepends a new release section to CHANGELOG.md from git log.

Usage:
    python scripts/update_changelog.py 1.3.0
    python scripts/update_changelog.py          # auto-increments patch version
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CHANGELOG = Path(__file__).parent.parent / "CHANGELOG.md"


def _last_tag() -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _current_version() -> str:
    """Read version from pyproject.toml."""
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "0.0.0"


def _next_patch(version: str) -> str:
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def _git_log_since(tag: str | None) -> list[str]:
    cmd = ["git", "log", "--oneline", "--no-merges"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    return lines


def main() -> None:
    new_version = sys.argv[1] if len(sys.argv) > 1 else _next_patch(_current_version())
    today = date.today().isoformat()
    last_tag = _last_tag()

    commits = _git_log_since(last_tag)
    if not commits:
        print("No commits since last tag — nothing to add.")
        return

    entry_lines = [f"## [{new_version}] — {today}\n"]
    for c in commits:
        entry_lines.append(f"- {c}\n")
    entry_lines.append("\n")
    new_entry = "".join(entry_lines)

    existing = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else ""
    CHANGELOG.write_text(new_entry + existing, encoding="utf-8")
    print(f"Prepended {len(commits)} commit(s) as version {new_version} to {CHANGELOG}")


if __name__ == "__main__":
    main()
