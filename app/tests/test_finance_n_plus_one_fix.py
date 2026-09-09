"""
Regression tests for Phase 40A-FIX P1 #1 -- the N+1 query fix in Finance
scenario/commitment building. See docs/product/... final report for the
full audit. Proves two things, structurally, not just "the old tests
still pass":

  1. The new batched db.py functions (list_venture_hire_plans_for_owner_by_ids/
     list_venture_financial_plans_for_owner_by_ids) are functionally
     correct: same rows, same ownership scoping, same status filtering,
     same empty-list short-circuit as the per-id functions they replace.
  2. Building a scenario or creating a commitment that references MANY
     plan ids now calls the batched function EXACTLY ONCE per id-list,
     never once per id -- a direct, structural proof of the fix, not an
     inference from "it's still fast."

Run with:
    python -m app.tests.test_finance_n_plus_one_fix
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import (
    engine,
    list_venture_hire_plans_for_owner_by_ids,
    list_venture_financial_plans_for_owner_by_ids,
)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


USER_A = "zztest_nplus1_user_a"
USER_B = "zztest_nplus1_user_b"

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
            "venture_financial_commitments", "venture_financial_scenarios",
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
        "name": name, "description": "Test venture for N+1 fix.", "industry": None,
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


def _post_snapshot(venture_id: int, user_id: str, **overrides):
    body = {
        "as_of_date": "2026-09-01", "cash_balance_cents": 50_000_000, "monthly_recurring_revenue_cents": 2_000_000,
        "monthly_non_recurring_revenue_cents": 0, "payroll_cents": 0, "contractors_cents": 2_000_000,
        "software_cents": 0, "marketing_cents": 1_000_000, "rent_cents": 0, "professional_services_cents": 0,
        "other_expenses_cents": 4_000_000,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/financials", json=body, headers=_auth_headers(user_id))


def _create_hire(venture_id: int, user_id: str, **overrides):
    body = {
        "role": "Engineer", "employment_type": "employee", "annual_salary_cents": 12_000_000,
        "burden_percent": 0.2, "monthly_cost_cents": None, "one_time_cost_cents": None,
        "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/hire-plans", json=body, headers=_auth_headers(user_id))


def _create_financial_plan(venture_id: int, user_id: str, **overrides):
    body = {
        "plan_type": "expense_change", "label": "Test plan", "category": "marketing",
        "amount_cents": 100_000, "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/financial-plans", json=body, headers=_auth_headers(user_id))


def _create_scenario(venture_id: int, user_id: str, name: str, hire_ids=None, financial_ids=None):
    return client.post(
        f"/ventures/{venture_id}/scenarios",
        json={"name": name, "hire_plan_ids": hire_ids or [], "financial_plan_ids": financial_ids or []},
        headers=_auth_headers(user_id),
    )


# --- Layer 1: batched function correctness -----------------------------------


def test_batched_hire_lookup_matches_ownership_and_status() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest NPlus1 Correctness")
            h1 = _create_hire(venture["id"], USER_A, role="A").json()
            h2 = _create_hire(venture["id"], USER_A, role="B").json()
            h3 = _create_hire(venture["id"], USER_A, role="C").json()
            client.patch(f"/ventures/{venture['id']}/hire-plans/{h3['id']}", json={"status": "cancelled"}, headers=_auth_headers(USER_A))

            all_status = list_venture_hire_plans_for_owner_by_ids(USER_A, venture["id"], [h1["id"], h2["id"], h3["id"]])
            expect({r["id"] for r in all_status} == {h1["id"], h2["id"], h3["id"]}, "unfiltered batched lookup must return every referenced, owned id regardless of status")

            planned_only = list_venture_hire_plans_for_owner_by_ids(USER_A, venture["id"], [h1["id"], h2["id"], h3["id"]], status="planned")
            expect({r["id"] for r in planned_only} == {h1["id"], h2["id"]}, "status-filtered batched lookup must exclude the cancelled hire")
    finally:
        _cleanup()


def test_batched_hire_lookup_never_returns_another_users_row() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest NPlus1 Owner")
            hire_a = _create_hire(venture_a["id"], USER_A).json()
            venture_b = _create_venture(USER_B, "ZZTest NPlus1 Other")

            result = list_venture_hire_plans_for_owner_by_ids(USER_B, venture_b["id"], [hire_a["id"]])
            expect(result == [], "a batched lookup scoped to User B/venture B must never return User A's hire plan")
    finally:
        _cleanup()


def test_batched_financial_plan_lookup_empty_list_short_circuits() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest NPlus1 Empty")
            result = list_venture_financial_plans_for_owner_by_ids(USER_A, venture["id"], [])
            expect(result == [], "an empty id list must return [] without querying")
    finally:
        _cleanup()


# --- Layer 2: structural call-count proof ------------------------------------


def test_scenario_building_calls_batched_lookup_once_not_per_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest NPlus1 ScenarioCallCount")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire_ids = [_create_hire(venture["id"], USER_A, role=f"Hire {i}", start_date="2026-10-01").json()["id"] for i in range(5)]
            plan_ids = [_create_financial_plan(venture["id"], USER_A, label=f"Plan {i}", start_date="2026-10-01").json()["id"] for i in range(5)]

            call_counts = {"hire": 0, "financial": 0}
            original_hire = api.list_venture_hire_plans_for_owner_by_ids
            original_financial = api.list_venture_financial_plans_for_owner_by_ids

            def counting_hire(*args, **kwargs):
                call_counts["hire"] += 1
                return original_hire(*args, **kwargs)

            def counting_financial(*args, **kwargs):
                call_counts["financial"] += 1
                return original_financial(*args, **kwargs)

            api.list_venture_hire_plans_for_owner_by_ids = counting_hire
            api.list_venture_financial_plans_for_owner_by_ids = counting_financial
            try:
                scenario = _create_scenario(venture["id"], USER_A, "Big Plan", hire_ids=hire_ids, financial_ids=plan_ids)
                expect(scenario.status_code == 200, scenario.text)
                body = scenario.json()
                expect(len(body["assumptions"]) == 10, f"all 5 hires + 5 financial plans must be represented, got: {body['assumptions']}")
            finally:
                api.list_venture_hire_plans_for_owner_by_ids = original_hire
                api.list_venture_financial_plans_for_owner_by_ids = original_financial

            # create_scenario() itself calls the batched hire lookup ONCE for
            # its own ownership check, then _build_scenario_response() calls
            # it ONCE more to build the response -- 2 calls total for 5
            # referenced hires, never 5. Same for financial plans.
            expect(call_counts["hire"] == 2, f"expected exactly 2 batched hire calls (1 validation + 1 response-build) for 5 referenced hires, got {call_counts['hire']}")
            expect(call_counts["financial"] == 2, f"expected exactly 2 batched financial-plan calls for 5 referenced plans, got {call_counts['financial']}")
    finally:
        _cleanup()


def test_commitment_creation_calls_batched_lookup_once_not_per_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest NPlus1 CommitmentCallCount")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            # A single-item commitment is the normal case, but the fix must
            # scale the SAME way (one call) even with several referenced
            # financial plans bundled into one commitment.
            plan_ids = [_create_financial_plan(venture["id"], USER_A, label=f"Plan {i}", category="marketing", amount_cents=10_000 + i, start_date="2026-10-01").json()["id"] for i in range(4)]

            call_counts = {"financial": 0}
            original_financial = api.list_venture_financial_plans_for_owner_by_ids

            def counting_financial(*args, **kwargs):
                call_counts["financial"] += 1
                return original_financial(*args, **kwargs)

            api.list_venture_financial_plans_for_owner_by_ids = counting_financial
            try:
                response = client.post(
                    f"/ventures/{venture['id']}/financial-commitments",
                    json={"financial_plan_ids": plan_ids},
                    headers=_auth_headers(USER_A),
                )
                expect(response.status_code == 200, response.text)
                expect(len(response.json()["plan_snapshot"]) == 4, "all 4 referenced financial plans must be frozen")
            finally:
                api.list_venture_financial_plans_for_owner_by_ids = original_financial

            expect(call_counts["financial"] == 1, f"expected exactly 1 batched financial-plan call for 4 referenced plans, got {call_counts['financial']}")
    finally:
        _cleanup()


TESTS = [
    test_batched_hire_lookup_matches_ownership_and_status,
    test_batched_hire_lookup_never_returns_another_users_row,
    test_batched_financial_plan_lookup_empty_list_short_circuits,
    test_scenario_building_calls_batched_lookup_once_not_per_plan,
    test_commitment_creation_calls_batched_lookup_once_not_per_plan,
]


def main() -> None:
    print("\nPhase 40A-FIX -- Finance N+1 Query Fix tests")
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
