"""
===============================================================================
FILE: tesseract_provider.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
Local OCR via Tesseract — firewall-safe fallback and default provider.

PERFORMANCE:
Target ≤ 2.5s on typical label images after preprocessing.
===============================================================================
"""

from __future__ import annotations

import asyncio
import io
import re

import pytesseract
from PIL import Image

from src.domain.interfaces import IOCRProvider
from src.domain.models import OCRBlock, OCRResult
from src.ingest.preprocess import preprocess_for_ocr


class TesseractOCRProvider(IOCRProvider):
    @property
    def name(self) -> str:
        return "tesseract"

    async def extract(self, image_bytes: bytes) -> OCRResult:
        try:
            return await asyncio.to_thread(self._extract_sync, image_bytes)
        except Exception:
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)

    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        processed = preprocess_for_ocr(image_bytes)
        with Image.open(io.BytesIO(processed)) as img:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            full_text = pytesseract.image_to_string(img)
            blocks: list[OCRBlock] = []
            confidences: list[float] = []
            n = len(data["text"])
            for i in range(n):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue
                try:
                    conf = float(data["conf"][i])
                except (ValueError, TypeError):
                    conf = 0.0
                if conf < 0:
                    continue
                confidences.append(conf / 100.0)
                is_bold = self._heuristic_bold(text, full_text)
                blocks.append(OCRBlock(text=text, confidence=conf / 100.0, is_bold=is_bold))

            avg_conf = sum(confidences) / len(confidences) if confidences else 0.3
            return OCRResult(
                full_text=full_text.strip(),
                blocks=blocks,
                confidence=min(1.0, avg_conf),
                provider=self.name,
            )

    @staticmethod
    def _heuristic_bold(text: str, full_text: str) -> bool:
        if text.isupper() and len(text) > 3:
            return True
        if "GOVERNMENT WARNING" in text.upper():
            return True
        pattern = re.compile(re.escape(text), re.IGNORECASE)
        matches = pattern.findall(full_text)
        return len(matches) == 1 and text == text.upper()
