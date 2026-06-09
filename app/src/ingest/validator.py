"""
===============================================================================
FILE: validator.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
Validate uploaded label images (MIME, size, decodability).

SECURITY:
Reject non-image payloads; enforce max upload size.

PERFORMANCE:
Fast decode check only — full OCR happens downstream.
===============================================================================
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from src.config import settings


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

    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if content_type and content_type not in allowed:
        raise UploadValidationError(
            "Unsupported file type. Please upload a JPEG or PNG label image."
        )

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
        with Image.open(io.BytesIO(content)) as img:
            img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise UploadValidationError(
            "Image unreadable — please upload a flat, well-lit photo of the label."
        ) from exc

    return content
