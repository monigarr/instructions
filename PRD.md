# Product Requirements Document (PRD)

**Product:** AI-Powered Alcohol Label Verification App — *LabelForge Agent Factory*  
**Document type:** Prototype / proof-of-concept PRD (technical interview showcase)  
**Primary source:** [ClientRequirement.md](ClientRequirement.md)  
**Approach & trade-offs:** [APPROACH.md](APPROACH.md)  
**Security & accessibility:** [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md)  
**Status:** Implemented (P1 + P2+ in `app/`); **live** on Streamlit Community Cloud at [labelforge-monigarr.streamlit.app](https://labelforge-monigarr.streamlit.app/) (root `streamlit_app.py` → implementation `app/streamlit_app.py`). The full FastAPI + React stack is configured on Render at [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) (service currently suspended). Deployment steps: [README.md](README.md#1-streamlit-community-cloud-live-deploy-target)  
**Author:** Monica Peters (MoniGarr) | Gauntlet AI GFA Cohort 5 Fellowship, 2026  
**Last updated:** 2026-10-19

---

## Document hierarchy

| Layer | Authority | Role |
|-------|-----------|------|
| **Client truth** | [ClientRequirement.md](ClientRequirement.md) | Normative requirements and **two deliverables only** |
| **Approach** | [APPROACH.md](APPROACH.md) | Tools, assumptions, trade-offs, upgrade/deferred register |
| **Security & accessibility** | [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md) | Prototype posture, controls, 508 fixes, hardening backlog |
| **This PRD** | [PRD.md](PRD.md) | Requirements, scope boundary, phases, acceptance criteria |
| **Archived design docs** | [docs/archive/](docs/archive/) | Historical target-state design, proof index, onboarding, review guide, audit |

**Rule:** Ship **P1 MVP** first. Factory, RAG, and eval CI are proof of senior engineering — not a third client deliverable. The eight superseded root documents were archived on 2026-10-19; each carries an archive banner.

---

## 1. Executive summary

The TTB Compliance Division reviews roughly 150,000 alcohol label applications per year. Much of each review is repetitive data matching between application fields and label artwork. This project delivers a **standalone prototype** that satisfies [ClientRequirement.md](ClientRequirement.md): fast label verification, batch throughput, and a **grandmother-simple UI**.

**P1 (submission):** Working source repo + deployed URL with upload → extract → compare → results (single + batch), TTB field coverage, and documented approach in README.

**P2+ (interview craft):** Evolve toward the **LabelForge Agent Software Factory** — graph orchestration, RAG, evals, S.O.L.I.D. boundaries — as described in [ARCHITECTURE.md](docs/archive/ARCHITECTURE.md). This depth demonstrates senior AI-native design but does **not** replace the two client deliverables.

This is **not** a COLA integration project.

---

## 2. Problem statement

| Pain point | Detail |
|------------|--------|
| Manual verification load | Agents spend significant time confirming form values match label artwork (brand, ABV, warnings, etc.) |
| Throughput limits | Peak importers may submit 200–300 labels at once; current workflow is largely one-at-a-time |
| Prior pilot failure | A scanning vendor pilot failed adoption because processing took 30–40 seconds per label |
| UX risk | Past modernization tools failed when interfaces were hard to navigate |
| Unmeasurable AI risk | Ad-hoc OCR/LLM pipelines lack eval gates, traceability, and regression control |

**Desired outcome:** A fast, approachable tool that automates routine matching, surfaces mismatches clearly, leaves human judgment authoritative—and demonstrates **production-grade AI-native engineering** (agents, graphs, RAG, evals, SOLID) suitable for a senior technical interview.

---

## 3. Stakeholders and users

| Stakeholder | Role | Key needs |
|-------------|------|-----------|
| Sarah Chen | Deputy Director, Label Compliance | Speed (~5 s/label), batch uploads, simple UX |
| Dave Morrison | Senior Compliance Agent (28 yrs) | Faster queue processing; nuance for near-matches (e.g., casing differences) |
| Jenny Park | Junior Compliance Agent | Exact government warning validation; tolerance for imperfect photos (stretch) |
| Marcus Williams | IT Systems Administrator | Standalone prototype; security awareness; firewall/API constraints |
| **Technical evaluator** | Interview reviewer | AI-native architecture depth, code quality, creative problem-solving, working demo |

**Primary user:** TTB compliance agents reviewing label applications.

**Secondary audience:** Engineering evaluators assessing AI-first architecture, agent orchestration, and eval discipline.

---

## 4. Goals and success metrics

### 4.1 Product goals (ClientRequirement.md)

1. Automate routine label-vs-application field matching for common TTB label elements.
2. Return verification results quickly enough for daily agent use (**≤ ~5 s**).
3. Support batch review during peak import periods (**200–300** scale).
4. Present results in a UI that requires minimal training.
5. Document approach, tools, assumptions, and trade-offs in README.

### 4.2 Engineering goals (interview — P2+, not submission blockers)

6. Evolve toward autonomous agent software factory with graph orchestration, RAG grounding, and eval discipline.
7. Demonstrate S.O.L.I.D. boundaries in code organization and README approach section.

### 4.3 Success metrics

#### Client metrics (must meet for submission — §10)

| Metric | Target |
|--------|--------|
| Single-label processing time | **≤ ~5 seconds** (user-perceived; Sarah Chen) |
| Batch upload | **200–300 labels** in one session |
| Core field coverage | All fields in §6.1 |
| Deployability | Publicly testable deployed URL |
| Repository completeness | Runnable locally from README |
| UX | Clean, obvious; no hunting for buttons |

> **Live demo constraint:** the Streamlit Community Cloud free tier throttles sustained CPU, so the public demo caps batches at **25 labels**. The 200–300 requirement is fully supported and tested locally, in Docker, and through the API; the cap is documented in [README.md](README.md#batch-limits-by-surface).

#### Engineering metrics (aspirational — P2+; supports interview, not ClientRequirement.md)

| Metric | Target |
|--------|--------|
| Eval: field verdict accuracy | **≥ 95%** on golden fixture set |
| Eval: government warning detection | **100%** recall on warning adversarial fixtures |
| Eval: false-pass rate | **0%** on low-confidence adversarial fixtures |
| Traceability | `trace_id` in logs linking pipeline stages (optional in UI) |

### 4.4 Architecture goals (phased target — ARCHITECTURE.md)

| Goal | Evidence |
|------|----------|
| **S.O.L.I.D. codebase** | Interface-driven agents, rules, retrievers, OCR providers |
| **Graph orchestration** | LangGraph (or equivalent) state machine with conditional routing |
| **RAG grounding** | TTB corpus retrieval before compliance verdict nodes |
| **Agent specialization** | Single-responsibility agents composed by factory |
| **Eval-driven quality** | Offline datasets + CI eval runner + optional LangSmith traces |
| **Human-in-the-loop** | Graph pause/resume at low-confidence or mismatch review nodes |

---

## 5. Scope

### 5.1 In scope — client (ClientRequirement.md) — **P1 must ship**

- Standalone web prototype for label verification
- Upload label image(s) plus corresponding application data
- AI/OCR extraction and comparison of label fields
- Pass/fail or flagged mismatch reporting per label and per field
- Batch upload and batch results view
- Simple, accessible UI and basic error handling
- README: setup, run, approach, tools, assumptions, trade-offs
- **Two deliverables only:** source repo + deployed URL ([§10](#10-deliverables))

### 5.1b In scope — phased target (interview craft — **P2+**, [archived design](docs/archive/ARCHITECTURE.md))

- Agent Software Factory composition root
- LangGraph (or equivalent) workflow with fallbacks
- RAG over TTB regulatory corpus
- Offline eval harness + CI regression gate (enforced in GitHub Actions; production deploy unaffected)
- S.O.L.I.D. ports/adapters for OCR, rules, retrieval
- Structured logging / optional LangSmith traces

*None of §5.1b blocks submission if §5.1 and §10 are complete.*

### 5.2 Out of scope

- Direct integration with the COLA system
- Production FedRAMP / full federal compliance deployment
- Long-term document retention or PII handling policies (prototype uses non-sensitive exercise data)
- Full legal adjudication of borderline compliance cases (human review remains authoritative)
- Fully autonomous approval without human agent sign-off

**Scope boundary reaffirmed 2026-10-19.** The following remain deliberately cut and are not partial implementations: document retention/purge policy, data-classification program, CUI/PIA documentation, NIST 800-53 / CISA attestation, and a VPAT. Production identity/SSO, WAF/rate limiting, managed queue/object storage, and database-backed audit state are also out of scope. Security and accessibility posture — including what was implemented and what remains for production — is documented in [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md); the deferred register is in [APPROACH.md](APPROACH.md) §7–§9.

### 5.3 Stretch / nice-to-have

- Robust handling of skewed, glare-heavy, or poorly lit label photos
- LLM-generated plain-language mismatch explanations (RAG-grounded, not free-form)
- Online eval sampling in deployed demo environment
- Multi-beverage RAG rule packs (beer, wine, spirits)

---

## 6. Functional requirements

### 6.1 Label field verification

The app must verify label artwork against application data for TTB-relevant elements. At minimum, support the distilled spirits example and common cross-beverage fields from [ClientRequirement.md](ClientRequirement.md):

| Field | Verification notes |
|-------|-------------------|
| Brand name | Match against application; configurable fuzzy match for casing/punctuation (Dave Morrison) |
| Class / type designation | e.g., "Kentucky Straight Bourbon Whiskey" |
| Alcohol content | e.g., "45% Alc./Vol. (90 Proof)" |
| Net contents | e.g., "750 mL" |
| Government health warning | **Exact** text match; `GOVERNMENT WARNING:` in **all caps** and **bold** |
| Name and address of bottler/producer | Where present on label type |
| Country of origin | For import labels where applicable |

**Reference example (distilled spirits):**

- Brand Name: `OLD TOM DISTILLERY`
- Class/Type: `Kentucky Straight Bourbon Whiskey`
- Alcohol Content: `45% Alc./Vol. (90 Proof)`
- Net Contents: `750 mL`
- Government Warning: standard TTB warning text

Additional test labels (AI-generated or sourced) are encouraged by the client for demo; required for P1 submission quality.

### 6.2 Verification workflow

#### P1 MVP path (client submission — must implement)

1. Human agent provides label image(s) and application field values (form, CSV, or JSON).
2. System validates upload, extracts text from label (OCR/vision), structures fields.
3. System compares extracted values to application data **field by field** (deterministic rules).
4. System displays per-label and per-field status: `match`, `mismatch`, or `unable_to_verify` (with reason).
5. Human agent reviews flagged items; system does **not** auto-approve legally.

```text
P1: upload → validate → extract → structure → rules → results (single + batch)
```

#### P2+ target path (LabelForge factory — ARCHITECTURE.md)

Optional evolution: factory instantiates a verification graph with conditional routing, RAG enrich node, nuance agent, and eval hooks. Same client-visible outcomes; richer backend orchestration.

```text
P2+: ingest → extract → structure → [rag_enrich] → rules → [nuance] → aggregate → END
```

### 6.3 Batch processing

- Accept **200–300** labels per batch operation (client peak scenario).
- Show batch progress and aggregate summary (passed / failed / needs review).
- Partial failures must not fail entire batch.
- P1: concurrent or queued processing acceptable; P2+ may use `BatchSupervisorAgent` pattern.

### 6.4 User interface (client-first)

- **Clean, obvious layout** — benchmark: Sarah Chen’s “my mother could figure out” standard.
- **USWDS 3.0–aligned styling** — federal design tokens and system font stack (no third-party font CDN) in custom CSS; two-tab workflow (Verify One Label / Batch Verify).
- **Must show:** label image, extracted values, application values, field-level diffs for mismatches.
- **Batch quick-starts:** demo catalog batch (34), plus 25-label (live free tier), 200-label, and 300-label scale tests. The 200/300 controls are visible but disabled on the public free-tier demo; they remain enabled locally and in Docker (Sarah/Janet peak-load requirement).
- **Must not:** hide complexity behind opaque scores; require training to find primary actions (Dave Morrison).
- **Optional (P2+ / logs / README):** pipeline stage names, `trace_id`, graph node provenance — keep out of default agent UI unless minimal.

### 6.5 Error handling and edge cases

- Reject or flag unreadable images with re-upload guidance.
- Never silent false-pass on low confidence.
- Document fuzzy brand behavior in README assumptions.
- P2+: graph retry — 1 retry on transient OCR failure → local fallback → `unable_to_verify`.

---

## 7. AI-native factory requirements (P2+ target state)

> **Not client deliverables.** This section defines phased engineering depth per [ARCHITECTURE.md](docs/archive/ARCHITECTURE.md). Implement after P1 repo + URL satisfy §10.

### 7.1 Autonomous Agent Software Factory

The **LabelForge Factory** is the composition root that:

| Capability | Requirement |
|------------|-------------|
| Agent registry | Register agents by role with version metadata |
| Tool injection | Inject OCR, RAG retriever, rules engine, clock, logger via interfaces |
| Graph compilation | Build verification graph from declarative config (YAML/code) |
| Run lifecycle | Create `run_id`, persist state snapshots (in-memory PoC; pluggable store) |
| Policy enforcement | Block auto-approve paths; eval regression thresholds in CI (P3) |
| Batch mode | Spawn parallel graph runs under concurrency budget |

**Specialized agents (minimum roster):**

| Agent | Single responsibility |
|-------|----------------------|
| **IngestionAgent** | Validate uploads, normalize images, assign `label_id` |
| **VisionExtractionAgent** | OCR/vision extraction via `IOCRProvider` |
| **FieldStructuringAgent** | Map raw OCR → `ExtractedLabelRecord` |
| **ComplianceRAGAgent** | Retrieve TTB rules, canonical warning text, field definitions |
| **RulesEngineAgent** | Deterministic field comparison (owns final verdict bits) |
| **NuanceAgent** | Brand fuzzy equivalence proposals (human-review flagged) |
| **BatchSupervisorAgent** | Fan-out/fan-in, progress, aggregation |
| **EvalRunnerAgent** | Execute offline eval suites (CI/dev; not user-facing) |

### 7.2 Graph orchestration (LangGraph-style)

| Requirement | Detail |
|-------------|--------|
| State schema | Typed `VerificationState` (image ref, application data, extractions, RAG context, verdicts, timings, errors) |
| Nodes | One node per agent responsibility; idempotent where possible |
| Edges | Sequential pipeline + conditional routes (confidence, provider health, retries) |
| Checkpoints | Optional HITL pause before final verdict emission |
| Fallback path | Cloud OCR node → local OCR node → unable-to-verify terminus |
| Observability | Emit span per node with duration and outcome |

**P2+ target graph topology** (full factory — not required for P1 submission):

```text
START → ingest → extract → structure → rag_enrich → rules → nuance → aggregate → END
                      ↓ (low confidence)          ↓ (strict fail)
                   retry/fallback            needs_human_review
```

### 7.3 RAG (Retrieval-Augmented Generation)

RAG is used to **ground** compliance reasoning—not to replace deterministic rules.

| Requirement | Detail |
|-------------|--------|
| **Corpus** | TTB label requirement summaries, canonical government warning text, field glossaries, beverage-type notes |
| **Chunking** | Semantic chunks with metadata (`field`, `beverage_type`, `severity`) |
| **Vector store** | Chroma, pgvector, or Azure AI Search (prototype-flexible) |
| **Embeddings** | Configurable provider; local embedding option for firewall scenarios |
| **Retrieval** | Top-k retrieval per field during `rag_enrich` node; cite `chunk_id` in logs/UI |
| **Grounding rule** | LLM (if used) may **explain** mismatches only from retrieved chunks; verdict bits come from RulesEngineAgent |
| **Refresh** | Script to re-index corpus when TTB fixtures update |

### 7.4 Evaluation framework (Evals) — engineering practice, not a client deliverable

Evals support **correctness** and **creative problem-solving** (ClientRequirement evaluation criteria). They are **recommended from P1** (golden labels + unit tests on rules) and **expanded in P3** (CI regression). They are **not** a third submission item alongside repo + URL.

| Eval layer | Purpose | CI policy (P3 target) |
|------------|---------|----------------------|
| **Unit** | Normalizers, individual `IFieldRule` | Recommended P1; block in P3 |
| **Agent** | Mock-state agent node I/O contracts | P2+ |
| **Graph integration** | End-to-end run on golden fixtures | P2+ |
| **RAG** | Retrieval precision/recall | P2+ |
| **Performance** | P95 latency ≤ 5 s | Warn anytime; document in README |
| **Adversarial** | Wrong warning case, false-pass bait | P3 recommended |

**Golden dataset structure:**

```text
evals/
  datasets/
    golden_labels.jsonl      # image + application + expected verdicts
    adversarial_labels.jsonl
    rag_queries.jsonl        # query + expected chunk ids
  metrics/
    field_accuracy.py      # per-field + aggregate accuracy
    warning_recall.py
    latency_p95.py
    rag_precision.py       # per-field RAG hit rate
  runners/
    run_eval_suite.py        # invoked in GitHub Actions
```

**Reporting:** Eval summary artifact uploaded in CI; README documents how to run locally.

### 7.5 S.O.L.I.D. engineering standards

| Principle | Project application |
|-----------|---------------------|
| **S** — Single Responsibility | One agent / one rule class / one graph node per concern |
| **O** — Open/Closed | Add beverage types or field rules without modifying orchestrator core |
| **L** — Liskov Substitution | `AzureOCRProvider` and `TesseractOCRProvider` interchangeable via `IOCRProvider` |
| **I** — Interface Segregation | Separate `IOCRProvider`, `IRulesEngine`, `IRAGRetriever`, `IAgentNode`, `IGraphRunner` |
| **D** — Dependency Inversion | Factory wires concrete adapters from config; domain depends on abstractions |

All production code files must use [CODE_COMMENT_HEADER_TEMPLATE.md](docs/archive/CODE_COMMENT_HEADER_TEMPLATE.md).

---

## 8. Non-functional requirements

### Client (must meet — P1)

| Category | Requirement |
|----------|-------------|
| **Performance** | **≤ ~5 seconds** per label (user-perceived core path) |
| **Usability** | Simple workflow; grandmother-simple UI |
| **Security (prototype)** | No sensitive data; no secrets in repo; don’t “do anything crazy” |
| **Network** | Document cloud API dependency or implement/document offline OCR fallback |
| **Portability** | README enables local setup and run by evaluators |

### Engineering (P2+ — recommended)

| Category | Requirement |
|----------|-------------|
| **Maintainability** | SOLID modules; swappable OCR provider |
| **Observability** | Structured JSON logs; `trace_id` in logs/results and `X-Trace-ID` response header (not required in UI) |
| **Testability** | Rules unit tests P1; golden eval suite P2+; ≥ 80% rules coverage aspirational |

---

## 9. Technical constraints and context

- No mandated language/framework; **recommended stack** documented in [ARCHITECTURE.md](docs/archive/ARCHITECTURE.md).
- Azure is agency context; prototype deploys to any HTTPS-accessible URL.
- COLA (.NET legacy) — **no direct coupling**.
- Interview time-box: **P1 ships first** (repo + URL + §10.2); factory/RAG/eval CI per §12 and [ARCHITECTURE.md](docs/archive/ARCHITECTURE.md).

### Recommended AI-native stack (as shipped)

| Layer | Technology |
|-------|------------|
| API | Python FastAPI + Uvicorn |
| Graph (optional) | LangGraph (`USE_FACTORY_GRAPH=true`) |
| Agents/tools | LangChain or lightweight custom `IAgentNode` |
| RAG (optional) | LangChain retriever + Chroma (`RAG_ENABLED=true`) |
| OCR | Tesseract default (offline) + Azure Document Intelligence fallback + content-addressed fixture sidecar |
| Evals | Custom runner + optional LangSmith traces |
| UI | React + TypeScript (production); Streamlit (Community Cloud surface) |
| Batch | Live Streamlit capped at 25 labels (free-tier CPU); chunked/resumable 200–300 off the free tier; concurrent API batch with optional persistence |
| Packaging | Docker (non-root) + hash-pinned `requirements.lock` |
| CI | GitHub Actions: `test`, `ui`, `lint-and-security`, `locked-install`, `streamlit-smoke`, `docker` |

---

## 10. Deliverables

> **Client truth lives in [ClientRequirement.md](ClientRequirement.md) and §10 below.** It lists exactly **two** submissions. Everything else is implementation or phased target state. The historical checklist moved to [docs/archive/DELIVERABLES.md](docs/archive/DELIVERABLES.md).

**Authoritative client list:** [ClientRequirement.md](ClientRequirement.md) § Deliverables.  
**Proof with file paths and URLs:** [docs/archive/DELIVERABLES_PROOF.md](docs/archive/DELIVERABLES_PROOF.md) (historical index; live setup is [README.md](README.md)).

**Current repository:** [github.com/monigarr/instructions](https://github.com/monigarr/instructions) — application in [`app/`](app/).  
**Deployed URLs:**  
- Streamlit Community Cloud — **live** at [https://labelforge-monigarr.streamlit.app/](https://labelforge-monigarr.streamlit.app/); entrypoint `streamlit_app.py` (root shim → `app/streamlit_app.py`), dependencies root `requirements.txt`, apt `packages.txt`, Python 3.11 (deployment steps: [README.md](README.md#1-streamlit-community-cloud-live-deploy-target)); free-tier batch cap **25**
- Render Starter — [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) ([`render.yaml`](render.yaml)); service is currently **suspended**, resume it in the Render dashboard

Only **two submissions** are mandatory. LabelForge factory work (§7) is **phased engineering depth** — prove it in **code + README approach**, not as extra doc deliverables.

### 10.1 Required client submissions

#### A. Source code repository (GitHub or similar)

| Client asks for | Acceptance criteria |
|-----------------|---------------------|
| All source code | Runnable app: label upload, field extraction, comparison, single + batch flows |
| README with setup and run instructions | Evaluator can clone, install, run, and verify a sample label unaided |
| Brief approach documentation | Tools, architecture summary, assumptions, trade-offs, limitations |

#### B. Deployed application URL

| Client asks for | Acceptance criteria |
|-----------------|---------------------|
| Working prototype | Public HTTPS URL; same core flows as local |
| Accessible for hands-on test | Single-label + batch verification + clear results |

**Deployed surfaces (same engine):**

| Surface | Entry point | Status |
|---------|-------------|--------|
| Streamlit Community Cloud | root `streamlit_app.py` + `requirements.txt` + `packages.txt` | **live** at [labelforge-monigarr.streamlit.app](https://labelforge-monigarr.streamlit.app/); public, no login; redeploys on `main`; free-tier batch cap **25** |
| Render (Docker, FastAPI + React) | [`render.yaml`](render.yaml) | configured at [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com); currently suspended — resume in dashboard |
| Railway (Docker) | [`app/railway.toml`](app/railway.toml) | supported |
| Docker Compose | [`app/docker-compose.yml`](app/docker-compose.yml) | supported |

### 10.2 Client requirements the deliverables must prove

| Requirement | Constraint source |
|-------------|-------------------|
| ≤ ~5 s per label (user-perceived) | Sarah Chen |
| Batch upload (200–300 scale) | Sarah Chen |
| Simple, obvious UI | Sarah Chen; Dave Morrison |
| Standalone — no COLA integration | Marcus Williams |
| No sensitive data; sensible prototype security | Marcus Williams |
| Firewall-aware (cloud API fallback documented or implemented) | Marcus Williams |
| TTB fields + distilled spirits example | ClientRequirement.md § Sample Label |
| Exact government warning (caps, bold, word-for-word) | Jenny Park |
| Brand casing nuance (creative problem-solving) | Dave Morrison |
| Additional test labels encouraged | ClientRequirement.md |
| Working core over incomplete ambition | Evaluation Criteria |

### 10.3 P1 vs P2+ in the application repository

| Phase | Client required? | Typical contents |
|-------|------------------|------------------|
| **P1 — submit** | **Yes** | `README`, app source, `fixtures/`, test labels, `.env.example`, deployed URL |
| **P2+ — craft** | No | `factory/`, `graph/`, `rag/`, `evals/` — per [archived target layout](docs/archive/ARCHITECTURE.md) |

Omitting P2+ folders does **not** fail submission if §10.1–10.2 are met. Document factory roadmap in README approach section when P2+ is planned or partial.

### 10.4 Recommended repository contents (supports evaluation criteria — not extra client submissions)

| Artifact | Purpose |
|----------|---------|
| `fixtures/` + test labels | Client-encouraged sample labels; demo and regression |
| Verification source (any structure) | OCR/extraction, rules, batch — e.g. `src/` with factory/graph/agents/rag/rules |
| `evals/` | Quality gates with CI regression enforcement; supports “correctness” and “creative problem-solving” |
| `.env.example` | Document OCR/API config without secrets |

### 10.5 Supporting documentation (this instructions repo — not submitted as deliverables)

| Artifact | Purpose |
|----------|---------|
| [README.md](README.md) | Setup, run, five runtime deployment options (plus CI), reviewer paths |
| [APPROACH.md](APPROACH.md) | Approach, tools, assumptions, trade-offs, upgrade/deferred register |
| [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md) | Prototype posture, implemented controls, 508 fixes, hardening backlog |
| [ClientRequirement.md](ClientRequirement.md) | Primary source of truth |
| [PRD.md](PRD.md) | This document |
| [docs/archive/](docs/archive/) | Historical proof index, checklist, target-state design, onboarding, review guide, audit |

> Superseded root documents were archived on 2026-10-19. Each archived file carries a banner pointing back to the canonical set.

---

## 11. Evaluation criteria (client + interview)

### Client evaluators

1. Correctness and completeness of core requirements (fields, speed, batch, UX)
2. Code quality and organization
3. Appropriate technical choices for scope
4. User experience and error handling
5. Attention to requirements (especially warning exactness)
6. Creative problem-solving

### Interview evaluators (AI-native depth)

Evidence map: [APPROACH.md](APPROACH.md) §2–§6 · Live deployment: [labelforge-monigarr.streamlit.app](https://labelforge-monigarr.streamlit.app/) · Render (currently suspended): [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) · Deploy steps: [README.md](README.md#1-streamlit-community-cloud-live-deploy-target)

7. **Agent factory pattern** — composable agents with clear boundaries → [`app/src/factory/`](app/src/factory/)
8. **Graph orchestration** — stateful workflow, fallbacks → [`app/src/graph/`](app/src/graph/)
9. **RAG discipline** — grounded retrieval; rules own verdicts → [`app/src/rag/`](app/src/rag/)
10. **Eval culture** — golden datasets, per-field CI gates, adversarial cases → [`app/evals/`](app/evals/), [`app/tests/test_eval_metrics.py`](app/tests/test_eval_metrics.py)
11. **S.O.L.I.D. evidence** — interfaces, DI, OCR adapters → [`app/src/domain/interfaces.py`](app/src/domain/interfaces.py)
12. **Pragmatic shipping** — P1 live on Streamlit Community Cloud ([labelforge-monigarr.streamlit.app](https://labelforge-monigarr.streamlit.app/)) with the full stack deployable on Render (currently suspended); P2+ behind flags → [`render.yaml`](render.yaml), [`streamlit_app.py`](streamlit_app.py), [`app/streamlit_app.py`](app/streamlit_app.py), [`app/README.md`](app/README.md)

**Guidance:** **P1 satisfies ClientRequirement.md.** P2–P4 add interview craft; never block URL submission on eval CI or full graph.

---

## 12. Implementation phases

| Phase | Scope | Client / exit criteria |
|-------|-------|------------------------|
| **P0 — Foundation** | Interfaces, project skeleton, README draft | Compiles locally |
| **P1 — MVP (SUBMIT)** | Ingest → extract → structure → rules → UI; single + batch; fixtures | **Repo + URL live**; §10.2 met; P95 ≤ ~5 s documented |
| **P2 — Graph + RAG** | Factory, LangGraph, ComplianceRAGAgent, NuanceAgent | Interview craft; README approach updated |
| **P3 - Eval hardening** | Golden/adversarial suites; **69** pytest tests (100% rules coverage); CI regression gate enforced (six jobs incl. lockfile audit, secret scan, Streamlit smoke, Docker) | Engineering quality; production deploy unaffected |
| **P4 — Stretch** | **Partially shipped:** batch checkpoint/resume (HITL-style review gate), `PREPROCESS_IMPERFECT` image preprocessing. **Documented as cut:** LLM-generated plain-language explanations, online eval sampling. | Jenny Park stretch; cuts recorded in [APPROACH.md](APPROACH.md) §9 |

---

## 13. Assumptions and open questions

### Assumptions

- Synthetic/non-sensitive labels only in prototype.
- Application data provided alongside each label (no COLA API).
- Government warning canonical text seeded into RAG corpus and rules fixtures.
- Bold detection uses OCR/layout heuristics; behavior documented.
- LLM calls optional; deterministic rules path sufficient for MVP verdicts.

### Open questions

- Evaluator network restrictions for cloud OCR/LLM at demo time? (Documented: Tesseract default; Azure optional with fallback per Marcus Williams)

**Resolved:**

- Batch manifest format: **JSON** (`POST /batch/verify`) and **CSV** (`POST /batch/verify-csv`) — see [APPROACH.md](APPROACH.md) §4

### Achieved metrics (beyond aspirational targets)

| Metric | PRD target | Achieved |
|--------|------------|----------|
| Golden summary accuracy | ≥ 95% | **100%** (30 golden cases) |
| Adversarial warning recall | 100% | **100%** |
| False-pass rate (adversarial) | 0% | **0%** |
| Production `/verify` latency | ≤ ~5 s | **~3.7 s** on Render Starter |
| Batch scale | 200–300 labels | **300/300** completed in the API and local Streamlit (chunked, resumable); live free-tier demo intentionally capped at **25** |
| Dependency advisories | none known on shipped surface | `pip-audit` clean on `requirements.lock`; npm production clean |

---

## 14. References

- [ClientRequirement.md](ClientRequirement.md) — primary source of truth
- [README.md](README.md) — setup, run, five runtime deployment options (plus CI)
- [APPROACH.md](APPROACH.md) — approach, tools, assumptions, trade-offs, upgrade register
- [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md) — security and accessibility posture
- [docs/archive/ARCHITECTURE.md](docs/archive/ARCHITECTURE.md) — phased target-state design (historical)
- [docs/archive/CODE_COMMENT_HEADER_TEMPLATE.md](docs/archive/CODE_COMMENT_HEADER_TEMPLATE.md) — historical file-header standard
- [TTB label guidance](https://www.ttb.gov) — regulatory corpus source
