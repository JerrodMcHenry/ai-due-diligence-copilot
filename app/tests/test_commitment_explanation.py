"""
Regression tests for Phase 38D-C -- Founder Explanation + Learning
Capture V1: the PATCH /ventures/{id}/financial-commitments/{id}/explanation
endpoint (app/api.py), update_venture_financial_commitment_explanation_for_owner()
(app/database/db.py), and the historical-integrity guarantees that
recording/editing an explanation must never touch any frozen field.

Same JWT-mocking harness and zztest_* user-id convention as every other
Finance test file in this repo.

Run with:
    python -m app.tests.test_commitment_explanation
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_explanation_user_a"
USER_B = "zztest_explanation_user_b"

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
        "name": name, "description": "Test venture for Founder Explanation.", "industry": None,
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


def _get_commitment(venture_id: int, user_id: str, commitment_id: int):
    return client.get(f"/ventures/{venture_id}/financial-commitments/{commitment_id}", headers=_auth_headers(user_id))


def _comparison(venture_id: int, user_id: str, commitment_id: int):
    return client.get(f"/ventures/{venture_id}/financial-commitments/{commitment_id}/comparison", headers=_auth_headers(user_id))


def _set_explanation(venture_id: int, user_id: str, commitment_id: int, text_: str):
    return client.patch(
        f"/ventures/{venture_id}/financial-commitments/{commitment_id}/explanation",
        json={"founder_explanation": text_},
        headers=_auth_headers(user_id),
    )


def _committed_with_one_observed_month(user_id: str, name: str):
    """Shared fixture: a venture with a commitment that has exactly one
    comparable (observed) month, used by most cases below."""
    venture = _create_venture(user_id, name)
    _post_snapshot(venture["id"], user_id, as_of_date="2026-09-01")
    hire = _create_hire(venture["id"], user_id, start_date="2026-10-01").json()
    commitment = _commit(venture["id"], user_id, hire_plan_ids=[hire["id"]]).json()
    _post_snapshot(venture["id"], user_id, as_of_date="2026-10-15", cash_balance_cents=44_000_000)
    return venture, hire, commitment


def test_signed_out_cannot_access_explanation_endpoint() -> None:
    with _patched_auth():
        expect(
            client.patch("/ventures/1/financial-commitments/1/explanation", json={"founder_explanation": "x"}).status_code == 401,
            "PATCH explanation must require auth",
        )


def test_case_a_explanation_cannot_be_recorded_against_another_users_commitment() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation A")
            response = _set_explanation(venture["id"], USER_B, commitment["id"], "Not my commitment.")
            expect(response.status_code == 404, f"User B must not record an explanation on User A's commitment, got: {response.status_code}")
    finally:
        _cleanup()


def test_case_b_explanation_survives_reload() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation B")
            text_ = "We accelerated the hire after closing an enterprise pilot."
            saved = _set_explanation(venture["id"], USER_A, commitment["id"], text_)
            expect(saved.status_code == 200, saved.text)
            expect(saved.json()["founder_explanation"] == text_, saved.json())
            expect(saved.json()["explanation_recorded_at"] is not None, saved.json())

            reread = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(reread["founder_explanation"] == text_, "the explanation must survive an independent GET/reload")
    finally:
        _cleanup()


def test_case_c_explanation_can_be_edited() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation C")
            _set_explanation(venture["id"], USER_A, commitment["id"], "First explanation.")
            edited = _set_explanation(venture["id"], USER_A, commitment["id"], "Revised explanation.")
            expect(edited.status_code == 200, edited.text)
            expect(edited.json()["founder_explanation"] == "Revised explanation.", edited.json())

            reread = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(reread["founder_explanation"] == "Revised explanation.", "the edit must persist, replacing the original text entirely -- no revision history kept")
    finally:
        _cleanup()


def test_case_d_editing_explanation_changes_no_frozen_expectation_field() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation D")
            before = _get_commitment(venture["id"], USER_A, commitment["id"]).json()

            _set_explanation(venture["id"], USER_A, commitment["id"], "First.")
            _set_explanation(venture["id"], USER_A, commitment["id"], "Second, edited.")

            after = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(after["plan_snapshot"] == before["plan_snapshot"], "plan_snapshot must never move when saving/editing an explanation")
            expect(after["expected_monthly"] == before["expected_monthly"], "expected_monthly must never move")
            expect(after["committed_at"] == before["committed_at"], "committed_at must never move")
            expect(after["source_snapshot_id"] == before["source_snapshot_id"], "source_snapshot_id must never move")
            expect(after["calculation_version"] == before["calculation_version"], "calculation_version must never move")
    finally:
        _cleanup()


def test_case_e_editing_explanation_changes_no_actual_financial_snapshot() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation E")
            before_snapshots = client.get(f"/ventures/{venture['id']}/financials/history", headers=_auth_headers(USER_A)).json()

            _set_explanation(venture["id"], USER_A, commitment["id"], "An explanation.")

            after_snapshots = client.get(f"/ventures/{venture['id']}/financials/history", headers=_auth_headers(USER_A)).json()
            expect(before_snapshots == after_snapshots, "recording an explanation must never touch any venture_financial_snapshots row")
    finally:
        _cleanup()


def test_case_f_editing_live_plans_after_explanation_still_leaves_expectation_unchanged() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation F")
            before = _get_commitment(venture["id"], USER_A, commitment["id"]).json()

            _set_explanation(venture["id"], USER_A, commitment["id"], "Explained before editing the live plan.")
            _patch_hire(venture["id"], USER_A, hire["id"], annual_salary_cents=99_000_000)

            after = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(after["plan_snapshot"] == before["plan_snapshot"], "editing the live hire after explanation capture must not move the frozen plan_snapshot")
            expect(after["expected_monthly"] == before["expected_monthly"], "editing the live hire after explanation capture must not move expected_monthly")
            expect(after["founder_explanation"] == "Explained before editing the live plan.", "the explanation itself must remain intact through the unrelated plan edit")
    finally:
        _cleanup()


def test_case_g_newer_snapshot_updates_comparison_but_never_overwrites_explanation() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation G")
            _set_explanation(venture["id"], USER_A, commitment["id"], "Original explanation, before more data arrived.")

            before_comparison = _comparison(venture["id"], USER_A, commitment["id"]).json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-11-15", cash_balance_cents=39_000_000)
            after_comparison = _comparison(venture["id"], USER_A, commitment["id"]).json()

            expect(
                after_comparison["comparison_status"] != before_comparison["comparison_status"]
                or len([m for m in after_comparison["months"] if m["actual_snapshot_id"]]) >
                len([m for m in before_comparison["months"] if m["actual_snapshot_id"]]),
                "a newer snapshot must change the comparison's own observed-month coverage",
            )

            reread = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(
                reread["founder_explanation"] == "Original explanation, before more data arrived.",
                "a NEW actual snapshot must never silently overwrite an existing founder explanation",
            )
    finally:
        _cleanup()


def test_case_h_awaiting_actuals_commitment_rejects_explanation_capture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Explanation H")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()

            comparison = _comparison(venture["id"], USER_A, commitment["id"]).json()
            expect(comparison["comparison_status"] == "awaiting_actuals", "sanity: no actual has been recorded yet")

            response = _set_explanation(venture["id"], USER_A, commitment["id"], "Premature explanation.")
            expect(response.status_code == 409, f"an explanation must be rejected while the plan is still awaiting all actuals, got: {response.status_code} {response.text}")

            reread = _get_commitment(venture["id"], USER_A, commitment["id"]).json()
            expect(reread["founder_explanation"] is None, "a rejected explanation attempt must never be persisted")
    finally:
        _cleanup()


def test_case_i_partially_observed_commitment_supports_explanation_capture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Explanation I")
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-09-01")
            hire = _create_hire(venture["id"], USER_A, start_date="2026-10-01").json()
            commitment = _commit(venture["id"], USER_A, hire_plan_ids=[hire["id"]]).json()
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-15")  # only month 1 of a 24-month plan

            comparison = _comparison(venture["id"], USER_A, commitment["id"]).json()
            expect(comparison["comparison_status"] == "partially_observed", comparison["comparison_status"])

            response = _set_explanation(venture["id"], USER_A, commitment["id"], "Explaining an early, partial result.")
            expect(response.status_code == 200, f"a partially observed commitment must support explanation capture, got: {response.status_code} {response.text}")
    finally:
        _cleanup()


def test_case_j_null_actual_metrics_remain_null_after_explanation_capture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture, hire, commitment = _committed_with_one_observed_month(USER_A, "ZZTest Explanation J")
            # The observed snapshot never recorded revenue.
            _post_snapshot(venture["id"], USER_A, as_of_date="2026-10-20", monthly_recurring_revenue_cents=None, monthly_non_recurring_revenue_cents=None)

            _set_explanation(venture["id"], USER_A, commitment["id"], "Cash came in as expected.")

            comparison = _comparison(venture["id"], USER_A, commitment["id"]).json()
            month1 = comparison["months"][0]
            expect(month1["revenue"]["actual"] is None, "an unknown actual revenue must remain null, never a fabricated zero, regardless of explanation capture")
            expect(month1["revenue"]["variance"] is None, month1)
    finally:
        _cleanup()


def test_case_k_no_ai_call_occurs() -> None:
    """Structural: recording an explanation must never import or call
    anything from app.ai's OpenAI/Tavily-backed modules -- only the
    already-existing pure comparison function."""
    import inspect
    source = inspect.getsource(api.update_financial_commitment_explanation)
    for forbidden in ("openai", "tavily", "OpenAI", "generate_", "chat.completions"):
        expect(forbidden not in source, f"the explanation endpoint must never reference {forbidden!r}")


TESTS = [
    test_signed_out_cannot_access_explanation_endpoint,
    test_case_a_explanation_cannot_be_recorded_against_another_users_commitment,
    test_case_b_explanation_survives_reload,
    test_case_c_explanation_can_be_edited,
    test_case_d_editing_explanation_changes_no_frozen_expectation_field,
    test_case_e_editing_explanation_changes_no_actual_financial_snapshot,
    test_case_f_editing_live_plans_after_explanation_still_leaves_expectation_unchanged,
    test_case_g_newer_snapshot_updates_comparison_but_never_overwrites_explanation,
    test_case_h_awaiting_actuals_commitment_rejects_explanation_capture,
    test_case_i_partially_observed_commitment_supports_explanation_capture,
    test_case_j_null_actual_metrics_remain_null_after_explanation_capture,
    test_case_k_no_ai_call_occurs,
]


def main() -> None:
    print("\nPhase 38D-C -- Founder Explanation + Learning Capture V1 tests")
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
