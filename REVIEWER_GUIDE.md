# Reviewer Guide — LabelForge (3-minute demo)

**Author:** Monica Peters (MoniGarr) · Gauntlet AI GFA Cohort 5, 2026

| | |
|---|---|
| **Live demo** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| **Repo** | [github.com/monigarr/instructions](https://github.com/monigarr/instructions) — application in [`app/`](app/) |
| **Proof index** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) |
| **Client requirements** | [ClientRequirement.md](ClientRequirement.md) — two deliverables only |

Production defaults: `USE_FACTORY_GRAPH=false`, `RAG_ENABLED=false` (fast P1 pipeline).

---

## Submission cover (paste-ready)

> Per [ClientRequirement.md](ClientRequirement.md): (1) source repo [github.com/monigarr/instructions](https://github.com/monigarr/instructions) — run from [`app/README.md`](app/README.md); (2) live demo [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com). Start with this guide or [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) §0. Production uses Tesseract + deterministic rules (≤ ~5 s). LangGraph, agents, RAG, and 30-golden eval CI live in `app/` for engineering depth — toggled via env flags in README.

---

## 3-minute hands-on script

### Step 1 — Happy path (~60 s) · Sarah Chen / core workflow

1. Open [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)
2. On **Verify One Label**, click **Load sample: Old Tom (pass)** (prefills application JSON)
3. Upload `app/fixtures/labels/old_tom_match.png` from the repo
4. Click **Verify Label**
5. **Expect:** summary **passed**, all fields **match**, elapsed **~3–5 s** (Sarah’s adoption threshold)

### Step 2 — Warning exactness (~60 s) · Jenny Park

1. Click **Load sample: Warning fail**
2. Upload `app/fixtures/labels/warning_title_case.png`
3. Click **Verify Label**
4. **Expect:** summary **failed** — government warning **mismatch** (title case rejected)

### Step 3 — Brand nuance (~60 s) · Dave Morrison

1. Click **Load sample: Brand nuance**
2. Upload `app/fixtures/labels/stones_throw_brand.png`
3. Click **Verify Label**
4. **Expect:** summary **needs review** — brand casing difference flagged for human judgment

### Step 4 — Batch (~60 s) · Sarah Chen / Janet Seattle

1. Switch to **Batch Verify**
2. Upload all PNGs from `app/fixtures/labels/` (or a subset of 5+)
3. Upload `app/fixtures/applications/batch_manifest.json`
4. Click **Start Batch Verification**
5. **Expect:** progress counts, passed / failed / needs review summary

---

## Stakeholder traceability

| Stakeholder | Requirement | Proof in ~30 s |
|-------------|-------------|----------------|
| **Sarah Chen** | ≤ ~5 s per label; batch 200–300 | `elapsed_ms` on verify response; Batch tab + `batch_manifest.json` |
| **Jenny Park** | Government warning exactness | Step 2 above; fixtures `warning_wording_change`, `warning_missing` |
| **Dave Morrison** | Brand nuance, don’t make workflow harder | Step 3 above; `needs_review` not auto-pass |
| **Marcus Williams** | Standalone, offline-capable, no COLA | Tesseract default; footer + README; no COLA imports |

---

## Interview reviewers (optional, +10 min)

```bash
cd app
pip install -e ".[dev]"
python evals/runners/run_eval_suite.py
```

Enable factory depth locally: `USE_FACTORY_GRAPH=true`, `RAG_ENABLED=true` in `.env`.

| Depth | Entry |
|-------|-------|
| Eval harness | [`app/evals/runners/run_eval_suite.py`](app/evals/runners/run_eval_suite.py) |
| LangGraph | [`app/src/graph/verification_graph.py`](app/src/graph/verification_graph.py) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) §1–6 |
| OpenAPI | [labelforge-w32d.onrender.com/docs](https://labelforge-w32d.onrender.com/docs) |

---

## How we measure speed (important)

| Measurement | OCR path | What it proves |
|---------------|----------|----------------|
| **Production `/verify`** | Tesseract | Sarah’s **≤ ~5 s** adoption threshold (~3.7 s observed on Render) |
| **Golden eval P95** | Sidecar text (`.txt` fixtures) | Rule/structure **correctness regression** at CI speed — not production latency |
| **Local Tesseract benchmark** | Tesseract on sample PNGs | End-to-end latency without sidecar — see [`app/README.md`](app/README.md) § Performance |

---

*Last updated: 2026-06-09*
