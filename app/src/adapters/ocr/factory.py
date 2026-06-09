"""OCR provider factory."""

from __future__ import annotations

import shutil

from src.adapters.ocr.azure_provider import AzureOCRProvider
from src.adapters.ocr.sidecar_provider import SidecarByStemOCRProvider
from src.adapters.ocr.tesseract_provider import TesseractOCRProvider
from src.config import settings
from src.domain.interfaces import IOCRProvider


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def create_ocr_provider(preferred: str | None = None) -> IOCRProvider:
    choice = (preferred or settings.ocr_provider or "tesseract").lower()
    if choice == "azure" and settings.azure_configured:
        return AzureOCRProvider()
    if _tesseract_available():
        return TesseractOCRProvider()
    return SidecarByStemOCRProvider()


def create_fallback_provider(primary: IOCRProvider) -> IOCRProvider:
    if _tesseract_available() and primary.name != "tesseract":
        return TesseractOCRProvider()
    return SidecarByStemOCRProvider()
