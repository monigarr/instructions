"""RAG retrieval hit-rate metric."""

from __future__ import annotations


def rag_hit_rate(expected_chunk_ids: list[str], retrieved_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 1.0
    expected = set(expected_chunk_ids)
    retrieved = set(retrieved_chunk_ids)
    return 1.0 if expected & retrieved else 0.0
