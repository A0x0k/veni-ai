"""
Git Intelligence & PR Generation for Veni AI.

Advanced git operations:
- Smart commit messages
- PR descriptions with context
- Branch management
- Code review assistance
"""

import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PRDescription:
    """Generated PR description."""

    title: str
    body: str
    changes_summary: str
    files_changed: List[str]
    insertions: int
    deletions: int
    test_results: Optional[str] = None


@dataclass
class ReviewComment:
    """A code review comment."""

    file: str
    line: Optional[int]
    severity: str  # "suggestion", "warning", "issue"
    comment: str


class GitIntelligence:
    """Advanced git operations and intelligence."""

    def __init__(self, bot: Any, repo_path: Optional[str] = None):
        self.bot = bot
        self.repo_path = repo_path or str(bot.workspace_root)

    def _run(self, *args: str) -> Tuple[str, str, int]:
        """Run a git command."""
        cmd = ["git", "-C", self.repo_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode

    def get_diff(self, staged: bool = False) -> str:
        """Get git diff."""
        args = ["diff", "--cached"] if staged else ["diff"]
        out, _, _ = self._run(*args)
        return out

    def get_diff_stats(self) -> Dict[str, Any]:
        """Get diff statistics."""
        out, _, _ = self._run("diff", "--stat", "--cached")
        if not out.strip():
            out, _, _ = self._run("diff", "--stat")

        files = []
        insertions = 0
        deletions = 0

        for line in out.strip().splitlines():
            if "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) >= 2:
                files.append(parts[0].strip())
                stats = parts[-1].strip()
                insertions += stats.count("+")
                deletions += stats.count("-")

        return {
            "files_changed": len(files),
            "files": files,
            "insertions": insertions,
            "deletions": deletions,
        }

    def generate_commit_message(self) -> str:
        """Generate a smart commit message from diff."""
        diff = self.get_diff()
        if not diff.strip():
            diff = self.get_diff(staged=True)

        if not diff.strip():
            return "No changes to commit"

        # Analyze diff for intelligent message
        files = set()
        for line in diff.splitlines():
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                path = line.split("/", 1)[-1]
                files.add(path)

        # Categorize changes
        categories = {
            "feat": [],
            "fix": [],
            "docs": [],
            "refactor": [],
            "test": [],
            "chore": [],
        }

        for f in files:
            if f.endswith((".md", ".txt", ".rst")):
                categories["docs"].append(f)
            elif "test" in f.lower():
                categories["test"].append(f)
            elif f.startswith(("fix", "bug", "patch")):
                categories["fix"].append(f)
            else:
                categories["feat"].append(f)

        # Build message
        parts = []
        if categories["feat"]:
            parts.append(f"feat: add/modify {', '.join(categories['feat'][:3])}")
        if categories["fix"]:
            parts.append(f"fix: resolve issues in {', '.join(categories['fix'][:3])}")
        if categories["docs"]:
            parts.append("docs: update documentation")
        if categories["test"]:
            parts.append("test: add/update tests")
        if categories["refactor"]:
            parts.append("refactor: restructure code")

        return "\n\n".join(parts) if parts else "chore: miscellaneous changes"

    def create_branch(self, name: str, track: bool = True) -> bool:
        """Create and switch to a new branch."""
        args = ["checkout", "-b", name]
        if track:
            args.extend(["--track", f"origin/{name}"])
        _, err, code = self._run(*args)
        return code == 0

    def generate_pr_description(self) -> PRDescription:
        """Generate a comprehensive PR description."""
        stats = self.get_diff_stats()
        commit_msg = self.generate_commit_message()

        title = commit_msg.split("\n\n")[0]

        body_lines = [
            "## Summary",
            "",
            commit_msg,
            "",
            "## Changes",
            "",
            f"- **{stats['files_changed']}** file(s) changed",
            f"- **+{stats['insertions']}** insertions",
            f"- **-{stats['deletions']}** deletions",
            "",
            "## Files Modified",
            "",
        ]

        for f in stats["files"]:
            body_lines.append(f"- `{f}`")

        body_lines.extend(
            [
                "",
                "## Testing",
                "",
                "- [ ] Tests pass locally",
                "- [ ] No new warnings",
                "",
            ]
        )

        return PRDescription(
            title=title,
            body="\n".join(body_lines),
            changes_summary=commit_msg,
            files_changed=stats["files"],
            insertions=stats["insertions"],
            deletions=stats["deletions"],
        )

    def review_code(self, diff_content: str = "") -> List[ReviewComment]:
        """Review code changes and generate comments."""
        if not diff_content:
            diff_content = self.get_diff()

        comments = []

        for line in diff_content.splitlines():
            if line.startswith("+"):
                # Check for common issues in additions
                stripped = line[1:].strip()

                # Debug statements
                if "print(" in stripped or "console.log" in stripped:
                    comments.append(
                        ReviewComment(
                            file="diff",
                            severity="warning",
                            comment="Debug statement left in code",
                        )
                    )

                # Hardcoded values
                if any(
                    kw in stripped.lower()
                    for kw in ["password", "secret", "api_key", "token"]
                ):
                    comments.append(
                        ReviewComment(
                            file="diff",
                            severity="issue",
                            comment="Possible hardcoded credential",
                        )
                    )

                # TODO comments
                if "TODO" in stripped or "FIXME" in stripped:
                    comments.append(
                        ReviewComment(
                            file="diff",
                            severity="suggestion",
                            comment="Consider creating a ticket for this TODO",
                        )
                    )

        return comments

    def get_log(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent commit history."""
        out, _, code = self._run(
            "log",
            f"-{count}",
            "--format=%h|%s|%an|%ar",
        )
        if code != 0:
            return []

        commits = []
        for line in out.strip().splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    }
                )
        return commits

    def get_current_branch(self) -> str:
        """Get current branch name."""
        out, _, _ = self._run("branch", "--show-current")
        return out.strip()

    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files."""
        out, _, _ = self._run("status", "--porcelain")
        files = []
        for line in out.strip().splitlines():
            if line.startswith("?? "):
                files.append(line[3:])
        return files
