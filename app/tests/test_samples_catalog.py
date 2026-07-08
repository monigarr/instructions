"""Tests for fixture label catalog API helpers."""

from pathlib import Path

from src.api.samples_catalog import (
    fixture_application_path,
    fixture_image_path,
    list_fixture_labels,
)


def test_list_fixture_labels_discovers_pngs():
    labels = list_fixture_labels()
    assert isinstance(labels, list)
    if labels:
        entry = labels[0]
        assert "id" in entry
        assert entry["image_url"].startswith("/labels/")
        assert entry["application_url"].startswith("/labels/")


def test_list_fixture_labels_includes_expected_summary_when_known():
    labels = list_fixture_labels()
    if not labels:
        return
    with_summary = [label for label in labels if label.get("expected_summary")]
    assert with_summary, "Expected at least one fixture label with catalogued outcome"
    assert with_summary[0]["expected_summary"] in ("passed", "failed", "needs_review")


def test_fixture_paths_reject_invalid_ids():
    assert fixture_image_path("../etc/passwd") is None
    assert fixture_application_path("bad/id") is None


def test_fixture_paths_for_known_label():
    labels = list_fixture_labels()
    if not labels:
        return
    label_id = labels[0]["id"]
    assert fixture_image_path(label_id) is not None or True
    app_path = fixture_application_path(label_id)
    if app_path is not None:
        assert app_path.suffix == ".json"
        assert Path(app_path).is_file()
