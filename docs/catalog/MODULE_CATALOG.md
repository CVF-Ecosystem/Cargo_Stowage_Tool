# Module Catalog

Machine-readable source: `docs/catalog/MODULE_REGISTRY.json`

Status: GOVERNED

## Metrics

- Total modules: 6
- Enforced: 4
- Partial: 0
- Contract-only: 2
- Stub: 0
- Deprecated: 0

| id | status | path | evidence | description |
|---|---|---|---|---|
| scst-api | ENFORCED | `services/backend/app/api` | services/backend/app/api/routes.py; backend tests and launcher-smoke.log | Local health/demo/validate and sanitized vessel profile/case/GLB API; no source PDF served. |
| scst-contract | CONTRACT_ONLY | `contracts/openapi.json` | tooling/export_contract.py; contract-hashes.txt and reviewer-source-manifest.json | OpenAPI and derived frontend types for scst.m1.v1. |
| scst-domain | ENFORCED | `services/backend/app/domain` | tests/backend/test_validation.py; docs/reviews/SCST_M1_EVIDENCE/reviewer-pytest.log (51 pass); reviewer-backend.json (498 checks); tests/backend/test_vinafco.py; docs/reviews/SCST_VINAFCO268_REVIEW.md | BOX/single-layer integer geometry/rules; synthetic default and profile-bound mixed reference plans. |
| scst-frontend | ENFORCED | `apps/frontend/src` | tests/browser/workspace.spec.ts; docs/reviews/SCST_M1_EVIDENCE/reviewer-browser.log (5 pass); tests/browser/vinafco.spec.ts; docs/reviews/SCST_VINAFCO268_EVIDENCE/reviewer-browser.log | Checked/draft workspace, Three/SVG and optional VINAFCO268 GLB/case view with recovery. |
| scst-launcher | ENFORCED | `tooling` | tests/launcher_smoke.py; tests/cold_start_smoke.py; launcher-smoke.log; cold-start.log | Windows local setup, loopback server and contract generation. |
| scst-vessel-reference | CONTRACT_ONLY | `services/backend/data/vessels/vinafco268` | docs/reviews/SCST_VINAFCO268_ASSESSMENT.md; docs/reviews/SCST_VINAFCO268_EVIDENCE/source-asset-validation.json | Sanitized technical profile with provenance/estimates/nulls and illustrative GLB; source PDF remains local. |
