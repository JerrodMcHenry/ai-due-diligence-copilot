from pydantic import BaseModel, Field
from typing import Literal

from models.scoring import PillarScoreBreakdown
from models.evidence import Evidence


ConfidenceLevel = Literal["Low", "Medium", "High"]


class AnalysisResult(BaseModel):
    summary: str = ""
    confidence: ConfidenceLevel = "Low"

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    evidence: list[Evidence | str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    score_breakdown: PillarScoreBreakdown = Field(default_factory=PillarScoreBreakdown)


class MarketAnalysisResult(AnalysisResult):
    tam: str = ""
    sam: str = ""
    som: str = ""
    growth_rate: str = ""


class FounderAnalysisResult(AnalysisResult):
    founder_market_fit: str = ""
    fundraising_signal: str = ""


class TractionAnalysisResult(AnalysisResult):
    customer_growth: str = ""
    revenue_growth: str = ""
    fundraising_signal: str = ""


class ProductAnalysisResult(AnalysisResult):
    customer_value: str = ""
    technical_defensibility: str = ""
    ease_of_adoption: str = ""
    product_maturity: str = ""


class ExecutionAnalysisResult(AnalysisResult):
    gtm_execution: str = ""
    product_execution: str = ""
    operational_execution: str = ""
    strategic_execution: str = ""


class FinancialAnalysisResult(AnalysisResult):
    revenue_quality: str = ""
    pricing_model: str = ""
    unit_economics: str = ""
    burn_rate: str = ""
    runway: str = ""
    capital_efficiency: str = ""
    fundraising_readiness: str = ""