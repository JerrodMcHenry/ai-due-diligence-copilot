import type { MyStartupMembership } from "@/types";

import { apiFetch } from "./client";

// Phase 7.1C -- Founder Membership Authorization Foundation. Requires a
// real Clerk session token, same pattern as lib/api/startupClaims.ts.
// This is the entry point for Phase 7.2's /founder: the caller's own
// current startup_memberships rows, and nothing else -- never pending
// claims, saved startups, or modeled ventures.

export function getMyStartups(token: string): Promise<MyStartupMembership[]> {
  return apiFetch<MyStartupMembership[]>("/me/startups", { token });
}
