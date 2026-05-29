from pydantic import BaseModel

class StartupAnalysisRequest(BaseModel):
    company_text: str