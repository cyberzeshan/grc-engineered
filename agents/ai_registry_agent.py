from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from agents.base_agent import BaseAgent, _strip_fences
from core.models import AIUseCaseInput, AIRegistryEntry

SYSTEM_PROMPT = """You are an AI governance specialist maintaining the organization's AI use-case registry
in compliance with the EU AI Act.

Classification framework (EU AI Act):
- UNACCEPTABLE RISK (Article 5): Prohibited — social scoring, real-time biometric surveillance, manipulation
- HIGH RISK (Article 6 + Annex III): CV screening, credit scoring, access to education/employment, law enforcement
- LIMITED RISK (Article 50): Chatbots, deepfake detection, emotion recognition — transparency obligations apply
- MINIMAL RISK: Code assistants, recommendation engines, spam filters — no specific obligations

For each entry:
1. Apply the correct EU AI Act classification with rationale citing the relevant article
2. Identify residual risks specific to this deployment
3. Specify controls required for compliance
4. Recommend review frequency (Quarterly/Annually/Bi-annually)

Respond with valid JSON only (no markdown fences):
{
  "system_name": "...",
  "eu_ai_act_classification": "Unacceptable Risk|High Risk|Limited Risk|Minimal Risk",
  "classification_rationale": "citing Article ...",
  "residual_risks": ["..."],
  "controls_required": ["..."],
  "review_frequency": "Quarterly|Annually|Bi-annually",
  "registry_entry_markdown": "full registry entry in Markdown"
}"""


class AIRegistryAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=SYSTEM_PROMPT)

    def register_use_case(self, inp: AIUseCaseInput) -> AIRegistryEntry:
        prompt = (
            f"Create an AI registry entry.\n\n"
            f"System Name: {inp.system_name}\n"
            f"Vendor: {inp.vendor}\n"
            f"Business Owner: {inp.business_owner}\n"
            f"Use Case: {inp.use_case_description}\n"
            f"Personal Data Involved: {inp.personal_data_involved}\n"
            f"Automated Decision Making: {inp.automated_decision_making}\n"
            f"Human Oversight Mechanism: {inp.human_oversight_mechanism}\n\n"
            "Return valid JSON matching the AIRegistryEntry schema."
        )
        raw = self.run(prompt)
        try:
            data = json.loads(_strip_fences(raw))
            return AIRegistryEntry(**data)
        except Exception:
            return AIRegistryEntry(
                system_name=inp.system_name,
                eu_ai_act_classification="Limited Risk",
                classification_rationale="Defaulted — manual classification required.",
                residual_risks=["Manual review required"],
                controls_required=["Manual review required"],
                review_frequency="Annually",
                registry_entry_markdown=f"# {inp.system_name}\n\nManual classification required.\n",
            )

    def register_batch(self, use_cases: list[AIUseCaseInput]) -> list[AIRegistryEntry]:
        return [self.register_use_case(u) for u in use_cases]

    def save_registry(self, entries: list[AIRegistryEntry], output_dir: str = "./outputs") -> str:
        path = Path(output_dir) / "ai_registry.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        sections = [f"# AI Use-Case Registry\n\nGenerated {date.today()}\n"]
        for e in entries:
            sections.append(e.registry_entry_markdown)
        path.write_text("\n\n---\n\n".join(sections), encoding="utf-8")
        return str(path)
