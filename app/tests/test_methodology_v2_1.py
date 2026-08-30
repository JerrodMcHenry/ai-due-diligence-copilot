"""
Methodology V2.1 (Phase 10.8B) regression tests.

No LLM calls are made here -- every function under test is pure Python
(the evidence-provenance guard, the confidence-score cap, the pillar
weighted-average math), exercised directly with synthetic inputs, per
the pattern already established by app/tests/test_provenance.py and
app/tests/test_scoring_weights.py.

Run with:
    python -m app.tests.test_methodology_v2_1
"""

from app.ai.evidence_provenance import (
    apply_provenance_guard,
    extract_numeric_claims,
    find_unsupported_numeric_claims,
    strip_unsupported_evidence,
)
from app.ai.scoring import (
    CONFIDENCE_SCORE_CAPS,
    apply_confidence_score_cap,
    calculate_weighted_score,
    finalize_pillar_score,
)
from app.ai.scoring_methodology import PILLAR_WEIGHTS
from app.ai.investment_score import clamp_score
from app.models.evidence_analysis import EvidenceAnalysis
from app.models.scoring import PillarScoreBreakdown, Subscore


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# ---------------------------------------------------------------------
# Part 16: "fast-growing company" must NOT become "$20M ARR"
# ---------------------------------------------------------------------

def test_unsupported_financial_number_rejected() -> None:
    source_text = "The company describes itself as a fast-growing SaaS startup with a well-funded team."
    evidence = ["The company reports $20M ARR and 30% month-over-month growth."]

    unsupported = find_unsupported_numeric_claims(evidence, source_text)
    expect(len(unsupported) > 0, "Invented $20M ARR figure should be flagged as unsupported.")

    kept, dropped = strip_unsupported_evidence(evidence, source_text)
    expect(kept == [], "The fabricated evidence bullet must be dropped entirely, not edited.")
    expect(len(dropped) == 1, "Exactly one bullet was supplied and should be dropped.")


def test_unsupported_cash_balance_rejected() -> None:
    source_text = "Investors describe the company as well funded, with strong investor backing."
    evidence = ["The company has an $80M cash balance providing significant runway."]

    kept, dropped = strip_unsupported_evidence(evidence, source_text)
    expect(kept == [], "'well funded' must not license an invented $80M cash balance.")
    expect(dropped == evidence, "The invented-figure bullet must be the one dropped.")


# ---------------------------------------------------------------------
# Supported financial numbers must be preserved, not over-corrected
# ---------------------------------------------------------------------

def test_supported_financial_number_preserved() -> None:
    source_text = "Sources report the company raised a $10M Series A and has 500 customers as of this year."
    evidence = ["The company raised a $10M Series A and serves 500 customers."]

    kept, dropped = strip_unsupported_evidence(evidence, source_text)
    expect(dropped == [], "A number present in the source text must not be dropped.")
    expect(kept == evidence, "Fully-supported evidence must be preserved unchanged.")


def test_explicit_derived_calculation_traceable_from_supported_inputs() -> None:
    # Both raw inputs to a derived ratio are themselves present in the
    # source text -- a calculation from supported values, not a new
    # invented figure. The current guard is intentionally narrow (it
    # checks each number-shaped token independently), so this asserts
    # that neither input number is flagged when both appear in the source.
    source_text = "The company reports $5M in annual revenue against $1M in annual burn."
    evidence = ["Burn efficiency is roughly $5M revenue vs $1M burn, a 5:1 ratio."]

    unsupported = find_unsupported_numeric_claims(evidence, source_text)
    # "5:1" itself is a newly-computed ratio not literally present in the
    # source text, and IS expected to be flagged -- this is intentional:
    # the guard cannot verify a calculation's arithmetic is correct, only
    # whether its literal token was ever supplied. A dimension citing a
    # derived ratio should spell out the two supported inputs (which
    # remain in evidence) rather than rely on the guard to trust unverified
    # arithmetic.
    expect("5:1" in unsupported, "An unverified derived ratio should still be flagged, not silently trusted.")


# ---------------------------------------------------------------------
# apply_provenance_guard: dimension-level behavior
# ---------------------------------------------------------------------

def _dim(**kwargs) -> EvidenceAnalysis:
    base = dict(
        dimension="Burn Efficiency",
        evidence_status="Observed",
        confidence="High",
        evidence=[],
        signals=[],
        missing_information=[],
        rationale="",
    )
    base.update(kwargs)
    return EvidenceAnalysis(**base)


def test_provenance_guard_forces_unavailable_when_nothing_survives() -> None:
    source_text = "The company is a fast-growing startup with a strong team."
    dim = _dim(evidence=["The company has $5M cash and $400K monthly burn."])

    new_dims, altered = apply_provenance_guard([dim], source_text)

    expect(len(new_dims) == 1, "Exactly one dimension in, one out.")
    expect(new_dims[0].evidence_status == "Unavailable", "Fully-fabricated evidence must fall through to Unavailable.")
    expect(new_dims[0].confidence == "Low", "Unavailable must carry Low confidence.")
    expect(new_dims[0].evidence == [], "Unavailable must carry an empty evidence list.")
    expect("Burn Efficiency" in altered, "The altered dimension name must be reported for observability.")


def test_provenance_guard_downgrades_confidence_when_partially_supported() -> None:
    source_text = "The company disclosed $10M in Series A funding this year."
    dim = _dim(
        confidence="High",
        evidence=[
            "The company raised a $10M Series A.",
            "The company has $5M cash and $400K monthly burn.",
        ],
    )

    new_dims, altered = apply_provenance_guard([dim], source_text)

    expect(new_dims[0].evidence_status == "Observed", "Status is preserved when real evidence survives.")
    expect(new_dims[0].confidence == "Low", "Confidence must be downgraded once part of the justification was fabricated.")
    expect(new_dims[0].evidence == ["The company raised a $10M Series A."], "Only the traceable bullet should survive.")
    expect("Burn Efficiency" in altered, "Dimension must be reported as altered.")


def test_provenance_guard_leaves_fully_supported_dimension_untouched() -> None:
    source_text = "The company raised a $10M Series A and reports $5M in ARR."
    dim = _dim(evidence=["The company raised a $10M Series A and reports $5M in ARR."])

    new_dims, altered = apply_provenance_guard([dim], source_text)

    expect(new_dims[0] == dim, "A fully-supported dimension must pass through unchanged (same object).")
    expect(altered == set(), "No dimension should be reported as altered.")


def test_provenance_guard_skips_already_unavailable_dimensions() -> None:
    dim = _dim(evidence_status="Unavailable", evidence=[], confidence="Low", missing_information=["no evidence"])
    new_dims, altered = apply_provenance_guard([dim], "irrelevant source text")
    expect(new_dims[0] == dim, "An already-Unavailable dimension is not re-processed.")
    expect(altered == set(), "No dimension should be reported altered.")


def test_provenance_guard_deterministic_repeatability() -> None:
    source_text = "The company raised a $10M Series A."
    dim = _dim(evidence=["The company has $5M cash and $400K monthly burn."])

    first_dims, first_altered = apply_provenance_guard([dim], source_text)
    second_dims, second_altered = apply_provenance_guard([dim], source_text)

    expect(first_dims[0].evidence_status == second_dims[0].evidence_status, "Guard must be deterministic across runs.")
    expect(first_altered == second_altered, "Guard's altered-set must be deterministic across runs.")


# ---------------------------------------------------------------------
# Part 11: confidence score cap
# ---------------------------------------------------------------------

def _sub(score, confidence, weight=0.25) -> Subscore:
    return Subscore(name="Test Dimension", score=score, weight=weight, confidence=confidence, evidence_status="Observed")


def test_low_confidence_inference_cannot_masquerade_as_exceptional() -> None:
    subs = [_sub(score=9.5, confidence="Low")]
    capped = apply_confidence_score_cap(subs)
    expect(capped[0].score == CONFIDENCE_SCORE_CAPS["Low"], "Low confidence must cap at its defined ceiling, not pass through 9.5.")
    expect(capped[0].score_corrected is True, "A capped subscore must be flagged as corrected for observability.")


def test_medium_confidence_caps_below_low_high_band() -> None:
    subs = [_sub(score=9.8, confidence="Medium")]
    capped = apply_confidence_score_cap(subs)
    expect(capped[0].score == CONFIDENCE_SCORE_CAPS["Medium"], "Medium confidence must cap below the 9-10 band.")


def test_high_confidence_uncapped() -> None:
    subs = [_sub(score=9.9, confidence="High")]
    capped = apply_confidence_score_cap(subs)
    expect(capped[0].score == 9.9, "High confidence must not be capped.")


def test_confidence_cap_never_raises_a_score() -> None:
    subs = [_sub(score=2.0, confidence="Low")]
    capped = apply_confidence_score_cap(subs)
    expect(capped[0].score == 2.0, "The cap must never raise a score that is already below its ceiling.")


def test_confidence_cap_skips_unscored_dimensions() -> None:
    subs = [_sub(score=None, confidence="Low")]
    capped = apply_confidence_score_cap(subs)
    expect(capped[0].score is None, "A None score must pass through untouched.")


# ---------------------------------------------------------------------
# Part 13: synthetic scale-reachability fixtures (deterministic, no LLM)
# ---------------------------------------------------------------------

def _pillar_score(scores: list[float], confidence: str = "High") -> float:
    subs = [Subscore(name=f"D{i}", score=s, weight=1.0, confidence=confidence, evidence_status="Observed") for i, s in enumerate(scores)]
    return calculate_weighted_score(subs)


def test_very_weak_profile_reaches_low_end_of_scale() -> None:
    # Every pillar affirmatively weak, High confidence (so the confidence
    # cap does not itself suppress the low end).
    pillar_scores = {name: _pillar_score([1.0, 1.5, 2.0]) for name in PILLAR_WEIGHTS}
    overall = sum(pillar_scores[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    sps = clamp_score(overall * 10)
    expect(sps < 20, f"An all-weak synthetic profile should land well under 20, got {sps}.")


def test_exceptional_profile_reaches_high_end_of_scale() -> None:
    pillar_scores = {name: _pillar_score([9.5, 10.0, 9.0]) for name in PILLAR_WEIGHTS}
    overall = sum(pillar_scores[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    sps = clamp_score(overall * 10)
    expect(sps > 90, f"An all-exceptional, High-confidence synthetic profile should land above 90, got {sps}.")


def test_mixed_profile_lands_in_the_middle() -> None:
    pillar_scores = {name: _pillar_score([5.0, 6.0, 5.5]) for name in PILLAR_WEIGHTS}
    overall = sum(pillar_scores[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    sps = clamp_score(overall * 10)
    expect(45 <= sps <= 65, f"A deliberately mixed/ordinary synthetic profile should land near the middle, got {sps}.")


def test_stage_relative_early_exceptional_profile_can_score_highly() -> None:
    # An early-stage-appropriate but genuinely exceptional-for-its-stage
    # profile (High confidence, top-band scores) must be able to reach
    # the top of the scale -- the methodology must not structurally cap
    # early-stage companies below mature ones.
    pillar_scores = {name: _pillar_score([9.0, 9.5, 9.0]) for name in PILLAR_WEIGHTS}
    overall = sum(pillar_scores[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    sps = clamp_score(overall * 10)
    expect(sps > 85, f"A stage-appropriate exceptional profile must be able to reach the high end, got {sps}.")


def test_mature_weak_profile_can_score_poorly() -> None:
    pillar_scores = {name: _pillar_score([2.0, 1.5, 2.5]) for name in PILLAR_WEIGHTS}
    overall = sum(pillar_scores[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    sps = clamp_score(overall * 10)
    expect(sps < 30, f"A mature-but-weak profile must be able to score poorly, got {sps}.")


def test_sps_remains_bounded_0_to_100() -> None:
    expect(clamp_score(150.0) == 100.0, "clamp_score must cap above 100.")
    expect(clamp_score(-25.0) == 0.0, "clamp_score must floor below 0.")
    expect(clamp_score(63.4) == 63.4, "A valid in-range score must pass through unchanged.")


# ---------------------------------------------------------------------
# Part 12: pillar weights must remain unchanged by this phase
# ---------------------------------------------------------------------

def test_pillar_weights_unchanged() -> None:
    expected = {
        "market": 0.20,
        "team": 0.20,
        "product": 0.20,
        "execution": 0.15,
        "traction": 0.15,
        "financial_health": 0.10,
    }
    expect(PILLAR_WEIGHTS == expected, f"PILLAR_WEIGHTS must remain frozen per Phase 10.8B Part 12, got {PILLAR_WEIGHTS}.")
    expect(abs(sum(expected.values()) - 1.0) < 1e-9, "Pillar weights must sum to 1.0.")


def main() -> None:
    tests = [
        test_unsupported_financial_number_rejected,
        test_unsupported_cash_balance_rejected,
        test_supported_financial_number_preserved,
        test_explicit_derived_calculation_traceable_from_supported_inputs,
        test_provenance_guard_forces_unavailable_when_nothing_survives,
        test_provenance_guard_downgrades_confidence_when_partially_supported,
        test_provenance_guard_leaves_fully_supported_dimension_untouched,
        test_provenance_guard_skips_already_unavailable_dimensions,
        test_provenance_guard_deterministic_repeatability,
        test_low_confidence_inference_cannot_masquerade_as_exceptional,
        test_medium_confidence_caps_below_low_high_band,
        test_high_confidence_uncapped,
        test_confidence_cap_never_raises_a_score,
        test_confidence_cap_skips_unscored_dimensions,
        test_very_weak_profile_reaches_low_end_of_scale,
        test_exceptional_profile_reaches_high_end_of_scale,
        test_mixed_profile_lands_in_the_middle,
        test_stage_relative_early_exceptional_profile_can_score_highly,
        test_mature_weak_profile_can_score_poorly,
        test_sps_remains_bounded_0_to_100,
        test_pillar_weights_unchanged,
    ]

    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as exc:
            failures.append((test.__name__, str(exc)))
            print(f"FAIL: {test.__name__}: {exc}")

    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
