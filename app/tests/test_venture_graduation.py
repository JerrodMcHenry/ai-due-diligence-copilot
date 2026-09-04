"""
Regression tests for Phase 31 -- Venture -> Startup Graduation V1:
app/database/db.py's venture_graduations section (create_venture_graduation,
resolve_startup_for_graduation, get_venture_graduation_for_owner/_by_startup),
and the GET/POST /ventures/{id}/graduation* endpoints in app/api.py.

Reuses the exact same local-RSA-keypair JWT-mocking harness as
test_startup_claims.py/test_founder_workspace.py (no live Clerk
dependency). Every row here uses a distinctive zztest_grad_* user-id
prefix and a "ZZTest Grad" company-name prefix, cleaned up in a finally
block even on failure. No test here makes an LLM/Tavily call.

Central theses under test:
  - Graduation is founder-initiated only, never automatic (no test here
    calls create_venture_graduation() from anywhere but a POST
    /ventures/{id}/graduate the test itself issued).
  - Idempotent: a repeated graduate call for the same venture never
    creates a second startup or a second venture_graduations row.
  - Cross-user-proof both directions: a venture belonging to someone else
    can't be graduated, and a startup belonging to someone else can't be
    "connected".
  - Name-collision-safe: graduating into an existing, unowned startup
    name is blocked (409), never silently merged.
  - VPS/SPS firewall: graduation never mutates the venture's own
    model_result, and never creates an `analyses` row for the new
    startup.

Run with:
    python -m app.tests.test_venture_graduation
"""

import threading
import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import (
    engine,
    get_or_create_startup,
    create_modeled_venture,
    get_modeled_venture_for_user,
    resolve_startup_for_graduation,
    user_has_startup_membership,
)

USER_A = "zztest_grad_user_a"
USER_B = "zztest_grad_user_b"
ALL_USERS = [USER_A, USER_B]

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"
TEST_PREFIX = "ZZTest Grad"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


client = TestClient(api.app)


# --- JWT mocking harness (identical pattern to prior phases' tests) --------


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


# --- Test data helpers -------------------------------------------------------


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in ALL_USERS:
            connection.execute(
                text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"),
                {"id": user_id},
            )


def _make_venture(user_id: str, name_suffix: str, assumptions: dict | None = None) -> int:
    return create_modeled_venture(
        user_id=user_id,
        name=f"{TEST_PREFIX} {name_suffix}",
        description="A test venture.",
        industry=None,
        business_model=None,
        target_customer=None,
        stage=None,
        assumptions=assumptions or {},
        model_result=None,
    )


def _cleanup() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("""
                DELETE FROM venture_graduations
                WHERE user_id = ANY(:ids)
                   OR venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))
                   OR startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
            """),
            {"ids": ALL_USERS, "pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("""
                DELETE FROM startup_memberships
                WHERE user_id = ANY(:ids)
                   OR startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
            """),
            {"ids": ALL_USERS, "pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("""
                DELETE FROM startup_claims
                WHERE user_id = ANY(:ids)
                   OR startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
            """),
            {"ids": ALL_USERS, "pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"),
            {"ids": ALL_USERS},
        )
        connection.execute(
            text("""
                DELETE FROM analyses
                WHERE startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
            """),
            {"pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("DELETE FROM startups WHERE normalized_name LIKE :pattern"),
            {"pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"),
            {"ids": ALL_USERS},
        )


# --- 1-3: baseline status / unauthenticated -----------------------------------


def test_ungraduated_venture_reports_not_graduated() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "Ungraduated")
        with _patched_auth():
            response = client.get(f"/ventures/{venture_id}/graduation", headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}")
        body = response.json()
        expect(body["graduated"] is False, "A never-graduated venture must report graduated=False")
        expect(body["startup_id"] is None, "startup_id must be None when not graduated")
    finally:
        _cleanup()


def test_unauthenticated_status_check_rejected() -> None:
    with _patched_auth():
        response = client.get("/ventures/1/graduation")
        expect(response.status_code == 401, f"Expected 401, got {response.status_code}")


def test_unauthenticated_graduate_rejected() -> None:
    with _patched_auth():
        response = client.post(
            "/ventures/1/graduate",
            json={"company_name": "X", "trigger": "manual"},
        )
        expect(response.status_code == 401, f"Expected 401, got {response.status_code}")


# --- 4-6: cross-user authorization --------------------------------------------


def test_other_users_venture_cannot_be_graduated() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "NotYours")
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": f"{TEST_PREFIX} NotYours Inc", "trigger": "manual"},
                headers=_auth_headers(USER_B),
            )
        expect(response.status_code == 404, f"Graduating someone else's venture must 404, got {response.status_code}")
    finally:
        _cleanup()


def test_other_users_venture_status_check_404s() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "StatusNotYours")
        with _patched_auth():
            response = client.get(f"/ventures/{venture_id}/graduation", headers=_auth_headers(USER_B))
        expect(response.status_code == 404, f"Checking someone else's graduation status must 404, got {response.status_code}")
    finally:
        _cleanup()


def test_nonexistent_venture_404s() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            response = client.post(
                "/ventures/999999999/graduate",
                json={"company_name": "X", "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
    finally:
        _cleanup()


# --- 7-9: the real graduation path ---------------------------------------------


def test_graduation_creates_startup_and_membership() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "RealGrad")
        company_name = f"{TEST_PREFIX} RealGrad Inc"
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual", "fields_transferred_count": 5},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
        body = response.json()
        expect(body["startup_name"] == company_name, "Returned startup_name must match what was submitted")
        expect(body["connected_existing_startup"] is False, "A freshly created startup must not be marked connected_existing")

        startup_id = body["startup_id"]
        with engine.begin() as connection:
            membership = connection.execute(text("""
                SELECT role FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": startup_id}).mappings().first()
        expect(membership is not None, "Graduation must grant a real startup_memberships row")
        expect(membership["role"] == "member", "Granted role must be 'member'")
    finally:
        _cleanup()


def test_graduation_is_idempotent_on_repeat() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "Repeat")
        company_name = f"{TEST_PREFIX} Repeat Inc"
        with _patched_auth():
            first = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
            second = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": "A Completely Different Name", "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        expect(first.status_code == 200 and second.status_code == 200, "Both calls must succeed")
        expect(
            first.json()["startup_id"] == second.json()["startup_id"],
            "A repeated graduation must return the SAME startup, never create a second one",
        )
        with engine.begin() as connection:
            count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
        expect(count == 1, f"Expected exactly one venture_graduations row, got {count}")
    finally:
        _cleanup()


def test_double_click_race_creates_one_membership() -> None:
    """Simulates a double-click / two parallel tabs: two graduate calls
    for the same venture in quick succession must still leave exactly one
    membership row, never two claims worth of duplicate grants."""
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "DoubleClick")
        company_name = f"{TEST_PREFIX} DoubleClick Inc"
        with _patched_auth():
            client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
            second = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        startup_id = second.json()["startup_id"]
        with engine.begin() as connection:
            count = connection.execute(text("""
                SELECT COUNT(*) FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": startup_id}).scalar()
        expect(count == 1, f"Expected exactly one membership row, got {count}")
    finally:
        _cleanup()


# --- 10-12: name-collision safety and connect-existing ------------------------


def test_colliding_name_owned_by_someone_else_is_blocked() -> None:
    _ensure_test_users()
    try:
        # USER_B already has an unrelated, real startup with this exact name.
        existing_startup_id = get_or_create_startup(f"{TEST_PREFIX} Collision Inc")
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO startup_memberships (user_id, startup_id, role)
                VALUES (:uid, :sid, 'member')
                ON CONFLICT DO NOTHING
            """), {"uid": USER_B, "sid": existing_startup_id})

        venture_id = _make_venture(USER_A, "Collider")
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": f"{TEST_PREFIX} Collision Inc", "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 409, f"A name collision with someone else's startup must 409, got {response.status_code}")

        with engine.begin() as connection:
            membership = connection.execute(text("""
                SELECT 1 FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": existing_startup_id}).scalar()
        expect(membership is None, "A blocked collision must never grant USER_A membership on USER_B's startup")
    finally:
        _cleanup()


def test_connect_existing_startup_the_founder_already_owns() -> None:
    _ensure_test_users()
    try:
        existing_startup_id = get_or_create_startup(f"{TEST_PREFIX} AlreadyMine Inc")
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO startup_memberships (user_id, startup_id, role)
                VALUES (:uid, :sid, 'member')
                ON CONFLICT DO NOTHING
            """), {"uid": USER_A, "sid": existing_startup_id})

        venture_id = _make_venture(USER_A, "ConnectMine")
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={
                    "company_name": "ignored",
                    "trigger": "manual",
                    "connect_existing_startup_id": existing_startup_id,
                },
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
        body = response.json()
        expect(body["startup_id"] == existing_startup_id, "Must connect to the exact startup requested")
        expect(body["connected_existing_startup"] is True, "connected_existing_startup must be True for this path")
    finally:
        _cleanup()


def test_connect_existing_startup_not_owned_is_rejected() -> None:
    _ensure_test_users()
    try:
        # USER_B owns this one; USER_A has no membership on it at all.
        someone_elses_startup_id = get_or_create_startup(f"{TEST_PREFIX} NotYoursConnect Inc")
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO startup_memberships (user_id, startup_id, role)
                VALUES (:uid, :sid, 'member')
                ON CONFLICT DO NOTHING
            """), {"uid": USER_B, "sid": someone_elses_startup_id})

        venture_id = _make_venture(USER_A, "ConnectNotMine")
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={
                    "company_name": "ignored",
                    "trigger": "manual",
                    "connect_existing_startup_id": someone_elses_startup_id,
                },
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Connecting to a startup you don't own must 404, got {response.status_code}")
    finally:
        _cleanup()


# --- 13-15: VPS/SPS firewall and Founder Workspace linkage --------------------


def test_graduation_never_creates_an_analysis_row() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "NoAnalysis")
        company_name = f"{TEST_PREFIX} NoAnalysis Inc"
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        startup_id = response.json()["startup_id"]
        with engine.begin() as connection:
            count = connection.execute(text("""
                SELECT COUNT(*) FROM analyses WHERE startup_id = :sid
            """), {"sid": startup_id}).scalar()
        expect(count == 0, "Graduation must never create an analyses/SPS row -- SPS analysis stays an explicit, separate founder action")
    finally:
        _cleanup()


def test_graduation_never_mutates_venture_model_result() -> None:
    _ensure_test_users()
    try:
        assumptions = {"validation": {"paying_customers": 3, "monthly_revenue": 500.0}}
        venture_id = _make_venture(USER_A, "VpsUnchanged", assumptions=assumptions)
        before = get_modeled_venture_for_user(USER_A, venture_id)

        with _patched_auth():
            client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": f"{TEST_PREFIX} VpsUnchanged Inc", "trigger": "suggested"},
                headers=_auth_headers(USER_A),
            )

        after = get_modeled_venture_for_user(USER_A, venture_id)
        expect(
            before.get("model_result") == after.get("model_result"),
            "Graduation must never change the venture's own VPS model_result",
        )
        expect(
            before.get("assumptions") == after.get("assumptions"),
            "Graduation must never change the venture's own assumptions",
        )
    finally:
        _cleanup()


def test_founder_workspace_shows_graduation_provenance() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "Provenance")
        company_name = f"{TEST_PREFIX} Provenance Inc"
        with _patched_auth():
            graduate_response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
            startup_id = graduate_response.json()["startup_id"]
            workspace_response = client.get(f"/founder/startups/{startup_id}", headers=_auth_headers(USER_A))

        expect(workspace_response.status_code == 200, f"Expected 200, got {workspace_response.status_code}")
        body = workspace_response.json()
        expect(body["graduated_from_venture"] is not None, "Founder Workspace must show graduation provenance")
        expect(body["graduated_from_venture"]["venture_id"] == venture_id, "Must link back to the exact source venture")
        expect(body["methodology"] is None, "A graduation-only startup must have no fabricated methodology/SPS yet")
    finally:
        _cleanup()


def test_workspace_for_non_graduated_startup_has_no_provenance() -> None:
    _ensure_test_users()
    try:
        startup_id = get_or_create_startup(f"{TEST_PREFIX} PlainStartup Inc")
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO startup_memberships (user_id, startup_id, role)
                VALUES (:uid, :sid, 'member')
                ON CONFLICT DO NOTHING
            """), {"uid": USER_A, "sid": startup_id})

        with _patched_auth():
            response = client.get(f"/founder/startups/{startup_id}", headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}")
        expect(response.json()["graduated_from_venture"] is None, "A non-graduated startup must show no graduation provenance")
    finally:
        _cleanup()


# ---------------------------------------------------------------------------
# Phase 31A -- Graduation Integrity & Acceptance Hardening.
#
# These tests directly simulate a crash at each meaningful boundary of
# the write sequence (startup+claim atomically -> membership -> linkage)
# by calling the internal functions themselves partway through, exactly
# as a real process crash would leave things -- then drive the REAL
# public endpoint as the retry, proving the system converges to one
# correct Venture <-> Startup relationship regardless of where the first
# attempt stopped. See resolve_startup_for_graduation() and
# create_venture_graduation()'s own docstrings in app/database/db.py for
# the full failure-mode analysis these tests prove.
# ---------------------------------------------------------------------------


def test_failure_after_startup_creation_orphan_recovers_on_retry() -> None:
    """
    Simulates a crash exactly after resolve_startup_for_graduation()
    returns (a brand new startup + its atomic pending claim committed)
    but before create_venture_graduation() ever runs -- finding #1's
    exact failure shape. A plain retry of the full endpoint under the
    SAME company name must recover cleanly: same startup, no duplicate,
    membership actually granted, no permanent lockout.
    """
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "OrphanRetry")
        company_name = f"{TEST_PREFIX} OrphanRetry Inc"

        orphan_startup_id, connected, claim_id = resolve_startup_for_graduation(company_name, USER_A)
        expect(connected is False, "A brand new startup must not be reported as connected_existing_startup")
        expect(claim_id is not None, "A brand new startup must get its own atomic pending claim")
        expect(
            user_has_startup_membership(USER_A, orphan_startup_id) is False,
            "Sanity: the simulated crash must leave no membership yet",
        )

        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Retry after an orphaned startup must succeed, got {response.status_code}: {response.text}")
        body = response.json()
        expect(body["startup_id"] == orphan_startup_id, "Retry must recover the SAME orphaned startup, never create a second one")

        with engine.begin() as connection:
            startup_count = connection.execute(text("""
                SELECT COUNT(*) FROM startups WHERE normalized_name = :name
            """), {"name": company_name.strip().lower()}).scalar()
        expect(startup_count == 1, f"Expected exactly one startup with this name, got {startup_count}")
        expect(
            user_has_startup_membership(USER_A, orphan_startup_id) is True,
            "Retry must actually grant membership, not just report success",
        )
    finally:
        _cleanup()


def test_orphan_from_one_user_still_blocks_a_different_user() -> None:
    """The orphan-recovery fix must not weaken cross-user protection: an
    orphan startup created by USER_A's own crashed attempt must still
    409 for USER_B trying to graduate under the exact same name."""
    _ensure_test_users()
    try:
        company_name = f"{TEST_PREFIX} OrphanCrossUser Inc"
        resolve_startup_for_graduation(company_name, USER_A)  # simulated crash -- USER_A's own orphan

        venture_id_b = _make_venture(USER_B, "OrphanCrossUserVenture")
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id_b}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_B),
            )
        expect(response.status_code == 409, f"USER_A's orphan must still block USER_B, got {response.status_code}")
    finally:
        _cleanup()


def test_failure_before_linkage_after_membership_retry_converges() -> None:
    """
    Simulates a crash strictly between "membership granted" and
    "venture_graduations row inserted" -- finding #2's exact failure
    shape. A plain retry must converge on exactly one graduation row,
    never a duplicate startup or duplicate membership.
    """
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "LinkageRetry")
        company_name = f"{TEST_PREFIX} LinkageRetry Inc"

        startup_id, _connected, claim_id = resolve_startup_for_graduation(company_name, USER_A)

        from app.database.db import _ensure_graduation_membership
        _ensure_graduation_membership(USER_A, startup_id, claim_id)

        with engine.begin() as connection:
            graduation_before = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
        expect(graduation_before == 0, "Sanity: the simulated crash must leave no graduation row yet")
        expect(
            user_has_startup_membership(USER_A, startup_id) is True,
            "Sanity: membership must actually exist before the retry",
        )

        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
        body = response.json()
        expect(body["startup_id"] == startup_id, "Retry must link to the SAME startup, never create a second one")
        expect(body["connected_existing_startup"] is True, "Retry must recognize membership already existed")

        with engine.begin() as connection:
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
            membership_count = connection.execute(text("""
                SELECT COUNT(*) FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": startup_id}).scalar()
        expect(graduation_count == 1, f"Expected exactly one graduation row after retry, got {graduation_count}")
        expect(membership_count == 1, f"Expected exactly one membership row, got {membership_count}")
    finally:
        _cleanup()


def test_repeated_post_after_success_never_duplicates_anything() -> None:
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "RepeatedPost")
        company_name = f"{TEST_PREFIX} RepeatedPost Inc"

        startup_id = None
        with _patched_auth():
            for _ in range(5):
                response = client.post(
                    f"/ventures/{venture_id}/graduate",
                    json={"company_name": company_name, "trigger": "manual"},
                    headers=_auth_headers(USER_A),
                )
                expect(response.status_code == 200, f"Expected 200 on every repeat, got {response.status_code}")
                body = response.json()
                if startup_id is None:
                    startup_id = body["startup_id"]
                expect(body["startup_id"] == startup_id, "Every repeat must return the SAME startup")

        with engine.begin() as connection:
            startup_count = connection.execute(text("""
                SELECT COUNT(*) FROM startups WHERE normalized_name = :name
            """), {"name": company_name.strip().lower()}).scalar()
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
            membership_count = connection.execute(text("""
                SELECT COUNT(*) FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": startup_id}).scalar()
            claim_count = connection.execute(text("""
                SELECT COUNT(*) FROM startup_claims WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": startup_id}).scalar()

        expect(startup_count == 1, f"Expected exactly one startup after 5 repeats, got {startup_count}")
        expect(graduation_count == 1, f"Expected exactly one graduation row after 5 repeats, got {graduation_count}")
        expect(membership_count == 1, f"Expected exactly one membership row after 5 repeats, got {membership_count}")
        expect(claim_count == 1, f"Expected exactly one claim row after 5 repeats, got {claim_count}")
    finally:
        _cleanup()


def test_parallel_graduation_requests_converge_to_one_relationship() -> None:
    """True concurrency: two threads POST /graduate for the SAME venture
    and SAME company name at (as close to) the same instant. Proves the
    UNIQUE(venture_id)/UNIQUE(startup_id) constraints and
    resolve_startup_for_graduation()'s own IntegrityError race-recovery
    branch actually hold under real concurrent access, not just
    sequential retries. The auth patch wraps the ENTIRE parallel section
    (not one `with` per thread) so one thread's context-manager exit can
    never restore unpatched auth state while the other thread's request
    is still in flight."""
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "Parallel")
        company_name = f"{TEST_PREFIX} Parallel Inc"

        results = []
        start_barrier = threading.Barrier(2)

        def worker():
            start_barrier.wait()
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
            results.append(response)

        with _patched_auth():
            t1 = threading.Thread(target=worker)
            t2 = threading.Thread(target=worker)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        expect(
            all(r.status_code == 200 for r in results),
            f"Both concurrent requests must succeed, got {[r.status_code for r in results]}",
        )
        startup_ids = {r.json()["startup_id"] for r in results}
        expect(len(startup_ids) == 1, f"Both concurrent requests must converge on the SAME startup, got {startup_ids}")
        winning_startup_id = next(iter(startup_ids))

        with engine.begin() as connection:
            startup_count = connection.execute(text("""
                SELECT COUNT(*) FROM startups WHERE normalized_name = :name
            """), {"name": company_name.strip().lower()}).scalar()
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
            membership_count = connection.execute(text("""
                SELECT COUNT(*) FROM startup_memberships WHERE user_id = :uid AND startup_id = :sid
            """), {"uid": USER_A, "sid": winning_startup_id}).scalar()

        expect(startup_count == 1, f"Expected exactly one startup after a parallel race, got {startup_count}")
        expect(graduation_count == 1, f"Expected exactly one graduation row after a parallel race, got {graduation_count}")
        expect(membership_count == 1, f"Expected exactly one membership row after a parallel race, got {membership_count}")
    finally:
        _cleanup()


def test_connecting_startup_already_graduated_by_another_venture_is_blocked() -> None:
    """Database invariant #3: a startup may be the graduation target of
    at most one venture. A second venture (even from the SAME user)
    trying to "connect" a startup that already has a different origin
    venture must be blocked, never silently create a second linkage."""
    _ensure_test_users()
    try:
        venture_1 = _make_venture(USER_A, "OriginVenture")
        company_name = f"{TEST_PREFIX} OriginVenture Inc"
        with _patched_auth():
            first = client.post(
                f"/ventures/{venture_1}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        startup_id = first.json()["startup_id"]

        venture_2 = _make_venture(USER_A, "SecondVenture")
        with _patched_auth():
            second = client.post(
                f"/ventures/{venture_2}/graduate",
                json={
                    "company_name": "ignored",
                    "trigger": "manual",
                    "connect_existing_startup_id": startup_id,
                },
                headers=_auth_headers(USER_A),
            )
        expect(second.status_code == 409, f"Connecting an already-graduated startup must 409, got {second.status_code}")

        with engine.begin() as connection:
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE startup_id = :sid
            """), {"sid": startup_id}).scalar()
        expect(graduation_count == 1, f"The startup must still have exactly one graduation link, got {graduation_count}")
    finally:
        _cleanup()


def test_database_invariants_unique_constraints_exist() -> None:
    """Direct, live verification (not just behavioral inference) that
    both UNIQUE constraints this phase's integrity depends on actually
    exist in the real schema."""
    with engine.begin() as connection:
        rows = connection.execute(text("""
            SELECT indexdef FROM pg_indexes WHERE tablename = 'venture_graduations'
        """)).mappings().all()
    defs = [row["indexdef"] for row in rows]

    expect(
        any("UNIQUE" in d and "(venture_id)" in d for d in defs),
        "venture_graduations must have a UNIQUE index on venture_id",
    )
    expect(
        any("UNIQUE" in d and "(startup_id)" in d for d in defs),
        "venture_graduations must have a UNIQUE index on startup_id (database invariant #3)",
    )


def test_deleting_venture_cascades_link_but_preserves_startup() -> None:
    """FK ON DELETE CASCADE behaves per this repo's own existing
    convention (see venture_graduations' own FK definitions): deleting a
    graduated venture removes the LINK, never the resulting startup or
    the founder's membership on it."""
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "CascadeVenture")
        company_name = f"{TEST_PREFIX} CascadeVenture Inc"
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        startup_id = response.json()["startup_id"]

        with engine.begin() as connection:
            connection.execute(text("DELETE FROM modeled_ventures WHERE id = :vid"), {"vid": venture_id})

        with engine.begin() as connection:
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE startup_id = :sid
            """), {"sid": startup_id}).scalar()
            startup_exists = connection.execute(text("""
                SELECT 1 FROM startups WHERE id = :sid
            """), {"sid": startup_id}).scalar()

        expect(graduation_count == 0, "Deleting the venture must cascade-delete its graduation link")
        expect(startup_exists is not None, "Deleting the venture must NOT delete the resulting startup")
        expect(
            user_has_startup_membership(USER_A, startup_id) is True,
            "Deleting the venture must NOT revoke the founder's startup membership",
        )
    finally:
        _cleanup()


def test_deleting_startup_cascades_link_but_preserves_venture() -> None:
    """The reverse direction: deleting the startup removes the LINK,
    never the originating venture or its history."""
    _ensure_test_users()
    try:
        venture_id = _make_venture(USER_A, "CascadeStartup")
        company_name = f"{TEST_PREFIX} CascadeStartup Inc"
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture_id}/graduate",
                json={"company_name": company_name, "trigger": "manual"},
                headers=_auth_headers(USER_A),
            )
        startup_id = response.json()["startup_id"]

        with engine.begin() as connection:
            connection.execute(text("DELETE FROM startups WHERE id = :sid"), {"sid": startup_id})

        with engine.begin() as connection:
            graduation_count = connection.execute(text("""
                SELECT COUNT(*) FROM venture_graduations WHERE venture_id = :vid
            """), {"vid": venture_id}).scalar()
            venture_exists = connection.execute(text("""
                SELECT 1 FROM modeled_ventures WHERE id = :vid
            """), {"vid": venture_id}).scalar()

        expect(graduation_count == 0, "Deleting the startup must cascade-delete its graduation link")
        expect(venture_exists is not None, "Deleting the startup must NOT delete the originating venture")
    finally:
        _cleanup()


TESTS = [
    test_ungraduated_venture_reports_not_graduated,
    test_unauthenticated_status_check_rejected,
    test_unauthenticated_graduate_rejected,
    test_other_users_venture_cannot_be_graduated,
    test_other_users_venture_status_check_404s,
    test_nonexistent_venture_404s,
    test_graduation_creates_startup_and_membership,
    test_graduation_is_idempotent_on_repeat,
    test_double_click_race_creates_one_membership,
    test_colliding_name_owned_by_someone_else_is_blocked,
    test_connect_existing_startup_the_founder_already_owns,
    test_connect_existing_startup_not_owned_is_rejected,
    test_graduation_never_creates_an_analysis_row,
    test_graduation_never_mutates_venture_model_result,
    test_founder_workspace_shows_graduation_provenance,
    test_workspace_for_non_graduated_startup_has_no_provenance,
    # Phase 31A -- Graduation Integrity & Acceptance Hardening.
    test_failure_after_startup_creation_orphan_recovers_on_retry,
    test_orphan_from_one_user_still_blocks_a_different_user,
    test_failure_before_linkage_after_membership_retry_converges,
    test_repeated_post_after_success_never_duplicates_anything,
    test_parallel_graduation_requests_converge_to_one_relationship,
    test_connecting_startup_already_graduated_by_another_venture_is_blocked,
    test_database_invariants_unique_constraints_exist,
    test_deleting_venture_cascades_link_but_preserves_startup,
    test_deleting_startup_cascades_link_but_preserves_venture,
]


def main() -> None:
    print("\nPhase 31 -- Venture -> Startup Graduation V1 tests")
    print("-" * 72)

    _cleanup()

    failures: list[str] = []

    for test in TESTS:
        name = test.__name__

        try:
            test()
        except AssertionError as error:
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    _cleanup()

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
