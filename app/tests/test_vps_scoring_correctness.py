"""
Phase 29B -- Founder UX & Methodology Acceptance Audit.

Four real, live-reproduced correctness bugs found in app/ai/vps_scoring.py
by adversarial and repeated-input testing through the actual founder
creation flow (TestClient against the real /ventures* endpoints), fixed
in the same session. Each test here protects one distinct defect found
live, not a snapshot of today's scores.

1. `market_description` (free text, contributes zero points to
   market_potential's own score) used to be enough, by itself, to flip
   that category from Unavailable to "scored at exactly the neutral
   base" -- confirmed as the exact cause of a live nondeterminism: the
   same "structured early startup" fixture, run 5 times through the real
   AI structuring pipeline with identical founder-stated facts, produced
   VPS 4.4 four times and 4.6 once, purely because the LLM inconsistently
   decided whether to paraphrase a sentence into this non-scoring field.
2. `price_point` (never itself used inside _score_economic_potential's
   own score math) had the identical defect: alone, it silently scored
   economic_potential at exactly 5.0 with an EMPTY basis list.
3. `expected_cac: 0` (the best possible acquisition cost) was scored as
   if CAC exceeded price point -- a genuine inversion, confirmed live:
   cac=0/price=49 scored 3.0 (penalized), *worse* than cac=10/price=49's
   7.0.
4. `price_point: 0` (an explicitly-stated free product) was treated as
   though no price point had been stated at all, via a truthy check
   instead of an `is not None` check.
5. A founder who explicitly reports ONLY retention (e.g. "65% retention",
   no interviews/waitlist/paying-customers/revenue) had that real,
   explicitly-stated fact silently discarded -- the validation category
   returned Unavailable, identical to reporting nothing at all.

Run with:
    python -m app.tests.test_vps_scoring_correctness
"""

import copy

from app.ai.vps_scoring import compute_vps


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


EMPTY_ASSUMPTIONS = {
    "target_customer": None,
    "market": {"market_description": None, "estimated_market_size": None, "competition_intensity": None},
    "problem_solution": {"problem_statement": None, "solution_description": None, "differentiation": None},
    "founder": {"founder_count": None, "relevant_domain_experience_years": None, "has_technical_cofounder": None, "has_business_cofounder": None},
    "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
    "economics": {"pricing_model": None, "price_point": None, "expected_gross_margin_pct": None},
    "validation": {"customer_interviews": None, "waitlist_signups": None, "paying_customers": None, "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None},
    "capital": {"starting_capital": None, "monthly_burn": None},
}


def _cat(result: dict, key: str) -> dict:
    return next(c for c in result["categories"] if c["key"] == key)


# --- 1. market_description alone must not score market_potential -----------


def test_market_description_alone_does_not_score_market_potential() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["market"]["market_description"] = "A large and growing market for hair restoration products"
    result = _cat(compute_vps(a), "market_potential")
    expect(result["score"] is None, f"A free-text description with no size/competition data must leave market_potential Unavailable, got {result}")


def test_market_description_with_size_still_scores_normally() -> None:
    """The fix must not accidentally break the case where description is
    present ALONGSIDE a real scoring field."""
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["market"]["market_description"] = "A large and growing market"
    a["market"]["estimated_market_size"] = "Large"
    result = _cat(compute_vps(a), "market_potential")
    expect(result["score"] == 6.5, f"size=Large alone must still score exactly as before (5.0 + 1.5), got {result['score']}")


def test_the_exact_live_reproduced_nondeterminism_is_fixed() -> None:
    """The two real canonical models captured live for the Part 3
    'structured early startup' fixture (identical founder-stated facts;
    one run's LLM call additionally wrote a market_description sentence,
    the other four did not) must now produce identical VPS."""
    without_description = {
        "target_customer": "men and women aged 25-45",
        "market": {"market_description": None, "estimated_market_size": None, "competition_intensity": None},
        "problem_solution": {"problem_statement": None, "solution_description": "A hair loss serum", "differentiation": None},
        "founder": {"founder_count": None, "relevant_domain_experience_years": None, "has_technical_cofounder": None, "has_business_cofounder": None},
        "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
        "economics": {"pricing_model": "Subscription", "price_point": 49, "expected_gross_margin_pct": None},
        "validation": {"customer_interviews": 15, "waitlist_signups": None, "paying_customers": 8, "monthly_revenue": None, "prior_monthly_revenue": None, "retention_pct": None},
        "capital": {"starting_capital": None, "monthly_burn": None},
    }
    with_description = copy.deepcopy(without_description)
    with_description["market"]["market_description"] = "The hair loss treatment market targeting adults aged 25-45"

    vps_without = compute_vps(without_description)["vps"]
    vps_with = compute_vps(with_description)["vps"]
    expect(vps_without == vps_with, f"A market_description sentence with no size/competition data must never change VPS: {vps_without} vs {vps_with}")


# --- 2. price_point alone must not score economic_potential -----------------


def test_price_point_alone_does_not_score_economic_potential() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["economics"]["price_point"] = 49
    result = _cat(compute_vps(a), "economic_potential")
    expect(result["score"] is None, f"price_point alone (never used in this category's own score math) must leave economic_potential Unavailable, got {result}")


def test_price_point_with_pricing_model_still_scores_normally() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["economics"]["price_point"] = 49
    a["economics"]["pricing_model"] = "Subscription"
    result = _cat(compute_vps(a), "economic_potential")
    expect(result["score"] == 6.0, f"pricing_model alone must still score exactly as before (5.0 + 1.0), got {result['score']}")


# --- 3. CAC=0 must score as the best case, not a penalty --------------------


def test_zero_cac_scores_as_a_strong_positive_signal() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["gtm"]["expected_cac"] = 0
    a["economics"]["price_point"] = 49
    result = _cat(compute_vps(a), "gtm_feasibility")
    expect(result["score"] == 7.0, f"CAC=0 against a real price point is the best possible ratio and must score at least as well as a normal good ratio, got {result}")
    expect("exceeds" not in result["basis"][0] or "zero" in result["basis"][0], f"basis must not claim CAC exceeds price point for a $0 CAC: {result['basis']}")


def test_zero_cac_never_scores_worse_than_a_real_positive_cac() -> None:
    a_zero = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a_zero["gtm"]["expected_cac"] = 0
    a_zero["economics"]["price_point"] = 49

    a_real = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a_real["gtm"]["expected_cac"] = 10
    a_real["economics"]["price_point"] = 49

    score_zero = _cat(compute_vps(a_zero), "gtm_feasibility")["score"]
    score_real = _cat(compute_vps(a_real), "gtm_feasibility")["score"]
    expect(score_zero >= score_real, f"Free customer acquisition (CAC=0) must never score worse than a real positive CAC against the same price: zero={score_zero}, real={score_real}")


# --- 4. price_point=0 must be honestly distinguished from "not stated" ------


def test_zero_price_point_is_not_treated_as_unstated() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["economics"]["price_point"] = 0
    a["gtm"]["expected_cac"] = 50
    result = _cat(compute_vps(a), "gtm_feasibility")
    expect("no price point" not in result["basis"][0], f"A stated $0 price point must never be described as 'no price point to check it against': {result['basis']}")
    expect(result["score"] == 3.0, f"$0 price against a real positive CAC is a genuine negative signal (CAC cannot be recovered), got {result}")


# --- 5. A founder-reported retention fact must never be silently discarded --


def test_retention_reported_alone_is_not_silently_discarded() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["validation"]["retention_pct"] = 65
    result = _cat(compute_vps(a), "validation")
    expect(result["score"] is not None, "A founder who explicitly reports retention must have it reflected, not discarded as Unavailable")
    expect(len(result["basis"]) > 0 and "65" in result["basis"][0], f"The reported retention figure must appear in basis, got {result['basis']}")


def test_retention_reported_alone_is_a_negative_signal_when_weak() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["validation"]["retention_pct"] = 65
    result = _cat(compute_vps(a), "validation")
    expect(result["score"] < 5.0, f"65% retention alone is explicitly weak/negative evidence and must score below neutral, got {result['score']}")


def test_retention_reported_alone_is_a_positive_signal_when_strong() -> None:
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["validation"]["retention_pct"] = 96
    result = _cat(compute_vps(a), "validation")
    expect(result["score"] > 0, f"96% retention alone is real positive evidence and must not be discarded, got {result['score']}")


def test_retention_modifier_still_applies_in_commercial_regime_unchanged() -> None:
    """The fix moves the modifier call, not its behavior -- a paying-
    customers case with retention must score identically to before."""
    a = copy.deepcopy(EMPTY_ASSUMPTIONS)
    a["validation"]["paying_customers"] = 20
    a["validation"]["retention_pct"] = 96
    result = _cat(compute_vps(a), "validation")
    # base (paying=20 -> commercial scale 4.5) + retention modifier (+0.5)
    expect(result["score"] == 5.0, f"Commercial-regime retention modifier must be unchanged by this fix, got {result['score']}")


TESTS = [
    test_market_description_alone_does_not_score_market_potential,
    test_market_description_with_size_still_scores_normally,
    test_the_exact_live_reproduced_nondeterminism_is_fixed,
    test_price_point_alone_does_not_score_economic_potential,
    test_price_point_with_pricing_model_still_scores_normally,
    test_zero_cac_scores_as_a_strong_positive_signal,
    test_zero_cac_never_scores_worse_than_a_real_positive_cac,
    test_zero_price_point_is_not_treated_as_unstated,
    test_retention_reported_alone_is_not_silently_discarded,
    test_retention_reported_alone_is_a_negative_signal_when_weak,
    test_retention_reported_alone_is_a_positive_signal_when_strong,
    test_retention_modifier_still_applies_in_commercial_regime_unchanged,
]


def main() -> None:
    print("\nVPS Scoring Correctness (Phase 29B) -- regression tests")
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
