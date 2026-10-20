"""
===============================================================================
FILE: sidecar_provider.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
Serve OCR text from committed fixture sidecar (.txt) files when Tesseract is
unavailable — for local development and offline evals only.

SECURITY:
  - The sidecar is only used when the submitted image bytes are a byte-for-byte
    match for the committed fixture image for that stem. A client-supplied
    label_id can therefore never fabricate fixture text for an arbitrary upload.
  - Stems are validated with the shared label-id validator before any path join
    (no traversal).
===============================================================================
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from src.domain.interfaces import IOCRProvider
from src.domain.label_id import sanitize_label_id
from src.domain.models import OCRBlock, OCRResult

FIXTURES_LABELS = Path(__file__).resolve().parents[3] / "fixtures" / "labels"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture_text_for_stem(stem: str, image_bytes: bytes) -> str | None:
    """Return sidecar text only when the upload matches that fixture image exactly."""
    safe_stem = sanitize_label_id(stem)
    if safe_stem is None:
        return None
    image_path = FIXTURES_LABELS / f"{safe_stem}.png"
    text_path = FIXTURES_LABELS / f"{safe_stem}.txt"
    if not image_path.is_file() or not text_path.is_file():
        return None
    if _sha256(image_bytes) != _sha256(image_path.read_bytes()):
        return None
    return text_path.read_text(encoding="utf-8")


def _result_from_text(text: str, provider: str) -> OCRResult:
    return OCRResult(
        full_text=text,
        blocks=[
            OCRBlock(
                text=line,
                confidence=0.95,
                is_bold="GOVERNMENT WARNING" in line.upper(),
            )
            for line in text.splitlines()
            if line.strip()
        ],
        confidence=0.95 if text else 0.0,
        provider=provider,
    )


class SidecarTextOCRProvider(IOCRProvider):
    """Content-addressed sidecar lookup — never fabricates text for unknown images."""

    @property
    def name(self) -> str:
        return "sidecar"

    async def extract(self, image_bytes: bytes) -> OCRResult:
        return await asyncio.to_thread(self._extract_sync, image_bytes)

    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        for text_path in sorted(FIXTURES_LABELS.glob("*.txt")):
            text = _fixture_text_for_stem(text_path.stem, image_bytes)
            if text:
                return _result_from_text(text, self.name)
        return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)


class SidecarByStemOCRProvider(IOCRProvider):
    """OCR from fixtures/labels/{stem}.txt, gated on an exact fixture-image hash match."""

    def __init__(self) -> None:
        self._stem_hint: str | None = None

    def set_stem_hint(self, stem: str) -> None:
        self._stem_hint = sanitize_label_id(stem)

    @property
    def name(self) -> str:
        return "sidecar_stem"

    async def extract(self, image_bytes: bytes) -> OCRResult:
        return await asyncio.to_thread(self._extract_sync, image_bytes)

    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        if not self._stem_hint:
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)
        text = _fixture_text_for_stem(self._stem_hint, image_bytes)
        if not text:
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)
        return _result_from_text(text, self.name)
