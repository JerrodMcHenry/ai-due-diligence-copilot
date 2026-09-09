// Phase 38C -- Cross-System Founder Intelligence V1
// (docs/product/SIE_FOUNDER_COMMAND_CENTER_V1.md is the governing spec).
//
// Pure, deterministic, zero I/O -- same discipline as
// commandCenterPriority.ts and this codebase's other journey resolvers.
// Every function here reasons only over data the Command Center already
// has on hand from its two existing fetches (GET .../recommendation,
// GET .../financials) -- no new backend endpoint, no new fetch, no AI.
//
// Deliberately does NOT implement Decision x Finance: audited
// `venture_decisions` directly (app/models/venture_missions.py's
// VentureDecisionResponse) and found its only structural relationship is
// `related_mission_id` (Build), never a reference to any
// venture_hire_plans/venture_financial_plans row. Implementing a
// connection here would require either text-matching a decision's own
// founder_choice string against a hire's role/label (explicitly
// forbidden by this phase's own directive) or a new schema column this
// phase's own default expectation (no migration) argues against adding
// speculatively. See this phase's own final report for the full finding
// and the smallest schema change that WOULD close this gap, left
// unbuilt.

// --- PLAN x ACTUAL (revenue_target only) ------------------------------
//
// Section 10's own "Plan Baseline Problem": `expense_change` plans store
// a SIGNED DELTA against whatever a category's value was AT THE TIME the
// plan started -- and this codebase deliberately never freezes that
// baseline (ScenarioResponse's own docstring, app/models/
// venture_financial_plans.py: "assumptions/projection/... are all
// COMPUTED at read time, never stored"). Reconstructing "what payroll
// was expected to become" for an expense_change plan would require
// either a historical snapshot dated at-or-before the plan's start_date
// (not guaranteed to exist, and this module never assumes one does) or a
// new frozen-baseline column (a real, but NOT SMALL, schema change) --
// neither is implemented here, per Section 10's own explicit instruction
// not to fake plan-vs-actual history.
//
// `revenue_target` plans are structurally different: `amount_cents` is
// an ABSOLUTE monthly figure (see CreateFinancialPlanRequest's own
// docstring, app/models/venture_financial_plans.py -- "it replaces total
// revenue outright"), so comparing it against the latest snapshot's own
// `total_monthly_revenue_cents` needs no historical reconstruction at
// all. This is the one Plan x Actual connection this phase implements.

type MinimalFinancialPlan = {
  plan_type: string;
  status: string;
  label: string;
  start_date: string; // "YYYY-MM-DD"
  amount_cents: number;
};

type MinimalDerivedMetrics = {
  total_monthly_revenue_cents: number | null;
};

export type RevenueTargetDivergence = {
  planLabel: string;
  plannedAmountCents: number;
  actualAmountCents: number;
  startDate: string;
};

export function findRevenueTargetDivergence(
  financialPlans: MinimalFinancialPlan[],
  derived: MinimalDerivedMetrics | null,
  asOfDate: string | null
): RevenueTargetDivergence | null {
  if (!derived || derived.total_monthly_revenue_cents === null || !asOfDate) {
    return null;
  }

  const eligible = financialPlans
    .filter((p) => p.plan_type === "revenue_target" && p.status === "planned" && p.start_date <= asOfDate)
    // If more than one revenue target has come due, the most recently
    // started one is the founder's own current expectation.
    .sort((a, b) => (a.start_date < b.start_date ? 1 : -1));

  const plan = eligible[0];
  if (!plan) {
    return null;
  }

  // Test Case F -- a matching actual is not a divergence at all; no
  // magnitude/materiality threshold is applied (that would itself be an
  // invented rule) -- plain inequality is the only test.
  if (plan.amount_cents === derived.total_monthly_revenue_cents) {
    return null;
  }

  return {
    planLabel: plan.label,
    plannedAmountCents: plan.amount_cents,
    actualAmountCents: derived.total_monthly_revenue_cents,
    startDate: plan.start_date,
  };
}

// --- BUILD x FINANCE (snapshot staleness only) -------------------------
//
// Section 6's own explicit rule: no arbitrary runway threshold. This
// connection never touches runway/burn/cash qualitatively at all -- it
// only ever states a snapshot's own age, using the 60-day staleness
// figure this same design document already established in its own §22
// (Phase 38A), not a new number invented for this phase. Never fires
// when Finance itself already owns the primary "what matters now" slot
// (the out_of_cash financial priority card already names its own
// snapshot date) -- see CommandCenter.tsx's own placement logic.
const STALE_SNAPSHOT_DAYS = 60;

export type StaleFinanceContext = {
  focusText: string;
  daysStale: number;
};

export function findStaleFinanceContext(
  currentFocusText: string | null,
  snapshotDate: string | null,
  today: Date
): StaleFinanceContext | null {
  if (!currentFocusText || !snapshotDate) {
    return null;
  }

  const snapshotMs = new Date(`${snapshotDate}T00:00:00`).getTime();
  const daysStale = Math.floor((today.getTime() - snapshotMs) / (1000 * 60 * 60 * 24));

  if (daysStale <= STALE_SNAPSHOT_DAYS) {
    return null;
  }

  return { focusText: currentFocusText, daysStale };
}
