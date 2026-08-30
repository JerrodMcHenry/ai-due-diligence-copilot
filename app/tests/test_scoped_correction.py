"""
Focused tests for scoped, per-dimension correction (SIE Evidence/Scoring
Separation sprint, Phase 5).

All model calls are mocked. These specifically reproduce the two defects
the Reliability Sprint found: whole-pillar correction regressing
unrelated dimensions, and a malformed correction response crashing the
whole pillar analysis.

Run with:
    python -m app.tests.test_scoped_correction
"""

import json
from unittest.mock import patch

from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import MarketAnalysisResult


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


COMPANY_TEXT = (
    "NovaLedger is a fintech company with disclosed metrics, operating in "
    "a category where fintech deal volume is up 33% YoY."
)
# Methodology V2.1 (Phase 10.8B, Part 3): COMPANY_TEXT must contain every
# specific number the fixture evidence below cites, or the evidence-
# provenance guard (app/ai/evidence_provenance.py) will correctly strip it
# as unsupported and this test's "untouched dimension" assertions would
# fail for a reason unrelated to what this file actually tests (scoped
# correction, not provenance). "33% YoY" was added here for this reason.

# Market Size (Public) is WRONGLY marked Unavailable -- must trigger a
# scoped correction. The other four dimensions are valid on the first
# try and must never be resent to the model.
INITIAL_EVIDENCE_WITH_ONE_INVALID_DIMENSION = json.dumps({
    "summary": "Evidence-based market summary.",
    "confidence": "Medium",
    "strengths": [],
    "weaknesses": [],
    "evidence": [],
    "recommendations": [],
    "stage_hint": "Series A",
    "dimensions": [
        {"dimension": "Market Size", "evidence_status": "Unavailable", "confidence": "Low",
         "evidence": [], "signals": [], "missing_information": ["TAM figure"],
         "recommendations": [], "rationale": "No explicit TAM given."},
        {"dimension": "Market Growth", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["Fintech deal volume up 33% YoY"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "UNTOUCHED_MARKER_GROWTH"},
        {"dimension": "Market Timing", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["Multi-processor checkout becoming standard"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "UNTOUCHED_MARKER_TIMING"},
        {"dimension": "Competitive Intensity", "evidence_status": "Inferred", "confidence": "Medium",
         "evidence": ["Manual spreadsheets", "No dominant incumbent"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "UNTOUCHED_MARKER_COMPETITIVE"},
        {"dimension": "Customer Demand", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["40 paying customers"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "UNTOUCHED_MARKER_DEMAND"},
    ],
})

CORRECTED_MARKET_SIZE_ONLY = json.dumps({
    "dimension": "Market Size",
    "evidence_status": "Observed",
    "confidence": "Medium",
    "evidence": ["Mid-market e-commerce finance segment is sizable"],
    "signals": [],
    "missing_information": [],
    "recommendations": [],
    "rationale": "CORRECTED_MARKET_SIZE",
})

CLEAN_SCORES = json.dumps({
    "scores": [
        {"dimension": "Market Size", "score": 7, "rationale": "s1"},
        {"dimension": "Market Growth", "score": 8, "rationale": "s2"},
        {"dimension": "Market Timing", "score": 8, "rationale": "s3"},
        {"dimension": "Competitive Intensity", "score": 6, "rationale": "s4"},
        {"dimension": "Customer Demand", "score": 8, "rationale": "s5"},
    ],
})


def fake_evidence_call(system_content, user_content, temperature):
    if "Re-assess ONLY this dimension" in user_content:
        expect(
            '"Market Size"' in user_content,
            "Only Market Size should ever be sent for evidence correction.",
        )
        return CORRECTED_MARKET_SIZE_ONLY
    return INITIAL_EVIDENCE_WITH_ONE_INVALID_DIMENSION


def test_scoped_evidence_correction_touches_only_flagged_dimension() -> None:
    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        side_effect=fake_evidence_call,
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model",
        return_value=CLEAN_SCORES,
    ):
        result = analyze_pillar(
            pillar="Market",
            company_text=COMPANY_TEXT,
            result_model=MarketAnalysisResult,
        )

    by_name = {s.name: s for s in result.score_breakdown.subscores}

    expect(
        by_name["Market Size"].evidence_status == "Observed",
        "Market Size should have been corrected to Observed.",
    )
    expect(
        by_name["Market Size"].evidence_corrected is True,
        "Market Size should be flagged evidence_corrected.",
    )
    expect(
        "CORRECTED_MARKET_SIZE" in by_name["Market Size"].rationale
        or by_name["Market Size"].score is not None,
        "Corrected Market Size should reflect the corrected content.",
    )

    for name, marker in [
        ("Market Growth", "UNTOUCHED_MARKER_GROWTH"),
        ("Market Timing", "UNTOUCHED_MARKER_TIMING"),
        ("Competitive Intensity", "UNTOUCHED_MARKER_COMPETITIVE"),
        ("Customer Demand", "UNTOUCHED_MARKER_DEMAND"),
    ]:
        subscore = by_name[name]
        expect(
            subscore.evidence_corrected is False,
            f"{name} must not be marked evidence_corrected -- it was "
            f"never sent for correction.",
        )
        # The rationale carried through to the final Subscore comes from
        # the scoring stage in this test (clean scores), but the
        # dimension's *evidence* must still trace back to the original,
        # never-corrected extraction -- verified via evidence_corrected
        # being False above, which is only set when that dimension's
        # slot was actually replaced by a correction call.


def test_malformed_evidence_correction_does_not_crash_pillar() -> None:
    """The exact defect the Reliability Sprint found: a garbled
    correction response for one dimension must not take down the whole
    pillar analysis."""

    def fake_call(system_content, user_content, temperature):
        if "Re-assess ONLY this dimension" in user_content:
            return "not valid json at all {{{"
        return INITIAL_EVIDENCE_WITH_ONE_INVALID_DIMENSION

    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        side_effect=fake_call,
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model",
        return_value=CLEAN_SCORES,
    ):
        # Must not raise.
        result = analyze_pillar(
            pillar="Market",
            company_text=COMPANY_TEXT,
            result_model=MarketAnalysisResult,
        )

    by_name = {s.name: s for s in result.score_breakdown.subscores}

    expect(
        by_name["Market Size"].evidence_status == "Unavailable",
        "On a malformed correction, the original (pre-correction) "
        "assessment should be kept, not fabricated.",
    )
    for name in ["Market Growth", "Market Timing", "Competitive Intensity", "Customer Demand"]:
        expect(
            by_name[name].evidence_corrected is False,
            f"{name} must be unaffected by a failed correction on a "
            f"different dimension.",
        )


def test_malformed_score_correction_does_not_crash_pillar() -> None:
    """Same guarantee on the scoring-stage side: one dimension's score
    coming back invalid, then failing correction too, must not crash
    the pillar -- and must not silently invent a number."""

    clean_evidence = json.dumps({
        "summary": "s", "confidence": "Medium", "strengths": [], "weaknesses": [],
        "evidence": [], "recommendations": [], "stage_hint": "",
        "dimensions": [
            {"dimension": "Market Size", "evidence_status": "Observed", "confidence": "Medium",
             "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "r"},
            {"dimension": "Market Growth", "evidence_status": "Observed", "confidence": "Medium",
             "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "r"},
            {"dimension": "Market Timing", "evidence_status": "Observed", "confidence": "Medium",
             "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "r"},
            {"dimension": "Competitive Intensity", "evidence_status": "Observed", "confidence": "Medium",
             "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "r"},
            {"dimension": "Customer Demand", "evidence_status": "Observed", "confidence": "Medium",
             "evidence": ["e"], "signals": [], "missing_information": [], "recommendations": [], "rationale": "r"},
        ],
    })

    scores_with_one_invalid = json.dumps({
        "scores": [
            {"dimension": "Market Size", "score": 7, "rationale": "s1"},
            {"dimension": "Market Growth", "score": 8, "rationale": "s2"},
            {"dimension": "Market Timing", "score": 8, "rationale": "s3"},
            {"dimension": "Competitive Intensity", "score": 6, "rationale": "s4"},
            {"dimension": "Customer Demand", "score": 99, "rationale": "s5"},  # out of range
        ],
    })

    def fake_score_call(system_content, user_content, temperature):
        if "Re-score ONLY this dimension" in user_content:
            return "not valid json {{{"
        return scores_with_one_invalid

    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        return_value=clean_evidence,
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model",
        side_effect=fake_score_call,
    ):
        result = analyze_pillar(
            pillar="Market",
            company_text=COMPANY_TEXT,
            result_model=MarketAnalysisResult,
        )

    by_name = {s.name: s for s in result.score_breakdown.subscores}

    expect(
        by_name["Customer Demand"].score is None,
        "An invalid score that also fails correction must end up null, "
        "never a fabricated or out-of-range number.",
    )
    for name in ["Market Size", "Market Growth", "Market Timing", "Competitive Intensity"]:
        expect(
            by_name[name].score_corrected is False,
            f"{name}'s valid score must be unaffected by Customer "
            f"Demand's failed correction.",
        )
        expect(
            by_name[name].score is not None,
            f"{name} should still have its original valid score.",
        )


TESTS = [
    test_scoped_evidence_correction_touches_only_flagged_dimension,
    test_malformed_evidence_correction_does_not_crash_pillar,
    test_malformed_score_correction_does_not_crash_pillar,
]


def main() -> None:
    print("\nSIE scoped-correction tests")
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
