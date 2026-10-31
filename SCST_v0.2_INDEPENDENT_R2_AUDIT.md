# Steel Cargo Stowage Tool — Independent Audit R2

**Audit date:** 2026-10-31  
**Reviewed:** `CVF_Steel_Cargo_Independent_Review_R1.docx`; `Steel_Cargo_Stowage_Tool_v0.2_Official_Local_Agent_Package.zip`  
**Verdict:** `CONDITIONAL_ACCEPT_FOR_LOCAL_AGENT_REVIEW`; **not** `IMPLEMENTATION_FREEZE` or `OPERATIONAL_READY`.

## 1. Verification performed

- Extracted the v0.2 ZIP and inspected its master spec, dispositions R01–R14, data schemas, reference Python validator, test suite, roadmap and CVF adapter contract.
- Ran `python tooling/verify_package.py` on the extracted package: **65/65** hashes matched.
- Ran `python tests/run_all.py --output /mnt/data/review_v02/independent_test_evidence`: **86/86 PASS**, zero failures, errors or skips. Environment: Python 3.12, jsonschema 4.26.0. These are synthetic contract checks; **not** engineering/solver/FE/BE/CVF runtime tests.
- Verified the nested historic v0.1 ZIP equals the uploaded v0.1 ZIP byte-for-byte. The R1 DOCX nested in v0.2 is **not byte-identical** to the R1 DOCX uploaded in this conversation, although extracted paragraphs and tables match. Source provenance should be reconciled if the package claims byte-exact historical reproduction.
- Ran two additional schema probes: a `testOnly=false` VERIFIED manifest with `cargoUnits[0].massBasis=SYNTHETIC`, and a `testOnly=false` vessel profile with synthetic cargo-limit evidence, both passed **JSON Schema only**. This is a pending **backend domain acceptance invariant**, not evidence of an exploitable application (there is no production backend in the ZIP).

## 2. Accepted architecture

- Local-first modular monolith: separate React/Three.js frontend and Python/backend modules; no microservices.
- Immutable vessel/hold/manifest/case/plan content and content-hash-linked receipts; a separate lifecycle/event model.
- No AI-issued verification, limit changes, selection, or field authorization. A deterministic cargo validation layer remains authoritative even on CVF ALLOW.
- Separate core gate G4a from optional Agent/CVF gate G4b.
- Scope-limited geometry and explicit review coverage without claiming hull strength, vessel stability, lashing, crane access or sequence have been evaluated.

## 3. Open issues before freeze

| ID | Priority | Finding | Required next action |
|---|---|---|---|
| R2-01 | P0 owner decision | v0.2 narrows pilot to **one BOX, confirmed empty target hold**, and layered stacking requires separately reviewed profiles. This is a deliberate scope tradeoff not yet explicitly approved by owner. | Obtain explicit owner acceptance; set first-layer feasibility vs multi-layer value milestone. |
| R2-02 | P0 implementation contract | Synthetic evidence and masses can fit schemas with `testOnly=false`; reference validator never authorizes operational data. | Define and test backend invariant that prohibits SYNTHETIC sources and unverified evidence in verified operational records; preserve draft data separately. |
| R2-03 | P0 role model | v0.2 says one local operator but also requires distinct selection and professional field-review authority. | Specify whether engineering review is an authenticated tool role or an externally signed evidence record; link real identity, scope and exact plan hash. |
| R2-04 | P1 real-world data | v0.2 allows integer kg/mm; fractional kg is correctly blocked rather than rounded down, but actual manifests may require finer mass precision. | Sample real manifests and decide integer grams or fixed-point decimal with a conversion/rounding contract before mass schema is widely pinned. |
| R2-05 | P1 usability/field value | Full-base-support rectangular envelopes are an abstraction, not actual contact/anti-roll capacity for bundled pipes/rebar; no actual approved profile supplied. | Obtain at least one reviewed support profile and two or more field-informed stacking cases. Never label 3D fit as certified stowage. |
| R2-06 | P1 provenance | DOCX in v0.2 `history/` differs in raw bytes from separately uploaded R1 despite extracted text equality. | Document re-export/transformation and authoritative source SHA; do not claim byte-identical R1 history without evidence. |
| R2-07 | P1 runtime | 86 tests validate only the package's reference code; LAT-001…025, actual solver, auth, DB, UI and CVF bridge remain not run. | Require commands, commits, input/ref hashes, expected/actual and logs; keep gates pending until implementation tests pass. |
| R2-08 | P1 provenance | Final manifest units cite sourceLineId plus overall source; per-field OCR-to-confirmed-value traceability is specified in prose but not proven as an immutable link in the package. | Specify/test resolution from each verified critical value to draft field, source span and confirmation receipt in backend persistence. |

## 4. Disposition of R1

The 14 R1 findings are materially **addressed at the level of design/spec or consciously limited by scope**. This does **not** mean they are closed by production test. High-impact corrected areas: GT/DWT/payload separation (R01), explicit empty hold boundary (R02), versioned support profiles (R03), separated rule outcomes/decision states (R04), BOX geometry conventions (R05), immutable content hashes (R06), cargo/dunnage budget (R07), solver proof statuses (R08), manifest partition checks (R09), incomplete draft model (R10), certificate effective dates (R11), proposed local auth/CVF bridge (R12), rule sources/applicability (R13), and improved LAT/gate tests (R14).

## 5. Gate decision and handoff

**Approve:** v0.2 as local-agent design input for code skeleton, ingestion/draft prototype, domain validator, API contract, hash/ref implementation and independent test harness.

**Do not approve yet:** operational cargo plan, production optimizer, multi-tier placement recommendations, real CVF-enabled mutation, or engineering field clearance.

**Agent local first return:** `LOCAL_DESIGN_REVIEW.md`, `OPEN_DECISIONS.md`, updated test matrix for R2-01…R2-08, and exact source/build/runtime evidence. No silent CVF core changes. Owner approves narrowed pilot scope and role model. Technical reviewers supply actual constraints and acceptance criteria for stacking and voyage cargo allowance.

## 6. Evidence boundaries

`verify_package` demonstrates hashes in the supplied checksum manifest match the supplied files, not authorship. `86/86 PASS` demonstrates synthetic reference checks only. The additional two probes demonstrate schema acceptance, not operational permission. The package itself states `operationalEligible=false`. No field or production readiness assertion is made.
