"""
Regression tests for Idea Lab / Venture Simulator V1 --
app/ai/vps_scoring.py, app/ai/vps_guidance.py, app/database/db.py's
modeled_ventures CRUD functions, and the /ventures* endpoints in
app/api.py.

Two layers of coverage, matching test_compare.py's/test_discovery.py's
own convention:
- Pure unit tests against compute_vps()/generate_guidance() directly --
  no I/O, no auth needed, since these are deterministic functions of
  their input.
- API-layer tests through TestClient, reusing the exact same local-RSA-
  keypair JWT-mocking harness as test_backend_authentication.py (no live
  Clerk dependency), covering auth/ownership/isolation.

Every DB row created here uses a distinctive zztest_idealab_* user-id
prefix, cleaned up in a finally block even on failure. No test here makes
an LLM/Tavily call -- VPS scoring is entirely deterministic Python.

Run with:
    python -m app.tests.test_idea_lab
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.ai.vps_scoring import compute_vps
from app.ai.vps_guidance import generate_guidance
from app.database.db import engine, get_rankings, discover_startups

USER_A = "zztest_idealab_user_a"
USER_B = "zztest_idealab_user_b"

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


client = TestClient(api.app)


# --- JWT mocking harness (mirrors test_backend_authentication.py) ---------


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(_public_key)


def _make_token(sub: str, exp_delta: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": TEST_ISSUER,
        "azp": TEST_AZP,
        "iat": now,
        "exp": now + exp_delta,
    }
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


SAMPLE_ASSUMPTIONS = {
    "target_customer": "small construction companies",
    "market": {"estimated_market_size": "Large", "competition_intensity": "Medium"},
    "problem_solution": {
        "problem_statement": "Manual AR is slow",
        "solution_description": "AI automation",
        "differentiation": "Purpose-built for construction billing workflows",
    },
    "founder": {
        "founder_count": 2,
        "relevant_domain_experience_years": 3,
        "has_technical_cofounder": True,
        "has_business_cofounder": False,
    },
    "gtm": {"primary_acquisition_strategy": "Outbound", "expected_cac": 900},
    "economics": {"pricing_model": "Subscription", "price_point": 400, "expected_gross_margin_pct": 78},
    "validation": {"customer_interviews": 6, "waitlist_signups": 0, "paying_customers": 0, "monthly_revenue": None},
    "capital": {"starting_capital": 40000, "monthly_burn": 18000},
}


def _create_venture_body(name="ZZTest Idea Lab Venture", assumptions=None):
    return {
        "name": name,
        "description": "Test venture description.",
        "industry": "Construction Tech",
        "business_model": "Subscription",
        "target_customer": "small construction companies",
        "stage": "Researching",
        "assumptions": assumptions if assumptions is not None else SAMPLE_ASSUMPTIONS,
    }


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in (USER_A, USER_B):
            connection.execute(
                text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"),
                {"id": user_id},
            )


def _cleanup() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"),
            {"ids": [USER_A, USER_B]},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"),
            {"ids": [USER_A, USER_B]},
        )


# --- Pure scoring engine tests (no auth, no I/O) ----------------------------


def test_identical_inputs_produce_identical_vps() -> None:
    result1 = compute_vps(SAMPLE_ASSUMPTIONS)
    result2 = compute_vps(SAMPLE_ASSUMPTIONS)
    expect(result1 == result2, "compute_vps must be a pure function -- identical input must give identical output")


def test_changing_relevant_assumption_changes_appropriate_category() -> None:
    baseline = compute_vps(SAMPLE_ASSUMPTIONS)
    baseline_validation = next(c for c in baseline["categories"] if c["key"] == "validation")

    stronger = dict(SAMPLE_ASSUMPTIONS)
    stronger["validation"] = {"customer_interviews": 30, "waitlist_signups": 200, "paying_customers": 10, "monthly_revenue": 5000}
    updated = compute_vps(stronger)
    updated_validation = next(c for c in updated["categories"] if c["key"] == "validation")

    expect(
        updated_validation["score"] > baseline_validation["score"],
        f"Stronger validation assumptions must raise the Validation category score ({baseline_validation['score']} -> {updated_validation['score']})",
    )
    expect(updated["vps"] > baseline["vps"], "Overall VPS must rise when validation strengthens")


def test_irrelevant_assumption_does_not_alter_unrelated_category() -> None:
    baseline = compute_vps(SAMPLE_ASSUMPTIONS)
    baseline_validation = next(c for c in baseline["categories"] if c["key"] == "validation")

    changed_founder = dict(SAMPLE_ASSUMPTIONS)
    changed_founder["founder"] = {
        "founder_count": 5,
        "relevant_domain_experience_years": 15,
        "has_technical_cofounder": True,
        "has_business_cofounder": True,
    }
    updated = compute_vps(changed_founder)
    updated_validation = next(c for c in updated["categories"] if c["key"] == "validation")

    expect(
        updated_validation["score"] == baseline_validation["score"],
        "Changing founder assumptions must never alter the Validation category score",
    )


def test_pure_idea_has_no_fabricated_vps() -> None:
    result = compute_vps({})
    expect(result["vps"] is None, "A venture with zero assumptions must have VPS None, never a fabricated number")
    expect(
        all(c["score"] is None for c in result["categories"]),
        "Every category must be Unavailable (None) for a venture with zero assumptions",
    )


def test_unavailable_pillar_never_defaults_to_zero() -> None:
    # Only validation provided -- every other category must stay None,
    # not silently become 0 and drag down a fabricated overall average
    # incorrectly (it should instead be EXCLUDED via renormalization).
    result = compute_vps({"validation": {"customer_interviews": 25, "paying_customers": 5, "waitlist_signups": 100, "monthly_revenue": 2000}})
    non_validation = [c for c in result["categories"] if c["key"] != "validation"]
    expect(
        all(c["score"] is None for c in non_validation),
        "Categories with no supporting assumptions must stay Unavailable (None), never default to 0",
    )
    expect(result["vps"] is not None, "VPS should still compute from the one available category")


def test_assumptions_preserve_unknown_values() -> None:
    sparse = {"target_customer": "someone", "market": {"estimated_market_size": None, "competition_intensity": None}}
    result = compute_vps(sparse)
    market = next(c for c in result["categories"] if c["key"] == "market_potential")
    expect(market["score"] is None, "A market category with no real size/competition data must remain Unavailable")


def test_assumption_vs_observation_provenance_is_structural() -> None:
    """Provenance is structural (see vps_scoring.py's own docstring): every
    field under `validation` is a founder-reported observation; every
    other top-level group is a modeled assumption. This test locks that
    structural boundary in place."""
    from app.models.idea_lab import VentureAssumptions

    fields = set(VentureAssumptions.model_fields.keys())
    expect("validation" in fields, "VentureAssumptions must have a distinct `validation` (observation) group")

    assumption_groups = fields - {"validation", "target_customer"}
    expect(
        assumption_groups == {"market", "problem_solution", "founder", "gtm", "economics", "capital"},
        f"Unexpected assumption groups: {assumption_groups}",
    )


def test_guidance_frames_validation_gap_as_expected_not_failure() -> None:
    result = compute_vps(SAMPLE_ASSUMPTIONS)
    guidance = generate_guidance(SAMPLE_ASSUMPTIONS, result)
    expect(
        any("expected at the idea stage" in gap for gap in guidance["validation_gaps"]),
        "Validation gaps must be framed as expected-at-this-stage, not as a failure",
    )


# --- 1: creation requires auth ----------------------------------------------


def test_venture_creation_requires_auth() -> None:
    with _patched_auth():
        response = client.post("/ventures", json=_create_venture_body())
        expect(response.status_code == 401, f"Expected 401, got {response.status_code}")


# --- 23: all Idea Lab endpoints remain private ------------------------------


def test_all_idea_lab_endpoints_require_auth() -> None:
    with _patched_auth():
        expect(client.get("/ventures").status_code == 401, "GET /ventures must require auth")
        expect(client.get("/ventures/1").status_code == 401, "GET /ventures/{id} must require auth")
        expect(client.put("/ventures/1", json=_create_venture_body()).status_code == 401, "PUT must require auth")
        expect(client.delete("/ventures/1").status_code == 401, "DELETE must require auth")
        expect(
            client.post("/ventures/scenario-compare", json={"current_assumptions": {}, "modified_assumptions": {}}).status_code == 401,
            "scenario-compare must require auth",
        )


# --- 2: venture belongs to authenticated user -------------------------------


def test_venture_belongs_to_authenticated_user() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            response = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A))
            expect(response.status_code == 200, f"Create failed: {response.text}")
            venture_id = response.json()["id"]

            with engine.begin() as connection:
                row = connection.execute(
                    text("SELECT user_id FROM modeled_ventures WHERE id = :id"), {"id": venture_id}
                ).mappings().first()

            expect(row["user_id"] == USER_A, f"Expected owner {USER_A}, got {row['user_id']!r}")
    finally:
        _cleanup()


# --- 3-5: cross-user isolation -----------------------------------------------


def test_user_cannot_access_another_users_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            created = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A)).json()
            venture_id = created["id"]

            response = client.get(f"/ventures/{venture_id}", headers=_auth_headers(USER_B))
            expect(response.status_code == 404, f"Expected 404 for another user's venture, got {response.status_code}")
    finally:
        _cleanup()


def test_user_cannot_modify_another_users_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            created = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A)).json()
            venture_id = created["id"]

            response = client.put(
                f"/ventures/{venture_id}",
                json=_create_venture_body(name="Hijacked name"),
                headers=_auth_headers(USER_B),
            )
            expect(response.status_code == 404, f"Expected 404, got {response.status_code}")

            with engine.begin() as connection:
                row = connection.execute(
                    text("SELECT name FROM modeled_ventures WHERE id = :id"), {"id": venture_id}
                ).mappings().first()
            expect(row["name"] != "Hijacked name", "USER_B must not be able to rename USER_A's venture")
    finally:
        _cleanup()


def test_user_cannot_delete_another_users_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            created = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A)).json()
            venture_id = created["id"]

            response = client.delete(f"/ventures/{venture_id}", headers=_auth_headers(USER_B))
            expect(response.status_code == 404, f"Expected 404, got {response.status_code}")

            still_there = client.get(f"/ventures/{venture_id}", headers=_auth_headers(USER_A))
            expect(still_there.status_code == 200, "USER_A's venture must survive USER_B's delete attempt")
    finally:
        _cleanup()


# --- 6-10: no canonical/ownership side effects ------------------------------


def test_venture_creation_has_no_canonical_side_effects() -> None:
    _ensure_test_users()
    try:
        with engine.begin() as connection:
            before_startups = connection.execute(text("SELECT COUNT(*) FROM startups")).scalar()
            before_analyses = connection.execute(text("SELECT COUNT(*) FROM analyses")).scalar()
            before_memberships = connection.execute(text("SELECT COUNT(*) FROM startup_memberships")).scalar()
            before_saved = connection.execute(text("SELECT COUNT(*) FROM saved_startups")).scalar()

        with _patched_auth():
            response = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A))
            expect(response.status_code == 200, f"Create failed: {response.text}")

        with engine.begin() as connection:
            after_startups = connection.execute(text("SELECT COUNT(*) FROM startups")).scalar()
            after_analyses = connection.execute(text("SELECT COUNT(*) FROM analyses")).scalar()
            after_memberships = connection.execute(text("SELECT COUNT(*) FROM startup_memberships")).scalar()
            after_saved = connection.execute(text("SELECT COUNT(*) FROM saved_startups")).scalar()

        expect(after_startups == before_startups, "Venture creation must never create a startups row")
        expect(after_analyses == before_analyses, "Venture creation must never create an analyses row")
        expect(after_memberships == before_memberships, "Venture creation must never create a startup_membership")
        expect(after_saved == before_saved, "Venture creation must never create a saved_startup")
    finally:
        _cleanup()


def test_vps_never_stored_as_sps() -> None:
    """The computed model_result JSONB must never be written into
    analyses.methodology, and must use the key "vps", never
    "startup_intelligence_score" (SPS's own field name)."""
    _ensure_test_users()
    try:
        with _patched_auth():
            response = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A))
            body = response.json()

        expect("vps" in body["model_result"], "model_result must use the key 'vps'")
        expect(
            "startup_intelligence_score" not in body["model_result"],
            "model_result must never use SPS's own field name",
        )

        with engine.begin() as connection:
            analyses_with_venture_name = connection.execute(
                text("SELECT COUNT(*) FROM analyses WHERE company_name = :name"),
                {"name": _create_venture_body()["name"]},
            ).scalar()
        expect(analyses_with_venture_name == 0, "A modeled venture must never appear as an analyses row")
    finally:
        _cleanup()


# --- 11-12: never appears in Rankings/Discovery -----------------------------


def test_modeled_venture_never_appears_in_rankings_or_discovery() -> None:
    _ensure_test_users()
    try:
        venture_name = "ZZTest Idea Lab Rankings Check"
        with _patched_auth():
            response = client.post("/ventures", json=_create_venture_body(name=venture_name), headers=_auth_headers(USER_A))
            expect(response.status_code == 200, f"Create failed: {response.text}")

        rankings = get_rankings()
        expect(
            all(row["company_name"] != venture_name for row in rankings),
            "A modeled venture must never appear in Rankings",
        )

        discovery = discover_startups()
        expect(
            all(row["company_name"] != venture_name for row in discovery),
            "A modeled venture must never appear in Discovery",
        )
    finally:
        _cleanup()


# --- 18: scenario comparison preserves the original ------------------------


def test_scenario_comparison_preserves_original_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            created = client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A)).json()
            venture_id = created["id"]

            hypothetical = dict(SAMPLE_ASSUMPTIONS)
            hypothetical["validation"] = {"customer_interviews": 100, "waitlist_signups": 500, "paying_customers": 50, "monthly_revenue": 20000}

            scenario_response = client.post(
                "/ventures/scenario-compare",
                json={"current_assumptions": SAMPLE_ASSUMPTIONS, "modified_assumptions": hypothetical},
                headers=_auth_headers(USER_A),
            )
            expect(scenario_response.status_code == 200, f"Scenario compare failed: {scenario_response.text}")
            expect(
                scenario_response.json()["modified"]["vps"] > scenario_response.json()["current"]["vps"],
                "The hypothetical scenario should score higher given much stronger validation",
            )

            reopened = client.get(f"/ventures/{venture_id}", headers=_auth_headers(USER_A)).json()
            expect(
                reopened["assumptions"]["validation"]["paying_customers"] == 0,
                "scenario-compare must never overwrite the venture's persisted assumptions",
            )
    finally:
        _cleanup()


# --- 19: invalid numeric inputs fail cleanly --------------------------------


def test_invalid_numeric_inputs_fail_cleanly() -> None:
    with _patched_auth():
        bad_assumptions = dict(SAMPLE_ASSUMPTIONS)
        bad_assumptions["validation"] = {"customer_interviews": -5, "waitlist_signups": 0, "paying_customers": 0, "monthly_revenue": None}
        response = client.post(
            "/ventures", json=_create_venture_body(assumptions=bad_assumptions), headers=_auth_headers(USER_A)
        )
        expect(response.status_code == 422, f"Negative customer_interviews should be rejected, got {response.status_code}")


# --- 20: API never accepts a client-controlled user_id ----------------------


def test_api_never_accepts_client_controlled_user_id() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            body = _create_venture_body()
            body["user_id"] = USER_B  # not a real field -- must be ignored, not honored
            response = client.post("/ventures", json=body, headers=_auth_headers(USER_A))
            expect(response.status_code == 200, f"Create failed: {response.text}")

            with engine.begin() as connection:
                row = connection.execute(
                    text("SELECT user_id FROM modeled_ventures WHERE id = :id"), {"id": response.json()["id"]}
                ).mappings().first()

            expect(
                row["user_id"] == USER_A,
                f"A client-supplied user_id field must be ignored; expected {USER_A}, got {row['user_id']!r}",
            )
    finally:
        _cleanup()


# --- 21-22: old canonical behavior + public endpoints unaffected ------------


def test_canonical_behavior_and_public_endpoints_unaffected() -> None:
    before_rankings = len(get_rankings())
    before_discovery = len(discover_startups())

    _ensure_test_users()
    try:
        with _patched_auth():
            client.post("/ventures", json=_create_venture_body(), headers=_auth_headers(USER_A))

        expect(len(get_rankings()) == before_rankings, "Rankings population must be unaffected by Idea Lab activity")
        expect(len(discover_startups()) == before_discovery, "Discovery population must be unaffected by Idea Lab activity")

        expect(client.get("/rankings").status_code == 200, "/rankings must remain public")
        expect(client.get("/discover").status_code == 200, "/discover must remain public")
        expect(client.get("/compare", params={"startups": "1,2"}).status_code in (200, 400), "/compare must remain public")
    finally:
        _cleanup()


TESTS = [
    test_identical_inputs_produce_identical_vps,
    test_changing_relevant_assumption_changes_appropriate_category,
    test_irrelevant_assumption_does_not_alter_unrelated_category,
    test_pure_idea_has_no_fabricated_vps,
    test_unavailable_pillar_never_defaults_to_zero,
    test_assumptions_preserve_unknown_values,
    test_assumption_vs_observation_provenance_is_structural,
    test_guidance_frames_validation_gap_as_expected_not_failure,
    test_venture_creation_requires_auth,
    test_all_idea_lab_endpoints_require_auth,
    test_venture_belongs_to_authenticated_user,
    test_user_cannot_access_another_users_venture,
    test_user_cannot_modify_another_users_venture,
    test_user_cannot_delete_another_users_venture,
    test_venture_creation_has_no_canonical_side_effects,
    test_vps_never_stored_as_sps,
    test_modeled_venture_never_appears_in_rankings_or_discovery,
    test_scenario_comparison_preserves_original_venture,
    test_invalid_numeric_inputs_fail_cleanly,
    test_api_never_accepts_client_controlled_user_id,
    test_canonical_behavior_and_public_endpoints_unaffected,
]


def main() -> None:
    print("\nIdea Lab / Venture Simulator V1 tests")
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

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
