import type {
  CreateFinancialSnapshotRequest,
  CreateHirePlanRequest,
  FinancialHistoryResponse,
  HireImpactPreview,
  HirePlan,
  HirePlanStatus,
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
