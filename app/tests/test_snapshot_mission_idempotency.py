"""
Regression tests for Phase 40A-FIX P1 #2 -- request-identity idempotency
on financial snapshot creation and mission creation. See
docs/product/... final report for the full audit.

Covers, per the directive's own required test list: first submission,
exact retry, a separate intentional submission, cross-user behavior,
cross-venture behavior, reload/direct-API-replay behavior, and "no
fabricated row on a failed request." Idempotency represents REQUEST
IDENTITY (the key), never payload similarity -- two genuinely separate
submissions with identical field values must both persist.

Run with:
    python -m app.tests.test_snapshot_mission_idempotency
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


USER_A = "zztest_idempotency_user_a"
USER_B = "zztest_idempotency_user_b"

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
        for table in ("venture_missions", "venture_financial_snapshots"):
            connection.execute(
                text(f"DELETE FROM {table} WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
                {"ids": [USER_A, USER_B]},
            )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture_body(name: str) -> dict:
    return {
        "name": name, "description": "Test venture for idempotency.", "industry": None,
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


def _mission_body(**overrides) -> dict:
    body = {"title": "Interview 10 customers", "mission_type": "customer_discovery", "source": "founder_created"}
    body.update(overrides)
    return body


def _post_mission(venture_id: int, user_id: str, **overrides):
    return client.post(f"/ventures/{venture_id}/missions", json=_mission_body(**overrides), headers=_auth_headers(user_id))


def _history(venture_id: int, user_id: str) -> list:
    return client.get(f"/ventures/{venture_id}/financials/history", headers=_auth_headers(user_id)).json()["snapshots"]


def _missions(venture_id: int, user_id: str) -> list:
    return client.get(f"/ventures/{venture_id}/missions", headers=_auth_headers(user_id)).json()


# --- Financial snapshot idempotency ------------------------------------------


def test_snapshot_first_submission_creates_a_row() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Snapshot A")
            response = _post_snapshot(venture["id"], USER_A, idempotency_key="zzkey-1")
            expect(response.status_code == 200, response.text)
            expect(len(_history(venture["id"], USER_A)) == 1, "first submission must create exactly one snapshot")
    finally:
        _cleanup()


def test_snapshot_exact_retry_returns_same_row_no_duplicate() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Snapshot B")
            first = _post_snapshot(venture["id"], USER_A, idempotency_key="zzkey-2").json()["latest_snapshot"]
            second = _post_snapshot(venture["id"], USER_A, idempotency_key="zzkey-2").json()["latest_snapshot"]
            expect(first["id"] == second["id"], "a retried request with the same idempotency_key must return the SAME row, not a new one")
            expect(len(_history(venture["id"], USER_A)) == 1, f"exactly one snapshot must exist after a retry, got: {_history(venture['id'], USER_A)}")
    finally:
        _cleanup()


def test_snapshot_separate_intentional_submissions_are_both_real() -> None:
    """Idempotency represents request identity, not payload similarity --
    two genuinely separate submissions (no key, or different keys) with
    IDENTICAL field values must both persist as real historical rows."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Snapshot C")
            _post_snapshot(venture["id"], USER_A)  # no key at all
            _post_snapshot(venture["id"], USER_A)  # no key at all, identical payload
            expect(len(_history(venture["id"], USER_A)) == 2, "two separate keyless submissions with identical payloads must both be recorded as real history")
    finally:
        _cleanup()


def test_snapshot_cross_user_idempotency_key_replay_is_isolated() -> None:
    """User B replaying User A's own idempotency_key must never read or
    touch User A's resource -- it must create User B's OWN new snapshot,
    scoped entirely to User B's own venture."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Idempotency CrossUser A")
            venture_b = _create_venture(USER_B, "ZZTest Idempotency CrossUser B")

            a_snapshot = _post_snapshot(venture_a["id"], USER_A, idempotency_key="zzkey-shared").json()["latest_snapshot"]
            b_response = _post_snapshot(venture_b["id"], USER_B, idempotency_key="zzkey-shared")
            expect(b_response.status_code == 200, f"User B must be able to use the same literal key string -- it's scoped globally at the DB level but must never leak User A's data, got: {b_response.text}")
            b_snapshot = b_response.json()["latest_snapshot"]

            expect(b_snapshot["id"] != a_snapshot["id"], "User B's replay of the same key string must never return User A's row")
            expect(b_snapshot["venture_id"] == venture_b["id"], b_snapshot)
            expect(len(_history(venture_a["id"], USER_A)) == 1, "User A's history must be unaffected by User B's own request")
    finally:
        _cleanup()


def test_snapshot_reload_and_direct_api_replay_is_stable() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Snapshot Reload")
            first = _post_snapshot(venture["id"], USER_A, idempotency_key="zzkey-reload").json()["latest_snapshot"]
            # Simulate a founder reloading and the browser/client resending
            # the exact same request (e.g. a retried fetch after a flaky
            # network response) -- direct API replay, not just a UI click.
            for _ in range(3):
                replay = _post_snapshot(venture["id"], USER_A, idempotency_key="zzkey-reload").json()["latest_snapshot"]
                expect(replay["id"] == first["id"], "every replay must resolve to the exact same original row")
            expect(len(_history(venture["id"], USER_A)) == 1, "no orphan/duplicate rows after repeated replay")
    finally:
        _cleanup()


def test_snapshot_no_partial_row_on_ownership_failure() -> None:
    """A request that fails authorization before persistence must never
    leave a fabricated/partial row behind."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Idempotency NoOrphan")
            response = _post_snapshot(venture_a["id"], USER_B, idempotency_key="zzkey-orphan")
            expect(response.status_code == 404, f"User B must not be able to write to User A's venture, got: {response.status_code}")
            expect(_history(venture_a["id"], USER_A) == [], "a failed/unauthorized request must never leave any row behind")
    finally:
        _cleanup()


# --- Mission idempotency ------------------------------------------------


def test_mission_first_submission_creates_a_row() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Mission A")
            response = _post_mission(venture["id"], USER_A, idempotency_key="zzmkey-1")
            expect(response.status_code == 200, response.text)
            expect(len(_missions(venture["id"], USER_A)) == 1, "first submission must create exactly one mission")
    finally:
        _cleanup()


def test_mission_exact_retry_returns_same_row_no_duplicate() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Mission B")
            first = _post_mission(venture["id"], USER_A, idempotency_key="zzmkey-2").json()
            second = _post_mission(venture["id"], USER_A, idempotency_key="zzmkey-2").json()
            expect(first["id"] == second["id"], "a retried mission request with the same idempotency_key must return the SAME row")
            expect(len(_missions(venture["id"], USER_A)) == 1, f"exactly one mission must exist after a retry, got: {_missions(venture['id'], USER_A)}")
    finally:
        _cleanup()


def test_mission_separate_intentional_submissions_are_both_real() -> None:
    """This is the exact gap the fix closes: founder_created missions
    were NEVER deduplicated by the pre-existing source_ref mechanism, so
    a genuine double-submit with no key at all was already possible
    before this phase. Confirm two intentionally identical
    founder-authored missions still both persist -- payload similarity
    alone must never merge them."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Mission C")
            _post_mission(venture["id"], USER_A)
            _post_mission(venture["id"], USER_A)
            expect(len(_missions(venture["id"], USER_A)) == 2, "two separate keyless mission submissions with identical titles must both be recorded")
    finally:
        _cleanup()


def test_mission_vps_guidance_source_ref_dedup_still_works_unchanged() -> None:
    """The PRE-EXISTING title-based dedup for vps_guidance/pitch_deck_coach
    sources must be completely untouched by this phase -- confirmed by
    calling create_mission with NO idempotency_key at all (the default,
    byte-identical code path)."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Idempotency Mission VPS")
            first = _post_mission(venture["id"], USER_A, title="Validate pricing", source="vps_guidance").json()
            second = _post_mission(venture["id"], USER_A, title="Validate pricing", source="vps_guidance").json()
            expect(first["id"] == second["id"], "the pre-existing vps_guidance source_ref dedup must still collapse an identical-title suggestion, unchanged")
            expect(len(_missions(venture["id"], USER_A)) == 1, _missions(venture["id"], USER_A))
    finally:
        _cleanup()


def test_mission_cross_user_idempotency_key_replay_is_isolated() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Idempotency Mission CrossUser A")
            venture_b = _create_venture(USER_B, "ZZTest Idempotency Mission CrossUser B")

            a_mission = _post_mission(venture_a["id"], USER_A, idempotency_key="zzmkey-shared").json()
            b_response = _post_mission(venture_b["id"], USER_B, idempotency_key="zzmkey-shared")
            expect(b_response.status_code == 200, b_response.text)
            b_mission = b_response.json()

            expect(b_mission["id"] != a_mission["id"], "User B's replay of the same key string must never return User A's mission")
            expect(b_mission["venture_id"] == venture_b["id"], b_mission)
            expect(len(_missions(venture_a["id"], USER_A)) == 1, "User A's missions must be unaffected by User B's own request")
    finally:
        _cleanup()


def test_mission_no_partial_row_on_ownership_failure() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Idempotency Mission NoOrphan")
            response = _post_mission(venture_a["id"], USER_B, idempotency_key="zzmkey-orphan")
            expect(response.status_code == 404, f"User B must not be able to write to User A's venture, got: {response.status_code}")
            expect(_missions(venture_a["id"], USER_A) == [], "a failed/unauthorized mission request must never leave any row behind")
    finally:
        _cleanup()


TESTS = [
    test_snapshot_first_submission_creates_a_row,
    test_snapshot_exact_retry_returns_same_row_no_duplicate,
    test_snapshot_separate_intentional_submissions_are_both_real,
    test_snapshot_cross_user_idempotency_key_replay_is_isolated,
    test_snapshot_reload_and_direct_api_replay_is_stable,
    test_snapshot_no_partial_row_on_ownership_failure,
    test_mission_first_submission_creates_a_row,
    test_mission_exact_retry_returns_same_row_no_duplicate,
    test_mission_separate_intentional_submissions_are_both_real,
    test_mission_vps_guidance_source_ref_dedup_still_works_unchanged,
    test_mission_cross_user_idempotency_key_replay_is_isolated,
    test_mission_no_partial_row_on_ownership_failure,
]


def main() -> None:
    print("\nPhase 40A-FIX -- Snapshot + Mission Idempotency tests")
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
