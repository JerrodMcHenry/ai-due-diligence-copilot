"""
Focused tests for the Customer Demand lifecycle wiring (v2-blocking gap
closure, post-implementation review):
app.ai.analyze_pillar.apply_customer_demand_lifecycle_override(), which
wires the already-existing, already-tested
app.ai.sie_v2_anchors.resolve_customer_demand_applicability() into the live
Market-pillar path.

Customer Demand is a HYBRID dimension -- these tests check APPLICABILITY
(is this dimension even the right question to ask), not Blocker 1's
Deterministic fail-closed contract, which is covered separately in
test_sie_v2_deterministic_integration.py.

Run with:
    python -m app.tests.test_sie_v2_customer_demand_lifecycle
"""

from app.ai.analyze_pillar import apply_customer_demand_lifecycle_override
from app.ai.scoring import finalize_pillar_score
from app.models.scoring import PillarScoreBreakdown, Subscore
from app.models.evidence_analysis import EvidenceAnalysis, PillarEvidenceAnalysis


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _market_pillar_evidence(customer_demand_facts: dict | None) -> PillarEvidenceAnalysis:
    return PillarEvidenceAnalysis(
        pillar="Market",
        dimensions=[
            EvidenceAnalysis(dimension="Market Size", evidence_status="Observed", confidence="Medium", evidence=["evidence"]),
            EvidenceAnalysis(dimension="Market Growth", evidence_status="Observed", confidence="Medium", evidence=["evidence"]),
            EvidenceAnalysis(dimension="Market Timing", evidence_status="Observed", confidence="Medium", evidence=["evidence"]),
            EvidenceAnalysis(dimension="Competitive Intensity", evidence_status="Observed", confidence="Medium", evidence=["evidence"]),
            EvidenceAnalysis(
                dimension="Customer Demand",
                evidence_status="Inferred",
                confidence="Medium",
                evidence=["demand-validation evidence"],
                structured_facts=customer_demand_facts,
            ),
        ],
    )


def _market_subscores(customer_demand_score: float = 7.0) -> list[Subscore]:
    # Weights match the real Market pillar config (scoring_methodology.py):
    # Market Size .25, Market Growth .20, Market Timing .20,
    # Competitive Intensity .15, Customer Demand .20.
    return [
        Subscore(name="Market Size", score=8.0, weight=0.25, evidence_status="Observed"),
        Subscore(name="Market Growth", score=8.0, weight=0.20, evidence_status="Observed"),
        Subscore(name="Market Timing", score=8.0, weight=0.20, evidence_status="Observed"),
        Subscore(name="Competitive Intensity", score=8.0, weight=0.15, evidence_status="Observed"),
        Subscore(
            name="Customer Demand",
            score=customer_demand_score,
            weight=0.20,
            evidence_status="Inferred",
            rationale="Ordinary Hybrid-stage judgment",
        ),
    ]


def test_pre_seed_with_loi_waitlist_pilot_evidence_stays_applicable() -> None:
    facts = {
        "financing_round_label": "Pre-Seed",
        "has_disclosed_customer_or_revenue_data": False,
        "is_single_market_or_pre_scale": True,
        "realized_traction_evidence_exists": False,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(7.0), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score == 7.0, f"Pre-Seed with early-validation evidence must stay applicable/unchanged, got {cd.score}")
    expect(cd.evidence_status == "Inferred", "Score and evidence_status must be untouched when Expected")


def test_pre_seed_with_no_evidence_stays_expected_but_unavailable_not_na() -> None:
    """A Pre-Seed company with genuinely no demand evidence should remain
    whatever the ordinary evidence stage already correctly decided
    (Expected-but-Unavailable) -- the lifecycle override must NOT force it
    to Not Applicable just because no evidence exists."""
    facts = {
        "financing_round_label": "Pre-Seed",
        "has_disclosed_customer_or_revenue_data": False,
        "is_single_market_or_pre_scale": True,
        "realized_traction_evidence_exists": False,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    subscores = _market_subscores(customer_demand_score=None)
    subscores[-1] = subscores[-1].model_copy(update={"score": None, "evidence_status": "Unavailable", "missing_evidence_state": "expected_but_unavailable"})
    result = apply_customer_demand_lifecycle_override(subscores, pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.evidence_status == "Unavailable", "Should remain Unavailable")
    expect(
        cd.missing_evidence_state == "expected_but_unavailable",
        f"Must NOT be overwritten to 'not_applicable' -- Pre-Seed with no evidence is Expected, not superseded; got {cd.missing_evidence_state}",
    )


def test_seed_with_demand_validation_but_no_realized_traction_stays_applicable() -> None:
    facts = {
        "financing_round_label": "Seed",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": True,
        "realized_traction_evidence_exists": False,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(6.0), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score == 6.0, f"Seed with no realized Traction yet must stay applicable, got {cd.score}")


def test_seed_with_substantial_realized_traction_is_superseded() -> None:
    facts = {
        "financing_round_label": "Seed",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": True,
        "realized_traction_evidence_exists": True,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(6.0), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score is None, f"Seed with substantial realized Traction must be superseded (score=None), got {cd.score}")
    expect(cd.evidence_status == "Unavailable", f"Must become Unavailable, got {cd.evidence_status}")
    expect(cd.missing_evidence_state == "not_applicable", f"Must carry the Not Applicable missing-evidence state, got {cd.missing_evidence_state}")


def test_series_a_plus_with_realized_traction_is_not_applicable() -> None:
    facts = {
        "financing_round_label": "Series B",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": False,
        "realized_traction_evidence_exists": True,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(7.0), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score is None, f"Mature Series B+ must be Not Applicable, got {cd.score}")
    expect(cd.missing_evidence_state == "not_applicable", "Must carry the Not Applicable missing-evidence state")


def test_series_a_label_but_operationally_pre_traction_stays_applicable() -> None:
    """Maturity-based, not label-based: a 'Series A'-labeled company with no
    disclosed customer/revenue data and single-market/pre-scale evidence
    must still be evaluated under the Seed rule (genuinely early despite
    the label) -- financing_round_label alone must never mechanically
    determine applicability."""
    facts = {
        "financing_round_label": "Series A",
        "has_disclosed_customer_or_revenue_data": False,
        "is_single_market_or_pre_scale": True,
        "realized_traction_evidence_exists": False,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(6.5), pillar_evidence, stage_hint="Series A")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score == 6.5, f"Genuinely early Series A-labeled company must stay applicable despite the label, got {cd.score}")


def test_realized_traction_evidence_not_reused_to_score_customer_demand() -> None:
    """The override must only ever REMOVE a score (set it to None) -- it
    must never substitute realized-Traction-derived content INTO Customer
    Demand's score or rationale as if it were demand-validation evidence."""
    facts = {
        "financing_round_label": "Series C",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": False,
        "realized_traction_evidence_exists": True,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(9.0), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score is None, "Superseded Customer Demand must never retain or receive any numeric score")
    expect(
        "used only to decide applicability" in cd.rationale,
        "Rationale must make explicit that realized-Traction evidence was not reused to score this dimension",
    )


def test_other_market_dimensions_untouched_by_customer_demand_override() -> None:
    facts = {
        "financing_round_label": "Series C",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": False,
        "realized_traction_evidence_exists": True,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    result = apply_customer_demand_lifecycle_override(_market_subscores(9.0), pillar_evidence, stage_hint="")
    market_size = next(s for s in result if s.name == "Market Size")
    expect(market_size.score == 8.0, "Non-Customer-Demand dimensions must pass through completely unchanged")


def test_missing_structured_facts_leaves_customer_demand_untouched() -> None:
    """Backward compatibility / conservative default: with no lifecycle
    facts extracted at all, Customer Demand must be left exactly as the
    ordinary Hybrid scoring stage produced it -- never forced to N/A."""
    pillar_evidence = _market_pillar_evidence(None)
    result = apply_customer_demand_lifecycle_override(_market_subscores(7.5), pillar_evidence, stage_hint="")
    cd = next(s for s in result if s.name == "Customer Demand")
    expect(cd.score == 7.5, f"No structured_facts -> no override, got score={cd.score}")


def test_na_customer_demand_excluded_from_market_pillar_denominator_and_weights_renormalize() -> None:
    """Once Customer Demand is superseded, the Market pillar's weighted
    average must renormalize over the remaining 4 dimensions (weights
    .25/.20/.20/.15 summing to .80) exactly as calculate_weighted_score()
    already does for any Unavailable subscore -- no separate
    renormalization step should be needed."""
    facts = {
        "financing_round_label": "Series C",
        "has_disclosed_customer_or_revenue_data": True,
        "is_single_market_or_pre_scale": False,
        "realized_traction_evidence_exists": True,
    }
    pillar_evidence = _market_pillar_evidence(facts)
    subscores = apply_customer_demand_lifecycle_override(_market_subscores(9.0), pillar_evidence, stage_hint="")
    breakdown = finalize_pillar_score(PillarScoreBreakdown(pillar="Market", subscores=subscores))

    expect(breakdown.score is not None, "Market pillar must still score from the remaining 4 dimensions")
    # All 4 remaining dimensions are 8.0 -- the renormalized weighted
    # average must equal 8.0 regardless of Customer Demand's excluded weight.
    expect(
        abs(breakdown.score - 8.0) < 0.01,
        f"Renormalized Market pillar score should be 8.0 (all remaining dims are 8.0), got {breakdown.score}",
    )
    cd = next(s for s in subscores if s.name == "Customer Demand")
    expect(cd.evidence_status == "Unavailable", "Customer Demand must be excluded from the scored set")


TESTS = [
    test_pre_seed_with_loi_waitlist_pilot_evidence_stays_applicable,
    test_pre_seed_with_no_evidence_stays_expected_but_unavailable_not_na,
    test_seed_with_demand_validation_but_no_realized_traction_stays_applicable,
    test_seed_with_substantial_realized_traction_is_superseded,
    test_series_a_plus_with_realized_traction_is_not_applicable,
    test_series_a_label_but_operationally_pre_traction_stays_applicable,
    test_realized_traction_evidence_not_reused_to_score_customer_demand,
    test_other_market_dimensions_untouched_by_customer_demand_override,
    test_missing_structured_facts_leaves_customer_demand_untouched,
    test_na_customer_demand_excluded_from_market_pillar_denominator_and_weights_renormalize,
]


def main() -> None:
    print("\nSIE Methodology v2 -- Customer Demand lifecycle wiring tests")
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
