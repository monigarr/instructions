"""Batch supervisor agent — fan-out with concurrency cap."""

from __future__ import annotations

from src.verify.batch_service import BatchVerificationService


class BatchSupervisorAgent:
    role = "batch_supervisor"

    def __init__(self, service: BatchVerificationService | None = None) -> None:
        self._service = service or BatchVerificationService()

    async def run_batch(self, items):
        return await self._service.run_batch(items)
