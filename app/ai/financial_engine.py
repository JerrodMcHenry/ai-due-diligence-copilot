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
    now extended (Phase 35C) to accept dated PLAN items on top of the
    flat actual snapshot.

    `plan_items`, when given, is a list of GENERIC dated cost items --
    {id, monthly_cost_cents, one_time_cost_cents, start_date, end_date}.
    This function has no idea any of them represent a "hire" -- that
    translation happens exactly once, in hire_to_plan_item() below, per
    §9 of the Phase 35C directive ("hiring should be the first typed
    dated plan input into a general projection architecture," never
    hiring-specific logic baked into the engine itself). A future revenue
    assumption, cost cut, or financing event becomes just another item in
    this same list, with no change to this function.

    Omitting `plan_items` (or passing []) reproduces Phase 35B's exact
    original behavior byte-for-byte -- every month's plan_expense_impact_cents
    is 0, so total_revenue/total_expenses collapse to the same constant
    base_revenue/base_expenses every month, exactly as before (see
    test_venture_financials.py's own Case O regression test, and
    test_venture_hire_plans.py's Case O here).

    Returns [] when cash, revenue, or expenses are unknown -- a
    projection cannot honestly be drawn without all three (never
    substitutes an assumed value, same rule as compute_derived_metrics).

    Each month is {month_index (1-based), date, starting_cash_cents,
    revenue_cents, expenses_cents (both TOTAL, i.e. base + plan impact),
    plan_expense_impact_cents, active_plan_item_ids, net_cash_change_cents,
    ending_cash_cents, depleted}. Terminates early (the last row has
    depleted=True, ending_cash_cents floored at 0 -- cash can never be
    displayed as negative) the month cash would run out; otherwise runs
    the full `horizon_months` and stops -- bounded so a cash-flow-positive
    company never gets a meaningless endless table (§9 of the 35B
    directive).
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
        recurring_impact = sum((p["monthly_cost_cents"] or 0) for p in active_items)
        one_time_impact = sum(
            (p.get("one_time_cost_cents") or 0)
            for p in plan_items
            if _is_one_time_month(p["start_date"], month_date, i)
        )
        plan_expense_impact = recurring_impact + one_time_impact

        total_revenue = base_revenue
        total_expenses = base_expenses + plan_expense_impact
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
            "active_plan_item_ids": [p["id"] for p in active_items],
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
