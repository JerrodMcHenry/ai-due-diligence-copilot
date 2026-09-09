"""
Regression tests for Phase 39B -- Contextual Hiring History Retrieval V1:
the pure retrieval function (app/ai/hiring_history.py) and the new
GET /ventures/{id}/financial-commitments/relevant-hire-history endpoint
(app/api.py).

Two layers, same convention as test_commitment_comparison.py:
  1. Direct unit tests of `find_relevant_hire_history()` against plain
     dicts and a stub comparison function -- no DB, no HTTP -- covering
     the eligibility/selection/silence rules exhaustively.
  2. API-level integration tests (TestClient, real DB) for
     authorization, the no-recompute guarantee, and a full live-shaped
     source-mutation regression.

Run with:
    python -m app.tests.test_hiring_history
"""

import time
from datetime import date, datetime

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine
from app.ai.hiring_history import find_relevant_hire_history


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# --- Layer 1: pure function unit tests --------------------------------------


def _hire_item(**overrides) -> dict:
    item = {
        "id": 1, "kind": "hire", "label": "Backend Engineer", "role": "Backend Engineer",
        "employment_type": "employee", "start_date": "2026-10-01", "end_date": None,
        "annual_salary_cents": 18_000_000, "burden_percent": 0.25, "monthly_cost_cents": 1_875_000,
        "one_time_cost_cents": None, "category": None, "amount_cents": None,
    }
    item.update(overrides)
    return item


def _revenue_item(**overrides) -> dict:
    item = {
        "id": 2, "kind": "revenue_target", "label": "Reach $30K MRR", "role": None,
        "employment_type": None, "start_date": "2026-10-01", "end_date": None,
        "annual_salary_cents": None, "burden_percent": None, "monthly_cost_cents": None,
        "one_time_cost_cents": None, "category": None, "amount_cents": 3_000_000,
    }
    item.update(overrides)
    return item


def _expense_item(**overrides) -> dict:
    item = {
        "id": 3, "kind": "expense_change", "label": "Cut contractors", "role": None,
        "employment_type": None, "start_date": "2026-10-01", "end_date": None,
        "annual_salary_cents": None, "burden_percent": None, "monthly_cost_cents": None,
        "one_time_cost_cents": None, "category": "contractors", "amount_cents": -500_000,
    }
    item.update(overrides)
    return item


def _commitment(id_: int, committed_at: str, plan_snapshot: list, founder_explanation: str | None = None) -> dict:
    return {
        "id": id_, "committed_at": datetime.fromisoformat(committed_at), "plan_snapshot": plan_snapshot,
        "founder_explanation": founder_explanation,
    }


def _month(
    month_index: int, iso_date: str, expected: int, actual: int | None,
    snapshot_id: int | None = 99, actual_as_of_date: str | None = None,
) -> dict:
    """`actual_as_of_date` defaults to `iso_date` -- the common case in
    these tests -- but can be set independently to exercise the real
    distinction the retrieval module itself relies on: the matched
    snapshot's own as_of_date is what gets shown as `observed_month`,
    never the expected-month's own (day-of-month-inheriting) marker."""
    return {
        "month_index": month_index, "date": iso_date,
        "actual_snapshot_id": snapshot_id if actual is not None else None,
        "actual_as_of_date": (actual_as_of_date or iso_date) if actual is not None else None,
        "expenses": {"expected": expected, "actual": actual, "variance": (actual - expected) if actual is not None else None},
    }


def _comparison(status: str, months: list) -> dict:
    return {"comparison_status": status, "months": months}


def _stub_comparison_map(mapping: dict):
    """Returns a `build_comparison` callable that looks up a
    pre-computed comparison by commitment id -- the same injection
    pattern find_relevant_hire_history() itself documents."""
    def _build(commitment: dict) -> dict:
        return mapping[commitment["id"]]
    return _build


def test_case_a_no_commitments_is_silence() -> None:
    result = find_relevant_hire_history([], _stub_comparison_map({}))
    expect(result is None, "no commitments at all must produce silence")


def test_case_c_awaiting_actuals_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("awaiting_actuals", [_month(1, "2026-10-01", 9_000_000, None)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "a commitment with no observed actuals must produce silence")


def test_case_d_observed_actuals_is_a_candidate() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is not None, "an observed commitment must produce a candidate")
    expect(result["historical_commitment_id"] == 1, result)
    expect(result["role"] == "Backend Engineer", result)
    expect(result["expected_total_expenses_cents"] == 9_000_000, result)
    expect(result["actual_total_expenses_cents"] == 9_700_000, result)
    expect(result["expense_variance_cents"] == 700_000, result)


def test_case_e_founder_explanation_is_included_verbatim() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()], founder_explanation="Contractor overlap lasted longer than expected.")]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["founder_explanation"] == "Contractor overlap lasted longer than expected.", result)


def test_case_f_contractor_only_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item(employment_type="contractor")])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "a contractor-only commitment must never be surfaced as employee-hire history")


def test_case_g_revenue_target_only_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_revenue_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "a revenue-target-only commitment must never be surfaced as hiring history")


def test_case_h_expense_change_only_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_expense_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "an expense-change-only commitment must never be surfaced as hiring history")


def test_case_i_bundled_commitment_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item(), _revenue_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "a bundled (multi-item) commitment must never be used -- 39A's own aggregation finding")


def test_case_j_two_eligible_commitments_returns_most_recent_only() -> None:
    commitments = [
        _commitment(1, "2026-06-01T00:00:00", [_hire_item(id=1, role="Old Engineer")]),
        _commitment(2, "2026-09-01T00:00:00", [_hire_item(id=1, role="New Engineer")]),
    ]
    comparisons = {
        1: _comparison("observed", [_month(1, "2026-07-01", 9_000_000, 9_700_000)]),
        2: _comparison("observed", [_month(1, "2026-10-01", 9_500_000, 9_600_000)]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["historical_commitment_id"] == 2, "the most recently committed eligible hire must win")
    expect(result["role"] == "New Engineer", result)


def test_case_k_newer_wins_even_without_explanation() -> None:
    commitments = [
        _commitment(1, "2026-06-01T00:00:00", [_hire_item(id=1)], founder_explanation="Old explanation."),
        _commitment(2, "2026-09-01T00:00:00", [_hire_item(id=1)], founder_explanation=None),
    ]
    comparisons = {
        1: _comparison("observed", [_month(1, "2026-07-01", 9_000_000, 9_700_000)]),
        2: _comparison("observed", [_month(1, "2026-10-01", 9_500_000, 9_600_000)]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["historical_commitment_id"] == 2, "recency must win over richer history -- never bias toward the one with an explanation")
    expect(result["founder_explanation"] is None, result)


def test_case_l_actual_above_expected_is_positive_variance() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 90_000_00, 97_000_00)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["expense_variance_cents"] == 7_000_00, result)


def test_case_m_actual_below_expected_is_negative_variance() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 90_000_00, 87_000_00)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["expense_variance_cents"] == -3_000_00, result)


def test_case_n_actual_equals_expected_is_zero_variance() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 90_000_00, 90_000_00)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["expense_variance_cents"] == 0, result)


def test_case_o_explanation_absent_is_omitted() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()], founder_explanation=None)]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["founder_explanation"] is None, result)


def test_case_p_explanation_present_is_verbatim() -> None:
    text_ = "Contractor overlap lasted longer than expected."
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()], founder_explanation=text_)]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["founder_explanation"] == text_, result)


def test_case_w_only_eligible_ones_considered_among_many() -> None:
    commitments = [
        _commitment(1, "2026-01-01T00:00:00", [_revenue_item()]),
        _commitment(2, "2026-02-01T00:00:00", [_expense_item()]),
        _commitment(3, "2026-03-01T00:00:00", [_hire_item(id=1, employment_type="contractor")]),
        _commitment(4, "2026-04-01T00:00:00", [_hire_item(id=1), _revenue_item()]),  # bundled
        _commitment(5, "2026-05-01T00:00:00", [_hire_item(id=1, role="Eligible Hire A")]),
        _commitment(6, "2026-06-01T00:00:00", [_revenue_item()]),
        _commitment(7, "2026-07-01T00:00:00", [_expense_item()]),
        _commitment(8, "2026-08-01T00:00:00", [_hire_item(id=1, role="Eligible Hire B")]),
        _commitment(9, "2026-09-01T00:00:00", [_revenue_item()]),
        _commitment(10, "2026-10-01T00:00:00", [_expense_item()]),
    ]
    comparisons = {
        3: _comparison("observed", [_month(1, "2026-04-01", 1, 1)]),
        4: _comparison("observed", [_month(1, "2026-05-01", 1, 1)]),
        5: _comparison("observed", [_month(1, "2026-06-01", 9_000_000, 9_100_000)]),
        8: _comparison("observed", [_month(1, "2026-09-01", 9_500_000, 9_400_000)]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["historical_commitment_id"] == 8, f"of ten commitments, only the newest ELIGIBLE one must be returned, got: {result}")
    expect(result["role"] == "Eligible Hire B", result)


def test_case_x_newest_ineligible_older_eligible_wins() -> None:
    commitments = [
        _commitment(1, "2026-06-01T00:00:00", [_hire_item(id=1, role="Older Eligible Hire")]),
        _commitment(2, "2026-09-01T00:00:00", [_hire_item(id=1), _revenue_item()]),  # newest, but bundled -> ineligible
    ]
    comparisons = {
        1: _comparison("observed", [_month(1, "2026-07-01", 9_000_000, 9_700_000)]),
        2: _comparison("observed", [_month(1, "2026-10-01", 9_500_000, 9_600_000)]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["historical_commitment_id"] == 1, "the newest commitment is ineligible (bundled) -- the older, eligible one must be selected instead")
    expect(result["role"] == "Older Eligible Hire", result)


def test_case_y_unknown_actual_expenses_are_never_fabricated_as_zero() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    # Month 2 has an actual snapshot but expenses were never recorded;
    # month 1 genuinely has a known expense figure.
    comparisons = {
        1: _comparison("partially_observed", [
            _month(1, "2026-10-01", 9_000_000, 9_700_000),
            _month(2, "2026-11-01", 9_500_000, None, snapshot_id=100),
        ]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is not None, "a genuinely known earlier month must still be used")
    expect(result["observed_month"] == "2026-10-01", "must fall back to the latest month with a KNOWN expense figure, not the literally-latest month")
    expect(result["actual_total_expenses_cents"] == 9_700_000, result)


def test_case_y2_no_month_has_known_expenses_is_silence() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {
        1: _comparison("partially_observed", [
            _month(1, "2026-10-01", 9_000_000, None, snapshot_id=100),
        ]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result is None, "if no observed month has a known expense figure, the whole commitment must be silent -- never fabricate a zero")


def test_observed_month_uses_the_actual_snapshots_own_date_not_the_projection_marker() -> None:
    """Found live during this phase's own walkthrough: a source
    snapshot's day-of-month (e.g. the 20th) propagates into every
    expected month's own `date` field via `_add_months()`, which need
    not match the day the REAL matching actual snapshot was recorded
    on. `observed_month` must report the latter, not the former."""
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-20", 9_000_000, 9_700_000, actual_as_of_date="2026-10-15")])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["observed_month"] == "2026-10-15", f"observed_month must be the matched snapshot's own as_of_date, got: {result}")


def test_case_z_deterministic_across_repeated_calls() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    build = _stub_comparison_map(comparisons)
    first = find_relevant_hire_history(commitments, build)
    second = find_relevant_hire_history(commitments, build)
    expect(first == second, "repeated calls against unchanged inputs must return an identical result")


def test_exclude_commitment_id_is_honored() -> None:
    commitments = [_commitment(1, "2026-09-01T00:00:00", [_hire_item()])]
    comparisons = {1: _comparison("observed", [_month(1, "2026-10-01", 9_000_000, 9_700_000)])}
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons), exclude_commitment_id=1)
    expect(result is None, "an explicitly excluded commitment must never be returned")


def test_order_independence_of_input_list() -> None:
    """§5: selection must be re-derived internally (committed_at DESC,
    id DESC), never trust the caller's own list ordering."""
    commitments = [
        _commitment(2, "2026-09-01T00:00:00", [_hire_item(id=1, role="Newer")]),
        _commitment(1, "2026-06-01T00:00:00", [_hire_item(id=1, role="Older")]),
    ]
    comparisons = {
        1: _comparison("observed", [_month(1, "2026-07-01", 9_000_000, 9_700_000)]),
        2: _comparison("observed", [_month(1, "2026-10-01", 9_500_000, 9_600_000)]),
    }
    result = find_relevant_hire_history(commitments, _stub_comparison_map(comparisons))
    expect(result["role"] == "Newer", "the function must sort by committed_at itself, not trust caller order")


TESTS_PURE = [
    test_case_a_no_commitments_is_silence,
    test_case_c_awaiting_actuals_is_silence,
    test_case_d_observed_actuals_is_a_candidate,
    test_case_e_founder_explanation_is_included_verbatim,
    test_case_f_contractor_only_is_silence,
    test_case_g_revenue_target_only_is_silence,
    test_case_h_expense_change_only_is_silence,
    test_case_i_bundled_commitment_is_silence,
    test_case_j_two_eligible_commitments_returns_most_recent_only,
    test_case_k_newer_wins_even_without_explanation,
    test_case_l_actual_above_expected_is_positive_variance,
    test_case_m_actual_below_expected_is_negative_variance,
    test_case_n_actual_equals_expected_is_zero_variance,
    test_case_o_explanation_absent_is_omitted,
    test_case_p_explanation_present_is_verbatim,
    test_case_w_only_eligible_ones_considered_among_many,
    test_case_x_newest_ineligible_older_eligible_wins,
    test_case_y_unknown_actual_expenses_are_never_fabricated_as_zero,
    test_case_y2_no_month_has_known_expenses_is_silence,
    test_observed_month_uses_the_actual_snapshots_own_date_not_the_projection_marker,
    test_case_z_deterministic_across_repeated_calls,
    test_exclude_commitment_id_is_honored,
    test_order_independence_of_input_list,
]


# --- Layer 2: API integration tests -----------------------------------------

USER_A = "zztest_hiringhistory_user_a"
USER_B = "zztest_hiringhistory_user_b"

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()

client = TestClient(api.app)


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(_public_key)


def _make_token(sub: str, exp_delta: int = 3600) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iss": TEST_ISSUER, "azp": TEST_AZP, "iat": now, "exp": now + exp_delta}
    return pyjwt.encode(payload, _private_key, algorithm="RS256")


class _patched_auth:
    def __enter__(self):
        self._orig_issuer = auth.CLERK_ISSUER
        self._orig_jwks_client = auth._jwks_client
        self._orig_resolve_parties = auth._resolve_authorized_parties
        auth.CLERK_ISSUER = TEST_ISSUER
        auth._jwks_client = lambda: _FakeJWKSClient()
        auth._resolve_authorized_parties = lambda: [TEST_AZP]
        return self

    def __exit__(self, *exc):
        auth.CLERK_ISSUER = self._orig_issuer
        auth._jwks_client = self._orig_jwks_client
        auth._resolve_authorized_parties = self._orig_resolve_parties
        return False


def _auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in (USER_A, USER_B):
            connection.execute(text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"), {"id": user_id})


def _cleanup() -> None:
    with engine.begin() as connection:
        for table in (
            "venture_financial_commitments", "venture_decisions", "venture_financial_scenarios",
            "venture_financial_plans", "venture_hire_plans", "venture_financial_snapshots",
        ):
            connection.execute(
                text(f"DELETE FROM {table} WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
                {"ids": [USER_A, USER_B]},
            )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture_body(name: str) -> dict:
    return {
        "name": name, "description": "Test venture for Hiring History.", "industry": None,
        "business_model": None, "target_customer": None, "stage": "Idea",
        "assumptions": {
            "target_customer": None,
            "market": {"market_description": None, "estimated_market_size": None, "competition_intensity": None},
            "problem_solution": {"problem_statement": None, "solution_description": None, "differentiation": None},
            "founder": {"founder_count": None, "relevant_domain_experience_years": None, "has_technical_cofounder": None, "has_business_cofounder": None},
            "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
            "economics": {"pricing_model": None, "price_point": None, "expected_gross_margin_pct": None},
            "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": None, "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None},
            "capital": {"starting_capital": None, "monthly_burn": None},
        },
    }


def _create_venture(user_id: str, name: str) -> dict:
    response = client.post("/ventures", json=_create_venture_body(name), headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Venture create failed: {response.text}")
    return response.json()


def _snapshot_body(**overrides) -> dict:
    body = {
        "as_of_date": "2026-09-01", "cash_balance_cents": 50_000_000, "monthly_recurring_revenue_cents": 2_000_000,
        "monthly_non_recurring_revenue_cents": 0, "payroll_cents": 0, "contractors_cents": 2_000_000,
        "software_cents": 0, "marketing_cents": 1_000_000, "rent_cents": 0, "professional_services_cents": 0,
        "other_expenses_cents": 4_000_000,
    }
    body.update(overrides)
    return body


def _post_snapshot(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/financials", json=_snapshot_body(**overrides), headers=_auth_headers(user_id))


def _create_hire(venture_id: int, user_id: str, **overrides):
    body = {
        "role": "Backend Engineer", "employment_type": "employee", "annual_salary_cents": 18_000_000,
        "burden_percent": 0.25, "monthly_cost_cents": None, "one_time_cost_cents": None,
        "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/hire-plans", json=body, headers=_auth_headers(user_id))


def _patch_hire(venture_id: int, user_id: str, hire_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/hire-plans/{hire_id}", json=fields, headers=_auth_headers(user_id))


def _commit(venture_id: int, user_id: str, **body):
    return client.post(f"/ventures/{venture_id}/financial-commitments", json=body, headers=_auth_headers(user_id))


def _relevant_hire_history(venture_id: int, user_id: str):
    return client.get(f"/ventures/{venture_id}/financial-commitments/relevant-hire-history", headers=_auth_headers(user_id))


def test_api_signed_out_cannot_access_endpoint() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/financial-commitments/relevant-hire-history").status_code == 401, "must require auth")


def test_api_no_history_is_a_null_body_not_an_error() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest HiringHistory A")
            response = _relevant_hire_history(venture["id"], USER_A)
            expect(response.status_code == 200, f"no history must be a normal 200, got: {response.status_code} {response.text}")
            expect(response.json() is None, "no relevant history must be a null body, never an error")
    finally:
        _cleanup()


def test_api_real_candidate_is_returned_with_correct_provenance() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest HiringHistory B")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, role="Backend Engineer", start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15", payroll_cents=1_950_000)

            response = _relevant_hire_history(venture["id"], USER_A)
            expect(response.status_code == 200, response.text)
            body = response.json()
            expect(body is not None, "a real observed hire commitment must produce a candidate")
            expect(body["historical_commitment_id"] == commitment["id"], body)
            expect(body["role"] == "Backend Engineer", body)
    finally:
        _cleanup()


def test_api_ownership_blocks_user_b() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest HiringHistory Ownership")
            expect(_relevant_hire_history(venture["id"], USER_B).status_code == 404, "User B must not read User A's hiring history")
    finally:
        _cleanup()


def test_api_no_recomputation_on_retrieval() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest HiringHistory Norecompute")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]])
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            original = api.project_monthly_cash_flow

            def _boom(*args, **kwargs):
                raise AssertionError("hiring-history retrieval must never call project_monthly_cash_flow")

            api.project_monthly_cash_flow = _boom
            try:
                response = _relevant_hire_history(venture["id"], USER_A)
                expect(response.status_code == 200, f"retrieval must succeed without recomputation, got: {response.status_code} {response.text}")
                expect(response.json() is not None, "a real candidate must still be returned")
            finally:
                api.project_monthly_cash_flow = original
    finally:
        _cleanup()


def test_api_source_mutation_safety() -> None:
    """§17 of the directive: commit -> retrieve -> edit the live hire ->
    retrieve again -> historical expected-side values must be identical."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest HiringHistory Mutation")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, role="Backend Engineer", annual_salary_cents=18_000_000, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            before = _relevant_hire_history(venture["id"], USER_A).json()
            expect(before is not None, "sanity: a real candidate must exist before the mutation")

            _patch_hire(venture["id"], USER_A, hire["id"], annual_salary_cents=99_000_000)

            after = _relevant_hire_history(venture["id"], USER_A).json()
            expect(after is not None, "the candidate must still exist after an unrelated live edit")
            expect(after["annual_salary_cents"] == before["annual_salary_cents"] == 18_000_000, "the historical salary must never move, no matter what the LIVE hire plan now says")
            expect(after["modeled_monthly_cost_cents"] == before["modeled_monthly_cost_cents"], "modeled_monthly_cost_cents must remain frozen")
            expect(after["expected_total_expenses_cents"] == before["expected_total_expenses_cents"], "expected_total_expenses_cents must remain frozen")
            expect(commitment["id"] == after["historical_commitment_id"], after)
    finally:
        _cleanup()


TESTS_API = [
    test_api_signed_out_cannot_access_endpoint,
    test_api_no_history_is_a_null_body_not_an_error,
    test_api_real_candidate_is_returned_with_correct_provenance,
    test_api_ownership_blocks_user_b,
    test_api_no_recomputation_on_retrieval,
    test_api_source_mutation_safety,
]

TESTS = TESTS_PURE + TESTS_API


def main() -> None:
    print("\nPhase 39B -- Contextual Hiring History Retrieval V1 tests")
    print("-" * 72)

    failures = []
    for test in TESTS:
        name = test.__name__
        try:
            test()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}\n      {e}")
            failures.append(name)
        except Exception as e:
            print(f"ERROR {name}\n      {type(e).__name__}: {e}")
            failures.append(name)

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
