"""Government warning recall on adversarial fixtures."""

from __future__ import annotations


def warning_recall(results: list[dict]) -> float:
    """Fraction of adversarial wrong-warning cases correctly flagged as mismatch."""
    if not results:
        return 1.0
    hits = sum(1 for r in results if r.get("detected_mismatch"))
    return hits / len(results)
