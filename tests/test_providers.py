"""Unit tests for core/providers.py — no LLM calls made."""
from __future__ import annotations

import pytest


def test_create_provider_returns_anthropic(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

    import importlib
    import core.providers as mod
    importlib.reload(mod)

    from core.providers import AnthropicProvider, create_provider
    provider = create_provider()
    assert isinstance(provider, AnthropicProvider)
    assert provider.provider_name == "anthropic"
    assert provider.model_name == "claude-sonnet-4-6"


def test_create_provider_respects_anthropic_model_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    from core.providers import AnthropicProvider, create_provider
    provider = create_provider()
    assert isinstance(provider, AnthropicProvider)
    assert provider.model_name == "claude-haiku-4-5-20251001"


def test_create_provider_raises_without_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from core.providers import create_provider
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        create_provider()


def test_create_provider_returns_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    from core.providers import OllamaProvider, create_provider
    provider = create_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.provider_name == "ollama"
    assert provider.model_name == "llama3.2"


def test_create_provider_ollama_defaults(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from core.providers import OllamaProvider, create_provider
    provider = create_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.model_name == "llama3.2"


def test_ollama_tool_schema_conversion():
    from core.providers import OllamaProvider

    anthropic_tools = [
        {
            "name": "read_framework_file",
            "description": "Read a framework source document",
            "input_schema": {
                "type": "object",
                "properties": {
                    "framework_name": {"type": "string", "description": "Filename"}
                },
                "required": ["framework_name"],
            },
        }
    ]

    result = OllamaProvider._to_openai_tools(anthropic_tools)

    assert len(result) == 1
    tool = result[0]
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "read_framework_file"
    assert tool["function"]["description"] == "Read a framework source document"
    assert "framework_name" in tool["function"]["parameters"]["properties"]


def test_ollama_tool_schema_conversion_empty():
    from core.providers import OllamaProvider
    assert OllamaProvider._to_openai_tools([]) == []


def test_ollama_tool_schema_missing_description():
    """Tool without description should not crash conversion."""
    from core.providers import OllamaProvider

    tools = [{"name": "my_tool", "input_schema": {"type": "object", "properties": {}}}]
    result = OllamaProvider._to_openai_tools(tools)
    assert result[0]["function"]["description"] == ""
