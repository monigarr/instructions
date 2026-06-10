#!/usr/bin/env python3
"""Generate eval manifests and expected verdicts from synthetic fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate_fixtures import WARNING_PARAPHRASED, fixture_catalog
from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ApplicationRecord, OCRBlock, OCRResult
from src.rag.retriever import _load_corpus_chunks
from src.rules.engine import DeterministicRulesEngine
from src.structure.field_mapper import structure_fields

DATASETS = ROOT / "evals" / "datasets"
EXPECTED_DIR = DATASETS / "expected"
LABELS_DIR = ROOT / "fixtures" / "labels"

ADVERSARIAL_CASES = [
    {
        "label_id": "warning_title_case",
        "issue": "title_case_warning_header",
        "rule": "government_warning",
        "expected_status": "mismatch",
    },
    {
        "label_id": "warning_wording_change",
        "issue": "paraphrased_warning_body",
        "rule": "government_warning",
        "expected_status": "mismatch",
    },
    {
        "label_id": "warning_missing",
        "issue": "missing_warning",
        "rule": "government_warning",
        "expected_status": "unable_to_verify",
    },
    {
        "label_id": "low_confidence_blank",
        "issue": "false_pass_bait",
        "rule": "false_pass",
        "expected_status": "no_auto_pass",
    },
]

RAG_QUERY_SPECS = [
    {
        "field": "government_warning",
        "query": "Is Government Warning title case acceptable?",
        "match_keywords": ["title case", "NOT acceptable", "all caps"],
    },
    {
        "field": "government_warning",
        "query": "What is the exact government warning text?",
        "match_keywords": ["GOVERNMENT WARNING:", "Surgeon General"],
    },
    {
        "field": "brand_name",
        "query": "STONE'S THROW vs Stone's Throw — same brand?",
        "match_keywords": ["Nuance", "STONE'S THROW", "Stone's Throw"],
    },
    {
        "field": "alcohol_content",
        "query": "How should ABV and proof appear on the label?",
        "match_keywords": ["Alc./Vol", "proof", "45%"],
    },
    {
        "field": "class_type",
        "query": "Must class/type match the application exactly?",
        "match_keywords": ["match the application", "class/type", "designation"],
    },
]


def _ocr_from_sidecar(label_id: str) -> OCRResult:
    path = LABELS_DIR / f"{label_id}.txt"
    text = path.read_text(encoding="utf-8")
    blocks = [
        OCRBlock(text=line, confidence=0.95, is_bold="GOVERNMENT WARNING" in line.upper())
        for line in text.splitlines()
        if line.strip()
    ]
    return OCRResult(full_text=text, blocks=blocks, confidence=0.95, provider="sidecar_stem")


def _expected_verdicts(label_id: str, app: dict) -> list[dict]:
    ocr = _ocr_from_sidecar(label_id)
    extracted = structure_fields(ocr)
    application = ApplicationRecord(**app)
    engine = DeterministicRulesEngine()
    verdicts = engine.evaluate_all(application, extracted)
    return [{"field": v.field, "status": v.status.value} for v in verdicts]


def _resolve_rag_chunk_ids(field: str, keywords: list[str]) -> list[str]:
    chunks = _load_corpus_chunks()
    hits: list[str] = []
    for chunk in chunks:
        if chunk["field"] != field:
            continue
        excerpt_lower = chunk["excerpt"].lower()
        if all(kw.lower() in excerpt_lower for kw in keywords):
            hits.append(chunk["chunk_id"])
    if not hits:
        for chunk in chunks:
            if chunk["field"] != field:
                continue
            excerpt_lower = chunk["excerpt"].lower()
            if any(kw.lower() in excerpt_lower for kw in keywords):
                hits.append(chunk["chunk_id"])
    return hits[:3]


def main() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    golden_lines: list[str] = []
    for fx in fixture_catalog():
        label_id = fx["id"]
        golden_lines.append(
            json.dumps(
                {
                    "label_id": label_id,
                    "fixture": f"fixtures/labels/{label_id}.png",
                    "application": f"fixtures/applications/{label_id}.json",
                    "expected_summary": fx["expected_summary"],
                }
            )
        )

        if fx.get("blank"):
            (EXPECTED_DIR / f"{label_id}.json").write_text("[]\n", encoding="utf-8")
            continue

        expected = _expected_verdicts(label_id, fx["app"])
        (EXPECTED_DIR / f"{label_id}.json").write_text(
            json.dumps(expected, indent=2) + "\n",
            encoding="utf-8",
        )

    (DATASETS / "golden_labels.jsonl").write_text("\n".join(golden_lines) + "\n", encoding="utf-8")

    adv_lines = [json.dumps(case) for case in ADVERSARIAL_CASES]
    (DATASETS / "adversarial_labels.jsonl").write_text("\n".join(adv_lines) + "\n", encoding="utf-8")

    rag_lines: list[str] = []
    for spec in RAG_QUERY_SPECS:
        chunk_ids = _resolve_rag_chunk_ids(spec["field"], spec["match_keywords"])
        rag_lines.append(
            json.dumps(
                {
                    "field": spec["field"],
                    "query": spec["query"],
                    "expected_chunk_ids": chunk_ids,
                }
            )
        )
    (DATASETS / "rag_queries.jsonl").write_text("\n".join(rag_lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(golden_lines)} golden labels, {len(adv_lines)} adversarial cases, {len(rag_lines)} RAG queries")


if __name__ == "__main__":
    main()
