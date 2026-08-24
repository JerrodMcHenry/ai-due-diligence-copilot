"""
Tests for SIE Methodology v2 deterministic/hybrid anchor functions
(app/ai/sie_v2_anchors.py) -- growth conversion, Unit Economics families,
Burn Efficiency/Runway qualitative bands, Customer Demand lifecycle, and
Retention. Includes reproducibility checks (Part 12: identical inputs must
produce identical outputs for Deterministic dimensions).

Run with:
    python -m app.tests.test_sie_v2_anchors
"""

from app.ai.sie_v2_anchors import (
    AnchorResult,
    score_growth_metric,
    score_customer_growth,
    score_from_structured_facts,
    score_retention,
    score_unit_economics_saas,
    score_unit_economics_non_saas,
    UnitEconomicsFamily,
    score_burn_efficiency_qualitative,
    score_runway_qualitative,
    resolve_customer_demand_applicability,
    CustomerDemandLifecycleState,
)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# --- Growth Velocity / Customer Growth / Revenue Growth ---

def test_trivial_base_growth_is_not_applicable() -> None:
    result = score_growth_metric(2, 6, 1.0, "consumer")
    expect(result.result == AnchorResult.NOT_APPLICABLE, f"2->6 should be Not Applicable, got {result.result}")
    expect(result.score is None, "Not Applicable result must not carry a score")


def test_large_scale_growth_scores_higher_than_small_scale_at_same_percentage() -> None:
    """Do not reward mathematically impressive growth from an economically
    meaningless base as if it were equivalent to large-scale growth."""
    small = score_growth_metric(1_000, 3_000, 1.0, "smb_saas_platform")  # 200% growth, near floor
    large = score_growth_metric(5_000_000, 15_000_000, 1.0, "smb_saas_platform")  # 200% growth, huge base
    expect(small.result == AnchorResult.SCORED, "Small-base case should still score (above floor)")
    expect(large.result == AnchorResult.SCORED, "Large-base case should score")
    expect(
        large.score >= small.score,
        f"Same 200% growth at a much larger scale should score >= the small-scale case: "
        f"large={large.score}, small={small.score}",
    )


def test_slower_growth_from_large_base_not_penalized_as_weak() -> None:
    """A large-base company growing 20% should not be scored as if it were failing."""
    result = score_growth_metric(5_000_000, 6_000_000, 1.0, "smb_saas_platform")  # 20% growth, huge base
    expect(result.result == AnchorResult.SCORED, "Should score")
    expect(result.score >= 5.0, f"20% growth at large scale should be Credible or better, got {result.score}")


def test_projection_vs_actual_mismatch_withheld() -> None:
    result = score_growth_metric(8_000_000, 50_000_000, 1.0, "enterprise_saas", metric_confirmed_actual=False)
    expect(
        result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
        f"A confirmed-actual-vs-projection pair must be withheld, got {result.result}",
    )
    expect(result.score is None, "Withheld result must not carry a score")


def test_short_window_dampens_score() -> None:
    long_window = score_growth_metric(16_000, 90_000, 2.0, "insurance")
    short_window = score_growth_metric(16_000, 90_000, 0.55, "insurance")
    expect(short_window.confidence == "Low", "Sub-2-quarter window must be flagged Low confidence")
    expect(
        short_window.score <= long_window.score,
        f"Short-window score ({short_window.score}) should not exceed the same ratio over a longer, "
        f"more trustworthy window ({long_window.score})",
    )


def test_deterministic_reproducibility() -> None:
    """Part 12: identical inputs must produce identical outputs, full stop."""
    results = [score_growth_metric(20_000, 80_000, 3.5, "smb_saas_platform") for _ in range(5)]
    scores = {r.score for r in results}
    expect(len(scores) == 1, f"Deterministic function produced varying scores across identical calls: {scores}")


def test_structured_facts_dispatch_for_growth_dimensions() -> None:
    facts = {"start_value": 10_000, "end_value": 40_000, "window_years": 1.17, "business_model_family": "hardware", "metric_confirmed_actual": True}
    result = score_from_structured_facts("Growth Velocity", facts)
    expect(result.result == AnchorResult.SCORED, f"Expected SCORED, got {result.result}")
    expect(result.score is not None and result.score >= 7.0, f"227% CAGR at hardware scale should be Strong/Exceptional, got {result.score}")


# --- Blocker 2: Customer Growth != Growth Velocity ---

def test_customer_growth_and_growth_velocity_can_diverge_on_identical_evidence() -> None:
    """Blocker 2: the exact same structured_facts must be able to legitimately
    produce different Customer Growth and Growth Velocity scores, since the
    two dimensions ask different questions (achieved multiple vs. annualized,
    scale-normalized rate) -- prior to this fix both routed through the same
    engine and could never diverge for identical input."""
    facts = {
        "start_value": 5_000_000,
        "end_value": 15_000_000,
        "window_years": 5.0,
        "business_model_family": "smb_saas_platform",
        "metric_confirmed_actual": True,
    }
    customer_growth = score_from_structured_facts("Customer Growth", facts)
    growth_velocity = score_from_structured_facts("Growth Velocity", facts)

    expect(customer_growth.result == AnchorResult.SCORED, f"Customer Growth should score, got {customer_growth.result}")
    expect(growth_velocity.result == AnchorResult.SCORED, f"Growth Velocity should score, got {growth_velocity.result}")
    expect(
        customer_growth.score != growth_velocity.score,
        f"Identical raw evidence produced identical scores ({customer_growth.score}) -- Customer Growth and "
        f"Growth Velocity must be able to diverge, not silently route through one shared engine",
    )


def test_customer_growth_scoreable_without_window_while_growth_velocity_is_not() -> None:
    """Counterexample: a real achieved multiple with no disclosed time window
    can still support a Customer Growth read (it is not a rate calculation),
    while Growth Velocity's stricter annualization requirement withholds --
    demonstrating the two dimensions are not interchangeable."""
    facts_no_window = {
        "start_value": 20_000,
        "end_value": 60_000,
        "business_model_family": "consumer",
        "metric_confirmed_actual": True,
        # window_years deliberately omitted
    }
    customer_growth = score_from_structured_facts("Customer Growth", facts_no_window)
    growth_velocity = score_from_structured_facts("Growth Velocity", facts_no_window)

    expect(customer_growth.result == AnchorResult.SCORED, f"Customer Growth should still score without a window, got {customer_growth.result}")
    expect(customer_growth.confidence == "Low", "A missing window should lower confidence, not block the score")
    expect(
        growth_velocity.result == AnchorResult.INSUFFICIENT_EVIDENCE,
        f"Growth Velocity requires a window to annualize -- expected INSUFFICIENT_EVIDENCE, got {growth_velocity.result}",
    )


def test_customer_growth_deterministic_reproducibility() -> None:
    """Part 12: identical inputs must produce identical outputs for the new
    Customer Growth engine too, not just Growth Velocity's."""
    results = [score_customer_growth(1_000, 4_000, 2.0, "smb_saas_platform") for _ in range(5)]
    scores = {r.score for r in results}
    expect(len(scores) == 1, f"Deterministic function produced varying scores across identical calls: {scores}")


def test_structured_facts_malformed_input_withheld_not_crashed() -> None:
    result = score_from_structured_facts("Customer Growth", {"start_value": "not-a-number"})
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, f"Malformed input must be withheld, not crash, got {result.result}")


def test_unit_economics_growth_shaped_input_withheld_not_crashed() -> None:
    """A growth-metric-shaped payload (no "families" key) must never be
    silently scored as Unit Economics -- withheld, not crashed."""
    result = score_from_structured_facts("Unit Economics", {"start_value": 1, "end_value": 2, "window_years": 1})
    expect(
        result.result == AnchorResult.INSUFFICIENT_EVIDENCE,
        f"Growth-shaped input with no 'families' key must be withheld as insufficient evidence, got {result.result}",
    )
    expect(result.score is None, "Must not fabricate a score from mismatched input shape")


# --- Blocker 4: Unit Economics structured-fact family routing ---

def test_unit_economics_saas_family_routes_to_saas_anchors() -> None:
    facts = {"families": [{"business_model_family": "saas_subscription", "gross_margin_pct": 85, "cac_payback_months": 8, "ltv_cac_ratio": 4}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.SCORED, f"SaaS family with full figures should score, got {result.result}")
    expect(result.score is not None and result.score >= 7.0, f"Strong SaaS figures should score well, got {result.score}")


def test_unit_economics_marketplace_family_withheld_not_saas_scored() -> None:
    """A marketplace take-rate alone must never be scored via SaaS thresholds."""
    facts = {"families": [{"business_model_family": "marketplace", "has_primary_metric": True, "has_supporting_signal": False}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"Marketplace take-rate alone must be withheld, got {result.result}")
    expect(result.score is None, "Non-SaaS families must never produce a fabricated numeric score")


def test_unit_economics_insurance_family_routes_to_non_saas() -> None:
    facts = {"families": [{"business_model_family": "insurance", "has_primary_metric": True, "has_supporting_signal": True}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"Insurance has no FROZEN numeric anchor -- expected withheld, got {result.result}")
    expect(result.score is None, "Insurance is not SaaS -- must never receive a SaaS-shaped numeric score")


def test_unit_economics_hardware_family_routes_to_non_saas() -> None:
    facts = {"families": [{"business_model_family": "hardware", "has_primary_metric": False}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, f"No primary metric at all should be insufficient, got {result.result}")


def test_unit_economics_commerce_dtc_family_routes_to_non_saas() -> None:
    facts = {"families": [{"business_model_family": "commerce_dtc", "has_primary_metric": True, "has_supporting_signal": False}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"DTC thesis-not-outcome must be withheld, got {result.result}")
    expect(result.score is None, "Commerce/DTC is not SaaS -- must never receive a SaaS-shaped numeric score")


def test_unit_economics_deeptech_family_routes_to_non_saas() -> None:
    facts = {"families": [{"business_model_family": "deeptech_partnership", "has_primary_metric": True, "has_supporting_signal": True}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"Deeptech has no FROZEN numeric anchor, got {result.result}")
    expect(result.score is None, "Deeptech is not SaaS -- must never receive a SaaS-shaped numeric score")


def test_unit_economics_insufficient_evidence_when_no_families_detected() -> None:
    result = score_from_structured_facts("Unit Economics", {"families": []})
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, f"Empty families list must be insufficient evidence, got {result.result}")


def test_unit_economics_mixed_business_model_does_not_force_a_single_family() -> None:
    """A company that genuinely spans two families (e.g. a fintech with a
    SaaS software layer and an insurance-underwriting layer) must not be
    arbitrarily forced into one family -- both are considered, and the
    SaaS reading (the only family with a real numeric anchor) is used while
    the other family's evidence is still named in the rationale."""
    facts = {
        "families": [
            {"business_model_family": "saas_subscription", "gross_margin_pct": 82, "cac_payback_months": 11, "ltv_cac_ratio": 3.5},
            {"business_model_family": "insurance", "has_primary_metric": True, "has_supporting_signal": True},
        ]
    }
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.SCORED, f"The SaaS family should still score even with a second family present, got {result.result}")
    expect("insurance" in result.rationale, "The second family's evidence must be named, not silently dropped")


def test_unit_economics_generic_industry_commentary_rejected_via_dispatcher() -> None:
    facts = {"families": [{"business_model_family": "marketplace", "has_primary_metric": True, "has_supporting_signal": True, "is_generic_industry_commentary": True}]}
    result = score_from_structured_facts("Unit Economics", facts)
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, f"Generic industry commentary must be rejected even through the dispatcher, got {result.result}")


# --- Retention ---

def test_retention_frozen_anchors() -> None:
    strong = score_retention(nrr_pct=140)
    weak = score_retention(nrr_pct=95)
    expect(strong.score > weak.score, "NRR>130% must score higher than NRR<100%")
    expect(strong.score >= 9.0, f"NRR=140% should be in the 9-10 FROZEN band, got {strong.score}")


def test_retention_no_evidence_insufficient() -> None:
    result = score_retention()
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, "No retention figures should be insufficient evidence, not a fabricated score")


# --- Unit Economics families ---

def test_saas_unit_economics_frozen_anchors() -> None:
    strong = score_unit_economics_saas(gross_margin_pct=85, cac_payback_months=8, ltv_cac_ratio=4)
    weak = score_unit_economics_saas(gross_margin_pct=40, cac_payback_months=30, ltv_cac_ratio=1)
    expect(strong.score > weak.score, "Strong SaaS unit economics must score higher than weak")


def test_marketplace_take_rate_alone_insufficient() -> None:
    """FROZEN withholding rule: a take-rate alone, with no supporting cost signal, is insufficient."""
    result = score_unit_economics_non_saas(UnitEconomicsFamily.MARKETPLACE, has_primary_metric=True, has_supporting_signal=False)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"Take-rate alone must be withheld, got {result.result}")
    expect(result.score is None, "Must not force a score from a lone primary metric")


def test_commerce_dtc_thesis_not_outcome() -> None:
    result = score_unit_economics_non_saas(UnitEconomicsFamily.COMMERCE_DTC, has_primary_metric=True, has_supporting_signal=False)
    expect(result.score is None, "A structural thesis alone (no realized outcome evidence) must not produce a score")


def test_generic_industry_commentary_rejected() -> None:
    result = score_unit_economics_non_saas(
        UnitEconomicsFamily.MARKETPLACE, has_primary_metric=True, has_supporting_signal=True, is_generic_industry_commentary=True,
    )
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, "Generic industry-wide commentary must never count as company-specific evidence")


def test_non_saas_family_with_full_evidence_still_no_invented_threshold() -> None:
    """Even with a primary metric AND a supporting signal, no NUMBER is invented for
    non-SaaS families -- Part 11 lists these as having no anchor of any kind."""
    result = score_unit_economics_non_saas(UnitEconomicsFamily.INSURANCE, has_primary_metric=True, has_supporting_signal=True)
    expect(result.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED, f"Expected CALIBRATION_ANCHOR_REQUIRED, got {result.result}")
    expect(result.score is None, "No non-SaaS family may produce a scored result -- no threshold is FROZEN for any of them")


# --- Burn Efficiency ---

def test_burn_efficiency_documented_crisis_is_clearly_poor() -> None:
    result = score_burn_efficiency_qualitative(
        documented_crisis_requiring_emergency_financing_or_cuts=True,
        explicit_nonhedged_spend_growing_faster_than_value=False,
        explicit_signal_spend_matched_to_milestones=False,
        disclosed_spend_control_or_efficiency_improvement=False,
        disclosed_burn_multiple_below_1x_or_profitable_claim=False,
    )
    expect(result.score <= 2.0, f"Documented crisis should be Clearly Poor (<=2), got {result.score}")


def test_burn_efficiency_vague_narrative_rejected_regardless_of_direction() -> None:
    """Symmetry check: vague positive AND vague negative narratives are both rejected."""
    vague_positive = score_burn_efficiency_qualitative(
        documented_crisis_requiring_emergency_financing_or_cuts=False,
        explicit_nonhedged_spend_growing_faster_than_value=False,
        explicit_signal_spend_matched_to_milestones=False,
        disclosed_spend_control_or_efficiency_improvement=False,
        disclosed_burn_multiple_below_1x_or_profitable_claim=True,
        is_vague_or_hedged_narrative=True,
    )
    expect(vague_positive.result == AnchorResult.INSUFFICIENT_EVIDENCE, "A vague positive claim must be rejected just like a vague negative one")


# --- Runway ---

def test_runway_large_raise_in_isolation_insufficient() -> None:
    result = score_runway_qualitative(
        near_insolvency_unresolved_at_snapshot=False,
        near_insolvency_just_addressed_by_fresh_capital=False,
        direct_nonhedged_financing_inadequacy_claim=False,
        direct_claim_financing_adequate_unremarkable=False,
        committed_undrawn_credit_facility_disclosed=False,
        quantified_reserves_relative_to_disclosed_burn_or_spend_plan=False,
        is_large_raise_in_isolation_only=True,
    )
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, "Fundraising amount alone must never imply financial health")


def test_runway_absence_of_data_is_not_distress() -> None:
    result = score_runway_qualitative(
        near_insolvency_unresolved_at_snapshot=False,
        near_insolvency_just_addressed_by_fresh_capital=False,
        direct_nonhedged_financing_inadequacy_claim=False,
        direct_claim_financing_adequate_unremarkable=False,
        committed_undrawn_credit_facility_disclosed=False,
        quantified_reserves_relative_to_disclosed_burn_or_spend_plan=False,
    )
    expect(result.result == AnchorResult.INSUFFICIENT_EVIDENCE, "No qualifying evidence must be Insufficient Evidence, never a low score inferred from silence")
    expect(result.score is None, "Absence of public cash data must not be scored as distress")


def test_runway_near_insolvency_unresolved_worse_than_addressed() -> None:
    unresolved = score_runway_qualitative(True, False, False, False, False, False)
    addressed = score_runway_qualitative(False, True, False, False, False, False)
    expect(unresolved.score < addressed.score, "Unresolved near-insolvency should score worse than crisis-just-addressed")


# --- Customer Demand lifecycle ---

def test_customer_demand_pre_seed_expected() -> None:
    state = resolve_customer_demand_applicability("Pre-Seed", False, True, False)
    expect(state == CustomerDemandLifecycleState.EXPECTED, f"Pre-Seed should be Expected, got {state}")


def test_customer_demand_mature_series_b_not_applicable() -> None:
    state = resolve_customer_demand_applicability("Series B", True, False, True)
    expect(state == CustomerDemandLifecycleState.NOT_APPLICABLE, f"Mature Series B with real Traction should be N/A, got {state}")


def test_customer_demand_genuinely_early_despite_series_a_label() -> None:
    """Maturity-based, not label-based: a 'Series A' company with no disclosed
    customer/revenue data and single-market/pre-scale evidence should be
    evaluated under the Seed rule, not mechanically defaulted to N/A."""
    state = resolve_customer_demand_applicability("Series A", False, True, False)
    expect(
        state == CustomerDemandLifecycleState.EXPECTED_UNTIL_SUPERSEDED,
        f"Genuinely early Series A-labeled company should still be Expected-until-superseded, got {state}",
    )


TESTS = [
    test_trivial_base_growth_is_not_applicable,
    test_large_scale_growth_scores_higher_than_small_scale_at_same_percentage,
    test_slower_growth_from_large_base_not_penalized_as_weak,
    test_projection_vs_actual_mismatch_withheld,
    test_short_window_dampens_score,
    test_deterministic_reproducibility,
    test_structured_facts_dispatch_for_growth_dimensions,
    test_customer_growth_and_growth_velocity_can_diverge_on_identical_evidence,
    test_customer_growth_scoreable_without_window_while_growth_velocity_is_not,
    test_customer_growth_deterministic_reproducibility,
    test_structured_facts_malformed_input_withheld_not_crashed,
    test_unit_economics_growth_shaped_input_withheld_not_crashed,
    test_unit_economics_saas_family_routes_to_saas_anchors,
    test_unit_economics_marketplace_family_withheld_not_saas_scored,
    test_unit_economics_insurance_family_routes_to_non_saas,
    test_unit_economics_hardware_family_routes_to_non_saas,
    test_unit_economics_commerce_dtc_family_routes_to_non_saas,
    test_unit_economics_deeptech_family_routes_to_non_saas,
    test_unit_economics_insufficient_evidence_when_no_families_detected,
    test_unit_economics_mixed_business_model_does_not_force_a_single_family,
    test_unit_economics_generic_industry_commentary_rejected_via_dispatcher,
    test_retention_frozen_anchors,
    test_retention_no_evidence_insufficient,
    test_saas_unit_economics_frozen_anchors,
    test_marketplace_take_rate_alone_insufficient,
    test_commerce_dtc_thesis_not_outcome,
    test_generic_industry_commentary_rejected,
    test_non_saas_family_with_full_evidence_still_no_invented_threshold,
    test_burn_efficiency_documented_crisis_is_clearly_poor,
    test_burn_efficiency_vague_narrative_rejected_regardless_of_direction,
    test_runway_large_raise_in_isolation_insufficient,
    test_runway_absence_of_data_is_not_distress,
    test_runway_near_insolvency_unresolved_worse_than_addressed,
    test_customer_demand_pre_seed_expected,
    test_customer_demand_mature_series_b_not_applicable,
    test_customer_demand_genuinely_early_despite_series_a_label,
]


def main() -> None:
    print("\nSIE Methodology v2 -- anchor function tests")
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
