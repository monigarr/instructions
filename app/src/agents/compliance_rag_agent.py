"""Compliance RAG agent — retrieves TTB regulatory context."""

from __future__ import annotations

from src.rag.retriever import ChromaRAGRetriever


class ComplianceRAGAgent:
    role = "compliance_rag"

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._retriever = ChromaRAGRetriever() if enabled else None

    async def run(self, state: dict) -> dict:
        if not self._enabled or not self._retriever:
            return {**state, "rag_context": [], "route": "rag_skipped"}

        extracted = state.get("extracted")
        if not extracted:
            return {**state, "rag_context": [], "route": "rag_skipped"}

        contexts = []
        for field in ("government_warning", "brand_name", "class_type", "alcohol_content"):
            val = getattr(extracted, field, None) or field
            ctx = await self._retriever.retrieve_for_field(field, str(val))
            contexts.append(ctx)
        return {**state, "rag_context": contexts, "route": "rag_enrich"}
