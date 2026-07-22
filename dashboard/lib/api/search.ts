import type { StartupSearchResult } from "@/types";

import { apiFetch } from "./client";

export function searchStartups(query: string): Promise<StartupSearchResult[]> {
  return apiFetch<StartupSearchResult[]>(
    `/analyses/search?query=${encodeURIComponent(query)}`
  );
}
