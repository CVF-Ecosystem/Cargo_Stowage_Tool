import { resolve } from "node:path";

export const evidencePath = (name: string) =>
  resolve(__dirname, "../../docs/reviews/SCST_SUP_01_EVIDENCE/browser", name);
