"""
Perplexity AI provider implementation.
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class PerplexityClient(AIClient):
    """Perplexity AI API client (OpenAI compatible)."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_search=True,
    )

    def __init__(self, api_key: str, model: str = "sonar"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.perplexity.ai/chat/completions"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"model": self.model, "messages": messages, "stream": stream}

        # Add generation params
        for param in ["temperature", "max_tokens", "top_p"]:
            if kwargs.get(param) is not None:
                payload[param] = kwargs[param]

        try:
            response = request_with_retries(
                "POST",
                self.base_url,
                json=payload,
                headers=headers,
                stream=stream,
                timeout=120,
            )

            if response.status_code != 200:
                yield f"Error: HTTP {response.status_code} - {response.text}"
                return

            if stream:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            try:
                                data = json.loads(line_str[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                yield data.get("choices", [{}])[0].get("message", {}).get("content", "")

        except Exception as e:
            yield f"Error: Perplexity API request failed - {str(e)}"
