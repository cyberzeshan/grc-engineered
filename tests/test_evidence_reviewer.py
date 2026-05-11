"""Integration tests for EvidenceReviewerAgent."""
from __future__ import annotations

from datetime import date, timedelta
import pytest
from tests.conftest import needs_llm


@needs_llm
def test_review_fresh_complete_evidence():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    inp = EvidenceReviewInput(
        control_id="CC6.1",
        control_description="Logical access is restricted to authorized users.",
        artifact_filename="access_review_q1.pdf",
        artifact_text=(
            f"Quarterly Access Review — Production AWS Account\n"
            f"Date: {date.today().isoformat()}\n"
            "Reviewer: Jane Smith\n"
            "All 47 active users verified. 3 terminated accounts removed."
        ),
        collection_date=date.today().isoformat(),
        system_name="Production AWS Account",
    )
    result = EvidenceReviewerAgent().review(inp)

    assert result.control_id == "CC6.1"
    assert result.freshness_pass is True
    assert 0 <= result.completeness_score <= 100
    assert isinstance(result.recommendation, str)


@needs_llm
def test_review_stale_evidence_tagged():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    stale_date = (date.today() - timedelta(days=120)).isoformat()
    inp = EvidenceReviewInput(
        control_id="CC7.1",
        control_description="Vulnerabilities are identified and remediated.",
        artifact_filename="vuln_scan_old.csv",
        artifact_text="Vulnerability scan export. Date: 2024-01-01. Host: unknown.",
        collection_date=stale_date,
        system_name="",
    )
    result = EvidenceReviewerAgent().review(inp)

    assert result.freshness_pass is False
    assert "STALE" in result.tags


@needs_llm
def test_review_output_fields_are_typed():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    inp = EvidenceReviewInput(
        control_id="A.9.1",
        control_description="Access control policy is established.",
        artifact_filename="access_policy.pdf",
        artifact_text=f"Access Control Policy v2.3 — Production\nApproved: {date.today().isoformat()}",
        collection_date=date.today().isoformat(),
        system_name="Production",
    )
    result = EvidenceReviewerAgent().review(inp)

    assert isinstance(result.control_id, str)
    assert isinstance(result.artifact_filename, str)
    assert isinstance(result.completeness_score, int)
    assert isinstance(result.freshness_pass, bool)
    assert isinstance(result.relevance_pass, bool)
    assert isinstance(result.tags, list)
    assert isinstance(result.recommendation, str)


@needs_llm
def test_review_batch_processes_all_artifacts():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    today = date.today().isoformat()
    artifacts = [
        EvidenceReviewInput(
            control_id=f"CC{i}.1",
            control_description="Control description.",
            artifact_filename=f"artifact_{i}.pdf",
            artifact_text=f"Evidence content for control {i}. Date: {today}. System: TestApp.",
            collection_date=today,
            system_name="TestApp",
        )
        for i in range(1, 4)
    ]
    results = EvidenceReviewerAgent().review_batch(artifacts)

    assert len(results) == 3
    assert all(r.control_id.startswith("CC") for r in results)
