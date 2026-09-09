"""
Regression tests for Phase 38D-B -- Committed Expectation vs Actual V1:
the pure comparison function (app/ai/commitment_comparison.py) and the
new GET /ventures/{id}/financial-commitments/{id}/comparison endpoint
(app/api.py).

Two layers, same file:
  1. Direct unit tests of `build_commitment_comparison()` against plain
     dicts -- no DB, no HTTP -- for the tricky semantic cases (month
     alignment, pre-commit exclusion, multi-snapshot tie-break, null
     handling). Same hand-rolled expect()/PASS-FAIL convention as every
     other backend test file.
  2. API-level integration tests (TestClient, real DB) for the full
     lifecycle: authorization, awaiting/partial/observed status,
     immutability re-verification after this phase's own comparison
     reads exist.

Run with:
    python -m app.tests.test_commitment_comparison
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
from app.ai.commitment_comparison import build_commitment_comparison
from app.ai.financial_engine import compute_derived_metrics


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# --- Layer 1: pure function unit tests --------------------------------------


def _expected_month(month_index: int, iso_date: str, **overrides) -> dict:
    month = {
        "month_index": month_index, "date": iso_date, "starting_cash_cents": 50_000_000,
        "revenue_cents": 2_000_000, "expenses_cents": 7_000_000, "plan_expense_impact_cents": 0,
        "plan_revenue_active": False, "active_plan_item_ids": [],
        "net_cash_change_cents": -5_000_000, "ending_cash_cents": 45_000_000, "depleted": False,
    }
    month.update(overrides)
    return month


def _commitment(committed_at: str, expected_monthly: list[dict], **overrides) -> dict:
    row = {
        "id": 1, "committed_at": datetime.fromisoformat(committed_at), "source_snapshot_id": 900,
        "scenario_name": "Test Plan", "calculation_version": "1", "expected_monthly": expected_monthly,
    }
    row.update(overrides)
    return row


def _snapshot(id_: int, as_of_date: str, recorded_at: str = "2026-01-01T00:00:00", **overrides) -> dict:
    row = {
        "id": id_, "as_of_date": date.fromisoformat(as_of_date), "recorded_at": datetime.fromisoformat(recorded_at),
        "cash_balance_cents": 40_000_000, "monthly_recurring_revenue_cents": 1_800_000,
        "monthly_non_recurring_revenue_cents": 0, "payroll_cents": 6_000_000, "contractors_cents": 0,
        "software_cents": 0, "marketing_cents": 0, "rent_cents": 0, "professional_services_cents": 0,
        "other_expenses_cents": 0,
    }
    row.update(overrides)
    return row


def test_case_a_no_actual_snapshot_is_awaiting_actuals() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    result = build_commitment_comparison(commitment, [], compute_derived_metrics)
    expect(result["comparison_status"] == "awaiting_actuals", result)
    expect(result["months"][0]["cash"]["actual"] is None, result)
    expect(result["latest_comparable_month"] is None, result)


def test_case_b_c_matching_month_snapshot_produces_signed_cash_variance() -> None:
    commitment = _commitment(
        "2026-09-01T00:00:00",
        [_expected_month(1, "2026-10-01", ending_cash_cents=31_000_000)],
    )
    snapshots = [_snapshot(10, "2026-10-15", cash_balance_cents=24_700_000)]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    expect(result["comparison_status"] == "observed", result)
    month = result["months"][0]
    expect(month["actual_snapshot_id"] == 10, month)
    expect(month["cash"]["expected"] == 31_000_000, month)
    expect(month["cash"]["actual"] == 24_700_000, month)
    expect(month["cash"]["variance"] == -6_300_000, f"variance must be actual - expected (signed), got: {month['cash']}")


def test_case_d_revenue_variance_is_signed() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01", revenue_cents=8_000_000)])
    snapshots = [_snapshot(10, "2026-10-15", monthly_recurring_revenue_cents=7_400_000, monthly_non_recurring_revenue_cents=0)]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["revenue"]["expected"] == 8_000_000, month)
    expect(month["revenue"]["actual"] == 7_400_000, month)
    expect(month["revenue"]["variance"] == -600_000, month)


def test_case_e_expense_variance_is_signed() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01", expenses_cents=9_500_000)])
    snapshots = [_snapshot(10, "2026-10-15", payroll_cents=10_200_000)]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["expenses"]["expected"] == 9_500_000, month)
    expect(month["expenses"]["actual"] == 10_200_000, month)
    expect(month["expenses"]["variance"] == 700_000, f"an expense OVERRUN must be a POSITIVE variance (actual - expected), got: {month['expenses']}")


def test_case_f_net_cash_change_is_computed_identically_on_both_sides() -> None:
    # Expected: revenue 8,000,000 - expenses 9,500,000 = -1,500,000.
    commitment = _commitment(
        "2026-09-01T00:00:00",
        [_expected_month(1, "2026-10-01", revenue_cents=8_000_000, expenses_cents=9_500_000, net_cash_change_cents=-1_500_000)],
    )
    # Actual: revenue 7,400,000 - expenses 10,200,000 = -2,800,000.
    snapshots = [_snapshot(10, "2026-10-15", monthly_recurring_revenue_cents=7_400_000, payroll_cents=10_200_000)]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["net_cash_change"]["expected"] == -1_500_000, month)
    expect(month["net_cash_change"]["actual"] == -2_800_000, f"actual net cash change must be actual revenue - actual expenses, got: {month['net_cash_change']}")
    expect(month["net_cash_change"]["variance"] == -1_300_000, month)


def test_case_g_unavailable_expected_never_happens_but_missing_actual_field_is_null() -> None:
    # A snapshot exists this month, but revenue was never recorded --
    # NULL != 0, must never become a fake $0 actual/variance for that
    # ONE metric, even though cash/expenses ARE known.
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    snapshots = [_snapshot(10, "2026-10-15", monthly_recurring_revenue_cents=None, monthly_non_recurring_revenue_cents=None)]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["revenue"]["actual"] is None, month)
    expect(month["revenue"]["variance"] is None, "an unknown actual revenue must never produce a fake variance")
    expect(month["net_cash_change"]["actual"] is None, "net cash change must also be unknown when either side of it is unknown")
    expect(month["cash"]["actual"] is not None, "an unrelated, genuinely-known metric in the SAME snapshot must still be compared")


def test_case_h_no_snapshot_at_all_means_every_metric_is_unavailable() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    result = build_commitment_comparison(commitment, [], compute_derived_metrics)
    month = result["months"][0]
    for key in ("cash", "revenue", "expenses", "net_cash_change"):
        expect(month[key]["actual"] is None, month)
        expect(month[key]["variance"] is None, month)


def test_case_i_no_snapshot_in_month_means_no_interpolation() -> None:
    commitment = _commitment(
        "2026-09-01T00:00:00",
        [_expected_month(1, "2026-10-01"), _expected_month(2, "2026-11-01")],
    )
    # Only a November snapshot exists -- October must NOT borrow it.
    snapshots = [_snapshot(10, "2026-11-15")]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    expect(result["months"][0]["cash"]["actual"] is None, "October has no snapshot of its own and must not be filled in from November")
    expect(result["months"][1]["cash"]["actual"] is not None, "November's own snapshot must still be used for November")


def test_case_j_multiple_snapshots_same_month_latest_as_of_date_wins() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    snapshots = [
        _snapshot(10, "2026-10-05", cash_balance_cents=10_000_000),
        _snapshot(11, "2026-10-18", cash_balance_cents=20_000_000),
        _snapshot(12, "2026-10-31", cash_balance_cents=30_000_000),
    ]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["actual_snapshot_id"] == 12, f"the LATEST as_of_date within the month must win, got: {month}")
    expect(month["cash"]["actual"] == 30_000_000, month)


def test_case_j2_same_as_of_date_tiebreak_uses_recorded_at() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    snapshots = [
        _snapshot(10, "2026-10-15", recorded_at="2026-10-15T09:00:00", cash_balance_cents=10_000_000),
        _snapshot(11, "2026-10-15", recorded_at="2026-10-15T17:00:00", cash_balance_cents=20_000_000),
    ]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    month = result["months"][0]
    expect(month["actual_snapshot_id"] == 11, f"identical as_of_date must tie-break on the LATEST recorded_at, got: {month}")


def test_case_k_snapshots_in_neighboring_months_are_never_used() -> None:
    commitment = _commitment("2026-09-01T00:00:00", [_expected_month(1, "2026-10-01")])
    snapshots = [_snapshot(9, "2026-09-30"), _snapshot(11, "2026-11-01")]
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    expect(result["months"][0]["actual_snapshot_id"] is None, "a September or November snapshot must never stand in for October")


def test_case_l_m_partial_actual_history_leaves_future_months_awaiting() -> None:
    commitment = _commitment(
        "2026-09-01T00:00:00",
        [_expected_month(i, f"2026-{9+i:02d}-01") for i in range(1, 4)],  # Oct, Nov, Dec
    )
    snapshots = [_snapshot(10, "2026-10-15"), _snapshot(11, "2026-11-15")]  # no December yet
    result = build_commitment_comparison(commitment, snapshots, compute_derived_metrics)
    expect(result["comparison_status"] == "partially_observed", result)
    expect(result["months"][0]["actual_snapshot_id"] is not None, "October must be observed")
    expect(result["months"][1]["actual_snapshot_id"] is not None, "November must be observed")
    expect(result["months"][2]["actual_snapshot_id"] is None, "December (a future month) must remain awaiting actuals")
    expect(result["latest_comparable_month"] == date(2026, 11, 1), result)


def test_case_z_pre_commit_same_month_snapshot_is_not_used() -> None:
    """§20/§33: a snapshot whose as_of_date predates the commitment
    itself must never be mistaken for a realized post-commitment
    actual, even when it falls in the right calendar month."""
    commitment = _commitment("2026-12-20T00:00:00", [_expected_month(1, "2026-12-15")])
    pre_commit_snapshot = _snapshot(10, "2026-12-05")  # before committed_at
    result = build_commitment_comparison(commitment, [pre_commit_snapshot], compute_derived_metrics)
    expect(result["months"][0]["actual_snapshot_id"] is None, "a December 5 snapshot must not become the actual for a plan committed December 20")
    expect(result["comparison_status"] == "awaiting_actuals", result)


def test_case_z2_post_commit_same_month_snapshot_is_used() -> None:
    commitment = _commitment("2026-12-20T00:00:00", [_expected_month(1, "2026-12-15")])
    post_commit_snapshot = _snapshot(10, "2026-12-22")  # after committed_at
    result = build_commitment_comparison(commitment, [post_commit_snapshot], compute_derived_metrics)
    expect(result["months"][0]["actual_snapshot_id"] == 10, "a December 22 snapshot -- after the Dec 20 commit -- must be used")


def test_case_y_first_projection_month_is_one_calendar_month_after_the_source_snapshot() -> None:
    """§19: project_monthly_cash_flow()'s own month_index=1 is
    `_add_months(as_of_date, 1)` -- one calendar month AFTER the source
    snapshot's own as_of_date, never the same month. This test proves
    the comparison's own alignment agrees with that engine semantic
    directly, rather than assuming it."""
    from app.ai.financial_engine import project_monthly_cash_flow
    source_snapshot = _snapshot(1, "2026-06-15", cash_balance_cents=50_000_000)
    projection = project_monthly_cash_flow(source_snapshot, source_snapshot["as_of_date"], horizon_months=2)
    expect(projection[0]["date"] == date(2026, 7, 15), f"month_index=1 must be July (one month after the June source snapshot), got: {projection[0]['date']}")

    commitment = _commitment("2026-06-15T00:00:00", [
        {**projection[0], "date": projection[0]["date"].isoformat()},
    ])
    # A June-dated snapshot (the source snapshot's own month) must NOT be
    # usable as July's actual, and a July snapshot must be.
    june_snapshot = _snapshot(2, "2026-06-20")
    july_snapshot = _snapshot(3, "2026-07-20")
    result = build_commitment_comparison(commitment, [june_snapshot, july_snapshot], compute_derived_metrics)
    expect(result["months"][0]["actual_snapshot_id"] == 3, "only the July snapshot may satisfy month_index=1's own July calendar month")


TESTS_PURE = [
    test_case_a_no_actual_snapshot_is_awaiting_actuals,
    test_case_b_c_matching_month_snapshot_produces_signed_cash_variance,
    test_case_d_revenue_variance_is_signed,
    test_case_e_expense_variance_is_signed,
    test_case_f_net_cash_change_is_computed_identically_on_both_sides,
    test_case_g_unavailable_expected_never_happens_but_missing_actual_field_is_null,
    test_case_h_no_snapshot_at_all_means_every_metric_is_unavailable,
    test_case_i_no_snapshot_in_month_means_no_interpolation,
    test_case_j_multiple_snapshots_same_month_latest_as_of_date_wins,
    test_case_j2_same_as_of_date_tiebreak_uses_recorded_at,
    test_case_k_snapshots_in_neighboring_months_are_never_used,
    test_case_l_m_partial_actual_history_leaves_future_months_awaiting,
    test_case_z_pre_commit_same_month_snapshot_is_not_used,
    test_case_z2_post_commit_same_month_snapshot_is_used,
    test_case_y_first_projection_month_is_one_calendar_month_after_the_source_snapshot,
]


# --- Layer 2: API integration tests -----------------------------------------

USER_A = "zztest_comparison_user_a"
USER_B = "zztest_comparison_user_b"

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
        "name": name, "description": "Test venture for Commitment Comparison.", "industry": None,
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
        "role": "Senior Engineer", "employment_type": "employee", "annual_salary_cents": 18_000_000,
        "burden_percent": 0.25, "monthly_cost_cents": None, "one_time_cost_cents": None,
        "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/hire-plans", json=body, headers=_auth_headers(user_id))


def _patch_hire(venture_id: int, user_id: str, hire_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/hire-plans/{hire_id}", json=fields, headers=_auth_headers(user_id))


def _commit(venture_id: int, user_id: str, **body):
    return client.post(f"/ventures/{venture_id}/financial-commitments", json=body, headers=_auth_headers(user_id))


def _comparison(venture_id: int, user_id: str, commitment_id: int):
    return client.get(f"/ventures/{venture_id}/financial-commitments/{commitment_id}/comparison", headers=_auth_headers(user_id))


def test_api_signed_out_cannot_access_comparison() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/financial-commitments/1/comparison").status_code == 401, "GET comparison must require auth")


def test_api_new_commitment_with_no_actuals_is_awaiting() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison Awaiting")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            response = _comparison(venture["id"], USER_A, commitment["id"])
            expect(response.status_code == 200, response.text)
            body = response.json()
            expect(body["comparison_status"] == "awaiting_actuals", body)
            expect(all(m["cash"]["actual"] is None for m in body["months"]), body)
    finally:
        _cleanup()


def test_api_matching_snapshot_produces_observed_comparison() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison Observed")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15", cash_balance_cents=44_000_000)

            body = _comparison(venture["id"], USER_A, commitment["id"]).json()
            expect(body["comparison_status"] == "partially_observed", body)
            month1 = body["months"][0]
            expect(month1["cash"]["actual"] == 44_000_000, month1)
            expect(month1["cash"]["variance"] == 44_000_000 - month1["cash"]["expected"], month1)
    finally:
        _cleanup()


def test_api_ownership_blocks_user_b() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison Ownership")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            expect(_comparison(venture["id"], USER_B, commitment["id"]).status_code == 404, "User B must not read User A's comparison")
    finally:
        _cleanup()


def test_api_no_recomputation_on_comparison_read() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison Norecompute")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            original = api.project_monthly_cash_flow

            def _boom(*args, **kwargs):
                raise AssertionError("comparison must never call the projection engine")

            api.project_monthly_cash_flow = _boom
            try:
                response = _comparison(venture["id"], USER_A, commitment["id"])
                expect(response.status_code == 200, f"comparison must succeed without recomputation, got: {response.status_code} {response.text}")
            finally:
                api.project_monthly_cash_flow = original
    finally:
        _cleanup()


def test_api_source_mutation_regression_expected_side_unchanged() -> None:
    """Re-verifies 38D-A's own load-bearing immutability guarantee still
    holds now that a comparison read-path exists alongside it."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison Immutability")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, role="Engineer", annual_salary_cents=18_000_000, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            before = _comparison(venture["id"], USER_A, commitment["id"]).json()

            _patch_hire(venture["id"], USER_A, hire["id"], annual_salary_cents=40_000_000)
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            after = _comparison(venture["id"], USER_A, commitment["id"]).json()
            for m_before, m_after in zip(before["months"], after["months"]):
                expect(m_before["cash"]["expected"] == m_after["cash"]["expected"], "expected cash must never move after a source plan edit")
                expect(m_before["revenue"]["expected"] == m_after["revenue"]["expected"], "expected revenue must never move")
                expect(m_before["expenses"]["expected"] == m_after["expenses"]["expected"], "expected expenses must never move")
    finally:
        _cleanup()


def test_api_cash_flow_positive_actual_is_neutral_arithmetic() -> None:
    """Case W: a healthy/cash-flow-positive actual month must produce
    plain signed arithmetic, never a runway field or any qualitative
    label."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison CFP")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            _post_snapshot(
                venture["id"], USER_A, as_of_date="2026-10-15",
                cash_balance_cents=60_000_000, monthly_recurring_revenue_cents=9_000_000,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=1_000_000,
            )
            body = _comparison(venture["id"], USER_A, commitment["id"]).json()
            month1 = body["months"][0]
            expect("runway" not in month1, month1)
            expect(month1["net_cash_change"]["actual"] == 8_000_000, month1)
    finally:
        _cleanup()


def test_api_out_of_cash_actual_is_literal_arithmetic_only() -> None:
    """Case X: an out-of-cash actual month must still produce only plain
    arithmetic -- no recommendation, no alert field."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Comparison OOC")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            _post_snapshot(
                venture["id"], USER_A, as_of_date="2026-10-15",
                cash_balance_cents=0, monthly_recurring_revenue_cents=1_000_000,
                payroll_cents=8_000_000, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=0,
            )
            body = _comparison(venture["id"], USER_A, commitment["id"]).json()
            month1 = body["months"][0]
            expect(month1["cash"]["actual"] == 0, month1)
            expect(month1["cash"]["variance"] is not None, month1)
            expect(set(month1.keys()) == {"month_index", "date", "actual_snapshot_id", "actual_as_of_date", "cash", "revenue", "expenses", "net_cash_change"}, "no extra recommendation/alert field may exist on a month comparison")
    finally:
        _cleanup()


TESTS_API = [
    test_api_signed_out_cannot_access_comparison,
    test_api_new_commitment_with_no_actuals_is_awaiting,
    test_api_matching_snapshot_produces_observed_comparison,
    test_api_ownership_blocks_user_b,
    test_api_no_recomputation_on_comparison_read,
    test_api_source_mutation_regression_expected_side_unchanged,
    test_api_cash_flow_positive_actual_is_neutral_arithmetic,
    test_api_out_of_cash_actual_is_literal_arithmetic_only,
]

TESTS = TESTS_PURE + TESTS_API


def main() -> None:
    print("\nPhase 38D-B -- Committed Expectation vs Actual V1 tests")
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
