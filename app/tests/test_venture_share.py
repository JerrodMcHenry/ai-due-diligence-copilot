"""
Regression tests for Phase 27 -- Shareable Venture Snapshot V1: the four
share_* columns on modeled_ventures (app/database/db.py), its Pydantic
contracts (app/models/idea_lab.py), and the three endpoints
(GET/PUT /ventures/{id}/share, GET /ventures/{id}/share/preview,
GET /ventures/share/{public_id}) in app/api.py.

Same JWT-mocking harness, TestClient, and zztest_* user-id convention as
test_venture_history.py -- no live Clerk dependency, every row cleaned up
in a finally block even on failure.

The single most important thing this file proves: PRIVATE BY DEFAULT and
THE ALLOWLIST. A venture with real CAC/burn/starting-capital/gross-margin
figures and a real founder mission/capture/model-update history must
leak NONE of that through the public snapshot endpoint, whether sharing
is on or off, and regardless of the VPS/validation toggles -- verified
by asserting the exact sensitive values are absent from the raw response
text, not just absent from the typed fields a lazy test might check.

Run with:
    python -m app.tests.test_venture_share
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_share_user_a"
USER_B = "zztest_share_user_b"

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


# Deliberately loaded with real values in every sensitive field the
# directive names (Part 4/20): CAC, burn, starting capital, gross margin
# -- none of these strings must ever appear in a public snapshot payload.
SENSITIVE_MARKERS = ["31337", "$88,000", "starting_capital", "monthly_burn", "expected_cac", "expected_gross_margin_pct"]

SAMPLE_ASSUMPTIONS = {
    "target_customer": "regional medical practices",
    "market": {"estimated_market_size": "Large", "competition_intensity": "Medium"},
    "problem_solution": {
        "problem_statement": "Medical practices lose revenue to denied insurance claims.",
        "solution_description": "Automated claim-denial detection and resubmission.",
        "differentiation": "Purpose-built for regional practices, not enterprise health systems.",
    },
    "founder": {
        "founder_count": 2,
        "relevant_domain_experience_years": 6,
        "has_technical_cofounder": True,
        "has_business_cofounder": True,
    },
    "gtm": {"primary_acquisition_strategy": "Outbound to practice managers", "expected_cac": 31337},
    "economics": {"pricing_model": "Subscription", "price_point": 299, "expected_gross_margin_pct": 91},
    "validation": {
        "customer_interviews": 22,
        "waitlist_signups": 5,
        "paying_customers": 14,
        "monthly_revenue": 4186,
        "prior_monthly_revenue": None,
        "retention_pct": 92,
    },
    "capital": {"starting_capital": 88000, "monthly_burn": 12000},
}


def _create_venture_body(name="ZZTest Share Venture"):
    return {
        "name": name,
        "description": f"Private founder notes mentioning CAC $31337 and burn $88,000 that must never leak. {SENSITIVE_MARKERS}",
        "industry": "Healthtech",
        "business_model": "Subscription",
        "target_customer": "regional medical practices",
        "stage": "Validating",
        "assumptions": SAMPLE_ASSUMPTIONS,
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
            text("DELETE FROM venture_model_updates WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
            {"ids": [USER_A, USER_B]},
        )
        connection.execute(
            text("DELETE FROM venture_missions WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
            {"ids": [USER_A, USER_B]},
        )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture(user_id: str, name="ZZTest Share Venture") -> dict:
    with _patched_auth():
        response = client.post("/ventures", json=_create_venture_body(name=name), headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Venture create failed: {response.text}")
    return response.json()


def _create_mission(venture_id: int, user_id: str, **overrides) -> dict:
    body = {
        "title": "Investigate a private founder concern",
        "description": "Private description text that must never be public.",
        "mission_type": "customer_discovery",
        "related_category": "validation",
        "source": "founder_created",
        **overrides,
    }
    with _patched_auth():
        response = client.post(f"/ventures/{venture_id}/missions", json=body, headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Mission create failed: {response.text}")
    return response.json()


def _capture(venture_id: int, user_id: str, text_body: str) -> dict:
    with _patched_auth():
        response = client.post(
            f"/ventures/{venture_id}/capture",
            json={"text": text_body, "category": None},
            headers=_auth_headers(user_id),
        )
    expect(response.status_code == 200, f"Capture failed: {response.text}")
    return response.json()


def _get_share_settings(venture_id: int, user_id: str) -> dict:
    with _patched_auth():
        response = client.get(f"/ventures/{venture_id}/share", headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Get share settings failed: {response.text}")
    return response.json()


def _update_share(venture_id: int, user_id: str, enabled: bool, show_vps: bool = False, show_validation: bool = True) -> dict:
    with _patched_auth():
        response = client.put(
            f"/ventures/{venture_id}/share",
            json={"enabled": enabled, "show_vps": show_vps, "show_validation": show_validation},
            headers=_auth_headers(user_id),
        )
    expect(response.status_code == 200, f"Update share failed: {response.text}")
    return response.json()


def _get_preview(venture_id: int, user_id: str):
    with _patched_auth():
        return client.get(f"/ventures/{venture_id}/share/preview", headers=_auth_headers(user_id))


def _get_public(public_id: str):
    # Deliberately NO _patched_auth(), NO Authorization header -- this is
    # THE public route; it must work with zero auth context at all.
    return client.get(f"/ventures/share/{public_id}")


def _venture_details(venture_id: int, user_id: str) -> dict:
    with _patched_auth():
        response = client.get(f"/ventures/{venture_id}", headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Get venture failed: {response.text}")
    return response.json()


# --- A. Private by default ---------------------------------------------------


def test_new_venture_is_private_by_default() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        settings = _get_share_settings(venture["id"], USER_A)

        expect(settings["enabled"] is False, "A brand-new venture must not be shared by default")
        expect(settings["public_id"] is None, "No public id should exist until sharing is explicitly enabled")
        expect(settings["show_vps"] is False, "VPS must default to hidden")
        expect(settings["show_validation"] is True, "Validation/evidence defaults to shown (Part 2's 30-second test), but this is still gated behind explicit share activation")
    finally:
        _cleanup()


def test_disabled_venture_has_no_public_route() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        # Never enabled -- there is no public_id at all yet, so there is
        # structurally no URL to even attempt.
        settings = _get_share_settings(venture["id"], USER_A)
        expect(settings["public_id"] is None, "Never-shared venture must have no public id")
    finally:
        _cleanup()


# --- B. Explicit share activation --------------------------------------------


def test_enabling_share_generates_a_public_id() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        updated = _update_share(venture["id"], USER_A, enabled=True)

        expect(updated["enabled"] is True, "Sharing must now be enabled")
        expect(updated["public_id"] is not None and len(updated["public_id"]) >= 16, "A real, non-trivial public id must be generated")
        expect(str(venture["id"]) not in updated["public_id"], "The public id must not be (or trivially contain) the sequential venture id")
    finally:
        _cleanup()


def test_public_id_is_stable_across_disable_and_reenable() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        first = _update_share(venture["id"], USER_A, enabled=True)
        _update_share(venture["id"], USER_A, enabled=False)
        third = _update_share(venture["id"], USER_A, enabled=True)

        expect(first["public_id"] == third["public_id"], "Re-enabling must reuse the exact same public id -- Part 15's own 'URL remains stable' requirement")
    finally:
        _cleanup()


# --- C. Disable behavior ------------------------------------------------------


def test_disabling_share_makes_public_url_inaccessible() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        enabled = _update_share(venture["id"], USER_A, enabled=True)
        public_id = enabled["public_id"]

        live = _get_public(public_id)
        expect(live.status_code == 200, "Enabled snapshot must be publicly reachable")

        _update_share(venture["id"], USER_A, enabled=False)

        after_disable = _get_public(public_id)
        expect(after_disable.status_code == 404, f"A disabled snapshot's OLD public URL must stop resolving, got {after_disable.status_code}")
    finally:
        _cleanup()


def test_invalid_public_id_returns_404() -> None:
    response = _get_public("this-id-was-never-generated-by-anyone")
    expect(response.status_code == 404, "A malformed/unknown public id must 404, never 500 or leak anything")


# --- D. The allowlisted public DTO -------------------------------------------


def test_public_snapshot_contains_no_sensitive_figures() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        enabled = _update_share(venture["id"], USER_A, enabled=True, show_vps=True, show_validation=True)

        response = _get_public(enabled["public_id"])
        expect(response.status_code == 200, "Enabled snapshot must be reachable")
        raw = response.text

        for marker in SENSITIVE_MARKERS:
            expect(marker not in raw, f"Sensitive marker '{marker}' must never appear in the public snapshot payload")

        body = response.json()
        expect("description" not in body, "Raw founder description must never be a field on the public DTO at all")
        expect("assumptions" not in body, "The full assumptions blob must never be serialized to the public DTO")
    finally:
        _cleanup()


def test_public_snapshot_has_no_capture_or_history_or_actions() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        _capture(venture["id"], USER_A, "Private capture text that recipients must never see.")
        _create_mission(venture["id"], USER_A)
        enabled = _update_share(venture["id"], USER_A, enabled=True)

        response = _get_public(enabled["public_id"])
        raw = response.text

        expect("Private capture text" not in raw, "Capture text must never appear in a public snapshot")
        expect("Private description text" not in raw, "Private mission description text must never appear in a public snapshot")
        expect("Investigate a private founder concern" not in raw, "Private Action/mission titles must never appear in a public snapshot")

        body = response.json()
        for forbidden_key in ("history", "events", "missions", "actions", "captures", "fundraising", "cap_table", "safe_terms"):
            expect(forbidden_key not in body, f"'{forbidden_key}' must not be a field on the public snapshot DTO")
    finally:
        _cleanup()


def test_public_snapshot_is_the_allowlisted_shape() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        enabled = _update_share(venture["id"], USER_A, enabled=True, show_vps=True, show_validation=True)

        body = _get_public(enabled["public_id"]).json()
        allowed_keys = {
            "name", "stage", "problem_statement", "solution_description",
            "target_customer", "evidence", "current_frontier", "vps",
            "vps_categories", "updated_at",
        }
        expect(set(body.keys()) == allowed_keys, f"Public DTO must be exactly the allowlisted shape, got extra/missing keys: {set(body.keys()) ^ allowed_keys}")

        expect(body["name"] == "ZZTest Share Venture", "Name must be present")
        expect(body["problem_statement"] == SAMPLE_ASSUMPTIONS["problem_solution"]["problem_statement"], "Problem statement must be the real one")
        expect(any("14 paying customer" in e for e in body["evidence"]), "Evidence must include the real paying-customer count")
        expect(any("$299/month pricing" in e for e in body["evidence"]), "Evidence must include the real price point")
        expect(not any("gross margin" in e.lower() or "cac" in e.lower() or "burn" in e.lower() for e in body["evidence"]), "Evidence must never include margin/CAC/burn")
    finally:
        _cleanup()


# --- E. Visibility toggles ----------------------------------------------------


def test_vps_hidden_by_default_shown_when_enabled() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        hidden = _update_share(venture["id"], USER_A, enabled=True, show_vps=False)
        hidden_body = _get_public(hidden["public_id"]).json()
        expect(hidden_body["vps"] is None, "VPS must be null when show_vps is False")
        expect(hidden_body["vps_categories"] is None, "Category breakdown must be null when show_vps is False")

        shown = _update_share(venture["id"], USER_A, enabled=True, show_vps=True)
        shown_body = _get_public(shown["public_id"]).json()
        expect(shown_body["vps"] is not None, "VPS must be present when show_vps is True")
        expect(shown_body["vps_categories"] is not None and len(shown_body["vps_categories"]) > 0, "Category breakdown must be present when show_vps is True")
    finally:
        _cleanup()


def test_validation_evidence_toggle() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        hidden = _update_share(venture["id"], USER_A, enabled=True, show_validation=False)
        hidden_body = _get_public(hidden["public_id"]).json()
        expect(hidden_body["evidence"] == [], "Evidence list must be empty when show_validation is False")

        shown = _update_share(venture["id"], USER_A, enabled=True, show_validation=True)
        shown_body = _get_public(shown["public_id"]).json()
        expect(len(shown_body["evidence"]) > 0, "Evidence list must be populated when show_validation is True")
    finally:
        _cleanup()


# --- F. Current frontier ------------------------------------------------------


def test_public_frontier_matches_private_next_milestone() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        private_view = _venture_details(venture["id"], USER_A)
        expected_frontier = (private_view["model_result"] or {}).get("next_milestones", [None])[0]

        enabled = _update_share(venture["id"], USER_A, enabled=True)
        body = _get_public(enabled["public_id"]).json()

        expect(body["current_frontier"] == expected_frontier, f"Public frontier must match the private next_milestones[0], got '{body['current_frontier']}' vs '{expected_frontier}'")
    finally:
        _cleanup()


# --- G. Rename reflected safely -----------------------------------------------


def test_rename_is_reflected_in_public_snapshot() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A, name="Original Name")
        enabled = _update_share(venture["id"], USER_A, enabled=True)

        with _patched_auth():
            rename_response = client.put(
                f"/ventures/{venture['id']}",
                json={
                    "name": "Renamed Venture",
                    "description": venture["description"],
                    "industry": venture["industry"],
                    "business_model": venture["business_model"],
                    "target_customer": venture["target_customer"],
                    "stage": venture["stage"],
                    "assumptions": venture["assumptions"],
                },
                headers=_auth_headers(USER_A),
            )
        expect(rename_response.status_code == 200, f"Rename failed: {rename_response.text}")

        body = _get_public(enabled["public_id"]).json()
        expect(body["name"] == "Renamed Venture", "Public snapshot must reflect the new name (live view, not frozen)")
    finally:
        _cleanup()


# --- H. Ownership / cross-user isolation --------------------------------------


def test_other_user_cannot_read_or_change_share_settings() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)

        with _patched_auth():
            get_response = client.get(f"/ventures/{venture['id']}/share", headers=_auth_headers(USER_B))
        expect(get_response.status_code == 404, "A different user must not be able to read another founder's share settings")

        with _patched_auth():
            put_response = client.put(
                f"/ventures/{venture['id']}/share",
                json={"enabled": True, "show_vps": True, "show_validation": True},
                headers=_auth_headers(USER_B),
            )
        expect(put_response.status_code == 404, "A different user must not be able to enable sharing on another founder's venture")

        # Confirm USER_B's attempt truly had no effect.
        settings = _get_share_settings(venture["id"], USER_A)
        expect(settings["enabled"] is False, "USER_B's forged enable attempt must not have taken effect")
    finally:
        _cleanup()


# --- I. Firewalls: sharing never touches VPS/history/actions ----------------


def test_enabling_and_disabling_share_never_changes_vps_or_writes_history() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        before_vps = (venture["model_result"] or {}).get("vps")

        _update_share(venture["id"], USER_A, enabled=True, show_vps=True, show_validation=True)
        _update_share(venture["id"], USER_A, enabled=False)
        _update_share(venture["id"], USER_A, enabled=True, show_vps=False, show_validation=False)

        after = _venture_details(venture["id"], USER_A)
        after_vps = (after["model_result"] or {}).get("vps")
        expect(before_vps == after_vps, f"VPS must never change from any share operation, got {before_vps} -> {after_vps}")

        with _patched_auth():
            history_response = client.get(f"/ventures/{venture['id']}/history", headers=_auth_headers(USER_A))
        history = history_response.json()
        expect(history["model_updates_count"] == 0, "No share operation may ever write a venture_model_updates row")
        event_types = {e["event_type"] for e in history["events"]}
        expect(event_types == {"venture_created"}, f"Share operations must create no new history events at all, got {event_types}")
    finally:
        _cleanup()


def test_preview_never_requires_sharing_to_be_enabled() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        # Sharing was never enabled -- preview must still work.
        response = _get_preview(venture["id"], USER_A)
        expect(response.status_code == 200, f"Preview must work before sharing is ever enabled, got {response.status_code}: {response.text}")
        expect(response.json()["name"] == "ZZTest Share Venture", "Preview must reflect the real venture name")
    finally:
        _cleanup()


def test_preview_and_public_dto_are_byte_identical_shape() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        _update_share(venture["id"], USER_A, enabled=True, show_vps=True, show_validation=True)

        preview = _get_preview(venture["id"], USER_A).json()
        settings = _get_share_settings(venture["id"], USER_A)
        public = _get_public(settings["public_id"]).json()

        expect(set(preview.keys()) == set(public.keys()), "Preview and public DTO must be the exact same shape (Part 16)")
        expect(preview == public, "Preview and public payload must be identical when the toggles match the currently-saved settings")
    finally:
        _cleanup()


# --- J. Live evolution ---------------------------------------------------------


def test_snapshot_evolves_live_after_explicit_model_update() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        enabled = _update_share(venture["id"], USER_A, enabled=True, show_validation=True)

        before_body = _get_public(enabled["public_id"]).json()
        expect(any("14 paying customer" in e for e in before_body["evidence"]), "Must start with the real reported count")

        new_assumptions = dict(SAMPLE_ASSUMPTIONS)
        new_assumptions["validation"] = {**SAMPLE_ASSUMPTIONS["validation"], "paying_customers": 21}
        with _patched_auth():
            client.put(
                f"/ventures/{venture['id']}",
                json={
                    "name": venture["name"],
                    "description": venture["description"],
                    "industry": venture["industry"],
                    "business_model": venture["business_model"],
                    "target_customer": venture["target_customer"],
                    "stage": venture["stage"],
                    "assumptions": new_assumptions,
                },
                headers=_auth_headers(USER_A),
            )

        after_body = _get_public(enabled["public_id"]).json()
        expect(any("21 paying customer" in e for e in after_body["evidence"]), "Live-view snapshot must reflect the newly updated real evidence")
        expect(not any("14 paying customer" in e for e in after_body["evidence"]), "The stale count must no longer appear")
    finally:
        _cleanup()


TESTS = [
    test_new_venture_is_private_by_default,
    test_disabled_venture_has_no_public_route,
    test_enabling_share_generates_a_public_id,
    test_public_id_is_stable_across_disable_and_reenable,
    test_disabling_share_makes_public_url_inaccessible,
    test_invalid_public_id_returns_404,
    test_public_snapshot_contains_no_sensitive_figures,
    test_public_snapshot_has_no_capture_or_history_or_actions,
    test_public_snapshot_is_the_allowlisted_shape,
    test_vps_hidden_by_default_shown_when_enabled,
    test_validation_evidence_toggle,
    test_public_frontier_matches_private_next_milestone,
    test_rename_is_reflected_in_public_snapshot,
    test_other_user_cannot_read_or_change_share_settings,
    test_enabling_and_disabling_share_never_changes_vps_or_writes_history,
    test_preview_never_requires_sharing_to_be_enabled,
    test_preview_and_public_dto_are_byte_identical_shape,
    test_snapshot_evolves_live_after_explicit_model_update,
]


def main() -> None:
    print("\nShareable Venture Snapshot V1 -- regression tests")
    print("-" * 72)

    failures: list[str] = []
    for test in TESTS:
        name = test.__name__
        try:
            test()
            print(f"PASS  {name}")
        except Exception as error:  # noqa: BLE001
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
