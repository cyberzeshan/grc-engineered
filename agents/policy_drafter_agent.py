from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from agents.base_agent import BaseAgent
from core.models import PolicyDraftInput, PolicyDraftOutput

SYSTEM_PROMPT = """You are a senior GRC writer responsible for maintaining the organization's policy library.

When given a change trigger (new regulation text, updated framework clause, or risk event):
1. Produce a full revised policy in structured Markdown, clearly showing what changed
2. Every revision must include a change log entry with date, trigger, and a one-sentence rationale
3. Mark changed sections with <!-- CHANGED: reason --> comments in the Markdown
4. Be conservative — only change what the trigger requires; do not refactor unrelated sections
5. Preserve the original policy structure and numbering

Respond with valid JSON only (no markdown fences):
{
  "policy_name": "...",
  "revised_policy_text": "full revised Markdown",
  "change_log_entry": {
    "date": "YYYY-MM-DD",
    "trigger": "...",
    "rationale": "one-sentence rationale",
    "changed_sections": ["section names"]
  },
  "sections_changed": ["section names"]
}"""


class PolicyDrafterAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=SYSTEM_PROMPT)

    def draft_revision(self, inp: PolicyDraftInput) -> PolicyDraftOutput:
        prompt = (
            f"Draft a policy revision.\n\n"
            f"Policy Name: {inp.policy_name}\n"
            f"Effective Date: {inp.effective_date}\n"
            f"Change Trigger: {inp.change_trigger}\n"
            f"Trigger Source: {inp.trigger_source}\n\n"
            f"Current Policy Text:\n{inp.current_policy_text}\n\n"
            "Return valid JSON matching the PolicyDraftOutput schema."
        )
        raw = self.run_streaming(prompt)
        try:
            data = json.loads(raw)
            return PolicyDraftOutput(**data)
        except Exception:
            return PolicyDraftOutput(
                policy_name=inp.policy_name,
                revised_policy_text=raw,
                change_log_entry={
                    "date": date.today().isoformat(),
                    "trigger": inp.change_trigger,
                    "rationale": "Auto-generated — manual review required.",
                    "changed_sections": [],
                },
                sections_changed=[],
            )

    def save_outputs(self, output: PolicyDraftOutput, output_dir: str = "./outputs") -> dict[str, str]:
        base = Path(output_dir)
        base.mkdir(parents=True, exist_ok=True)
        safe_name = output.policy_name.replace(" ", "_").lower()
        md_path = base / f"{safe_name}_revised.md"
        log_path = base / f"{safe_name}_change_log.json"
        md_path.write_text(output.revised_policy_text, encoding="utf-8")
        log_path.write_text(json.dumps(output.change_log_entry, indent=2), encoding="utf-8")
        return {"markdown": str(md_path), "change_log": str(log_path)}
