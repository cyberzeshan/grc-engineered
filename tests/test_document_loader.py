"""Unit tests for core/document_loader.py."""
from __future__ import annotations

import pytest
from core.document_loader import load_document, load_text_file


def test_load_text_file_reads_content(tmp_path):
    f = tmp_path / "policy.txt"
    f.write_text("This is the access control policy.", encoding="utf-8")
    assert load_text_file(f) == "This is the access control policy."


def test_load_text_file_handles_encoding_errors(tmp_path):
    f = tmp_path / "bad_encoding.txt"
    f.write_bytes(b"valid text \xff\xfe invalid bytes")
    result = load_text_file(f)
    assert "valid text" in result


def test_load_document_dispatches_txt(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Plain text document.", encoding="utf-8")
    assert load_document(f) == "Plain text document."


def test_load_document_dispatches_md(tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("# ISO 27001 Policy\n\nContent here.", encoding="utf-8")
    result = load_document(f)
    assert "ISO 27001 Policy" in result


def test_load_document_pdf(tmp_path):
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    pdf_path = tmp_path / "blank.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    result = load_document(pdf_path)
    assert isinstance(result, str)


def test_load_document_docx(tmp_path):
    pytest.importorskip("docx")
    from docx import Document
    doc = Document()
    doc.add_paragraph("Vendor risk assessment policy.")
    docx_path = tmp_path / "policy.docx"
    doc.save(str(docx_path))
    result = load_document(docx_path)
    assert "Vendor risk assessment policy." in result


def test_ingest_knowledge_directory(tmp_path):
    from core.document_loader import ingest_knowledge_directory
    from core.vector_store import VectorStore

    # Create a small knowledge directory
    kb = tmp_path / "knowledge"
    kb.mkdir()
    (kb / "iso27001.txt").write_text("ISO 27001 requires an ISMS.", encoding="utf-8")
    (kb / "soc2.txt").write_text("SOC 2 Trust Services Criteria CC6.1.", encoding="utf-8")
    (kb / "ignore.xyz").write_text("Not a supported format.", encoding="utf-8")

    vs = VectorStore(persist_dir=str(tmp_path / "chroma"))
    results = ingest_knowledge_directory(vs, knowledge_path=str(kb))

    assert "iso27001.txt" in results
    assert "soc2.txt" in results
    assert "ignore.xyz" not in results
    assert all(v >= 0 for v in results.values())
    assert vs.count() > 0
