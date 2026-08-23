import { apiFetch } from "./client";

import type { SPSHistoryPoint, StartupProfileResponse } from "@/types";

export async function getStartupProfile(
  companyName: string
): Promise<StartupProfileResponse> {
  return apiFetch<StartupProfileResponse>(
    `/startup/${encodeURIComponent(companyName)}`
  );
}

export async function getSPSHistory(
  companyName: string
): Promise<SPSHistoryPoint[]> {
  return apiFetch<SPSHistoryPoint[]>(
    `/startup/${encodeURIComponent(companyName)}/sps-history`
  );
}
