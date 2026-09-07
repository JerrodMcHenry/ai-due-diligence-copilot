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

export interface VentureFinancialsResponse {
  latest_snapshot: FinancialSnapshot | null;
  derived: DerivedFinancialMetrics | null;
  projection: ProjectedMonth[];
}

export interface FinancialHistoryResponse {
  snapshots: FinancialSnapshot[];
}
