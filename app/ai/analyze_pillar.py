"""
Orchestrator for the two-stage pillar pipeline (SIE Evidence/Scoring
Separation sprint):

    enriched_text
        |
        v
    Evidence Analysis   (app/ai/evidence_extraction.py -- no score)
        |
        v
    Scoring             (app/ai/pillar_scoring.py -- judges the
        |                 normalized evidence, never rediscovers it)
        v
    PillarAnalysis

analyze_pillar()'s public signature and return type are UNCHANGED from
before this sprint -- the six pillar wrappers (market_analysis.py,
founder_analysis.py, etc.) and everything downstream of them
(due_diligence_workflow.py, the reliability harness) call it exactly as
before and get back the same result_model instance shape. Only the
internal implementation is now two calls instead of one, with
per-dimension scoped correction instead of whole-pillar correction.
"""

from app.ai.scoring import finalize_pillar_score, get_scoring_dimensions
from app.ai.evidence_extraction import extract_pillar_evidence
from app.ai.pillar_scoring import score_pillar_evidence
from app.models.scoring import PillarScoreBreakdown, Subscore

from app.ai.pillar_shared import (  # noqa: F401 -- re-exported for backward compatibility
    PILLAR_ANALYSIS_MODEL,
    PILLAR_PROMPT_VERSION,
    QUANTITATIVE_DISCLOSURE_TERMS,
    get_methodology_by_name,
)


DEFAULT_SYSTEM_MESSAGE = (
    "You are a General Partner at a top-tier venture capital firm. "
    "You evaluate intrinsic startup quality, not pitch quality. "
    "You do not use hindsight during historical calibration. "
    "Return only valid JSON."
)


def print_raw_subscores(pillar: str, score_breakdown: PillarScoreBreakdown) -> None:
    """Temporary calibration logging."""
    print("\n" + "=" * 70)
    print(f"{pillar.upper()} RAW SUBSCORES")
    print("=" * 70)

    for subscore in score_breakdown.subscores:
        corrected = ""
        if subscore.evidence_corrected or subscore.score_corrected:
            tags = []
            if subscore.evidence_corrected:
                tags.append("evidence-corrected")
            if subscore.score_corrected:
                tags.append("score-corrected")
            corrected = f" [{', '.join(tags)}]"

        print(
            f"{subscore.name:<30}"
            f" Score: {str(subscore.score):<5}"
            f" | Evidence: {subscore.evidence_status:<11}"
            f" | Confidence: {subscore.confidence}"
            f"{corrected}"
        )

    print("=" * 70 + "\n")


def build_subscores(
    pillar: str,
    pillar_evidence,
    scores: dict[str, tuple[float, str]],
    evidence_corrected_names: set[str],
    score_corrected_names: set[str],
) -> list[Subscore]:
    """
    Merge stage 1 (evidence) and stage 2 (score) into the final Subscore
    list the rest of the system already understands. Weight comes from
    the canonical per-dimension config (app/ai/scoring_methodology.py),
    never from the model.
    """
    weights_by_name = dict(get_scoring_dimensions(pillar))

    subscores: list[Subscore] = []

    for dim in pillar_evidence.dimensions:
        score, scoring_rationale = scores.get(dim.dimension, (None, ""))

        # Combine the evidence-classification rationale with the
        # scoring-stage rationale so the final Subscore.rationale reads
        # as one coherent explanation, while the two stages' reasoning
        # remains separately inspectable via evidence_analysis if a
        # caller wants it (see the reliability harness, Phase 6).
        if dim.evidence_status == "Unavailable":
            rationale = dim.rationale
        elif scoring_rationale:
            rationale = scoring_rationale
        else:
            rationale = dim.rationale

        subscores.append(
            Subscore(
                name=dim.dimension,
                score=score,
                weight=weights_by_name.get(dim.dimension, 0.0),
                confidence=dim.confidence,
                evidence_status=dim.evidence_status,
                rationale=rationale,
                evidence=dim.evidence,
                recommendations=dim.recommendations,
                missing_information=dim.missing_information,
                signals=dim.signals,
                evidence_corrected=dim.dimension in evidence_corrected_names,
                score_corrected=dim.dimension in score_corrected_names,
            )
        )

    return subscores


def analyze_pillar(
    pillar: str,
    company_text: str,
    result_model,
    system_message: str | None = None,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
):
    system_content = system_message or DEFAULT_SYSTEM_MESSAGE

    pillar_evidence, narrative_fields, evidence_corrected_names = (
        extract_pillar_evidence(
            pillar=pillar,
            company_text=company_text,
            system_content=system_content,
            extra_fields=extra_fields,
            extra_rules=extra_rules,
        )
    )

    # Stage-aware scoring guidance without re-sending the raw corpus:
    # the evidence stage already read the full text and can name the
    # stage as a short fact; nothing else about the raw text crosses
    # into the scoring stage. Popped before constructing result_model
    # since it isn't one of that model's fields.
    stage_hint = narrative_fields.pop("stage_hint", "") or ""

    scores, score_corrected_names = score_pillar_evidence(
        pillar=pillar,
        pillar_evidence=pillar_evidence,
        system_content=system_content,
        stage=stage_hint,
    )

    subscores = build_subscores(
        pillar=pillar,
        pillar_evidence=pillar_evidence,
        scores=scores,
        evidence_corrected_names=evidence_corrected_names,
        score_corrected_names=score_corrected_names,
    )

    score_breakdown = PillarScoreBreakdown(pillar=pillar, subscores=subscores)
    score_breakdown = finalize_pillar_score(score_breakdown)

    print_raw_subscores(pillar=pillar, score_breakdown=score_breakdown)

    result_data = dict(narrative_fields)
    result_data["score_breakdown"] = score_breakdown

    return result_model(**result_data)
