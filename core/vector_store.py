from __future__ import annotations

import os
import uuid
from pathlib import Path

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None  # type: ignore
    CHROMADB_AVAILABLE = False


class VectorStore:
    """ChromaDB-backed vector store for GRC knowledge retrieval.

    Requires chromadb (64-bit Python on Windows): pip install chromadb
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        if not CHROMADB_AVAILABLE:
            raise RuntimeError(
                "chromadb is not installed. Install it with: pip install chromadb\n"
                "On Windows, 64-bit Python is required."
            )
        path = persist_dir or os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="grc_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not documents:
            return
        ids = ids or [str(uuid.uuid4()) for _ in documents]
        metadatas = metadatas or [{"source": "unknown"} for _ in documents]
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 3) -> list[str]:
        total = self.collection.count()
        if total == 0:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, total),
        )
        return results["documents"][0] if results["documents"] else []

    def query_with_metadata(
        self, query_text: str, n_results: int = 3
    ) -> list[dict]:
        total = self.collection.count()
        if total == 0:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, total),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({"text": doc, "metadata": meta, "distance": dist})
        return out

    def count(self) -> int:
        return self.collection.count()

    def ingest_file(self, file_path: str | Path, chunk_size: int = 1500, overlap: int = 200) -> int:
        """Chunk and ingest a text file. Returns number of chunks added."""
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = _chunk_text(text, chunk_size, overlap)
        if not chunks:
            return 0
        metadatas = [{"source": path.name, "chunk": i} for i in range(len(chunks))]
        ids = [f"{path.stem}_{i}" for i in range(len(chunks))]
        # upsert by deleting existing ids first to avoid duplicates
        existing = self.collection.get(ids=ids)
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])
        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return len(chunks)


def _chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
