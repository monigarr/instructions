"""Tests for scale fixture generation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_scale_fixtures import SCALE_COUNT, scale_fixture_catalog

ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / "fixtures" / "labels"
APPS = ROOT / "fixtures" / "applications"


def test_scale_fixture_catalog_unique_ids():
    fixtures = scale_fixture_catalog(SCALE_COUNT)
    ids = [fx["id"] for fx in fixtures]
    assert len(ids) == SCALE_COUNT
    assert len(set(ids)) == SCALE_COUNT
    assert ids[0] == "scale_001"
    assert ids[-1] == f"scale_{SCALE_COUNT:03d}"


def test_scale_fixture_catalog_mixed_outcomes():
    fixtures = scale_fixture_catalog(SCALE_COUNT)
    summaries = {fx["expected_summary"] for fx in fixtures}
    assert "passed" in summaries
    assert "failed" in summaries
    assert "needs_review" in summaries


def test_scale_manifest_files_when_generated():
    path_200 = APPS / "batch_manifest_200.json"
    path_300 = APPS / "batch_manifest_300.json"
    if not path_200.is_file() or not path_300.is_file():
        return
    manifest_200 = json.loads(path_200.read_text(encoding="utf-8"))
    manifest_300 = json.loads(path_300.read_text(encoding="utf-8"))
    assert len(manifest_200) == 200
    assert len(manifest_300) == 300
    assert manifest_200[0]["label_id"] == "scale_001"
    assert manifest_300[-1]["label_id"] == "scale_300"


def test_scale_fixtures_have_assets_when_generated():
    sample_id = "scale_001"
    png = LABELS / f"{sample_id}.png"
    txt = LABELS / f"{sample_id}.txt"
    app_json = APPS / f"{sample_id}.json"
    if not png.is_file():
        return
    assert png.is_file()
    assert txt.is_file()
    assert app_json.is_file()
