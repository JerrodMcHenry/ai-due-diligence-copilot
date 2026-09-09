"""
Phase 35B -- Financial State Persistence + Runway Engine V1.

Deterministic, zero-AI, zero-database, zero-network calculation over a
persisted financial snapshot -- same discipline as
app/ai/build_recommendation.py and dashboard/lib/fundraising/*.ts: pure
functions, inputs in, deterministic outputs out. See
docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md for the full design
record (money representation, unknown-vs-zero semantics, projection
methodology).

Two entry points:

- compute_derived_metrics(snapshot) -- total revenue, total expenses, net
  burn, runway, and a plain-language `status`. Never invents a number for
  a missing input: any field genuinely unknown (None) that a calculation
  depends on makes that calculation's result None too ("insufficient
  data"), never a silently-assumed zero.

- project_monthly_cash_flow(snapshot, horizon_months) -- a deterministic
  month-by-month projection holding the current snapshot's revenue/
  expenses flat. This is explicitly "what happens if the current monthly
  snapshot continues," never a prediction -- callers must render it with
  that framing (see FinanceOverview.tsx). Bounded at `horizon_months` to
  avoid a meaningless endless table for a cash-flow-positive company, and
  terminated early (flagged, not silently dropped) the month cash would
  go negative for a burning company.

Money is always integer CENTS (a plain Python `int`, arbitrary-precision
by language design -- no bigint/Rational machinery needed for addition/
subtraction of money; the one place this module divides -- runway months
-- uses `fractions.Fraction` for an exact intermediate result, rounded
only once, at the very end, to a display-friendly float). Never a `float`
anywhere money is added or compared.
"""

import calendar
from datetime import date
from fractions import Fraction

_EXPENSE_FIELDS = (
    "payroll_cents",
    "contractors_cents",
    "software_cents",
    "marketing_cents",
    "rent_cents",
    "professional_services_cents",
    "other_expenses_cents",
)

_REVENUE_FIELDS = (
    "monthly_recurring_revenue_cents",
    "monthly_non_recurring_revenue_cents",
)

DEFAULT_PROJECTION_HORIZON_MONTHS = 24

# Phase 38D-A -- Financial Commitment Persistence + Frozen Expectation V1.
# Stamped onto every venture_financial_commitments row at the moment its
# expected_monthly is computed (§9/§24 of docs/product/
# SIE_COMMITTED_PLAN_LEARNING_ARCHITECTURE_V1.md) so a future reader can
# tell which era's projection math produced a given frozen number. Bump
# this BY HAND only when project_monthly_cash_flow()'s own math changes
# in a way that would produce a different result for the same inputs --
# never automatically, never as a trigger to recompute anything: a
# commitment's own already-stored expected_monthly is NEVER recalculated
# against a newer version, by design (a historical expectation must not
# silently mutate just because the engine improved later).
FINANCIAL_PROJECTION_CALCULATION_VERSION = "1"


def _sum_or_none(values: list[int | None]) -> int | None:
    """None ("unknown") poisons the sum -- summing an unknown quantity
    with known ones is not itself knowable, and must never be silently
    treated as if the unknown field were zero (Phase 35B §15's own
    "unknown is not zero" rule, applied to arithmetic, not just display).
    An explicit 0 is a real value and sums normally."""
    if any(v is None for v in values):
        return None
    return sum(values)


def _add_months(d: date, months: int) -> date:
    """Pure stdlib month arithmetic (no dateutil dependency in this
    project) -- clamps day-of-month for shorter target months (e.g. Jan
    31 + 1 month -> Feb 28/29), the same clamping every calendar library
    uses for this case."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def compute_derived_metrics(snapshot: dict) -> dict:
    """
    `snapshot` is a venture_financial_snapshots row (or any dict with the
    same keys) -- cash_balance_cents plus the revenue/expense fields
    above, any of which may be None (unknown).

    Returns:
        total_monthly_revenue_cents: int | None
        total_monthly_expenses_cents: int | None
        net_burn_cents: int | None   -- positive = burning cash, negative
            = generating cash, 0 = exactly break-even. None when revenue
            or expenses (or both) are unknown.
        runway_months: float | None  -- only set when net_burn_cents > 0
            AND cash is known. Rounded to 1 decimal at this final step
            only -- the division itself is exact (fractions.Fraction),
            matching dashboard/lib/fundraising/rational.ts's own
            "exact arithmetic, round only for display" discipline.
        status: one of "insufficient_data" | "cash_flow_positive" |
            "break_even" | "burning" | "out_of_cash". Never "infinite
            runway" -- see FinanceOverview.tsx for the founder-facing
            copy this status maps to.
    """
    revenue = _sum_or_none([snapshot.get(f) for f in _REVENUE_FIELDS])
    expenses = _sum_or_none([snapshot.get(f) for f in _EXPENSE_FIELDS])
    cash = snapshot.get("cash_balance_cents")

    if revenue is None or expenses is None:
        return {
            "total_monthly_revenue_cents": revenue,
            "total_monthly_expenses_cents": expenses,
            "net_burn_cents": None,
            "runway_months": None,
            "status": "insufficient_data",
        }

    net_burn = expenses - revenue

    if net_burn < 0:
        status = "cash_flow_positive"
    elif net_burn == 0:
        status = "break_even"
    elif cash is None:
        status = "burning"
    elif cash <= 0:
        status = "out_of_cash"
    else:
        status = "burning"

    runway_months = None
    if status == "out_of_cash":
        runway_months = 0.0
    elif status == "burning" and cash is not None:
        runway_months = round(float(Fraction(cash, net_burn)), 1)

    return {
        "total_monthly_revenue_cents": revenue,
        "total_monthly_expenses_cents": expenses,
        "net_burn_cents": net_burn,
        "runway_months": runway_months,
        "status": status,
    }


def _is_one_time_month(item_start: date, month_date: date, month_index: int) -> bool:
    """A one-time cost hits the calendar month matching the plan item's
    own start_date. Edge case: if that month is already BEFORE the first
    month this projection ever shows (start_date at or before as_of_date),
    it is applied in month 1 instead of silently dropped -- a real cost
    must never disappear just because it started "now" rather than
    strictly in the future."""
    if (item_start.year, item_start.month) == (month_date.year, month_date.month):
        return True
    return month_index == 1 and item_start < month_date


def project_monthly_cash_flow(
    snapshot: dict,
    as_of_date: date,
    horizon_months: int = DEFAULT_PROJECTION_HORIZON_MONTHS,
    plan_items: list[dict] | None = None,
) -> list[dict]:
    """
    A deterministic "what happens if the current monthly snapshot
    continues" projection -- NOT a forecast (no growth, no seasonality,
    no assumption about the future beyond "these numbers stay the same"),
    extended in Phase 35C (dated hiring costs) and Phase 35D (dated
    revenue/expense plans) to accept dated PLAN items on top of the flat
    actual snapshot.

    `plan_items`, when given, is a list of GENERIC dated financial
    effects, each one of two kinds (Phase 35D §8 -- "the projection engine
    should conceptually consume dated financial effects rather than
    React/database-specific objects"):

      - `kind: "expense_delta"` -- {id, kind, monthly_cost_cents (a
        SIGNED recurring delta -- positive adds to expenses, negative
        reduces them), one_time_cost_cents, start_date, end_date}. A hire
        (Phase 35C, always positive) and an expense-change plan (Phase
        35D, either sign) are the SAME shape to this function -- it has
        no idea which produced a given item. This is what proves 35C's
        own adapter pattern generalizes, exactly as that phase's directive
        asked this phase to confirm.
      - `kind: "revenue_target"` -- {id, kind, target_revenue_cents,
        start_date, end_date}. Deliberately NOT a delta: an absolute
        monthly figure that REPLACES (never adds to) base revenue for
        every month it's active, so "MRR becomes $40,000" always means
        exactly that regardless of what the underlying actual snapshot
        says -- see revenue_plan_to_plan_item()'s own docstring for why a
        delta representation would silently drift from the founder's
        stated assumption if the actual snapshot later changes. If more
        than one revenue_target item is active in the same month
        (composing two overlapping revenue plans in one scenario --  not
        a supported V1 use case), the most-recently-created one wins,
        deterministically, rather than the two being meaninglessly summed
        or averaged.

    Omitting `plan_items` (or passing []) reproduces Phase 35B's exact
    original behavior byte-for-byte -- see test_venture_financials.py's
    own Case O regression test, test_venture_hire_plans.py's Case O, and
    this phase's own Case V/W.

    Returns [] when cash, revenue, or expenses are unknown -- a
    projection cannot honestly be drawn without all three (never
    substitutes an assumed value, same rule as compute_derived_metrics).

    Each month is {month_index (1-based), date, starting_cash_cents,
    revenue_cents, expenses_cents (both TOTAL, i.e. base adjusted by any
    active plan items), plan_expense_impact_cents, plan_revenue_active
    (bool -- whether a revenue_target item is overriding base revenue
    this month), active_plan_item_ids, net_cash_change_cents,
    ending_cash_cents, depleted}. `expenses_cents` is floored at 0 --
    total company spend can never be displayed as negative, the
    projection-time half of Phase 35D §7's "never negative expense"
    invariant (the other half, rejecting an impossible plan at creation
    time, lives in validate_expense_plan_amount() below). Terminates
    early (the last row has depleted=True, ending_cash_cents floored at 0)
    the month cash would run out; otherwise runs the full `horizon_months`
    and stops -- bounded so a cash-flow-positive company never gets a
    meaningless endless table (§9 of the 35B directive).
    """
    metrics = compute_derived_metrics(snapshot)
    cash = snapshot.get("cash_balance_cents")
    base_revenue = metrics["total_monthly_revenue_cents"]
    base_expenses = metrics["total_monthly_expenses_cents"]

    if cash is None or base_revenue is None or base_expenses is None:
        return []

    plan_items = plan_items or []

    months: list[dict] = []
    starting_cash = cash

    for i in range(1, horizon_months + 1):
        month_date = _add_months(as_of_date, i)

        active_items = [
            p for p in plan_items
            if p["start_date"] <= month_date and (p.get("end_date") is None or month_date <= p["end_date"])
        ]
        expense_items = [p for p in active_items if p.get("kind", "expense_delta") == "expense_delta"]
        revenue_items = [p for p in active_items if p.get("kind") == "revenue_target"]

        recurring_impact = sum((p.get("monthly_cost_cents") or 0) for p in expense_items)
        one_time_impact = sum(
            (p.get("one_time_cost_cents") or 0)
            for p in plan_items
            if p.get("kind", "expense_delta") == "expense_delta" and _is_one_time_month(p["start_date"], month_date, i)
        )
        plan_expense_impact = recurring_impact + one_time_impact

        if revenue_items:
            winning_revenue_item = max(revenue_items, key=lambda p: p["id"])
            total_revenue = winning_revenue_item["target_revenue_cents"]
            plan_revenue_active = True
        else:
            total_revenue = base_revenue
            plan_revenue_active = False

        total_expenses = max(base_expenses + plan_expense_impact, 0)
        net_cash_change = total_revenue - total_expenses
        ending_cash = starting_cash + net_cash_change
        depleted = ending_cash <= 0 and net_cash_change < 0
        display_ending_cash = max(ending_cash, 0) if depleted else ending_cash

        months.append({
            "month_index": i,
            "date": month_date,
            "starting_cash_cents": starting_cash,
            "revenue_cents": total_revenue,
            "expenses_cents": total_expenses,
            "plan_expense_impact_cents": plan_expense_impact,
            "plan_revenue_active": plan_revenue_active,
            # Sorted, deterministically, regardless of the CALLER's own
            # plan_items list order (Phase 35D §9: "test order
            # independence" -- every monetary field is already
            # commutative by construction; this makes the one cosmetic,
            # non-monetary field order-independent too, so the full
            # month dict, not just its dollar amounts, is identical no
            # matter what order plans were supplied in).
            "active_plan_item_ids": sorted(p["id"] for p in active_items),
            "net_cash_change_cents": net_cash_change,
            "ending_cash_cents": display_ending_cash,
            "depleted": depleted,
        })

        if depleted:
            break
        starting_cash = ending_cash

    return months


# ---------------------------------------------------------------------------
# Phase 35C -- Hiring + Operating Plan Engine V1.
#
# The ONE place hiring-specific fields (employment_type, salary, burden,
# a contractor's flat monthly cost) are read -- everything downstream
# (the projection engine above) only ever sees the generic
# {monthly_cost_cents, one_time_cost_cents, start_date, end_date} shape.
# ---------------------------------------------------------------------------

_BURDEN_BASIS_POINTS_DENOMINATOR = 10_000  # 1 basis point = 0.01%; see compute_hire_monthly_cost_cents


def compute_hire_monthly_cost_cents(hire: dict) -> int | None:
    """
    For an employee: annual_salary_cents * (1 + burden_percent/100) / 12,
    computed with exact `Fraction` arithmetic (burden_percent -- a
    founder-entered percentage like 25 or 12.5 -- is converted to an
    exact basis-point fraction first, avoiding float noise), rounded to
    the nearest cent only at the very end. Returns None if either input
    is missing -- never assumes a "typical" burden (§6 of the directive:
    "prefer no hidden default").

    For a contractor: `monthly_cost_cents` directly -- it IS the input,
    never derived from anything else. Returns None if missing.
    """
    if hire["employment_type"] == "employee":
        salary = hire.get("annual_salary_cents")
        burden = hire.get("burden_percent")
        if salary is None or burden is None:
            return None
        burden_fraction = Fraction(round(burden * 100), _BURDEN_BASIS_POINTS_DENOMINATOR)
        annual_fully_loaded = Fraction(salary) * (1 + burden_fraction)
        return round(annual_fully_loaded / 12)

    return hire.get("monthly_cost_cents")


def compute_hire_annual_cost_cents(hire: dict) -> int | None:
    """The fully-loaded annual figure (§3 of the directive's worked
    example: $225,000/year alongside $18,750/month) -- derived from the
    same monthly figure, never computed independently (so the two
    numbers can never silently disagree)."""
    monthly = compute_hire_monthly_cost_cents(hire)
    return None if monthly is None else monthly * 12


def hire_to_plan_item(hire: dict) -> dict:
    """Adapts one venture_hire_plans row into the generic dated-plan-item
    shape project_monthly_cash_flow() consumes. Returns None (never a
    zero-cost item) when the hire's own monthly cost can't be computed --
    an incomplete hire plan row should never silently contribute $0 to a
    projection."""
    monthly_cost = compute_hire_monthly_cost_cents(hire)
    if monthly_cost is None:
        return None
    return {
        "id": hire["id"],
        "monthly_cost_cents": monthly_cost,
        "one_time_cost_cents": hire.get("one_time_cost_cents") or 0,
        "start_date": hire["start_date"],
        "end_date": hire.get("end_date"),
    }


def hire_plan_items_for_projection(hires: list[dict]) -> list[dict]:
    """Filters to status='planned' hires only (cancelled/actualized hires
    must never affect a projection -- §5/§19 of the directive) and adapts
    each to the generic plan-item shape, dropping any that can't be
    costed (see hire_to_plan_item's own docstring)."""
    items = [hire_to_plan_item(h) for h in hires if h.get("status") == "planned"]
    return [item for item in items if item is not None]


# ---------------------------------------------------------------------------
# Phase 35D -- Operating Scenarios + Financial Plan Reconciliation V1.
#
# The second and third adapters into the SAME generic projection engine
# above, proving 35C's own "hiring should be the first typed dated plan
# input into a general projection architecture" claim: neither adapter
# below changes project_monthly_cash_flow() itself, only translates a
# venture_financial_plans row into the {kind, ...} shape it already
# understands.
# ---------------------------------------------------------------------------

_EXPENSE_CATEGORY_FIELDS = {
    "payroll": "payroll_cents",
    "contractors": "contractors_cents",
    "software": "software_cents",
    "marketing": "marketing_cents",
    "rent": "rent_cents",
    "professional_services": "professional_services_cents",
    "other": "other_expenses_cents",
}


def validate_expense_plan_amount(
    latest_snapshot: dict | None,
    category: str,
    amount_cents: int,
    other_active_deltas_cents: int = 0,
) -> str | None:
    """
    Phase 35D §7: "a cost-cut plan must never make an expense category
    mathematically negative." Returns an error message (reject) if this
    delta, applied to what the LATEST actual snapshot says that category
    currently is, would drive it negative -- None means the plan is safe
    to create.

    Phase 35D-A §14/§15 (Case L/K): `other_active_deltas_cents` is the sum
    of every OTHER currently-`planned` expense_change plan already active
    on this same category (0 if there are none, or the caller doesn't
    pass one -- every pre-35D-A call site is unaffected). Without this, two
    individually-safe cuts on the same category (e.g. contractors -$10K,
    then contractors -$15K against a $20K category) could each pass this
    check in isolation while their COMBINED effect drives the category
    negative -- a real gap the projection engine's own total-expenses
    floor (see project_monthly_cash_flow's docstring) does not close,
    because that floor operates on the aggregate total, not per category.

    A ONE-TIME, creation-time check against currently-known actual state,
    not a continuously-re-validated runtime constraint (documented
    limitation, §7 of the directive's own "choose the safest
    representation" framing): if the actual snapshot changes later such
    that this delta WOULD have been rejected, the already-created plan is
    not retroactively invalidated -- the projection engine's own
    total-expenses floor is the safety net for that case, at the level of
    the total, not the individual category.

    Skips validation (returns None -- allowed) when no actual snapshot
    exists yet, or the category's current value is unknown -- there is
    nothing to validate against, and project_monthly_cash_flow() already
    returns [] for a venture with no usable actual state regardless.
    """
    if latest_snapshot is None:
        return None
    current_value = latest_snapshot.get(_EXPENSE_CATEGORY_FIELDS[category])
    if current_value is None:
        return None
    combined_delta = amount_cents + other_active_deltas_cents
    if current_value + combined_delta < 0:
        category_label = category.replace("_", " ")
        shortfall_dollars = -(current_value + combined_delta) / 100
        if other_active_deltas_cents != 0:
            return (
                f"This would take {category_label} below $0 once combined with your other planned "
                f"changes to this category. {category_label.capitalize()} is currently "
                f"${current_value / 100:,.0f}/month, and your planned changes to it now total "
                f"-${-combined_delta / 100:,.0f}/month -- ${shortfall_dollars:,.0f} more than there is to cut."
            )
        return (
            f"This would take {category_label} below $0. It's currently ${current_value / 100:,.0f}/month, "
            f"which isn't enough to absorb a ${abs(amount_cents) / 100:,.0f}/month cut "
            f"(short by ${shortfall_dollars:,.0f})."
        )
    return None


def _date_ranges_overlap(start_a, end_a, start_b, end_b) -> bool:
    """True if [start_a, end_a] and [start_b, end_b] share any date --
    a None end means "still active," i.e. unbounded. Shared helper for
    validate_no_overlapping_revenue_target(); a plain closed-interval
    overlap test, nothing financial-engine-specific about it."""
    if end_a is not None and start_b > end_a:
        return False
    if end_b is not None and start_a > end_b:
        return False
    return True


def validate_no_overlapping_revenue_target(
    other_active_plans: list[dict],
    start_date,
    end_date,
) -> str | None:
    """
    Phase 35D-A §15/Case M: two revenue_target plans active in the same
    month is not a supported composition (project_monthly_cash_flow()
    breaks the tie deterministically -- highest id wins -- but silently,
    with no founder-visible explanation). Rather than let a founder
    create that ambiguous state at all, the safer V1 behavior chosen here
    is to PREVENT it: a new or edited revenue_target plan is rejected if
    its own active date range overlaps any OTHER currently-`planned`
    revenue_target plan's own range. `other_active_plans` is the venture's
    other planned revenue_target rows (already excluding the plan being
    edited, if any) -- empty means nothing to conflict with.
    """
    for other in other_active_plans:
        if _date_ranges_overlap(start_date, end_date, other["start_date"], other.get("end_date")):
            return (
                f"You already have an active revenue plan (\"{other['label']}\") covering this period, "
                f"starting {other['start_date'].isoformat() if hasattr(other['start_date'], 'isoformat') else other['start_date']}. "
                "Cancel or edit that plan first, or choose dates that don't overlap it."
            )
    return None


def expense_plan_to_plan_item(plan: dict) -> dict:
    """Adapts one venture_financial_plans row (plan_type='expense_change')
    into the generic expense_delta shape. `amount_cents` is the row's own
    SIGNED delta (positive = increase, negative = cut) -- the category
    itself (payroll/marketing/etc.) is display/validation-only metadata
    the projection engine never sees; only the net effect on total
    expenses matters to it."""
    return {
        "id": plan["id"],
        "kind": "expense_delta",
        "monthly_cost_cents": plan["amount_cents"],
        "one_time_cost_cents": 0,
        "start_date": plan["start_date"],
        "end_date": plan.get("end_date"),
    }


def revenue_plan_to_plan_item(plan: dict) -> dict:
    """Adapts one venture_financial_plans row (plan_type='revenue_target')
    into the generic revenue_target shape. Deliberately an ABSOLUTE
    target (`amount_cents` on the row IS the target, stored as entered),
    never a delta computed against base revenue at creation time -- a
    delta would silently drift from the founder's stated "$40,000/month"
    assumption the moment the underlying actual snapshot's own revenue
    changed for an unrelated reason (a new snapshot recorded, a
    reconciliation). An absolute target means exactly the same thing
    every time it's read, regardless of what else changes."""
    return {
        "id": plan["id"],
        "kind": "revenue_target",
        "target_revenue_cents": plan["amount_cents"],
        "start_date": plan["start_date"],
        "end_date": plan.get("end_date"),
    }


def financial_plan_to_plan_item(plan: dict) -> dict | None:
    if plan["plan_type"] == "expense_change":
        return expense_plan_to_plan_item(plan)
    if plan["plan_type"] == "revenue_target":
        return revenue_plan_to_plan_item(plan)
    return None


def financial_plan_items_for_projection(plans: list[dict]) -> list[dict]:
    """Same discipline as hire_plan_items_for_projection(): status='planned'
    only (cancelled/actualized plans -- §17 of the directive, the same
    lifecycle as hires -- must never affect a projection)."""
    items = [financial_plan_to_plan_item(p) for p in plans if p.get("status") == "planned"]
    return [item for item in items if item is not None]
