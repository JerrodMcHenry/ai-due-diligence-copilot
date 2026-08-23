"""
Regression test for the stage-extraction/mapping defect (SIE Scoring
Reliability sprint, Phase 6).

generate_structured_analysis() (app/ai/structured_analysis.py) returns a
single "stage" key (e.g. "Series A"). build_sie_methodology_analysis()
previously read "company_stage" and "funding_stage" instead -- keys that
never existed in that dict -- so SIEContext.company_stage and
funding_stage were silently empty on every analysis, including
NovaLedger's, which explicitly stated "Series A" in its company_text.

No LLM calls are made here -- build_sie_methodology_analysis() is
exercised directly with a synthetic structured_analysis dict and empty
(but valid) pillar-analysis-result objects, since the mapping happens
entirely in plain Python before any scoring math runs.

Run with:
    python -m app.tests.test_stage_extraction
"""

from app.models.analysis import (
    ExecutionAnalysisResult,
    FinancialAnalysisResult,
    FounderAnalysisResult,
    MarketAnalysisResult,
    ProductAnalysisResult,
    TractionAnalysisResult,
)
from app.workflows.due_diligence_workflow import build_sie_methodology_analysis


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build(structured_analysis: dict):
    return build_sie_methodology_analysis(
        structured_analysis=structured_analysis,
        readiness=None,
        founder_analysis=FounderAnalysisResult(),
        market_analysis=MarketAnalysisResult(),
        product_analysis=ProductAnalysisResult(),
        execution_analysis=ExecutionAnalysisResult(),
        traction_analysis=TractionAnalysisResult(),
        financial_analysis=FinancialAnalysisResult(),
    )


def test_explicit_stage_populates_company_stage_and_funding_stage() -> None:
    """The NovaLedger case: an explicit stage in the extracted structured
    analysis must end up on the canonical context, not be silently
    dropped."""
    analysis = build({
        "company_name": "NovaLedger",
        "industry": "Fintech",
        "business_model": "SaaS",
        "stage": "Series A",
    })

    expect(
        analysis.context.company_stage == "Series A",
        f"Expected context.company_stage == 'Series A', got "
        f"{analysis.context.company_stage!r}",
    )
    expect(
        analysis.context.funding_stage == "Series A",
        f"Expected context.funding_stage == 'Series A', got "
        f"{analysis.context.funding_stage!r}",
    )


def test_missing_stage_leaves_context_empty_not_error() -> None:
    """When the model genuinely doesn't return a stage, context fields
    should stay empty strings rather than raising or defaulting to a
    placeholder value."""
    analysis = build({
        "company_name": "UnknownCo",
        "industry": "SaaS",
        "business_model": "SaaS",
    })

    expect(
        analysis.context.company_stage == "",
        f"Expected empty company_stage when no stage was extracted, got "
        f"{analysis.context.company_stage!r}",
    )
    expect(
        analysis.context.funding_stage == "",
        f"Expected empty funding_stage when no stage was extracted, got "
        f"{analysis.context.funding_stage!r}",
    )


def test_other_context_fields_still_populated_correctly() -> None:
    """The stage fix must not disturb the other context fields."""
    analysis = build({
        "company_name": "NovaLedger",
        "industry": "Fintech",
        "business_model": "SaaS",
        "stage": "Series A",
    })

    expect(
        analysis.context.company_name == "NovaLedger",
        f"company_name regressed: {analysis.context.company_name!r}",
    )
    expect(
        analysis.context.industry == "Fintech",
        f"industry regressed: {analysis.context.industry!r}",
    )
    expect(
        analysis.context.business_model == "SaaS",
        f"business_model regressed: {analysis.context.business_model!r}",
    )


TESTS = [
    test_explicit_stage_populates_company_stage_and_funding_stage,
    test_missing_stage_leaves_context_empty_not_error,
    test_other_context_fields_still_populated_correctly,
]


def main() -> None:
    print("\nSIE stage-extraction regression tests")
    print("-" * 72)

    failures: list[str] = []

    for test in TESTS:
        name = test.__name__

        try:
            test()
        except AssertionError as error:
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
