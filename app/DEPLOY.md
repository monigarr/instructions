# Deployment Guide

**Live Streamlit URL:** [https://labelforge-monigarr.streamlit.app/](https://labelforge-monigarr.streamlit.app/)  
**Render URL:** [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) (configured; currently suspended)  
**Approach:** [APPROACH.md](../APPROACH.md) · **Security & accessibility:** [SECURITY_ACCESSIBILITY.md](../SECURITY_ACCESSIBILITY.md) · **Blueprint:** [`render.yaml`](../render.yaml) · **Historical docs:** [docs/archive/](../docs/archive/)  
**Client constraints:** [ClientRequirement.md](../ClientRequirement.md) — standalone PoC, firewall-aware OCR (Marcus Williams)

The public Streamlit app is live and is the deployed URL for the submission. The full FastAPI + React stack is configured for Render Starter, but that service is currently suspended and must be resumed in the Render dashboard. Tesseract OCR runs in-container/on Community Cloud; no API keys are required for the default demo path.

## Docker (recommended)

```bash
cd app
docker compose up --build
```

Open http://localhost:8000 — API + built UI on one port. Tesseract is included in the container. The Docker build runs `generate_fixtures.py` and `generate_scale_fixtures.py` so scale batch manifests are available in the image.

## Railway

1. Create project from this repo; set root directory to `app`
2. Use `Dockerfile` builder (see `railway.toml`)
3. Set environment variables from `.env.example`
4. Copy the generated HTTPS URL into the root `README.md` and `app/README.md`

## Render

LabelForge ships with a [Render Blueprint](../render.yaml) at the repo root for one-click deploy.

### Option A — Blueprint (recommended)

1. Log in at [render.com](https://render.com)
2. **New → Blueprint**
3. Connect GitHub → select `monigarr/instructions`
4. Review the generated service (`labelforge`, Starter plan, Docker, root dir `app`)
5. Click **Apply** / **Create**

The Blueprint sets:

| Setting | Value |
|---------|--------|
| Runtime | Docker |
| Root directory | `app` |
| Instance type | Starter (~$7/mo, always-on) |
| Health check | `/health` |
| `OCR_PROVIDER` | `tesseract` |
| `USE_FACTORY_GRAPH` | `false` |
| `RAG_ENABLED` | `false` |
| `BATCH_PERSIST` | `true` |
| `LATENCY_GATE_ENABLED` | `true` |

> **Hostname note:** Blueprint service name is `labelforge`. Render assigns the live hostname suffix (e.g. `labelforge-w32d.onrender.com`).

Render injects `PORT` automatically (default `10000`). The Dockerfile reads `${PORT:-8000}` so local Docker Compose still works on port 8000.

First build takes ~5-10 minutes (Node 24 UI build + Tesseract install + pip).

### Option B — Manual dashboard

1. **New → Web Service**
2. Connect GitHub repo `monigarr/instructions`
3. Configure:

| Setting | Value |
|---------|--------|
| Runtime | Docker |
| Root Directory | `app` |
| Dockerfile | `Dockerfile` |
| Instance type | Starter |
| Health Check Path | `/health` |
| Auto-Deploy | On |

4. Add environment variables from the table below (or use Blueprint defaults)
5. Deploy and copy the generated `*.onrender.com` URL into the root `README.md` and `app/README.md`

## Environment variables (platform)

| Variable | Production value | Notes |
|----------|------------------|-------|
| `OCR_PROVIDER` | `tesseract` | Default in Docker; offline/firewall-safe per [ClientRequirement.md](../ClientRequirement.md) |
| `USE_FACTORY_GRAPH` | `false` | P1 linear pipeline for client demo |
| `RAG_ENABLED` | `false` | RAG optional; enable locally for interview depth |
| `STRICT_WARNING` | `true` | Government warning exactness (Jenny Park) |
| `BATCH_CONCURRENCY` | `6` | Protect latency under 200–300 batch load |
| `BATCH_PERSIST` | `true` | File-backed batch store survives restarts |
| `LATENCY_GATE_ENABLED` | `true` | Adds `latency_warning` when elapsed exceeds threshold |
| `PORT` | **Do not set** | Render injects automatically |

Optional Azure OCR keys from `.env.example` only if you want cloud OCR instead of Tesseract. Never commit secrets.

## Local Vite dev (UI only)

When running `npm run dev` on `:5173`, set in `app/ui/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

[`vite.config.ts`](ui/vite.config.ts) proxies `/verify`, `/batch`, and `/health` only — not `/samples` or `/labels`. See [app/README.md](README.md) § Quick start.

**Node versions:** Node.js 22+ for local dev; Docker and CI use Node 24.

## Streamlit Community Cloud

**Status:** live at [https://labelforge-monigarr.streamlit.app/](https://labelforge-monigarr.streamlit.app/). Pushes to `main` redeploy automatically. The steps below reproduce the deployment.

1. Push the repository to GitHub (branch `main`).
2. At [share.streamlit.io](https://share.streamlit.io): **Create app** → **Deploy from GitHub**.
3. Repository `monigarr/instructions`, branch `main`, main file path `streamlit_app.py` (repo root). The shim executes `app/streamlit_app.py`; a subdirectory entrypoint also works where the form permits it.
4. Advanced settings → Python **3.11 or 3.12** (both tested); leave secrets empty. If the app reports an untested runtime (for example 3.14) and import errors appear after a hot reload, reboot or redeploy on a tested version.
5. Deploy. Community Cloud installs root [`requirements.txt`](../requirements.txt), apt packages from root [`packages.txt`](../packages.txt) (`tesseract-ocr`), and reads root [`.streamlit/config.toml`](../.streamlit/config.toml).
6. Smoke-test the gallery and the **25-label** free-tier batch, then record the assigned URL. The current live app is `https://labelforge-monigarr.streamlit.app/`.

The free tier throttles sustained CPU, so the live demo hard-caps each batch at **25 labels**. The 25/200/300 controls remain visible, but 200/300 are disabled on Community Cloud; uploaded manifests larger than 25 are rejected rather than truncated. Local and Docker Streamlit runs keep 200/300 enabled. Detection is automatic (`/mount/src`); `LABELFORGE_FREE_TIER=1` forces the cap, `=0` disables it for tests or a non-Cloud host.

The free tier has **1 GB of memory**. Streamlit batches run two OCR jobs at a time (chunks of 25) and release Python/glibc memory after every chunk, so run **one batch at a time** per app instance. Off the free tier, overlapping 200-300 label runs can still trip a 1 GB container's memory limit; the app recovers automatically, but in-flight results are lost unless the chunk checkpoint can be resumed in the same session.

Root `requirements.txt` and [`app/requirements.txt`](requirements.txt) carry identical Streamlit pins; CI fails if they drift. `app/pyproject.toml` remains the API/Docker project and is safe to keep (Community Cloud checks `requirements.txt` first in that directory). Do **not** add a high-priority `uv.lock`, `Pipfile`, or `environment.yml` at the repo root or in `app/` — those would shadow the Streamlit pins. The hash-pinned lockfile lives at the repo root for the API/Docker surface.

## Smoke test after deploy

**Streamlit:** open [https://labelforge-monigarr.streamlit.app/](https://labelforge-monigarr.streamlit.app/), select **Old Tom — Pass**, click **Verify label**, and confirm **All fields match**. Then open **Batch verify**, confirm **25 labels** is selected, and run the free-tier batch; verify that **200 labels** and **300 labels** are visible but disabled. Test 200/300 locally or in Docker. Community Cloud runs Tesseract 4.1.1; the bold-header heuristic compares the header against the adjacent warning line, so the happy-path sample should pass. If the app was already running before this fix was pushed, use **Manage app → Reboot app** once to reload the imported engine modules.

**Render (after resuming the service):**

```bash
curl https://labelforge-w32d.onrender.com/health
curl -X POST https://labelforge-w32d.onrender.com/verify \
  -F "image=@fixtures/labels/old_tom_match.png" \
  -F "application=$(cat fixtures/applications/old_tom_match.json)"
```

Expected `/health` includes `batch_persist: true` and `latency_gate_enabled: true` on production. Browser: use **Try this sample** on **Old Tom — Pass**, then verify single-label and batch flows.

## Local without Tesseract

If Tesseract is not on PATH, the fixture sidecar can supply OCR text only for a **committed fixture image uploaded byte-for-byte unchanged** (e.g. the `old_tom_match` sample from the gallery). Sidecar text is content-addressed, so an arbitrary upload with a copied `label_id` returns no text rather than fabricated compliance values. Production Docker images and Streamlit Cloud include Tesseract.

*Last verified against repo: 2026-10-19*
