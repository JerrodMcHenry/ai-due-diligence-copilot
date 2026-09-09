"""
Phase 38D-B -- Committed Expectation vs Actual V1. See
docs/product/SIE_COMMITTED_PLAN_LEARNING_ARCHITECTURE_V1.md §33 for the
accepted design this implements.

Pure, deterministic, read-time-only comparison -- no persistence, no AI,
no interpretation. Answers exactly one question per month: "what did we
expect (frozen at commitment time) vs. what actually happened (the
canonical financial snapshot)?" The three facts (expected, actual,
variance) are never rewritten into each other -- see this module's own
per-field construction below.

EXPECTED comes exclusively from `commitment["expected_monthly"]`
(app/database/db.py's own already-frozen JSONB column) -- never
recomputed, never re-derived from live plan rows. ACTUAL comes
exclusively from `venture_financial_snapshots` rows (via
compute_derived_metrics(), the SAME function every other actual-state
read in this codebase already uses) -- never inferred from a plan's own
`status` field or any other proxy (§4 of the 38D-B directive).
"""

from datetime import date, datetime


def _as_date(value) -> date:
    """Both `commitment["expected_monthly"][i]["date"]` and a snapshot's
    own `as_of_date` may arrive as a real `date` object (read straight
    from Postgres) or an ISO string (read back out of the JSONB column,
    see db.py's own `_parse_commitment_json_fields` docstring for why) --
    the same defensive coercion this codebase already applies to JSONB
    reads elsewhere. `commitment["committed_at"]` arrives as a real
    `datetime` (a plain TIMESTAMP column, never JSONB) -- `datetime` is
    itself a subclass of `date` in Python, so it must be checked FIRST
    and reduced with `.date()`, or a naive `isinstance(x, date)` check
    would silently accept it unconverted and later fail to compare
    against a plain `date`."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _month_key(d: date) -> tuple[int, int]:
    return (d.year, d.month)


def _eligible_snapshots_for_month(
    snapshots: list[dict], month_key: tuple[int, int], committed_at_date: date
) -> list[dict]:
    """A snapshot is eligible to represent a given expected month's
    actual ONLY when:

    1. its own `as_of_date` falls in that exact calendar month (§5 of the
       38D-B directive -- calendar-month alignment, never nearest/
       previous/next/interpolated), AND
    2. its `as_of_date` is on or after the commitment's own `committed_at`
       date (§20 -- a backdated snapshot whose as_of_date predates the
       commitment cannot honestly represent a REALIZED result of a plan
       that did not yet exist; see this module's own docstring in
       docs/product/SIE_COMMITTED_PLAN_LEARNING_ARCHITECTURE_V1.md §33
       for the full worked example this rule is derived from).

    When more than one eligible snapshot exists in the same month
    (§18), the winner is the one `get_latest_venture_financial_snapshot_for_owner()`
    would already pick -- `(as_of_date DESC, recorded_at DESC)` -- reused
    verbatim, not a new tie-break invented for this phase.
    """
    candidates = [
        s for s in snapshots
        if _month_key(_as_date(s["as_of_date"])) == month_key and _as_date(s["as_of_date"]) >= committed_at_date
    ]
    candidates.sort(key=lambda s: (_as_date(s["as_of_date"]), s["recorded_at"]), reverse=True)
    return candidates


def _metric(expected_value: int, actual_value: int | None) -> dict:
    """§8 of the 38D-B directive: NULL != 0. `expected_value` is never
    None -- a commitment can only ever be created when every field of
    every frozen month was already known (38D-A's own 422 guard on an
    incomplete snapshot), so this is a genuine invariant, not an
    unchecked assumption. `actual_value` may legitimately be None (no
    matching snapshot this month, or the snapshot exists but that
    specific field was never recorded) -- variance follows it to None,
    never a fabricated zero."""
    return {
        "expected": expected_value,
        "actual": actual_value,
        "variance": (actual_value - expected_value) if actual_value is not None else None,
    }


def build_commitment_comparison(commitment: dict, snapshots: list[dict], derive_metrics) -> dict:
    """
    `commitment` is a raw `venture_financial_commitments` row (as
    returned by get_venture_financial_commitment_for_owner() --
    already-parsed `expected_monthly`/`plan_snapshot` JSON). `snapshots`
    is the FULL history for this venture (list_venture_financial_snapshots_for_owner(),
    already ownership-scoped by the caller). `derive_metrics` is
    app.ai.financial_engine.compute_derived_metrics, passed in rather
    than imported directly so tests can exercise this function with
    plain dicts with zero risk of this module silently drifting from
    the ONE canonical actual-state derivation (§4).

    Never mutates `commitment` or `snapshots`. Never writes anything.
    """
    committed_at_date = _as_date(commitment["committed_at"])

    months: list[dict] = []
    observed_count = 0
    latest_comparable_month: date | None = None

    for month in commitment["expected_monthly"]:
        month_date = _as_date(month["date"])
        month_key = _month_key(month_date)
        eligible = _eligible_snapshots_for_month(snapshots, month_key, committed_at_date)
        actual_snapshot = eligible[0] if eligible else None

        if actual_snapshot is not None:
            derived = derive_metrics(actual_snapshot)
            actual_cash = actual_snapshot.get("cash_balance_cents")
            actual_revenue = derived["total_monthly_revenue_cents"]
            actual_expenses = derived["total_monthly_expenses_cents"]
            # Computed with the EXACT SAME formula project_monthly_cash_flow()
            # itself uses for the expected side (net_cash_change =
            # revenue - expenses) -- deliberately NOT derived from
            # compute_derived_metrics()'s own `net_burn_cents`, which is
            # the OPPOSITE sign convention (expenses - revenue, "positive
            # = burning"). Computing it fresh from the same two numbers
            # already extracted above avoids ever silently flipping a
            # sign -- see §6/§7 of the 38D-B directive.
            actual_net_cash_change = (
                actual_revenue - actual_expenses
                if actual_revenue is not None and actual_expenses is not None
                else None
            )
            observed_count += 1
            latest_comparable_month = month_date
        else:
            actual_cash = actual_revenue = actual_expenses = actual_net_cash_change = None

        months.append({
            "month_index": month["month_index"],
            "date": month_date,
            "actual_snapshot_id": actual_snapshot["id"] if actual_snapshot else None,
            "actual_as_of_date": _as_date(actual_snapshot["as_of_date"]) if actual_snapshot else None,
            "cash": _metric(month["ending_cash_cents"], actual_cash),
            "revenue": _metric(month["revenue_cents"], actual_revenue),
            "expenses": _metric(month["expenses_cents"], actual_expenses),
            "net_cash_change": _metric(month["net_cash_change_cents"], actual_net_cash_change),
        })

    total_months = len(months)
    if observed_count == 0:
        comparison_status = "awaiting_actuals"
    elif observed_count < total_months:
        comparison_status = "partially_observed"
    else:
        comparison_status = "observed"

    return {
        "commitment_id": commitment["id"],
        "committed_at": commitment["committed_at"],
        "source_snapshot_id": commitment["source_snapshot_id"],
        "scenario_name": commitment["scenario_name"],
        "calculation_version": commitment["calculation_version"],
        "months": months,
        "latest_comparable_month": latest_comparable_month,
        "comparison_status": comparison_status,
    }
