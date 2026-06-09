"""SOLID port interfaces for LabelForge."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from src.domain.models import (
    ApplicationRecord,
    BatchProgress,
    ExtractedLabelRecord,
    FieldVerdict,
    OCRResult,
    RAGContext,
    VerificationResult,
)


class IOCRProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def extract(self, image_bytes: bytes) -> OCRResult: ...


class IFieldRule(ABC):
    @property
    @abstractmethod
    def field_name(self) -> str: ...

    @abstractmethod
    def evaluate(
        self,
        application: ApplicationRecord,
        extracted: ExtractedLabelRecord,
    ) -> FieldVerdict: ...


class IRulesEngine(ABC):
    @abstractmethod
    def evaluate_all(
        self,
        application: ApplicationRecord,
        extracted: ExtractedLabelRecord,
    ) -> list[FieldVerdict]: ...


class IRAGRetriever(ABC):
    @abstractmethod
    async def retrieve_for_field(self, field: str, query: str, top_k: int = 3) -> RAGContext: ...


class IAgentNode(Protocol):
    role: str

    async def run(self, state: dict[str, Any]) -> dict[str, Any]: ...


class IGraphRunner(ABC):
    @abstractmethod
    async def run(
        self,
        image_bytes: bytes,
        application: ApplicationRecord,
        trace_id: str,
    ) -> VerificationResult: ...


class IBatchSupervisor(ABC):
    @abstractmethod
    async def run_batch(
        self,
        items: list[tuple[str, bytes, ApplicationRecord]],
    ) -> BatchProgress: ...

    @abstractmethod
    def get_progress(self, batch_id: str) -> BatchProgress | None: ...
