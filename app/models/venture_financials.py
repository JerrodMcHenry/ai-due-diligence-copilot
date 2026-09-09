"""
Phase 35B -- Financial State Persistence + Runway Engine V1 --
request/response contracts.

Its own file, mirroring app/models/venture_missions.py's own precedent
(a conceptually adjacent-but-distinct concern gets its own module, not a
grab-bag addition to idea_lab.py). See
docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md for the full design.

Every money field is INTEGER CENTS end to end -- the API speaks the exact
same unit as the database and the calculation engine (app/ai/financial_engine.py).
Dollar<->cents conversion happens ONLY in the frontend's presentation
layer (dashboard/lib/finance/money.ts), never here and never in SQL --
one conversion boundary, not several.

Every field is `int | None` (never a bare `int` with an implied 0
default) -- None means "unknown," never zero. See
CreateFinancialSnapshotRequest's own docstring.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.venture_hire_plans import HirePlanResponse, ProjectedMonthWithPlan
from app.models.venture_financial_plans import FinancialPlanResponse, ReconciliationItem


class CreateFinancialSnapshotRequest(BaseModel):
    """
    A full financial snapshot, as of one date. Always creates a NEW row
    (app/database/db.py::create_venture_financial_snapshot() is
    append-only) -- there is no "patch one field" request shape, by
    design: a founder editing their numbers is shown their most recent
    snapshot pre-filled and submits a complete new one, so every snapshot
    row is a self-contained point-in-time picture, never a partial diff
    that would require merge logic to interpret later.

    Every field but `as_of_date` is optional and nullable -- omitting a
    field (or sending it as `null`) means "unknown," and is never
    silently treated as zero anywhere in app/ai/financial_engine.py. A
    founder who wants to record "no marketing spend" must send `0`
    explicitly, not omit the field.
    """
    as_of_date: date
    cash_balance_cents: int | None = None
    monthly_recurring_revenue_cents: int | None = None
    monthly_non_recurring_revenue_cents: int | None = None
    payroll_cents: int | None = None
    contractors_cents: int | None = None
    software_cents: int | None = None
    marketing_cents: int | None = None
    rent_cents: int | None = None
    professional_services_cents: int | None = None
    other_expenses_cents: int | None = None
    # Phase 40A-FIX -- Private Beta P1 Hardening. Optional, client-
    # generated -- a retried submission with the same key returns the
    # existing row instead of creating a duplicate historical snapshot
    # (see create_venture_financial_snapshot()'s own docstring,
    # app/database/db.py). Identical shape to venture_decisions/
    # venture_financial_commitments' own idempotency_key field. Two
    # genuinely separate submissions (no key, or two different keys) are
    # both real, legitimate historical records -- never deduplicated by
    # payload similarity.
    idempotency_key: str | None = Field(default=None, max_length=100)


class FinancialSnapshotResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    as_of_date: date
    cash_balance_cents: int | None = None
    monthly_recurring_revenue_cents: int | None = None
    monthly_non_recurring_revenue_cents: int | None = None
    payroll_cents: int | None = None
    contractors_cents: int | None = None
    software_cents: int | None = None
    marketing_cents: int | None = None
    rent_cents: int | None = None
    professional_services_cents: int | None = None
    other_expenses_cents: int | None = None
    recorded_at: datetime


class DerivedFinancialMetrics(BaseModel):
    """See app/ai/financial_engine.py::compute_derived_metrics() for the
    exact derivation of every field here -- nothing here is computed
    twice; this model is just that function's return shape, typed."""
    total_monthly_revenue_cents: int | None = None
    total_monthly_expenses_cents: int | None = None
    net_burn_cents: int | None = None
    runway_months: float | None = None
    status: str


class ProjectedMonth(BaseModel):
    month_index: int
    date: date
    starting_cash_cents: int
    revenue_cents: int
    expenses_cents: int
    net_cash_change_cents: int
    ending_cash_cents: int
    depleted: bool


class VentureFinancialsResponse(BaseModel):
    """
    GET/POST /ventures/{venture_id}/financials. `latest_snapshot` is None
    exactly when the venture has never had a snapshot recorded (§15's
    empty state -- the frontend must render "add your financial
    snapshot," never a row of fake zeros). `derived`/`projection` are
    only meaningfully populated when a snapshot exists; both are still
    always present (never a separately-optional field the frontend has
    to null-check twice) -- `derived.status == "insufficient_data"` and
    `projection == []` are the honest "nothing to show yet" values in
    every other case.

    Phase 35C additive fields: `hire_plans` (every hire for this venture,
    any status) and `projection_with_plan` (the SAME projection engine,
    given the status='planned' ones) -- `projection` above stays the
    baseline-only meaning it already had in Phase 35B, byte-identical,
    for regression safety; `projection_with_plan` is new.

    Phase 35D additive fields: `financial_plans` (every revenue/expense
    plan, any status -- mirrors `hire_plans`), `pending_reconciliation`
    (§13/§14 -- planned items whose start_date has already passed as of
    the latest snapshot and haven't been reconciled against it yet; empty
    whenever nothing needs asking). See
    docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md.
    """
    latest_snapshot: FinancialSnapshotResponse | None = None
    derived: DerivedFinancialMetrics | None = None
    projection: list[ProjectedMonth] = Field(default_factory=list)
    hire_plans: list[HirePlanResponse] = Field(default_factory=list)
    financial_plans: list[FinancialPlanResponse] = Field(default_factory=list)
    pending_reconciliation: list[ReconciliationItem] = Field(default_factory=list)
    projection_with_plan: list[ProjectedMonthWithPlan] = Field(default_factory=list)


class FinancialHistoryResponse(BaseModel):
    """GET /ventures/{venture_id}/financials/history -- every snapshot
    ever recorded, oldest first. Not wired to a dedicated History UI in
    this phase (§13 of the directive: "do not build a full Finance
    History UI"), but real, queryable, and tested -- see
    test_venture_financials.py's history-safety case."""
    snapshots: list[FinancialSnapshotResponse] = Field(default_factory=list)
