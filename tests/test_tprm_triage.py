"""Integration tests for TPRMTriageAgent."""
from __future__ import annotations

import pytest
from tests.conftest import needs_llm

VALID_TIERS = {"Critical", "High", "Medium", "Low"}


@needs_llm
def test_triage_returns_valid_profile():
    from agents.tprm_triage_agent import TPRMTriageAgent
    from core.models import VendorIntakeInput

    inp = VendorIntakeInput(
        vendor_name="Acme Payroll Inc.",
        vendor_website="https://acmepayroll.com",
        data_types_shared=["PII", "financial"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
        business_justification="Payroll processing for all employees.",
    )
    result = TPRMTriageAgent().triage_vendor(inp)

    assert result.vendor_name == "Acme Payroll Inc."
    assert result.risk_tier in VALID_TIERS
    assert isinstance(result.tier_rationale, str)
    assert isinstance(result.ai_flag, bool)
    assert isinstance(result.next_steps, list)
    assert isinstance(result.draft_profile_markdown, str)


@needs_llm
def test_ai_vendor_flagged():
    from agents.tprm_triage_agent import TPRMTriageAgent
    from core.models import VendorIntakeInput

    inp = VendorIntakeInput(
        vendor_name="SmartHire AI",
        vendor_website="https://smarthireai.com",
        data_types_shared=["PII"],
        data_location="United States",
        soc2_available=True,
        uses_ai=True,
        business_justification="AI-powered recruitment screening tool.",
    )
    result = TPRMTriageAgent().triage_vendor(inp)

    assert result.ai_flag is True
    assert any("questionnaire" in step.lower() or "ai" in step.lower() for step in result.next_steps)


@needs_llm
def test_low_risk_vendor_tier():
    from agents.tprm_triage_agent import TPRMTriageAgent
    from core.models import VendorIntakeInput

    inp = VendorIntakeInput(
        vendor_name="Zoom Communications",
        vendor_website="https://zoom.us",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
        business_justification="Video conferencing for internal meetings only.",
    )
    result = TPRMTriageAgent().triage_vendor(inp)

    assert result.risk_tier in VALID_TIERS  # agent must return a valid tier
    assert len(result.draft_profile_markdown) > 0


@needs_llm
def test_triage_batch_processes_all_vendors():
    from agents.tprm_triage_agent import TPRMTriageAgent
    from core.models import VendorIntakeInput

    vendors = [
        VendorIntakeInput(
            vendor_name=f"Vendor {i}",
            vendor_website=f"https://vendor{i}.com",
            data_types_shared=["none"],
            data_location="United States",
            soc2_available=True,
            uses_ai=False,
            business_justification="Internal tool.",
        )
        for i in range(1, 3)
    ]
    results = TPRMTriageAgent().triage_batch(vendors)

    assert len(results) == 2
    assert all(r.risk_tier in VALID_TIERS for r in results)
