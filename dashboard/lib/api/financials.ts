import type { CreateFinancialSnapshotRequest, FinancialHistoryResponse, VentureFinancialsResponse } from "@/types";

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
