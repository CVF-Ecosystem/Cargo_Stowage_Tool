# Module Catalog

Machine-readable source: `docs/catalog/MODULE_REGISTRY.json`

Status: GOVERNED

## Metrics

- Total modules: 7
- Enforced: 5
- Partial: 0
- Contract-only: 2
- Stub: 0
- Deprecated: 0

| id | status | path | evidence | description |
|---|---|---|---|---|
| scst-api | ENFORCED | `services/backend/app/api` | services/backend/app/api/routes.py; backend tests and launcher-smoke.log | Local validate/demo/reference APIs plus CSV preview and immutable snapshot save/list/re-evaluated open. |
| scst-contract | CONTRACT_ONLY | `contracts/openapi.json` | tooling/export_contract.py; contract-hashes.txt and reviewer-source-manifest.json | OpenAPI/types accepting scst.m1.v1 and scst.m2a.v1; backend conditional invariants retained. |
| scst-domain | ENFORCED | `services/backend/app/domain` | tests/backend/test_validation.py; docs/reviews/SCST_M1_EVIDENCE/reviewer-pytest.log (51 pass); reviewer-backend.json (498 checks); tests/backend/test_vinafco.py; docs/reviews/SCST_VINAFCO268_REVIEW.md; tests/backend/test_m2a.py; docs/reviews/SCST_M2A_REVIEW.md | Versioned v1/v2 BOX/single-layer model, empty drafts, exact mm/g and reference-bound mixed plans. |
| scst-frontend | ENFORCED | `apps/frontend/src` | tests/browser/workspace.spec.ts; docs/reviews/SCST_M1_EVIDENCE/reviewer-browser.log (5 pass); tests/browser/vinafco.spec.ts; docs/reviews/SCST_VINAFCO268_EVIDENCE/reviewer-browser.log; tests/browser/m2a.spec.ts; docs/reviews/SCST_M2A_EVIDENCE/reviewer-browser.log | Checked/draft manual/CSV/save-open workspace, Three/SVG/reference modes and async error recovery. |
| scst-launcher | ENFORCED | `tooling` | tests/launcher_smoke.py; tests/cold_start_smoke.py; launcher-smoke.log; cold-start.log | Windows local setup, loopback server and contract generation. |
| scst-local-data | ENFORCED | `services/backend/app/adapters` | tests/backend/test_m2a.py; tests/m2a_restart_smoke.py; docs/reviews/SCST_M2A_REVIEW.md | Atomic strict CSV preview and immutable local SQLite snapshot/re-evaluation; no operational approval. |
| scst-vessel-reference | CONTRACT_ONLY | `services/backend/data/vessels/vinafco268` | docs/reviews/SCST_VINAFCO268_ASSESSMENT.md; docs/reviews/SCST_VINAFCO268_EVIDENCE/source-asset-validation.json | Sanitized technical profile with provenance/estimates/nulls and illustrative GLB; source PDF remains local. |
