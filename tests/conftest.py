"""Shared pytest configuration and fixtures."""
from __future__ import annotations

import os
import pytest

# True when at least one LLM backend is available
HAS_LLM = (
    bool(os.getenv("ANTHROPIC_API_KEY"))
    or os.getenv("LLM_PROVIDER", "anthropic").lower() == "ollama"
)

needs_llm = pytest.mark.skipif(
    not HAS_LLM,
    reason=(
        "No LLM provider configured. "
        "Set ANTHROPIC_API_KEY for Claude or LLM_PROVIDER=ollama for local Ollama."
    ),
)
