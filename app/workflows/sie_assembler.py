from app.models.startup import (
    SIEMethodologyAnalysis,
    SIEContext,
    PillarAnalysis,
    PartialStructuralCoverage,
)

from app.ai.scoring import finalize_pillar_score
from app.ai.scorecard import build_startup_scorecard
from app.ai.investment_score import calculate_investment_score
from app.ai.sie_v2_evidence_semantics import compute_partial_structural_coverage
from app.models.analysis_context import AnalysisContext


def finalize_score_breakdown(analysis_result):
    score_breakdown = getattr(analysis_result, "score_breakdown", None)

    if score_breakdown is None:
        return None

    return finalize_pillar_score(score_breakdown)


def build_pillar_analysis(analysis_result) -> PillarAnalysis:
    score_breakdown = finalize_score_breakdown(analysis_result)

    final_score = score_breakdown.score if score_breakdown else None
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
    scores: dict | None = None,
    readiness: dict | None = None,
    analysis_context: AnalysisContext | None = None

) -> SIEMethodologyAnalysis:
    sie_analysis = SIEMethodologyAnalysis(
        context=context,
        analysis_context=analysis_context or AnalysisContext(),

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
        ],
    )

    # SIE Methodology v2, Part 9 item 6 (Blocker 3 fix, post-implementation
    # review): PSC is derived from actual whole-pillar availability -- each
    # pillar's already-finalized score, None meaning that pillar had zero
    # scored dimensions -- and is purely a display label layered on top.
    # Computed AFTER the six PillarAnalysis objects above (so it reads their
    # real final scores) but BEFORE calculate_investment_score() runs, to
    # make unmistakable in the code that PSC cannot influence SPS: SPS is
    # computed from sie_analysis's pillar scores exactly as before, and
    # structural_coverage is never read by calculate_investment_score() or
    # build_startup_scorecard().
    psc = compute_partial_structural_coverage(
        {
            "market": sie_analysis.market.score,
            "team": sie_analysis.team.score,
            "product": sie_analysis.product.score,
            "execution": sie_analysis.execution.score,
            "traction": sie_analysis.traction.score,
            "financial_health": sie_analysis.financial_health.score,
        }
    )
    sie_analysis.structural_coverage = PartialStructuralCoverage(**psc)

    investment_score = calculate_investment_score(sie_analysis)

    sie_analysis.startup_intelligence_score = investment_score.overall_score
    sie_analysis.startup_scorecard = build_startup_scorecard(sie_analysis)

    if sie_analysis.startup_scorecard:
        sie_analysis.startup_scorecard.overall_score = (
            investment_score.overall_score
        )
        sie_analysis.startup_scorecard.recommendation = (
            investment_score.recommendation
        )

    return sie_analysis