"""Domain records for label verification."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerdictStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNABLE_TO_VERIFY = "unable_to_verify"
    NEEDS_REVIEW = "needs_review"


class LabelSummary(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ApplicationRecord(BaseModel):
    label_id: str = "single"
    brand_name: str | None = None
    class_type: str | None = None
    alcohol_content: str | None = None
    net_contents: str | None = None
    government_warning: str | None = None
    bottler_producer_address: str | None = None
    country_of_origin: str | None = None


class OCRBlock(BaseModel):
    text: str
    confidence: float = 1.0
    is_bold: bool = False


class OCRResult(BaseModel):
    full_text: str
    blocks: list[OCRBlock] = Field(default_factory=list)
    confidence: float = 1.0
    provider: str = "unknown"


class ExtractedLabelRecord(BaseModel):
    brand_name: str | None = None
    class_type: str | None = None
    alcohol_content: str | None = None
    net_contents: str | None = None
    government_warning: str | None = None
    government_warning_header_bold: bool | None = None
    bottler_producer_address: str | None = None
    country_of_origin: str | None = None
    raw_text: str = ""
    extraction_confidence: float = 1.0


class FieldVerdict(BaseModel):
    field: str
    status: VerdictStatus
    application_value: str | None = None
    label_value: str | None = None
    reason: str = ""
    confidence: float = 1.0


class VerificationResult(BaseModel):
    label_id: str
    verdicts: list[FieldVerdict]
    summary: LabelSummary
    elapsed_ms: float
    trace_id: str | None = None
    errors: list[str] = Field(default_factory=list)


class BatchItemResult(BaseModel):
    label_id: str
    status: LabelSummary
    result: VerificationResult | None = None
    error: str | None = None


class BatchProgress(BaseModel):
    batch_id: str
    total: int
    completed: int
    passed: int
    failed: int
    needs_review: int
    errors: int
    items: list[BatchItemResult] = Field(default_factory=list)
    finished: bool = False


class NuanceSuggestion(BaseModel):
    field: str
    application_value: str
    label_value: str
    equivalent: bool
    reason: str


class RAGChunk(BaseModel):
    chunk_id: str
    field: str | None = None
    excerpt: str
    score: float = 0.0


class RAGContext(BaseModel):
    field: str
    chunks: list[RAGChunk] = Field(default_factory=list)


class VerificationStateDict(BaseModel):
    """Serializable graph state for P2+."""

    run_id: str
    trace_id: str
    label_id: str
    application: ApplicationRecord
    ocr_result: OCRResult | None = None
    extracted: ExtractedLabelRecord | None = None
    rag_context: list[RAGContext] = Field(default_factory=list)
    verdicts: list[FieldVerdict] = Field(default_factory=list)
    nuance: NuanceSuggestion | None = None
    status: str = "running"
    errors: list[str] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    route: str = ""
    image_bytes: bytes | None = None

    model_config = {"arbitrary_types_allowed": True}

    def to_graph_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude={"image_bytes"})
