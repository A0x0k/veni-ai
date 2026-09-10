"""
DuckDuckGo AI provider implementation (Free, no API key).
"""

import json
import logging
from typing import Any, Dict, Generator, List, Optional

import requests

from .base import AIClient, ProviderCapabilities

logger = logging.getLogger("veni.providers.duckduckgo")

class DuckDuckGoClient(AIClient):
    """DuckDuckGo AI client (Free tier, no key required)."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_search=True,
    )

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.base_url = "https://duckduckgo.com/duckchat/v1"
        self._vqd: Optional[str] = None
        self._model_map = {
            "gpt-4o-mini": "gpt-4o-mini",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "llama-3.1-70b": "meta-llama/Llama-3.1-70B-Instruct-Turbo",
            "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        }

    def _get_vqd(self) -> str:
        """Fetch the required VQD token."""
        headers = {"x-vqd-accept": "1"}
        resp = requests.get(f"{self.base_url}/status", headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to initialize DuckDuckGo Chat: {resp.text}")
        return resp.headers.get("x-vqd-token", "")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:

        if not self._vqd:
            self._vqd = self._get_vqd()

        headers = {
            "Content-Type": "application/json",
            "x-vqd-token": self._vqd,
        }

        # DuckDuckGo requires simple message format
        # We send only the last few messages for simplicity in free mode
        payload = {
            "model": self._model_map.get(self.model, self.model),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                stream=True,
                timeout=30
            )

            if resp.status_code == 429:
                yield "Error: DuckDuckGo rate limit exceeded. Wait a few minutes."
                return

            if resp.status_code != 200:
                yield f"Error: DuckDuckGo API failed with status {resp.status_code}"
                return

            # Update VQD for next turn
            self._vqd = resp.headers.get("x-vqd-token", self._vqd)

            for line in resp.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        if line_str == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line_str[6:])
                            chunk = data.get("message", "")
                            if chunk:
                                yield chunk
                        except Exception:
                            continue
        except Exception as e:
            yield f"Error: DuckDuckGo Chat failed - {str(e)}"
