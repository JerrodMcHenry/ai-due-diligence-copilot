"""
Phase 10.8F -- Traction matrix, renormalization attack, pillar
ablation, scale reachability, upper/lower tail, monotonicity,
boundary, sensitivity, weight sensitivity, classification-error
sensitivity, provenance-error sensitivity, explanation trace,
reproducibility snapshot (Rulebook/Calibration-Plan Parts 13, 22-39).

Run with:
    python -m app.calibration.sps_v3.tests.test_aggregation_and_tails
"""

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.calibration.sps_v3 import factory as f
from app.calibration.sps_v3.aggregation import evaluate_sps, evaluate_pillar, compute_pillar_strength
from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.evaluators import evaluate_all_dimensions, DIMENSION_PILLARS, PILLAR_WEIGHTS
from app.calibration.sps_v3.profiles import CORE_PROFILES
from app.calibration.sps_v3.registry import DEFAULT_REGISTRY, build_default_registry
from app.calibration.sps_v3.types import (
    AvailabilityStatus,
    CustomerType,
    FounderExperienceType,
    FounderOutcomeType,
    MarketEstimateSourceType,
    ProvenanceGrade,
    RevenueMetricType,
    Stage,
)

D2019 = date(2019, 1, 1)
D2024 = date(2024, 1, 1)
D2025 = date(2025, 1, 1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _find(dims, dim_id):
    return next(d for d in dims if d.dimension_id == dim_id)


# ---------------------------------------------------------------------
# Part 13/23 -- Traction evidence-type discipline
# ---------------------------------------------------------------------

def test_one_arr_point_supports_scale_not_growth() -> None:
    company = SyntheticCompany("SYNTH_ONE_ARR_POINT", Stage.SEED, evidence=(f.revenue("500000", D2025, RevenueMetricType.ARR),))
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    scale = _find(dims, "current_scale")
    growth = _find(dims, "growth_trajectory")
    expect(scale.availability == AvailabilityStatus.SCORABLE, "One ARR point should support Current Scale.")
    expect(growth.availability == AvailabilityStatus.UNAVAILABLE_INSUFFICIENT, f"One ARR point must NOT support Growth Trajectory, got {growth.availability}")


def test_two_arr_points_support_growth() -> None:
    company = SyntheticCompany(
        "SYNTH_TWO_ARR_POINTS", Stage.SEED,
        evidence=(f.revenue("500000", D2025, RevenueMetricType.ARR), f.revenue("250000", D2024, RevenueMetricType.ARR)),
    )
    growth = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "growth_trajectory")
    expect(growth.availability == AvailabilityStatus.SCORABLE, "Two dated ARR points should support Growth Trajectory.")


def test_customer_count_supports_adoption_not_retention() -> None:
    company = SyntheticCompany("SYNTH_10K_CUSTOMERS", Stage.SERIES_A, evidence=(f.customer_count(10000, D2025, CustomerType.PAYING),))
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    expect(_find(dims, "customer_adoption").availability == AvailabilityStatus.SCORABLE, "10,000 customers should support Customer Adoption.")
    expect(_find(dims, "retention_engagement").availability == AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE, "Customer count alone must not support Retention/Engagement.")


def test_retention_supports_retention_not_adoption_breadth() -> None:
    company = SyntheticCompany("SYNTH_HIGH_RETENTION_ONLY", Stage.SERIES_A, evidence=(f.retention(nrr="130"),))
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    expect(_find(dims, "retention_engagement").availability == AvailabilityStatus.SCORABLE, "High retention should support Retention/Engagement.")
    expect(_find(dims, "customer_adoption").availability == AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE, "Retention data alone must not support Customer Adoption breadth.")


def test_signed_pilot_supports_commercial_validation_distinct_from_paying() -> None:
    pilot_company = SyntheticCompany("SYNTH_PILOT_ONLY", Stage.SEED, evidence=(f.commercial_contract(CustomerType.PILOT, "PilotCo"),))
    d = _find(evaluate_all_dimensions(pilot_company, DEFAULT_REGISTRY), "commercial_validation")
    expect(d.availability == AvailabilityStatus.SCORABLE, "A signed pilot should support Commercial Validation.")
    expect(d.classification.classification == "SINGLE_SIGNAL", f"A single pilot should classify as SINGLE_SIGNAL, not a stronger tier automatically equal to a paying customer, got {d.classification.classification}")


# ---------------------------------------------------------------------
# Part 26 -- renormalization attack
# ---------------------------------------------------------------------

def test_one_exceptional_dimension_does_not_single_handedly_create_exceptional_pillar() -> None:
    """A pillar with exactly the minimum 2 scorable dimensions -- one
    COMPREHENSIVE, one SINGLE_SIGNAL -- must show a MODERATE strength,
    not an inflated one; and a pillar below the minimum dimension count
    must not publish at all regardless of how strong the one dimension is."""
    one_dim_only = SyntheticCompany(
        "SYNTH_ONE_EXCEPTIONAL_DIM_ONLY", Stage.SERIES_A,
        evidence=tuple(f.competitor(f"C{i}", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY) for i in range(4)),
    )
    pillar = evaluate_pillar("Market", evaluate_all_dimensions(one_dim_only, DEFAULT_REGISTRY), DEFAULT_REGISTRY)
    expect(not pillar.publishable, f"A pillar with only 1 scorable dimension (however strong) must not publish; got publishable={pillar.publishable}")

    two_dims_mixed = SyntheticCompany(
        "SYNTH_TWO_DIM_MIXED_STRENGTH", Stage.SERIES_A,
        evidence=tuple(f.competitor(f"C{i}", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY) for i in range(4))
        + (f.market_size("100000000", "small segment"),),
    )
    pillar2 = evaluate_pillar("Market", evaluate_all_dimensions(two_dims_mixed, DEFAULT_REGISTRY), DEFAULT_REGISTRY)
    expect(pillar2.publishable, "2 scorable dimensions should meet the minimum and publish.")
    expect(
        Decimal("6") <= pillar2.strength <= Decimal("8"),
        f"A COMPREHENSIVE(9.5)+SINGLE_SIGNAL(5.5) pair should average to a moderate ~7.5-ish strength, not be inflated toward 9.5 by the one strong dimension alone; got {pillar2.strength}",
    )


def test_one_weak_dimension_does_not_unfairly_crater_a_pillar() -> None:
    strong_4 = tuple(f.competitor(f"C{i}", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY) for i in range(4))
    weak_1 = (f.market_size("1000", "trivially tiny"),)  # SINGLE_SIGNAL band, not negative -- still positive-ish
    company = SyntheticCompany("SYNTH_ONE_WEAK_AMONG_STRONG", Stage.SERIES_A, evidence=strong_4 + weak_1)
    pillar = evaluate_pillar("Market", evaluate_all_dimensions(company, DEFAULT_REGISTRY), DEFAULT_REGISTRY)
    expect(pillar.strength > Decimal("6"), f"One ordinary (not negative) dimension among 2 strong ones should not crater pillar strength below 6, got {pillar.strength}")


# ---------------------------------------------------------------------
# Part 27 -- pillar ablation
# ---------------------------------------------------------------------

def test_pillar_ablation_one_at_a_time() -> None:
    full = CORE_PROFILES["A"]()
    dims_full = evaluate_all_dimensions(full, DEFAULT_REGISTRY)
    sps_full = evaluate_sps(dims_full, full.stage, DEFAULT_REGISTRY)
    expect(sps_full.publishable, "Baseline profile A must be publishable for ablation to be meaningful.")

    results = {}
    for pillar in PILLAR_WEIGHTS:
        ablated_dims = tuple(
            replace(d, score=None, availability=AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE, classification=None)
            if d.pillar == pillar else d
            for d in dims_full
        )
        sps_ablated = evaluate_sps(ablated_dims, full.stage, DEFAULT_REGISTRY)
        results[pillar] = sps_ablated
        print(f"  Ablate {pillar:<18}: SPS={sps_ablated.sps} publishable={sps_ablated.publishable} reason={sps_ablated.withhold_reason}")

    # No single-pillar ablation should be able to move SPS by more than
    # ~half the ablated pillar's own weight-equivalent points (a crude
    # sanity bound -- flags a genuinely disproportionate swing as a
    # finding, does not assert an exact number).
    for pillar, result in results.items():
        if result.sps is not None and sps_full.sps is not None:
            delta = abs(sps_full.sps - result.sps)
            max_reasonable = PILLAR_WEIGHTS[pillar] * Decimal("10") * Decimal("1.5")
            if delta > max_reasonable:
                print(f"  FINDING: ablating {pillar} moved SPS by {delta} points, more than the crude {max_reasonable}-point sanity bound for a {PILLAR_WEIGHTS[pillar]*100}%-weighted pillar.")


# ---------------------------------------------------------------------
# Part 28/29/30 -- scale reachability, upper tail, lower tail
# ---------------------------------------------------------------------

def _build_saturated_company(negative: bool = False) -> SyntheticCompany:
    evidence = []
    for i in range(4):
        evidence.append(f.market_size(f"{5000000000+i}", f"segment {i}", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY))
        evidence.append(f.market_growth(f"{40+i}", f"category growth {i}", ProvenanceGrade.HIGH_QUALITY_SECONDARY))
        evidence.append(f.competitor(f"Competitor{i}", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY))
        evidence.append(f.customer_evidence(f"named outcome {i}", f"Customer{i}", quantified=True))
        evidence.append(f.founder_experience(f"CEO role {i}", FounderExperienceType.DIRECT_DOMAIN))
        evidence.append(f.founder_experience(f"technical lead {i}", FounderExperienceType.DIRECT_DOMAIN))
        evidence.append(f.founder_experience(f"leadership exec {i}", FounderExperienceType.DIRECT_DOMAIN))
        evidence.append(f.product_capability(f"defensib moat {i}", shipped=True))
        evidence.append(f.product_capability(f"expansion path {i}", shipped=True))
        evidence.append(f.product_capability(f"gtm channel {i}", shipped=True))
        evidence.append(f.product_capability(f"strategy wedge {i}", shipped=True))
        evidence.append(f.product_capability(f"process cadence {i}", shipped=True))
        evidence.append(f.product_capability(f"shipped core {i}", shipped=True, integration=f"Integration{i}"))
        evidence.append(f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, f"ContractCo{i}", renewal=True))
    evidence.append(f.founder_outcome("PriorCo", FounderOutcomeType.ACQUIRED, attributed=True))
    evidence.append(f.founder_outcome("SecondPriorCo", FounderOutcomeType.IPO, attributed=True))
    evidence.append(f.founder_outcome("ThirdPriorCo", FounderOutcomeType.ACQUIRED, attributed=True))
    evidence.append(f.founder_outcome("FourthPriorCo", FounderOutcomeType.IPO, attributed=True))
    evidence.append(f.revenue("3000000", D2025, RevenueMetricType.ARR))
    evidence.append(f.revenue("500000", D2024, RevenueMetricType.ARR))
    for i in range(4):
        evidence.append(f.customer_count(200 + i, D2025, CustomerType.PAYING))
        evidence.append(f.retention(nrr=str(130 + i)))
    evidence.append(f.runway_statement("30"))
    return SyntheticCompany("SYNTH_MAX_SATURATED_TEST", Stage.SERIES_A, evidence=tuple(evidence))


def test_upper_tail_90_plus_reachable_with_maximal_evidence() -> None:
    company = _build_saturated_company()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    result = evaluate_sps(dims, company.stage, DEFAULT_REGISTRY)
    print(f"  Maximally-saturated synthetic profile: SPS={result.sps}")
    expect(result.publishable, "Maximally-saturated profile should be publishable.")
    expect(result.sps >= Decimal("90"), f"90+ was NOT reached even by a maximally-saturated synthetic profile: SPS={result.sps} -- see report for exact mathematical cause if this fails.")


def test_lower_tail_below_50_and_below_40_reachable() -> None:
    evidence = [f.revenue("1000000", D2024, RevenueMetricType.ARR), f.revenue("1000000", D2025, RevenueMetricType.ARR), f.customer_count(50, D2025, CustomerType.PAYING), f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN)]
    negatives = [f.negative_signal("demonstrated_weakness", dim_id, "SEVERE") for dim_id in DIMENSION_PILLARS]
    company = SyntheticCompany("SYNTH_MAX_NEGATIVE_TEST", Stage.SERIES_A, evidence=tuple(evidence), negative_signals=tuple(negatives))
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    result = evaluate_sps(dims, company.stage, DEFAULT_REGISTRY)
    print(f"  Maximally-negative synthetic profile: SPS={result.sps}")
    expect(result.sps < Decimal("50"), f"Below-50 not reached by maximal negative evidence: SPS={result.sps}")
    expect(result.sps < Decimal("40"), f"Below-40 not reached by maximal negative evidence: SPS={result.sps}")


def test_lower_tail_below_20_requires_lower_provisional_band() -> None:
    """Documents (does not assert pass/fail against an uncalibrated
    number) whether 0-19 is reachable under the DEFAULT provisional
    band.negative_signal=2.0, and confirms it becomes reachable with a
    lower provisional value -- a CALIBRATION_REQUIRED finding, not a
    structural defect, since the provisional value is explicitly
    marked non-final."""
    evidence = [f.revenue("1000000", D2024, RevenueMetricType.ARR), f.revenue("1000000", D2025, RevenueMetricType.ARR), f.customer_count(50, D2025, CustomerType.PAYING), f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN)]
    negatives = [f.negative_signal("demonstrated_weakness", dim_id, "SEVERE") for dim_id in DIMENSION_PILLARS]
    company = SyntheticCompany("SYNTH_MAX_NEGATIVE_LOWERBAND_TEST", Stage.SERIES_A, evidence=tuple(evidence), negative_signals=tuple(negatives))

    default_result = evaluate_sps(evaluate_all_dimensions(company, DEFAULT_REGISTRY), company.stage, DEFAULT_REGISTRY)
    print(f"  Default band.negative_signal=2.0: SPS={default_result.sps} (0-19 reached: {default_result.sps < Decimal('20') if default_result.sps is not None else 'N/A'})")

    lowered_registry = DEFAULT_REGISTRY.with_override("band.negative_signal", Decimal("1.0"))
    lowered_result = evaluate_sps(evaluate_all_dimensions(company, lowered_registry), company.stage, lowered_registry)
    print(f"  Lowered band.negative_signal=1.0:  SPS={lowered_result.sps}")
    expect(lowered_result.sps < Decimal("20"), f"Even with a lower provisional band, 0-19 was not reached: SPS={lowered_result.sps}")


def test_scale_reachability_all_seven_bands() -> None:
    """Uses ONLY the profiles/fixtures already built (never hand-assigns
    a dimension score directly) to check which of the 7 canonical bands
    are reachable under current provisional parameters."""
    candidates = {
        "0-19": (SyntheticCompany("SYNTH_BAND_0_19", Stage.SERIES_A,
                                   evidence=(f.revenue("1000000", D2024, RevenueMetricType.ARR), f.revenue("1000000", D2025, RevenueMetricType.ARR), f.customer_count(50, D2025, CustomerType.PAYING), f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN)),
                                   negative_signals=tuple(f.negative_signal("demonstrated_weakness", dim_id, "SEVERE") for dim_id in DIMENSION_PILLARS)),
                 DEFAULT_REGISTRY.with_override("band.negative_signal", Decimal("1.0"))),
        "20-39": (SyntheticCompany("SYNTH_BAND_20_39", Stage.SERIES_A,
                                    evidence=(f.revenue("1000000", D2024, RevenueMetricType.ARR), f.revenue("1000000", D2025, RevenueMetricType.ARR), f.customer_count(50, D2025, CustomerType.PAYING), f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN)),
                                    negative_signals=tuple(f.negative_signal("demonstrated_weakness", dim_id, "SEVERE") for dim_id in DIMENSION_PILLARS)),
                  DEFAULT_REGISTRY),
        "40-59": (CORE_PROFILES["J"](), DEFAULT_REGISTRY),
        "60-69": (CORE_PROFILES["I"](), DEFAULT_REGISTRY),
        "70-79": None,   # attempted below via interpolation
        "80-89": None,
        "90-100": (_build_saturated_company(), DEFAULT_REGISTRY),
    }

    results = {}
    for band, entry in candidates.items():
        if entry is None:
            continue
        company, registry = entry
        r = evaluate_sps(evaluate_all_dimensions(company, registry), company.stage, registry)
        results[band] = r.sps
        print(f"  Band target {band}: got SPS={r.sps} (publishable={r.publishable})")

    # 70-79 and 80-89: interpolate by partially saturating (2 of 4 repeats).
    for target_band, repeat_count in (("70-79", 2), ("80-89", 3)):
        evidence = []
        for i in range(repeat_count):
            evidence.append(f.market_size(f"{5000000000+i}", f"segment {i}", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY))
            evidence.append(f.competitor(f"Competitor{i}", differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY))
            evidence.append(f.founder_experience(f"CEO role {i}", FounderExperienceType.DIRECT_DOMAIN))
            evidence.append(f.product_capability(f"shipped core {i}", shipped=True, integration=f"Integration{i}"))
            evidence.append(f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, f"ContractCo{i}", renewal=True))
        evidence.append(f.revenue("2000000", D2025, RevenueMetricType.ARR))
        evidence.append(f.revenue("1000000", D2024, RevenueMetricType.ARR))
        evidence.append(f.customer_count(150, D2025, CustomerType.PAYING))
        evidence.append(f.retention(nrr="115"))
        evidence.append(f.runway_statement("20"))
        company = SyntheticCompany(f"SYNTH_BAND_{target_band.replace('-', '_')}", Stage.SERIES_A, evidence=tuple(evidence))
        r = evaluate_sps(evaluate_all_dimensions(company, DEFAULT_REGISTRY), company.stage, DEFAULT_REGISTRY)
        results[target_band] = r.sps
        print(f"  Band target {target_band} (interpolated, {repeat_count}x signals): got SPS={r.sps} (publishable={r.publishable})")

    unreached = []
    band_ranges = {"0-19": (0, 19), "20-39": (20, 39), "40-59": (40, 59), "60-69": (60, 69), "70-79": (70, 79), "80-89": (80, 89), "90-100": (90, 100)}
    for band, (lo, hi) in band_ranges.items():
        sps = results.get(band)
        if sps is None or not (Decimal(lo) <= sps <= Decimal(hi)):
            unreached.append(f"{band} (attempted, landed at {sps})")
    print(f"  Bands not precisely hit by these specific attempts: {unreached if unreached else 'none -- all 7 bands reached by some constructed profile'}")


# ---------------------------------------------------------------------
# Part 31 -- monotonicity
# ---------------------------------------------------------------------

def test_retention_monotonicity() -> None:
    low = SyntheticCompany("SYNTH_MONO_RETENTION_LOW", Stage.SERIES_A, evidence=(f.retention(nrr="90"),))
    high = SyntheticCompany("SYNTH_MONO_RETENTION_HIGH", Stage.SERIES_A, evidence=(f.retention(nrr="140"),))
    d_low = _find(evaluate_all_dimensions(low, DEFAULT_REGISTRY), "retention_engagement")
    d_high = _find(evaluate_all_dimensions(high, DEFAULT_REGISTRY), "retention_engagement")
    expect(d_high.score >= d_low.score, f"Higher NRR should never score lower: 90%->{d_low.score}, 140%->{d_high.score}")


def test_runway_monotonicity() -> None:
    short = SyntheticCompany("SYNTH_MONO_RUNWAY_SHORT", Stage.SERIES_A, evidence=(f.runway_statement("10"),))
    long_ = SyntheticCompany("SYNTH_MONO_RUNWAY_LONG", Stage.SERIES_A, evidence=(f.runway_statement("30"),))
    d_short = _find(evaluate_all_dimensions(short, DEFAULT_REGISTRY), "capital_efficiency")
    d_long = _find(evaluate_all_dimensions(long_, DEFAULT_REGISTRY), "capital_efficiency")
    expect(d_long.score >= d_short.score, f"Longer runway should never score lower: 10mo->{d_short.score}, 30mo->{d_long.score}")


def test_market_size_not_monotonic_at_extreme_and_that_is_correct() -> None:
    """Documents, does not assert failure: this harness's Market Size
    evaluator has NO upper-bound sanity check -- an absurdly large
    market_size figure still classifies via signal COUNT, not magnitude,
    so 'larger is better without limit' is not actually modeled (which
    is correct per Rulebook Part 30, Test 11's own instruction that
    market size should not be treated as infinitely better) -- but this
    also means the evaluator does not distinguish a $5B market from a
    $5T one at all, since only the signal COUNT (not the magnitude)
    drives the classification tier. Flagged as a CALIBRATION_REQUIRED
    scope gap: no magnitude-aware banding exists for Market Size in
    this harness, unlike Current Scale's stage-relative dollar bands."""
    small = SyntheticCompany("SYNTH_MONO_MKT_SMALL", Stage.SERIES_A, evidence=(f.market_size("100000000", "s"),))
    huge = SyntheticCompany("SYNTH_MONO_MKT_HUGE", Stage.SERIES_A, evidence=(f.market_size("100000000000000", "s"),))
    d_small = _find(evaluate_all_dimensions(small, DEFAULT_REGISTRY), "market_size")
    d_huge = _find(evaluate_all_dimensions(huge, DEFAULT_REGISTRY), "market_size")
    print(f"  FINDING: Market Size evaluator gives identical score ({d_small.score} vs {d_huge.score}) to a $100M and a $100T market -- no magnitude-aware banding implemented, only signal-count-based classification. CALIBRATION REQUIRED / scope gap for a future pass.")


# ---------------------------------------------------------------------
# Part 32 -- boundary tests
# ---------------------------------------------------------------------

def test_current_scale_stage_boundary_discontinuity() -> None:
    registry = DEFAULT_REGISTRY
    ceiling = registry.value("traction.current_scale.seed.arr_ordinary_ceiling")
    just_below = SyntheticCompany("SYNTH_BOUNDARY_JUST_BELOW", Stage.SEED, evidence=(f.revenue(str(ceiling - 1), D2025, RevenueMetricType.ARR),))
    at = SyntheticCompany("SYNTH_BOUNDARY_AT", Stage.SEED, evidence=(f.revenue(str(ceiling), D2025, RevenueMetricType.ARR),))
    just_above = SyntheticCompany("SYNTH_BOUNDARY_JUST_ABOVE", Stage.SEED, evidence=(f.revenue(str(ceiling + 1), D2025, RevenueMetricType.ARR),))
    scores = {
        "just_below": _find(evaluate_all_dimensions(just_below, registry), "current_scale").score,
        "at": _find(evaluate_all_dimensions(at, registry), "current_scale").score,
        "just_above": _find(evaluate_all_dimensions(just_above, registry), "current_scale").score,
    }
    print(f"  Current Scale (Seed) boundary at ARR={ceiling}: {scores}")
    jump = scores["just_above"] - scores["just_below"]
    print(f"  Discontinuity at the ordinary/strong boundary: {jump} points for a $2 ARR difference -- a real cliff, inherent to discrete banding (Rulebook Part 8's chosen granularity), not a bug.")


# ---------------------------------------------------------------------
# Part 33 -- sensitivity analysis
# ---------------------------------------------------------------------

def test_sensitivity_of_overall_coverage_floor() -> None:
    company = CORE_PROFILES["D"]()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    param = DEFAULT_REGISTRY.get("gate.overall_coverage_floor_pct")
    lo, hi = param.sensitivity_range
    print(f"  Sensitivity of gate.overall_coverage_floor_pct (baseline={param.value}, range {lo}-{hi}) on profile D:")
    for candidate in (lo, param.value, hi):
        r_registry = DEFAULT_REGISTRY.with_override("gate.overall_coverage_floor_pct", candidate)
        r = evaluate_sps(evaluate_all_dimensions(company, r_registry), company.stage, r_registry)
        print(f"    floor={candidate}: publishable={r.publishable} sps={r.sps}")


def test_sensitivity_of_band_values() -> None:
    company = CORE_PROFILES["A"]()
    for param_name in ("band.single_signal", "band.multiple_signals", "band.comprehensive"):
        param = DEFAULT_REGISTRY.get(param_name)
        lo, hi = param.sensitivity_range
        results = []
        for candidate in (lo, param.value, hi):
            r_registry = DEFAULT_REGISTRY.with_override(param_name, candidate)
            r = evaluate_sps(evaluate_all_dimensions(company, r_registry), company.stage, r_registry)
            results.append((candidate, r.sps))
        spread = results[-1][1] - results[0][1] if all(x[1] is not None for x in results) else None
        print(f"  Sensitivity of {param_name} (range {lo}-{hi}) on profile A's SPS: {results} -> spread={spread}")


# ---------------------------------------------------------------------
# Part 34 -- pillar weight sensitivity (NOT changing production weights
# -- this only perturbs the LOCAL evaluate_sps call for measurement)
# ---------------------------------------------------------------------

def test_pillar_weight_sensitivity() -> None:
    """Measures ranking stability, NOT a recommendation to change
    weights. Perturbs Financial Health's weight (smallest, most
    private-data-dependent pillar) +/-50% relative and observes SPS
    movement across profiles A/D/E, keeping all OTHER weights fixed and
    renormalizing to sum to 1.0 for the perturbed trial only."""
    import app.calibration.sps_v3.aggregation as agg_module
    original_weights = dict(PILLAR_WEIGHTS)
    for label, new_fh_weight in (("baseline", Decimal("0.10")), ("halved", Decimal("0.05")), ("doubled", Decimal("0.20"))):
        perturbed = dict(original_weights)
        perturbed["Financial Health"] = new_fh_weight
        total = sum(perturbed.values())
        perturbed = {k: v / total for k, v in perturbed.items()}
        agg_module.PILLAR_WEIGHTS = perturbed
        try:
            for key in ("A", "D", "E"):
                company = CORE_PROFILES[key]()
                r = evaluate_sps(evaluate_all_dimensions(company, DEFAULT_REGISTRY), company.stage, DEFAULT_REGISTRY)
                print(f"  Financial Health weight={label} ({new_fh_weight}): profile {key} SPS={r.sps}")
        finally:
            agg_module.PILLAR_WEIGHTS = original_weights
    expect(agg_module.PILLAR_WEIGHTS == original_weights, "Pillar weight perturbation leaked outside the test -- production weights must be restored.")


# ---------------------------------------------------------------------
# Part 35 -- classification error sensitivity
# ---------------------------------------------------------------------

def test_classification_error_sensitivity_one_level() -> None:
    """Moving a dimension's classification one adjacent tier changes
    its score by exactly one band-gap; measures which dimensions'
    pillar-level impact is disproportionate (high weight + high
    band-gap)."""
    tiers = [
        ("SINGLE_SIGNAL", DEFAULT_REGISTRY.value("band.single_signal")),
        ("MULTIPLE_SIGNALS", DEFAULT_REGISTRY.value("band.multiple_signals")),
        ("COMPREHENSIVE", DEFAULT_REGISTRY.value("band.comprehensive")),
    ]
    for i in range(len(tiers) - 1):
        gap = tiers[i + 1][1] - tiers[i][1]
        print(f"  One-level classification error {tiers[i][0]}->{tiers[i+1][0]}: {gap}-point dimension-score delta.")
    # Weighted by the single highest-weight dimension in the methodology
    # (Runway family / Founder-Market Fit-shaped 0.25-0.35 range) to show
    # the worst-case single-dimension pillar impact:
    max_dim_weight = Decimal("0.35")
    worst_case_pillar_delta = max_dim_weight * (tiers[2][1] - tiers[0][1])
    print(f"  Worst-case pillar-level delta from a 2-level classification miss on the highest-weighted (0.35) dimension: {worst_case_pillar_delta} points.")


# ---------------------------------------------------------------------
# Part 36 -- provenance error sensitivity
# ---------------------------------------------------------------------

def test_provenance_downgrade_does_not_collapse_strength_only_confidence() -> None:
    for grade in (ProvenanceGrade.PRIMARY_VERIFIED, ProvenanceGrade.HIGH_QUALITY_SECONDARY, ProvenanceGrade.SECONDARY_ESTIMATE):
        company = SyntheticCompany(f"SYNTH_PROVENANCE_{grade.value}", Stage.SERIES_A, evidence=(f.market_size("1000000000", "s", grade=grade),))
        d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "market_size")
        print(f"  provenance={grade.value}: score={d.score} confidence={d.confidence.value}")
        expect(d.score == DEFAULT_REGISTRY.value("band.single_signal"), f"Strength changed with provenance grade alone at {grade.value}: {d.score}")


# ---------------------------------------------------------------------
# Part 38 -- explanation trace reconstruction
# ---------------------------------------------------------------------

def test_explanation_trace_reconstructs_pillar_strength() -> None:
    company = CORE_PROFILES["A"]()
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    for pillar in PILLAR_WEIGHTS:
        pillar_dims = [d for d in dims if d.pillar == pillar]
        scorable = [d for d in pillar_dims if d.score is not None]
        if not scorable:
            continue
        reconstructed = sum(d.score * d.weight for d in scorable) / sum(d.weight for d in scorable)
        actual = compute_pillar_strength(tuple(pillar_dims))
        expect(
            abs(reconstructed.quantize(Decimal("0.01")) - actual) < Decimal("0.02"),
            f"{pillar}: reconstructed strength {reconstructed} from the trace's own (score, weight) pairs does not match the actual computed strength {actual} -- the trace is not sufficient to reconstruct the number.",
        )
        for d in scorable:
            expect(d.rule_trace.rule_id, f"{pillar}/{d.dimension_id}: missing rule_id in trace.")
            expect(d.cited_evidence_ids, f"{pillar}/{d.dimension_id}: a scored dimension has no cited evidence ids in its trace.")


# ---------------------------------------------------------------------
# Part 39 -- reproducibility snapshot
# ---------------------------------------------------------------------

# Phase 10.8G, Part 32: a NEW post-amendment snapshot, distinct from
# the preserved pre-amendment baseline
# (snapshot_baseline_10_8F_preamendment.json, copied verbatim from
# 10.8F before any amendment code ran -- never overwritten). Scoring
# behavior legitimately changed between 10.8F and 10.8G (the
# redundant-evidence fix alone moved several profiles' SPS), so a new
# snapshot filename is required rather than silently overwriting the
# old one in place.
SNAPSHOT_PATH = "app/calibration/sps_v3/tests/snapshot_baseline_10_8G_postamendment.json"


def _snapshot_dict(company: SyntheticCompany) -> dict:
    dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
    result = evaluate_sps(dims, company.stage, DEFAULT_REGISTRY)
    return {
        "company_id": company.company_id,
        "sps": str(result.sps) if result.sps is not None else None,
        "publishable": result.publishable,
        "coverage": str(result.coverage.overall_pct),
        "confidence": result.confidence.overall.value,
        "dimensions": {d.dimension_id: {"score": str(d.score) if d.score is not None else None, "availability": d.availability.value} for d in dims},
    }


def test_reproducibility_snapshot() -> None:
    import os
    snapshot = {key: _snapshot_dict(builder()) for key, builder in CORE_PROFILES.items()}
    if not os.path.exists(SNAPSHOT_PATH):
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, sort_keys=True)
        print(f"  Baseline snapshot written to {SNAPSHOT_PATH} (first run).")
        return
    with open(SNAPSHOT_PATH, encoding="utf-8") as fh:
        baseline = json.load(fh)
    expect(snapshot == baseline, "Reproducibility snapshot mismatch -- re-running the harness produced a different result than the recorded baseline.")
    print("  Snapshot matches recorded baseline.")


def main() -> None:
    tests = [
        test_one_arr_point_supports_scale_not_growth,
        test_two_arr_points_support_growth,
        test_customer_count_supports_adoption_not_retention,
        test_retention_supports_retention_not_adoption_breadth,
        test_signed_pilot_supports_commercial_validation_distinct_from_paying,
        test_one_exceptional_dimension_does_not_single_handedly_create_exceptional_pillar,
        test_one_weak_dimension_does_not_unfairly_crater_a_pillar,
        test_pillar_ablation_one_at_a_time,
        test_upper_tail_90_plus_reachable_with_maximal_evidence,
        test_lower_tail_below_50_and_below_40_reachable,
        test_lower_tail_below_20_requires_lower_provisional_band,
        test_scale_reachability_all_seven_bands,
        test_retention_monotonicity,
        test_runway_monotonicity,
        test_market_size_not_monotonic_at_extreme_and_that_is_correct,
        test_current_scale_stage_boundary_discontinuity,
        test_sensitivity_of_overall_coverage_floor,
        test_sensitivity_of_band_values,
        test_pillar_weight_sensitivity,
        test_classification_error_sensitivity_one_level,
        test_provenance_downgrade_does_not_collapse_strength_only_confidence,
        test_explanation_trace_reconstructs_pillar_strength,
        test_reproducibility_snapshot,
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
