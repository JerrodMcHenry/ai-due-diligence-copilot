"""
Regression tests for Phase 38D-A -- Financial Commitment Persistence +
Frozen Expectation V1: the venture_financial_commitments table
(app/database/db.py), its Pydantic contracts
(app/models/venture_financial_commitments.py), and the new
/ventures/{id}/financial-commitments[/{id}] endpoints in app/api.py.

Same JWT-mocking harness and zztest_* user-id convention as
test_venture_scenarios.py -- no live Clerk dependency, every row cleaned
up in a finally block even on failure.

Run with:
    python -m app.tests.test_venture_financial_commitments
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_commitment_user_a"
USER_B = "zztest_commitment_user_b"

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
        "name": name, "description": "Test venture for Financial Commitments.", "industry": None,
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


def _create_hire(venture_id: int, user_id: str, **overrides):
    body = {
        "role": "Senior Engineer", "employment_type": "employee", "annual_salary_cents": 18_000_000,
        "burden_percent": 0.25, "monthly_cost_cents": None, "one_time_cost_cents": None,
        "start_date": "2026-10-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/hire-plans", json=body, headers=_auth_headers(user_id))


def _create_financial_plan(venture_id: int, user_id: str, **overrides):
    body = {
        "plan_type": "expense_change", "label": "Test plan", "category": "marketing",
        "amount_cents": 1_500_000, "start_date": "2026-11-01", "end_date": None,
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/financial-plans", json=body, headers=_auth_headers(user_id))


def _patch_hire(venture_id: int, user_id: str, hire_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/hire-plans/{hire_id}", json=fields, headers=_auth_headers(user_id))


def _patch_financial_plan(venture_id: int, user_id: str, plan_id: int, **fields):
    return client.patch(f"/ventures/{venture_id}/financial-plans/{plan_id}", json=fields, headers=_auth_headers(user_id))


def _create_scenario(venture_id: int, user_id: str, name: str, hire_ids=None, financial_ids=None):
    return client.post(
        f"/ventures/{venture_id}/scenarios",
        json={"name": name, "hire_plan_ids": hire_ids or [], "financial_plan_ids": financial_ids or []},
        headers=_auth_headers(user_id),
    )


def _create_decision(venture_id: int, user_id: str, **overrides):
    body = {
        "sie_recommendation": "Delay hiring until Q1", "sie_reasoning": "Runway is tight.",
        "founder_choice": "Proceed with the October hire",
    }
    body.update(overrides)
    return client.post(f"/ventures/{venture_id}/decisions", json=body, headers=_auth_headers(user_id))


def _commit(venture_id: int, user_id: str, **body):
    return client.post(f"/ventures/{venture_id}/financial-commitments", json=body, headers=_auth_headers(user_id))


def _list_commitments(venture_id: int, user_id: str):
    return client.get(f"/ventures/{venture_id}/financial-commitments", headers=_auth_headers(user_id))


def _get_commitment(venture_id: int, user_id: str, commitment_id: int):
    return client.get(f"/ventures/{venture_id}/financial-commitments/{commitment_id}", headers=_auth_headers(user_id))


# --- Authorization -----------------------------------------------------------


def test_signed_out_cannot_access_commitment_endpoints() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/financial-commitments").status_code == 401, "GET financial-commitments must require auth")
        expect(client.post("/ventures/1/financial-commitments", json={}).status_code == 401, "POST financial-commitments must require auth")


# --- Case A: model but never commit -----------------------------------------


def test_case_a_modeling_a_scenario_never_creates_a_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment A")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _create_scenario(venture["id"], USER_A, "Growth Plan", hire_ids=[hire["id"]])

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(rows == [], "modeling/saving a scenario alone must never create a commitment row")
    finally:
        _cleanup()


# --- Case B: commit a scenario -----------------------------------------------


def test_case_b_committing_a_scenario_creates_one_immutable_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment B")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            scenario = _create_scenario(venture["id"], USER_A, "Growth Plan", hire_ids=[hire["id"]]).json()

            response = _commit(venture["id"], USER_A, scenario_id=scenario["id"])
            expect(response.status_code == 200, f"committing a scenario must succeed, got: {response.status_code} {response.text}")
            commitment = response.json()
            expect(commitment["scenario_id"] == scenario["id"], commitment)
            expect(commitment["scenario_name"] == "Growth Plan", commitment)
            expect(commitment["status"] == "active", commitment)
            expect(len(commitment["expected_monthly"]) > 0, "a real commitment must freeze a non-empty projection")

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(len(rows) == 1, f"exactly one commitment row must exist, got: {rows}")
    finally:
        _cleanup()


# --- Case C: hire inputs frozen ----------------------------------------------


def test_case_c_hire_inputs_are_frozen_in_plan_snapshot() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment C")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(
                venture["id"], USER_A, role="Engineer", start_date="2026-10-01",
                annual_salary_cents=18_000_000, burden_percent=0.25,
            ).json()

            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            item = next(i for i in commitment["plan_snapshot"] if i["id"] == hire["id"])
            expect(item["kind"] == "hire", item)
            expect(item["role"] == "Engineer", item)
            expect(item["annual_salary_cents"] == 18_000_000, item)
            expect(item["burden_percent"] == 0.25, item)
            expect(item["start_date"] == "2026-10-01", item)
    finally:
        _cleanup()


# --- Case D: revenue target frozen -------------------------------------------


def test_case_d_revenue_target_is_frozen_in_plan_snapshot() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment D")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(
                venture["id"], USER_A, plan_type="revenue_target", label="Reach $30K MRR", category=None,
                amount_cents=3_000_000, start_date="2026-10-01",
            ).json()

            commitment = _commit(venture["id"], USER_A, financial_plan_ids=[plan["id"]]).json()
            item = next(i for i in commitment["plan_snapshot"] if i["id"] == plan["id"])
            expect(item["kind"] == "revenue_target", item)
            expect(item["amount_cents"] == 3_000_000, item)
            expect(item["start_date"] == "2026-10-01", item)
    finally:
        _cleanup()


# --- Case E: expense change frozen -------------------------------------------


def test_case_e_expense_change_is_frozen_in_plan_snapshot() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment E")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(
                venture["id"], USER_A, plan_type="expense_change", label="Cut contractors", category="contractors",
                amount_cents=-1_000_000, start_date="2026-10-01",
            ).json()

            commitment = _commit(venture["id"], USER_A, financial_plan_ids=[plan["id"]]).json()
            item = next(i for i in commitment["plan_snapshot"] if i["id"] == plan["id"])
            expect(item["kind"] == "expense_change", item)
            expect(item["category"] == "contractors", item)
            expect(item["amount_cents"] == -1_000_000, item)
    finally:
        _cleanup()


# --- Case F: mixed scenario ----------------------------------------------


def test_case_f_mixed_scenario_freezes_every_included_active_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment F")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            expense = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Marketing", category="marketing", amount_cents=1_500_000, start_date="2026-11-01").json()
            revenue = _create_financial_plan(venture["id"], USER_A, plan_type="revenue_target", label="Growth", category=None, amount_cents=4_000_000, start_date="2026-12-01").json()
            scenario = _create_scenario(venture["id"], USER_A, "Full Plan", hire_ids=[hire["id"]], financial_ids=[expense["id"], revenue["id"]]).json()

            commitment = _commit(venture["id"], USER_A, scenario_id=scenario["id"]).json()
            ids = {i["id"] for i in commitment["plan_snapshot"]}
            expect(ids == {hire["id"], expense["id"], revenue["id"]}, f"all three included plans must be frozen, got: {ids}")
            expect(set(commitment["hire_plan_ids"]) == {hire["id"]}, commitment)
            expect(set(commitment["financial_plan_ids"]) == {expense["id"], revenue["id"]}, commitment)
    finally:
        _cleanup()


# --- Cases G/H/I: source mutation test ---------------------------------------


def test_case_ghi_editing_any_source_plan_after_commit_leaves_commitment_unchanged() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment GHI")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, role="Engineer", annual_salary_cents=18_000_000, start_date="2026-10-01").json()
            revenue = _create_financial_plan(venture["id"], USER_A, plan_type="revenue_target", label="Reach $30K MRR", category=None, amount_cents=3_000_000, start_date="2026-10-01").json()
            expense = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Cut contractors", category="contractors", amount_cents=-1_000_000, start_date="2026-10-01").json()
            scenario = _create_scenario(venture["id"], USER_A, "Full Plan", hire_ids=[hire["id"]], financial_ids=[revenue["id"], expense["id"]]).json()

            before = _commit(venture["id"], USER_A, scenario_id=scenario["id"]).json()

            # Edit every underlying source row (Cases G, H, I).
            _patch_hire(venture["id"], USER_A, hire["id"], annual_salary_cents=30_000_000)
            _patch_financial_plan(venture["id"], USER_A, revenue["id"], amount_cents=9_000_000)
            _patch_financial_plan(venture["id"], USER_A, expense["id"], amount_cents=-500_000)

            after = _get_commitment(venture["id"], USER_A, before["id"]).json()
            expect(after["plan_snapshot"] == before["plan_snapshot"], "plan_snapshot must be byte-identical after every source plan is edited")
            expect(after["expected_monthly"] == before["expected_monthly"], "expected_monthly must be byte-identical after every source plan is edited")
            expect(after["calculation_version"] == before["calculation_version"], "calculation_version must be unchanged")
            expect(after["committed_at"] == before["committed_at"], "committed_at must be unchanged")
    finally:
        _cleanup()


# --- Case J: newer snapshot ---------------------------------------------


def test_case_j_a_newer_snapshot_does_not_change_an_existing_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment J")
            first_snapshot = _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01").json()["latest_snapshot"]
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            before = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            expect(before["source_snapshot_id"] == first_snapshot["id"], before)

            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-01", cash_balance_cents=1_000_000)

            after = _get_commitment(venture["id"], USER_A, before["id"]).json()
            expect(after["source_snapshot_id"] == first_snapshot["id"], "the commitment must still reference the ORIGINAL snapshot, not the new one")
            expect(after["expected_monthly"] == before["expected_monthly"], "expected_monthly must be unaffected by a newer snapshot")
    finally:
        _cleanup()


# --- Case K: GET never recomputes ---------------------------------------


def test_case_k_reading_a_commitment_never_recomputes_the_projection() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment K")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            # Patch the name as BOUND INSIDE app.api (a `from X import Y`
            # copies the reference at import time -- patching the origin
            # module financial_engine.project_monthly_cash_flow would not
            # affect api.py's own already-bound name). If GET ever started
            # recomputing, this would be the call site that did it.
            original = api.project_monthly_cash_flow

            def _boom(*args, **kwargs):
                raise AssertionError("project_monthly_cash_flow must never be called on a GET read")

            api.project_monthly_cash_flow = _boom
            try:
                response = _get_commitment(venture["id"], USER_A, commitment["id"])
                expect(response.status_code == 200, f"GET must succeed without recomputation, got: {response.status_code} {response.text}")
                expect(response.json()["expected_monthly"] == commitment["expected_monthly"], "GET must return the exact stored projection")
            finally:
                api.project_monthly_cash_flow = original
    finally:
        _cleanup()


# --- Case L: no snapshot -------------------------------------------------


def test_case_l_no_financial_snapshot_blocks_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment L")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            response = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]])
            expect(response.status_code == 404, f"a commitment without any financial snapshot must be blocked, got: {response.status_code} {response.text}")

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(rows == [], "a blocked commit attempt must never leave a row behind")
    finally:
        _cleanup()


# --- Case M: unknown required values --------------------------------------


def test_case_m_unknown_financial_values_block_commitment_with_no_fake_row() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment M")
            # cash_balance_cents omitted entirely -- an honestly incomplete snapshot.
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01", cash_balance_cents=None)
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            response = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]])
            expect(response.status_code == 422, f"an incomplete snapshot must block commitment honestly, got: {response.status_code} {response.text}")

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(rows == [], "no fake commitment row may exist when the projection could not be honestly calculated")
    finally:
        _cleanup()


# --- Case N: different user reads -----------------------------------------


def test_case_n_different_user_cannot_read_a_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment N")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            expect(_list_commitments(venture["id"], USER_B).status_code == 404, "User B must not list User A's commitments")
            expect(_get_commitment(venture["id"], USER_B, commitment["id"]).status_code == 404, "User B must not read User A's commitment by id")
    finally:
        _cleanup()


# --- Case O/P: different user commits / foreign plan reference -----------


def test_case_op_different_user_cannot_commit_a_foreign_scenario_or_plan() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Commitment OP Owner")
            _post_snapshot(venture_a["id"], USER_A, as_of_date="2026-09-01")
            hire_a = _create_hire(venture_a["id"], USER_A, start_date="2026-10-01").json()
            scenario_a = _create_scenario(venture_a["id"], USER_A, "Mine", hire_ids=[hire_a["id"]]).json()

            venture_b = _create_venture(USER_B, "ZZTest Commitment OP Other")
            _post_snapshot(venture_b["id"], USER_B, as_of_date="2026-09-01")

            expect(
                _commit(venture_b["id"], USER_B, scenario_id=scenario_a["id"]).status_code == 404,
                "User B must not commit User A's scenario, even scoped through User B's own venture",
            )
            expect(
                _commit(venture_b["id"], USER_B, hire_plan_ids=[hire_a["id"]]).status_code == 404,
                "User B must not commit a bare reference to User A's hire plan",
            )
            expect(
                _commit(venture_a["id"], USER_B, scenario_id=scenario_a["id"]).status_code == 404,
                "User B must not commit against User A's venture at all",
            )
    finally:
        _cleanup()


# --- Case Q: valid related_decision_id ------------------------------------


def test_case_q_valid_related_decision_id_is_stored() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment Q")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            decision = _create_decision(venture["id"], USER_A).json()

            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]], related_decision_id=decision["id"]).json()
            expect(commitment["related_decision_id"] == decision["id"], commitment)
    finally:
        _cleanup()


# --- Case R: foreign related_decision_id ----------------------------------


def test_case_r_foreign_related_decision_id_is_rejected() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Commitment R Owner")
            decision_a = _create_decision(venture_a["id"], USER_A).json()

            venture_b = _create_venture(USER_B, "ZZTest Commitment R Other")
            _post_snapshot(venture_b["id"], USER_B, as_of_date="2026-09-01")
            hire_b = _create_hire(venture_b["id"], USER_B, start_date="2026-10-01").json()

            response = _commit(venture_b["id"], USER_B, hire_plan_ids=[hire_b["id"]], related_decision_id=decision_a["id"])
            expect(response.status_code == 404, f"a related_decision_id belonging to another venture/user must be rejected, got: {response.status_code} {response.text}")
    finally:
        _cleanup()


# --- Case S: no related_decision_id ---------------------------------------


def test_case_s_commitment_succeeds_without_a_related_decision() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment S")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            expect(commitment["related_decision_id"] is None, commitment)
    finally:
        _cleanup()


# --- Case T: cancelled plan ------------------------------------------------


def test_case_t_cancelled_plan_is_excluded_exactly_like_the_live_scenario_engine() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment T")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            plan = _create_financial_plan(venture["id"], USER_A, plan_type="expense_change", label="Cut", category="marketing", amount_cents=-500_000, start_date="2026-10-01").json()
            _patch_financial_plan(venture["id"], USER_A, plan["id"], status="cancelled")

            commitment = _commit(venture["id"], USER_A, financial_plan_ids=[plan["id"]]).json()
            expect(commitment["plan_snapshot"] == [], "a cancelled plan must be excluded from plan_snapshot, exactly like the live scenario engine already excludes it")
            expect(commitment["financial_plan_ids"] == [], "a cancelled plan's id must not appear in the stored financial_plan_ids either")
    finally:
        _cleanup()


# --- Case U: actualized hire -------------------------------------------------


def test_case_u_actualized_hire_is_excluded_exactly_like_the_live_scenario_engine() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment U")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            _patch_hire(venture["id"], USER_A, hire["id"], status="actualized")

            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            expect(commitment["plan_snapshot"] == [], "an actualized hire must be excluded from plan_snapshot, exactly like the live scenario engine already excludes it")
            expect(commitment["hire_plan_ids"] == [], "an actualized hire's id must not appear in the stored hire_plan_ids either")
    finally:
        _cleanup()


# --- Duplicate-submit behavior (§16) ---------------------------------------


def test_idempotent_retry_does_not_create_a_second_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment Idempotency")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            first = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]], idempotency_key="zztest-key-1").json()
            second = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]], idempotency_key="zztest-key-1").json()
            expect(first["id"] == second["id"], "a retried request with the same idempotency_key must return the SAME row, not a new one")

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(len(rows) == 1, f"exactly one row must exist after an idempotent retry, got: {rows}")
    finally:
        _cleanup()


def test_repeat_commitments_with_no_idempotency_key_are_both_real() -> None:
    """§16: two genuinely separate founder actions must never be
    deduplicated merely because their plan contents happen to match."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Commitment Repeat")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()

            first = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            second = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            expect(first["id"] != second["id"], "two separate commit actions with no idempotency_key must both be recorded as real, distinct history")

            rows = _list_commitments(venture["id"], USER_A).json()
            expect(len(rows) == 2, f"two distinct commitment rows must exist, got: {rows}")
    finally:
        _cleanup()


TESTS = [
    test_signed_out_cannot_access_commitment_endpoints,
    test_case_a_modeling_a_scenario_never_creates_a_commitment,
    test_case_b_committing_a_scenario_creates_one_immutable_commitment,
    test_case_c_hire_inputs_are_frozen_in_plan_snapshot,
    test_case_d_revenue_target_is_frozen_in_plan_snapshot,
    test_case_e_expense_change_is_frozen_in_plan_snapshot,
    test_case_f_mixed_scenario_freezes_every_included_active_plan,
    test_case_ghi_editing_any_source_plan_after_commit_leaves_commitment_unchanged,
    test_case_j_a_newer_snapshot_does_not_change_an_existing_commitment,
    test_case_k_reading_a_commitment_never_recomputes_the_projection,
    test_case_l_no_financial_snapshot_blocks_commitment,
    test_case_m_unknown_financial_values_block_commitment_with_no_fake_row,
    test_case_n_different_user_cannot_read_a_commitment,
    test_case_op_different_user_cannot_commit_a_foreign_scenario_or_plan,
    test_case_q_valid_related_decision_id_is_stored,
    test_case_r_foreign_related_decision_id_is_rejected,
    test_case_s_commitment_succeeds_without_a_related_decision,
    test_case_t_cancelled_plan_is_excluded_exactly_like_the_live_scenario_engine,
    test_case_u_actualized_hire_is_excluded_exactly_like_the_live_scenario_engine,
    test_idempotent_retry_does_not_create_a_second_commitment,
    test_repeat_commitments_with_no_idempotency_key_are_both_real,
]


def main() -> None:
    print("\nPhase 38D-A -- Financial Commitment Persistence + Frozen Expectation V1 tests")
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
