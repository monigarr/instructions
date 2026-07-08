"""P1 linear verification pipeline."""

from __future__ import annotations

import asyncio
import time
import uuid

from src.adapters.ocr.factory import create_fallback_provider, create_ocr_provider
from src.config import settings
from src.domain.fixture_stem import resolve_fixture_stem
from src.domain.interfaces import IOCRProvider, IRulesEngine
from src.domain.models import ApplicationRecord, LabelSummary, OCRResult, VerificationResult, VerdictStatus
from src.ingest.validator import UploadValidationError, validate_image_upload
from src.rules.engine import DeterministicRulesEngine
from src.structure.field_mapper import structure_fields


def _summarize(verdicts) -> LabelSummary:
    if any(v.status == VerdictStatus.MISMATCH for v in verdicts):
        return LabelSummary.FAILED
    if any(v.status in (VerdictStatus.UNABLE_TO_VERIFY, VerdictStatus.NEEDS_REVIEW) for v in verdicts):
        return LabelSummary.NEEDS_REVIEW
    return LabelSummary.PASSED


class VerificationPipeline:
    def __init__(
        self,
        ocr_provider: IOCRProvider | None = None,
        rules_engine: IRulesEngine | None = None,
    ) -> None:
        self._primary = ocr_provider or create_ocr_provider()
        self._fallback = create_fallback_provider(self._primary)
        self._rules = rules_engine or DeterministicRulesEngine()

    async def _extract_with_fallback(self, image_bytes: bytes, label_id: str | None = None):
        errors: list[str] = []
        from src.adapters.ocr.sidecar_provider import SidecarByStemOCRProvider

        stem = resolve_fixture_stem(label_id) if label_id else None
        if isinstance(self._primary, SidecarByStemOCRProvider) and stem:
            self._primary.set_stem_hint(stem)
        if isinstance(self._fallback, SidecarByStemOCRProvider) and stem:
            self._fallback.set_stem_hint(stem)
        providers = [self._primary]
        if self._fallback.name != self._primary.name:
            providers.append(self._fallback)

        for provider in providers:
            try:
                ocr = await asyncio.wait_for(
                    provider.extract(image_bytes),
                    timeout=settings.ocr_timeout_seconds,
                )
                if ocr.confidence >= settings.ocr_confidence_threshold and ocr.full_text.strip():
                    return ocr, errors
                errors.append(f"OCR ({provider.name}) low confidence or empty text.")
            except Exception as exc:
                errors.append(f"OCR ({provider.name}) failed: {exc}")

        return OCRResult(full_text="", blocks=[], confidence=0.0, provider="none"), errors

    async def verify(
        self,
        image_bytes: bytes,
        application: ApplicationRecord,
        content_type: str | None = None,
    ) -> VerificationResult:
        start = time.perf_counter()
        trace_id = str(uuid.uuid4())
        errors: list[str] = []

        try:
            image_bytes = validate_image_upload(image_bytes, content_type)
        except UploadValidationError as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return VerificationResult(
                label_id=application.label_id,
                verdicts=[],
                summary=LabelSummary.FAILED,
                elapsed_ms=elapsed,
                trace_id=trace_id,
                errors=[str(exc)],
            )

        ocr, ocr_errors = await self._extract_with_fallback(image_bytes, application.label_id)
        errors.extend(ocr_errors)

        if not ocr.full_text.strip():
            elapsed = (time.perf_counter() - start) * 1000
            return VerificationResult(
                label_id=application.label_id,
                verdicts=[],
                summary=LabelSummary.NEEDS_REVIEW,
                elapsed_ms=elapsed,
                trace_id=trace_id,
                errors=errors + ["Image unreadable — please upload a flat, well-lit photo of the label."],
            )

        extracted = structure_fields(ocr)
        verdicts = self._rules.evaluate_all(application, extracted)
        elapsed = (time.perf_counter() - start) * 1000

        return VerificationResult(
            label_id=application.label_id,
            verdicts=verdicts,
            summary=_summarize(verdicts),
            elapsed_ms=elapsed,
            trace_id=trace_id,
            errors=errors,
            latency_warning=settings.latency_gate_enabled and elapsed > settings.latency_warn_ms,
        )
