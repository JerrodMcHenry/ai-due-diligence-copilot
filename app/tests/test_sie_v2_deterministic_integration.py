"""
Integration tests for the Deterministic-dimension override wiring
(app/ai/analyze_pillar.py::apply_deterministic_overrides) and backward
compatibility with analyses stored before the v2 fields existed.

Run with:
    python -m app.tests.test_sie_v2_deterministic_integration
"""

from app.ai.analyze_pillar import apply_deterministic_overrides, build_subscores
from app.models.scoring import Subscore
from app.models.evidence_analysis import EvidenceAnalysis, PillarEvidenceAnalysis
from app.models.startup import SIEMethodologyAnalysis, PillarAnalysis
from app.models.scoring import PillarScoreBreakdown


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _traction_pillar_evidence(growth_velocity_facts: dict | None) -> PillarEvidenceAnalysis:
    return PillarEvidenceAnalysis(
        pillar="Traction",
        dimensions=[
            EvidenceAnalysis(dimension="Customer Growth", evidence_status="Unavailable", confidence="Low", missing_information=["no data"]),
            EvidenceAnalysis(dimension="Revenue Growth", evidence_status="Unavailable", confidence="Low", missing_information=["no data"]),
            EvidenceAnalysis(dimension="Retention", evidence_status="Unavailable", confidence="Low", missing_information=["no data"]),
            EvidenceAnalysis(dimension="Engagement", evidence_status="Observed", confidence="Medium", evidence=["real usage evidence"]),
            EvidenceAnalysis(
                dimension="Growth Velocity",
                evidence_status="Unavailable",  # deliberately Unavailable pre-override -- the override must still work
                confidence="Low",
                structured_facts=growth_velocity_facts,
            ),
        ],
    )


def _base_subscores() -> list[Subscore]:
    return [
        Subscore(name="Customer Growth", score=None, weight=0.15, evidence_status="Unavailable"),
        Subscore(name="Revenue Growth", score=None, weight=0.25, evidence_status="Unavailable"),
        Subscore(name="Retention", score=None, weight=0.25, evidence_status="Unavailable"),
        Subscore(name="Engagement", score=6.0, weight=0.15, evidence_status="Observed"),
        # LLM stage would have produced SOME score here if it were allowed to
        # judge a Deterministic dimension -- the override must replace it.
        Subscore(name="Growth Velocity", score=4.0, weight=0.20, evidence_status="Inferred", rationale="LLM guess -- must be overridden"),
    ]


def test_deterministic_override_replaces_llm_score_with_python_computed_one() -> None:
    facts = {"start_value": 10_000, "end_value": 40_000, "window_years": 1.17, "business_model_family": "hardware", "metric_confirmed_actual": True}
    pillar_evidence = _traction_pillar_evidence(facts)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)

    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.score != 4.0, "The LLM's original score must be replaced")
    expect(gv.score is not None and gv.score >= 7.0, f"227% CAGR at hardware scale should score Strong/Exceptional, got {gv.score}")
    expect(gv.evidence_status == "Observed", "A successfully computed deterministic score should be Observed, not Unavailable")
    expect("[Deterministic v2 anchor]" in gv.rationale, "Rationale must be traceable to the deterministic anchor, not the discarded LLM text")


def test_deterministic_override_fails_closed_when_no_structured_facts() -> None:
    """Blocker 1: an LLM-scored number must NEVER survive for a Deterministic
    dimension when no structured_facts were extracted -- score must become
    None and evidence_status Unavailable, unconditionally."""
    pillar_evidence = _traction_pillar_evidence(None)
    original = _base_subscores()  # Growth Velocity pre-seeded with an LLM score of 4.0
    result = apply_deterministic_overrides(original, pillar_evidence)

    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.score is None, f"Fail-closed violated: LLM score {gv.score} survived with no structured_facts")
    expect(gv.evidence_status == "Unavailable", f"Must become Unavailable, got {gv.evidence_status}")
    expect("fail closed" in gv.rationale.lower(), "Rationale must document the fail-closed decision")


def test_retention_regression_llm_score_cannot_survive_without_structured_facts() -> None:
    """Exact regression case discovered in the live harness run: Retention
    retained an LLM score of 7.0 despite structured_facts being absent."""
    pillar_evidence = PillarEvidenceAnalysis(
        pillar="Traction",
        dimensions=[
            EvidenceAnalysis(
                dimension="Retention",
                evidence_status="Observed",  # the LLM evidence stage was confident
                confidence="Medium",
                evidence=["strong renewal language, no exact NRR/GRR figure"],
                structured_facts=None,  # but no typed NRR/GRR/churn figures were extracted
            ),
        ],
    )
    subscores = [Subscore(name="Retention", score=7.0, weight=0.25, evidence_status="Observed", rationale="LLM judged this from renewal language")]
    result = apply_deterministic_overrides(subscores, pillar_evidence)

    retention = result[0]
    expect(retention.score is None, f"Regression: Retention must not retain an LLM score, got {retention.score}")
    expect(retention.evidence_status == "Unavailable", f"Retention must become Unavailable, got {retention.evidence_status}")


def test_every_deterministic_dimension_class_fails_closed() -> None:
    """Blocker 1 explicitly requires proof for EVERY Deterministic dimension,
    not just Growth Velocity/Retention."""
    from app.ai.sie_v2_methodology import deterministic_dimension_names

    for name in deterministic_dimension_names():
        pillar_evidence = PillarEvidenceAnalysis(
            pillar="Traction" if name != "Unit Economics" else "Financial Health",
            dimensions=[EvidenceAnalysis(dimension=name, evidence_status="Observed", confidence="Medium", evidence=["some narrative evidence"], structured_facts=None)],
        )
        subscores = [Subscore(name=name, score=6.0, weight=0.2, evidence_status="Observed", rationale="LLM guess")]
        result = apply_deterministic_overrides(subscores, pillar_evidence)
        expect(result[0].score is None, f"{name}: LLM score survived with no structured_facts (fail-closed violated)")
        expect(result[0].evidence_status == "Unavailable", f"{name}: must become Unavailable")


def test_unit_economics_override_end_to_end_via_family_routing() -> None:
    """Blocker 4: Unit Economics must produce a real Python-computed score
    through the same apply_deterministic_overrides() seam as the other
    Deterministic dimensions, once structured_facts carries a family."""
    pillar_evidence = PillarEvidenceAnalysis(
        pillar="Financial Health",
        dimensions=[
            EvidenceAnalysis(
                dimension="Unit Economics",
                evidence_status="Observed",
                confidence="Medium",
                evidence=["84% gross margin, 10-month CAC payback, 6.4x LTV:CAC"],
                structured_facts={
                    "families": [
                        {
                            "business_model_family": "saas_subscription",
                            "gross_margin_pct": 84,
                            "cac_payback_months": 10,
                            "ltv_cac_ratio": 6.4,
                        }
                    ]
                },
            ),
        ],
    )
    subscores = [Subscore(name="Unit Economics", score=4.0, weight=0.25, evidence_status="Inferred", rationale="LLM guess -- must be overridden")]
    result = apply_deterministic_overrides(subscores, pillar_evidence)

    ue = result[0]
    expect(ue.score != 4.0, "The LLM's original score must be replaced")
    expect(ue.score is not None and ue.score >= 7.0, f"Strong disclosed SaaS unit economics should score well, got {ue.score}")
    expect(ue.evidence_status == "Observed", "A successfully computed deterministic score should be Observed")
    expect("[Deterministic v2 anchor]" in ue.rationale, "Rationale must be traceable to the deterministic anchor")


def test_deterministic_override_never_fabricates_a_score_from_bad_facts() -> None:
    facts = {"start_value": 100, "end_value": 300, "window_years": 1.0, "business_model_family": "consumer", "metric_confirmed_actual": False}
    pillar_evidence = _traction_pillar_evidence(facts)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)

    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.score is None, "A projection-vs-actual mismatch must be withheld, not scored")
    expect(gv.evidence_status == "Unavailable", "Withheld deterministic dimensions must be Unavailable, never a fabricated score")


def test_non_deterministic_dimensions_untouched() -> None:
    pillar_evidence = _traction_pillar_evidence(None)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)
    engagement = next(s for s in result if s.name == "Engagement")
    expect(engagement.score == 6.0, "Non-Deterministic dimensions must pass through the override function completely unchanged")


def test_deterministic_override_produces_valid_confidence_literal() -> None:
    """Regression guard: the AnchorScore.confidence string ('Low-Medium' etc.)
    must be collapsed to a value Subscore.confidence's Literal type accepts."""
    facts = {"start_value": 16_000, "end_value": 90_000, "window_years": 0.55, "business_model_family": "insurance", "metric_confirmed_actual": True}
    pillar_evidence = _traction_pillar_evidence(facts)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)
    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.confidence in ("Low", "Medium", "High"), f"Confidence must be a valid Subscore literal, got {gv.confidence!r}")


# --- Evidence-semantics wiring: missing_evidence_state metadata ---

def test_missing_evidence_state_populated_for_unavailable_non_deterministic_dimension() -> None:
    """build_subscores() must tag WHY a plain (non-Deterministic) Unavailable
    dimension is unscored, not merely leave score=None with no explanation."""
    pillar_evidence = PillarEvidenceAnalysis(
        pillar="Traction",
        dimensions=[
            EvidenceAnalysis(dimension="Engagement", evidence_status="Unavailable", confidence="Low", missing_information=["no usage data"]),
        ],
    )
    subs = build_subscores(
        pillar="Traction",
        pillar_evidence=pillar_evidence,
        scores={},
        evidence_corrected_names=set(),
        score_corrected_names=set(),
    )
    engagement = subs[0]
    expect(engagement.missing_evidence_state is not None, "An Unavailable dimension must carry a missing_evidence_state")
    expect(
        engagement.missing_evidence_state in ("expected_but_unavailable", "usually_private_and_unavailable"),
        f"Unexpected missing_evidence_state: {engagement.missing_evidence_state}",
    )


def test_missing_evidence_state_none_for_scored_dimension() -> None:
    pillar_evidence = PillarEvidenceAnalysis(
        pillar="Traction",
        dimensions=[
            EvidenceAnalysis(dimension="Engagement", evidence_status="Observed", confidence="Medium", evidence=["real usage evidence"]),
        ],
    )
    subs = build_subscores(
        pillar="Traction",
        pillar_evidence=pillar_evidence,
        scores={"Engagement": (7.0, "strong usage")},
        evidence_corrected_names=set(),
        score_corrected_names=set(),
    )
    expect(subs[0].missing_evidence_state is None, "A scored dimension must never carry a missing_evidence_state")


def test_missing_evidence_state_reflects_not_applicable_for_deterministic_override() -> None:
    """The Deterministic override path has a REAL structural signal
    (below-materiality-floor) -- it must use the precise NOT_APPLICABLE
    state, not the generic categorical default."""
    facts = {"start_value": 2, "end_value": 6, "window_years": 1.0, "business_model_family": "consumer", "metric_confirmed_actual": True}
    pillar_evidence = _traction_pillar_evidence(facts)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)
    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.evidence_status == "Unavailable", "Sanity: below-floor growth must be Unavailable")
    expect(gv.missing_evidence_state == "not_applicable", f"Expected 'not_applicable', got {gv.missing_evidence_state}")


def test_missing_evidence_state_cleared_when_deterministic_override_scores() -> None:
    """A dimension the evidence stage pre-marked Unavailable, then
    successfully scored via structured_facts, must not carry a stale
    missing_evidence_state from before the override."""
    facts = {"start_value": 10_000, "end_value": 40_000, "window_years": 1.17, "business_model_family": "hardware", "metric_confirmed_actual": True}
    pillar_evidence = _traction_pillar_evidence(facts)
    result = apply_deterministic_overrides(_base_subscores(), pillar_evidence)
    gv = next(s for s in result if s.name == "Growth Velocity")
    expect(gv.score is not None, "Sanity: this case should score")
    expect(gv.missing_evidence_state is None, f"A scored override must clear missing_evidence_state, got {gv.missing_evidence_state}")


# --- Backward compatibility: analyses stored before v2 fields existed ---

def test_old_style_evidence_analysis_without_structured_facts_still_validates() -> None:
    """An EvidenceAnalysis dict shaped exactly like pre-v2 stored JSON (no
    structured_facts key at all) must still construct a valid model."""
    old_style = {
        "dimension": "Growth Velocity",
        "evidence_status": "Unavailable",
        "confidence": "Low",
        "evidence": [],
        "signals": [],
        "missing_information": ["no data"],
        "recommendations": [],
        "rationale": "",
    }
    dim = EvidenceAnalysis(**old_style)
    expect(dim.structured_facts is None, "structured_facts must default to None for pre-v2 stored records, never error")


def test_old_style_sie_methodology_analysis_still_validates() -> None:
    """A minimal SIEMethodologyAnalysis dict shaped like a pre-v2 stored
    analysis (no v2-specific fields anywhere) must still round-trip through
    the model without error -- historical analyses are never recomputed or
    invalidated."""
    old_style = {
        "market": {"score": 6.5, "confidence": "Medium", "score_breakdown": {"pillar": "market", "score": 6.5, "subscores": []}},
        "startup_intelligence_score": 62.0,
    }
    analysis = SIEMethodologyAnalysis(**old_style)
    expect(analysis.market.score == 6.5, "Old-style stored analysis must round-trip unchanged")
    expect(analysis.startup_intelligence_score == 62.0, "Old-style SPS must be preserved exactly, never recomputed")


TESTS = [
    test_deterministic_override_replaces_llm_score_with_python_computed_one,
    test_deterministic_override_fails_closed_when_no_structured_facts,
    test_retention_regression_llm_score_cannot_survive_without_structured_facts,
    test_every_deterministic_dimension_class_fails_closed,
    test_unit_economics_override_end_to_end_via_family_routing,
    test_deterministic_override_never_fabricates_a_score_from_bad_facts,
    test_non_deterministic_dimensions_untouched,
    test_deterministic_override_produces_valid_confidence_literal,
    test_missing_evidence_state_populated_for_unavailable_non_deterministic_dimension,
    test_missing_evidence_state_none_for_scored_dimension,
    test_missing_evidence_state_reflects_not_applicable_for_deterministic_override,
    test_missing_evidence_state_cleared_when_deterministic_override_scores,
    test_old_style_evidence_analysis_without_structured_facts_still_validates,
    test_old_style_sie_methodology_analysis_still_validates,
]


def main() -> None:
    print("\nSIE Methodology v2 -- deterministic override integration tests")
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
