from __future__ import annotations

import json

from agents.base_agent import BaseAgent, _strip_fences
from core.models import AuditNarrativeInput, AuditNarrativeOutput

SYSTEM_PROMPT = """You are a GRC lead preparing audit-ready documentation for SOC 2 and ISO 27001 assessments.

Narrative types:
- control_description: Clear, professional prose describing how a control operates in practice
- exception_memo: Structured memo with root cause, compensating controls, remediation plan, and timeline
- auditor_response: Direct, factual response to a specific auditor question with evidence citations

Writing standards:
- Auditor-ready: clear, confident, no hedging language
- Evidence-grounded: cite specific artifacts that support each claim
- Professional tone: formal but readable, third-person for control descriptions
- Appropriate length: 200-400 words for control descriptions, 300-600 for exception memos

Respond with valid JSON only (no markdown fences):
{
  "narrative_type": "...",
  "control_id": "...",
  "narrative_text": "polished prose",
  "word_count": 0,
  "suggested_evidence_refs": ["..."]
}"""


class AuditNarrativeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=SYSTEM_PROMPT)

    def draft_narrative(self, inp: AuditNarrativeInput) -> AuditNarrativeOutput:
        evidence_block = "\n".join(f"- {s}" for s in inp.evidence_summaries)
        extras = ""
        if inp.exception_details:
            extras += f"\nException Details:\n{inp.exception_details}"
        if inp.auditor_question:
            extras += f"\nAuditor Question:\n{inp.auditor_question}"

        prompt = (
            f"Draft a {inp.narrative_type.replace('_', ' ')}.\n\n"
            f"Control ID: {inp.control_id}\n"
            f"Control Description: {inp.control_description}\n"
            f"Evidence Summaries:\n{evidence_block}{extras}\n\n"
            "Return valid JSON matching the AuditNarrativeOutput schema."
        )
        raw = self.run_streaming(prompt)
        try:
            data = json.loads(_strip_fences(raw))
            data["word_count"] = len(data.get("narrative_text", "").split())
            return AuditNarrativeOutput(**data)
        except Exception:
            narrative = raw if len(raw) > 50 else "Unable to generate narrative."
            return AuditNarrativeOutput(
                narrative_type=inp.narrative_type,
                control_id=inp.control_id,
                narrative_text=narrative,
                word_count=len(narrative.split()),
                suggested_evidence_refs=[],
            )
