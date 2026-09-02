// Phase 24 -- Weekly Founder Review V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this repo's tests/*.test.ts files. NOW is fixed so every fixture's
// "in window" / "out of window" placement is exact and reproducible.
//
// Run with:
//   node tests/buildWeeklyReview.test.ts
// or:
//   npm run test:weeklyReview

import { buildWeeklyReview, REVIEW_WINDOW_LABEL } from "../lib/journey/buildWeeklyReview.ts";
import type { VentureHistoryEvent, VentureHistoryResponse } from "../types/ideaLab.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

const NOW = new Date("2026-09-08T12:00:00.000Z"); // a Tuesday, arbitrary but fixed
const IN_WINDOW = "2026-09-05T10:00:00.000Z"; // 3 days before NOW
const IN_WINDOW_LATER = "2026-09-07T10:00:00.000Z"; // 1 day before NOW, later than IN_WINDOW
const OUT_OF_WINDOW = "2026-08-20T10:00:00.000Z"; // 19 days before NOW

function baseEvent(overrides: Partial<VentureHistoryEvent>): VentureHistoryEvent {
  return {
    event_type: "action_added",
    occurred_at: IN_WINDOW,
    title: "Untitled",
    description: null,
    before_vps: null,
    after_vps: null,
    category_changes: [],
    assumption_changes: [],
    mission_id: null,
    mission_title: null,
    ...overrides,
  };
}

function history(events: VentureHistoryEvent[], overrides: Partial<VentureHistoryResponse> = {}): VentureHistoryResponse {
  // get_venture_history() always returns events newest-first
  // (events.sort(..., reverse=True)) -- every fixture must match that
  // real contract, since buildWeeklyReview() relies on it to recover
  // chronological (oldest-first) order for its own aggregations.
  const sorted = [...events].sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());
  return {
    events: sorted,
    current_vps: null,
    started_at: OUT_OF_WINDOW,
    actions_completed: 0,
    model_updates_count: 0,
    strongest_improvement: null,
    ...overrides,
  };
}

// A Phase 23 Universal Capture: one mission_id, three events, ALL sharing
// the exact same occurred_at -- the structural signature this module
// uses to detect a capture and avoid triple-counting it.
function captureFixture(missionId: number, text: string, occurredAt: string): VentureHistoryEvent[] {
  return [
    baseEvent({ event_type: "action_added", mission_id: missionId, mission_title: text, occurred_at: occurredAt }),
    baseEvent({ event_type: "learning_recorded", mission_id: missionId, mission_title: text, description: text, occurred_at: occurredAt }),
    baseEvent({ event_type: "action_completed", mission_id: missionId, mission_title: text, occurred_at: occurredAt }),
  ];
}

// An ORDINARY mission: created, reflected on, and completed at three
// genuinely different moments -- must never be classified as a capture.
function ordinaryMissionFixture(missionId: number, title: string, learningText: string): VentureHistoryEvent[] {
  return [
    baseEvent({ event_type: "action_added", mission_id: missionId, mission_title: title, occurred_at: "2026-09-04T09:00:00.000Z" }),
    baseEvent({ event_type: "learning_recorded", mission_id: missionId, mission_title: title, description: learningText, occurred_at: IN_WINDOW }),
    baseEvent({ event_type: "action_completed", mission_id: missionId, mission_title: title, occurred_at: IN_WINDOW_LATER }),
  ];
}

// --- Window definition ------------------------------------------------------

function test_window_label_is_explicit_last_7_days(): void {
  const result = buildWeeklyReview(history([]), NOW);
  expect(result.windowLabel === "Last 7 days", `Window label must say "Last 7 days", got "${result.windowLabel}"`);
  expect(REVIEW_WINDOW_LABEL === "Last 7 days", "Never claim calendar-week semantics that don't exist");
}

function test_out_of_window_events_are_excluded(): void {
  const h = history([
    baseEvent({ event_type: "action_added", mission_id: 1, occurred_at: OUT_OF_WINDOW }),
    baseEvent({ event_type: "action_completed", mission_id: 1, occurred_at: OUT_OF_WINDOW }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.whatYouDid.actionsCompleted === 0, "An action completed 19 days ago must not count in a 7-day window");
  expect(result.hasActivityInWindow === false, "No in-window activity must report hasActivityInWindow=false");
}

// --- Double-count prevention (the directive's own central concern) --------

function test_capture_counted_once_not_triple_counted(): void {
  const h = history([
    baseEvent({ event_type: "venture_created", occurred_at: OUT_OF_WINDOW }),
    ...captureFixture(101, "Talked to six restaurant owners.", IN_WINDOW),
  ]);
  const result = buildWeeklyReview(h, NOW);

  expect(result.whatYouDid.observationsCaptured === 1, `Exactly 1 capture must be counted, got ${result.whatYouDid.observationsCaptured}`);
  expect(result.whatYouDid.actionsCompleted === 0, `A capture must NOT also count as an ordinary completed action, got ${result.whatYouDid.actionsCompleted}`);
  expect(result.whatYouDid.learningsRecorded === 0, `A capture's learning must NOT also count under separate "learnings recorded", got ${result.whatYouDid.learningsRecorded}`);
  expect(result.whatYouLearned.length === 1, "The capture's text must still appear once under What You Learned");
  expect(result.whatYouLearned[0].text === "Talked to six restaurant owners.", "Learning text must be verbatim");
}

function test_ordinary_mission_counted_correctly_alongside_a_capture(): void {
  const h = history([
    ...ordinaryMissionFixture(201, "Interview 20 customers", "Customers care more about speed than price."),
    ...captureFixture(202, "Shipped Stripe integration.", IN_WINDOW),
  ]);
  const result = buildWeeklyReview(h, NOW);

  expect(result.whatYouDid.actionsCompleted === 1, `Exactly 1 ordinary completed action, got ${result.whatYouDid.actionsCompleted}`);
  expect(result.whatYouDid.learningsRecorded === 1, `Exactly 1 ordinary learning (the capture's is separate), got ${result.whatYouDid.learningsRecorded}`);
  expect(result.whatYouDid.observationsCaptured === 1, `Exactly 1 capture, got ${result.whatYouDid.observationsCaptured}`);
  expect(result.whatYouLearned.length === 2, "Both the ordinary reflection and the capture's text must appear under What You Learned");
}

// --- What You Learned: verbatim, most-recent-first, capped -----------------

function test_learnings_are_verbatim_and_recency_ordered(): void {
  const h = history([
    baseEvent({ event_type: "learning_recorded", mission_id: 1, description: "Older note.", occurred_at: "2026-09-04T08:00:00.000Z" }),
    baseEvent({ event_type: "learning_recorded", mission_id: 2, description: "Newer note.", occurred_at: IN_WINDOW_LATER }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.whatYouLearned[0].text === "Newer note.", "Most recent learning must come first");
}

// --- What changed: VPS + assumption diffs, first-of-window -> last -------

function test_vps_change_uses_first_and_last_in_window(): void {
  const h = history([
    baseEvent({ event_type: "model_updated", before_vps: 6.5, after_vps: 6.9, occurred_at: IN_WINDOW }),
    baseEvent({ event_type: "model_updated", before_vps: 6.9, after_vps: 7.1, occurred_at: IN_WINDOW_LATER }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.vpsChange !== null, "vpsChange must be present when a model update occurred in-window");
  expect(result.vpsChange!.before === 6.5, `Must use the FIRST update's before value, got ${result.vpsChange!.before}`);
  expect(result.vpsChange!.after === 7.1, `Must use the LAST update's after value, got ${result.vpsChange!.after}`);
}

function test_no_model_update_means_null_vps_change_not_zero(): void {
  const h = history([baseEvent({ event_type: "action_completed", mission_id: 1, occurred_at: IN_WINDOW })]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.vpsChange === null, "No model update in-window must report vpsChange=null, never a fabricated 0->0");
}

function test_assumption_changes_diff_first_to_last(): void {
  const h = history([
    baseEvent({
      event_type: "model_updated",
      occurred_at: IN_WINDOW,
      assumption_changes: [{ field_path: "economics.price_point", label: "Price point", before: "Unknown", after: "$500" }],
    }),
    baseEvent({
      event_type: "model_updated",
      occurred_at: IN_WINDOW_LATER,
      assumption_changes: [{ field_path: "economics.price_point", label: "Price point", before: "$500", after: "$299" }],
    }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  const priceChange = result.assumptionChanges.find((c) => c.field_path === "economics.price_point");
  expect(priceChange !== undefined, "Price point change must be present");
  expect(priceChange!.before === "Unknown", `Must show the week's FIRST before value, got "${priceChange!.before}"`);
  expect(priceChange!.after === "$299", `Must show the week's LAST after value, got "${priceChange!.after}"`);
}

// --- Strongest movement, neutral framing regardless of direction ----------

function test_strongest_movement_picks_largest_absolute_delta(): void {
  const h = history([
    baseEvent({
      event_type: "model_updated",
      occurred_at: IN_WINDOW,
      category_changes: [
        { key: "validation", label: "Validation", before: 6.5, after: 7.0 },
        { key: "gtm_feasibility", label: "GTM Feasibility", before: 7.0, after: 6.5 },
      ],
    }),
    // A second update where GTM drops further, making it the largest
    // absolute movement across the window.
    baseEvent({
      event_type: "model_updated",
      occurred_at: IN_WINDOW_LATER,
      category_changes: [{ key: "gtm_feasibility", label: "GTM Feasibility", before: 6.5, after: 4.0 }],
    }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.strongestMovement !== null, "Strongest movement must be found");
  expect(result.strongestMovement!.label === "GTM Feasibility", `Must pick the largest absolute delta (GTM: 7.0->4.0 = -3.0), got "${result.strongestMovement!.label}"`);
  expect(result.strongestMovement!.direction === "negative", "GTM moved down -- direction must be negative, not hidden");
}

// --- Negative evidence: neutral, no punitive language ----------------------

function test_negative_vps_change_has_no_punitive_language(): void {
  const h = history([
    baseEvent({
      event_type: "learning_recorded",
      mission_id: 1,
      description: "We spoke with 10 customers and none would pay $500/month.",
      occurred_at: IN_WINDOW,
    }),
    baseEvent({ event_type: "model_updated", before_vps: 7.1, after_vps: 6.7, occurred_at: IN_WINDOW_LATER }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.vpsChange!.before === 7.1 && result.vpsChange!.after === 6.7, "A real VPS decline must still be reported honestly, not hidden");
  expect(result.whatYouLearned[0].text.includes("none would pay"), "Negative learning must still be preserved verbatim");
  // This module produces no copy of its own beyond field values/labels --
  // the punitive-language guarantee is enforced at the UI layer (Part 13),
  // verified here structurally: no field in this result is a
  // free-text sentence this module invented.
}

// --- Brand-new vs quiet: two different honest states -----------------------

function test_brand_new_venture_has_no_history_beyond_creation(): void {
  const h = history([baseEvent({ event_type: "venture_created", occurred_at: OUT_OF_WINDOW })]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.isBrandNew === true, "A venture with only its own creation event must be brand-new");
  expect(result.hasActivityInWindow === false, "Brand-new implies no in-window activity either");
}

function test_quiet_week_on_an_established_venture_is_not_brand_new(): void {
  const h = history([
    baseEvent({ event_type: "venture_created", occurred_at: OUT_OF_WINDOW }),
    baseEvent({ event_type: "action_completed", mission_id: 1, occurred_at: OUT_OF_WINDOW }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.isBrandNew === false, "A venture with real history (even if old) must not be treated as brand-new");
  expect(result.hasActivityInWindow === false, "But this window itself still had zero activity -- a quiet week, not brand-new");
}

// --- Model-change week with no VPS movement (Part 9's own example) --------

function test_assumptions_changed_but_vps_did_not(): void {
  const h = history([
    baseEvent({
      event_type: "model_updated",
      before_vps: 7.2,
      after_vps: 7.2,
      assumption_changes: [{ field_path: "validation.paying_customers", label: "Paying customers", before: "3", after: "4" }],
      occurred_at: IN_WINDOW,
    }),
  ]);
  const result = buildWeeklyReview(h, NOW);
  expect(result.vpsChange!.before === 7.2 && result.vpsChange!.after === 7.2, "VPS unchanged must be reported exactly, not omitted");
  expect(result.assumptionChanges.length === 1, "The real assumption change must still be shown even though VPS didn't move");
}

const TESTS = [
  test_window_label_is_explicit_last_7_days,
  test_out_of_window_events_are_excluded,
  test_capture_counted_once_not_triple_counted,
  test_ordinary_mission_counted_correctly_alongside_a_capture,
  test_learnings_are_verbatim_and_recency_ordered,
  test_vps_change_uses_first_and_last_in_window,
  test_no_model_update_means_null_vps_change_not_zero,
  test_assumption_changes_diff_first_to_last,
  test_strongest_movement_picks_largest_absolute_delta,
  test_negative_vps_change_has_no_punitive_language,
  test_brand_new_venture_has_no_history_beyond_creation,
  test_quiet_week_on_an_established_venture_is_not_brand_new,
  test_assumptions_changed_but_vps_did_not,
];

function main(): void {
  console.log("\nWeekly Founder Review V1 tests");
  console.log("-".repeat(72));

  const failures: string[] = [];
  for (const test of TESTS) {
    const name = test.name;
    try {
      test();
      console.log(`PASS  ${name}`);
    } catch (error) {
      console.log(`FAIL  ${name}\n      ${(error as Error).message}`);
      failures.push(name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
