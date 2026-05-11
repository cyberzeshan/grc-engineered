"""Unit tests for tools/evidence_scorer.py — pure rule-based logic, no LLM."""
from __future__ import annotations

from datetime import date, timedelta
import pytest
from tools.evidence_scorer import EvidenceScorer


@pytest.fixture
def scorer():
    return EvidenceScorer()


def today():
    return date.today().isoformat()


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ── Freshness ─────────────────────────────────────────────────────────────────

def test_fresh_evidence_passes(scorer):
    r = scorer.score(
        artifact_text=f"Report — MyApp\nDate: {today()}\nAll users verified.",
        collection_date=today(),
        system_name="MyApp",
    )
    assert r["freshness_pass"] is True
    assert "STALE" not in r["tags"]


def test_evidence_exactly_90_days_passes(scorer):
    r = scorer.score(
        artifact_text=f"Report — SysX\nDate: {days_ago(90)}\nContent.",
        collection_date=days_ago(90),
        system_name="SysX",
    )
    assert r["freshness_pass"] is True


def test_evidence_91_days_fails(scorer):
    r = scorer.score(
        artifact_text="Report content.",
        collection_date=days_ago(91),
        system_name="",
    )
    assert r["freshness_pass"] is False
    assert "STALE" in r["tags"]


def test_invalid_date_tagged(scorer):
    r = scorer.score(
        artifact_text="Report content.",
        collection_date="not-a-date",
        system_name="",
    )
    assert r["freshness_pass"] is False
    assert "INVALID_DATE" in r["tags"]


# ── System name ───────────────────────────────────────────────────────────────

def test_system_name_present_in_artifact(scorer):
    r = scorer.score(
        artifact_text="Production AWS Account — access review.",
        collection_date=today(),
        system_name="Production AWS Account",
    )
    assert "MISSING_SYSTEM_NAME" not in r["tags"]


def test_system_name_missing_from_artifact(scorer):
    r = scorer.score(
        artifact_text="Generic report with no system identified.",
        collection_date=today(),
        system_name="MySuperApp",
    )
    assert "MISSING_SYSTEM_NAME" in r["tags"]


def test_system_name_check_is_case_insensitive(scorer):
    r = scorer.score(
        artifact_text="production aws account audit.",
        collection_date=today(),
        system_name="Production AWS Account",
    )
    assert "MISSING_SYSTEM_NAME" not in r["tags"]


# ── Timestamp ─────────────────────────────────────────────────────────────────

def test_artifact_with_year_has_timestamp(scorer):
    r = scorer.score(
        artifact_text="Audit completed in 2025.",
        collection_date=today(),
        system_name="",
    )
    assert "MISSING_TIMESTAMP" not in r["tags"]


def test_artifact_with_month_has_timestamp(scorer):
    r = scorer.score(
        artifact_text="Review completed in January.",
        collection_date=today(),
        system_name="",
    )
    assert "MISSING_TIMESTAMP" not in r["tags"]


def test_artifact_without_timestamp(scorer):
    r = scorer.score(
        artifact_text="Some generic report content with no date markers.",
        collection_date=today(),
        system_name="",
    )
    assert "MISSING_TIMESTAMP" in r["tags"]


# ── Keyword relevance ─────────────────────────────────────────────────────────

def test_relevant_artifact_no_irrelevant_tag(scorer):
    r = scorer.score(
        artifact_text="Access review completed. All user accounts verified.",
        collection_date=today(),
        system_name="",
        control_keywords=["access", "user"],
    )
    assert "IRRELEVANT" not in r["tags"]
    assert r["relevance_pass"] is True


def test_irrelevant_artifact_tagged(scorer):
    r = scorer.score(
        artifact_text="This document discusses office furniture procurement.",
        collection_date=today(),
        system_name="",
        control_keywords=["access", "authentication", "user"],
    )
    assert "IRRELEVANT" in r["tags"]
    assert r["relevance_pass"] is False


def test_no_keywords_skips_relevance_check(scorer):
    r = scorer.score(
        artifact_text="Any content here.",
        collection_date=today(),
        system_name="",
        control_keywords=None,
    )
    assert "IRRELEVANT" not in r["tags"]
    assert r["relevance_pass"] is True


# ── Completeness score ────────────────────────────────────────────────────────

def test_perfect_evidence_scores_100(scorer):
    r = scorer.score(
        artifact_text=f"Production AWS Account — access review. Date: {today()}. All users verified.",
        collection_date=today(),
        system_name="Production AWS Account",
        control_keywords=["access", "users"],
    )
    assert r["completeness_score"] == 100
    assert r["tags"] == []


def test_completeness_score_never_below_zero(scorer):
    r = scorer.score(
        artifact_text="Irrelevant content.",
        collection_date=days_ago(200),
        system_name="MissingSystem",
        control_keywords=["access", "users", "authentication"],
    )
    assert r["completeness_score"] >= 0


def test_multiple_failures_accumulate(scorer):
    perfect = scorer.score(
        artifact_text=f"MyApp\nDate: {today()}\naccess users.",
        collection_date=today(),
        system_name="MyApp",
        control_keywords=["access"],
    )
    degraded = scorer.score(
        artifact_text="irrelevant content",
        collection_date=days_ago(100),
        system_name="MissingApp",
        control_keywords=["access"],
    )
    assert degraded["completeness_score"] < perfect["completeness_score"]
