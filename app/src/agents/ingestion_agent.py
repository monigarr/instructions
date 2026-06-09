"""Specialized graph agents."""

from __future__ import annotations

from src.ingest.validator import UploadValidationError, validate_image_upload


class IngestionAgent:
    role = "ingestion"

    async def run(self, state: dict) -> dict:
        image_bytes = state.get("image_bytes")
        errors = list(state.get("errors") or [])
        try:
            validate_image_upload(image_bytes)
            return {**state, "status": "running", "route": "ingest"}
        except UploadValidationError as exc:
            errors.append(str(exc))
            return {**state, "status": "failed", "errors": errors, "route": "failed"}
