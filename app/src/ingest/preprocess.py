"""Image pre-processing for OCR (P4 stretch — basic normalization in P1)."""

from __future__ import annotations

import io

from PIL import Image, ImageEnhance, ImageOps


def preprocess_for_ocr(image_bytes: bytes, deskew: bool = False) -> bytes:
    """Normalize contrast and size for faster, more reliable OCR."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img = ImageOps.exif_transpose(img)
        max_dim = 2000
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        if deskew:
            img = img.rotate(-2, expand=True, fillcolor=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
