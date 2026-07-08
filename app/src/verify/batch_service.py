"""Batch verification with concurrency cap and progress tracking."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from src.config import settings
from src.domain.interfaces import IBatchSupervisor
from src.domain.models import ApplicationRecord, BatchItemResult, BatchProgress, LabelSummary, VerificationResult
from src.verify.batch_store import FileBatchStore, InMemoryBatchStore
from src.verify.pipeline import VerificationPipeline

if TYPE_CHECKING:
    from src.factory.labelforge_factory import LabelForgeFactory

VerifyFn = Callable[[bytes, ApplicationRecord, str | None], Awaitable[VerificationResult]]


class BatchVerificationService(IBatchSupervisor):
    def __init__(
        self,
        pipeline: VerificationPipeline | None = None,
        factory: LabelForgeFactory | None = None,
        verify_fn: VerifyFn | None = None,
        store: InMemoryBatchStore | FileBatchStore | None = None,
    ) -> None:
        self._factory = factory
        self._pipeline = pipeline or VerificationPipeline()
        self._verify_fn = verify_fn
        if store is not None:
            self._store = store
        elif settings.batch_persist:
            self._store = FileBatchStore(settings.batch_persist_dir)
        else:
            self._store = InMemoryBatchStore()
        self._lock = asyncio.Lock()

    def get_progress(self, batch_id: str, *, summary_only: bool = False) -> BatchProgress | None:
        progress = self._store.get(batch_id)
        if progress is None:
            return None
        if summary_only:
            return progress.model_copy(update={"items": []})
        return progress

    async def _verify(self, image: bytes, app: ApplicationRecord, content_type: str | None) -> VerificationResult:
        if self._verify_fn is not None:
            return await self._verify_fn(image, app, content_type)
        if settings.use_factory_graph and self._factory is not None:
            runner = self._factory.create_graph_runner()
            return await runner.run(image, app, trace_id=app.label_id)
        return await self._pipeline.verify(image, app, content_type)

    async def _record_item(self, progress: BatchProgress, item: BatchItemResult, *, error: bool = False) -> None:
        async with self._lock:
            progress.items.append(item)
            progress.completed += 1
            if error:
                progress.errors += 1
            elif item.status == LabelSummary.PASSED:
                progress.passed += 1
            elif item.status == LabelSummary.FAILED:
                progress.failed += 1
            else:
                progress.needs_review += 1
            self._store.set(progress)

    async def run_batch(
        self,
        items: list[tuple[str, bytes, ApplicationRecord, str | None]],
    ) -> BatchProgress:
        batch_id = str(uuid.uuid4())
        progress = BatchProgress(
            batch_id=batch_id,
            total=len(items),
            completed=0,
            passed=0,
            failed=0,
            needs_review=0,
            errors=0,
            finished=False,
        )
        self._store.set(progress)

        sem = asyncio.Semaphore(settings.batch_concurrency)

        async def _process(label_id: str, image: bytes, app: ApplicationRecord, ctype: str | None):
            async with sem:
                try:
                    result = await self._verify(image, app, ctype)
                    if result.errors and not result.verdicts:
                        item = BatchItemResult(
                            label_id=label_id, status=LabelSummary.FAILED, error="; ".join(result.errors)
                        )
                        await self._record_item(progress, item, error=True)
                    else:
                        item = BatchItemResult(label_id=label_id, status=result.summary, result=result)
                        await self._record_item(progress, item)
                except Exception as exc:
                    item = BatchItemResult(label_id=label_id, status=LabelSummary.FAILED, error=str(exc))
                    await self._record_item(progress, item, error=True)

        await asyncio.gather(*[_process(lid, img, app, ct) for lid, img, app, ct in items])
        progress.finished = True
        self._store.set(progress)
        return progress

    async def start_batch_async(
        self,
        items: list[tuple[str, bytes, ApplicationRecord, str | None]],
    ) -> str:
        batch_id = str(uuid.uuid4())
        progress = BatchProgress(
            batch_id=batch_id,
            total=len(items),
            completed=0,
            passed=0,
            failed=0,
            needs_review=0,
            errors=0,
            finished=False,
        )
        self._store.set(progress)

        async def _run():
            sem = asyncio.Semaphore(settings.batch_concurrency)

            async def _process(label_id: str, image: bytes, app: ApplicationRecord, ctype: str | None):
                async with sem:
                    try:
                        result = await self._verify(image, app, ctype)
                        if result.errors and not result.verdicts:
                            item = BatchItemResult(
                                label_id=label_id, status=LabelSummary.FAILED, error="; ".join(result.errors)
                            )
                            await self._record_item(progress, item, error=True)
                        else:
                            item = BatchItemResult(label_id=label_id, status=result.summary, result=result)
                            await self._record_item(progress, item)
                    except Exception as exc:
                        item = BatchItemResult(label_id=label_id, status=LabelSummary.FAILED, error=str(exc))
                        await self._record_item(progress, item, error=True)

            await asyncio.gather(*[_process(lid, img, app, ct) for lid, img, app, ct in items])
            progress.finished = True
            self._store.set(progress)

        asyncio.create_task(_run())
        return batch_id
