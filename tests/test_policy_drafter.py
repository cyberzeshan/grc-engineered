"""Integration tests for PolicyDrafterAgent."""
from __future__ import annotations

import json
import pytest
from tests.conftest import needs_llm

POLICY_TEXT = """\
# Acceptable Use Policy

## 1. Purpose
This policy governs the acceptable use of company information systems.

## 2. Scope
All employees and contractors with access to company systems.

## 3. Permitted Uses
Systems may be used for legitimate business purposes.

## 4. Prohibited Uses
Systems may not be used for illegal activities or personal gain.
"""


@needs_llm
def test_draft_revision_returns_valid_output():
    from agents.policy_drafter_agent import PolicyDrafterAgent
    from core.models import PolicyDraftInput

    inp = PolicyDraftInput(
        policy_name="Acceptable Use Policy",
        current_policy_text=POLICY_TEXT,
        change_trigger="NIST CSF 2.0 now requires explicit references to supply chain risk.",
        trigger_source="NIST CSF 2.0",
        effective_date="2025-07-01",
    )
    result = PolicyDrafterAgent().draft_revision(inp)

    assert result.policy_name == "Acceptable Use Policy"
    assert isinstance(result.revised_policy_text, str)
    assert len(result.revised_policy_text) > 0
    assert isinstance(result.change_log_entry, dict)
    assert isinstance(result.sections_changed, list)


@needs_llm
def test_draft_revision_change_log_has_required_fields():
    from agents.policy_drafter_agent import PolicyDrafterAgent
    from core.models import PolicyDraftInput

    inp = PolicyDraftInput(
        policy_name="AI Acceptable Use Policy",
        current_policy_text="# AI Use Policy\n\nEmployees may use approved AI tools.",
        change_trigger="ISO 42001 Annex A now requires AI risk assessment documentation.",
        trigger_source="ISO 42001:2023",
        effective_date="2025-08-01",
    )
    result = PolicyDrafterAgent().draft_revision(inp)

    log = result.change_log_entry
    assert "date" in log or "trigger" in log or "rationale" in log


@needs_llm
def test_draft_revision_saves_files(tmp_path):
    from agents.policy_drafter_agent import PolicyDrafterAgent
    from core.models import PolicyDraftInput

    inp = PolicyDraftInput(
        policy_name="Test Policy",
        current_policy_text="# Test Policy\n\nOriginal content.",
        change_trigger="Annual review.",
        trigger_source="Internal",
        effective_date="2025-06-01",
    )
    result = PolicyDrafterAgent().draft_revision(inp)
    paths = PolicyDrafterAgent().save_outputs(result, output_dir=str(tmp_path))

    assert "markdown" in paths
    assert "change_log" in paths
    from pathlib import Path
    assert Path(paths["markdown"]).exists()
    assert Path(paths["change_log"]).exists()
