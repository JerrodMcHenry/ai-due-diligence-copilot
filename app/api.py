from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import (create_tables,
                         create_score_history_table, 
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
                         get_industry_analytics,
                         get_rankings,
                         add_company_name_column,
                         add_readiness_columns,
                         save_score_history,
                         get_score_history,
                         get_startup_trends,
                         get_top_startups,
                         get_top_improving_startups,
                         get_startup_by_name,
                         add_methodology_column,
                         get_sps_history
)

from app.models.startup import StartupAnalysisRequest, StartupAnalysisResponse, StartupProfileResponse, UpdateAnalysisRequest, WebsiteAnalysisRequest
from app.workflows.due_diligence_workflow import run_due_diligence
from app.ai.sie_v2_methodology import METHODOLOGY_VERSION
import json
import os
import traceback
from app.pdf_extractor import extract_text_from_pdf
from app.website_scrapper import extract_text_from_website
from app.reporting.pdf_generator import generate_pdf_report

app = FastAPI()

# Staging Deployment Preparation: local development origins are preserved
# as the default (identical behavior to before, when CORS_ALLOWED_ORIGINS
# is unset), while a deployed backend sets CORS_ALLOWED_ORIGINS to the
# real, deployed frontend origin(s) -- comma-separated, e.g.
# "https://sie-staging.vercel.app,https://app.example.com" -- so the
# origin list never has to be hardcoded or committed here, and never
# widens to a wildcard.
_LOCAL_DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _resolve_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or _LOCAL_DEV_CORS_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("RUNNING API.PY MIGRATIONS")

create_tables()
add_analysis_columns()
add_scoring_columns()
add_benchmarking_columns()
add_company_name_column()
add_readiness_columns()
add_methodology_column()
create_score_history_table()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/version")
def version():
    return {
        "app": "AI Due Diligence Copilot",
        "version": "1.0",
        # P0 Product Trust Cleanup: additive field only -- "version" above
        # is the app version and is left untouched (out of this cleanup's
        # scope). methodology_version reuses the same constant the backend
        # stamps onto every new canonical analysis
        # (app/ai/sie_v2_methodology.py), so the frontend has one safe,
        # already-correct source instead of a second hardcoded string.
        "methodology_version": METHODOLOGY_VERSION,
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

@app.get("/rankings")
def rankings():
    return get_rankings()

@app.get("/score-history/{company_name}")
def score_history(company_name: str):
    return get_score_history(company_name)

@app.get("/startup-trends/{company_name}")
def startup_trends(company_name: str):
    return get_startup_trends(company_name)

@app.get("/top-startups")
def top_startups(limit: int = 10):
    return get_top_startups(limit)

@app.get("/top-improving-startups")
def top_improving_startups(limit: int = 10):
    return get_top_improving_startups(limit)

@app.get(
    "/startup/{company_name}",
    response_model=StartupProfileResponse,
)
def get_startup_profile(company_name: str):
    startup = get_startup_by_name(company_name)

    if startup is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No canonical startup profile was found. "
                "The startup may need to be analyzed again."
            ),
        )

    return StartupProfileResponse(**startup)

@app.get("/startup/{company_name}/sps-history")
def get_startup_sps_history(company_name: str):
    return get_sps_history(company_name)

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
    # MVP hardening: this call is the one place a real user actually hits
    # this endpoint today (the frontend Analyze Startup page). It runs a
    # 3-5 minute pipeline with no internal retry-exhaustion boundary of its
    # own -- an OpenAI/Tavily outage, a genuinely malformed LLM response
    # that survives the pipeline's own single correction pass, or any
    # other unexpected failure previously propagated as a bare, unhandled
    # exception: FastAPI's default handler turns that into a generic 500
    # with no body detail, which is fine for not leaking internals, but
    # gives the user no honest explanation and (via app/analyze-pdf's
    # existing str(e) pattern nearby) it's easy to accidentally leak an
    # internal exception message here instead. Logging server-side and
    # raising a clean, non-leaking HTTPException keeps this endpoint
    # consistent with how every other error path in this file already
    # behaves (e.g. the 404s below), which the frontend already handles.
    try:
        results = run_due_diligence(request.company_text)
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=(
                "The analysis could not be completed. This can happen if a "
                "research or AI provider is temporarily unavailable. Please "
                "try again."
            ),
        )

    try:
        analysis_id = save_analysis(
            company_text=request.company_text,
            summary=results["summary"],
            risk_analysis=results["risk_analysis"],
            competitor_analysis=results["competitor_analysis"],
            memo=results["memo"],
            structured_analysis=results["structured_analysis"],
            investment_score=results["investment_score"],
            founder_analysis=results["founder_analysis"].model_dump(),
            market_analysis=results["market_analysis"].model_dump(),
            sources=results["sources"],
            traction_analysis=results["traction_analysis"].model_dump(),
            methodology=results["sie_analysis"].model_dump(mode="json"),
            market_score=results["market_score"],
            team_score=results["team_score"],
            product_score=results["product_score"],
            competition_score=results["competition_score"],
            traction_score=results["traction_score"],
            financial_score=results["financial_score"],
            overall_score=results["overall_score"],
            recommendation=results["recommendation"],
            readiness_score=results["readiness_score"],
            readiness_summary=results["readiness_summary"],

        )
        structured_analysis = results["structured_analysis"]

        save_score_history(
            analysis_id=analysis_id,
            company_name=structured_analysis.get("company_name"),
            industry=structured_analysis.get("industry"),
            stage=structured_analysis.get("stage"),
            business_model=structured_analysis.get("business_model"),
            market_score=results["market_score"],
            team_score=results["team_score"],
            product_score=results["product_score"],
            competition_score=results["competition_score"],
            traction_score=results["traction_score"],
            financial_score=results["financial_score"],
            overall_score=results["overall_score"],
            readiness_score=results["readiness_score"]
        )
    except Exception:
        # Distinct from the pipeline failure above on purpose: the
        # (expensive, multi-minute) analysis DID complete here -- only
        # persisting it failed. Telling the user that honestly matters:
        # retrying means re-running the whole pipeline, not just re-saving.
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=(
                "The analysis completed but could not be saved. Please try "
                "again."
            ),
        )

    sie_analysis = results["sie_analysis"]

    return StartupAnalysisResponse(
        context=sie_analysis.context,
        startup_scorecard=sie_analysis.startup_scorecard,
        methodology=sie_analysis,
    )
        
    


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
            founder_analysis=results["founder_analysis"].model_dump(),
            market_analysis=results["market_analysis"].model_dump(),
            sources=results["sources"],
            traction_analysis=results["traction_analysis"].model_dump(),
            methodology=results["sie_analysis"].model_dump(mode="json"),
            market_score=results["market_score"],
            team_score=results["team_score"],
            product_score=results["product_score"],
            competition_score=results["competition_score"],
            traction_score=results["traction_score"],
            financial_score=results["financial_score"],
            overall_score=results["overall_score"],
            recommendation=results["recommendation"],
            readiness_score=results["readiness_score"],
            readiness_summary=results["readiness_summary"]

            
            
        )

        sie_analysis = results["sie_analysis"]

        return StartupAnalysisResponse(
        context=sie_analysis.context,
        startup_scorecard=sie_analysis.startup_scorecard,
        methodology=sie_analysis,
)
        

    except ValueError as e:
        # ValueError here is always one of pdf_extractor.py's own
        # deliberate, controlled messages (e.g. "No readable text found in
        # PDF.") -- safe to show as-is, unlike the generic branch below.
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        # Staging Deployment Preparation: this previously returned
        # str(e) directly -- safe to overlook while the endpoint was only
        # ever reachable from a local dev server, but staging exposes this
        # backend publicly even though the frontend doesn't call this
        # endpoint yet. str(e) here could be an OpenAI/DB/PDF-library
        # internal error message, not one of our own controlled strings.
        # Same fail-closed pattern as /analyze-startup: log server-side,
        # never leak the raw exception to the client.
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=(
                "The analysis could not be completed. Please try again."
            ),
        )




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
        founder_analysis=results["founder_analysis"].model_dump(),
        market_analysis=results["market_analysis"].model_dump(),
        sources=results["sources"],
        traction_analysis=results["traction_analysis"].model_dump(),
        methodology=results["sie_analysis"].model_dump(mode="json"),
        market_score=results["market_score"],
        team_score=results["team_score"],
        product_score=results["product_score"],
        competition_score=results["competition_score"],
        traction_score=results["traction_score"],
        financial_score=results["financial_score"],
        overall_score=results["overall_score"],
        recommendation=results["recommendation"],
        readiness_score=results["readiness_score"],
        readiness_summary=results["readiness_summary"]
                
    )

    sie_analysis = results["sie_analysis"]

    return StartupAnalysisResponse(
        context=sie_analysis.context,
        startup_scorecard=sie_analysis.startup_scorecard,
        methodology=sie_analysis,
    )

@app.post("/migrate/add-benchmarking-columns")
def migrate_add_benchmarking_columns():
    add_benchmarking_columns()
    return {"message": "Benchmarking columns migration completed"}

@app.post("/migrate/add-company-name-column")
def migrate_add_company_name_column():
    add_company_name_column()
    return {"message": "Company name column migration completed"}

@app.post("/migrate/add-readiness-columns")
def migrate_add_readiness_columns():
    add_readiness_columns()
    return {"message": "Readiness columns migration completed"}