# LabelForge — TTB Alcohol Label Verification

Gauntlet AI GFA Cohort 5 take-home: **AI-powered alcohol label verification** for the TTB Compliance Division.

## Client deliverables

| Deliverable | Location |
|-------------|----------|
| **Source code + README** | [`app/`](app/) |
| **Deployed URL** | Documented in [`app/README.md`](app/README.md#demo-url) |

## Documentation (this repo)

| Document | Purpose |
|----------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Authoritative client requirements |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist |
| [PRD.md](PRD.md) | Product requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | LabelForge agent factory design (P2+) |

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
