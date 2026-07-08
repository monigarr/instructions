"""FastAPI application entrypoint."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.samples_catalog import (
    demo_batch_manifest,
    fixture_application_path,
    fixture_image_path,
    list_fixture_labels,
    list_samples,
    sample_application_path,
    sample_image_path,
    scale_batch_manifest,
)
from src.config import settings
from src.domain.fixture_stem import resolve_fixture_stem
from src.domain.models import ApplicationRecord
from src.factory.labelforge_factory import LabelForgeFactory
from src.verify.batch_service import BatchVerificationService
from src.verify.pipeline import VerificationPipeline

app = FastAPI(title="LabelForge", description="TTB Alcohol Label Verification", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_factory = LabelForgeFactory()
_pipeline = _factory.create_pipeline()
_batch_service = BatchVerificationService(pipeline=_pipeline, factory=_factory)


def _parse_application(data: str, label_id: str = "single") -> ApplicationRecord:
    try:
        parsed: dict[str, Any] = json.loads(data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid application JSON: {exc}") from exc
    parsed.setdefault("label_id", label_id)
    return ApplicationRecord(**parsed)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "ocr_provider": settings.ocr_provider,
        "use_factory_graph": settings.use_factory_graph,
        "rag_enabled": settings.rag_enabled,
        "batch_persist": settings.batch_persist,
        "latency_gate_enabled": settings.latency_gate_enabled,
    }


@app.get("/samples")
async def get_samples():
    return {"samples": list_samples()}


@app.get("/labels")
async def get_labels():
    return {"labels": list_fixture_labels()}


@app.get("/labels/{label_id}/image")
async def get_label_image(label_id: str):
    path = fixture_image_path(label_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Label image not found.")
    return FileResponse(path, media_type="image/png")


@app.get("/labels/{label_id}/application")
async def get_label_application(label_id: str):
    path = fixture_application_path(label_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Label application data not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/samples/{sample_id}/image")
async def get_sample_image(sample_id: str):
    path = sample_image_path(sample_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Sample image not found.")
    return FileResponse(path, media_type="image/png")


@app.get("/samples/{sample_id}/application")
async def get_sample_application(sample_id: str):
    path = sample_application_path(sample_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Sample application not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/samples/batch/demo")
async def get_demo_batch():
    manifest = demo_batch_manifest()
    return {
        "total": len(manifest),
        "manifest": manifest,
        "image_ids": sorted({entry["label_id"] for entry in manifest}),
    }


@app.get("/samples/batch/scale/{size}")
async def get_scale_batch(size: int):
    if size not in (200, 300):
        raise HTTPException(status_code=400, detail="Size must be 200 or 300.")
    manifest = scale_batch_manifest(size)
    base_ids = sorted({resolve_fixture_stem(entry["label_id"]) for entry in manifest})
    return {
        "total": len(manifest),
        "manifest": manifest,
        "image_ids": base_ids,
    }


@app.post("/verify")
async def verify_label(
    image: UploadFile = File(...),
    application: str = Form(...),
):
    content = await image.read()
    app_record = _parse_application(application)
    if settings.use_factory_graph:
        result = await _factory.create_graph_runner().run(content, app_record, trace_id=app_record.label_id)
    else:
        result = await _pipeline.verify(content, app_record, image.content_type)
    payload = result.model_dump()
    if settings.latency_gate_enabled:
        payload["latency_warning"] = result.elapsed_ms > settings.latency_warn_ms
    return payload


@app.post("/batch/verify")
async def batch_verify(
    manifest: str = Form(...),
    images: list[UploadFile] = File(...),
    async_mode: str = Form(default="true"),
):
    try:
        manifest_data = json.loads(manifest)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid manifest JSON: {exc}") from exc

    if not isinstance(manifest_data, list):
        raise HTTPException(status_code=400, detail="Manifest must be a JSON array of application records.")

    image_map: dict[str, tuple[bytes, str | None]] = {}
    for img in images:
        data = await img.read()
        stem = Path(img.filename or "unknown").stem
        image_map[stem] = (data, img.content_type)
        image_map[img.filename or ""] = (data, img.content_type)

    items: list[tuple[str, bytes, ApplicationRecord, str | None]] = []
    for entry in manifest_data:
        app_record = ApplicationRecord(**entry)
        label_id = app_record.label_id
        key_candidates = [label_id, f"{label_id}.png", f"{label_id}.jpg", f"labels/{label_id}"]
        matched = None
        for k in key_candidates:
            if k in image_map:
                matched = image_map[k]
                break
        if not matched:
            for fname, payload in image_map.items():
                if label_id in fname:
                    matched = payload
                    break
        if not matched:
            continue
        items.append((label_id, matched[0], app_record, matched[1]))

    if not items:
        raise HTTPException(status_code=400, detail="No manifest entries matched uploaded images.")

    if async_mode.lower() == "true":
        batch_id = await _batch_service.start_batch_async(items)
        return {"batch_id": batch_id, "total": len(items), "status": "processing"}
    progress = await _batch_service.run_batch(items)
    return progress.model_dump()


@app.post("/batch/verify-csv")
async def batch_verify_csv(
    manifest_csv: UploadFile = File(...),
    images: list[UploadFile] = File(default=[]),
    async_mode: str = Form(default="true"),
):
    raw = await manifest_csv.read()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    manifest_data = [dict(row) for row in reader]
    image_map: dict[str, tuple[bytes, str | None]] = {}
    for img in images:
        data = await img.read()
        stem = Path(img.filename or "unknown").stem
        image_map[stem] = (data, img.content_type)
    items: list[tuple[str, bytes, ApplicationRecord, str | None]] = []
    for entry in manifest_data:
        app_record = ApplicationRecord(**entry)
        label_id = app_record.label_id
        matched = image_map.get(label_id) or image_map.get(f"{label_id}.png")
        if matched:
            items.append((label_id, matched[0], app_record, matched[1]))
    if not items:
        raise HTTPException(status_code=400, detail="No CSV rows matched uploaded images.")
    if async_mode.lower() == "true":
        batch_id = await _batch_service.start_batch_async(items)
        return {"batch_id": batch_id, "total": len(items), "status": "processing"}
    progress = await _batch_service.run_batch(items)
    return progress.model_dump()


@app.get("/batch/{batch_id}")
async def get_batch(batch_id: str, summary_only: bool = Query(default=False)):
    progress = _batch_service.get_progress(batch_id, summary_only=summary_only)
    if not progress:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return progress.model_dump()


@app.post("/batch/{batch_id}/resume")
async def resume_batch_review(batch_id: str):
    """P4 HITL stub — human agent acknowledges review queue (no auto-approve)."""
    progress = _batch_service.get_progress(batch_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return {
        "batch_id": batch_id,
        "message": "Human review acknowledged. Proceed with COLA decision externally.",
        "needs_review": progress.needs_review,
    }


_ui_dist = Path(__file__).resolve().parents[2] / "ui" / "dist"
if _ui_dist.exists():
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
