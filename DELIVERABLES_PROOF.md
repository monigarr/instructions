# Deliverables Proof — LabelForge

**For code reviewers:** start with §0, then follow the path that matches your role.

| Link | Purpose |
|------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Authoritative client requirements |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Agent factory design (implemented in `app/`) |

**Last verified:** 2026-06-10 — 30 golden evals, CI green on push, **9** pytest tests, production `/verify` passes `old_tom_match`

---

## 0. Sixty-second reviewer summary

**Monica Peters (MoniGarr)** — AI-native full-stack prototype for TTB label verification: **shipped product first**, **deterministic rules for compliance verdicts**, **agent factory + eval harness** for interview-grade depth.

| | |
|---|---|
| **Live demo** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| **Repo** | [github.com/monigarr/instructions](https://github.com/monigarr/instructions) |
| **Client submission** | Live URL + P1 pipeline + 30-fixture catalog |
| **Interview depth** | 30 golden evals, graph flags, RAG corpus — optional at runtime |

### Client reviewers (ClientRequirement.md)

1. Open the **live URL** → upload `app/fixtures/labels/old_tom_match.png` + paste `app/fixtures/applications/old_tom_match.json`
2. Try **Batch Verify** with `batch_manifest.json` + label PNGs
3. Skim §2 below for requirement traceability

Production defaults: `use_factory_graph: false`, `rag_enabled: false`.

### Interview reviewers

1. Run eval suite: `cd app && python evals/runners/run_eval_suite.py`
2. Enable `USE_FACTORY_GRAPH=true` / `RAG_ENABLED=true` locally
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) and [`app/src/graph/verification_graph.py`](app/src/graph/verification_graph.py)

**Production smoke (2026-06-10):**

| Check | Result |
|-------|--------|
| `GET /health` | `200` — `ocr_provider: tesseract` |
| `POST /verify` | `200` — **`summary: passed`**, 7/7 fields `match`, **`elapsed_ms: 3683`** (~3.7 s) on Render Starter (`old_tom_match` + Tesseract OCR) |
| `POST /batch/verify` | `200` — async batch completed |
| `GET /` (UI) | `200` — LabelForge React app |
| **GitHub Actions CI** | `success` — [run 27246213961](https://github.com/monigarr/instructions/actions/runs/27246213961) on `a7eeafe` |

Production `/verify` smoke (repeatable from `app/`):

```bash
python -c "from pathlib import Path; import httpx; r=httpx.post('https://labelforge-w32d.onrender.com/verify', files={'image': ('old_tom_match.png', Path('fixtures/labels/old_tom_match.png').read_bytes(), 'image/png')}, data={'application': Path('fixtures/applications/old_tom_match.json').read_text(encoding='utf-8')}, timeout=120); d=r.json(); print(r.status_code, d['summary'], len(d['verdicts']), round(d['elapsed_ms'],1))"
```

Observed on 2026-06-10: `200 passed 7 3683.2` — client demo fixture passes end-to-end on production after word-wrapped warning text in fixture PNGs (`a7eeafe`).

---

## 1. Client deliverables (authoritative)

[ClientRequirement.md](ClientRequirement.md) lists exactly **two** submissions:

| # | Client deliverable | URL / location | Status |
|---|-------------------|----------------|--------|
| 1 | **Source code repository** | [github.com/monigarr/instructions](https://github.com/monigarr/instructions) → [`app/`](app/) | **Complete** |
| 2 | **Deployed application URL** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) | **Live** (Render Starter, Blueprint-managed) |

> **Note:** An older Render hostname (`labelforge.onrender.com`) was owner-suspended. The current production service is **`labelforge-w32d`**, deployed via [`render.yaml`](render.yaml).

### 1.1 Deliverable 1 — Source code repository

| Client asks for | Where it lives | How to verify |
|-----------------|----------------|---------------|
| All source code | [`app/`](app/) — FastAPI v0.1.0, React UI, rules, OCR, batch, fixtures, evals, agents, graph | `cd app && pip install -e ".[dev]" && pytest tests/ -v` (**9** tests) |
| README with setup and run instructions | [`app/README.md`](app/README.md) | Quick start + Docker path |
| Brief approach documentation | [`app/README.md`](app/README.md) § Approach | Stack, verification flow, assumptions, trade-offs |
| Repo overview | [`README.md`](README.md) | Client vs interview reviewer paths |
| Synthetic test labels | [`app/fixtures/`](app/fixtures/) — **30** golden cases | `python scripts/generate_fixtures.py` |

**Interview-only depth (not client submission items):**

| Capability | Path | One-line description |
|------------|------|----------------------|
| P1 verification pipeline | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) | Ingest → OCR → structure → rules → result |
| Deterministic TTB rules | [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) | Reproducible match/mismatch/needs_review per field |
| Agent factory + DI | [`app/src/factory/labelforge_factory.py`](app/src/factory/labelforge_factory.py) | Wires pipeline or LangGraph runner from config |
| LangGraph orchestration | [`app/src/graph/verification_graph.py`](app/src/graph/verification_graph.py) | Conditional OCR fallback, agent nodes |
| Specialized agents | [`app/src/agents/`](app/src/agents/) | Ingestion, vision, structuring, nuance, RAG, explanation |
| Eval harness | [`app/evals/`](app/evals/) | **30 golden** + adversarial + RAG query metrics |
| RAG corpus | [`app/src/rag/corpus/`](app/src/rag/corpus/) | TTB field guidance as markdown for grounding |
| OCR adapters | [`app/src/adapters/ocr/`](app/src/adapters/ocr/) | Tesseract (default), Azure, sidecar fallback |
| React UI | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) | Single + batch tabs, side-by-side verdict table |
| CI | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | pytest + eval datasets + **fail on regression** |

### 1.2 Deliverable 2 — Deployed application URL

| Environment | URL | Proof | Status |
|-------------|-----|-------|--------|
| **Production** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) | `GET /health`, UI at `/` | **Live** |
| **Local Docker** | [http://localhost:8000](http://localhost:8000) | Same API + built UI | After `cd app && docker compose up --build` |
| **Local dev UI** | [http://localhost:5173](http://localhost:5173) | Vite proxy to API :8000 | `cd app/ui && npm run dev` |

**Smoke test (production):**

```bash
curl https://labelforge-w32d.onrender.com/health

curl -X POST https://labelforge-w32d.onrender.com/verify \
  -F "image=@app/fixtures/labels/old_tom_match.png" \
  -F "application=$(cat app/fixtures/applications/old_tom_match.json)"
```

**Expected `/health`:**

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

Derived from [ClientRequirement.md](ClientRequirement.md).

### 2.1 Core workflow

| Requirement | Proof (files) | Live / local proof |
|-------------|---------------|-------------------|
| Upload label + application data | [`app/ui/src/App.tsx`](app/ui/src/App.tsx); `POST /verify`, `POST /batch/verify` | [Live demo](https://labelforge-w32d.onrender.com) — `old_tom_match` |
| Extract text/fields | [`app/src/adapters/ocr/`](app/src/adapters/ocr/), [`app/src/structure/field_mapper.py`](app/src/structure/field_mapper.py) | Response `verdicts[].label_value` per field |
| Compare field by field | [`app/src/rules/engine.py`](app/src/rules/engine.py), [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) | UI columns: Application vs Label |
| Match / mismatch / unable to verify | [`app/src/domain/models.py`](app/src/domain/models.py) | Fixtures `warning_title_case`, `unreadable_blank` |
| Human retains final judgment | `needs_review` verdicts; no auto-approve | `BrandFuzzyRule` → `needs_review`; UI footer |

### 2.2 TTB label fields

| Field | Example | Rule |
|-------|---------|------|
| Brand name | `OLD TOM DISTILLERY` | `BrandFuzzyRule` |
| Class / type | `Kentucky Straight Bourbon Whiskey` | `ClassTypeRule` |
| Alcohol content | `45% Alc./Vol. (90 Proof)` | `ABVPatternRule` |
| Net contents | `750 mL` | `NetContentsRule` |
| Government warning | Canonical TTB text | `WarningExactRule` + [`constants.py`](app/src/domain/constants.py) |
| Bottler/producer address | Louisville, KY | `AddressContainsRule` |
| Country of origin | France, Scotland, Japan, Mexico (imports) | `CountryExactRule` |

**Fixture catalog (30 golden evals):**

| Category | Fixture IDs |
|----------|-------------|
| Happy path | `old_tom_match`, `vodka_match`, `gin_match`, `rum_match`, `tequila_match`, `scotch_import_match`, `japan_import_match`, `mexico_tequila_import`, `import_france`, `class_type_lowercase_match`, `abv_format_variant_match`, `domestic_no_address_match` |
| Sarah — mismatches | `old_tom_abv_mismatch`, `net_contents_mismatch`, `net_contents_floz_mismatch`, `class_type_mismatch`, `proof_mismatch`, `brand_hard_mismatch`, `address_mismatch` |
| Jenny — warnings | `warning_title_case`, `warning_wording_change`, `warning_truncated`, `warning_missing` |
| Dave — brand nuance | `stones_throw_brand`, `brand_casing_nuance`, `brand_apostrophe_nuance`, `brand_substring_nuance` |
| Imports — failures | `import_country_mismatch`, `scotch_country_mismatch` |
| Error handling | `unreadable_blank` |

Canonical manifest: [`app/evals/datasets/golden_labels.jsonl`](app/evals/datasets/golden_labels.jsonl)

Regenerate:

```bash
cd app
python scripts/generate_fixtures.py
python scripts/generate_eval_datasets.py
```

### 2.3 Performance (~5 seconds per label)

| Evidence | Value | Source |
|----------|-------|--------|
| Client target | ≤ ~5 s user-perceived | Sarah Chen requirement |
| Production sample | **~3.7 s** on Render Starter (`old_tom_match`, Tesseract, `summary: passed`) | `elapsed_ms: 3683` on 2026-06-10 live `/verify` smoke |
| Local golden eval P95 | **~11.6 ms** (30 fixtures, sidecar OCR path) | `python evals/runners/run_eval_suite.py` |
| Instrumentation | `elapsed_ms` on every response | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) |

### 2.4 Batch processing (200–300 scale)

| Evidence | Location |
|----------|----------|
| Async batch API | `POST /batch/verify`, `GET /batch/{batch_id}` |
| CSV batch | `POST /batch/verify-csv` |
| Concurrency cap | `BATCH_CONCURRENCY=6` |
| Progress UI | Batch tab in [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Sample manifest | [`app/fixtures/applications/batch_manifest.json`](app/fixtures/applications/batch_manifest.json) — 30 entries |
| Factory graph parity | [`app/src/verify/batch_service.py`](app/src/verify/batch_service.py) uses LangGraph when `USE_FACTORY_GRAPH=true` |

### 2.5 UX & error handling

| Requirement | Proof |
|-------------|-------|
| Obvious UI — two tabs | Single Label / Batch Verify |
| Side-by-side mismatch view | Verdict table: Application, Label, Verdict |
| Actionable errors | [`app/src/ingest/validator.py`](app/src/ingest/validator.py); `unreadable_blank` fixture |
| Warning title-case rejection | `test_warning_title_case_rejected` in [`app/tests/test_rules.py`](app/tests/test_rules.py) |

---

## 3. Constraints proof

| Constraint | Proof |
|------------|-------|
| Standalone — no COLA | No COLA imports; documented in README |
| No sensitive data | Synthetic fixtures only |
| Prototype security | `.env.example` only; no secrets in git |
| Firewall / egress | Tesseract default; Azure optional with fallback |
| Working core over ambition | P1 ships by default; P2+ behind env flags |

---

## 4. Automated proof (local + CI)

```bash
cd app
pip install -e ".[dev]"
python scripts/generate_fixtures.py
python scripts/generate_eval_datasets.py
pytest tests/ -v          # 9 tests: 4 rules + 5 eval metric helpers
python evals/runners/run_eval_suite.py
```

**CI pipeline** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

1. `generate_fixtures.py`
2. `generate_eval_datasets.py`
3. `pytest tests/ -v` — **9** tests ([`test_rules.py`](app/tests/test_rules.py), [`test_eval_metrics.py`](app/tests/test_eval_metrics.py))
4. `run_eval_suite.py` — **fails build on regression** (per-field golden accuracy, summary accuracy, warning recall, false-pass rate)
5. UI build job — `npm run build` in `app/ui/`

**Eval suite (2026-06-09, 30 golden):**

```json
{
  "golden": {
    "golden_count": 30,
    "field_accuracy_avg": 1.0,
    "field_accuracy_by_field": {
      "brand_name": 1.0,
      "class_type": 1.0,
      "alcohol_content": 1.0,
      "net_contents": 1.0,
      "government_warning": 1.0,
      "bottler_producer_address": 1.0,
      "country_of_origin": 1.0
    },
    "summary_accuracy": 1.0,
    "latency_p95_ms": 11.6,
    "latency_samples": 30
  },
  "adversarial": {
    "warning_recall": 1.0,
    "false_pass_rate": 0.0,
    "false_pass_caught": 1,
    "false_pass_total": 1
  },
  "rag": {
    "rag_hit_rate_avg": 1.0,
    "rag_hit_rate_by_field": {
      "government_warning": 1.0,
      "brand_name": 1.0,
      "alcohol_content": 1.0,
      "class_type": 1.0
    },
    "rag_query_count": 5
  }
}
```

---

## 5. API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + config |
| `POST` | `/verify` | Single-label verification |
| `POST` | `/batch/verify` | Batch (JSON manifest + images) |
| `POST` | `/batch/verify-csv` | Batch (CSV manifest) |
| `GET` | `/batch/{batch_id}` | Poll batch progress |

Defined in [`app/src/api/main.py`](app/src/api/main.py).

---

## 6. Submission readiness

| Item | Ready? |
|------|--------|
| GitHub repo with full source | **Yes** |
| README + approach docs | **Yes** |
| 30 fixtures + tests + evals | **Yes** |
| CI regression gate | **Yes** |
| Render Blueprint + Docker | **Yes** |
| Live HTTPS URL responding | **Yes** — [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| Single + batch on production | **Yes** |

---

## 7. Document map

| Document | Role |
|----------|------|
| [ClientRequirement.md](ClientRequirement.md) | Source of truth — two deliverables |
| **This file** | Proof index for reviewers |
| [README.md](README.md) | Reviewer entry — client vs interview paths |
| [DELIVERABLES.md](DELIVERABLES.md) | Checklist |
| [PRD.md](PRD.md) | Product requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Agent factory design |
| [app/README.md](app/README.md) | Runnable app docs |

---

*Monica Peters (MoniGarr) — Gauntlet AI GFA Cohort 5 Fellowship, 2026*
