# Security and accessibility posture

> **Canonical docs:** [README](README.md) · [APPROACH](APPROACH.md) · **this file** · [PRD](PRD.md) · [ClientRequirement](ClientRequirement.md)
> **Status:** prototype / proof of concept · **Last reviewed:** 2026-10-19

LabelForge is a technical-interview prototype, not a production federal system. This document states the intended posture, the controls that are actually implemented, the accessibility work completed, and the gaps that remain. It is deliberately explicit: the client's IT stakeholder (Marcus Williams) asked for sensible prototype security and security awareness, and PRD §8 defines the bar.

---

## 1. Scope and intended use

- Public demo, **no authentication**, **synthetic fixtures only**.
- No COLA integration, no PII, no CUI, no controlled unclassified information.
- Do not upload real labels, personal data, or any document you would not publish.
- A `passed` verdict means "no discrepancy detected by deterministic rules"; it is **not** a legal approval.

Out of scope by design (PRD §5.2): retention/purge policy, CUI/PIA documentation, NIST 800-53 / CISA attestation, and a VPAT. Those are production-program deliverables, not prototype work.

---

## 2. Threat model (prototype)

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Service availability | oversized uploads, decompression bombs, giant batches | per-file 10 MB cap, 40 MP decode ceiling, 256 MB request cap, 400 files/batch, 2 MB manifest cap |
| Verdict integrity | client-supplied `label_id` fabricating compliant fixture text | sidecar OCR requires a byte-for-byte fixture-image hash match; label IDs validated; warning text never fabricated |
| Filesystem | path traversal via `label_id` / `batch_id` | shared validator + sanitized path joins in OCR sidecar and batch store |
| Browser security | wildcard CORS with credentials, clickjacking, MIME sniffing | explicit origin allowlist, credentials off, CSP, `X-Frame-Options: DENY`, `nosniff` |
| Information leak | stack traces or parser internals in responses | generic 500 + server-side `trace_id` correlation |
| Supply chain | vulnerable dependencies, committed secrets | hash-pinned lockfile, `pip-audit`, `npm audit`, `gitleaks`, Dependabot, non-root image |
| Container escape impact | root process in image | non-root `appuser` (uid 10001), writable paths limited to `/app/data` |

Non-goals for the prototype: defending against a determined attacker, multi-tenant isolation, DDoS, or abuse at internet scale. Those require platform controls listed in §6.

---

## 3. Implemented controls

### 3.1 API and input handling

| Control | Where |
|---------|-------|
| CORS allowlist (`CORS_ORIGINS`), `allow_credentials=False` | [`app/src/api/main.py`](app/src/api/main.py) |
| Security headers: CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP, HSTS | same |
| Request-size ceiling (`MAX_REQUEST_BYTES`, default 256 MB) checked before body read | same |
| Batch limits (`MAX_BATCH_FILES` 400, `MAX_BATCH_MANIFEST_BYTES` 2 MB) | same |
| Generic error responses with `trace_id`; full detail only in server logs | same |
| JSON-structured application logs, request `X-Trace-ID` propagation, no image/OCR payload logging | [`app/src/observability.py`](app/src/observability.py) |
| Upload validation: empty/size/MIME checks, magic-byte format allowlist (PNG/JPEG/WebP/GIF), 40 MP ceiling, full decode/verify | [`app/src/ingest/validator.py`](app/src/ingest/validator.py) |
| Every batch item passes the same validator inside the pipeline | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) |
| Batch IDs validated before any filesystem join | [`app/src/verify/batch_store.py`](app/src/verify/batch_store.py) |

### 3.2 Verdict integrity

| Control | Where |
|---------|-------|
| Sidecar OCR only for an exact hash match against a committed fixture image | [`app/src/adapters/ocr/sidecar_provider.py`](app/src/adapters/ocr/sidecar_provider.py) |
| Label-ID sanitization before path construction | [`app/src/domain/label_id.py`](app/src/domain/label_id.py) |
| No substitution of canonical government-warning text when extraction fails | [`app/src/structure/field_mapper.py`](app/src/structure/field_mapper.py) |
| OCR failures degrade to `unable_to_verify`, never a silent pass | [`app/src/verify/pipeline.py`](app/src/verify/pipeline.py) |

### 3.3 Supply chain and CI

| Control | Where |
|---------|-------|
| Hash-pinned lockfile for the API/Docker surface (`pip install --require-hashes`) | [`requirements.lock`](requirements.lock) |
| `pip-audit` against the lockfile | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| `npm audit --omit=dev --audit-level=high`; `npm ci` everywhere | same |
| `gitleaks` secret scan (current tree) | same |
| Ruff lint gate | same |
| Dependabot weekly for pip, npm, Actions | [`.github/dependabot.yml`](.github/dependabot.yml) |
| Non-root Docker user, healthcheck, deterministic build (no swallowed generator errors) | [`app/Dockerfile`](app/Dockerfile) |

### 3.4 Streamlit surface specifics

- Dependencies are exact-pinned in root [`requirements.txt`](requirements.txt) and [`app/requirements.txt`](app/requirements.txt) (CI enforces parity); the root manifest is what Community Cloud installs for the default root entrypoint. **Pillow 12.3.0** because Streamlit 1.66 pins `pillow<13` (patched line, zero known OSV advisories).
- No secrets or API keys are required; nothing is persisted server-side.
- Results live in browser session state only; uploaded bytes for a completed chunk are released.
- Uploads are re-validated by the same engine validator.
- HTTP security headers on `*.streamlit.app` are controlled by Streamlit, not this repository (shared-responsibility limitation).

### 3.5 Secrets

- `.env` is git-ignored; `.env.example` contains no secrets.
- CI scans the current tree for secrets.
- The demo needs no credentials. If Azure OCR is enabled, credentials belong in platform environment variables, never in the repo.
- If a credential is ever exposed, rotate it immediately; deleting the commit is not sufficient.

---

## 4. Accessibility

**Target:** Section 508 / WCAG 2.1 AA for the React UI. The Streamlit surface inherits Streamlit's built-in accessibility and is limited to theme-level adjustments.

### 4.1 Fixes completed (2026-10-19)

| Issue | Fix | Where |
|-------|-----|-------|
| File inputs used `display:none`, removing them from the keyboard tab order | visually hidden but focusable input (clip technique) with a visible `:focus-within` ring | [`app/ui/src/styles.css`](app/ui/src/styles.css) |
| Tabs exposed `aria-selected` without tab semantics | proper `role="tablist"` / `role="tab"` / `role="tabpanel"`, `aria-controls`, roving `tabIndex`, Left/Right arrow navigation, focusable panels | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |
| Success/warning text below AA contrast | success `#006a14` (6.84:1 on white, 6.05:1 on its tint) and warning `#765527` (6.78:1 on white, 6.07:1 on its tint) | [`app/ui/src/styles.css`](app/ui/src/styles.css) |
| Third-party Google Fonts request | removed; system font stack only (no third-party egress, no font-CDN dependency) | [`app/ui/index.html`](app/ui/index.html) |
| Misleading "drag a file" copy | reworded to "Click to choose…" to match actual behavior | [`app/ui/src/App.tsx`](app/ui/src/App.tsx) |

Existing positives retained: semantic landmarks (`header`, `nav`/tablist, `main`, `section`), labeled upload zones, `alt` text on previews, `role="alert"` errors, text + icon (not color alone) for verdicts, visible focus styles, responsive layout, and USWDS-aligned tokens.

### 4.2 Known accessibility gaps

- No automated axe/pa11y scan in CI (would require a headless browser step); keyboard behavior is verified manually.
- No formal VPAT — explicitly out of prototype scope (PRD §5.2).
- Streamlit's widget internals and page-level landmarks cannot be fully controlled by the app.
- Screen-reader testing has not been performed on physical assistive technology; a production program should budget for it.
- PDF/report export is not part of the prototype, so document-accessibility requirements do not apply.

---

## 5. Dependency security status

| Surface | Status |
|---------|--------|
| Python (API/Docker) | hash-pinned; `pip-audit` clean on the lockfile at audit time |
| Python (Streamlit) | exact-pinned root + app manifests (CI parity); Pillow 12.3.0 (0 known advisories) due to Streamlit's `<13` pin |
| npm production | 0 vulnerabilities |
| npm development | Vite/esbuild dev-server advisories remain; requires Vite 8 major (dev-only, never deployed) — tracked in [APPROACH.md](APPROACH.md) §7.2 |
| Container base images | `python:3.11-slim`, `node:24-alpine`; Node 20 removed (EOL) |

---

## 6. Production-hardening backlog

If this prototype were promoted to a production TTB system, the following would be required before handling real applications:

1. **Identity and access** — agency SSO/OIDC, role-based authorization, session management, audit of who verified what.
2. **Abuse protection** — WAF, per-user/IP rate limits, upload quotas, bot mitigation.
3. **Data protection** — encryption at rest/in transit with agency keys, retention/purge policy, records schedules, PII/CUI handling, PIA.
4. **Durable processing** — managed queue and object storage for batches; database-backed batch/audit state; idempotency keys.
5. **Observability** — centralized structured logs with retention, metrics/alerts, trace correlation, incident response runbook.
6. **Assurance** — NIST 800-53 control mapping, CISA attestation, penetration test, dependency and container scanning in the release pipeline, SBOM.
7. **Accessibility program** — VPAT/ACR, automated axe checks plus manual screen-reader testing, Section 508 conformance review.
8. **Verdict governance** — versioned rule sets, change control, legal review, human sign-off workflow, model/OCR change management.

None of these are claimed as complete. They are documented so reviewers can distinguish deliberate prototype scope from oversight.

---

## 7. Reporting

See [SECURITY.md](SECURITY.md) for private disclosure. Please do not open a public issue for an exploitable vulnerability.
