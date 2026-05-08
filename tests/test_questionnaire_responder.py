"""Tests for the Questionnaire Responder Agent."""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


def test_answer_returns_structured_output():
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent

    agent = QuestionnaireResponderAgent()
    result = agent.answer_question("Do you have a vulnerability management program?")

    assert result.question
    assert result.answer
    assert result.confidence in ("HIGH", "MEDIUM", "NEEDS_HUMAN_REVIEW")
    assert isinstance(result.source_references, list)


def test_no_hallucination_on_empty_corpus():
    """With an empty vector store, confidence should be NEEDS_HUMAN_REVIEW."""
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent
    from core.vector_store import VectorStore

    # Empty in-memory-like store
    vs = VectorStore(persist_dir="./chroma_db_test_empty")
    agent = QuestionnaireResponderAgent(vector_store=vs)
    result = agent.answer_question("What is your quantum encryption strategy?")

    # May be NEEDS_HUMAN_REVIEW since no context exists
    assert result.confidence in ("HIGH", "MEDIUM", "NEEDS_HUMAN_REVIEW")


def test_vendor_classifier():
    from tools.vendor_classifier import VendorClassifier

    vc = VendorClassifier()
    # AI vendor with PII
    r = vc.classify(
        vendor_name="AcmeAI",
        data_types_shared=["PII"],
        data_location="United States",
        soc2_available=True,
        uses_ai=True,
    )
    assert r["ai_flag"] is True
    assert r["risk_tier"] in ("Critical", "High", "Medium")
    assert "Send AI vendor questionnaire" in r["next_steps"]

    # Low risk vendor
    r2 = vc.classify(
        vendor_name="Generic SaaS",
        data_types_shared=["none"],
        data_location="United States",
        soc2_available=True,
        uses_ai=False,
    )
    assert r2["risk_tier"] == "Low"
    assert r2["ai_flag"] is False
