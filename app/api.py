from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from database.db import (create_tables, 
                         save_analysis, 
                         get_analyses, 
                         get_analysis_by_id, 
                         delete_analysis,
                         update_analysis,
                         search_analyses,
                         add_scoring_columns,
                         add_analysis_columns,
                         get_analytics,
                         add_benchmarking_columns,
                         get_industry_analytics
)

from models.startup import StartupAnalysisRequest, StartupAnalysisResponse, UpdateAnalysisRequest, WebsiteAnalysisRequest
from workflows.due_diligence_workflow import run_due_diligence
import json
from pdf_extractor import extract_text_from_pdf
from website_scrapper import extract_text_from_website
from reporting.pdf_generator import generate_pdf_report

app = FastAPI()

print("RUNNING API.PY MIGRATIONS")

create_tables()
add_analysis_columns()
add_scoring_columns()


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

@app.get("/analyses/search")
def search_saved_analyses(query: str):
    return search_analyses(query)

@app.get("/analyses/{analysis_id}")
def get_saved_analysis(analysis_id: int):
    analysis = get_analysis_by_id(analysis_id)

    if analysis is None:
        return {"error": "Analysis not found"}
    
    return analysis


@app.get("/analyses/{analysis_id}/pdf")
def download_analysis_pdf(analysis_id: int):
    analysis = get_analysis_by_id(analysis_id)

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    pdf_path = generate_pdf_report(analysis)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.split("/")[-1],
    )

@app.get("/analytics")
def analytics():
    return get_analytics()

@app.get("/analytics/industries")
def industry_analytics():
    return get_industry_analytics()

@app.put("/analyses/{analysis_id}")
def update_saved_analysis(
    analysis_id: int,
    request: UpdateAnalysisRequest
):
    updated_count = update_analysis(
        analysis_id,
        request.company_text,
        request.summary,
        request.risk_analysis,
        request.competitor_analysis,
        request.memo,
        request.structured_analysis,
        request.investment_score,
        request.founder_analysis,
        request.market_analysis,
        request.sources,
        request.traction_analysis
    )

    if updated_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    return {
        "message": "Analysis updated successfully"
    }

@app.delete("/analyses/{analysis_id}")
def delete_saved_analysis(analysis_id: int):
    deleted_count = delete_analysis(analysis_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    return {
        "message": "Analysis deleted successfully"
    }

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
        competitor_analysis=results["competitor_analysis"],
        memo=results["memo"],
        structured_analysis=results["structured_analysis"],
        investment_score=results["investment_score"],
        founder_analysis=results["founder_analysis"],
        market_analysis=results["market_analysis"],
        sources=results["sources"],
        traction_analysis=results["traction_analysis"],
        market_score=results["market_score"],
        team_score=results["team_score"],
        product_score=results["product_score"],
        competition_score=results["competition_score"],
        traction_score=results["traction_score"],
        financial_score=results["financial_score"],
        overall_score=results["overall_score"],
        recommendation=results["recommendation"]
                
    )
    
    return {
        "summary": results["summary"],
        "risk_analysis": results["risk_analysis"],
        "competitor_analysis": results["competitor_analysis"],
        "memo": results["memo"],
        "structured_analysis":results["structured_analysis"],
        "investment_score": results["investment_score"],
        "founder_analysis": results["founder_analysis"],
        "market_analysis": results["market_analysis"],
        "sources": results["sources"],
        "traction_analysis": results["traction_analysis"],
        "market_score": results["market_score"],
        "team_score": results["team_score"],
        "product_score": results["product_score"],
        "competition_score": results["competition_score"],
        "traction_score": results["traction_score"],
        "financial_score": results["financial_score"],
        "overall_score": results["overall_score"],
        "recommendation": results["recommendation"]
    }


@app.post("/analyze-pdf", response_model=StartupAnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await file.read()
        extracted_text = extract_text_from_pdf(pdf_bytes)

        results = run_due_diligence(extracted_text)

        save_analysis(
            company_text=extracted_text,
            summary=results["summary"],
            risk_analysis=results["risk_analysis"],
            competitor_analysis=results["competitor_analysis"],
            memo=results["memo"],
            structured_analysis=results["structured_analysis"],
            investment_score=results["investment_score"],
            founder_analysis=results["founder_analysis"],
            market_analysis=results["market_analysis"],
            sources=results["sources"],
            traction_analysis=results["traction_analysis"],
            market_score=results["market_score"],
            team_score=results["team_score"],
            product_score=results["product_score"],
            competition_score=results["competition_score"],
            traction_score=results["traction_score"],
            financial_score=results["financial_score"],
            overall_score=results["overall_score"],
            recommendation=results["recommendation"]
            
        )

        return {
            "summary": results["summary"],
            "risk_analysis": results["risk_analysis"],
            "competitor_analysis": results["competitor_analysis"],
            "memo": results["memo"],
            "structured_analysis": results["structured_analysis"],
            "investment_score": results["investment_score"],
            "founder_analysis": results["founder_analysis"],
            "market_analysis": results["market_analysis"],
            "sources": results["sources"],
            "traction_analysis": results["traction_analysis"],
            "market_score": results["market_score"],
            "team_score": results["team_score"],
            "product_score": results["product_score"],
            "competition_score": results["competition_score"],
            "traction_score": results["traction_score"],
            "financial_score": results["financial_score"],
            "overall_score": results["overall_score"],
            "recommendation": results["recommendation"]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.post("/analyze-website", response_model=StartupAnalysisResponse)
def analyze_website(request: WebsiteAnalysisRequest):

    website_text = extract_text_from_website(request.url)

    results = run_due_diligence(website_text)

    save_analysis(
        company_text=request.url,
        summary=results["summary"],
        risk_analysis=results["risk_analysis"],
        competitor_analysis=results["competitor_analysis"],
        memo=results["memo"],
        structured_analysis=results["structured_analysis"],
        investment_score=results["investment_score"],
        founder_analysis=results["founder_analysis"],
        market_analysis=results["market_analysis"],
        sources=results["sources"],
        traction_analysis=results["traction_analysis"],
        market_score=results["market_score"],
        team_score=results["team_score"],
        product_score=results["product_score"],
        competition_score=results["competition_score"],
        traction_score=results["traction_score"],
        financial_score=results["financial_score"],
        overall_score=results["overall_score"],
        recommendation=results["recommendation"]
                
    )

    return {
        "summary": results["summary"],
        "risk_analysis": results["risk_analysis"],
        "competitor_analysis": results["competitor_analysis"],
        "memo": results["memo"],
        "structured_analysis": results["structured_analysis"],
        "investment_score": results["investment_score"],
        "founder_analysis": results["founder_analysis"],
        "market_analysis": results["market_analysis"],
        "sources": results["sources"],
        "traction_analysis": results["traction_analysis"],
        "market_score": results["market_score"],
        "team_score": results["team_score"],
        "product_score": results["product_score"],
        "competition_score": results["competition_score"],
        "traction_score": results["traction_score"],
        "financial_score": results["financial_score"],
        "overall_score": results["overall_score"],
        "recommendation": results["recommendation"]
    }

@app.post("/migrate/add-benchmarking-columns")
def migrate_add_benchmarking_columns():
    add_benchmarking_columns()
    return {"message": "Benchmarking columns migration completed"}