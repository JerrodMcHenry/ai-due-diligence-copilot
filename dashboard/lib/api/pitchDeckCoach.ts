import type { PitchDeckReview, PitchDeckReviewSummary } from "@/types";

import { apiFetch } from "./client";

// Phase 10.8 -- Pitch Deck Coach V1. Deliberately its own module, not
// added to lib/api/analyze.ts -- POST /pitch-deck-reviews is a completely
// separate backend surface from POST /analyze (see
// app/ai/pitch_deck_coaching.py's own module docstring for the full
// architectural boundary). Every call here requires a real Clerk session
// token; a pitch deck review is a private, ownership-scoped resource,
// same posture as lib/api/ideaLab.ts's ventures.

// Coaching involves one real LLM call over a full deck's extracted text
// -- generous but bounded, mirroring lib/api/analyze.ts's own
// ANALYZE_TIMEOUT_MS reasoning (a genuinely hung request should
// eventually surface as a timeout, not hang forever).
const REVIEW_TIMEOUT_MS = 5 * 60 * 1000;

export function uploadPitchDeckReview(pdfFile: File, token: string): Promise<PitchDeckReview> {
  const formData = new FormData();
  formData.append("pdf", pdfFile);

  return apiFetch<PitchDeckReview>("/pitch-deck-reviews", {
    method: "POST",
    body: formData,
    timeoutMs: REVIEW_TIMEOUT_MS,
    token,
  });
}

export function listPitchDeckReviews(token: string): Promise<PitchDeckReviewSummary[]> {
  return apiFetch<PitchDeckReviewSummary[]>("/pitch-deck-reviews", { token });
}

export function getPitchDeckReview(reviewId: number, token: string): Promise<PitchDeckReview> {
  return apiFetch<PitchDeckReview>(`/pitch-deck-reviews/${reviewId}`, { token });
}
