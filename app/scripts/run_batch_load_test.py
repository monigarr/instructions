#!/usr/bin/env python3
"""Load-test batch verification at 200/300 scale."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

from src.domain.fixture_stem import resolve_fixture_stem

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
LABELS = FIXTURES / "labels"


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(0.95 * (len(s) - 1))
    return s[idx]


def _p99(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(0.99 * (len(s) - 1))
    return s[idx]


def _load_label_png(label_id: str) -> bytes | None:
    direct = LABELS / f"{label_id}.png"
    if direct.is_file():
        return direct.read_bytes()
    stem = resolve_fixture_stem(label_id)
    fallback = LABELS / f"{stem}.png"
    if fallback.is_file():
        return fallback.read_bytes()
    return None


def run_load_test(base_url: str, size: int, poll_interval: float = 1.0) -> dict:
    manifest_path = FIXTURES / "applications" / f"batch_manifest_{size}.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing {manifest_path}. Run generate_scale_fixtures.py first.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    form_files: list[tuple[str, tuple[str, bytes, str]]] = []
    for entry in manifest:
        label_id = entry["label_id"]
        data = _load_label_png(label_id)
        if data is None:
            continue
        fname = f"{label_id}.png"
        form_files.append(("images", (fname, data, "image/png")))

    form_data = {"manifest": json.dumps(manifest), "async_mode": "true"}
    start = time.perf_counter()
    with httpx.Client(base_url=base_url, timeout=300.0) as client:
        resp = client.post("/batch/verify", data=form_data, files=form_files)
        resp.raise_for_status()
        batch_id = resp.json()["batch_id"]

        while True:
            prog = client.get(f"/batch/{batch_id}?summary_only=true").json()
            if prog.get("finished"):
                break
            time.sleep(poll_interval)

        final = client.get(f"/batch/{batch_id}").json()

    elapsed_s = time.perf_counter() - start
    latencies = [
        item["result"]["elapsed_ms"]
        for item in final.get("items", [])
        if item.get("result") and item["result"].get("elapsed_ms") is not None
    ]
    return {
        "batch_id": batch_id,
        "size": size,
        "wall_clock_s": round(elapsed_s, 2),
        "throughput_per_min": round(final["total"] / (elapsed_s / 60), 2) if elapsed_s else 0,
        "completed": final["completed"],
        "passed": final["passed"],
        "failed": final["failed"],
        "needs_review": final["needs_review"],
        "errors": final["errors"],
        "latency_p95_ms": round(_p95(latencies), 1),
        "latency_p99_ms": round(_p99(latencies), 1),
        "latency_samples": len(latencies),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch load test for LabelForge")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--size", type=int, choices=[200, 300], default=200)
    args = parser.parse_args()
    report = run_load_test(args.base_url, args.size)
    print(json.dumps(report, indent=2))
    if report["completed"] != report["size"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
