> **Archived 2026-10-19.** Historical document retained for traceability. It predates the repository consolidation; canonical docs are [README](../README.md) | [APPROACH](../APPROACH.md) | [SECURITY_ACCESSIBILITY](../SECURITY_ACCESSIBILITY.md) | [PRD](../PRD.md) | [ClientRequirement](../ClientRequirement.md). Relative links inside this file may be stale.

# Reviewer Guide â€” LabelForge (3-minute demo)

**Author:** Monica Peters (MoniGarr) Â· Gauntlet AI GFA Cohort 5, 2026

| | |
|---|---|
| **Live demo** | [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) |
| **Repo** | [github.com/monigarr/instructions](https://github.com/monigarr/instructions) â€” application in [`app/`](app/) |
| **Proof index** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) |
| **Client requirements** | [ClientRequirement.md](ClientRequirement.md) â€” two deliverables only |

Production defaults: `USE_FACTORY_GRAPH=false`, `RAG_ENABLED=false`, `BATCH_PERSIST=true`, `LATENCY_GATE_ENABLED=true` (fast P1 pipeline).

**Fixture counts:** **10** one-click gallery samples Â· **34** synthetic catalog fixtures (`batch_manifest.json`) Â· **300** scale-test fixtures (`scale_001`â€“`scale_300`) Â· **30** golden CI eval cases.

---

## Submission cover (paste-ready)

> Per [ClientRequirement.md](ClientRequirement.md): (1) source repo [github.com/monigarr/instructions](https://github.com/monigarr/instructions) â€” run from [`app/README.md`](app/README.md); (2) live demo [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com). Start with this guide or [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) Â§0. Production uses Tesseract + deterministic rules (â‰¤ ~5 s). LangGraph, agents, RAG, and 30-golden eval CI live in `app/` for engineering depth â€” toggled via env flags in README.

---

## 3-minute hands-on script

### Step 1 â€” Happy path (~60 s) Â· Sarah Chen / core workflow

1. Open [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)
2. On **Verify One Label**, click **Try this sample** on the **Old Tom â€” Pass** card (loads label image + application JSON automatically)
3. Click **Verify Label**
4. **Expect:** summary **passed**, all fields **match**, elapsed **~3â€“5 s** (Sarahâ€™s adoption threshold)

### Step 2 â€” Warning exactness (~60 s) Â· Jenny Park

1. Click **Try this sample** on **Warning Title Case**
2. Click **Verify Label**
3. **Expect:** summary **failed** â€” government warning **mismatch** (title case rejected)

### Step 3 â€” Brand nuance (~60 s) Â· Dave Morrison

1. Click **Try this sample** on **Brand Nuance**
2. Click **Verify Label**
3. **Expect:** summary **needs review** â€” brand casing difference flagged for human judgment

### Step 4 â€” Batch (~60 s) Â· Sarah Chen / Janet Seattle

1. Switch to **Batch Verify**
2. Click **Run demo batch** or **Run 200-label scale test** / **Run 300-label scale test** (quick-start) â€” **or** upload `app/fixtures/applications/batch_manifest.json` + matching PNGs manually
3. Click **Start Batch Verification**
4. **Expect:** progress counts, passed / failed / needs review summary, batch P95 latency when complete

**Optional:** use the **label picker** dropdown to load any fixture PNG + application JSON not shown in the 10-card gallery.

---

## Stakeholder traceability

| Stakeholder | Requirement | Proof in ~30 s |
|-------------|-------------|----------------|
| **Sarah Chen** | â‰¤ ~5 s per label; batch 200â€“300 | `elapsed_ms` on verify response; Batch tab + scale quick-starts (200/300) |
| **Jenny Park** | Government warning exactness | Step 2 above; fixtures `warning_wording_change`, `warning_missing` |
| **Dave Morrison** | Brand nuance, donâ€™t make workflow harder | Step 3 above; `needs_review` not auto-pass |
| **Marcus Williams** | Standalone, offline-capable, no COLA | Tesseract default; synthetic fixtures; footer + README; no COLA imports |

---

## Interview reviewers (optional, +10 min)

```bash
cd app
pip install -e ".[dev]"
python scripts/generate_fixtures.py
python scripts/generate_scale_fixtures.py
python scripts/generate_eval_datasets.py
python evals/runners/run_eval_suite.py
```

Enable factory depth locally: `USE_FACTORY_GRAPH=true`, `RAG_ENABLED=true` in `.env`.

| Depth | Entry |
|-------|-------|
| Eval harness | [`app/evals/runners/run_eval_suite.py`](app/evals/runners/run_eval_suite.py) |
| LangGraph | [`app/src/graph/verification_graph.py`](app/src/graph/verification_graph.py) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) Â§1â€“6 |
| OpenAPI | [labelforge-w32d.onrender.com/docs](https://labelforge-w32d.onrender.com/docs) |

---

## How we measure speed (important)

| Measurement | OCR path | What it proves |
|-------------|----------|----------------|
| **Production `/verify`** | Tesseract | Sarahâ€™s **â‰¤ ~5 s** adoption threshold (~3.7 s observed on Render) |
| **Golden eval P95** | Sidecar text (`.txt` fixtures) | Rule/structure **correctness regression** at CI speed â€” not production latency |
| **Local Tesseract benchmark** | Tesseract on sample PNGs | End-to-end latency without sidecar â€” see [`app/README.md`](app/README.md) Â§ Performance |

---

*Last verified against repo: 2026-07-08*
