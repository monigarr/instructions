# Product Requirements Document (PRD)

**Product:** AI-Powered Alcohol Label Verification App — *LabelForge Agent Factory*  
**Document type:** Prototype / proof-of-concept PRD (technical interview showcase)  
**Primary source:** [ClientRequirement.md](ClientRequirement.md)  
**Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)  
**Deliverables:** [DELIVERABLES.md](DELIVERABLES.md)  
**Status:** Implemented (P1 + P2+ in `app/`); **production live** at [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)  
**Author:** Monica Peters (MoniGarr) | Gauntlet AI GFA Cohort 5 Fellowship, 2026  
**Last updated:** 2026-06-09

---

## Document hierarchy

| Layer | Authority | Role |
|-------|-----------|------|
| **Client truth** | [ClientRequirement.md](ClientRequirement.md) | Normative requirements and **two deliverables only** |
| **Proof** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | File paths + live URLs proving §10 deliverables |
| **Submission** | [DELIVERABLES.md](DELIVERABLES.md) + **§10 below** | Checklist for repo + URL + client constraints |
| **Target-state design** | [ARCHITECTURE.md](ARCHITECTURE.md) | Phased LabelForge factory — **P2+ shipped in `app/`** |
| **Interview craft** | §7, §4.3, §12 | Gauntlet-style depth in **code + README approach** after P1 ships |

**Rule:** Ship **P1 MVP** first. Factory, RAG, and eval CI are proof of senior engineering — not a third client deliverable.

---

## 1. Executive summary

The TTB Compliance Division reviews roughly 150,000 alcohol label applications per year. Much of each review is repetitive data matching between application fields and label artwork. This project delivers a **standalone prototype** that satisfies [ClientRequirement.md](ClientRequirement.md): fast label verification, batch throughput, and a **grandmother-simple UI**.

**P1 (submission):** Working source repo + deployed URL with upload → extract → compare → results (single + batch), TTB field coverage, and documented approach in README.

**P2+ (interview craft):** Evolve toward the **LabelForge Agent Software Factory** — graph orchestration, RAG, evals, S.O.L.I.D. boundaries — as described in [ARCHITECTURE.md](ARCHITECTURE.md). This depth demonstrates senior AI-native design but does **not** replace the two client deliverables.

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
| Batch upload | **200+ labels** in one session |
| Core field coverage | All fields in §6.1 |
| Deployability | Publicly testable deployed URL |
| Repository completeness | Runnable locally from README |
| UX | Clean, obvious; no hunting for buttons |

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
- **Two deliverables only:** source repo + deployed URL ([DELIVERABLES.md](DELIVERABLES.md))

### 5.1b In scope — phased target (interview craft — **P2+**, ARCHITECTURE.md)

- Agent Software Factory composition root
- LangGraph (or equivalent) workflow with fallbacks
- RAG over TTB regulatory corpus
- Offline eval harness + optional CI gates
- S.O.L.I.D. ports/adapters for OCR, rules, retrieval
- Structured logging / optional LangSmith traces

*None of §5.1b blocks submission if §5.1 and §10 are complete.*

### 5.2 Out of scope

- Direct integration with the COLA system
- Production FedRAMP / full federal compliance deployment
- Long-term document retention or PII handling policies (prototype uses non-sensitive exercise data)
- Full legal adjudication of borderline compliance cases (human review remains authoritative)
- Fully autonomous approval without human agent sign-off

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
- **Must show:** label image, extracted values, application values, field-level diffs for mismatches.
- **Must not:** hide complexity behind opaque scores; require training to find primary actions (Dave Morrison).
- **Optional (P2+ / logs / README):** pipeline stage names, `trace_id`, graph node provenance — keep out of default agent UI unless minimal.

### 6.5 Error handling and edge cases

- Reject or flag unreadable images with re-upload guidance.
- Never silent false-pass on low confidence.
- Document fuzzy brand behavior in README assumptions.
- Document fuzzy brand behavior in README assumptions.
- P2+: graph retry — 1 retry on transient OCR failure → local fallback → `unable_to_verify`.

---

## 7. AI-native factory requirements (P2+ target state)

> **Not client deliverables.** This section defines phased engineering depth per [ARCHITECTURE.md](ARCHITECTURE.md). Implement after P1 repo + URL satisfy §10.

### 7.1 Autonomous Agent Software Factory

The **LabelForge Factory** is the composition root that:

| Capability | Requirement |
|------------|-------------|
| Agent registry | Register agents by role with version metadata |
| Tool injection | Inject OCR, RAG retriever, rules engine, clock, logger via interfaces |
| Graph compilation | Build verification graph from declarative config (YAML/code) |
| Run lifecycle | Create `run_id`, persist state snapshots (in-memory PoC; pluggable store) |
| Policy enforcement | Block auto-approve paths; optional eval thresholds in CI (P3) |
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
    field_accuracy.py
    warning_recall.py
    latency_p95.py
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

All production code files must use [CODE_COMMENT_HEADER_TEMPLATE.md](CODE_COMMENT_HEADER_TEMPLATE.md).

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
| **Observability** | Structured logs; optional `trace_id` (logs/README, not required in UI) |
| **Testability** | Rules unit tests P1; golden eval suite P2+; ≥ 80% rules coverage aspirational |

---

## 9. Technical constraints and context

- No mandated language/framework; **recommended stack** documented in [ARCHITECTURE.md](ARCHITECTURE.md).
- Azure is agency context; prototype deploys to any HTTPS-accessible URL.
- COLA (.NET legacy) — **no direct coupling**.
- Interview time-box: **P1 ships first** (repo + URL + §10.2); factory/RAG/eval CI per §12 and [ARCHITECTURE.md](ARCHITECTURE.md).

### Recommended AI-native stack

| Layer | Technology |
|-------|------------|
| API | Python FastAPI |
| Graph | LangGraph |
| Agents/tools | LangChain or lightweight custom `IAgentNode` |
| RAG | LangChain retriever + Chroma (local) or Azure AI Search |
| OCR | Azure Document Intelligence + Tesseract fallback |
| Evals | Custom runner + optional LangSmith |
| UI | React + TypeScript |
| CI | GitHub Actions (`pytest`, `run_eval_suite.py`, deploy) |

---

## 10. Deliverables

> **Client truth lives here and in [DELIVERABLES.md](DELIVERABLES.md).** [ClientRequirement.md](ClientRequirement.md) lists exactly **two** submissions. Everything else is implementation or phased target state.

**Authoritative client list:** [ClientRequirement.md](ClientRequirement.md) § Deliverables.  
**Proof with file paths and URLs:** [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md).

**Current repository:** [github.com/monigarr/instructions](https://github.com/monigarr/instructions) — application in [`app/`](app/).  
**Deployed URL:** [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) — Render Starter, Blueprint-managed ([`render.yaml`](render.yaml)). Proof: [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md).

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
| **P2+ — craft** | No | `factory/`, `graph/`, `rag/`, `evals/` — per ARCHITECTURE.md target layout |

Omitting P2+ folders does **not** fail submission if §10.1–10.2 are met. Document factory roadmap in README approach section when P2+ is planned or partial.

### 10.4 Recommended repository contents (supports evaluation criteria — not extra client submissions)

| Artifact | Purpose |
|----------|---------|
| `fixtures/` + test labels | Client-encouraged sample labels; demo and regression |
| Verification source (any structure) | OCR/extraction, rules, batch — e.g. `src/` with factory/graph/agents/rag/rules |
| `evals/` (optional) | Quality gates; supports “correctness” and “creative problem-solving” |
| `.env.example` | Document OCR/API config without secrets |

### 10.5 Supporting documentation (this instructions repo — not submitted as deliverables)

| Artifact | Purpose |
|----------|---------|
| [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | Proof index — file locations, API endpoints, live URLs |
| [DELIVERABLES.md](DELIVERABLES.md) | Submission checklist mapped to ClientRequirement.md |
| [ClientRequirement.md](ClientRequirement.md) | Primary source of truth |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Phased target-state design (factory P2+ implemented in `app/`) |
| [PRD.md](PRD.md) | This document |

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

Evidence map: [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) §1.1 · Live demo: [labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com)

7. **Agent factory pattern** — composable agents with clear boundaries → [`app/src/factory/`](app/src/factory/)
8. **Graph orchestration** — stateful workflow, fallbacks → [`app/src/graph/`](app/src/graph/)
9. **RAG discipline** — grounded retrieval; rules own verdicts → [`app/src/rag/`](app/src/rag/)
10. **Eval culture** — golden datasets, CI gates, adversarial cases → [`app/evals/`](app/evals/)
11. **S.O.L.I.D. evidence** — interfaces, DI, OCR adapters → [`app/src/domain/interfaces.py`](app/src/domain/interfaces.py)
12. **Pragmatic shipping** — P1 live on Render; P2+ behind flags → [`render.yaml`](render.yaml), [`app/README.md`](app/README.md)

**Guidance:** **P1 satisfies ClientRequirement.md.** P2–P4 add interview craft; never block URL submission on eval CI or full graph.

---

## 12. Implementation phases

| Phase | Scope | Client / exit criteria |
|-------|-------|------------------------|
| **P0 — Foundation** | Interfaces, project skeleton, README draft | Compiles locally |
| **P1 — MVP (SUBMIT)** | Ingest → extract → structure → rules → UI; single + batch; fixtures | **Repo + URL live**; §10.2 met; P95 ≤ ~5 s documented |
| **P2 — Graph + RAG** | Factory, LangGraph, ComplianceRAGAgent, NuanceAgent | Interview craft; README approach updated |
| **P3 — Eval hardening** | Golden/adversarial suites; optional CI gates | Engineering quality; not submission blocker |
| **P4 — Stretch** | HITL node, explanations, image pre-processing | Jenny Park stretch; document if cut |

---

## 13. Assumptions and open questions

### Assumptions

- Synthetic/non-sensitive labels only in prototype.
- Application data provided alongside each label (no COLA API).
- Government warning canonical text seeded into RAG corpus and rules fixtures.
- Bold detection uses OCR/layout heuristics; behavior documented.
- LLM calls optional; deterministic rules path sufficient for MVP verdicts.

### Open questions

- Preferred batch manifest format (CSV schema vs. JSON)?
- Evaluator network restrictions for cloud OCR/LLM at demo time?

---

## 14. References

- [ClientRequirement.md](ClientRequirement.md) — primary source of truth
- [ARCHITECTURE.md](ARCHITECTURE.md) — phased target-state design (P2+ factory); P1 in §3A/§3C
- [DELIVERABLES.md](DELIVERABLES.md) — submission checklist
- [CODE_COMMENT_HEADER_TEMPLATE.md](CODE_COMMENT_HEADER_TEMPLATE.md) — file standards
- [TTB label guidance](https://www.ttb.gov) — regulatory corpus source
