"""
Tests for SIE Methodology v2 missing-evidence semantics
(app/ai/sie_v2_evidence_semantics.py): the nine-state classification,
Partial Structural Coverage, and Evidence Independence Metadata.

Run with:
    python -m app.tests.test_sie_v2_evidence_semantics
"""

from app.ai.sie_v2_evidence_semantics import (
    MissingEvidenceState,
    EXCLUDED_FROM_SCORED_SET,
    NEVER_IN_SCOPE,
    classify_unavailable_dimension,
    compute_partial_structural_coverage,
    compute_evidence_independence_metadata,
    EIMDimension,
)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_all_nine_states_defined() -> None:
    expect(len(list(MissingEvidenceState)) == 10, f"Expected 10 enum values (9 canonical + resolved-conflicting split), got {len(list(MissingEvidenceState))}")


def test_usually_private_and_expected_unavailable_identically_excluded() -> None:
    """Part 4's load-bearing rule: these two states are arithmetically
    identical -- both excluded from the scored set -- differing ONLY in
    diligence-flag severity."""
    expect(
        MissingEvidenceState.USUALLY_PRIVATE_AND_UNAVAILABLE in EXCLUDED_FROM_SCORED_SET,
        "Usually-Private-And-Unavailable must be excluded from the scored set",
    )
    expect(
        MissingEvidenceState.EXPECTED_BUT_UNAVAILABLE in EXCLUDED_FROM_SCORED_SET,
        "Expected-But-Unavailable must be excluded from the scored set",
    )


def test_not_expected_and_not_applicable_never_in_scope() -> None:
    expect(MissingEvidenceState.NOT_EXPECTED_BY_STAGE in NEVER_IN_SCOPE, "Not Expected By Stage must never enter the in-scope set")
    expect(MissingEvidenceState.NOT_APPLICABLE in NEVER_IN_SCOPE, "Not Applicable must never enter the in-scope set")


def test_missing_evidence_never_becomes_weak() -> None:
    """The absolute governing rule: none of the Unavailable sub-states carry
    an implied score. This is a structural property of the enum design (no
    numeric field exists on MissingEvidenceState), verified here by
    confirming excluded states never masquerade as a below-average default
    anywhere calling code might check."""
    for state in EXCLUDED_FROM_SCORED_SET:
        expect(not hasattr(state, "score"), f"{state} must not carry a score attribute")


def test_classify_private_dimension_unavailable() -> None:
    state = classify_unavailable_dimension("Private", stage_not_expected=False, stage_not_applicable=False, stage_optional=False)
    expect(state == MissingEvidenceState.USUALLY_PRIVATE_AND_UNAVAILABLE, f"Expected Usually-Private, got {state}")


def test_classify_public_dimension_genuinely_missing_is_expected_but_unavailable() -> None:
    state = classify_unavailable_dimension("Public", stage_not_expected=False, stage_not_applicable=False, stage_optional=False)
    expect(
        state == MissingEvidenceState.EXPECTED_BUT_UNAVAILABLE,
        f"An in-scope Public dimension with no evidence should be the ELEVATED Expected-But-Unavailable state, got {state}",
    )


def test_classify_stage_gates_take_priority() -> None:
    state = classify_unavailable_dimension("Public", stage_not_expected=True, stage_not_applicable=False, stage_optional=False)
    expect(state == MissingEvidenceState.NOT_EXPECTED_BY_STAGE, "Stage-not-expected must take priority over evidence-requirement classification")


# --- Partial Structural Coverage ---

def test_psc_not_triggered_when_all_pillars_scored() -> None:
    result = compute_partial_structural_coverage({"market": 6.0, "team": 5.5, "product": 7.0, "execution": 6.0, "traction": 5.0, "financial_health": 4.0})
    expect(result["partial_structural_coverage"] is False, "PSC must not trigger when every pillar has a real score")


def test_psc_triggered_by_one_unavailable_pillar() -> None:
    result = compute_partial_structural_coverage({"market": 6.0, "team": None, "product": 7.0})
    expect(result["partial_structural_coverage"] is True, "PSC must trigger when a pillar is entirely unavailable")
    expect(result["pillars_unavailable_entirely"] == ["team"], f"Unexpected pillar list: {result['pillars_unavailable_entirely']}")


def test_psc_is_display_only_never_touches_score() -> None:
    result = compute_partial_structural_coverage({"market": 6.0, "team": None})
    expect("score" not in result and "sps" not in result, "PSC computation must never produce or reference a score/SPS field")


# --- Evidence Independence Metadata ---

def test_eim_no_shared_events_full_independence() -> None:
    dims = [EIMDimension("A", 0.3, "evt1"), EIMDimension("B", 0.3, "evt2"), EIMDimension("C", 0.4, None)]
    result = compute_evidence_independence_metadata(dims)
    expect(result["effective_independent_dimensions"] == 3, f"3 distinct events should give 3 effective independent dims, got {result['effective_independent_dimensions']}")
    expect(result["possible_semantic_duplication"] is False, "No shared events -- must not flag duplication")


def test_eim_zenefits_style_concentration_detected() -> None:
    """Regression case: PASS C found Zenefits' entire Product pillar (3
    dimensions) derived from one sentence."""
    dims = [EIMDimension("Customer Value", 0.25, "evt_free_fast"), EIMDimension("Differentiation", 0.20, "evt_free_fast"), EIMDimension("Usability", 0.15, "evt_free_fast")]
    result = compute_evidence_independence_metadata(dims)
    expect(result["effective_independent_dimensions"] == 1, f"3 dims sharing one event should give 1 effective independent dim, got {result['effective_independent_dimensions']}")
    expect(result["possible_semantic_duplication"] is True, "3 dimensions sharing one event must flag possible semantic duplication")
    expect(result["concentration_ratio"] > 0.5, f"Concentration ratio should be high, got {result['concentration_ratio']}")


def test_eim_never_modifies_score() -> None:
    dims = [EIMDimension("A", 0.5, "evt1"), EIMDimension("B", 0.5, "evt1")]
    result = compute_evidence_independence_metadata(dims)
    expect("score" not in result, "EIM must never produce a score field -- Phase 11 explicitly forbids modifying SPS")


TESTS = [
    test_all_nine_states_defined,
    test_usually_private_and_expected_unavailable_identically_excluded,
    test_not_expected_and_not_applicable_never_in_scope,
    test_missing_evidence_never_becomes_weak,
    test_classify_private_dimension_unavailable,
    test_classify_public_dimension_genuinely_missing_is_expected_but_unavailable,
    test_classify_stage_gates_take_priority,
    test_psc_not_triggered_when_all_pillars_scored,
    test_psc_triggered_by_one_unavailable_pillar,
    test_psc_is_display_only_never_touches_score,
    test_eim_no_shared_events_full_independence,
    test_eim_zenefits_style_concentration_detected,
    test_eim_never_modifies_score,
]


def main() -> None:
    print("\nSIE Methodology v2 -- evidence semantics tests")
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
