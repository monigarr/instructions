# Security Audit Report — LabelForge

**Date:** July 8, 2026  
**Repository:** `instructions` (LabelForge / TTB Alcohol Label Verification)  
**Auditor:** Automated read-only security review  
**Scope:** Full repository; primary application code under `app/`  
**Methodology:** Static source review, configuration analysis, dependency review, endpoint inventory. No dynamic penetration testing or dependency CVE scanning was performed.

---

## Executive Summary

LabelForge is a TTB alcohol label verification prototype combining a FastAPI backend, React UI, OCR pipeline, deterministic rules engine, and optional RAG. The codebase demonstrates intentional prototype-level security awareness (secrets via environment variables, upload validation, fixture path whitelisting, deterministic verdicts). However, **the application is not production-hardened** and should not be exposed to untrusted networks or real sensitive label data without remediation.

| Severity | Count |
|----------|------:|
| Critical | 0 |
| High | 3 |
| Medium | 10 |
| Low | 5 |
| Informational | 8 |
| Positive controls | 10 |

**Top risks:**

1. **No authentication or authorization** on any API endpoint.
2. **Overly permissive CORS** (`"*"` appended to allowed origins with credentials enabled).
3. **Resource exhaustion** via unbounded in-memory upload buffering before validation.
4. **Path traversal** in batch result reads and sidecar OCR fixture lookups.
5. **Missing HTTP security headers** and no rate limiting.

Project documentation (`ARCHITECTURE.md`, `DELIVERABLES.md`, `PRD.md`) explicitly acknowledges prototype security gaps. This audit confirms those gaps in the implementation.

---

## Repository Overview

| Component | Path | Role |
|-----------|------|------|
| API server | `app/src/api/main.py` | FastAPI entrypoint; all HTTP routes |
| UI | `app/ui/` | React + Vite SPA; built to `ui/dist`, served by API |
| Verification pipeline | `app/src/verify/pipeline.py` | Linear OCR → rules flow (P1 default) |
| LangGraph factory | `app/src/graph/`, `app/src/agents/` | Optional orchestration (`USE_FACTORY_GRAPH=true`) |
| OCR adapters | `app/src/adapters/ocr/` | Tesseract (default), Azure DI, sidecar fixtures |
| Rules engine | `app/src/rules/` | Deterministic field rules (no LLM verdicts) |
| RAG | `app/src/rag/` | Chroma + static corpus (optional) |
| Batch processing | `app/src/verify/batch_service.py`, `batch_store.py` | Async batch verify + optional file persistence |
| Deployment | `app/Dockerfile`, `app/docker-compose.yml`, `render.yaml`, `app/railway.toml` | Container + cloud deploy |

**Exposed service:** Single combined web service (API + static UI) on port 8000 (or `$PORT` in cloud).

---

## Findings Summary

| ID | Severity | Location | Finding |
|----|----------|----------|---------|
| SEC-001 | **High** | `app/src/api/main.py:57–250` | No authentication on any endpoint |
| SEC-002 | **High** | `app/src/api/main.py:35–41` | CORS allows wildcard origin with credentials |
| SEC-003 | **High** | `app/src/api/main.py:139,167–170,207–215` | Full upload buffered in memory before size validation |
| SEC-004 | **Medium** | `app/src/verify/batch_store.py:34–43` | Path traversal via user-supplied `batch_id` on read |
| SEC-005 | **Medium** | `app/src/adapters/ocr/sidecar_provider.py:56`, `pipeline.py:41–45` | Path traversal via unvalidated `label_id` in sidecar OCR |
| SEC-006 | **Medium** | `app/src/ingest/validator.py:41–45` | MIME type check skipped when `content_type` omitted |
| SEC-007 | **Medium** | `app/src/ingest/validator.py:47–55` | No image decompression bomb / pixel dimension limits |
| SEC-008 | **Medium** | `app/src/api/main.py:151–229` | No limit on batch image count or manifest size |
| SEC-009 | **Medium** | `app/src/api/main.py` (no middleware) | Missing security headers (CSP, HSTS, X-Frame-Options, etc.) |
| SEC-010 | **Medium** | `app/pyproject.toml:7–17` | Python dependencies unpinned (no lockfile) |
| SEC-011 | **Medium** | `app/Dockerfile:8–24` | Container runs as root; no `USER` directive |
| SEC-012 | **Medium** | `render.yaml:19–20`, `batch_service.py:35–36` | Production enables batch persistence without access controls |
| SEC-013 | **Medium** | `app/src/api/samples_catalog.py:192–208` | Unauthenticated disk write on scale manifest endpoint |
| SEC-014 | **Medium** | `app/src/verify/batch_service.py:102–104,143–145` | Internal exception strings returned to API clients |
| SEC-015 | **Medium** | `app/src/api/main.py:232–237` | Batch results readable by ID without ownership binding |
| SEC-016 | **Low** | `app/src/api/main.py:57–66` | `/health` exposes internal configuration |
| SEC-017 | **Low** | `app/src/api/main.py:240–250` | HITL resume endpoint is unauthenticated stub |
| SEC-018 | **Low** | `app/src/api/main.py:173–188` | Batch silently skips unmatched manifest entries |
| SEC-019 | **Low** | `app/src/domain/models.py:24–32` | Application JSON fields have no length limits |
| SEC-020 | **Low** | `app/src/api/main.py:51–52,159–160` | JSON parse errors include exception detail |
| SEC-021 | **Info** | `app/src/api/main.py:33` | FastAPI `/docs` and `/openapi.json` exposed by default |
| SEC-022 | **Info** | `app/src/config.py:24` | API binds to `0.0.0.0` (expected for containers) |
| SEC-023 | **Info** | Repo root `data/chroma/` | Runtime Chroma artifacts outside `app/.gitignore` scope |
| SEC-024 | **Info** | `.github/workflows/ci.yml` | No dependency vulnerability scanning in CI |
| SEC-025 | **Info** | `app/Dockerfile:23–24` | `EXPOSE 10000` vs default port 8000 mismatch |
| SEC-026 | **Info** | Application code | No SQL or command injection vectors found |
| SEC-027 | **Info** | `app/src/rag/` | RAG corpus is static; no user corpus ingestion |
| SEC-028 | **Info** | `app/evals/`, `app/scripts/` | Dev scripts print reports to stdout |

---

## Detailed Findings

### 1. Authentication & Authorization

#### SEC-001 — No authentication on any endpoint (High)

All HTTP routes are publicly accessible. There is no API key, JWT, session, OAuth, or role-based access control.

**Affected endpoints:**

| Method | Path | Risk |
|--------|------|------|
| GET | `/health` | Configuration disclosure |
| GET | `/samples`, `/labels` | Fixture catalog enumeration |
| GET | `/labels/{id}/image`, `/labels/{id}/application` | Fixture data access |
| GET | `/samples/{id}/image`, `/samples/{id}/application` | Sample data access |
| GET | `/samples/batch/demo`, `/samples/batch/scale/{size}` | Batch manifest access |
| POST | `/verify` | Arbitrary label verification (CPU/OCR cost) |
| POST | `/batch/verify`, `/batch/verify-csv` | Batch submission (amplified cost) |
| GET | `/batch/{batch_id}` | Read batch verification results |
| POST | `/batch/{batch_id}/resume` | Acknowledge review (stub) |

**Impact:** Any network client can submit workloads, read verification results, and enumerate fixture data. Severity escalates to **Critical** if deployed publicly with real TTB label imagery or application data.

**Evidence:**

```33:41:app/src/api/main.py
app = FastAPI(title="LabelForge", description="TTB Alcohol Label Verification", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### SEC-015 — Batch results readable without ownership (Medium)

`GET /batch/{batch_id}` returns full verification results (field values, verdicts, errors) for any valid `batch_id`. New batches use UUIDs (reducing guessability), but there is no caller identity or access token binding.

```232:237:app/src/api/main.py
@app.get("/batch/{batch_id}")
async def get_batch(batch_id: str, summary_only: bool = Query(default=False)):
    progress = _batch_service.get_progress(batch_id, summary_only=summary_only)
    if not progress:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return progress.model_dump()
```

With `BATCH_PERSIST=true` (enabled in `render.yaml`), results are written to `./data/batches` on disk.

#### SEC-017 — HITL resume endpoint unauthenticated (Low)

`POST /batch/{batch_id}/resume` acknowledges human review without identity checks. Low impact today (no privileged state change), but establishes an insecure pattern for future privileged actions.

---

### 2. CORS & HTTP Security Headers

#### SEC-002 — Permissive CORS with credentials (High)

Configured origins from `CORS_ORIGINS` are extended with a literal `"*"`, combined with `allow_credentials=True` and wildcard methods/headers. Browsers may reject `*` + credentials per spec, but the configuration intent is clearly wide open and any cross-origin site may invoke the API.

```35:41:app/src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### SEC-009 — Missing security headers (Medium)

No middleware sets:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Frame-Options` / `frame-ancestors`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`

The UI loads Google Fonts from `fonts.googleapis.com` (`app/ui/index.html`) without CSP restrictions. Static files are served via `StaticFiles` with `html=True` (SPA fallback).

---

### 3. File Upload Handling

#### SEC-003 — Unbounded in-memory buffering before validation (High)

The API reads entire upload bodies into memory before pipeline validation runs:

```134:145:app/src/api/main.py
@app.post("/verify")
async def verify_label(
    image: UploadFile = File(...),
    application: str = Form(...),
):
    content = await image.read()
    ...
```

Batch endpoints repeat this pattern for every image (`await img.read()`). The 10 MB cap in `validate_image_upload()` applies only after buffering. An attacker can send very large payloads and exhaust server memory before rejection.

#### SEC-006 — MIME type check is optional (Medium)

Validation rejects bad MIME types only when `content_type` is provided. Omitted or spoofed content types skip the MIME gate; only PIL decode is used.

```41:45:app/src/ingest/validator.py
    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if content_type and content_type not in allowed:
        raise UploadValidationError(
            "Unsupported file type. Please upload a JPEG or PNG label image."
        )
```

#### SEC-007 — No decompression bomb protection (Medium)

PIL `Image.open().verify()` and `.load()` are used without `Image.MAX_IMAGE_PIXELS` limits or maximum dimension caps. A small compressed image can expand to very large pixel arrays, causing CPU/memory exhaustion.

#### SEC-008 — No batch size limits (Medium)

`/batch/verify` and `/batch/verify-csv` accept unbounded image lists and manifest payloads. Combined with `batch_concurrency=6`, this enables amplified resource consumption.

#### SEC-018 — Silent manifest skips (Low)

Unmatched manifest rows are skipped with `continue` rather than returning an error. Partial batches may process without operator awareness, affecting data integrity rather than direct security.

---

### 4. Path Traversal

#### SEC-004 — `batch_id` path traversal in `FileBatchStore` (Medium)

`_path()` joins user-supplied `batch_id` directly into the filesystem path without sanitization:

```34:43:app/src/verify/batch_store.py
    def _path(self, batch_id: str) -> Path:
        return self._dir / f"{batch_id}.json"

    def get(self, batch_id: str) -> BatchProgress | None:
        ...
        path = self._path(batch_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
```

A `batch_id` such as `../../../path/to/file` on `GET /batch/{batch_id}` could read JSON files outside `BATCH_PERSIST_DIR` if they exist and deserialize to `BatchProgress`. Batch creation uses UUIDs (safe for writes); the read path is the attack surface.

#### SEC-005 — `label_id` path traversal in sidecar OCR (Medium)

User-controlled `label_id` from application JSON flows through `resolve_fixture_stem()` without validation, then into a filesystem join:

```41:45:app/src/verify/pipeline.py
        stem = resolve_fixture_stem(label_id) if label_id else None
        if isinstance(self._primary, SidecarByStemOCRProvider) and stem:
            self._primary.set_stem_hint(stem)
```

```53:59:app/src/adapters/ocr/sidecar_provider.py
    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        if not self._stem_hint:
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)
        path = FIXTURES_LABELS / f"{self._stem_hint}.txt"
        if not path.exists():
            return OCRResult(full_text="", blocks=[], confidence=0.0, provider=self.name)
        text = path.read_text(encoding="utf-8")
```

A `label_id` like `../../secret` can escape `fixtures/labels/` when sidecar OCR fallback is active (Tesseract unavailable).

**Note:** A `sanitize_label_id()` helper exists in `app/src/domain/label_id.py` but is **not used** in the pipeline or sidecar paths. Fixture catalog API routes (`/labels/{id}`, `/samples/{id}`) do validate IDs with a regex whitelist — see positive controls.

---

### 5. Secrets & Configuration Management

**No hardcoded secrets found.** Grep across Python, TypeScript, and JSON found no API keys, tokens, or private keys in source.

| Check | Result |
|-------|--------|
| `.env` in repository | Not present (gitignored under `app/.gitignore`) |
| `.env.example` | Present with empty placeholders (`app/.env.example`) |
| Azure credentials | Loaded from `settings` only (`app/src/config.py`, `azure_provider.py`) |
| Credential logging | Not observed in OCR or API paths |

#### SEC-016 — Health endpoint configuration disclosure (Low)

```57:66:app/src/api/main.py
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
```

Useful for attacker reconnaissance; acceptable for internal monitoring with network controls.

#### SEC-023 — Chroma runtime data at repo root (Info)

Git status shows untracked `data/chroma/` at repository root. `app/.gitignore` covers `data/chroma/` relative to `app/` only. No root-level `.gitignore` exists. Operators should ensure persistence directories are excluded from version control and backups containing sensitive embeddings.

---

### 6. Injection Risks

#### SEC-026 — No SQL or command injection (Info)

- No SQL database usage; Chroma is embedded vector storage; batch data is JSON files.
- No `subprocess`, `os.system`, `shell=True`, or `eval()` in application code.
- Tesseract is invoked via the `pytesseract` library wrapper only.

---

### 7. LLM / RAG Security

**Verdict path is deterministic** — `DeterministicRulesEngine` evaluates field rules; no LLM owns compliance outcomes. LangGraph agents orchestrate OCR/rules; no OpenAI/Anthropic API calls were found in the verdict path.

| Topic | Assessment |
|-------|------------|
| Prompt injection affecting verdicts | **Not applicable** — rules engine is non-LLM |
| RAG query input | OCR-extracted text and field names (`app/src/rag/retriever.py`) |
| RAG impact on outcomes | Low — RAG enriches explanations only; rules own verdict bits |
| User-controlled application JSON | By design for a verification tool; not model injection |
| Corpus trust | Static developer-authored markdown under `app/src/rag/corpus/`; no user upload endpoint |

---

### 8. Dependency Security

#### Python (`app/pyproject.toml`)

| Package | Constraint | Notes |
|---------|------------|-------|
| fastapi | `>=0.115.0` | Lower bound only |
| uvicorn | `>=0.32.0` | Lower bound only |
| pillow | `>=11.0.0` | Image processing attack surface |
| pytesseract | `>=0.3.13` | Native tesseract dependency |
| langgraph | `>=0.2.0` | Optional graph path |
| chromadb | `>=0.5.0` (optional `[rag]`) | Vector DB |

#### SEC-010 — No Python lockfile (Medium)

Open lower bounds prevent reproducible builds and complicate CVE tracking. No `uv.lock`, `poetry.lock`, or `requirements.lock` observed.

#### JavaScript (`app/ui/package.json`)

- Minimal dependency tree (React 18, Vite 5, TypeScript 5).
- `app/ui/package-lock.json` exists — UI dependencies are pinned.

#### SEC-024 — No automated vulnerability scanning (Info)

`.github/workflows/ci.yml` runs tests and builds but does not include Dependabot, `pip-audit`, `npm audit`, Snyk, or similar.

---

### 9. Docker & Deployment

#### SEC-011 — Container runs as root (Medium)

```8:24:app/Dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
...
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

No non-root `USER` directive. Container compromise grants root inside the container namespace.

#### SEC-012 — Batch persistence without ACLs in production (Medium)

`render.yaml` sets `BATCH_PERSIST=true`. Batch JSON is written to `./data/batches` with no encryption, filesystem permissions hardening, or access control beyond unauthenticated API routes.

#### SEC-013 — Unauthenticated disk write on scale endpoint (Medium)

```192:208:app/src/api/samples_catalog.py
def scale_batch_manifest(size: int) -> list[dict]:
    path = APPS / f"batch_manifest_{size}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    ...
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
```

`GET /samples/batch/scale/{size}` (size 200 or 300) generates and writes manifest files when missing. Unauthenticated callers can trigger disk writes (disk-fill DoS vector).

#### SEC-025 — Dockerfile port mismatch (Info)

`EXPOSE 10000` but `CMD` defaults to port 8000. Railway/Render override via `$PORT`; local confusion only.

---

### 10. Error Handling & Information Disclosure

#### SEC-014 — Exception strings in API responses (Medium)

```102:104:app/src/verify/batch_service.py
                except Exception as exc:
                    item = BatchItemResult(label_id=label_id, status=LabelSummary.FAILED, error=str(exc))
                    await self._record_item(progress, item, error=True)
```

Raw `str(exc)` from internal exceptions flows to batch item errors and OCR error lists. May leak library paths, Azure error details, or environment hints.

OCR failures in the pipeline similarly append exception text:

```59:60:app/src/verify/pipeline.py
            except Exception as exc:
                errors.append(f"OCR ({provider.name}) failed: {exc}")
```

#### SEC-019 — Unbounded application JSON fields (Low)

`ApplicationRecord` string fields have no max length. Very large `application` form payloads could cause memory pressure.

#### SEC-020 — JSON parse error detail (Low)

`detail=f"Invalid application JSON: {exc}"` exposes parser messages in 400 responses. Generally acceptable for client debugging.

---

### 11. Logging & Client-Side Security

**Minimal server-side logging (positive):** No `logging` module usage observed in API/pipeline/OCR paths. Reduces risk of logging uploaded images, application data, or Azure keys.

**Errors returned in API body:** OCR/internal errors flow to client `errors[]` arrays and UI display rather than server logs.

**UI XSS:** No `dangerouslySetInnerHTML`, `innerHTML`, or `eval()` found in `app/ui/src/`. React's default escaping applies.

---

## Positive Security Controls

| Control | Location | Notes |
|---------|----------|-------|
| Fixture path validation | `app/src/api/samples_catalog.py:16,94–96,146–157` | Regex `^[a-zA-Z0-9][a-zA-Z0-9_.-]*$`; tests reject `../etc/passwd` |
| Upload validation module | `app/src/ingest/validator.py` | 10 MB cap, empty-file rejection, PIL decode check |
| Secrets via environment | `app/src/config.py`, `app/.env.example` | `.env` gitignored; `extra="ignore"` on settings |
| Deterministic verdict engine | `app/src/rules/engine.py` | Rules, not LLM, own compliance outcomes |
| OCR timeout | `app/src/verify/pipeline.py:52–55` | `asyncio.wait_for(..., timeout=settings.ocr_timeout_seconds)` |
| Batch concurrency cap | `app/src/verify/batch_service.py:88,129` | `asyncio.Semaphore(settings.batch_concurrency)` (default 6) |
| Atomic batch file writes | `app/src/verify/batch_store.py:52–56` | Temp file + `os.replace` |
| No shell execution | Application code | No subprocess from user input |
| `sanitize_label_id` helper exists | `app/src/domain/label_id.py` | Available but not wired into all paths |
| Minimal UI dependencies | `app/ui/package.json` | Small JS attack surface |
| Prototype security documented | `ARCHITECTURE.md`, `DELIVERABLES.md`, `PRD.md` | Acknowledged production gaps |

---

## Recommended Remediation (Prioritized)

These are guidance only; no changes were made during this audit.

### P0 — Before any public deployment with real data

1. **Add authentication** (API key, mutual TLS, or OAuth) to all mutating and data-bearing endpoints.
2. **Fix CORS:** Remove `"*"` from `allow_origins`; set explicit origins; disable `allow_credentials` unless required.
3. **Enforce upload limits at the HTTP layer** before `await file.read()` (middleware or streaming with size cap).
4. **Sanitize filesystem joins:** Apply `sanitize_label_id()` (or equivalent) to `batch_id` reads and sidecar stem hints; resolve paths and verify they remain under intended directories.

### P1 — Hardening

5. Add **rate limiting** on `/verify` and `/batch/*`.
6. Add **security headers middleware** (CSP, `X-Content-Type-Options`, `X-Frame-Options`, HSTS).
7. Set **`Image.MAX_IMAGE_PIXELS`** and maximum width/height before `.load()`.
8. Cap batch image count and manifest payload size.
9. **Disable FastAPI docs** in production (`docs_url=None`, `redoc_url=None`).
10. Return **generic error messages** to clients; log detailed exceptions server-side only.

### P2 — Operational hygiene

11. **Pin Python dependencies** and add CI vulnerability scanning (`pip-audit`, `npm audit`, Dependabot).
12. Run container as **non-root user**.
13. Add root-level `.gitignore` for `data/` artifacts or relocate persistence under `app/`.
14. Encrypt or restrict access to `BATCH_PERSIST_DIR` when persistence is enabled.
15. Gate `scale_batch_manifest` file writes behind auth or pre-generate manifests at build time.

---

## Audit Limitations

- **Static analysis only** — no runtime testing, fuzzing, or authenticated penetration testing.
- **No CVE database lookup** — dependency versions were reviewed for pinning policy, not known vulnerabilities.
- **Prototype context** — findings are assessed against documented prototype intent; production TTB workloads would require a stricter threat model (PII, regulatory data classification, federal ATO considerations).
- **Untracked files** — `data/chroma/` artifacts in git status were noted but not inspected for sensitive content.

---

## Conclusion

LabelForge implements reasonable prototype safeguards: environment-based secrets, upload validation, fixture ID whitelisting on catalog routes, and a deterministic rules engine that avoids LLM verdict manipulation. The primary security debt is **exposure control** — the service is designed to be reachable and usable without friction, which leaves authentication, CORS, rate limiting, and resource bounds as open gaps.

**Overall risk rating for prototype/local use:** Moderate (acceptable with network isolation).  
**Overall risk rating for internet-facing production use with real label data:** High — remediate P0 items before deployment.

---

*End of report.*
