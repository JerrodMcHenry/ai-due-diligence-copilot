from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError
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
                         get_sps_history,
                         create_startups_table,
                         add_startup_id_column,
                         create_users_table,
                         create_startup_memberships_table,
                         create_saved_startups_table,
                         backfill_startup_ids,
                         save_startup_for_user,
                         unsave_startup_for_user,
                         is_startup_saved_by_user,
                         get_saved_startups_for_user
)

from app.models.startup import StartupAnalysisRequest, StartupAnalysisResponse, StartupProfileResponse, UpdateAnalysisRequest, WebsiteAnalysisRequest, MAX_COMPANY_TEXT_LENGTH, SavedStartupEntry, SavedStartupStatus
from app.workflows.due_diligence_workflow import run_due_diligence, assemble_multi_source_text
from app.auth import AuthenticatedUser, RequireAuth
from app.ai.sie_v2_methodology import METHODOLOGY_VERSION
import json
import os
import traceback
from app.pdf_extractor import extract_text_from_pdf, MAX_PDF_BYTES, PdfExtractionError
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

# SIE Accounts & Ownership -- Canonical Startup Entity (first
# implementation slice). Order matters: startups must exist before
# analyses.startup_id can reference it, and users must exist before the
# membership/saved tables that reference it. backfill_startup_ids() runs
# last and is safe to call on every startup (idempotent -- see its own
# docstring in app/database/db.py). No existing canonical read query
# (get_rankings, search_analyses, get_startup_by_name, get_sps_history,
# get_top_improving_startups, get_analytics) is touched by this slice.
create_startups_table()
add_startup_id_column()
create_users_table()
create_startup_memberships_table()
create_saved_startups_table()
backfill_startup_ids()

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


# ---------------------------------------------------------------------------
# Saved Startups / Watchlist -- Phase 1. All four endpoints require a
# valid Clerk-authenticated user (RequireAuth -- the same dependency the
# four paid analyze endpoints already use) and derive the acting user
# EXCLUSIVELY from current_user.user_id (the verified JWT's `sub` claim)
# -- never from a path/query/body parameter a caller could set to another
# user's id. There is deliberately no /users/{user_id}/saved-startups
# route: "the authenticated user" and "me" are the same thing everywhere
# below, which makes reading/saving/removing another user's list
# structurally impossible, not just policy-enforced.
#
# This is a watchlist/bookmark relationship only -- none of these ever
# touch startup_memberships, and saving a startup never implies ownership
# of it (see save_startup_for_user()'s own docstring in app/database/db.py
# and the SIE Accounts & Ownership architecture design).
#
# Public intelligence routes (GET /startup/{company_name} and everything
# above) are completely untouched by this section -- these are new,
# additive routes, not a change to how any existing route is protected.
# ---------------------------------------------------------------------------

@app.get("/me/saved-startups", response_model=list[SavedStartupEntry])
def list_my_saved_startups(
    current_user: AuthenticatedUser = RequireAuth,
):
    return get_saved_startups_for_user(current_user.user_id)


@app.get("/me/saved-startups/{startup_id}", response_model=SavedStartupStatus)
def get_my_saved_startup_status(
    startup_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    return SavedStartupStatus(
        saved=is_startup_saved_by_user(current_user.user_id, startup_id)
    )


@app.post("/me/saved-startups/{startup_id}", response_model=SavedStartupStatus)
def save_my_startup(
    startup_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    try:
        save_startup_for_user(current_user.user_id, startup_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Startup not found.")

    return SavedStartupStatus(saved=True)


@app.delete("/me/saved-startups/{startup_id}", response_model=SavedStartupStatus)
def unsave_my_startup(
    startup_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    unsave_startup_for_user(current_user.user_id, startup_id)
    return SavedStartupStatus(saved=False)


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

# Unified Multi-Source Analyze Startup: three maxed-out sources joined
# together could otherwise be far larger than any single source was ever
# bounded to (company_text alone is capped at MAX_COMPANY_TEXT_LENGTH,
# but website/PDF extraction have their own separate byte-level caps with
# no shared character-count ceiling) -- this bounds the ASSEMBLED result,
# after every individual source has already validated on its own.
MAX_ASSEMBLED_TEXT_LENGTH = 150_000


def _read_pdf_upload_sync(file: UploadFile) -> bytes:
    """
    Sync counterpart to /analyze-pdf's _read_pdf_upload (below), for use
    inside POST /analyze's sync (non-async) path operation function --
    see analyze_unified()'s concurrency comment for why. Reads the
    upload's underlying file object directly (UploadFile.file, a plain
    SpooledTemporaryFile) in bounded chunks -- no `await` needed here,
    since it's FastAPI's automatic threadpool dispatch for a sync route
    that keeps this off the event loop, not anything async in this
    function itself. Still fully in-memory, still no temporary files.
    """
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = file.file.read(64 * 1024)

        if not chunk:
            break

        total += len(chunk)

        if total > MAX_PDF_BYTES:
            raise PdfExtractionError(
                f"That PDF is too large to analyze (max "
                f"{MAX_PDF_BYTES // (1024 * 1024)} MB)."
            )

        chunks.append(chunk)

    return b"".join(chunks)


@app.post("/analyze", response_model=StartupAnalysisResponse)
def analyze_unified(
    website_url: str | None = Form(None),
    company_text: str | None = Form(None),
    pdf: UploadFile | None = File(None),
    current_user: AuthenticatedUser = RequireAuth,
):
    # SIE Authentication Phase 2: requires a valid Clerk-authenticated
    # user -- RequireAuth resolves before this function body runs, so an
    # unauthenticated request is rejected with a clean 401 before any
    # extraction/pipeline work (and therefore before any paid OpenAI/
    # Tavily cost) ever happens. current_user is intentionally unused
    # beyond that: authentication means "this user exists" (see
    # get_or_create_user()'s docstring), never "this user owns this
    # startup" -- no startup_membership is created here or anywhere in
    # this function, by design.
    #
    # Unified Multi-Source Analyze Startup: website, pitch deck, and
    # user-provided text are evidence SOURCES feeding ONE canonical SIE
    # analysis, not separate mutually-exclusive analysis products (see
    # the Phase 1 design report and the Phase 2 product decision this
    # implements). This does not replace /analyze-startup,
    # /analyze-website, or /analyze-pdf -- they're untouched, kept for
    # backward compatibility -- it's the new primary path the frontend
    # now uses.
    #
    # Deliberately a sync `def`, not `async def`: FastAPI/Starlette
    # automatically runs a sync path operation in a worker thread, which
    # is what keeps the multi-minute pipeline call below from blocking
    # the event loop and starving concurrent requests (GET /health,
    # /analytics, ...) -- the exact bug /analyze-pdf has today from being
    # `async def` with fully synchronous, blocking work inside it. No
    # queue/worker architecture needed for this -- running synchronously
    # in a thread FastAPI already provides is the smallest idiomatic fix,
    # deliberately not applied to /analyze-pdf itself in this change.
    website_url = website_url.strip() if website_url else None
    company_text = company_text.strip() if company_text else None
    has_pdf = pdf is not None and bool(pdf.filename)

    if not website_url and not company_text and not has_pdf:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide at least one of: company website, pitch deck, or "
                "company information."
            ),
        )

    # Product decision: an explicitly supplied source that fails
    # validation/extraction rejects the WHOLE request before the
    # expensive pipeline runs -- never silently dropped in favor of
    # whatever other sources happened to succeed. A user who supplied a
    # website and a deck must get an analysis that used both, or a clear
    # error, never a silent website-only analysis they'd have no reason
    # to suspect was incomplete.
    website_text = None
    pdf_text = None

    if website_url:
        try:
            validated_url = WebsiteAnalysisRequest(url=website_url)
        except PydanticValidationError:
            raise HTTPException(
                status_code=400,
                detail="Website URL must start with http:// or https://",
            )

        try:
            website_text = extract_text_from_website(validated_url.url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            traceback.print_exc()
            raise HTTPException(
                status_code=400,
                detail=(
                    "That website could not be retrieved. Please check the "
                    "URL and try again."
                ),
            )

    if has_pdf:
        if not pdf.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="Only PDF files are supported."
            )

        try:
            pdf_bytes = _read_pdf_upload_sync(pdf)
            pdf_text = extract_text_from_pdf(pdf_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            traceback.print_exc()
            raise HTTPException(
                status_code=400,
                detail=(
                    "That PDF could not be read. Please check the file and "
                    "try again."
                ),
            )

    if company_text:
        # Reuses StartupAnalysisRequest's own bound (MAX_COMPANY_TEXT_LENGTH)
        # rather than duplicating the number -- company_text here is a raw
        # Form field, not something Pydantic validates on the way in, so
        # this is what actually enforces the same limit /analyze-startup
        # already does.
        try:
            StartupAnalysisRequest(company_text=company_text)
        except PydanticValidationError:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Additional company information must be no more than "
                    f"{MAX_COMPANY_TEXT_LENGTH:,} characters."
                ),
            )

    assembled_text = assemble_multi_source_text(
        website_text=website_text,
        pdf_text=pdf_text,
        user_text=company_text,
    )

    if len(assembled_text) > MAX_ASSEMBLED_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                "The combined information from your sources is too long "
                f"to analyze (max {MAX_ASSEMBLED_TEXT_LENGTH:,} characters "
                "combined). Please shorten one or more sources."
            ),
        )

    # Unified Multi-Source Analyze Startup, Provenance: evidence_sources
    # is the real, non-mutually-exclusive record of what fed this
    # analysis -- activates the already-existing (previously dormant)
    # AnalysisContext.evidence_sources list field, no new field added.
    # public_research is always included since enrich_research() always
    # runs inside run_due_diligence() below. analysis_type stays a single
    # derived DISPLAY label only (backward compatible with the existing
    # Startup Profile badge) via the exact deterministic rule specified:
    # pitch_deck present wins, otherwise public. Neither field is read by
    # scoring, evidence extraction, or any pillar analysis.
    evidence_sources: list[str] = []

    if website_text:
        evidence_sources.append("website")

    if pdf_text:
        evidence_sources.append("pitch_deck")

    if company_text:
        evidence_sources.append("company_description")

    evidence_sources.append("public_research")

    analysis_type = "pitch_deck" if pdf_text else "public"

    try:
        results = run_due_diligence(
            assembled_text,
            analysis_type=analysis_type,
            evidence_sources=evidence_sources,
        )
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
        # Persist the assembled, labeled multi-source text as
        # company_text rather than picking one arbitrary source --
        # nothing supplied is silently left out of the stored record.
        save_analysis(
            company_text=assembled_text,
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
    except Exception:
        # Distinct from the pipeline failure above on purpose, same as
        # every other ingestion endpoint: the (expensive, multi-minute)
        # analysis DID complete here -- only persisting it failed.
        # save_score_history() is deliberately not called here, for the
        # same established reason: Rankings/Search/Dashboard/SPS History
        # all read analyses.methodology JSONB directly, not the legacy
        # score_history table.
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


@app.post(
    "/analyze-startup",
    response_model=StartupAnalysisResponse
)
def analyze_startup(
    request: StartupAnalysisRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    # SIE Authentication Phase 2: this legacy endpoint triggers the exact
    # same paid pipeline as /analyze, so it requires the same
    # authentication -- no unauthenticated bypass around the frontend's
    # protected path. See /analyze's own comment for what RequireAuth
    # does and doesn't do (no ownership/membership created here either).
    #
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
        
    


async def _read_pdf_upload(file: UploadFile) -> bytes:
    """
    Reads the uploaded file in bounded chunks and aborts as soon as the
    running total exceeds MAX_PDF_BYTES, instead of first buffering an
    arbitrarily large upload fully into memory and only checking its
    size afterward -- this is what actually enforces the cap as a
    resource protection during upload, not just a post-hoc validation
    once the whole thing is already sitting in memory. Still entirely
    in-memory -- no temporary files.
    """
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(64 * 1024)

        if not chunk:
            break

        total += len(chunk)

        if total > MAX_PDF_BYTES:
            raise PdfExtractionError(
                f"That PDF is too large to analyze (max "
                f"{MAX_PDF_BYTES // (1024 * 1024)} MB)."
            )

        chunks.append(chunk)

    return b"".join(chunks)


@app.post("/analyze-pdf", response_model=StartupAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = RequireAuth,
):
    # SIE Authentication Phase 2: same paid pipeline as /analyze, same
    # required authentication -- see /analyze's own comment.
    #
    # Pitch Deck / PDF Ingestion: same three-stage fail-closed shape as
    # /analyze-startup and /analyze-website. Retrieval/extraction/
    # validation failures (bad, oversized, corrupt, encrypted, or
    # non-PDF upload) are the caller's to fix and get a 400 built from
    # pdf_extractor's own safe, already-user-facing message -- same
    # contract WebsiteFetchError uses for /analyze-website. Pipeline and
    # persistence failures are ours, and get the exact same generic,
    # non-leaking 502/500 responses every other ingestion path uses.
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await _read_pdf_upload(file)
        extracted_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=(
                "That PDF could not be read. Please check the file and "
                "try again."
            ),
        )

    try:
        results = run_due_diligence(extracted_text, analysis_type="pitch_deck")
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
    except Exception:
        # Distinct from the pipeline failure above on purpose, same as
        # /analyze-startup and /analyze-website: the (expensive,
        # multi-minute) analysis DID complete here -- only persisting it
        # failed. save_score_history() is deliberately not called here,
        # for the same reason already established for /analyze-website:
        # Rankings/Search/Dashboard/SPS History all read
        # analyses.methodology JSONB directly, not the legacy
        # score_history table.
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




@app.post("/analyze-website", response_model=StartupAnalysisResponse)
def analyze_website(
    request: WebsiteAnalysisRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    # SIE Authentication Phase 2: same paid pipeline as /analyze, same
    # required authentication -- see /analyze's own comment.
    #
    # Website / URL Ingestion: same fail-closed shape as /analyze-startup,
    # with one extra stage in front for retrieval. Retrieval/validation
    # failures (bad, unreachable, or disallowed URL) are the caller's to
    # fix and get a 400 built from website_scrapper's own safe,
    # already-user-facing message (WebsiteFetchError/ValueError) -- same
    # contract /analyze-pdf already uses for pdf_extractor's ValueErrors.
    # Pipeline and persistence failures are ours, and get the exact same
    # generic, non-leaking 502/500 responses /analyze-startup uses so a
    # website-sourced analysis fails no less safely than a text one.
    try:
        website_text = extract_text_from_website(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=(
                "That website could not be retrieved. Please check the URL "
                "and try again."
            ),
        )

    try:
        results = run_due_diligence(website_text)
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
    except Exception:
        # Distinct from the pipeline failure above on purpose, same as
        # /analyze-startup: the (expensive, multi-minute) analysis DID
        # complete here -- only persisting it failed. save_score_history()
        # is deliberately NOT called here -- Rankings/Search/Dashboard/SPS
        # History all already read analyses.methodology JSONB directly,
        # not the legacy score_history table, so it isn't required for
        # this analysis to appear correctly anywhere in the product.
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