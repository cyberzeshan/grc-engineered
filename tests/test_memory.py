"""Unit tests for core/memory.py — uses a temporary SQLite database."""
from __future__ import annotations

import pytest
from core.memory import SessionMemory


@pytest.fixture
def mem(tmp_path):
    return SessionMemory(db_path=str(tmp_path / "test_memory.db"))


def test_save_and_get_session_roundtrip(mem):
    ctx = {"agent": "evidence_reviewer", "run_id": "abc123", "score": 87}
    mem.save_session("session-1", "evidence_reviewer", ctx)
    result = mem.get_session("session-1")
    assert result == ctx


def test_get_session_unknown_id_returns_none(mem):
    assert mem.get_session("does-not-exist") is None


def test_save_session_updates_existing(mem):
    mem.save_session("s1", "questionnaire", {"step": 1})
    mem.save_session("s1", "questionnaire", {"step": 2})
    result = mem.get_session("s1")
    assert result["step"] == 2


def test_log_run_appears_in_history(mem):
    mem.log_run("s1", "tprm_triage", "Vendor: Acme", "Tier: High")
    history = mem.get_run_history()
    assert len(history) == 1
    assert history[0]["agent_type"] == "tprm_triage"
    assert history[0]["input_summary"] == "Vendor: Acme"
    assert history[0]["output_summary"] == "Tier: High"


def test_get_run_history_filtered_by_agent_type(mem):
    mem.log_run("s1", "evidence_review", "artifact.pdf", "Score: 90")
    mem.log_run("s2", "tprm_triage", "Vendor: X", "Tier: Low")
    mem.log_run("s3", "evidence_review", "artifact2.pdf", "Score: 60")

    evidence_runs = mem.get_run_history(agent_type="evidence_review")
    assert len(evidence_runs) == 2
    assert all(r["agent_type"] == "evidence_review" for r in evidence_runs)


def test_get_run_history_limit(mem):
    for i in range(10):
        mem.log_run(f"s{i}", "audit_narrative", f"input {i}", f"output {i}")

    limited = mem.get_run_history(limit=3)
    assert len(limited) == 3


def test_get_run_history_ordered_newest_first(mem):
    mem.log_run("s1", "policy_draft", "trigger 1", "draft 1")
    mem.log_run("s2", "policy_draft", "trigger 2", "draft 2")

    history = mem.get_run_history(agent_type="policy_draft")
    assert history[0]["input_summary"] == "trigger 2"


def test_multiple_sessions_are_independent(mem):
    mem.save_session("alpha", "questionnaire", {"q": "What is SOC 2?"})
    mem.save_session("beta", "questionnaire", {"q": "What is ISO 27001?"})

    assert mem.get_session("alpha")["q"] == "What is SOC 2?"
    assert mem.get_session("beta")["q"] == "What is ISO 27001?"


def test_session_context_preserves_nested_structures(mem):
    ctx = {
        "results": [{"id": 1, "score": 95}, {"id": 2, "score": 70}],
        "metadata": {"run": "batch-1"},
    }
    mem.save_session("nested", "evidence_review", ctx)
    result = mem.get_session("nested")
    assert result["results"][0]["score"] == 95
    assert result["metadata"]["run"] == "batch-1"
