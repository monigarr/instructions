"""RAG retrieval hit-rate metrics."""

from __future__ import annotations

from collections import defaultdict


def rag_hit_rate(expected_chunk_ids: list[str], retrieved_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 1.0
    expected = set(expected_chunk_ids)
    retrieved = set(retrieved_chunk_ids)
    return 1.0 if expected & retrieved else 0.0


def rag_hit_rate_by_field(rows: list[tuple[str, float]]) -> dict[str, float | None]:
    """Average hit rate per RAG query field."""
    totals: dict[str, list[float]] = defaultdict(list)
    for field, score in rows:
        totals[field].append(score)
    return {field: (sum(scores) / len(scores) if scores else None) for field, scores in totals.items()}
