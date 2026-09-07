"""
Regression tests for Phase 35B -- Financial State Persistence + Runway
Engine V1: the venture_financial_snapshots table (app/database/db.py),
its Pydantic contracts (app/models/venture_financials.py), the
deterministic calculation engine (app/ai/financial_engine.py), and the
new /ventures/{id}/financials, /ventures/{id}/financials/history
endpoints in app/api.py.

Same JWT-mocking harness and zztest_* user-id convention as
test_build_intelligence_loop.py -- no live Clerk dependency, every row
cleaned up in a finally block even on failure.

Run with:
    python -m app.tests.test_venture_financials
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_finance_user_a"
USER_B = "zztest_finance_user_b"

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
            connection.execute(
                text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"), {"id": user_id}
            )


def _cleanup() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM venture_financial_snapshots WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
            {"ids": [USER_A, USER_B]},
        )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture_body(name: str) -> dict:
    return {
        "name": name,
        "description": "Test venture for the Financial Decision Engine.",
        "industry": None,
        "business_model": None,
        "target_customer": None,
        "stage": "Idea",
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
        "as_of_date": "2026-01-01",
        "cash_balance_cents": None,
        "monthly_recurring_revenue_cents": None,
        "monthly_non_recurring_revenue_cents": None,
        "payroll_cents": None,
        "contractors_cents": None,
        "software_cents": None,
        "marketing_cents": None,
        "rent_cents": None,
        "professional_services_cents": None,
        "other_expenses_cents": None,
    }
    body.update(overrides)
    return body


def _post_snapshot(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/financials", json=_snapshot_body(**overrides), headers=_auth_headers(user_id))


def _get_financials(venture_id: int, user_id: str):
    return client.get(f"/ventures/{venture_id}/financials", headers=_auth_headers(user_id))


# --- Authorization -----------------------------------------------------------


def test_signed_out_cannot_access_financials_endpoints() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/financials").status_code == 401, "GET financials must require auth")
        expect(client.post("/ventures/1/financials", json={}).status_code == 401, "POST financials must require auth")
        expect(client.get("/ventures/1/financials/history").status_code == 401, "GET history must require auth")


# --- Case A: empty state ------------------------------------------------------


def test_case_a_empty_state_has_no_fake_zero_metrics() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance A")
            result = _get_financials(venture["id"], USER_A)
            expect(result.status_code == 200, result.text)
            body = result.json()
            expect(body["latest_snapshot"] is None, "a brand-new venture must have no snapshot")
            expect(body["derived"] is None, "a brand-new venture must have no derived metrics -- never a fake $0/0-month result")
            expect(body["projection"] == [], "a brand-new venture must have no projection")
    finally:
        _cleanup()


# --- Case B: basic burn --------------------------------------------------------


def test_case_b_basic_burn_and_runway() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance B")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,  # $500,000
                monthly_recurring_revenue_cents=2_000_000,  # $20,000
                monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0,
                other_expenses_cents=7_000_000,  # $70,000
            )
            expect(response.status_code == 200, response.text)
            derived = response.json()["derived"]
            expect(derived["net_burn_cents"] == 5_000_000, f"expected $50K/mo net burn, got: {derived}")
            expect(derived["runway_months"] == 10.0, f"expected 10.0 months runway, got: {derived}")
            expect(derived["status"] == "burning", derived)
    finally:
        _cleanup()


# --- Case C: multiple expense categories ---------------------------------------


def test_case_c_expense_categories_sum_correctly() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance C")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=0, monthly_non_recurring_revenue_cents=0,
                payroll_cents=4_000_000, contractors_cents=0, software_cents=500_000,
                marketing_cents=1_000_000, rent_cents=0, professional_services_cents=0,
                other_expenses_cents=1_500_000,
            )
            derived = response.json()["derived"]
            expect(derived["total_monthly_expenses_cents"] == 7_000_000, f"expected $70K total expenses, got: {derived}")
    finally:
        _cleanup()


# --- Case D: cash-flow positive -------------------------------------------------


def test_case_d_cash_flow_positive_shows_no_finite_runway() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance D")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=10_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=8_000_000, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=0,
            )
            derived = response.json()["derived"]
            expect(derived["status"] == "cash_flow_positive", derived)
            expect(derived["net_burn_cents"] == -2_000_000, f"expected -$20K/mo (generating cash), got: {derived}")
            expect(derived["runway_months"] is None, "a cash-flow-positive company must never show a finite runway countdown")
    finally:
        _cleanup()


# --- Case E: break-even ---------------------------------------------------------


def test_case_e_break_even() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance E")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=7_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=7_000_000,
            )
            derived = response.json()["derived"]
            expect(derived["net_burn_cents"] == 0, derived)
            expect(derived["status"] == "break_even", derived)
            expect(derived["runway_months"] is None, "break-even must never show a finite runway countdown")
    finally:
        _cleanup()


# --- Case F: zero cash -----------------------------------------------------------


def test_case_f_zero_cash_with_positive_burn_is_out_of_cash() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance F")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=0,
                monthly_recurring_revenue_cents=2_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=7_000_000,
            )
            derived = response.json()["derived"]
            expect(derived["status"] == "out_of_cash", derived)
            expect(derived["runway_months"] == 0.0, derived)
    finally:
        _cleanup()


# --- Case G / H: explicit zero vs. unknown ---------------------------------------


def test_case_g_explicit_zero_revenue_is_known_not_unknown() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance G")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=0, monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=5_000_000,
            )
            derived = response.json()["derived"]
            expect(derived["total_monthly_revenue_cents"] == 0, f"explicit zero revenue must be treated as known ($0), got: {derived}")
            expect(derived["status"] == "burning", "an explicit-zero-revenue snapshot with real expenses must still calculate burn")
    finally:
        _cleanup()


def test_case_h_unknown_revenue_never_silently_becomes_zero() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance H")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=None, monthly_non_recurring_revenue_cents=None,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=5_000_000,
            )
            derived = response.json()["derived"]
            expect(derived["total_monthly_revenue_cents"] is None, f"unknown revenue must stay unknown, got: {derived}")
            expect(derived["net_burn_cents"] is None, "burn must not be calculable when revenue is unknown")
            expect(derived["status"] == "insufficient_data", derived)
    finally:
        _cleanup()


# --- Case I / J: monthly projection ------------------------------------------


def test_case_i_monthly_projection_deterministic_depletion() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance I")
            response = _post_snapshot(
                venture["id"], USER_A,
                as_of_date="2026-01-01",
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=2_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=7_000_000,
            )
            projection = response.json()["projection"]
            expect(projection[0]["ending_cash_cents"] == 45_000_000, f"month 1 ending cash, got: {projection[0]}")
            expect(projection[1]["ending_cash_cents"] == 40_000_000, f"month 2 ending cash, got: {projection[1]}")
            expect(any(m["depleted"] for m in projection), "a burning company's projection must flag depletion")
            expect(projection[-1]["ending_cash_cents"] == 0, "cash must never be displayed as negative")
            expect(not any(m["ending_cash_cents"] < 0 for m in projection), "no month may show negative cash")
    finally:
        _cleanup()


def test_case_j_profitable_projection_never_terminates_early() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance J")
            response = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=10_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=8_000_000, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=0,
            )
            projection = response.json()["projection"]
            expect(projection[0]["ending_cash_cents"] == 52_000_000, f"month 1, got: {projection[0]}")
            expect(len(projection) == 24, f"a cash-flow-positive projection must run the full bounded horizon (24), got {len(projection)}")
            expect(not any(m["depleted"] for m in projection), "a profitable company's projection must never show depletion")
    finally:
        _cleanup()


# --- Case K: ownership security ---------------------------------------------


def test_case_k_ownership_security() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance K")
            _post_snapshot(venture["id"], USER_A, cash_balance_cents=50_000_000)

            read_as_b = _get_financials(venture["id"], USER_B)
            expect(read_as_b.status_code == 404, f"User B must not be able to read User A's venture financials, got {read_as_b.status_code}")

            write_as_b = _post_snapshot(venture["id"], USER_B, cash_balance_cents=1)
            expect(write_as_b.status_code == 404, f"User B must not be able to write User A's venture financials, got {write_as_b.status_code}")

            history_as_b = client.get(f"/ventures/{venture['id']}/financials/history", headers=_auth_headers(USER_B))
            expect(history_as_b.status_code == 404, "User B must not be able to read User A's financial history")
    finally:
        _cleanup()


# --- Case L: reload -----------------------------------------------------------


def test_case_l_reload_survives() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance L")
            posted = _post_snapshot(
                venture["id"], USER_A,
                cash_balance_cents=50_000_000,
                monthly_recurring_revenue_cents=2_000_000, monthly_non_recurring_revenue_cents=0,
                payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
                rent_cents=0, professional_services_cents=0, other_expenses_cents=7_000_000,
            ).json()

            reloaded = _get_financials(venture["id"], USER_A).json()
            expect(reloaded["latest_snapshot"]["cash_balance_cents"] == 50_000_000, "cash must survive reload")
            expect(reloaded["derived"] == posted["derived"], "derived metrics must be identical after reload (same deterministic computation)")
    finally:
        _cleanup()


# --- Case M: history safety ----------------------------------------------------


def test_case_m_updating_the_snapshot_preserves_prior_history() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Finance M")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-01-01", cash_balance_cents=50_000_000)
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-02-01", cash_balance_cents=45_000_000)

            current = _get_financials(venture["id"], USER_A).json()
            expect(current["latest_snapshot"]["cash_balance_cents"] == 45_000_000, "the LATEST snapshot must reflect the newest as_of_date")

            history = client.get(f"/ventures/{venture['id']}/financials/history", headers=_auth_headers(USER_A)).json()
            cash_values = [s["cash_balance_cents"] for s in history["snapshots"]]
            expect(50_000_000 in cash_values, f"the prior $500K snapshot must remain historically recoverable, got: {cash_values}")
            expect(45_000_000 in cash_values, f"the new $450K snapshot must also be present, got: {cash_values}")
            expect(len(history["snapshots"]) == 2, "updating financial state must never overwrite the prior row -- both must exist")
    finally:
        _cleanup()


# --- Case N: fundraising regression (documented, not a backend test) ----------
#
# The existing SAFE/priced-round/cap-table/runway engine
# (dashboard/lib/fundraising/*.ts) is 100% client-side TypeScript with no
# backend counterpart -- there is nothing for THIS file to test. Its own
# regression coverage is dashboard/tests/{fundraising,fundraisingUi}.test.ts,
# run unchanged as part of `npm test` (verified in this phase's own final
# report). This backend test file changes zero fundraising-related code,
# confirmed by this phase's own diff touching only new files plus
# app/api.py/app/database/db.py additions.


TESTS = [
    test_signed_out_cannot_access_financials_endpoints,
    test_case_a_empty_state_has_no_fake_zero_metrics,
    test_case_b_basic_burn_and_runway,
    test_case_c_expense_categories_sum_correctly,
    test_case_d_cash_flow_positive_shows_no_finite_runway,
    test_case_e_break_even,
    test_case_f_zero_cash_with_positive_burn_is_out_of_cash,
    test_case_g_explicit_zero_revenue_is_known_not_unknown,
    test_case_h_unknown_revenue_never_silently_becomes_zero,
    test_case_i_monthly_projection_deterministic_depletion,
    test_case_j_profitable_projection_never_terminates_early,
    test_case_k_ownership_security,
    test_case_l_reload_survives,
    test_case_m_updating_the_snapshot_preserves_prior_history,
]


def main() -> None:
    print("\nPhase 35B -- Financial State Persistence + Runway Engine V1 tests")
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
