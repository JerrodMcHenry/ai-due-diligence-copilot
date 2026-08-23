"""
Focused tests for the canonical SIE pillar-weight consolidation.

This repository has no pytest dependency (see app/calibration/README.md) --
these are plain, hand-rolled assertions in the same style as
app/calibration/run_calibration.py, so they run without adding a new test
framework.

Run with:
    python -m app.tests.test_scoring_weights
"""

import math

from app.ai import investment_score
from app.ai import scorecard
from app.ai.scoring_methodology import PILLAR_WEIGHTS as CANONICAL_WEIGHTS
from app.ai.investment_score import calculate_investment_score
from app.ai.scorecard import build_startup_scorecard
from app.models.scoring import PillarScoreBreakdown
from app.models.startup import PillarAnalysis, SIEMethodologyAnalysis


PILLAR_NAMES = [
    "market",
    "team",
    "product",
    "execution",
    "traction",
    "financial_health",
]


def make_pillar(score: float | None) -> PillarAnalysis:
    """
    Build a PillarAnalysis with a given score, kept consistent between
    PillarAnalysis.score (read by calculate_investment_score) and
    PillarAnalysis.score_breakdown.score (read by build_startup_scorecard),
    so both consumers see the same synthetic pillar result.
    """
    return PillarAnalysis(
        score=score,
        confidence="Medium",
        score_breakdown=PillarScoreBreakdown(
            score=score,
            confidence="Medium",
        ),
    )


def make_analysis(scores: dict[str, float | None]) -> SIEMethodologyAnalysis:
    """scores must contain all six pillar names, value None allowed."""
    kwargs = {
        name: make_pillar(scores[name])
        for name in PILLAR_NAMES
    }
    return SIEMethodologyAnalysis(**kwargs)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_canonical_weights_sum_to_one() -> None:
    total = sum(CANONICAL_WEIGHTS.values())
    expect(
        math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9),
        f"Canonical PILLAR_WEIGHTS must sum to 1.0, got {total}",
    )


def test_canonical_values_match_agreed_methodology() -> None:
    expected = {
        "market": 0.20,
        "team": 0.20,
        "product": 0.20,
        "execution": 0.15,
        "traction": 0.15,
        "financial_health": 0.10,
    }
    expect(
        CANONICAL_WEIGHTS == expected,
        f"Canonical PILLAR_WEIGHTS {CANONICAL_WEIGHTS} != agreed "
        f"methodology {expected}",
    )


def test_investment_score_uses_canonical_weights() -> None:
    expect(
        investment_score.PILLAR_WEIGHTS is CANONICAL_WEIGHTS,
        "app.ai.investment_score.PILLAR_WEIGHTS must be the same object "
        "as app.ai.scoring_methodology.PILLAR_WEIGHTS (no local copy).",
    )

    # Uniform score across all pillars: overall must equal it regardless
    # of how weight is split between pillars.
    uniform = make_analysis({name: 8.0 for name in PILLAR_NAMES})
    result = calculate_investment_score(uniform).overall_score
    expect(
        result == 80.0,
        f"Uniform pillar score of 8.0 must yield overall 80.0 "
        f"independent of weight split, got {result}",
    )

    # Distinguishing scores per pillar: overall must match a manual
    # weighted average using the canonical weights exactly.
    scores = {
        "market": 9.0, "team": 7.0, "product": 6.0,
        "execution": 5.0, "traction": 8.0, "financial_health": 4.0,
    }
    result = calculate_investment_score(make_analysis(scores)).overall_score
    expected = round(
        sum(scores[p] * CANONICAL_WEIGHTS[p] for p in PILLAR_NAMES) * 10,
        1,
    )
    expect(
        result == expected,
        f"calculate_investment_score did not apply canonical weights: "
        f"expected {expected}, got {result}",
    )


def test_scorecard_uses_canonical_weights() -> None:
    expect(
        scorecard.PILLAR_WEIGHTS is CANONICAL_WEIGHTS,
        "app.ai.scorecard.PILLAR_WEIGHTS must be the same object as "
        "app.ai.scoring_methodology.PILLAR_WEIGHTS (no local copy).",
    )

    scores = {
        "market": 9.0, "team": 7.0, "product": 6.0,
        "execution": 5.0, "traction": 8.0, "financial_health": 4.0,
    }
    result = build_startup_scorecard(make_analysis(scores)).overall_score
    expected = round(
        sum(scores[p] * CANONICAL_WEIGHTS[p] for p in PILLAR_NAMES) * 10,
        1,
    )
    expect(
        result == expected,
        f"build_startup_scorecard did not apply canonical weights: "
        f"expected {expected}, got {result}",
    )


def test_investment_score_and_scorecard_agree() -> None:
    """
    The two consumers must never silently diverge again now that they
    share one canonical weight source.
    """
    scores = {
        "market": 6.5, "team": 9.5, "product": 4.0,
        "execution": 8.5, "traction": 3.5, "financial_health": 7.5,
    }
    analysis = make_analysis(scores)

    investment_result = calculate_investment_score(analysis).overall_score
    scorecard_result = build_startup_scorecard(analysis).overall_score

    expect(
        investment_result == scorecard_result,
        f"calculate_investment_score ({investment_result}) and "
        f"build_startup_scorecard ({scorecard_result}) disagree despite "
        f"sharing a canonical weight source.",
    )


def test_unavailable_pillar_renormalization_unchanged() -> None:
    """
    Reproduces the shape of NovaLedger analysis 74: one pillar (execution)
    scored None/Unavailable. The existing behavior -- exclude that pillar
    and renormalize the remaining weight -- must be preserved by the
    weight-source consolidation; only the weight *values* should change.
    """
    scores = {
        "market": 7.6, "team": 8.6, "product": 6.9,
        "execution": None, "traction": 7.5, "financial_health": 7.0,
    }
    analysis = make_analysis(scores)

    investment_result = calculate_investment_score(analysis).overall_score
    scorecard_result = build_startup_scorecard(analysis).overall_score

    available = {p: s for p, s in scores.items() if s is not None}
    included_weight = sum(CANONICAL_WEIGHTS[p] for p in available)
    expected = round(
        sum(available[p] * CANONICAL_WEIGHTS[p] for p in available)
        / included_weight
        * 10,
        1,
    )

    expect(
        investment_result == expected,
        f"Renormalization over available pillars broke: expected "
        f"{expected}, got {investment_result} "
        f"(calculate_investment_score)",
    )
    expect(
        scorecard_result == expected,
        f"Renormalization over available pillars broke: expected "
        f"{expected}, got {scorecard_result} (build_startup_scorecard)",
    )

    # The excluded pillar's weight must not silently reappear as if the
    # pillar scored zero instead of being excluded and renormalized.
    naive_zero_fill = round(
        sum(
            (score or 0.0) * CANONICAL_WEIGHTS[pillar]
            for pillar, score in scores.items()
        )
        * 10,
        1,
    )
    expect(
        investment_result != naive_zero_fill,
        "Unavailable pillar appears to be scored as 0 instead of being "
        "excluded and having the remaining weight renormalized.",
    )


TESTS = [
    test_canonical_weights_sum_to_one,
    test_canonical_values_match_agreed_methodology,
    test_investment_score_uses_canonical_weights,
    test_scorecard_uses_canonical_weights,
    test_investment_score_and_scorecard_agree,
    test_unavailable_pillar_renormalization_unchanged,
]


def main() -> None:
    print("\nSIE canonical pillar-weight tests")
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
