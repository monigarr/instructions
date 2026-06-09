"""Field verdict accuracy metric."""

from __future__ import annotations


def field_accuracy(expected: list[dict], actual: list[dict]) -> float:
    if not expected:
        return 1.0
    actual_by_field = {a.get("field"): a.get("status") for a in actual}
    correct = sum(
        1 for exp in expected if actual_by_field.get(exp.get("field")) == exp.get("status")
    )
    return correct / len(expected)
