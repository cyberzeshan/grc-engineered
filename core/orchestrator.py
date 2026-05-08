from __future__ import annotations

import os

import anthropic

from agents.base_agent import DEFAULT_MODEL

AGENT_KEYS = [
    "control_mapping",
    "evidence_review",
    "questionnaire",
    "policy_draft",
    "tprm_triage",
    "ai_registry",
    "audit_narrative",
]

CLASSIFIER_SYSTEM = """You are a GRC task router. Given a task description, return ONLY one of these
exact keys (no explanation, no punctuation):

control_mapping
evidence_review
questionnaire
policy_draft
tprm_triage
ai_registry
audit_narrative

Choose the key that best matches the task."""


class GRCOrchestrator:
    """Routes natural-language GRC tasks to the right specialized agent."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        # Lazy-import agents to avoid circular imports
        self._agent_map: dict | None = None

    @property
    def agent_map(self) -> dict:
        if self._agent_map is None:
            from agents.control_mapping_agent import ControlMappingAgent
            from agents.evidence_reviewer_agent import EvidenceReviewerAgent
            from agents.questionnaire_responder_agent import QuestionnaireResponderAgent
            from agents.policy_drafter_agent import PolicyDrafterAgent
            from agents.tprm_triage_agent import TPRMTriageAgent
            from agents.ai_registry_agent import AIRegistryAgent
            from agents.audit_narrative_agent import AuditNarrativeAgent

            self._agent_map = {
                "control_mapping": ControlMappingAgent,
                "evidence_review": EvidenceReviewerAgent,
                "questionnaire": QuestionnaireResponderAgent,
                "policy_draft": PolicyDrafterAgent,
                "tprm_triage": TPRMTriageAgent,
                "ai_registry": AIRegistryAgent,
                "audit_narrative": AuditNarrativeAgent,
            }
        return self._agent_map

    def classify(self, task: str) -> str:
        response = self.client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=20,
            system=CLASSIFIER_SYSTEM,
            messages=[{"role": "user", "content": task}],
        )
        key = response.content[0].text.strip().lower()
        # Validate — fall back to audit_narrative if unknown
        return key if key in AGENT_KEYS else "audit_narrative"

    def route(self, task: str) -> tuple[str, str]:
        """Classify and run the task. Returns (agent_key, output)."""
        agent_key = self.classify(task)
        agent = self.agent_map[agent_key]()
        output = agent.run(task)
        return agent_key, output
