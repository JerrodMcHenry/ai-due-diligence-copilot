from pydantic import BaseModel, Field
from typing import Literal


class Subscore(BaseModel):
    name: str

    score: float | None = None

    weight: float

    rationale: str | None = None

    evidence: list[str] = Field(default_factory=list)

    recommendations: list[str] = Field(default_factory=list)


class PillarScoreBreakdown(BaseModel):
    pillar: str

    score: float | None = None

    confidence: Literal["Low", "Medium", "High"] | None = None

    scoring_summary: str | None = None

    subscores: list[Subscore] = Field(default_factory=list)


class StartupIntelligenceScore(BaseModel):
    overall_score: float | None = None
    recommendation: str | None = None

    market: PillarScoreBreakdown | None = None
    team: PillarScoreBreakdown | None = None
    product: PillarScoreBreakdown | None = None
    execution: PillarScoreBreakdown | None = None
    traction: PillarScoreBreakdown | None = None
    financial_health: PillarScoreBreakdown | None = None