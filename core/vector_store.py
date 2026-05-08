from __future__ import annotations

import os
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings


class VectorStore:
    """ChromaDB-backed vector store for GRC knowledge retrieval."""

    def __init__(self, persist_dir: str | None = None) -> None:
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
        metadatas = metadatas or [{} for _ in documents]
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 3) -> list[str]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count() or 1),
        )
        return results["documents"][0] if results["documents"] else []

    def query_with_metadata(
        self, query_text: str, n_results: int = 3
    ) -> list[dict]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count() or 1),
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
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
