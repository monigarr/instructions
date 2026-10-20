"""Tests for deployment-aware Streamlit batch limits."""

from __future__ import annotations

from src.domain.batch_limits import (
    FREE_TIER_BATCH_LIMIT,
    batch_limit,
    batch_limit_error,
    is_community_cloud,
)


def test_free_tier_override_enables_limit(monkeypatch):
    monkeypatch.setenv("LABELFORGE_FREE_TIER", "1")
    assert is_community_cloud() is True
    assert batch_limit() == FREE_TIER_BATCH_LIMIT


def test_free_tier_limit_accepts_exactly_25(monkeypatch):
    monkeypatch.setenv("LABELFORGE_FREE_TIER", "true")
    assert batch_limit_error(FREE_TIER_BATCH_LIMIT) is None


def test_free_tier_limit_rejects_26(monkeypatch):
    monkeypatch.setenv("LABELFORGE_FREE_TIER", "yes")
    error = batch_limit_error(FREE_TIER_BATCH_LIMIT + 1)
    assert error is not None
    assert "25" in error
    assert "200" in error


def test_local_mode_has_no_limit(monkeypatch):
    monkeypatch.setenv("LABELFORGE_FREE_TIER", "0")
    assert is_community_cloud() is False
    assert batch_limit() is None
    assert batch_limit_error(300) is None
