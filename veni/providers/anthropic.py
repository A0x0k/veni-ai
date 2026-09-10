"""
Anthropic provider implementation (Claude).
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class AnthropicClient(AIClient):
    """Anthropic API client."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_search=True,
        supports_tool_calls=True,
    )

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        system_prompt = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": user_messages,
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens") or 4096,
        }
        if tools:
            # Convert OpenAI-style tools to Anthropic format
            anthropic_tools = []
            for t in tools:
                if t.get("type") == "function":
                    fn = t["function"]
                    anthropic_tools.append(
                        {
                            "name": fn["name"],
                            "description": fn.get("description", ""),
                            "input_schema": {
                                "type": "object",
                                "properties": fn.get("parameters", {}).get(
                                    "properties", {}
                                ),
                                "required": fn.get("parameters", {}).get(
                                    "required", []
                                ),
                            },
                        }
                    )
                else:
                    # Already in Anthropic format
                    anthropic_tools.append(t)
            payload["tools"] = anthropic_tools

        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("top_p") is not None:
            payload["top_p"] = kwargs["top_p"]

        if system_prompt:
            payload["system"] = system_prompt

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
                                event_type = data.get("type", "")
                                if event_type == "content_block_delta":
                                    delta = data.get("delta", {})
                                    # Text content
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                                    # Tool call input (JSON)
                                    input_json = delta.get("partial_json", "")
                                    if input_json:
                                        # Emit tool call marker for core.py to parse
                                        yield f"[TOOL_INPUT_JSON]{input_json}"
                                elif event_type == "content_block_start":
                                    content_block = data.get("content_block", {})
                                    if content_block.get("type") == "tool_use":
                                        tool_name = content_block.get("name", "")
                                        tool_id = content_block.get("id", "")
                                        yield f"[TOOL_USE]{tool_name}:{tool_id}"
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                content_blocks = data.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "text":
                        yield block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_id = block.get("id", "")
                        tool_input = json.dumps(block.get("input", {}))
                        yield f"[TOOL_USE]{tool_name}:{tool_id}"
                        yield f"[TOOL_INPUT_JSON]{tool_input}"

        except Exception as e:
            yield f"Error: Anthropic API request failed - {str(e)}"
