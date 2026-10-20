"""
===============================================================================
FILE: validator.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
Validate uploaded label images (size, decodable, real raster format).

SECURITY:
  - Reject non-image payloads and unsupported/exotic container formats.
  - Format is sniffed from magic bytes, never trusted from the client.
  - Enforce a global decompression-bomb ceiling before full decode.
  - Never echo raw image bytes or parser internals back to the client.

PERFORMANCE:
  Fast decode check only — full OCR happens downstream.
===============================================================================
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from src.config import settings

# Raster formats this prototype accepts. Excludes formats with a history of
# parser issues that the app never needs (EPS, PDF, TGA, GD, font formats, JPEG2000).
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "GIF"}

# Hard ceiling on decoded pixels (40 MP ≈ 8000x5000). Pillow's own default is
# ~178 MP, which is far beyond any label photo and a memory/DoS risk.
MAX_DECODED_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = min(Image.MAX_IMAGE_PIXELS or MAX_DECODED_PIXELS, MAX_DECODED_PIXELS)


class UploadValidationError(Exception):
    pass


def validate_image_upload(content: bytes, content_type: str | None = None) -> bytes:
    if not content:
        raise UploadValidationError("Empty upload — please select a label image file.")

    if len(content) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes // (1024 * 1024)
        raise UploadValidationError(
            f"File too large (max {max_mb} MB). Upload a smaller label image."
        )

    allowed_mimes = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if content_type and content_type not in allowed_mimes:
        raise UploadValidationError(
            "Unsupported file type. Please upload a JPEG, PNG, WebP, or GIF label image."
        )

    try:
        with Image.open(io.BytesIO(content)) as probe:
            detected = probe.format
            width, height = probe.size
        if detected not in ALLOWED_FORMATS:
            raise UploadValidationError(
                "Unsupported image format. Please upload a JPEG, PNG, WebP, or GIF label image."
            )
        if width <= 0 or height <= 0 or width * height > MAX_DECODED_PIXELS:
            raise UploadValidationError(
                "Image dimensions are too large. Upload a label photo under 40 megapixels."
            )

        # Full decode/verify only after the format and dimensions are checked.
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
        with Image.open(io.BytesIO(content)) as img:
            img.load()
    except UploadValidationError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError) as exc:
        raise UploadValidationError(
            "Image unreadable — please upload a flat, well-lit photo of the label."
        ) from exc

    return content
