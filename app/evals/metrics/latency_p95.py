"""P95 latency metric."""

from __future__ import annotations


def latency_p95(values_ms: list[float]) -> float:
    if not values_ms:
        return 0.0
    sorted_vals = sorted(values_ms)
    idx = int(len(sorted_vals) * 0.95) - 1
    idx = max(0, min(idx, len(sorted_vals) - 1))
    return sorted_vals[idx]
