"""
Focused tests for minimal analysis provenance (SIE Scoring Reliability
sprint, Phase 5).

No LLM calls are made here -- build_sie_methodology_analysis() is
exercised directly with synthetic inputs, since provenance stamping
happens in plain Python before any scoring math runs.

Run with:
    python -m app.tests.test_provenance
"""

import hashlib

from app.ai.analyze_pillar import PILLAR_ANALYSIS_MODEL, PILLAR_PROMPT_VERSION
from app.ai.scoring_methodology import SCORING_VERSION
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


def build(**provenance_kwargs):
    return build_sie_methodology_analysis(
        structured_analysis={"company_name": "TestCo", "stage": "Seed"},
        readiness=None,
        founder_analysis=FounderAnalysisResult(),
        market_analysis=MarketAnalysisResult(),
        product_analysis=ProductAnalysisResult(),
        execution_analysis=ExecutionAnalysisResult(),
        traction_analysis=TractionAnalysisResult(),
        financial_analysis=FinancialAnalysisResult(),
        **provenance_kwargs,
    )


def test_static_provenance_always_stamped() -> None:
    """model/prompt/scoring versions are static constants -- they must be
    stamped even when the caller supplies no live-research provenance
    (e.g. the reliability harness)."""
    analysis = build()

    ctx = analysis.analysis_context
    expect(
        ctx.model_identifier == PILLAR_ANALYSIS_MODEL,
        f"model_identifier not stamped: {ctx.model_identifier!r}",
    )
    expect(
        ctx.prompt_version == PILLAR_PROMPT_VERSION,
        f"prompt_version not stamped: {ctx.prompt_version!r}",
    )
    expect(
        ctx.scoring_version == SCORING_VERSION,
        f"scoring_version not stamped: {ctx.scoring_version!r}",
    )
    expect(
        ctx.analyzed_at != "",
        "analyzed_at must be populated",
    )


def test_research_provenance_recorded_when_supplied() -> None:
    company_text = "TestCo builds developer tools."
    analysis = build(
        company_text=company_text,
        search_query="TestCo developer tools",
        research_brief="Verified facts: TestCo exists.",
        sources=[{"title": "TestCo homepage", "url": "https://testco.example"}],
    )

    ctx = analysis.analysis_context
    expected_hash = hashlib.sha256(company_text.encode("utf-8")).hexdigest()

    expect(
        ctx.company_text_hash == expected_hash,
        f"company_text_hash mismatch: {ctx.company_text_hash!r} != {expected_hash!r}",
    )
    expect(
        ctx.search_query == "TestCo developer tools",
        f"search_query not recorded: {ctx.search_query!r}",
    )
    expect(
        ctx.research_brief_snapshot == "Verified facts: TestCo exists.",
        f"research_brief_snapshot not recorded: {ctx.research_brief_snapshot!r}",
    )
    expect(
        ctx.source_snapshot == [{"title": "TestCo homepage", "url": "https://testco.example"}],
        f"source_snapshot not recorded: {ctx.source_snapshot!r}",
    )


def test_research_provenance_empty_when_not_supplied() -> None:
    """The harness (and any other caller that doesn't have live research)
    must get empty, not fabricated, values -- never a placeholder that
    could be mistaken for a real hash or query."""
    analysis = build()

    ctx = analysis.analysis_context
    expect(ctx.company_text_hash == "", "company_text_hash should be empty")
    expect(ctx.search_query == "", "search_query should be empty")
    expect(ctx.research_brief_snapshot == "", "research_brief_snapshot should be empty")
    expect(ctx.source_snapshot == [], "source_snapshot should be empty")


def test_two_identical_company_texts_hash_identically() -> None:
    """A deterministic hash is the whole point -- confirm it actually is
    one, and that different input produces a different hash."""
    a = build(company_text="Same text")
    b = build(company_text="Same text")
    c = build(company_text="Different text")

    expect(
        a.analysis_context.company_text_hash == b.analysis_context.company_text_hash,
        "Identical company_text must hash identically",
    )
    expect(
        a.analysis_context.company_text_hash != c.analysis_context.company_text_hash,
        "Different company_text must hash differently",
    )


TESTS = [
    test_static_provenance_always_stamped,
    test_research_provenance_recorded_when_supplied,
    test_research_provenance_empty_when_not_supplied,
    test_two_identical_company_texts_hash_identically,
]


def main() -> None:
    print("\nSIE provenance tests")
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
