"""
Synthetic profile library (Phase 10.8F, Parts 11-12).

Every profile ID starts with SYNTH_ and is validated at construction
(company.py) to contain no real-company-name fragment. All facts,
dates, and figures are invented for testing purposes only.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.calibration.sps_v3 import factory as f
from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.types import (
    CompetitorType,
    CustomerType,
    FounderExperienceType,
    FounderOutcomeType,
    MarketEstimateSourceType,
    ProvenanceGrade,
    RevenueMetricType,
    Stage,
)

D2024 = date(2024, 1, 1)
D2025 = date(2025, 1, 1)
D2026 = date(2026, 1, 1)


# ---------------------------------------------------------------------
# Part 11 -- required core profiles A-J
# ---------------------------------------------------------------------

def profile_a_exceptional_high_coverage() -> SyntheticCompany:
    """A. Exceptional / high coverage -- strong evidence across nearly
    all applicable dimensions."""
    return SyntheticCompany(
        "SYNTH_EXCEPTIONAL_HIGH_COVERAGE",
        Stage.SERIES_A,
        evidence=(
            f.market_size("5000000000", "vertical SaaS for logistics", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("40", "logistics SaaS category", ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("15", "catalyst: regulatory mandate", ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("Legacy Co", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("Rival Systems", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.customer_evidence("named customer reports 40% cost reduction", "Acme Logistics", quantified=True),
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "PriorCo Analytics"),
            f.founder_outcome("PriorCo Analytics", FounderOutcomeType.ACQUIRED, attributed=True),
            f.founder_experience("CTO", FounderExperienceType.DIRECT_DOMAIN, prior_entity=None),
            f.founder_experience("CTO", FounderExperienceType.DIRECT_DOMAIN, prior_entity=None),  # technical role signal
            f.product_capability("shipped complex integration layer", shipped=True, integration="Acme ERP"),
            f.product_capability("gtm repeatable outbound motion", shipped=True),
            f.product_capability("expansion cross-sell to adjacent SKU", shipped=True),
            f.competitor("Legacy Co", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.revenue("3000000", D2025, RevenueMetricType.ARR),
            f.revenue("1200000", D2024, RevenueMetricType.ARR),
            f.customer_count(180, D2025, CustomerType.PAYING),
            f.retention(nrr="125"),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, "Globex Inc", renewal=True),
            f.commercial_contract(CustomerType.PAYING, "Initech", renewal=True),
            f.runway_statement("24"),
        ),
    )


def profile_b_exceptional_medium_coverage() -> SyntheticCompany:
    """B. Exceptional / medium coverage -- same demonstrated strength
    where observable, materially less evidence overall."""
    return SyntheticCompany(
        "SYNTH_EXCEPTIONAL_MEDIUM_COVERAGE",
        Stage.SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "PriorCo Analytics"),
            f.founder_outcome("PriorCo Analytics", FounderOutcomeType.ACQUIRED, attributed=True),
            f.competitor("Legacy Co", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.customer_evidence("named enterprise pilot with quantified ROI", "Beta Corp", quantified=True),
            f.revenue("400000", D2025, RevenueMetricType.ARR),
        ),
    )


def profile_c_exceptional_insufficient_coverage() -> SyntheticCompany:
    """C. Exceptional / insufficient coverage -- very strong known
    evidence, too little methodology coverage overall to publish."""
    return SyntheticCompany(
        "SYNTH_EXCEPTIONAL_INSUFFICIENT_COVERAGE",
        Stage.PRE_SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.PRIOR_EXIT, "EarlierCo"),
            f.founder_outcome("EarlierCo", FounderOutcomeType.ACQUIRED, attributed=True),
        ),
    )


def profile_d_ordinary_high_coverage() -> SyntheticCompany:
    """D. Ordinary / high coverage -- broad evidence demonstrating
    genuinely ordinary performance."""
    return SyntheticCompany(
        "SYNTH_ORDINARY_HIGH_COVERAGE",
        Stage.SERIES_A,
        evidence=(
            f.market_size("800000000", "generic B2B tools", MarketEstimateSourceType.COMPANY_STATED),
            f.competitor("SomeCo", CompetitorType.ADJACENT),
            f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN),
            f.product_capability("basic shipped feature set", shipped=True),
            f.revenue("900000", D2025, RevenueMetricType.ARR),
            f.revenue("700000", D2024, RevenueMetricType.ARR),
            f.customer_count(60, D2025, CustomerType.PAYING),
            f.retention(nrr="98"),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID),
            f.runway_statement("15"),
        ),
    )


def profile_e_weak_high_coverage() -> SyntheticCompany:
    """E. Weak / high coverage -- broad affirmative evidence of
    weakness."""
    return SyntheticCompany(
        "SYNTH_WEAK_HIGH_COVERAGE",
        Stage.SERIES_A,
        evidence=(
            f.market_size("800000000", "crowded commodity tools"),
            f.competitor("BigIncumbent", CompetitorType.DIRECT),
            f.product_capability("shipped feature", shipped=True),
            f.revenue("400000", D2025, RevenueMetricType.ARR),
            f.revenue("600000", D2024, RevenueMetricType.ARR),
            f.customer_count(40, D2025, CustomerType.PAYING),
            f.runway_statement("2"),
        ),
        negative_signals=(
            f.negative_signal("revenue_decline", "growth_trajectory", "SEVERE"),
            f.negative_signal("customer_decline", "customer_adoption", "MODERATE"),
            f.negative_signal("high_churn", "retention_engagement", "SEVERE"),
            f.negative_signal("founder_departure", "leadership", "SEVERE"),
            f.negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE"),
            f.negative_signal("failed_commercial_expansion", "strategic_execution", "MODERATE"),
        ),
    )


def profile_f_weak_low_coverage() -> SyntheticCompany:
    """F. Weak / low coverage -- some negative evidence plus
    substantial unknowns."""
    return SyntheticCompany(
        "SYNTH_WEAK_LOW_COVERAGE",
        Stage.SEED,
        evidence=(
            f.revenue("50000", D2025, RevenueMetricType.ARR),
        ),
        negative_signals=(
            f.negative_signal("customer_decline", "customer_adoption", "MODERATE"),
        ),
    )


def profile_g_exceptional_pre_seed() -> SyntheticCompany:
    """G. Exceptional Pre-Seed -- no mature-company scale metrics
    required; strong stage-relative evidence."""
    return SyntheticCompany(
        "SYNTH_EXCEPTIONAL_PRE_SEED",
        Stage.PRE_SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN, prior_entity=None),
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "PriorStartup"),
            f.founder_outcome("PriorStartup", FounderOutcomeType.ACQUIRED, attributed=True),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, "PilotCo A"),
            f.commercial_contract(CustomerType.PILOT, "PilotCo B"),
            f.commercial_contract(CustomerType.PILOT, "PilotCo C"),
            f.product_capability("shipped functional MVP", shipped=True),
            f.competitor("IncumbentX", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def profile_h_weak_growth_company() -> SyntheticCompany:
    """H. Weak Growth-stage -- large absolute scale but declining
    growth, weak retention, execution deterioration."""
    return SyntheticCompany(
        "SYNTH_WEAK_GROWTH",
        Stage.GROWTH,
        evidence=(
            f.revenue("60000000", D2025, RevenueMetricType.ARR),
            f.revenue("80000000", D2024, RevenueMetricType.ARR),
            f.customer_count(3000, D2025, CustomerType.PAYING),
            f.market_size("10000000000", "enterprise category", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            f.negative_signal("revenue_decline", "growth_trajectory", "SEVERE"),
            f.negative_signal("high_churn", "retention_engagement", "SEVERE"),
            f.negative_signal("failed_commercial_expansion", "strategic_execution", "MODERATE"),
        ),
    )


def profile_i_strong_financial_health_unavailable() -> SyntheticCompany:
    """I. Strong / Financial Health unavailable -- strong across
    observable pillars with private financial data absent."""
    return SyntheticCompany(
        "SYNTH_STRONG_FINHEALTH_UNAVAILABLE",
        Stage.SERIES_A,
        evidence=(
            f.market_size("4000000000", "vertical fintech", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("35", "vertical fintech category", ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("OldGuard Inc", CompetitorType.DIRECT, differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.customer_evidence("named customer quantified savings", "MegaBank Sub", quantified=True),
            f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN),
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "FirstVenture"),
            f.founder_outcome("FirstVenture", FounderOutcomeType.ACQUIRED, attributed=True),
            f.product_capability("shipped integration", shipped=True, integration="Core Banking API"),
            f.product_capability("gtm repeatable channel", shipped=True),
            f.revenue("2500000", D2025, RevenueMetricType.ARR),
            f.revenue("900000", D2024, RevenueMetricType.ARR),
            f.customer_count(120, D2025, CustomerType.PAYING),
            f.retention(nrr="130"),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, renewal=True),
            # Deliberately zero CashObservation/BurnObservation/RunwayStatementObservation
            # -- Financial Health should resolve to UNAVAILABLE_PRIVATE_INFORMATION.
        ),
    )


def profile_j_abundant_evidence_substantial_negative() -> SyntheticCompany:
    """J. Abundant evidence + substantial negative evidence -- evidence
    abundance must not masquerade as strength."""
    return SyntheticCompany(
        "SYNTH_ABUNDANT_NEGATIVE",
        Stage.SERIES_A,
        evidence=(
            f.market_size("5000000000", "large but commoditizing market", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("BigCo", CompetitorType.DIRECT, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.competitor("MidCo", CompetitorType.DIRECT, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN),
            f.product_capability("shipped feature", shipped=True),
            f.revenue("5000000", D2025, RevenueMetricType.ARR),
            f.revenue("6000000", D2024, RevenueMetricType.ARR),
            f.customer_count(400, D2025, CustomerType.PAYING),
        ),
        negative_signals=(
            f.negative_signal("revenue_decline", "growth_trajectory", "SEVERE"),
            f.negative_signal("high_churn", "retention_engagement", "SEVERE"),
            f.negative_signal("founder_departure", "leadership", "SEVERE"),
            f.negative_signal("customer_concentration", "revenue_quality", "MODERATE"),
            f.negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE"),
        ),
    )


CORE_PROFILES = {
    "A": profile_a_exceptional_high_coverage,
    "B": profile_b_exceptional_medium_coverage,
    "C": profile_c_exceptional_insufficient_coverage,
    "D": profile_d_ordinary_high_coverage,
    "E": profile_e_weak_high_coverage,
    "F": profile_f_weak_low_coverage,
    "G": profile_g_exceptional_pre_seed,
    "H": profile_h_weak_growth_company,
    "I": profile_i_strong_financial_health_unavailable,
    "J": profile_j_abundant_evidence_substantial_negative,
}


# ---------------------------------------------------------------------
# Part 12 -- the 15 adversarial stress cases from the Calibration Plan.
# Several intentionally reuse Part 11 fixtures (explicitly permitted:
# "Overlap with Part 11 is fine; reuse fixtures rather than duplicating
# them"). Cases without a natural reuse get their own small fixture.
# ---------------------------------------------------------------------

def stress_1_famous_abundant_mediocre() -> SyntheticCompany:
    """Simulates 'famous company' via REDUNDANT low-signal secondary
    sources repeating the same generic fact, never via a real company
    name -- this is the harness's operationalization of 'fame' per
    Part 16's redundant-evidence attack, reused here."""
    redundant = tuple(
        f.competitor("SameCompetitor", CompetitorType.ADJACENT, grade=ProvenanceGrade.SECONDARY_ESTIMATE)
        for _ in range(20)
    )
    return SyntheticCompany("SYNTH_ABUNDANT_MEDIOCRE_SIGNAL", Stage.GROWTH, evidence=redundant)


def stress_2_obscure_sparse_strong() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_OBSCURE_SPARSE_STRONG",
        Stage.SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.PRIOR_EXIT, "QuietPriorCo", grade=ProvenanceGrade.PRIMARY_VERIFIED),
            f.founder_outcome("QuietPriorCo", FounderOutcomeType.ACQUIRED, attributed=True, grade=ProvenanceGrade.PRIMARY_VERIFIED),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, "OneRealCustomer", renewal=True, grade=ProvenanceGrade.PRIMARY_VERIFIED),
        ),
    )


def stress_3_preseed_no_revenue_exceptional_validation() -> SyntheticCompany:
    return profile_g_exceptional_pre_seed()


def stress_4_growth_large_revenue_sharp_decline() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_GROWTH_SHARP_DECLINE",
        Stage.GROWTH,
        evidence=(
            f.revenue("40000000", D2024, RevenueMetricType.ARR),
            f.revenue("20000000", D2025, RevenueMetricType.ARR),
        ),
    )


def stress_5_huge_market_terrible_product() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_HUGE_MARKET_TERRIBLE_PRODUCT",
        Stage.SERIES_A,
        evidence=(
            f.market_size("20000000000", "massive category", MarketEstimateSourceType.THIRD_PARTY_RESEARCH, ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            f.market_growth("50", "massive category growth", ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            f.negative_signal("product_shutdown", "product_execution", "SEVERE"),
        ),
    )


def stress_6_elite_team_no_traction() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_ELITE_TEAM_NO_TRACTION",
        Stage.SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "NotableCo"),
            f.founder_outcome("NotableCo", FounderOutcomeType.IPO, attributed=True, grade=ProvenanceGrade.PRIMARY_VERIFIED),
            f.founder_experience("CTO", FounderExperienceType.DIRECT_DOMAIN),
        ),
    )


def stress_7_mediocre_team_exceptional_traction() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_MEDIOCRE_TEAM_EXCEPTIONAL_TRACTION",
        Stage.SERIES_A,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.ADJACENT_DOMAIN),
            f.revenue("6000000", D2025, RevenueMetricType.ARR),
            f.revenue("1500000", D2024, RevenueMetricType.ARR),
            f.customer_count(500, D2025, CustomerType.PAYING),
            f.retention(nrr="140"),
            f.commercial_contract(CustomerType.SIGNED_CONTRACT_UNPAID, renewal=True),
            f.commercial_contract(CustomerType.PAYING, renewal=True),
        ),
    )


def stress_8_high_funding_weak_unit_economics() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_HIGH_FUNDING_WEAK_UNIT_ECON",
        Stage.SERIES_A,
        evidence=(
            f.revenue("2000000", D2025, RevenueMetricType.ARR),
            f.burn("400000", D2025),  # $4.8M annualized burn vs $2M revenue -> weak ratio
        ),
    )


def stress_9_profitable_slow_growth() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_PROFITABLE_SLOW_GROWTH",
        Stage.SERIES_A,
        evidence=(
            f.revenue("2200000", D2025, RevenueMetricType.ARR),
            f.revenue("2000000", D2024, RevenueMetricType.ARR),
            f.runway_statement("36"),
        ),
    )


def stress_10_high_growth_catastrophic_burn() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_HIGH_GROWTH_CATASTROPHIC_BURN",
        Stage.SERIES_A,
        evidence=(
            f.revenue("4000000", D2025, RevenueMetricType.ARR),
            f.revenue("1000000", D2024, RevenueMetricType.ARR),
            f.runway_statement("2"),
        ),
    )


def stress_11_great_product_tiny_market() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_GREAT_PRODUCT_TINY_MARKET",
        Stage.SEED,
        evidence=(
            f.product_capability("shipped highly-rated product", shipped=True, reliability="99.99% uptime"),
            f.customer_evidence("named customer quantified outcome", "NicheCo", quantified=True),
            f.market_size("15000000", "extremely narrow niche", MarketEstimateSourceType.COMPANY_STATED),
        ),
    )


def stress_12_conflicting_evidence() -> SyntheticCompany:
    # Two RevenueObservations, same metric_type+date, different amounts --
    # exercised directly in the test suite via a dedicated conflict
    # check rather than a scored profile (Rulebook Part 6: conflicting
    # observations should resolve to UNAVAILABLE_CONFLICTING_EVIDENCE,
    # not be silently included here as if resolved).
    return SyntheticCompany(
        "SYNTH_CONFLICTING_EVIDENCE",
        Stage.SEED,
        evidence=(
            f.revenue("1000000", D2025, RevenueMetricType.ARR, grade=ProvenanceGrade.PRIMARY_SELF_REPORTED, excerpt="founder states $1M ARR"),
            f.revenue("400000", D2025, RevenueMetricType.ARR, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY, excerpt="independent report states $400K ARR"),
        ),
    )


def stress_13_stale_evidence() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_STALE_EVIDENCE",
        Stage.SERIES_A,
        evidence=(
            f.revenue("1000000", date(2019, 1, 1), RevenueMetricType.ARR),
            f.founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN),
        ),
    )


def stress_14_founder_self_report_conflicts_external() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_SELF_REPORT_VS_EXTERNAL",
        Stage.SEED,
        evidence=(
            f.founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "ClaimedPriorCo", grade=ProvenanceGrade.PRIMARY_SELF_REPORTED),
            f.founder_outcome("ClaimedPriorCo", FounderOutcomeType.STILL_OPERATING, attributed=False, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def stress_15_nearly_no_evidence() -> SyntheticCompany:
    return SyntheticCompany(
        "SYNTH_NEARLY_NO_EVIDENCE",
        Stage.SEED,
        evidence=(
            f.product_capability("vague shipped claim", shipped=True, grade=ProvenanceGrade.SECONDARY_ESTIMATE),
        ),
    )


ADVERSARIAL_PROFILES = {
    1: stress_1_famous_abundant_mediocre,
    2: stress_2_obscure_sparse_strong,
    3: stress_3_preseed_no_revenue_exceptional_validation,
    4: stress_4_growth_large_revenue_sharp_decline,
    5: stress_5_huge_market_terrible_product,
    6: stress_6_elite_team_no_traction,
    7: stress_7_mediocre_team_exceptional_traction,
    8: stress_8_high_funding_weak_unit_economics,
    9: stress_9_profitable_slow_growth,
    10: stress_10_high_growth_catastrophic_burn,
    11: stress_11_great_product_tiny_market,
    12: stress_12_conflicting_evidence,
    13: stress_13_stale_evidence,
    14: stress_14_founder_self_report_conflicts_external,
    15: stress_15_nearly_no_evidence,
}
