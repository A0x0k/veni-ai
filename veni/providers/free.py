"""
Free AI provider implementation using multiple free endpoints.
"""

from typing import Any, Dict, Generator, List
from urllib.parse import quote

from .base import AIClient, ProviderCapabilities
from .http import request_with_retries


class FreeAIClient(AIClient):
    """Free AI API client with fallback endpoints."""

    capabilities = ProviderCapabilities(
        supports_streaming=False,
        supports_multimodal=False,
    )

    # Multiple free endpoints for redundancy
    ENDPOINTS = [
        "https://text.pollinations.ai/",
        "https://ai.love2024.workers.dev/",
    ]

    def __init__(self, model: str = "openai"):
        self.model = model
        self.current_endpoint = 0

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = True,
        tools: List[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        # Extract the conversation for the prompt
        system_prompt = "You are Veni, a helpful terminal AI assistant."
        conversation = []

        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            elif m["role"] in ["user", "assistant"]:
                conversation.append(m)

        # Get last user message for simple API
        last_user_msg = ""
        for m in reversed(conversation):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break

        if not last_user_msg:
            yield "Error: No user message to process."
            return

        # Build full prompt
        full_prompt = f"{system_prompt}\n\n"
        for m in conversation[-6:]:  # Last 6 messages for context
            role = "Human" if m["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {m['content']}\n"
        full_prompt += "Assistant: "

        # Try each endpoint
        last_error = None
        for endpoint in self.ENDPOINTS:
            try:
                result = self._call_endpoint(endpoint, full_prompt, last_user_msg)
                if result and not result.startswith("Error"):
                    yield result
                    return
                last_error = result
            except Exception as e:
                last_error = str(e)
                continue

        yield f"Error: All free AI endpoints failed. Last error: {last_error}\n\nTip: Install Ollama (ollama.com) for free local AI, or set an API key for cloud providers."

    def _call_endpoint(
        self, endpoint: str, full_prompt: str, simple_prompt: str
    ) -> str:
        """Try to get a response from an endpoint."""
        try:
            # Try simple mode first (more reliable)
            encoded = quote(simple_prompt.encode("utf-8"), safe="")
            url = f"{endpoint}{encoded}"
            params = {"model": self.model, "seed": str(hash(simple_prompt) % 10000)}

            response = request_with_retries("GET", url, params=params, timeout=20)

            if response.status_code == 404:
                raise Exception("Endpoint returned 404")

            response.raise_for_status()
            result = response.text.strip()

            if not result or len(result) < 2:
                raise Exception("Empty response")

            return result

        except Exception:
            # Try POST mode as fallback
            try:
                post_url = endpoint.rstrip("/")
                if "pollinations" in post_url:
                    post_url = f"{post_url}/openai"

                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": simple_prompt}],
                    "max_tokens": 500,
                }

                response = request_with_retries(
                    "POST",
                    post_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20,
                )

                if response.status_code == 200:
                    data = response.json()
                    return (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

            except Exception:
                pass

            raise Exception(f"Endpoint {endpoint} failed")
