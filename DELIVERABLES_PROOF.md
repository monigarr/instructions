# Deliverables Proof — LabelForge

**Primary source of truth:** [ClientRequirement.md](ClientRequirement.md)  
**Submission checklist:** [DELIVERABLES.md](DELIVERABLES.md)  
**Last verified:** 2026-06-09 (local tests + URL health checks)

This document maps each **client-required deliverable** and **functional requirement** to concrete proof: repository file paths, API endpoints, live URLs, and how an evaluator can reproduce the evidence.

---

## 1. Client deliverables (authoritative)

[ClientRequirement.md](ClientRequirement.md) § Deliverables lists exactly **two** submissions:

| # | Client deliverable | Proof | Status |
|---|-------------------|-------|--------|
| 1 | **Source code repository** (GitHub or similar) | [https://github.com/monigarr/instructions](https://github.com/monigarr/instructions) | **Live** |
| 2 | **Deployed application URL** | [https://labelforge.onrender.com](https://labelforge.onrender.com) | **Suspended** — service exists on Render but owner-suspended; reactivate in Render dashboard or redeploy via [render.yaml](render.yaml) |

### 1.1 Deliverable 1 — Source code repository

| Client asks for | Where it lives | How to verify |
|-----------------|----------------|---------------|
| All source code | [`app/`](app/) — FastAPI backend, React UI, rules, OCR, batch, fixtures, evals | `cd app && pip install -e ".[dev]" && pytest tests/ -v` |
| README with setup and run instructions | [`app/README.md`](app/README.md) | Follow Quick start; verify sample label |
| Brief approach documentation | [`app/README.md`](app/README.md) § Approach | Stack, verification flow, assumptions, trade-offs |
| Repo overview + doc index | [`README.md`](README.md) | Links to client docs and `app/` |

**Key application paths:**

| Area | Path |
|------|------|
| API entrypoint | [`app/src/api/main.py`](app/src/api/main.py) |
| Single-label pipeline | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) |
| Batch processing | [`app/src/verify/batch_service.py`](app/src/verify/batch_service.py) |
| TTB field rules | [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) |
| OCR (offline default) | [`app/src/adapters/ocr/tesseract_provider.py`](app/src/adapters/ocr/tesseract_provider.py) |
| OCR fallback / firewall-safe | [`app/src/adapters/ocr/sidecar_provider.py`](app/src/adapters/ocr/sidecar_provider.py) |
| React UI (single + batch tabs) | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Test labels + application fixtures | [`app/fixtures/labels/`](app/fixtures/labels/), [`app/fixtures/applications/`](app/fixtures/applications/) |
| Environment template (no secrets) | [`app/.env.example`](app/.env.example) |
| Unit tests | [`app/tests/test_rules.py`](app/tests/test_rules.py) |
| Eval harness (golden + adversarial) | [`app/evals/`](app/evals/) |
| CI | [`app/.github/workflows/ci.yml`](app/.github/workflows/ci.yml) |
| Docker / production image | [`app/Dockerfile`](app/Dockerfile), [`app/docker-compose.yml`](app/docker-compose.yml) |

### 1.2 Deliverable 2 — Deployed application URL

| Environment | URL | Proof endpoint | Status (2026-06-09) |
|-------------|-----|----------------|---------------------|
| **Production (Render)** | [https://labelforge.onrender.com](https://labelforge.onrender.com) | `GET /health` | **Suspended** — redeploy or resume service on Render |
| **Production UI** | [https://labelforge.onrender.com/](https://labelforge.onrender.com/) | Browser: Single Label + Batch tabs | Same as above |
| **Local API + built UI (Docker)** | [http://localhost:8000](http://localhost:8000) | `GET /health` | Works after `cd app && docker compose up --build` |
| **Local dev UI** | [http://localhost:5173](http://localhost:5173) | Vite dev server | Works with API on port 8000 |

**Deployment configuration (proof deploy is wired):**

| Artifact | Path | Purpose |
|----------|------|---------|
| Render Blueprint | [`render.yaml`](render.yaml) | One-click deploy; root dir `app`, health `/health` |
| Deploy guide | [`app/DEPLOY.md`](app/DEPLOY.md) | Render, Railway, Docker smoke tests |
| Railway config | [`app/railway.toml`](app/railway.toml) | Alternative platform |

**Smoke test (replace URL when production is live):**

```bash
curl https://labelforge.onrender.com/health
curl -X POST https://labelforge.onrender.com/verify \
  -F "image=@app/fixtures/labels/old_tom_match.png" \
  -F "application=$(cat app/fixtures/applications/old_tom_match.json)"
```

**Expected `/health` response shape** (from [`app/src/api/main.py`](app/src/api/main.py)):

```json
{
  "status": "ok",
  "ocr_provider": "tesseract",
  "use_factory_graph": false,
  "rag_enabled": false
}
```

---

## 2. Functional requirements proof

Derived from [ClientRequirement.md](ClientRequirement.md). Each row links stakeholder context to implementation evidence.

### 2.1 Core workflow

| Requirement | Proof (files) | Live / local proof |
|-------------|---------------|-------------------|
| Upload label + application data | UI: [`app/ui/src/App.tsx`](app/ui/src/App.tsx) (`onVerifySingle`, batch upload); API: `POST /verify`, `POST /batch/verify` in [`app/src/api/main.py`](app/src/api/main.py) | Upload `old_tom_match.png` + paste JSON from [`app/fixtures/applications/old_tom_match.json`](app/fixtures/applications/old_tom_match.json) |
| Extract text/fields from label | [`app/src/adapters/ocr/`](app/src/adapters/ocr/), [`app/src/structure/field_mapper.py`](app/src/structure/field_mapper.py) | Response includes structured `verdicts` with `label_value` per field |
| Compare field by field | [`app/src/rules/engine.py`](app/src/rules/engine.py), [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) | Verdict table: Application vs Label columns in UI |
| Match / mismatch / unable to verify | `VerdictStatus` in [`app/src/domain/models.py`](app/src/domain/models.py); rules return per-field status + `reason` | See `warning_title_case` and `unreadable_blank` fixtures |
| Human retains final judgment | UI footer + `needs_review` status; no auto-approve in pipeline | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) footer; `BrandFuzzyRule` → `needs_review` |

### 2.2 TTB label fields (minimum)

Client distilled-spirits example in [`app/fixtures/applications/old_tom_match.json`](app/fixtures/applications/old_tom_match.json):

| Field | Example value | Rule implementation |
|-------|---------------|---------------------|
| Brand name | `OLD TOM DISTILLERY` | `BrandFuzzyRule` — [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) |
| Class / type | `Kentucky Straight Bourbon Whiskey` | `ClassTypeRule` |
| Alcohol content | `45% Alc./Vol. (90 Proof)` | `ABVPatternRule` |
| Net contents | `750 mL` | `NetContentsRule` |
| Government warning | Canonical TTB text | `WarningExactRule` + [`app/src/domain/constants.py`](app/src/domain/constants.py) |
| Bottler/producer address | `Old Tom Distillery, Louisville, KY 40202` | `AddressRule` |
| Country of origin | (imports) | `CountryOfOriginRule`; fixture [`import_france`](app/fixtures/applications/import_france.json) |

**Additional test labels** (client-encouraged):

| Fixture stem | Label image | Application JSON | Demonstrates |
|--------------|-------------|------------------|--------------|
| `old_tom_match` | [`app/fixtures/labels/old_tom_match.png`](app/fixtures/labels/old_tom_match.png) | [`app/fixtures/applications/old_tom_match.json`](app/fixtures/applications/old_tom_match.json) | Happy path — client sample |
| `old_tom_abv_mismatch` | [`app/fixtures/labels/old_tom_abv_mismatch.png`](app/fixtures/labels/old_tom_abv_mismatch.png) | [`app/fixtures/applications/old_tom_abv_mismatch.json`](app/fixtures/applications/old_tom_abv_mismatch.json) | ABV mismatch |
| `warning_title_case` | [`app/fixtures/labels/warning_title_case.png`](app/fixtures/labels/warning_title_case.png) | [`app/fixtures/applications/warning_title_case.json`](app/fixtures/applications/warning_title_case.json) | Rejects title-case warning (Jenny Park) |
| `stones_throw_brand` | [`app/fixtures/labels/stones_throw_brand.png`](app/fixtures/labels/stones_throw_brand.png) | [`app/fixtures/applications/stones_throw_brand.json`](app/fixtures/applications/stones_throw_brand.json) | Brand casing nuance (Dave Morrison) |
| `import_france` | [`app/fixtures/labels/import_france.png`](app/fixtures/labels/import_france.png) | [`app/fixtures/applications/import_france.json`](app/fixtures/applications/import_france.json) | Country of origin |
| `unreadable_blank` | [`app/fixtures/labels/unreadable_blank.png`](app/fixtures/labels/unreadable_blank.png) | [`app/fixtures/applications/unreadable_blank.json`](app/fixtures/applications/unreadable_blank.json) | Unreadable upload handling |

Regenerate all fixtures: `cd app && python scripts/generate_fixtures.py` ([`app/scripts/generate_fixtures.py`](app/scripts/generate_fixtures.py))

### 2.3 Performance (~5 seconds per label)

| Evidence | Value | Source |
|----------|-------|--------|
| `elapsed_ms` in API response | Returned on every `/verify` call | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) |
| UI displays latency | Summary line shows ms | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Eval P95 (golden suite, local, 6 fixtures) | **7.8 ms** P95 | `python evals/runners/run_eval_suite.py` — [`app/evals/metrics/latency_p95.py`](app/evals/metrics/latency_p95.py) |
| Documented target | ≤ ~5 s user-perceived | [`app/README.md`](app/README.md) § Performance |

> **Note:** Eval P95 uses synthetic fixtures with sidecar OCR on developer hardware. Production P95 depends on instance size and cold start; document test conditions when reporting live numbers.

### 2.4 Batch processing (200–300 scale)

| Evidence | Location |
|----------|----------|
| Async batch API | `POST /batch/verify`, `GET /batch/{batch_id}` — [`app/src/api/main.py`](app/src/api/main.py) |
| CSV batch path | `POST /batch/verify-csv` |
| Concurrency cap (protects latency) | `BATCH_CONCURRENCY` default 6 — [`app/src/config.py`](app/src/config.py) |
| Progress + summary (passed/failed/needs review) | [`app/src/verify/batch_service.py`](app/src/verify/batch_service.py), batch tab in [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Sample manifest | [`app/fixtures/applications/batch_manifest.json`](app/fixtures/applications/batch_manifest.json) |

Architecture supports 200–300 items per session via async processing; test at scale locally or on deployed URL before submission.

### 2.5 User experience

| Requirement | Proof |
|-------------|-------|
| Clean, obvious UI | Two top-level tabs: **Single Label** / **Batch** — [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Side-by-side application vs label | Verdict table columns: Application, Label, Verdict |
| No hidden critical actions | Primary buttons: "Verify Label", "Start Batch Verification" |
| Standalone disclaimer | UI footer: no COLA integration |

### 2.6 Error handling

| Scenario | Proof |
|----------|-------|
| Bad upload / unreadable image | [`app/src/ingest/validator.py`](app/src/ingest/validator.py); fixture `unreadable_blank` |
| Invalid JSON | API 400 + UI error message |
| Low-confidence extraction | `unable_to_verify` verdicts; rules check `extraction_confidence` |
| Government warning title case | Unit test `test_warning_title_case_rejected` — [`app/tests/test_rules.py`](app/tests/test_rules.py) |

---

## 3. Constraints proof

| Constraint | Client source | Proof |
|------------|---------------|-------|
| Standalone — no COLA | Marcus Williams | No COLA imports or API calls; documented in [`app/README.md`](app/README.md) |
| No sensitive data | Marcus Williams | Synthetic fixtures only in [`app/fixtures/`](app/fixtures/) |
| Prototype security | Marcus Williams | [`.env.example`](app/.env.example) — no secrets committed; `.gitignore` in [`app/.gitignore`](app/.gitignore) |
| Firewall / egress | Marcus Williams | Tesseract default (`OCR_PROVIDER=tesseract`); optional Azure with fallback — [`app/src/adapters/ocr/factory.py`](app/src/adapters/ocr/factory.py) |
| Working core over ambition | Evaluation criteria | P1 pipeline ships; P2+ factory/graph/RAG behind env flags |

---

## 4. Automated proof (run locally)

```bash
cd app
pip install -e ".[dev]"
python scripts/generate_fixtures.py
pytest tests/ -v                    # 4 passed (2026-06-09)
python evals/runners/run_eval_suite.py
```

**Eval suite output (2026-06-09):**

```json
{
  "golden": {
    "golden_count": 6,
    "field_accuracy_avg": 1.0,
    "latency_p95_ms": 7.8,
    "latency_samples": 6
  },
  "adversarial": {
    "warning_recall": 1.0
  }
}
```

---

## 5. API reference (proof endpoints)

| Method | Path | Purpose | Defined in |
|--------|------|---------|------------|
| `GET` | `/health` | Liveness + config | [`app/src/api/main.py`](app/src/api/main.py) |
| `POST` | `/verify` | Single-label verification | same |
| `POST` | `/batch/verify` | Batch (JSON manifest + images) | same |
| `POST` | `/batch/verify-csv` | Batch (CSV manifest) | same |
| `GET` | `/batch/{batch_id}` | Poll batch progress | same |

---

## 6. Submission readiness snapshot

| Item | Ready? | Action if not |
|------|--------|---------------|
| GitHub repo with full source | **Yes** | — |
| README + approach docs | **Yes** | — |
| Fixtures + tests | **Yes** | — |
| Render Blueprint + Docker | **Yes** | — |
| Live HTTPS URL responding | **No** | Resume or redeploy [labelforge on Render](https://labelforge.onrender.com); update [`app/README.md`](app/README.md) Demo URL when live |

---

## 7. Document map (this repository)

| Document | Role |
|----------|------|
| [ClientRequirement.md](ClientRequirement.md) | **Source of truth** — two deliverables only |
| **This file** | Proof index — file paths + URLs |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist |
| [PRD.md](PRD.md) | Product requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Phased factory design (P2+ in codebase) |
| [app/README.md](app/README.md) | Runnable app docs |

---

*Maintained by Monica Peters (MoniGarr) — Gauntlet AI GFA Cohort 5 Fellowship, 2026*
