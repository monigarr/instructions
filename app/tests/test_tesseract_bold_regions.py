"""Regression tests for warning-header bold region selection."""

from __future__ import annotations

from src.adapters.ocr.tesseract_provider import TesseractOCRProvider
from src.domain.models import OCRBlock


def _block(text: str, bbox: tuple[int, int, int, int]) -> OCRBlock:
    return OCRBlock(text=text, bbox=bbox)


def test_warning_regions_ignore_brand_and_use_adjacent_warning_line() -> None:
    blocks = [
        _block("OLD", (41, 46, 40, 20)),
        _block("TOM", (90, 46, 40, 20)),
        _block("GOVERNMENT", (41, 245, 115, 12)),
        _block("WARNING:", (160, 245, 78, 12)),
        _block("(1)", (247, 245, 18, 15)),
        _block("According", (269, 245, 71, 15)),
        _block("beverages", (41, 271, 73, 15)),
        _block("during", (119, 271, 44, 15)),
    ]

    header_bbox, body_bbox = TesseractOCRProvider._warning_regions(blocks)

    assert header_bbox == (41, 245, 197, 12)
    assert body_bbox == (41, 271, 122, 15)


def test_warning_regions_without_government_returns_none() -> None:
    blocks = [_block("OLD", (41, 46, 40, 20))]

    assert TesseractOCRProvider._warning_regions(blocks) == (None, None)
