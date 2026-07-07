from pydantic import BaseModel, Field
from typing import Literal


ConfidenceLevel = Literal["Low", "Medium", "High"]


class Subscore(BaseModel):
    name: str = ""
    score: float = 0.0
    weight: float = 0.0
    rationale: str = ""
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PillarScoreBreakdown(BaseModel):
    pillar: str = ""
    score: float = 0.0
    confidence: ConfidenceLevel = "Low"
    scoring_summary: str = ""
    subscores: list[Subscore] = Field(default_factory=list)


class StartupIntelligenceScore(BaseModel):
    overall_score: float = 0.0
    recommendation: str = ""

    market: PillarScoreBreakdown = Field(default_factory=lambda: PillarScoreBreakdown(pillar="market"))
    team: PillarScoreBreakdown = Field(default_factory=lambda: PillarScoreBreakdown(pillar="team"))
    product: PillarScoreBreakdown = Field(default_factory=lambda: PillarScoreBreakdown(pillar="product"))
    execution: PillarScoreBreakdown = Field(default_factory=lambda: PillarScoreBreakdown(pillar="execution"))
    traction: PillarScoreBreakdown = Field(default_factory=lambda: PillarScoreBreakdown(pillar="traction"))
    financial_health: PillarScoreBreakdown = Field(
        default_factory=lambda: PillarScoreBreakdown(pillar="financial_health")
    )