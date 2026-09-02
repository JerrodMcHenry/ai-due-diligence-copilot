// Phase 24 -- Weekly Founder Review V1.
//
// Pure, deterministic aggregation over VentureHistoryResponse (Phase 16,
// extended in Phase 24 with assumption_changes -- see
// app/api.py::_diff_assumption_changes()). No new persistence, no new
// endpoint call beyond the existing GET /ventures/{id}/history this
// module already receives as an argument, no AI. Every field below is
// FACT (a real event) or DERIVED FACT (deterministic arithmetic over real
// events) -- see docs/product/WEEKLY_FOUNDER_REVIEW_V1.md's own fact
// classification table for which is which.
//
// THE DOUBLE-COUNT RULE (the directive's own "audit event semantics
// carefully" instruction): a Universal Capture (Phase 23) produces ONE
// venture_missions row whose created_at, learning_recorded_at, and
// completed_at are all set in a single atomic INSERT -- meaning all three
// resulting history events (action_added, learning_recorded,
// action_completed) share the EXACT SAME occurred_at timestamp. An
// ordinary mission's three events are, in real founder behavior, always
// spread across different moments (create it, later reflect, later still
// complete it). This module uses that structural fact -- never a
// mission_type/source flag, which get_venture_history() doesn't expose --
// to classify a mission_id as a capture, and counts it exactly ONCE
// (under "observations captured"), never also under "actions completed"
// or "learnings recorded".
//
// Zero "@/..." alias imports -- importable directly by plain Node, same
// convention as lib/fundraising/*.ts, lib/captureSignals.ts.

import type {
  VentureHistoryAssumptionChange,
  VentureHistoryCategoryChange,
  VentureHistoryEvent,
  VentureHistoryResponse,
} from "../../types/ideaLab.ts";

export const REVIEW_WINDOW_DAYS = 7;
export const REVIEW_WINDOW_LABEL = "Last 7 days";

export interface WhatYouDid {
  readonly actionsCompleted: number;
  readonly observationsCaptured: number;
  readonly learningsRecorded: number;
  readonly modelUpdates: number;
}

export interface LearningItem {
  readonly text: string; // verbatim, never rewritten
  readonly occurredAt: string;
  readonly missionTitle: string | null;
}

export interface VpsChange {
  readonly before: number | null;
  readonly after: number | null;
}

export interface StrongestMovement {
  readonly label: string;
  readonly before: number;
  readonly after: number;
  readonly direction: "positive" | "negative";
}

export interface WeeklyReviewData {
  readonly windowLabel: string;
  // True only when the venture has essentially no history at all yet
  // (nothing beyond its own creation) -- distinct from a "quiet week" on
  // an otherwise-active venture, which needs different, honest copy
  // (Part 11 vs Part 12).
  readonly isBrandNew: boolean;
  // True when there is real activity of any kind within the window --
  // the single signal the UI uses to choose between the active-week
  // layout and the quiet-week layout. Never inferred beyond the actual
  // counts below.
  readonly hasActivityInWindow: boolean;
  readonly whatYouDid: WhatYouDid;
  readonly whatYouLearned: readonly LearningItem[];
  readonly vpsChange: VpsChange | null; // null when no model update occurred in the window
  readonly assumptionChanges: readonly VentureHistoryAssumptionChange[];
  readonly strongestMovement: StrongestMovement | null;
}

const CATEGORY_CHANGE_EPSILON = 0.05; // mirrors dashboard's own categoryChangeExplain.ts / the backend's own threshold

function withinWindow(event: VentureHistoryEvent, sinceMs: number): boolean {
  return new Date(event.occurred_at).getTime() >= sinceMs;
}

// A mission_id is a "capture" (Phase 23's Universal Capture, Part 5's own
// double-count concern) iff all three of its lifecycle events exist and
// share the exact same occurred_at -- see this module's own docstring for
// why that's a safe, structural signal.
function classifyMissions(events: readonly VentureHistoryEvent[]): {
  captureIds: Set<number>;
  ordinaryCompletedIds: Set<number>;
  ordinaryLearningIds: Set<number>;
} {
  const byMission = new Map<number, { added?: string; learned?: string; completed?: string }>();

  for (const event of events) {
    if (event.mission_id === null) continue;
    const entry = byMission.get(event.mission_id) ?? {};
    if (event.event_type === "action_added") entry.added = event.occurred_at;
    if (event.event_type === "learning_recorded") entry.learned = event.occurred_at;
    if (event.event_type === "action_completed") entry.completed = event.occurred_at;
    byMission.set(event.mission_id, entry);
  }

  const captureIds = new Set<number>();
  const ordinaryCompletedIds = new Set<number>();
  const ordinaryLearningIds = new Set<number>();

  for (const [missionId, { added, learned, completed }] of byMission) {
    const isCapture = added !== undefined && learned !== undefined && completed !== undefined && added === learned && learned === completed;
    if (isCapture) {
      captureIds.add(missionId);
      continue;
    }
    if (completed !== undefined) ordinaryCompletedIds.add(missionId);
    if (learned !== undefined) ordinaryLearningIds.add(missionId);
  }

  return { captureIds, ordinaryCompletedIds, ordinaryLearningIds };
}

function aggregateAssumptionChanges(modelUpdateEventsChronological: readonly VentureHistoryEvent[]): VentureHistoryAssumptionChange[] {
  // First-in-window "before" paired with last-in-window "after", per
  // field -- an honest week-start-to-week-end comparison even when
  // several model updates happened, never a fabricated running total.
  // Input must already be chronological (oldest first).
  const firstBefore = new Map<string, { label: string; before: string }>();
  const lastAfter = new Map<string, { label: string; after: string }>();

  for (const event of modelUpdateEventsChronological) {
    for (const change of event.assumption_changes) {
      if (!firstBefore.has(change.field_path)) {
        firstBefore.set(change.field_path, { label: change.label, before: change.before });
      }
      lastAfter.set(change.field_path, { label: change.label, after: change.after });
    }
  }

  const result: VentureHistoryAssumptionChange[] = [];
  for (const [fieldPath, { label, before }] of firstBefore) {
    const after = lastAfter.get(fieldPath)?.after;
    if (after === undefined) continue;
    if (before === after) continue; // net-zero across the week -- not a real change to report
    result.push({ field_path: fieldPath, label, before, after });
  }
  return result;
}

function aggregateStrongestMovement(modelUpdateEventsChronological: readonly VentureHistoryEvent[]): StrongestMovement | null {
  const firstBefore = new Map<string, { label: string; before: number | null }>();
  const lastAfter = new Map<string, { label: string; after: number | null }>();

  for (const event of modelUpdateEventsChronological) {
    for (const change of event.category_changes as VentureHistoryCategoryChange[]) {
      if (!firstBefore.has(change.key)) {
        firstBefore.set(change.key, { label: change.label, before: change.before });
      }
      lastAfter.set(change.key, { label: change.label, after: change.after });
    }
  }

  let strongest: StrongestMovement | null = null;
  for (const [key, { label, before }] of firstBefore) {
    const after = lastAfter.get(key)?.after;
    if (before === null || after === null || after === undefined) continue;
    const delta = after - before;
    if (Math.abs(delta) < CATEGORY_CHANGE_EPSILON) continue;
    if (strongest === null || Math.abs(delta) > Math.abs(strongest.after - strongest.before)) {
      strongest = { label, before, after, direction: delta > 0 ? "positive" : "negative" };
    }
    void key;
  }
  return strongest;
}

export function buildWeeklyReview(
  history: VentureHistoryResponse,
  now: Date = new Date(),
  windowDays: number = REVIEW_WINDOW_DAYS
): WeeklyReviewData {
  const sinceMs = now.getTime() - windowDays * 24 * 60 * 60 * 1000;

  // A "brand-new" venture is one whose ENTIRE history (not just this
  // window) is nothing beyond its own creation -- Part 12's distinct
  // state from a merely-quiet week on an otherwise-real venture.
  const isBrandNew = history.events.filter((e) => e.event_type !== "venture_created").length === 0;

  const inWindow = history.events.filter((e) => e.event_type !== "venture_created" && withinWindow(e, sinceMs));

  const { captureIds, ordinaryCompletedIds, ordinaryLearningIds } = classifyMissions(inWindow);

  const modelUpdateEvents = inWindow.filter((e) => e.event_type === "model_updated");
  // get_venture_history() returns events newest-first; every aggregation
  // here needs chronological (oldest-first) order for an honest
  // first-of-window -> last-of-window comparison.
  const modelUpdateEventsChronological = [...modelUpdateEvents].reverse();

  const whatYouDid: WhatYouDid = {
    actionsCompleted: ordinaryCompletedIds.size,
    observationsCaptured: captureIds.size,
    learningsRecorded: ordinaryLearningIds.size,
    modelUpdates: modelUpdateEvents.length,
  };

  const learningEvents = inWindow.filter((e) => e.event_type === "learning_recorded" && e.description);
  const whatYouLearned: LearningItem[] = learningEvents
    .slice(0, 3) // already newest-first; "prefer the most meaningful/recent few" (Part 6)
    .map((e) => ({ text: e.description as string, occurredAt: e.occurred_at, missionTitle: e.mission_title }));

  const vpsChange: VpsChange | null =
    modelUpdateEventsChronological.length > 0
      ? {
          before: modelUpdateEventsChronological[0].before_vps,
          after: modelUpdateEventsChronological[modelUpdateEventsChronological.length - 1].after_vps,
        }
      : null;

  const assumptionChanges = aggregateAssumptionChanges(modelUpdateEventsChronological);
  const strongestMovement = aggregateStrongestMovement(modelUpdateEventsChronological);

  const hasActivityInWindow =
    whatYouDid.actionsCompleted > 0 ||
    whatYouDid.observationsCaptured > 0 ||
    whatYouDid.learningsRecorded > 0 ||
    whatYouDid.modelUpdates > 0;

  return {
    windowLabel: REVIEW_WINDOW_LABEL,
    isBrandNew,
    hasActivityInWindow,
    whatYouDid,
    whatYouLearned,
    vpsChange,
    assumptionChanges,
    strongestMovement,
  };
}
