import type { AnalyzeStartupResponse } from "@/types";

import { apiFetch } from "./client";

// The real analysis (research + six pillar analyses + summary/risk/memo/
// readiness) routinely takes several minutes. 10 minutes is a generous
// upper bound so a genuinely hung request eventually surfaces as a timeout
// instead of leaving the user stuck forever with no recourse -- not a
// realistic expectation of how long a normal run takes.
const ANALYZE_TIMEOUT_MS = 10 * 60 * 1000;

export function analyzeStartup(
  companyText: string
): Promise<AnalyzeStartupResponse> {
  return apiFetch<AnalyzeStartupResponse>("/analyze-startup", {
    method: "POST",
    body: { company_text: companyText },
    timeoutMs: ANALYZE_TIMEOUT_MS,
  });
}
