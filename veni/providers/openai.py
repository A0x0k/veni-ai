"""
OpenAI provider implementation.
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class OpenAIClient(AIClient):
    """OpenAI API client."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_multimodal=True,
        supports_tool_calls=True,
        supports_search=True,
        supports_file_edit=True,
    )

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

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

        # Prepare messages for multimodal if images are present
        processed_messages = []
        for msg in messages:
            if "images" in msg and msg["images"]:
                content = [{"type": "text", "text": msg["content"]}]
                for img_path in msg["images"]:
                    try:
                        b64_img = self.encode_image(img_path)
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_img}"
                                },
                            }
                        )
                    except Exception:
                        continue
                processed_messages.append({"role": msg["role"], "content": content})
            else:
                processed_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        payload = {
            "model": self.model,
            "messages": processed_messages,
            "stream": stream,
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
            payload["tool_choice"] = "auto"

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
                tool_calls_buffer = {}  # Accumulate tool call arguments
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            if line_str.strip() == "data: [DONE]":
                                break
                            try:
                                data = json.loads(line_str[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})

                                # Handle content
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]

                                # Handle native tool calls
                                if "tool_calls" in delta:
                                    for tc in delta["tool_calls"]:
                                        idx = tc.get("index", 0)
                                        if "function" in tc:
                                            fn = tc["function"]
                                            if idx not in tool_calls_buffer:
                                                tool_calls_buffer[idx] = {
                                                    "name": "",
                                                    "arguments": "",
                                                }
                                            if "name" in fn:
                                                tool_calls_buffer[idx]["name"] += fn[
                                                    "name"
                                                ]
                                            if "arguments" in fn:
                                                tool_calls_buffer[idx][
                                                    "arguments"
                                                ] += fn["arguments"]
                            except json.JSONDecodeError:
                                continue

                # Yield accumulated tool calls in CALL: format
                for idx, tc in sorted(tool_calls_buffer.items()):
                    if tc["name"]:
                        yield f"\nCALL: {tc['name']}({tc['arguments']})\n"

            else:
                data = response.json()
                msg = data.get("choices", [{}])[0].get("message", {})
                if "content" in msg and msg["content"]:
                    yield msg["content"]

                if "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        fn = tc["function"]
                        args = fn["arguments"]
                        yield f"\nCALL: {fn['name']}({args})\n"

        except Exception as e:
            yield f"Error: OpenAI API request failed - {str(e)}"
