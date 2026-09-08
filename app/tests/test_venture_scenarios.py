"""
Regression tests for Phase 35D -- Operating Scenarios + Financial Plan
Reconciliation V1: the venture_financial_plans / venture_financial_scenarios
tables (app/database/db.py), their Pydantic contracts
(app/models/venture_financial_plans.py), the extended calculation engine
(app/ai/financial_engine.py -- revenue_target/expense_delta plan items),
and the new /ventures/{id}/financial-plans[/preview|/{id}],
/ventures/{id}/scenarios[/{id}], /ventures/{id}/financials/reconcile
endpoints in app/api.py.

Same JWT-mocking harness and zztest_* user-id convention as
test_venture_hire_plans.py -- no live Clerk dependency, every row
cleaned up in a finally block even on failure.

Run with:
    python -m app.tests.test_venture_scenarios
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_scenario_user_a"
USER_B = "zztest_scenario_user_b"

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
            connection.execute(text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"), {"id": user_id})


def _cleanup() -> None:
    with engine.begin() as connection:
        for table in ("venture_financial_scenarios", "venture_financial_plans", "venture_hire_plans", "venture_financial_snapshots"):
            connection.execute(
                text(f"DELETE FROM {table} WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
                {"ids": [USER_A, USER_B]},
            )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture_body(name: str) -> dict:
    return {
        "name": name, "description": "Test venture for Operating Scenarios.", "industry": None,
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
        "as_of_date": "2026-09-01",
        "cash_balance_cents": 50_000_000,  # $500K
        "monthly_recurring_revenue_cents": 2_000_000,  # $20K
        "monthly_non_recurring_revenue_cents": 0,
        "payroll_cents": 0, "contractors_cents": 2_000_000, "software_cents": 0, "marketing_cents": 1_000_000,
        "rent_cents": 0, "professional_services_cents": 0, "other_expenses_cents": 4_000_000,  # total $70K
    }
    body.update(overrides)
    return body


def _post_snapshot(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/financials", json=_snapshot_body(**overrides), headers=_auth_headers(user_id))


def _get_financials(venture_id: int, user_id: str):
    return client.get(f"/ventures/{venture_id}/financials", headers=_auth_headers(user_id))


def _create_financial_plan(venture_id: int, user_id: str, **overrides):
    body = {
        "plan_type": "expense_change", "label": "Test plan", "category": "marketing",
        "amount_cents": 1_500_000, "start_date": "2026-11-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/financial-plans", json=body, headers=_auth_headers(user_id))


def _patch_financial_plan(venture_id: int, user_id: str, plan_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/financial-plans/{plan_id}", json=fields, headers=_auth_headers(user_id))


def _preview_financial_plan(venture_id: int, user_id: str, exclude_id: int | None = None, **overrides):
    query = f"?exclude_plan_id={exclude_id}" if exclude_id is not None else ""
    body = {"plan_type": "expense_change", "label": "Preview", "category": "marketing", "amount_cents": 1_500_000, "start_date": "2026-11-01", "end_date": None}
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/financial-plans/preview{query}", json=body, headers=_auth_headers(user_id))


def _create_hire(venture_id: int, user_id: str, **overrides):
    body = {
        "role": "Senior Engineer", "employment_type": "employee", "annual_salary_cents": 22_500_000,
        "burden_percent": 0.0, "monthly_cost_cents": None, "one_time_cost_cents": None,
        "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/hire-plans", json=body, headers=_auth_headers(user_id))


def _create_scenario(venture_id: int, user_id: str, name: str, hire_ids=None, financial_ids=None):
    return client.post(
        f"/ventures/{venture_id}/scenarios",
        json={"name": name, "hire_plan_ids": hire_ids or [], "financial_plan_ids": financial_ids or []},
        headers=_auth_headers(user_id),
    )


# --- Authorization -----------------------------------------------------------


def test_signed_out_cannot_access_scenario_endpoints() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/financial-plans").status_code == 401, "GET financial-plans must require auth")
        expect(client.post("/ventures/1/financial-plans", json={}).status_code == 401, "POST financial-plans must require auth")
        expect(client.get("/ventures/1/scenarios").status_code == 401, "GET scenarios must require auth")
        expect(client.post("/ventures/1/financials/reconcile", json={}).status_code == 401, "POST reconcile must require auth")


# --- Revenue plan (Cases A-C) --------------------------------------------


def test_case_a_revenue_target_applies_from_its_own_start_month() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario A")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="MRR downside", category=None,
                amount_cents=1_000_000, start_date="2026-12-01",
            )
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            month1, month2, month3 = projection[0], projection[1], projection[2]
            expect(month1["revenue_cents"] == 2_000_000, f"month 1 (Oct) must use base $20K revenue, got: {month1}")
            expect(month2["revenue_cents"] == 2_000_000, f"month 2 (Nov) must still use base revenue, got: {month2}")
            expect(month3["revenue_cents"] == 1_000_000, f"month 3 (Dec, the plan's own start month) must use the $10K target, got: {month3}")
            expect(month3["plan_revenue_active"] is True, month3)
    finally:
        _cleanup()


def test_case_b_revenue_target_upside_improves_cash_trajectory() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario B")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            baseline = _get_financials(venture["id"], USER_A).json()["projection"]
            _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Growth", category=None,
                amount_cents=4_000_000, start_date="2026-10-01",
            )
            with_plan = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(with_plan[0]["ending_cash_cents"] > baseline[0]["ending_cash_cents"], "a revenue upside must deterministically improve the cash trajectory")
    finally:
        _cleanup()


def test_case_c_revenue_target_end_date_resumes_base_revenue() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario C")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Temp downside", category=None,
                amount_cents=1_000_000, start_date="2026-10-01", end_date="2026-11-01",
            )
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(projection[0]["revenue_cents"] == 1_000_000, projection[0])
            expect(projection[1]["revenue_cents"] == 1_000_000, projection[1])
            expect(projection[2]["revenue_cents"] == 2_000_000, f"revenue must resume to base after the plan's own end_date, got: {projection[2]}")
    finally:
        _cleanup()


# --- Expense plan (Cases D-F) ---------------------------------------------


def test_case_d_expense_cut_applies_from_its_own_start_month() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario D")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")  # contractors = $20K
            _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Cut contractors", category="contractors",
                amount_cents=-1_000_000, start_date="2026-10-01",
            )
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(projection[0]["expenses_cents"] == 6_000_000, f"expected $60K total expenses after a $10K contractor cut, got: {projection[0]}")
    finally:
        _cleanup()


def test_case_e_expense_increase() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario E")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")  # marketing = $10K
            _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Increase marketing", category="marketing",
                amount_cents=1_500_000, start_date="2026-10-01",
            )
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(projection[0]["expenses_cents"] == 8_500_000, f"expected $85K total expenses after a $15K marketing increase, got: {projection[0]}")
    finally:
        _cleanup()


def test_case_f_impossible_expense_cut_is_rejected() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario F")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")  # contractors = $20K
            response = _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Impossible cut", category="contractors",
                amount_cents=-3_000_000, start_date="2026-10-01",  # -$30K against a $20K category
            )
            expect(response.status_code == 422, f"a cut larger than the current category value must be rejected, got: {response.status_code} {response.text}")
    finally:
        _cleanup()


# --- Phase 35D-A stress-test hardening: combined-category floor (Case L/K),
# revenue-target overlap prevention (Case M) --------------------------------


def test_case_35da_l_combined_same_category_cuts_are_rejected_once_they_exceed_the_category() -> None:
    """Two INDIVIDUALLY-safe cuts on the same category can still combine
    into an impossible one. contractors = $20K: a first -$10K cut is
    safe alone; a second -$15K cut would ALSO be safe alone (against the
    unchanged $20K snapshot value), but the two COMBINED (-$25K) would
    take contractors to -$5K. The second plan must be rejected."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario 35DA-L")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")  # contractors = $20K
            first = _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="First cut", category="contractors",
                amount_cents=-1_000_000, start_date="2026-10-01",
            )
            expect(first.status_code == 200, f"the first, individually-safe cut must be accepted, got: {first.status_code} {first.text}")

            second = _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Second cut", category="contractors",
                amount_cents=-1_500_000, start_date="2026-11-01",
            )
            expect(
                second.status_code == 422,
                f"a second cut that is only safe in isolation, but combines with the first to exceed the category, must be rejected, got: {second.status_code} {second.text}",
            )

            # A cut on a DIFFERENT category is unaffected by the first one.
            other_category = _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Marketing cut", category="marketing",
                amount_cents=-500_000, start_date="2026-11-01",
            )
            expect(other_category.status_code == 200, f"a cut on an unrelated category must not be blocked by another category's plans, got: {other_category.status_code} {other_category.text}")
    finally:
        _cleanup()


def test_case_35da_m_overlapping_revenue_targets_are_rejected_not_silently_resolved() -> None:
    """Case M: two revenue_target plans active over the same period is
    not a supported composition. Rather than let the engine's own
    highest-id tiebreak resolve it silently, creation is rejected
    outright -- the safer V1 behavior."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario 35DA-M")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            first = _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Plan A", category=None,
                amount_cents=4_000_000, start_date="2026-10-01", end_date="2026-12-01",
            )
            expect(first.status_code == 200, f"the first revenue plan must be accepted, got: {first.status_code} {first.text}")

            overlapping = _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Plan B", category=None,
                amount_cents=1_000_000, start_date="2026-11-01", end_date=None,
            )
            expect(
                overlapping.status_code == 422,
                f"a second revenue_target plan whose active range overlaps the first must be rejected, got: {overlapping.status_code} {overlapping.text}",
            )

            non_overlapping = _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Plan C", category=None,
                amount_cents=1_000_000, start_date="2027-01-01", end_date=None,
            )
            expect(
                non_overlapping.status_code == 200,
                f"a revenue_target plan starting strictly after the first one ends must be accepted, got: {non_overlapping.status_code} {non_overlapping.text}",
            )
    finally:
        _cleanup()


# --- Composition (Cases G-H) -----------------------------------------------


def test_case_g_hire_marketing_revenue_compose_in_correct_months() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario G")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_hire(venture["id"], USER_A, start_date="2026-10-01")  # month 1: +$18,750
            _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Marketing", category="marketing", amount_cents=1_500_000, start_date="2026-11-01")  # month 2
            _create_financial_plan(venture["id"], USER_A, plan_type="revenue_target", label="Growth", category=None, amount_cents=4_000_000, start_date="2026-12-01")  # month 3

            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            m1, m2, m3 = projection[0], projection[1], projection[2]
            expect(m1["expenses_cents"] == 8_875_000, m1)  # base 70K + hire 18,750
            expect(m2["expenses_cents"] == 10_375_000, m2)  # + marketing 15K
            expect(m3["revenue_cents"] == 4_000_000, m3)  # revenue target active
            expect(m3["expenses_cents"] == 10_375_000, m3)
    finally:
        _cleanup()


def test_case_h_plan_order_does_not_affect_the_projection() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario H")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            mkt = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Marketing", category="marketing", amount_cents=1_500_000, start_date="2026-11-01").json()

            # Two independent reads of the SAME plans -- the API itself
            # has no "order" concept (plans are always read from the DB
            # in a fixed order), so this proves the underlying engine
            # call is order-independent directly (mirrors the pure-
            # function proof in app/ai/financial_engine.py's own manual
            # verification during this phase's implementation).
            from app.ai.financial_engine import project_monthly_cash_flow, hire_to_plan_item, expense_plan_to_plan_item
            snapshot = _get_financials(venture["id"], USER_A).json()["latest_snapshot"]
            snapshot["as_of_date"] = __import__("datetime").date.fromisoformat(snapshot["as_of_date"])
            hire["start_date"] = __import__("datetime").date.fromisoformat(hire["start_date"])
            mkt["start_date"] = __import__("datetime").date.fromisoformat(mkt["start_date"])
            hire_item = hire_to_plan_item(hire)
            mkt_item = expense_plan_to_plan_item(mkt)
            proj_1 = project_monthly_cash_flow(snapshot, snapshot["as_of_date"], plan_items=[hire_item, mkt_item])
            proj_2 = project_monthly_cash_flow(snapshot, snapshot["as_of_date"], plan_items=[mkt_item, hire_item])
            expect(proj_1 == proj_2, "supplying the same plans in a different order must produce an identical projection")
    finally:
        _cleanup()


# --- Scenarios (Cases I-M) --------------------------------------------------


def test_case_i_scenarios_produce_different_deterministic_projections() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario I")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            cut = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Cut contractors", category="contractors", amount_cents=-1_000_000, start_date="2026-10-01").json()

            scenario_a = _create_scenario(venture["id"], USER_A, "Growth Plan", hire_ids=[hire["id"]]).json()
            scenario_b = _create_scenario(venture["id"], USER_A, "Conservative Plan", financial_ids=[cut["id"]]).json()

            expect(scenario_a["projection"][0]["expenses_cents"] != scenario_b["projection"][0]["expenses_cents"], "different plan selections must produce different projections")
            expect(len(scenario_a["assumptions"]) == 1 and len(scenario_b["assumptions"]) == 1, "each scenario must state its own assumption")
    finally:
        _cleanup()


def test_case_j_scenario_persists_through_reload() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario J")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            created = _create_scenario(venture["id"], USER_A, "Growth Plan", hire_ids=[hire["id"]]).json()

            reloaded = client.get(f"/ventures/{venture['id']}/scenarios", headers=_auth_headers(USER_A)).json()
            expect(len(reloaded) == 1 and reloaded[0]["id"] == created["id"], "the scenario must survive reload")
            expect(reloaded[0]["name"] == "Growth Plan", reloaded[0])
    finally:
        _cleanup()


def test_case_k_scenario_cannot_reference_another_users_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Scenario K Owner")
            hire_a = _create_hire(venture_a["id"], USER_A).json()

            venture_b = _create_venture(USER_B, "ZZTest Scenario K Other")
            response = _create_scenario(venture_b["id"], USER_B, "Sneaky", hire_ids=[hire_a["id"]])
            expect(response.status_code == 404, f"a scenario must not be able to reference another user's plan, got: {response.status_code}")
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM venture_hire_plans WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"), {"ids": [USER_A, USER_B]})
            connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        _cleanup()


def test_case_l_cancelled_plan_referenced_by_a_scenario_is_honestly_excluded() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario L")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            scenario = _create_scenario(venture["id"], USER_A, "Growth Plan", hire_ids=[hire["id"]]).json()
            expect(scenario["projection"][0]["plan_expense_impact_cents"] > 0, "sanity: the hire is active before cancelling")

            client.patch(f"/ventures/{venture['id']}/hire-plans/{hire['id']}", json={"status": "cancelled"}, headers=_auth_headers(USER_A))

            reloaded = client.get(f"/ventures/{venture['id']}/scenarios", headers=_auth_headers(USER_A)).json()[0]
            expect(reloaded["projection"][0]["plan_expense_impact_cents"] == 0, "a cancelled plan must be silently excluded, never a stale/error result")
            expect(hire["id"] in reloaded["hire_plan_ids"], "the scenario's own membership list is unchanged -- only the LIVE computation excludes the cancelled plan")
    finally:
        _cleanup()


def test_case_m_current_trajectory_never_includes_optional_plans() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario M")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_hire(venture["id"], USER_A, start_date="2026-10-01")
            financials = _get_financials(venture["id"], USER_A).json()
            expect(financials["projection"][0]["expenses_cents"] == 7_000_000, "the plain 'projection' (current trajectory) must never include a planned hire")
    finally:
        _cleanup()


# --- Reconciliation (Cases N-T) ---------------------------------------------


def test_case_n_active_hire_surfaces_for_reconciliation() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario N")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            # A LATER snapshot, dated on/after the hire's own start_date.
            after = _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15").json()
            pending_ids = [item["plan_id"] for item in after["pending_reconciliation"] if item["plan_kind"] == "hire"]
            expect(hire["id"] in pending_ids, f"the hire must surface for reconciliation once its start_date has passed, got: {after['pending_reconciliation']}")
    finally:
        _cleanup()


def test_case_o_reconciling_as_included_actualizes_and_stops_double_counting() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario O")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15", payroll_cents=1_875_000)  # payroll now includes the hire

            response = client.post(
                f"/ventures/{venture['id']}/financials/reconcile",
                json={"plan_kind": "hire", "plan_id": hire["id"], "included": True},
                headers=_auth_headers(USER_A),
            )
            expect(response.status_code == 200, response.text)
            body = response.json()
            stripped = [
                {k: v for k, v in m.items() if k not in ("plan_expense_impact_cents", "plan_revenue_active", "active_plan_item_ids")}
                for m in body["projection_with_plan"]
            ]
            expect(stripped == body["projection"], "once reconciled as included, the plan must stop affecting the projection")
            expect(body["pending_reconciliation"] == [], "resolving the only pending item must clear it")

            updated_hire = next(h for h in body["hire_plans"] if h["id"] == hire["id"])
            expect(updated_hire["status"] == "actualized", updated_hire)
    finally:
        _cleanup()


def test_case_p_reconciling_as_not_included_leaves_plan_active() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario P")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            response = client.post(
                f"/ventures/{venture['id']}/financials/reconcile",
                json={"plan_kind": "hire", "plan_id": hire["id"], "included": False},
                headers=_auth_headers(USER_A),
            )
            body = response.json()
            expect(body["pending_reconciliation"] == [], "answering 'not included' must still clear the pending question for THIS snapshot")
            updated_hire = next(h for h in body["hire_plans"] if h["id"] == hire["id"])
            expect(updated_hire["status"] == "planned", "declining must leave the plan active/planned")
            expect(body["projection_with_plan"][0]["plan_expense_impact_cents"] > 0, "a plan the founder said is NOT yet included must keep affecting the projection")
    finally:
        _cleanup()


def test_case_q_reconciliation_flow_for_expense_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario Q")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Cut contractors", category="contractors", amount_cents=-1_000_000, start_date="2026-10-01").json()
            after = _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15").json()
            pending_ids = [item["plan_id"] for item in after["pending_reconciliation"] if item["plan_kind"] == "financial"]
            expect(plan["id"] in pending_ids, "an expense plan must surface for reconciliation the same way a hire does")

            client.post(f"/ventures/{venture['id']}/financials/reconcile", json={"plan_kind": "financial", "plan_id": plan["id"], "included": True}, headers=_auth_headers(USER_A))
            updated = client.get(f"/ventures/{venture['id']}/financial-plans", headers=_auth_headers(USER_A)).json()
            expect(next(p for p in updated if p["id"] == plan["id"])["status"] == "actualized", updated)
    finally:
        _cleanup()


def test_case_r_reconciliation_flow_for_revenue_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario R")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(venture["id"], USER_A, plan_type="revenue_target", label="Growth", category=None, amount_cents=4_000_000, start_date="2026-10-01").json()
            after = _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15", monthly_recurring_revenue_cents=4_000_000).json()
            pending_ids = [item["plan_id"] for item in after["pending_reconciliation"] if item["plan_kind"] == "financial"]
            expect(plan["id"] in pending_ids, "a revenue plan must surface for reconciliation the same way an expense plan does")
    finally:
        _cleanup()


def test_case_s_unresolved_reconciliation_survives_reload() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario S")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")

            first_read = _get_financials(venture["id"], USER_A).json()
            second_read = _get_financials(venture["id"], USER_A).json()
            expect(len(first_read["pending_reconciliation"]) == 1, first_read["pending_reconciliation"])
            expect(first_read["pending_reconciliation"] == second_read["pending_reconciliation"], "an unresolved reconciliation question must survive reload unchanged")
            expect(first_read["pending_reconciliation"][0]["plan_id"] == hire["id"], first_read["pending_reconciliation"])
    finally:
        _cleanup()


def test_case_t_no_active_plans_means_no_reconciliation_noise() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario T")
            first = _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01").json()
            expect(first["pending_reconciliation"] == [], "a venture with no plans must never show reconciliation noise")
    finally:
        _cleanup()


# --- Security / regression (Cases U-Z) --------------------------------------


def test_case_u_ownership_security_across_new_endpoints() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario U")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(venture["id"], USER_A).json()
            scenario = _create_scenario(venture["id"], USER_A, "Mine", financial_ids=[plan["id"]]).json()

            expect(client.get(f"/ventures/{venture['id']}/financial-plans", headers=_auth_headers(USER_B)).status_code == 404, "User B must not list User A's financial plans")
            expect(_patch_financial_plan(venture["id"], USER_B, plan["id"], status="cancelled").status_code == 404, "User B must not edit User A's financial plan")
            expect(client.get(f"/ventures/{venture['id']}/scenarios", headers=_auth_headers(USER_B)).status_code == 404, "User B must not list User A's scenarios")
            expect(client.patch(f"/ventures/{venture['id']}/scenarios/{scenario['id']}", json={"name": "Hijacked"}, headers=_auth_headers(USER_B)).status_code == 404, "User B must not edit User A's scenario")
            expect(client.delete(f"/ventures/{venture['id']}/scenarios/{scenario['id']}", headers=_auth_headers(USER_B)).status_code == 404, "User B must not delete User A's scenario")
            expect(
                client.post(f"/ventures/{venture['id']}/financials/reconcile", json={"plan_kind": "financial", "plan_id": plan["id"], "included": True}, headers=_auth_headers(USER_B)).status_code == 404,
                "User B must not reconcile User A's plan",
            )
    finally:
        _cleanup()


def test_case_y_no_scenario_can_mutate_canonical_actual_state() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Scenario Y")
            before = _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01").json()["latest_snapshot"]
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _create_scenario(venture["id"], USER_A, "Growth", hire_ids=[hire["id"]])

            after = _get_financials(venture["id"], USER_A).json()["latest_snapshot"]
            expect(before == after, "creating and reading a scenario must never change the canonical actual snapshot")
    finally:
        _cleanup()


TESTS = [
    test_signed_out_cannot_access_scenario_endpoints,
    test_case_a_revenue_target_applies_from_its_own_start_month,
    test_case_b_revenue_target_upside_improves_cash_trajectory,
    test_case_c_revenue_target_end_date_resumes_base_revenue,
    test_case_d_expense_cut_applies_from_its_own_start_month,
    test_case_e_expense_increase,
    test_case_f_impossible_expense_cut_is_rejected,
    test_case_35da_l_combined_same_category_cuts_are_rejected_once_they_exceed_the_category,
    test_case_35da_m_overlapping_revenue_targets_are_rejected_not_silently_resolved,
    test_case_g_hire_marketing_revenue_compose_in_correct_months,
    test_case_h_plan_order_does_not_affect_the_projection,
    test_case_i_scenarios_produce_different_deterministic_projections,
    test_case_j_scenario_persists_through_reload,
    test_case_k_scenario_cannot_reference_another_users_plan,
    test_case_l_cancelled_plan_referenced_by_a_scenario_is_honestly_excluded,
    test_case_m_current_trajectory_never_includes_optional_plans,
    test_case_n_active_hire_surfaces_for_reconciliation,
    test_case_o_reconciling_as_included_actualizes_and_stops_double_counting,
    test_case_p_reconciling_as_not_included_leaves_plan_active,
    test_case_q_reconciliation_flow_for_expense_plan,
    test_case_r_reconciliation_flow_for_revenue_plan,
    test_case_s_unresolved_reconciliation_survives_reload,
    test_case_t_no_active_plans_means_no_reconciliation_noise,
    test_case_u_ownership_security_across_new_endpoints,
    test_case_y_no_scenario_can_mutate_canonical_actual_state,
]


def main() -> None:
    print("\nPhase 35D -- Operating Scenarios + Financial Plan Reconciliation V1 tests")
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
