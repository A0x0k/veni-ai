"""
Chat history management for Veni AI.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import tiktoken
except ImportError:
    tiktoken = None

from veni.logger import logger

_ENCODER_CACHE: Dict[str, Any] = {}
_DEFAULT_TIKTOKEN_MODEL = "gpt-4o"
_DEFAULT_IMAGE_TOKEN_COST = 500


def _load_encoding(model_key: str) -> Optional[Any]:
    if not tiktoken:
        return None
    try:
        return tiktoken.encoding_for_model(model_key)
    except Exception:
        pass
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception as exc:
        logger.debug("tiktoken encoding load failed (%s); falling back", exc)
        return None


def _estimate_text_tokens(text: str, model: Optional[str]) -> int:
    if not text:
        return 0
    model_key = model or _DEFAULT_TIKTOKEN_MODEL
    encoder = _ENCODER_CACHE.get(model_key)
    if not encoder:
        encoder = _load_encoding(model_key)
        if encoder:
            _ENCODER_CACHE[model_key] = encoder
    if encoder:
        try:
            return len(encoder.encode(text))
        except Exception as exc:
            logger.debug("tiktoken encode failed (%s); falling back", exc)
    return max(1, len(text) // 4)


class ChatMessage:
    """Represents a single message in the conversation."""

    def __init__(
        self,
        role: str,
        content: str,
        images: List[str] = None,
        pinned: bool = False,
        timestamp: Optional[float] = None,
    ):
        self.role = role
        self.content = content
        self.images = images or []
        self.pinned = pinned
        self.timestamp = time.time() if timestamp is None else timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "images": self.images,
            "pinned": self.pinned,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            images=data.get("images", []),
            pinned=data.get("pinned", False),
            timestamp=data.get("timestamp"),
        )

    def to_chat_dict(self) -> Dict[str, Any]:
        role = self.role
        content = self.content
        if role == "tool":
            role = "user"
            content = f"[Tool Output]\n{content}"
        msg = {"role": role, "content": content}
        if self.images:
            msg["images"] = self.images
        return msg

    def estimate_tokens(self, model: Optional[str] = None) -> int:
        """Estimate token usage for the message, optionally using tiktoken."""
        text_tokens = _estimate_text_tokens(self.content, model)
        image_tokens = len(self.images) * _DEFAULT_IMAGE_TOKEN_COST
        return text_tokens + image_tokens + 10


class ChatHistory:
    """Manages the conversation history and persistence."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".veni-chatbot" / "history"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.messages: List[ChatMessage] = []
        self.system_prompt = "You are Veni, a professional and helpful terminal-based AI assistant. You can use search and edit files. Keep responses concise and focused."
        # Accumulated summary of dropped messages
        self._context_summary: str = ""
        self._summarized_count: int = 0

    def add_message(self, role: str, content: str, images: List[str] = None):
        self.messages.append(ChatMessage(role, content, images))

    def add_tool_message(self, content: str):
        self.messages.append(ChatMessage("tool", content))

    def clear(self):
        self.messages = []

    def pin_message(self, index_from_end: int = 1) -> Optional[ChatMessage]:
        if not self.messages:
            return None
        idx = len(self.messages) - index_from_end
        if idx < 0 or idx >= len(self.messages):
            return None
        self.messages[idx].pinned = True
        return self.messages[idx]

    def unpin_message(self, index_from_end: int = 1) -> Optional[ChatMessage]:
        if not self.messages:
            return None
        idx = len(self.messages) - index_from_end
        if idx < 0 or idx >= len(self.messages):
            return None
        self.messages[idx].pinned = False
        return self.messages[idx]

    def list_pins(self) -> List[ChatMessage]:
        return [m for m in self.messages if m.pinned]

    def get_context_state(
        self, max_tokens: int = 4096, *, model: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Return (context_messages, token_count, dropped_count)."""
        system_content = self.system_prompt

        # Inject accumulated summary if present
        if self._context_summary:
            system_content = (
                f"{self.system_prompt}\n\n"
                f"## Previous Context Summary\n"
                f"The following is a summary of earlier conversation "
                f"messages that were pruned to fit the context window. "
                f"Use this to maintain continuity.\n\n"
                f"{self._context_summary}"
            )

        current_tokens = _estimate_text_tokens(system_content, model)

        pinned = [m for m in self.messages if m.pinned]
        unpinned = [m for m in self.messages if not m.pinned]

        # Always include pinned (in original order)
        pruned_messages: List[ChatMessage] = []
        for msg in pinned:
            current_tokens += msg.estimate_tokens(model)
            pruned_messages.append(msg)

        # Add unpinned from most recent, until limit reached
        dropped_messages: List[ChatMessage] = []
        for msg in reversed(unpinned):
            msg_tokens = msg.estimate_tokens(model)
            if current_tokens + msg_tokens > max_tokens:
                dropped_messages.append(msg)
                continue
            current_tokens += msg_tokens
            pruned_messages.insert(len(pinned), msg)

        # Update accumulated summary from dropped messages
        if dropped_messages:
            summary_parts = []
            for msg in reversed(dropped_messages):
                preview = msg.content[:200].replace("\n", " ").strip()
                if len(msg.content) > 200:
                    preview += "..."
                summary_parts.append(f"- {msg.role}: {preview}")
            new_summary = "\n".join(summary_parts)
            # Append to existing summary, capped at 2000 chars
            if self._context_summary:
                combined = self._context_summary + "\n" + new_summary
                self._context_summary = combined[-2000:]
            else:
                self._context_summary = new_summary[-2000:]

        # Final formatting
        result = [{"role": "system", "content": system_content}]
        for msg in pruned_messages:
            result.append(msg.to_chat_dict())
        dropped = max(0, len(self.messages) - len(pruned_messages))
        return result, int(current_tokens), dropped

    def clear_summary(self):
        """Clear the accumulated context summary (e.g., on new session)."""
        self._context_summary = ""

    def get_context_messages(
        self,
        max_tokens: int = 4096,
        *,
        model: Optional[str] = None,
        ai_client: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Prunes history to fit within max_tokens, keeping the system prompt."""
        # ai_client is kept for API compatibility with older callers; token
        # estimation currently only needs the model name.
        result, _, _ = self.get_context_state(max_tokens, model=model)
        return result

    def export(self, export_format: str, path: Path) -> Path:
        """Export the session to a file in md, txt, or json.

        Delegates to SessionExporter for unified export logic.
        """
        from veni.sharing import SessionExporter

        exporter = SessionExporter(self, memory=None)
        content = exporter.export_session(
            format=export_format,
            redact=True,
            include_metadata=True,
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def save(self, name: Optional[str] = None) -> Path:
        """Saves current session to JSON."""
        name = name or f"session_{int(time.time())}"
        path = self.storage_dir / f"{name}.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "system_prompt": self.system_prompt,
            "messages": [m.to_dict() for m in self.messages],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, name: str) -> bool:
        """Loads a session from JSON."""
        path = self.storage_dir / f"{name}.json"
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.system_prompt = data.get("system_prompt", self.system_prompt)
                self.messages = [
                    ChatMessage.from_dict(m) for m in data.get("messages", [])
                ]
            return True
        except Exception:
            return False

    def list_sessions(self) -> List[str]:
        """Lists available saved sessions."""
        return [f.stem for f in self.storage_dir.glob("*.json")]
