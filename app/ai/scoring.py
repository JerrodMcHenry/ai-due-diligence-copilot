from models.scoring import Subscore, PillarScoreBreakdown


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


def get_scoring_dimensions(pillar: str) -> list[tuple[str, float]]:
    return SIE_SCORING_CONFIG[pillar]


def calculate_weighted_score(subscores: list[Subscore]) -> float:
    if not subscores:
        return 0.0

    total_weight = sum(subscore.weight for subscore in subscores)

    if total_weight == 0:
        return 0.0

    weighted_score = (
        sum(subscore.score * subscore.weight for subscore in subscores)
        / total_weight
    )

    return round(weighted_score, 1)


def create_subscores(definitions: list[tuple[str, float]]) -> list[Subscore]:
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

    return score_breakdown