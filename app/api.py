from fastapi import FastAPI
from pydantic import BaseModel

from workflows.due_diligence_workflow import run_due_diligence

app = FastAPI()

class StartupAnalysisRequest(BaseModel):
    company_text: str

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "API is running"}

@app.post("/analyze-startup")
def analyze_startup(request: StartupAnalysisRequest):
    results = run_due_diligence(request.company_text)

    return results