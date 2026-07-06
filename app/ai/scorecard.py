from models.startup import SIEMethodologyAnalysis
from models.scoring import StartupIntelligenceScore


def build_startup_scorecard(
    analysis: SIEMethodologyAnalysis,
) -> StartupIntelligenceScore:
    return StartupIntelligenceScore(
        overall_score=analysis.startup_intelligence_score,
        recommendation=None,
        market=analysis.market.score_breakdown if analysis.market else None,
        team=analysis.team.score_breakdown if analysis.team else None,
        product=analysis.product.score_breakdown if analysis.product else None,
        execution=(
            analysis.execution.score_breakdown
            if analysis.execution
            else None
        ),
        traction=(
            analysis.traction.score_breakdown
            if analysis.traction
            else None
        ),
        financial_health=(
            analysis.financial_health.score_breakdown
            if analysis.financial_health
            else None
        ),
    )