"""
SIE Intelligence + Scoring Reset -- VPS regression suite.

Two permanent fixture sets, per this phase's own explicit charter:

1. Five canonical synthetic profiles (A-E), a SMALL permanent dynamic-
   range benchmark (Section 12) -- NOT a 50-company calibration project.
   The invariant that matters is A < B < C < D < E with meaningful
   separation; the letter labels are semantic regions, not exact
   numeric targets.

2. ApexGrid -- the FROZEN real-world regression case (Section 10). The
   exact facts below are transcribed unchanged from the actual
   ApexGrid venture (id 1067) as entered/tested live; nothing added,
   nothing removed. `APEXGRID_ASSUMPTIONS_WITH_RECOVERED_FIELDS` adds
   ONLY the two new fields this phase introduced (prior_monthly_revenue,
   retention_pct), populated from facts genuinely stated in ApexGrid's
   own description ("$3.1 million ARR twelve months ago", "net revenue
   retention is 128%") that had no field to land in before this phase --
   this is not new/invented evidence, it's evidence that already existed
   in the input and previously had nowhere to go.

Run with:
    python -m app.tests.test_vps_intelligence_reset
"""

from app.ai.vps_scoring import compute_vps
from app.ai.vps_guidance import generate_guidance


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# --- Canonical dynamic-range fixtures (Section 12) --------------------------

FIXTURE_A_WEAK = {
    "target_customer": "small local retailers",
    "market": {"estimated_market_size": "Small", "competition_intensity": "High"},
    "problem_solution": {"problem_statement": "Retailers want lower costs", "solution_description": "A generic discount app", "differentiation": None},
    "founder": {"founder_count": 1, "relevant_domain_experience_years": 0, "has_technical_cofounder": False, "has_business_cofounder": False},
    "gtm": {"primary_acquisition_strategy": "Cold email", "expected_cac": 900},
    "economics": {"pricing_model": "Flat fee", "price_point": 20, "expected_gross_margin_pct": 12},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 1, "monthly_revenue": 90, "prior_monthly_revenue": 600, "retention_pct": 25},
    "capital": {"starting_capital": 20000, "monthly_burn": 8000},
}

FIXTURE_B_PLAUSIBLE_UNPROVEN = {
    "target_customer": "mid-size logistics companies",
    "market": {"estimated_market_size": "Medium", "competition_intensity": "Medium"},
    "problem_solution": {"problem_statement": "Logistics dispatch is manual and error-prone", "solution_description": "AI dispatch optimization software", "differentiation": "Purpose-built routing model for regional freight"},
    "founder": {"founder_count": 2, "relevant_domain_experience_years": 3, "has_technical_cofounder": True, "has_business_cofounder": False},
    "gtm": {"primary_acquisition_strategy": "Outbound to regional carriers", "expected_cac": 400},
    "economics": {"pricing_model": "Per-seat subscription", "price_point": 500, "expected_gross_margin_pct": 60},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": None, "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None},
    "capital": {"starting_capital": 300000, "monthly_burn": 40000},
}

FIXTURE_C_PROMISING = {
    "target_customer": "independent dental practices",
    "market": {"estimated_market_size": "Large", "competition_intensity": "Medium"},
    "problem_solution": {"problem_statement": "Dental billing has high denial rates", "solution_description": "Automated claims scrubbing and resubmission", "differentiation": "Built specifically for dental CDT codes, not generic medical billing"},
    "founder": {"founder_count": 2, "relevant_domain_experience_years": 6, "has_technical_cofounder": True, "has_business_cofounder": True},
    "gtm": {"primary_acquisition_strategy": "Founder-led outbound plus dental association partnership", "expected_cac": 300},
    "economics": {"pricing_model": "Monthly subscription", "price_point": 800, "expected_gross_margin_pct": 72},
    "validation": {"customer_interviews": 30, "waitlist_signups": 40, "paying_customers": 14, "monthly_revenue": 11000, "prior_monthly_revenue": None, "retention_pct": None},
    "capital": {"starting_capital": 500000, "monthly_burn": 60000},
}

FIXTURE_D_STRONG = {
    "target_customer": "mid-market e-commerce brands",
    "market": {"estimated_market_size": "Very Large", "competition_intensity": "Medium"},
    "problem_solution": {"problem_statement": "Returns processing is manual and costly for e-commerce brands", "solution_description": "Automated returns and exchange platform integrated with major carts", "differentiation": "Only platform combining fraud detection with automated restocking workflows"},
    "founder": {"founder_count": 2, "relevant_domain_experience_years": 9, "has_technical_cofounder": True, "has_business_cofounder": True},
    "gtm": {"primary_acquisition_strategy": "Partner integrations with e-commerce platforms plus inside sales", "expected_cac": 800},
    "economics": {"pricing_model": "Usage-based subscription", "price_point": 2500, "expected_gross_margin_pct": 78},
    "validation": {"customer_interviews": 60, "waitlist_signups": None, "paying_customers": 65, "monthly_revenue": 140000, "prior_monthly_revenue": 95000, "retention_pct": 96},
    "capital": {"starting_capital": 6000000, "monthly_burn": 250000},
}

# Section 10's own ApexGrid facts, restated as a canonical "E" (exceptional/
# elite-territory) profile.
FIXTURE_E_EXCEPTIONAL = {
    "target_customer": "large commercial buildings and industrial facilities",
    "market": {"estimated_market_size": "Very Large", "competition_intensity": "Medium"},
    "problem_solution": {
        "problem_statement": "Energy costs and peak-demand charges are significant operating expenses",
        "solution_description": "Automated energy optimization platform integrating BMS, meters, storage, and pricing data",
        "differentiation": "Combines real-time price data, telemetry, and storage assets into one platform that can automatically execute optimization strategies, unlike systems that only monitor or recommend",
    },
    "founder": {"founder_count": 2, "relevant_domain_experience_years": 12, "has_technical_cofounder": True, "has_business_cofounder": True},
    "gtm": {"primary_acquisition_strategy": "Direct sales team plus energy-consulting partnerships", "expected_cac": 21000},
    "economics": {"pricing_model": "Annual subscription based on facility count and energy consumption", "price_point": 70000, "expected_gross_margin_pct": 84},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 186, "monthly_revenue": 983333, "prior_monthly_revenue": 258333, "retention_pct": 128},
    "capital": {"starting_capital": 14500000, "monthly_burn": 310000},
}

# A synthetic, maximally-strong profile (not one of the canonical A-E
# regression fixtures) used ONLY to demonstrate that 9+ overall and
# dimension-level 10 are mechanically reachable (Section 18, criteria
# 5-7) -- never used as an optimization target for any real company.
FIXTURE_MAXIMAL = {
    "target_customer": "a clearly named customer segment",
    "market": {"estimated_market_size": "Very Large", "competition_intensity": "Low"},
    "problem_solution": {
        "problem_statement": "A clearly stated, significant problem",
        "solution_description": "A clearly stated solution",
        "differentiation": "A specific, well-evidenced differentiation that is genuinely distinctive and defensible in the market, difficult for competitors to replicate quickly",
    },
    "founder": {"founder_count": 2, "relevant_domain_experience_years": 15, "has_technical_cofounder": True, "has_business_cofounder": True},
    "gtm": {"primary_acquisition_strategy": "Repeatable outbound plus partnerships", "expected_cac": 10000},
    "economics": {"pricing_model": "Annual subscription", "price_point": 100000, "expected_gross_margin_pct": 85},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 300, "monthly_revenue": 2_000_000, "prior_monthly_revenue": 400_000, "retention_pct": 135},
    "capital": {"starting_capital": 20_000_000, "monthly_burn": 400_000},
}


def test_canonical_fixtures_are_strictly_increasing_with_meaningful_separation() -> None:
    values = [compute_vps(fx)["vps"] for fx in [
        FIXTURE_A_WEAK, FIXTURE_B_PLAUSIBLE_UNPROVEN, FIXTURE_C_PROMISING, FIXTURE_D_STRONG, FIXTURE_E_EXCEPTIONAL,
    ]]
    labels = ["A", "B", "C", "D", "E"]
    for i in range(len(values) - 1):
        expect(
            values[i] < values[i + 1],
            f"Canonical fixture ordering violated: {labels[i]}={values[i]} must be < {labels[i + 1]}={values[i + 1]}",
        )
        expect(
            values[i + 1] - values[i] >= 0.3,
            f"Separation between {labels[i]} ({values[i]}) and {labels[i + 1]} ({values[i + 1]}) is too small to be meaningful",
        )


def test_fixture_d_reaches_8_plus_naturally() -> None:
    vps = compute_vps(FIXTURE_D_STRONG)["vps"]
    expect(vps >= 8.0, f"Fixture D (Strong) should naturally reach 8.0+, got {vps}")


def test_maximal_profile_reaches_9_plus_naturally() -> None:
    vps = compute_vps(FIXTURE_MAXIMAL)["vps"]
    expect(vps >= 9.0, f"A maximally strong synthetic profile should reach 9.0+, got {vps}")


def test_dimension_level_10_is_reachable() -> None:
    result = compute_vps(FIXTURE_MAXIMAL)
    scores = {c["key"]: c["score"] for c in result["categories"]}
    expect(scores["validation"] == 10.0, f"Validation should reach the 10.0 ceiling for elite-tier evidence, got {scores['validation']}")
    expect(scores["founder_readiness"] == 10.0, f"Founder Readiness should reach the 10.0 ceiling, got {scores['founder_readiness']}")


def test_fixture_a_is_weak_not_zero() -> None:
    # 0-2 is reserved for fundamentally-weak/severe-negative-evidence
    # (Section 6); a company with SOME evidence, even weak evidence,
    # should not be indistinguishable from a company with none.
    vps = compute_vps(FIXTURE_A_WEAK)["vps"]
    expect(0.5 < vps < 4.5, f"Fixture A should land in the Weak region, got {vps}")


# --- Unknown vs. Negative (Section 4) ---------------------------------------


def test_unknown_retention_and_growth_do_not_lower_validation_score() -> None:
    with_unknowns = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "prior_monthly_revenue": None, "retention_pct": None}}
    baseline_score = next(c for c in compute_vps(with_unknowns)["categories"] if c["key"] == "validation")["score"]

    # Compare against the SAME facts plus explicit unknown fields removed
    # entirely -- must be identical (renormalization/omission is
    # equivalent to explicit None here, by construction).
    without_fields = {"validation": {"paying_customers": 50, "monthly_revenue": 60000}}
    baseline_score_2 = next(c for c in compute_vps(without_fields)["categories"] if c["key"] == "validation")["score"]

    expect(baseline_score == baseline_score_2, "Omitted vs. explicit-None unknown fields must score identically")


def test_negative_growth_lowers_validation_score() -> None:
    growing = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "prior_monthly_revenue": 60000, "retention_pct": None}}
    declining = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "prior_monthly_revenue": 120000, "retention_pct": None}}
    unknown_prior = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "prior_monthly_revenue": None, "retention_pct": None}}

    score_flat = next(c for c in compute_vps(growing)["categories"] if c["key"] == "validation")["score"]
    score_declining = next(c for c in compute_vps(declining)["categories"] if c["key"] == "validation")["score"]
    score_unknown = next(c for c in compute_vps(unknown_prior)["categories"] if c["key"] == "validation")["score"]

    expect(score_declining < score_flat, f"A confirmed revenue decline must score lower than flat revenue ({score_declining} vs {score_flat})")
    expect(score_unknown == score_flat, f"Unknown prior revenue must score the SAME as flat/no-change, not like a decline ({score_unknown} vs {score_flat})")


def test_weak_retention_lowers_score_unknown_retention_does_not() -> None:
    base = {"validation": {"paying_customers": 50, "monthly_revenue": 60000}}
    weak_retention = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "retention_pct": 60}}
    strong_retention = {"validation": {"paying_customers": 50, "monthly_revenue": 60000, "retention_pct": 128}}

    score_base = next(c for c in compute_vps(base)["categories"] if c["key"] == "validation")["score"]
    score_weak = next(c for c in compute_vps(weak_retention)["categories"] if c["key"] == "validation")["score"]
    score_strong = next(c for c in compute_vps(strong_retention)["categories"] if c["key"] == "validation")["score"]

    expect(score_weak < score_base, f"61% retention is Section 4's own worked example of negative evidence -- must score below the unknown-retention baseline ({score_weak} vs {score_base})")
    expect(score_strong > score_base, f"128% retention (net expansion) must score above the unknown-retention baseline ({score_strong} vs {score_base})")


# --- Duplicate/monotonic sanity (Section 8) ---------------------------------


def test_scale_never_saturates_at_a_low_ceiling() -> None:
    # The exact confirmed defect: 10 paying customers used to score
    # identically to 186. They must now be clearly distinguishable.
    ten = {"validation": {"paying_customers": 10, "monthly_revenue": 5000}}
    one_eighty_six = {"validation": {"paying_customers": 186, "monthly_revenue": 983333}}
    score_ten = next(c for c in compute_vps(ten)["categories"] if c["key"] == "validation")["score"]
    score_186 = next(c for c in compute_vps(one_eighty_six)["categories"] if c["key"] == "validation")["score"]
    expect(score_186 > score_ten + 2.0, f"186 paying customers at $983K/mo must score well above 10 paying customers at $5K/mo (got {score_186} vs {score_ten})")


def test_any_nonzero_revenue_no_longer_gets_the_same_flat_bonus() -> None:
    tiny = {"validation": {"paying_customers": 5, "monthly_revenue": 1}}
    huge = {"validation": {"paying_customers": 5, "monthly_revenue": 900000}}
    score_tiny = next(c for c in compute_vps(tiny)["categories"] if c["key"] == "validation")["score"]
    score_huge = next(c for c in compute_vps(huge)["categories"] if c["key"] == "validation")["score"]
    expect(score_huge > score_tiny, f"$900K/mo must score higher than $1/mo (previously both got the same flat +2 bonus): {score_huge} vs {score_tiny}")


# --- ApexGrid: the frozen real-world regression case (Section 10) ----------

# Transcribed unchanged from the real ApexGrid venture (modeled_ventures id
# 1067) as it was actually persisted -- founder fields are null because
# that evidence was genuinely never captured (see this phase's report on
# the confirmed 4000-character input-truncation root cause).
APEXGRID_ASSUMPTIONS_AS_PERSISTED = {
    "gtm": {"expected_cac": 21000.0, "primary_acquisition_strategy": "Direct sales team"},
    "market": {
        "market_description": "U.S. commercial and industrial facilities with substantial electricity consumption facing high energy costs and peak-demand charges",
        "competition_intensity": "High",
        "estimated_market_size": "Very Large",
    },
    "capital": {"monthly_burn": 310000.0, "starting_capital": 14500000.0},
    "founder": {"founder_count": None, "has_business_cofounder": None, "has_technical_cofounder": None, "relevant_domain_experience_years": None},
    "economics": {"price_point": 63000.0, "pricing_model": "Annual subscription based on facility count and energy consumption", "expected_gross_margin_pct": 84.0},
    "validation": {"monthly_revenue": 983333.0, "paying_customers": 186, "waitlist_signups": None, "customer_interviews": None},
    "target_customer": "Large commercial buildings and industrial facilities including logistics operators, manufacturers, data-center operators, cold-storage companies, and large commercial-property owners",
    "problem_solution": {
        "differentiation": "Combines real-time energy-price data, facility telemetry, storage assets, and automated load optimization in one platform that can automatically execute approved optimization strategies",
        "problem_statement": "Energy costs and peak-demand charges are significant operating expenses; existing building-management systems monitor equipment but do not optimize energy consumption against real-time electricity economics",
        "solution_description": "Platform integrates with building-management systems, smart meters, HVAC, battery storage, and utility pricing data to optimize energy consumption and shift usage away from peak-demand periods automatically",
    },
}

# The SAME facts, with ONLY the two new fields this phase introduced
# populated from facts genuinely stated in ApexGrid's own description
# ("$3.1 million ARR twelve months ago" -> $258,333/mo; "net revenue
# retention is 128%").
APEXGRID_ASSUMPTIONS_WITH_RECOVERED_FIELDS = {
    **APEXGRID_ASSUMPTIONS_AS_PERSISTED,
    "validation": {
        **APEXGRID_ASSUMPTIONS_AS_PERSISTED["validation"],
        "prior_monthly_revenue": 258333.0,
        "retention_pct": 128.0,
    },
}


def test_apexgrid_validation_no_longer_ignores_scale() -> None:
    result = compute_vps(APEXGRID_ASSUMPTIONS_AS_PERSISTED)
    validation = next(c for c in result["categories"] if c["key"] == "validation")
    expect(
        validation["score"] is not None and validation["score"] > 6.0,
        f"186 paying customers / $983K-mo revenue must not score near the old ~5.0 defect, got {validation['score']}",
    )


def test_apexgrid_validation_reaches_elite_with_recovered_growth_and_retention_evidence() -> None:
    result = compute_vps(APEXGRID_ASSUMPTIONS_WITH_RECOVERED_FIELDS)
    validation = next(c for c in result["categories"] if c["key"] == "validation")
    expect(validation["score"] == 10.0, f"ApexGrid's real growth (~281%) and retention (128% NRR) evidence should reach the Validation ceiling, got {validation['score']}")


def test_apexgrid_overall_vps_improves_substantially() -> None:
    before = compute_vps(APEXGRID_ASSUMPTIONS_AS_PERSISTED)["vps"]
    after = compute_vps(APEXGRID_ASSUMPTIONS_WITH_RECOVERED_FIELDS)["vps"]
    expect(before is not None and before > 7.0, f"Even without the two new fields, fixing the saturation defect alone should raise ApexGrid from the observed 6.5 to above 7.0 (got {before})")
    expect(after is not None and after > before, f"Recovered growth/retention evidence should raise the overall score further ({after} vs {before})")


def test_apexgrid_no_longer_gets_beginner_interview_recommendation() -> None:
    result = compute_vps(APEXGRID_ASSUMPTIONS_AS_PERSISTED)
    guidance = generate_guidance(APEXGRID_ASSUMPTIONS_AS_PERSISTED, result)
    expect(
        not any("Interview 20+" in m for m in guidance["next_milestones"]),
        f"A company with 186 paying customers must never be told to interview 20+ people to validate the problem is real, got: {guidance['next_milestones']}",
    )
    expect(
        not any("expected at the idea stage" in gap for gap in guidance["validation_gaps"]),
        f"A company with real commercial scale must not be told validation gaps are 'expected at the idea stage', got: {guidance['validation_gaps']}",
    )


def test_apexgrid_next_milestone_targets_the_real_bottleneck() -> None:
    result = compute_vps(APEXGRID_ASSUMPTIONS_AS_PERSISTED)
    guidance = generate_guidance(APEXGRID_ASSUMPTIONS_AS_PERSISTED, result)
    expect(len(guidance["next_milestones"]) > 0, "Expected at least one milestone")
    expect(
        "repeatably" in guidance["next_milestones"][0],
        f"ApexGrid's actual bottleneck (GTM Feasibility, not customer discovery) should be the top recommendation, got: {guidance['next_milestones'][0]!r}",
    )


def test_apexgrid_founder_readiness_stays_unavailable_not_penalized() -> None:
    # This is the honest outcome given the founder-background evidence
    # was never captured (see the report's root-cause trace) -- Unknown
    # must never be silently scored as 0 or as a penalty. It stays
    # excluded from the weighted average (renormalized around), not
    # counted against the venture.
    result = compute_vps(APEXGRID_ASSUMPTIONS_AS_PERSISTED)
    founder = next(c for c in result["categories"] if c["key"] == "founder_readiness")
    expect(founder["score"] is None, f"Founder Readiness with zero founder evidence must stay Unavailable (None), not a fabricated low score, got {founder['score']}")


TESTS = [
    test_canonical_fixtures_are_strictly_increasing_with_meaningful_separation,
    test_fixture_d_reaches_8_plus_naturally,
    test_maximal_profile_reaches_9_plus_naturally,
    test_dimension_level_10_is_reachable,
    test_fixture_a_is_weak_not_zero,
    test_unknown_retention_and_growth_do_not_lower_validation_score,
    test_negative_growth_lowers_validation_score,
    test_weak_retention_lowers_score_unknown_retention_does_not,
    test_scale_never_saturates_at_a_low_ceiling,
    test_any_nonzero_revenue_no_longer_gets_the_same_flat_bonus,
    test_apexgrid_validation_no_longer_ignores_scale,
    test_apexgrid_validation_reaches_elite_with_recovered_growth_and_retention_evidence,
    test_apexgrid_overall_vps_improves_substantially,
    test_apexgrid_no_longer_gets_beginner_interview_recommendation,
    test_apexgrid_next_milestone_targets_the_real_bottleneck,
    test_apexgrid_founder_readiness_stays_unavailable_not_penalized,
]


def main() -> None:
    print("\nSIE Intelligence + Scoring Reset -- VPS regression suite")
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
