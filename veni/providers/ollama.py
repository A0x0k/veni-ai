"""
Ollama AI provider implementation.
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class OllamaClient(AIClient):
    """Ollama API client for local LLMs."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_multimodal=True,
        supports_file_edit=True,
    )

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.2"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/chat"

        # Format messages for Ollama
        ollama_messages = []
        for msg in messages:
            m = {"role": msg["role"], "content": msg["content"]}
            if "images" in msg and msg["images"]:
                m["images"] = []
                for img_path in msg["images"]:
                    try:
                        m["images"].append(self.encode_image(img_path))
                    except Exception:
                        continue
            ollama_messages.append(m)

        payload = {"model": self.model, "messages": ollama_messages, "stream": stream}
        if tools:
            # Simple conversion for Ollama tools (supported in newer versions)
            payload["tools"] = tools

        options = {}
        if kwargs.get("temperature") is not None:
            options["temperature"] = kwargs["temperature"]
        if kwargs.get("top_p") is not None:
            options["top_p"] = kwargs["top_p"]
        if kwargs.get("max_tokens") is not None:
            options["num_predict"] = kwargs["max_tokens"]
        if options:
            payload["options"] = options

        try:
            response = request_with_retries(
                "POST",
                url,
                json=payload,
                stream=stream,
                timeout=120,
            )
            response.raise_for_status()

            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                yield data.get("message", {}).get("content", "")

        except Exception as e:
            if (
                "ConnectionError" in type(e).__name__
                or "ConnectionRefusedError" in type(e).__name__
            ):
                yield "Error: Cannot connect to Ollama. Make sure the Ollama service is running on localhost:11434"
                return
            yield f"Error: {str(e)}"
