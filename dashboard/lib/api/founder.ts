import type { FounderStartupWorkspace } from "@/types";

import { apiFetch } from "./client";

// Phase 7.2 -- Founder Workspace V1. Requires a real Clerk session token,
// same pattern as lib/api/startupMemberships.ts. This is the only
// startup-scoped Founder Workspace call -- the backend enforces
// membership (RequireStartupMember) independently of anything this
// function sends; it never sends a user_id or role.

export function getFounderStartupWorkspace(
  startupId: number,
  token: string
): Promise<FounderStartupWorkspace> {
  return apiFetch<FounderStartupWorkspace>(`/founder/startups/${startupId}`, {
    token,
  });
}
