import type { RankingEntry } from "@/types";

import { apiFetch } from "./client";

export function getRankings(): Promise<RankingEntry[]> {
  return apiFetch<RankingEntry[]>("/rankings");
}
