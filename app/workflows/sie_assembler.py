from models.startup import (
    SIEMethodologyAnalysis,
    SIEContext,
    PillarAnalysis,
)

from ai.scoring import finalize_pillar_score
from ai.scorecard import build_startup_scorecard


def finalize_score_breakdown(analysis_result):
    score_breakdown = getattr(analysis_result, "score_breakdown", None)

    if score_breakdown is None:
        return None

    return finalize_pillar_score(score_breakdown)


def build_pillar_analysis(analysis_result) -> PillarAnalysis:
    score_breakdown = finalize_score_breakdown(analysis_result)

    final_score = score_breakdown.score if score_breakdown else 0.0
    final_confidence = (
        score_breakdown.confidence
        if score_breakdown
        else "Low"
    )

    evidence = getattr(analysis_result, "evidence", [])

    return PillarAnalysis(
        score=final_score,
        confidence=final_confidence,
        summary=getattr(analysis_result, "summary", "") or "",
        evidence=evidence,
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
    readiness: dict | None = None,
) -> SIEMethodologyAnalysis:
    sie_analysis = SIEMethodologyAnalysis(
        context=context,

        market=build_pillar_analysis(market_analysis),
        team=build_pillar_analysis(team_analysis),
        product=build_pillar_analysis(product_analysis),
        execution=build_pillar_analysis(execution_analysis),
        traction=build_pillar_analysis(traction_analysis),
        financial_health=build_pillar_analysis(financial_analysis),

        milestone_readiness_score=(
            readiness.get("readiness_score") or 0.0
            if readiness
            else 0.0
),

        executive_coaching_summary=(
            readiness.get("readiness_summary") or ""
            if readiness
            else ""
),

        next_actions=[
    "Validate retention and churn metrics",
    "Clarify product differentiation",
    "Document go-to-market strategy",
    "Provide unit economics and runway data",
]
    )

    sie_analysis.startup_scorecard = build_startup_scorecard(sie_analysis)

    sie_analysis.startup_intelligence_score = (
        sie_analysis.startup_scorecard.overall_score
    )

    return sie_analysis