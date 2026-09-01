"""
Regression tests for Phase 16 -- Founder Progress / Venture History V1:
the venture_model_updates table (app/database/db.py), its Pydantic
contracts (app/models/idea_lab.py), and GET /ventures/{id}/history
(app/api.py).

Same JWT-mocking harness and zztest_* user-id convention as
test_founder_missions.py/test_idea_lab.py -- no live Clerk dependency,
every row cleaned up in a finally block even on failure.

The single most important thing this file proves, again: the VPS
FIREWALL. Adding a mission, recording learning, and completing a mission
must never change a venture's stored VPS -- only an explicit PUT
/ventures/{id} with changed assumptions may, and that is the ONLY thing
that ever writes a venture_model_updates row.

Run with:
    python -m app.tests.test_venture_history
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_history_user_a"
USER_B = "zztest_history_user_b"

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


SAMPLE_ASSUMPTIONS = {
    "target_customer": "regional accounting firms",
    "market": {"estimated_market_size": "Medium", "competition_intensity": "Medium"},
    "problem_solution": {
        "problem_statement": "Client onboarding is manual",
        "solution_description": "Automated onboarding and document collection",
        "differentiation": "Purpose-built templates for accounting workflows",
    },
    "founder": {
        "founder_count": 2,
        "relevant_domain_experience_years": 6,
        "has_technical_cofounder": True,
        "has_business_cofounder": True,
    },
    "gtm": {"primary_acquisition_strategy": "Outbound", "expected_cac": 500},
    "economics": {"pricing_model": "Subscription", "price_point": 200, "expected_gross_margin_pct": 75},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 14, "monthly_revenue": 2800, "prior_monthly_revenue": None, "retention_pct": None},
    "capital": {"starting_capital": 100000, "monthly_burn": 8000},
}


def _create_venture_body(name="ZZTest History Venture"):
    return {
        "name": name,
        "description": "Test venture for Founder Progress / Venture History.",
        "industry": "Fintech",
        "business_model": "Subscription",
        "target_customer": "regional accounting firms",
        "stage": "Researching",
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


def _create_venture(user_id: str, name="ZZTest History Venture") -> dict:
    with _patched_auth():
        response = client.post("/ventures", json=_create_venture_body(name=name), headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Venture create failed: {response.text}")
    return response.json()


def _create_mission(venture_id: int, user_id: str, **overrides) -> dict:
    body = {
        "title": "Interview 10 potential customers",
        "description": "Learn how they solve this problem today.",
        "mission_type": "customer_discovery",
        "related_category": "validation",
        "source": "founder_created",
        **overrides,
    }
    with _patched_auth():
        response = client.post(f"/ventures/{venture_id}/missions", json=body, headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Mission create failed: {response.text}")
    return response.json()


def _get_history(venture_id: int, user_id: str) -> dict:
    with _patched_auth():
        response = client.get(f"/ventures/{venture_id}/history", headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"History fetch failed: {response.text}")
    return response.json()


def _events_of_type(history: dict, event_type: str) -> list:
    return [e for e in history["events"] if e["event_type"] == event_type]


# --- A. Brand-new venture ----------------------------------------------------


def test_new_venture_has_honest_minimal_history() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        history = _get_history(venture["id"], USER_A)

        expect(len(history["events"]) == 1, f"A brand-new venture should have exactly one event (venture_created), got {len(history['events'])}")
        expect(history["events"][0]["event_type"] == "venture_created", "The one event must be venture_created")
        expect(history["model_updates_count"] == 0, "No model updates yet")
        expect(history["actions_completed"] == 0, "No actions completed yet")
        expect(history["strongest_improvement"] is None, "No improvement to report yet -- must not be fabricated")
        expect(history["current_vps"] == venture["model_result"]["vps"], "current_vps must match the venture's actual VPS")
    finally:
        _cleanup()


# --- B. Action started (added) ------------------------------------------------


def test_action_added_appears_and_vps_unchanged() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]

        mission = _create_mission(venture["id"], USER_A)
        history = _get_history(venture["id"], USER_A)

        action_events = _events_of_type(history, "action_added")
        expect(len(action_events) == 1, "Expected exactly one action_added event")
        expect(action_events[0]["mission_id"] == mission["id"], "action_added event must reference the real mission id")
        expect(action_events[0]["title"] == mission["title"], "action_added event title must match the mission title")
        expect(history["current_vps"] == vps_before, "Adding an action must never change VPS")
    finally:
        _cleanup()


# --- C. Learning recorded -----------------------------------------------------


def test_learning_recorded_preserves_verbatim_text_and_vps_unchanged() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]
        mission = _create_mission(venture["id"], USER_A)

        learning_text = "9 of 12 clinics already pay a consultant to recover denied claims."
        with _patched_auth():
            response = client.post(
                f"/ventures/{venture['id']}/missions/{mission['id']}/learning",
                json={"learning_summary": learning_text},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Recording learning failed: {response.text}")

        history = _get_history(venture["id"], USER_A)
        learning_events = _events_of_type(history, "learning_recorded")
        expect(len(learning_events) == 1, "Expected exactly one learning_recorded event")
        expect(learning_events[0]["description"] == learning_text, "Founder-written learning must be preserved verbatim")
        expect(learning_events[0]["mission_id"] == mission["id"], "learning_recorded event must reference the real mission id")
        expect(history["current_vps"] == vps_before, "Recording learning must never change VPS")
    finally:
        _cleanup()


# --- D. Action completed ------------------------------------------------------


def test_action_completed_appears_and_vps_unchanged() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]
        mission = _create_mission(venture["id"], USER_A)

        with _patched_auth():
            response = client.patch(
                f"/ventures/{venture['id']}/missions/{mission['id']}/status",
                json={"status": "completed"},
                headers=_auth_headers(USER_A),
            )
        expect(response.status_code == 200, f"Completing mission failed: {response.text}")

        history = _get_history(venture["id"], USER_A)
        completed_events = _events_of_type(history, "action_completed")
        expect(len(completed_events) == 1, "Expected exactly one action_completed event")
        expect(completed_events[0]["mission_id"] == mission["id"], "action_completed event must reference the real mission id")
        expect(history["actions_completed"] == 1, "actions_completed summary must count this")
        expect(history["current_vps"] == vps_before, "Completing an action must never change VPS")
    finally:
        _cleanup()


# --- E. Positive model update --------------------------------------------------


def test_positive_model_update_shows_before_after_and_raises_vps() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]
        mission = _create_mission(venture["id"], USER_A, related_category="validation", mission_type="pricing")

        stronger_assumptions = dict(SAMPLE_ASSUMPTIONS)
        # 14 -> 60 crosses a real evidence-anchor tier boundary in
        # _validation_commercial_scale() (10-49 "solid" -> 50-99
        # "strong"), guaranteeing a genuine category-score change --
        # 14 -> 19 stays within the same tier and correctly produces NO
        # reported change, which is honest but not what this test needs
        # to exercise.
        stronger_assumptions["validation"] = {**SAMPLE_ASSUMPTIONS["validation"], "paying_customers": 60}
        body = {**_create_venture_body(), "assumptions": stronger_assumptions, "related_mission_id": mission["id"]}
        with _patched_auth():
            response = client.put(f"/ventures/{venture['id']}", json=body, headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Model update failed: {response.text}")
        updated = response.json()
        vps_after = updated["model_result"]["vps"]

        history = _get_history(venture["id"], USER_A)
        model_events = _events_of_type(history, "model_updated")
        expect(len(model_events) == 1, "Expected exactly one model_updated event")
        event = model_events[0]
        expect(event["before_vps"] == vps_before, f"before_vps must be the real prior VPS ({vps_before}), got {event['before_vps']}")
        expect(event["after_vps"] == vps_after, f"after_vps must be the real new VPS ({vps_after}), got {event['after_vps']}")
        expect(event["mission_id"] == mission["id"], "The model_updated event must link back to the mission that triggered it")
        expect(len(event["category_changes"]) > 0, "Expected at least one category to show a real before/after change")

        validation_change = next((c for c in event["category_changes"] if c["key"] == "validation"), None)
        expect(validation_change is not None, "Validation category should be among the reported changes")
        expect(validation_change["after"] > validation_change["before"], "Validation should have genuinely increased")
        expect(history["model_updates_count"] == 1, "model_updates_count summary must count this")
        expect(history["strongest_improvement"] is not None, "A real positive change should populate strongest_improvement")
    finally:
        _cleanup()


# --- F. Negative model update ---------------------------------------------------


def test_negative_model_update_displayed_honestly() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]

        weaker_assumptions = dict(SAMPLE_ASSUMPTIONS)
        weaker_assumptions["validation"] = {**SAMPLE_ASSUMPTIONS["validation"], "paying_customers": 1, "monthly_revenue": 100}
        body = {**_create_venture_body(), "assumptions": weaker_assumptions}
        with _patched_auth():
            response = client.put(f"/ventures/{venture['id']}", json=body, headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Model update failed: {response.text}")
        updated = response.json()
        vps_after = updated["model_result"]["vps"]
        expect(vps_after < vps_before, f"Fixture assumption: this change should genuinely lower VPS ({vps_before} -> {vps_after})")

        history = _get_history(venture["id"], USER_A)
        model_events = _events_of_type(history, "model_updated")
        expect(len(model_events) == 1, "Expected exactly one model_updated event")
        expect(model_events[0]["before_vps"] == vps_before, "Negative change must still show the real before value")
        expect(model_events[0]["after_vps"] == vps_after, "Negative change must still show the real, lower after value -- never hidden or floored")
        expect(model_events[0]["event_type"] == "model_updated", "A negative change is still labeled model_updated, not some separate punitive event type")
    finally:
        _cleanup()


# --- G. Model update with no VPS movement ---------------------------------------


def test_model_update_with_no_vps_movement_still_recorded_honestly() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        vps_before = venture["model_result"]["vps"]

        # Change the WORDING of an already-truthy field
        # (economics.pricing_model) that only ever contributes a flat
        # presence bonus to Economic Potential ("if pricing_model:" --
        # see vps_scoring.py's own _score_economic_potential) -- a real,
        # persisted assumptions change with an honestly UNCHANGED VPS,
        # since it was already truthy before and after.
        same_score_assumptions = {
            **SAMPLE_ASSUMPTIONS,
            "economics": {**SAMPLE_ASSUMPTIONS["economics"], "pricing_model": "Monthly subscription, billed annually"},
        }
        body = {**_create_venture_body(), "assumptions": same_score_assumptions}
        with _patched_auth():
            response = client.put(f"/ventures/{venture['id']}", json=body, headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Model update failed: {response.text}")

        history = _get_history(venture["id"], USER_A)
        model_events = _events_of_type(history, "model_updated")
        expect(len(model_events) == 1, "A real change to a persisted field must still be recorded, even with no VPS movement")
        expect(model_events[0]["before_vps"] == model_events[0]["after_vps"] == vps_before, "VPS must be reported unchanged, never a fabricated delta")
    finally:
        _cleanup()


def test_no_op_save_does_not_create_a_history_entry() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        # Save with byte-identical assumptions -- must not manufacture a
        # history entry for a click that changed nothing.
        body = _create_venture_body()
        with _patched_auth():
            response = client.put(f"/ventures/{venture['id']}", json=body, headers=_auth_headers(USER_A))
        expect(response.status_code == 200, f"Save failed: {response.text}")

        history = _get_history(venture["id"], USER_A)
        expect(len(_events_of_type(history, "model_updated")) == 0, "A no-op save (identical assumptions) must not create a model_updated event")
    finally:
        _cleanup()


# --- H. Reload / persistence ----------------------------------------------------


def test_history_persists_across_reload() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        _create_mission(venture["id"], USER_A)

        first = _get_history(venture["id"], USER_A)
        second = _get_history(venture["id"], USER_A)
        expect(first == second, "Reloading history must return the identical result")
    finally:
        _cleanup()


# --- I. Multiple events / deterministic chronological ordering ------------------


def test_multiple_events_are_deterministically_ordered_most_recent_first() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        mission = _create_mission(venture["id"], USER_A)
        with _patched_auth():
            client.post(
                f"/ventures/{venture['id']}/missions/{mission['id']}/learning",
                json={"learning_summary": "Early signal: interest, but no commitment yet."},
                headers=_auth_headers(USER_A),
            )
        with _patched_auth():
            client.patch(
                f"/ventures/{venture['id']}/missions/{mission['id']}/status",
                json={"status": "completed"},
                headers=_auth_headers(USER_A),
            )
        stronger_assumptions = dict(SAMPLE_ASSUMPTIONS)
        stronger_assumptions["validation"] = {**SAMPLE_ASSUMPTIONS["validation"], "paying_customers": 22}
        with _patched_auth():
            client.put(
                f"/ventures/{venture['id']}",
                json={**_create_venture_body(), "assumptions": stronger_assumptions},
                headers=_auth_headers(USER_A),
            )

        history = _get_history(venture["id"], USER_A)
        occurred_ats = [e["occurred_at"] for e in history["events"]]
        expect(occurred_ats == sorted(occurred_ats, reverse=True), "Events must be sorted most-recent-first, deterministically")
        expect(history["events"][0]["event_type"] == "model_updated", "The most recent event should be the model update, run last")
        expect(history["events"][-1]["event_type"] == "venture_created", "The oldest event should be venture_created")

        types_present = {e["event_type"] for e in history["events"]}
        expect(
            types_present == {"venture_created", "action_added", "learning_recorded", "action_completed", "model_updated"},
            f"Expected all 5 event types to be present, got {types_present}",
        )
    finally:
        _cleanup()


# --- Authorization / isolation ---------------------------------------------------


def test_history_requires_auth() -> None:
    response = client.get("/ventures/1/history")
    expect(response.status_code == 401, f"Expected 401, got {response.status_code}")


def test_history_is_owner_scoped() -> None:
    _ensure_test_users()
    try:
        venture = _create_venture(USER_A)
        with _patched_auth():
            response = client.get(f"/ventures/{venture['id']}/history", headers=_auth_headers(USER_B))
        expect(response.status_code == 404, f"A different user's venture history must 404, got {response.status_code}")
    finally:
        _cleanup()


TESTS = [
    test_new_venture_has_honest_minimal_history,
    test_action_added_appears_and_vps_unchanged,
    test_learning_recorded_preserves_verbatim_text_and_vps_unchanged,
    test_action_completed_appears_and_vps_unchanged,
    test_positive_model_update_shows_before_after_and_raises_vps,
    test_negative_model_update_displayed_honestly,
    test_model_update_with_no_vps_movement_still_recorded_honestly,
    test_no_op_save_does_not_create_a_history_entry,
    test_history_persists_across_reload,
    test_multiple_events_are_deterministically_ordered_most_recent_first,
    test_history_requires_auth,
    test_history_is_owner_scoped,
]


def main() -> None:
    print("\nFounder Progress / Venture History V1 tests")
    print("-" * 72)

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
