# LabelForge — TTB Alcohol Label Verification

Gauntlet AI GFA Cohort 5 take-home: **AI-powered alcohol label verification** for the TTB Compliance Division.

**Repository:** [github.com/monigarr/instructions](https://github.com/monigarr/instructions)  
**Live demo:** [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)

---

## Who is reviewing?

### Client reviewers (ClientRequirement.md)

[ClientRequirement.md](ClientRequirement.md) defines exactly **two submissions**. Start here — no graph/RAG/eval depth required.

| Step | What to do | What it proves |
|------|------------|----------------|
| **1. Try the product** | [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) → upload `fixtures/labels/old_tom_match.png` + paste `fixtures/applications/old_tom_match.json` → **Verify Label** | Deployed URL works; P1 path is live |
| **2. Spot-check batch** | Batch tab → upload `batch_manifest.json` + all label PNGs | Peak-load batch flow (Sarah/Janet) |
| **3. Skim fixture catalog** | 30 synthetic labels in [`app/fixtures/`](app/fixtures/) — see [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) §2.2 | TTB fields, warning exactness, brand nuance, imports |
| **4. Read proof index** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | Every client requirement → file path + smoke test |

**Submission = live URL + P1 pipeline + fixture catalog.** Production runs `USE_FACTORY_GRAPH=false`, `RAG_ENABLED=false` (fast, auditable).

| # | Client deliverable | Proof |
|---|-------------|-------|
| 1 | Source code repository | [`app/`](app/) + [`app/README.md`](app/README.md) |
| 2 | Deployed application URL | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |

### Interview reviewers (engineering depth)

After the client path above, explore **optional P2+ layers** — same verdict outcomes, richer orchestration:

| Layer | Entry point | Env flags |
|-------|-------------|-----------|
| **Eval harness** (30 golden + adversarial + RAG queries) | [`app/evals/runners/run_eval_suite.py`](app/evals/runners/run_eval_suite.py) | CI blocks regression |
| **Agent factory + LangGraph** | [`app/src/factory/labelforge_factory.py`](app/src/factory/labelforge_factory.py), [`app/src/graph/verification_graph.py`](app/src/graph/verification_graph.py) | `USE_FACTORY_GRAPH=true` |
| **RAG grounding** | [`app/src/rag/corpus/`](app/src/rag/corpus/), [`app/src/agents/compliance_rag_agent.py`](app/src/agents/compliance_rag_agent.py) | `RAG_ENABLED=true` |
| **Architecture narrative** | [ARCHITECTURE.md](ARCHITECTURE.md) §1–6 | — |

Batch verify routes through the factory graph when `USE_FACTORY_GRAPH=true` (single + batch parity).

---

## AI-native engineering (why this is not “just an OCR wrapper”)

| Signal | Implementation | Reviewer entry point |
|--------|----------------|----------------------|
| **Deterministic compliance core** | Rules own verdict bits; agents assist extraction, not legal outcomes | [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py) |
| **Agent software factory** | LangGraph orchestration, specialized agents, factory DI | [`app/src/factory/`](app/src/factory/), [`app/src/graph/`](app/src/graph/) |
| **Eval discipline** | 30 golden + adversarial + RAG suites; CI fails on regression | [`app/evals/`](app/evals/) |
| **RAG grounding** | TTB field corpus (markdown); optional Chroma | [`app/src/rag/corpus/`](app/src/rag/corpus/) |
| **Ports & adapters** | Swappable OCR (Tesseract / Azure / sidecar fallback) | [`app/src/adapters/ocr/`](app/src/adapters/ocr/) |
| **Production path** | Docker, Render Blueprint, GitHub Actions CI | [`render.yaml`](render.yaml), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

---

## Current state (2026-06-09)

| Layer | Status |
|-------|--------|
| **Application** | FastAPI v0.1.0 + React, single + batch verify, 30 synthetic fixtures, 30 golden evals |
| **Production** | Live on Render — [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) (`USE_FACTORY_GRAPH=false`, `RAG_ENABLED=false`) |
| **CI** | 9 pytest tests + fixture/eval dataset generation + eval suite (per-field regression gate) + UI build |
| **Documentation** | Client requirements, proof index, PRD, architecture |

---

## Documentation map

| Document | Audience | Purpose |
|----------|----------|---------|
| [**DELIVERABLES_PROOF.md**](DELIVERABLES_PROOF.md) | **Client reviewers first** | Proof index — URLs, paths, smoke tests |
| [ClientRequirement.md](ClientRequirement.md) | Normative | Authoritative client requirements (do not edit for proof) |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission | Client checklist |
| [PRD.md](PRD.md) | Product | Requirements + phased delivery |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Interview | LabelForge agent factory (P2+ in code) |
| [app/README.md](app/README.md) | Developers | Run locally, approach, trade-offs |

---

## Quick start (local)

```bash
cd app
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
cp .env.example .env
python scripts/generate_fixtures.py
python scripts/generate_eval_datasets.py
uvicorn src.api.main:app --reload --port 8000
```

UI: `cd app/ui && npm install && npm run dev` → http://localhost:5173  
Docker: `cd app && docker compose up --build` → http://localhost:8000

---

## Author

Monica Peters (MoniGarr) — Gauntlet AI GFA Cohort 5 Fellowship, 2026
