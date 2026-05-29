from fastapi import FastAPI

from models.startup import StartupAnalysisRequest, StartupAnalysisResponse
from workflows.due_diligence_workflow import run_due_diligence

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/version")
def version():
    return {
        "app": "AI Due Diligence Copilot",
        "version": "1.0"
    }

@app.get("/")
def health_check():
    return {"status": "API is running"}



@app.post(
    "/analyze-startup",
    response_model=StartupAnalysisResponse
)
def analyze_startup(request: StartupAnalysisRequest):
    results = run_due_diligence(request.company_text)
    
    return {
        "summary": results["summary"],
        "risk_analysis": results["risk_analysis"],
        "memo": results["memo"]
    }
