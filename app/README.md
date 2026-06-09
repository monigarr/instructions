# LabelForge — TTB Alcohol Label Verification

Standalone proof-of-concept for TTB compliance agents: upload label artwork, compare extracted fields to application data, and review match/mismatch results — single label or batch.

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for UI)
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
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd app/ui
npm install
npm run dev
```

Open http://localhost:5173 — verify a sample label using `fixtures/labels/old_tom_match.png` and `fixtures/applications/old_tom_match.json`.

### Docker (API + built UI)

```bash
cd app
docker compose up --build
```

Open http://localhost:8000

## Demo URL

| Environment | URL | Status |
|-------------|-----|--------|
| **Production (Render)** | https://labelforge.onrender.com | **Suspended** — resume service on Render or redeploy via [DEPLOY.md](DEPLOY.md) + [render.yaml](../render.yaml) |
| **Local (Docker)** | http://localhost:8000 | `docker compose up --build` |
| **Local dev UI** | http://localhost:5173 | `npm run dev` in `ui/` with API on :8000 |

**Proof index:** [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md) — file paths, API smoke tests, fixture map.

Document cold-start delay (~10–30 s on free tiers) and env vars in platform settings when production is live.

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

- Typical Tesseract path on synthetic fixtures: **~1–3 s** locally (depends on image size and CPU)
- Batch processing uses a concurrency cap (`BATCH_CONCURRENCY`, default 6) to protect latency under load
- `elapsed_ms` is returned in every verification response for benchmarking

Document your test conditions when reporting P95 in production.

### Batch processing

- Supports **200–300** labels per session via async batch API with progress polling
- Partial failures do not fail the entire batch
- Test with `fixtures/applications/batch_manifest.json` + matching label images

### Assumptions & trade-offs

- **Standalone prototype** — no COLA integration
- **Synthetic labels only** — no real applicant PII
- **Government warning bold detection** — heuristic (OCR/layout); uncertain cases flagged `needs_review`
- **Brand nuance** — fuzzy normalization flags likely-equivalent casing (Dave Morrison); human confirms
- **Imperfect photos** — basic contrast normalization only; glare/angles not fully handled (stretch cut)
- **Cloud APIs** — optional Azure OCR; Tesseract fallback when outbound traffic blocked

### Factory / graph mode (P2+)

Set `USE_FACTORY_GRAPH=true` and optionally `RAG_ENABLED=true` in `.env` to use LangGraph orchestration with RAG enrichment. Client-visible outcomes remain the same; rules still own verdict bits.

Index RAG corpus (optional): `python scripts/index_rag_corpus.py` (requires `pip install -e ".[rag]"`).

### Architecture evolution (P1 → P4)

| Phase | Capability |
|-------|------------|
| P1 | Linear pipeline: ingest → OCR → structure → rules → UI |
| P2 | LabelForgeFactory, LangGraph agents, conditional OCR fallback, NuanceAgent |
| P2 | RAG corpus + ComplianceRAGAgent (Chroma optional) |
| P3 | `evals/` golden + adversarial suites, GitHub Actions CI |
| P4 | Image pre-processing, HITL batch resume stub, RAG-grounded ExplanationAgent |

## Environment variables

See `.env.example`. Never commit secrets.

## Running tests

```bash
cd app
pytest tests/ -v
python evals/runners/run_eval_suite.py
```

## Deployment

```bash
cd app
docker compose up --build
# Or deploy docker image to Railway / Render / Fly.io with port 8000
```

Set environment variables on the platform. Build UI first: `cd ui && npm run build`.

## Fixtures

| Label | Purpose |
|-------|---------|
| `old_tom_match` | Happy path — distilled spirits example |
| `old_tom_abv_mismatch` | ABV mismatch |
| `warning_title_case` | Rejects title-case warning header |
| `stones_throw_brand` | Brand casing nuance |
| `import_france` | Country of origin |
| `unreadable_blank` | Unreadable upload handling |

Regenerate: `python scripts/generate_fixtures.py`

## License

TBD
