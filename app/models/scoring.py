from typing import Literal

from pydantic import BaseModel, Field


ConfidenceLevel = Literal["Low", "Medium", "High"]

EvidenceStatus = Literal[
    "Observed",
    "Inferred",
    "Unavailable",
]


class Subscore(BaseModel):
    name: str = ""

    # None means the dimension could not be responsibly scored.
    score: float | None = None

    weight: float = 0.0

    confidence: ConfidenceLevel = "Low"

    evidence_status: EvidenceStatus = "Observed"

    rationale: str = ""

    evidence: list[str] = Field(default_factory=list)

    recommendations: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(default_factory=list)

    # --- Evidence/Scoring Separation sprint additions ---
    #
    # Structured facts distinct from quoted `evidence` -- e.g. a short
    # normalized signal like "MRR grew $18K to $61K" rather than a full
    # quoted sentence. Populated by the evidence-extraction stage
    # (app/ai/evidence_extraction.py), carried through unchanged by the
    # scoring stage. Empty for analyses produced before this field
    # existed -- never backfilled.
    signals: list[str] = Field(default_factory=list)

    # Diagnostics, not methodology: whether this dimension's evidence
    # assessment or numeric score required a scoped correction pass
    # (app/ai/analyze_pillar.py). Never affects scoring or aggregation --
    # purely for explainability/observability. False for analyses
    # produced before this field existed.
    evidence_corrected: bool = False
    score_corrected: bool = False

    # SIE Methodology v2 Part 4 (evidence-semantics wiring, post-
    # implementation review): WHICH of the nine canonical missing-evidence
    # states applies, populated only when evidence_status == "Unavailable"
    # (see app.ai.sie_v2_evidence_semantics.MissingEvidenceState). This is
    # purely additive REPORTING granularity layered on top of the existing,
    # unchanged 3-state (Observed/Inferred/Unavailable) arithmetic -- it
    # never changes whether a dimension is excluded from the scored set,
    # only records WHY. None for every Subscore produced before this field
    # existed, and for every Observed/Inferred Subscore -- never backfilled,
    # never required.
    missing_evidence_state: str | None = None


class PillarScoreBreakdown(BaseModel):
    pillar: str = ""

    # None means no dimensions in the pillar were scorable.
    score: float | None = None

    confidence: ConfidenceLevel = "Low"

    # Percentage of configured pillar weight supported by
    # observed or inferred evidence.
    evidence_coverage: float = 0.0

    scoring_summary: str = ""

    subscores: list[Subscore] = Field(default_factory=list)


class StartupIntelligenceScore(BaseModel):
    overall_score: float | None = None

    recommendation: str = ""

    market: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="market"
        )
    )

    team: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="team"
        )
    )

    product: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="product"
        )
    )

    execution: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="execution"
        )
    )

    traction: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="traction"
        )
    )

    financial_health: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(
            pillar="financial_health"
        )
    )