# Deployment Guide

**Production URL:** https://labelforge.onrender.com (Render Blueprint in [`render.yaml`](../render.yaml))  
**Proof index:** [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md)

> As of 2026-06-09 the Render service is **owner-suspended**. Resume it in the Render dashboard or redeploy via Blueprint before interview submission.

## Docker (recommended)

```bash
cd app
docker compose up --build
```

Open http://localhost:8000 — API + built UI on one port. Tesseract is included in the container.

## Railway

1. Create project from this repo; set root directory to `app`
2. Use `Dockerfile` builder (see `railway.toml`)
3. Set environment variables from `.env.example`
4. Copy the generated HTTPS URL into `app/README.md`

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

Render injects `PORT` automatically (default `10000`). The Dockerfile reads `${PORT:-8000}` so local Docker Compose still works on port 8000.

First build takes ~5–10 minutes (Node UI build + Tesseract install + pip).

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
5. Deploy and copy the generated `*.onrender.com` URL into `app/README.md`

## Environment variables (platform)

| Variable | Value |
|----------|--------|
| `OCR_PROVIDER` | `tesseract` (default in Docker) |
| `USE_FACTORY_GRAPH` | `false` |
| `RAG_ENABLED` | `false` |
| `STRICT_WARNING` | `true` |
| `BATCH_CONCURRENCY` | `6` |
| `PORT` | **Do not set** — Render injects automatically |

Optional Azure OCR keys from `.env.example` only if you want cloud OCR instead of Tesseract. Never commit secrets.

## Smoke test after deploy

```bash
curl https://YOUR_URL/health
curl -X POST https://YOUR_URL/verify \
  -F "image=@fixtures/labels/old_tom_match.png" \
  -F "application=$(cat fixtures/applications/old_tom_match.json)"
```

Browser: open the URL, upload a label image, paste application JSON, verify single-label and batch flows.

## Local without Tesseract

If Tesseract is not on PATH, set `label_id` in application JSON to match a fixture stem (e.g. `old_tom_match`) — sidecar `.txt` files in `fixtures/labels/` are used for demo OCR. Production Docker images include Tesseract.
