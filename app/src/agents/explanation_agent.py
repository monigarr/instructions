"""RAG-grounded mismatch explanations (P4 stretch)."""

from __future__ import annotations

from src.domain.models import FieldVerdict, RAGContext


class ExplanationAgent:
    role = "explanation"

    async def run(self, state: dict) -> dict:
        verdicts: list[FieldVerdict] = state.get("verdicts") or []
        rag_context: list[RAGContext] = state.get("rag_context") or []
        explanations: dict[str, str] = {}
        rag_by_field = {c.field: c for c in rag_context}
        for v in verdicts:
            if v.status.value in ("mismatch", "needs_review"):
                chunk = ""
                ctx = rag_by_field.get(v.field)
                if ctx and ctx.chunks:
                    chunk = ctx.chunks[0].excerpt[:200]
                explanations[v.field] = (
                    f"{v.reason}" + (f" Regulatory context: {chunk}" if chunk else "")
                )
        return {**state, "explanations": explanations, "route": "explanation"}
