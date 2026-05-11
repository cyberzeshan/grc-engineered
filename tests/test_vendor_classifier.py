"""Unit tests for tools/vendor_classifier.py — pure rule-based logic, no LLM."""
from __future__ import annotations

import pytest
from tools.vendor_classifier import VendorClassifier


@pytest.fixture
def vc():
    return VendorClassifier()


# ── Risk tier classification ──────────────────────────────────────────────────

def test_no_data_soc2_available_is_low(vc):
    r = vc.classify(
        vendor_name="Generic SaaS",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
    )
    assert r["risk_tier"] == "Low"


def test_pii_with_soc2_no_high_risk_geo_is_high(vc):
    r = vc.classify(
        vendor_name="Payroll Inc.",
        data_types_shared=["PII", "financial"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
    )
    assert r["risk_tier"] == "High"


def test_pii_no_soc2_is_critical(vc):
    r = vc.classify(
        vendor_name="Risky Vendor",
        data_types_shared=["PII"],
        data_location="United States",
        soc2_available=False,
        uses_ai=False,
    )
    assert r["risk_tier"] == "Critical"


def test_pii_high_risk_geo_is_critical(vc):
    r = vc.classify(
        vendor_name="Foreign Vendor",
        data_types_shared=["PII"],
        data_location="China",
        soc2_available=True,
        uses_ai=False,
    )
    assert r["risk_tier"] == "Critical"


def test_ai_vendor_no_sensitive_data_is_medium(vc):
    r = vc.classify(
        vendor_name="AI Analytics",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=True,
    )
    assert r["risk_tier"] == "Medium"


def test_no_soc2_no_data_is_medium(vc):
    r = vc.classify(
        vendor_name="Small Startup",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=False,
        uses_ai=False,
    )
    assert r["risk_tier"] == "Medium"


# ── AI flag detection ─────────────────────────────────────────────────────────

def test_uses_ai_true_sets_flag(vc):
    r = vc.classify(
        vendor_name="AI Corp",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=True,
    )
    assert r["ai_flag"] is True


def test_uses_ai_false_no_flag(vc):
    r = vc.classify(
        vendor_name="Basic SaaS",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
    )
    assert r["ai_flag"] is False


def test_description_with_ai_keyword_sets_flag(vc):
    r = vc.classify(
        vendor_name="Clever Corp",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
        description="Machine learning-based analytics platform",
    )
    assert r["ai_flag"] is True


def test_description_with_llm_keyword_sets_flag(vc):
    r = vc.classify(
        vendor_name="LLM Vendor",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
        description="LLM-powered document processing",
    )
    assert r["ai_flag"] is True


# ── Next steps ────────────────────────────────────────────────────────────────

def test_ai_flag_adds_questionnaire_step(vc):
    r = vc.classify(
        vendor_name="AI Vendor",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=True,
    )
    assert "Send AI vendor questionnaire" in r["next_steps"]


def test_no_soc2_adds_request_step(vc):
    r = vc.classify(
        vendor_name="No SOC2 Vendor",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=False,
        uses_ai=False,
    )
    assert "Request SOC 2 Type II report" in r["next_steps"]


def test_critical_tier_adds_security_review_step(vc):
    r = vc.classify(
        vendor_name="Critical Vendor",
        data_types_shared=["PII"],
        data_location="United States",
        soc2_available=False,
        uses_ai=False,
    )
    assert "Schedule vendor security review call" in r["next_steps"]


def test_high_risk_geo_adds_legal_escalation(vc):
    r = vc.classify(
        vendor_name="Russia-based Vendor",
        data_types_shared=["PII"],
        data_location="Russia",
        soc2_available=True,
        uses_ai=False,
    )
    assert "Escalate to legal for data transfer impact assessment" in r["next_steps"]


def test_all_countries_detected(vc):
    for country in ["China", "Russia", "Iran", "North Korea", "Belarus"]:
        r = vc.classify(
            vendor_name="Test",
            data_types_shared=["PII"],
            data_location=country,
            soc2_available=True,
            uses_ai=False,
        )
        assert r["risk_tier"] == "Critical", f"Expected Critical for {country}"


def test_low_risk_has_empty_next_steps(vc):
    r = vc.classify(
        vendor_name="Safe Vendor",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
    )
    assert r["next_steps"] == []
