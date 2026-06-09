#!/usr/bin/env python3
"""Offline eval suite for LabelForge."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evals.metrics.field_accuracy import field_accuracy
from evals.metrics.latency_p95 import latency_p95
from evals.metrics.warning_recall import warning_recall
from src.domain.models import ApplicationRecord
from src.rules.engine import DeterministicRulesEngine
from src.rules.field_rules import WarningExactRule
from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ExtractedLabelRecord, VerdictStatus
from src.verify.pipeline import VerificationPipeline

DATASETS = Path(__file__).resolve().parents[1] / "datasets"


async def run_golden() -> dict:
    from src.adapters.ocr.sidecar_provider import SidecarByStemOCRProvider

    sidecar = SidecarByStemOCRProvider()
    pipeline = VerificationPipeline(ocr_provider=sidecar)
    labels_dir = ROOT / "fixtures" / "labels"
    apps_dir = ROOT / "fixtures" / "applications"
    latencies: list[float] = []
    accuracies: list[float] = []

    for app_path in sorted(apps_dir.glob("*.json")):
        if app_path.name == "batch_manifest.json":
            continue
        label_id = app_path.stem
        img_path = labels_dir / f"{label_id}.png"
        if not img_path.exists():
            continue
        sidecar.set_stem_hint(label_id)
        app = ApplicationRecord(**json.loads(app_path.read_text(encoding="utf-8")))
        image = img_path.read_bytes()
        result = await pipeline.verify(image, app)
        latencies.append(result.elapsed_ms)

        expected_path = DATASETS / "expected" / f"{label_id}.json"
        if expected_path.exists():
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
            actual = [v.model_dump() for v in result.verdicts]
            accuracies.append(field_accuracy(expected, actual))

    return {
        "golden_count": len(latencies),
        "field_accuracy_avg": sum(accuracies) / len(accuracies) if accuracies else None,
        "latency_p95_ms": latency_p95(latencies),
        "latency_samples": len(latencies),
    }


def run_adversarial_warning() -> dict:
    rule = WarningExactRule()
    bad = GOVERNMENT_WARNING_CANONICAL.replace("GOVERNMENT WARNING:", "Government Warning:")
    from src.domain.models import ApplicationRecord

    app = ApplicationRecord(label_id="adv", government_warning=GOVERNMENT_WARNING_CANONICAL)
    extracted = ExtractedLabelRecord(government_warning=bad, extraction_confidence=0.9)
    v = rule.evaluate(app, extracted)
    results = [{"detected_mismatch": v.status == VerdictStatus.MISMATCH}]
    return {"warning_recall": warning_recall(results)}


async def main() -> int:
    golden = await run_golden()
    adversarial = run_adversarial_warning()
    report = {"golden": golden, "adversarial": adversarial}
    print(json.dumps(report, indent=2))

    ok = True
    if golden["latency_p95_ms"] > 5000:
        print("WARN: P95 latency exceeds 5s target", file=sys.stderr)
    if adversarial["warning_recall"] < 1.0:
        print("FAIL: warning recall below 100%", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
