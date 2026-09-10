"""
Proactive Error Detection & Prevention for Veni AI.

Monitors file changes, test results, and code patterns
to catch problems before they compound.
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Issue:
    """A detected issue with metadata."""

    severity: Severity
    category: str  # "syntax", "import", "security", "performance", "style"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


class ErrorDetector:
    """
    Proactively detects potential issues in code.

    Checks:
    - Syntax errors
    - Missing imports
    - Unused imports
    - Common security issues
    - Performance anti-patterns
    - Style inconsistencies
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._issues: List[Issue] = []
        self._baseline_files: Set[str] = set()

    def scan_file(self, file_path: Path) -> List[Issue]:
        """Scan a single file for issues."""
        issues = []
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return issues

        ext = file_path.suffix.lower()

        # Language-specific checks
        if ext == ".py":
            issues.extend(self._check_python(content, str(file_path)))
        elif ext in (".js", ".ts", ".tsx", ".jsx"):
            issues.extend(self._check_javascript(content, str(file_path)))
        elif ext in (".html", ".htm"):
            issues.extend(self._check_html(content, str(file_path)))

        # Universal checks
        issues.extend(self._check_security(content, str(file_path)))
        issues.extend(self._check_performance(content, str(file_path)))

        self._issues.extend(issues)
        return issues

    def scan_workspace(self) -> List[Issue]:
        """Scan all code files in workspace."""
        issues = []
        extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".html",
            ".htm",
            ".json",
            ".yaml",
            ".yml",
        }

        for ext in extensions:
            for file_path in self.bot.workspace_root.rglob(f"*{ext}"):
                # Skip common non-code dirs
                if any(
                    skip in file_path.parts
                    for skip in [
                        "node_modules",
                        "venv",
                        ".venv",
                        "__pycache__",
                        ".git",
                        "dist",
                        "build",
                    ]
                ):
                    continue
                issues.extend(self.scan_file(file_path))

        return issues

    def analyze_test_results(self, test_output: str) -> List[Issue]:
        """Parse test output and create issues."""
        issues = []

        # Common test failure patterns
        patterns = [
            (
                r"E\s+.*Error: (.+)",
                Severity.ERROR,
                "test_error",
                "Test error: {0}",
            ),
            (
                r"F\s+.*FAILED\s*(.+)",
                Severity.ERROR,
                "test_failed",
                "Test failed: {0}",
            ),
            (
                r"ModuleNotFoundError: No module named '(.+)'",
                Severity.ERROR,
                "missing_module",
                "Missing module: {0}. Run: pip install {0}",
            ),
            (
                r"ImportError: cannot import name '(.+)'",
                Severity.ERROR,
                "import_error",
                "Import error: cannot import {0}",
            ),
        ]

        for pattern, severity, category, msg_template in patterns:
            for match in re.finditer(pattern, test_output):
                message = msg_template.format(match.group(1))
                issues.append(
                    Issue(
                        severity=severity,
                        category=category,
                        message=message,
                        suggestion=f"Check test output for details: {match.group(0)[:100]}",
                    )
                )

        self._issues.extend(issues)
        return issues

    def get_issues(
        self,
        severity: Optional[Severity] = None,
        category: Optional[str] = None,
        unresolved_only: bool = True,
    ) -> List[Issue]:
        """Get issues with optional filters."""
        issues = self._issues

        if unresolved_only:
            issues = [i for i in issues if not i.resolved]

        if severity:
            issues = [i for i in issues if i.severity == severity]

        if category:
            issues = [i for i in issues if i.category == category]

        return issues

    def resolve_issue(self, index: int) -> bool:
        """Mark an issue as resolved."""
        if 0 <= index < len(self._issues):
            self._issues[index].resolved = True
            return True
        return False

    def get_summary(self) -> Dict[str, int]:
        """Get issue summary by severity."""
        summary = {s.value: 0 for s in Severity}
        for issue in self._issues:
            if not issue.resolved:
                summary[issue.severity.value] += 1
        return summary

    def clear(self):
        """Clear all issues."""
        self._issues.clear()

    # --- Language-specific checkers ---

    def _check_python(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.splitlines()

        imports = set()
        used_names: Set[str] = set()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                match = re.match(r"(?:import|from)\s+(\w+)", stripped)
                if match:
                    imports.add(match.group(1))

            # Track usage
            for imp in imports:
                if imp in stripped and not stripped.startswith(("import", "from", "#")):
                    used_names.add(imp)

            # Common issues
            if stripped.endswith(" "):
                issues.append(
                    Issue(
                        severity=Severity.INFO,
                        category="style",
                        message="Trailing whitespace",
                        file_path=file_path,
                        line_number=i,
                        suggestion="Remove trailing whitespace",
                    )
                )

            if "\t" in line and not stripped.startswith("#"):
                issues.append(
                    Issue(
                        severity=Severity.WARNING,
                        category="style",
                        message="Tab character found (use spaces)",
                        file_path=file_path,
                        line_number=i,
                        suggestion="Replace tabs with 4 spaces",
                    )
                )

        # Unused imports
        for imp in imports:
            if imp not in used_names:
                issues.append(
                    Issue(
                        severity=Severity.WARNING,
                        category="import",
                        message=f"Unused import: {imp}",
                        file_path=file_path,
                        suggestion=f"Remove 'import {imp}' or use it",
                    )
                )

        # Missing __init__ in packages
        if (
            "__init__.py" not in file_path
            and (Path(file_path).parent / "__init__.py").exists() is False
        ):
            parent = Path(file_path).parent
            if any(parent.rglob("*.py")) and parent != self.bot.workspace_root:
                issues.append(
                    Issue(
                        severity=Severity.INFO,
                        category="import",
                        message=f"Missing __init__.py in {parent.name}/",
                        file_path=file_path,
                        suggestion="Create __init__.py to make this a package",
                    )
                )

        return issues

    def _check_javascript(self, content: str, file_path: str) -> List[Issue]:
        issues = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # console.log in production
            if "console.log" in stripped and not stripped.startswith("//"):
                issues.append(
                    Issue(
                        severity=Severity.INFO,
                        category="performance",
                        message="console.log found",
                        file_path=file_path,
                        line_number=i,
                        suggestion="Remove console.log before production",
                    )
                )

            # var instead of let/const
            if re.match(r"\bvar\s+", stripped):
                issues.append(
                    Issue(
                        severity=Severity.WARNING,
                        category="style",
                        message="Use 'let' or 'const' instead of 'var'",
                        file_path=file_path,
                        line_number=i,
                        suggestion="Replace 'var' with 'let' or 'const'",
                    )
                )

        return issues

    def _check_html(self, content: str, file_path: str) -> List[Issue]:
        issues = []

        # Unclosed tags (basic check)
        open_tags = re.findall(r"<(\w+)[^>]*[^/]>", content)
        close_tags = re.findall(r"</(\w+)>", content)

        for tag in open_tags:
            if open_tags.count(tag) > close_tags.count(tag):
                issues.append(
                    Issue(
                        severity=Severity.WARNING,
                        category="syntax",
                        message=f"Possibly unclosed <{tag}> tag",
                        file_path=file_path,
                        suggestion=f"Add </{tag}> to close the tag",
                    )
                )

        return issues

    def _check_security(self, content: str, file_path: str) -> List[Issue]:
        issues = []

        # Hardcoded secrets
        secret_patterns = [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token"),
        ]

        for pattern, message in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(
                    Issue(
                        severity=Severity.CRITICAL,
                        category="security",
                        message=message,
                        file_path=file_path,
                        suggestion="Use environment variables or a config file",
                    )
                )

        # SQL injection risk
        if re.search(r"execute\s*\(\s*f['\"]", content) or re.search(
            r"raw\s*\(\s*f['\"]", content
        ):
            issues.append(
                Issue(
                    severity=Severity.ERROR,
                    category="security",
                    message="Possible SQL injection with f-string",
                    file_path=file_path,
                    suggestion="Use parameterized queries instead",
                )
            )

        # eval/exec usage
        if re.search(r"\beval\s*\(", content) or re.search(r"\bexec\s*\(", content):
            issues.append(
                Issue(
                    severity=Severity.ERROR,
                    category="security",
                    message="eval/exec found — potential code injection",
                    file_path=file_path,
                    suggestion="Avoid eval/exec; use safer alternatives",
                )
            )

        return issues

    def _check_performance(self, content: str, file_path: str) -> List[Issue]:
        issues = []

        # Python: importing inside functions
        if file_path.endswith(".py"):
            if re.search(r"def\s+\w+.*?:\n\s+import\s", content, re.DOTALL):
                issues.append(
                    Issue(
                        severity=Severity.INFO,
                        category="performance",
                        message="Import inside function",
                        file_path=file_path,
                        suggestion="Move imports to module level for performance",
                    )
                )

        return issues


# --- Auto-Detection for Intelligence ---

INTELLIGENCE_PATTERNS = {
    "persona_suggestions": [
        (r"(teach|learn|explain|understand|how does|what is)", "teacher"),
        (r"(analyze|data|trend|pattern|metric)", "analyst"),
        (r"(brainstorm|creative|innovate|imagine|idea)", "creative"),
        (r"(career|advice|should i|decision|recommend)", "advisor"),
        (r"(review|critique|flaw|feedback|improve)", "critic"),
        (r"(translate|rewrite|rephrase|for beginners)", "translator"),
        (r"(strategy|long.term|competitive|roadmap|plan)", "strategist"),
        (r"(motivat|habit|goal|get better|improve my)", "coach"),
        (r"(evidence|hypothesis|experiment|research|prove)", "scientist"),
        (r"(news|current event|summary|report|happen)", "journalist"),
        (r"(meaning|ethics|why|should|purpose|nature of)", "philosopher"),
    ],
    "mode_suggestions": [
        (r"(quick|brief|short|tl.dr|summarize)", "brief"),
        (r"(in detail|deep dive|comprehensive)", "detailed"),
        (r"(guide me|help me think|what do you think)", "socratic"),
        (r"(how to|steps|walk me through|tutorial)", "step_by_step"),
        (r"(vs|versus|compare|which is better|difference)", "compare"),
        (r"(argue|both sides|controversial|debate)", "debate"),
        (r"(brainstorm|imagine|what if|creative)", "creative"),
        (r"(framework|template|table|structure|plan)", "structured"),
        (r"(paper|thesis|academic|citation|literature)", "academic"),
    ],
}


def suggest_intelligence(query: str) -> Dict[str, Optional[str]]:
    """Suggest persona and mode based on user query."""
    query_lower = query.lower()
    result: Dict[str, Optional[str]] = {"persona": None, "mode": None}

    for pattern, persona_name in INTELLIGENCE_PATTERNS["persona_suggestions"]:
        if re.search(pattern, query_lower):
            result["persona"] = persona_name
            break

    for pattern, mode_name in INTELLIGENCE_PATTERNS["mode_suggestions"]:
        if re.search(pattern, query_lower):
            result["mode"] = mode_name
            break

    return result
