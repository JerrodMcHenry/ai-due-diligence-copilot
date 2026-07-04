from pydantic import BaseModel, Field
from typing import Literal


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


class MarketAnalysisResult(AnalysisResult):
    tam: str | None = None
    sam: str | None = None
    som: str | None = None
    growth_rate: str | None = None


class FounderAnalysisResult(AnalysisResult):
    founder_market_fit: str | None = None
    fundraising_signal: str | None = None


class TractionAnalysisResult(AnalysisResult):
    customer_growth: str | None = None
    revenue_growth: str | None = None
    fundraising_signal: str | None = None