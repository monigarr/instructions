"""Field structuring agent."""

from __future__ import annotations

from src.structure.field_mapper import structure_fields


class FieldStructuringAgent:
    role = "field_structuring"

    async def run(self, state: dict) -> dict:
        ocr = state.get("ocr_result")
        if not ocr:
            errors = list(state.get("errors") or [])
            errors.append("No OCR result to structure.")
            return {**state, "errors": errors, "status": "failed"}
        extracted = structure_fields(ocr)
        return {**state, "extracted": extracted, "route": "structure"}
