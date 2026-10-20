> **Archived 2026-10-19.** Historical document retained for traceability. It predates the repository consolidation; canonical docs are [README](../README.md) | [APPROACH](../APPROACH.md) | [SECURITY_ACCESSIBILITY](../SECURITY_ACCESSIBILITY.md) | [PRD](../PRD.md) | [ClientRequirement](../ClientRequirement.md). Relative links inside this file may be stale.

# Deliverables

**For code reviewers:** [README.md](README.md) â†’ [**ONBOARDING.md**](ONBOARDING.md) (engineers) Â· [**REVIEWER_GUIDE.md**](REVIEWER_GUIDE.md) (3-min demo) â†’ [**DELIVERABLES_PROOF.md**](DELIVERABLES_PROOF.md) (proof index) â†’ this checklist.

**Primary source of truth:** [ClientRequirement.md](ClientRequirement.md)  
**Proof index:** [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) â€” file paths + live URLs  
**Derived specs:** [PRD.md](PRD.md) Â§10 Â· [ARCHITECTURE.md](ARCHITECTURE.md) (phased target state)

## Document hierarchy

| Layer | Document | What it governs |
|-------|----------|-----------------|
| **Normative (client)** | [ClientRequirement.md](ClientRequirement.md) | The only authoritative **must** list |
| **Proof** | [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | Evidence map â€” repo paths, endpoints, URLs |
| **Submission checklist** | This file + [PRD.md](PRD.md) Â§10 | What you submit and what the app must prove |
| **Target-state design** | [ARCHITECTURE.md](ARCHITECTURE.md) | Agent factory depth in `app/` (P2+ shipped in code) |

**Ship order:** Execute **P1** first (working repo + URL + core verification). Treat LabelForge factory depth (agents, graph, RAG, evals) as **senior craft in code and README approach** â€” not doc checkboxes that block submission.

This checklist defines what you **must submit** and what the **delivered prototype must do**. PRD and ARCHITECTURE support implementation; they do **not** replace the two client-required submissions.

---

## 1. Required submissions (ClientRequirement.md)

These are the **only mandatory deliverables** stated by the client.

### 1.1 Source code repository (GitHub or similar)

| Item | Client requirement | Acceptance criteria |
|------|------------------|---------------------|
| **All source code** | Complete prototype codebase | Builds and runs locally; implements label verification end-to-end |
| **README** | Setup and run instructions | Evaluator can clone, install, run app, and verify at least one sample label without contacting you |
| **Approach documentation** | Brief documentation of approach, tools used, assumptions made | README (or linked doc) covers: stack choices, how verification works, known limits, trade-offs |

**README must also document** (derived from client constraints):

- Standalone prototype â€” **no COLA integration**
- Performance target: **~5 seconds or less** per label (user-perceived)
- Batch upload support for peak loads (**200â€“300** applications)
- UX goal: simple, obvious UI (â€œno hunting for buttonsâ€)
- Network note: outbound cloud APIs may be blocked; document fallback if used
- Prototype security: no sensitive data storage; no â€œcrazyâ€ security anti-patterns
- Government warning validation behavior (exact text, `GOVERNMENT WARNING:` all caps and bold)
- Brand-name nuance handling (e.g., casing differences) if implemented
- Stretch vs. cut scope (e.g., imperfect photos â€” optional per Jenny Park)

**Repository should include:**

- Application source (UI, verification logic, AI/OCR integration)
- Sample or synthetic **test labels** (client encourages additional labels; AI-generated OK)
- Fixture application data matching sample label fields
- `.env.example` or equivalent â€” **no secrets committed**

### 1.2 Deployed application URL

| Item | Client requirement | Acceptance criteria |
|------|------------------|---------------------|
| **Working prototype** | URL evaluators can access and test | Public HTTPS link; core flows work without local setup |
| **Hands-on test** | Same capabilities as local | Single-label verify + batch upload + view results |

**Deployed app must demonstrate:**

1. Upload label image + application/form data  
2. Compare label to application and show per-field outcomes  
3. Batch processing (not strictly one-at-a-time only)  
4. Clear mismatch display and usable error handling  

Document in README: demo URL, any cold-start delay, rate limits, or API keys needed for full functionality.

---

## 2. Functional requirements the deliverables must satisfy

Derived from [ClientRequirement.md](ClientRequirement.md) stakeholder interviews and TTB context. **The repository and deployed URL together must prove these.**

### 2.1 Core workflow

- [x] Agent uploads **label artwork** and provides **application data** (form, file, or equivalent) â€” [`app/ui/src/App.tsx`](app/ui/src/App.tsx), `POST /verify`
- [x] System **extracts** text/fields from the label (AI/OCR or equivalent â€” language/framework choice is yours) â€” [`app/src/adapters/ocr/`](app/src/adapters/ocr/), [`app/src/structure/field_mapper.py`](app/src/structure/field_mapper.py)
- [x] System **compares** extracted values to application data **field by field** â€” [`app/src/rules/field_rules.py`](app/src/rules/field_rules.py)
- [x] System reports **match**, **mismatch**, or **unable to verify** (with reason) per field and per label â€” [`app/src/domain/models.py`](app/src/domain/models.py)
- [x] Human compliance agent retains final judgment â€” tool **assists**, does not replace legal review â€” `needs_review` verdicts, UI footer

### 2.2 TTB label fields (minimum)

Handle labels with information like the clientâ€™s **distilled spirits example**, plus common elements listed in ClientRequirement.md:

| Field | Example / note |
|-------|----------------|
| Brand name | `OLD TOM DISTILLERY` â€” consider casing/punctuation nuance (Dave Morrison) |
| Class / type | `Kentucky Straight Bourbon Whiskey` |
| Alcohol content | `45% Alc./Vol. (90 Proof)` |
| Net contents | `750 mL` |
| Government warning | Standard TTB warning text â€” **exact**, word-for-word; `GOVERNMENT WARNING:` **all caps and bold** (Jenny Park) |
| Bottler/producer name and address | Where applicable on label type |
| Country of origin | For imports, where applicable |

*Client encourages additional test labels beyond the single example.*

### 2.3 Performance (Sarah Chen â€” adoption threshold)

- [x] **~5 seconds or less** per label for the core verification path (user-perceived) â€” `elapsed_ms` in API; eval P95 **~11.6 ms** on golden fixtures locally (sidecar OCR path; [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) Â§2.3)
- [x] Prior vendor pilot failed at 30â€“40 s â€” speed is **non-negotiable** for credibility â€” documented in [`app/README.md`](app/README.md) Â§ Performance

### 2.4 Batch processing (Sarah Chen / Janet Seattle office)

- [x] Support **batch uploads** â€” not only one label at a time â€” [`app/src/api/main.py`](app/src/api/main.py) `POST /batch/verify`
- [x] Target scale: **200â€“300** label applications in peak scenarios â€” async batch with concurrency cap ([`app/src/verify/batch_service.py`](app/src/verify/batch_service.py))
- [x] Batch progress and summary (passed / failed / needs review) â€” `GET /batch/{batch_id}`, batch tab UI

### 2.5 User experience (Sarah Chen / Dave Morrison)

- [x] **Clean, obvious UI** â€” suitable for users with low tech comfort (benchmark: approachable to a non-technical senior user) â€” [`app/ui/src/App.tsx`](app/ui/src/App.tsx)
- [x] No hidden critical actions; minimal training to complete a verification â€” two-tab layout, primary action buttons
- [x] Side-by-side or clear view of **application value vs. label value** for mismatches â€” verdict table columns
- [x] Tool must **not** make the workflow harder than manual review (Dave Morrison) â€” single-screen flow

### 2.6 Error handling

- [x] Reject or flag bad/unreadable uploads with **actionable** messages â€” [`app/src/ingest/validator.py`](app/src/ingest/validator.py), `unreadable_blank` fixture
- [x] Do not silently pass low-confidence extractions â€” `unable_to_verify` + confidence checks in rules
- [x] Document behavior for edge cases in README assumptions â€” [`app/README.md`](app/README.md) Â§ Assumptions & trade-offs

---

## 3. Constraints the deliverables must respect

| Constraint | Source | Deliverable implication |
|------------|--------|-------------------------|
| **Standalone PoC** | Marcus Williams | No COLA integration; no dependency on COLA auth |
| **No sensitive data** | Marcus Williams | Use synthetic/sample labels; no real applicant PII in repo or demo |
| **Prototype security** | Marcus Williams | Sensible defaults; document production gaps â€” donâ€™t â€œdo anything crazyâ€ |
| **Firewall / egress** | Marcus Williams | Cloud ML APIs may fail on agency networks; document dependency or provide offline-capable path |
| **Free choice of stack** | Technical Requirements | Any language/framework; justify choices in README approach section |
| **Working core over ambition** | Evaluation Criteria | Ship complete single + batch + field verification before stretch features |
| **Document trade-offs** | Evaluation Criteria | README lists limitations (e.g., imperfect photos, bold detection heuristics) |

### Explicitly out of scope (do not block submission on these)

- COLA direct integration  
- Production FedRAMP / full federal compliance deployment  
- Full legal adjudication of every borderline case  
- Perfect handling of glare, angles, bad lighting *(stretch â€” Jenny Park)*  

---

## 4. How evaluators will judge your deliverables

From [ClientRequirement.md](ClientRequirement.md) **Evaluation Criteria**:

1. **Correctness and completeness** of core requirements  
2. **Code quality and organization**  
3. **Appropriate technical choices** for the scope  
4. **User experience and error handling**  
5. **Attention to requirements** (especially **5 s speed**, **batch**, **government warning exactness**, **simple UI**)  
6. **Creative problem-solving** (e.g., fuzzy brand match, batch UX, offline OCR fallback)  

**Client guidance:** A **working core application with clean code** is preferred over ambitious but incomplete features. Document trade-offs and limitations.

---

## 5. Submission checklist

Use this before you submit the interview.

### Repository

- [x] Public (or accessible) GitHub repo with all source code â€” [github.com/monigarr/instructions](https://github.com/monigarr/instructions)  
- [x] README: install, run, sample verification steps â€” [`app/README.md`](app/README.md)  
- [x] README: approach, tools, assumptions, trade-offs, limitations â€” [`app/README.md`](app/README.md) Â§ Approach  
- [x] Test labels + fixture data included or generated via documented script â€” [`app/fixtures/`](app/fixtures/), [`app/scripts/generate_fixtures.py`](app/scripts/generate_fixtures.py)  
- [x] No secrets in git; `.env.example` provided if needed â€” [`app/.env.example`](app/.env.example)  
- [x] Core requirements Â§2 satisfied in running app â€” see [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md)  

### Deployment

- [x] Live URL in README â€” [https://labelforge-w32d.onrender.com](https://labelforge-w32d.onrender.com) ([`app/README.md`](app/README.md), [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md))  
- [x] Single-label verification works on deployed URL â€” smoke tested 2026-06-09  
- [x] Batch verification works on deployed URL â€” 2-label async batch completed on production  
- [x] URL stable for evaluator demo â€” Render Starter (always-on)

### Requirements traceability

- [x] â‰¤ ~5 s per label validated on representative samples (note test conditions in README) â€” eval suite + `elapsed_ms`  
- [x] Batch upload tested at non-trivial volume â€” **34**-entry demo manifest + **300** scale fixtures; UI quick-starts for 200/300; load script ([DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) Â§2.4)
- [x] 30 golden evals with CI regression gate â€” [`app/evals/`](app/evals/), [`.github/workflows/ci.yml`](.github/workflows/ci.yml); **28** pytest tests across 6 modules
- [x] Government warning rule demonstrated (including rejection of wrong-case warning if feasible) â€” `test_warning_title_case_rejected` in [`app/tests/test_rules.py`](app/tests/test_rules.py)  
- [x] Standalone â€” no COLA references as runtime dependency  

---

## 6. Supporting artifacts (this instructions repo â€” not client-required)

These documents **support** building and defending the solution; they are **not** substitutes for Â§1.

| Artifact | Purpose |
|----------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Primary requirements and stakeholder context |
| [DELIVERABLES_PROOF.md](DELIVERABLES_PROOF.md) | Proof index â€” file paths, endpoints, live URLs |
| [PRD.md](PRD.md) | Product requirements and acceptance criteria |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, AI factory pattern, trade-offs |
| [app/DEPLOY.md](app/DEPLOY.md) | Deployment guide (Docker, Render, Railway) |
| [CODE_COMMENT_HEADER_TEMPLATE.md](CODE_COMMENT_HEADER_TEMPLATE.md) | Code file header standard for application repo |

**Phased implementation (not client-required):**

| Phase | Ship when | Client coverage |
|-------|-----------|-----------------|
| **P1 â€” MVP** | **Submit interview** | Single + batch verify, TTB fields, â‰¤ ~5 s, simple UI, README approach |
| **P2+ â€” Factory depth** | After P1 stable | RAG, full graph, 30 golden eval CI â€” interview craft per [ARCHITECTURE.md](ARCHITECTURE.md) |

Agent factory, RAG, graphs, and evals may appear **internally** or in README approach documentation as long as **Â§1â€“Â§3** are satisfied in the shipped repository and deployed URL.

---

## 7. References

- [ClientRequirement.md](ClientRequirement.md) â€” **authoritative** deliverables, constraints, evaluation criteria  
- [TTB label guidance](https://www.ttb.gov) â€” regulatory context for label elements  

*Last updated: 2026-07-08*
