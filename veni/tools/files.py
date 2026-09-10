"""
File system tools for Veni AI.
"""

from typing import Any, Dict

from veni.tools.base import AITool


class FileReadTool(AITool):
    """Tool for reading file contents."""

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the content of a file from the local file system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the file to read.",
                }
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> str:
        """Read file and return content."""
        path = kwargs.get("path")
        if not isinstance(path, str) or not path.strip():
            return "Error: Missing required string argument 'path'."
        try:
            file_path = self.bot.resolve_workspace_path(path)
        except ValueError as exc:
            return f"Error: {exc}"

        if not file_path.exists():
            return f"Error: File not found at {path}"
        if not file_path.is_file():
            return f"Error: Path is not a file: {path}"

        try:
            content = file_path.read_text(encoding="utf-8")
            return f"Content of {path}:\n\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"


class FileWriteTool(AITool):
    """Tool for creating and writing files."""

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Create a new file or overwrite an existing file with given content. "
            "Use this to generate code, configs, docs, or any text-based file."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path where to write the file.",
                },
                "content": {
                    "type": "string",
                    "description": "The full content to write to the file.",
                },
                "apply": {
                    "type": "boolean",
                    "description": (
                        "When false or omitted, only preview the diff. "
                        "Set true to apply after approval."
                    ),
                },
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs: Any) -> str:
        """Preview or apply a file write and return a diff preview."""
        path = kwargs.get("path")
        content = kwargs.get("content")
        apply = kwargs.get("apply", False) is True
        if not isinstance(path, str) or not path.strip():
            return "Error: Missing required string argument 'path'."
        if not isinstance(content, str):
            return "Error: Missing required string argument 'content'."
        try:
            file_path = self.bot.resolve_workspace_path(path)
        except ValueError as exc:
            return f"Error: {exc}"

        preview = self.build_preview(path, content)
        if not apply:
            return preview

        try:
            # Ensure parent directories exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            return f"Error writing file: {e}"

        return f"{preview}\n\nApplied changes to {path}."

    def build_preview(self, path: str, content: str) -> str:
        """Build a preview for a proposed file write without mutating disk."""
        try:
            file_path = self.bot.resolve_workspace_path(path)
        except ValueError as exc:
            return f"Error: {exc}"

        existed = file_path.exists()
        old_content = ""

        if existed:
            try:
                old_content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                return f"Error reading existing file: {e}"

        action = "create" if not existed else "modify"
        diff = self._build_diff(path, old_content, content)
        if diff:
            return (
                f"Preview {action} file: {path}\n"
                "No changes have been written yet.\n\n"
                f"{diff}"
            )
        return f"Preview {action} file: {path} (no changes)"

    def _build_diff(self, path: str, old_content: str, new_content: str) -> str:
        """Generate a unified diff using shared utility."""
        if not old_content:
            # New file — show full content as additions
            lines = new_content.splitlines(keepends=True)
            added = "".join(f"+{line}" for line in lines)
            return f"--- /dev/null\n+++ {path}\n{added}"

        from veni.tools.diff import make_diff

        return make_diff(old_content, new_content, filepath=path)
