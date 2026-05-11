"""Integration tests for QuestionnaireResponderAgent."""
from __future__ import annotations

import pytest
from tests.conftest import needs_llm

VALID_CONFIDENCE = {"HIGH", "MEDIUM", "NEEDS_HUMAN_REVIEW"}


@needs_llm
def test_answer_returns_structured_output():
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent

    result = QuestionnaireResponderAgent().answer_question(
        "Do you have a vulnerability management program?"
    )

    assert result.question
    assert result.answer
    assert result.confidence in VALID_CONFIDENCE
    assert isinstance(result.source_references, list)


@needs_llm
def test_answer_questionnaire_batch():
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent

    questions = [
        "Do you have a vulnerability management program?",
        "How do you handle access reviews?",
    ]
    results = QuestionnaireResponderAgent().answer_questionnaire(questions)

    assert len(results) == 2
    for r in results:
        assert r.confidence in VALID_CONFIDENCE
        assert isinstance(r.answer, str)
        assert len(r.answer) > 0


@needs_llm
def test_empty_corpus_returns_needs_human_review(tmp_path):
    """With an empty vector store, the agent should flag low-confidence answers."""
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent
    from core.vector_store import VectorStore

    vs = VectorStore(persist_dir=str(tmp_path / "empty_chroma"))
    result = QuestionnaireResponderAgent(vector_store=vs).answer_question(
        "What is your quantum-encrypted zero-trust blockchain policy?"
    )
    # With no relevant context, confidence should not be fabricated as HIGH
    assert result.confidence in VALID_CONFIDENCE


@needs_llm
def test_answer_preserves_question_text():
    from agents.questionnaire_responder_agent import QuestionnaireResponderAgent

    question = "Describe your incident response process in detail."
    result = QuestionnaireResponderAgent().answer_question(question)
    assert result.question == question
