import type { DiscoveryFilterOptions, DiscoveryFilters, DiscoveryResponse } from "@/types";

import { apiFetch } from "./client";

// Startup Discovery V1. Both endpoints are public -- no token option here,
// unlike lib/api/savedStartups.ts -- exploring the canonical startup
// universe is intelligence, same as Rankings/Search/Startup Profile, not a
// paid or personalized action.

function buildDiscoveryQueryString(filters: DiscoveryFilters): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }

    params.set(key, String(value));
  }

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

export function discoverStartups(
  filters: DiscoveryFilters = {}
): Promise<DiscoveryResponse> {
  return apiFetch<DiscoveryResponse>(
    `/discover${buildDiscoveryQueryString(filters)}`
  );
}

export function getDiscoveryFilterOptions(): Promise<DiscoveryFilterOptions> {
  return apiFetch<DiscoveryFilterOptions>("/discover/filter-options");
}
