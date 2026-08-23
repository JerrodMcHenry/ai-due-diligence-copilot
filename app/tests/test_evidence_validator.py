"""
Focused tests for evidence-stage validation (originally SIE Scoring
Reliability sprint Phase 4; updated for the Evidence/Scoring Separation
sprint, where validation now operates on a single EvidenceAnalysis
object per dimension instead of a whole score_breakdown).

No LLM calls are made here -- these exercise validate_dimension_evidence()
directly, reproducing the exact NovaLedger-style cases the forensic
audit found: a dimension marked Unavailable even though the required
evidence was explicitly present in company_text the whole time.

This only tests that the validator correctly *flags* these cases so the
scoped correction pass (app/ai/evidence_extraction.py) gets a chance to
re-examine them -- it does not, and cannot, unit-test that the LLM's
correction makes the right final call, since that requires a live model
call. That part is covered by the live frozen-evidence reliability
harness (app/reliability/).

Run with:
    python -m app.tests.test_evidence_validator
"""

from app.ai.evidence_extraction import validate_dimension_evidence
from app.models.evidence_analysis import EvidenceAnalysis


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unavailable(dimension: str) -> EvidenceAnalysis:
    return EvidenceAnalysis(
        dimension=dimension,
        evidence_status="Unavailable",
        confidence="Low",
        evidence=[],
        missing_information=["Detailed operating metrics for this dimension."],
        rationale="Public information does not clearly establish this dimension.",
    )


def flagged(errors: list[str]) -> bool:
    return any(
        "supplied company information appears to explicitly disclose" in e
        for e in errors
    )


def test_disclosed_burn_and_runway_flags_private_dimension() -> None:
    """Financial Health / Burn Efficiency is Private. NovaLedger analysis
    74 marked it Unavailable despite company_text explicitly disclosing
    both burn rate and runway -- exactly the evidence its own methodology
    says is sufficient to score it."""
    company_text = (
        "Current monthly burn is approximately $180,000. The company "
        "reports approximately 14 months of runway at the current burn "
        "rate. Gross margin on the core product is approximately 78%."
    )

    errors = validate_dimension_evidence(
        pillar="Financial Health",
        dimension=unavailable("Burn Efficiency"),
        company_text=company_text,
    )

    expect(
        flagged(errors),
        f"Expected Burn Efficiency to be flagged for re-examination given "
        f"disclosed burn/runway; errors were: {errors}",
    )


def test_disclosed_revenue_and_customer_growth_flags_inferred_dimension() -> None:
    """Team / Business Capability is Inferred. NovaLedger analysis 74
    marked it Unavailable despite customer and revenue growth being
    explicitly disclosed in company_text."""
    company_text = (
        "NovaLedger has grown from 10 to 40 paying customers over the "
        "past two quarters. Monthly recurring revenue has grown from "
        "$18,000 to $61,000 over the same period."
    )

    errors = validate_dimension_evidence(
        pillar="Team",
        dimension=unavailable("Business Capability"),
        company_text=company_text,
    )

    expect(
        flagged(errors),
        f"Expected Business Capability to be flagged for re-examination "
        f"given disclosed revenue/customer growth; errors were: {errors}",
    )


def test_disclosed_execution_metrics_flags_inferred_dimension() -> None:
    """Execution / Product Execution is Inferred. NovaLedger analysis 74
    marked it Unavailable despite the product being explicitly described
    as shipped and used by paying customers."""
    company_text = (
        "NovaLedger has a shipped product used by 40 paying mid-market "
        "e-commerce customers. The product integrates directly with "
        "Stripe, Shopify Payments, and PayPal APIs."
    )

    errors = validate_dimension_evidence(
        pillar="Execution",
        dimension=unavailable("Product Execution"),
        company_text=company_text,
    )

    expect(
        flagged(errors),
        f"Expected Product Execution to be flagged for re-examination "
        f"given disclosed shipped-product/customer evidence; errors "
        f"were: {errors}",
    )


def test_genuinely_unavailable_dimension_is_not_flagged() -> None:
    """Negative control: no disclosed quantitative signals at all. The
    validator must not manufacture a flag when there truly is nothing to
    re-examine."""
    company_text = (
        "The company builds developer tools. No further information "
        "about the business is provided in this description."
    )

    errors = validate_dimension_evidence(
        pillar="Financial Health",
        dimension=unavailable("Burn Efficiency"),
        company_text=company_text,
    )

    expect(
        not flagged(errors),
        f"Genuinely unavailable dimension should not be flagged; "
        f"errors were: {errors}",
    )


def test_single_incidental_term_is_not_enough_to_flag() -> None:
    """Conservatism check: exactly one matching term must not trigger the
    flag, mirroring the methodology's own '>= 2 credible signals' bar for
    Inferred dimensions."""
    company_text = "The company generates revenue from its work."

    errors = validate_dimension_evidence(
        pillar="Team",
        dimension=unavailable("Leadership"),
        company_text=company_text,
    )

    expect(
        not flagged(errors),
        f"Zero/one matching term should not trigger the flag; "
        f"errors were: {errors}",
    )


def test_public_dimension_unavailable_still_rejected() -> None:
    """Regression guard: the hard Public+Unavailable rejection is
    unchanged for Public dimensions with no methodology-grounded
    exemption (see app/tests/test_public_evidence_consistency.py for
    Market Size / Market Growth / Usability, which now behave
    differently -- deliberately, per the Public Evidence Validation
    Consistency Fix)."""
    errors = validate_dimension_evidence(
        pillar="Team",
        dimension=unavailable("Founder-Market Fit"),
        company_text="No related information provided.",
    )

    expect(
        any("Public dimensions must be assessed" in e for e in errors),
        f"Public+Unavailable must still be hard-rejected for dimensions "
        f"with no exemption; errors were: {errors}",
    )


def test_evidence_analysis_carries_no_score() -> None:
    """The evidence layer itself cannot express a numeric judgment --
    there is no field for it to be misused."""
    dim = unavailable("Burn Efficiency")
    expect(
        not hasattr(dim, "score"),
        "EvidenceAnalysis must not expose a score attribute.",
    )


TESTS = [
    test_disclosed_burn_and_runway_flags_private_dimension,
    test_disclosed_revenue_and_customer_growth_flags_inferred_dimension,
    test_disclosed_execution_metrics_flags_inferred_dimension,
    test_genuinely_unavailable_dimension_is_not_flagged,
    test_single_incidental_term_is_not_enough_to_flag,
    test_public_dimension_unavailable_still_rejected,
    test_evidence_analysis_carries_no_score,
]


def main() -> None:
    print("\nSIE evidence-validator tests")
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
