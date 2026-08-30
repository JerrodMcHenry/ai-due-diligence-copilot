from app.models.scoring import PillarScoreBreakdown, Subscore
from app.ai.scoring_methodology import SCORING_METHODOLOGY


# SIE Methodology v2: SIE_SCORING_CONFIG (name+weight only) used to be a
# second, independently-maintained copy of the same 28/30 dimension names
# and weights already defined in SCORING_METHODOLOGY (scoring_methodology.py).
# The two had no mechanism forcing them to stay in sync. get_scoring_dimensions()
# now derives its (name, weight) tuples from SCORING_METHODOLOGY directly --
# one authoritative source (SIE_Methodology_v2_Specification.md Part 2 gap
# analysis, Phase 2) -- rather than maintaining a duplicate dict here.
#
# MARKET_SUBSCORES etc. below are kept only because older code may still
# import them by name; they are computed from the same single source, not a
# second definition of it.

def get_scoring_dimensions(
    pillar: str,
) -> list[tuple[str, float]]:
    return [(d.name, d.weight) for d in SCORING_METHODOLOGY[pillar]]


MARKET_SUBSCORES = get_scoring_dimensions("Market")
TEAM_SUBSCORES = get_scoring_dimensions("Team")
PRODUCT_SUBSCORES = get_scoring_dimensions("Product")
EXECUTION_SUBSCORES = get_scoring_dimensions("Execution")
TRACTION_SUBSCORES = get_scoring_dimensions("Traction")
FINANCIAL_SUBSCORES = get_scoring_dimensions("Financial Health")


def calculate_weighted_score(
    subscores: list[Subscore],
) -> float | None:
    scorable_subscores = [
        subscore
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    ]

    if not scorable_subscores:
        return None

    total_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
    )

    if total_weight <= 0:
        return None

    weighted_score = (
        sum(
            subscore.score * subscore.weight
            for subscore in scorable_subscores
        )
        / total_weight
    )

    return round(weighted_score, 1)



CONFIDENCE_VALUES = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def calculate_pillar_confidence(
    subscores: list[Subscore],
) -> str:
    scorable_subscores = [
        subscore
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    ]

    if not scorable_subscores:
        return "Low"

    total_weight = sum(
        subscore.weight
        for subscore in subscores
    )

    covered_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
    )

    if total_weight <= 0:
        return "Low"

    coverage_ratio = covered_weight / total_weight

    weighted_confidence = sum(
        CONFIDENCE_VALUES[subscore.confidence]
        * subscore.weight
        for subscore in scorable_subscores
    ) / covered_weight

    observed_weight = sum(
        subscore.weight
        for subscore in scorable_subscores
        if subscore.evidence_status == "Observed"
    )

    observed_ratio = observed_weight / covered_weight

    if (
        coverage_ratio >= 0.80
        and weighted_confidence >= 2.4
        and observed_ratio >= 0.40
    ):
        return "High"

    if (
        coverage_ratio >= 0.40
        and weighted_confidence >= 1.6
    ):
        return "Medium"

    return "Low"




def calculate_evidence_coverage(
    subscores: list[Subscore],
) -> float:
    if not subscores:
        return 0.0

    total_weight = sum(
        subscore.weight
        for subscore in subscores
    )

    if total_weight <= 0:
        return 0.0

    covered_weight = sum(
        subscore.weight
        for subscore in subscores
        if (
            subscore.score is not None
            and subscore.evidence_status != "Unavailable"
        )
    )

    return round(
        (covered_weight / total_weight) * 100,
        1,
    )


def create_subscores(
    definitions: list[tuple[str, float]],
) -> list[Subscore]:
    return [
        Subscore(
            name=name,
            weight=weight,
        )
        for name, weight in definitions
    ]


# Methodology V2.1 (Phase 10.8B, Part 11): confidence and score quality
# answer different questions -- "how strong does this look" vs. "how
# defensible is that judgment" -- and v2.0 kept them fully independent:
# a Low-confidence, 15%-evidence-coverage Traction subscore could still
# reach 8.0 and count in the weighted average exactly like a fully-
# evidenced one. Phase 10.8's real-company validation and Phase 10.8A's
# audit found this in production data (docs/validation/
# SPS_DISCRIMINATION_AUDIT.md, Sections 10-11).
#
# This does not "multiply SPS by confidence" (explicitly rejected by
# Part 11) and does not touch dimensions that are already within their
# cap. It implements the "confidence remains separate but low-evidence
# claims cannot reach high anchors" option: a High score is still
# possible from thin evidence only up to a defensible ceiling; only
# High-confidence evidence (which already requires >=80% pillar
# coverage AND >=40% Observed-status weight, see
# calculate_pillar_confidence below) can support a 9-10 dimension score.
CONFIDENCE_SCORE_CAPS: dict[str, float] = {
    "Low": 6.0,
    "Medium": 8.5,
    "High": 10.0,
}


def apply_confidence_score_cap(
    subscores: list[Subscore],
) -> list[Subscore]:
    """
    Deterministic post-processing step: no subscore may exceed the
    defensible ceiling for its own (already-decided, Stage-1) confidence
    level. Never raises a score, never touches score=None/Unavailable
    dimensions, and never touches a score already at or below its cap.
    """
    capped: list[Subscore] = []

    for subscore in subscores:
        if subscore.score is None:
            capped.append(subscore)
            continue

        cap = CONFIDENCE_SCORE_CAPS.get(subscore.confidence, 10.0)

        if subscore.score <= cap:
            capped.append(subscore)
            continue

        capped.append(
            subscore.model_copy(
                update={
                    "score": cap,
                    "score_corrected": True,
                    "rationale": (
                        f"[Confidence cap applied -- Methodology V2.1, Part 11] "
                        f"Score reduced to {cap}, the maximum defensible score for "
                        f"{subscore.confidence}-confidence evidence. "
                        f"Original scoring rationale: {subscore.rationale}"
                    ),
                }
            )
        )

    return capped


def finalize_pillar_score(
    score_breakdown: PillarScoreBreakdown,
) -> PillarScoreBreakdown:
    score_breakdown.score = calculate_weighted_score(
        score_breakdown.subscores
    )

    score_breakdown.evidence_coverage = (
        calculate_evidence_coverage(
            score_breakdown.subscores
        )
    )

    score_breakdown.confidence = (
        calculate_pillar_confidence(
            score_breakdown.subscores
        )
    )

    return score_breakdown