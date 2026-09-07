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


def project_monthly_cash_flow(
    snapshot: dict,
    as_of_date: date,
    horizon_months: int = DEFAULT_PROJECTION_HORIZON_MONTHS,
) -> list[dict]:
    """
    A deterministic "what happens if the current monthly snapshot
    continues" projection -- NOT a forecast (no growth, no seasonality,
    no assumption about the future beyond "these numbers stay the same").
    Phase 35B has no dated hiring/financing events yet (that's a future
    phase, per docs/product/SIE_FINANCIAL_DECISION_ENGINE_V2.md §12/§25)
    -- this function is architected to accept them later (a caller could
    pass a snapshot whose revenue/expenses already reflect a hypothetical
    change starting at some month, or this function could be extended
    with a `dated_line_items` parameter) WITHOUT changing its signature
    or return shape today.

    Returns [] when cash, revenue, or expenses are unknown -- a
    projection cannot honestly be drawn without all three (never
    substitutes an assumed value, same rule as compute_derived_metrics).

    Each month is {month_index (1-based), date, starting_cash_cents,
    revenue_cents, expenses_cents, net_cash_change_cents, ending_cash_cents,
    depleted}. Terminates early (the last row has depleted=True, ending_cash_cents
    floored at 0 -- cash can never be displayed as negative) the month
    cash would run out for a burning company; otherwise runs the full
    `horizon_months` and stops -- bounded so a cash-flow-positive company
    never gets a meaningless endless table (§9 of the directive).
    """
    metrics = compute_derived_metrics(snapshot)
    cash = snapshot.get("cash_balance_cents")
    revenue = metrics["total_monthly_revenue_cents"]
    expenses = metrics["total_monthly_expenses_cents"]

    if cash is None or revenue is None or expenses is None:
        return []

    months: list[dict] = []
    starting_cash = cash
    net_cash_change = revenue - expenses

    for i in range(1, horizon_months + 1):
        ending_cash = starting_cash + net_cash_change
        depleted = ending_cash <= 0 and net_cash_change < 0
        display_ending_cash = max(ending_cash, 0) if depleted else ending_cash

        months.append({
            "month_index": i,
            "date": _add_months(as_of_date, i),
            "starting_cash_cents": starting_cash,
            "revenue_cents": revenue,
            "expenses_cents": expenses,
            "net_cash_change_cents": net_cash_change,
            "ending_cash_cents": display_ending_cash,
            "depleted": depleted,
        })

        if depleted:
            break
        starting_cash = ending_cash

    return months
