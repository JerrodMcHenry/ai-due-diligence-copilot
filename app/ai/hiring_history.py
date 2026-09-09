"""
Phase 39B -- Contextual Hiring History Retrieval V1. See
docs/product/SIE_HISTORICAL_INTELLIGENCE_RETRIEVAL_V1.md §22-23 for the
accepted design this implements.

The first production slice of "Historical Intelligence" (Phase 39A):
while a founder is actively modeling a NEW employee hire, retrieve at
most ONE structurally relevant prior committed employee hire from the
same venture -- its frozen expectation, its observed actual, and the
founder's own explanation, verbatim. This is historical CONTEXT, never
a recommendation -- there is no field in this module's own output for
"what to do now," by construction (Phase 39A §4's own load-bearing rule).

Pure, deterministic, read-time-only -- identical discipline to
app/ai/commitment_comparison.py. No persistence, no AI, no causal
inference. `build_comparison` is injected (never imported directly) so
this module never silently drifts from the ONE canonical comparison
implementation and so tests can exercise it with plain dicts.
"""


def _eligible_single_hire_item(commitment: dict) -> dict | None:
    """
    A commitment is eligible only when its OWN plan_snapshot contains
    EXACTLY ONE item, and that item is an EMPLOYEE hire (`kind == "hire"`,
    `employment_type == "employee"`). This is the Phase 39A §12 finding,
    applied as a hard gate: `expected_monthly` is a BLENDED monthly
    aggregate across every item in a commitment's own plan_snapshot --
    for a bundled (multi-item) commitment, the aggregate expected/actual
    expense figures cannot be honestly attributed to one hire alone.
    Never loosened, per §4 of the 39B directive.

    Contractor hires are deliberately excluded -- V1 supports employee
    hires only (§3 of the directive: no inference, no equivalence
    assumed for a structurally different `employment_type`).
    """
    plan_snapshot = commitment.get("plan_snapshot") or []
    if len(plan_snapshot) != 1:
        return None
    item = plan_snapshot[0]
    if item.get("kind") != "hire" or item.get("employment_type") != "employee":
        return None
    return item


def _latest_month_with_known_expenses(comparison: dict) -> dict | None:
    """
    The single deterministic observed month this module ever uses: the
    MOST RECENT month (comparison["months"] is chronological ascending,
    per build_commitment_comparison()'s own contract) that both (a) has
    a matched actual snapshot at all, and (b) has a KNOWN (non-null)
    actual expense figure specifically -- §8/§9 Case Y of the directive:
    a month with SOME actual data but an unknown expense field must never
    be treated as though expenses were $0, and must never be chosen over
    an earlier month that genuinely has a known expense figure. Never an
    average, never the largest-variance month, never cherry-picked.
    """
    for month in reversed(comparison["months"]):
        if month["actual_snapshot_id"] is not None and month["expenses"]["actual"] is not None:
            return month
    return None


def _build_result(commitment: dict, item: dict, month: dict) -> dict:
    """
    Every field here is a verbatim, already-persisted fact -- see the
    provenance table in docs/product/SIE_HISTORICAL_INTELLIGENCE_RETRIEVAL_V1.md.
    `expense_variance_cents` is `month["expenses"]["variance"]` exactly
    as build_commitment_comparison() already computed it (actual -
    expected, sign preserved) -- no second variance implementation.
    Deliberately does NOT attribute the total-expense variance to the
    hire itself (§7 of the directive: "the plan expected total monthly
    expenses of $X; the observed month recorded $Y," never "the hire
    cost $Z more than expected" -- the latter is not supported by any
    hire-specific actual-cost data this codebase has).

    `observed_month` is deliberately `month["actual_as_of_date"]` -- the
    MATCHED SNAPSHOT's own as_of_date -- never `month["date"]` (the
    expected-month's own calendar marker, which inherits the source
    commitment's snapshot's day-of-month via `_add_months()` and can
    land on an arbitrary day, e.g. the 20th, that has no relationship to
    when the actual snapshot was actually recorded). Confirmed live
    during this phase's own walkthrough: a source snapshot dated Sept 20
    produced an expected-month marker of Oct 20, while the real matching
    actual snapshot was recorded Oct 15 -- showing "Oct 20" as the
    "observed month" would have been a confusing, avoidable mismatch.
    `actual_as_of_date` is guaranteed non-null here because this
    function is only ever called on a month `_latest_month_with_known_expenses()`
    already confirmed has a matched actual snapshot.
    """
    return {
        "historical_commitment_id": commitment["id"],
        "committed_at": commitment["committed_at"],
        "role": item["role"],
        "employment_type": item["employment_type"],
        "annual_salary_cents": item.get("annual_salary_cents"),
        "burden_percent": item.get("burden_percent"),
        "modeled_monthly_cost_cents": item.get("monthly_cost_cents"),
        "observed_month": month["actual_as_of_date"],
        "expected_total_expenses_cents": month["expenses"]["expected"],
        "actual_total_expenses_cents": month["expenses"]["actual"],
        "expense_variance_cents": month["expenses"]["variance"],
        "founder_explanation": commitment.get("founder_explanation"),
    }


def find_relevant_hire_history(
    commitments: list[dict],
    build_comparison,
    exclude_commitment_id: int | None = None,
) -> dict | None:
    """
    `commitments` is the venture's full, already ownership-scoped
    `list_venture_financial_commitments_for_owner()` result, in ANY
    order -- this function re-sorts internally
    (`committed_at DESC, id DESC`, §5 of the directive's own preferred
    tie-break) so it never depends on the caller's own query ordering.
    `build_comparison` is a single-argument callable, `commitment ->
    comparison dict`, expected to be `app.ai.commitment_comparison.build_commitment_comparison`
    already partially applied to this venture's snapshots and
    `compute_derived_metrics` -- injected so this module has zero direct
    dependency on the database or the financial engine (§6/§16: this
    function must keep working even if the projection engine itself is
    broken, because it never calls it).

    Returns the single most recent eligible candidate's result dict, or
    None -- silence -- when no commitment qualifies. Never raises for a
    "no history" venture; that is the expected, majority-case outcome.
    """
    ordered = sorted(commitments, key=lambda c: (c["committed_at"], c["id"]), reverse=True)

    for commitment in ordered:
        if exclude_commitment_id is not None and commitment["id"] == exclude_commitment_id:
            continue

        item = _eligible_single_hire_item(commitment)
        if item is None:
            continue

        comparison = build_comparison(commitment)
        if comparison["comparison_status"] == "awaiting_actuals":
            continue

        month = _latest_month_with_known_expenses(comparison)
        if month is None:
            continue

        return _build_result(commitment, item, month)

    return None
