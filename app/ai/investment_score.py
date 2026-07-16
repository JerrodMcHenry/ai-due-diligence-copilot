from pydantic import BaseModel, Field

from models.startup import SIEMethodologyAnalysis


class ScoreAdjustment(BaseModel):
    name: str
    points: float
    rationale: str


class InvestmentScore(BaseModel):
    base_score: float = 0.0
    adjustments: list[ScoreAdjustment] = Field(default_factory=list)
    overall_score: float = 0.0
    recommendation: str = ""


PILLAR_WEIGHTS = {
    "market": 0.20,
    "team": 0.20,
    "product": 0.15,
    "execution": 0.15,
    "traction": 0.15,
    "financial_health": 0.15,
}


def clamp_score(score: float) -> float:
    return max(
        0.0,
        min(100.0, round(score, 1)),
    )


def calculate_base_score(
    analysis: SIEMethodologyAnalysis,
) -> float:
    """
    Calculate the overall score using only pillars that were
    responsibly scored.

    Pillars with score=None are excluded instead of being treated
    as zero. The remaining pillar weights are renormalized.
    """
    scored_pillars: list[tuple[float, float]] = []

    for pillar_name, weight in PILLAR_WEIGHTS.items():
        pillar = getattr(
            analysis,
            pillar_name,
            None,
        )

        if pillar is None:
            continue

        pillar_score = getattr(
            pillar,
            "score",
            None,
        )

        if pillar_score is None:
            continue

        scored_pillars.append(
            (pillar_score, weight)
        )

    if not scored_pillars:
        return 0.0

    included_weight = sum(
        weight
        for _, weight in scored_pillars
    )

    if included_weight <= 0:
        return 0.0

    weighted_score = sum(
        pillar_score * weight
        for pillar_score, weight in scored_pillars
    ) / included_weight

    return round(
        weighted_score * 10,
        1,
    )


def collect_text(
    analysis: SIEMethodologyAnalysis,
) -> str:
    parts: list[str] = []

    for pillar_name in PILLAR_WEIGHTS:
        pillar = getattr(
            analysis,
            pillar_name,
            None,
        )

        if pillar is None:
            continue

        parts.append(
            getattr(pillar, "summary", "") or ""
        )

        parts.extend(
            str(item)
            for item in getattr(
                pillar,
                "evidence",
                [],
            )
        )

        parts.extend(
            getattr(
                pillar,
                "strengths",
                [],
            )
        )

        parts.extend(
            getattr(
                pillar,
                "weaknesses",
                [],
            )
        )

    return " ".join(parts).lower()


def get_adjustments(
    analysis: SIEMethodologyAnalysis,
) -> list[ScoreAdjustment]:
    """
    Methodology v1 does not apply keyword-based score adjustments.

    Bonuses and penalties based on phrases such as "competition",
    "132%", or "25 months" are too brittle and can double-count
    evidence already reflected in pillar scores.

    Keep this function so the API shape remains backward-compatible.
    Deterministic, methodology-backed adjustments can be added later.
    """
    return []


def get_recommendation(score: float) -> str:
    if score >= 90:
        return "Exceptional Investment Candidate"

    if score >= 80:
        return "High Potential"

    if score >= 70:
        return "Promising but Needs Diligence"

    if score >= 60:
        return "Speculative"

    if score >= 50:
        return "High Risk"

    return "Not Investment Ready"


def calculate_investment_score(
    analysis: SIEMethodologyAnalysis,
) -> InvestmentScore:
    base_score = calculate_base_score(
        analysis
    )

    adjustments = get_adjustments(
        analysis
    )

    adjustment_total = sum(
        adjustment.points
        for adjustment in adjustments
    )

    overall_score = clamp_score(
        base_score + adjustment_total
    )

    return InvestmentScore(
        base_score=base_score,
        adjustments=adjustments,
        overall_score=overall_score,
        recommendation=get_recommendation(
            overall_score
        ),
    )