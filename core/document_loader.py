from __future__ import annotations

import os
from pathlib import Path


def load_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def load_pdf(path: str | Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        raise RuntimeError("pypdf not installed. Run: pip install pypdf")


def load_docx(path: str | Path) -> str:
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")


def load_document(path: str | Path) -> str:
    """Auto-detect format and extract plain text."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return load_pdf(p)
    if ext in {".docx", ".doc"}:
        return load_docx(p)
    return load_text_file(p)


def ingest_knowledge_directory(
    vector_store,
    knowledge_path: str | None = None,
    extensions: set[str] | None = None,
) -> dict[str, int]:
    """Walk the knowledge directory and ingest all supported documents.

    Returns a dict of {filename: chunks_added}.
    """
    base = Path(knowledge_path or os.getenv("KNOWLEDGE_PATH", "./knowledge"))
    extensions = extensions or {".txt", ".md", ".pdf", ".docx"}
    results: dict[str, int] = {}
    for file_path in base.rglob("*"):
        if file_path.suffix.lower() in extensions and file_path.is_file():
            try:
                n = vector_store.ingest_file(file_path)
                results[file_path.name] = n
            except Exception as exc:
                results[file_path.name] = -1
                print(f"[DocumentLoader] Failed to ingest {file_path.name}: {exc}")
    return results
