"""Tests for structured logging, trace propagation, and safe trace ids."""

from __future__ import annotations

import json
import logging
import uuid

import pytest

from src.observability import (
    JsonFormatter,
    configure_logging,
    current_trace_id,
    new_trace_id,
    reset_trace_id,
    set_trace_id,
)
from src.verify.pipeline import VerificationPipeline


def test_new_trace_id_accepts_safe_values_and_rejects_injection():
    assert new_trace_id("req-123_abc.def") == "req-123_abc.def"
    assert new_trace_id("  spaced  ") == "spaced"
    assert new_trace_id("bad id with spaces") != "bad id with spaces"
    assert new_trace_id("x" * 65) != "x" * 65
    assert new_trace_id("line\nbreak") != "line\nbreak"
    generated = new_trace_id()
    assert str(uuid.UUID(generated)) == generated


def test_trace_context_propagates_and_resets():
    assert current_trace_id() is None
    token = set_trace_id("trace-1")
    assert current_trace_id() == "trace-1"
    reset_trace_id(token)
    assert current_trace_id() is None


def test_json_formatter_includes_context_and_extra_fields():
    token = set_trace_id("ctx-42")
    try:
        record = logging.LogRecord(
            name="labelforge.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="verification_completed",
            args=(),
            exc_info=None,
        )
        record.label_id = "old_tom_match"
        record.summary = "passed"
        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_trace_id(token)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "labelforge.test"
    assert payload["message"] == "verification_completed"
    assert payload["trace_id"] == "ctx-42"
    assert payload["label_id"] == "old_tom_match"
    assert payload["summary"] == "passed"
    assert payload["timestamp"].endswith("Z")


def test_configure_logging_is_idempotent():
    root = logging.getLogger()
    before = [h for h in root.handlers if getattr(h, "_labelforge_handler", False)]
    configure_logging("INFO", True)
    configure_logging("INFO", True)
    after = [h for h in root.handlers if getattr(h, "_labelforge_handler", False)]
    assert len(after) == 1
    assert len(before) <= 1


@pytest.mark.asyncio
async def test_pipeline_inherits_request_trace_id():
    token = set_trace_id("request-trace-1")
    try:
        result = await VerificationPipeline().verify(b"not-an-image", label_id_app())
    finally:
        reset_trace_id(token)
    assert result.trace_id == "request-trace-1"
    assert result.summary.value == "failed"


def label_id_app():
    from src.domain.models import ApplicationRecord

    return ApplicationRecord(label_id="invalid-upload")
