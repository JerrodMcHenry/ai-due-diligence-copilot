from models.scoring import PillarScoreBreakdown, Subscore


SIE_SCORING_CONFIG = {
    "Market": [
        ("Market Size", 0.25),
        ("Market Growth", 0.20),
        ("Market Timing", 0.20),
        ("Competitive Intensity", 0.15),
        ("Customer Demand", 0.20),
    ],
    "Team": [
        ("Founder-Market Fit", 0.25),
        ("Technical Capability", 0.20),
        ("Business Capability", 0.20),
        ("Leadership", 0.20),
        ("Execution Track Record", 0.15),
    ],
    "Product": [
        ("Customer Value", 0.25),
        ("Differentiation", 0.20),
        ("Usability", 0.15),
        ("Defensibility", 0.20),
        ("Adoption Potential", 0.20),
    ],
    "Execution": [
        ("Go-to-Market Execution", 0.20),
        ("Product Execution", 0.20),
        ("Operational Execution", 0.20),
        ("Strategic Execution", 0.20),
        ("Execution Velocity", 0.20),
    ],
    "Traction": [
        ("Customer Growth", 0.20),
        ("Revenue Growth", 0.20),
        ("Retention", 0.20),
        ("Engagement", 0.20),
        ("Commercial Validation", 0.20),
    ],
    "Financial Health": [
        ("Revenue Quality", 0.20),
        ("Unit Economics", 0.20),
        ("Burn Efficiency", 0.20),
        ("Runway", 0.20),
        ("Fundraising Readiness", 0.20),
    ],
}


MARKET_SUBSCORES = SIE_SCORING_CONFIG["Market"]
TEAM_SUBSCORES = SIE_SCORING_CONFIG["Team"]
PRODUCT_SUBSCORES = SIE_SCORING_CONFIG["Product"]
EXECUTION_SUBSCORES = SIE_SCORING_CONFIG["Execution"]
TRACTION_SUBSCORES = SIE_SCORING_CONFIG["Traction"]
FINANCIAL_SUBSCORES = SIE_SCORING_CONFIG["Financial Health"]


def get_scoring_dimensions(
    pillar: str,
) -> list[tuple[str, float]]:
    return SIE_SCORING_CONFIG[pillar]


def calculate_weighted_score(
    subscores: list[Subscore],
) -> float | None:
    scorable_subscores = [
        subscore
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    ]

    if not scorable_subscores:
        return None

    total_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
    )

    if total_weight <= 0:
        return None

    weighted_score = (
        sum(
            subscore.score * subscore.weight
            for subscore in scorable_subscores
        )
        / total_weight
    )

    return round(weighted_score, 1)



CONFIDENCE_VALUES = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def calculate_pillar_confidence(
    subscores: list[Subscore],
) -> str:
    scorable_subscores = [
        subscore
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    ]

    if not scorable_subscores:
        return "Low"

    total_weight = sum(
        subscore.weight
        for subscore in subscores
    )

    covered_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
    )

    if total_weight <= 0:
        return "Low"

    coverage_ratio = covered_weight / total_weight

    weighted_confidence = sum(
        CONFIDENCE_VALUES[subscore.confidence]
        * subscore.weight
        for subscore in scorable_subscores
    ) / covered_weight

    observed_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
        if subscore.evidence_status == "Observed"
    )

    observed_ratio = observed_weight / covered_weight

    if (
        coverage_ratio >= 0.80
        and weighted_confidence >= 2.4
        and observed_ratio >= 0.40
    ):
        return "High"

    if (
        coverage_ratio >= 0.40
        and weighted_confidence >= 1.6
    ):
        return "Medium"

    return "Low"




def calculate_evidence_coverage(
    subscores: list[Subscore],
) -> float:
    if not subscores:
        return 0.0

    total_weight = sum(
        subscore.weight
        for subscore in subscores
    )

    if total_weight <= 0:
        return 0.0

    covered_weight = sum(
        subscore.weight
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    )

    return round(
        (covered_weight / total_weight) * 100,
        1,
    )


def create_subscores(
    definitions: list[tuple[str, float]],
) -> list[Subscore]:
    return [
        Subscore(
            name=name,
            weight=weight,
        )
        for name, weight in definitions
    ]


def finalize_pillar_score(
    score_breakdown: PillarScoreBreakdown,
) -> PillarScoreBreakdown:
    score_breakdown.score = calculate_weighted_score(
        score_breakdown.subscores
    )

    score_breakdown.evidence_coverage = (
        calculate_evidence_coverage(
            score_breakdown.subscores
        )
    )

    score_breakdown.confidence = (
        calculate_pillar_confidence(
            score_breakdown.subscores
        )
    )

    return score_breakdown