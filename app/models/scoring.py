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