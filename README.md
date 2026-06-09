# LabelForge — TTB Alcohol Label Verification

Gauntlet AI GFA Cohort 5 take-home: **AI-powered alcohol label verification** for the TTB Compliance Division.

**Repository:** [github.com/monigarr/instructions](https://github.com/monigarr/instructions)

## Current state (2026-06-09)

| Layer | Status |
|-------|--------|
| **Application code** | Complete in [`app/`](app/) — FastAPI + React UI, single + batch verify, TTB rules, fixtures, tests, evals, Docker, CI |
| **Planning docs** | Client requirements, PRD, architecture, deliverables checklist |
| **Production URL** | [labelforge.onrender.com](https://labelforge.onrender.com) — **suspended**; resume on Render or redeploy via [`render.yaml`](render.yaml) |

## Client deliverables

Per [ClientRequirement.md](ClientRequirement.md) — proof with file paths and URLs in [**DELIVERABLES_PROOF.md**](DELIVERABLES_PROOF.md).

| Deliverable | Proof |
|-------------|-------|
| **1. Source code repository** | [`app/`](app/) + [`app/README.md`](app/README.md) |
| **2. Deployed application URL** | [https://labelforge.onrender.com](https://labelforge.onrender.com) (reactivate before submission) |

## Documentation (this repo)

| Document | Purpose |
|----------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Authoritative client requirements |
| [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | **Proof index** — file locations + live URLs |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist |
| [PRD.md](PRD.md) | Product requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | LabelForge agent factory design (P2+ implemented in `app/`) |

## Quick start

```bash
cd app
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
cp .env.example .env
python scripts/generate_fixtures.py
uvicorn src.api.main:app --reload --port 8000
```

UI: `cd app/ui && npm install && npm run dev` → http://localhost:5173

## Author

Monica Peters (MoniGarr) — Gauntlet AI GFA Cohort 5 Fellowship, 2026
