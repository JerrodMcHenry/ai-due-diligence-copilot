import type {
  BuildRecommendationResponse,
  CreateDecisionRequest,
  CreateEvidenceRequest,
  VentureDecision,
  VentureEvidence,
} from "@/types";

import { apiFetch } from "./client";

// Phase 34D -- SIE Build Intelligence Loop V1. Every call here requires a
// real Clerk session token, same as lib/api/ventureMissions.ts -- these
// resources belong to a modeled venture, never public. Deliberately its
// own file, mirroring ventureMissions.ts being separate from ideaLab.ts:
// Evidence/Decisions/Recommendation are the two genuinely new resources
// this phase adds (docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md
// §D), kept apart from the pre-existing mission calls they build on top
// of rather than folded into that file.

export function getVentureRecommendation(ventureId: number, token: string): Promise<BuildRecommendationResponse> {
  return apiFetch<BuildRecommendationResponse>(`/ventures/${ventureId}/recommendation`, { token });
}

export function listVentureEvidence(
  ventureId: number,
  token: string,
  missionId?: number
): Promise<VentureEvidence[]> {
  const query = missionId !== undefined ? `?mission_id=${missionId}` : "";
  return apiFetch<VentureEvidence[]>(`/ventures/${ventureId}/evidence${query}`, { token });
}

export function createVentureEvidence(
  ventureId: number,
  request: CreateEvidenceRequest,
  token: string
): Promise<VentureEvidence> {
  return apiFetch<VentureEvidence>(`/ventures/${ventureId}/evidence`, {
    method: "POST",
    body: request,
    token,
  });
}

// Phase 34G-A -- Intelligence Resolution + Learning Integrity Hardening,
// §3/§6. Marks one specific evidence row (from a recommendation's own
// `blocking_evidence`) as no longer the current picture, in the
// founder's own words -- never edits/deletes it. See
// resolve_venture_evidence_for_owner() in app/database/db.py.
export function resolveVentureEvidence(
  ventureId: number,
  evidenceId: number,
  resolutionNote: string,
  token: string
): Promise<VentureEvidence> {
  return apiFetch<VentureEvidence>(`/ventures/${ventureId}/evidence/${evidenceId}/resolve`, {
    method: "POST",
    body: { resolution_note: resolutionNote },
    token,
  });
}

export function listVentureDecisions(ventureId: number, token: string): Promise<VentureDecision[]> {
  return apiFetch<VentureDecision[]>(`/ventures/${ventureId}/decisions`, { token });
}

export function createVentureDecision(
  ventureId: number,
  request: CreateDecisionRequest,
  token: string
): Promise<VentureDecision> {
  return apiFetch<VentureDecision>(`/ventures/${ventureId}/decisions`, {
    method: "POST",
    body: request,
    token,
  });
}
