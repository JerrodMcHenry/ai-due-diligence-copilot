import type {
  CreateStartupClaimRequest,
  StartupClaimActionResponse,
  StartupClaimStatus,
  StartupClaimSubmissionResponse,
} from "@/types";

import { apiFetch } from "./client";

// Phase 7.1B. Every call here requires a real Clerk session token, same
// pattern as lib/api/savedStartups.ts -- claiming a startup is a private,
// authenticated action. None of these functions accept or forward a
// user_id, role, status, or verification_method -- the request bodies
// below are the complete, exhaustive set of fields this frontend ever
// sends to these endpoints.

export function getMyStartupClaimStatus(
  startupId: number,
  token: string
): Promise<StartupClaimStatus | null> {
  return apiFetch<StartupClaimStatus | null>(`/me/startup-claims/${startupId}`, {
    token,
  });
}

export function submitStartupClaim(
  request: CreateStartupClaimRequest,
  token: string
): Promise<StartupClaimSubmissionResponse> {
  return apiFetch<StartupClaimSubmissionResponse>("/startup-claims", {
    method: "POST",
    body: request,
    token,
  });
}

export function cancelMyStartupClaim(
  claimId: number,
  token: string
): Promise<StartupClaimActionResponse> {
  return apiFetch<StartupClaimActionResponse>(`/me/startup-claims/${claimId}/cancel`, {
    method: "POST",
    token,
  });
}
