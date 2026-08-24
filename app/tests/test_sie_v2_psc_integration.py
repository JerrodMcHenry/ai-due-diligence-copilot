"""
Integration tests for Partial Structural Coverage (PSC) wiring into the live
canonical output (app/workflows/sie_assembler.py::assemble_sie_analysis --
Blocker 3, post-implementation review).

Run with:
    python -m app.tests.test_sie_v2_psc_integration
"""

from app.workflows.sie_assembler import assemble_sie_analysis
from app.models.startup import SIEContext, SIEMethodologyAnalysis, PartialStructuralCoverage
from app.models.analysis import (
    MarketAnalysisResult,
    FounderAnalysisResult,
    ProductAnalysisResult,
    ExecutionAnalysisResult,
    TractionAnalysisResult,
    FinancialAnalysisResult,
)
from app.models.scoring import PillarScoreBreakdown, Subscore


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _scored_pillar(result_model, pillar_name: str):
    return result_model(
        summary=f"{pillar_name} summary",
        score_breakdown=PillarScoreBreakdown(
            pillar=pillar_name,
            subscores=[Subscore(name="Dim A", score=7.0, weight=1.0, evidence_status="Observed")],
        ),
    )


def _unavailable_pillar(result_model, pillar_name: str):
    return result_model(
        summary=f"{pillar_name} summary",
        score_breakdown=PillarScoreBreakdown(
            pillar=pillar_name,
            subscores=[Subscore(name="Dim A", score=None, weight=1.0, evidence_status="Unavailable")],
        ),
    )


def _assemble(traction_scored: bool):
    traction = (
        _scored_pillar(TractionAnalysisResult, "Traction")
        if traction_scored
        else _unavailable_pillar(TractionAnalysisResult, "Traction")
    )
    return assemble_sie_analysis(
        context=SIEContext(company_name="PSC Test Co"),
        market_analysis=_scored_pillar(MarketAnalysisResult, "Market"),
        team_analysis=_scored_pillar(FounderAnalysisResult, "Team"),
        product_analysis=_scored_pillar(ProductAnalysisResult, "Product"),
        execution_analysis=_scored_pillar(ExecutionAnalysisResult, "Execution"),
        traction_analysis=traction,
        financial_analysis=_scored_pillar(FinancialAnalysisResult, "Financial Health"),
    )


def test_psc_populated_when_all_pillars_scored() -> None:
    analysis = _assemble(traction_scored=True)
    expect(analysis.structural_coverage is not None, "structural_coverage must be populated by assemble_sie_analysis")
    expect(
        analysis.structural_coverage.partial_structural_coverage is False,
        "All six pillars scored -- PSC must not trigger",
    )
    expect(analysis.structural_coverage.pillars_unavailable_entirely == [], "No pillar should be listed as unavailable")


def test_psc_triggers_when_a_whole_pillar_is_unavailable() -> None:
    analysis = _assemble(traction_scored=False)
    expect(analysis.structural_coverage is not None, "structural_coverage must be populated")
    expect(analysis.structural_coverage.partial_structural_coverage is True, "A wholly-unavailable pillar must trigger PSC")
    expect(
        "traction" in analysis.structural_coverage.pillars_unavailable_entirely,
        f"Traction should be listed, got {analysis.structural_coverage.pillars_unavailable_entirely}",
    )


def test_psc_never_changes_sps_math() -> None:
    """Blocker 3's hard requirement: PSC is a display label, never a
    mathematical penalty to startup_intelligence_score."""
    scored = _assemble(traction_scored=True)
    unavailable = _assemble(traction_scored=False)

    # Both cases must go through the exact same calculate_investment_score()
    # call -- the PSC-triggering case's SPS must be a pure function of the
    # pillar scores that actually exist, not additionally penalized because
    # structural_coverage.partial_structural_coverage is True.
    expect(
        isinstance(scored.startup_intelligence_score, float) and isinstance(unavailable.startup_intelligence_score, float),
        "startup_intelligence_score must always be a float regardless of PSC state",
    )
    # The two scenarios differ in which pillars are scored, so their SPS
    # values are not expected to match -- what matters is that computing SPS
    # never reads structural_coverage at all. Verify by constructing an
    # analysis, capturing its SPS, then overwriting structural_coverage and
    # recomputing -- the score must be identical either way.
    from app.ai.investment_score import calculate_investment_score

    before = calculate_investment_score(scored).overall_score
    scored.structural_coverage = PartialStructuralCoverage(partial_structural_coverage=True, pillars_unavailable_entirely=["market", "team", "product", "execution", "traction", "financial_health"], note="synthetic")
    after = calculate_investment_score(scored).overall_score
    expect(before == after, f"SPS changed after mutating structural_coverage alone: {before} -> {after}")


def test_old_style_stored_analysis_without_structural_coverage_still_validates() -> None:
    """A pre-Blocker-3 stored JSONB methodology blob has no
    structural_coverage key at all -- must decode to None, not error and
    not be silently treated as 'fully covered.'"""
    old_style = {
        "market": {"score": 6.5, "confidence": "Medium", "score_breakdown": {"pillar": "market", "score": 6.5, "subscores": []}},
        "startup_intelligence_score": 62.0,
    }
    analysis = SIEMethodologyAnalysis(**old_style)
    expect(analysis.structural_coverage is None, "Historical records must decode structural_coverage as None, never a fabricated value")


TESTS = [
    test_psc_populated_when_all_pillars_scored,
    test_psc_triggers_when_a_whole_pillar_is_unavailable,
    test_psc_never_changes_sps_math,
    test_old_style_stored_analysis_without_structural_coverage_still_validates,
]


def main() -> None:
    print("\nSIE Methodology v2 -- Partial Structural Coverage integration tests")
    print("-" * 72)

    failures: list[str] = []
    for test in TESTS:
        name = test.__name__
        try:
            test()
        except AssertionError as error:
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)
        except Exception as error:  # noqa: BLE001 -- surface unexpected errors as failures too
            print(f"ERROR {name}\n      {type(error).__name__}: {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
