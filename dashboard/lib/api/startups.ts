import { apiFetch } from "./client";

import type { StartupProfileResponse } from "@/types";

export async function getStartupProfile(
  companyName: string
): Promise<StartupProfileResponse> {
  return apiFetch<StartupProfileResponse>(
    `/startup/${encodeURIComponent(companyName)}`
  );
}
