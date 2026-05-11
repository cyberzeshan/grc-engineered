"""Integration tests for AuditNarrativeAgent."""
from __future__ import annotations

import pytest
from tests.conftest import needs_llm

VALID_NARRATIVE_TYPES = {"control_description", "exception_memo", "auditor_response"}


@needs_llm
def test_draft_control_description():
    from agents.audit_narrative_agent import AuditNarrativeAgent
    from core.models import AuditNarrativeInput

    inp = AuditNarrativeInput(
        narrative_type="control_description",
        control_id="CC6.1",
        control_description="Logical access to systems is restricted to authorized users through RBAC.",
        evidence_summaries=[
            "Q1 2025 access review — 47 users verified, 3 terminated accounts removed",
            "Role-based access policy v2.3 approved January 2025",
        ],
    )
    result = AuditNarrativeAgent().draft_narrative(inp)

    assert result.control_id == "CC6.1"
    assert result.narrative_type == "control_description"
    assert isinstance(result.narrative_text, str)
    assert len(result.narrative_text) > 0
    assert result.word_count > 0
    assert isinstance(result.suggested_evidence_refs, list)


@needs_llm
def test_draft_exception_memo():
    from agents.audit_narrative_agent import AuditNarrativeAgent
    from core.models import AuditNarrativeInput

    inp = AuditNarrativeInput(
        narrative_type="exception_memo",
        control_id="CC6.3",
        control_description="Multi-factor authentication is enforced for all privileged accounts.",
        evidence_summaries=[
            "MFA enforced on all 45 standard user accounts",
            "Infrastructure migration log — migration window 2025-03-01 to 2025-03-14",
        ],
        exception_details=(
            "MFA was not enforced for 2 service accounts for 14 days "
            "during infrastructure migration to AWS."
        ),
    )
    result = AuditNarrativeAgent().draft_narrative(inp)

    assert result.narrative_type == "exception_memo"
    assert isinstance(result.narrative_text, str)
    assert len(result.narrative_text) > 50


@needs_llm
def test_draft_auditor_response():
    from agents.audit_narrative_agent import AuditNarrativeAgent
    from core.models import AuditNarrativeInput

    inp = AuditNarrativeInput(
        narrative_type="auditor_response",
        control_id="CC6.1",
        control_description="Logical access is restricted to authorized users.",
        evidence_summaries=[
            "Q1 2025 access review — completed 2025-01-15",
            "AWS IAM policy export — principle of least privilege enforced",
        ],
        auditor_question=(
            "How does the organization ensure access rights are reviewed "
            "and revoked when employees leave?"
        ),
    )
    result = AuditNarrativeAgent().draft_narrative(inp)

    assert result.narrative_type == "auditor_response"
    assert isinstance(result.narrative_text, str)
    assert len(result.narrative_text) > 0


@needs_llm
def test_word_count_is_reasonable():
    from agents.audit_narrative_agent import AuditNarrativeAgent
    from core.models import AuditNarrativeInput

    inp = AuditNarrativeInput(
        narrative_type="control_description",
        control_id="A.9.1",
        control_description="An access control policy is established and maintained.",
        evidence_summaries=["Access Control Policy v3.0 — approved 2025-01"],
    )
    result = AuditNarrativeAgent().draft_narrative(inp)

    # System prompt asks for 200-400 words for control descriptions
    # We allow a wide range since the model may vary
    assert result.word_count >= 50
    assert result.word_count == len(result.narrative_text.split())


@needs_llm
def test_output_fields_are_typed():
    from agents.audit_narrative_agent import AuditNarrativeAgent
    from core.models import AuditNarrativeInput

    inp = AuditNarrativeInput(
        narrative_type="control_description",
        control_id="CC7.2",
        control_description="Security events are monitored and evaluated.",
        evidence_summaries=["SIEM alert dashboard — 2025 Q1"],
    )
    result = AuditNarrativeAgent().draft_narrative(inp)

    assert isinstance(result.narrative_type, str)
    assert isinstance(result.control_id, str)
    assert isinstance(result.narrative_text, str)
    assert isinstance(result.word_count, int)
    assert isinstance(result.suggested_evidence_refs, list)
