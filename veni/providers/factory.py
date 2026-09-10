"""
Provider factory for AI clients.
"""

import os
from typing import Optional

from veni.config import config
from veni.providers.anthropic import AnthropicClient
from veni.providers.deepseek import DeepSeekClient
from veni.providers.duckduckgo import DuckDuckGoClient
from veni.providers.free import FreeAIClient
from veni.providers.gemini import GeminiClient
from veni.providers.groq import GroqClient
from veni.providers.mistral import MistralClient
from veni.providers.ollama import OllamaClient
from veni.providers.openai import OpenAIClient
from veni.providers.openrouter import OpenRouterClient
from veni.providers.perplexity import PerplexityClient
from veni.providers.qwen import QwenClient


def create_ai_client(
    provider: str = None, model: Optional[str] = None, api_key: Optional[str] = None
):
    """Factory to create the appropriate AI client."""
    # Use config defaults if not provided
    if not provider:
        provider = config.get("default_provider", "ollama")

    provider = provider.lower()

    # Provider-specific logic
    if provider == "ollama":
        return OllamaClient(model=model or config.get("default_model", "llama3.2"))

    elif provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY") or config.get("api_keys.openai")
        if not key:
            raise ValueError("OpenAI API Key is missing. Set it in config or env var.")
        return OpenAIClient(api_key=key, model=model or "gpt-4o")

    elif provider == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY") or config.get("api_keys.gemini")
        if not key:
            raise ValueError("Gemini API Key is missing. Set it in config or env var.")
        return GeminiClient(api_key=key, model=model or "gemini-2.0-flash")

    elif provider == "anthropic":
        key = (
            api_key
            or os.getenv("ANTHROPIC_API_KEY")
            or config.get("api_keys.anthropic")
        )
        if not key:
            raise ValueError(
                "Anthropic API Key is missing. Set it in config or env var."
            )
        return AnthropicClient(api_key=key, model=model or "claude-3-5-sonnet-20240620")

    elif provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY") or config.get("api_keys.groq")
        if not key:
            raise ValueError("Groq API Key is missing. Set it in config or env var.")
        return GroqClient(api_key=key, model=model or "llama-3.1-70b-versatile")

    elif provider == "deepseek":
        key = (
            api_key or os.getenv("DEEPSEEK_API_KEY") or config.get("api_keys.deepseek")
        )
        if not key:
            raise ValueError(
                "DeepSeek API Key is missing. Set it in config or env var."
            )
        return DeepSeekClient(api_key=key, model=model or "deepseek-chat")

    elif provider == "qwen":
        key = api_key or os.getenv("QWEN_API_KEY") or config.get("api_keys.qwen")
        if not key:
            raise ValueError("Qwen API Key is missing. Set it in config or env var.")
        return QwenClient(api_key=key, model=model or "qwen-max")

    elif provider == "openrouter":
        key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY")
            or config.get("api_keys.openrouter")
        )
        if not key:
            raise ValueError(
                "OpenRouter API Key is missing. Set it in config or env var."
            )
        return OpenRouterClient(
            api_key=key, model=model or "google/gemini-2.0-flash-001"
        )

    elif provider == "mistral":
        key = api_key or os.getenv("MISTRAL_API_KEY") or config.get("api_keys.mistral")
        if not key:
            raise ValueError("Mistral API Key is missing. Set it in config or env var.")
        return MistralClient(api_key=key, model=model or "mistral-large-latest")

    elif provider == "perplexity":
        key = (
            api_key
            or os.getenv("PERPLEXITY_API_KEY")
            or config.get("api_keys.perplexity")
        )
        if not key:
            raise ValueError(
                "Perplexity API Key is missing. Set it in config or env var."
            )
        return PerplexityClient(api_key=key, model=model or "sonar")

    elif provider == "free":
        return FreeAIClient(model=model or "openai")

    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_provider_name(client) -> str:
    """Helper to get the string name of a provider from its client instance."""
    if isinstance(client, OllamaClient):
        return "ollama"
    if isinstance(client, OpenAIClient):
        return "openai"
    if isinstance(client, GeminiClient):
        return "gemini"
    if isinstance(client, AnthropicClient):
        return "anthropic"
    if isinstance(client, GroqClient):
        return "groq"
    if isinstance(client, DeepSeekClient):
        return "deepseek"
    if isinstance(client, QwenClient):
        return "qwen"
    if isinstance(client, OpenRouterClient):
        return "openrouter"
    if isinstance(client, MistralClient):
        return "mistral"
    if isinstance(client, PerplexityClient):
        return "perplexity"
    if isinstance(client, FreeAIClient):
        return "free"
    return "unknown"
