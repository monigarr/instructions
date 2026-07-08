# Deployment Guide

**Production URL:** [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)  
**Onboarding:** [ONBOARDING.md](../ONBOARDING.md) · **Blueprint:** [`render.yaml`](../render.yaml) · **Proof index:** [DELIVERABLES_PROOF.md](../DELIVERABLES_PROOF.md)  
**Client constraints:** [ClientRequirement.md](../ClientRequirement.md) — standalone PoC, firewall-aware OCR (Marcus Williams)

Live on Render Starter (always-on). Tesseract OCR runs in-container; no API keys required for the default demo path.

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
| `USE_FACTORY_GRAPH` | `false` |
| `RAG_ENABLED` | `false` |
| `BATCH_PERSIST` | `true` |
| `LATENCY_GATE_ENABLED` | `true` |

> **Hostname note:** Blueprint service name is `labelforge`. Render assigns the live hostname suffix (e.g. `labelforge-w32d.onrender.com`).

Render injects `PORT` automatically (default `10000`). The Dockerfile reads `${PORT:-8000}` so local Docker Compose still works on port 8000.

First build takes ~5–10 minutes (Node 20 UI build + Tesseract install + pip).

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

**Node versions:** Node.js 18+ for local dev; Docker and CI use Node 20.

## Smoke test after deploy

```bash
curl https://labelforge-w32d.onrender.com/health
curl -X POST https://labelforge-w32d.onrender.com/verify \
  -F "image=@fixtures/labels/old_tom_match.png" \
  -F "application=$(cat fixtures/applications/old_tom_match.json)"
```

Expected `/health` includes `batch_persist: true` and `latency_gate_enabled: true` on production.

Browser: open the URL, use **Try this sample** on **Old Tom — Pass**, verify single-label and batch flows.

## Local without Tesseract

If Tesseract is not on PATH, set `label_id` in application JSON to match a fixture stem (e.g. `old_tom_match`) — sidecar `.txt` files in `fixtures/labels/` are used for demo OCR. Production Docker images include Tesseract.

*Last verified against repo: 2026-07-08*
