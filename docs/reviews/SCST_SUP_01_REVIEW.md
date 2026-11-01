# SCST — SUP-01 independent implementation review

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra implementation; Sol browser worker
Reviewer: root-independent-implementation-reviewer

## Disposition and source boundary

**Accept technical SUP-01 and its internally exercised user flow.** Business/operational acceptance remains pending;
SUP-02/03 and M2d are not opened. Root reviewed worker source/test diffs, evidence and screenshots independently of
the implementation actors. Root authored SPEC/WO and documentation; Sol independently reviewed the CVF-DEV
continuation before BUILD. No full CVF adoption or real-provider agent-governance proof is asserted.

Admission commit `17ee7e5`, source manifest [here](SCST_SUP_01_EVIDENCE/reviewed-source-manifest.json), final frontend
bundle `index-D-_1-kxf.js`. Scope is Viewer/Scene, one CSS rule and browser tests/artifact helper; no backend,
profile/GLB/source data, contract, dependency, policy, gate implementation, CI or hook change.

## Acceptance matrix

| Criterion | Independent review and actual evidence | Result / limit |
|---|---|---|
| S1-01 | Stable renderer/controls/canvas lifetime; cargo keyed by ID/signature and latest callback refs; asset key/generation guard with disposal of obsolete loads. Tests retain canvas/camera/unchanged mesh UUID, update case marker and discard late GLB after detaching hold. | VERIFIED for selected synthetic/VINAFCO flows; no universal lifetime claim. |
| S1-02 | Bounds/FOV/aspect fit, top/side/focus/reset, focus guard and label-only hold changes reviewed. Browser oracle independently multiplies view/projection matrices for corner containment on desktop/mobile; 2D/picking/context loss remain usable. | VERIFIED at1440×1100/390×844 Chromium156. Other browser/device combinations NOT_TESTED. |
| S1-03 | Original GLB material inventory checked; only identified vỏ/vách nodes use owned clones, restore and disposal inspected. Visibility/case preserve asset; inherited precision, translation, payload/history and isolated snapshot round trips pass. | VERIFIED at existing estimated profile; no domain safety or measured-hold acceptance. |
| S1-04 | Opt-in `?viewerDiagnostics=1` guards heavy per-mesh traversal/serialization; normal route has no heavy attributes. Render-on-demand retained, three asset/material cycles show stable geometry/texture counts. Same-script old/final observations and all browser cases run. | VERIFIED within bounded cases; timings are API-response/automation observations, not visual latency/FPS or causal benchmark. |

[Worker return](SCST_SUP_01_EVIDENCE/worker-return.md), [browser return](SCST_SUP_01_EVIDENCE/browser-return.md),
[36/36 full regression log](SCST_SUP_01_EVIDENCE/browser/full-browser.log), [baseline](SCST_SUP_01_EVIDENCE/browser/viewer-baseline.json)
and [final candidate](SCST_SUP_01_EVIDENCE/browser/viewer-candidate.json) bind the checks. Build/typecheck passed with
the pre-existing Three chunk warning. Five focused cases passed; after artifact helper repair, two focused corrected-output
cases passed. All31 inherited numerical/flow assertions remain, plus five SUP cases. Backend suite was not rerun:
backend/contracts unchanged and prior104 backend evidence is inherited, not claimed as freshly executed.

## Internal product flow and observations

Synthetic select/orbit/edit/apply/undo/presets and isolated save/reopen, VINAFCO source1076 import/planner/apply,
selection/focus/ghost/case/2D/fallback were exercised on the packaged frontend with a real local backend and separate
test SQLite. Full-capacity source flow has167 placed/909 unplaced; a32t focused flow has22 placed. No claim that all
1076 fit the hold. Root visually inspected source scene and mobile fallback; ship/cargo, controls and cm/kg labels are visible,
with no document overflow in the tested mobile flow. Source geometry and exact underlying data remain unchanged.

Before/after observations show old canvas replacement on apply/undo/visibility and two extra GLB requests on hide/show;
final candidate retains canvas/camera on apply, canvas on undo/visibility and has zero extra visibility GLB requests.
Three diagnostic cycles at the reference scene retain83 geometries/1 texture. These are bounded observations,
not long-duration leak, throughput, FPS or operational proof. Raw timing ranges include automation/API and three samples only.

## Findings, repairs and evidence custody

- Early worker shell paths failed before writing; corrected and disclosed in worker return. Initial browser assumptions
  about editable name, placed ID, group pagination and canvas aspect failed; final cases use actual controls/data.
- Root found screenshots absent at declared location despite36 passing assertions. Relative paths assumed frontend cwd,
  but CLI ran from project root. Worker recovered27 exact generated files by nonrecursive file moves; wrong base now has
  zero files. No pre/post move hashes were captured, so no before-recovery byte-equality claim. Root checked the final
  inventory and inspected images; final hashes match the recovery receipt.
- Test helper now resolves evidence paths from module directory. Corrected screenshot and diagnostic output were exercised
  from project-root cwd. The full suite is valid for unchanged runtime assertions; only output I/O paths changed afterwards,
  so a full repeat was not justified. [Recovery receipt](SCST_SUP_01_EVIDENCE/browser/artifact-recovery.json),
  [final inventory](SCST_SUP_01_EVIDENCE/reviewer-artifact-inventory.json), [learning SCST-L002](learnings/SCST_L002_TEST_ARTIFACT_CWD.md).

Reviewer-local repair assessment for the artifact finding: `reviewerLocalRepairBoundary=NEW_EVIDENCE_REQUIRED`;
`reviewerLocalRepairBasis=actual misplaced file identities and corrected output evidence were not available at discovery`.
`unchangedObjective=YES`, `unchangedDesign=YES`, `unchangedPaths=YES`, `unchangedAuthority=YES`,
`unchangedEffects=YES`, `unchangedCommitOwner=YES`, `evidenceDetermined=NO`. Browser worker supplied recovery
and focused I/O proof within the existing order; no new runtime feature or authority was introduced. No open runtime defect remains.

## CVF application, limits and continuation

SCST-DA01 binds exact stored/geometry data versus rounded presentation; DA04 binds native reuse, explicit packet/gate
receipts and evidence limits; DA05 binds usable internal flow before owner feedback. DA02/03 remain boundaries on
user persistence and source/domain changes. The transferred operator-local guidance hash matched its manifest while
public Core pin stayedc4c8767. This describes source/artifact application, not proof that CVF controls agent behavior.
Live governance provider NOT_RUN, hosted CI NOT_OBSERVED, hook not installed; DEV-01 IMPLEMENTED_UNPROVED,
DEV-02/03 UNKNOWN retained. Scoped continuation rationale remains in the independent CVF-DEV reconciliation.

Root integrity checks preserve protected files/authority and user SQLite bytes during regression. Mechanical phase gates
have scope in their receipts; none is PROVEN_HERMETIC/hosted CI/live-governance proof. Learning intake SCST-L002 is
generation only, parent assessment pending; existing SCST-L001 remains separately pending.

The120minute prep/worker/browser/review ceiling was shared without reset; no extra backend/provider/platform investigation.
SUP-01 is a settled technical slice, not completion of all M2/product outcomes. Next when selected: bounded SPEC SUP-02
for evolving cargo/profile revisions; SUP-03 packing, M2d export, measured hold/16 envelopes and business/operational
acceptance retain owners and re-entry conditions in the roadmap. Only local commit is authorized; no push/deploy.
