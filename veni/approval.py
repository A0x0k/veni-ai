"""
Approval gate middleware for Veni AI.

Provides a safety layer that intercepts tool executions
and requires user approval before running destructive operations.
Includes path traversal detection and encoded command detection.

SECURITY NOTICE
---------------
This approval gate is a best-effort usability guard, NOT a security boundary.
The blocklist approach cannot prevent all dangerous operations — for example,
a command like ``python -c "import shutil; shutil.rmtree('/')"`` would not be
caught. Do not rely on this gate to protect against malicious AI output or
untrusted tool inputs. Run Veni in a sandboxed environment (container, VM)
if you need a hard security boundary.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from rich.prompt import Confirm


# Risk levels for tool operations
class RiskLevel(Enum):
    SAFE = 0  # No side effects (read, search)
    LOW = 1  # Minor side effects (create file)
    MEDIUM = 2  # Modifiable side effects (edit file, shell)
    HIGH = 3  # Destructive potential (shell with rm, etc.)


# Tool risk classification
_TOOL_RISK: Dict[str, RiskLevel] = {
    "read_file": RiskLevel.SAFE,
    "web_search": RiskLevel.SAFE,
    "repo_map": RiskLevel.SAFE,
    "speak": RiskLevel.SAFE,
    "write_file": RiskLevel.SAFE,
    "shell_exec": RiskLevel.MEDIUM,
}

# Shell command patterns that escalate risk
_HIGH_RISK_PATTERNS = [
    "rm -r",
    "rm -f",
    "remove-item",
    "erase ",
    "del /f",
    "del /s",
    "rmdir /s",
    "sudo",
    "shutdown",
    "reboot",
    "format",
    "mkfs",
    "dd ",
]

_MUTATING_SHELL_PATTERNS = [
    "git apply",
    "git checkout",
    "git clean",
    "git commit",
    "git reset",
    "mv ",
    "cp ",
    "move ",
    "copy ",
    "mkdir ",
    "md ",
    "touch ",
    "echo ",
    ">",
    ">>",
]

# Encoded command patterns that attempt to bypass blocklists
_ENCODED_COMMAND_PATTERNS = [
    re.compile(r"base64\s*-d\s*['\"]?[A-Za-z0-9+/=]{20,}['\"]?", re.IGNORECASE),
    re.compile(r"from\s+base64\s+import.*b64decode", re.IGNORECASE),
    re.compile(r"bytes\.fromhex\(['\"][A-Fa-f0-9]{20,}['\"]\)", re.IGNORECASE),
    re.compile(r"import\s+os.*\.system\(", re.IGNORECASE),
    re.compile(r"import\s+subprocess.*\.run\(", re.IGNORECASE),
    re.compile(r"import\s+shutil.*\.rmtree\(", re.IGNORECASE),
]

# Paths that should never be written to without explicit HIGH risk warning
_SENSITIVE_SYSTEM_PATHS = [
    "/etc",
    "/usr",
    "/bin",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\ProgramData",
    "C:\\System32",
    "C:\\Users\\Default",
]


class ApprovalGate:
    """
    Safety middleware for tool execution.

    Intercepts tool calls and requires user approval
    for operations above a certain risk threshold.
    """

    def __init__(
        self,
        enabled: bool = True,
        max_risk: RiskLevel = RiskLevel.LOW,
        non_interactive: bool = False,
    ):
        self.enabled = enabled
        self.max_risk = max_risk
        self.non_interactive = non_interactive
        self._log: list[dict[str, Any]] = []

    def check(
        self,
        tool_name: str,
        args: Dict[str, Any],
        preview: str = "",
    ) -> bool:
        """
        Check if a tool execution requires approval.

        Returns True if execution should proceed, False if blocked.
        """
        if not self.enabled:
            return True

        risk = self._assess_risk(tool_name, args)
        self._log.append({"tool": tool_name, "risk": risk.value, "approved": None})

        # Auto-approve safe operations
        if risk.value <= self.max_risk.value:
            self._log[-1]["approved"] = True
            return True

        # In non-interactive mode, block risky operations
        if self.non_interactive:
            self._log[-1]["approved"] = False
            return False

        # Ask user for approval
        return self._prompt_approval(tool_name, args, risk, preview)

    def _assess_risk(self, tool_name: str, args: Dict[str, Any]) -> RiskLevel:
        """Assess the risk level of a tool execution."""
        base_risk = _TOOL_RISK.get(tool_name, RiskLevel.MEDIUM)

        if tool_name == "write_file":
            risk = RiskLevel.MEDIUM if args.get("apply") is True else RiskLevel.SAFE
            path = args.get("path", "")
            if path and self._check_path_traversal(path):
                return RiskLevel.HIGH
            if path and self._check_sensitive_path(path):
                return RiskLevel.HIGH
            return risk

        # Escalate shell commands with dangerous patterns
        if tool_name == "shell_exec":
            command = args.get("command", "")
            if self._check_encoded_command(command):
                return RiskLevel.HIGH
            cmd_lower = command.lower()
            for pattern in _HIGH_RISK_PATTERNS:
                if pattern in cmd_lower:
                    return RiskLevel.HIGH
            if any(pattern in cmd_lower for pattern in _MUTATING_SHELL_PATTERNS):
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM

        if tool_name in ("read_file",):
            path = args.get("path", "")
            if path and self._check_path_traversal(path):
                return RiskLevel.HIGH

        return base_risk

    def _check_path_traversal(self, path: str) -> bool:
        """Detect path traversal attempts (e.g., '../../../etc/passwd')."""
        normalized = Path(path).as_posix()
        traversal_count = normalized.count("../")
        if traversal_count > 1:
            return True
        if ".." in normalized.split("/"):
            return True
        return False

    def _check_sensitive_path(self, path: str) -> bool:
        """Detect writes to known system-sensitive locations."""
        normalized = Path(path).resolve(strict=False).as_posix().lower()
        for sensitive in _SENSITIVE_SYSTEM_PATHS:
            if normalized.startswith(sensitive.lower()):
                return True
        return False

    @staticmethod
    def _check_encoded_command(command: str) -> bool:
        """Detect encoded/obfuscated commands attempting to bypass blocklists."""
        for pattern in _ENCODED_COMMAND_PATTERNS:
            if pattern.search(command):
                return True
        return False

    def _prompt_approval(
        self,
        tool_name: str,
        args: Dict[str, Any],
        risk: RiskLevel,
        preview: str = "",
    ) -> bool:
        """Ask the user to approve a tool execution."""
        from rich.panel import Panel
        from rich.text import Text

        from veni.commands.base import console

        risk_colors = {
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
        }
        risk_labels = {
            RiskLevel.MEDIUM: "⚠️  MEDIUM RISK",
            RiskLevel.HIGH: "🚨 HIGH RISK",
        }

        # Build summary
        summary = f"Tool: {tool_name}"
        if "command" in args:
            summary += f"\nCommand: {args['command']}"
        elif "path" in args:
            summary += f"\nPath: {args['path']}"

        if preview:
            summary += f"\n\n{preview}"

        panel = Panel(
            Text.assemble(
                (
                    f"{risk_labels.get(risk, 'UNKNOWN')} TOOL EXECUTION\n",
                    risk_colors.get(risk, "white"),
                ),
                (summary, "white"),
                "\n\nDo you want to proceed?",
            ),
            border_style=risk_colors.get(risk, "white"),
            title=" Approval Required ",
        )
        console.print(panel)

        try:
            approved = Confirm.ask("Proceed?", default=False)
            self._log[-1]["approved"] = approved
            return approved
        except (KeyboardInterrupt, EOFError):
            self._log[-1]["approved"] = False
            return False

    def get_log(self) -> list[dict[str, Any]]:
        """Return the approval log for this session."""
        return list(self._log)

    def reset(self):
        """Clear the approval log."""
        self._log.clear()
