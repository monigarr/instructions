> **Archived 2026-10-19.** Historical document retained for traceability. It predates the repository consolidation; canonical docs are [README](../README.md) | [APPROACH](../APPROACH.md) | [SECURITY_ACCESSIBILITY](../SECURITY_ACCESSIBILITY.md) | [PRD](../PRD.md) | [ClientRequirement](../ClientRequirement.md). Relative links inside this file may be stale.

# Onboarding â€” LabelForge

**Audience:** Software engineers, software architects, DevOps, and technical reviewers onboarding to this repository.

| | |
|---|---|
| **Normative requirements** | [ClientRequirement.md](ClientRequirement.md) â€” **do not edit**; all product decisions trace here |
| **Live demo** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| **Application code** | [`app/`](app/) |
| **3-minute demo** | [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) |
| **Proof index** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) |

**Author:** Monica Peters (MoniGarr) Â· Gauntlet AI GFA Cohort 5, 2026  
**Built with:** AI First / AI Native software architecture and engineering techniques (agent factory, eval harness, deterministic compliance core).

---

## 1. Start here by role

| Role | Read first | Then | Time |
|------|------------|------|------|
| **Client / product reviewer** | [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) Â§0 | ~5 min |
| **New software engineer** | This doc Â§2â€“6 | [app/README.md](app/README.md) | ~30 min |
| **Software architect** | This doc Â§7â€“8 | [ARCHITECTURE.md](ARCHITECTURE.md) Â§1â€“6 | ~45 min |
| **DevOps / SRE** | [app/DEPLOY.md](app/DEPLOY.md) | [render.yaml](render.yaml), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | ~20 min |
| **Interview / depth reviewer** | [README.md](README.md) Â§ Interview reviewers | [ARCHITECTURE.md](ARCHITECTURE.md), [PRD.md](PRD.md) | ~60 min |

---

## 2. What this repository delivers

[ClientRequirement.md](ClientRequirement.md) defines exactly **two** client submissions:

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | **Source code repository** | [github.com/monigarr/instructions](https://github.com/monigarr/instructions) â†’ [`app/`](app/) |
| 2 | **Deployed application URL** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |

Everything else in this repo (PRD, architecture, eval harness, agent factory) supports **engineering quality** and **interview depth** â€” it does not expand the clientâ€™s mandatory scope.

### Stakeholder requirements (from ClientRequirement.md)

| Stakeholder | Requirement | Implementation |
|-------------|-------------|----------------|
| **Sarah Chen** | â‰¤ ~5 s per label; batch **200â€“300** at peak | Tesseract OCR; `elapsed_ms` in API/UI; async batch + scale manifests |
| **Jenny Park** | Government warning **exact**; `GOVERNMENT WARNING:` all caps and bold | [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py); warning fixtures |
| **Dave Morrison** | Brand nuance â†’ human judgment, not auto-pass | `needs_review` verdicts; fuzzy brand normalization |
| **Marcus Williams** | Standalone PoC; firewall-safe; no COLA; no sensitive data | Tesseract default; synthetic fixtures only; no COLA integration |

---

## 3. Repository map

```text
instructions/                          # Repo root (docs + Blueprint)
â”œâ”€â”€ ClientRequirement.md               # Normative source of truth
â”œâ”€â”€ ONBOARDING.md                      # This document
â”œâ”€â”€ README.md                          # Repo entry point
â”œâ”€â”€ REVIEWER_GUIDE.md                  # 3-minute hands-on demo
â”œâ”€â”€ DELIVERABLES.md / DELIVERABLES_PROOF.md
â”œâ”€â”€ PRD.md / ARCHITECTURE.md
â”œâ”€â”€ render.yaml                        # Render Blueprint (production)
â”œâ”€â”€ .github/workflows/ci.yml           # CI pipeline
â””â”€â”€ app/                               # Runnable application
    â”œâ”€â”€ src/                           # Python backend
    â”‚   â”œâ”€â”€ api/                       # FastAPI routes
    â”‚   â”œâ”€â”€ verify/                    # P1 pipeline + batch service
    â”‚   â”œâ”€â”€ rules/                     # Deterministic TTB field rules
    â”‚   â”œâ”€â”€ adapters/ocr/              # Tesseract, Azure, sidecar
    â”‚   â”œâ”€â”€ factory/ + graph/ + agents/  # P2+ LangGraph (optional)
    â”‚   â””â”€â”€ rag/                       # Optional RAG corpus
    â”œâ”€â”€ ui/src/                        # React + TypeScript (USWDS-aligned CSS)
    â”œâ”€â”€ fixtures/                      # Synthetic labels + manifests
    â”œâ”€â”€ scripts/                       # Fixture generation, load tests
    â”œâ”€â”€ evals/                         # Golden + adversarial eval harness
    â””â”€â”€ tests/                         # Pytest unit tests
```

### Module boundaries (backend)

| Module | Responsibility |
|--------|----------------|
| [`src/verify/pipeline.py`](app/src/verify/pipeline.py) | **P1 default:** ingest â†’ OCR â†’ structure â†’ rules â†’ verdicts |
| [`src/rules/field_rules.py`](app/src/rules/field_rules.py) | Deterministic match / mismatch / needs_review per TTB field |
| [`src/verify/batch_service.py`](app/src/verify/batch_service.py) | Async batch orchestration, progress, partial failure isolation |
| [`src/factory/labelforge_factory.py`](app/src/factory/labelforge_factory.py) | DI wiring; LangGraph when `USE_FACTORY_GRAPH=true` |
| [`src/api/main.py`](app/src/api/main.py) | REST API + static UI mount |

**Design principle:** Orchestration is pluggable; **deterministic rules own compliance verdict bits**. Agents and RAG assist extraction and nuance â€” they do not auto-approve labels.

---

## 4. Fixture taxonomy (canonical counts)

Use these numbers consistently across docs and reviews:

| Layer | Count | ID pattern | Purpose |
|-------|-------|------------|---------|
| **Golden CI eval set** | **30** | catalog IDs | [`golden_labels.jsonl`](app/evals/datasets/golden_labels.jsonl) â€” CI regression gate |
| **Synthetic catalog** | **34** | e.g. `old_tom_match` | Stakeholder-mapped scenarios; [`batch_manifest.json`](app/fixtures/applications/batch_manifest.json) demo batch |
| **Scale test fixtures** | **300** | `scale_001` â€¦ `scale_300` | Peak-load batch testing; [`batch_manifest_200.json`](app/fixtures/applications/batch_manifest_200.json), [`batch_manifest_300.json`](app/fixtures/applications/batch_manifest_300.json) |
| **Curated gallery** | **10** | subset of catalog | One-click **Try this sample** cards in UI |
| **Stretch (non-golden)** | **4** | in catalog + gallery | OCR/visual stress; excluded from golden CI |
| **Pytest unit tests** | **28** | 6 modules | See Â§6 |

**Scale manifest expected outcomes** (from [`scale_manifest_summary.json`](app/fixtures/applications/scale_manifest_summary.json)): ~51% passed Â· ~42% failed Â· ~7% needs_review.

**Glossary:**

- **Golden** â€” committed eval set; CI fails on regression  
- **Catalog** â€” full synthetic scenario library (34)  
- **Scale** â€” programmatic 300-label layer for 200/300 batch load tests  
- **Gallery** â€” curated UX subset (10)  
- **Stretch** â€” imperfect-photo / visual-bold cases not in golden CI  

---

## 5. Developer runbook

### Prerequisites

- Python **3.11+**
- Node.js **18+** (Node **20** in Docker/CI)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on `PATH` for local production-like latency
- Git

### Full bootstrap

```bash
cd app
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

python scripts/generate_fixtures.py        # 34 catalog fixtures + batch_manifest.json
python scripts/generate_scale_fixtures.py  # 300 scale fixtures + batch_manifest_200/300
python scripts/generate_eval_datasets.py   # golden_labels.jsonl + expected verdicts

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd app/ui
npm install
npm run dev          # http://localhost:5173 â€” hot reload
# or
npm run build        # production bundle â†’ app/ui/dist/
```

For Vite dev on `:5173`, create `app/ui/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

[`vite.config.ts`](app/ui/vite.config.ts) proxies `/verify`, `/batch`, and `/health` only. Gallery and label picker need `VITE_API_URL` or use Docker / `:8000` (built UI + API on one port).

### Docker (API + built UI)

```bash
cd app
docker compose up --build
# â†’ http://localhost:8000
```

The Dockerfile runs `generate_fixtures.py` and `generate_scale_fixtures.py` at build time.

### Smoke tests

```bash
# Health
curl http://localhost:8000/health

# Single verify
curl -X POST http://localhost:8000/verify \
  -F "image=@fixtures/labels/old_tom_match.png" \
  -F "application=$(cat fixtures/applications/old_tom_match.json)"

# Batch load test (200 labels)
python scripts/run_batch_load_test.py --base-url http://localhost:8000 --size 200
```

---

## 6. Environment and configuration matrix

`GET /health` reflects runtime flags â€” use it as the source of truth on any environment.

| Variable | Local default (`.env.example`) | Production ([`render.yaml`](render.yaml)) | Notes |
|----------|-------------------------------|----------------------------------------|-------|
| `OCR_PROVIDER` | `tesseract` | `tesseract` | Offline/firewall-safe (Marcus Williams) |
| `USE_FACTORY_GRAPH` | `false` | `false` | P1 linear pipeline for client demo |
| `RAG_ENABLED` | `false` | `false` | Enable locally for interview depth |
| `STRICT_WARNING` | `true` | `true` | Jenny Park â€” warning exactness |
| `BATCH_CONCURRENCY` | `6` | `6` | Protect latency under 200â€“300 load |
| `BATCH_PERSIST` | `false` | `true` | File-backed batch store on Render |
| `LATENCY_GATE_ENABLED` | `false` | `true` | Adds `latency_warning` when slow |
| `PREPROCESS_IMPERFECT` | `false` | `false` | Stretch â€” deskew/sharpen for imperfect photos |

**P1 vs P2+ at a glance:**

| Mode | Flags | Path |
|------|-------|------|
| **P1 (production default)** | `USE_FACTORY_GRAPH=false`, `RAG_ENABLED=false` | [`pipeline.py`](app/src/verify/pipeline.py) |
| **P2+ (interview / local)** | `USE_FACTORY_GRAPH=true`, optional `RAG_ENABLED=true` | [`verification_graph.py`](app/src/graph/verification_graph.py) |

---

## 7. Quality gates

### Pytest (28 tests, 6 modules)

```bash
cd app && pytest tests/ -v
```

| Module | Tests | Focus |
|--------|-------|-------|
| `test_rules.py` | 7 | Warning exactness, brand nuance, ABV mismatch |
| `test_eval_metrics.py` | 5 | Field accuracy, RAG hit rate helpers |
| `test_batch_service.py` | 4 | Batch progress, partial failures, persistence |
| `test_samples_catalog.py` | 4 | Fixture discovery, path validation |
| `test_fixture_stem.py` | 4 | Batch label_id â†’ sidecar stem resolution |
| `test_scale_fixtures.py` | 4 | 300 scale catalog + manifest integrity |

### Eval suite (CI regression gate)

```bash
cd app && python evals/runners/run_eval_suite.py --output eval-report.json
```

- **30 golden** cases â€” field + summary accuracy  
- **Adversarial** warning recall  
- **RAG** query hit rate (when enabled)  
- Uses **sidecar OCR** in CI for deterministic rule testing â€” **not** production latency  

### Latency measurement (critical distinction)

| Measurement | OCR path | Proves |
|-------------|----------|--------|
| **Production `/verify`** | Tesseract | Sarahâ€™s **â‰¤ ~5 s** adoption threshold |
| **Golden eval P95** | Sidecar `.txt` fixtures | Rule correctness at CI speed |
| **`run_latency_benchmark.py`** | Tesseract | Production P95 gate (CI step, non-blocking) |

---

## 8. User interface

| Feature | Component | Notes |
|---------|-----------|-------|
| Single + batch tabs | [`App.tsx`](app/ui/src/App.tsx) | Two-tab UX (Sarah â€” â€œno hunting for buttonsâ€) |
| Sample gallery (10) | [`SampleGallery.tsx`](app/ui/src/SampleGallery.tsx) | One-click load image + application JSON |
| Full label library | [`LabelPickerCard.tsx`](app/ui/src/LabelPickerCard.tsx) | All fixture PNGs via `GET /labels` |
| Verdict table | [`VerdictTable.tsx`](app/ui/src/VerdictTable.tsx) | Application vs label vs verdict per field |
| Batch quick-starts | [`App.tsx`](app/ui/src/App.tsx) | Demo (34), 200-label, 300-label scale tests |
| Latency badge | [`LatencyBadge.tsx`](app/ui/src/LatencyBadge.tsx) | Per-label and batch P95 |

### USWDS 3.0 alignment

The UI uses **USWDS 3.0 design tokens** ([U.S. Web Design System](https://designsystem.digital.gov/)) implemented in custom CSS â€” not the full `@uswds/uswds` npm package:

- **Typography:** Public Sans (loaded via Google Fonts in [`index.html`](app/ui/index.html))
- **Colors:** Theme tokens â€” primary `#005ea2`, ink `#1b1b1b`, success/error/warning palettes
- **Components:** Button, alert, table, and spacing patterns aligned with USWDS guidance
- **Accessibility:** Skip link, focus rings, `aria-live` batch progress, semantic tables

Rebuild UI after CSS/TSX changes:

```bash
cd app/ui && npm run build
```

---

## 9. Scripts reference

| Script | Output |
|--------|--------|
| [`generate_fixtures.py`](app/scripts/generate_fixtures.py) | 34 catalog PNG + JSON + `batch_manifest.json` |
| [`generate_scale_fixtures.py`](app/scripts/generate_scale_fixtures.py) | 300 `scale_NNN` fixtures + `batch_manifest_200/300.json` + summary |
| [`generate_scale_manifest.py`](app/scripts/generate_scale_manifest.py) | Thin wrapper â†’ calls `generate_scale_fixtures.main()` |
| [`generate_eval_datasets.py`](app/scripts/generate_eval_datasets.py) | `golden_labels.jsonl`, expected verdicts, adversarial/RAG queries |
| [`run_batch_load_test.py`](app/scripts/run_batch_load_test.py) | CLI 200/300 batch load test against running API |
| [`index_rag_corpus.py`](app/scripts/index_rag_corpus.py) | Optional Chroma index (requires `pip install -e ".[rag]"`) |

---

## 10. CI pipeline

[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

1. Install Tesseract  
2. `pip install -e ".[dev]"`  
3. `generate_fixtures.py`  
4. `generate_scale_fixtures.py`  
5. `generate_eval_datasets.py`  
6. `pytest tests/ -v` â€” **28 tests**  
7. `run_latency_benchmark.py` â€” non-blocking  
8. `run_eval_suite.py` â€” **fails on regression**  
9. Separate job: `npm run build` in `app/ui/`  

---

## 11. Deployment

See [app/DEPLOY.md](app/DEPLOY.md) and [render.yaml](render.yaml).

| Environment | URL |
|-------------|-----|
| **Production** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| **Local Docker** | http://localhost:8000 |
| **Local Vite dev** | http://localhost:5173 (API at `:8000`) |

Production smoke:

```bash
curl https://labelforge-w32d.onrender.com/health
```

Expected: `batch_persist: true`, `latency_gate_enabled: true`, `ocr_provider: tesseract`.

---

## 12. Known limitations and trade-offs

Documented per [ClientRequirement.md](ClientRequirement.md) â€” working core over ambitious incomplete features:

- **No COLA integration** â€” standalone PoC only  
- **Synthetic fixtures only** â€” no real applicant PII  
- **Government warning bold** â€” pixel + OCR heuristics; uncertain cases â†’ `needs_review`  
- **Imperfect photos** â€” stretch goal; basic normalization default; `PREPROCESS_IMPERFECT=true` for deskew/sharpen  
- **Cloud OCR** â€” Azure optional; Tesseract fallback when firewall blocks egress  
- **Scale fixtures** â€” programmatic diversity for load testing; golden eval remains 30 catalog cases  

---

## 13. Documentation index

| Document | Purpose |
|----------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Normative client requirements |
| [ONBOARDING.md](ONBOARDING.md) | This guide |
| [README.md](README.md) | Repository entry point |
| [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) | 3-minute demo script |
| [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | Requirement â†’ file path proof index |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist |
| [PRD.md](PRD.md) | Product requirements + phased delivery |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Agent factory deep dive |
| [app/README.md](app/README.md) | Developer quick start + API |
| [app/DEPLOY.md](app/DEPLOY.md) | Docker, Render, Railway, env vars |

---

*Last verified against repo: 2026-07-08*
