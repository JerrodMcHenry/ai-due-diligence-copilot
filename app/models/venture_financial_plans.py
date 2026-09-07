"""
Phase 35D -- Operating Scenarios + Financial Plan Reconciliation V1 --
request/response contracts for revenue/expense plans, saved scenarios,
and reconciliation. See docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md.

Every money field is INTEGER CENTS, matching every other Finance
contract. `amount_cents` means different things by `plan_type` -- an
ABSOLUTE target for `revenue_target`, a SIGNED recurring delta for
`expense_change` -- see CreateFinancialPlanRequest's own docstring.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

FinancialPlanType = Literal["revenue_target", "expense_change"]
ExpenseCategory = Literal["payroll", "contractors", "software", "marketing", "rent", "professional_services", "other"]
PlanStatus = Literal["planned", "cancelled", "actualized"]


class CreateFinancialPlanRequest(BaseModel):
    """
    `plan_type="revenue_target"`: `amount_cents` is the ABSOLUTE monthly
    revenue figure this plan asserts from `start_date` onward (§4 of the
    directive: "prefer absolute target values over ambiguous percentage
    compounding") -- `category` must be omitted.

    `plan_type="expense_change"`: `amount_cents` is a SIGNED recurring
    monthly delta against the named `category` (positive = increase,
    negative = cut) -- `category` is required. Rejected (422, at the API
    layer) if this delta would drive that category's currently-known
    actual value below zero (§7: "never negative expense").
    """
    plan_type: FinancialPlanType
    label: str = Field(min_length=1, max_length=200)
    category: ExpenseCategory | None = None
    amount_cents: int
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def _fields_match_plan_type(self) -> "CreateFinancialPlanRequest":
        if self.plan_type == "revenue_target":
            if self.category is not None:
                raise ValueError("A revenue_target plan has no category -- it replaces total revenue outright.")
            if self.amount_cents < 0:
                raise ValueError("A revenue target cannot be negative.")
        else:
            if self.category is None:
                raise ValueError("An expense_change plan requires a category.")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class UpdateFinancialPlanRequest(BaseModel):
    """Partial update -- mirrors UpdateHirePlanRequest's own shape and
    reasoning exactly (app/models/venture_hire_plans.py)."""
    label: str | None = Field(default=None, min_length=1, max_length=200)
    category: ExpenseCategory | None = None
    amount_cents: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: PlanStatus | None = None


class FinancialPlanResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    plan_type: FinancialPlanType
    label: str
    category: ExpenseCategory | None = None
    amount_cents: int
    start_date: date
    end_date: date | None = None
    status: PlanStatus
    last_reconciled_snapshot_id: int | None = None
    created_at: datetime
    updated_at: datetime


# --- Scenarios ---------------------------------------------------------------


class CreateScenarioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    hire_plan_ids: list[int] = Field(default_factory=list)
    financial_plan_ids: list[int] = Field(default_factory=list)


class UpdateScenarioRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    hire_plan_ids: list[int] | None = None
    financial_plan_ids: list[int] | None = None


class ScenarioProjectedMonth(BaseModel):
    month_index: int
    date: date
    starting_cash_cents: int
    revenue_cents: int
    expenses_cents: int
    plan_expense_impact_cents: int
    plan_revenue_active: bool
    active_plan_item_ids: list[int] = Field(default_factory=list)
    net_cash_change_cents: int
    ending_cash_cents: int
    depleted: bool


class ScenarioResponse(BaseModel):
    """
    A scenario's `assumptions`/`projection`/`ending_cash_at_horizon_cents`/
    `depletion_date` are all COMPUTED at read time, never stored -- see
    docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md's own "scenario
    baseline semantics" section. Two identical GET calls return identical
    results only as long as the underlying actual snapshot and selected
    plans haven't changed in between -- this is the deliberate, documented
    tradeoff of never freezing a copy of canonical truth into a scenario.
    A cancelled or actualized plan referenced by `hire_plan_ids`/
    `financial_plan_ids` is silently excluded from the computation (never
    an error) -- its id simply stops contributing, exactly matching how
    the Finance Overview's own "with planned changes" projection already
    treats a since-cancelled/actualized hire.
    """
    id: int
    venture_id: int
    user_id: str
    name: str
    hire_plan_ids: list[int]
    financial_plan_ids: list[int]
    created_at: datetime
    updated_at: datetime
    assumptions: list[str] = Field(default_factory=list)
    projection: list[ScenarioProjectedMonth] = Field(default_factory=list)
    ending_cash_at_horizon_cents: int | None = None
    depletion_date: date | None = None


class FinancialPlanImpactPreview(BaseModel):
    """Ephemeral, NEVER-PERSISTED preview for a revenue/expense plan --
    mirrors HireImpactPreview's own role exactly (app/models/venture_hire_plans.py),
    minus the derived-cost fields a revenue/expense plan doesn't need
    (its `amount_cents` is already exactly what the projection uses, no
    salary/burden conversion involved)."""
    baseline_projection: list[ScenarioProjectedMonth] = Field(default_factory=list)
    with_plan_projection: list[ScenarioProjectedMonth] = Field(default_factory=list)


# --- Reconciliation ------------------------------------------------------


class ReconciliationItem(BaseModel):
    """One 'is this now included in your finances?' question -- §13/§14
    of the directive. `plan_kind` says which table to PATCH when the
    founder answers."""
    plan_kind: Literal["hire", "financial"]
    plan_id: int
    label: str
    monthly_amount_cents: int | None = None
    start_date: date


class ReconcilePlanRequest(BaseModel):
    plan_kind: Literal["hire", "financial"]
    plan_id: int
    included: bool
