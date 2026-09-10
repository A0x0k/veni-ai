"""
Base class for AI clients.
"""

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional


@dataclass
class ProviderCapabilities:
    """Describe what a provider can handle."""

    supports_streaming: bool = True
    supports_multimodal: bool = False
    supports_vision: bool = False
    supports_tool_calls: bool = False
    supports_search: bool = False
    supports_voice: bool = False
    supports_file_edit: bool = False


class AIClient(ABC):
    """Abstract base class for all AI providers."""

    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    capabilities: ProviderCapabilities = ProviderCapabilities()

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Send a chat request to the provider.

        Args:
            messages: List of message objects.
            stream: Whether to stream the response.
            tools: Optional list of tool declarations.
            kwargs: Optional generation settings.

        Yields:
            Chunks of the response string or tool call metadata.
        """
        pass

    async def chat_async(
        self, messages: List[Dict[str, Any]], stream: bool = True, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Async bridge for providers that only support sync chat.
        """
        for chunk in self.chat(messages, stream=stream, **kwargs):
            yield chunk

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Helper to encode an image file to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
