import { mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

// SUP-02B D8: browser evidence is never written into closed packets under docs/reviews/.
// Output goes to SCST_EVIDENCE_DIR when set, otherwise to a per-run temp directory.
// SCST_EVIDENCE_RUN is set once per Playwright run; workers inherit it from the runner process.
process.env.SCST_EVIDENCE_RUN ??= String(Date.now());

export const evidenceDir = (): string => {
  const dir = process.env.SCST_EVIDENCE_DIR
    ? resolve(process.env.SCST_EVIDENCE_DIR)
    : resolve(tmpdir(), `scst-evidence-${process.env.SCST_EVIDENCE_RUN}`);
  mkdirSync(dir, { recursive: true });
  return dir;
};

export const evidencePath = (name: string): string => resolve(evidenceDir(), name);
