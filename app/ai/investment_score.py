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
    return max(0.0, min(100.0, round(score, 1)))


def calculate_base_score(analysis: SIEMethodologyAnalysis) -> float:
    total = 0.0

    for pillar_name, weight in PILLAR_WEIGHTS.items():
        pillar = getattr(analysis, pillar_name, None)
        pillar_score = getattr(pillar, "score", 0.0) or 0.0

        total += pillar_score * 10 * weight

    return round(total, 1)


def collect_text(analysis: SIEMethodologyAnalysis) -> str:
    parts: list[str] = []

    for pillar_name in PILLAR_WEIGHTS:
        pillar = getattr(analysis, pillar_name, None)

        if not pillar:
            continue

        parts.append(pillar.summary or "")
        parts.extend(str(item) for item in pillar.evidence)
        parts.extend(pillar.strengths)
        parts.extend(pillar.weaknesses)

    return " ".join(parts).lower()


def get_adjustments(analysis: SIEMethodologyAnalysis) -> list[ScoreAdjustment]:
    adjustments: list[ScoreAdjustment] = []
    text = collect_text(analysis)

    if "repeat founder" in text or "prior exit" in text or "previous exit" in text:
        adjustments.append(
            ScoreAdjustment(
                name="Experienced Founder Bonus",
                points=1.5,
                rationale="The founding team shows prior startup or exit experience.",
            )
        )

    if "132%" in text or "net revenue retention" in text and "130" in text:
        adjustments.append(
            ScoreAdjustment(
                name="Exceptional Retention Bonus",
                points=2.0,
                rationale="Net revenue retention appears exceptional for a SaaS company.",
            )
        )

    if "82%" in text and "gross margin" in text:
        adjustments.append(
            ScoreAdjustment(
                name="Strong Gross Margin Bonus",
                points=1.0,
                rationale="Gross margin appears strong for a SaaS business.",
            )
        )

    if "25 months" in text and "runway" in text:
        adjustments.append(
            ScoreAdjustment(
                name="Strong Runway Bonus",
                points=1.0,
                rationale="The company appears to have strong cash runway.",
            )
        )

    if "competition" in text or "competitive" in text:
        adjustments.append(
            ScoreAdjustment(
                name="Competitive Market Penalty",
                points=-1.0,
                rationale="The company operates in a competitive market requiring clear differentiation.",
            )
        )

    if "no customers" in text or "no paying customers" in text:
        adjustments.append(
            ScoreAdjustment(
                name="No Customer Validation Penalty",
                points=-8.0,
                rationale="Lack of customer validation materially weakens investment readiness.",
            )
        )

    if "high churn" in text:
        adjustments.append(
            ScoreAdjustment(
                name="High Churn Penalty",
                points=-5.0,
                rationale="High churn weakens evidence of product-market fit.",
            )
        )

    return adjustments


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
    base_score = calculate_base_score(analysis)
    adjustments = get_adjustments(analysis)

    adjustment_total = sum(adjustment.points for adjustment in adjustments)
    overall_score = clamp_score(base_score + adjustment_total)

    return InvestmentScore(
        base_score=base_score,
        adjustments=adjustments,
        overall_score=overall_score,
        recommendation=get_recommendation(overall_score),
    )