from models.startup import SIEMethodologyAnalysis
from models.scoring import StartupIntelligenceScore
from ai.startup_scoring import PILLAR_WEIGHTS


def get_recommendation(score: float) -> str:
    if score >= 85:
        return "Strong Investment Candidate"
    if score >= 70:
        return "Promising but Needs Diligence"
    if score >= 55:
        return "Early but Watchable"
    if score >= 40:
        return "Needs Significant Validation"
    return "Not Investment Ready"


def build_startup_scorecard(
    analysis: SIEMethodologyAnalysis,
) -> StartupIntelligenceScore:
    market = analysis.market.score_breakdown
    team = analysis.team.score_breakdown
    product = analysis.product.score_breakdown
    execution = analysis.execution.score_breakdown
    traction = analysis.traction.score_breakdown
    financial_health = analysis.financial_health.score_breakdown

    overall_score_0_to_10 = (
    market.score * PILLAR_WEIGHTS["market"]
    + team.score * PILLAR_WEIGHTS["team"]
    + product.score * PILLAR_WEIGHTS["product"]
    + execution.score * PILLAR_WEIGHTS["execution"]
    + traction.score * PILLAR_WEIGHTS["traction"]
    + financial_health.score * PILLAR_WEIGHTS["financial_health"]
)

    overall_score = round(overall_score_0_to_10 * 10, 1)

    return StartupIntelligenceScore(
        overall_score=overall_score,
        recommendation=get_recommendation(overall_score),
        market=market,
        team=team,
        product=product,
        execution=execution,
        traction=traction,
        financial_health=financial_health,
    )