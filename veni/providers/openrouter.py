"""
OpenRouter provider implementation.
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class OpenRouterClient(AIClient):
    """OpenRouter API client (OpenAI compatible with extra headers)."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_search=True,
        supports_vision=True,
    )

    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-001"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

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
            "HTTP-Referer": "https://github.com/neoastra303/Veni-AI",
            "X-Title": "Veni AI Chatbot",
        }

        # Prepare payload
        processed_messages = []
        for msg in messages:
            m = {"role": msg["role"], "content": msg["content"]}
            # Handle vision if present
            if "images" in msg and msg["images"]:
                content = [{"type": "text", "text": msg["content"]}]
                for img_path in msg["images"]:
                    try:
                        b64 = self.encode_image(img_path)
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })
                    except Exception:
                        continue
                m["content"] = content
            processed_messages.append(m)

        payload = {"model": self.model, "messages": processed_messages, "stream": stream}

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

                                # OpenRouter can return tool calls
                                if "tool_calls" in delta:
                                    for tc in delta["tool_calls"]:
                                        fn = tc.get("function", {})
                                        name = fn.get("name", "")
                                        args = fn.get("arguments", "")
                                        if name:
                                            yield f"\nCALL: {name}({args})\n"
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                yield message.get("content", "")

        except Exception as e:
            yield f"Error: OpenRouter API request failed - {str(e)}"
