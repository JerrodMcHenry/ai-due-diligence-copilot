"""
Phase 31C, Part 7 -- Final VPS Semantic Integrity Audit.

A NARROW verification pass, not a methodology redesign. Tests the exact
representative transitions the directive names:

    unknown -> modeled assumption
    unknown -> real evidence
    assumption -> stronger evidence
    assumption -> contradictory evidence
    weak evidence -> stronger evidence
    positive evidence
    negative evidence
    mixed evidence

plus determinism, provenance handling, unknown handling, availability
gates, monotonic behavior where it should logically exist, and
legitimate non-monotonic behavior where learning exposes weakness.

Conclusion of this audit (see Phase 31C's own final report): no
methodology bug was found. compute_vps()'s Phase 29A dampening branch
(a lone, uncorroborated modeled assumption reports at the neutral
anchor; real Validation evidence is trusted immediately, even alone) is
working exactly as designed, and is the correct, intentional mechanism
by which "real evidence is not guaranteed to increase VPS" -- not a
defect to fix. No weight, threshold, or formula in vps_scoring.py is
changed by this file. VPS is frozen after this phase.

Run with:
    python -m app.tests.test_vps_final_integrity_audit
"""

from app.ai.vps_scoring import compute_vps, VPS_CATEGORY_WEIGHTS


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def empty_assumptions() -> dict:
    return {
        "target_customer": None,
        "market": {"market_description": None, "estimated_market_size": None, "competition_intensity": None},
        "problem_solution": {"problem_statement": None, "solution_description": None, "differentiation": None},
        "founder": {
            "founder_count": None,
            "relevant_domain_experience_years": None,
            "has_technical_cofounder": None,
            "has_business_cofounder": None,
        },
        "gtm": {"primary_acquisition_strategy": None, "expected_cac": None},
        "economics": {"pricing_model": None, "price_point": None, "expected_gross_margin_pct": None},
        "validation": {
            "customer_interviews": None,
            "waitlist_signups": None,
            "paying_customers": None,
            "monthly_revenue": None,
            "prior_monthly_revenue": None,
            "retention_pct": None,
        },
        "capital": {"starting_capital": None, "monthly_burn": None},
    }


def category(result: dict, key: str) -> dict:
    for c in result["categories"]:
        if c["key"] == key:
            return c
    raise AssertionError(f"No category {key!r} in result")


# --- Determinism ---------------------------------------------------------


def test_determinism_identical_input_identical_output() -> None:
    assumptions = empty_assumptions()
    assumptions["market"]["estimated_market_size"] = "Large"
    assumptions["validation"]["paying_customers"] = 12
    assumptions["validation"]["retention_pct"] = 95.0

    results = [compute_vps(assumptions) for _ in range(20)]
    expect(len(set(str(r) for r in results)) == 1, "compute_vps() must be perfectly deterministic across repeated calls")


# --- Unknown handling / availability gates --------------------------------


def test_all_unknown_returns_no_score_never_fabricated() -> None:
    result = compute_vps(empty_assumptions())
    expect(result["vps"] is None, "A venture with zero assumptions must report vps=None, never 0 or 5")
    for c in result["categories"]:
        expect(c["score"] is None, f"Category {c['key']} must be Unavailable, not fabricated")


def test_economic_potential_requires_pricing_model_or_margin_not_price_point_alone() -> None:
    """Availability gate check: price_point alone must NOT establish
    economic_potential as scored -- only pricing_model/margin actually
    move that category's score (see _score_economic_potential's own
    docstring for the prior, now-fixed defect this guards against
    regressing)."""
    assumptions = empty_assumptions()
    assumptions["economics"]["price_point"] = 29.0
    result = compute_vps(assumptions)
    expect(
        category(result, "economic_potential")["score"] is None,
        "price_point alone must not unlock economic_potential -- it carries no basis-worthy signal by itself",
    )


def test_gtm_feasibility_requires_strategy_or_cac_not_price_point_alone() -> None:
    assumptions = empty_assumptions()
    assumptions["economics"]["price_point"] = 29.0
    result = compute_vps(assumptions)
    expect(
        category(result, "gtm_feasibility")["score"] is None,
        "price_point alone must not unlock gtm_feasibility -- strategy or cac is required",
    )


# --- unknown -> modeled assumption ----------------------------------------


def test_unknown_to_lone_modeled_assumption_dampens_to_neutral_anchor() -> None:
    """A single, uncorroborated modeled assumption must not single-
    handedly set VPS to its own raw score -- Phase 29A's own fix."""
    assumptions = empty_assumptions()
    assumptions["market"]["estimated_market_size"] = "Large"  # raw market_potential score would be 6.5

    result = compute_vps(assumptions)
    scored = [c for c in result["categories"] if c["score"] is not None]

    expect(len(scored) == 1, "Sanity: exactly one category should be scored")
    expect(result["sole_uncorroborated_category"] is True, "The dampening flag must fire for a lone modeled assumption")
    expect(result["vps"] == 5.0, f"A lone modeled assumption must dampen to the neutral anchor 5.0, got {result['vps']}")
    expect(
        category(result, "market_potential")["score"] == 6.5,
        "The category's own displayed score must stay its real, undamped value even while the aggregate dampens",
    )


# --- unknown -> real evidence ----------------------------------------------


def test_unknown_to_lone_real_evidence_is_trusted_immediately() -> None:
    """Unlike a lone MODELED assumption, real founder-reported evidence
    (Validation) is never dampened, even when it's the only category
    scored -- provenance changes the trust rule, exactly as this
    module's own docstring on VentureAssumptions describes."""
    assumptions = empty_assumptions()
    assumptions["validation"]["paying_customers"] = 5  # raw validation score = 3.0

    result = compute_vps(assumptions)
    scored = [c for c in result["categories"] if c["score"] is not None]

    expect(len(scored) == 1, "Sanity: exactly one category should be scored")
    expect(
        result["sole_uncorroborated_category"] is False,
        "Real validation evidence must never trigger the lone-assumption dampening flag",
    )
    expect(
        result["vps"] == category(result, "validation")["score"],
        "A lone but REAL evidence category must be trusted at its own raw score, not dampened toward 5.0",
    )


# --- assumption -> stronger evidence ---------------------------------------


def test_assumption_plus_corroborating_evidence_moves_off_the_anchor() -> None:
    assumptions = empty_assumptions()
    assumptions["market"]["estimated_market_size"] = "Large"
    before = compute_vps(assumptions)
    expect(before["vps"] == 5.0, "Sanity: still dampened with one category")

    assumptions["validation"]["paying_customers"] = 50  # raw validation score = 5.5
    after = compute_vps(assumptions)

    expect(after["sole_uncorroborated_category"] is False, "A second scored category must turn dampening off")
    market_score = category(after, "market_potential")["score"]
    validation_score = category(after, "validation")["score"]
    expected = round(
        (market_score * VPS_CATEGORY_WEIGHTS["market_potential"] + validation_score * VPS_CATEGORY_WEIGHTS["validation"])
        / (VPS_CATEGORY_WEIGHTS["market_potential"] + VPS_CATEGORY_WEIGHTS["validation"]),
        1,
    )
    expect(after["vps"] == expected, f"Expected the real renormalized weighted average {expected}, got {after['vps']}")
    expect(after["vps"] > before["vps"], "Strong corroborating evidence must raise VPS off the dampened anchor here")


# --- assumption -> contradictory evidence (legitimate non-monotonic) ------


def test_assumption_plus_contradictory_weak_evidence_can_lower_vps() -> None:
    """The central Part 7 property: real evidence is NOT guaranteed to
    raise VPS. A favorable-looking lone assumption, once corroborated by
    genuinely weak real evidence, must be allowed to fall -- this is
    honest, not a bug."""
    assumptions = empty_assumptions()
    assumptions["market"]["estimated_market_size"] = "Large"
    before = compute_vps(assumptions)
    expect(before["vps"] == 5.0, "Sanity: still dampened with one category")

    assumptions["validation"]["paying_customers"] = 1  # raw validation score = 2.0, genuinely weak
    after = compute_vps(assumptions)

    expect(after["sole_uncorroborated_category"] is False, "A second scored category must turn dampening off")
    expect(
        after["vps"] < before["vps"],
        f"Weak real evidence must be allowed to lower VPS from the dampened anchor ({before['vps']} -> {after['vps']})",
    )


# --- weak evidence -> stronger evidence (monotonic where it should exist) -


def test_more_paying_customers_never_lowers_validation_score() -> None:
    """Holding every other input fixed, MORE paying customers must never
    score worse than fewer -- true monotonicity within one evidence type."""
    tiers = [0, 1, 3, 10, 50, 100, 500]
    scores = []
    for paying in tiers:
        assumptions = empty_assumptions()
        assumptions["validation"]["paying_customers"] = paying
        result = compute_vps(assumptions)
        scores.append(category(result, "validation")["score"] if paying else None)

    real_scores = [s for s in scores if s is not None]
    expect(
        real_scores == sorted(real_scores),
        f"Validation score must be monotonically non-decreasing in paying_customers, got {list(zip(tiers[1:], real_scores))}",
    )


# --- positive / negative / mixed evidence ----------------------------------


def test_positive_evidence_retention_raises_validation_score() -> None:
    base = empty_assumptions()
    base["validation"]["paying_customers"] = 20
    baseline_score = category(compute_vps(base), "validation")["score"]

    base["validation"]["retention_pct"] = 120.0  # strong net-expansion signal
    improved_score = category(compute_vps(base), "validation")["score"]

    expect(improved_score > baseline_score, "Strong retention (>=110%) must raise the validation score")


def test_negative_evidence_retention_lowers_validation_score() -> None:
    base = empty_assumptions()
    base["validation"]["paying_customers"] = 20
    baseline_score = category(compute_vps(base), "validation")["score"]

    base["validation"]["retention_pct"] = 50.0  # genuinely weak retention
    worsened_score = category(compute_vps(base), "validation")["score"]

    expect(worsened_score < baseline_score, "Weak retention (<70%) must lower the validation score")


def test_mixed_evidence_combines_both_modifiers_additively() -> None:
    """Growth (positive) and retention (negative) reported together must
    both apply -- neither silently cancels or overrides the other; the
    net effect is their honest sum, whichever sign that nets out to."""
    base = empty_assumptions()
    base["validation"]["monthly_revenue"] = 15000.0
    base_score = category(compute_vps(base), "validation")["score"]

    mixed = empty_assumptions()
    mixed["validation"]["monthly_revenue"] = 15000.0
    mixed["validation"]["prior_monthly_revenue"] = 5000.0  # 200% growth: positive modifier
    mixed["validation"]["retention_pct"] = 50.0  # negative modifier
    mixed_result = compute_vps(mixed)
    mixed_score = category(mixed_result, "validation")["score"]
    basis = category(mixed_result, "validation")["basis"]

    expect(
        any("growth" in b for b in basis) and any("retention" in b for b in basis),
        f"Both the growth and retention signals must appear in the basis explanation, got {basis}",
    )
    # Growth modifier (+1.5 for >=150% growth) and retention modifier
    # (-2.5 for <70%) net to -1.0 relative to revenue alone -- confirms
    # both applied (not just one overriding the other), and that a mixed
    # picture nets out honestly rather than defaulting to either extreme.
    expect(
        abs((mixed_score - base_score) - (1.5 - 2.5)) < 0.01,
        f"Expected the two modifiers to combine additively (net -1.0), got a net delta of {mixed_score - base_score}",
    )


# --- score explanations matching actual score changes ----------------------


def test_basis_explanation_present_exactly_when_a_modifier_actually_applied() -> None:
    with_retention = empty_assumptions()
    with_retention["validation"]["paying_customers"] = 20
    with_retention["validation"]["retention_pct"] = 120.0
    basis_with = category(compute_vps(with_retention), "validation")["basis"]
    expect(any("retention" in b for b in basis_with), "A retention modifier that applied must appear in basis")

    without_retention = empty_assumptions()
    without_retention["validation"]["paying_customers"] = 20
    basis_without = category(compute_vps(without_retention), "validation")["basis"]
    expect(
        not any("retention" in b for b in basis_without),
        "No retention claim may appear in basis when retention was never reported",
    )


TESTS = [
    test_determinism_identical_input_identical_output,
    test_all_unknown_returns_no_score_never_fabricated,
    test_economic_potential_requires_pricing_model_or_margin_not_price_point_alone,
    test_gtm_feasibility_requires_strategy_or_cac_not_price_point_alone,
    test_unknown_to_lone_modeled_assumption_dampens_to_neutral_anchor,
    test_unknown_to_lone_real_evidence_is_trusted_immediately,
    test_assumption_plus_corroborating_evidence_moves_off_the_anchor,
    test_assumption_plus_contradictory_weak_evidence_can_lower_vps,
    test_more_paying_customers_never_lowers_validation_score,
    test_positive_evidence_retention_raises_validation_score,
    test_negative_evidence_retention_lowers_validation_score,
    test_mixed_evidence_combines_both_modifiers_additively,
    test_basis_explanation_present_exactly_when_a_modifier_actually_applied,
]


def main() -> None:
    print("\nPhase 31C, Part 7 -- Final VPS Semantic Integrity Audit")
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
