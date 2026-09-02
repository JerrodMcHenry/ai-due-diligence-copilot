// Phase 26 -- Retention Loop Closure, Part 8/9/11 (cross-session working
// context). A pure, deterministic function -- no LLM, no new persistence,
// no new endpoint. Mirrors resolveRecentLearning.ts's own shape exactly:
// reads only data the caller already has in hand (the SAME
// GET /ventures/{id}/history response buildWeeklyReview.ts already
// consumes), does no I/O, and returns a small typed result the caller
// renders as-is.
//
// Unlike buildWeeklyReview.ts's own "What changed" (a first-in-window ->
// last-in-window aggregation across a rolling 7-day window), this finds
// the SINGLE most recent model_updated event across the venture's ENTIRE
// history, with no window at all -- "since your last model update," not
// "this week." The backend already returns events newest-first
// (app/api.py::get_venture_history()'s own `events.sort(..., reverse=
// True)`), so the first model_updated event in the list IS the latest
// one; no sorting or aggregation of this module's own is needed.
export type LatestModelChange = {
  occurredAt: string;
  beforeVps: number | null;
  afterVps: number | null;
  // The first curated assumption-field diff on that update, if any --
  // the same curated, already-formatted list app/api.py::
  // _diff_assumption_changes() produces (Phase 24). Only the first is
  // shown -- a compact orientation line, not a full changelog (the full
  // list is still one click away via "Venture history").
  primaryAssumptionChange: { label: string; before: string; after: string } | null;
};

type MinimalEvent = {
  event_type: string;
  occurred_at: string;
  before_vps: number | null;
  after_vps: number | null;
  assumption_changes: { label: string; before: string; after: string }[];
};

export function resolveLatestModelChange(events: MinimalEvent[]): LatestModelChange | null {
  const latest = events.find((e) => e.event_type === "model_updated");
  if (!latest) return null;

  return {
    occurredAt: latest.occurred_at,
    beforeVps: latest.before_vps,
    afterVps: latest.after_vps,
    primaryAssumptionChange: latest.assumption_changes[0] ?? null,
  };
}
