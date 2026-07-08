"""Map OCR output to structured label fields."""

from __future__ import annotations

import re

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ExtractedLabelRecord, OCRResult


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_after_label(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return _normalize_space(m.group(1))
    return None


def structure_fields(ocr: OCRResult) -> ExtractedLabelRecord:
    text = ocr.full_text
    upper = text.upper()

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    brand = lines[0] if lines else None
    brand_match = _find_after_label(text, [r"^([A-Z0-9][A-Z0-9 &'.\-]{2,40})\s*$"])
    if brand_match and "\n" not in brand_match:
        brand = brand_match

    class_type = None
    class_patterns = [
        r"(Kentucky Straight Bourbon Whiskey)",
        r"(Straight Bourbon Whiskey)",
        r"(Bourbon Whiskey)",
        r"(Cognac)",
        r"(Blended Scotch Whisky)",
        r"(Scotch Whisky)",
        r"(Whiskey)",
        r"(Vodka)",
        r"(Gin)",
        r"(Rum)",
        r"(Tequila)",
        r"(Brandy)",
    ]
    for pat in class_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            class_type = _normalize_space(m.group(1))
            break

    abv = None
    abv_m = re.search(
        r"(\d{1,2}(?:\.\d+)?\s*%\s*Alc\.?/?Vol\.?(?:\s*\(\d+\s*Proof\))?)",
        text,
        re.IGNORECASE,
    )
    if abv_m:
        abv = _normalize_space(abv_m.group(1))

    net = None
    net_m = re.search(r"(\d+(?:\.\d+)?\s*(?:mL|ml|L|l|fl\.?\s*oz\.?))", text, re.IGNORECASE)
    if net_m:
        net = _normalize_space(net_m.group(1))

    warning = None
    warning_header_bold = None
    warning_bold_confidence = None
    warning_header_bbox = None
    warn_m = re.search(
        r"(GOVERNMENT WARNING:[\s\S]*?(?:health problems\.|machinery[^\n]*\.))",
        text,
        re.IGNORECASE,
    )
    if warn_m:
        warning = _normalize_space(warn_m.group(1))
        if "GOVERNMENT WARNING:" in warning:
            header = "GOVERNMENT WARNING:"
            warning = header + warning.split(":", 1)[1].strip()
            if not warning.startswith("GOVERNMENT WARNING:"):
                warning = "GOVERNMENT WARNING: " + warning.split(":", 1)[-1].strip()
        gov_blocks = [b for b in ocr.blocks if "GOVERNMENT" in b.text.upper()]
        pixel_confidences = [b.bold_confidence for b in gov_blocks if b.bold_confidence is not None]
        has_pixel_analysis = len(pixel_confidences) > 0
        avg_bold_confidence = sum(pixel_confidences) / len(pixel_confidences) if pixel_confidences else None

        if gov_blocks:
            bboxes = [b.bbox for b in gov_blocks if b.bbox]
            if bboxes:
                left = min(b[0] for b in bboxes)
                top = min(b[1] for b in bboxes)
                right = max(b[0] + b[2] for b in bboxes)
                bottom = max(b[1] + b[3] for b in bboxes)
                warning_header_bbox = (left, top, right - left, bottom - top)

        heuristic_bold = any(b.is_bold and "GOVERNMENT" in b.text.upper() for b in ocr.blocks)
        caps_fallback = "GOVERNMENT WARNING:" in text and "government warning:" not in text

        if has_pixel_analysis:
            warning_header_bold = heuristic_bold and avg_bold_confidence is not None and avg_bold_confidence >= 0.3
            if avg_bold_confidence is not None and avg_bold_confidence < 0.5:
                warning_header_bold = False if avg_bold_confidence < 0.3 else warning_header_bold
            warning_bold_confidence = avg_bold_confidence
        else:
            warning_header_bold = heuristic_bold or caps_fallback

    address = None
    addr_m = re.search(
        r"(?:Distilled|Bottled|Produced)(?:\s+and\s+Bottled)?\s+by[,\s]+([\s\S]{10,120}?)(?:\n\n|\n[A-Z]|$)",
        text,
        re.IGNORECASE,
    )
    if addr_m:
        address = _normalize_space(addr_m.group(1))
    elif re.search(r"\d{5}", text):
        zip_m = re.search(r"([\w\s,\.]+\d{5}(?:-\d{4})?)", text)
        if zip_m:
            address = _normalize_space(zip_m.group(1))

    country = None
    for c in ("Product of France", "Product of Mexico", "Product of Scotland", "Product of Japan"):
        if c.lower() in text.lower():
            country = c.replace("Product of ", "")
            break
    if not country:
        origin_m = re.search(r"Product of\s+([A-Za-z\s]+)", text, re.IGNORECASE)
        if origin_m:
            country = _normalize_space(origin_m.group(1))

    if not warning and "GOVERNMENT" in upper:
        idx = upper.find("GOVERNMENT")
        warning = _normalize_space(text[idx : idx + 400])

    return ExtractedLabelRecord(
        brand_name=brand,
        class_type=class_type,
        alcohol_content=abv,
        net_contents=net,
        government_warning=warning or (GOVERNMENT_WARNING_CANONICAL if "SURGEON GENERAL" in upper else None),
        government_warning_header_bold=warning_header_bold,
        government_warning_bold_confidence=warning_bold_confidence,
        government_warning_header_bbox=warning_header_bbox,
        bottler_producer_address=address,
        country_of_origin=country,
        raw_text=text,
        extraction_confidence=ocr.confidence,
    )
