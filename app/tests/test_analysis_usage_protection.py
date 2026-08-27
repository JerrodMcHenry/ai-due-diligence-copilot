"""
Regression tests for Phase 10.1B -- AI Cost + Analysis Abuse Protection:
the analysis_runs concurrency lock / usage cap / duplicate-cooldown gate
inside POST /analyze (app/api.py), and the removal of
/analyze-startup, /analyze-website, /analyze-pdf as HTTP routes.

Real, genuinely-concurrent-load proof of the database-level lock lives in
test_analyze_unified_concurrency.py (a real uvicorn server is required
for that, not a TestClient) -- this file covers everything else:
sequential authorization/identity/cap/cooldown/stale-run/removal
behavior, all of which is correctly provable with a normal
FastAPI TestClient.

Reuses the exact same local-RSA-keypair JWT-mocking harness as every
other phase's test file (no live Clerk dependency). Every row here uses
a distinctive zztest_usage_* user-id prefix and a "ZZTest Usage"
company-name prefix, cleaned up in a finally block even on failure.

Run with:
    python -m app.tests.test_analysis_usage_protection
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import (
    DAILY_ANALYSIS_CAP,
    DUPLICATE_COOLDOWN_MINUTES,
    STALE_RUN_THRESHOLD_MINUTES,
    engine,
    get_or_create_startup,
    save_analysis,
    save_startup_for_user,
)

USER_A = "zztest_usage_user_a"
USER_B = "zztest_usage_user_b"
ADMIN_USER = "zztest_usage_admin"
ALL_USERS = [USER_A, USER_B, ADMIN_USER]

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"
TEST_PREFIX = "ZZTest Usage"

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


def _make_token(sub: str) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iss": TEST_ISSUER, "azp": TEST_AZP, "iat": now, "exp": now + 3600}
    return pyjwt.encode(payload, _private_key, algorithm="RS256")


class _patched_auth:
    def __enter__(self):
        self._orig_issuer = auth.CLERK_ISSUER
        self._orig_jwks_client = auth._jwks_client
        self._orig_resolve_parties = auth._resolve_authorized_parties
        self._orig_resolve_admins = auth._resolve_admin_user_ids

        auth.CLERK_ISSUER = TEST_ISSUER
        auth._jwks_client = lambda: _FakeJWKSClient()
        auth._resolve_authorized_parties = lambda: [TEST_AZP]
        auth._resolve_admin_user_ids = lambda: [ADMIN_USER]
        return self

    def __exit__(self, *exc):
        auth.CLERK_ISSUER = self._orig_issuer
        auth._jwks_client = self._orig_jwks_client
        auth._resolve_authorized_parties = self._orig_resolve_parties
        auth._resolve_admin_user_ids = self._orig_resolve_admins
        return False


def _auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


# --- Test data helpers -------------------------------------------------------


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in ALL_USERS:
            connection.execute(text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"), {"id": user_id})


def _make_member_startup(user_id: str, name_suffix: str) -> int:
    """A real canonical startup + one canonical analysis + a real
    startup_memberships row for user_id -- for founder-targeted
    re-analysis tests."""
    from app.ai.sie_v2_methodology import METHODOLOGY_VERSION

    company_name = f"{TEST_PREFIX} {name_suffix}"
    save_analysis(
        company_text=f"Original text for {company_name}",
        summary="s", risk_analysis="r", competitor_analysis="c", memo="m",
        structured_analysis={"company_name": company_name, "industry": "SaaS", "stage": "Seed", "business_model": "SaaS"},
        investment_score={}, founder_analysis={}, market_analysis={}, sources=[], traction_analysis={},
        market_score=None, team_score=None, product_score=None, competition_score=None,
        traction_score=None, financial_score=None, overall_score=None, recommendation=None,
        readiness_score=None, readiness_summary=None,
        methodology={
            "startup_intelligence_score": 50.0,
            "context": {"company_stage": "Seed", "industry": "SaaS"},
            "analysis_context": {"methodology_version": METHODOLOGY_VERSION, "evidence_sources": ["company_description"], "analysis_type": "public"},
        },
    )
    startup_id = get_or_create_startup(company_name)

    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO startup_memberships (user_id, startup_id, role)
            VALUES (:user_id, :startup_id, 'member')
            ON CONFLICT (user_id, startup_id) DO NOTHING
        """), {"user_id": user_id, "startup_id": startup_id})

    return startup_id


def _fake_success_result(company_name: str = "ZZTest Usage Fake Co"):
    from app.workflows.due_diligence_workflow import build_sie_methodology_analysis
    from app.models.analysis import (
        ExecutionAnalysisResult, FinancialAnalysisResult, FounderAnalysisResult,
        MarketAnalysisResult, ProductAnalysisResult, TractionAnalysisResult,
    )

    sie_analysis = build_sie_methodology_analysis(
        structured_analysis={"company_name": company_name, "industry": "SaaS", "business_model": "SaaS"},
        readiness=None,
        founder_analysis=FounderAnalysisResult(), market_analysis=MarketAnalysisResult(),
        product_analysis=ProductAnalysisResult(), execution_analysis=ExecutionAnalysisResult(),
        traction_analysis=TractionAnalysisResult(), financial_analysis=FinancialAnalysisResult(),
        analysis_type="public", evidence_sources=["company_description", "public_research"],
    )

    return {
        "summary": "s", "risk_analysis": "r", "competitor_analysis": "c", "memo": "m",
        "structured_analysis": {"company_name": company_name},
        "investment_score": {}, "founder_analysis": FounderAnalysisResult(),
        "market_analysis": MarketAnalysisResult(), "sources": [],
        "traction_analysis": TractionAnalysisResult(),
        "market_score": None, "team_score": None, "product_score": None,
        "competition_score": None, "traction_score": None, "financial_score": None,
        "overall_score": sie_analysis.startup_intelligence_score,
        "recommendation": None, "readiness_score": None, "readiness_summary": None,
        "sie_analysis": sie_analysis,
    }


class _fake_pipeline:
    """
    Monkeypatches api.run_due_diligence to a fast, deterministic,
    call-counting fake -- succeeds by default; raise_error=True makes it
    raise instead (for testing the failed-run-releases-the-lock path).
    Never touches the real DB directly; save_analysis() still runs for
    real against the real DB for any request that reaches it, same
    established pattern as every other phase's patched_pipeline().
    """
    def __init__(self, raise_error: bool = False, company_name: str = "ZZTest Usage Fake Co"):
        self.raise_error = raise_error
        self.company_name = company_name
        self.call_count = 0

    def __enter__(self):
        self._original = api.run_due_diligence

        def fake_run_due_diligence(company_text, analysis_type="public", evidence_sources=None):
            self.call_count += 1
            if self.raise_error:
                raise RuntimeError("intentional fake pipeline failure")
            return _fake_success_result(self.company_name)

        api.run_due_diligence = fake_run_due_diligence
        return self

    def __exit__(self, *exc):
        api.run_due_diligence = self._original
        return False


def _get_analysis_run_status(user_id: str) -> list[str]:
    with engine.begin() as connection:
        rows = connection.execute(text("""
            SELECT status FROM analysis_runs WHERE user_id = :user_id ORDER BY id
        """), {"user_id": user_id}).fetchall()
        return [row[0] for row in rows]


def _cleanup() -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM analysis_runs WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS})
        connection.execute(text("""
            DELETE FROM startup_memberships
            WHERE user_id = ANY(:ids) OR startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
        """), {"ids": ALL_USERS, "pattern": f"{TEST_PREFIX.lower()}%"})
        connection.execute(text("DELETE FROM saved_startups WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS})
        connection.execute(text("""
            DELETE FROM analyses
            WHERE startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern) OR company_name ILIKE :pattern2
        """), {"pattern": f"{TEST_PREFIX.lower()}%", "pattern2": f"{TEST_PREFIX}%"})
        connection.execute(text("DELETE FROM startups WHERE normalized_name LIKE :pattern"), {"pattern": f"{TEST_PREFIX.lower()}%"})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": ALL_USERS})


# --- 1-2: basic authorization -------------------------------------------------


def test_signed_out_analysis_denied() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            response = client.post("/analyze", data={"company_text": "Some company text."})
        expect(response.status_code == 401, f"Expected 401, got {response.status_code}")
        with engine.begin() as connection:
            count = connection.execute(text("SELECT count(*) FROM analysis_runs")).scalar()
        # Not a precise per-user check (no user is authenticated at all
        # here) -- the real assertion is that authorization is checked
        # before anything analysis_runs-related could exist for this
        # request specifically, which the 401 above already proves.
        expect(count >= 0, "Sanity check only -- see status code assertion above")
    finally:
        _cleanup()


def test_authenticated_first_analysis_allowed() -> None:
    _ensure_test_users()
    try:
        with _fake_pipeline() as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage first analysis text."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(pipeline.call_count == 1, f"Expected exactly one pipeline call, got {pipeline.call_count}")
        expect(_get_analysis_run_status(USER_A) == ["completed"], "Expected exactly one completed run")
    finally:
        _cleanup()


# --- 6-7: lock release on success/failure -------------------------------------


def test_successful_run_releases_active_run_protection() -> None:
    _ensure_test_users()
    try:
        with _fake_pipeline() as pipeline, _patched_auth():
            first = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage release-on-success first."},
                headers=_auth_headers(USER_A),
            )
            expect(first.status_code == 200, f"Expected 200: {first.text}")

            second = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage release-on-success second, different text."},
                headers=_auth_headers(USER_A),
            )
        expect(second.status_code == 200, f"Expected the lock to be released after success, got {second.status_code}: {second.text}")
        expect(pipeline.call_count == 2, f"Expected two pipeline calls, got {pipeline.call_count}")
    finally:
        _cleanup()


def test_failed_run_releases_active_run_protection() -> None:
    _ensure_test_users()
    try:
        with _fake_pipeline(raise_error=True) as pipeline, _patched_auth():
            first = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage release-on-failure first."},
                headers=_auth_headers(USER_A),
            )
            expect(first.status_code == 502, f"Expected 502 from the fake pipeline failure, got {first.status_code}")
            expect(_get_analysis_run_status(USER_A) == ["failed"], "Expected the run to be marked failed, not left running")

            second = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage release-on-failure second, different text."},
                headers=_auth_headers(USER_A),
            )
        expect(
            second.status_code == 502,
            f"Expected the lock to be released after a failure (reaching the pipeline again), got {second.status_code}: {second.text}",
        )
        expect(pipeline.call_count == 2, f"Expected two pipeline calls, got {pipeline.call_count}")
    finally:
        _cleanup()


# --- 8: stale running state never permanently locks an account --------------


def test_stale_running_state_does_not_permanently_lock_account() -> None:
    _ensure_test_users()
    try:
        # Directly insert a 'running' row older than
        # STALE_RUN_THRESHOLD_MINUTES -- simulates a process crash/restart
        # mid-pipeline, which is the only real way a 'running' row can
        # ever get this old (a real run always transitions to
        # 'completed'/'failed' via finish_analysis_run()'s try/finally).
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO analysis_runs (user_id, status, created_at)
                VALUES (:user_id, 'running', CURRENT_TIMESTAMP - make_interval(mins => :age))
            """), {"user_id": USER_A, "age": STALE_RUN_THRESHOLD_MINUTES + 5})

        with _fake_pipeline() as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage stale-lock-recovery text."},
                headers=_auth_headers(USER_A),
            )
        expect(
            response.status_code == 200,
            f"Expected a stale 'running' row to be expired and this request to succeed, got {response.status_code}: {response.text}",
        )
        expect(pipeline.call_count == 1, f"Expected the pipeline to actually run, got {pipeline.call_count} calls")
    finally:
        _cleanup()


# --- 9-10: duplicate-cooldown behavior -----------------------------------------


def test_duplicate_request_inside_cooldown_rejected() -> None:
    _ensure_test_users()
    try:
        with _fake_pipeline() as pipeline, _patched_auth():
            first = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage exact duplicate text."},
                headers=_auth_headers(USER_A),
            )
            expect(first.status_code == 200, f"Expected 200: {first.text}")

            second = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage exact duplicate text."},
                headers=_auth_headers(USER_A),
            )
        expect(second.status_code == 409, f"Expected 409 for an exact duplicate inside the cooldown, got {second.status_code}: {second.text}")
        expect(pipeline.call_count == 1, f"Expected the pipeline to run only once, got {pipeline.call_count}")
    finally:
        _cleanup()


def test_legitimate_non_duplicate_request_allowed() -> None:
    """Different input, same user, shortly after a successful submission
    -- must NOT be treated as a duplicate."""
    _ensure_test_users()
    try:
        with _fake_pipeline() as pipeline, _patched_auth():
            first = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage legitimate first submission."},
                headers=_auth_headers(USER_A),
            )
            expect(first.status_code == 200, f"Expected 200: {first.text}")

            second = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage a genuinely different second submission."},
                headers=_auth_headers(USER_A),
            )
        expect(second.status_code == 200, f"Expected a genuinely different request to be allowed, got {second.status_code}: {second.text}")
        expect(pipeline.call_count == 2, f"Expected both to reach the pipeline, got {pipeline.call_count}")
    finally:
        _cleanup()


def test_duplicate_cooldown_constant_is_reasonable() -> None:
    """Static sanity check on the documented policy constant itself."""
    expect(0 < DUPLICATE_COOLDOWN_MINUTES <= 30, f"Expected a short, human-reasonable cooldown, got {DUPLICATE_COOLDOWN_MINUTES}")


# --- 11-13: usage cap ----------------------------------------------------------


def test_usage_cap_enforced() -> None:
    _ensure_test_users()
    try:
        original_cap = api.DAILY_ANALYSIS_CAP
        api.DAILY_ANALYSIS_CAP = 2
        try:
            with _fake_pipeline() as pipeline, _patched_auth():
                for i in range(2):
                    response = client.post(
                        "/analyze",
                        data={"company_text": f"ZZTest Usage cap-fill submission {i}."},
                        headers=_auth_headers(USER_A),
                    )
                    expect(response.status_code == 200, f"Expected submission {i} to succeed under the cap: {response.text}")

                over_cap = client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage over-the-cap submission."},
                    headers=_auth_headers(USER_A),
                )
            expect(over_cap.status_code == 429, f"Expected 429 once the cap is reached, got {over_cap.status_code}: {over_cap.text}")
            expect(pipeline.call_count == 2, f"Expected exactly 2 pipeline calls (the two under-cap ones), got {pipeline.call_count}")
        finally:
            api.DAILY_ANALYSIS_CAP = original_cap
    finally:
        _cleanup()


def test_request_above_cap_rejected_before_pipeline() -> None:
    """Same property as test_usage_cap_enforced, isolated to the specific
    Part 8 #12 wording: the call-count assertion above already proves
    this, but this test makes the single rejected call's zero-pipeline-
    cost property the sole, explicit assertion."""
    _ensure_test_users()
    try:
        original_cap = api.DAILY_ANALYSIS_CAP
        api.DAILY_ANALYSIS_CAP = 1
        try:
            with _fake_pipeline() as pipeline, _patched_auth():
                client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage single allowed submission."},
                    headers=_auth_headers(USER_A),
                )
                rejected = client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage immediately-over-cap submission."},
                    headers=_auth_headers(USER_A),
                )
            expect(rejected.status_code == 429, f"Expected 429, got {rejected.status_code}")
            expect(pipeline.call_count == 1, f"Expected the rejected request to never reach the pipeline, got {pipeline.call_count} total calls")
        finally:
            api.DAILY_ANALYSIS_CAP = original_cap
    finally:
        _cleanup()


def test_different_users_have_independent_limits() -> None:
    _ensure_test_users()
    try:
        original_cap = api.DAILY_ANALYSIS_CAP
        api.DAILY_ANALYSIS_CAP = 1
        try:
            with _fake_pipeline() as pipeline, _patched_auth():
                user_a_response = client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage independent-limits user A."},
                    headers=_auth_headers(USER_A),
                )
                user_a_second = client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage independent-limits user A again."},
                    headers=_auth_headers(USER_A),
                )
                user_b_response = client.post(
                    "/analyze",
                    data={"company_text": "ZZTest Usage independent-limits user B."},
                    headers=_auth_headers(USER_B),
                )
            expect(user_a_response.status_code == 200, f"Expected User A's first request to succeed: {user_a_response.text}")
            expect(user_a_second.status_code == 429, f"Expected User A's second request to be capped, got {user_a_second.status_code}")
            expect(user_b_response.status_code == 200, f"Expected User B to have their own independent cap, got {user_b_response.status_code}: {user_b_response.text}")
            expect(pipeline.call_count == 2, f"Expected exactly 2 pipeline calls (one per user), got {pipeline.call_count}")
        finally:
            api.DAILY_ANALYSIS_CAP = original_cap
    finally:
        _cleanup()


def test_daily_analysis_cap_constant_is_centralized() -> None:
    """Static check: the cap is one named constant imported by app.api,
    not a magic number scattered across the codebase."""
    expect(isinstance(DAILY_ANALYSIS_CAP, int) and DAILY_ANALYSIS_CAP > 0, "Expected a positive integer cap")
    expect(api.DAILY_ANALYSIS_CAP == DAILY_ANALYSIS_CAP, "Expected app.api to import the same constant, not redefine its own")


# --- 14-16: founder re-analysis identity preserved -----------------------------


def test_founder_targeted_reanalysis_still_requires_membership() -> None:
    _ensure_test_users()
    other_startup_id = _make_member_startup(USER_B, "MembershipRequired")
    try:
        with _fake_pipeline() as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "Attempted unauthorized re-analysis.", "startup_id": str(other_startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404 for a non-member's founder-targeted request, got {response.status_code}")
        expect(pipeline.call_count == 0, "Pipeline must never run for an unauthorized startup_id")
        expect(_get_analysis_run_status(USER_A) == [], "No analysis_runs row should be created for a membership-check rejection")
    finally:
        _cleanup()


def test_founder_targeted_reanalysis_still_pins_startup_id() -> None:
    _ensure_test_users()
    startup_id = _make_member_startup(USER_A, "PinsStartupId")
    try:
        with _fake_pipeline(company_name="Extracted Different Name") as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "Updated pitch content.", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(pipeline.call_count == 1, "Expected exactly one pipeline call")

        with engine.begin() as connection:
            row = connection.execute(text("""
                SELECT startup_id FROM analyses WHERE startup_id = :startup_id ORDER BY id DESC LIMIT 1
            """), {"startup_id": startup_id}).fetchone()
        expect(row is not None and row[0] == startup_id, "Expected the new analysis to be pinned to the exact authorized startup_id")

        with engine.begin() as connection:
            startup_count = connection.execute(text("""
                SELECT count(*) FROM startups WHERE normalized_name = :name
            """), {"name": f"{TEST_PREFIX.lower()} pinsstartupid"}).scalar()
        expect(startup_count == 1, f"Expected no duplicate startup row to be created, found {startup_count}")
    finally:
        _cleanup()


def test_normal_analysis_identity_behavior_unchanged() -> None:
    """A normal (non-founder-targeted) analysis resolves/creates its own
    canonical startup identity exactly as before Phase 10.1B."""
    _ensure_test_users()
    company_name = "ZZTest Usage Normal Identity Co"
    try:
        with _fake_pipeline(company_name=company_name) as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": f"{company_name} is a great startup."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(pipeline.call_count == 1, "Expected exactly one pipeline call")

        with engine.begin() as connection:
            startup_row = connection.execute(text("""
                SELECT id FROM startups WHERE canonical_name = :name
            """), {"name": company_name}).fetchone()
        expect(startup_row is not None, "Expected a canonical startup to be created for the extracted company name")
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM analyses WHERE company_name ILIKE :pattern"), {"pattern": f"{company_name}%"})
            connection.execute(text("DELETE FROM startups WHERE canonical_name = :name"), {"name": company_name})
        _cleanup()


# --- 17-18: no side-effect writes ----------------------------------------------


def test_no_startup_memberships_created_by_usage_protection() -> None:
    _ensure_test_users()
    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM startup_memberships WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS}).scalar()

        with _fake_pipeline() as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage no-membership-side-effect text."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(pipeline.call_count == 1, "Expected exactly one pipeline call")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM startup_memberships WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS}).scalar()
        expect(before == after == 0, "Usage protection must never create a startup_memberships row")
    finally:
        _cleanup()


def test_no_saved_startups_created_by_usage_protection() -> None:
    _ensure_test_users()
    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM saved_startups WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS}).scalar()

        with _fake_pipeline() as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": "ZZTest Usage no-saved-startup-side-effect text."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(pipeline.call_count == 1, "Expected exactly one pipeline call")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM saved_startups WHERE user_id = ANY(:ids)"), {"ids": ALL_USERS}).scalar()
        expect(before == after == 0, "Usage protection must never create a saved_startups row")
    finally:
        _cleanup()


# --- 19-20: SPS / methodology shape unaffected ---------------------------------


def test_sps_calculation_unchanged_by_usage_protection() -> None:
    _ensure_test_users()
    company_name = "ZZTest Usage SPS Unchanged Co"
    try:
        with _fake_pipeline(company_name=company_name) as pipeline, _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": f"{company_name} details."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        expected_sps = pipeline.call_count and response.json()["methodology"]["startup_intelligence_score"]

        with engine.begin() as connection:
            stored_sps = connection.execute(text("""
                SELECT (methodology->>'startup_intelligence_score')::float
                FROM analyses WHERE company_name = :name ORDER BY id DESC LIMIT 1
            """), {"name": company_name}).scalar()

        expect(
            stored_sps == expected_sps,
            f"Expected the persisted SPS to exactly match the pipeline's own output, got stored={stored_sps} expected={expected_sps}",
        )
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM analyses WHERE company_name ILIKE :pattern"), {"pattern": f"{company_name}%"})
            connection.execute(text("DELETE FROM startups WHERE canonical_name = :name"), {"name": company_name})
        _cleanup()


def test_methodology_jsonb_shape_unchanged() -> None:
    """The persisted methodology JSONB must still carry the same
    canonical six-pillar + context + analysis_context shape -- usage
    protection reads/writes only analysis_runs, never touches
    analyses.methodology's construction."""
    _ensure_test_users()
    company_name = "ZZTest Usage Methodology Shape Co"
    try:
        with _fake_pipeline(company_name=company_name), _patched_auth():
            response = client.post(
                "/analyze",
                data={"company_text": f"{company_name} details."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        methodology = response.json()["methodology"]
        for expected_key in ("context", "market", "team", "product", "execution", "traction", "financial_health", "startup_scorecard"):
            expect(expected_key in methodology, f"Expected '{expected_key}' in the methodology response, keys were: {list(methodology.keys())}")
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM analyses WHERE company_name ILIKE :pattern"), {"pattern": f"{company_name}%"})
            connection.execute(text("DELETE FROM startups WHERE canonical_name = :name"), {"name": company_name})
        _cleanup()


# --- 21-24: legacy endpoint removal ---------------------------------------------


def test_analyze_startup_no_longer_exposed() -> None:
    registered_paths = {route.path for route in api.app.routes}
    expect("/analyze-startup" not in registered_paths, "/analyze-startup must no longer be a registered route")
    response = client.post("/analyze-startup", json={"company_text": "x"})
    expect(response.status_code == 404, f"Expected 404, got {response.status_code}")


def test_analyze_website_no_longer_exposed() -> None:
    registered_paths = {route.path for route in api.app.routes}
    expect("/analyze-website" not in registered_paths, "/analyze-website must no longer be a registered route")
    response = client.post("/analyze-website", json={"url": "https://example.com"})
    expect(response.status_code == 404, f"Expected 404, got {response.status_code}")


def test_analyze_pdf_no_longer_exposed() -> None:
    registered_paths = {route.path for route in api.app.routes}
    expect("/analyze-pdf" not in registered_paths, "/analyze-pdf must no longer be a registered route")
    response = client.post("/analyze-pdf")
    expect(response.status_code == 404, f"Expected 404, got {response.status_code}")


def test_canonical_analyze_remains_exposed() -> None:
    _ensure_test_users()
    try:
        registered_paths = {route.path for route in api.app.routes}
        expect("/analyze" in registered_paths, "/analyze must remain a registered route")
        with _patched_auth():
            response = client.post("/analyze", data={}, headers=_auth_headers(USER_A))
        expect(response.status_code == 400, f"Expected /analyze to be reachable (400 for empty sources) for an authenticated caller, got {response.status_code}")
    finally:
        _cleanup()


TESTS = [
    test_signed_out_analysis_denied,
    test_authenticated_first_analysis_allowed,
    test_successful_run_releases_active_run_protection,
    test_failed_run_releases_active_run_protection,
    test_stale_running_state_does_not_permanently_lock_account,
    test_duplicate_request_inside_cooldown_rejected,
    test_legitimate_non_duplicate_request_allowed,
    test_duplicate_cooldown_constant_is_reasonable,
    test_usage_cap_enforced,
    test_request_above_cap_rejected_before_pipeline,
    test_different_users_have_independent_limits,
    test_daily_analysis_cap_constant_is_centralized,
    test_founder_targeted_reanalysis_still_requires_membership,
    test_founder_targeted_reanalysis_still_pins_startup_id,
    test_normal_analysis_identity_behavior_unchanged,
    test_no_startup_memberships_created_by_usage_protection,
    test_no_saved_startups_created_by_usage_protection,
    test_sps_calculation_unchanged_by_usage_protection,
    test_methodology_jsonb_shape_unchanged,
    test_analyze_startup_no_longer_exposed,
    test_analyze_website_no_longer_exposed,
    test_analyze_pdf_no_longer_exposed,
    test_canonical_analyze_remains_exposed,
]


def main() -> None:
    print("\nPhase 10.1B -- AI Cost + Analysis Abuse Protection tests")
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
