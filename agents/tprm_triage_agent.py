from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from core.models import VendorIntakeInput, VendorRiskProfile

SYSTEM_PROMPT = """You are a third-party risk analyst responsible for vendor intake and tiering.

Tiering criteria:
- CRITICAL: Processes PII or financial data AND is hosted outside home country OR has significant sub-processor dependencies
- HIGH: Processes PII or financial data, has a SOC 2 but with noted exceptions, OR is an AI/ML vendor with data access
- MEDIUM: Limited data access, strong compliance posture, well-known vendor
- LOW: No data access, commodity SaaS, no sensitive processing

AI flag: Set ai_flag=true if uses_ai=true OR if the use-case description strongly implies AI/ML core product.
When ai_flag=true, always include "Send AI questionnaire" in next_steps.

Respond with valid JSON only (no markdown fences):
{
  "vendor_name": "...",
  "risk_tier": "Critical|High|Medium|Low",
  "tier_rationale": "...",
  "ai_flag": true/false,
  "next_steps": ["..."],
  "draft_profile_markdown": "full vendor risk profile in Markdown"
}"""


class TPRMTriageAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=SYSTEM_PROMPT)

    def triage_vendor(self, inp: VendorIntakeInput) -> VendorRiskProfile:
        prompt = (
            f"Triage this new vendor.\n\n"
            f"Vendor: {inp.vendor_name} ({inp.vendor_website})\n"
            f"Data Types Shared: {', '.join(inp.data_types_shared)}\n"
            f"Data Location: {inp.data_location}\n"
            f"SOC 2 Available: {inp.soc2_available}\n"
            f"Uses AI: {inp.uses_ai}\n"
            f"Business Justification: {inp.business_justification}\n\n"
            "Return valid JSON matching the VendorRiskProfile schema."
        )
        raw = self.run(prompt)
        try:
            data = json.loads(raw)
            return VendorRiskProfile(**data)
        except Exception:
            return VendorRiskProfile(
                vendor_name=inp.vendor_name,
                risk_tier="High",
                tier_rationale="Defaulted to High — manual triage required.",
                ai_flag=inp.uses_ai,
                next_steps=["Manual review required"],
                draft_profile_markdown=f"# {inp.vendor_name}\n\nManual triage required.\n",
            )

    def triage_batch(self, vendors: list[VendorIntakeInput]) -> list[VendorRiskProfile]:
        return [self.triage_vendor(v) for v in vendors]
