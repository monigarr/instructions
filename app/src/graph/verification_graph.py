"""LangGraph state machine for label verification."""

from __future__ import annotations

import time
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from src.config import settings
from src.domain.interfaces import IOCRProvider, IRulesEngine
from src.domain.models import VerdictStatus


class VerificationState(dict):
    """TypedDict-compatible state bag for LangGraph."""


def build_verification_graph(
    ocr_provider: IOCRProvider,
    rules_engine: IRulesEngine,
    rag_enabled: bool,
):
    from src.agents.ingestion_agent import IngestionAgent
    from src.agents.vision_extraction_agent import VisionExtractionAgent
    from src.agents.field_structuring_agent import FieldStructuringAgent
    from src.agents.compliance_rag_agent import ComplianceRAGAgent
    from src.agents.rules_engine_agent import RulesEngineAgent
    from src.agents.nuance_agent import NuanceAgent
    from src.adapters.ocr.tesseract_provider import TesseractOCRProvider

    ingest = IngestionAgent()
    extract = VisionExtractionAgent(ocr_provider)
    fallback = VisionExtractionAgent(TesseractOCRProvider(), is_fallback=True)
    structure = FieldStructuringAgent()
    rag = ComplianceRAGAgent(enabled=rag_enabled)
    rules = RulesEngineAgent(rules_engine)
    nuance = NuanceAgent()

    graph = StateGraph(dict)

    async def timed_node(name: str, agent, state: dict) -> dict:
        t0 = time.perf_counter()
        out = await agent.run(state)
        timings = dict(out.get("timings_ms") or state.get("timings_ms") or {})
        timings[name] = (time.perf_counter() - t0) * 1000
        out["timings_ms"] = timings
        return out

    async def n_ingest(state: dict) -> dict:
        return await timed_node("ingest", ingest, state)

    async def n_extract(state: dict) -> dict:
        return await timed_node("extract", extract, state)

    async def n_fallback(state: dict) -> dict:
        out = await timed_node("ocr_fallback", fallback, state)
        out["route"] = "ocr_fallback"
        return out

    async def n_structure(state: dict) -> dict:
        return await timed_node("structure", structure, state)

    async def n_rag(state: dict) -> dict:
        return await timed_node("rag_enrich", rag, state)

    async def n_rules(state: dict) -> dict:
        return await timed_node("rules", rules, state)

    async def n_nuance(state: dict) -> dict:
        return await timed_node("nuance", nuance, state)

    async def n_aggregate(state: dict) -> dict:
        verdicts = state.get("verdicts") or []
        status = "complete"
        if any(v.status == VerdictStatus.MISMATCH for v in verdicts):
            status = "needs_human_review"
        elif any(v.status in (VerdictStatus.UNABLE_TO_VERIFY, VerdictStatus.NEEDS_REVIEW) for v in verdicts):
            status = "needs_human_review"
        return {**state, "status": status, "route": "aggregate"}

    graph.add_node("ingest", n_ingest)
    graph.add_node("extract", n_extract)
    graph.add_node("ocr_fallback", n_fallback)
    graph.add_node("structure", n_structure)
    graph.add_node("rag_enrich", n_rag)
    graph.add_node("rules", n_rules)
    graph.add_node("nuance", n_nuance)
    graph.add_node("aggregate", n_aggregate)

    graph.set_entry_point("ingest")

    def after_ingest(state: dict) -> Literal["extract", "failed"]:
        if state.get("status") == "failed":
            return "failed"
        return "extract"

    def after_extract(state: dict) -> Literal["structure", "ocr_fallback"]:
        ocr = state.get("ocr_result")
        if not ocr or not getattr(ocr, "full_text", "").strip():
            return "ocr_fallback"
        if getattr(ocr, "confidence", 0) < settings.ocr_confidence_threshold:
            return "ocr_fallback"
        return "structure"

    def after_fallback(state: dict) -> Literal["structure", "unable_to_verify"]:
        ocr = state.get("ocr_result")
        if not ocr or not getattr(ocr, "full_text", "").strip():
            errors = list(state.get("errors") or [])
            errors.append("Image unreadable after OCR fallback.")
            return "unable_to_verify"
        return "structure"

    def after_rules(state: dict) -> Literal["nuance", "aggregate"]:
        verdicts = state.get("verdicts") or []
        for v in verdicts:
            if v.field == "brand_name" and v.status == VerdictStatus.NEEDS_REVIEW:
                return "nuance"
        return "aggregate"

    graph.add_conditional_edges("ingest", after_ingest, {"extract": "extract", "failed": END})
    graph.add_conditional_edges("extract", after_extract, {"structure": "structure", "ocr_fallback": "ocr_fallback"})
    graph.add_conditional_edges(
        "ocr_fallback",
        after_fallback,
        {"structure": "structure", "unable_to_verify": END},
    )
    graph.add_edge("structure", "rag_enrich")
    graph.add_edge("rag_enrich", "rules")
    graph.add_conditional_edges("rules", after_rules, {"nuance": "nuance", "aggregate": "aggregate"})
    graph.add_edge("nuance", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()
