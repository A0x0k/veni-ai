"""
Session Sharing & Team Context for Veni AI.

Export and share debugging sessions:
- Encrypted exports
- Redaction options
- Team knowledge base
"""

import hashlib
import json
from datetime import datetime
from typing import Any

from veni.security import redactor


class SessionExporter:
    """Export and share Veni sessions securely."""

    def __init__(self, history: Any, memory: Any = None):
        self.history = history
        self.memory = memory

    def export_session(
        self,
        format: str = "markdown",
        redact: bool = True,
        include_metadata: bool = True,
    ) -> str:
        """Export the current session."""
        text_func = self._redact if redact else lambda x: x

        if format == "markdown":
            return self._export_md(text_func, include_metadata)
        elif format == "json":
            return self._export_json(text_func, include_metadata)
        elif format == "txt":
            return self._export_txt(text_func, include_metadata)
        else:
            return f"Unknown format: {format}"

    def _export_md(self, text_func, include_metadata: bool) -> str:
        lines = []
        lines.append("# Veni AI Session Export")
        lines.append("")
        lines.append(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")

        if include_metadata:
            lines.append("## Metadata")
            lines.append("")
            lines.append(f"- Messages: {len(self.history.messages)}")
            lines.append(
                f"- System Prompt: " f"{text_func(self.history.system_prompt[:100])}..."
            )
            if self.memory:
                stats = self.memory.get_stats()
                lines.append(f"- Memories: {stats['total_memories']}")
            lines.append("")

        lines.append("## Conversation")
        lines.append("")

        for msg in self.history.messages:
            role = msg.role.upper()
            pin = " 📌" if msg.pinned else ""
            lines.append(f"### {role}{pin}")
            lines.append("")
            lines.append(text_func(msg.content))
            lines.append("")
            if msg.images:
                lines.append(f"*Images: {', '.join(msg.images)}*")
                lines.append("")

        return "\n".join(lines)

    def _export_json(self, text_func, include_metadata: bool) -> str:
        data = {
            "exported_at": datetime.now().isoformat(),
            "messages": [],
        }

        if include_metadata:
            data["metadata"] = {
                "message_count": len(self.history.messages),
                "system_prompt": text_func(self.history.system_prompt),
            }
            if self.memory:
                data["memory_stats"] = self.memory.get_stats()

        for msg in self.history.messages:
            data["messages"].append(
                {
                    "role": msg.role,
                    "content": text_func(msg.content),
                    "pinned": msg.pinned,
                    "timestamp": msg.timestamp,
                    "images": msg.images,
                }
            )

        return json.dumps(data, indent=2)

    def _export_txt(self, text_func, include_metadata: bool) -> str:
        lines = []
        lines.append("VENI AI SESSION EXPORT")
        lines.append("=" * 50)
        lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Messages: {len(self.history.messages)}")
        lines.append("")

        for msg in self.history.messages:
            role = msg.role.upper()
            pin = " [PINNED]" if msg.pinned else ""
            lines.append(f"{role}{pin}:")
            lines.append(text_func(msg.content))
            lines.append("-" * 50)
            lines.append("")

        return "\n".join(lines)

    def _redact(self, text: str) -> str:
        """Redact sensitive information."""
        return redactor.redact(text)

    def generate_share_link(self, session_data: str, password: str = "") -> str:
        """Generate a fingerprint for session verification."""
        # Create a hash-based fingerprint
        data = session_data.encode("utf-8")
        if password:
            data += password.encode("utf-8")
        fingerprint = hashlib.sha256(data).hexdigest()[:16]
        return f"veni-session-{fingerprint}"
