"""
Shell execution tool for Veni AI.

Allows the AI to run arbitrary shell commands safely with:
- Working directory control (bot.cwd)
- Output truncation for long results
- Timeout protection
- Blocked command allowlist/denylist

SECURITY NOTICE
---------------
The command blocklist (_BLOCKED_COMMANDS) is a best-effort guard against
obvious destructive patterns. It cannot prevent all dangerous commands —
for example, indirect invocations via Python, PowerShell scripts, or
encoded payloads will not be caught. Do not treat this as a hard security
boundary. Run Veni in a sandboxed environment (container, VM) if you need
strong isolation.
"""

import platform
import re
import shlex
import subprocess
from typing import Any, Dict, List, Sequence

from veni.tools.base import AITool

# Token-based blocked command patterns
_BLOCKED_COMMANDS = {
    "rm", "dd", "mkfs", "format", "sudo", "remove-item", "del", "erase", "rmdir",
    "apt-get", "apt", "brew", "pip", "npm", "yarn", "shutdown", "reboot"
}

_DANGEROUS_FLAGS = {"-rf", "-fr", "-f"}

_BLOCKED_LITERAL_SNIPPETS = [
    ":(){:|:&};:",  # Fork bomb
]


# Token-sequence patterns that are always blocked regardless of platform.
# Each entry is a tuple of consecutive tokens that must appear in order.
_BLOCKED_TOKEN_PATTERNS: list[tuple[str, ...]] = [
    # Unix destructive
    ("rm", "-rf"), ("rm", "-fr"), ("rm", "-r"), ("rm", "-f"),
    # PowerShell destructive
    ("remove-item", "-recurse"), ("remove-item", "-r"),
    ("ri", "-recurse"), ("ri", "-r"),
    ("del", "/s"), ("del", "/f"),
    ("rmdir", "/s"),
    # Disk wipe
    ("dd",), ("format", "c:"), ("format", "d:"),
]
# Platform-specific shell — detected at import time so tests can mock it
def _detect_shell() -> tuple[str, list[str]]:
    """Return (shell_executable, args_prefix) for the current platform."""
    if platform.system() == "Windows":
        import shutil
        for candidate in ("pwsh", "powershell", "powershell.exe"):
            if shutil.which(candidate):
                return candidate, ["-NoLogo", "-NoProfile", "-Command"]
        return "cmd.exe", ["/c"]
    return "/bin/bash", ["-c"]

_SHELL, _SHELL_ARGS = _detect_shell()

# Maximum output length before truncation
_MAX_OUTPUT = 8000


class ShellExecTool(AITool):
    """Tool for executing shell commands safely."""

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "shell_exec"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command in the current working directory. "
            "Use this to run builds, tests, install dependencies, "
            "search files, and diagnose issues. "
            "Output is automatically truncated if very long."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "The shell command to execute. "
                        "Examples: 'ls -la', 'grep -r \"error\" .', 'pytest tests/'"
                    ),
                }
            },
            "required": ["command"],
        }

    def execute(self, **kwargs: Any) -> str:
        """Execute a shell command and return the output."""
        command_raw = kwargs.get("command")
        if not isinstance(command_raw, str) or not command_raw.strip():
            return "Error: Missing required string argument 'command'."
        command = command_raw
        # Safety: check blocked commands
        blocked = self._check_blocked(command)
        if blocked:
            return (
                f"Error: Command blocked for safety: '{blocked}'.\n"
                f"Dangerous commands (rm -rf, dd, fork bombs, etc.) are not allowed. "
                f"If you need to install dependencies or mutate the system, ask the user first."
            )

        cwd = str(self.bot.cwd)
        try:
            result = subprocess.run(
                [_SHELL] + _SHELL_ARGS + [command],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n--- stderr ---\n"
                output += result.stderr

            if not output.strip():
                output = "(command completed with no output)"

            # Truncate if too long
            if len(output) > _MAX_OUTPUT:
                output = (
                    output[:_MAX_OUTPUT]
                    + f"\n\n... [output truncated, {len(output) - _MAX_OUTPUT} more characters] ..."
                    + "\nTip: pipe to 'head -50' or use more specific filters."
                )

            exit_info = f"Exit code: {result.returncode}"
            return f"{exit_info}\n{output}".strip()

        except subprocess.TimeoutExpired:
            return (
                "Error: Command timed out after 30 seconds.\n"
                "Tip: the command may be running an infinite loop or waiting for input. "
                "Try a simpler command or add flags to make it non-interactive."
            )
        except FileNotFoundError:
            return f"Error: Command not found: '{command.split()[0]}'"
        except Exception as e:
            return f"Error executing command: {e}"

    def _check_blocked(self, command: str) -> str:
        """Return blocked reason if found, empty string otherwise."""
        cmd_lower = command.lower()
        for snippet in _BLOCKED_LITERAL_SNIPPETS:
            if snippet in cmd_lower:
                return snippet

        tokens = self._tokenize_command(command)
        for pattern in _BLOCKED_TOKEN_PATTERNS:
            if self._contains_token_pattern(tokens, pattern):
                return " ".join(pattern)
        return ""

    @staticmethod
    def _tokenize_command(command: str) -> List[str]:
        return [
            tok.lower()
            for tok in re.findall(
                r"[A-Za-z0-9_./:\\-]+|&&|\|\||[|&;><(){}]",
                command,
            )
        ]

    @staticmethod
    def _contains_token_pattern(tokens: Sequence[str], pattern: Sequence[str]) -> bool:
        if not pattern or len(pattern) > len(tokens):
            return False
        plen = len(pattern)
        for i in range(len(tokens) - plen + 1):
            if list(tokens[i : i + plen]) == list(pattern):
                return True
        return False