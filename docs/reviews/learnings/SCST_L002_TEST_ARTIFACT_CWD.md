# Project Learning Record — SCST-L002

Status: CANDIDATE
Source project: Cargo_Stowage_Tool
Source revision: 17ee7e5f304e59e35a97dfd4c6c796a28411abbd
Updated: 01-11-2026

## Observation and mechanism

SUP-01 browser assertions passed 36/36, but root review found no screenshots at the declared project destination.
Legacy test artifact paths used `../../docs/...`, assuming frontend cwd; the actual Playwright CLI ran from project root.
Twenty-seven SUP-01 PNG/geometry files landed outside the project. This is a local application/execution error;
workspace isolation and evidence custody rules already existed, not proof of a missing CVF engine or agent control.

Expected: output paths resolve inside the declared evidence boundary regardless of invoking cwd. Test PASS alone
does not establish correct artifact custody. Source/failure and actual paths are recorded in
[browser return](../SCST_SUP_01_EVIDENCE/browser-return.md) and [recovery receipt](../SCST_SUP_01_EVIDENCE/browser/artifact-recovery.json).

## Local repair and evidence

The worker moved only exact generated files from the verified wrong base into project evidence, without recursive
operations or unrelated files. Pre/post move hashes were not captured; the receipt contains the final inventory,
not a byte-equality proof before recovery. Wrong-base remaining file count is zero. New `tests/browser/evidence.ts`
resolves paths from its own module directory; all screenshot/geometry writes use it. Focused screenshot and
diagnostic JSON checks from root passed at the corrected destination. Existing 36 assertions were not weakened;
the full suite was not repeated for the I/O-only path change. Root reviewed the helper and inspected recovered images.

## Parent value and feedback

Candidate benefit: add a concrete cwd-independent artifact-path example to existing evidence-custody guidance;
dedup against project-development application and learning-loop standards before changing any rule/checker.
Parent decides value/admission. This record and generated intake do not change Core, install a watcher, or prove governance behavior.

| Boundary | State | Owner / next condition |
|---|---|---|
| Local repair | APPLIED_LOCALLY | Root review of paths, receipt and focused corrected-output proof |
| Parent value decision | PENDING_PARENT_ASSESSMENT | CVF parent; generated docs/learning_intake/SCST-L002.intake.json |
| Parent implementation / return / adoption | NOT_IMPLEMENTED / NOT_RETURNED / NOT_APPLIED | Only after parent review and an authorized returned change |
