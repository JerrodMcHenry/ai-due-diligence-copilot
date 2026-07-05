from models.startup import (
    SIEMethodologyAnalysis,
    SIEContext,
    PillarAnalysis,
)

from ai.scoring import finalize_pillar_score
from ai.startup_scoring import calculate_startup_intelligence_score


def finalize_score_breakdown(analysis_result):
    score_breakdown = getattr(analysis_result, "score_breakdown", None)

    if score_breakdown is None:
        return None

    return finalize_pillar_score(score_breakdown)


def build_pillar_analysis(
    analysis_result,
    score: float | None = None,
) -> PillarAnalysis:
    score_breakdown = finalize_score_breakdown(analysis_result)

    final_score = (
        score_breakdown.score
        if score_breakdown and score_breakdown.score is not None
        else score
    )

    return PillarAnalysis(
        score=final_score,
        confidence=getattr(analysis_result, "confidence", None),
        summary=getattr(analysis_result, "summary", None),
        evidence=getattr(analysis_result, "evidence", []),
        strengths=getattr(analysis_result, "strengths", []),
        weaknesses=getattr(analysis_result, "weaknesses", []),
        recommendations=getattr(analysis_result, "recommendations", []),
        score_breakdown=score_breakdown,
    )


def assemble_sie_analysis(
    context: SIEContext,
    market_analysis,
    team_analysis,
    product_analysis,
    execution_analysis,
    traction_analysis,
    financial_analysis,
    scores: dict,
    readiness: dict | None = None,
) -> SIEMethodologyAnalysis:
    sie_analysis = SIEMethodologyAnalysis(
        context=context,

        market=build_pillar_analysis(
            market_analysis,
            scores.get("market_score"),
        ),

        team=build_pillar_analysis(
            team_analysis,
            scores.get("team_score"),
        ),

        product=build_pillar_analysis(
            product_analysis,
            scores.get("product_score"),
        ),

        execution=build_pillar_analysis(
            execution_analysis,
            scores.get("competition_score"),
        ),

        traction=build_pillar_analysis(
            traction_analysis,
            scores.get("traction_score"),
        ),

        financial_health=build_pillar_analysis(
            financial_analysis,
            scores.get("financial_score"),
        ),

        milestone_readiness_score=(
            readiness.get("readiness_score")
            if readiness
            else None
        ),

        executive_coaching_summary=(
            readiness.get("readiness_summary")
            if readiness
            else None
        ),

        next_actions=(
            readiness.get("strengths", []) + readiness.get("weaknesses", [])
            if readiness
            else []
        ),
    )

    sie_analysis.startup_intelligence_score = (
        calculate_startup_intelligence_score(sie_analysis)
    )

    return sie_analysis