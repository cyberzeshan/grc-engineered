"""Integration tests for AIRegistryAgent."""
from __future__ import annotations

import pytest
from tests.conftest import needs_llm

VALID_CLASSIFICATIONS = {"Unacceptable Risk", "High Risk", "Limited Risk", "Minimal Risk"}
VALID_FREQUENCIES = {"Quarterly", "Annually", "Bi-annually"}


@needs_llm
def test_register_minimal_risk_tool():
    from agents.ai_registry_agent import AIRegistryAgent
    from core.models import AIUseCaseInput

    inp = AIUseCaseInput(
        system_name="GitHub Copilot",
        vendor="Microsoft / GitHub",
        business_owner="Engineering",
        use_case_description=(
            "Code completion and suggestion tool for software engineers. "
            "No customer data is sent to the model."
        ),
        personal_data_involved=False,
        automated_decision_making=False,
        human_oversight_mechanism="Developer reviews all suggestions before acceptance.",
    )
    result = AIRegistryAgent().register_use_case(inp)

    assert result.system_name == "GitHub Copilot"
    assert result.eu_ai_act_classification in VALID_CLASSIFICATIONS
    assert isinstance(result.classification_rationale, str)
    assert isinstance(result.residual_risks, list)
    assert isinstance(result.controls_required, list)
    assert result.review_frequency in VALID_FREQUENCIES
    assert len(result.registry_entry_markdown) > 0


@needs_llm
def test_register_high_risk_tool():
    from agents.ai_registry_agent import AIRegistryAgent
    from core.models import AIUseCaseInput

    inp = AIUseCaseInput(
        system_name="CV Screener AI",
        vendor="HireBot Inc.",
        business_owner="HR",
        use_case_description=(
            "Automated CV screening tool that scores and ranks job applicants. "
            "Used to shortlist candidates for interviews."
        ),
        personal_data_involved=True,
        automated_decision_making=True,
        human_oversight_mechanism="HR manager reviews final shortlist.",
    )
    result = AIRegistryAgent().register_use_case(inp)

    # CV screening is explicitly listed in EU AI Act Annex III as High Risk
    assert result.eu_ai_act_classification in VALID_CLASSIFICATIONS
    assert len(result.controls_required) > 0


@needs_llm
def test_register_use_case_output_fields_typed():
    from agents.ai_registry_agent import AIRegistryAgent
    from core.models import AIUseCaseInput

    inp = AIUseCaseInput(
        system_name="Spam Filter",
        vendor="EmailCorp",
        business_owner="IT",
        use_case_description="Filters incoming spam email for employees.",
        personal_data_involved=False,
        automated_decision_making=False,
        human_oversight_mechanism="Users can report false positives.",
    )
    result = AIRegistryAgent().register_use_case(inp)

    assert isinstance(result.system_name, str)
    assert isinstance(result.eu_ai_act_classification, str)
    assert isinstance(result.classification_rationale, str)
    assert isinstance(result.residual_risks, list)
    assert isinstance(result.controls_required, list)
    assert isinstance(result.review_frequency, str)
    assert isinstance(result.registry_entry_markdown, str)


@needs_llm
def test_register_batch_and_save(tmp_path):
    from agents.ai_registry_agent import AIRegistryAgent
    from core.models import AIUseCaseInput

    use_cases = [
        AIUseCaseInput(
            system_name="Code Assistant",
            vendor="GitHub",
            business_owner="Engineering",
            use_case_description="Code completion for developers.",
            personal_data_involved=False,
            automated_decision_making=False,
            human_oversight_mechanism="Manual review by developer.",
        ),
        AIUseCaseInput(
            system_name="Chatbot",
            vendor="OpenAI",
            business_owner="Support",
            use_case_description="Customer support chatbot.",
            personal_data_involved=False,
            automated_decision_making=False,
            human_oversight_mechanism="Escalation to human agent available.",
        ),
    ]
    agent = AIRegistryAgent()
    entries = agent.register_batch(use_cases)

    assert len(entries) == 2
    assert all(e.eu_ai_act_classification in VALID_CLASSIFICATIONS for e in entries)

    registry_path = agent.save_registry(entries, output_dir=str(tmp_path))
    from pathlib import Path
    assert Path(registry_path).exists()
    content = Path(registry_path).read_text()
    assert "AI Use-Case Registry" in content
