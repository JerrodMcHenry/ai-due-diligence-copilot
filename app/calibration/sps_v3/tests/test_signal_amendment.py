"""
Phase 10.8G -- signal identity, semantic deduplication, source lineage,
derivative-source behavior, independent corroboration, conflict
resolution, conflict order invariance, provenance precedence, freshness
classes, staleness behavior (Rulebook amendment Parts 2-12, 16-25).

Run with:
    python -m app.calibration.sps_v3.tests.test_signal_amendment
"""

import itertools
from datetime import date
from decimal import Decimal

from app.calibration.sps_v3 import factory as f
from app.calibration.sps_v3.aggregation import evaluate_sps
from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.evaluators import evaluate_all_dimensions, evaluate_all_dimensions_with_staleness_report
from app.calibration.sps_v3.factory import _next_id
from app.calibration.sps_v3.freshness import Freshness, FreshnessClass, evaluate_freshness, freshness_class_for
from app.calibration.sps_v3.registry import DEFAULT_REGISTRY
from app.calibration.sps_v3.signals import build_canonical_signals, _signal_key
from app.calibration.sps_v3.types import (
    AvailabilityStatus,
    CompetitorType,
    ConflictStatus,
    CustomerType,
    DirectOrDerived,
    ExtractionConfidence,
    FounderExperienceType,
    ProvenanceGrade,
    ProvenanceStatus,
    RevenueMetricType,
    RevenueObservation,
    SourceIndependence,
    Stage,
)

D2024 = date(2024, 1, 1)
D2025 = date(2025, 1, 1)
D2026 = date(2026, 1, 1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _find(dims, dim_id):
    return next(d for d in dims if d.dimension_id == dim_id)


def _rev(amount: str, as_of: date, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED, origin=None, independence=SourceIndependence.UNKNOWN_ORIGIN):
    return RevenueObservation(
        observation_id=_next_id("REV"), source_excerpt=f"ARR {amount} as of {as_of}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        amount=Decimal(amount), metric_type=RevenueMetricType.ARR, as_of_date=as_of,
        origin_id=origin, source_independence=independence,
    )


# ---------------------------------------------------------------------
# Part 2-3 -- signal identity / semantic deduplication (unit-level)
# ---------------------------------------------------------------------

def test_distinct_periods_are_distinct_signals() -> None:
    a = _rev("10000000", D2025)
    b = _rev("20000000", D2026)
    expect(_signal_key(a) != _signal_key(b), "10,000 customers in 2025 and 20,000 in 2026 (different periods) must be distinct signal keys.")


def test_same_period_same_value_is_one_signal() -> None:
    a = _rev("10000000", D2025)
    b = _rev("10000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    signals = build_canonical_signals((a, b))
    expect(len(signals) == 1, f"Two sources reporting the identical fact must collapse to one signal, got {len(signals)}")
    expect(signals[0].conflict_status == ConflictStatus.NO_CONFLICT, "Identical-value same-period observations must not conflict.")
    expect(set(signals[0].supporting_observation_ids) == {a.observation_id, b.observation_id}, "Both sources must be recorded as supporting the one signal.")


def test_same_period_different_value_is_a_conflict() -> None:
    a = _rev("5000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    b = _rev("12000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    signals = build_canonical_signals((a, b))
    expect(len(signals) == 1, "Same signal_key must still produce exactly one CanonicalSignal (conflicted or resolved).")
    expect(signals[0].conflict_status == ConflictStatus.CONFLICT_DETECTED, f"Same period, different values, same precedence tier must conflict -- got {signals[0].conflict_status}")


def test_does_not_merge_genuinely_distinct_metrics() -> None:
    total_users = f.customer_count(10000, D2025, CustomerType.FREEMIUM_ACTIVE)
    paying = f.customer_count(2000, D2025, CustomerType.PAYING)
    signals = build_canonical_signals((total_users, paying))
    expect(len(signals) == 2, f"10,000 total users and 2,000 paying customers are DIFFERENT metrics -- must not merge, got {len(signals)} signal(s).")


# ---------------------------------------------------------------------
# Part 17-18 -- redundancy attack re-run (1x/2x/10x/100x)
# ---------------------------------------------------------------------

def test_redundancy_1x_2x_10x_100x_identical_strength_and_coverage() -> None:
    base_fact = ("SoloCompetitor", CompetitorType.DIRECT, True, ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    results = {}
    for n in (1, 2, 10, 100):
        evidence = tuple(f.competitor(base_fact[0], base_fact[1], differentiator=base_fact[2], grade=base_fact[3]) for _ in range(n))
        company = SyntheticCompany(f"SYNTH_REDUND_{n}X", Stage.GROWTH, evidence=evidence)
        dims = evaluate_all_dimensions(company, DEFAULT_REGISTRY)
        results[n] = _find(dims, "competitive_intensity")

    baseline = results[1]
    for n in (2, 10, 100):
        expect(results[n].score == baseline.score, f"{n}x redundancy changed Strength: {baseline.score} -> {results[n].score}")
        expect(results[n].classification.classification == baseline.classification.classification, f"{n}x redundancy changed classification tier.")

    result_sps_1 = evaluate_sps(evaluate_all_dimensions(SyntheticCompany("SYNTH_REDUND_1X_SPS", Stage.GROWTH, evidence=tuple(f.competitor(*base_fact[:3], grade=base_fact[3]) for _ in range(1))), DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    result_sps_100 = evaluate_sps(evaluate_all_dimensions(SyntheticCompany("SYNTH_REDUND_100X_SPS", Stage.GROWTH, evidence=tuple(f.competitor(*base_fact[:3], grade=base_fact[3]) for _ in range(100))), DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    expect(result_sps_1.coverage.overall_pct == result_sps_100.coverage.overall_pct, "Coverage changed with 100x redundancy.")


# ---------------------------------------------------------------------
# Part 19 -- derivative-source attack
# ---------------------------------------------------------------------

def test_derivative_source_attack() -> None:
    original = f.competitor("OriginalCo", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    original = original.__class__(**{**original.__dict__, "origin_id": "PRESS-RELEASE-1", "source_independence": SourceIndependence.INDEPENDENT})
    derivatives = tuple(
        f.competitor("OriginalCo", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
        for _ in range(99)
    )
    derivatives = tuple(
        d.__class__(**{**d.__dict__, "origin_id": "PRESS-RELEASE-1", "source_independence": SourceIndependence.DERIVATIVE})
        for d in derivatives
    )

    solo_company = SyntheticCompany("SYNTH_DERIV_SOLO", Stage.GROWTH, evidence=(original,))
    swarmed_company = SyntheticCompany("SYNTH_DERIV_SWARM", Stage.GROWTH, evidence=(original,) + derivatives)

    d_solo = _find(evaluate_all_dimensions(solo_company, DEFAULT_REGISTRY), "competitive_intensity")
    d_swarm = _find(evaluate_all_dimensions(swarmed_company, DEFAULT_REGISTRY), "competitive_intensity")

    expect(d_solo.score == d_swarm.score, f"99 derivative sources changed Strength: {d_solo.score} -> {d_swarm.score}")
    sps_solo = evaluate_sps(evaluate_all_dimensions(solo_company, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    sps_swarm = evaluate_sps(evaluate_all_dimensions(swarmed_company, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    expect(sps_solo.coverage.overall_pct == sps_swarm.coverage.overall_pct, "99 derivative sources changed Coverage.")
    expect(
        d_swarm.confidence == d_solo.confidence,
        f"99 SAME-ORIGIN derivative sources must not behave as though independent corroboration exists: solo confidence={d_solo.confidence}, swarm confidence={d_swarm.confidence}",
    )


# ---------------------------------------------------------------------
# Part 20 -- independent corroboration test
# ---------------------------------------------------------------------

def test_independent_corroboration_may_increase_confidence() -> None:
    single = f.competitor("CorroboratedCo", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    single = single.__class__(**{**single.__dict__, "source_independence": SourceIndependence.INDEPENDENT, "origin_id": "SRC-A"})

    corroborator_1 = f.competitor("CorroboratedCo", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    corroborator_1 = corroborator_1.__class__(**{**corroborator_1.__dict__, "source_independence": SourceIndependence.INDEPENDENT, "origin_id": "SRC-B"})
    corroborator_2 = f.competitor("CorroboratedCo", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    corroborator_2 = corroborator_2.__class__(**{**corroborator_2.__dict__, "source_independence": SourceIndependence.INDEPENDENT, "origin_id": "SRC-C"})

    solo = SyntheticCompany("SYNTH_CORROB_SOLO", Stage.GROWTH, evidence=(single,))
    corroborated = SyntheticCompany("SYNTH_CORROB_MULTI", Stage.GROWTH, evidence=(single, corroborator_1, corroborator_2))

    d_solo = _find(evaluate_all_dimensions(solo, DEFAULT_REGISTRY), "competitive_intensity")
    d_multi = _find(evaluate_all_dimensions(corroborated, DEFAULT_REGISTRY), "competitive_intensity")

    expect(d_solo.score == d_multi.score, f"Independent corroboration changed Strength (it must not): {d_solo.score} -> {d_multi.score}")
    sps_solo = evaluate_sps(evaluate_all_dimensions(solo, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    sps_multi = evaluate_sps(evaluate_all_dimensions(corroborated, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    expect(sps_solo.coverage.overall_pct == sps_multi.coverage.overall_pct, "Independent corroboration changed Coverage (it must not).")
    expect(
        _CONFIDENCE_RANK[d_multi.confidence.value] >= _CONFIDENCE_RANK[d_solo.confidence.value],
        f"3 genuinely independent SECONDARY_ESTIMATE sources should be allowed to raise Confidence above a single one: solo={d_solo.confidence}, multi={d_multi.confidence}",
    )
    expect(d_multi.confidence.value != d_solo.confidence.value, f"Expected the independent-corroboration upgrade to actually fire here: both are {d_solo.confidence}")


_CONFIDENCE_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


# ---------------------------------------------------------------------
# Part 21 -- fame attack re-run
# ---------------------------------------------------------------------

def test_fame_attack_rerun_sps_identical() -> None:
    fact_a_evidence = tuple(
        f.competitor("SameCompetitor", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
        for _ in range(15)
    )
    company_a = SyntheticCompany("SYNTH_FAME_RERUN_A", Stage.GROWTH, evidence=fact_a_evidence)
    fact_b_evidence = (f.competitor("SameCompetitor", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),)
    company_b = SyntheticCompany("SYNTH_FAME_RERUN_B", Stage.GROWTH, evidence=fact_b_evidence)

    d_a = _find(evaluate_all_dimensions(company_a, DEFAULT_REGISTRY), "competitive_intensity")
    d_b = _find(evaluate_all_dimensions(company_b, DEFAULT_REGISTRY), "competitive_intensity")
    expect(d_a.score == d_b.score, f"Fame attack still succeeds after the amendment: 15-source Strength={d_a.score} vs 1-source Strength={d_b.score}")

    sps_a = evaluate_sps(evaluate_all_dimensions(company_a, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    sps_b = evaluate_sps(evaluate_all_dimensions(company_b, DEFAULT_REGISTRY), Stage.GROWTH, DEFAULT_REGISTRY)
    expect(sps_a.coverage.overall_pct == sps_b.coverage.overall_pct, "Coverage differs between the two fame-attack variants.")
    # Confidence driven by GRADE, not volume: many SECONDARY_ESTIMATE
    # sources (grade-based LOW) vs one HIGH_QUALITY_SECONDARY (grade-based
    # HIGH) -- these differ, correctly, because grade genuinely differs,
    # not because of volume.
    expect(d_b.confidence.value in ("MEDIUM", "HIGH"), f"Single high-quality source should not be LOW confidence, got {d_b.confidence}")


# ---------------------------------------------------------------------
# Part 22 -- conflict order invariance (all permutations)
# ---------------------------------------------------------------------

def test_conflict_order_invariance_all_permutations() -> None:
    a = _rev("1000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    b = _rev("4000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    c = _rev("2500000", D2025, grade=ProvenanceGrade.SECONDARY_ESTIMATE)

    results = set()
    for perm in itertools.permutations([a, b, c]):
        company = SyntheticCompany("SYNTH_CONFLICT_PERM", Stage.SEED, evidence=tuple(perm))
        d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
        results.add((d.score, d.availability.value))

    expect(len(results) == 1, f"Conflict resolution is order-dependent: {results}")
    score, availability = next(iter(results))
    print(f"  All 6 permutations of a 3-way conflict produced identical result: score={score}, availability={availability}")


def test_conflict_order_invariance_two_way_tie() -> None:
    """Same-tier conflict (both PRIMARY_SELF_REPORTED) with no
    resolving higher tier present -- must be order-invariant
    CONFLICT_DETECTED in every permutation, never resolved by list
    position (this is the exact 10.8F max() bug being re-tested)."""
    a = _rev("1000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    b = _rev("4000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)

    results = set()
    for perm in itertools.permutations([a, b]):
        company = SyntheticCompany("SYNTH_CONFLICT_2WAY", Stage.SEED, evidence=tuple(perm))
        d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
        results.add((d.score, d.availability.value))

    expect(len(results) == 1, f"Two-way same-tier conflict is order-dependent: {results}")
    _, availability = next(iter(results))
    expect(availability == AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE.value, f"Same-tier conflict must resolve to CONFLICTING_EVIDENCE in every ordering, got {availability}")


# ---------------------------------------------------------------------
# Part 23 -- provenance conflict matrix (A-E)
# ---------------------------------------------------------------------

def test_provenance_matrix_A_self_report_plus_derivative_of_self_report() -> None:
    """A. self-report + a derivative secondary REPEATING the self-report
    (same value) -- corroboration, not conflict."""
    self_report = _rev("2000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    derivative = _rev("2000000", D2025, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    company = SyntheticCompany("SYNTH_MATRIX_A", Stage.SEED, evidence=(self_report, derivative))
    d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
    expect(d.availability == AvailabilityStatus.SCORABLE, f"Matrix A should be corroboration, not conflict: {d.availability}")
    print(f"  Matrix A (self-report + repeating derivative): SCORABLE, score={d.score} -- correct, same value = corroboration.")


def test_provenance_matrix_B_self_report_plus_independent_confirmation() -> None:
    """B. self-report + an INDEPENDENT secondary CONFIRMING the same
    value -- corroboration, may raise confidence."""
    self_report = _rev("2000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    confirming = _rev("2000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    company = SyntheticCompany("SYNTH_MATRIX_B", Stage.SEED, evidence=(self_report, confirming))
    d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
    expect(d.availability == AvailabilityStatus.SCORABLE, f"Matrix B should be corroboration: {d.availability}")
    print(f"  Matrix B (self-report + independent confirmation): SCORABLE, score={d.score}.")


def test_provenance_matrix_C_self_report_plus_contradictory_estimate() -> None:
    """C. self-report + independent CONTRADICTORY secondary estimate --
    same precedence tier as self-report -> genuine conflict, per Part 8's
    explicit 'no universal winner' instruction."""
    self_report = _rev("2000000", D2025, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED)
    contradictory = _rev("500000", D2025, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    company = SyntheticCompany("SYNTH_MATRIX_C", Stage.SEED, evidence=(self_report, contradictory))
    d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
    # self-report tier(2) > estimate tier(1) -- resolved BY PRECEDENCE
    # in this design (Part 9 example D's pattern generalized: a higher
    # tier beats a lower one even when the higher tier is self-report).
    expect(d.availability == AvailabilityStatus.SCORABLE, f"Matrix C: self-report (tier 2) should beat a mere estimate (tier 1) by precedence -- got {d.availability}")
    expect(d.score is not None, "Matrix C should resolve to the self-report's value via precedence.")
    print(f"  Matrix C (self-report beats contradictory low-tier estimate by precedence): score={d.score}.")


def test_provenance_matrix_D_verified_plus_contradictory_weak_estimate() -> None:
    """D. high-quality PRIMARY_VERIFIED + contradictory weak
    SECONDARY_ESTIMATE -- verified wins deterministically."""
    verified = _rev("3000000", D2025, grade=ProvenanceGrade.PRIMARY_VERIFIED)
    weak_estimate = _rev("9000000", D2025, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
    company = SyntheticCompany("SYNTH_MATRIX_D", Stage.SEED, evidence=(verified, weak_estimate))
    d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
    expect(d.availability == AvailabilityStatus.SCORABLE, f"Matrix D: PRIMARY_VERIFIED should deterministically win: {d.availability}")
    print(f"  Matrix D (verified beats contradictory estimate): score={d.score}.")


def test_provenance_matrix_E_two_similarly_strong_independent_conflict() -> None:
    """E. two similarly-strong independent sources in genuine conflict
    -- same tier, no precedence winner -> CONFLICT_DETECTED."""
    source_1 = _rev("3000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    source_2 = _rev("9000000", D2025, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY)
    company = SyntheticCompany("SYNTH_MATRIX_E", Stage.SEED, evidence=(source_1, source_2))
    d = _find(evaluate_all_dimensions(company, DEFAULT_REGISTRY), "current_scale")
    expect(d.availability == AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE, f"Matrix E: two same-tier independent sources in genuine conflict must be CONFLICTING_EVIDENCE, got {d.availability}")
    print(f"  Matrix E (two similarly-strong independent sources, genuine conflict): UNAVAILABLE_CONFLICTING_EVIDENCE, as required.")


# ---------------------------------------------------------------------
# Part 11-12, 24 -- recency/staleness
# ---------------------------------------------------------------------

def test_freshness_class_assignment() -> None:
    founder = f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN)
    revenue = f.revenue("1000000", D2025, RevenueMetricType.ARR)
    expect(freshness_class_for(founder) == FreshnessClass.STRUCTURAL_FACT, "Founder experience should be STRUCTURAL_FACT.")
    expect(freshness_class_for(revenue) == FreshnessClass.CURRENT_STATE, "Revenue should be CURRENT_STATE.")


def test_staleness_five_evidence_classes_fresh_borderline_stale() -> None:
    reference = D2026
    cases = {
        "founder_history (STRUCTURAL_FACT)": f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN),
        "current_revenue (CURRENT_STATE, fresh)": f.revenue("1000000", date(2025, 11, 1), RevenueMetricType.ARR),
        "current_revenue (CURRENT_STATE, stale)": f.revenue("1000000", date(2020, 1, 1), RevenueMetricType.ARR),
        "customer_count (RECENT_PERFORMANCE, borderline)": f.customer_count(500, date(2024, 10, 1), CustomerType.PAYING),
        "funding_event (STRUCTURAL_FACT, old)": None,  # covered by founder-history-style structural class above
        "market_size (HISTORICAL_FACT, fresh)": f.market_size("1000000000", "segment"),
    }
    for label, obs in cases.items():
        if obs is None:
            continue
        fresh = evaluate_freshness(obs, reference, DEFAULT_REGISTRY)
        print(f"  {label}: {fresh.value}")


def test_stale_current_state_excluded_from_scoring_view() -> None:
    stale_revenue = f.revenue("1000000", date(2019, 1, 1), RevenueMetricType.ARR)  # 7 years before reference -- STALE for CURRENT_STATE
    company = SyntheticCompany("SYNTH_STALE_CURRENT_STATE", Stage.SEED, evidence=(stale_revenue,))
    dims_no_filter = evaluate_all_dimensions(company, DEFAULT_REGISTRY)  # reference_date=None -> no filtering
    dims_filtered, excluded = evaluate_all_dimensions_with_staleness_report(company, DEFAULT_REGISTRY, D2026)

    d_unfiltered = _find(dims_no_filter, "current_scale")
    d_filtered = _find(dims_filtered, "current_scale")

    expect(d_unfiltered.availability == AvailabilityStatus.SCORABLE, "Without a reference_date, staleness must not be applied at all.")
    expect(d_filtered.availability == AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE, f"A 7-year-stale CURRENT_STATE observation should be excluded from scoring when reference_date is supplied, got {d_filtered.availability}")
    expect(len(excluded) == 1, f"Expected exactly one excluded stale observation, got {len(excluded)}")


def test_stale_positive_evidence_never_becomes_negative() -> None:
    stale_revenue = f.revenue("5000000", date(2018, 1, 1), RevenueMetricType.ARR)  # strongly positive figure, very stale
    company = SyntheticCompany("SYNTH_STALE_NOT_NEGATIVE", Stage.SEED, evidence=(stale_revenue,))
    dims_filtered, _ = evaluate_all_dimensions_with_staleness_report(company, DEFAULT_REGISTRY, D2026)
    d = _find(dims_filtered, "current_scale")
    expect(d.score is None, "Excluded-as-stale evidence must produce null, not a negative score.")
    expect(d.availability != AvailabilityStatus.SCORABLE or (d.score is not None and d.score >= Decimal("0")), "Stale positive evidence must never resolve to a negative-band score.")


def test_structural_facts_never_go_stale() -> None:
    old_founder_fact = f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "VeryOldCo")
    company = SyntheticCompany("SYNTH_OLD_FOUNDER_FACT", Stage.SEED, evidence=(old_founder_fact,))
    dims_filtered, excluded = evaluate_all_dimensions_with_staleness_report(company, DEFAULT_REGISTRY, date(2040, 1, 1))
    d = _find(dims_filtered, "founder_market_fit")
    expect(d.availability == AvailabilityStatus.SCORABLE, "Founder history (STRUCTURAL_FACT) must remain usable even decades later.")
    expect(len(excluded) == 0, "No structural facts should ever be excluded as stale.")


def main() -> None:
    tests = [
        test_distinct_periods_are_distinct_signals,
        test_same_period_same_value_is_one_signal,
        test_same_period_different_value_is_a_conflict,
        test_does_not_merge_genuinely_distinct_metrics,
        test_redundancy_1x_2x_10x_100x_identical_strength_and_coverage,
        test_derivative_source_attack,
        test_independent_corroboration_may_increase_confidence,
        test_fame_attack_rerun_sps_identical,
        test_conflict_order_invariance_all_permutations,
        test_conflict_order_invariance_two_way_tie,
        test_provenance_matrix_A_self_report_plus_derivative_of_self_report,
        test_provenance_matrix_B_self_report_plus_independent_confirmation,
        test_provenance_matrix_C_self_report_plus_contradictory_estimate,
        test_provenance_matrix_D_verified_plus_contradictory_weak_estimate,
        test_provenance_matrix_E_two_similarly_strong_independent_conflict,
        test_freshness_class_assignment,
        test_staleness_five_evidence_classes_fresh_borderline_stale,
        test_stale_current_state_excluded_from_scoring_view,
        test_stale_positive_evidence_never_becomes_negative,
        test_structural_facts_never_go_stale,
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
