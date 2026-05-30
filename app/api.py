from fastapi import FastAPI
from database.db import create_tables, save_analysis, get_analyses, get_analysis_by_id

from models.startup import StartupAnalysisRequest, StartupAnalysisResponse
from workflows.due_diligence_workflow import run_due_diligence

app = FastAPI()
create_tables()

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

@app.get("/analyses")
def get_saved_analyses():
    return get_analyses()

@app.get("/analyses/{analysis_id}")
def get_saved_analysis(analysis_id: int):
    analysis = get_analysis_by_id(analysis_id)

    if analysis is None:
        return {"error": "Analysis not found"}
    
    return analysis

@app.post(
    "/analyze-startup",
    response_model=StartupAnalysisResponse
)
def analyze_startup(request: StartupAnalysisRequest):
    results = run_due_diligence(request.company_text)

    save_analysis(
        company_text=request.company_text,
        summary=results["summary"],
        risk_analysis=results["risk_analysis"],
        memo=results["memo"]
    )
    
    return {
        "summary": results["summary"],
        "risk_analysis": results["risk_analysis"],
        "memo": results["memo"]
    }
