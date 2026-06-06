from pydantic import BaseModel

class StartupAnalysisRequest(BaseModel):
    company_text: str
    

class StartupAnalysisResponse(BaseModel):
    summary: str
    risk_analysis: str
    competitor_analysis: str
    memo: str
    structured_analysis: str
    investment_score: dict
    founder_analysis: dict
    market_analysis: dict

class UpdateAnalysisRequest(BaseModel):
    company_text: str
    summary: str
    risk_analysis: str
    competitor_analysis: str
    memo: str
    structured_analysis: str
    investment_score: dict
    founder_analysis: dict
    market_analysis: dict