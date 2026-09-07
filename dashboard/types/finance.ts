// Phase 35B -- Financial State Persistence + Runway Engine V1. Mirrors
// app/models/venture_financials.py exactly. See
// docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md for the full design.
//
// Every money field is INTEGER CENTS, matching the database and the
// Python calculation engine exactly -- dollar<->cents conversion happens
// ONLY in dashboard/lib/finance/money.ts, never here. `null` always means
// "unknown," never zero -- see CreateFinancialSnapshotRequest's own
// field-level comment.

export interface CreateFinancialSnapshotRequest {
  as_of_date: string; // "YYYY-MM-DD"
  cash_balance_cents: number | null;
  monthly_recurring_revenue_cents: number | null;
  monthly_non_recurring_revenue_cents: number | null;
  payroll_cents: number | null;
  contractors_cents: number | null;
  software_cents: number | null;
  marketing_cents: number | null;
  rent_cents: number | null;
  professional_services_cents: number | null;
  other_expenses_cents: number | null;
}

export interface FinancialSnapshot extends CreateFinancialSnapshotRequest {
  id: number;
  venture_id: number;
  user_id: string;
  recorded_at: string;
}

// Mirrors app/ai/financial_engine.py::compute_derived_metrics() exactly.
export type FinancialStatus = "insufficient_data" | "cash_flow_positive" | "break_even" | "burning" | "out_of_cash";

export interface DerivedFinancialMetrics {
  total_monthly_revenue_cents: number | null;
  total_monthly_expenses_cents: number | null;
  net_burn_cents: number | null;
  runway_months: number | null;
  status: FinancialStatus;
}

export interface ProjectedMonth {
  month_index: number;
  date: string; // "YYYY-MM-DD"
  starting_cash_cents: number;
  revenue_cents: number;
  expenses_cents: number;
  net_cash_change_cents: number;
  ending_cash_cents: number;
  depleted: boolean;
}

// --- Phase 35C -- Hiring + Operating Plan Engine V1 -------------------------
// Mirrors app/models/venture_hire_plans.py exactly.

export type EmploymentType = "employee" | "contractor";
export type HirePlanStatus = "planned" | "cancelled" | "actualized";

export interface CreateHirePlanRequest {
  role: string;
  employment_type: EmploymentType;
  // Employee: annual_salary_cents + burden_percent required, monthly_cost_cents null.
  // Contractor: monthly_cost_cents required, the other two null.
  annual_salary_cents: number | null;
  burden_percent: number | null;
  monthly_cost_cents: number | null;
  one_time_cost_cents: number | null;
  start_date: string; // "YYYY-MM-DD"
  end_date: string | null;
}

export interface HirePlan extends CreateHirePlanRequest {
  id: number;
  venture_id: number;
  user_id: string;
  status: HirePlanStatus;
  created_at: string;
  updated_at: string;
  // Always DERIVED (app/ai/financial_engine.py) -- never re-computed on
  // the frontend, so the number a founder sees can never drift from the
  // one the projection actually used.
  computed_monthly_cost_cents: number | null;
  computed_annual_cost_cents: number | null;
}

export interface ProjectedMonthWithPlan extends ProjectedMonth {
  plan_expense_impact_cents: number;
  plan_revenue_active: boolean;
  active_plan_item_ids: number[];
}

export interface HireImpactPreview {
  computed_monthly_cost_cents: number | null;
  computed_annual_cost_cents: number | null;
  baseline_projection: ProjectedMonthWithPlan[];
  with_hire_projection: ProjectedMonthWithPlan[];
}

// --- Phase 35D -- Operating Scenarios + Financial Plan Reconciliation V1 ---
// Mirrors app/models/venture_financial_plans.py exactly.

export type FinancialPlanType = "revenue_target" | "expense_change";
export type ExpenseCategory = "payroll" | "contractors" | "software" | "marketing" | "rent" | "professional_services" | "other";
export type PlanStatus = "planned" | "cancelled" | "actualized";

export interface CreateFinancialPlanRequest {
  plan_type: FinancialPlanType;
  label: string;
  // revenue_target: null. expense_change: required.
  category: ExpenseCategory | null;
  // revenue_target: an ABSOLUTE monthly revenue target (replaces base
  // revenue outright). expense_change: a SIGNED recurring monthly delta
  // (positive = increase, negative = cut).
  amount_cents: number;
  start_date: string;
  end_date: string | null;
}

export interface FinancialPlan extends CreateFinancialPlanRequest {
  id: number;
  venture_id: number;
  user_id: string;
  status: PlanStatus;
  last_reconciled_snapshot_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface FinancialPlanImpactPreview {
  baseline_projection: ProjectedMonthWithPlan[];
  with_plan_projection: ProjectedMonthWithPlan[];
}

export interface CreateScenarioRequest {
  name: string;
  hire_plan_ids: number[];
  financial_plan_ids: number[];
}

export interface Scenario extends CreateScenarioRequest {
  id: number;
  venture_id: number;
  user_id: string;
  created_at: string;
  updated_at: string;
  // Computed live at read time -- never stored. See ScenarioResponse's
  // own docstring in app/models/venture_financial_plans.py for why.
  assumptions: string[];
  projection: ProjectedMonthWithPlan[];
  ending_cash_at_horizon_cents: number | null;
  depletion_date: string | null;
}

export interface ReconciliationItem {
  plan_kind: "hire" | "financial";
  plan_id: number;
  label: string;
  monthly_amount_cents: number | null;
  start_date: string;
}

export interface VentureFinancialsResponse {
  latest_snapshot: FinancialSnapshot | null;
  derived: DerivedFinancialMetrics | null;
  projection: ProjectedMonth[];
  hire_plans: HirePlan[];
  financial_plans: FinancialPlan[];
  projection_with_plan: ProjectedMonthWithPlan[];
  pending_reconciliation: ReconciliationItem[];
}

export interface FinancialHistoryResponse {
  snapshots: FinancialSnapshot[];
}
