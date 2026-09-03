"""
Phase 29A -- VPS Determinism, Reproducibility & Calibration Fix.

A real, live-reproduced P0 defect: the same founder description ("I want
to start a hair loss company for men and women with our special serum"),
submitted through the real AI structuring pipeline 20 times with zero
changes, produced VPS 6.5 fifteen times and 8.0 five times. Traced to its
exact mechanism (see app/ai/vps_scoring.py::compute_vps()'s own updated
docstring for the full root-cause narrative) and fixed there.

This file protects, permanently, against a recurrence of the EXACT
mechanism found -- a single, uncorroborated modeled-assumption category
(no real validation evidence anywhere in the model) single-handedly
setting VPS -- not a brittle snapshot of today's scores. The 20 real
draft assumption-dicts captured during this phase's own live
reproduction are embedded below as a permanent fixture (Section "REAL
REPRODUCTION FIXTURE") so this exact defect can never silently return
even if compute_vps() is refactored later.

Run with:
    python -m app.tests.test_vps_determinism_and_calibration
"""

import copy
import json

from app.ai.vps_scoring import compute_vps


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


BASE_HAIR_LOSS_ASSUMPTIONS = {
    "target_customer": "Men and women experiencing hair loss",
    "market": {"market_description": None, "estimated_market_size": None, "competition_intensity": None},
    "problem_solution": {
        "problem_statement": "Hair loss in men and women",
        "solution_description": "Special serum for hair loss",
        "differentiation": "Use of a special serum",
    },
    "founder": {"founder_count": None, "relevant_domain_experience_years": None, "has_technical_cofounder": None, "has_business_cofounder": None},
    "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
    "economics": {"pricing_model": None, "price_point": None, "expected_gross_margin_pct": None},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": None, "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None},
    "capital": {"starting_capital": None, "monthly_burn": None},
}


def _merge(base: dict, overrides: dict) -> dict:
    m = copy.deepcopy(base)
    for k, v in overrides.items():
        m[k].update(v)
    return m


# --- 1. Identical canonical model -> identical VPS, byte-for-byte ---------


def test_identical_model_produces_byte_identical_result_x100() -> None:
    serialized = [json.dumps(compute_vps(BASE_HAIR_LOSS_ASSUMPTIONS), sort_keys=True) for _ in range(100)]
    expect(len(set(serialized)) == 1, f"100 identical calls must produce exactly 1 unique result, got {len(set(serialized))}")


# --- 2. The exact reported bug: two semantically-identical differentiation
#        phrasings must no longer produce different VPS ---------------------


def test_trivial_differentiation_paraphrase_no_longer_swings_vps() -> None:
    """The exact mechanism found live: 'Special serum' (14 chars, under
    the old bonus threshold) vs. 'Use of a special serum' (23 chars,
    over it) -- the SAME underlying fact, paraphrased -- used to swing
    VPS from 6.5 to 8.0 because problem_solution was the only scored
    category. Both must now produce the identical, neutral-anchored VPS."""
    short = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {"problem_solution": {"differentiation": "Special serum"}})
    long = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {"problem_solution": {"differentiation": "Use of a special serum"}})

    vps_short = compute_vps(short)["vps"]
    vps_long = compute_vps(long)["vps"]

    expect(vps_short == vps_long, f"A trivial paraphrase of the same fact must never change VPS, got {vps_short} vs {vps_long}")
    expect(vps_short == 5.0, f"A single uncorroborated modeled-assumption category (no validation) must report the neutral anchor, got {vps_short}")


# --- 3. Real reproduction fixture: the 20 actual draft assumption-dicts ----
#        captured live during this phase's own 20-run audit -----------------

# Only the fields that varied across the 20 real runs are worth encoding
# distinctly; every other field was uniformly Unknown across all 20 (see
# docs/methodology/VPS_DETERMINISM_AND_CALIBRATION_AUDIT.md's own field-
# variability table). Reconstructing the 3 distinct canonical models the
# real audit actually observed:
_REAL_RUN_VARIANT_1 = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "problem_solution": {"problem_statement": "Hair loss in men and women", "solution_description": "Special serum for hair loss", "differentiation": "Special serum"},
})
_REAL_RUN_VARIANT_2 = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "problem_solution": {"problem_statement": "Hair loss in men and women", "solution_description": "Special serum for hair loss", "differentiation": "Use of a special serum"},
})
_REAL_RUN_VARIANT_3 = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "problem_solution": {"problem_statement": "Hair loss affects men and women", "solution_description": "Special serum to treat hair loss", "differentiation": "Use of a special serum"},
})


def test_all_three_real_reproduction_variants_produce_identical_vps() -> None:
    values = {compute_vps(v)["vps"] for v in (_REAL_RUN_VARIANT_1, _REAL_RUN_VARIANT_2, _REAL_RUN_VARIANT_3)}
    expect(values == {5.0}, f"All 3 real canonical-model variants observed live must now produce the identical VPS, got {values}")


# --- 4. The narrow fix must not dampen a SOLE category that IS validation --


def test_sole_validation_category_is_not_dampened() -> None:
    """Real evidence (paying customers, revenue) must never be treated as
    an 'uncorroborated guess' just because it's the only thing known --
    Invariant E: real evidence and modeled assumptions stay distinct."""
    only_validation = copy.deepcopy(BASE_HAIR_LOSS_ASSUMPTIONS)
    only_validation["problem_solution"] = {"problem_statement": None, "solution_description": None, "differentiation": None}
    only_validation["validation"] = {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 50, "monthly_revenue": 80000, "prior_monthly_revenue": None, "retention_pct": None}

    result = compute_vps(only_validation)
    validation_score = next(c["score"] for c in result["categories"] if c["key"] == "validation")
    expect(result["vps"] == validation_score, f"A sole VALIDATION category (real evidence) must be reported at its own real score ({validation_score}), not dampened to neutral, got VPS={result['vps']}")
    expect(result["vps"] > 5.0, f"50 real paying customers + $80K/mo revenue, even alone, must score above neutral, got {result['vps']}")


def test_two_scored_categories_are_not_dampened() -> None:
    """The fix is deliberately narrow -- the MOMENT a second independent
    category is scored (even a second modeled assumption, not just real
    validation evidence), normal renormalization resumes exactly as
    before this phase."""
    two_categories = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
        "market": {"estimated_market_size": "Large", "competition_intensity": "Medium"},
    })
    result = compute_vps(two_categories)
    ps_score = next(c["score"] for c in result["categories"] if c["key"] == "problem_solution")
    market_score = next(c["score"] for c in result["categories"] if c["key"] == "market_potential")
    expected = round((ps_score * 0.20 + market_score * 0.20) / 0.40, 1)
    expect(result["vps"] == expected, f"Two scored categories must use ordinary renormalization unchanged, expected {expected}, got {result['vps']}")


# --- 5. Calibration ladder (Part 8's own fixtures, this exact venture) -----

_LADDER_A = BASE_HAIR_LOSS_ASSUMPTIONS
_LADDER_B = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {"validation": {"customer_interviews": 20}})
_LADDER_C = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "validation": {"customer_interviews": 20, "paying_customers": 5},
    "economics": {"price_point": 29, "pricing_model": "Subscription"},
})
_LADDER_D = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "validation": {"customer_interviews": 20, "paying_customers": 15, "monthly_revenue": 3000, "retention_pct": 90},
    "economics": {"price_point": 29, "pricing_model": "Subscription"},
    "gtm": {"primary_acquisition_strategy": "Paid social ads", "expected_cac": 40},
})
_LADDER_E = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {
    "validation": {"customer_interviews": 40, "paying_customers": 120, "monthly_revenue": 60000, "prior_monthly_revenue": 20000, "retention_pct": 108},
    "economics": {"price_point": 39, "pricing_model": "Subscription", "expected_gross_margin_pct": 75},
    "gtm": {"primary_acquisition_strategy": "Paid social + affiliate", "expected_cac": 45},
})


def test_calibration_ladder_is_strictly_monotonic() -> None:
    values = [compute_vps(fx)["vps"] for fx in (_LADDER_A, _LADDER_B, _LADDER_C, _LADDER_D, _LADDER_E)]
    labels = ["A (idea only)", "B (customer discovery)", "C (early validation)", "D (early traction)", "E (stronger operating)"]
    for i in range(len(values) - 1):
        expect(
            values[i] < values[i + 1],
            f"Calibration ladder violated: {labels[i]}={values[i]} must be < {labels[i + 1]}={values[i + 1]}",
        )


def test_customer_discovery_no_longer_scores_below_idea_only() -> None:
    """The exact inversion this phase found and fixed: real customer-
    discovery evidence (20 interviews) must never score LOWER than the
    same idea with zero evidence at all."""
    idea_only = compute_vps(_LADDER_A)["vps"]
    with_discovery = compute_vps(_LADDER_B)["vps"]
    expect(with_discovery > idea_only, f"Real evidence must never lower VPS relative to no evidence at all: idea-only={idea_only}, with-discovery={with_discovery}")


# --- 6. Scoring purity, reconfirmed (Part 4/11) -----------------------------


def test_rich_multi_category_model_still_perfectly_deterministic() -> None:
    rich = {
        "target_customer": "commercial buildings",
        "market": {"market_description": "big", "estimated_market_size": "Very Large", "competition_intensity": "High"},
        "problem_solution": {"problem_statement": "x", "solution_description": "y", "differentiation": "z" * 30},
        "founder": {"founder_count": 2, "relevant_domain_experience_years": 8, "has_technical_cofounder": True, "has_business_cofounder": True},
        "gtm": {"primary_acquisition_strategy": "Direct sales", "expected_cac": 21000},
        "economics": {"pricing_model": "Subscription", "price_point": 299, "expected_gross_margin_pct": 84},
        "validation": {"customer_interviews": 16, "waitlist_signups": None, "paying_customers": 187, "monthly_revenue": 983333, "prior_monthly_revenue": 258333, "retention_pct": 128},
        "capital": {"starting_capital": None, "monthly_burn": 310000},
    }
    results = [json.dumps(compute_vps(rich), sort_keys=True) for _ in range(100)]
    expect(len(set(results)) == 1, "A rich, fully-populated model must also be perfectly deterministic across 100 executions")


# --- 7. The transparency flag (Part 13): exposed exactly when, and only
#        when, the dampening branch fires -- so the review screen can
#        explain the gap between the shown category score and the VPS
#        without re-deriving this rule itself. ------------------------------


def test_sole_uncorroborated_category_flag_true_exactly_when_dampened() -> None:
    result = compute_vps(BASE_HAIR_LOSS_ASSUMPTIONS)
    expect(result["sole_uncorroborated_category"] is True, "Flag must be True for the exact reported bug's fixture (one modeled category, no validation)")
    expect(result["vps"] == 5.0, "Sanity: this fixture must still dampen to the neutral anchor")


def test_sole_uncorroborated_category_flag_false_when_validation_alone_scored() -> None:
    only_validation = copy.deepcopy(BASE_HAIR_LOSS_ASSUMPTIONS)
    only_validation["problem_solution"] = {"problem_statement": None, "solution_description": None, "differentiation": None}
    only_validation["validation"] = {"customer_interviews": None, "waitlist_signups": None, "paying_customers": 50, "monthly_revenue": 80000, "prior_monthly_revenue": None, "retention_pct": None}
    result = compute_vps(only_validation)
    expect(result["sole_uncorroborated_category"] is False, "A sole VALIDATION category is real evidence, not an uncorroborated guess -- flag must be False")


def test_sole_uncorroborated_category_flag_false_when_two_categories_scored() -> None:
    two_categories = _merge(BASE_HAIR_LOSS_ASSUMPTIONS, {"market": {"estimated_market_size": "Large", "competition_intensity": "Medium"}})
    result = compute_vps(two_categories)
    expect(result["sole_uncorroborated_category"] is False, "Flag must be False once a second category is scored, matching normal renormalization resuming")


def test_sole_uncorroborated_category_flag_false_when_nothing_scored() -> None:
    empty = copy.deepcopy(BASE_HAIR_LOSS_ASSUMPTIONS)
    empty["problem_solution"] = {"problem_statement": None, "solution_description": None, "differentiation": None}
    result = compute_vps(empty)
    expect(result["vps"] is None, "Sanity: a fully-empty model must report vps=None, not a fabricated score")
    expect(result["sole_uncorroborated_category"] is False, "Flag must be False when VPS itself is None (no category at all, not 'one uncorroborated one')")


# --- 8. VPSResult pydantic contract (Part 16): the new field must be
#        serializable with a safe default, never breaking an existing
#        caller that doesn't know about it yet. ------------------------------


def test_vps_result_model_accepts_new_field_with_safe_default() -> None:
    from app.models.idea_lab import VPSResult

    # A caller/fixture built before Phase 29A (no sole_uncorroborated_category
    # key at all) must still validate -- the field defaults to False, never
    # required, so older persisted model_result JSON keeps loading.
    legacy_shaped = {"vps": 5.0, "label": "MODELED / ASSUMPTION-BASED", "categories": []}
    parsed = VPSResult.model_validate(legacy_shaped)
    expect(parsed.sole_uncorroborated_category is False, "Missing field on legacy data must default to False, not raise or fabricate True")

    result = compute_vps(BASE_HAIR_LOSS_ASSUMPTIONS)
    from app.ai.vps_guidance import generate_guidance
    guidance = generate_guidance(BASE_HAIR_LOSS_ASSUMPTIONS, result)
    full = VPSResult.model_validate({**result, **guidance})
    expect(full.sole_uncorroborated_category is True, "A real compute_vps()+generate_guidance() merge must round-trip the flag through the Pydantic contract unchanged")


TESTS = [
    test_identical_model_produces_byte_identical_result_x100,
    test_trivial_differentiation_paraphrase_no_longer_swings_vps,
    test_all_three_real_reproduction_variants_produce_identical_vps,
    test_sole_validation_category_is_not_dampened,
    test_two_scored_categories_are_not_dampened,
    test_calibration_ladder_is_strictly_monotonic,
    test_customer_discovery_no_longer_scores_below_idea_only,
    test_rich_multi_category_model_still_perfectly_deterministic,
    test_sole_uncorroborated_category_flag_true_exactly_when_dampened,
    test_sole_uncorroborated_category_flag_false_when_validation_alone_scored,
    test_sole_uncorroborated_category_flag_false_when_two_categories_scored,
    test_sole_uncorroborated_category_flag_false_when_nothing_scored,
    test_vps_result_model_accepts_new_field_with_safe_default,
]


def main() -> None:
    print("\nVPS Determinism, Reproducibility & Calibration Fix (Phase 29A) -- regression tests")
    print("-" * 72)

    failures: list[str] = []
    for test in TESTS:
        name = test.__name__
        try:
            test()
            print(f"PASS  {name}")
        except Exception as error:  # noqa: BLE001
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
