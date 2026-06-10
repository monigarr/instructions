#!/usr/bin/env python3
"""Offline eval suite for LabelForge."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evals.metrics.field_accuracy import field_accuracy, field_accuracy_by_field
from evals.metrics.latency_p95 import latency_p95
from evals.metrics.rag_precision import rag_hit_rate, rag_hit_rate_by_field
from evals.metrics.warning_recall import warning_recall
from scripts.generate_fixtures import WARNING_PARAPHRASED
from src.domain.constants import FIELD_NAMES, GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, VerdictStatus
from src.rag.retriever import ChromaRAGRetriever
from src.rules.engine import DeterministicRulesEngine
from src.rules.field_rules import WarningExactRule
from src.verify.pipeline import VerificationPipeline

DATASETS = Path(__file__).resolve().parents[1] / "datasets"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _build_adversarial_extracted(issue: str) -> ExtractedLabelRecord:
    if issue == "title_case_warning_header":
        bad = GOVERNMENT_WARNING_CANONICAL.replace("GOVERNMENT WARNING:", "Government Warning:")
        return ExtractedLabelRecord(government_warning=bad, extraction_confidence=0.9)
    if issue == "paraphrased_warning_body":
        return ExtractedLabelRecord(government_warning=WARNING_PARAPHRASED, extraction_confidence=0.9)
    if issue == "missing_warning":
        return ExtractedLabelRecord(government_warning=None, extraction_confidence=0.9)
    if issue == "false_pass_bait":
        return ExtractedLabelRecord(extraction_confidence=0.0)
    raise ValueError(f"Unknown adversarial issue: {issue}")


async def run_golden() -> dict:
    from src.adapters.ocr.sidecar_provider import SidecarByStemOCRProvider

    sidecar = SidecarByStemOCRProvider()
    pipeline = VerificationPipeline(ocr_provider=sidecar)
    labels_dir = ROOT / "fixtures" / "labels"
    latencies: list[float] = []
    accuracies: list[float] = []
    summary_checks: list[bool] = []
    field_rows: list[tuple[list[dict], list[dict]]] = []

    for row in _load_jsonl(DATASETS / "golden_labels.jsonl"):
        label_id = row["label_id"]
        img_path = labels_dir / f"{label_id}.png"
        app_path = ROOT / row["application"]
        if not img_path.exists() or not app_path.exists():
            continue

        sidecar.set_stem_hint(label_id)
        app = ApplicationRecord(**json.loads(app_path.read_text(encoding="utf-8")))
        result = await pipeline.verify(img_path.read_bytes(), app)
        latencies.append(result.elapsed_ms)

        expected_summary = row.get("expected_summary")
        if expected_summary:
            summary_checks.append(result.summary.value == expected_summary)

        expected_path = DATASETS / "expected" / f"{label_id}.json"
        if expected_path.exists():
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
            if expected:
                actual = [v.model_dump() for v in result.verdicts]
                field_rows.append((expected, actual))
                accuracies.append(field_accuracy(expected, actual))

    per_field = field_accuracy_by_field(field_rows)

    return {
        "golden_count": len(latencies),
        "field_accuracy_avg": sum(accuracies) / len(accuracies) if accuracies else None,
        "field_accuracy_by_field": per_field,
        "summary_accuracy": sum(summary_checks) / len(summary_checks) if summary_checks else None,
        "latency_p95_ms": latency_p95(latencies),
        "latency_samples": len(latencies),
    }


def run_adversarial() -> dict:
    warning_results: list[dict] = []
    false_pass_hits = 0
    false_pass_total = 0
    app = ApplicationRecord(label_id="adv", government_warning=GOVERNMENT_WARNING_CANONICAL)
    warning_rule = WarningExactRule()
    engine = DeterministicRulesEngine()

    for row in _load_jsonl(DATASETS / "adversarial_labels.jsonl"):
        issue = row["issue"]
        rule_name = row.get("rule", "government_warning")
        expected_status = row.get("expected_status", "mismatch")

        if rule_name == "false_pass":
            false_pass_total += 1
            extracted = _build_adversarial_extracted(issue)
            verdicts = engine.evaluate_all(app, extracted)
            falsely_passed = any(v.status == VerdictStatus.MATCH for v in verdicts)
            if not falsely_passed:
                false_pass_hits += 1
            continue

        extracted = _build_adversarial_extracted(issue)
        verdict = warning_rule.evaluate(app, extracted)
        if expected_status == "mismatch":
            passed = verdict.status == VerdictStatus.MISMATCH
        elif expected_status == "unable_to_verify":
            passed = verdict.status == VerdictStatus.UNABLE_TO_VERIFY
        else:
            passed = verdict.status.value == expected_status
        warning_results.append({"detected_mismatch": passed})

    return {
        "warning_recall": warning_recall(warning_results),
        "false_pass_rate": 0.0 if false_pass_total == 0 else 1.0 - (false_pass_hits / false_pass_total),
        "false_pass_caught": false_pass_hits,
        "false_pass_total": false_pass_total,
    }


async def run_rag() -> dict:
    retriever = ChromaRAGRetriever()
    scores: list[float] = []
    field_scores: list[tuple[str, float]] = []

    for row in _load_jsonl(DATASETS / "rag_queries.jsonl"):
        ctx = await retriever.retrieve_for_field(row["field"], row["query"], top_k=3)
        retrieved_ids = [c.chunk_id for c in ctx.chunks]
        score = rag_hit_rate(row.get("expected_chunk_ids", []), retrieved_ids)
        scores.append(score)
        field_scores.append((row["field"], score))

    return {
        "rag_hit_rate_avg": sum(scores) / len(scores) if scores else None,
        "rag_hit_rate_by_field": rag_hit_rate_by_field(field_scores),
        "rag_query_count": len(scores),
    }


def _check_golden_field_accuracy(golden: dict) -> bool:
    ok = True
    by_field = golden.get("field_accuracy_by_field") or {}
    for field in FIELD_NAMES:
        accuracy = by_field.get(field)
        if accuracy is None:
            continue
        if accuracy < 1.0:
            print(f"FAIL: golden field accuracy for {field} below 100% ({accuracy:.2%})", file=sys.stderr)
            ok = False
    if golden.get("field_accuracy_avg") is not None and golden["field_accuracy_avg"] < 1.0:
        print("FAIL: golden field accuracy below 100%", file=sys.stderr)
        ok = False
    return ok


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run LabelForge offline eval suite")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON report to this path (stdout still prints the report)",
    )
    args = parser.parse_args()

    golden = await run_golden()
    adversarial = run_adversarial()
    rag = await run_rag()
    report = {"golden": golden, "adversarial": adversarial, "rag": rag}
    report_json = json.dumps(report, indent=2)
    print(report_json)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_json + "\n", encoding="utf-8")

    ok = True
    if golden["latency_p95_ms"] > 5000:
        print("WARN: P95 latency exceeds 5s target", file=sys.stderr)
    if golden.get("summary_accuracy") is not None and golden["summary_accuracy"] < 1.0:
        print("FAIL: golden summary accuracy below 100%", file=sys.stderr)
        ok = False
    if not _check_golden_field_accuracy(golden):
        ok = False
    if adversarial["warning_recall"] < 1.0:
        print("FAIL: warning recall below 100%", file=sys.stderr)
        ok = False
    if adversarial["false_pass_rate"] > 0.0:
        print("FAIL: false-pass rate above 0%", file=sys.stderr)
        ok = False
    if rag.get("rag_hit_rate_avg") is not None and rag["rag_hit_rate_avg"] < 0.8:
        print("WARN: RAG hit rate below 0.8", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
