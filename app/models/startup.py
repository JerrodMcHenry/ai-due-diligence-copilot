from pydantic import BaseModel

class StartupAnalysisRequest(BaseModel):
    company_text: str
    

class StartupAnalysisResponse(BaseModel):
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

class WebsiteAnalysisRequest(BaseModel):
    url: str