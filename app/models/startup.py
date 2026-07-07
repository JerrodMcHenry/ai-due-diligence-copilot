from pydantic import BaseModel, Field
from typing import Literal

from models.scoring import StartupIntelligenceScore, PillarScoreBreakdown
from models.evidence import Evidence


ConfidenceLevel = Literal["Low", "Medium", "High"]


class StartupAnalysisRequest(BaseModel):
    company_text: str


class WebsiteAnalysisRequest(BaseModel):
    url: str


class PillarAnalysis(BaseModel):
    score: float = 0.0
    confidence: ConfidenceLevel = "Low"
    summary: str = ""
    evidence: list[Evidence | str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    score_breakdown: PillarScoreBreakdown = Field(default_factory=PillarScoreBreakdown)


class SIEContext(BaseModel):
    company_name: str = ""
    industry: str = ""
    business_model: str = ""
    company_stage: str = ""
    funding_stage: str = ""


class SIEMethodologyAnalysis(BaseModel):
    context: SIEContext = Field(default_factory=SIEContext)

    market: PillarAnalysis = Field(default_factory=PillarAnalysis)
    team: PillarAnalysis = Field(default_factory=PillarAnalysis)
    product: PillarAnalysis = Field(default_factory=PillarAnalysis)
    execution: PillarAnalysis = Field(default_factory=PillarAnalysis)
    traction: PillarAnalysis = Field(default_factory=PillarAnalysis)
    financial_health: PillarAnalysis = Field(default_factory=PillarAnalysis)

    startup_intelligence_score: float = 0.0
    startup_scorecard: StartupIntelligenceScore = Field(default_factory=StartupIntelligenceScore)

    milestone_readiness_score: float = 0.0
    momentum_score: float = 0.0
    confidence_score: float = 0.0

    executive_coaching_summary: str = ""
    next_actions: list[str] = Field(default_factory=list)


class StartupAnalysisResponse(BaseModel):
    context: SIEContext = Field(default_factory=SIEContext)
    startup_scorecard: StartupIntelligenceScore = Field(default_factory=StartupIntelligenceScore)
    methodology: SIEMethodologyAnalysis = Field(default_factory=SIEMethodologyAnalysis)


class UpdateAnalysisRequest(BaseModel):
    methodology: SIEMethodologyAnalysis