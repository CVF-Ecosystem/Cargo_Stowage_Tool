# Module Catalog

Machine-readable source: `docs/catalog/MODULE_REGISTRY.json`

Status: GOVERNED

## Metrics

- Total modules: 10
- Enforced: 7
- Partial: 0
- Contract-only: 3
- Stub: 0
- Deprecated: 0

| id | status | path | evidence | description |
|---|---|---|---|---|
| scst-api | ENFORCED | `services/backend/app/api` | services/backend/app/api/routes.py; backend tests and launcher-smoke.log; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md; docs/reviews/SCST_M2C_REVIEW.md | Local validate/demo/reference APIs plus CSV preview and immutable snapshot save/list/re-evaluated open. Pipe-source library and explicit preview preservecurrentcontext. ExplicitplannerpreviewAPI withindependentcandidate validation. M2c exact read-only A/B comparison and baseline/restore UI integration. |
| scst-comparison | ENFORCED | `services/backend/app/domain/comparison` | tests/backend/test_m2c.py; tests/browser/m2c.spec.ts; docs/reviews/SCST_M2C_REVIEW.md | Independent A/B evaluation, complete ID/context/placement changes and integer deltas, no storage writes or ranking. |
| scst-contract | CONTRACT_ONLY | `contracts/openapi.json` | tooling/export_contract.py; contract-hashes.txt and reviewer-source-manifest.json; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md; docs/reviews/SCST_M2C_REVIEW.md | OpenAPI/types for M1/M2a/pipe-list versions; conditional backendsourcebindings and limits. M2c exact read-only A/B comparison and baseline/restore UI integration. |
| scst-domain | ENFORCED | `services/backend/app/domain` | tests/backend/test_validation.py; docs/reviews/SCST_M1_EVIDENCE/reviewer-pytest.log (51 pass); reviewer-backend.json (498 checks); tests/backend/test_vinafco.py; docs/reviews/SCST_VINAFCO268_REVIEW.md; tests/backend/test_m2a.py; docs/reviews/SCST_M2A_REVIEW.md; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md; docs/reviews/SCST_M2C_REVIEW.md | Versioned v1/v2≤200 and fixedsource1076 BOX/single-layer model, registrybindings, exactµm/mm/g, fullcount bounded diagnostics. M2c exact read-only A/B comparison and baseline/restore UI integration. |
| scst-frontend | ENFORCED | `apps/frontend/src` | tests/browser/workspace.spec.ts; docs/reviews/SCST_M1_EVIDENCE/reviewer-browser.log (5 pass); tests/browser/vinafco.spec.ts; docs/reviews/SCST_VINAFCO268_EVIDENCE/reviewer-browser.log; tests/browser/m2a.spec.ts; docs/reviews/SCST_M2A_EVIDENCE/reviewer-browser.log; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md; docs/reviews/SCST_M2C_REVIEW.md; docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md | Checked/draft manual/CSV/save-open workspace, Three/SVG/reference modes and async error recovery. Sourcegroupfilter/50rowpagination and source/counter/exactgeometry support. M2bpreview/apply/reasons/roundedmass andimmediateviewercargo. M2c exact read-only A/B comparison and baseline/restore UI integration. Practical kg/cm/m presentation and explicit-field edits preserve exact untouched data. |
| scst-launcher | ENFORCED | `tooling` | tests/launcher_smoke.py; tests/cold_start_smoke.py; launcher-smoke.log; cold-start.log | Windows local setup, loopback server and contract generation. |
| scst-local-data | ENFORCED | `services/backend/app/adapters` | tests/backend/test_m2a.py; tests/m2a_restart_smoke.py; docs/reviews/SCST_M2A_REVIEW.md; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md | Atomic strict CSV preview and immutable local SQLite snapshot/re-evaluation; no operational approval. Fixedhashpipe registry reused by model/preview; genericCSV still200. |
| scst-pipe-source | CONTRACT_ONLY | `services/backend/data/pipe_list` | docs/reviews/SCST_PIPE_LIST_ASSESSMENT.md; tests/backend/test_pipe_list.py; docs/reviews/SCST_M2B_REVIEW.md | 31groups/1076bundles, exactµm/K×Lgrams, sourcehash/row/warnings; no measuredgeometry or operationalapproval. |
| scst-planner | ENFORCED | `services/backend/app/domain/planner` | tests/backend/test_m2b.py; tests/browser/m2b.spec.ts; docs/reviews/SCST_M2B_REVIEW.md | Deterministic guillotinepreview/completeunplacedreasons; integergramcapacity, conservativegrid andexactµm validation; nooptimality/operationalclaim. |
| scst-vessel-reference | CONTRACT_ONLY | `services/backend/data/vessels/vinafco268` | docs/reviews/SCST_VINAFCO268_ASSESSMENT.md; docs/reviews/SCST_VINAFCO268_EVIDENCE/source-asset-validation.json; docs/reviews/SCST_PIPE_LIST_REVIEW.md; docs/reviews/SCST_M2B_REVIEW.md | Sanitized technical profile with provenance/estimates/nulls and illustrative GLB; source PDF remains local. |
