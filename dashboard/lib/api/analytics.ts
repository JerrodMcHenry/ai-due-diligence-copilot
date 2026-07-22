import type {
  AnalyticsSummary,
  ImprovingStartup,
  StartupRanking,
} from "@/types";

import { apiFetch } from "./client";

export function getAnalytics(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>("/analytics");
}

export function getTopStartups(): Promise<StartupRanking[]> {
  return apiFetch<StartupRanking[]>("/top-startups");
}

export function getTopImprovingStartups(): Promise<ImprovingStartup[]> {
  return apiFetch<ImprovingStartup[]>("/top-improving-startups");
}
