"""Batch service and store tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.domain.models import ApplicationRecord, BatchProgress, LabelSummary, VerificationResult
from src.verify.batch_service import BatchVerificationService
from src.verify.batch_store import FileBatchStore, InMemoryBatchStore


def _app(label_id: str) -> ApplicationRecord:
    return ApplicationRecord(label_id=label_id, brand_name="TEST")


def _result(label_id: str, summary: LabelSummary) -> VerificationResult:
    return VerificationResult(label_id=label_id, verdicts=[], summary=summary, elapsed_ms=10.0)


@pytest.mark.asyncio
async def test_batch_service_counts_and_finishes():
    calls = {"n": 0}

    async def verify_fn(image: bytes, app: ApplicationRecord, content_type: str | None) -> VerificationResult:
        calls["n"] += 1
        summary = LabelSummary.PASSED if app.label_id.endswith("pass") else LabelSummary.FAILED
        return _result(app.label_id, summary)

    svc = BatchVerificationService(verify_fn=verify_fn)
    items = [
        ("a_pass", b"img", _app("a_pass"), "image/png"),
        ("b_fail", b"img", _app("b_fail"), "image/png"),
    ]
    progress = await svc.run_batch(items)
    assert progress.finished is True
    assert progress.total == 2
    assert progress.completed == 2
    assert progress.passed == 1
    assert progress.failed == 1
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_batch_service_isolates_item_failures():
    async def verify_fn(image: bytes, app: ApplicationRecord, content_type: str | None) -> VerificationResult:
        if app.label_id == "boom":
            raise RuntimeError("boom")
        return _result(app.label_id, LabelSummary.PASSED)

    svc = BatchVerificationService(verify_fn=verify_fn)
    items = [
        ("ok_pass", b"img", _app("ok_pass"), None),
        ("boom", b"img", _app("boom"), None),
    ]
    progress = await svc.run_batch(items)
    assert progress.errors == 1
    assert progress.passed == 1
    assert progress.finished is True


@pytest.mark.asyncio
async def test_batch_summary_only():
    async def verify_fn(image: bytes, app: ApplicationRecord, content_type: str | None) -> VerificationResult:
        return _result(app.label_id, LabelSummary.PASSED)

    svc = BatchVerificationService(verify_fn=verify_fn)
    progress = await svc.run_batch([("x_pass", b"img", _app("x_pass"), None)])
    summary = svc.get_progress(progress.batch_id, summary_only=True)
    assert summary is not None
    assert summary.completed == 1
    assert summary.items == []


def test_batch_store_roundtrip(tmp_path: Path):
    store = FileBatchStore(tmp_path)
    progress = BatchProgress(
        batch_id="abc",
        total=2,
        completed=1,
        passed=1,
        failed=0,
        needs_review=0,
        errors=0,
        finished=False,
    )
    store.set(progress)
    loaded = store.get("abc")
    assert loaded is not None
    assert loaded.total == 2
    assert loaded.completed == 1

    store2 = FileBatchStore(tmp_path)
    restored = store2.load_all()
    assert "abc" in restored
