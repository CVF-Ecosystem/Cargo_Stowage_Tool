import type { Evaluation, Plan } from "../features/model";
import type { components } from "./generated/api";
export type VesselProfile = components["schemas"]["VesselProfile"];

export async function requestEvaluation(plan?: Plan): Promise<Evaluation> {
  const response = await fetch(plan ? "/api/validate" : "/api/demo", {
    method: plan ? "POST" : "GET",
    headers: plan ? { "Content-Type": "application/json" } : undefined,
    body: plan ? JSON.stringify(plan) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    if (response.status === 422)
      throw new Error(
        "Dữ liệu không đúng cấu trúc được hỗ trợ. Phương án trước vẫn được giữ.",
      );
    throw new Error(
      `Không thể kiểm phương án (HTTP ${response.status}). Thử lại khi backend sẵn sàng.`,
    );
  }
  const data = (await response.json()) as Evaluation;
  if (
    data.plan?.contract_version !== "scst.m1.v1" ||
    !["SYNTHETIC", "MIXED_REFERENCE"].includes(data.plan.source)
  )
    throw new Error("Phiên bản dữ liệu API không tương thích.");
  return data;
}

export async function requestVesselProfile(): Promise<VesselProfile> {
  const response = await fetch("/api/vessels/vinafco268", { signal: AbortSignal.timeout(15000) }).catch(() => { throw new Error("Không tải được dữ liệu phương tiện."); });
  if (!response.ok) throw new Error("Không tải được dữ liệu phương tiện.");
  return await response.json() as VesselProfile;
}

export async function requestVesselPlan(caseId: string): Promise<Evaluation> {
  const response = await fetch(`/api/vessels/vinafco268/cases/${encodeURIComponent(caseId)}/plan`, { signal: AbortSignal.timeout(15000) }).catch(() => { throw new Error("Không tải được trạng thái phương tiện."); });
  if (!response.ok) throw new Error("Không tải được trạng thái phương tiện.");
  return await response.json() as Evaluation;
}
