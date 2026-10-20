"""Structured logging and request-scoped trace identifiers.

The API emits one JSON object per log line so platform log viewers (Render,
Railway, Docker, Cloud) can filter by ``trace_id`` without parsing prose. A
context variable carries the identifier into async tasks, so pipeline and batch
logs inherit the request that caused them without threading an argument through
every layer.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from contextvars import ContextVar, Token
from datetime import UTC, datetime

_TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)
_VALID_TRACE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_EXTRA_FIELDS = (
    "event",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "label_id",
    "summary",
    "provider",
    "error_count",
)


def new_trace_id(candidate: str | None = None) -> str:
    """Return a caller-supplied trace id if safe, otherwise a fresh UUID.

    Accepting an inbound id lets a proxy or test correlate requests, but the
    value is constrained to avoid log injection or unbounded headers.
    """
    if candidate and _VALID_TRACE_ID.fullmatch(candidate.strip()):
        return candidate.strip()
    return str(uuid.uuid4())


def current_trace_id() -> str | None:
    return _TRACE_ID.get()


def set_trace_id(trace_id: str) -> Token[str | None]:
    return _TRACE_ID.set(trace_id)


def reset_trace_id(token: Token[str | None]) -> None:
    _TRACE_ID.reset(token)


class _TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = getattr(record, "trace_id", None) or current_trace_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None) or current_trace_id() or "-",
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Install a single application handler without disturbing uvicorn/pytest.

    Repeated calls replace only the handler this function owns, so importing the
    API in tests or reloading under uvicorn does not duplicate log lines.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter()
        if json_output
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s trace_id=%(trace_id)s %(message)s")
    )
    handler.addFilter(_TraceIdFilter())
    handler._labelforge_handler = True  # type: ignore[attr-defined]

    root = logging.getLogger()
    for existing in list(root.handlers):
        if getattr(existing, "_labelforge_handler", False):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper())
    logging.getLogger("labelforge").setLevel(level.upper())
