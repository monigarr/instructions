"""File-backed batch progress persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from src.domain.models import BatchProgress


class InMemoryBatchStore:
    def __init__(self) -> None:
        self._batches: dict[str, BatchProgress] = {}

    def get(self, batch_id: str) -> BatchProgress | None:
        return self._batches.get(batch_id)

    def set(self, progress: BatchProgress) -> None:
        self._batches[progress.batch_id] = progress

    def load_all(self) -> dict[str, BatchProgress]:
        return dict(self._batches)


class FileBatchStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, BatchProgress] = {}
        self.load_all()

    def _path(self, batch_id: str) -> Path:
        return self._dir / f"{batch_id}.json"

    def get(self, batch_id: str) -> BatchProgress | None:
        if batch_id in self._cache:
            return self._cache[batch_id]
        path = self._path(batch_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        progress = BatchProgress.model_validate(data)
        self._cache[batch_id] = progress
        return progress

    def set(self, progress: BatchProgress) -> None:
        self._cache[progress.batch_id] = progress
        path = self._path(progress.batch_id)
        payload = progress.model_dump()
        fd, tmp = tempfile.mkstemp(dir=self._dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def load_all(self) -> dict[str, BatchProgress]:
        for path in self._dir.glob("*.json"):
            batch_id = path.stem
            if batch_id not in self._cache:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._cache[batch_id] = BatchProgress.model_validate(data)
        return dict(self._cache)
