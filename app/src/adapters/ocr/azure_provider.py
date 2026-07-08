"""
===============================================================================
FILE: azure_provider.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
Azure Document Intelligence OCR when credentials are configured.

PERFORMANCE:
Network-bound; pipeline falls back to Tesseract on timeout/failure.
===============================================================================
"""

from __future__ import annotations

import asyncio

from src.config import settings
from src.domain.interfaces import IOCRProvider
from src.domain.models import OCRBlock, OCRResult
from src.ingest.preprocess import preprocess_for_ocr


class AzureOCRProvider(IOCRProvider):
    @property
    def name(self) -> str:
        return "azure"

    async def extract(self, image_bytes: bytes) -> OCRResult:
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            from azure.core.credentials import AzureKeyCredential
        except ImportError as exc:
            raise RuntimeError("azure-ai-documentintelligence not installed") from exc

        processed = preprocess_for_ocr(
            image_bytes,
            deskew=settings.preprocess_imperfect,
            enhance_imperfect=settings.preprocess_imperfect,
        )

        def _call() -> OCRResult:
            client = DocumentIntelligenceClient(
                endpoint=settings.azure_document_intelligence_endpoint,
                credential=AzureKeyCredential(settings.azure_document_intelligence_key),
            )
            poller = client.begin_analyze_document(
                "prebuilt-read",
                AnalyzeDocumentRequest(bytes_source=processed),
            )
            result = poller.result()
            lines: list[OCRBlock] = []
            confidences: list[float] = []
            full_parts: list[str] = []
            if result.pages:
                for page in result.pages:
                    for line in page.lines or []:
                        text = line.content or ""
                        full_parts.append(text)
                        conf = 0.9
                        is_bold = text.isupper() and "GOVERNMENT" in text.upper()
                        lines.append(OCRBlock(text=text, confidence=conf, is_bold=is_bold))
                        confidences.append(conf)
            avg = sum(confidences) / len(confidences) if confidences else 0.5
            return OCRResult(
                full_text="\n".join(full_parts),
                blocks=lines,
                confidence=avg,
                provider=self.name,
            )

        return await asyncio.to_thread(_call)
