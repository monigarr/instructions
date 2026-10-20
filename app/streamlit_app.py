"""
===============================================================================
FILE: streamlit_app.py
AUTHOR: MoniGarr (Monica Peters)
CREATED: 2026-10-19
UPDATED: 2026-10-19
CLASSIFICATION: Internal

PURPOSE:
Streamlit Community Cloud implementation — a third deployment surface over the
same verification engine used by the FastAPI/React app and Docker image. The
repo-root streamlit_app.py shim executes this file for the default deploy path.

DEPENDENCIES:
  - src.verify.pipeline — P1 linear verification pipeline (no FastAPI needed)
  - src.domain.models — ApplicationRecord / result models
  - src.api.samples_catalog — curated gallery + fixture manifests

SECURITY:
  - Prototype posture: no authentication, synthetic fixtures only (PRD §8).
  - Uploads validated by the same ingest validator as the API (size/MIME/decode).
  - No application data is logged; results stay in the browser session.

PERFORMANCE:
  - Single label: same ~5 s/label budget as the API.
  - Batch: chunked at 25 labels with concurrency 2 (below the API's 6) so the
    free Community Cloud tier stays within memory. On Community Cloud the live
    demo is capped at 25 labels per run because sustained 200–300 label batches
    trigger platform CPU throttling; local, Docker, Render, and the API still
    support 200–300. Python and glibc memory are released after each chunk.

OPERATIONAL:
  - Run locally: streamlit run streamlit_app.py (or app/streamlit_app.py)
  - Community Cloud: root entrypoint streamlit_app.py; deps requirements.txt;
    apt packages (tesseract-ocr) via root packages.txt.
  - Rollback: the API/React/Docker/Render surfaces are unchanged.
===============================================================================
"""

from __future__ import annotations

import asyncio
import csv
import gc
import hashlib
import io
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.api.samples_catalog import SAMPLE_CATALOG  # noqa: E402
from src.domain.batch_limits import (  # noqa: E402
    FREE_TIER_BATCH_LIMIT,
    batch_limit,
    batch_limit_error,
    is_community_cloud,
)
from src.domain.fixture_stem import resolve_fixture_stem  # noqa: E402
from src.domain.models import ApplicationRecord, LabelSummary, VerificationResult  # noqa: E402
from src.verify.pipeline import VerificationPipeline  # noqa: E402

ROOT = APP_DIR
FIXTURES = ROOT / "fixtures"
LABELS = FIXTURES / "labels"
APPLICATIONS = FIXTURES / "applications"

CHUNK_SIZE = 25
# The free Community Cloud tier has limited CPU and memory. Two OCR jobs at a
# time keeps peak usage below the limit, and the live demo is capped at one
# 25-label chunk because longer runs trigger platform CPU throttling.
CHUNK_CONCURRENCY = 2
LATENCY_BUDGET_MS = 5000.0
IS_COMMUNITY_CLOUD = is_community_cloud()
BATCH_LIMIT = batch_limit()


def _release_memory() -> None:
    """Return freed Python/glibc memory to the OS after each batch chunk.

    Streaming 200-300 labels repeatedly allocates large OCR buffers. CPython and
    glibc can retain those arenas after the objects are freed, which eventually
    trips the Community Cloud memory limit. ``malloc_trim`` is Linux-only and
    optional; the rest of the app works if it is unavailable.
    """
    gc.collect()
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):
        pass


STATUS_ICON = {
    "match": "✅",
    "mismatch": "❌",
    "needs_review": "⚠️",
    "unable_to_verify": "❔",
}
SUMMARY_STYLE = {
    LabelSummary.PASSED.value: ("✅ Passed", "success"),
    LabelSummary.FAILED.value: ("❌ Failed", "error"),
    LabelSummary.NEEDS_REVIEW.value: ("⚠️ Needs review", "warning"),
}

st.set_page_config(
    page_title="LabelForge — TTB Label Verification",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner=False)
def get_pipeline() -> VerificationPipeline:
    """One pipeline per server process — same engine as the API."""
    return VerificationPipeline()


def _sample_bytes(sample_id: str) -> bytes | None:
    path = LABELS / f"{sample_id}.png"
    return path.read_bytes() if path.is_file() else None


def _sample_application(sample_id: str) -> dict[str, Any] | None:
    path = APPLICATIONS / f"{sample_id}.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("label_id", sample_id)
    return data


def _verdict_rows(result: VerificationResult) -> list[dict[str, Any]]:
    return [
        {
            "Field": verdict.field.replace("_", " ").title(),
            "Status": f"{STATUS_ICON.get(verdict.status.value, '•')} {verdict.status.value.replace('_', ' ')}",
            "Application": verdict.application_value or "—",
            "Label": verdict.label_value or "—",
            "Reason": verdict.reason or "—",
        }
        for verdict in result.verdicts
    ]


def _render_result(result: VerificationResult, *, show_raw_text: str | None = None) -> None:
    label, banner = SUMMARY_STYLE.get(result.summary.value, ("Unknown", "info"))
    getattr(st, banner)(f"**{label}** — {result.label_id}")
    cols = st.columns(4)
    cols[0].metric("Elapsed", f"{result.elapsed_ms / 1000:.2f} s")
    cols[1].metric("Fields checked", len(result.verdicts))
    cols[2].metric("Mismatches", sum(1 for v in result.verdicts if v.status.value == "mismatch"))
    cols[3].metric("Needs review", sum(
        1 for v in result.verdicts if v.status.value in ("needs_review", "unable_to_verify")
    ))
    if result.elapsed_ms > LATENCY_BUDGET_MS:
        st.warning(
            f"This label took {result.elapsed_ms / 1000:.1f} s, above the ~5 s/label budget. "
            "Try a flatter, better-lit image."
        )
    if result.verdicts:
        st.dataframe(_verdict_rows(result), hide_index=True)
    for error in result.errors:
        st.warning(error)
    if show_raw_text:
        with st.expander("Extracted text (OCR)"):
            st.text(show_raw_text)
    st.caption(f"trace_id: {result.trace_id or 'n/a'}")


def _batch_results_rows(batch: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label_id in batch["order"]:
        entry = batch["results"].get(label_id)
        if entry is None:
            continue
        if entry.get("error"):
            rows.append(
                {
                    "Label": label_id,
                    "Status": "❌ error",
                    "Elapsed (s)": "",
                    "Failed fields": "",
                    "Detail": entry["error"],
                }
            )
            continue
        result = entry["result"]
        failed = [
            v["field"]
            for v in result.get("verdicts", [])
            if v["status"] in ("mismatch", "unable_to_verify", "needs_review")
        ]
        rows.append(
            {
                "Label": label_id,
                "Status": f"{STATUS_ICON.get(result['summary'], '•')} {result['summary'].replace('_', ' ')}",
                "Elapsed (s)": round(result.get("elapsed_ms", 0) / 1000, 2),
                "Failed fields": ", ".join(failed) or "—",
                "Detail": "; ".join(result.get("errors", [])) or "—",
            }
        )
    return rows


def _batch_csv(batch: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["label_id", "status", "elapsed_ms", "failed_fields", "error", "trace_id"])
    for label_id in batch["order"]:
        entry = batch["results"].get(label_id)
        if entry is None:
            continue
        if entry.get("error"):
            writer.writerow([label_id, "error", "", "", entry["error"], ""])
            continue
        result = entry["result"]
        failed = [
            v["field"]
            for v in result.get("verdicts", [])
            if v["status"] in ("mismatch", "unable_to_verify", "needs_review")
        ]
        writer.writerow(
            [
                label_id,
                result["summary"],
                round(result.get("elapsed_ms", 0), 1),
                ";".join(failed),
                ";".join(result.get("errors", [])),
                result.get("trace_id", ""),
            ]
        )
    return buffer.getvalue()


def _builtin_batch(size: int) -> list[dict[str, Any]]:
    path = APPLICATIONS / f"batch_manifest_{size}.json"
    manifest: list[dict[str, Any]]
    if path.is_file():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    elif size == FREE_TIER_BATCH_LIMIT:
        # Keep the free-tier demo available even if the generated 25-label
        # manifest is missing; the first 25 scale fixtures are stable.
        fallback = APPLICATIONS / "batch_manifest_200.json"
        manifest = json.loads(fallback.read_text(encoding="utf-8"))[:size]
    else:
        manifest = json.loads((APPLICATIONS / "batch_manifest.json").read_text(encoding="utf-8"))
    items = []
    for entry in manifest:
        label_id = str(entry.get("label_id") or "single")
        items.append(
            {
                "label_id": label_id,
                "application": entry,
                "image_key": resolve_fixture_stem(label_id),
            }
        )
    return items


def _fixture_size_control() -> int:
    """Render the fixture-size chooser, disabling 200/300 on the free tier."""
    default = FREE_TIER_BATCH_LIMIT if BATCH_LIMIT is not None else 200
    if "fixture_batch_size" not in st.session_state:
        st.session_state["fixture_batch_size"] = default
    if BATCH_LIMIT is not None and int(st.session_state["fixture_batch_size"]) > BATCH_LIMIT:
        st.session_state["fixture_batch_size"] = default

    current = int(st.session_state["fixture_batch_size"])
    options = (
        (FREE_TIER_BATCH_LIMIT, f"{FREE_TIER_BATCH_LIMIT} labels"),
        (200, "200 labels"),
        (300, "300 labels"),
    )
    st.caption("Fixture batch")
    columns = st.columns(3)
    for column, (size, label) in zip(columns, options, strict=True):
        disabled = BATCH_LIMIT is not None and size > BATCH_LIMIT
        help_text = None
        if disabled:
            help_text = (
                "Unavailable on the Streamlit Community Cloud free tier. "
                "Use local, Docker, Render, or the FastAPI batch endpoints for "
                "200–300 labels."
            )
        with column:
            if st.button(
                label,
                key=f"fixture_size_{size}",
                type="primary" if size == current else "secondary",
                disabled=disabled,
                help=help_text,
            ):
                st.session_state["fixture_batch_size"] = size
                current = size
    return current


def _signature(items: list[dict[str, Any]]) -> str:
    payload = "|".join(f"{item['label_id']}:{item['image_key']}" for item in items)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _new_batch(items: list[dict[str, Any]], images: dict[str, bytes] | None) -> None:
    limit_error = batch_limit_error(len(items))
    if limit_error:
        raise ValueError(limit_error)
    st.session_state["batch"] = {
        "signature": _signature(items),
        "items": items,
        "order": [item["label_id"] for item in items],
        "cursor": 0,
        "results": {},
        "elapsed": [],
        "finished": False,
        "error": None,
        "started_at": time.time(),
    }
    st.session_state["batch_images"] = images or {}


def _load_image(state: dict[str, Any], item: dict[str, Any]) -> bytes:
    images = st.session_state.get("batch_images") or {}
    key = item["image_key"]
    if key in images:
        return images[key]
    path = LABELS / f"{key}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Fixture image not found for {item['label_id']} ({key}.png)")
    return path.read_bytes()


async def _verify_chunk(items: list[dict[str, Any]]) -> list[tuple[str, Any]]:
    pipeline = get_pipeline()
    sem = asyncio.Semaphore(CHUNK_CONCURRENCY)

    async def _one(item: dict[str, Any]) -> tuple[str, Any]:
        async with sem:
            try:
                image = _load_image(st.session_state["batch"], item)
                application = ApplicationRecord(**item["application"])
                result = await pipeline.verify(image, application, "image/png")
                return item["label_id"], result
            except Exception as exc:  # per-item isolation: one bad label never sinks the batch
                return item["label_id"], exc

    return await asyncio.gather(*[_one(item) for item in items])


def _run_batch() -> None:
    batch = st.session_state.get("batch")
    if not batch or batch["finished"]:
        return
    progress = st.progress(0.0, text="Starting batch…")
    status = st.empty()
    total = len(batch["order"])
    try:
        while batch["cursor"] < total:
            start_index = batch["cursor"]
            chunk = batch["items"][start_index : start_index + CHUNK_SIZE]
            outcomes = asyncio.run(_verify_chunk(chunk))
            for label_id, outcome in outcomes:
                # Classify by exception, not by isinstance(VerificationResult).
                # Community Cloud hot reloads can leave the pipeline holding a
                # different copy of the model class, which made valid results
                # look like errors and reported every label as failed.
                if isinstance(outcome, BaseException):
                    batch["results"][label_id] = {"error": str(outcome)}
                else:
                    batch["results"][label_id] = {"result": outcome.model_dump(mode="json")}
                    batch["elapsed"].append(outcome.elapsed_ms)
            batch["cursor"] = start_index + len(chunk)
            # Release uploaded bytes for completed items — bounded memory on free tier.
            images = st.session_state.get("batch_images") or {}
            for item in chunk:
                images.pop(item["image_key"], None)
            _release_memory()
            done = batch["cursor"]
            progress.progress(
                done / total,
                text=f"Verified {done} of {total} labels "
                f"(chunk {done // CHUNK_SIZE}/{max(1, -(-total // CHUNK_SIZE))})…",
            )
            status.caption(
                f"Checkpoint saved after {done} labels — safe to resume if the session stops."
            )
        batch["finished"] = True
        batch["error"] = None
        progress.progress(1.0, text=f"Batch complete — {total} labels verified.")
        status.empty()
        _release_memory()
    except Exception as exc:  # keep the checkpoint; the Resume button continues
        batch["error"] = str(exc)
        _release_memory()
        progress.empty()
        st.error(
            f"Batch paused after {batch['cursor']} of {total} labels: {exc}. "
            "Results so far are saved in this session — use Resume batch to continue."
        )


def _batch_metrics(batch: dict[str, Any]) -> None:
    rows = _batch_results_rows(batch)
    passed = sum(1 for row in rows if row["Status"].endswith("passed"))
    failed = sum(1 for row in rows if row["Status"].endswith("failed"))
    review = sum(1 for row in rows if "review" in row["Status"])
    errors = sum(1 for row in rows if "error" in row["Status"])
    slow = sum(1 for ms in batch["elapsed"] if ms > LATENCY_BUDGET_MS)
    cols = st.columns(5)
    cols[0].metric("Verified", f"{len(rows)}/{len(batch['order'])}")
    cols[1].metric("Passed", passed)
    cols[2].metric("Failed", failed)
    cols[3].metric("Needs review", review)
    cols[4].metric("Errors", errors)
    if batch["elapsed"]:
        mean_s = sum(batch["elapsed"]) / len(batch["elapsed"]) / 1000
        st.caption(
            f"Mean latency {mean_s:.2f} s/label · target ≤ {LATENCY_BUDGET_MS / 1000:.0f} s · "
            f"above target: {slow}"
        )
    if batch["error"]:
        st.warning(f"Last interruption: {batch['error']}")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏷️ LabelForge")
st.caption(
    "TTB alcohol label verification — compare a label image against its application data. "
    "Prototype: synthetic fixtures, no login, results are not stored."
)

tab_single, tab_batch, tab_about = st.tabs(["Verify one label", "Batch verify", "About"])

# ---------------------------------------------------------------------------
# Tab 1 — single label
# ---------------------------------------------------------------------------
with tab_single:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("1. Choose a label")
        sample_titles = ["Upload my own label"] + [
            f"{sample['title']} — {sample['category']}" for sample in SAMPLE_CATALOG
        ]
        choice = st.selectbox("Label source", sample_titles, index=1)
        sample_id = None
        image_bytes: bytes | None = None
        if choice == "Upload my own label":
            upload = st.file_uploader(
                "Label image (PNG, JPEG, WebP, GIF — max 10 MB)",
                type=["png", "jpg", "jpeg", "webp", "gif"],
                key="single_upload",
            )
            if upload is not None:
                image_bytes = upload.getvalue()
                st.image(image_bytes, caption=upload.name, width=320)
        else:
            sample_id = SAMPLE_CATALOG[sample_titles.index(choice) - 1]["id"]
            image_bytes = _sample_bytes(sample_id)
            if image_bytes:
                st.image(image_bytes, caption=sample_id, width=320)
            sample = SAMPLE_CATALOG[sample_titles.index(choice) - 1]
            st.info(sample["description"])

    with right:
        st.subheader("2. Application data")
        default_app = _sample_application(sample_id) if sample_id else None
        if default_app is None:
            default_app = {
                "label_id": "single",
                "brand_name": "",
                "class_type": "",
                "alcohol_content": "",
                "net_contents": "",
                "government_warning": "",
                "bottler_producer_address": "",
                "country_of_origin": "",
            }
        if sample_id:
            st.caption("Loaded from the curated sample application — edit if you like.")
        app_text = st.text_area(
            "Application JSON (from the COLA application)",
            value=json.dumps(default_app, indent=2),
            height=340,
            key=f"app_json_{sample_id or 'upload'}",
        )

    if st.button("Verify label", type="primary", key="verify_single"):
        if not image_bytes:
            st.error("Choose a sample or upload a label image first.")
        else:
            try:
                application_data = json.loads(app_text)
                application = ApplicationRecord(**application_data)
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"Application JSON is invalid: {exc}")
            else:
                with st.spinner("Running OCR + deterministic rules…"):
                    try:
                        result = asyncio.run(
                            get_pipeline().verify(image_bytes, application, "image/png")
                        )
                    except Exception as exc:  # never a silent failure
                        st.error(f"Verification failed: {exc}")
                    else:
                        st.divider()
                        _render_result(result)

    with st.expander("What this checks"):
        st.markdown(
            "- Brand name (fuzzy, casing/apostrophe nuance)\n"
            "- Class/type designation\n"
            "- Alcohol content (ABV/proof format)\n"
            "- Net contents\n"
            "- Government warning (exact text + header boldness)\n"
            "- Bottler/producer address\n"
            "- Country of origin (imports)"
        )

# ---------------------------------------------------------------------------
# Tab 2 — batch (chunked + resumable, 200–300 supported)
# ---------------------------------------------------------------------------
with tab_batch:
    st.subheader("Batch verify")
    if BATCH_LIMIT is not None:
        st.caption(
            f"Free-tier mode: one batch of up to {BATCH_LIMIT} labels at a time. "
            "The live Community Cloud tier throttles sustained CPU, so 200/300 "
            "are disabled here; they remain available locally, in Docker, and "
            "through the FastAPI batch endpoints."
        )
    else:
        st.caption(
            "Batches run in chunks of 25 with concurrency 2 and checkpoint after every chunk. "
            "A 200–300 label run is supported and can resume after an interruption."
        )

    source = st.radio(
        "Batch source",
        ["Built-in fixture batch", "Upload images + manifest"],
        horizontal=True,
        key="batch_source",
    )

    items: list[dict[str, Any]] = []
    images: dict[str, bytes] | None = None
    ready = False

    if source.startswith("Built-in"):
        size = _fixture_size_control()
        items = _builtin_batch(int(size))
        ready = True
        st.info(
            f"{len(items)} synthetic labels from the repo's scale manifest "
            f"(`batch_manifest_{size}.json`). Images stream from disk one chunk at a time."
        )
    else:
        manifest_file = st.file_uploader(
            "Manifest JSON — a list of application records (each needs `label_id`)",
            type=["json"],
            key="batch_manifest",
        )
        image_files = st.file_uploader(
            "Label images — filenames must match each `label_id` (e.g. `old_tom_match.png`)",
            type=["png", "jpg", "jpeg", "webp", "gif"],
            accept_multiple_files=True,
            key="batch_images_upload",
        )
        if manifest_file is not None and image_files:
            try:
                manifest = json.loads(manifest_file.getvalue())
                if not isinstance(manifest, list):
                    raise ValueError("Manifest must be a JSON array.")
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"Manifest is invalid: {exc}")
            else:
                limit_error = batch_limit_error(len(manifest))
                if limit_error:
                    # Check the manifest itself, not only matched images, so a
                    # large upload cannot slip through with partial images.
                    st.error(limit_error)
                else:
                    image_map: dict[str, bytes] = {}
                    for upload in image_files:
                        data = upload.getvalue()
                        stem = Path(upload.name).stem
                        image_map[stem] = data
                        image_map[upload.name] = data
                    for entry in manifest:
                        label_id = str(entry.get("label_id") or "")
                        key = Path(label_id).stem if label_id else ""
                        if key in image_map:
                            items.append(
                                {"label_id": label_id, "application": entry, "image_key": key}
                            )
                    missing = len(manifest) - len(items)
                    images = image_map
                    ready = bool(items)
                    if missing:
                        st.warning(f"{missing} manifest rows had no matching image and will be skipped.")
                    if items:
                        st.info(f"{len(items)} labels matched and ready to verify.")

    signature = _signature(items) if items else ""
    existing = st.session_state.get("batch")
    resumable = (
        existing is not None
        and not existing["finished"]
        and existing["signature"] == signature
    )
    finished = (
        existing is not None
        and existing["signature"] == signature
        and existing["finished"]
    )

    col_start, col_resume, col_reset = st.columns(3)
    with col_start:
        start = st.button(
            "Start batch" if not resumable else "Restart batch",
            type="primary",
            disabled=not ready,
            key="batch_start",
        )
    with col_resume:
        resume = st.button("Resume batch", disabled=not resumable, key="batch_resume")
    with col_reset:
        reset = st.button("Clear results", disabled=existing is None, key="batch_reset")

    if start and ready:
        _new_batch(items, images)
        _run_batch()
    elif resume and resumable:
        _run_batch()
    elif reset:
        st.session_state.pop("batch", None)
        st.session_state.pop("batch_images", None)

    current = st.session_state.get("batch")
    if current is not None and current["signature"] == signature:
        st.divider()
        _batch_metrics(current)
        rows = _batch_results_rows(current)
        if rows:
            st.dataframe(rows, hide_index=True)
            st.download_button(
                "Download results CSV",
                data=_batch_csv(current),
                file_name="labelforge_batch_results.csv",
                mime="text/csv",
            )

# ---------------------------------------------------------------------------
# Tab 3 — about
# ---------------------------------------------------------------------------
with tab_about:
    st.subheader("What this deployment is")
    st.markdown(
        "LabelForge is a TTB alcohol label verification prototype. This Streamlit surface "
        "uses the **same verification engine** as the FastAPI API and React UI — the "
        "deterministic rules engine, OCR adapters, and batch supervisor are shared code, "
        "not a reimplementation.\n\n"
        "**Verification is deterministic and explainable:** every field yields a status "
        "(`match`, `mismatch`, `needs_review`, `unable_to_verify`) with the application "
        "value, label value, and reason. The tool never auto-approves a COLA.\n\n"
        "**Batch scale:** the live Community Cloud free tier is capped at 25 labels "
        "per run because sustained CPU is throttled. Local, Docker, Render, and the "
        "FastAPI batch endpoints support 200–300 labels in chunks of 25 with "
        "concurrency 2; each chunk is checkpointed, per-item failures are isolated, "
        "and an interrupted run resumes where it stopped."
    )
    st.subheader("Prototype posture and limits")
    st.markdown(
        "- No authentication on this public demo; do not upload sensitive documents.\n"
        "- Synthetic fixtures only — all brands and labels in the repo are fictional.\n"
        "- Results live in the browser session only; nothing is persisted server-side.\n"
        "- OCR is Tesseract (offline). Deployed Community Cloud uses Tesseract 4.1.1; "
        "golden evals are re-run against that version before publishing.\n"
        "- The FastAPI + React app, Docker image, Render, and Railway deployments remain "
        "available and unchanged."
    )
    st.subheader("Runtime check")
    provider = "tesseract" if shutil.which("tesseract") else "sidecar (tesseract not found)"
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("OCR provider", provider)
    col_b.metric("Chunk size", CHUNK_SIZE)
    col_c.metric("Concurrency", CHUNK_CONCURRENCY)
    st.caption(
        "Source: github.com/monigarr/instructions · Client brief: ClientRequirement.md · "
        "Approach: APPROACH.md"
    )
