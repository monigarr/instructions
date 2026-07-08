# LabelForge — TTB Alcohol Label Verification

Standalone proof-of-concept for TTB compliance agents: upload label artwork, compare extracted fields to application data, and review match/mismatch results — single label or batch.

**Live demo:** [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) · **Onboarding:** [ONBOARDING.md](../ONBOARDING.md) · **Proof index:** [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md) · **3-min demo:** [REVIEWER_GUIDE.md](../REVIEWER_GUIDE.md)

**Normative requirements:** [ClientRequirement.md](../ClientRequirement.md) — all approach and fixture decisions trace to this document.

---

## For code reviewers

**Client reviewers** ([ClientRequirement.md](../ClientRequirement.md)): live URL → P1 pipeline → [fixture catalog](#fixtures) below. That is the submission.

**Interview reviewers:** eval harness, graph flags, RAG — see [repo README](../README.md) § Interview reviewers.

| If you want to see… | Start here |
|---------------------|------------|
| End-to-end P1 pipeline (default deploy) | [`src/verify/pipeline.py`](src/verify/pipeline.py) |
| Deterministic compliance rules | [`src/rules/field_rules.py`](src/rules/field_rules.py) |
| Agent factory + LangGraph (optional) | [`src/factory/labelforge_factory.py`](src/factory/labelforge_factory.py), [`src/graph/verification_graph.py`](src/graph/verification_graph.py) |
| Eval gates — 30 golden + adversarial + RAG | [`evals/runners/run_eval_suite.py`](evals/runners/run_eval_suite.py) |
| RAG corpus + agent (optional) | [`src/rag/corpus/`](src/rag/corpus/), [`src/agents/compliance_rag_agent.py`](src/agents/compliance_rag_agent.py) |
| UI (single + batch, USWDS-aligned) | [`ui/src/App.tsx`](ui/src/App.tsx), [`ui/src/styles.css`](ui/src/styles.css) |
| API surface | [`src/api/main.py`](src/api/main.py) |

**Design principle:** rules own verdict bits; AI assists extraction and nuance (`needs_review`), not legal auto-approve. P2+ depth is toggled via `USE_FACTORY_GRAPH` / `RAG_ENABLED` — default deploy stays fast and auditable. Single **and batch** verify use the factory graph when `USE_FACTORY_GRAPH=true`.

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+ locally (Node 20 in Docker/CI)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and on `PATH` (default offline OCR)

### Backend

```bash
cd app
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/generate_fixtures.py
python scripts/generate_scale_fixtures.py
python scripts/generate_eval_datasets.py
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd app/ui
npm install
npm run dev
```

Open http://localhost:5173 — use the **sample gallery** (10 one-click cards) or the **label picker** to browse all fixture labels.

**Vite dev note:** [`vite.config.ts`](ui/vite.config.ts) proxies only `/verify`, `/batch`, and `/health`. For the sample gallery and label picker on `:5173`, create `app/ui/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

Alternatively, use Docker or `localhost:8000` (built UI + API on one port).

### Docker (API + built UI)

```bash
cd app
docker compose up --build
```

Open http://localhost:8000

## Demo URL

| Environment | URL | Status |
|-------------|-----|--------|
| **Production (Render)** | https://labelforge-w32d.onrender.com | Live — Starter plan (always-on, no free-tier cold start) |
| **Local (Docker)** | http://localhost:8000 | `docker compose up --build` |
| **Local dev UI** | http://localhost:5173 | `npm run dev` + `VITE_API_URL=http://localhost:8000` |

**Proof index:** [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md) — file paths, API smoke tests, fixture map.

Deploy via [DEPLOY.md](DEPLOY.md) and [render.yaml](../render.yaml). Tesseract OCR runs in-container; no API keys required for the default demo path.

## Approach

### Stack

| Layer | Choice | Why |
|-------|--------|-----|
| API | FastAPI (Python) | Async I/O, strong typing, fast iteration |
| UI | React + TypeScript | Clear side-by-side mismatch view for agents |
| OCR | Tesseract (default) + optional Azure Document Intelligence | Tesseract works offline (firewall-safe); Azure when credentials available |
| Rules | Deterministic `IFieldRule` classes | Reproducible verdicts; government warning exactness |
| P2+ | LangGraph, Chroma RAG, agent factory | Interview-grade orchestration without blocking MVP |

### How verification works

1. **Upload & validate** — image type, size, decodability
2. **Extract** — OCR via configured provider; fallback to Tesseract on failure/low confidence
3. **Structure** — map raw text to TTB fields (brand, class, ABV, net contents, warning, address, origin)
4. **Compare** — deterministic rules emit `match`, `mismatch`, `unable_to_verify`, or `needs_review` per field
5. **Human review** — tool assists; agents retain legal authority (no auto-approve)

### Performance

Target: **≤ ~5 seconds** user-perceived per label (Sarah Chen requirement).

| Measurement | OCR path | Typical value | Purpose |
|-------------|----------|---------------|---------|
| **Production / manual demo** | Tesseract | **~1–5 s** (depends on CPU; ~3.7 s on Render Starter) | Honest end-to-end latency |
| **Golden eval P95** | Sidecar text (`.txt` fixtures) | **~11.6 ms** (30 golden cases) | CI correctness regression — not production latency |
| **Batch** | Tesseract | Concurrency cap `BATCH_CONCURRENCY=6` | Protect latency under 200–300 load |
| **Production P95 gate** | Tesseract | `python evals/runners/run_latency_benchmark.py` | Separate from golden sidecar eval |

- `elapsed_ms` is returned in every verification response for benchmarking
- Set `LATENCY_GATE_ENABLED=true` to add `latency_warning` when elapsed exceeds `LATENCY_WARN_MS` (default 5000)
- Document your test conditions when reporting P95 in production

The eval suite uses [`SidecarByStemOCRProvider`](src/adapters/ocr/sidecar_provider.py) so CI validates verdict logic without Tesseract variance. Use production URL or local Tesseract for Sarah’s speed requirement.

### Batch processing

- Supports **200–300** labels per session via async batch API with progress polling
- Partial failures do not fail the entire batch
- **Quick-start in UI:** demo batch button (loads full `batch_manifest.json`; label shows count from API), 200/300 scale test buttons
- Scale manifests: `python scripts/generate_scale_fixtures.py` → 300 unique `scale_NNN` fixtures, `batch_manifest_200.json`, `batch_manifest_300.json`, and `scale_manifest_summary.json` (~51% pass / ~42% fail / ~7% needs_review per summary)
- Load test: `python scripts/run_batch_load_test.py --base-url http://localhost:8000 --size 200`
- `GET /batch/{id}?summary_only=true` for lightweight polling at scale
- Set `BATCH_PERSIST=true` to survive process restarts (file-backed store)
- When `USE_FACTORY_GRAPH=true`, batch items run through the same LangGraph path as single verify
- **CSV batch:** `POST /batch/verify-csv` (API); UI directs users to JSON manifest or quick-start buttons
- **Batch P95 latency** displayed in UI when batch completes

### UI features

Styling follows [USWDS 3.0](https://designsystem.digital.gov/) design tokens (Public Sans, federal color palette, button/alert/table patterns) in custom CSS — not the full `@uswds/uswds` npm package. Rebuild after UI changes: `cd ui && npm run build`.

| Feature | Component | API |
|---------|-----------|-----|
| Sample gallery (10 cards) | [`SampleGallery.tsx`](ui/src/SampleGallery.tsx) | `GET /samples`, `/samples/{id}/*` |
| Label picker (full library) | [`LabelPickerCard.tsx`](ui/src/LabelPickerCard.tsx) | `GET /labels`, `/labels/{id}/*` |
| Single verify + verdict table | [`App.tsx`](ui/src/App.tsx), [`VerdictTable.tsx`](ui/src/VerdictTable.tsx) | `POST /verify` |
| Batch verify + P95 | [`App.tsx`](ui/src/App.tsx) | `POST /batch/verify`, `GET /batch/{id}` |
| Latency badge | [`LatencyBadge.tsx`](ui/src/LatencyBadge.tsx) | `elapsed_ms` on verify response |

One-click **Try this sample** loads both label image and application JSON automatically.

### API reference

Defined in [`src/api/main.py`](src/api/main.py). Full table in [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md) §5.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + config |
| `GET` | `/samples` | Curated gallery (10) |
| `GET` | `/samples/{id}/image`, `/application` | Gallery assets |
| `GET` | `/samples/batch/demo`, `/samples/batch/scale/{200\|300}` | Batch quick-start metadata |
| `GET` | `/labels` | All fixture labels (catalog + extras) |
| `GET` | `/labels/{id}/image`, `/application` | Fixture assets |
| `POST` | `/verify` | Single-label verification |
| `POST` | `/batch/verify` | Batch (JSON manifest + images) |
| `POST` | `/batch/verify-csv` | Batch (CSV manifest + images) |
| `GET` | `/batch/{batch_id}` | Poll progress (`?summary_only=true`) |
| `POST` | `/batch/{batch_id}/resume` | HITL stub (API only; no UI button) |

### Assumptions & trade-offs

- **Standalone prototype** — no COLA integration ([ClientRequirement.md](../ClientRequirement.md), Marcus Williams)
- **Synthetic labels only** — no real applicant PII
- **Government warning bold detection** — pixel + OCR heuristics; uncertain cases flagged `needs_review` (never auto-fail)
- **Brand nuance** — fuzzy normalization flags likely-equivalent casing (Dave Morrison); human confirms
- **Imperfect photos** — basic contrast normalization by default; set `PREPROCESS_IMPERFECT=true` for sharpen/deskew stretch
- **Cloud APIs** — optional Azure OCR; Tesseract fallback when outbound traffic blocked (Marcus Williams firewall note)

### Factory / graph mode (P2+)

Set `USE_FACTORY_GRAPH=true` and optionally `RAG_ENABLED=true` in `.env` to use LangGraph orchestration with RAG enrichment. Client-visible outcomes remain the same; rules still own verdict bits.

Index RAG corpus (optional): `python scripts/index_rag_corpus.py` (requires `pip install -e ".[rag]"`).

### Design decisions

1. **Rules, not LLM, for verdicts** — Reproducible match/mismatch/needs_review; government warning exactness (Jenny Park) is auditable in code.
2. **LangGraph for orchestration** — Conditional OCR fallback, brand nuance branch, per-node timings; same outcomes as P1 pipeline.
3. **RAG is optional grounding** — TTB field corpus enriches agent context; never overrides `WarningExactRule` or other deterministic rules.

### Architecture evolution (P1 → P4)

| Phase | Capability |
|-------|------------|
| P1 | Linear pipeline: ingest → OCR → structure → rules → UI |
| P2 | LabelForgeFactory, LangGraph agents, conditional OCR fallback, NuanceAgent |
| P2 | RAG corpus + ComplianceRAGAgent (Chroma optional) |
| P3 | 30 golden evals + adversarial + RAG queries; per-field CI regression gate; **28** pytest tests |
| P4 | Image pre-processing, HITL batch resume stub, RAG-grounded ExplanationAgent |

## Environment variables

See `.env.example`. Never commit secrets.

For local Vite dev, also set `VITE_API_URL=http://localhost:8000` in `ui/.env.local` (not in `.env.example` — UI-only).

## Running tests

```bash
cd app
pytest tests/ -v          # 28 tests: test_rules (7), test_eval_metrics (5), test_batch_service (4),
                          # test_samples_catalog (4), test_fixture_stem (4), test_scale_fixtures (4)
python evals/runners/run_eval_suite.py
```

The eval suite reports aggregate and **per-field** golden accuracy (`field_accuracy_by_field`), summary accuracy, adversarial warning recall, false-pass rate, RAG hit rate (`rag_hit_rate_by_field`), and P95 latency. CI fails on golden/summary/adversarial regression ([`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

## Regenerate eval data

Synthetic fixtures and eval manifests are derived from use cases in [ClientRequirement.md](../ClientRequirement.md) (Sarah routine matching, Jenny warning exactness, Dave brand nuance, import labels, unreadable uploads).

```bash
cd app
python scripts/generate_fixtures.py        # 34 catalog PNG labels + application JSON + demo batch manifest
python scripts/generate_scale_fixtures.py  # 300 unique scale labels + batch_manifest_200/300.json
python scripts/generate_eval_datasets.py   # golden_labels.jsonl (30), expected/*.json, adversarial + RAG queries
python evals/runners/run_eval_suite.py   # field accuracy, summary, warning recall, RAG hit rate, P95 latency
```

## Deployment

```bash
cd app
docker compose up --build
# Or deploy docker image to Railway / Render / Fly.io with port 8000
```

Set environment variables on the platform. Build UI first: `cd ui && npm run build`. See [DEPLOY.md](DEPLOY.md).

## Fixtures

**34 synthetic catalog fixtures** mapped to [ClientRequirement.md](../ClientRequirement.md) stakeholder stories. **300** scale-test fixtures (`scale_001`–`scale_300`) support 200/300 batch load tests. **30** are in the golden CI eval set ([`evals/datasets/golden_labels.jsonl`](evals/datasets/golden_labels.jsonl)). **10** appear in the curated sample gallery.

| Category | Fixture IDs |
|----------|-------------|
| Happy path | `old_tom_match`, `vodka_match`, `gin_match`, `rum_match`, `tequila_match`, `scotch_import_match`, `japan_import_match`, `mexico_tequila_import`, `import_france`, `class_type_lowercase_match`, `abv_format_variant_match`, `domestic_no_address_match` |
| Sarah — routine mismatches | `old_tom_abv_mismatch`, `net_contents_mismatch`, `net_contents_floz_mismatch`, `class_type_mismatch`, `proof_mismatch`, `brand_hard_mismatch`, `address_mismatch` |
| Jenny — warning exactness | `warning_title_case`, `warning_wording_change`, `warning_truncated`, `warning_missing` |
| Dave — brand nuance | `stones_throw_brand`, `brand_casing_nuance`, `brand_apostrophe_nuance`, `brand_substring_nuance` |
| Imports — failures | `import_country_mismatch`, `scotch_country_mismatch` |
| Error handling | `unreadable_blank` |
| Stretch (non-golden CI) | `warning_not_bold`, `label_slight_rotation`, `label_low_contrast`, `label_glare_band` |

Regenerate fixtures and eval manifests: see **Regenerate eval data** above.

## License

Evaluation prototype for Gauntlet AI GFA Cohort 5 take-home — not licensed for production use.

*Last verified against repo: 2026-07-08*
