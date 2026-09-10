"""Unit tests for AI provider implementations."""

import json
import os
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

from veni.providers.anthropic import AnthropicClient
from veni.providers.base import AIClient, ProviderCapabilities
from veni.providers.deepseek import DeepSeekClient
from veni.providers.factory import create_ai_client, get_provider_name
from veni.providers.gemini import GeminiClient
from veni.providers.groq import GroqClient
from veni.providers.mistral import MistralClient
from veni.providers.ollama import OllamaClient
from veni.providers.openai import OpenAIClient
from veni.providers.openrouter import OpenRouterClient
from veni.providers.perplexity import PerplexityClient
from veni.providers.qwen import QwenClient


@pytest.fixture
def sample_messages():
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]


@pytest.fixture
def mock_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {"content": "Hello! How can I help you today?"},
                "index": 0,
            }
        ]
    }
    mock_resp.iter_lines.return_value = [
        b"data: " + json.dumps({
            "choices": [{"delta": {"content": "Hello"}, "index": 0}]
        }).encode()
    ]
    return mock_resp


# ── Provider Capabilities ─────────────────────────────────────────────────


class TestProviderCapabilities:
    def test_default_capabilities(self):
        caps = ProviderCapabilities()
        assert caps.supports_streaming is True
        assert caps.supports_multimodal is False
        assert caps.supports_vision is False
        assert caps.supports_tool_calls is False

    def test_openai_capabilities(self):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        assert client.capabilities.supports_tool_calls is True
        assert client.capabilities.supports_multimodal is True

    def test_ollama_capabilities(self):
        client = OllamaClient(model="llama3.2")
        assert client.capabilities.supports_multimodal is True
        assert client.capabilities.supports_streaming is True

    def test_anthropic_capabilities(self):
        client = AnthropicClient(api_key="sk-test", model="claude-3-5-sonnet-20240620")
        assert client.capabilities.supports_tool_calls is True


# ── OpenAI Provider ────────────────────────────────────────────────────────


class TestOpenAIClient:
    def test_initialization(self):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        assert client.api_key == "sk-test"
        assert client.model == "gpt-4o"
        assert client.base_url == "https://api.openai.com/v1/chat/completions"

    def test_chat_streaming(self, sample_messages, mock_response):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        with patch("veni.providers.openai.request_with_retries", return_value=mock_response):
            result = list(client.chat(sample_messages, stream=True))
            assert len(result) >= 1
            assert "Hello" in "".join(result)

    def test_chat_non_streaming(self, sample_messages, mock_response):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        mock_response.iter_lines.side_effect = AttributeError
        with patch("veni.providers.openai.request_with_retries", return_value=mock_response):
            result = list(client.chat(sample_messages, stream=False))
            assert len(result) >= 1

    def test_chat_error_response(self, sample_messages):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        error_resp = MagicMock()
        error_resp.status_code = 401
        error_resp.text = "Invalid API key"
        with patch("veni.providers.openai.request_with_retries", return_value=error_resp):
            result = list(client.chat(sample_messages))
            assert "Error" in result[0]

    def test_chat_network_error(self, sample_messages):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        with patch("veni.providers.openai.request_with_retries", side_effect=ConnectionError("Failed")):
            result = list(client.chat(sample_messages))
            assert "Error" in result[0]

    def test_image_encoding_skip(self, sample_messages):
        """Verify bad images are skipped gracefully."""
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        messages = [
            {
                "role": "user",
                "content": "Describe this",
                "images": ["nonexistent.jpg"],
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "No image found"}}]
        }
        mock_resp.iter_lines.side_effect = AttributeError
        with patch("veni.providers.openai.request_with_retries", return_value=mock_resp):
            result = list(client.chat(messages, stream=False))
            assert len(result) >= 1

    def test_tool_calls_in_streaming(self, sample_messages):
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b"data: " + json.dumps({
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {"name": "test_tool", "arguments": '{"arg": "val"}'},
                        }]
                    },
                    "index": 0,
                }]
            }).encode(),
            b"data: [DONE]",
        ]
        with patch("veni.providers.openai.request_with_retries", return_value=mock_resp):
            result = list(client.chat(sample_messages, tools=[{"name": "test_tool"}]))
            assert any("CALL:" in chunk for chunk in result)


# ── Ollama Provider ────────────────────────────────────────────────────────


class TestOllamaClient:
    def test_initialization(self):
        client = OllamaClient(model="llama3.2")
        assert client.model == "llama3.2"
        assert "ollama" in client.base_url.lower() or "localhost" in client.base_url

    def test_chat_streaming(self, sample_messages):
        client = OllamaClient(model="llama3.2")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b'{"message": {"content": "Hello"}, "done": false}',
            b'{"message": {"content": " world"}, "done": true}',
        ]
        with patch("veni.providers.ollama.request_with_retries", return_value=mock_resp):
            result = list(client.chat(sample_messages))
            assert len(result) >= 1

    def test_chat_error(self, sample_messages):
        client = OllamaClient(model="llama3.2")
        with patch("veni.providers.ollama.request_with_retries", side_effect=Exception("Ollama not running")):
            result = list(client.chat(sample_messages))
            assert "Error" in result[0]


# ── Factory ────────────────────────────────────────────────────────────────


class TestProviderFactory:
    def test_create_openai(self):
        client = create_ai_client("openai", api_key="sk-test")
        assert isinstance(client, OpenAIClient)

    def test_create_ollama(self):
        client = create_ai_client("ollama")
        assert isinstance(client, OllamaClient)

    def test_create_gemini(self):
        client = create_ai_client("gemini", api_key="test-key")
        assert isinstance(client, GeminiClient)

    def test_create_anthropic(self):
        client = create_ai_client("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicClient)

    def test_create_groq(self):
        client = create_ai_client("groq", api_key="test-key")
        assert isinstance(client, GroqClient)

    def test_create_deepseek(self):
        client = create_ai_client("deepseek", api_key="test-key")
        assert isinstance(client, DeepSeekClient)

    def test_create_mistral(self):
        client = create_ai_client("mistral", api_key="test-key")
        assert isinstance(client, MistralClient)

    def test_create_perplexity(self):
        client = create_ai_client("perplexity", api_key="test-key")
        assert isinstance(client, PerplexityClient)

    def test_create_qwen(self):
        client = create_ai_client("qwen", api_key="test-key")
        assert isinstance(client, QwenClient)

    def test_create_openrouter(self):
        client = create_ai_client("openrouter", api_key="test-key")
        assert isinstance(client, OpenRouterClient)

    def test_create_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_ai_client("unknown_provider")

    def test_create_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch("veni.providers.factory.config.get", return_value=None):
            with pytest.raises(ValueError, match="API Key is missing"):
                create_ai_client("openai")


class TestGetProviderName:
    def test_get_openai_name(self):
        client = OpenAIClient(api_key="sk-test")
        assert get_provider_name(client) == "openai"

    def test_get_ollama_name(self):
        client = OllamaClient()
        assert get_provider_name(client) == "ollama"

    def test_get_unknown_name(self):
        class FakeClient(AIClient):
            def chat(self, messages, stream=True, tools=None, **kwargs):
                if False:
                    yield ""
                return iter(())

        assert get_provider_name(FakeClient()) == "unknown"


# ── Image Encoding ─────────────────────────────────────────────────────────


class TestImageEncoding:
    def test_encode_image_success(self, tmp_path):
        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"fake-image-data")
        result = AIClient.encode_image(str(img_file))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encode_image_not_found(self):
        with pytest.raises(FileNotFoundError):
            AIClient.encode_image("/nonexistent/image.png")
