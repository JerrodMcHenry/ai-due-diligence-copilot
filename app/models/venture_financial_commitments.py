"""
Phase 38D-A -- Financial Commitment Persistence + Frozen Expectation V1 --
request/response contracts. See
docs/product/SIE_COMMITTED_PLAN_LEARNING_ARCHITECTURE_V1.md for the
accepted architecture this implements.

A Committed Plan is NOT a scenario (`app/models/venture_financial_plans.py::ScenarioResponse`
stays exactly what it already is -- hypothetical, always recomputed live).
It is a separate, append-only fact: the founder explicitly chose to
proceed, and SIE froze exactly what that meant financially at that
moment. `plan_snapshot`/`expected_monthly` are never recomputed on read
-- see `get_venture_financial_commitment_for_owner()`'s own docstring in
app/database/db.py.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.venture_financial_plans import ScenarioProjectedMonth

CommitmentStatus = Literal["active", "superseded", "abandoned"]
PlanSnapshotKind = Literal["hire", "revenue_target", "expense_change"]


class PlanSnapshotItem(BaseModel):
    """One included plan/hire's own input VALUES, frozen at commitment
    time -- never a bare id. The underlying `venture_hire_plans`/
    `venture_financial_plans` row may be edited or have its status
    changed after this is written; this row's own meaning must not
    depend on ever reading that row again (§6 of the accepted
    architecture)."""
    id: int
    kind: PlanSnapshotKind
    label: str
    start_date: date
    end_date: date | None = None
    # Hire-specific fields (kind == "hire").
    role: str | None = None
    employment_type: str | None = None
    annual_salary_cents: int | None = None
    burden_percent: float | None = None
    monthly_cost_cents: int | None = None
    one_time_cost_cents: int | None = None
    # revenue_target / expense_change-specific fields.
    category: str | None = None
    amount_cents: int | None = None


class CreateFinancialCommitmentRequest(BaseModel):
    """
    Exactly one commitment source is required -- see §4/§18 of the
    accepted architecture ("both scenario and individual-plan commitment
    fall out of the same array shape, no separate mode"). Supplying
    `scenario_id` means "commit to this saved scenario as it exists right
    now" -- the server resolves it into hire_plan_ids/financial_plan_ids
    itself; the request must not also supply those directly (ambiguous
    otherwise -- which one wins?). Omitting `scenario_id` means "commit
    to exactly these individual plans," with no saved scenario involved.
    """
    scenario_id: int | None = None
    hire_plan_ids: list[int] = Field(default_factory=list)
    financial_plan_ids: list[int] = Field(default_factory=list)
    # §12/§13: never inferred, never text-matched -- set only when the
    # founder is explicitly committing as part of an existing Decision.
    related_decision_id: int | None = None
    founder_rationale: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "CreateFinancialCommitmentRequest":
        has_scenario = self.scenario_id is not None
        has_explicit_plans = bool(self.hire_plan_ids) or bool(self.financial_plan_ids)
        if has_scenario and has_explicit_plans:
            raise ValueError(
                "Provide either scenario_id or hire_plan_ids/financial_plan_ids -- not both."
            )
        if not has_scenario and not has_explicit_plans:
            raise ValueError("A commitment must reference a scenario or at least one plan.")
        return self


class FinancialCommitmentResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    committed_at: datetime
    source_snapshot_id: int
    scenario_id: int | None = None
    scenario_name: str | None = None
    hire_plan_ids: list[int]
    financial_plan_ids: list[int]
    plan_snapshot: list[PlanSnapshotItem]
    calculation_version: str
    projection_start: date
    projection_horizon_months: int
    expected_monthly: list[ScenarioProjectedMonth]
    related_decision_id: int | None = None
    status: CommitmentStatus
    supersedes_commitment_id: int | None = None
    founder_rationale: str | None = None
