"""Unit tests for core/vector_store.py — uses a temporary ChromaDB directory."""
from __future__ import annotations

import pytest

pytest.importorskip("chromadb", reason="chromadb not installed — skipping vector store tests")

from core.vector_store import VectorStore, _chunk_text


@pytest.fixture
def vs(tmp_path):
    return VectorStore(persist_dir=str(tmp_path / "chroma_test"))


# ── _chunk_text ───────────────────────────────────────────────────────────────

def test_chunk_text_short_input_returns_one_chunk():
    text = "Short document."
    chunks = _chunk_text(text, chunk_size=1500, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_respects_chunk_size():
    text = "a" * 3000
    chunks = _chunk_text(text, chunk_size=1000, overlap=0)
    assert len(chunks) == 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_overlap_produces_shared_content():
    text = "a" * 2000
    chunks = _chunk_text(text, chunk_size=1000, overlap=200)
    # With overlap=200, first chunk ends at 1000, second starts at 800
    assert len(chunks) >= 2


def test_chunk_text_empty_input():
    assert _chunk_text("", chunk_size=1500, overlap=200) == []


def test_chunk_text_whitespace_only_skipped():
    text = "   \n\n   "
    chunks = _chunk_text(text, chunk_size=1500, overlap=200)
    assert chunks == []


# ── VectorStore ───────────────────────────────────────────────────────────────

def test_add_documents_increases_count(vs):
    assert vs.count() == 0
    vs.add_documents(["ISO 27001 requires access controls.", "SOC 2 CC6.1 covers logical access."])
    assert vs.count() == 2


def test_add_documents_empty_list_is_noop(vs):
    vs.add_documents([])
    assert vs.count() == 0


def test_query_returns_results(vs):
    vs.add_documents([
        "Access reviews must be performed quarterly.",
        "Vulnerability scans must be run monthly.",
        "Encryption at rest is required for all PII.",
    ])
    results = vs.query("How often should access reviews happen?", n_results=1)
    assert len(results) == 1
    assert isinstance(results[0], str)
    assert len(results[0]) > 0


def test_query_empty_store_returns_empty(vs):
    results = vs.query("access controls", n_results=3)
    assert results == []


def test_query_n_results_capped_to_collection_size(vs):
    vs.add_documents(["Only one document in the store."])
    results = vs.query("document", n_results=10)
    assert len(results) == 1


def test_query_with_metadata_returns_expected_structure(vs):
    vs.add_documents(
        documents=["ISO 27001 A.9.1 requires access control policies."],
        metadatas=[{"source": "ISO_27001.txt", "chunk": 0}],
    )
    results = vs.query_with_metadata("access control policy", n_results=1)
    assert len(results) == 1
    record = results[0]
    assert "text" in record
    assert "metadata" in record
    assert "distance" in record
    assert record["metadata"]["source"] == "ISO_27001.txt"


def test_ingest_file_creates_chunks(vs, tmp_path):
    doc = tmp_path / "framework.txt"
    doc.write_text("a" * 4000, encoding="utf-8")  # 4000 chars → 3 chunks at 1500/200

    n = vs.ingest_file(doc)
    assert n > 0
    assert vs.count() == n


def test_ingest_file_deduplicates_on_reingest(vs, tmp_path):
    doc = tmp_path / "policy.txt"
    doc.write_text("Security policy text. " * 100, encoding="utf-8")

    n1 = vs.ingest_file(doc)
    n2 = vs.ingest_file(doc)  # same file, same IDs — should overwrite not duplicate

    assert vs.count() == n1
    assert n1 == n2


def test_add_documents_with_custom_ids(vs):
    vs.add_documents(
        documents=["Control A.8.2 — Information classification"],
        ids=["ctrl-a82"],
    )
    assert vs.count() == 1
