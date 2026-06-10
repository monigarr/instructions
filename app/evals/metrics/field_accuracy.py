"""Field verdict accuracy metrics."""

from __future__ import annotations

from collections import defaultdict

from src.domain.constants import FIELD_NAMES


def field_accuracy(expected: list[dict], actual: list[dict]) -> float:
    if not expected:
        return 1.0
    actual_by_field = {a.get("field"): a.get("status") for a in actual}
    correct = sum(
        1 for exp in expected if actual_by_field.get(exp.get("field")) == exp.get("status")
    )
    return correct / len(expected)


def field_accuracy_by_field(
    rows: list[tuple[list[dict], list[dict]]],
) -> dict[str, float | None]:
    """Per-field accuracy aggregated across golden rows with non-empty expectations."""
    correct: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)

    for expected, actual in rows:
        if not expected:
            continue
        actual_by_field = {a.get("field"): a.get("status") for a in actual}
        for exp in expected:
            field = exp.get("field")
            if not field:
                continue
            total[field] += 1
            if actual_by_field.get(field) == exp.get("status"):
                correct[field] += 1

    return {
        field: (correct[field] / total[field] if total[field] else None)
        for field in FIELD_NAMES
    }
