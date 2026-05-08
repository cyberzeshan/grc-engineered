from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ── Control Mapping ──────────────────────────────────────────────────────────

class ControlMappingInput(BaseModel):
    control_id: str
    framework_source: str
    target_frameworks: list[str]
    current_ccf_text: str


class ControlMappingOutput(BaseModel):
    control_id: str
    mappings: dict[str, str]
    gaps: list[str]
    drift_alerts: list[str]
    oscal_fragment: dict[str, Any]


# ── Evidence Reviewer ────────────────────────────────────────────────────────

class EvidenceReviewInput(BaseModel):
    control_id: str
    control_description: str
    artifact_filename: str
    artifact_text: str
    collection_date: str
    system_name: str


class EvidenceReviewOutput(BaseModel):
    control_id: str
    artifact_filename: str
    completeness_score: int = Field(ge=0, le=100)
    freshness_pass: bool
    relevance_pass: bool
    tags: list[str]
    recommendation: str


# ── Questionnaire Responder ──────────────────────────────────────────────────

class QuestionnaireAnswer(BaseModel):
    question: str
    answer: str
    confidence: str  # "HIGH" | "MEDIUM" | "NEEDS_HUMAN_REVIEW"
    source_references: list[str]


# ── Policy Drafter ───────────────────────────────────────────────────────────

class PolicyDraftInput(BaseModel):
    policy_name: str
    current_policy_text: str
    change_trigger: str
    trigger_source: str
    effective_date: str


class PolicyDraftOutput(BaseModel):
    policy_name: str
    revised_policy_text: str
    change_log_entry: dict[str, Any]
    sections_changed: list[str]


# ── TPRM Triage ──────────────────────────────────────────────────────────────

class VendorIntakeInput(BaseModel):
    vendor_name: str
    vendor_website: str
    data_types_shared: list[str]
    data_location: str
    soc2_available: bool
    uses_ai: bool
    business_justification: str


class VendorRiskProfile(BaseModel):
    vendor_name: str
    risk_tier: str  # "Critical" | "High" | "Medium" | "Low"
    tier_rationale: str
    ai_flag: bool
    next_steps: list[str]
    draft_profile_markdown: str


# ── AI Registry ──────────────────────────────────────────────────────────────

class AIUseCaseInput(BaseModel):
    system_name: str
    vendor: str
    business_owner: str
    use_case_description: str
    personal_data_involved: bool
    automated_decision_making: bool
    human_oversight_mechanism: str


class AIRegistryEntry(BaseModel):
    system_name: str
    eu_ai_act_classification: str
    classification_rationale: str
    residual_risks: list[str]
    controls_required: list[str]
    review_frequency: str
    registry_entry_markdown: str


# ── Audit Narrative ──────────────────────────────────────────────────────────

class AuditNarrativeInput(BaseModel):
    narrative_type: str  # "control_description" | "exception_memo" | "auditor_response"
    control_id: str
    control_description: str
    evidence_summaries: list[str]
    exception_details: str | None = None
    auditor_question: str | None = None


class AuditNarrativeOutput(BaseModel):
    narrative_type: str
    control_id: str
    narrative_text: str
    word_count: int
    suggested_evidence_refs: list[str]
