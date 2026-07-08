"""Pixel-based bold detection for government warning headers."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class BoldAnalysis:
    bold_score: float
    bold_confidence: float


def _region_metrics(region: Image.Image) -> tuple[float, float]:
    gray = region.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_pixels = list(edges.getdata())
    edge_density = sum(p / 255.0 for p in edge_pixels) / len(edge_pixels) if edge_pixels else 0.0

    binary = gray.point(lambda p: 0 if p < 140 else 255)
    ink_pixels = list(binary.getdata())
    ink_fill = sum(1 for p in ink_pixels if p < 128) / len(ink_pixels) if ink_pixels else 0.0
    return edge_density, ink_fill


def analyze_bold_header(
    image_bytes: bytes,
    header_bbox: tuple[int, int, int, int] | None,
    body_bbox: tuple[int, int, int, int] | None = None,
) -> BoldAnalysis:
    """
    Compare stroke/ink density in the warning header vs adjacent body text.

    Returns bold_score in [0, 1] and bold_confidence in [0, 1].
    """
    if header_bbox is None:
        return BoldAnalysis(bold_score=0.5, bold_confidence=0.0)

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = ImageOps.exif_transpose(img.convert("RGB"))
        left, top, width, height = header_bbox
        if width <= 0 or height <= 0:
            return BoldAnalysis(bold_score=0.5, bold_confidence=0.0)

        pad = 2
        x0 = max(0, left - pad)
        y0 = max(0, top - pad)
        x1 = min(img.width, left + width + pad)
        y1 = min(img.height, top + height + pad)
        header_crop = img.crop((x0, y0, x1, y1))
        header_edge, header_ink = _region_metrics(header_crop)

        body_edge, body_ink = 0.0, 0.0
        if body_bbox is not None:
            bl, bt, bw, bh = body_bbox
            if bw > 0 and bh > 0:
                bx0 = max(0, bl)
                by0 = max(0, bt)
                bx1 = min(img.width, bl + bw)
                by1 = min(img.height, bt + bh)
                body_crop = img.crop((bx0, by0, bx1, by1))
                body_edge, body_ink = _region_metrics(body_crop)

        if body_ink <= 0.001:
            body_y = min(img.height, y1 + 20)
            body_h = min(40, img.height - body_y)
            if body_h > 5:
                body_crop = img.crop((x0, body_y, x1, body_y + body_h))
                body_edge, body_ink = _region_metrics(body_crop)

        if body_ink <= 0.001:
            return BoldAnalysis(bold_score=0.5, bold_confidence=0.2)

        ink_ratio = header_ink / body_ink if body_ink > 0 else 1.0
        edge_ratio = header_edge / body_edge if body_edge > 0 else 1.0
        ratio = (ink_ratio * 0.7) + (edge_ratio * 0.3)
        bold_score = max(0.0, min(1.0, (ratio - 0.9) / 0.5))
        confidence = min(1.0, abs(ratio - 1.0) * 2.5 + 0.25)
        return BoldAnalysis(bold_score=bold_score, bold_confidence=confidence)
