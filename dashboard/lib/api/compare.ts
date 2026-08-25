import type { ComparisonResponse } from "@/types";

import { apiFetch } from "./client";

// Compare Startups V1. Public -- no token option, same as lib/api/
// discovery.ts -- comparing canonical intelligence is public intelligence,
// not a paid or personalized action.
export function compareStartups(
  startupIds: number[]
): Promise<ComparisonResponse> {
  return apiFetch<ComparisonResponse>(
    `/compare?startups=${startupIds.join(",")}`
  );
}
