"""
Phase 34D -- SIE Build Intelligence Loop V1. Generalized by Phase 34G --
SIE Intelligence Advantage V1, then hardened by Phase 34G-A --
Intelligence Resolution + Learning Integrity Hardening (see
docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md for the full sequencing
methodology, evidence-maturity rules, contradiction-resolution mechanism,
and the honest accounting of what this module can and cannot yet
distinguish).

Phase 34G-A's own governing addition: EXISTS is not the same as CURRENTLY
DECISION-DOMINANT. A contradiction is never resolved by counting rows
(no "8 supports > 1 contradiction = validated") -- it is only ever
cleared by an explicit founder action (`resolve_venture_evidence_for_owner()`
in app/database/db.py) that supersedes the specific old row, at which
point it is simply no longer part of the `evidence_rows` this module
reasons over -- still fully queryable in venture history, just no longer
decision-blocking. See `_determine_focus_stage()`'s own docstring.

Deterministic, template-driven -- no LLM call, no randomness, same
discipline as app/ai/vps_guidance.py's own next_milestones()/
validation_gaps(). See docs/product/SIE_BUILD_METHODOLOGY_V1.md (canonical
methodology) and docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md
§I (accepted recommendation-engine contract) -- this module implements
that contract exactly.

Three entry points:

- generate_interpretation(question_text, confirmed_evidence) -- called
  once confirmed Evidence exists for a mission's question. Answers "what
  did we learn / what does the evidence support / what does it not
  establish" in plain prose. Never says "validated." Never a score.

- build_intelligence_state(venture_name, model_result, active_mission, evidence_rows, target_customer)
  -- answers "what matters now": either the currently-active question
  (if one is being tested and has no interpretation yet) or a fresh
  recommendation, now computed by walking a generic, deterministic
  FUNNEL of prerequisite stages (Phase 34G §5) rather than only reading
  the two special-cased "outcomes"/"commitments" branches Phase 34D
  originally shipped.

- build_company_intelligence_summary(...) -- Phase 34G §10-13. A concise,
  evidence-driven "what SIE knows / what SIE is still figuring out /
  what changed recently" summary, built entirely from already-persisted
  evidence/mission/decision rows -- never a score, never a database dump.

Deliberately generic: every function below reasons over evidence_type/
relationship/structured_value -- never over business-domain vocabulary
("controllers", "invoices", "SMBs"). The LedgerFlow walkthrough in
docs/product/SIE_BUILD_METHODOLOGY_V1.md §19 and the macroeconomic-data
venture walkthrough in SIE_INTELLIGENCE_ADVANTAGE_V1.md are worked
EXAMPLES of what this logic produces, not special cases this module
detects.
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
    establish" is always paired with it. Never says "validated." Phase
    34G §7's own worked example ("10 people said they'd buy" is never
    treated as equivalent to "10 people paid") is enforced structurally
    here -- the summary sentence names the ACTUAL evidence_type present
    (via `_EVIDENCE_TYPE_ADJECTIVE`), it never upgrades a claim's
    strength based on what the founder might have hoped it proved.
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

    # SIE_BUILD_METHODOLOGY_V1.md §7 / Phase 34G §8: contradiction is
    # first-class, never averaged away into a clean verdict.
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


def _needs_known_customer(candidate_text: str) -> bool:
    """
    Phase 34F, Section 7. A small, named prerequisite check: any milestone
    that names "target customer(s)" presupposes SIE already knows who that
    is.
    """
    return "target customer" in candidate_text.lower()


def _fallback_recommendation(venture_name: str, model_result: dict | None, target_customer: str | None = None) -> dict:
    """No Evidence exists yet for this venture -- fall back to the
    existing, unchanged deterministic next_milestones() ranking
    (app/ai/vps_guidance.py), reused verbatim rather than re-derived,
    EXCEPT where the chosen milestone fails the one prerequisite check
    above (Phase 34F, Section 7) -- in that case, ask the prerequisite
    question first. `vps_guidance.py`'s own next_milestones() list is
    untouched either way (it still offers the original milestone, and
    still feeds NextMoves/WeeklyReview unchanged); this override applies
    only to what CurrentQuestionCard's "What matters now" hero shows.

    Phase 34G: this path is only reached when there is no venture_evidence
    at all yet -- once any exists, `_recommendation_for_stage()` below
    takes over.
    """
    milestones = (model_result or {}).get("next_milestones") or []
    chosen = milestones[0] if milestones else None

    has_known_customer = bool(target_customer and target_customer.strip())
    if chosen and _needs_known_customer(chosen) and not has_known_customer:
        return {
            "question_text": f"Figure out exactly who you're building {venture_name} for.",
            "why_it_matters": (
                "You haven't identified a specific customer yet. Before testing demand, narrow down who "
                "experiences this problem most acutely."
            ),
            "recommended_test_type": "other",
            "recommended_test_title": "Choose your first customer segment to investigate",
            "what_to_do": (
                "Choose the first customer group you want to investigate -- for example a specific job "
                "title, industry, or use case that experiences this problem most acutely."
            ),
            "what_to_record": "Which group you chose to focus on, and why.",
            "what_result_would_be_informative": "A believable, specific answer for who has this problem worst -- not \"everyone.\"",
            "what_this_will_not_prove": (
                "Whether that group will actually pay for a solution -- that becomes the next question, "
                "once you know who to ask."
            ),
        }

    question_text = chosen if chosen else (
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


# ---------------------------------------------------------------------------
# Phase 34G -- SIE Intelligence Advantage V1: recommendation sequencing.
#
# The directive's own 9-stage funnel (customer clarity -> problem
# evidence -> workflow/solution evidence -> willingness to commit ->
# transaction evidence -> value realization/usage -> retention ->
# repeatable acquisition -> scaling) is collapsed to the 5 stages below,
# because that is exactly as much as the EXISTING evidence_type taxonomy
# (founder_claim/reported_preference/observed_behavior/commitment/
# transaction/longitudinal_outcome) can distinguish without either (a)
# reading a founder's own statement text for business vocabulary
# (forbidden -- see the genericity requirement above) or (b) a new
# structured field this phase does not add. "Workflow/solution evidence"
# and "willingness to commit" both collapse into COMMITMENT_EVIDENCE
# (evidence_type "commitment"/"observed_behavior" carries no further
# distinction); "repeatable acquisition" and "scaling" both collapse into
# a single terminal GROWTH stage. See
# docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md's "known unsupported
# cases" for the full, honest accounting of exactly what this means SIE
# cannot yet distinguish (Cases G vs. H, and Case I's financial-
# constraint override).
# ---------------------------------------------------------------------------

_FUNNEL_ORDER = ["problem_evidence", "commitment_evidence", "transaction_evidence", "retention"]

_EVIDENCE_TYPES_BY_STAGE = {
    "problem_evidence": ("founder_claim", "reported_preference"),
    "commitment_evidence": ("commitment", "observed_behavior"),
    "transaction_evidence": ("transaction",),
    "retention": ("longitudinal_outcome",),
}

# Phase 34G §9's own "Day 1 vs. Day 20" worked example needs SOME
# threshold past which more interviews stop being the highest-value
# question -- an internal, deterministic constant in the same spirit as
# vps_guidance.py's own STRENGTH_THRESHOLD/_has_meaningful_commercial_scale(),
# never a founder-facing score or exposed number.
_STRONG_INTERVIEW_COUNT = 10


def _relationship_mix(rows: list[dict]) -> str | None:
    """
    None (no evidence at all) | "supports" | "contradicts" | "mixed" |
    "insufficient" (evidence exists but every row is relationship=
    "neutral" -- present, but not yet classified either way).

    "mixed" whenever supports AND contradicts coexist, or an explicit
    mixed-tagged row exists -- SIE_BUILD_METHODOLOGY_V1.md §7/Phase 34G
    §8's own "never average contradiction into a clean verdict" rule,
    generalized here beyond just longitudinal outcomes to every stage.
    """
    if not rows:
        return None
    supports = any(r.get("relationship") == "supports" for r in rows)
    contradicts = any(r.get("relationship") == "contradicts" for r in rows)
    mixed_flag = any(r.get("relationship") == "mixed" for r in rows)
    if mixed_flag or (supports and contradicts):
        return "mixed"
    if contradicts:
        return "contradicts"
    if supports:
        return "supports"
    return "insufficient"


def _problem_evidence_strength(rows: list[dict]) -> str | None:
    """
    "strong" | "weak" | None. Phase 34G §9's declining-information-value
    rule: sums any `structured_value` recorded against
    "validation.customer_interviews" across all supporting rows -- the
    exact same additive-count precedent captureSignals.ts/MissionsSection's
    own model-update flow already establishes (Phase 26) -- and treats
    the count as "strong" once it clears the threshold. A supporting row
    with no countable interview figure (e.g. a single confirmed
    founder_claim) still counts as "weak" -- present, but not yet
    substantial enough to declare this stage's uncertainty resolved.
    """
    supporting = [r for r in rows if r.get("relationship") == "supports"]
    if not supporting:
        return None
    total_interviews = sum(
        (r.get("structured_value") or 0)
        for r in supporting
        if r.get("structured_field_path") == "validation.customer_interviews"
    )
    return "strong" if total_interviews >= _STRONG_INTERVIEW_COUNT else "weak"


def _determine_focus_stage(evidence_rows: list[dict]) -> tuple[str, str | None, list[dict]]:
    """
    Phase 34G's core sequencing decision, extended by Phase 34G-A --
    returns (stage_id, mix, blocking_rows) where stage_id is one of
    "problem_evidence", "commitment_evidence", "transaction_evidence",
    "retention", "growth"; mix is the `_relationship_mix()` result
    driving that choice (None when the stage simply has no evidence
    yet); and `blocking_rows` is the specific evidence rows (relationship
    "contradicts" or "mixed") causing a `mix` of "contradicts"/"mixed" --
    always `[]` otherwise. Customer clarity is checked by the caller
    (`build_intelligence_state()`) BEFORE this function is ever called --
    it is always the first prerequisite, ahead of anything evidence
    could show, so it is not one of this function's own stages.

    Two passes, in this order:

    1. Any stage with a standing, unresolved contradiction/mixed tension
       wins outright, in funnel order -- checked BEFORE looking at what
       accumulated further downstream, so a real tension is never
       silently bypassed just because something else happened later
       (Phase 34G §8). Phase 34G-A note: this pass does NOT weigh how
       MANY supporting rows exist against how many contradicting ones --
       "8 supports > 1 contradiction = resolved" is exactly the
       majority-vote shortcut the 34G-A directive forbids. A live
       contradiction is cleared only by an explicit founder action
       (`resolve_venture_evidence_for_owner()`, surfaced via
       `blocking_rows` below) that marks the specific old row
       `superseded_by_id` -- at which point it is no longer part of
       `evidence_rows` at all (the caller already filters those out),
       not by this function silently outvoting it.

    2. Otherwise, the highest-value question is the stage one step past
       the LATEST stage with supporting evidence -- later supporting
       evidence presupposes every earlier stage (a real transaction
       cannot happen unless the problem was at least real enough to
       test), so an earlier stage with no evidence recorded is not
       itself the highest-value question once something further down
       the funnel already happened (this is exactly what makes Case D
       -- prototype usage with no separately-recorded interviews --
       correctly move to the transaction/payment question rather than
       looping back to ask for interviews it doesn't need).

    This is a fixed, deterministic template selector -- never a numeric
    formula, never a founder-facing score (Phase 34G §6's own explicit
    requirement).
    """
    stage_rows = {
        stage: [e for e in evidence_rows if e["evidence_type"] in types]
        for stage, types in _EVIDENCE_TYPES_BY_STAGE.items()
    }
    stage_mix = {stage: _relationship_mix(stage_rows[stage]) for stage in _FUNNEL_ORDER}

    for stage in _FUNNEL_ORDER:
        if stage_mix[stage] in ("contradicts", "mixed"):
            blocking = [r for r in stage_rows[stage] if r.get("relationship") in ("contradicts", "mixed")]
            return stage, stage_mix[stage], blocking

    latest_resolved_index = -1
    for i, stage in enumerate(_FUNNEL_ORDER):
        if stage_mix[stage] == "supports":
            latest_resolved_index = i

    if latest_resolved_index == -1:
        return _FUNNEL_ORDER[0], stage_mix[_FUNNEL_ORDER[0]], []

    if _FUNNEL_ORDER[latest_resolved_index] == "problem_evidence":
        if _problem_evidence_strength(stage_rows["problem_evidence"]) != "strong":
            return "problem_evidence", "supports", []

    if latest_resolved_index + 1 >= len(_FUNNEL_ORDER):
        return "growth", "supports", []
    next_stage = _FUNNEL_ORDER[latest_resolved_index + 1]
    return next_stage, stage_mix[next_stage], []


_RESOLUTION_PATH_ADDENDUM = (
    " If one of the specific results below no longer reflects the current situation -- a one-off, a "
    "different segment, or something from before a real change -- you can mark it resolved and SIE will "
    "re-evaluate what matters most."
)


def _recommendation_for_stage(venture_name: str, stage: str, mix: str | None, blocking_rows: list[dict]) -> dict:
    """
    Renders one (stage, mix, blocking_rows) triple from
    `_determine_focus_stage()` into the full BuildRecommendation shape.
    Every sentence names the actual evidence state driving it (Phase 34G
    §14's "explain WHY" requirement) -- never a generic "talk to more
    customers."

    Phase 34G-A §2/§10: when a live contradiction/mixed tension
    (`blocking_rows` non-empty) is what's pinning this stage, the
    why_it_matters copy gets one additional, shared sentence (rather than
    rewriting all eight per-stage templates by hand) naming the concrete
    path to resolution -- SIE never leaves the founder with "what's
    driving the difference?" and no way forward (§10's explicit bad
    outcome). `blocking_evidence` on the returned dict is exactly the
    rows a founder-facing "was this addressed?" affordance should render
    next to -- never the full evidence history, never a score.
    """
    if stage == "problem_evidence":
        if mix == "contradicts":
            question_text = f"Is the problem {venture_name} addresses actually real for this customer?"
            why_it_matters = (
                "What you've recorded so far pushes against the original assumption that this problem is "
                "real and painful -- worth understanding directly before building further around it."
            )
        elif mix == "mixed":
            question_text = f"Why do some of {venture_name}'s target customers experience this problem and others don't?"
            why_it_matters = (
                "Some of what you've recorded supports the problem being real, some contradicts it -- that "
                "tension is worth understanding before treating this as settled either way."
            )
        elif mix == "supports":
            question_text = f"Do enough of {venture_name}'s target customers experience this problem to build around?"
            why_it_matters = (
                "You have some initial signal the problem is real, but not yet enough to be confident it's "
                "widespread and painful enough to justify building a solution."
            )
        else:
            question_text = f"Do {venture_name}'s target customers actually experience this problem?"
            why_it_matters = (
                "You know who you're building for, but not yet whether they genuinely feel this problem -- "
                "that's the most important unknown before anything else."
            )
        test_type = "customer_discovery"

    elif stage == "commitment_evidence":
        if mix == "contradicts":
            question_text = f"Why won't {venture_name}'s target customers engage with a real solution?"
            why_it_matters = "You have evidence the problem is real, but people aren't engaging with what you've shown them -- worth understanding why before testing pricing."
        elif mix == "mixed":
            question_text = f"Why do some {venture_name} prospects engage with the solution and others don't?"
            why_it_matters = "Engagement so far is mixed -- some evidence supports it, some contradicts it. Understanding the difference matters more right now than moving straight to pricing."
        else:
            question_text = f"Will {venture_name}'s target customers meaningfully engage with a real solution?"
            why_it_matters = (
                "You have evidence the problem is real, but not yet whether a proposed solution actually "
                "helps -- the next question is whether people will commit real time, data, or effort to "
                "trying one, before you test whether they'll pay."
            )
        test_type = "other"

    elif stage == "transaction_evidence":
        if mix == "contradicts":
            question_text = f"Why won't {venture_name}'s engaged prospects actually pay?"
            why_it_matters = "People are engaging with the solution but declining to pay -- understanding why matters more right now than repeating the same offer."
        elif mix == "mixed":
            question_text = f"Why do some {venture_name} prospects pay and others decline?"
            why_it_matters = "Some prospects have paid, some have declined -- that split is worth understanding rather than averaging into a single acceptance rate."
        else:
            question_text = f"Will {venture_name}'s engaged prospects actually pay?"
            why_it_matters = (
                "You have evidence people will engage with the solution -- the next question is whether "
                "that translates into an actual, real transaction, not just interest."
            )
        test_type = "willingness_to_pay_test"

    elif stage == "retention":
        if mix == "contradicts":
            question_text = f"Why are {venture_name} customers leaving, and is that fixable?"
            why_it_matters = "Retention evidence points the wrong way -- worth understanding before investing further in acquisition."
        elif mix == "mixed":
            question_text = f"What's driving the difference between {venture_name} customers who stay and those who don't?"
            why_it_matters = (
                "You have some evidence customers stick around and some evidence they don't -- "
                "understanding what causes the difference matters more right now than testing "
                "willingness to pay again."
            )
        else:
            question_text = f"Will customers actually use and retain {venture_name}?"
            why_it_matters = (
                "You now have real transaction evidence -- the next question is whether customers get "
                "enough recurring value to keep using and paying, not whether more people will pay once."
            )
        test_type = "retention_observation"

    else:  # "growth" -- terminal bucket, see module docstring for the honest gap this represents.
        question_text = f"Can {venture_name} acquire new customers beyond however you found the first ones?"
        why_it_matters = (
            "You have healthy retention evidence -- the next real question is whether growth can continue "
            "predictably, not just repeat whatever produced the first customers."
        )
        test_type = "other"

    if blocking_rows:
        why_it_matters = why_it_matters + _RESOLUTION_PATH_ADDENDUM

    template = _TEST_TEMPLATES[test_type]
    return {
        "question_text": question_text,
        "why_it_matters": why_it_matters,
        "recommended_test_type": test_type,
        "recommended_test_title": question_text,
        "blocking_evidence": [
            {"id": r["id"], "statement": r["statement"], "relationship": r["relationship"]} for r in blocking_rows
        ],
        **template,
    }


def build_intelligence_state(
    venture_name: str,
    model_result: dict | None,
    active_mission: dict | None,
    evidence_rows: list[dict],
    target_customer: str | None = None,
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

    `target_customer` (Phase 34F, Section 7) is the venture's own
    top-level field, passed through so the sequencing logic (Phase 34G)
    can apply its customer-clarity prerequisite.

    Phase 34G: once ANY venture_evidence exists, the recommendation comes
    from `_determine_focus_stage()` walking the generic funnel (§5) --
    this replaces the two special-cased "outcomes"/"commitments"
    branches Phase 34D originally shipped with one general mechanism
    that produces the same LedgerFlow behavior as a special case, not a
    hardcoded one.
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
        return {
            "current_question": None,
            "recommendation": _fallback_recommendation(venture_name, model_result, target_customer),
        }

    if not (target_customer and target_customer.strip()):
        # Customer clarity is always the first prerequisite, regardless
        # of what other evidence has accumulated (Phase 34F/34G) --
        # checked here, ahead of the funnel walk, exactly like
        # `_fallback_recommendation()`'s own check for the no-evidence
        # case.
        return {
            "current_question": None,
            "recommendation": _fallback_recommendation(venture_name, model_result, target_customer),
        }

    stage, mix, blocking_rows = _determine_focus_stage(evidence_rows)
    recommendation = _recommendation_for_stage(venture_name, stage, mix, blocking_rows)
    return {"current_question": None, "recommendation": recommendation}


# ---------------------------------------------------------------------------
# Phase 34G §10-13 -- Company Intelligence State.
#
# A concise, evidence-driven "what SIE knows / what SIE is still figuring
# out / what changed recently" summary, built entirely from already-
# persisted rows -- never a score, never a database dump, never invented.
# State-dependent by construction: each section is simply absent (empty
# list) when there's nothing genuine to say yet (§18's own "a brand-new
# venture should not need to render every section" requirement).
# ---------------------------------------------------------------------------

_KNOWS_BULLET_CAP = 6
_CHANGED_BULLET_CAP = 3

# Phase 34G-A §9. Plain-language phrasing of "what's still unresolved at
# or beyond this funnel stage" -- keyed by the SAME stage ids
# `_determine_focus_stage()` already uses, so "still figuring out" is
# derived from the identical deterministic computation the primary
# recommendation itself uses, rather than a separately-stale source
# (the prior design's bug: it read the most recently COMPLETED mission's
# own interpretation text, which does not update when evidence is
# confirmed outside a mission's own result-recording flow -- exactly
# what happened during the 34G live walkthrough). "One intelligence
# state should drive both surfaces" (34G-A §9's own instruction) is
# satisfied by construction: both call `_determine_focus_stage()` on the
# same `evidence_rows`.
_STAGE_UNRESOLVED_PHRASE = {
    "problem_evidence": "Whether target customers actually experience this problem",
    "commitment_evidence": "Whether target customers will meaningfully engage with a real solution",
    "transaction_evidence": "Actual willingness to pay",
    "retention": "Sustained usage or retention over time",
    "growth": "Repeatable acquisition beyond how you found the first customers",
}

# The concrete, named tension for a stage currently pinned by
# contradicting/mixed evidence -- used INSTEAD OF (not in addition to)
# that stage's own generic `_STAGE_UNRESOLVED_PHRASE` entry, since the two
# would otherwise say nearly the same thing twice.
_STAGE_TENSION_PHRASE = {
    "problem_evidence": "Whether this problem is real for enough customers -- current evidence points both ways",
    "commitment_evidence": "Why some prospects engage with the solution and others don't",
    "transaction_evidence": "Why some prospects pay and others decline",
    "retention": "What's driving the difference between customers who stay and those who don't",
}

_FUNNEL_ORDER_WITH_GROWTH = _FUNNEL_ORDER + ["growth"]


def _still_figuring_out_from_stage(stage: str, mix: str | None) -> list[str]:
    bullets: list[str] = []
    start_index = _FUNNEL_ORDER_WITH_GROWTH.index(stage)
    if mix in ("contradicts", "mixed") and stage in _STAGE_TENSION_PHRASE:
        bullets.append(_STAGE_TENSION_PHRASE[stage])
        start_index += 1  # this stage's own generic phrase would restate the tension phrase above
    for later_stage in _FUNNEL_ORDER_WITH_GROWTH[start_index:]:
        phrase = _STAGE_UNRESOLVED_PHRASE.get(later_stage)
        if phrase:
            bullets.append(phrase)
    bullets.append("Unit economics at scale")
    return bullets


def build_company_intelligence_summary(
    evidence_rows: list[dict],
    completed_missions: list[dict],
    latest_decision: dict | None,
    target_customer: str | None = None,
) -> dict:
    """
    Returns {"what_sie_knows": list[str], "still_figuring_out": list[str],
    "what_changed": list[str]}.

    `evidence_rows` should already be filtered to non-superseded (§18 of
    the 34D architecture doc's own append-only rule: a corrected row is
    never shown alongside the row it corrected -- and, per Phase 34G-A
    §3/§6, this is now also how a founder-resolved contradiction stops
    being decision-dominant here without erasing it from history: a
    superseded row simply never reaches this function). `completed_missions`
    should be every mission with `completed_at` set, in the order the
    caller already has them (creation order); this function reads only
    the most recent one or two for "what changed" -- it does not walk
    the full history. `target_customer` (Phase 34G-A) lets "still figuring
    out" agree with the exact same customer-clarity gate the primary
    recommendation itself checks first.
    """
    # WHAT SIE KNOWS: each confirmed evidence row's own statement,
    # verbatim -- never rephrased into a stronger claim than what was
    # actually recorded (Phase 34G §11's own "state what happened, not
    # what SIE wishes it proved"). Ordered weakest evidence type first so
    # the strongest, most decision-relevant facts read last; capped so
    # this never becomes a database dump.
    ordered_evidence = sorted(
        evidence_rows,
        key=lambda e: _EVIDENCE_STRENGTH_ORDER.index(e["evidence_type"]) if e["evidence_type"] in _EVIDENCE_STRENGTH_ORDER else 0,
    )
    what_sie_knows = [e["statement"] for e in ordered_evidence[-_KNOWS_BULLET_CAP:]]

    # STILL FIGURING OUT (Phase 34G-A §9 fix): derived from the SAME
    # funnel-stage computation driving the primary recommendation, not
    # from a separately-stale mission-completion snapshot. Empty exactly
    # when the recommendation itself has nothing evidence-based to show
    # yet (no evidence at all, or customer clarity still unresolved) --
    # matching `build_intelligence_state()`'s own two early-exit
    # conditions so the two surfaces never disagree about *why* nothing
    # is shown either.
    still_figuring_out: list[str] = []
    if evidence_rows and target_customer and target_customer.strip():
        stage, mix, _blocking_rows = _determine_focus_stage(evidence_rows)
        still_figuring_out = _still_figuring_out_from_stage(stage, mix)

    # WHAT CHANGED RECENTLY: the most recently completed mission's own
    # question -> its own already-generated interpretation summary, the
    # single most-recently-recorded evidence row's own statement when it
    # postdates that mission summary (Phase 34G-A: this is what makes
    # evidence confirmed OUTSIDE the mission-result flow -- including a
    # founder-explicit resolution, §6 -- visible here at all), plus the
    # most recent decision's own founder_choice if one exists -- entirely
    # persisted facts, never invented (Phase 34G §13's own explicit
    # instruction).
    what_changed: list[str] = []
    most_recent_mission = completed_missions[-1] if completed_missions else None
    mission_summary_time = most_recent_mission.get("interpretation_generated_at") if most_recent_mission else None
    if most_recent_mission:
        summary = most_recent_mission.get("interpretation_summary")
        question = most_recent_mission.get("question_text") or most_recent_mission.get("title")
        if summary and question:
            what_changed.append(f'"{question}" -- {summary}')
    if evidence_rows:
        most_recent_evidence = max(evidence_rows, key=lambda e: e["recorded_at"])
        if mission_summary_time is None or most_recent_evidence["recorded_at"] > mission_summary_time:
            what_changed.insert(0, f'New evidence: "{most_recent_evidence["statement"]}"')
    if latest_decision and latest_decision.get("founder_choice"):
        what_changed.append(f"You decided: {latest_decision['founder_choice']}")

    return {
        "what_sie_knows": what_sie_knows,
        "still_figuring_out": still_figuring_out,
        "what_changed": what_changed[:_CHANGED_BULLET_CAP],
    }
