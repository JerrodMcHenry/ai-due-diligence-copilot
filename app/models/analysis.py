from pydantic import BaseModel, Field
from typing import Literal
from models.scoring import PillarScoreBreakdown


class AnalysisResult(BaseModel):
    summary: str | None = None

    confidence: Literal[
        "Low",
        "Medium",
        "High"
    ] | None = None

    strengths: list[str] = Field(default_factory=list)

    weaknesses: list[str] = Field(default_factory=list)

    evidence: list[str] = Field(default_factory=list)

    recommendations: list[str] = Field(default_factory=list)

    score_breakdown: PillarScoreBreakdown | None = None


class MarketAnalysisResult(AnalysisResult):
    tam: str | None = None
    sam: str | None = None
    som: str | None = None
    growth_rate: str | None = None



class FounderAnalysisResult(AnalysisResult):
    score_breakdown: PillarScoreBreakdown | None = None

    founder_market_fit: str | None = None
    fundraising_signal: str | None = None


class TractionAnalysisResult(AnalysisResult):
    customer_growth: str | None = None
    revenue_growth: str | None = None
    fundraising_signal: str | None = None


class ProductAnalysisResult(AnalysisResult):
    customer_value: str | None = None
    technical_defensibility: str | None = None
    ease_of_adoption: str | None = None
    product_maturity: str | None = None

    

class ExecutionAnalysisResult(AnalysisResult):
    gtm_execution: str | None = None
    product_execution: str | None = None
    operational_execution: str | None = None
    strategic_execution: str | None = None

class FinancialAnalysisResult(AnalysisResult):
    revenue_quality: str | None = None
    pricing_model: str | None = None
    unit_economics: str | None = None
    burn_rate: str | None = None
    runway: str | None = None
    capital_efficiency: str | None = None
    fundraising_readiness: str | None = None