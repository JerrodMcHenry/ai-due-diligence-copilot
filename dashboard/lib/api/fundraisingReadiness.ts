import type { FundraisingReadiness } from "@/types";

import { apiFetch } from "./client";

// Phase 8 -- Fundraising Readiness V1. Requires a real Clerk session
// token, same pattern as every other Founder Workspace call -- private
// fundraising preparation, never a public endpoint.

export function getFundraisingReadiness(
  startupId: number,
  token: string
): Promise<FundraisingReadiness> {
  return apiFetch<FundraisingReadiness>(`/founder/startups/${startupId}/fundraising`, {
    token,
  });
}
