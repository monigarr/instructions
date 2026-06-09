"""Chroma-based RAG retriever for TTB corpus."""

from __future__ import annotations

import asyncio
from pathlib import Path

from src.config import settings
from src.domain.interfaces import IRAGRetriever
from src.domain.models import RAGChunk, RAGContext

_CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
_INDEX: dict | None = None


def _load_corpus_chunks() -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(_CORPUS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        field = path.stem.replace("_", " ")
        for i, para in enumerate(text.split("\n\n")):
            para = para.strip()
            if para:
                chunks.append(
                    {
                        "chunk_id": f"{path.stem}_{i}",
                        "field": path.stem,
                        "excerpt": para[:500],
                    }
                )
    return chunks


def _get_index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        persist = settings.chroma_persist_dir
        Path(persist).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=persist)
        ef = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(name="ttb_corpus", embedding_function=ef)
        if collection.count() == 0:
            chunks = _load_corpus_chunks()
            if chunks:
                collection.add(
                    ids=[c["chunk_id"] for c in chunks],
                    documents=[c["excerpt"] for c in chunks],
                    metadatas=[{"field": c["field"]} for c in chunks],
                )
        _INDEX = collection
    except Exception:
        _INDEX = {"fallback": _load_corpus_chunks()}
    return _INDEX


class ChromaRAGRetriever(IRAGRetriever):
    async def retrieve_for_field(self, field: str, query: str, top_k: int = 3) -> RAGContext:
        return await asyncio.to_thread(self._retrieve_sync, field, query, top_k)

    def _retrieve_sync(self, field: str, query: str, top_k: int) -> RAGContext:
        index = _get_index()
        chunks: list[RAGChunk] = []
        if isinstance(index, dict) and "fallback" in index:
            for c in index["fallback"]:
                if field.replace("_", "") in c["field"].replace("_", "") or field in c["excerpt"].lower():
                    chunks.append(RAGChunk(chunk_id=c["chunk_id"], field=c["field"], excerpt=c["excerpt"], score=0.5))
            return RAGContext(field=field, chunks=chunks[:top_k])
        try:
            results = index.query(query_texts=[query], n_results=top_k, where={"field": field})
            ids = results["ids"][0] if results["ids"] else []
            docs = results["documents"][0] if results["documents"] else []
            dists = results["distances"][0] if results["distances"] else []
            for cid, doc, dist in zip(ids, docs, dists):
                score = max(0.0, 1.0 - float(dist))
                chunks.append(RAGChunk(chunk_id=cid, field=field, excerpt=doc, score=score))
        except Exception:
            for c in _load_corpus_chunks():
                if field in c["field"]:
                    chunks.append(RAGChunk(chunk_id=c["chunk_id"], field=c["field"], excerpt=c["excerpt"], score=0.4))
        return RAGContext(field=field, chunks=chunks[:top_k])
