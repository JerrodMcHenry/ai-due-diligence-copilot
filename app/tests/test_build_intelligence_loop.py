"""
Regression tests for Phase 34D -- SIE Build Intelligence Loop V1: the
venture_evidence / venture_decisions tables (app/database/db.py), the
additive venture_missions columns, their Pydantic contracts
(app/models/venture_missions.py), the deterministic recommendation module
(app/ai/build_recommendation.py), and the new
/ventures/{id}/evidence, /ventures/{id}/decisions,
/ventures/{id}/recommendation endpoints in app/api.py.

Same JWT-mocking harness and zztest_* user-id convention as
test_founder_missions.py -- no live Clerk dependency, every row cleaned
up in a finally block even on failure.

The single most important thing this file proves, alongside ownership and
append-only history: SIE's recommendation changes when the underlying
evidence changes (the "updated guidance" requirement) -- and does so
GENERICALLY, never via any LedgerFlow-specific branch in the recommendation
code itself (see test_recommendation_is_generic_not_domain_specific).

Run with:
    python -m app.tests.test_build_intelligence_loop
"""

import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

USER_A = "zztest_buildloop_user_a"
USER_B = "zztest_buildloop_user_b"

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


client = TestClient(api.app)


# --- JWT mocking harness (mirrors test_founder_missions.py) -----------------


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


EMPTY_VALIDATION = {
    "customer_interviews": None, "waitlist_signups": None, "paying_customers": None,
    "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None,
}

SAMPLE_ASSUMPTIONS = {
    "target_customer": "finance teams",
    "market": {"estimated_market_size": "Medium", "competition_intensity": "Medium"},
    "problem_solution": {
        "problem_statement": "Manual invoice follow-up wastes time",
        "solution_description": "Automated AR collections",
        "differentiation": "AI-prioritized follow-up",
    },
    "founder": {"founder_count": 1, "relevant_domain_experience_years": 3, "has_technical_cofounder": True, "has_business_cofounder": False},
    "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
    "economics": {"pricing_model": None, "price_point": None, "expected_gross_margin_pct": None},
    "validation": dict(EMPTY_VALIDATION),
    "capital": {"starting_capital": None, "monthly_burn": None},
}


def _create_venture_body(name: str) -> dict:
    return {
        "name": name,
        "description": "Test venture for the Build intelligence loop.",
        "industry": "B2B software",
        "business_model": "Subscription",
        "target_customer": "finance teams",
        "stage": "Idea",
        "assumptions": SAMPLE_ASSUMPTIONS,
    }


def _ensure_test_users() -> None:
    with engine.begin() as connection:
        for user_id in (USER_A, USER_B):
            connection.execute(
                text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"), {"id": user_id}
            )


def _cleanup() -> None:
    with engine.begin() as connection:
        for table in ("venture_evidence", "venture_decisions", "venture_missions", "venture_model_updates"):
            connection.execute(
                text(f"DELETE FROM {table} WHERE venture_id IN (SELECT id FROM modeled_ventures WHERE user_id = ANY(:ids))"),
                {"ids": [USER_A, USER_B]},
            )
        connection.execute(text("DELETE FROM modeled_ventures WHERE user_id = ANY(:ids)"), {"ids": [USER_A, USER_B]})
        connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A, USER_B]})


def _create_venture(user_id: str, name: str) -> dict:
    response = client.post("/ventures", json=_create_venture_body(name), headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Venture create failed: {response.text}")
    return response.json()


def _create_mission(venture_id: int, user_id: str, **overrides) -> dict:
    body = {
        "title": "Offer a paid pilot to 5 qualified prospects",
        "mission_type": "willingness_to_pay_test",
        "source": "founder_created",
        "question_text": "Will qualified prospects actually pay for a dedicated solution?",
        "why_it_matters": "Willingness to pay is a stronger signal than interest.",
        **overrides,
    }
    response = client.post(f"/ventures/{venture_id}/missions", json=body, headers=_auth_headers(user_id))
    expect(response.status_code == 200, f"Mission create failed: {response.text}")
    return response.json()


def _create_evidence(venture_id: int, user_id: str, **overrides) -> dict:
    body = {
        "evidence_type": "transaction",
        "statement": "2 of 5 qualified prospects accepted a $500/month paid pilot",
        "provenance": "founder_observed",
        "relationship": "supports",
        **overrides,
    }
    response = client.post(f"/ventures/{venture_id}/evidence", json=body, headers=_auth_headers(user_id))
    return response


def _create_decision(venture_id: int, user_id: str, **overrides) -> dict:
    body = {
        "sie_recommendation": "Continue the paid pilots and test retention.",
        "sie_reasoning": "Willingness-to-pay evidence is early but real.",
        "founder_choice": "proceed_with_pilots",
        "evidence_ids": [],
        **overrides,
    }
    response = client.post(f"/ventures/{venture_id}/decisions", json=body, headers=_auth_headers(user_id))
    return response


# --- Authorization -----------------------------------------------------------


def test_signed_out_cannot_access_build_loop_endpoints() -> None:
    with _patched_auth():
        expect(client.get("/ventures/1/evidence").status_code == 401, "GET evidence must require auth")
        expect(client.post("/ventures/1/evidence", json={}).status_code == 401, "POST evidence must require auth")
        expect(client.get("/ventures/1/decisions").status_code == 401, "GET decisions must require auth")
        expect(client.post("/ventures/1/decisions", json={}).status_code == 401, "POST decisions must require auth")
        expect(client.get("/ventures/1/recommendation").status_code == 401, "GET recommendation must require auth")


def test_mission_persists_question_and_why_it_matters() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Question Persistence")
            mission = _create_mission(venture["id"], USER_A)
            expect(mission["question_text"] == "Will qualified prospects actually pay for a dedicated solution?", "question_text must persist")
            expect(mission["why_it_matters"] == "Willingness to pay is a stronger signal than interest.", "why_it_matters must persist")
            expect(mission["interpretation_summary"] is None, "no interpretation should exist before any evidence")

            # Re-fetch (simulates a reload) via the list endpoint.
            listed = client.get(f"/ventures/{venture['id']}/missions", headers=_auth_headers(USER_A)).json()
            expect(listed[0]["question_text"] == mission["question_text"], "question_text must survive reload")
    finally:
        _cleanup()


def test_owner_can_confirm_evidence_and_receive_interpretation() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Evidence Confirm")
            mission = _create_mission(venture["id"], USER_A)

            response = _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"])
            expect(response.status_code == 200, f"Evidence create failed: {response.text}")
            evidence = response.json()
            expect(evidence["founder_confirmed"] is True, "confirmed evidence must be founder_confirmed=True")
            expect(evidence["evidence_type"] == "transaction", "evidence_type must persist")
            expect(evidence["superseded_by_id"] is None, "fresh evidence must not be superseded")

            updated_mission = client.get(f"/ventures/{venture['id']}/missions", headers=_auth_headers(USER_A)).json()[0]
            expect(updated_mission["interpretation_summary"] is not None, "interpretation must be generated once evidence is confirmed")
            expect(updated_mission["interpretation_limitations"] is not None, "limitations must be generated once evidence is confirmed")
            expect("validated" not in updated_mission["interpretation_summary"].lower(), 'interpretation must never say "validated"')
            expect(
                "retention" in updated_mission["interpretation_limitations"].lower()
                or "repeatable" in updated_mission["interpretation_limitations"].lower(),
                "limitations must name at least one real thing this evidence does not establish",
            )
    finally:
        _cleanup()


def test_invalid_provenance_is_rejected() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Provenance Validation")
            response = _create_evidence(venture["id"], USER_A, provenance="definitely_true")
            expect(response.status_code == 422, "An unrecognized provenance value must be rejected, not silently accepted")
    finally:
        _cleanup()


def test_evidence_never_carries_a_score_field() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest No Evidence Score")
            evidence = _create_evidence(venture["id"], USER_A).json()
            expect("score" not in evidence, "venture_evidence response must never carry a score field")
            expect("confidence" not in evidence, "venture_evidence response must never carry a confidence field")
    finally:
        _cleanup()


def test_evidence_cannot_attach_to_mission_from_another_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Venture A")
            venture_b = _create_venture(USER_A, "ZZTest Venture B")
            mission_on_a = _create_mission(venture_a["id"], USER_A)

            response = _create_evidence(venture_b["id"], USER_A, related_mission_id=mission_on_a["id"])
            expect(response.status_code == 404, "Evidence must not attach to a mission belonging to a different venture")
    finally:
        _cleanup()


def test_decision_marks_mission_completed_and_separates_recommendation_from_choice() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Decision Separation")
            mission = _create_mission(venture["id"], USER_A)
            evidence = _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"]).json()

            decision_response = _create_decision(
                venture["id"], USER_A,
                related_mission_id=mission["id"],
                sie_recommendation="Continue the paid pilots and test retention.",
                sie_reasoning="Willingness-to-pay evidence is early but real.",
                founder_choice="Proceed with the two paid pilots before investing heavily in a larger build.",
                founder_rationale="I want more signal before committing engineering time.",
                evidence_ids=[evidence["id"]],
            )
            expect(decision_response.status_code == 200, f"Decision create failed: {decision_response.text}")
            decision = decision_response.json()

            expect(decision["sie_recommendation"] != decision["founder_choice"], "SIE's recommendation and the founder's choice must never be collapsed into one value")
            expect(decision["founder_rationale"] == "I want more signal before committing engineering time.", "founder rationale must persist")
            expect(decision["evidence_ids"] == [evidence["id"]], "evidence_ids must persist")

            missions = client.get(f"/ventures/{venture['id']}/missions", headers=_auth_headers(USER_A)).json()
            expect(missions[0]["status"] == "completed", "recording a decision must mark its mission completed")
    finally:
        _cleanup()


def test_decision_founder_can_disagree_with_recommendation() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Founder Disagreement")
            mission = _create_mission(venture["id"], USER_A)

            decision = _create_decision(
                venture["id"], USER_A,
                related_mission_id=mission["id"],
                sie_recommendation="Continue testing willingness to pay.",
                sie_reasoning="Sample size is still small.",
                founder_choice="pause",
                founder_rationale="I'm pivoting to a different customer segment instead.",
            ).json()
            expect(decision["founder_choice"] == "pause", "the founder must be able to choose something other than what SIE recommended")
            expect(decision["sie_recommendation"] == "Continue testing willingness to pay.", "SIE's original recommendation must still be preserved even when the founder disagrees")
    finally:
        _cleanup()


def test_decision_reversal_preserves_prior_decision() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Decision Reversal")
            mission = _create_mission(venture["id"], USER_A)
            first = _create_decision(venture["id"], USER_A, related_mission_id=mission["id"]).json()

            reversal = _create_decision(
                venture["id"], USER_A,
                related_mission_id=mission["id"],
                founder_choice="pause",
                supersedes_decision_id=first["id"],
            ).json()

            all_decisions = client.get(f"/ventures/{venture['id']}/decisions", headers=_auth_headers(USER_A)).json()
            ids = {d["id"] for d in all_decisions}
            expect(first["id"] in ids and reversal["id"] in ids, "both the original and the reversing decision must remain queryable")
            expect(reversal["supersedes_decision_id"] == first["id"], "the reversal must point at the decision it supersedes")
    finally:
        _cleanup()


def test_evidence_correction_preserves_original_via_supersession() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Evidence Correction")
            original = _create_evidence(venture["id"], USER_A, statement="1 of 5 accepted").json()
            corrected = _create_evidence(venture["id"], USER_A, statement="2 of 5 accepted").json()

            with engine.begin() as connection:
                connection.execute(
                    text("UPDATE venture_evidence SET superseded_by_id = :new_id WHERE id = :old_id"),
                    {"new_id": corrected["id"], "old_id": original["id"]},
                )

            all_evidence = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_A)).json()
            original_row = next(e for e in all_evidence if e["id"] == original["id"])
            expect(original_row["statement"] == "1 of 5 accepted", "the original evidence statement must never be rewritten in place")
            expect(original_row["superseded_by_id"] == corrected["id"], "the original must point at its correction")
    finally:
        _cleanup()


def test_idempotency_key_prevents_duplicate_evidence() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Evidence Idempotency")
            key = "zztest-idem-key-evidence-1"
            first = _create_evidence(venture["id"], USER_A, idempotency_key=key).json()
            second = _create_evidence(venture["id"], USER_A, idempotency_key=key).json()
            expect(first["id"] == second["id"], "a retried evidence submission with the same idempotency_key must not create a duplicate row")

            all_evidence = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_A)).json()
            expect(len(all_evidence) == 1, f"expected exactly 1 evidence row, got {len(all_evidence)}")
    finally:
        _cleanup()


def test_idempotency_key_prevents_duplicate_decision() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Decision Idempotency")
            key = "zztest-idem-key-decision-1"
            first = _create_decision(venture["id"], USER_A, idempotency_key=key).json()
            second = _create_decision(venture["id"], USER_A, idempotency_key=key).json()
            expect(first["id"] == second["id"], "a retried decision submission with the same idempotency_key must not create a duplicate row")

            all_decisions = client.get(f"/ventures/{venture['id']}/decisions", headers=_auth_headers(USER_A)).json()
            expect(len(all_decisions) == 1, f"expected exactly 1 decision row, got {len(all_decisions)}")
    finally:
        _cleanup()


def test_another_user_cannot_read_or_write_evidence() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Evidence Cross-User")
            evidence = _create_evidence(venture["id"], USER_A).json()

            read_response = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_B))
            expect(read_response.status_code == 404, "a non-owner must not be able to read another user's venture evidence")

            write_response = _create_evidence(venture["id"], USER_B)
            expect(write_response.status_code == 404, "a non-owner must not be able to write evidence onto another user's venture")

            still_one = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_A)).json()
            expect(len(still_one) == 1, "USER_B's attempted write must not have created a row")
    finally:
        _cleanup()


def test_another_user_cannot_read_or_write_decisions() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Decision Cross-User")
            _create_decision(venture["id"], USER_A)

            read_response = client.get(f"/ventures/{venture['id']}/decisions", headers=_auth_headers(USER_B))
            expect(read_response.status_code == 404, "a non-owner must not be able to read another user's venture decisions")

            write_response = _create_decision(venture["id"], USER_B)
            expect(write_response.status_code == 404, "a non-owner must not be able to write a decision onto another user's venture")
    finally:
        _cleanup()


def test_evidence_cannot_reference_decision_from_another_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Cross-Venture Decision A")
            venture_b = _create_venture(USER_A, "ZZTest Cross-Venture Decision B")
            decision_on_a = _create_decision(venture_a["id"], USER_A).json()

            response = _create_evidence(venture_b["id"], USER_A, related_decision_id=decision_on_a["id"])
            expect(response.status_code == 404, "Evidence must not attach to a decision belonging to a different venture")
    finally:
        _cleanup()


def test_decision_cannot_reference_evidence_from_another_venture() -> None:
    _ensure_test_users()
    try:
        with _patched_auth():
            venture_a = _create_venture(USER_A, "ZZTest Cross-Venture Evidence A")
            venture_b = _create_venture(USER_A, "ZZTest Cross-Venture Evidence B")
            evidence_on_a = _create_evidence(venture_a["id"], USER_A).json()

            response = _create_decision(venture_b["id"], USER_A, evidence_ids=[evidence_on_a["id"]])
            expect(response.status_code == 404, "A decision must not be able to cite evidence belonging to a different venture")
    finally:
        _cleanup()


def test_extraction_or_evidence_failure_never_erases_the_raw_result() -> None:
    """§17: 'AI extraction failure does not destroy founder-entered
    result' / 'evidence persistence failure does not erase the result'.
    Extraction is client-side (captureSignals.ts) and result-recording
    (POST .../missions/{id}/learning) is a separate, independent request
    from evidence confirmation (POST .../evidence) -- this test proves
    that structurally: a mission's learning_summary is unaffected by a
    subsequent invalid (422-rejected) evidence submission attempt."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Partial Failure Isolation")
            mission = _create_mission(venture["id"], USER_A)

            result_response = client.post(
                f"/ventures/{venture['id']}/missions/{mission['id']}/learning",
                json={"learning_summary": "Offered the pilot to five prospects. Two accepted at $500/month."},
                headers=_auth_headers(USER_A),
            )
            expect(result_response.status_code == 200, f"Recording a result failed: {result_response.text}")

            bad_evidence_response = _create_evidence(venture["id"], USER_A, provenance="not_a_real_value", related_mission_id=mission["id"])
            expect(bad_evidence_response.status_code == 422, "invalid evidence must be rejected")

            reloaded = client.get(f"/ventures/{venture['id']}/missions", headers=_auth_headers(USER_A)).json()[0]
            expect(
                reloaded["learning_summary"] == "Offered the pilot to five prospects. Two accepted at $500/month.",
                "a failed evidence submission must never erase the already-saved raw result",
            )
    finally:
        _cleanup()


def test_recommendation_reflects_willingness_to_pay_evidence() -> None:
    """The core §12 requirement: SIE's next question changes once
    supporting commitment/transaction evidence exists, moving from
    willingness-to-pay toward retention -- without the founder needing
    to do anything except record what happened."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Updated Guidance")

            before = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(before["recommendation"] is not None, "a fresh venture with no evidence must still get a recommendation")

            mission = _create_mission(venture["id"], USER_A)
            during = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(during["current_question"] is not None, "an active, uninterpreted mission must surface as the current question")
            expect(during["recommendation"] is None, "no new recommendation should appear while a question is actively being tested")

            _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"], evidence_type="transaction", relationship="supports")
            _create_decision(venture["id"], USER_A, related_mission_id=mission["id"])

            after = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(after["current_question"] is None, "the mission is now completed -- there must be no stale current_question")
            expect(after["recommendation"] is not None, "a new recommendation must appear once the prior question resolved")
            expect(
                "retain" in after["recommendation"]["question_text"].lower() or "retention" in after["recommendation"]["question_text"].lower(),
                f"expected the next question to move toward retention, got: {after['recommendation']['question_text']}",
            )
            expect(
                before["recommendation"]["question_text"] != after["recommendation"]["question_text"],
                "the recommendation must genuinely change once evidence changed what matters",
            )
    finally:
        _cleanup()


def test_recommendation_recognizes_mixed_retention_outcome() -> None:
    """Day 60 of the methodology's own LedgerFlow walkthrough: mixed
    renewal/churn evidence must steer toward understanding WHY retention
    is mixed, not back to willingness-to-pay or generic discovery."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest Mixed Retention")
            mission = _create_mission(venture["id"], USER_A)
            _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"], evidence_type="transaction", relationship="supports")
            decision = _create_decision(venture["id"], USER_A, related_mission_id=mission["id"]).json()

            _create_evidence(
                venture["id"], USER_A,
                evidence_type="longitudinal_outcome",
                statement="One customer renewed.",
                provenance="founder_observed",
                relationship="supports",
                related_decision_id=decision["id"],
            )
            _create_evidence(
                venture["id"], USER_A,
                evidence_type="longitudinal_outcome",
                statement="One customer churned.",
                provenance="founder_observed",
                relationship="contradicts",
                related_decision_id=decision["id"],
            )

            after = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            question = after["recommendation"]["question_text"].lower()
            expect(
                "stay" in question or "leaving" in question or "difference" in question or "don't" in question,
                f"expected a retention-driver question after mixed outcome evidence, got: {question}",
            )
    finally:
        _cleanup()


def test_recommendation_is_generic_not_domain_specific() -> None:
    """§21 genericity requirement, enforced at the code level: the exact
    same evidence-type/relationship inputs must produce the same class of
    guidance shift for a venture whose name/description has nothing to do
    with invoices or controllers."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "PetPlaylist -- a music-curation app for dog owners")
            mission = _create_mission(
                venture["id"], USER_A,
                question_text="Will dog owners actually pay for curated playlists?",
                why_it_matters="Willingness to pay is the key open question.",
            )
            before = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()

            _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"], evidence_type="commitment", relationship="supports", statement="3 of 8 users started a paid trial")
            _create_decision(venture["id"], USER_A, related_mission_id=mission["id"])

            after = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(after["recommendation"] is not None, "a non-LedgerFlow venture must still receive a recommendation")
            expect(
                "retain" in after["recommendation"]["question_text"].lower() or "retention" in after["recommendation"]["question_text"].lower(),
                f"the same evidence-type shift must move toward retention regardless of business domain, got: {after['recommendation']['question_text']}",
            )
            expect(
                "controller" not in after["recommendation"]["question_text"].lower()
                and "invoice" not in after["recommendation"]["question_text"].lower(),
                "the recommendation engine must never leak unrelated business vocabulary from another venture",
            )
    finally:
        _cleanup()


def test_evidence_and_decision_never_change_vps_or_assumptions() -> None:
    """THE FIREWALL, restated for this phase's new tables: recording
    evidence and decisions must never touch modeled_ventures.assumptions
    or .model_result -- only an explicit PUT /ventures/{id} can do that,
    unchanged by this phase."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_venture(USER_A, "ZZTest VPS Firewall Holds")
            before_get = client.get(f"/ventures/{venture['id']}", headers=_auth_headers(USER_A)).json()

            mission = _create_mission(venture["id"], USER_A)
            _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"])
            _create_decision(venture["id"], USER_A, related_mission_id=mission["id"])

            after_get = client.get(f"/ventures/{venture['id']}", headers=_auth_headers(USER_A)).json()
            expect(before_get["assumptions"] == after_get["assumptions"], "assumptions must be unchanged by the evidence/decision endpoints")
            expect(before_get["model_result"] == after_get["model_result"], "model_result (VPS) must be unchanged by the evidence/decision endpoints")
    finally:
        _cleanup()


TESTS = [
    test_signed_out_cannot_access_build_loop_endpoints,
    test_mission_persists_question_and_why_it_matters,
    test_owner_can_confirm_evidence_and_receive_interpretation,
    test_invalid_provenance_is_rejected,
    test_evidence_never_carries_a_score_field,
    test_evidence_cannot_attach_to_mission_from_another_venture,
    test_decision_marks_mission_completed_and_separates_recommendation_from_choice,
    test_decision_founder_can_disagree_with_recommendation,
    test_decision_reversal_preserves_prior_decision,
    test_evidence_correction_preserves_original_via_supersession,
    test_idempotency_key_prevents_duplicate_evidence,
    test_idempotency_key_prevents_duplicate_decision,
    test_another_user_cannot_read_or_write_evidence,
    test_another_user_cannot_read_or_write_decisions,
    test_evidence_cannot_reference_decision_from_another_venture,
    test_decision_cannot_reference_evidence_from_another_venture,
    test_extraction_or_evidence_failure_never_erases_the_raw_result,
    test_recommendation_reflects_willingness_to_pay_evidence,
    test_recommendation_recognizes_mixed_retention_outcome,
    test_recommendation_is_generic_not_domain_specific,
    test_evidence_and_decision_never_change_vps_or_assumptions,
]


def main() -> None:
    print("\nSIE Build Intelligence Loop V1 tests")
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
        except Exception as error:
            print(f"ERROR {name}\n      {type(error).__name__}: {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
