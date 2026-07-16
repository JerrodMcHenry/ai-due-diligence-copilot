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