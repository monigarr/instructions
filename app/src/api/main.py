"""FastAPI application entrypoint."""

from __future__ import annotations

import json
import csv
import io
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config import settings
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
_batch_service = BatchVerificationService(_pipeline)


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
    return result.model_dump()


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
async def get_batch(batch_id: str):
    progress = _batch_service.get_progress(batch_id)
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
