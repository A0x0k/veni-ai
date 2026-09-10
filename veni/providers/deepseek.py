"""
DeepSeek provider implementation (DeepSeek-V3/R1).
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class DeepSeekClient(AIClient):
    """DeepSeek API client (OpenAI compatible)."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_search=True,
    )

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/chat/completions"

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
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("max_tokens") is not None:
            payload["max_tokens"] = kwargs["max_tokens"]
        if kwargs.get("top_p") is not None:
            payload["top_p"] = kwargs["top_p"]

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
                            if line_str.strip() == "data: [DONE]":
                                break
                            try:
                                data = json.loads(line_str[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                                # DeepSeek R1 specific reasoning content
                                if "reasoning_content" in delta:
                                    # Emit as a collapsible thinking block for the UI
                                    reasoning = delta["reasoning_content"]
                                    if reasoning:
                                        yield f"\n[💭 Reasoning: {reasoning}]\n"
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                # Include reasoning content if available
                reasoning = message.get("reasoning_content", "")
                if reasoning:
                    yield f"[💭 Reasoning: {reasoning}]\n\n{content}"
                else:
                    yield content

        except Exception as e:
            yield f"Error: DeepSeek API request failed - {str(e)}"
