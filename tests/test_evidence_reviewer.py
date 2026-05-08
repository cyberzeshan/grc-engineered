"""Tests for the Evidence Reviewer Agent."""
import os
import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


def test_review_good_evidence():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    inp = EvidenceReviewInput(
        control_id="CC6.1",
        control_description="Logical access is restricted to authorized users.",
        artifact_filename="access_review_q1.pdf",
        artifact_text=(
            f"Quarterly Access Review — Production AWS Account\n"
            f"Date: {date.today().isoformat()}\n"
            "Reviewer: Jane Smith\nAll 47 users verified. 3 terminated accounts removed."
        ),
        collection_date=date.today().isoformat(),
        system_name="Production AWS Account",
    )
    agent = EvidenceReviewerAgent()
    result = agent.review(inp)

    assert result.control_id == "CC6.1"
    assert result.freshness_pass is True
    assert isinstance(result.completeness_score, int)
    assert 0 <= result.completeness_score <= 100


def test_review_stale_evidence():
    from agents.evidence_reviewer_agent import EvidenceReviewerAgent
    from core.models import EvidenceReviewInput

    stale_date = (date.today() - timedelta(days=120)).isoformat()
    inp = EvidenceReviewInput(
        control_id="CC7.1",
        control_description="Vulnerabilities are identified and remediated.",
        artifact_filename="vuln_scan_old.csv",
        artifact_text="Vulnerability scan export. Date: 2024-01-01. No system identified.",
        collection_date=stale_date,
        system_name="",
    )
    agent = EvidenceReviewerAgent()
    result = agent.review(inp)

    assert result.freshness_pass is False
    assert "STALE" in result.tags


def test_evidence_scorer_rules():
    from tools.evidence_scorer import EvidenceScorer

    scorer = EvidenceScorer()
    # Good evidence
    r = scorer.score(
        artifact_text=f"Access Review — MyApp\nDate: {date.today().isoformat()}\nAll users verified.",
        collection_date=date.today().isoformat(),
        system_name="MyApp",
        control_keywords=["access", "users"],
    )
    assert r["freshness_pass"] is True
    assert r["completeness_score"] > 50
    assert not r["tags"]

    # Stale evidence
    r2 = scorer.score(
        artifact_text="Some evidence",
        collection_date=(date.today() - timedelta(days=100)).isoformat(),
        system_name="X",
    )
    assert r2["freshness_pass"] is False
    assert "STALE" in r2["tags"]
