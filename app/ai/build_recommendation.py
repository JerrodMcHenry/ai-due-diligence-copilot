"""
Phase 34D -- SIE Build Intelligence Loop V1.

Deterministic, template-driven -- no LLM call, no randomness, same
discipline as app/ai/vps_guidance.py's own next_milestones()/
validation_gaps(). See docs/product/SIE_BUILD_METHODOLOGY_V1.md (canonical
methodology) and docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md
§I (accepted recommendation-engine contract) -- this module implements
that contract exactly.

Two entry points:

- generate_interpretation(question_text, confirmed_evidence) -- called
  once confirmed Evidence exists for a mission's question. Answers "what
  did we learn / what does the evidence support / what does it not
  establish" in plain prose. Never says "validated." Never a score.

- build_intelligence_state(venture_name, model_result, missions, evidence_rows)
  -- answers "what matters now": either the currently-active question
  (if one is being tested and has no interpretation yet) or a fresh
  recommendation (computed from accumulated Evidence, generalizing
  vps_guidance.py's own next_milestones() tiering to also reason over
  Evidence, not just VentureAssumptions).

Deliberately generic: every template below reasons over evidence_type/
relationship/venture_name -- never over business-domain vocabulary
("controllers", "invoices", "SMBs"). The LedgerFlow walkthrough in
docs/product/SIE_BUILD_METHODOLOGY_V1.md §19 is a worked EXAMPLE of what
this logic produces, not a special case this module detects.
"""

# Evidence types ordered weakest -> strongest, per
# SIE_BUILD_METHODOLOGY_V1.md §4. Used only to pick which single type
# drives the interpretation's adjective when several are present at once
# -- never combined into a number.
_EVIDENCE_STRENGTH_ORDER = [
    "founder_claim",
    "reported_preference",
    "observed_behavior",
    "commitment",
    "transaction",
    "longitudinal_outcome",
    "external_source",
]

_EVIDENCE_TYPE_ADJECTIVE = {
    "founder_claim": "unverified, founder-stated",
    "reported_preference": "early preference-based",
    "observed_behavior": "observed-behavior",
    "commitment": "initial commitment-level",
    "transaction": "initial transactional",
    "longitudinal_outcome": "longitudinal",
    "external_source": "external",
}


def _strongest_type(evidence: list[dict]) -> str:
    present = {e["evidence_type"] for e in evidence}
    for candidate in reversed(_EVIDENCE_STRENGTH_ORDER):
        if candidate in present:
            return candidate
    return "founder_claim"


def generate_interpretation(question_text: str, confirmed_evidence: list[dict]) -> dict:
    """
    Returns {"summary": str, "limitations": str}. `confirmed_evidence`
    is every venture_evidence row currently linked to the mission this
    question belongs to (not just the newest one) -- an interpretation
    always reasons over the FULL evidence set for this question, per
    SIE_BUILD_METHODOLOGY_V1.md §9.

    Never overclaims: "supports" is the strongest verb used, "does not
    establish" is always paired with it. Never says "validated."
    """
    if not confirmed_evidence:
        return {
            "summary": "Nothing has been confirmed as evidence for this question yet.",
            "limitations": "Nothing here has been tested against the real world yet -- this remains a modeled assumption, not an observation.",
        }

    supports = [e for e in confirmed_evidence if e.get("relationship") == "supports"]
    contradicts = [e for e in confirmed_evidence if e.get("relationship") == "contradicts"]
    mixed = [e for e in confirmed_evidence if e.get("relationship") == "mixed"]

    strongest = _strongest_type(confirmed_evidence)
    adjective = _EVIDENCE_TYPE_ADJECTIVE[strongest]

    # SIE_BUILD_METHODOLOGY_V1.md §7: contradiction is first-class, never
    # averaged away into a clean verdict.
    if supports and contradicts:
        summary = (
            f'{adjective.capitalize()} evidence is mixed on "{question_text}" -- '
            "some of what you recorded supports it, some contradicts it. That tension is worth "
            "understanding before treating this as settled either way."
        )
    elif contradicts:
        summary = (
            f'{adjective.capitalize()} evidence contradicts what was previously believed about '
            f'"{question_text}".'
        )
    elif mixed and not supports:
        summary = f'{adjective.capitalize()} evidence on "{question_text}" is mixed.'
    else:
        summary = f'{adjective.capitalize()} evidence supports "{question_text}".'

    # Deliberately generic and always-honest: a single test/round of
    # evidence essentially never establishes any of these, regardless of
    # business domain -- see SIE_BUILD_METHODOLOGY_V1.md §11's own
    # worked example ("This does not establish willingness to pay,
    # adoption, retention, or whether the same problem is present in
    # other customer segments.").
    missing = []
    if strongest not in ("commitment", "transaction", "longitudinal_outcome"):
        missing.append("actual willingness to pay")
    if strongest != "longitudinal_outcome":
        missing.append("sustained usage or retention over time")
    missing.append("repeatable acquisition beyond this specific test")
    missing.append("whether this holds across a broader segment")
    missing.append("unit economics at scale")

    limitations = "This does not establish " + ", ".join(missing) + "."

    return {"summary": summary, "limitations": limitations}


# ---------------------------------------------------------------------------
# Recommendation -- "what matters now."
# ---------------------------------------------------------------------------

# Deterministic, generic templates per test_type -- mirrors
# dashboard/components/idea-lab/missionSuggestions.ts's own per-milestone
# `why` precedent, generalized to a fixed set of TEST TYPES
# (SIE_BUILD_METHODOLOGY_V1.md §10) instead of exact milestone strings.
_TEST_TEMPLATES = {
    "customer_discovery": {
        "what_to_do": "Talk directly to potential customers about the problem -- before pitching any solution.",
        "what_to_record": "What they said in their own words, and whether they described the problem unprompted.",
        "what_result_would_be_informative": "A clear pattern -- most people describing the same pain, or most people not recognizing it at all.",
        "what_this_will_not_prove": "Whether anyone would actually pay for a solution, or whether they'd change how they work today.",
    },
    "willingness_to_pay_test": {
        "what_to_do": "Offer a real, specific price to qualified prospects and see who says yes.",
        "what_to_record": "How many accepted, at what price, and anything they said about hesitation.",
        "what_result_would_be_informative": "A real acceptance rate at a real price -- not a hypothetical 'would you pay' answer.",
        "what_this_will_not_prove": "Whether they'll actually use it, renew, or refer others.",
    },
    "retention_observation": {
        "what_to_do": "Track whether the customers you already have keep using and paying over the next few weeks.",
        "what_to_record": "Who stayed, who left, and anything they said about why.",
        "what_result_would_be_informative": "A real pattern in who renews versus who churns.",
        "what_this_will_not_prove": "Whether you can acquire new customers at the same rate, or profitably.",
    },
    "other": {
        "what_to_do": "Take the smallest real-world action that would give you a genuine answer.",
        "what_to_record": "What you heard or observed, in your own words.",
        "what_result_would_be_informative": "A clear signal, one way or another, about whether this holds up in the real world.",
        "what_this_will_not_prove": "Whether the whole venture will succeed -- only whether this specific question resolves.",
    },
}


def _fallback_recommendation(venture_name: str, model_result: dict | None) -> dict:
    """No Evidence exists yet for this venture -- fall back to the
    existing, unchanged deterministic next_milestones() ranking
    (app/ai/vps_guidance.py), reused verbatim rather than re-derived."""
    milestones = (model_result or {}).get("next_milestones") or []
    question_text = milestones[0] if milestones else (
        f"What's the biggest assumption behind {venture_name} that hasn't been tested yet?"
    )
    test_type = "customer_discovery" if "interview" in question_text.lower() else (
        "willingness_to_pay_test" if "paying customer" in question_text.lower() else "other"
    )
    template = _TEST_TEMPLATES[test_type]
    return {
        "question_text": question_text,
        "why_it_matters": "This is the most important unknown at this stage -- answering it will shape everything else you test next.",
        "recommended_test_type": test_type,
        "recommended_test_title": question_text,
        **template,
    }


def build_intelligence_state(
    venture_name: str,
    model_result: dict | None,
    active_mission: dict | None,
    evidence_rows: list[dict],
) -> dict:
    """
    Returns {"current_question": dict | None, "recommendation": dict | None}.

    `active_mission` is the venture's most recent status='active' mission
    that carries a question_text, or None. Exactly one of the two return
    fields is non-null at a time:

    - a question is being tested and has no interpretation yet -> only
      current_question is set (nothing new to recommend until it
      resolves);
    - otherwise (nothing active, or the active mission's evidence has
      already been interpreted and is awaiting a founder decision) ->
      only recommendation is set.
    """
    if active_mission is not None and not active_mission.get("interpretation_summary"):
        return {
            "current_question": {
                "mission_id": active_mission["id"],
                "question_text": active_mission["question_text"],
                "why_it_matters": active_mission.get("why_it_matters"),
            },
            "recommendation": None,
        }

    if not evidence_rows:
        return {"current_question": None, "recommendation": _fallback_recommendation(venture_name, model_result)}

    # Reason over ALL accumulated evidence, most decision-relevant
    # category first -- outcomes (longitudinal) outrank a single
    # commitment/transaction, which outrank nothing at all. This is the
    # exact generalization SIE_BUILD_METHODOLOGY_V1.md §19's LedgerFlow
    # walkthrough describes, expressed generically over evidence_type/
    # relationship so it applies to any venture (§21 genericity
    # requirement) -- nothing below reads statement text or business
    # vocabulary.
    outcomes = [e for e in evidence_rows if e["evidence_type"] == "longitudinal_outcome"]
    commitments = [
        e for e in evidence_rows
        if e["evidence_type"] in ("commitment", "transaction") and e.get("relationship") == "supports"
    ]

    if outcomes:
        supports = any(o.get("relationship") == "supports" for o in outcomes)
        contradicts = any(o.get("relationship") == "contradicts" for o in outcomes)
        mixed = any(o.get("relationship") == "mixed" for o in outcomes)

        if mixed or (supports and contradicts):
            question_text = f"What's driving the difference between {venture_name} customers who stay and those who don't?"
            why_it_matters = (
                "You have some evidence customers stick around and some evidence they don't -- "
                "understanding what causes the difference matters more right now than testing "
                "willingness to pay again."
            )
        elif contradicts:
            question_text = f"Why are {venture_name} customers leaving, and is that fixable?"
            why_it_matters = "Retention evidence points the wrong way -- worth understanding before investing further in acquisition."
        else:
            question_text = f"Can {venture_name} keep growing a base of customers who stay and keep paying?"
            why_it_matters = "Early retention evidence is positive -- the next real question is whether that holds as you grow."

        test_type = "retention_observation"

    elif commitments:
        question_text = f"Will customers actually use and retain {venture_name}?"
        why_it_matters = (
            "You now have initial willingness-to-pay evidence. Retention and recurring value are "
            "more important unknowns right now than repeating the same pricing question."
        )
        test_type = "retention_observation"

    else:
        # Evidence exists but nothing strong enough yet to shift focus --
        # fall back to the same deterministic ranking as the no-evidence
        # case, so a founder with only weak/contradicted early evidence
        # still gets a sensible next step rather than nothing.
        return {"current_question": None, "recommendation": _fallback_recommendation(venture_name, model_result)}

    template = _TEST_TEMPLATES[test_type]
    recommendation = {
        "question_text": question_text,
        "why_it_matters": why_it_matters,
        "recommended_test_type": test_type,
        "recommended_test_title": question_text,
        **template,
    }
    return {"current_question": None, "recommendation": recommendation}
