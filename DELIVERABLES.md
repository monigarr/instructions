# Deliverables

**Primary source of truth:** [ClientRequirement.md](ClientRequirement.md)  
**Derived specs:** [PRD.md](PRD.md) §10 · [ARCHITECTURE.md](ARCHITECTURE.md) (phased target state)

## Document hierarchy

| Layer | Document | What it governs |
|-------|----------|-----------------|
| **Normative (client)** | [ClientRequirement.md](ClientRequirement.md) | The only authoritative **must** list |
| **Submission checklist** | This file + [PRD.md](PRD.md) §10 | What you submit and what the app must prove |
| **Target-state design** | [ARCHITECTURE.md](ARCHITECTURE.md) | How to build toward agent factory depth **after P1** — not a third deliverable |

**Ship order:** Execute **P1** first (working repo + URL + core verification). Treat LabelForge factory depth (agents, graph, RAG, evals) as **senior craft in code and README approach** — not doc checkboxes that block submission.

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

- Standalone prototype — **no COLA integration**
- Performance target: **~5 seconds or less** per label (user-perceived)
- Batch upload support for peak loads (**200–300** applications)
- UX goal: simple, obvious UI (“no hunting for buttons”)
- Network note: outbound cloud APIs may be blocked; document fallback if used
- Prototype security: no sensitive data storage; no “crazy” security anti-patterns
- Government warning validation behavior (exact text, `GOVERNMENT WARNING:` all caps and bold)
- Brand-name nuance handling (e.g., casing differences) if implemented
- Stretch vs. cut scope (e.g., imperfect photos — optional per Jenny Park)

**Repository should include:**

- Application source (UI, verification logic, AI/OCR integration)
- Sample or synthetic **test labels** (client encourages additional labels; AI-generated OK)
- Fixture application data matching sample label fields
- `.env.example` or equivalent — **no secrets committed**

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

- [ ] Agent uploads **label artwork** and provides **application data** (form, file, or equivalent)
- [ ] System **extracts** text/fields from the label (AI/OCR or equivalent — language/framework choice is yours)
- [ ] System **compares** extracted values to application data **field by field**
- [ ] System reports **match**, **mismatch**, or **unable to verify** (with reason) per field and per label
- [ ] Human compliance agent retains final judgment — tool **assists**, does not replace legal review

### 2.2 TTB label fields (minimum)

Handle labels with information like the client’s **distilled spirits example**, plus common elements listed in ClientRequirement.md:

| Field | Example / note |
|-------|----------------|
| Brand name | `OLD TOM DISTILLERY` — consider casing/punctuation nuance (Dave Morrison) |
| Class / type | `Kentucky Straight Bourbon Whiskey` |
| Alcohol content | `45% Alc./Vol. (90 Proof)` |
| Net contents | `750 mL` |
| Government warning | Standard TTB warning text — **exact**, word-for-word; `GOVERNMENT WARNING:` **all caps and bold** (Jenny Park) |
| Bottler/producer name and address | Where applicable on label type |
| Country of origin | For imports, where applicable |

*Client encourages additional test labels beyond the single example.*

### 2.3 Performance (Sarah Chen — adoption threshold)

- [ ] **~5 seconds or less** per label for the core verification path (user-perceived)
- [ ] Prior vendor pilot failed at 30–40 s — speed is **non-negotiable** for credibility

### 2.4 Batch processing (Sarah Chen / Janet Seattle office)

- [ ] Support **batch uploads** — not only one label at a time
- [ ] Target scale: **200–300** label applications in peak scenarios
- [ ] Batch progress and summary (passed / failed / needs review)

### 2.5 User experience (Sarah Chen / Dave Morrison)

- [ ] **Clean, obvious UI** — suitable for users with low tech comfort (benchmark: approachable to a non-technical senior user)
- [ ] No hidden critical actions; minimal training to complete a verification
- [ ] Side-by-side or clear view of **application value vs. label value** for mismatches
- [ ] Tool must **not** make the workflow harder than manual review (Dave Morrison)

### 2.6 Error handling

- [ ] Reject or flag bad/unreadable uploads with **actionable** messages
- [ ] Do not silently pass low-confidence extractions
- [ ] Document behavior for edge cases in README assumptions

---

## 3. Constraints the deliverables must respect

| Constraint | Source | Deliverable implication |
|------------|--------|-------------------------|
| **Standalone PoC** | Marcus Williams | No COLA integration; no dependency on COLA auth |
| **No sensitive data** | Marcus Williams | Use synthetic/sample labels; no real applicant PII in repo or demo |
| **Prototype security** | Marcus Williams | Sensible defaults; document production gaps — don’t “do anything crazy” |
| **Firewall / egress** | Marcus Williams | Cloud ML APIs may fail on agency networks; document dependency or provide offline-capable path |
| **Free choice of stack** | Technical Requirements | Any language/framework; justify choices in README approach section |
| **Working core over ambition** | Evaluation Criteria | Ship complete single + batch + field verification before stretch features |
| **Document trade-offs** | Evaluation Criteria | README lists limitations (e.g., imperfect photos, bold detection heuristics) |

### Explicitly out of scope (do not block submission on these)

- COLA direct integration  
- Production FedRAMP / full federal compliance deployment  
- Full legal adjudication of every borderline case  
- Perfect handling of glare, angles, bad lighting *(stretch — Jenny Park)*  

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

- [ ] Public (or accessible) GitHub repo with all source code  
- [ ] README: install, run, sample verification steps  
- [ ] README: approach, tools, assumptions, trade-offs, limitations  
- [ ] Test labels + fixture data included or generated via documented script  
- [ ] No secrets in git; `.env.example` provided if needed  
- [ ] Core requirements §2 satisfied in running app  

### Deployment

- [ ] Live URL in README (and submission form if applicable)  
- [ ] Single-label verification works on deployed URL  
- [ ] Batch verification works on deployed URL  
- [ ] URL stable enough for evaluator demo session  

### Requirements traceability

- [ ] ≤ ~5 s per label validated on representative samples (note test conditions in README)  
- [ ] Batch upload tested at non-trivial volume (document max tested batch size)  
- [ ] Government warning rule demonstrated (including rejection of wrong-case warning if feasible)  
- [ ] Standalone — no COLA references as runtime dependency  

---

## 6. Supporting artifacts (this instructions repo — not client-required)

These documents **support** building and defending the solution; they are **not** substitutes for §1.

| Artifact | Purpose |
|----------|---------|
| [ClientRequirement.md](ClientRequirement.md) | Primary requirements and stakeholder context |
| [PRD.md](PRD.md) | Product requirements and acceptance criteria |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, AI factory pattern, trade-offs |
| [CODE_COMMENT_HEADER_TEMPLATE.md](CODE_COMMENT_HEADER_TEMPLATE.md) | Code file header standard for application repo |

**Phased implementation (not client-required):**

| Phase | Ship when | Client coverage |
|-------|-----------|-----------------|
| **P1 — MVP** | **Submit interview** | Single + batch verify, TTB fields, ≤ ~5 s, simple UI, README approach |
| **P2+ — Factory depth** | After P1 stable | RAG, full graph, eval CI — interview craft per [ARCHITECTURE.md](ARCHITECTURE.md) |

Agent factory, RAG, graphs, and evals may appear **internally** or in README approach documentation as long as **§1–§3** are satisfied in the shipped repository and deployed URL.

---

## 7. References

- [ClientRequirement.md](ClientRequirement.md) — **authoritative** deliverables, constraints, evaluation criteria  
- [TTB label guidance](https://www.ttb.gov) — regulatory context for label elements  

*Last updated: 2026-06-10*
