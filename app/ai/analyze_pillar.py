"""
Orchestrator for the two-stage pillar pipeline (SIE Evidence/Scoring
Separation sprint):

    enriched_text
        |
        v
    Evidence Analysis   (app/ai/evidence_extraction.py -- no score)
        |
        v
    Scoring             (app/ai/pillar_scoring.py -- judges the
        |                 normalized evidence, never rediscovers it)
        v
    PillarAnalysis

analyze_pillar()'s public signature and return type are UNCHANGED from
before this sprint -- the six pillar wrappers (market_analysis.py,
founder_analysis.py, etc.) and everything downstream of them
(due_diligence_workflow.py, the reliability harness) call it exactly as
before and get back the same result_model instance shape. Only the
internal implementation is now two calls instead of one, with
per-dimension scoped correction instead of whole-pillar correction.
"""

from app.ai.scoring import finalize_pillar_score, get_scoring_dimensions
from app.ai.evidence_extraction import extract_pillar_evidence
from app.ai.pillar_scoring import score_pillar_evidence
from app.models.scoring import PillarScoreBreakdown, Subscore

from app.ai.sie_v2_methodology import deterministic_dimension_names, get_dimension
from app.ai.sie_v2_anchors import (
    score_from_structured_facts,
    AnchorResult,
    resolve_customer_demand_applicability,
    CustomerDemandLifecycleState,
)
from app.ai.sie_v2_evidence_semantics import classify_unavailable_dimension, MissingEvidenceState

from app.ai.pillar_shared import (  # noqa: F401 -- re-exported for backward compatibility
    PILLAR_ANALYSIS_MODEL,
    PILLAR_PROMPT_VERSION,
    QUANTITATIVE_DISCLOSURE_TERMS,
    get_methodology_by_name,
)


DEFAULT_SYSTEM_MESSAGE = (
    "You are a General Partner at a top-tier venture capital firm. "
    "You evaluate intrinsic startup quality, not pitch quality. "
    "You do not use hindsight during historical calibration. "
    "Return only valid JSON."
)


def print_raw_subscores(pillar: str, score_breakdown: PillarScoreBreakdown) -> None:
    """Temporary calibration logging."""
    print("\n" + "=" * 70)
    print(f"{pillar.upper()} RAW SUBSCORES")
    print("=" * 70)

    for subscore in score_breakdown.subscores:
        corrected = ""
        if subscore.evidence_corrected or subscore.score_corrected:
            tags = []
            if subscore.evidence_corrected:
                tags.append("evidence-corrected")
            if subscore.score_corrected:
                tags.append("score-corrected")
            corrected = f" [{', '.join(tags)}]"

        print(
            f"{subscore.name:<30}"
            f" Score: {str(subscore.score):<5}"
            f" | Evidence: {subscore.evidence_status:<11}"
            f" | Confidence: {subscore.confidence}"
            f"{corrected}"
        )

    print("=" * 70 + "\n")


def _default_missing_evidence_state(dimension_name: str) -> str:
    """
    Evidence-semantics wiring (post-implementation review): the minimum
    metadata needed for live output to distinguish WHY a dimension is
    unscored, not merely score=None. Real per-dimension stage-applicability
    flags (Part 4's not-expected/not-applicable/optional gates) are not
    threaded through the generic pillar pipeline yet -- only
    evidence_requirement (Public/Inferred/Private, already known from the
    canonical dimension spec) is available here, so
    classify_unavailable_dimension() is called with the stage flags
    defaulted to False. This yields the categorical "usually private" vs.
    "expected but unavailable" split the frozen spec defines from Public/
    Inferred vs. Private dimensions -- it never claims a more precise
    stage-driven state than the pipeline actually knows. Callers with a
    real stage signal (e.g. the Deterministic NOT_APPLICABLE anchor outcome
    below) pass a more specific state instead of using this default.
    """
    spec = get_dimension(dimension_name)
    evidence_requirement = spec.evidence_requirement if spec else "Public"
    return classify_unavailable_dimension(
        evidence_requirement=evidence_requirement,
        stage_not_expected=False,
        stage_not_applicable=False,
        stage_optional=False,
    ).value


def build_subscores(
    pillar: str,
    pillar_evidence,
    scores: dict[str, tuple[float, str]],
    evidence_corrected_names: set[str],
    score_corrected_names: set[str],
) -> list[Subscore]:
    """
    Merge stage 1 (evidence) and stage 2 (score) into the final Subscore
    list the rest of the system already understands. Weight comes from
    the canonical per-dimension config (app/ai/scoring_methodology.py),
    never from the model.
    """
    weights_by_name = dict(get_scoring_dimensions(pillar))

    subscores: list[Subscore] = []

    for dim in pillar_evidence.dimensions:
        score, scoring_rationale = scores.get(dim.dimension, (None, ""))

        # Combine the evidence-classification rationale with the
        # scoring-stage rationale so the final Subscore.rationale reads
        # as one coherent explanation, while the two stages' reasoning
        # remains separately inspectable via evidence_analysis if a
        # caller wants it (see the reliability harness, Phase 6).
        if dim.evidence_status == "Unavailable":
            rationale = dim.rationale
        elif scoring_rationale:
            rationale = scoring_rationale
        else:
            rationale = dim.rationale

        subscores.append(
            Subscore(
                name=dim.dimension,
                score=score,
                weight=weights_by_name.get(dim.dimension, 0.0),
                confidence=dim.confidence,
                evidence_status=dim.evidence_status,
                rationale=rationale,
                evidence=dim.evidence,
                recommendations=dim.recommendations,
                missing_information=dim.missing_information,
                signals=dim.signals,
                evidence_corrected=dim.dimension in evidence_corrected_names,
                score_corrected=dim.dimension in score_corrected_names,
                missing_evidence_state=(
                    _default_missing_evidence_state(dim.dimension)
                    if dim.evidence_status == "Unavailable"
                    else None
                ),
            )
        )

    return subscores


def apply_deterministic_overrides(
    subscores: list[Subscore],
    pillar_evidence,
) -> list[Subscore]:
    """
    SIE Methodology v2, Part 8: Deterministic dimensions must be
    Python/rule-driven, full stop -- the LLM scoring stage's number is NEVER
    the final score for one of these dimensions, regardless of whether it
    happens to look reasonable. This is a FAIL-CLOSED contract (Blocker 1
    fix, post-implementation review): every Deterministic-named Subscore is
    unconditionally rewritten below -- either to a real Python-computed
    score (structured_facts present and valid), or to score=None /
    evidence_status="Unavailable" (structured_facts absent or invalid).
    There is no third path where the pre-existing LLM-scored Subscore is
    passed through unchanged, which was the exact defect this fix closes
    (discovered live: Retention retained an LLM score of 7.0 with no
    structured_facts backing it).
    """
    deterministic_names = deterministic_dimension_names()
    evidence_by_name = {d.dimension: d for d in pillar_evidence.dimensions}

    overridden: list[Subscore] = []
    for sub in subscores:
        if sub.name not in deterministic_names:
            overridden.append(sub)
            continue

        evidence = evidence_by_name.get(sub.name)
        structured_facts = getattr(evidence, "structured_facts", None) if evidence else None

        if not structured_facts:
            # FAIL CLOSED: no structured facts -> no score, unconditionally.
            # Never fall through to whatever the LLM scoring stage produced.
            overridden.append(
                sub.model_copy(
                    update={
                        "score": None,
                        "evidence_status": "Unavailable",
                        "confidence": "Low",
                        "rationale": (
                            "[Deterministic v2 -- fail closed] No structured_facts extracted for this "
                            "Deterministic dimension; per Part 8, a Deterministic dimension's score must "
                            "be Python-computed or absent, never an LLM judgment. Original evidence-stage "
                            f"rationale: {getattr(evidence, 'rationale', '') if evidence else ''}"
                        ),
                        "missing_information": (
                            list(getattr(evidence, "missing_information", []) or [])
                            or ["No structured, typed facts (e.g. a dated two-point series) were extracted for this dimension."]
                        ),
                        "missing_evidence_state": _default_missing_evidence_state(sub.name),
                    }
                )
            )
            continue

        result = score_from_structured_facts(sub.name, structured_facts)

        if result.result == AnchorResult.SCORED:
            overridden.append(
                sub.model_copy(
                    update={
                        "score": result.score,
                        "confidence": (result.confidence or "Medium").split("-")[0],  # collapse "Low-Medium" etc. to the model's ConfidenceLevel vocabulary
                        "evidence_status": "Observed",
                        "rationale": f"[Deterministic v2 anchor] {result.rationale}",
                        # Clear any missing_evidence_state build_subscores() may
                        # have set from the pre-override evidence_status (e.g.
                        # a dimension the evidence stage marked Unavailable
                        # before structured_facts was successfully computed
                        # into a real score here) -- a scored dimension must
                        # never carry a stale "why it's unscored" tag.
                        "missing_evidence_state": None,
                    }
                )
            )
        elif result.result == AnchorResult.NOT_APPLICABLE:
            overridden.append(
                sub.model_copy(
                    update={
                        "score": None,
                        "evidence_status": "Unavailable",
                        "confidence": "Low",
                        "rationale": f"[Deterministic v2 anchor -- Not Applicable] {result.rationale}",
                        # A real stage/structural signal, not the generic
                        # evidence_requirement-based default -- the anchor
                        # itself determined this is structurally excluded
                        # (e.g. below the materiality floor).
                        "missing_evidence_state": MissingEvidenceState.NOT_APPLICABLE.value,
                    }
                )
            )
        else:
            # CALIBRATION_ANCHOR_REQUIRED or INSUFFICIENT_EVIDENCE: real
            # structured facts were found but no defensible score could be
            # produced from them (missing anchor, malformed input, or a
            # projection-vs-actual mismatch) -- withheld, not guessed.
            overridden.append(
                sub.model_copy(
                    update={
                        "score": None,
                        "evidence_status": "Unavailable",
                        "confidence": "Low",
                        "rationale": f"[Deterministic v2 anchor -- withheld] {result.rationale}",
                        "missing_evidence_state": _default_missing_evidence_state(sub.name),
                    }
                )
            )

    return overridden


def apply_customer_demand_lifecycle_override(
    subscores: list[Subscore],
    pillar_evidence,
    stage_hint: str,
) -> list[Subscore]:
    """
    SIE Methodology v2, Part 8 (Customer Demand lifecycle fix, post-
    implementation review -- v2-blocking gap closure): wires the
    already-existing, already-tested resolve_customer_demand_applicability()
    into the live Market-pillar path.

    Customer Demand is a HYBRID dimension, not Deterministic -- this
    function does NOT apply Blocker 1's fail-closed contract, and it does
    not change how Customer Demand is scored when it IS applicable. It only
    ever REMOVES a score: if the frozen maturity-based lifecycle rule
    resolves to Not Applicable (realized Traction has superseded
    demand-validation evidence for this company's actual maturity), the
    ordinary Hybrid-scored Subscore -- whatever app/ai/pillar_scoring.py
    judged -- is forced to score=None/Unavailable before it can reach
    PillarScoreBreakdown/finalize_pillar_score(), so it is automatically
    excluded from the Market pillar's weighted-average denominator
    (calculate_weighted_score() already renormalizes over only scorable
    subscores -- no separate renormalization step is needed here).

    If no lifecycle facts were extracted for Customer Demand, or the
    resolved state is EXPECTED or EXPECTED_UNTIL_SUPERSEDED (Customer
    Demand genuinely is still the right question), every subscore -- not
    just Customer Demand -- passes through completely unchanged. The
    financing_round_label always comes first from the dimension's own
    structured_facts (the model's in-context read at the point of
    assessing Customer Demand specifically); stage_hint is only a fallback
    when the model left that field blank, never the sole determinant --
    resolve_customer_demand_applicability() still requires the three
    evidence flags below to reach a Not Applicable conclusion via anything
    other than an explicit Pre-seed label.
    """
    evidence_by_name = {d.dimension: d for d in pillar_evidence.dimensions}
    evidence = evidence_by_name.get("Customer Demand")
    structured_facts = getattr(evidence, "structured_facts", None) if evidence else None

    if not structured_facts:
        return subscores

    try:
        state = resolve_customer_demand_applicability(
            financing_round_label=(
                structured_facts.get("financing_round_label") or stage_hint or ""
            ),
            has_disclosed_customer_or_revenue_data=bool(
                structured_facts.get("has_disclosed_customer_or_revenue_data", False)
            ),
            is_single_market_or_pre_scale=bool(
                structured_facts.get("is_single_market_or_pre_scale", False)
            ),
            realized_traction_evidence_exists=bool(
                structured_facts.get("realized_traction_evidence_exists", False)
            ),
        )
    except (TypeError, ValueError, AttributeError):
        # Malformed structured_facts -- leave the ordinary Hybrid score
        # untouched rather than guessing at a lifecycle state from bad input.
        return subscores

    if state != CustomerDemandLifecycleState.NOT_APPLICABLE:
        return subscores

    overridden: list[Subscore] = []
    for sub in subscores:
        if sub.name != "Customer Demand":
            overridden.append(sub)
            continue
        overridden.append(
            sub.model_copy(
                update={
                    "score": None,
                    "evidence_status": "Unavailable",
                    "confidence": "Low",
                    "rationale": (
                        "[Customer Demand lifecycle -- Not Applicable] Realized Traction evidence has "
                        "superseded demand-validation evidence for this company's actual maturity (Part 8's "
                        "maturity-based, not label-based, lifecycle rule). Realized Traction evidence was "
                        "used only to decide applicability here, never to score this dimension. Original "
                        f"scoring-stage rationale: {sub.rationale}"
                    ),
                    "missing_evidence_state": MissingEvidenceState.NOT_APPLICABLE.value,
                }
            )
        )
    return overridden


def analyze_pillar(
    pillar: str,
    company_text: str,
    result_model,
    system_message: str | None = None,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
):
    system_content = system_message or DEFAULT_SYSTEM_MESSAGE

    pillar_evidence, narrative_fields, evidence_corrected_names = (
        extract_pillar_evidence(
            pillar=pillar,
            company_text=company_text,
            system_content=system_content,
            extra_fields=extra_fields,
            extra_rules=extra_rules,
        )
    )

    # Stage-aware scoring guidance without re-sending the raw corpus:
    # the evidence stage already read the full text and can name the
    # stage as a short fact; nothing else about the raw text crosses
    # into the scoring stage. Popped before constructing result_model
    # since it isn't one of that model's fields.
    stage_hint = narrative_fields.pop("stage_hint", "") or ""

    scores, score_corrected_names = score_pillar_evidence(
        pillar=pillar,
        pillar_evidence=pillar_evidence,
        system_content=system_content,
        stage=stage_hint,
    )

    subscores = build_subscores(
        pillar=pillar,
        pillar_evidence=pillar_evidence,
        scores=scores,
        evidence_corrected_names=evidence_corrected_names,
        score_corrected_names=score_corrected_names,
    )

    # SIE Methodology v2, Part 8: Deterministic dimensions' final score must
    # be Python-computed, never the LLM scoring stage's judgment, whenever
    # the required structured inputs exist.
    subscores = apply_deterministic_overrides(subscores, pillar_evidence)

    # SIE Methodology v2, Part 8 (Customer Demand lifecycle fix): applied
    # after the Deterministic overrides (order is immaterial between the
    # two -- they touch disjoint dimension names) and, critically, BEFORE
    # PillarScoreBreakdown/finalize_pillar_score() below, so a Not
    # Applicable Customer Demand can never survive into the canonical
    # PillarAnalysis with a numeric score. A no-op for every pillar other
    # than Market (no other pillar has a "Customer Demand" dimension).
    subscores = apply_customer_demand_lifecycle_override(subscores, pillar_evidence, stage_hint)

    score_breakdown = PillarScoreBreakdown(pillar=pillar, subscores=subscores)
    score_breakdown = finalize_pillar_score(score_breakdown)

    print_raw_subscores(pillar=pillar, score_breakdown=score_breakdown)

    result_data = dict(narrative_fields)
    result_data["score_breakdown"] = score_breakdown

    return result_model(**result_data)
