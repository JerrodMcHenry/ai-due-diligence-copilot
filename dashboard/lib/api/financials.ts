import type {
  CreateFinancialPlanRequest,
  CreateFinancialSnapshotRequest,
  CreateHirePlanRequest,
  CreateScenarioRequest,
  FinancialHistoryResponse,
  FinancialPlan,
  FinancialPlanImpactPreview,
  HireImpactPreview,
  HirePlan,
  HirePlanStatus,
  PlanStatus,
  Scenario,
  VentureFinancialsResponse,
} from "@/types";

import { apiFetch } from "./client";

// Phase 35B -- Financial State Persistence + Runway Engine V1. Same
// pattern as lib/api/buildIntelligence.ts -- every call requires a real
// Clerk session token; these resources belong to a modeled venture,
// never public.

export function getVentureFinancials(ventureId: number, token: string): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials`, { token });
}

export function createVentureFinancialSnapshot(
  ventureId: number,
  request: CreateFinancialSnapshotRequest,
  token: string
): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials`, {
    method: "POST",
    body: request,
    token,
  });
}

export function getVentureFinancialHistory(ventureId: number, token: string): Promise<FinancialHistoryResponse> {
  return apiFetch<FinancialHistoryResponse>(`/ventures/${ventureId}/financials/history`, { token });
}

// --- Phase 35C -- Hiring + Operating Plan Engine V1 -------------------------

export function createHirePlan(ventureId: number, request: CreateHirePlanRequest, token: string): Promise<HirePlan> {
  return apiFetch<HirePlan>(`/ventures/${ventureId}/hire-plans`, { method: "POST", body: request, token });
}

export function listHirePlans(ventureId: number, token: string): Promise<HirePlan[]> {
  return apiFetch<HirePlan[]>(`/ventures/${ventureId}/hire-plans`, { token });
}

export function updateHirePlan(
  ventureId: number,
  hirePlanId: number,
  fields: Partial<CreateHirePlanRequest> & { status?: HirePlanStatus },
  token: string
): Promise<HirePlan> {
  return apiFetch<HirePlan>(`/ventures/${ventureId}/hire-plans/${hirePlanId}`, { method: "PATCH", body: fields, token });
}

// NEVER persists (Phase 35C §17: PERSISTED PLAN vs. TEMPORARY COMPARISON)
// -- used both for "see financial impact before saving" and for the
// hire-now-vs-later comparison (called twice with different start dates).
export function previewHirePlan(
  ventureId: number,
  request: CreateHirePlanRequest,
  token: string,
  excludeHirePlanId?: number
): Promise<HireImpactPreview> {
  const query = excludeHirePlanId !== undefined ? `?exclude_hire_plan_id=${excludeHirePlanId}` : "";
  return apiFetch<HireImpactPreview>(`/ventures/${ventureId}/hire-plans/preview${query}`, {
    method: "POST",
    body: request,
    token,
  });
}

// --- Phase 35D -- Operating Scenarios + Financial Plan Reconciliation V1 ---

export function createFinancialPlan(ventureId: number, request: CreateFinancialPlanRequest, token: string): Promise<FinancialPlan> {
  return apiFetch<FinancialPlan>(`/ventures/${ventureId}/financial-plans`, { method: "POST", body: request, token });
}

export function listFinancialPlans(ventureId: number, token: string): Promise<FinancialPlan[]> {
  return apiFetch<FinancialPlan[]>(`/ventures/${ventureId}/financial-plans`, { token });
}

export function updateFinancialPlan(
  ventureId: number,
  planId: number,
  fields: Partial<CreateFinancialPlanRequest> & { status?: PlanStatus },
  token: string
): Promise<FinancialPlan> {
  return apiFetch<FinancialPlan>(`/ventures/${ventureId}/financial-plans/${planId}`, { method: "PATCH", body: fields, token });
}

// NEVER persists -- same discipline as previewHirePlan().
export function previewFinancialPlan(
  ventureId: number,
  request: CreateFinancialPlanRequest,
  token: string,
  excludePlanId?: number
): Promise<FinancialPlanImpactPreview> {
  const query = excludePlanId !== undefined ? `?exclude_plan_id=${excludePlanId}` : "";
  return apiFetch<FinancialPlanImpactPreview>(`/ventures/${ventureId}/financial-plans/preview${query}`, {
    method: "POST",
    body: request,
    token,
  });
}

export function listScenarios(ventureId: number, token: string): Promise<Scenario[]> {
  return apiFetch<Scenario[]>(`/ventures/${ventureId}/scenarios`, { token });
}

export function createScenario(ventureId: number, request: CreateScenarioRequest, token: string): Promise<Scenario> {
  return apiFetch<Scenario>(`/ventures/${ventureId}/scenarios`, { method: "POST", body: request, token });
}

export function updateScenario(
  ventureId: number,
  scenarioId: number,
  fields: Partial<CreateScenarioRequest>,
  token: string
): Promise<Scenario> {
  return apiFetch<Scenario>(`/ventures/${ventureId}/scenarios/${scenarioId}`, { method: "PATCH", body: fields, token });
}

export function deleteScenario(ventureId: number, scenarioId: number, token: string): Promise<{ deleted: boolean }> {
  return apiFetch<{ deleted: boolean }>(`/ventures/${ventureId}/scenarios/${scenarioId}`, { method: "DELETE", token });
}

// §16: founder-controlled model bookkeeping, never a verification gate --
// the founder's own yes/no answer is recorded verbatim.
export function reconcileFinancialPlan(
  ventureId: number,
  planKind: "hire" | "financial",
  planId: number,
  included: boolean,
  token: string
): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials/reconcile`, {
    method: "POST",
    body: { plan_kind: planKind, plan_id: planId, included },
    token,
  });
}
