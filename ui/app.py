"""GRC Agent Platform — Streamlit demo dashboard."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="GRC Agent Platform",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ grc-engineered")

_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
if _provider == "ollama":
    _model = os.getenv("OLLAMA_MODEL", "llama3.2")
    st.sidebar.caption(f"Powered by Ollama · {_model}")
    _base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import httpx
        httpx.get(f"{_base_url}/api/tags", timeout=2)
    except Exception:
        st.sidebar.error(
            f"Ollama not reachable at {_base_url}. "
            "Make sure Ollama is running: `ollama serve`"
        )
else:
    _model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    st.sidebar.caption(f"Powered by Claude · {_model}")
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.sidebar.error("ANTHROPIC_API_KEY not set. Add it to your .env file.")

agent_choice = st.sidebar.radio(
    "Select Agent",
    [
        "🗂 Control Mapping",
        "📋 Evidence Reviewer",
        "❓ Questionnaire Responder",
        "📝 Policy Drafter",
        "🏢 TPRM Triage",
        "🤖 AI Registry",
        "📄 Audit Narrative",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Resources**")
st.sidebar.markdown(
    "[GitHub Repository](https://github.com/cyberzeshan/grc-engineered) | "
    "[README](https://github.com/cyberzeshan/grc-engineered#readme)"
)


# ── Helper ───────────────────────────────────────────────────────────────────
def render_json(data: dict | list) -> None:
    st.json(data)


def run_agent_safe(fn):
    try:
        return fn()
    except Exception as exc:
        st.error(f"Agent error: {exc}")
        return None


# ── Pages ────────────────────────────────────────────────────────────────────

if agent_choice == "🗂 Control Mapping":
    st.title("Control Mapping Agent")
    st.caption("Maps controls across ISO 27001, SOC 2, NIST CSF, and ISO 42001. Produces OSCAL JSON.")

    with st.form("control_mapping_form"):
        control_id = st.text_input("Control ID", value="A.8.2")
        framework_source = st.selectbox(
            "Source Framework",
            ["ISO_27001_2022", "SOC2_TSC", "NIST_CSF_2", "ISO_42001"],
        )
        target_frameworks = st.multiselect(
            "Target Frameworks",
            ["ISO_27001_2022", "SOC2_TSC", "NIST_CSF_2", "ISO_42001"],
            default=["SOC2_TSC", "NIST_CSF_2"],
        )
        ccf_text = st.text_area(
            "Current CCF Text",
            value="The organization classifies information in terms of legal requirements, value, criticality and sensitivity to unauthorized disclosure or modification.",
            height=120,
        )
        submitted = st.form_submit_button("Run Agent")

    if submitted:
        with st.spinner("Running Control Mapping Agent..."):
            from agents.control_mapping_agent import ControlMappingAgent
            from core.models import ControlMappingInput

            inp = ControlMappingInput(
                control_id=control_id,
                framework_source=framework_source,
                target_frameworks=target_frameworks,
                current_ccf_text=ccf_text,
            )
            agent = ControlMappingAgent()
            result = run_agent_safe(lambda: agent.map_control(inp))

        if result:
            st.success("Control mapping complete")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Mappings")
                for fw, ref in result.mappings.items():
                    st.write(f"**{fw}** → `{ref}`")
                if result.gaps:
                    st.warning("Gaps: " + ", ".join(result.gaps))
                if result.drift_alerts:
                    st.error("Drift Alerts: " + "\n".join(result.drift_alerts))
            with col2:
                st.subheader("OSCAL Fragment")
                st.json(result.oscal_fragment)


elif agent_choice == "📋 Evidence Reviewer":
    st.title("Evidence Reviewer Agent")
    st.caption("Scores evidence artifacts for completeness, freshness, and relevance.")

    with st.form("evidence_form"):
        col1, col2 = st.columns(2)
        with col1:
            control_id = st.text_input("Control ID", value="CC6.1")
            control_desc = st.text_area("Control Description", value="Logical access is restricted to authorized users.", height=80)
            artifact_filename = st.text_input("Artifact Filename", value="access_review_q1.pdf")
        with col2:
            system_name = st.text_input("System Name", value="AWS Production Account")
            collection_date = st.date_input("Collection Date")
        artifact_text = st.text_area(
            "Artifact Content (paste extracted text)",
            value="Quarterly Access Review — AWS Production Account\nDate: 2025-01-15\nAll 47 active users verified.",
            height=150,
        )
        submitted = st.form_submit_button("Run Agent")

    if submitted:
        with st.spinner("Reviewing evidence..."):
            from agents.evidence_reviewer_agent import EvidenceReviewerAgent
            from core.models import EvidenceReviewInput

            inp = EvidenceReviewInput(
                control_id=control_id,
                control_description=control_desc,
                artifact_filename=artifact_filename,
                artifact_text=artifact_text,
                collection_date=str(collection_date),
                system_name=system_name,
            )
            agent = EvidenceReviewerAgent()
            result = run_agent_safe(lambda: agent.review(inp))

        if result:
            st.subheader("Review Result")
            col1, col2, col3 = st.columns(3)
            color = "green" if result.completeness_score >= 75 else ("orange" if result.completeness_score >= 50 else "red")
            col1.metric("Completeness Score", f"{result.completeness_score}/100")
            col2.metric("Freshness", "PASS" if result.freshness_pass else "FAIL")
            col3.metric("Relevance", "PASS" if result.relevance_pass else "FAIL")
            if result.tags:
                for tag in result.tags:
                    st.warning(f"Tag: {tag}")
            st.info(f"**Recommendation:** {result.recommendation}")


elif agent_choice == "❓ Questionnaire Responder":
    st.title("Questionnaire Responder Agent")
    st.caption("Answers security questionnaire questions from your CCF/policy corpus.")

    questions_input = st.text_area(
        "Enter questions (one per line)",
        value="Do you have a vulnerability management program?\nHow do you handle access reviews?\nDescribe your incident response process.",
        height=150,
    )
    if st.button("Run Agent"):
        questions = [q.strip() for q in questions_input.strip().split("\n") if q.strip()]
        if not questions:
            st.warning("Please enter at least one question.")
        else:
            with st.spinner(f"Answering {len(questions)} questions..."):
                from agents.questionnaire_responder_agent import QuestionnaireResponderAgent

                agent = QuestionnaireResponderAgent()
                answers = run_agent_safe(lambda: agent.answer_questionnaire(questions))

            if answers:
                for i, ans in enumerate(answers, 1):
                    color = {"HIGH": "🟢", "MEDIUM": "🟡", "NEEDS_HUMAN_REVIEW": "🔴"}.get(ans.confidence, "⚪")
                    with st.expander(f"{color} Q{i}: {ans.question[:80]}...", expanded=i == 1):
                        st.write(ans.answer)
                        st.caption(f"Confidence: **{ans.confidence}** | Sources: {', '.join(ans.source_references) or 'none'}")


elif agent_choice == "📝 Policy Drafter":
    st.title("Policy Drafter Agent")
    st.caption("Drafts policy revisions triggered by framework updates or risk events.")

    with st.form("policy_form"):
        col1, col2 = st.columns(2)
        with col1:
            policy_name = st.text_input("Policy Name", value="AI Acceptable Use Policy")
            trigger_source = st.text_input("Trigger Source", value="ISO 42001:2023")
            effective_date = st.date_input("Effective Date")
        with col2:
            change_trigger = st.text_area(
                "Change Trigger",
                value="ISO 42001 Annex A clause A.6.2 now requires explicit documentation of AI system risk assessments before deployment.",
                height=100,
            )
        current_policy = st.text_area(
            "Current Policy Text",
            value="# AI Acceptable Use Policy\n\n## 1. Purpose\nThis policy governs the use of AI tools by employees.\n\n## 2. Scope\nAll employees using AI-assisted tools.\n\n## 3. Permitted Uses\nAI tools may be used for productivity, code assistance, and content drafting.\n\n## 4. Prohibited Uses\nAI tools may not be used to process confidential customer data.",
            height=200,
        )
        submitted = st.form_submit_button("Draft Revision")

    if submitted:
        with st.spinner("Drafting policy revision..."):
            from agents.policy_drafter_agent import PolicyDrafterAgent
            from core.models import PolicyDraftInput

            inp = PolicyDraftInput(
                policy_name=policy_name,
                current_policy_text=current_policy,
                change_trigger=change_trigger,
                trigger_source=trigger_source,
                effective_date=str(effective_date),
            )
            agent = PolicyDrafterAgent()
            result = run_agent_safe(lambda: agent.draft_revision(inp))

        if result:
            st.subheader("Revised Policy")
            st.markdown(result.revised_policy_text)
            st.subheader("Change Log Entry")
            st.json(result.change_log_entry)


elif agent_choice == "🏢 TPRM Triage":
    st.title("TPRM Triage Agent")
    st.caption("Auto-tiers vendors and flags AI-class vendors for specialized questionnaires.")

    with st.form("tprm_form"):
        col1, col2 = st.columns(2)
        with col1:
            vendor_name = st.text_input("Vendor Name", value="Acme Payroll Inc.")
            vendor_website = st.text_input("Website", value="https://acmepayroll.com")
            data_location = st.text_input("Data Processing Location", value="United States")
        with col2:
            data_types = st.multiselect(
                "Data Types Shared",
                ["PII", "financial", "health", "biometric", "none"],
                default=["PII", "financial"],
            )
            soc2_available = st.checkbox("SOC 2 Available", value=True)
            uses_ai = st.checkbox("Vendor Uses AI/ML")
        business_justification = st.text_area("Business Justification", value="Payroll processing for all employees.", height=80)
        submitted = st.form_submit_button("Triage Vendor")

    if submitted:
        with st.spinner("Triaging vendor..."):
            from agents.tprm_triage_agent import TPRMTriageAgent
            from core.models import VendorIntakeInput

            inp = VendorIntakeInput(
                vendor_name=vendor_name,
                vendor_website=vendor_website,
                data_types_shared=data_types,
                data_location=data_location,
                soc2_available=soc2_available,
                uses_ai=uses_ai,
                business_justification=business_justification,
            )
            agent = TPRMTriageAgent()
            result = run_agent_safe(lambda: agent.triage_vendor(inp))

        if result:
            tier_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
            icon = tier_colors.get(result.risk_tier, "⚪")
            st.metric("Risk Tier", f"{icon} {result.risk_tier}")
            if result.ai_flag:
                st.warning("AI vendor flagged — send AI questionnaire")
            st.write(f"**Rationale:** {result.tier_rationale}")
            st.subheader("Next Steps")
            for step in result.next_steps:
                st.write(f"• {step}")
            st.subheader("Draft Vendor Profile")
            st.markdown(result.draft_profile_markdown)


elif agent_choice == "🤖 AI Registry":
    st.title("AI Use-Case Registry Agent")
    st.caption("Creates EU AI Act-compliant registry entries for AI tools.")

    with st.form("ai_registry_form"):
        col1, col2 = st.columns(2)
        with col1:
            system_name = st.text_input("AI System Name", value="GitHub Copilot")
            vendor = st.text_input("Vendor", value="Microsoft / GitHub")
            business_owner = st.text_input("Business Owner", value="Engineering")
        with col2:
            personal_data = st.checkbox("Personal Data Involved")
            auto_decision = st.checkbox("Automated Decision Making")
            oversight = st.text_input("Human Oversight Mechanism", value="Developer reviews all suggestions before acceptance")
        use_case = st.text_area(
            "Use Case Description",
            value="Code completion and suggestion tool used by software engineers. Provides real-time code suggestions based on context. No customer data is passed to the model.",
            height=100,
        )
        submitted = st.form_submit_button("Register Use Case")

    if submitted:
        with st.spinner("Creating registry entry..."):
            from agents.ai_registry_agent import AIRegistryAgent
            from core.models import AIUseCaseInput

            inp = AIUseCaseInput(
                system_name=system_name,
                vendor=vendor,
                business_owner=business_owner,
                use_case_description=use_case,
                personal_data_involved=personal_data,
                automated_decision_making=auto_decision,
                human_oversight_mechanism=oversight,
            )
            agent = AIRegistryAgent()
            result = run_agent_safe(lambda: agent.register_use_case(inp))

        if result:
            risk_icons = {
                "Minimal Risk": "🟢",
                "Limited Risk": "🟡",
                "High Risk": "🟠",
                "Unacceptable Risk": "🔴",
            }
            icon = risk_icons.get(result.eu_ai_act_classification, "⚪")
            st.metric("EU AI Act Classification", f"{icon} {result.eu_ai_act_classification}")
            st.write(f"**Rationale:** {result.classification_rationale}")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Residual Risks")
                for r in result.residual_risks:
                    st.write(f"• {r}")
            with col2:
                st.subheader("Controls Required")
                for c in result.controls_required:
                    st.write(f"• {c}")
            st.write(f"**Review Frequency:** {result.review_frequency}")
            st.subheader("Registry Entry")
            st.markdown(result.registry_entry_markdown)


elif agent_choice == "📄 Audit Narrative":
    st.title("Audit Narrative Agent")
    st.caption("Drafts audit-ready control descriptions, exception memos, and auditor responses.")

    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            narrative_type = st.selectbox(
                "Narrative Type",
                ["control_description", "exception_memo", "auditor_response"],
            )
            control_id = st.text_input("Control ID", value="CC6.1")
        with col2:
            control_desc = st.text_area("Control Description", value="Logical access to systems is restricted to authorized users through role-based access controls.", height=80)
        evidence = st.text_area(
            "Evidence Summaries (one per line)",
            value="Q1 2025 access review — 47 users verified, 3 terminated accounts removed\nRole-based access policy v2.3 approved January 2025\nAWS IAM policy export showing principle of least privilege",
            height=100,
        )
        exception_details = auditor_question = ""
        if narrative_type == "exception_memo":
            exception_details = st.text_area("Exception Details", value="MFA was not enforced for 2 service accounts for 14 days during infrastructure migration.", height=80)
        elif narrative_type == "auditor_response":
            auditor_question = st.text_input("Auditor Question", value="How does the organization ensure access rights are reviewed and revoked when employees leave?")
        submitted = st.form_submit_button("Draft Narrative")

    if submitted:
        with st.spinner("Drafting narrative..."):
            from agents.audit_narrative_agent import AuditNarrativeAgent
            from core.models import AuditNarrativeInput

            inp = AuditNarrativeInput(
                narrative_type=narrative_type,
                control_id=control_id,
                control_description=control_desc,
                evidence_summaries=[e.strip() for e in evidence.strip().split("\n") if e.strip()],
                exception_details=exception_details or None,
                auditor_question=auditor_question or None,
            )
            agent = AuditNarrativeAgent()
            result = run_agent_safe(lambda: agent.draft_narrative(inp))

        if result:
            st.subheader(f"Narrative — {result.narrative_type.replace('_', ' ').title()}")
            st.write(result.narrative_text)
            st.caption(f"Word count: {result.word_count}")
            if result.suggested_evidence_refs:
                st.subheader("Suggested Evidence References")
                for ref in result.suggested_evidence_refs:
                    st.write(f"• {ref}")
