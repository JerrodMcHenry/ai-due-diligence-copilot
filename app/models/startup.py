from pydantic import BaseModel

class StartupAnalysisRequest(BaseModel):
    company_text: str


class StartupAnalysisResponse(BaseModel):
    summary: str
    risk_analysis: str
    memo: str

class UpdateAnalysisRequest(BaseModel):
    company_text: str
    summary: str
    risk_analysis: str
    memo: str