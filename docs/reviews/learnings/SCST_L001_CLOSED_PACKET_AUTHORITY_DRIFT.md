# Project Learning Record - SCST-L001

Status: CANDIDATE
Source project: Cargo_Stowage_Tool
Source revision: 2f29a1ae5f0d10a0318055c92a8aceefe3388e14
Updated: 31-10-2026

## Trigger / Observation

Work order `SCST_M1_SKELETON` was dispatched at `f2b688e` with coverage authority bound to the live roadmap section "## Phạm vi và đầu ra từng mốc" (sha256 `560ba09f…`). After the work order closed, commit `2f29a1a` edited that section. A direct coverage check of the closed work order then returned `COV_AUTHORITY_STALE`.

Expected: a closed packet stays verifiable against the criteria it was dispatched with. Observed: the validator reads only the current file and the registry allows one path per milestone ID, so there is no way to point at the dispatch-time revision. Phase gates did not catch this because closed, unchanged packets are not re-checked. Classification: missing control (machine gate gap), plus a local application error (the editing agent did not check which packets referenced the section).

## Source / Evidence

- Reproduction: `validate_file(root, "docs/work_orders/SCST_M1_SKELETON.md")` from `scripts/cvf_gates/cvf_milestone_coverage.py` returned `['COV_AUTHORITY_STALE']` before the repair. Independently observed by an external reviewer and by the local agent (source-inspected and executed).
- Validator lines: `cvf_milestone_coverage.py` reads `section(read_file(root, authority["path"]))` and requires the registry binding to equal the block path/heading.

## Project Action / Verification

Local repair: froze the dispatch revision as `docs/roadmaps/snapshots/SCST_ROADMAP_v0.2_at_f2b688e.md` (from `git show f2b688e`, section bytes unchanged), registered `SCST-ROADMAP-AT-F2B688E`, and repointed only `milestone.id` and `authority.path` in the closed work order, keeping the original hash. A direct validation now returns no issues. Rule for this project: before editing a registered authority section, list the work orders that bind it, and freeze a snapshot for any closed one.

## Parent Value / Dedup

Owner: CVF milestone coverage machine contract (`CVF-DG-COV-01`). Proposed benefit: allow an authority reference to carry a revision (commit or blob) or a frozen snapshot, so closed packets survive later edits of the live roadmap without editing their block; optionally warn when a changed authority section is still bound by other packets. Parent reviewer decides.

## Feedback State And Links

| Boundary | State | Evidence / owner / next move |
|---|---|---|
| Project finding/action | APPLIED_LOCALLY | snapshot + registry entry + work order note; direct validation clean |
| Parent value decision | PENDING_PARENT_ASSESSMENT | intake `docs/learning_intake/SCST-L001.intake.json` |
| Parent implementation | NOT_IMPLEMENTED | — |
| Return to source project | NOT_RETURNED | — |
| Source project adoption | NOT_APPLIED | — |

## Claim Boundary

Proves only that this one closed packet validates again against a frozen copy of its dispatch-time section. No claim about other projects, hosted CI, or parent acceptance.
