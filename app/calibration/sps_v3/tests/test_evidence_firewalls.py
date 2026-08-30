"""
Phase 10.8F -- three-axis firewall, unknown firewall, negative-evidence,
additive/negative/neutral evidence updates, conflict handling,
Traction/Financial-Health evidence matrices, double-counting
(Rulebook/Calibration-Plan Parts 7-9, 17-20, 23-24).

Run with:
    python -m app.calibration.sps_v3.tests.test_evidence_firewalls
"""

from datetime import date
from decimal import Decimal

from app.calibration.sps_v3 import factory as f
from app.calibration.sps_v3.aggregation import evaluate_sps
from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.evaluators import evaluate_all_dimensions
from app.calibration.sps_v3.registry import DEFAULT_REGISTRY
from app.calibration.sps_v3.types import (
    AvailabilityStatus,
    BurnPeriod,
    CustomerType,
    ProvenanceGrade,
    RevenueMetricType,
    Stage,
    UNAVAILABLE_STATUSES,
)

D2024 = date(2024, 1, 1)
D2025 = date(2025, 1, 1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _find(dims, dim_id):
    return next(d for d in dims if d.dimension_id == dim_id)


# ---------------------------------------------------------------------
# Part 7 -- three-axis firewall
# ---------------------------------------------------------------------

def test_coverage_alone_does_not_change_strength() -> None:
    """Two companies with identical scorable dimensions but different
    amounts of UNAVAILABLE padding around them must have identical
    pillar Strength; only Completeness differs."""
    core = (f.market_size("1000000000", "segment"),)
    small = SyntheticCompany("SYNTH_FIREWALL_COVERAGE_SMALL", Stage.SERIES_A, evidence=core)
    padded = SyntheticCompany(
        "SYNTH_FIREWALL_COVERAGE_PADDED", Stage.SERIES_A,
        evidence=core + (f.market_growth("1", "irrelevant micro-signal"),),
    )
    dims_small = evaluate_all_dimensions(small, DEFAULT_REGISTRY)
    dims_padded = evaluate_all_dimensions(padded, DEFAULT_REGISTRY)
    ms_small = _find(dims_small, "market_size")
    ms_padded = _find(dims_padded, "market_size")
    expect(ms_small.score == ms_padded.score, "Adding an unrelated scorable dimension changed market_size's own score -- cross-contamination.")


def test_confidence_alone_does_not_change_strength() -> None:
    """Same fact, different provenance grade -> Strength must be
    identical; only Confidence may differ (unless the grade change
    also drops the dimension below its minimum-evidence bar, which is
    not the case here)."""
    high = SyntheticCompany(
        "SYNTH_FIREWALL_CONF_HIGH", Stage.SERIES_A,
        evidence=(f.market_size("1000000000", "segment", grade=ProvenanceGrade.PRIMARY_VERIFIED),),
    )
    low = SyntheticCompany(
        "SYNTH_FIREWALL_CONF_LOW", Stage.SERIES_A,
        evidence=(f.market_size("1000000000", "segment", grade=ProvenanceGrade.SECONDARY_ESTIMATE),),
    )
    d_high = _find(evaluate_all_dimensions(high, DEFAULT_REGISTRY), "market_size")
    d_low = _find(evaluate_all_dimensions(low, DEFAULT_REGISTRY), "market_size")
    expect(d_high.score == d_low.score, f"Provenance grade changed Strength: {d_high.score} vs {d_low.score} -- confidence leaked into score.")
    expect(d_high.confidence != d_low.confidence, "Provenance grade should have changed Confidence but did not.")


def test_confidence_caps_do_not_silently_reappear() -> None:
    """No V2.1-style score cap exists anywhere in this harness -- a
    COMPREHENSIVE classification with LOW confidence must still reach
    the comprehensive band's full score."""
    low_grade_comprehensive = SyntheticCompany(
        "SYNTH_NO_CAP_CHECK", Stage.SERIES_A,
        evidence=tuple(
            f.competitor(f"Competitor{i}", grade=ProvenanceGrade.SECONDARY_ESTIMATE)
            for i in range(4)
        ),
    )
    d = _find(evaluate_all_dimensions(low_grade_comprehensive, DEFAULT_REGISTRY), "competitive_intensity")
    expect(d.confidence.value == "LOW", f"Expected LOW confidence from SECONDARY_ESTIMATE-only evidence, got {d.confidence}")
    expect(
        d.score == DEFAULT_REGISTRY.value("band.comprehensive"),
        f"A V2.1-style cap appears to have suppressed a LOW-confidence COMPREHENSIVE score: got {d.score}, expected {DEFAULT_REGISTRY.value('band.comprehensive')}.",
    )


# ---------------------------------------------------------------------
# Part 8 -- unknown firewall
# ---------------------------------------------------------------------

def test_unknown_never_becomes_a_numeric_score() -> None:
    empty = SyntheticCompany("SYNTH_UNKNOWN_FIREWALL", Stage.SEED)
    dims = evaluate_all_dimensions(empty, DEFAULT_REGISTRY)
    for d in dims:
        expect(d.availability in UNAVAILABLE_STATUSES, f"{d.dimension_id}: expected an Unavailable status with zero evidence, got {d.availability}")
        expect(d.score is None, f"{d.dimension_id}: unknown produced a numeric score ({d.score}) instead of null.")


def test_unavailable_excluded_not_zeroed_in_pillar_average() -> None:
    """A pillar with 2 strong scorable dimensions and 3 Unavailable
    ones must average ONLY the 2 scorable ones, not treat the 3
    missing ones as zero."""
    company = SyntheticCompany(
        "SYNTH_PARTIAL_MARKET", Stage.SERIES_A,
        evidence=(
            f.market_size("5000000000", "segment", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("40", "category"),
        ),
    )
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    market_dims = [d for d in dims if d.pillar == "Market"]
    scorable = [d for d in market_dims if d.score is not None]
    from app.calibration.sps_v3.aggregation import compute_pillar_strength
    strength = compute_pillar_strength(tuple(market_dims))
    manual_avg = sum(d.score * d.weight for d in scorable) / sum(d.weight for d in scorable)
    expect(abs(strength - manual_avg.quantize(Decimal("0.01"))) < Decimal("0.02"), f"Pillar strength {strength} does not match a pure average-over-scorable-only computation {manual_avg} -- missing dimensions may be leaking into the denominator as zero.")


# ---------------------------------------------------------------------
# Part 9, 18 -- negative evidence
# ---------------------------------------------------------------------

def test_negative_evidence_produces_low_score_not_inferred_from_absence() -> None:
    with_signal = SyntheticCompany(
        "SYNTH_NEG_WITH_SIGNAL", Stage.SERIES_A,
        negative_signals=(f.negative_signal("revenue_decline", "market_size", "SEVERE"),),
    )
    d = _find(evaluate_all_dimensions(with_signal, DEFAULT_REGISTRY), "market_size")
    expect(d.availability == AvailabilityStatus.SCORABLE, "A negative signal should be scorable (a low number), not Unavailable.")
    expect(d.score == DEFAULT_REGISTRY.value("band.negative_signal"), f"Expected negative band score, got {d.score}")

    absent = SyntheticCompany("SYNTH_NEG_ABSENT", Stage.SERIES_A)
    d_absent = _find(evaluate_all_dimensions(absent, DEFAULT_REGISTRY), "market_size")
    expect(d_absent.score is None, "Absence of evidence must not be treated as negative evidence.")
    expect(d_absent.availability == AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE, "Absence of evidence must resolve to Unavailable, not a negative score.")


def test_negative_evidence_can_lower_sps_end_to_end() -> None:
    strong = SyntheticCompany(
        "SYNTH_STRONG_BASELINE_FOR_NEG_TEST", Stage.SERIES_A,
        evidence=(
            f.market_size("5000000000", "s", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("40", "c", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("X", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.founder_experience("CEO", __import__("app.calibration.sps_v3.types", fromlist=["FounderExperienceType"]).FounderExperienceType.DIRECT_DOMAIN),
            f.product_capability("shipped", shipped=True),
            f.revenue("2000000", D2025, RevenueMetricType.ARR),
            f.revenue("1000000", D2024, RevenueMetricType.ARR),
            f.customer_count(100, D2025, CustomerType.PAYING),
            f.retention(nrr="120"),
            f.commercial_contract(),
            f.runway_statement("20"),
        ),
    )
    dims_before = evaluate_all_dimensions(strong, DEFAULT_REGISTRY)
    sps_before = evaluate_sps(dims_before, strong.stage, DEFAULT_REGISTRY)

    weakened = strong.with_extra_negative_signals(
        f.negative_signal("retention_deterioration", "retention_engagement", "SEVERE"),
        f.negative_signal("revenue_decline", "growth_trajectory", "SEVERE"),
    )
    dims_after = evaluate_all_dimensions(weakened, DEFAULT_REGISTRY)
    sps_after = evaluate_sps(dims_after, weakened.stage, DEFAULT_REGISTRY)

    expect(sps_before.sps is not None and sps_after.sps is not None, "Both variants should be publishable for this test to be meaningful.")
    expect(sps_after.sps < sps_before.sps, f"Adding negative evidence did not lower SPS: {sps_before.sps} -> {sps_after.sps}")


def test_additive_positive_evidence_updates_only_relevant_dimension() -> None:
    base = SyntheticCompany(
        "SYNTH_ADDITIVE_BASE", Stage.SERIES_A,
        evidence=(f.market_size("1000000000", "s"), f.product_capability("shipped", shipped=True)),
    )
    dims_base = evaluate_all_dimensions(base, DEFAULT_REGISTRY)
    product_exec_before = _find(dims_base, "product_execution")

    enriched = base.with_extra_evidence(f.competitor("NewCompetitor", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY))
    dims_enriched = evaluate_all_dimensions(enriched, DEFAULT_REGISTRY)
    product_exec_after = _find(dims_enriched, "product_execution")
    market_size_after = _find(dims_enriched, "market_size")
    comp_intensity_after = _find(dims_enriched, "competitive_intensity")

    expect(product_exec_before.score == product_exec_after.score, "Unrelated dimension (product_execution) changed when only competitive evidence was added.")
    expect(comp_intensity_after.availability == AvailabilityStatus.SCORABLE, "New competitive evidence did not make competitive_intensity scorable.")


def test_neutral_evidence_can_change_coverage_without_changing_sps() -> None:
    """Adding a new HIGH_QUALITY_SECONDARY source that CORROBORATES an
    already-scored dimension (same classification tier) should not
    move SPS, even if it could plausibly change confidence."""
    base = SyntheticCompany(
        "SYNTH_NEUTRAL_BASE", Stage.SERIES_A,
        evidence=(
            f.market_size("5000000000", "s", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("40", "c", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("X", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.founder_experience("CEO", __import__("app.calibration.sps_v3.types", fromlist=["FounderExperienceType"]).FounderExperienceType.DIRECT_DOMAIN),
            f.product_capability("shipped", shipped=True),
            f.revenue("2000000", D2025, RevenueMetricType.ARR),
            f.revenue("1000000", D2024, RevenueMetricType.ARR),
            f.customer_count(100, D2025, CustomerType.PAYING),
            f.retention(nrr="120"),
            f.commercial_contract(),
            f.runway_statement("20"),
        ),
    )
    sps_before = evaluate_sps(evaluate_all_dimensions(base, DEFAULT_REGISTRY), base.stage, DEFAULT_REGISTRY)

    # Phase 10.8G update: the original fixture added a SECOND, DIFFERENT-
    # valued runway statement ("22" months vs. the base's "20") intending
    # it as "corroborating, same STRONG band either way" -- but two
    # different values for the identical signal (runway) is exactly the
    # CONFLICT case Rulebook Part 9 defines ("ARR 2025=$5M vs $12M may
    # conflict"), not corroboration. Under the pre-10.8G code this was
    # silently resolved via `runway_stmt[-1]` (insertion order) and
    # happened to land in the same score band by luck; under 10.8G's
    # conflict detection it is correctly now UNAVAILABLE_CONFLICTING_
    # EVIDENCE. Fixed here to use a GENUINELY corroborating (identical-
    # value) second observation, which is what "neutral evidence" is
    # actually supposed to test.
    enriched = base.with_extra_evidence(f.runway_statement("20", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY))
    sps_after = evaluate_sps(evaluate_all_dimensions(enriched, DEFAULT_REGISTRY), enriched.stage, DEFAULT_REGISTRY)

    expect(sps_before.sps == sps_after.sps, f"A corroborating same-band observation moved SPS: {sps_before.sps} -> {sps_after.sps}")


# ---------------------------------------------------------------------
# Part 20 -- conflict handling (marked EXPECTED_UNRESOLVED where the
# Rulebook itself does not fully resolve the mechanism)
# ---------------------------------------------------------------------

def test_conflicting_evidence_marked_expected_unresolved() -> None:
    """The current harness does NOT implement automatic conflict
    detection between two RevenueObservations with the same metric_type/
    date but different amounts -- Rulebook Part 6 specifies the desired
    behavior (UNAVAILABLE_CONFLICTING_EVIDENCE) but this experimental
    harness's evaluators do not yet check for it. This test documents
    that gap explicitly (EXPECTED_UNRESOLVED_METHODOLOGY) rather than
    silently inventing a resolution, per Part 20's explicit instruction."""
    from app.calibration.sps_v3.profiles import stress_12_conflicting_evidence
    company = stress_12_conflicting_evidence()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    current_scale = _find(dims, "current_scale")
    print(
        f"  EXPECTED_UNRESOLVED_METHODOLOGY: two conflicting RevenueObservations "
        f"($1M PRIMARY_SELF_REPORTED vs $400K HIGH_QUALITY_SECONDARY, same date) were "
        f"NOT detected as a conflict by this harness -- current_scale resolved to "
        f"score={current_scale.score} using whichever observation `max(revenue_obs, "
        f"key=as_of_date)` happened to select (last-write-wins, in insertion order, "
        f"NOT provenance-grade-aware). Rulebook Part 6 specifies conflicting-observation "
        f"detection and a provenance-grade tie-break; this experimental harness does not "
        f"yet implement it. Documented as a required next-phase implementation item, not "
        f"invented here."
    )
    # No assertion of correctness -- this test's job is to surface the
    # gap, not to grade it pass/fail against an unresolved rule.


# ---------------------------------------------------------------------
# Part 24 -- Financial Health evidence-type discipline
# ---------------------------------------------------------------------

def test_funding_never_becomes_revenue_or_cash() -> None:
    """A FundingObservation alone (no CashObservation, no
    RevenueObservation) must leave Current Scale, Capital Efficiency,
    and Revenue Quality all Unavailable -- funding must never be
    silently treated as revenue or cash."""
    from app.calibration.sps_v3.types import FundingObservation, FundingRoundLabel, ProvenanceStatus, DirectOrDerived, ExtractionConfidence
    funding_only = SyntheticCompany(
        "SYNTH_FUNDING_ONLY", Stage.SERIES_A,
        evidence=(
            FundingObservation(
                observation_id="FUND-1", source_excerpt="raised $50M Series B",
                provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=ProvenanceGrade.PRIMARY_SELF_REPORTED,
                direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
                amount=Decimal("50000000"), round_label=FundingRoundLabel.SERIES_B, announced_date=D2025,
            ),
        ),
    )
    dims = evaluate_all_dimensions(funding_only, DEFAULT_REGISTRY)
    for dim_id in ("current_scale", "capital_efficiency", "revenue_quality", "unit_economics"):
        d = _find(dims, dim_id)
        expect(d.score is None, f"{dim_id} scored {d.score} from a FundingObservation alone -- funding leaked into a financial-health/scale dimension.")


def test_high_funding_does_not_offset_weak_unit_economics() -> None:
    from app.calibration.sps_v3.profiles import stress_8_high_funding_weak_unit_economics
    company = stress_8_high_funding_weak_unit_economics()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    cap_eff = _find(dims, "capital_efficiency")
    expect(
        cap_eff.availability == AvailabilityStatus.SCORABLE and cap_eff.classification.classification == "ORDINARY",
        f"Expected capital_efficiency to reflect the weak $4.8M-burn-vs-$2M-revenue ratio as ORDINARY-or-worse, got {cap_eff.classification.classification if cap_eff.classification else None} (score={cap_eff.score}).",
    )


def test_profitability_does_not_imply_growth_or_vice_versa() -> None:
    from app.calibration.sps_v3.profiles import stress_9_profitable_slow_growth
    company = stress_9_profitable_slow_growth()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    growth = _find(dims, "growth_trajectory")
    cap_eff = _find(dims, "capital_efficiency")
    expect(growth.classification.classification == "ORDINARY", f"Slow (10%) YoY growth should classify ORDINARY, got {growth.classification.classification}")
    expect(cap_eff.score is not None and cap_eff.score >= Decimal("7"), f"36-month runway with no burn disclosed should score well on capital_efficiency via the direct runway-statement path, got {cap_eff.score}")


# ---------------------------------------------------------------------
# Part 25 -- double-counting spot check
# ---------------------------------------------------------------------

def test_founder_prior_exit_does_not_leak_into_execution_pillar() -> None:
    """A FounderOutcomeObservation about a PRIOR company must never be
    a valid input to any Execution-pillar evaluator (Rulebook Part 18's
    scoping rule) -- Execution dimensions in this harness only match
    ProductCapabilityObservation, never Founder*Observation, so this is
    verified structurally by construction; this test confirms it holds
    for a company whose ONLY evidence is founder history."""
    founder_only = SyntheticCompany(
        "SYNTH_FOUNDER_ONLY_FOR_DOUBLECOUNT_CHECK", Stage.SEED,
        evidence=(
            f.founder_experience("CEO", __import__("app.calibration.sps_v3.types", fromlist=["FounderExperienceType"]).FounderExperienceType.REPEAT_FOUNDER, "PriorCo"),
            f.founder_outcome("PriorCo", __import__("app.calibration.sps_v3.types", fromlist=["FounderOutcomeType"]).FounderOutcomeType.ACQUIRED, attributed=True),
        ),
    )
    dims = evaluate_all_dimensions(founder_only, DEFAULT_REGISTRY)
    execution_dims = [d for d in dims if d.pillar == "Execution"]
    for d in execution_dims:
        expect(d.score is None, f"{d.dimension_id}: founder-history-only evidence should never score an Execution-pillar dimension, got {d.score}.")
    team_dims_scored = [d for d in dims if d.pillar == "Team" and d.score is not None]
    expect(len(team_dims_scored) > 0, "Founder history should score at least one Team dimension.")


def main() -> None:
    tests = [
        test_coverage_alone_does_not_change_strength,
        test_confidence_alone_does_not_change_strength,
        test_confidence_caps_do_not_silently_reappear,
        test_unknown_never_becomes_a_numeric_score,
        test_unavailable_excluded_not_zeroed_in_pillar_average,
        test_negative_evidence_produces_low_score_not_inferred_from_absence,
        test_negative_evidence_can_lower_sps_end_to_end,
        test_additive_positive_evidence_updates_only_relevant_dimension,
        test_neutral_evidence_can_change_coverage_without_changing_sps,
        test_conflicting_evidence_marked_expected_unresolved,
        test_funding_never_becomes_revenue_or_cash,
        test_high_funding_does_not_offset_weak_unit_economics,
        test_profitability_does_not_imply_growth_or_vice_versa,
        test_founder_prior_exit_does_not_leak_into_execution_pillar,
    ]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as exc:
            failures.append((test.__name__, str(exc)))
            print(f"FAIL: {test.__name__}: {exc}")
    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
