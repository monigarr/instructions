"""Deployment-aware batch limits for the Streamlit surface.

The Streamlit Community Cloud free tier throttles sustained CPU, so the live
demo is capped at one 25-label chunk. Local, Docker, Render, and the FastAPI
batch endpoints keep the full 200-300 label support.
"""

from __future__ import annotations

import os
from pathlib import Path

FREE_TIER_BATCH_LIMIT = 25


def is_community_cloud() -> bool:
    """Return True when running on Streamlit Community Cloud.

    ``LABELFORGE_FREE_TIER`` is an explicit override for tests and for any
    future host that enforces the same limit. Otherwise, Community Cloud runs
    apps from ``/mount/src``; local, Docker, Render, and Railway do not.
    """
    override = os.getenv("LABELFORGE_FREE_TIER")
    if override is not None:
        return override.strip().lower() in {"1", "true", "yes", "on"}
    return Path("/mount/src").is_dir()


def batch_limit() -> int | None:
    """Maximum labels allowed in one Streamlit batch, or None when uncapped."""
    return FREE_TIER_BATCH_LIMIT if is_community_cloud() else None


def batch_limit_error(count: int) -> str | None:
    """Return a user-facing error when ``count`` exceeds the deployment limit."""
    limit = batch_limit()
    if limit is None or count <= limit:
        return None
    return (
        f"The Streamlit Community Cloud free tier allows up to {limit} "
        f"labels per batch (this run has {count}). Split the upload into "
        f"batches of {limit}, or use the local, Docker, Render, or "
        "FastAPI surfaces for 200–300 labels."
    )
