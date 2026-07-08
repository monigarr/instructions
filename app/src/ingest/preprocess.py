"""Image pre-processing for OCR (P4 stretch — basic normalization in P1)."""

from __future__ import annotations

import io

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def _estimate_skew_angle(img: Image.Image) -> float:
    """Rough skew estimate from edge projection; returns degrees to rotate."""
    gray = img.convert("L").filter(ImageFilter.FIND_EDGES)
    w, h = gray.size
    best_angle = 0.0
    best_score = 0.0
    for angle in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
        rotated = gray.rotate(angle, expand=False, fillcolor=255)
        projection = [0] * h
        pixels = rotated.load()
        for y in range(h):
            for x in range(w):
                if pixels[x, y] < 128:
                    projection[y] += 1
        score = max(projection) - min(projection)
        if score > best_score:
            best_score = score
            best_angle = angle
    return -best_angle if best_angle != 0 else 0.0


def preprocess_for_ocr(
    image_bytes: bytes,
    deskew: bool = False,
    enhance_imperfect: bool = False,
) -> bytes:
    """Normalize contrast and size for faster, more reliable OCR."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img = ImageOps.exif_transpose(img)
        max_dim = 2000
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        if enhance_imperfect:
            img = ImageOps.autocontrast(img, cutoff=1)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=2))
            if deskew:
                angle = _estimate_skew_angle(img)
                if abs(angle) >= 1:
                    img = img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
        elif deskew:
            img = img.rotate(-2, expand=True, fillcolor=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
