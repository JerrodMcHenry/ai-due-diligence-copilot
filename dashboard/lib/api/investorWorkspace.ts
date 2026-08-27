import type { InvestorWorkspace } from "@/types";

import { apiFetch } from "./client";

// Phase 9 -- Investor Workspace V1. Requires a real Clerk session token,
// same pattern as lib/api/savedStartups.ts -- GET /investor/workspace
// derives the acting user exclusively from the verified JWT (RequireAuth),
// never from a parameter this function could get wrong.
export function getInvestorWorkspace(token: string): Promise<InvestorWorkspace> {
  return apiFetch<InvestorWorkspace>("/investor/workspace", { token });
}
