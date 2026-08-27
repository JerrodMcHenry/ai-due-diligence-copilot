import type { AnalyzeStartupResponse } from "@/types";

import { apiFetch } from "./client";

// The real analysis (research + six pillar analyses + summary/risk/memo/
// readiness) routinely takes several minutes. 10 minutes is a generous
// upper bound so a genuinely hung request eventually surfaces as a timeout
// instead of leaving the user stuck forever with no recourse -- not a
// realistic expectation of how long a normal run takes.
const ANALYZE_TIMEOUT_MS = 10 * 60 * 1000;

// Unified Multi-Source Analyze Startup: website, pitch deck, and
// user-provided text are evidence sources feeding ONE canonical
// analysis, not separate mutually-exclusive modes -- POST /analyze
// accepts any combination of the three (at least one required) and
// assembles them server-side (see
// app/workflows/due_diligence_workflow.py::assemble_multi_source_text)
// before running the exact same pipeline.
//
// Phase 10.1B: this is now the ONLY paid analysis entry point --
// analyzeStartup()/analyzeWebsite()/analyzePdf() (POST /analyze-startup,
// /analyze-website, /analyze-pdf) were removed along with the backend
// routes themselves (zero product consumers). POST /analyze also now
// enforces AI-cost/abuse protection server-side (a same-account
// concurrency lock, a short duplicate-submission cooldown, and a beta
// usage cap) -- surfaced to the caller as ordinary 409/429 HTTP statuses,
// handled in AnalyzeStartupForm.tsx's existing status-code-driven error
// copy, nothing new needed in this file itself.
//
// SIE Authentication Phase 2: POST /analyze now requires a valid Clerk
// bearer token server-side -- `token` is the caller's real Clerk session
// token (from useAuth().getToken() in the page, see
// AnalyzeStartupForm.tsx), attached as `Authorization: Bearer <token>`
// via apiFetch's `token` option. This function never reads or stores the
// token itself; it only forwards what it's given for this one request.
export function analyzeMultiSource({
  websiteUrl,
  pdfFile,
  companyText,
  startupId,
  token,
}: {
  websiteUrl?: string;
  pdfFile?: File | null;
  companyText?: string;
  // Phase 7.2.1 -- Deterministic Founder Re-analysis: OPTIONAL. Omitted
  // entirely for a normal analysis (identical request shape to before
  // this field existed). When present, POST /analyze treats it as the
  // authoritative canonical startup to attach this analysis to -- see
  // that endpoint's own comment in app/api.py -- after independently
  // re-verifying the caller's membership itself; this value is never
  // trusted just because it was sent.
  startupId?: number | null;
  token?: string | null;
}): Promise<AnalyzeStartupResponse> {
  const formData = new FormData();

  if (websiteUrl) {
    formData.append("website_url", websiteUrl);
  }

  if (pdfFile) {
    formData.append("pdf", pdfFile);
  }

  if (companyText) {
    formData.append("company_text", companyText);
  }

  if (startupId != null) {
    formData.append("startup_id", String(startupId));
  }

  return apiFetch<AnalyzeStartupResponse>("/analyze", {
    method: "POST",
    body: formData,
    timeoutMs: ANALYZE_TIMEOUT_MS,
    token,
  });
}
