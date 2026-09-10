"""
Conversational Debugging Mode for Veni AI.

When something breaks, Veni becomes a debug partner:
- Analyzes errors
- Suggests root causes
- Proposes fixes
- Validates solutions
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DebugSession:
    """An active debugging session."""

    error_type: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: str = ""
    proposed_fix: str = ""
    attempts: int = 0
    resolved: bool = False
    context: str = ""  # Surrounding code


@dataclass
class DebugPattern:
    """A recognized error pattern."""

    name: str
    regex: str
    severity: str  # "error", "warning", "info"
    explanation: str
    fix_suggestion: str


# Common error patterns
ERROR_PATTERNS = [
    DebugPattern(
        name="missing_import",
        regex=r"ModuleNotFoundError: No module named '(.+?)'",
        severity="error",
        explanation="A required module is not installed.",
        fix_suggestion="Install with: pip install {0}",
    ),
    DebugPattern(
        name="attribute_error",
        regex=r"AttributeError: '(.+?)' object has no attribute '(.+?)'",
        severity="error",
        explanation="Trying to access an attribute that doesn't exist.",
        fix_suggestion=(
            "Check if the object is the correct type. "
            "Maybe you meant a different method/attribute?"
        ),
    ),
    DebugPattern(
        name="type_error",
        regex=r"TypeError: (.+)",
        severity="error",
        explanation="An operation was applied to the wrong type.",
        fix_suggestion="Check the types of your variables. Use isinstance() if needed.",
    ),
    DebugPattern(
        name="key_error",
        regex=r"KeyError: '(.+?)'",
        severity="error",
        explanation="Dictionary key doesn't exist.",
        fix_suggestion="Use dict.get('{0}') or check if key exists with 'in' operator.",
    ),
    DebugPattern(
        name="index_error",
        regex=r"IndexError: (list index out of range|.*)",
        severity="error",
        explanation="Accessing an index that doesn't exist.",
        fix_suggestion="Check the list length before indexing, or use a safer access pattern.",
    ),
    DebugPattern(
        name="syntax_error",
        regex=r"SyntaxError: (.+)",
        severity="error",
        explanation="Python syntax error.",
        fix_suggestion="Check the syntax at the reported line. Common issues: missing colons, unmatched brackets.",
    ),
    DebugPattern(
        name="import_error",
        regex=r"ImportError: (?:cannot import name '(.+?)' from '(.+?)'|.+)",
        severity="error",
        explanation="Import failed.",
        fix_suggestion="Check the import path and spelling. The module or name may have changed.",
    ),
    DebugPattern(
        name="file_not_found",
        regex=r"FileNotFoundError: \[Errno \d+\] (.+): '(.+?)'",
        severity="error",
        explanation="File doesn't exist at the specified path.",
        fix_suggestion="Check the file path. Use os.path.exists() or Path.exists() before accessing.",
    ),
    DebugPattern(
        name="value_error",
        regex=r"ValueError: (.+)",
        severity="error",
        explanation="Value is inappropriate for the operation.",
        fix_suggestion="Validate the input value before the operation.",
    ),
    DebugPattern(
        name="test_assertion",
        regex=r"AssertionError: (.*)",
        severity="error",
        explanation="A test assertion failed.",
        fix_suggestion="Check what the test expects vs what's actually happening.",
    ),
]


class DebugMode:
    """
    Conversational debugging engine.

    Usage:
        debug = DebugMode(bot)
        result = debug.analyze(error_output)
        if result.suggestion:
            debug.apply_fix(result.suggestion)
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._sessions: List[DebugSession] = []
        self._active_session: Optional[DebugSession] = None

    def analyze(self, error_output: str) -> DebugSession:
        """Analyze error output and suggest fixes."""
        session = DebugSession(
            error_type="unknown",
            error_message=error_output[:500],
        )

        # Try to match known patterns
        for pattern in ERROR_PATTERNS:
            match = re.search(pattern.regex, error_output, re.DOTALL)
            if match:
                session.error_type = pattern.name
                groups = match.groups()
                session.error_message = pattern.explanation
                session.proposed_fix = pattern.fix_suggestion.format(*groups)

                # Extract file and line if available
                file_match = re.search(r'File "([^"]+)", line (\d+)', error_output)
                if file_match:
                    session.file_path = file_match.group(1)
                    session.line_number = int(file_match.group(2))

                # Extract stack trace
                trace_match = re.search(
                    r"Traceback \(most recent call last\):(.+)",
                    error_output,
                    re.DOTALL,
                )
                if trace_match:
                    session.stack_trace = trace_match.group(1).strip()

                break

        # If no pattern matched, try generic analysis
        if session.error_type == "unknown":
            session = self._generic_analysis(error_output, session)

        self._active_session = session
        self._sessions.append(session)
        return session

    def get_conversational_response(self, error_output: str) -> str:
        """Generate a conversational debugging response."""
        session = self.analyze(error_output)

        parts = []

        # Acknowledge the error
        parts.append(f"I found the issue: **{session.error_type}**")
        parts.append("")

        # Explain
        parts.append(session.error_message)
        parts.append("")

        # Suggest fix
        if session.proposed_fix:
            parts.append(f"**Suggested fix:** {session.proposed_fix}")
            parts.append("")

        # Offer to apply
        if session.file_path:
            parts.append(f"📁 File: `{session.file_path}`")
            if session.line_number:
                parts.append(f"📍 Line: {session.line_number}")
            parts.append("")
            parts.append("Want me to fix it?")

        return "\n".join(parts)

    def apply_fix(self, fix_description: str) -> str:
        """Attempt to apply a fix."""
        if not self._active_session:
            return "No active debug session."

        session = self._active_session
        session.attempts += 1

        # For now, suggest the fix to the user
        return (
            f"Here's what I'd change:\n\n"
            f"Based on: {fix_description}\n\n"
            f"I'll need you to confirm the fix before I apply it. "
            f"Use `/edit` to apply changes to specific files."
        )

    def run_tests_and_analyze(self) -> Optional[DebugSession]:
        """Run tests and analyze failures."""
        import subprocess

        try:
            result = subprocess.run(
                ["pytest", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.bot.workspace_root),
            )

            if result.returncode == 0:
                return None  # All tests pass

            # Analyze failures
            return self.analyze(result.stderr or result.stdout)

        except FileNotFoundError:
            return None  # pytest not installed
        except subprocess.TimeoutExpired:
            return self.analyze("Error: Tests timed out after 60 seconds")
        except Exception as e:
            return self.analyze(f"Error running tests: {e}")

    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get debug session history."""
        return [
            {
                "error_type": s.error_type,
                "message": s.error_message[:100],
                "file": s.file_path,
                "attempts": s.attempts,
                "resolved": s.resolved,
            }
            for s in self._sessions
        ]

    def _generic_analysis(
        self, error_output: str, session: DebugSession
    ) -> DebugSession:
        """Fallback generic analysis."""
        # Try to extract error type
        error_match = re.search(r"(\w+Error|\w+Exception):(.+)", error_output)
        if error_match:
            session.error_type = error_match.group(1)
            session.error_message = error_match.group(2).strip()[:200]

        # Try to find file reference
        file_match = re.search(r'File "([^"]+)"', error_output)
        if file_match:
            session.file_path = file_match.group(1)

        session.proposed_fix = (
            "I couldn't identify a specific pattern. "
            "Let me analyze the error more carefully. "
            "Can you share the relevant code?"
        )

        return session
