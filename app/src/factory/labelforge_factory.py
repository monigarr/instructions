"""LabelForge composition root — wires pipeline and P2+ graph."""

from __future__ import annotations

from src.adapters.ocr.factory import create_ocr_provider
from src.config import settings
from src.domain.interfaces import IGraphRunner
from src.rules.engine import DeterministicRulesEngine
from src.verify.pipeline import VerificationPipeline


class LabelForgeFactory:
    """Composition root for LabelForge verification services."""

    def __init__(self) -> None:
        self._ocr = create_ocr_provider()
        self._rules = DeterministicRulesEngine()
        self._pipeline = VerificationPipeline(ocr_provider=self._ocr, rules_engine=self._rules)
        self._graph_runner: IGraphRunner | None = None

    def create_pipeline(self) -> VerificationPipeline:
        return self._pipeline

    def create_graph_runner(self) -> IGraphRunner:
        if self._graph_runner is None:
            from src.graph.runner import LangGraphRunner

            self._graph_runner = LangGraphRunner(
                ocr_provider=self._ocr,
                rules_engine=self._rules,
                rag_enabled=settings.rag_enabled,
            )
        return self._graph_runner
