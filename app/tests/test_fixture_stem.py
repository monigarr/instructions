"""Tests for batch label_id → fixture stem resolution."""

from src.domain.fixture_stem import resolve_fixture_stem


def test_resolve_fixture_stem_strips_scale_suffix():
    assert resolve_fixture_stem("old_tom_match_001") == "old_tom_match"


def test_resolve_fixture_stem_preserves_unique_scale_ids():
    assert resolve_fixture_stem("scale_042") == "scale_042"


def test_resolve_fixture_stem_strips_multi_segment_base():
    assert resolve_fixture_stem("stones_throw_brand_005") == "stones_throw_brand"


def test_resolve_fixture_stem_unchanged_when_no_suffix():
    assert resolve_fixture_stem("old_tom_match") == "old_tom_match"
