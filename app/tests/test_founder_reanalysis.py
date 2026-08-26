"""
Regression tests for Phase 7.2.1 -- Deterministic Founder Re-analysis:
the optional startup_id parameter on POST /analyze (app/api.py) and
save_analysis()'s optional authoritative startup_id override
(app/database/db.py).

Reuses the exact same local-RSA-keypair JWT-mocking harness as
test_founder_workspace.py/test_startup_membership.py (no live Clerk
dependency) for real per-request identities -- unlike
test_analyze_unified.py's single fixed dependency_overrides identity,
these tests genuinely care about which user is making the request, so
each test presents its own signed token for USER_A/USER_B/etc.

app.api.run_due_diligence is monkeypatched to a fast, deterministic,
LLM-free fake (same technique as test_analyze_unified.py, reusing the
REAL build_sie_methodology_analysis() plumbing) -- restored after every
test even on failure. save_analysis() itself is NEVER faked: tests that
should reach persistence exercise the real function against the real
database, so "no duplicate startup", "canonical_name unchanged", and
"exact startup_id persisted" are genuine, not asserted against a stub.

Every row here uses a distinctive zztest_reanalysis_* user-id prefix and
a "ZZTest Reanalysis" company-name prefix, cleaned up in a finally block
even on failure.

Run with:
    python -m app.tests.test_founder_reanalysis
"""

import time
from contextlib import contextmanager

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import (
    engine,
    get_or_create_startup,
    save_analysis,
    save_startup_for_user,
    create_modeled_venture,
)
from app.models.analysis import (
    ExecutionAnalysisResult,
    FinancialAnalysisResult,
    FounderAnalysisResult,
    MarketAnalysisResult,
    ProductAnalysisResult,
    TractionAnalysisResult,
)
from app.workflows.due_diligence_workflow import build_sie_methodology_analysis

USER_A = "zztest_reanalysis_user_a"
USER_B = "zztest_reanalysis_user_b"
ADMIN_USER = "zztest_reanalysis_admin"
ALL_USERS = [USER_A, USER_B, ADMIN_USER]

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"
TEST_PREFIX = "ZZTest Reanalysis"

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
    def __init__(self, admin_ids=None):
        self._admin_ids = admin_ids if admin_ids is not None else [ADMIN_USER]

    def __enter__(self):
        self._orig_issuer = auth.CLERK_ISSUER
        self._orig_jwks_client = auth._jwks_client
        self._orig_resolve_parties = auth._resolve_authorized_parties
        self._orig_resolve_admins = auth._resolve_admin_user_ids

        auth.CLERK_ISSUER = TEST_ISSUER
        auth._jwks_client = lambda: _FakeJWKSClient()
        auth._resolve_authorized_parties = lambda: [TEST_AZP]
        auth._resolve_admin_user_ids = lambda: self._admin_ids
        return self

    def __exit__(self, *exc):
        auth.CLERK_ISSUER = self._orig_issuer
        auth._jwks_client = self._orig_jwks_client
        auth._resolve_authorized_parties = self._orig_resolve_parties
        auth._resolve_admin_user_ids = self._orig_resolve_admins
        return False


def _auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


# --- Fast, LLM-free fake pipeline (same technique as test_analyze_unified.py) -


@contextmanager
def patched_pipeline(extracted_company_name: str = "ZZTest Reanalysis Extracted Variant"):
    """
    Patches app.api's module-level run_due_diligence only -- save_analysis
    is deliberately left REAL (see module docstring) so persistence
    behavior under test is genuine. call_log records whether the pipeline
    actually ran, which is exactly what the authorization-boundary tests
    below need to assert ("the pipeline must never run for an
    unauthorized request").
    """
    call_log: list[dict] = []

    def fake_run_due_diligence(company_text, analysis_type="public", evidence_sources=None):
        call_log.append({"ran": True, "company_text": company_text})

        sie_analysis = build_sie_methodology_analysis(
            structured_analysis={
                "company_name": extracted_company_name,
                "industry": "SaaS",
                "business_model": "SaaS",
            },
            readiness=None,
            founder_analysis=FounderAnalysisResult(),
            market_analysis=MarketAnalysisResult(),
            product_analysis=ProductAnalysisResult(),
            execution_analysis=ExecutionAnalysisResult(),
            traction_analysis=TractionAnalysisResult(),
            financial_analysis=FinancialAnalysisResult(),
            analysis_type=analysis_type,
            evidence_sources=evidence_sources,
        )

        return {
            "summary": "s",
            "risk_analysis": "r",
            "competitor_analysis": "c",
            "memo": "m",
            "structured_analysis": {"company_name": extracted_company_name},
            "investment_score": {},
            "founder_analysis": FounderAnalysisResult(),
            "market_analysis": MarketAnalysisResult(),
            "sources": [],
            "traction_analysis": TractionAnalysisResult(),
            "market_score": None,
            "team_score": None,
            "product_score": None,
            "competition_score": None,
            "traction_score": None,
            "financial_score": None,
            "overall_score": sie_analysis.startup_intelligence_score,
            "recommendation": None,
            "readiness_score": None,
            "readiness_summary": None,
            "sie_analysis": sie_analysis,
        }

    original_run_due_diligence = api.run_due_diligence
    api.run_due_diligence = fake_run_due_diligence

    try:
        yield call_log
    finally:
        api.run_due_diligence = original_run_due_diligence


# --- Test data helpers -------------------------------------------------------


def _make_canonical_startup(name_suffix: str) -> int:
    """A real canonical startup with one real analysis already on record
    (via the real save_analysis(), no startup_id override) -- the
    'existing authoritative canonical startup' every test below
    re-analyzes against."""
    company_name = f"{TEST_PREFIX} {name_suffix}"
    save_analysis(
        company_text=f"Original analysis text for {company_name}",
        summary="s", risk_analysis="r", competitor_analysis="c", memo="m",
        structured_analysis={"company_name": company_name, "industry": "SaaS", "stage": "Seed", "business_model": "SaaS"},
        investment_score={}, founder_analysis={}, market_analysis={}, sources=[], traction_analysis={},
        market_score=None, team_score=None, product_score=None, competition_score=None,
        traction_score=None, financial_score=None, overall_score=None, recommendation=None,
        readiness_score=None, readiness_summary=None,
        methodology={"startup_intelligence_score": 50.0},
    )
    return get_or_create_startup(company_name)


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in ALL_USERS:
            connection.execute(
                text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"),
                {"id": user_id},
            )


def _grant_membership(user_id: str, startup_id: int, role: str = "member") -> None:
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO startup_memberships (user_id, startup_id, role)
            VALUES (:user_id, :startup_id, :role)
            ON CONFLICT (user_id, startup_id) DO NOTHING
        """), {"user_id": user_id, "startup_id": startup_id, "role": role})


def _cleanup() -> None:
    with engine.begin() as connection:
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
            text("DELETE FROM saved_startups WHERE user_id = ANY(:ids)"),
            {"ids": ALL_USERS},
        )
        connection.execute(
            text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"),
            {"ids": ALL_USERS},
        )
        connection.execute(
            text("""
                DELETE FROM analyses
                WHERE startup_id IN (SELECT id FROM startups WHERE normalized_name LIKE :pattern)
                   OR company_name ILIKE :pattern2
            """),
            {"pattern": f"{TEST_PREFIX.lower()}%", "pattern2": f"{TEST_PREFIX}%"},
        )
        connection.execute(
            text("DELETE FROM startups WHERE normalized_name LIKE :pattern"),
            {"pattern": f"{TEST_PREFIX.lower()}%"},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"),
            {"ids": ALL_USERS},
        )


# --- 1: normal analysis without startup_id is unchanged -----------------------


def test_normal_analysis_without_startup_id_uses_get_or_create() -> None:
    _ensure_test_users()
    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM startups")).scalar()

        company_name = f"{TEST_PREFIX} NormalFlow"
        with _patched_auth(), patched_pipeline(extracted_company_name=company_name) as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "Some company description text."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
        expect(len(call_log) == 1, "Pipeline must run exactly once for a normal request")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM startups")).scalar()
            row = connection.execute(
                text("SELECT startup_id, company_name FROM analyses WHERE company_name = :n ORDER BY id DESC LIMIT 1"),
                {"n": company_name},
            ).mappings().first()

        expect(after == before + 1, f"Expected exactly one new startup via get_or_create, before={before} after={after}")
        expect(row is not None and row["company_name"] == company_name, "company_name must be exactly what was extracted")
    finally:
        _cleanup()


# --- 2-6: authoritative startup_id write-path behavior ------------------------


def test_authorized_reanalysis_uses_supplied_startup_id() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("Authoritative")
    try:
        _grant_membership(USER_A, startup_id)

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "Updated info.", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
        expect(len(call_log) == 1, "Pipeline must run exactly once for an authorized request")

        with engine.begin() as connection:
            row = connection.execute(
                text("SELECT startup_id FROM analyses WHERE startup_id = :s ORDER BY id DESC LIMIT 1"),
                {"s": startup_id},
            ).mappings().first()
        expect(row is not None and row["startup_id"] == startup_id, "New analysis must be attached to the supplied startup_id")
    finally:
        _cleanup()


def test_founder_reanalysis_does_not_create_another_startup() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("NoDuplicate")
    try:
        _grant_membership(USER_A, startup_id)

        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM startups")).scalar()

        with _patched_auth(), patched_pipeline(extracted_company_name=f"{TEST_PREFIX} NoDuplicate Inc."):
            response = client.post(
                "/analyze",
                data={"company_text": "New deck content.", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM startups")).scalar()
        expect(after == before, f"Founder re-analysis must never create a new startup, before={before} after={after}")
    finally:
        _cleanup()


def test_extracted_company_name_variation_cannot_create_another_startup() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("NameVariant")
    try:
        _grant_membership(USER_A, startup_id)

        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM startups")).scalar()

        variants = [
            f"{TEST_PREFIX} NameVariant Inc.",
            f"{TEST_PREFIX} NameVariant, Inc.",
            f"{TEST_PREFIX} NameVariant App",
        ]

        for variant in variants:
            with _patched_auth(), patched_pipeline(extracted_company_name=variant):
                response = client.post(
                    "/analyze",
                    data={"company_text": "content", "startup_id": str(startup_id)},
                    headers=_auth_headers(USER_A),
                )
            expect(response.status_code == 200, f"Expected 200 for variant {variant!r}: {response.text}")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM startups")).scalar()
            distinct_startup_ids = connection.execute(
                text("SELECT DISTINCT startup_id FROM analyses WHERE startup_id = :s"),
                {"s": startup_id},
            ).scalars().all()

        expect(after == before, f"No new startup from any name variant, before={before} after={after}")
        expect(distinct_startup_ids == [startup_id], "All three re-analyses must resolve to the exact same startup_id")
    finally:
        _cleanup()


def test_existing_canonical_name_is_not_overwritten() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("PreserveCanonical")
    try:
        _grant_membership(USER_A, startup_id)

        with _patched_auth(), patched_pipeline(extracted_company_name=f"{TEST_PREFIX} PreserveCanonical Renamed LLC"):
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        with engine.begin() as connection:
            canonical = connection.execute(
                text("SELECT canonical_name FROM startups WHERE id = :s"), {"s": startup_id}
            ).scalar()
        expect(
            canonical == f"{TEST_PREFIX} PreserveCanonical",
            f"canonical_name must never change from a re-analysis, got {canonical!r}",
        )
    finally:
        _cleanup()


def test_persisted_analysis_receives_exact_authoritative_startup_id() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("ExactId")
    try:
        _grant_membership(USER_A, startup_id)

        with _patched_auth(), patched_pipeline():
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        with engine.begin() as connection:
            row = connection.execute(
                text("SELECT startup_id, company_name FROM analyses WHERE startup_id = :s ORDER BY id DESC LIMIT 1"),
                {"s": startup_id},
            ).mappings().first()
        expect(row["startup_id"] == startup_id, "Persisted startup_id must be exact")
        expect(row["company_name"] == f"{TEST_PREFIX} ExactId", "Persisted company_name must be the canonical_name, not the extracted variant")
    finally:
        _cleanup()


# --- 7-16: authorization boundary ---------------------------------------------


def test_member_can_reanalyze_their_startup() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("MemberOwn")
    try:
        _grant_membership(USER_A, startup_id)

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(len(call_log) == 1, "Pipeline must run for an authorized member")
    finally:
        _cleanup()


def test_non_member_cannot_reanalyze_another_startup() -> None:
    _ensure_test_users()
    startup_a = _make_canonical_startup("MineNotB_A")
    startup_b = _make_canonical_startup("MineNotB_B")
    try:
        _grant_membership(USER_A, startup_a)

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_b)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must NEVER run for an unauthorized startup_id")
    finally:
        _cleanup()


def test_saved_startup_does_not_authorize_reanalysis() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("SavedNotMember")
    try:
        save_startup_for_user(USER_A, startup_id)

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for a merely-saved startup")
    finally:
        _cleanup()


def test_pending_claim_does_not_authorize_reanalysis() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("PendingClaimNotMember")
    try:
        with _patched_auth(admin_ids=[ADMIN_USER]):
            client.post(
                "/startup-claims",
                json={"startup_id": startup_id, "justification": "x"},
                headers=_auth_headers(USER_A),
            )

            with patched_pipeline() as call_log:
                response = client.post(
                    "/analyze",
                    data={"company_text": "content", "startup_id": str(startup_id)},
                    headers=_auth_headers(USER_A),
                )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for a merely-pending claim")
    finally:
        _cleanup()


def test_approved_historical_claim_without_membership_does_not_authorize() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("ApprovedNoMembership")
    try:
        with _patched_auth(admin_ids=[ADMIN_USER]):
            submitted = client.post(
                "/startup-claims",
                json={"startup_id": startup_id, "justification": "x"},
                headers=_auth_headers(USER_A),
            )
            claim_id = submitted.json()["id"]
            approved = client.post(f"/admin/startup-claims/{claim_id}/approve", headers=_auth_headers(ADMIN_USER))
            expect(approved.status_code == 200, f"Approval failed: {approved.text}")

            # Simulate the membership later being removed (no removal
            # feature exists yet -- same documented limitation as Phase
            # 7.1C/7.2's own tests) while the claim row stays 'approved'.
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM startup_memberships WHERE user_id = :u AND startup_id = :s"),
                    {"u": USER_A, "s": startup_id},
                )

            with patched_pipeline() as call_log:
                response = client.post(
                    "/analyze",
                    data={"company_text": "content", "startup_id": str(startup_id)},
                    headers=_auth_headers(USER_A),
                )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for an approved-but-removed membership")
    finally:
        _cleanup()


def test_modeled_venture_does_not_authorize_reanalysis() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("VentureNotMember")
    try:
        create_modeled_venture(
            user_id=USER_A, name="Some idea", description=None, industry=None,
            business_model=None, target_customer=None, stage=None,
            assumptions={}, model_result=None,
        )

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for a modeled-venture-only user")
    finally:
        _cleanup()


def test_signed_out_founder_targeted_request_fails() -> None:
    startup_id = _make_canonical_startup("SignedOut")
    try:
        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
            )
        expect(response.status_code == 401, f"Expected 401, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for a signed-out request")
    finally:
        _cleanup()


def test_invalid_startup_id_fails_before_pipeline() -> None:
    _ensure_test_users()
    try:
        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": "999999999"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run for a nonexistent startup_id")
    finally:
        _cleanup()


def test_membership_removed_before_submission_blocks_reanalysis() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("RemovedBeforeSubmit")
    try:
        _grant_membership(USER_A, startup_id)

        # Founder "opened Analyze" while still a member...
        with _patched_auth():
            still_member = client.get(f"/founder/startups/{startup_id}", headers=_auth_headers(USER_A))
        expect(still_member.status_code == 200, "Sanity: must start out authorized")

        # ...then membership is removed before they actually submit.
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM startup_memberships WHERE user_id = :u AND startup_id = :s"),
                {"u": USER_A, "s": startup_id},
            )

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must never run once membership has been removed")
    finally:
        _cleanup()


def test_failed_founder_targeted_analysis_creates_nothing() -> None:
    _ensure_test_users()
    startup_a = _make_canonical_startup("FailedNothingA")
    startup_b = _make_canonical_startup("FailedNothingB")
    try:
        _grant_membership(USER_A, startup_a)

        with engine.begin() as connection:
            startups_before = connection.execute(text("SELECT count(*) FROM startups")).scalar()
            analyses_before = connection.execute(text("SELECT count(*) FROM analyses")).scalar()

        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_b)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 404, f"Expected 404, got {response.status_code}")
        expect(len(call_log) == 0, "Pipeline must not run")

        with engine.begin() as connection:
            startups_after = connection.execute(text("SELECT count(*) FROM startups")).scalar()
            analyses_after = connection.execute(text("SELECT count(*) FROM analyses")).scalar()

        expect(startups_after == startups_before, "A failed founder-targeted request must create zero startups")
        expect(analyses_after == analyses_before, "A failed founder-targeted request must create zero analyses")
    finally:
        _cleanup()


# --- 18: existing analyses remain unchanged -----------------------------------


def test_existing_analyses_remain_unchanged() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("Untouched")
    try:
        _grant_membership(USER_A, startup_id)

        with engine.begin() as connection:
            original = connection.execute(
                text("SELECT id, company_text, methodology FROM analyses WHERE startup_id = :s ORDER BY id ASC LIMIT 1"),
                {"s": startup_id},
            ).mappings().first()

        with _patched_auth(), patched_pipeline():
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        with engine.begin() as connection:
            still_there = connection.execute(
                text("SELECT id, company_text FROM analyses WHERE id = :id"), {"id": original["id"]}
            ).mappings().first()
        expect(still_there is not None, "The original analysis row must still exist")
        expect(still_there["company_text"] == original["company_text"], "The original analysis must never be rewritten")
    finally:
        _cleanup()


# --- 19: normal /analyze behavior remains functional --------------------------


def test_normal_analyze_behavior_remains_functional() -> None:
    _ensure_test_users()
    try:
        with _patched_auth(), patched_pipeline() as call_log:
            response = client.post(
                "/analyze",
                data={"company_text": "A normal public analysis, no startup_id at all."},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")
        expect(len(call_log) == 1, "Normal analysis must still run the pipeline exactly once")
        body = response.json()
        expect("methodology" in body and "context" in body, "Response shape must be unchanged")
    finally:
        _cleanup()


# --- 20: no new startup_memberships write path --------------------------------


def test_reanalysis_creates_no_membership_write_path() -> None:
    _ensure_test_users()
    startup_id = _make_canonical_startup("NoMembershipWrite")
    try:
        _grant_membership(USER_A, startup_id)

        with engine.begin() as connection:
            before = connection.execute(text("SELECT count(*) FROM startup_memberships")).scalar()

        with _patched_auth(), patched_pipeline():
            response = client.post(
                "/analyze",
                data={"company_text": "content", "startup_id": str(startup_id)},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Expected 200: {response.text}")

        with engine.begin() as connection:
            after = connection.execute(text("SELECT count(*) FROM startup_memberships")).scalar()
        expect(after == before, "Re-analysis must never create/modify a startup_memberships row")
    finally:
        _cleanup()


def test_exactly_one_membership_insert_path_still_exists() -> None:
    """Static re-audit (same technique as
    test_startup_membership.py::test_exactly_one_membership_insert_path_exists):
    Phase 7.2.1 touches app/api.py and app/database/db.py but must never
    add a second `INSERT INTO startup_memberships` -- the only one
    remains approve_startup_claim()."""
    import pathlib
    import re

    app_dir = pathlib.Path(__file__).resolve().parent.parent
    insert_pattern = re.compile(r"INSERT\s+INTO\s+startup_memberships", re.IGNORECASE)
    def_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(")

    matches: list[tuple[pathlib.Path, int, str]] = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        lines = path.read_text().splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = insert_pattern.search(line)
            if match and "#" in line[: match.start()]:
                continue
            if match:
                enclosing_function = "<module level>"
                for prior_line in reversed(lines[:line_number - 1]):
                    def_match = def_pattern.match(prior_line)
                    if def_match:
                        enclosing_function = def_match.group(1)
                        break
                matches.append((path, line_number, enclosing_function))

    locations = [f"{path.name}:{line_number} (in {fn})" for path, line_number, fn in matches]
    expect(len(matches) == 1, f"Expected exactly one INSERT INTO startup_memberships, found {len(matches)}: {locations}")
    expect(
        matches[0][0].name == "db.py" and matches[0][2] == "approve_startup_claim",
        f"The one INSERT must still live inside db.py's approve_startup_claim(); found {locations}",
    )


TESTS = [
    test_normal_analysis_without_startup_id_uses_get_or_create,
    test_authorized_reanalysis_uses_supplied_startup_id,
    test_founder_reanalysis_does_not_create_another_startup,
    test_extracted_company_name_variation_cannot_create_another_startup,
    test_existing_canonical_name_is_not_overwritten,
    test_persisted_analysis_receives_exact_authoritative_startup_id,
    test_member_can_reanalyze_their_startup,
    test_non_member_cannot_reanalyze_another_startup,
    test_saved_startup_does_not_authorize_reanalysis,
    test_pending_claim_does_not_authorize_reanalysis,
    test_approved_historical_claim_without_membership_does_not_authorize,
    test_modeled_venture_does_not_authorize_reanalysis,
    test_signed_out_founder_targeted_request_fails,
    test_invalid_startup_id_fails_before_pipeline,
    test_membership_removed_before_submission_blocks_reanalysis,
    test_failed_founder_targeted_analysis_creates_nothing,
    test_existing_analyses_remain_unchanged,
    test_normal_analyze_behavior_remains_functional,
    test_reanalysis_creates_no_membership_write_path,
    test_exactly_one_membership_insert_path_still_exists,
]


def main() -> None:
    print("\nPhase 7.2.1 -- Deterministic Founder Re-analysis tests")
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
