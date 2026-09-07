"""
Phase 35C -- Hiring + Operating Plan Engine V1 -- request/response
contracts. See docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md.

Its own file, mirroring app/models/venture_financials.py's own
precedent. Every money field is INTEGER CENTS, matching the database and
app/ai/financial_engine.py exactly -- dollar<->cents conversion happens
only in the frontend (dashboard/lib/finance/money.ts).

PLAN, not ACTUAL: nothing here ever touches venture_financial_snapshots.
A hire plan is a founder's stated intention, calculated against the
canonical actual state, never mutating it.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EmploymentType = Literal["employee", "contractor"]
HirePlanStatus = Literal["planned", "cancelled", "actualized"]


class CreateHirePlanRequest(BaseModel):
    """
    For `employment_type="employee"`: `annual_salary_cents` and
    `burden_percent` are required, `monthly_cost_cents` must be omitted --
    the monthly figure is always DERIVED (app/ai/financial_engine.py::
    compute_hire_monthly_cost_cents()), never independently entered, so
    the two can never silently disagree.

    For `employment_type="contractor"`: `monthly_cost_cents` is required
    directly (it IS the input), `annual_salary_cents`/`burden_percent`
    must be omitted.

    `burden_percent` has NO default anywhere in this contract or the
    frontend form -- §6 of the directive: "prefer no hidden default."
    25% is a common real-world figure, not a universal constant this
    system should assume on a founder's behalf.
    """
    role: str = Field(min_length=1, max_length=200)
    employment_type: EmploymentType
    annual_salary_cents: int | None = None
    burden_percent: float | None = Field(default=None, ge=0)
    monthly_cost_cents: int | None = None
    one_time_cost_cents: int | None = None
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def _fields_match_employment_type(self) -> "CreateHirePlanRequest":
        if self.employment_type == "employee":
            if self.annual_salary_cents is None or self.burden_percent is None:
                raise ValueError("An employee hire requires annual_salary_cents and burden_percent.")
            if self.monthly_cost_cents is not None:
                raise ValueError("An employee hire's monthly cost is always derived -- do not pass monthly_cost_cents directly.")
        else:
            if self.monthly_cost_cents is None:
                raise ValueError("A contractor hire requires monthly_cost_cents.")
            if self.annual_salary_cents is not None or self.burden_percent is not None:
                raise ValueError("A contractor hire has no salary/burden -- pass monthly_cost_cents only.")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class UpdateHirePlanRequest(BaseModel):
    """
    Partial update -- every field optional, only the ones provided
    change. `status` is how a founder cancels or actualizes a plan (§5/
    §19 of the directive) -- a dedicated, explicit action, never inferred.
    Field-shape validation (employee vs. contractor) is re-checked by the
    caller (app/api.py) against the MERGED result, not here in isolation,
    since a partial request alone can't know the other side's existing
    values.
    """
    role: str | None = Field(default=None, min_length=1, max_length=200)
    annual_salary_cents: int | None = None
    burden_percent: float | None = Field(default=None, ge=0)
    monthly_cost_cents: int | None = None
    one_time_cost_cents: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: HirePlanStatus | None = None


class HirePlanResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    role: str
    employment_type: EmploymentType
    annual_salary_cents: int | None = None
    burden_percent: float | None = None
    monthly_cost_cents: int | None = None
    one_time_cost_cents: int | None = None
    start_date: date
    end_date: date | None = None
    status: HirePlanStatus
    created_at: datetime
    updated_at: datetime
    # Phase 35C -- always DERIVED (app/ai/financial_engine.py), never
    # stored -- see this model's own module docstring. Present on every
    # response so the frontend never re-implements the cost formula.
    computed_monthly_cost_cents: int | None = None
    computed_annual_cost_cents: int | None = None


class ProjectedMonthWithPlan(BaseModel):
    """Mirrors app/models/venture_financials.py::ProjectedMonth, extended
    with the plan-impact breakdown app/ai/financial_engine.py's own
    extended project_monthly_cash_flow() now returns. revenue_cents/
    expenses_cents are TOTALS (base + plan impact) -- see that function's
    own docstring for why this is backward-compatible with Phase 35B."""
    month_index: int
    date: date
    starting_cash_cents: int
    revenue_cents: int
    expenses_cents: int
    plan_expense_impact_cents: int
    active_plan_item_ids: list[int] = Field(default_factory=list)
    net_cash_change_cents: int
    ending_cash_cents: int
    depleted: bool


class HireImpactPreview(BaseModel):
    """
    Response for the ephemeral, NEVER-PERSISTED preview endpoint (§17 of
    the directive: PERSISTED PLAN vs. TEMPORARY COMPARISON) -- computing
    "what would this hire do" before a founder commits to saving it, and
    reused for the hire-now-vs-later comparison (§11) by calling the
    preview endpoint twice with different start dates.
    """
    computed_monthly_cost_cents: int | None = None
    computed_annual_cost_cents: int | None = None
    baseline_projection: list[ProjectedMonthWithPlan] = Field(default_factory=list)
    with_hire_projection: list[ProjectedMonthWithPlan] = Field(default_factory=list)


