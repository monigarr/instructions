"""LangGraph verification runner (P2+)."""

from __future__ import annotations

import time
import uuid

from src.domain.interfaces import IOCRProvider, IRulesEngine
from src.domain.models import ApplicationRecord, LabelSummary, VerificationResult, VerdictStatus
from src.graph.verification_graph import build_verification_graph
from src.ingest.validator import UploadValidationError, validate_image_upload


def _summarize(verdicts) -> LabelSummary:
    if any(v.status == VerdictStatus.MISMATCH for v in verdicts):
        return LabelSummary.FAILED
    if any(v.status in (VerdictStatus.UNABLE_TO_VERIFY, VerdictStatus.NEEDS_REVIEW) for v in verdicts):
        return LabelSummary.NEEDS_REVIEW
    return LabelSummary.PASSED


class LangGraphRunner:
    def __init__(
        self,
        ocr_provider: IOCRProvider,
        rules_engine: IRulesEngine,
        rag_enabled: bool = False,
    ) -> None:
        self._graph = build_verification_graph(ocr_provider, rules_engine, rag_enabled)

    async def run(
        self,
        image_bytes: bytes,
        application: ApplicationRecord,
        trace_id: str | None = None,
    ) -> VerificationResult:
        start = time.perf_counter()
        tid = trace_id or str(uuid.uuid4())
        state = {
            "run_id": str(uuid.uuid4()),
            "trace_id": tid,
            "label_id": application.label_id,
            "image_bytes": image_bytes,
            "application": application,
            "ocr_result": None,
            "extracted": None,
            "rag_context": [],
            "verdicts": [],
            "nuance": None,
            "status": "running",
            "errors": [],
            "timings_ms": {},
            "route": "start",
        }
        try:
            validate_image_upload(image_bytes)
        except UploadValidationError as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return VerificationResult(
                label_id=application.label_id,
                verdicts=[],
                summary=LabelSummary.FAILED,
                elapsed_ms=elapsed,
                trace_id=tid,
                errors=[str(exc)],
            )

        final = await self._graph.ainvoke(state)
        elapsed = (time.perf_counter() - start) * 1000
        verdicts = final.get("verdicts") or []
        return VerificationResult(
            label_id=application.label_id,
            verdicts=verdicts,
            summary=_summarize(verdicts) if verdicts else LabelSummary.NEEDS_REVIEW,
            elapsed_ms=elapsed,
            trace_id=tid,
            errors=final.get("errors") or [],
        )
