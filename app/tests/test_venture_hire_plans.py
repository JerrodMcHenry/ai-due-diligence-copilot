"""
Regression tests for Phase 35C -- Hiring + Operating Plan Engine V1: the
venture_hire_plans table (app/database/db.py), its Pydantic contracts
(app/models/venture_hire_plans.py), the extended calculation engine
(app/ai/financial_engine.py), and the new
/ventures/{id}/hire-plans[/preview|/{id}] endpoints in app/api.py.

Same JWT-mocking harness and zztest_* user-id convention as
test_venture_financials.py -- no live Clerk dependency, every row
cleaned up in a finally block even on failure.

Run with:
    python -m app.tests.test_venture_hire_plans
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_hireplan_user_a"
USER_B = "zztest_hireplan_user_b"

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
        for table in ("venture_hire_plans", "venture_financial_snapshots"):
            connection.execute(
                text(f"DELETE FROM {table} WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
                {"ids": [USER_A, USER_B]},
            )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture_body(name: str) -> dict:
    return {
        "name": name,
        "description": "Test venture for the Hiring + Operating Plan Engine.",
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
        "as_of_date": "2026-09-01",
        "cash_balance_cents": None, "monthly_recurring_revenue_cents": None, "monthly_non_recurring_revenue_cents": None,
        "payroll_cents": None, "contractors_cents": None, "software_cents": None, "marketing_cents": None,
        "rent_cents": None, "professional_services_cents": None, "other_expenses_cents": None,
    }
    body.update(overrides)
    return body


def _post_snapshot(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/financials", json=_snapshot_body(**overrides), headers=_auth_headers(user_id))


def _base_snapshot(venture_id: int, user_id: str, **overrides):
    """$500K cash / $20K MRR / $70K expenses (all in `other_expenses_cents`
    for simplicity) -- the exact Phase 35C directive worked example,
    unless overridden."""
    defaults = dict(
        cash_balance_cents=50_000_000,
        monthly_recurring_revenue_cents=2_000_000, monthly_non_recurring_revenue_cents=0,
        payroll_cents=0, contractors_cents=0, software_cents=0, marketing_cents=0,
        rent_cents=0, professional_services_cents=0, other_expenses_cents=7_000_000,
    )
    defaults.update(overrides)
    return _post_snapshot(venture_id, user_id, **defaults)


def _get_financials(venture_id: int, user_id: str):
    return client.get(f"/ventures/{venture_id}/financials", headers=_auth_headers(user_id))


def _employee_body(**overrides) -> dict:
    body = {
        "role": "Senior Engineer",
        "employment_type": "employee",
        "annual_salary_cents": 18_000_000,  # $180,000
        "burden_percent": 25.0,
        "monthly_cost_cents": None,
        "one_time_cost_cents": None,
        "start_date": "2026-12-01",
        "end_date": None,
    }
    body.update(overrides)
    return body


def _create_hire(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/hire-plans", json=_employee_body(**overrides), headers=_auth_headers(user_id))


def _patch_hire(venture_id: int, user_id: str, hire_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/hire-plans/{hire_id}", json=fields, headers=_auth_headers(user_id))


def _preview_hire(venture_id: int, user_id: str, exclude_id: int | None = None, **overrides):
    query = f"?exclude_hire_plan_id={exclude_id}" if exclude_id is not None else ""
    return client.post(f"/ventures/{venture_id}/hire-plans/preview{query}", json=_employee_body(**overrides), headers=_auth_headers(user_id))


# --- Authorization -----------------------------------------------------------


def test_signed_out_cannot_access_hire_plan_endpoints() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/hire-plans").status_code == 401, "GET hire-plans must require auth")
        expect(client.post("/ventures/1/hire-plans", json={}).status_code == 401, "POST hire-plans must require auth")
        expect(client.patch("/ventures/1/hire-plans/1", json={}).status_code == 401, "PATCH hire-plans must require auth")
        expect(client.post("/ventures/1/hire-plans/preview", json={}).status_code == 401, "POST preview must require auth")


# --- Case A / B: employee cost model ------------------------------------------


def test_case_a_basic_employee_cost() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire A")
            response = _create_hire(venture["id"], USER_A)
            expect(response.status_code == 200, response.text)
            body = response.json()
            expect(body["computed_annual_cost_cents"] == 22_500_000, f"expected $225,000/year, got: {body}")
            expect(body["computed_monthly_cost_cents"] == 1_875_000, f"expected $18,750/month, got: {body}")
    finally:
        _cleanup()


def test_case_b_zero_burden() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire B")
            response = _create_hire(venture["id"], USER_A, burden_percent=0.0)
            body = response.json()
            expect(body["computed_monthly_cost_cents"] == 1_500_000, f"expected $15,000/month with zero burden, got: {body}")
    finally:
        _cleanup()


# --- Case C: contractor, active only during its own window -------------------


def test_case_c_contractor_active_window() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire C")
            _base_snapshot(venture["id"], USER_A, as_of_date="2025-12-01")
            _create_hire(
                venture["id"], USER_A,
                role="Design Contractor", employment_type="contractor",
                annual_salary_cents=None, burden_percent=None, monthly_cost_cents=1_200_000,
                start_date="2026-01-01", end_date="2026-06-30",
            )
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            january = next(m for m in projection if m["date"] == "2026-01-01")
            july = next(m for m in projection if m["date"] == "2026-07-01")
            expect(january["plan_expense_impact_cents"] == 1_200_000, f"contractor must be active in January, got: {january}")
            expect(july["plan_expense_impact_cents"] == 0, f"contractor must NOT be active in July (after its end date), got: {july}")
    finally:
        _cleanup()


# --- Case D: future start date ------------------------------------------------


def test_case_d_future_start_date_has_no_early_cost() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire D")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_hire(venture["id"], USER_A, start_date="2026-12-01")  # 3 months out
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            month1, month2, month3 = projection[0], projection[1], projection[2]
            expect(month1["plan_expense_impact_cents"] == 0, f"month 1 (Oct) must have no hire cost yet, got: {month1}")
            expect(month2["plan_expense_impact_cents"] == 0, f"month 2 (Nov) must have no hire cost yet, got: {month2}")
            expect(month3["plan_expense_impact_cents"] == 1_875_000, f"month 3 (Dec, the start month) must include the hire, got: {month3}")
    finally:
        _cleanup()


# --- Case E: one-time cost, single month only ---------------------------------


def test_case_e_one_time_cost_hits_one_month_only() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire E")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            _create_hire(venture["id"], USER_A, start_date="2026-10-01", one_time_cost_cents=500_000)
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            month1 = projection[0]  # October, the start month
            month2 = projection[1]  # November
            expect(
                month1["plan_expense_impact_cents"] == 1_875_000 + 500_000,
                f"start month must include recurring + one-time cost, got: {month1}",
            )
            expect(
                month2["plan_expense_impact_cents"] == 1_875_000,
                f"the month after must drop back to recurring cost only (no lingering one-time charge), got: {month2}",
            )
    finally:
        _cleanup()


# --- Case F: current vs. hire burn --------------------------------------------


def test_case_f_current_vs_hire_burn() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire F")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            financials_before = _get_financials(venture["id"], USER_A).json()
            expect(financials_before["derived"]["net_burn_cents"] == 5_000_000, f"expected base $50K burn, got: {financials_before['derived']}")

            _create_hire(venture["id"], USER_A, start_date="2026-12-01")
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            post_start_month = projection[2]  # December
            expect(
                post_start_month["net_cash_change_cents"] == -6_875_000,
                f"expected $68,750/mo net burn after the hire starts, got: {post_start_month}",
            )
    finally:
        _cleanup()


# --- Case G: hire now vs. later (preview, never persisted) --------------------


def test_case_g_hire_now_vs_later_via_preview() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire G")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")

            preview_soon = _preview_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            preview_later = _preview_hire(venture["id"], USER_A, start_date="2027-01-01").json()

            depletion_soon = next((m["date"] for m in preview_soon["with_hire_projection"] if m["depleted"]), None)
            depletion_later = next((m["date"] for m in preview_later["with_hire_projection"] if m["depleted"]), None)

            expect(depletion_soon is not None and depletion_later is not None, "both previews should deplete within the horizon")
            expect(depletion_soon < depletion_later, f"hiring later must preserve more cash / push depletion later, got soon={depletion_soon} later={depletion_later}")

            # Preview must never persist anything.
            all_hires = client.get(f"/ventures/{venture['id']}/hire-plans", headers=_auth_headers(USER_A)).json()
            expect(all_hires == [], f"preview must never create a real hire-plan row, got: {all_hires}")
    finally:
        _cleanup()


# --- Case H / I: profitable-company transitions -------------------------------


def test_case_h_hire_turns_a_profitable_company_burning() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire H")
            # $100K revenue, $80K expenses -> +$20K/mo cash-flow positive baseline.
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01", monthly_recurring_revenue_cents=10_000_000, other_expenses_cents=8_000_000)
            baseline = _get_financials(venture["id"], USER_A).json()
            expect(baseline["derived"]["status"] == "cash_flow_positive", baseline["derived"])

            # A hire costing more than the $20K/mo surplus flips it negative.
            _create_hire(venture["id"], USER_A, annual_salary_cents=36_000_000, burden_percent=0.0, start_date="2026-10-01")  # $30K/mo
            with_hire = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(with_hire[0]["net_cash_change_cents"] < 0, f"the hire must flip net cash change negative, got: {with_hire[0]}")
    finally:
        _cleanup()


def test_case_i_still_profitable_after_hire() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire I")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01", monthly_recurring_revenue_cents=20_000_000, other_expenses_cents=8_000_000)  # +$120K/mo baseline
            _create_hire(venture["id"], USER_A, start_date="2026-10-01")  # $18,750/mo -- small next to the surplus
            projection = _get_financials(venture["id"], USER_A).json()["projection_with_plan"]
            expect(len(projection) == 24, f"a still-profitable company must run the full bounded horizon, got {len(projection)}")
            expect(not any(m["depleted"] for m in projection), "must never show fake depletion for a still-profitable company")
    finally:
        _cleanup()


# --- Case J / M: cancelled / actualized never affect projections -------------


def test_case_j_cancelled_plan_does_not_affect_projection() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire J")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            with_hire = _get_financials(venture["id"], USER_A).json()
            expect(with_hire["projection_with_plan"][0]["plan_expense_impact_cents"] > 0, "sanity: the hire should be active before cancelling")

            cancel_response = _patch_hire(venture["id"], USER_A, hire["id"], status="cancelled")
            expect(cancel_response.status_code == 200, cancel_response.text)
            expect(cancel_response.json()["status"] == "cancelled", cancel_response.json())

            after_cancel = _get_financials(venture["id"], USER_A).json()
            stripped = [
                {k: v for k, v in m.items() if k not in ("plan_expense_impact_cents", "active_plan_item_ids")}
                for m in after_cancel["projection_with_plan"]
            ]
            expect(stripped == after_cancel["projection"], "a cancelled plan must produce the SAME projection as no plan at all")
    finally:
        _cleanup()


def test_case_m_actualized_plan_stops_affecting_projection() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire M")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            _patch_hire(venture["id"], USER_A, hire["id"], status="actualized")

            after = _get_financials(venture["id"], USER_A).json()
            stripped = [
                {k: v for k, v in m.items() if k not in ("plan_expense_impact_cents", "active_plan_item_ids")}
                for m in after["projection_with_plan"]
            ]
            expect(stripped == after["projection"], "an actualized plan must stop being added on top of the projection (double-counting guard)")

            # The row itself must still exist, never deleted -- history preserved.
            all_hires = client.get(f"/ventures/{venture['id']}/hire-plans", headers=_auth_headers(USER_A)).json()
            expect(any(h["id"] == hire["id"] and h["status"] == "actualized" for h in all_hires), "the actualized row must remain queryable, not deleted")
    finally:
        _cleanup()


# --- Case K: reload ------------------------------------------------------------


def test_case_k_reload_survives() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire K")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            created = _create_hire(venture["id"], USER_A, start_date="2026-12-01").json()

            reloaded = _get_financials(venture["id"], USER_A).json()
            expect(len(reloaded["hire_plans"]) == 1, reloaded["hire_plans"])
            expect(reloaded["hire_plans"][0]["id"] == created["id"], "the same hire plan must survive reload")
            expect(reloaded["hire_plans"][0]["computed_monthly_cost_cents"] == 1_875_000, reloaded["hire_plans"][0])
    finally:
        _cleanup()


# --- Case L: security ----------------------------------------------------------


def test_case_l_ownership_security() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire L")
            hire = _create_hire(venture["id"], USER_A).json()

            expect(client.get(f"/ventures/{venture['id']}/hire-plans", headers=_auth_headers(USER_B)).status_code == 404, "User B must not list User A's hire plans")
            expect(_create_hire(venture["id"], USER_B).status_code == 404, "User B must not create a hire plan on User A's venture")
            expect(_patch_hire(venture["id"], USER_B, hire["id"], status="cancelled").status_code == 404, "User B must not cancel User A's hire plan")
            expect(_preview_hire(venture["id"], USER_B).status_code == 404, "User B must not preview against User A's venture")
    finally:
        _cleanup()


# --- Case N: edit preserves the row, never deletes ----------------------------


def test_case_n_edit_lifecycle_preserves_the_row() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire N")
            created = _create_hire(venture["id"], USER_A, role="Senior Engineer").json()

            edited = _patch_hire(venture["id"], USER_A, created["id"], role="Staff Engineer")
            expect(edited.status_code == 200, edited.text)
            expect(edited.json()["role"] == "Staff Engineer", edited.json())
            expect(edited.json()["id"] == created["id"], "editing must update the SAME row, never create a new one")

            all_hires = client.get(f"/ventures/{venture['id']}/hire-plans", headers=_auth_headers(USER_A)).json()
            expect(len(all_hires) == 1, f"an edit must never leave a duplicate/orphaned row behind, got: {all_hires}")
    finally:
        _cleanup()


# --- Case O: Finance (35B) regression, at the API layer -----------------------


def test_case_o_no_plans_means_identical_projections() -> None:
    """Direct proof that the Phase 35C extension is byte-identical to
    Phase 35B when no hire plans exist -- `projection` and
    `projection_with_plan` must be exactly equal."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Hire O")
            _base_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            financials = _get_financials(venture["id"], USER_A).json()
            expect(
                financials["projection"] == [
                    {k: v for k, v in m.items() if k not in ("plan_expense_impact_cents", "active_plan_item_ids")}
                    for m in financials["projection_with_plan"]
                ],
                "with zero hire plans, the with-plan projection must reduce to exactly the baseline projection",
            )
    finally:
        _cleanup()


# --- Case P: Fundraising regression (documented, not a backend test) ---------
#
# The existing SAFE/priced-round/cap-table engine
# (dashboard/lib/fundraising/*.ts) is 100% client-side TypeScript,
# untouched by this phase -- confirmed by this phase's own diff touching
# only new files plus additive app/api.py/app/database/db.py changes.
# Its regression coverage is dashboard/tests/{fundraising,fundraisingUi}.test.ts,
# run unchanged as part of `npm test` (see this phase's final report).


TESTS = [
    test_signed_out_cannot_access_hire_plan_endpoints,
    test_case_a_basic_employee_cost,
    test_case_b_zero_burden,
    test_case_c_contractor_active_window,
    test_case_d_future_start_date_has_no_early_cost,
    test_case_e_one_time_cost_hits_one_month_only,
    test_case_f_current_vs_hire_burn,
    test_case_g_hire_now_vs_later_via_preview,
    test_case_h_hire_turns_a_profitable_company_burning,
    test_case_i_still_profitable_after_hire,
    test_case_j_cancelled_plan_does_not_affect_projection,
    test_case_m_actualized_plan_stops_affecting_projection,
    test_case_k_reload_survives,
    test_case_l_ownership_security,
    test_case_n_edit_lifecycle_preserves_the_row,
    test_case_o_no_plans_means_identical_projections,
]


def main() -> None:
    print("\nPhase 35C -- Hiring + Operating Plan Engine V1 tests")
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
