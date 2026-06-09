"""Vision extraction agent — OCR via IOCRProvider."""

from __future__ import annotations

import asyncio

from src.config import settings
from src.domain.interfaces import IOCRProvider


class VisionExtractionAgent:
    role = "vision_extraction"

    def __init__(self, provider: IOCRProvider, is_fallback: bool = False) -> None:
        self._provider = provider
        self._is_fallback = is_fallback

    async def run(self, state: dict) -> dict:
        image_bytes = state["image_bytes"]
        errors = list(state.get("errors") or [])
        try:
            ocr = await asyncio.wait_for(
                self._provider.extract(image_bytes),
                timeout=settings.ocr_timeout_seconds,
            )
        except Exception as exc:
            errors.append(f"OCR error ({self._provider.name}): {exc}")
            return {**state, "errors": errors, "route": "ocr_fallback" if not self._is_fallback else "failed"}
        return {**state, "ocr_result": ocr, "errors": errors, "route": self._provider.name}
