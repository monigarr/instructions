"""Curated sample catalog for demo and quick-start UX."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.domain.fixture_stem import resolve_fixture_stem

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
LABELS = FIXTURES / "labels"
APPS = FIXTURES / "applications"

_LABEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")

SAMPLE_CATALOG: list[dict] = [
    {
        "id": "old_tom_match",
        "title": "Old Tom — Pass",
        "description": "All fields match. Happy-path verification.",
        "expected_summary": "passed",
        "category": "Happy path",
    },
    {
        "id": "warning_title_case",
        "title": "Warning Title Case",
        "description": "Government warning header not in all caps (Jenny Park).",
        "expected_summary": "failed",
        "category": "Warning compliance",
    },
    {
        "id": "warning_not_bold",
        "title": "Warning Not Bold",
        "description": "Correct warning text but regular-weight header — visual bold check.",
        "expected_summary": "needs_review",
        "category": "Warning compliance",
    },
    {
        "id": "stones_throw_brand",
        "title": "Brand Nuance",
        "description": "Brand casing difference — human review (Dave Morrison).",
        "expected_summary": "needs_review",
        "category": "Brand nuance",
    },
    {
        "id": "import_france",
        "title": "Import — France",
        "description": "Country of origin verification for imported spirits.",
        "expected_summary": "passed",
        "category": "Import label",
    },
    {
        "id": "net_contents_mismatch",
        "title": "Net Contents Mismatch",
        "description": "Volume on label differs from application.",
        "expected_summary": "failed",
        "category": "Field mismatch",
    },
    {
        "id": "unreadable_blank",
        "title": "Unreadable Label",
        "description": "Blank image — OCR failure path.",
        "expected_summary": "needs_review",
        "category": "Edge case",
    },
    {
        "id": "label_slight_rotation",
        "title": "Slight Rotation",
        "description": "Imperfect photo — label rotated ~3° (stretch goal).",
        "expected_summary": "passed",
        "category": "Imperfect photo",
    },
    {
        "id": "label_low_contrast",
        "title": "Low Contrast",
        "description": "Imperfect photo — faded/low-contrast capture.",
        "expected_summary": "passed",
        "category": "Imperfect photo",
    },
    {
        "id": "label_glare_band",
        "title": "Glare Band",
        "description": "Imperfect photo — glare across upper label.",
        "expected_summary": "passed",
        "category": "Imperfect photo",
    },
]

ALLOWED_SAMPLE_IDS = {s["id"] for s in SAMPLE_CATALOG}


def _valid_label_id(label_id: str) -> bool:
    return bool(_LABEL_ID_PATTERN.match(label_id))


def _discover_fixture_label_ids() -> list[str]:
    if not LABELS.is_dir():
        return []
    return sorted(p.stem for p in LABELS.glob("*.png") if _valid_label_id(p.stem))


def _load_expected_summaries() -> dict[str, str]:
    summaries: dict[str, str] = {}
    golden_path = ROOT / "evals" / "datasets" / "golden_labels.jsonl"
    if golden_path.is_file():
        for line in golden_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            label_id = row.get("label_id")
            expected = row.get("expected_summary")
            if label_id and expected:
                summaries[str(label_id)] = str(expected)
    try:
        from scripts.generate_fixtures import fixture_catalog

        for fx in fixture_catalog():
            label_id = fx.get("id")
            expected = fx.get("expected_summary")
            if label_id and expected:
                summaries[str(label_id)] = str(expected)
    except ImportError:
        pass
    return summaries


def list_fixture_labels() -> list[dict]:
    """All label images in fixtures/labels; optional expected_summary when catalogued."""
    expected_by_id = _load_expected_summaries()
    labels: list[dict] = []
    for label_id in _discover_fixture_label_ids():
        entry: dict[str, str] = {
            "id": label_id,
            "image_url": f"/labels/{label_id}/image",
            "application_url": f"/labels/{label_id}/application",
        }
        expected = expected_by_id.get(label_id)
        if expected:
            entry["expected_summary"] = expected
        labels.append(entry)
    return labels


def fixture_image_path(label_id: str) -> Path | None:
    if not _valid_label_id(label_id):
        return None
    path = LABELS / f"{label_id}.png"
    return path if path.is_file() else None


def fixture_application_path(label_id: str) -> Path | None:
    if not _valid_label_id(label_id):
        return None
    path = APPS / f"{label_id}.json"
    return path if path.is_file() else None


def list_samples() -> list[dict]:
    return [
        {
            **sample,
            "thumbnail_url": f"/samples/{sample['id']}/image",
            "application_url": f"/samples/{sample['id']}/application",
        }
        for sample in SAMPLE_CATALOG
    ]


def sample_image_path(sample_id: str) -> Path | None:
    if sample_id not in ALLOWED_SAMPLE_IDS:
        return None
    path = LABELS / f"{sample_id}.png"
    return path if path.exists() else None


def sample_application_path(sample_id: str) -> Path | None:
    if sample_id not in ALLOWED_SAMPLE_IDS:
        return None
    path = APPS / f"{sample_id}.json"
    return path if path.exists() else None


def demo_batch_manifest() -> list[dict]:
    path = APPS / "batch_manifest.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def scale_batch_manifest(size: int) -> list[dict]:
    path = APPS / f"batch_manifest_{size}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    base_path = APPS / "batch_manifest.json"
    if not base_path.exists():
        return []
    base = json.loads(base_path.read_text(encoding="utf-8"))
    manifest: list[dict] = []
    for i in range(size):
        src = base[i % len(base)]
        entry = dict(src)
        entry["label_id"] = f"{src['label_id']}_{i + 1:03d}"
        manifest.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
