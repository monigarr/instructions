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

from src.config import settings
from src.domain.interfaces import IOCRProvider
from src.domain.models import OCRBlock, OCRResult
from src.ingest.bold_analyzer import analyze_bold_header
from src.ingest.preprocess import preprocess_for_ocr


class TesseractOCRProvider(IOCRProvider):
    @property
    def name(self) -> str:
        return "tesseract"

    async def extract(self, image_bytes: bytes) -> OCRResult:
        try:
            return await asyncio.to_thread(self._extract_sync, image_bytes)
        except Exception:  # noqa: BLE001 — OCR failure returns an empty result, never crashes the request
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)

    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        processed = preprocess_for_ocr(
            image_bytes,
            deskew=settings.preprocess_imperfect,
            enhance_imperfect=settings.preprocess_imperfect,
        )
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
                left = int(data["left"][i])
                top = int(data["top"][i])
                width = int(data["width"][i])
                height = int(data["height"][i])
                bbox = (left, top, width, height)
                is_bold = self._heuristic_bold(text, full_text)
                blocks.append(
                    OCRBlock(
                        text=text,
                        confidence=conf / 100.0,
                        is_bold=is_bold,
                        bbox=bbox,
                    )
                )

            blocks = self._apply_pixel_bold(processed, blocks)

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

    @staticmethod
    def _union_bbox(blocks: list[OCRBlock]) -> tuple[int, int, int, int] | None:
        bboxes = [b.bbox for b in blocks if b.bbox]
        if not bboxes:
            return None
        left = min(b[0] for b in bboxes)
        top = min(b[1] for b in bboxes)
        right = max(b[0] + b[2] for b in bboxes)
        bottom = max(b[1] + b[3] for b in bboxes)
        return (left, top, right - left, bottom - top)

    @classmethod
    def _warning_regions(
        cls, blocks: list[OCRBlock]
    ) -> tuple[tuple[int, int, int, int] | None, tuple[int, int, int, int] | None]:
        """Return the warning-header bbox and the adjacent body-line bbox.

        The header is usually split into ``GOVERNMENT`` and ``WARNING:`` tokens.
        Group all-caps tokens on the anchor line, then compare against the first
        text line below the header. Using the first block in the document (for
        example the brand) produced bogus bold scores.
        """
        anchor = next((b for b in blocks if b.bbox and "GOVERNMENT" in b.text.upper()), None)
        if anchor is None or anchor.bbox is None:
            return None, None

        anchor_top, anchor_height = anchor.bbox[1], anchor.bbox[3]
        line_tolerance = max(3, anchor_height // 2)
        line_blocks = sorted(
            [b for b in blocks if b.bbox and abs(b.bbox[1] - anchor_top) <= line_tolerance],
            key=lambda b: b.bbox[0],
        )
        anchor_index = line_blocks.index(anchor)
        header_blocks = [anchor]
        for b in line_blocks[anchor_index + 1 :]:
            if not b.text.isupper():
                break
            header_blocks.append(b)
        for b in reversed(line_blocks[:anchor_index]):
            if not b.text.isupper():
                break
            header_blocks.insert(0, b)
        header_bbox = cls._union_bbox(header_blocks) or anchor.bbox
        header_bottom = header_bbox[1] + header_bbox[3]

        body_candidates = [
            b for b in blocks if b.bbox and b.text.strip() and b.bbox[1] > header_bottom + 2
        ]
        body_candidates.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
        body_bbox = None
        if body_candidates:
            body_top = body_candidates[0].bbox[1]
            body_height = body_candidates[0].bbox[3]
            body_tolerance = max(3, body_height // 2)
            body_line = [b for b in body_candidates if abs(b.bbox[1] - body_top) <= body_tolerance]
            body_bbox = cls._union_bbox(body_line)

        return header_bbox, body_bbox

    @classmethod
    def _apply_pixel_bold(cls, image_bytes: bytes, blocks: list[OCRBlock]) -> list[OCRBlock]:
        header_bbox, body_bbox = cls._warning_regions(blocks)
        if header_bbox is None:
            return blocks

        analysis = analyze_bold_header(image_bytes, header_bbox, body_bbox)
        pixel_bold = analysis.bold_score >= 0.6

        updated: list[OCRBlock] = []
        for block in blocks:
            if "GOVERNMENT" in block.text.upper():
                combined_bold = (
                    block.is_bold and pixel_bold if analysis.bold_confidence >= 0.3 else pixel_bold
                )
                if analysis.bold_confidence < 0.3:
                    combined_bold = block.is_bold
                updated.append(
                    block.model_copy(
                        update={
                            "is_bold": combined_bold,
                            "bold_confidence": analysis.bold_confidence,
                        }
                    )
                )
            else:
                updated.append(block)
        return updated
