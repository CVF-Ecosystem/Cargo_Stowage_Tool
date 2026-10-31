# CVF Project Bootstrap Log

## 1. Record Metadata
- Record ID: BOOTSTRAP-20261031-Cargo_Stowage_Tool
- Date: 2026-10-31
- Prepared By:
- Reviewed By:
- CVF Core Commit: c4c8767ac8861854f40d466ba338ffd11eb9558e

## 2. Workspace Topology
- Workspace Layout: SIBLING_HIDDEN_CORE
- Workspace Rules: ../WORKSPACE_RULES.md
- CVF Core: ../.Controlled-Vibe-Framework-CVF
- Project Path: .
- Local absolute paths: `.cvf/local-binding.json` (git-ignored, generated per machine)
- VS Code workspace file: generated locally at workspace root and not required for continuity

## 3. Isolation Validation
- [x] CVF core and downstream project are sibling folders
- [x] Workspace rules file exists at workspace root
- [x] IDE/terminal target is project workspace
- [x] terminal.integrated.cwd is ${workspaceFolder}
- [ ] Team acknowledgment recorded

## 4. Bootstrap Actions
- [x] CVF core available
- [x] Project folder available
- [x] VS Code terminal defaults configured
- [x] Agent Instructions: PRESENT
- [x] .cvf/manifest.json: PRESENT (knowledgePath: knowledge/)
- [x] .cvf/policy.json: PRESENT
- [x] WORKSPACE_RULES.md: PRESENT
- [x] knowledge/ folder: PRESENT (add .md files and run ingest script to enable project-knowledge injection)
- [x] Seven-step phase model: INTAKE -> DESIGN -> SPEC -> WORK_ORDER -> BUILD -> REVIEW -> FREEZE
- [x] Tranche inheritance rule: reuse accepted evidence, record the entry stage, and gate every applicable transition
- [x] Project continuity front doors: PRESENT
- [x] Implementation status and docs index/catalog: PRESENT
- [x] Governed downstream catalog kit (Artifact Registry, Module Registry, schemas, catalog manager): PRESENT
- [x] Downstream gate profile (cvf.downstreamGateProfile@1.2.0): INSTALLED (files pinned; invocation and CI execution are reported by the doctor coverage readout, not assumed)
- [ ] Runtime artifacts migrated (if needed)
- [ ] Toolchain baseline recorded (python, node, pnpm, optional uv)

## 5. Post-Bootstrap Checks
Run the workspace doctor to verify enforcement artifacts:
  powershell -ExecutionPolicy Bypass -File <cvf-core>\scripts\check_cvf_workspace_agent_enforcement.ps1 -ProjectPath "<this-project-path>"

Optional secret-free live readiness check:
  powershell -ExecutionPolicy Bypass -File <cvf-core>\scripts\check_cvf_workspace_agent_enforcement.ps1 -ProjectPath "<this-project-path>" -CheckLiveReadiness

Governed downstream catalog check (also run by the doctor when the kit is present):
  powershell -ExecutionPolicy Bypass -File "<this-project-path>\scripts\manage_cvf_downstream_catalog.ps1" -Check

Workspace-to-web evidence bridge receipt (run during REVIEW/FREEZE):
  powershell -ExecutionPolicy Bypass -File <cvf-core>\scripts\write_cvf_workspace_web_evidence_bridge.ps1 -ProjectPath "<this-project-path>" -CheckLiveReadiness -ReleaseGateResult "ATTACH_LATEST_CVF_CORE_GATE_RESULT"

- [ ] Workspace doctor: PASS
- [ ] Optional live readiness: PASS / MISSING KEY / NOT RUN
- [ ] Workspace-to-web evidence bridge receipt: PRESENT / NOT NEEDED
- [ ] API health check
- [ ] Frontend startup check
- [ ] Critical workflow smoke check

## 6. Approval
- Result: PASS / PASS WITH NOTE / FAIL
- Approved By:
- Approval Date:
