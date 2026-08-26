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
                         get_saved_startups_for_user,
                         discover_startups,
                         count_discover_startups,
                         get_discovery_filter_options,
                         DEFAULT_DISCOVERY_LIMIT,
                         MAX_DISCOVERY_LIMIT,
                         get_startups_for_comparison,
                         MIN_COMPARISON_STARTUPS,
                         MAX_COMPARISON_STARTUPS,
                         create_modeled_ventures_table,
                         create_modeled_venture,
                         list_modeled_ventures_for_user,
                         get_modeled_venture_for_user,
                         update_modeled_venture_for_user,
                         delete_modeled_venture_for_user,
                         create_startup_claims_table,
                         create_startup_claim,
                         list_startup_claims_for_user,
                         get_startup_claim_status_for_user,
                         list_pending_startup_claims_for_admin,
                         approve_startup_claim,
                         reject_startup_claim,
                         cancel_startup_claim,
                         StartupNotFoundError,
                         DuplicatePendingClaimError,
                         AlreadyMemberError,
                         get_startup_memberships_for_user,
                         get_founder_startup_workspace,
                         create_founder_actions_table,
                         list_founder_actions_for_startup,
                         create_founder_action,
                         update_founder_action_status
)
from typing import Literal
from fastapi import Query

from app.models.startup import StartupAnalysisRequest, StartupAnalysisResponse, StartupProfileResponse, UpdateAnalysisRequest, WebsiteAnalysisRequest, MAX_COMPANY_TEXT_LENGTH, SavedStartupEntry, SavedStartupStatus, DiscoveryResponse, DiscoveryFilterOptions, ComparisonResponse, ComparisonStartup, ComparisonPillar, ComparisonSubscore
from app.models.idea_lab import CreateVentureRequest, UpdateVentureRequest, VentureResponse, VentureSummary, VPSResult, ScenarioCompareRequest, ScenarioCompareResponse, StructureIdeaRequest, StructureIdeaResponse, VentureDraft
from app.models.startup_claim import CreateStartupClaimRequest, StartupClaimSubmissionResponse, MyStartupClaim, StartupClaimStatus, AdminStartupClaim, RejectStartupClaimRequest, StartupClaimActionResponse
from app.models.startup_membership import MyStartupMembership
from app.models.founder import FounderStartupWorkspace
from app.models.founder_action import FounderAction, CreateFounderActionRequest, UpdateFounderActionStatusRequest, FOUNDER_ACTION_PILLARS
from app.ai.idea_structuring import structure_idea, IdeaStructuringError
from app.workflows.due_diligence_workflow import run_due_diligence, assemble_multi_source_text
from app.auth import AuthenticatedUser, RequireAuth, RequireAdmin, RequireStartupMember, require_startup_member
from app.ai.sie_v2_methodology import METHODOLOGY_VERSION
from app.ai.vps_scoring import compute_vps
from app.ai.vps_guidance import generate_guidance
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

# Idea Lab / Venture Simulator V1. modeled_ventures has no FK to
# startups/analyses (see create_modeled_ventures_table()'s own docstring
# in app/database/db.py) -- ordering relative to the migrations above
# only matters because it references users(id), which must already exist.
create_modeled_ventures_table()

# Phase 7.1A -- Startup Claim & Membership backend lifecycle. Purely
# additive: references users(id)/startups(id), which already exist by
# this point. Does not alter startup_memberships's existing schema/
# default at all (see create_startup_claims_table()'s own docstring in
# app/database/db.py for why).
create_startup_claims_table()

# Phase 7.3 -- Founder Progress & Improvement V1. Purely additive:
# references startups(id)/users(id), which already exist by this point.
# Never touches startup_memberships or analyses -- see
# create_founder_actions_table()'s own module-level comment in
# app/database/db.py for the full "workflow state, never scoring" boundary.
create_founder_actions_table()

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


# ---------------------------------------------------------------------------
# Startup Discovery V1. Public (no RequireAuth) -- exploring the canonical
# startup universe is intelligence, same as Rankings/Search/Startup
# Profile, not a paid action. Every filter is optional; Query(...) bounds
# below are the "invalid filters fail cleanly" layer (a 422 before any SQL
# ever runs), on top of app/database/db.py's own defensive clamping.
# Distinct from Rankings on purpose -- Rankings is "the canonical
# leaderboard" (unfiltered, full population); Discovery is "help me find
# startups matching my criteria" (filtered, sorted, paginated). Both read
# the exact same canonical population; neither is a second definition of
# it. See discover_startups()'s own docstring in app/database/db.py.
# ---------------------------------------------------------------------------

@app.get("/discover", response_model=DiscoveryResponse)
def discover(
    query: str | None = Query(None, max_length=200),
    industry: str | None = Query(None, max_length=200),
    stage: str | None = Query(None, max_length=200),
    business_model: str | None = Query(None, max_length=200),
    min_sps: float | None = Query(None, ge=0, le=100),
    max_sps: float | None = Query(None, ge=0, le=100),
    min_market: float | None = Query(None, ge=0, le=10),
    min_team: float | None = Query(None, ge=0, le=10),
    min_product: float | None = Query(None, ge=0, le=10),
    min_execution: float | None = Query(None, ge=0, le=10),
    min_traction: float | None = Query(None, ge=0, le=10),
    min_financial_health: float | None = Query(None, ge=0, le=10),
    sort: Literal["sps_desc", "sps_asc", "newest", "name_asc"] = "sps_desc",
    limit: int = Query(DEFAULT_DISCOVERY_LIMIT, ge=1, le=MAX_DISCOVERY_LIMIT),
    offset: int = Query(0, ge=0),
):
    filters = dict(
        query=query,
        industry=industry,
        stage=stage,
        business_model=business_model,
        min_sps=min_sps,
        max_sps=max_sps,
        min_market=min_market,
        min_team=min_team,
        min_product=min_product,
        min_execution=min_execution,
        min_traction=min_traction,
        min_financial_health=min_financial_health,
    )

    try:
        results = discover_startups(sort=sort, limit=limit, offset=offset, **filters)
        total = count_discover_startups(**filters)
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Discovery results could not be loaded. Please try again.",
        )

    return DiscoveryResponse(total=total, results=results)


@app.get("/discover/filter-options", response_model=DiscoveryFilterOptions)
def discover_filter_options():
    try:
        return get_discovery_filter_options()
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Filter options could not be loaded. Please try again.",
        )


# ---------------------------------------------------------------------------
# Compare Startups V1. Public (no RequireAuth) -- comparing canonical
# intelligence is the same kind of public intelligence as Rankings/Search/
# Startup Profile, not a paid or personalized action. Reuses
# get_startups_for_comparison()'s canonical startup_id resolution (see its
# own docstring in app/database/db.py) -- this endpoint's own job is only
# input parsing/bounding and slimming the full methodology JSONB down to
# ComparisonStartup's fields.
# ---------------------------------------------------------------------------

def _build_comparison_pillar(pillar_key: str, methodology: dict) -> ComparisonPillar:
    pillar_data = methodology.get(pillar_key) or {}
    score_breakdown = pillar_data.get("score_breakdown") or {}
    subscores_data = score_breakdown.get("subscores") or []

    subscores = [
        ComparisonSubscore(
            name=subscore.get("name", ""),
            score=subscore.get("score"),
            weight=subscore.get("weight", 0.0),
            confidence=subscore.get("confidence", "Low"),
            evidence_status=subscore.get("evidence_status", "Observed"),
            rationale=subscore.get("rationale", ""),
            recommendations=subscore.get("recommendations") or [],
            missing_information=subscore.get("missing_information") or [],
        )
        for subscore in subscores_data
    ]

    return ComparisonPillar(
        pillar=pillar_key,
        score=pillar_data.get("score"),
        confidence=pillar_data.get("confidence", "Low"),
        evidence_coverage=score_breakdown.get("evidence_coverage", 0.0),
        summary=pillar_data.get("summary", ""),
        strengths=pillar_data.get("strengths") or [],
        weaknesses=pillar_data.get("weaknesses") or [],
        recommendations=pillar_data.get("recommendations") or [],
        subscores=subscores,
    )


def _build_comparison_startup(row: dict) -> ComparisonStartup:
    methodology = row["methodology"]
    context = methodology.get("context") or {}

    return ComparisonStartup(
        startup_id=row["startup_id"],
        company_name=context.get("company_name") or row["company_name"] or "",
        industry=context.get("industry", ""),
        company_stage=context.get("company_stage", ""),
        business_model=context.get("business_model", ""),
        latest_analysis_at=row["created_at"],
        overall_score=methodology.get("startup_intelligence_score"),
        market=_build_comparison_pillar("market", methodology),
        team=_build_comparison_pillar("team", methodology),
        product=_build_comparison_pillar("product", methodology),
        execution=_build_comparison_pillar("execution", methodology),
        traction=_build_comparison_pillar("traction", methodology),
        financial_health=_build_comparison_pillar("financial_health", methodology),
    )


@app.get("/compare", response_model=ComparisonResponse)
def compare(startups: str = Query(..., min_length=1, max_length=200)):
    # Deliberately permissive parsing -- a malformed/non-numeric token is
    # dropped, not a 422, matching Part 5's "invalid IDs fail gracefully".
    # Only "fewer than MIN_COMPARISON_STARTUPS well-formed ids" is a hard
    # rejection; everything else degrades to the most useful response it
    # can, with missing_startup_ids reporting what didn't resolve.
    raw_tokens = [token.strip() for token in startups.split(",") if token.strip()]

    parsed_ids: list[int] = []
    for token in raw_tokens:
        try:
            parsed_ids.append(int(token))
        except ValueError:
            continue

    deduped_ids = list(dict.fromkeys(parsed_ids))

    if len(deduped_ids) < MIN_COMPARISON_STARTUPS:
        raise HTTPException(
            status_code=400,
            detail=f"Provide at least {MIN_COMPARISON_STARTUPS} distinct startup IDs to compare.",
        )

    # Safely bounded, not hard-rejected: a shared/old link listing more
    # than the current max simply compares the first
    # MAX_COMPARISON_STARTUPS rather than erroring the whole request.
    bounded_ids = deduped_ids[:MAX_COMPARISON_STARTUPS]

    try:
        rows = get_startups_for_comparison(bounded_ids)
        resolved_ids = {row["startup_id"] for row in rows}
        missing_ids = [id_ for id_ in bounded_ids if id_ not in resolved_ids]
        comparison_startups = [_build_comparison_startup(row) for row in rows]
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Comparison could not be loaded. Please try again.",
        )

    return ComparisonResponse(startups=comparison_startups, missing_startup_ids=missing_ids)


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


# ---------------------------------------------------------------------------
# Idea Lab / Venture Simulator V1. Every endpoint below requires
# RequireAuth and derives the acting user EXCLUSIVELY from
# current_user.user_id -- there is no /users/{user_id}/ventures route, so
# reading/editing/deleting another user's venture is structurally
# impossible, the same discipline as Saved Startups. modeled_ventures has
# no relationship to startups/analyses at all (see
# create_modeled_ventures_table()'s own docstring) -- nothing here can
# ever appear in Rankings, Discovery, or canonical Compare, and none of
# it creates a startup_membership or saved_startup.
#
# The Venture Potential Score (VPS) computed below is architecturally
# separate from SPS: compute_vps()/generate_guidance() (app/ai/
# vps_scoring.py, vps_guidance.py) never import from or call into
# app/ai/scoring.py, scoring_methodology.py, or investment_score.py, and
# never touch the analyses table. See those modules' own docstrings for
# the full reasoning.
# ---------------------------------------------------------------------------

def _build_model_result(assumptions: dict) -> dict:
    vps_result = compute_vps(assumptions)
    guidance = generate_guidance(assumptions, vps_result)
    return {**vps_result, **guidance}


# ---------------------------------------------------------------------------
# Phase 6.1 -- AI-Assisted Idea Setup. A stateless drafting endpoint: it
# reads nothing from and writes nothing to modeled_ventures (or any other
# table), never calls compute_vps()/_build_model_result(), and cannot
# create a Startup/Analysis -- there is no code path from here into
# save_analysis(), get_or_create_startup(), or any Rankings/Discovery
# query. Requires RequireAuth per the task's explicit instruction ("use
# the existing authenticated user boundary even though nothing is
# persisted") even though current_user is otherwise unused here -- this
# keeps the whole /ventures* surface consistently behind auth rather than
# carving out one public exception.
#
# Fails closed on every failure mode: StructureIdeaRequest's own
# min/max_length bounds reject empty/oversized input with a 422 before
# this function body ever runs; any LLM/parsing failure inside
# structure_idea() raises IdeaStructuringError, caught below and turned
# into one generic, safe 502 -- never the raw provider exception.
# ---------------------------------------------------------------------------

@app.post("/ventures/structure-idea", response_model=StructureIdeaResponse)
def structure_idea_endpoint(
    request: StructureIdeaRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    try:
        draft_dict = structure_idea(request.description)
        draft = VentureDraft(**draft_dict)
    except IdeaStructuringError:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail="We couldn't structure that idea right now. Please try again.",
        )
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail="We couldn't structure that idea right now. Please try again.",
        )

    return StructureIdeaResponse(draft=draft)


@app.post("/ventures", response_model=VentureResponse)
def create_venture(
    request: CreateVentureRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    assumptions_dict = request.assumptions.model_dump()
    model_result = _build_model_result(assumptions_dict)

    try:
        venture_id = create_modeled_venture(
            user_id=current_user.user_id,
            name=request.name,
            description=request.description,
            industry=request.industry,
            business_model=request.business_model,
            target_customer=request.target_customer,
            stage=request.stage,
            assumptions=assumptions_dict,
            model_result=model_result,
        )
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Your venture could not be saved. Please try again.",
        )

    venture = get_modeled_venture_for_user(current_user.user_id, venture_id)
    return VentureResponse(**venture)


@app.get("/ventures", response_model=list[VentureSummary])
def list_ventures(current_user: AuthenticatedUser = RequireAuth):
    ventures = list_modeled_ventures_for_user(current_user.user_id)

    return [
        VentureSummary(
            id=venture["id"],
            name=venture["name"],
            stage=venture["stage"],
            vps=(venture["model_result"] or {}).get("vps"),
            updated_at=venture["updated_at"],
        )
        for venture in ventures
    ]


@app.get("/ventures/{venture_id}", response_model=VentureResponse)
def get_venture(
    venture_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    venture = get_modeled_venture_for_user(current_user.user_id, venture_id)

    if venture is None:
        # Deliberately the same 404 whether the id doesn't exist at all or
        # belongs to a different user -- see
        # get_modeled_venture_for_user()'s own docstring.
        raise HTTPException(status_code=404, detail="Venture not found.")

    return VentureResponse(**venture)


@app.put("/ventures/{venture_id}", response_model=VentureResponse)
def update_venture(
    venture_id: int,
    request: UpdateVentureRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    assumptions_dict = request.assumptions.model_dump()
    model_result = _build_model_result(assumptions_dict)

    updated = update_modeled_venture_for_user(
        user_id=current_user.user_id,
        venture_id=venture_id,
        name=request.name,
        description=request.description,
        industry=request.industry,
        business_model=request.business_model,
        target_customer=request.target_customer,
        stage=request.stage,
        assumptions=assumptions_dict,
        model_result=model_result,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Venture not found.")

    venture = get_modeled_venture_for_user(current_user.user_id, venture_id)
    return VentureResponse(**venture)


@app.delete("/ventures/{venture_id}")
def delete_venture(
    venture_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    deleted = delete_modeled_venture_for_user(current_user.user_id, venture_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Venture not found.")

    return {"deleted": True}


@app.post("/ventures/scenario-compare", response_model=ScenarioCompareResponse)
def compare_venture_scenarios(
    request: ScenarioCompareRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    """
    Part 11: current vs. modified scenario -- stateless (both assumption
    sets come from the request body; nothing is read from or written to
    modeled_ventures here), so trying a scenario never overwrites the
    venture's actually-saved assumptions. Requires auth only because it's
    part of the private Idea Lab surface, not because it reads any
    per-user data. Deliberately a distinct endpoint from GET /compare --
    it never touches startups/analyses/canonical Startup identity, and a
    modeled venture can never be passed to /compare's startup_id-based
    contract.
    """
    current_result = _build_model_result(request.current_assumptions.model_dump())
    modified_result = _build_model_result(request.modified_assumptions.model_dump())

    return ScenarioCompareResponse(
        current=VPSResult(**current_result),
        modified=VPSResult(**modified_result),
    )


# ---------------------------------------------------------------------------
# Phase 7.1A -- Startup Claim & Membership backend lifecycle.
#
# CORE INVARIANT: startup_memberships represents actual authorized
# relationships. A pending, rejected, or cancelled claim NEVER creates a
# membership -- the only endpoint below that can possibly result in a new
# startup_memberships row is approve_my_claim_admin_action (the admin
# approval action), which delegates to approve_startup_claim(), the one
# function in this codebase allowed to write that table (see its own
# docstring in app/database/db.py).
#
# user_id is derived exclusively from RequireAuth/current_user.user_id on
# every founder-facing endpoint below -- never accepted from a path,
# query, or body parameter. Admin endpoints are gated by RequireAdmin,
# which itself is built on the same unchanged JWT verification (see
# app/auth.py) plus a server-side ADMIN_USER_IDS allowlist check.
# ---------------------------------------------------------------------------

@app.post("/startup-claims", response_model=StartupClaimSubmissionResponse)
def submit_startup_claim(
    request: CreateStartupClaimRequest,
    current_user: AuthenticatedUser = RequireAuth,
):
    try:
        claim_id = create_startup_claim(
            user_id=current_user.user_id,
            startup_id=request.startup_id,
            justification=request.justification,
            contact_email=request.contact_email,
        )
    except StartupNotFoundError:
        raise HTTPException(status_code=404, detail="Startup not found.")
    except AlreadyMemberError:
        raise HTTPException(
            status_code=409,
            detail="You already have access to this startup -- no claim is needed.",
        )
    except DuplicatePendingClaimError:
        raise HTTPException(
            status_code=409,
            detail="You already have a pending claim for this startup.",
        )
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Your claim could not be submitted. Please try again.",
        )

    return StartupClaimSubmissionResponse(
        id=claim_id, startup_id=request.startup_id, status="pending"
    )


@app.get("/me/startup-claims", response_model=list[MyStartupClaim])
def list_my_startup_claims(current_user: AuthenticatedUser = RequireAuth):
    return list_startup_claims_for_user(current_user.user_id)


@app.get("/me/startup-claims/{startup_id}", response_model=StartupClaimStatus | None)
def get_my_startup_claim_status(
    startup_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    """Smallest useful helper for Phase 7.1B's 'Claim this startup'
    control -- the caller's own most recent claim for this one startup,
    or null if they've never claimed it. Never reveals anyone else's
    claim status for the same startup."""
    status = get_startup_claim_status_for_user(current_user.user_id, startup_id)

    if status is None:
        return None

    return StartupClaimStatus(
        claim_id=status["id"],
        status=status["status"],
        submitted_at=status["submitted_at"],
        reviewed_at=status["reviewed_at"],
        rejection_reason=status["rejection_reason"],
    )


@app.post("/me/startup-claims/{claim_id}/cancel", response_model=StartupClaimActionResponse)
def cancel_my_startup_claim(
    claim_id: int,
    current_user: AuthenticatedUser = RequireAuth,
):
    cancelled = cancel_startup_claim(current_user.user_id, claim_id)

    if not cancelled:
        # Same non-leaking shape as every other user-scoped resource in
        # this codebase: "doesn't exist", "belongs to someone else", and
        # "isn't pending anymore" are all indistinguishable from the
        # caller's perspective.
        raise HTTPException(status_code=404, detail="Claim not found.")

    return StartupClaimActionResponse(claim_id=claim_id, status="cancelled")


@app.get("/admin/startup-claims", response_model=list[AdminStartupClaim])
def list_admin_startup_claims(current_user: AuthenticatedUser = RequireAdmin):
    return list_pending_startup_claims_for_admin()


@app.post("/admin/startup-claims/{claim_id}/approve", response_model=StartupClaimActionResponse)
def approve_admin_startup_claim(
    claim_id: int,
    current_user: AuthenticatedUser = RequireAdmin,
):
    result = approve_startup_claim(claim_id, current_user.user_id)

    if result is None:
        raise HTTPException(
            status_code=409,
            detail="This claim is not currently pending (it may not exist, or has already been reviewed).",
        )

    return StartupClaimActionResponse(claim_id=claim_id, status="approved")


@app.post("/admin/startup-claims/{claim_id}/reject", response_model=StartupClaimActionResponse)
def reject_admin_startup_claim(
    claim_id: int,
    request: RejectStartupClaimRequest,
    current_user: AuthenticatedUser = RequireAdmin,
):
    rejected = reject_startup_claim(claim_id, current_user.user_id, request.rejection_reason)

    if not rejected:
        raise HTTPException(
            status_code=409,
            detail="This claim is not currently pending (it may not exist, or has already been reviewed).",
        )

    return StartupClaimActionResponse(claim_id=claim_id, status="rejected")


# ---------------------------------------------------------------------------
# Phase 7.1C -- Founder Membership Authorization Foundation. Read-only:
# get_startup_memberships_for_user() derives every row exclusively from
# startup_memberships (see that function's own docstring) -- never from
# startup_claims, saved_startups, or modeled_ventures. This is the
# intended entry point for a future /founder surface (Phase 7.2): "which
# canonical startups does this authenticated user legitimately belong
# to?" user_id is derived exclusively from RequireAuth/current_user.user_id,
# never from a path, query, or body parameter, same discipline as every
# other /me/* endpoint above.
# ---------------------------------------------------------------------------

@app.get("/me/startups", response_model=list[MyStartupMembership])
def list_my_startups(current_user: AuthenticatedUser = RequireAuth):
    return get_startup_memberships_for_user(current_user.user_id)


# ---------------------------------------------------------------------------
# Phase 7.2 -- Founder Workspace V1. RequireStartupMember (app/auth.py)
# resolves startup_id from this route's own path parameter and 404s
# before this function body ever runs if the caller has no live
# startup_memberships row for it -- never authorized by startup_claims,
# saved_startups, modeled_ventures, or anything client-supplied. This is
# the only startup-scoped Founder Workspace endpoint in V1.
# ---------------------------------------------------------------------------

@app.get("/founder/startups/{startup_id}", response_model=FounderStartupWorkspace)
def get_founder_startup(
    startup_id: int,
    current_user: AuthenticatedUser = RequireStartupMember,
):
    workspace = get_founder_startup_workspace(startup_id)

    if workspace is None:
        # Should be unreachable once RequireStartupMember has already
        # passed (a membership row can't reference a nonexistent
        # startups.id, per that table's own FK) -- kept as a clean 404
        # rather than a 500 in case that ever stops being true.
        raise HTTPException(status_code=404, detail="Startup not found.")

    return workspace


# ---------------------------------------------------------------------------
# Phase 7.3 -- Founder Progress & Improvement V1. Same RequireStartupMember
# gate as GET /founder/startups/{startup_id} above -- every endpoint below
# 404s before its body runs if the caller has no live startup_memberships
# row for this exact startup_id, never authorized by startup_claims,
# saved_startups, modeled_ventures, or anything client-supplied.
#
# Shared plan, not per-member (Part 11): none of these endpoints filter
# by current_user.user_id -- any verified member of the startup sees and
# can act on every action in it. created_by_user_id (set from
# current_user.user_id, never accepted from the request body) is
# provenance only.
#
# founder_actions is pure workflow state -- no endpoint here ever touches
# analyses, methodology, startup_intelligence_score, or
# startup_memberships. See app/database/db.py's own Phase 7.3 section for
# the full boundary statement and app/tests/test_founder_actions.py for
# the code-level audit.
#
# No separate GET .../suggested-actions endpoint exists: the six pillars'
# real recommendations are already present in GET /founder/startups/
# {startup_id}'s own `methodology` field (Phase 7.2), and the frontend
# derives suggested actions from that response client-side -- identical
# in spirit to how PrioritiesSection's "Top Priorities" already ranks by
# weakest pillar. Adding a second endpoint to return the same data a
# different way would duplicate, not simplify, this surface.
# ---------------------------------------------------------------------------

@app.get("/founder/startups/{startup_id}/actions", response_model=list[FounderAction])
def list_founder_actions(
    startup_id: int,
    current_user: AuthenticatedUser = RequireStartupMember,
):
    return list_founder_actions_for_startup(startup_id)


@app.post("/founder/startups/{startup_id}/actions", response_model=FounderAction)
def create_founder_action_endpoint(
    startup_id: int,
    request: CreateFounderActionRequest,
    current_user: AuthenticatedUser = RequireStartupMember,
):
    if request.related_pillar is not None and request.related_pillar not in FOUNDER_ACTION_PILLARS:
        raise HTTPException(
            status_code=400,
            detail=f"related_pillar must be one of {sorted(FOUNDER_ACTION_PILLARS)} or omitted.",
        )

    return create_founder_action(
        startup_id=startup_id,
        created_by_user_id=current_user.user_id,
        title=request.title.strip(),
        description=(request.description.strip() if request.description else None),
        related_pillar=request.related_pillar,
        source=request.source,
    )


@app.patch("/founder/startups/{startup_id}/actions/{action_id}", response_model=FounderAction)
def update_founder_action_status_endpoint(
    startup_id: int,
    action_id: int,
    request: UpdateFounderActionStatusRequest,
    current_user: AuthenticatedUser = RequireStartupMember,
):
    updated = update_founder_action_status(startup_id, action_id, request.status)

    if updated is None:
        # Same non-leaking shape as every other startup/claim-scoped
        # resource in this codebase: "doesn't exist" and "belongs to a
        # different startup" are indistinguishable from the caller's
        # perspective.
        raise HTTPException(status_code=404, detail="Action not found.")

    return updated


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
    # Phase 7.2.1 -- Deterministic Founder Re-analysis: OPTIONAL. Absent
    # (None) on every normal/public analysis -- that path is completely
    # unchanged, see below and save_analysis()'s own docstring. When
    # present, this becomes the authoritative canonical identity for the
    # resulting analysis (Founder Workspace's "Re-analyze"), gated by the
    # membership check immediately below -- never trusted merely because
    # the client supplied it.
    startup_id: int | None = Form(None),
    current_user: AuthenticatedUser = RequireAuth,
):
    # SIE Authentication Phase 2: requires a valid Clerk-authenticated
    # user -- RequireAuth resolves before this function body runs, so an
    # unauthenticated request is rejected with a clean 401 before any
    # extraction/pipeline work (and therefore before any paid OpenAI/
    # Tavily cost) ever happens. current_user is intentionally unused
    # beyond that when startup_id is absent: authentication means "this
    # user exists" (see get_or_create_user()'s docstring), never "this
    # user owns this startup" -- no startup_membership is created here or
    # anywhere in this function, by design, regardless of startup_id.
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
    #
    # Phase 7.2.1: the founder-targeted membership check runs FIRST --
    # before URL/PDF validation, before any extraction, before the
    # pipeline -- so an unauthorized or invalid startup_id fails closed
    # with zero side effects and zero pipeline cost, per that phase's own
    # "do not run the expensive analysis pipeline" requirement.
    # require_startup_member() is called directly as a plain function
    # (not via its usual Depends() wiring, which only resolves startup_id
    # from a route's own PATH parameter -- this route has none, since
    # startup_id is optional here) -- same function, same
    # membership-only check, same non-leaking 404, as every other
    # RequireStartupMember caller; reused, not reimplemented.
    if startup_id is not None:
        require_startup_member(startup_id=startup_id, current_user=current_user)

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
            readiness_summary=results["readiness_summary"],
            # Phase 7.2.1: None on every normal/public analysis (the
            # `if startup_id is not None` guard above is the only thing
            # that ever populates it, and only after that same value
            # already passed require_startup_member()) -- passing it
            # through here is what makes save_analysis() skip
            # get_or_create_startup() and attach directly to this exact
            # authorized canonical startup instead.
            startup_id=startup_id,
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