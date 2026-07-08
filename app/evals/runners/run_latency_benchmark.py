#!/usr/bin/env python3
"""Tesseract latency benchmark — production path P95 gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evals.metrics.latency_p95 import latency_p95
from src.domain.models import ApplicationRecord
from src.verify.pipeline import VerificationPipeline

LATENCY_FIXTURES = [
    "old_tom_match",
    "warning_title_case",
    "stones_throw_brand",
    "warning_not_bold",
    "import_france",
    "net_contents_mismatch",
    "label_slight_rotation",
    "label_low_contrast",
]

THRESHOLD_MS = 5000.0


async def run_benchmark() -> dict:
    labels_dir = ROOT / "fixtures" / "labels"
    apps_dir = ROOT / "fixtures" / "applications"
    pipeline = VerificationPipeline()
    latencies: list[float] = []
    results: list[dict] = []

    for stem in LATENCY_FIXTURES:
        png = labels_dir / f"{stem}.png"
        app_json = apps_dir / f"{stem}.json"
        if not png.exists() or not app_json.exists():
            continue
        app = ApplicationRecord.model_validate_json(app_json.read_text(encoding="utf-8"))
        image_bytes = png.read_bytes()
        result = await pipeline.verify(image_bytes, app, "image/png")
        latencies.append(result.elapsed_ms)
        results.append({"label_id": stem, "elapsed_ms": round(result.elapsed_ms, 1), "summary": result.summary})

    p95 = latency_p95(latencies)
    return {
        "latency_p95_ms": round(p95, 1),
        "latency_samples": len(latencies),
        "threshold_ms": THRESHOLD_MS,
        "passed": p95 <= THRESHOLD_MS,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="latency-report.json")
    args = parser.parse_args()
    report = asyncio.run(run_benchmark())
    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        print(f"FAIL: P95 {report['latency_p95_ms']} ms exceeds {THRESHOLD_MS} ms", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
