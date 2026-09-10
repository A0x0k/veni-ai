"""
Gemini provider implementation.
"""

import json
from typing import Any, Dict, Generator, List

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class GeminiClient(AIClient):
    """Google Gemini API client."""

    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_multimodal=True,
        supports_search=True,
    )

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        # Reset base_url in case model changed
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent"

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        # Format history for Gemini
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            parts = [{"text": msg["content"]}]

            # Handle images
            if "images" in msg and msg["images"]:
                for img_path in msg["images"]:
                    try:
                        b64_img = self.encode_image(img_path)
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": b64_img,
                                }
                            }
                        )
                    except Exception:
                        continue

            contents.append({"role": role, "parts": parts})

        payload = {"contents": contents}
        if tools:
            # Simple conversion for Gemini tools (functions)
            payload["tools"] = [{"function_declarations": tools}]

        gen_config = {}
        if kwargs.get("temperature") is not None:
            gen_config["temperature"] = kwargs["temperature"]
        if kwargs.get("top_p") is not None:
            gen_config["topP"] = kwargs["top_p"]
        if kwargs.get("max_tokens") is not None:
            gen_config["maxOutputTokens"] = kwargs["max_tokens"]
        if gen_config:
            payload["generationConfig"] = gen_config

        try:
            # Note: Gemini stream uses standard HTTP chunked transfer, not SSE like OpenAI
            response = request_with_retries(
                "POST",
                self.base_url,
                json=payload,
                headers=headers,
                params=params,
                stream=True,
                timeout=120,
            )

            if response.status_code != 200:
                yield f"Error: HTTP {response.status_code} - {response.text}"
                return

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8").strip()
                    # Clean up the JSON array structure from Gemini stream
                    if line_str.startswith(","):
                        line_str = line_str[1:].strip()
                    if line_str.startswith("["):
                        line_str = line_str[1:].strip()
                    if line_str.endswith("]"):
                        line_str = line_str[:-1].strip()

                    try:
                        data = json.loads(line_str)
                        chunk = (
                            data.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            yield f"Error: Gemini API request failed - {str(e)}"
