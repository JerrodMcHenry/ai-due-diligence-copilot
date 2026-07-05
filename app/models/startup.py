from pydantic import BaseModel, Field
from typing import Literal
from models.scoring import StartupIntelligenceScore, PillarScoreBreakdown

class StartupAnalysisRequest(BaseModel):
    company_text: str
    

class PillarAnalysis(BaseModel):
    score: float | None = None
    confidence: Literal["Low", "Medium", "High"] | None = None
    summary: str | None = None
    evidence: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    score_breakdown: PillarScoreBreakdown | None = None


class SIEContext(BaseModel):
    company_name: str | None = None
    industry: str | None = None
    business_model: str | None = None
    company_stage: str | None = None
    funding_stage: str | None = None


class SIEMethodologyAnalysis(BaseModel):
    context: SIEContext | None = None
    market: PillarAnalysis | None = None
    team: PillarAnalysis | None = None
    product: PillarAnalysis | None = None
    execution: PillarAnalysis | None = None
    traction: PillarAnalysis | None = None
    financial_health: PillarAnalysis | None = None
    startup_intelligence_score: float | None = None
    startup_scorecard: StartupIntelligenceScore | None = None
    milestone_readiness_score: float | None = None
    momentum_score: float | None = None
    confidence_score: float | None = None
    executive_coaching_summary: str | None = None
    next_actions: list[str] = Field(default_factory=list)


class StartupAnalysisResponse(BaseModel):
    summary: str
    risk_analysis: str
    competitor_analysis: str
    memo: str
    structured_analysis: dict
    investment_score: dict
    founder_analysis: dict
    market_analysis: dict
    sources: list = Field(default_factory=list)
    traction_analysis: dict
    

    market_score: int | None = None
    team_score: int | None = None
    product_score: int | None = None
    competition_score: int | None = None
    traction_score: int | None = None
    financial_score: int | None = None
    overall_score: int | None = None
    recommendation: str | None = None
    readiness: dict | None = None
    readiness_score: int | None = None
    readiness_summary: str | None = None
    sie_analysis: SIEMethodologyAnalysis | None = None

class UpdateAnalysisRequest(BaseModel):
    summary: str
    risk_analysis: str
    competitor_analysis: str
    memo: str
    structured_analysis: dict
    investment_score: dict
    founder_analysis: dict
    market_analysis: dict
    sources: list = []
    traction_analysis: dict

    market_score: int | None = None
    team_score: int | None = None
    product_score: int | None = None
    competition_score: int | None = None
    traction_score: int | None = None
    financial_score: int | None = None
    overall_score: int | None = None
    recommendation: str | None = None
    readiness: dict | None = None
    readiness_score: int | None = None
    readiness_summary: str | None = None
    sie_analysis: SIEMethodologyAnalysis | None = None

class WebsiteAnalysisRequest(BaseModel):
    url: str