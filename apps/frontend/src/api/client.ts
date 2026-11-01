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
    !["scst.m1.v1", "scst.m2a.v1", "scst.pipe-list.v1"].includes(data.plan?.contract_version) ||
    !["SYNTHETIC", "MIXED_REFERENCE", "USER_ENTERED"].includes(data.plan.source)
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

export type CsvPreview = components["schemas"]["CsvPreview"];
export type SavedSummary = components["schemas"]["SavedSummary"];
async function jsonRequest<T>(path: string, body?: unknown): Promise<T> {
  try {
    const response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: body === undefined ? undefined : {"Content-Type":"application/json"}, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error();
    return await response.json() as T;
  } catch { throw new Error("Không thể xử lý dữ liệu local; phương án đang mở được giữ nguyên."); }
}
export const previewCsv = (plan: Plan, csv_text: string) => jsonRequest<CsvPreview>("/api/import/csv/preview", {plan,csv_text});
export const saveSnapshot = (plan: Plan, name: string) => jsonRequest<SavedSummary>("/api/snapshots", {plan,name});
export const listSnapshots = () => jsonRequest<SavedSummary[]>("/api/snapshots");
export const openSnapshot = (id: string) => jsonRequest<Evaluation>(`/api/snapshots/${encodeURIComponent(id)}`);

export type PipeLibrary = components["schemas"]["PipeLibrary"];
export const getPipeLibrary = () => jsonRequest<PipeLibrary>("/api/pipe-list");
export const previewPipeList = (plan: Plan) => jsonRequest<Evaluation>("/api/pipe-list/preview",plan);

export type PlannerPreview = components["schemas"]["PlannerPreview"];
export const previewPlanner = (plan: Plan) => jsonRequest<PlannerPreview>("/api/planner/preview",plan);

export type CompareResult = components["schemas"]["CompareResult"];
export const comparePlans = (before: Plan, after: Plan) => jsonRequest<CompareResult>("/api/plans/compare",{before,after});
