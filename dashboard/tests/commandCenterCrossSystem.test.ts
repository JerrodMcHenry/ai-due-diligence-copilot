// Phase 38C -- Cross-System Founder Intelligence V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/commandCenterPriority.test.ts (this repo has no jest/vitest), run
// directly by Node's native TypeScript support.
//
// Run with:
//   node tests/commandCenterCrossSystem.test.ts
import {
  findRevenueTargetDivergence,
  findStaleFinanceContext,
} from "../lib/build/commandCenterCrossSystem.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// --- findRevenueTargetDivergence ------------------------------------------

function test_no_plans_no_divergence() {
  const result = findRevenueTargetDivergence([], { total_monthly_revenue_cents: 500000 }, "2026-09-01");
  expect(result === null, "no financial plans at all must never produce a divergence");
}

function test_no_derived_metrics_no_divergence() {
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, null, "2026-09-01");
  expect(result === null, "unknown Finance state (no derived metrics) must never produce a divergence");
}

function test_unknown_actual_revenue_no_divergence() {
  // Test Case P: unknown financial values must never become a fake zero
  // or a fabricated comparison.
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: null }, "2026-09-01");
  expect(result === null, "unknown actual revenue (insufficient_data) must never produce a divergence");
}

function test_expense_change_plans_are_never_compared() {
  // Section 10's own Plan Baseline Problem: expense_change plans store a
  // signed delta against a baseline this codebase never freezes, so they
  // must never be treated as a Plan x Actual comparison.
  const plans = [
    { plan_type: "expense_change", status: "planned", label: "Add a support hire", start_date: "2026-08-01", amount_cents: 700000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 500000 }, "2026-09-01");
  expect(result === null, "expense_change plans must never be used for a Plan x Actual comparison");
}

function test_plan_not_yet_started_no_divergence() {
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-12-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 500000 }, "2026-09-01");
  expect(result === null, "a revenue target whose start_date hasn't arrived yet must not be compared");
}

function test_cancelled_plan_ignored() {
  // Test Case J: a cancelled plan must never produce an active-plan
  // consequence.
  const plans = [
    { plan_type: "revenue_target", status: "cancelled", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 2200000 }, "2026-09-01");
  expect(result === null, "a cancelled revenue target must never be surfaced");
}

function test_matching_actual_no_false_divergence() {
  // Test Case F: matching actual is not a divergence.
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 3000000 }, "2026-09-01");
  expect(result === null, "an actual that exactly matches the plan must not be surfaced as a divergence");
}

function test_real_divergence_surfaced() {
  // Test Case G: a real divergence is a defensible, neutral fact.
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 2200000 }, "2026-09-01");
  expect(result !== null, "a real difference between planned and actual revenue must be surfaced");
  expect(result!.plannedAmountCents === 3000000, "plannedAmountCents must be the plan's own amount_cents verbatim");
  expect(result!.actualAmountCents === 2200000, "actualAmountCents must be the derived metric verbatim");
  expect(result!.planLabel === "Reach $30K MRR", "planLabel must be the plan's own label verbatim");
}

function test_most_recently_started_plan_wins() {
  const plans = [
    { plan_type: "revenue_target", status: "planned", label: "Reach $20K MRR", start_date: "2026-06-01", amount_cents: 2000000 },
    { plan_type: "revenue_target", status: "planned", label: "Reach $30K MRR", start_date: "2026-08-01", amount_cents: 3000000 },
  ];
  const result = findRevenueTargetDivergence(plans, { total_monthly_revenue_cents: 2200000 }, "2026-09-01");
  expect(result !== null, "expected a divergence");
  expect(result!.planLabel === "Reach $30K MRR", "the most recently started due target must win when more than one has come due");
}

// --- findStaleFinanceContext -----------------------------------------------

function test_no_focus_text_no_staleness() {
  const result = findStaleFinanceContext(null, "2026-01-01", new Date("2026-09-01"));
  expect(result === null, "no Build focus text must never produce a staleness statement");
}

function test_no_snapshot_no_staleness() {
  const result = findStaleFinanceContext("Understand retention", null, new Date("2026-09-01"));
  expect(result === null, "no financial snapshot at all must never produce a staleness statement");
}

function test_fresh_snapshot_no_staleness() {
  const result = findStaleFinanceContext("Understand retention", "2026-08-15", new Date("2026-09-01"));
  expect(result === null, "a snapshot within the 60-day window must not be flagged stale");
}

function test_stale_snapshot_surfaced() {
  const result = findStaleFinanceContext("Understand retention", "2026-01-01", new Date("2026-09-01"));
  expect(result !== null, "a snapshot older than 60 days must be flagged stale");
  expect(result!.focusText === "Understand retention", "focusText must be the Build focus text verbatim");
  expect(result!.daysStale > 60, "daysStale must reflect the real elapsed days, not a fixed number");
}

const TESTS = [
  test_no_plans_no_divergence,
  test_no_derived_metrics_no_divergence,
  test_unknown_actual_revenue_no_divergence,
  test_expense_change_plans_are_never_compared,
  test_plan_not_yet_started_no_divergence,
  test_cancelled_plan_ignored,
  test_matching_actual_no_false_divergence,
  test_real_divergence_surfaced,
  test_most_recently_started_plan_wins,
  test_no_focus_text_no_staleness,
  test_no_snapshot_no_staleness,
  test_fresh_snapshot_no_staleness,
  test_stale_snapshot_surfaced,
];

function main(): void {
  console.log("\nPhase 38C -- Cross-System Founder Intelligence V1 tests");
  console.log("-".repeat(72));

  const failures: string[] = [];

  for (const test of TESTS) {
    try {
      test();
      console.log(`PASS  ${test.name}`);
    } catch (error) {
      console.log(`FAIL  ${test.name}\n      ${(error as Error).message}`);
      failures.push(test.name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
