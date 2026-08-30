"""
Tests for the SIE Methodology v2 canonical configuration
(app/ai/sie_v2_methodology.py) and its wiring into
app/ai/scoring_methodology.py / app/ai/scoring.py.

Run with:
    python -m app.tests.test_sie_v2_methodology
"""

import math

from app.ai.sie_v2_methodology import (
    DIMENSIONS,
    PILLAR_WEIGHTS,
    METHODOLOGY_VERSION,
    ScoringMode,
    AnchorStatus,
    dimensions_for_pillar,
    deterministic_dimension_names,
    UNSCORED_NARRATIVE_FLAGS,
    REMOVED_DIMENSIONS,
    FROZEN_ANCHORS,
    FROZEN_AS_PROVISIONAL_ANCHORS,
    REJECTED_ANCHORS,
)
from app.ai.scoring_methodology import SCORING_METHODOLOGY, PILLAR_WEIGHTS as PROD_PILLAR_WEIGHTS
from app.ai.scoring import get_scoring_dimensions


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_exactly_28_dimensions() -> None:
    expect(len(DIMENSIONS) == 28, f"v2 must have exactly 28 scored dimensions, got {len(DIMENSIONS)}")


def test_pillar_dimension_counts_match_spec() -> None:
    expected = {"Market": 5, "Team": 5, "Product": 5, "Execution": 4, "Traction": 5, "Financial Health": 4}
    for pillar, count in expected.items():
        actual = len(dimensions_for_pillar(pillar))
        expect(actual == count, f"{pillar} should have {count} dimensions, got {actual}")


def test_pillar_weights_sum_to_one() -> None:
    for pillar in ("Market", "Team", "Product", "Execution", "Traction", "Financial Health"):
        total = round(sum(d.weight for d in dimensions_for_pillar(pillar)), 6)
        expect(total == 1.0, f"{pillar} dimension weights must sum to 1.0, got {total}")


def test_frozen_pillar_weights_unchanged() -> None:
    expected = {"market": 0.20, "team": 0.20, "product": 0.20, "execution": 0.15, "traction": 0.15, "financial_health": 0.10}
    for pillar, weight in expected.items():
        expect(PILLAR_WEIGHTS[pillar] == weight, f"{pillar} weight should be {weight}, got {PILLAR_WEIGHTS[pillar]}")
    total = sum(PILLAR_WEIGHTS.values())
    expect(math.isclose(total, 1.0, abs_tol=1e-9), f"Pillar weights must sum to 1.0, got {total}")


def test_scoring_mode_split_5_15_8() -> None:
    deterministic = [d for d in DIMENSIONS if d.mode == ScoringMode.DETERMINISTIC]
    hybrid = [d for d in DIMENSIONS if d.mode == ScoringMode.HYBRID]
    constrained_llm = [d for d in DIMENSIONS if d.mode == ScoringMode.CONSTRAINED_LLM]
    expect(len(deterministic) == 5, f"Deterministic should be 5, got {len(deterministic)}")
    expect(len(hybrid) == 15, f"Hybrid should be 15, got {len(hybrid)}")
    expect(len(constrained_llm) == 8, f"Constrained LLM should be 8, got {len(constrained_llm)}")


def test_deterministic_dimension_names_exact() -> None:
    expected = {"Customer Growth", "Revenue Growth", "Retention", "Growth Velocity", "Unit Economics"}
    actual = deterministic_dimension_names()
    expect(actual == expected, f"Deterministic dimension set mismatch: {actual} != {expected}")


def test_methodology_version_stamped() -> None:
    # Bumped for Methodology V2.1 (Phase 10.8B, 2026-08-29) -- see
    # docs/validation/SPS_METHODOLOGY_V2_1_CHANGELOG.md. The 28-dimension
    # architecture this file otherwise tests is unchanged; only the
    # version string moved, deliberately, per Part 17's "version
    # honestly" instruction.
    expect(METHODOLOGY_VERSION == "v2.1-spec-2026-08-29", f"Unexpected methodology version: {METHODOLOGY_VERSION}")


def test_removed_and_unscored_dimensions_not_in_v2_list() -> None:
    v2_names = {d.name for d in DIMENSIONS}
    for removed in REMOVED_DIMENSIONS:
        expect(removed not in v2_names, f"{removed} was removed in v2 and must not appear in DIMENSIONS")
    for unscored in UNSCORED_NARRATIVE_FLAGS:
        expect(unscored not in v2_names, f"{unscored} is an unscored narrative flag and must not appear in DIMENSIONS")


def test_execution_weights_frozen_conservative_default() -> None:
    execution_dims = dimensions_for_pillar("Execution")
    for d in execution_dims:
        expect(d.weight == 0.25, f"Execution dimension {d.name} should be weighted .25, got {d.weight}")


def test_traction_weights_match_spec() -> None:
    expected = {"Customer Growth": 0.15, "Revenue Growth": 0.25, "Retention": 0.25, "Engagement": 0.15, "Growth Velocity": 0.20}
    for d in dimensions_for_pillar("Traction"):
        expect(d.weight == expected[d.name], f"Traction/{d.name} weight should be {expected[d.name]}, got {d.weight}")


def test_financial_health_weights_match_spec() -> None:
    expected = {"Revenue Quality": 0.20, "Unit Economics": 0.25, "Burn Efficiency": 0.25, "Runway": 0.30}
    for d in dimensions_for_pillar("Financial Health"):
        expect(d.weight == expected[d.name], f"Financial Health/{d.name} weight should be {expected[d.name]}, got {d.weight}")


def test_no_anchor_classified_reject() -> None:
    expect(len(REJECTED_ANCHORS) == 0, f"No anchor should be classified REJECT, found {REJECTED_ANCHORS}")


def test_frozen_and_provisional_registries_nonempty() -> None:
    expect(len(FROZEN_ANCHORS) >= 5, "Expected at least 5 FROZEN anchors from the calibration program")
    expect(len(FROZEN_AS_PROVISIONAL_ANCHORS) >= 5, "Expected at least 5 FROZEN_AS_PROVISIONAL anchors")


# --- Wiring into the production scoring_methodology.py / scoring.py ---

def test_production_scoring_methodology_matches_v2_dimension_list() -> None:
    v2_names_by_pillar = {
        pillar: {d.name for d in dimensions_for_pillar(pillar)}
        for pillar in ("Market", "Team", "Product", "Execution", "Traction", "Financial Health")
    }
    for pillar, names in v2_names_by_pillar.items():
        prod_names = {d.name for d in SCORING_METHODOLOGY[pillar]}
        expect(
            prod_names == names,
            f"app/ai/scoring_methodology.py's {pillar} dimension names don't match v2: "
            f"{prod_names} != {names}",
        )


def test_production_pillar_weights_match_v2() -> None:
    expect(PROD_PILLAR_WEIGHTS == PILLAR_WEIGHTS, "scoring_methodology.PILLAR_WEIGHTS must match sie_v2_methodology.PILLAR_WEIGHTS exactly")


def test_get_scoring_dimensions_single_source_of_truth() -> None:
    """Regression guard for the SIE_SCORING_CONFIG/SCORING_METHODOLOGY duplication
    fix (Phase 2): get_scoring_dimensions() must derive from SCORING_METHODOLOGY,
    not maintain its own copy."""
    for pillar in ("Market", "Team", "Product", "Execution", "Traction", "Financial Health"):
        from_scoring = dict(get_scoring_dimensions(pillar))
        from_methodology = {d.name: d.weight for d in SCORING_METHODOLOGY[pillar]}
        expect(
            from_scoring == from_methodology,
            f"get_scoring_dimensions('{pillar}') diverges from SCORING_METHODOLOGY -- "
            f"a second source of truth has reappeared.",
        )


TESTS = [
    test_exactly_28_dimensions,
    test_pillar_dimension_counts_match_spec,
    test_pillar_weights_sum_to_one,
    test_frozen_pillar_weights_unchanged,
    test_scoring_mode_split_5_15_8,
    test_deterministic_dimension_names_exact,
    test_methodology_version_stamped,
    test_removed_and_unscored_dimensions_not_in_v2_list,
    test_execution_weights_frozen_conservative_default,
    test_traction_weights_match_spec,
    test_financial_health_weights_match_spec,
    test_no_anchor_classified_reject,
    test_frozen_and_provisional_registries_nonempty,
    test_production_scoring_methodology_matches_v2_dimension_list,
    test_production_pillar_weights_match_v2,
    test_get_scoring_dimensions_single_source_of_truth,
]


def main() -> None:
    print("\nSIE Methodology v2 -- canonical configuration tests")
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
