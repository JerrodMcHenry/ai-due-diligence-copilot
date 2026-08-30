"""
Focused tests for the two-stage evidence/scoring pipeline (SIE
Evidence/Scoring Separation sprint, Phases 2-4).

All model calls are mocked -- no live LLM calls, no API cost. These
tests validate the pipeline's structure and data flow, not the model's
judgment quality (that's what the frozen-evidence harness measures).

Run with:
    python -m app.tests.test_evidence_scoring_pipeline
"""

import json
from unittest.mock import patch

from app.models.evidence_analysis import EvidenceAnalysis, PillarEvidenceAnalysis
from app.ai.evidence_extraction import build_evidence_prompt, extract_pillar_evidence
from app.ai.pillar_scoring import build_scoring_prompt, score_pillar_evidence
from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import MarketAnalysisResult


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


COMPANY_TEXT = (
    "NovaLedger has 40 paying customers, MRR grew from $18,000 to "
    "$61,000, net revenue retention is 115%, and fintech deal volume in "
    "its category grew 33% year-over-year."
)
# Methodology V2.1 (Phase 10.8B, Part 3): every specific number the fixture
# evidence below cites must actually appear in COMPANY_TEXT above -- the
# evidence-provenance guard (app/ai/evidence_provenance.py) now strips any
# quoted evidence bullet whose number cannot be traced to the supplied
# company text, exactly as it should for a real fabricated figure. The
# "33% YoY growth" fact was added to COMPANY_TEXT above for this reason
# (it did not appear in the original fixture, which predates the guard).

# All five Market dimensions correctly assessed on the first try.
INITIAL_EVIDENCE_JSON = json.dumps({
    "summary": "Evidence-based market summary.",
    "confidence": "Medium",
    "strengths": [],
    "weaknesses": [],
    "evidence": [],
    "recommendations": [],
    "stage_hint": "Series A",
    "dimensions": [
        {"dimension": "Market Size", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["Mid-market e-commerce finance segment"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "Public category evidence."},
        {"dimension": "Market Growth", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["Fintech deal volume up 33% YoY"], "signals": ["33% YoY growth"], "missing_information": [],
         "recommendations": [], "rationale": "Disclosed growth stat."},
        {"dimension": "Market Timing", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["Multi-processor checkout becoming standard"], "signals": [], "missing_information": [],
         "recommendations": [], "rationale": "Timing signal present."},
        {"dimension": "Competitive Intensity", "evidence_status": "Inferred", "confidence": "Medium",
         "evidence": ["Manual spreadsheets are primary competitor", "No dominant incumbent"], "signals": [],
         "missing_information": [], "recommendations": [], "rationale": "Two independent signals."},
        {"dimension": "Customer Demand", "evidence_status": "Observed", "confidence": "Medium",
         "evidence": ["40 paying customers", "NRR 115%"], "signals": ["NRR 115%"], "missing_information": [],
         "recommendations": [], "rationale": "Direct traction facts."},
    ],
})

# All five dimensions score cleanly on the first try.
INITIAL_SCORES_JSON = json.dumps({
    "scores": [
        {"dimension": "Market Size", "score": 7, "rationale": "Sizable segment."},
        {"dimension": "Market Growth", "score": 8, "rationale": "Strong disclosed growth."},
        {"dimension": "Market Timing", "score": 8, "rationale": "Good timing signal."},
        {"dimension": "Competitive Intensity", "score": 6, "rationale": "Moderate competitive risk."},
        {"dimension": "Customer Demand", "score": 8, "rationale": "Strong traction evidence."},
    ],
})


def test_evidence_analysis_model_has_no_score_field() -> None:
    """Phase 7 #1: evidence extraction produces no numeric score --
    enforced structurally by the model itself, not just by convention."""
    field_names = set(EvidenceAnalysis.model_fields.keys())
    expect(
        "score" not in field_names,
        f"EvidenceAnalysis must not have a score field; fields were: {field_names}",
    )


def test_scoring_prompt_never_contains_raw_company_text() -> None:
    """Phase 4 / Phase 7 #3: the scorer must not receive the raw
    corpus. It can only see what stage 1 already normalized."""
    evidence = PillarEvidenceAnalysis(
        pillar="Market",
        dimensions=[
            EvidenceAnalysis(
                dimension="Market Size",
                evidence_status="Observed",
                confidence="Medium",
                evidence=["Mid-market e-commerce finance segment"],
                rationale="Public category evidence.",
            ),
        ],
    )

    prompt = build_scoring_prompt("Market", evidence, stage="Series A")

    expect(
        COMPANY_TEXT not in prompt,
        "Scoring prompt must not contain the raw company_text verbatim.",
    )
    expect(
        "40 paying customers" not in prompt,
        "Scoring prompt must not leak raw-text facts that were never "
        "surfaced through the evidence stage's `evidence`/`signals` fields.",
    )


def test_identical_normalized_evidence_reused_independently() -> None:
    """Phase 7 #2: the SAME normalized evidence object can be scored
    independently more than once without re-deriving anything -- the
    scoring stage is a pure function of the evidence object plus the
    (fixed) rubric, not of call history."""
    evidence = PillarEvidenceAnalysis(
        pillar="Market",
        dimensions=[
            EvidenceAnalysis(
                dimension="Market Size",
                evidence_status="Observed",
                confidence="Medium",
                evidence=["Mid-market e-commerce finance segment"],
                rationale="Public category evidence.",
            ),
        ],
    )

    prompt_1 = build_scoring_prompt("Market", evidence, stage="Series A")
    prompt_2 = build_scoring_prompt("Market", evidence, stage="Series A")

    expect(
        prompt_1 == prompt_2,
        "The same EvidenceAnalysis object must produce the identical "
        "scoring prompt on repeated calls.",
    )


def test_unavailable_evidence_never_sent_to_scorer() -> None:
    evidence = PillarEvidenceAnalysis(
        pillar="Market",
        dimensions=[
            EvidenceAnalysis(
                dimension="Market Size",
                evidence_status="Unavailable",
                confidence="Low",
                missing_information=["TAM figure"],
            ),
        ],
    )

    prompt = build_scoring_prompt("Market", evidence, stage="")

    expect(
        prompt == "",
        "A pillar with no scoreable dimensions must produce an empty "
        "scoring prompt (no model call should even be made).",
    )


def test_full_pipeline_end_to_end_with_mocked_calls() -> None:
    """Exercises analyze_pillar() through both stages with clean mocked
    responses (no correction needed) and checks the assembled Subscore
    list is fully correct: right scores, right weights (from config,
    never from the model), evidence/signals carried through, no
    correction flags set."""
    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        return_value=INITIAL_EVIDENCE_JSON,
    ), patch(
        "app.ai.pillar_scoring.call_analysis_model",
        return_value=INITIAL_SCORES_JSON,
    ):
        result = analyze_pillar(
            pillar="Market",
            company_text=COMPANY_TEXT,
            result_model=MarketAnalysisResult,
        )

    breakdown = result.score_breakdown
    by_name = {s.name: s for s in breakdown.subscores}

    expect(len(breakdown.subscores) == 5, f"Expected 5 subscores, got {len(breakdown.subscores)}")

    expect(by_name["Market Size"].score == 7.0, "Market Size score mismatch")
    expect(by_name["Market Size"].weight == 0.25, "Market Size weight must come from config (0.25)")
    expect(by_name["Market Growth"].signals == ["33% YoY growth"], "Signals not carried through")
    expect(
        not any(s.evidence_corrected or s.score_corrected for s in breakdown.subscores),
        "No correction should have occurred on clean responses.",
    )
    expect(breakdown.score is not None, "Pillar score should be computed")


def test_evidence_extraction_direct() -> None:
    """extract_pillar_evidence() in isolation, verifying it hands back a
    PillarEvidenceAnalysis with no scores and the narrative fields
    separately."""
    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        return_value=INITIAL_EVIDENCE_JSON,
    ):
        pillar_evidence, narrative_fields, corrected = extract_pillar_evidence(
            pillar="Market",
            company_text=COMPANY_TEXT,
            system_content="test",
        )

    expect(len(pillar_evidence.dimensions) == 5, "Expected 5 dimensions")
    expect(corrected == set(), "No correction should have occurred")
    expect(narrative_fields.get("stage_hint") == "Series A", "stage_hint not parsed")
    expect("summary" in narrative_fields, "summary missing from narrative fields")


# Genuinely malformed JSON (missing a comma) -- not the "extra text
# surrounding valid JSON" case parse_json_from_response's regex fallback
# already handles, but a real json.JSONDecodeError.
MALFORMED_JSON = '{"summary": "ok" "confidence": "Medium", "dimensions": []}'


def test_malformed_json_response_retried_then_recovers() -> None:
    """Robustness fix (post-implementation review, discovered via a live
    end-to-end run): a genuinely malformed first response must trigger one
    corrective retry, not crash the pillar outright."""
    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        side_effect=[MALFORMED_JSON, INITIAL_EVIDENCE_JSON],
    ):
        pillar_evidence, narrative_fields, corrected = extract_pillar_evidence(
            pillar="Market",
            company_text=COMPANY_TEXT,
            system_content="test",
        )

    expect(len(pillar_evidence.dimensions) == 5, "Retry should recover the full 5-dimension response")
    expect(narrative_fields.get("stage_hint") == "Series A", "Recovered response's narrative fields should parse normally")


def test_malformed_json_response_degrades_without_crashing_when_retry_also_fails() -> None:
    """If the corrective retry ALSO fails to parse, the pillar must degrade
    to an all-Unavailable placeholder (never fabricate evidence, never
    crash the whole analysis) -- the same fail-closed posture Blocker 1
    established for missing structured_facts, extended to a raw JSON parse
    failure."""
    with patch(
        "app.ai.evidence_extraction.call_analysis_model",
        side_effect=[MALFORMED_JSON, MALFORMED_JSON],
    ):
        pillar_evidence, narrative_fields, corrected = extract_pillar_evidence(
            pillar="Market",
            company_text=COMPANY_TEXT,
            system_content="test",
        )

    expect(len(pillar_evidence.dimensions) == 5, f"All 5 Market dimensions should still be present as placeholders, got {len(pillar_evidence.dimensions)}")
    expect(
        all(d.evidence_status == "Unavailable" for d in pillar_evidence.dimensions),
        "Every dimension must degrade to Unavailable, never a fabricated score/evidence",
    )
    expect(narrative_fields == {}, "Narrative fields must be empty, not fabricated, when both parse attempts fail")


TESTS = [
    test_evidence_analysis_model_has_no_score_field,
    test_scoring_prompt_never_contains_raw_company_text,
    test_identical_normalized_evidence_reused_independently,
    test_unavailable_evidence_never_sent_to_scorer,
    test_full_pipeline_end_to_end_with_mocked_calls,
    test_evidence_extraction_direct,
    test_malformed_json_response_retried_then_recovers,
    test_malformed_json_response_degrades_without_crashing_when_retry_also_fails,
]


def main() -> None:
    print("\nSIE evidence/scoring pipeline tests")
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
