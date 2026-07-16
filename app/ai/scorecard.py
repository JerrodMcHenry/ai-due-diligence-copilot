from models.startup import SIEMethodologyAnalysis
from models.scoring import StartupIntelligenceScore
from ai.startup_scoring import PILLAR_WEIGHTS


def get_recommendation(score: float | None) -> str:
    if score is None:
        return "Insufficient Evidence"

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
    pillar_breakdowns = {
        "market": (
            analysis.market.score_breakdown
            if analysis.market
            else None
        ),
        "team": (
            analysis.team.score_breakdown
            if analysis.team
            else None
        ),
        "product": (
            analysis.product.score_breakdown
            if analysis.product
            else None
        ),
        "execution": (
            analysis.execution.score_breakdown
            if analysis.execution
            else None
        ),
        "traction": (
            analysis.traction.score_breakdown
            if analysis.traction
            else None
        ),
        "financial_health": (
            analysis.financial_health.score_breakdown
            if analysis.financial_health
            else None
        ),
    }

    scored_pillars: list[tuple[float, float]] = []

    for pillar_name, score_breakdown in pillar_breakdowns.items():
        if score_breakdown is None:
            continue

        if score_breakdown.score is None:
            continue

        scored_pillars.append(
            (
                score_breakdown.score,
                PILLAR_WEIGHTS[pillar_name],
            )
        )

    if scored_pillars:
        included_weight = sum(
            weight
            for _, weight in scored_pillars
        )

        weighted_score_0_to_10 = sum(
            score * weight
            for score, weight in scored_pillars
        ) / included_weight

        overall_score = round(
            weighted_score_0_to_10 * 10,
            1,
        )
    else:
        overall_score = None

    return StartupIntelligenceScore(
        overall_score=overall_score,
        recommendation=get_recommendation(
            overall_score
        ),
        market=(
            pillar_breakdowns["market"]
            or StartupIntelligenceScore.model_fields[
                "market"
            ].default_factory()
        ),
        team=(
            pillar_breakdowns["team"]
            or StartupIntelligenceScore.model_fields[
                "team"
            ].default_factory()
        ),
        product=(
            pillar_breakdowns["product"]
            or StartupIntelligenceScore.model_fields[
                "product"
            ].default_factory()
        ),
        execution=(
            pillar_breakdowns["execution"]
            or StartupIntelligenceScore.model_fields[
                "execution"
            ].default_factory()
        ),
        traction=(
            pillar_breakdowns["traction"]
            or StartupIntelligenceScore.model_fields[
                "traction"
            ].default_factory()
        ),
        financial_health=(
            pillar_breakdowns["financial_health"]
            or StartupIntelligenceScore.model_fields[
                "financial_health"
            ].default_factory()
        ),
    )