import type {
  CreateVentureRequest,
  GraduateVentureRequest,
  GraduateVentureResponse,
  ScenarioCompareResponse,
  StructureIdeaResponse,
  UpdateVentureShareRequest,
  VentureAssumptions,
  VentureGraduationStatus,
  VentureHistoryResponse,
  VentureResponse,
  VentureShareSettings,
  VentureSnapshotResponse,
  VentureSummary,
} from "@/types";

import { apiFetch } from "./client";

// Idea Lab / Venture Simulator V1. Every call here requires a real Clerk
// session token, same pattern as lib/api/savedStartups.ts -- modeled
// ventures are private user data, never public intelligence.

// Phase 6.1: stateless -- creates nothing, computes no VPS. See POST
// /ventures/structure-idea's own docstring in app/api.py.
export function structureIdea(
  description: string,
  token: string
): Promise<StructureIdeaResponse> {
  return apiFetch<StructureIdeaResponse>("/ventures/structure-idea", {
    method: "POST",
    body: { description },
    token,
  });
}

export function listVentures(token: string): Promise<VentureSummary[]> {
  return apiFetch<VentureSummary[]>("/ventures", { token });
}

export function getVenture(id: number, token: string): Promise<VentureResponse> {
  return apiFetch<VentureResponse>(`/ventures/${id}`, { token });
}

export function createVenture(
  request: CreateVentureRequest,
  token: string
): Promise<VentureResponse> {
  return apiFetch<VentureResponse>("/ventures", {
    method: "POST",
    body: request,
    token,
  });
}

export function updateVenture(
  id: number,
  request: CreateVentureRequest,
  token: string
): Promise<VentureResponse> {
  return apiFetch<VentureResponse>(`/ventures/${id}`, {
    method: "PUT",
    body: request,
    token,
  });
}

// Phase 16 -- Founder Progress / Venture History V1.
export function getVentureHistory(id: number, token: string): Promise<VentureHistoryResponse> {
  return apiFetch<VentureHistoryResponse>(`/ventures/${id}/history`, { token });
}

export function deleteVenture(id: number, token: string): Promise<{ deleted: boolean }> {
  return apiFetch<{ deleted: boolean }>(`/ventures/${id}`, {
    method: "DELETE",
    token,
  });
}

// Phase 27 -- Shareable Venture Snapshot V1. These three, unlike every
// other function in this file, are NOT all founder-only: getVentureShare/
// updateVentureShare/getVentureSharePreview require a token (owner-only,
// same as every other venture endpoint); getPublicVentureSnapshot
// deliberately takes NO token at all -- it is THE public, unauthenticated
// route, and passing no `token` to apiFetch already omits the
// Authorization header entirely (see lib/api/client.ts).

export function getVentureShare(id: number, token: string): Promise<VentureShareSettings> {
  return apiFetch<VentureShareSettings>(`/ventures/${id}/share`, { token });
}

export function updateVentureShare(
  id: number,
  request: UpdateVentureShareRequest,
  token: string
): Promise<VentureShareSettings> {
  return apiFetch<VentureShareSettings>(`/ventures/${id}/share`, {
    method: "PUT",
    body: request,
    token,
  });
}

export function getVentureSharePreview(id: number, token: string): Promise<VentureSnapshotResponse> {
  return apiFetch<VentureSnapshotResponse>(`/ventures/${id}/share/preview`, { token });
}

// THE public call -- no token, callable from the public /v/[publicId]
// page with zero Clerk session in scope.
export function getPublicVentureSnapshot(publicId: string): Promise<VentureSnapshotResponse> {
  return apiFetch<VentureSnapshotResponse>(`/ventures/share/${publicId}`);
}

// Phase 28 -- Product Analytics & Growth Measurement V1. Two narrow,
// purpose-built client-event calls (Part 4's own explicit exception to
// "prefer server-side" for events a backend transaction genuinely can't
// see). Both take no body -- the event name and every field are decided
// server-side from the URL path alone (see the matching endpoints' own
// docstrings in app/api.py).
export function logSnapshotLinkCopied(ventureId: number, token: string): Promise<{ logged: boolean }> {
  return apiFetch<{ logged: boolean }>(`/ventures/${ventureId}/share/link-copied`, {
    method: "POST",
    token,
  });
}

// Public, no token -- callable from an anonymous recipient's browser.
export function logSnapshotCtaClicked(publicId: string): Promise<{ logged: boolean }> {
  return apiFetch<{ logged: boolean }>(`/ventures/share/${publicId}/cta-clicked`, {
    method: "POST",
  });
}

// Phase 31 -- Venture -> Startup Graduation V1. All three founder-only,
// same token discipline as every other function in this file -- a
// venture's graduation state is private founder data, never public.

export function logGraduationPromptShown(ventureId: number, token: string): Promise<{ logged: boolean }> {
  return apiFetch<{ logged: boolean }>(`/ventures/${ventureId}/graduation/prompt-shown`, {
    method: "POST",
    token,
  });
}

export function logGraduationStarted(ventureId: number, token: string): Promise<{ logged: boolean }> {
  return apiFetch<{ logged: boolean }>(`/ventures/${ventureId}/graduation/started`, {
    method: "POST",
    token,
  });
}

export function getVentureGraduationStatus(
  id: number,
  token: string
): Promise<VentureGraduationStatus> {
  return apiFetch<VentureGraduationStatus>(`/ventures/${id}/graduation`, { token });
}

export function graduateVenture(
  id: number,
  request: GraduateVentureRequest,
  token: string
): Promise<GraduateVentureResponse> {
  return apiFetch<GraduateVentureResponse>(`/ventures/${id}/graduate`, {
    method: "POST",
    body: request,
    token,
  });
}

// Fire-and-forget-shaped from the caller's side, mirroring
// logSnapshotLinkCopied()'s own pattern -- the server decides every
// field from the URL path and auth context, never from anything sent
// here.
export function logStartupOpenedFromVenture(
  ventureId: number,
  token: string
): Promise<{ logged: boolean }> {
  return apiFetch<{ logged: boolean }>(`/ventures/${ventureId}/graduation/startup-opened`, {
    method: "POST",
    token,
  });
}

export function compareVentureScenarios(
  currentAssumptions: VentureAssumptions,
  modifiedAssumptions: VentureAssumptions,
  token: string
): Promise<ScenarioCompareResponse> {
  return apiFetch<ScenarioCompareResponse>("/ventures/scenario-compare", {
    method: "POST",
    body: {
      current_assumptions: currentAssumptions,
      modified_assumptions: modifiedAssumptions,
    },
    token,
  });
}
