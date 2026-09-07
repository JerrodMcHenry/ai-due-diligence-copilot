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

            # Phase 34G: "transaction" specifically (not "commitment") --
            # the generalized funnel (build_recommendation.py) now
            # correctly distinguishes non-monetary commitment evidence
            # from an actual transaction (§7's own "10 said they'd buy"
            # vs. "10 paid" distinction), so this must mirror
            # test_recommendation_reflects_willingness_to_pay_evidence's
            # own evidence_type exactly to test genericity apples-to-apples.
            _create_evidence(venture["id"], USER_A, related_mission_id=mission["id"], evidence_type="transaction", relationship="supports", statement="3 of 8 users paid for the trial")
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


def test_recommendation_respects_customer_prerequisite() -> None:
    """Phase 34F, Section 7: SIE must never recommend interviewing 'target
    customers' when it doesn't yet know who the target customer is. Uses
    the phase's own acceptance-test scenario (a macroeconomic-data
    venture with no described customer) -- vps_guidance.py's own
    next_milestones() would otherwise put "Interview 20+ target
    customers..." first, exactly like every other fresh, no-traction
    venture; the fallback recommendation must substitute a customer-
    identification question instead."""
    _ensure_test_users()
    try:
        with _patched_auth():
            body = {
                "name": "ZZTest Macro Data Venture",
                "description": "I want to create a product that streamlines macroeconomic data. A Macrobond but cooler.",
                "industry": None,
                "business_model": None,
                "target_customer": None,
                "stage": "Idea",
                "assumptions": {**SAMPLE_ASSUMPTIONS, "target_customer": None},
            }
            response = client.post("/ventures", json=body, headers=_auth_headers(USER_A))
            expect(response.status_code == 200, f"Venture create failed: {response.text}")
            venture = response.json()

            rec = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(rec["recommendation"] is not None, "a fresh venture with no evidence must still get a recommendation")
            question = rec["recommendation"]["question_text"].lower()
            expect(
                "target customer" not in question,
                f"must never recommend interviewing 'target customers' before a customer is described, got: {question}",
            )
            expect(
                "who" in question or "customer segment" in question or "figure out" in question,
                f"expected a customer-identification question first, got: {question}",
            )

            # Once a target customer IS described, the original
            # (unmodified) vps_guidance.py milestone becomes reachable
            # again -- this is a fallback override, not a suppression.
            update_body = {**body, "target_customer": "economists at investment banks", "assumptions": {**body["assumptions"], "target_customer": "economists at investment banks"}}
            updated = client.put(f"/ventures/{venture['id']}", json=update_body, headers=_auth_headers(USER_A)).json()
            expect(updated["target_customer"] == "economists at investment banks", "the update must have taken")

            rec_after = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(
                "target customer" in rec_after["recommendation"]["question_text"].lower(),
                f"once a target customer is known, the original interview milestone should be reachable again, got: {rec_after['recommendation']['question_text']}",
            )
    finally:
        _cleanup()


def _venture_body_with_customer(name: str, target_customer: str | None) -> dict:
    return {
        "name": name,
        "description": "Test venture for the Phase 34G sequencing matrix.",
        "industry": None,
        "business_model": None,
        "target_customer": target_customer,
        "stage": "Idea",
        "assumptions": {**SAMPLE_ASSUMPTIONS, "target_customer": target_customer},
    }


def _create_matrix_venture(name: str, target_customer: str | None) -> dict:
    response = client.post("/ventures", json=_venture_body_with_customer(name, target_customer), headers=_auth_headers(USER_A))
    expect(response.status_code == 200, f"Venture create failed: {response.text}")
    return response.json()


def _recommendation_for(venture_id: int) -> dict:
    return client.get(f"/ventures/{venture_id}/recommendation", headers=_auth_headers(USER_A)).json()["recommendation"]


# ---------------------------------------------------------------------------
# Phase 34G §15 -- Test Matrix. Ten deliberately different venture
# histories, exercising `_determine_focus_stage()`/`_recommendation_for_stage()`
# (app/ai/build_recommendation.py) purely through the public API, exactly
# like every other test in this file. Cases G and H, and Case I, are
# written to PROVE the documented, honest limitation
# (docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md's own "known unsupported
# cases") rather than to fake support that doesn't exist.
# ---------------------------------------------------------------------------


def test_sequencing_case_a_vague_idea_needs_customer_clarity() -> None:
    """No customer defined, no evidence -- must ask for customer clarity,
    never "interview 20+ target customers" with no target customer
    described (the exact Phase 34F/34G acceptance-test failure)."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix A", None)
            rec = _recommendation_for(venture["id"])
            question = rec["question_text"].lower()
            expect("target customer" not in question, f"must never recommend interviewing undefined target customers, got: {question}")
            expect("who" in question or "customer segment" in question or "figure out" in question, f"expected customer-clarity framing, got: {question}")
    finally:
        _cleanup()


def test_sequencing_case_b_customer_defined_problem_unvalidated() -> None:
    """Target customer known, no problem evidence yet -- priority must be
    problem evidence (i.e. the customer-discovery test type), not
    anything further down the funnel."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix B", "investment research analysts")
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "customer_discovery", f"expected problem-evidence/customer_discovery priority, got: {rec['recommended_test_type']}")
    finally:
        _cleanup()


def test_sequencing_case_c_problem_strongly_supported_moves_on() -> None:
    """15 qualified interviews, strongly supporting the problem, no
    commitment/transaction evidence yet -- must move PAST problem
    evidence (declining information value, §9), not continue
    recommending more interviews."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix C", "investment research analysts")
            _create_evidence(
                venture["id"], USER_A,
                evidence_type="reported_preference", relationship="supports",
                statement="15 of 15 interviewed analysts described the same painful manual workflow",
                structured_field_path="validation.customer_interviews", structured_value=15,
            )
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] != "customer_discovery", f"must not still be asking for more problem interviews, got: {rec}")
            expect("interview" not in rec["question_text"].lower(), f"must not still recommend interviewing, got: {rec['question_text']}")
    finally:
        _cleanup()


def test_sequencing_case_d_prototype_used_moves_to_willingness_to_pay() -> None:
    """5 target customers tested a prototype, 4 repeatedly complete the
    intended workflow, no one has paid -- priority must be willingness
    to commit/pay, even though no separate interview evidence was ever
    recorded (later evidence presupposes the problem was real enough to
    test)."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix D", "investment research analysts")
            _create_evidence(
                venture["id"], USER_A,
                evidence_type="observed_behavior", relationship="supports",
                statement="4 of 5 prototype testers repeatedly completed the intended workflow",
            )
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "willingness_to_pay_test", f"expected a willingness-to-pay priority, got: {rec['recommended_test_type']}")
    finally:
        _cleanup()


def test_sequencing_case_e_paying_pilots_move_to_retention() -> None:
    """3 qualified customers paid for pilots -- priority must be value
    realization/retention, never a repeat of hypothetical
    willingness-to-pay interviews."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix E", "investment research analysts")
            _create_evidence(
                venture["id"], USER_A,
                evidence_type="transaction", relationship="supports",
                statement="3 of 5 qualified customers paid for a pilot",
            )
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "retention_observation", f"expected a retention priority, got: {rec['recommended_test_type']}")
            expect("pay" not in rec["question_text"].lower() or "retain" in rec["question_text"].lower(), f"must not recommend hypothetical willingness-to-pay again, got: {rec['question_text']}")
    finally:
        _cleanup()


def test_sequencing_case_f_mixed_retention_preserves_tension() -> None:
    """3 paid, 2 renewed, 1 churned -- priority must be understanding the
    retention DIFFERENCE, and the mixed evidence must never collapse into
    "retention validated."."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix F", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 paying customers renewed")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 paying customers churned")
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "retention_observation", f"expected the recommendation to stay at retention, got: {rec}")
            expect(
                "difference" in rec["question_text"].lower() or "why" in rec["question_text"].lower(),
                f"expected the mixed evidence to surface as its own question, got: {rec['question_text']}",
            )
            expect("validated" not in rec["why_it_matters"].lower(), "mixed evidence must never be described as 'validated'")
    finally:
        _cleanup()


def test_sequencing_case_g_strong_retention_founder_led_sales() -> None:
    """10 paying customers, strong usage, strong renewal, all founder-led
    sales, no repeatable acquisition channel -- priority should move to
    growth/acquisition, since retention is resolved."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix G", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="9 of 10 paying customers renewed with strong usage")
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] != "retention_observation", f"retention is resolved -- must not still be the priority, got: {rec}")
            expect(
                "acquire" in rec["question_text"].lower() or "acquisition" in rec["question_text"].lower(),
                f"expected a growth/acquisition-oriented question, got: {rec['question_text']}",
            )
    finally:
        _cleanup()


def test_sequencing_case_h_repeatable_acquisition_documented_gap() -> None:
    """Repeatable acquisition evidence exists, retention healthy,
    economics/scaling uncertainty remains -- the directive's own expected
    priority is SCALING/ECONOMICS, distinct from Case G's REPEATABLE
    ACQUISITION. The current evidence_type taxonomy (commitment/
    transaction/observed_behavior/longitudinal_outcome) has no dedicated
    way to represent "acquisition channel diversity" or "founder-led vs.
    repeatable channel" without either reading business-vocabulary text
    (forbidden) or a new structured field (out of scope this phase) --
    see docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md's own "known
    unsupported cases". This test documents that fact directly: Case H's
    evidence, as expressible today, produces the SAME growth-stage
    recommendation as Case G, rather than faking a distinction the
    architecture cannot yet draw."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix H", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="9 of 10 paying customers renewed with strong usage")
            rec = _recommendation_for(venture["id"])
            expect(
                "acquire" in rec["question_text"].lower() or "acquisition" in rec["question_text"].lower(),
                f"documented gap: Case H currently produces the same growth-stage question as Case G, got: {rec['question_text']}",
            )
    finally:
        _cleanup()


def test_sequencing_case_i_financial_constraint_documented_gap() -> None:
    """Paying customers exist; runway is critically short. Phase 34G §15
    itself invites documenting this honestly rather than faking support:
    no persisted signal in venture_evidence/venture_missions carries
    cash/burn/runway data today (FundraisingSimulator's own inputs are
    ephemeral client-side state, never persisted -- see the Phase 34F
    architecture audit), so the recommendation engine has structurally
    no way to know about a financial constraint. This test proves that
    fact directly: setting `capital.starting_capital`/`monthly_burn` to
    values implying near-zero runway does NOT change the recommendation
    at all, confirming the gap is real rather than silently working by
    accident."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix I", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="transaction", relationship="supports", statement="3 of 5 qualified customers paid for a pilot")
            rec_before = _recommendation_for(venture["id"])

            critical_runway_body = {
                "name": venture["name"], "description": venture["description"], "industry": None,
                "business_model": None, "target_customer": venture["target_customer"], "stage": "Idea",
                "assumptions": {**venture["assumptions"], "capital": {"starting_capital": 5000, "monthly_burn": 25000}},
            }
            client.put(f"/ventures/{venture['id']}", json=critical_runway_body, headers=_auth_headers(USER_A))
            rec_after = _recommendation_for(venture["id"])

            expect(
                rec_before["question_text"] == rec_after["question_text"],
                "documented gap: a critical financial constraint currently has NO effect on the recommendation "
                "(no persisted signal reaches the recommendation engine) -- this must be corrected in a future "
                "phase, not silently faked here.",
            )
    finally:
        _cleanup()


def test_sequencing_case_j_contradictory_segments_preserve_tension() -> None:
    """Enterprise customers retain, SMB customers churn -- must not
    average into a generic "customers like the product" conclusion. The
    evidence_type taxonomy has no dedicated segment tag, but the
    relationship-based mixed-evidence mechanism (identical to Case F)
    still correctly preserves the tension rather than fabricating a
    clean, false consensus."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Matrix J", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="Enterprise customers repeatedly renew")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="SMB customers churn after the first month")
            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "retention_observation", f"expected the recommendation to stay at retention, got: {rec}")
            expect(
                "difference" in rec["question_text"].lower() or "why" in rec["question_text"].lower(),
                f"expected the contradictory segments to surface as their own question, got: {rec['question_text']}",
            )
    finally:
        _cleanup()


def test_company_intelligence_summary_reflects_confirmed_evidence_and_history() -> None:
    """Phase 34G §10-13: `company_intelligence` in the recommendation
    response must be built from actually-persisted evidence/mission/
    decision rows -- never invented, never a score, never every blank
    field. Walks a mission through confirm -> decide and checks all
    three lists end up populated from exactly those real facts."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Company Intelligence", "investment research analysts")

            # Brand new: nothing to know, nothing to have changed yet.
            fresh = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            expect(fresh["company_intelligence"]["what_sie_knows"] == [], "a brand-new venture must have no 'what SIE knows' facts yet")
            expect(fresh["company_intelligence"]["what_changed"] == [], "a brand-new venture must have no 'what changed' facts yet")

            mission = _create_mission(
                venture["id"], USER_A,
                question_text="Do investment research analysts actually experience this problem?",
                why_it_matters="Testing problem clarity first.",
            )
            statement = "12 of 15 interviewed analysts described the same painful manual workflow"
            evidence = _create_evidence(
                venture["id"], USER_A, related_mission_id=mission["id"],
                evidence_type="reported_preference", relationship="supports", statement=statement,
            ).json()
            _create_decision(venture["id"], USER_A, related_mission_id=mission["id"], founder_choice="proceed_to_prototype", evidence_ids=[evidence["id"]])

            after = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            summary = after["company_intelligence"]
            expect(statement in summary["what_sie_knows"], f"the confirmed evidence's own statement must appear verbatim in what_sie_knows, got: {summary['what_sie_knows']}")
            expect(len(summary["still_figuring_out"]) > 0, "a completed, interpreted mission must leave at least one still-figuring-out item")
            expect(
                any("proceed_to_prototype" in item for item in summary["what_changed"]),
                f"the founder's own decision must appear in what_changed, got: {summary['what_changed']}",
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


def _resolve_evidence(venture_id: int, user_id: str, evidence_id: int, resolution_note: str):
    return client.post(
        f"/ventures/{venture_id}/evidence/{evidence_id}/resolve",
        json={"resolution_note": resolution_note},
        headers=_auth_headers(user_id),
    )


# ---------------------------------------------------------------------------
# Phase 34G-A -- Intelligence Resolution + Learning Integrity Hardening,
# §11. Cases A-G/M/N below exercise the backend sequencing/resolution/
# still-figuring-out fixes directly. Cases H-L (structured capture) are
# exercised as pure-function tests in
# dashboard/tests/buildIntelligenceLoop.test.ts, mirroring where the
# equivalent 34D-A evidence-mapping tests already live -- captureSignals/
# evidenceMapping have no backend equivalent to test against here.
# ---------------------------------------------------------------------------


def test_resolution_case_a_contradiction_remains_visible_after_later_support() -> None:
    """One earlier contradicting result stays visible (not silently
    dropped) even after a flood of later supporting evidence for the same
    stage -- this is the exact Stage 6 shape from the 34G live walkthrough
    (docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md §14)."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution A", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            churn = _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned").json()
            for i in range(8):
                _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement=f"Customer {i} renewed for a third straight month")

            rec = _recommendation_for(venture["id"])
            expect(rec["recommended_test_type"] == "retention_observation", f"expected recommendation to stay pinned at retention, got: {rec}")
            blocking_ids = {item["id"] for item in rec["blocking_evidence"]}
            expect(churn["id"] in blocking_ids, f"the specific contradicting row must remain visible as blocking_evidence, got: {rec['blocking_evidence']}")

            all_evidence = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_A)).json()
            expect(any(e["id"] == churn["id"] and e["statement"] == "1 of 3 pilot customers churned" for e in all_evidence), "the original churn statement must remain queryable, verbatim")
    finally:
        _cleanup()


def test_resolution_case_b_volume_never_numerically_erases_contradiction() -> None:
    """Explicitly forbidden shortcut: '8 supports > 1 contradiction =
    validated.' Even a large, lopsided volume of supporting evidence must
    never silently clear a live contradiction -- only an explicit
    founder resolution (Case C) can."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution B", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 customer churned early")
            for i in range(20):
                _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement=f"Customer {i} renewed")

            rec = _recommendation_for(venture["id"])
            expect(
                rec["recommended_test_type"] == "retention_observation" and len(rec["blocking_evidence"]) > 0,
                f"20:1 supporting-to-contradicting volume must NOT numerically resolve the tension, got: {rec}",
            )
    finally:
        _cleanup()


def test_resolution_case_c_explicit_resolution_clears_decision_dominance() -> None:
    """The one sanctioned way to clear a live contradiction: an explicit
    founder action naming why the old result no longer reflects the
    current picture. After resolving, the funnel is free to advance past
    the previously-pinned stage."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution C", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            churn = _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned").json()
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="8 of 9 newer customers renewed for 3 straight months")

            pinned = _recommendation_for(venture["id"])
            expect(pinned["recommended_test_type"] == "retention_observation", f"expected retention to be pinned before resolution, got: {pinned}")

            resolve_response = _resolve_evidence(venture["id"], USER_A, churn["id"], "This was a one-off from before we fixed onboarding -- newer cohorts don't show this pattern.")
            expect(resolve_response.status_code == 200, f"resolve must succeed for an owned, unresolved row: {resolve_response.text}")

            after = _recommendation_for(venture["id"])
            expect(after["recommended_test_type"] != "retention_observation", f"expected the funnel to advance past retention once the blocking contradiction was resolved, got: {after}")
            expect(after["blocking_evidence"] == [], f"no contradiction should remain blocking once resolved, got: {after['blocking_evidence']}")
    finally:
        _cleanup()


def test_resolution_case_d_superseded_evidence_remains_in_history() -> None:
    """Resolving never edits or deletes -- the original row, and its
    original wording, must still be readable afterward."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution D", "investment research analysts")
            churn = _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned").json()

            resolve_response = _resolve_evidence(venture["id"], USER_A, churn["id"], "Segment-specific -- this was SMB, not our current enterprise focus.")
            expect(resolve_response.status_code == 200, f"resolve failed: {resolve_response.text}")
            new_row = resolve_response.json()

            all_evidence = client.get(f"/ventures/{venture['id']}/evidence", headers=_auth_headers(USER_A)).json()
            original_row = next(e for e in all_evidence if e["id"] == churn["id"])
            expect(original_row["statement"] == "1 of 3 pilot customers churned", "the original statement must never be rewritten")
            expect(original_row["superseded_by_id"] == new_row["id"], "the original must point at its resolution note")
            expect(any(e["id"] == new_row["id"] for e in all_evidence), "the new resolution-note row must also be queryable")

            # Idempotent/safe: resolving an already-resolved row is a
            # clean no-op (404), never a duplicate resolution.
            second_attempt = _resolve_evidence(venture["id"], USER_A, churn["id"], "Trying again")
            expect(second_attempt.status_code == 404, "resolving an already-resolved row must not silently succeed twice")
    finally:
        _cleanup()


def test_resolution_case_e_segment_specificity_is_a_documented_gap() -> None:
    """§4/§11 Case E: segment/context attribution is NOT structurally
    representable today -- there is no `segment` column anywhere in the
    venture_evidence schema/response. This test asserts that limitation
    directly rather than pretending a founder's own segment-flavored
    wording in a resolution note is the same thing as real, structured
    segment support -- resolving a 'this was SMB, not enterprise' row
    uses the exact same generic mechanism as any other resolution, with
    no segment-aware behavior anywhere in the response shape."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution E", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="Enterprise customers repeatedly renew")
            smb_churn = _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="SMB customers churn after the first month").json()

            expect("segment" not in smb_churn, "documented gap: venture_evidence has no structured segment field -- confirmed absent from the API response shape")

            resolve_response = _resolve_evidence(venture["id"], USER_A, smb_churn["id"], "This was specifically SMB -- our focus is enterprise, where retention is strong.")
            new_row = resolve_response.json()
            expect("segment" not in new_row, "the resolution note is free text, not a structured segment tag -- the gap is not silently faked by the resolution mechanism")
    finally:
        _cleanup()


def test_resolution_case_f_unresolved_contradiction_blocks_premature_certainty() -> None:
    """An unresolved mixed/contradicting state must never be described as
    settled -- the recommendation stays at the tension, never claims
    retention is validated."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution F", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned")
            rec = _recommendation_for(venture["id"])
            expect("validated" not in rec["why_it_matters"].lower(), f"must never claim retention is validated while a contradiction is unresolved, got: {rec['why_it_matters']}")
            # blocking_evidence surfaces the specific row(s) causing the
            # tension (what a founder would actually resolve) -- the
            # supporting row isn't itself "blocking" anything; both sides
            # of the tension are still preserved verbatim in
            # company_intelligence.what_sie_knows (Case A/F's own point).
            expect(len(rec["blocking_evidence"]) == 1, f"the contradicting row should be visible as the tension, got: {rec['blocking_evidence']}")
            expect(rec["blocking_evidence"][0]["statement"] == "1 of 3 pilot customers churned", f"got: {rec['blocking_evidence']}")
    finally:
        _cleanup()


def test_resolution_case_g_founder_can_see_the_path_to_resolution() -> None:
    """§10's explicit bad outcome ('what's driving the difference?'
    forever, with no way forward) must not happen -- the recommendation
    text itself names a concrete path once a contradiction pins it."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution G", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned")
            rec = _recommendation_for(venture["id"])
            expect(
                "mark it resolved" in rec["why_it_matters"].lower(),
                f"the founder must be told a concrete path exists to resolve the tension, got: {rec['why_it_matters']}",
            )
    finally:
        _cleanup()


def test_resolution_case_m_still_figuring_out_agrees_with_recommendation() -> None:
    """§9: one intelligence state drives both surfaces. Once problem
    evidence is strongly resolved, 'still figuring out' must not still
    primarily claim the founder is figuring out whether the problem
    exists -- and at a live tension, its first item must name that exact
    tension, matching the recommendation's own framing."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution M", "investment research analysts")
            _create_evidence(
                venture["id"], USER_A, evidence_type="reported_preference", relationship="supports",
                statement="12 customer conversations", structured_field_path="validation.customer_interviews", structured_value=12,
            )
            rec_response = client.get(f"/ventures/{venture['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            still = rec_response["company_intelligence"]["still_figuring_out"]
            expect(
                not any("experience this problem" in item.lower() for item in still),
                f"problem existence is already strongly resolved -- 'still figuring out' must not still lead with it, got: {still}",
            )
            expect(
                any("engage" in item.lower() for item in still),
                f"'still figuring out' should now lead with the actual next unresolved stage, got: {still}",
            )

            # A live tension case: still_figuring_out's own framing must
            # match the recommendation's, not a stale, unrelated source.
            venture2 = _create_matrix_venture("ZZTest Resolution M2", "investment research analysts")
            _create_evidence(venture2["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            _create_evidence(venture2["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned")
            rec2_response = client.get(f"/ventures/{venture2['id']}/recommendation", headers=_auth_headers(USER_A)).json()
            still2 = rec2_response["company_intelligence"]["still_figuring_out"]
            expect(
                len(still2) > 0 and "driving the difference" in still2[0].lower(),
                f"'still figuring out' must lead with the same tension the recommendation names, got: {still2}",
            )
    finally:
        _cleanup()


def test_resolution_case_n_no_score_is_ever_created() -> None:
    """Every new response shape introduced by this phase -- blocking
    evidence, the resolution response -- must carry no numeric score,
    confidence, or strength field anywhere a founder could read it as
    one."""
    _ensure_test_users()
    try:
        with _patched_auth():
            venture = _create_matrix_venture("ZZTest Resolution N", "investment research analysts")
            _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="supports", statement="2 of 3 pilot customers renewed")
            churn = _create_evidence(venture["id"], USER_A, evidence_type="longitudinal_outcome", relationship="contradicts", statement="1 of 3 pilot customers churned").json()
            rec = _recommendation_for(venture["id"])
            forbidden = ("score", "confidence", "strength", "probability")
            for item in rec["blocking_evidence"]:
                for key in item:
                    expect(not any(term in key.lower() for term in forbidden), f"blocking_evidence must carry no score-like field, got key: {key}")
            resolved = _resolve_evidence(venture["id"], USER_A, churn["id"], "No longer representative").json()
            for key in resolved:
                expect(not any(term in key.lower() for term in forbidden), f"the resolution response must carry no score-like field, got key: {key}")
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
    test_recommendation_respects_customer_prerequisite,
    test_sequencing_case_a_vague_idea_needs_customer_clarity,
    test_sequencing_case_b_customer_defined_problem_unvalidated,
    test_sequencing_case_c_problem_strongly_supported_moves_on,
    test_sequencing_case_d_prototype_used_moves_to_willingness_to_pay,
    test_sequencing_case_e_paying_pilots_move_to_retention,
    test_sequencing_case_f_mixed_retention_preserves_tension,
    test_sequencing_case_g_strong_retention_founder_led_sales,
    test_sequencing_case_h_repeatable_acquisition_documented_gap,
    test_sequencing_case_i_financial_constraint_documented_gap,
    test_sequencing_case_j_contradictory_segments_preserve_tension,
    test_company_intelligence_summary_reflects_confirmed_evidence_and_history,
    test_evidence_and_decision_never_change_vps_or_assumptions,
    test_resolution_case_a_contradiction_remains_visible_after_later_support,
    test_resolution_case_b_volume_never_numerically_erases_contradiction,
    test_resolution_case_c_explicit_resolution_clears_decision_dominance,
    test_resolution_case_d_superseded_evidence_remains_in_history,
    test_resolution_case_e_segment_specificity_is_a_documented_gap,
    test_resolution_case_f_unresolved_contradiction_blocks_premature_certainty,
    test_resolution_case_g_founder_can_see_the_path_to_resolution,
    test_resolution_case_m_still_figuring_out_agrees_with_recommendation,
    test_resolution_case_n_no_score_is_ever_created,
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
