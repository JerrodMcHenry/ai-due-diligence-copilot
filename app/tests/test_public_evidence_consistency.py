"""
Focused tests for the Public Evidence Validation Consistency Fix.

Root inconsistency being fixed: validate_dimension_evidence() used to
hard-reject EVERY Public+Unavailable combination unconditionally, while
build_dimension_correction_prompt() explicitly permits the model to
preserve Unavailable when genuinely no evidence exists. For Market
Size / Market Growth / Product Usability (frozen NovaLedger evidence,
two 10-run experiments), this meant correction fired every time and
resolved nothing 100% of the time -- an unconditional rule enforcing an
outcome the correction step was never actually constrained to produce.

No LLM calls are made here -- validate_dimension_evidence() and
build_dimension_correction_prompt() are exercised directly with
synthetic EvidenceAnalysis objects.

Run with:
    python -m app.tests.test_public_evidence_consistency
"""

from unittest.mock import patch

from app.ai.evidence_extraction import (
    build_dimension_correction_prompt,
    validate_dimension_evidence,
)
from app.ai.scoring import get_scoring_dimensions
from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import MarketAnalysisResult
from app.models.evidence_analysis import EvidenceAnalysis


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def dimension_weight(pillar: str, name: str) -> float:
    for dim_name, weight in get_scoring_dimensions(pillar):
        if dim_name == name:
            return weight
    raise KeyError(f"No such dimension: {pillar}/{name}")


def unavailable(pillar: str, name: str, missing_information: list[str]) -> EvidenceAnalysis:
    return EvidenceAnalysis(
        dimension=name,
        evidence_status="Unavailable",
        confidence="Low",
        evidence=[],
        missing_information=missing_information,
        rationale="Synthetic test rationale.",
    )


def flagged_for(errors: list[str], name: str) -> bool:
    return any(name in e for e in errors)


# --- 1. Public + genuinely no relevant evidence can remain Unavailable ---

def test_market_size_with_genuinely_no_evidence_remains_unflagged() -> None:
    """Market Size has a TAM/SAM/SOM exemption, but if the model's own
    missing_information describes a genuinely broader gap (not just the
    excused figure), that must still be respected as legitimate."""
    dim = unavailable(
        "Market",
        "Market Size",
        ["No information about customer segments, product category, or "
         "any market-related facts whatsoever."],
    )

    errors = validate_dimension_evidence("Market", dim, company_text="irrelevant")

    expect(
        not flagged_for(errors, "Market Size"),
        f"A genuinely broader gap (not just TAM) must not be flagged; "
        f"errors were: {errors}",
    )


# --- 2/3. Missing TAM alone must trigger reconsideration for Market Size ---

def test_market_size_missing_tam_only_is_flagged_for_reconsideration() -> None:
    dim = unavailable(
        "Market",
        "Market Size",
        ["Total addressable market (TAM) figure"],
    )

    errors = validate_dimension_evidence("Market", dim, company_text="irrelevant")

    expect(
        flagged_for(errors, "Market Size"),
        f"Missing TAM alone must be flagged for reconsideration (not "
        f"silently accepted as Unavailable); errors were: {errors}",
    )
    expect(
        any("must NOT be required" in e for e in errors),
        "The flag should explain that the cited gap is explicitly not "
        "required by this dimension's own methodology.",
    )


def test_market_size_missing_tam_and_something_else_is_not_excused() -> None:
    """If missing_information cites TAM AND something genuinely required
    beyond it, the exemption must not apply -- only a pure "just the
    excused figure" case should be reconsidered."""
    dim = unavailable(
        "Market",
        "Market Size",
        ["Total addressable market (TAM) figure",
         "Any description of the target customer or product category"],
    )

    errors = validate_dimension_evidence("Market", dim, company_text="irrelevant")

    expect(
        not flagged_for(errors, "Market Size"),
        f"A genuinely mixed gap must not be treated as excused-only; "
        f"errors were: {errors}",
    )


# --- 4. Missing CAGR alone must trigger reconsideration for Market Growth ---

def test_market_growth_missing_cagr_only_is_flagged_for_reconsideration() -> None:
    dim = unavailable(
        "Market",
        "Market Growth",
        ["Exact market-wide growth rate (CAGR)"],
    )

    errors = validate_dimension_evidence("Market", dim, company_text="irrelevant")

    expect(
        flagged_for(errors, "Market Growth"),
        f"Missing CAGR alone must be flagged for reconsideration; "
        f"errors were: {errors}",
    )


# --- 5/6. Product Usability may remain Unavailable; retention alone
# does not force it to score ---

def test_usability_unavailable_with_only_capability_evidence_cited_stays_unflagged() -> None:
    dim = unavailable(
        "Product",
        "Usability",
        ["Onboarding time, activation data, or user satisfaction "
         "information -- only product capability is described."],
    )

    errors = validate_dimension_evidence("Product", dim, company_text="irrelevant")

    expect(
        not flagged_for(errors, "Usability"),
        f"Product Usability must be allowed to remain Unavailable -- "
        f"acknowledged methodology ambiguity, not an engineering defect; "
        f"errors were: {errors}",
    )


def test_usability_mentioning_retention_in_missing_info_still_not_forced() -> None:
    """Retention being name-dropped in missing_information must not
    somehow trigger a different, more aggressive path -- Usability has
    no exemption list at all, and is never flagged regardless of what
    its missing_information says, which is the deliberate point: we are
    NOT encoding "retention is sufficient" as a new rule."""
    dim = unavailable(
        "Product",
        "Usability",
        ["Retention data alone was considered but judged insufficient "
         "without direct usability signals."],
    )

    errors = validate_dimension_evidence("Product", dim, company_text="irrelevant")

    expect(
        not flagged_for(errors, "Usability"),
        f"Usability must remain unflagged regardless of retention being "
        f"mentioned -- no retention-sufficiency rule was added; "
        f"errors were: {errors}",
    )


# --- 7. No evidence is fabricated during correction ---

def test_correction_prompt_still_forbids_fabrication_and_permits_unavailable() -> None:
    dim = unavailable(
        "Market",
        "Market Size",
        ["Total addressable market (TAM) figure"],
    )
    errors = validate_dimension_evidence("Market", dim, company_text="irrelevant")

    prompt = build_dimension_correction_prompt(
        pillar="Market",
        dimension=dim,
        validation_errors=errors,
    )

    expect(
        "Do not create evidence merely to avoid an Unavailable result" in prompt,
        "Correction prompt must still forbid fabricating evidence.",
    )
    expect(
        'preserve\n  evidence_status "Unavailable"' in prompt
        or "preserve" in prompt.lower() and "unavailable" in prompt.lower(),
        "Correction prompt must still explicitly permit preserving "
        "Unavailable if no relevant evidence truly exists.",
    )


# --- 8/9. Scoped correction still isolated; malformed correction still
# cannot crash the pillar (specific to this fix's new code path) ---

MARKET_EVIDENCE_WITH_EXCUSABLE_MARKET_SIZE = """
{
  "summary": "s", "confidence": "Medium", "strengths": [], "weaknesses": [],
  "evidence": [], "recommendations": [], "stage_hint": "Series A",
  "dimensions": [
    {"dimension": "Market Size", "evidence_status": "Unavailable", "confidence": "Low",
     "evidence": [], "signals": [], "missing_information": ["Total addressable market (TAM) figure"],
     "recommendations": [], "rationale": "UNCORRECTED"},
    {"dimension": "Market Growth", "evidence_status": "Observed", "confidence": "Medium",
     "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "UNTOUCHED_GROWTH"},
    {"dimension": "Market Timing", "evidence_status": "Observed", "confidence": "Medium",
     "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "UNTOUCHED_TIMING"},
    {"dimension": "Competitive Intensity", "evidence_status": "Inferred", "confidence": "Medium",
     "evidence": ["e", "e2"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "UNTOUCHED_COMPETITIVE"},
    {"dimension": "Customer Demand", "evidence_status": "Observed", "confidence": "Medium",
     "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "UNTOUCHED_DEMAND"}
  ]
}
"""

CLEAN_SCORES = """
{"scores": [
  {"dimension": "Market Growth", "score": 8, "rationale": "s"},
  {"dimension": "Market Timing", "score": 8, "rationale": "s"},
  {"dimension": "Competitive Intensity", "score": 6, "rationale": "s"},
  {"dimension": "Customer Demand", "score": 8, "rationale": "s"}
]}
"""


def test_market_size_correction_does_not_alter_sibling_dimensions() -> None:
    def fake_call(system_content, user_content, temperature):
        if "Re-assess ONLY this dimension" in user_content:
            expect(
                '"Market Size"' in user_content,
                "Only Market Size should be sent for correction.",
            )
            return (
                '{"dimension": "Market Size", "evidence_status": "Inferred", '
                '"confidence": "Medium", "evidence": ["Mid-market e-commerce '
                'segment"], "signals": [], "missing_information": [], '
                '"recommendations": [], "rationale": "CORRECTED"}'
            )
        return MARKET_EVIDENCE_WITH_EXCUSABLE_MARKET_SIZE

    with patch(
        "app.ai.evidence_extraction.call_analysis_model", side_effect=fake_call
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model", return_value=CLEAN_SCORES
    ):
        result = analyze_pillar(
            pillar="Market", company_text="x", result_model=MarketAnalysisResult,
        )

    by_name = {s.name: s for s in result.score_breakdown.subscores}

    expect(
        by_name["Market Size"].evidence_status == "Inferred"
        and by_name["Market Size"].evidence_corrected,
        "Market Size should have been corrected via the new exemption path.",
    )
    for name, marker in [
        ("Market Growth", "UNTOUCHED_GROWTH"),
        ("Market Timing", "UNTOUCHED_TIMING"),
        ("Competitive Intensity", "UNTOUCHED_COMPETITIVE"),
        ("Customer Demand", "UNTOUCHED_DEMAND"),
    ]:
        expect(
            by_name[name].evidence_corrected is False,
            f"{name} must be unaffected by Market Size's correction.",
        )


def test_malformed_correction_on_excused_dimension_does_not_crash_pillar() -> None:
    def fake_call(system_content, user_content, temperature):
        if "Re-assess ONLY this dimension" in user_content:
            return "not valid json {{{"
        return MARKET_EVIDENCE_WITH_EXCUSABLE_MARKET_SIZE

    with patch(
        "app.ai.evidence_extraction.call_analysis_model", side_effect=fake_call
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model", return_value=CLEAN_SCORES
    ):
        result = analyze_pillar(
            pillar="Market", company_text="x", result_model=MarketAnalysisResult,
        )

    by_name = {s.name: s for s in result.score_breakdown.subscores}

    expect(
        by_name["Market Size"].evidence_status == "Unavailable"
        and by_name["Market Size"].score is None,
        "A malformed correction must fall back to the original "
        "Unavailable assessment, not crash or fabricate a score.",
    )
    for name in ["Market Growth", "Market Timing", "Competitive Intensity", "Customer Demand"]:
        expect(
            by_name[name].evidence_corrected is False,
            f"{name} must be unaffected by Market Size's failed correction.",
        )


TESTS = [
    test_market_size_with_genuinely_no_evidence_remains_unflagged,
    test_market_size_missing_tam_only_is_flagged_for_reconsideration,
    test_market_size_missing_tam_and_something_else_is_not_excused,
    test_market_growth_missing_cagr_only_is_flagged_for_reconsideration,
    test_usability_unavailable_with_only_capability_evidence_cited_stays_unflagged,
    test_usability_mentioning_retention_in_missing_info_still_not_forced,
    test_correction_prompt_still_forbids_fabrication_and_permits_unavailable,
    test_market_size_correction_does_not_alter_sibling_dimensions,
    test_malformed_correction_on_excused_dimension_does_not_crash_pillar,
]


def main() -> None:
    print("\nPublic Evidence Validation Consistency Fix tests")
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
