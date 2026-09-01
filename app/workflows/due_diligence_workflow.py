import hashlib
from datetime import datetime, timezone

from app.ai.summarize import summarize_company
from app.ai.risk_analysis import analyze_risks
from app.ai.memo_generator import generate_investment_memo
from app.ai.structured_analysis import generate_structured_analysis
from app.ai.competitor_anlalysis import analyze_competitors

from app.ai.founder_analysis import analyze_founders
from app.ai.market_analysis import analyze_market
from app.ai.research_enrichment import enrich_research
from app.ai.traction_analysis import analyze_traction
from app.ai.readiness_score import generate_readiness_score
from app.ai.product_analysis import analyze_product
from app.ai.execution_analysis import analyze_execution
from app.ai.financial_analysis import analyze_financials
from app.ai.analyze_pillar import PILLAR_ANALYSIS_MODEL, PILLAR_PROMPT_VERSION
from app.ai.scoring_methodology import SCORING_VERSION
from app.ai.sie_v2_methodology import METHODOLOGY_VERSION, ANCHOR_REGISTRY_VERSION

from app.models.startup import SIEContext
from app.models.analysis_context import AnalysisContext
from app.workflows.sie_assembler import assemble_sie_analysis
from app.ai.sps_v3_adapter import sps_v3_enabled, compute_sps_v3_assessment


def build_provenance_context(
    company_text: str = "",
    search_query: str = "",
    research_brief: str = "",
    sources: list | None = None,
    analysis_type: str = "public",
    evidence_sources: list[str] | None = None,
) -> AnalysisContext:
    """
    Build the provenance record for one analysis (SIE Scoring Reliability
    sprint, Phase 5). model_identifier / prompt_version / scoring_version
    are always stamped (they are static constants, always knowable).
    company_text_hash / search_query / research_brief_snapshot /
    source_snapshot are only populated when the caller actually has live
    research to record -- run_due_diligence() always supplies them; the
    frozen-evidence reliability harness does not, since it intentionally
    bypasses live research and has no new research to attribute.

    Pitch Deck / PDF Ingestion: analysis_type is provenance/display
    metadata only (see AnalysisContext.analysis_type's AnalysisType
    literal) -- it never reaches scoring, evidence, or any pillar
    analysis. Defaults to "public" so every existing caller (text,
    website, calibration, the reliability harness) is unaffected; only
    /analyze-pdf and /analyze pass a non-default value through
    run_due_diligence().

    Unified Multi-Source Analyze Startup: evidence_sources is the real,
    non-mutually-exclusive record of which evidence source TYPES fed this
    analysis (see AnalysisContext.evidence_sources' EvidenceSourceType
    literal, already defined and already list-shaped -- this activates
    it, it doesn't add a new field). Left as None for every caller except
    POST /analyze, so AnalysisContext's own pre-existing default
    (["company_description"]) is unchanged for /analyze-startup,
    /analyze-website, /analyze-pdf, calibration, and the reliability
    harness -- exactly their current (dormant-field) behavior, preserved.
    Like analysis_type, this is provenance/display metadata only.
    """
    kwargs = dict(
        analysis_type=analysis_type,
        # SIE Methodology v2: methodology_version was previously never
        # explicitly set here, so it silently stayed at AnalysisContext's
        # Pydantic default ("1.0") for every analysis, v1 included -- a
        # real provenance gap the v2 implementation gap analysis found and
        # fixes. anchor_registry_version is new in v2: distinguishes "same
        # 28 dimensions, refined anchor" from "different dimension set" if
        # the anchor registry is ever updated independently of the
        # architecture (see app/ai/sie_v2_methodology.py).
        methodology_version=METHODOLOGY_VERSION,
        anchor_registry_version=ANCHOR_REGISTRY_VERSION,
        scoring_version=SCORING_VERSION,
        model_identifier=PILLAR_ANALYSIS_MODEL,
        prompt_version=PILLAR_PROMPT_VERSION,
        company_text_hash=(
            hashlib.sha256(company_text.encode("utf-8")).hexdigest()
            if company_text
            else ""
        ),
        search_query=search_query,
        research_brief_snapshot=research_brief,
        source_snapshot=sources or [],
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )

    if evidence_sources is not None:
        kwargs["evidence_sources"] = evidence_sources

    return AnalysisContext(**kwargs)


def build_sie_methodology_analysis(
    structured_analysis,
    readiness,
    founder_analysis,
    market_analysis,
    product_analysis,
    execution_analysis,
    traction_analysis,
    financial_analysis,
    company_text: str = "",
    search_query: str = "",
    research_brief: str = "",
    sources: list | None = None,
    analysis_type: str = "public",
    evidence_sources: list[str] | None = None,
):
    # generate_structured_analysis() (app/ai/structured_analysis.py) asks the
    # model for a single "stage" field (e.g. "Series A") -- there is no
    # separate "company_stage" or "funding_stage" key in its output. Reading
    # those two keys here always returned None, so both context fields were
    # silently empty on every analysis regardless of what the model actually
    # extracted. Map the one stage signal that exists to both fields; they
    # are the same concept as far as extraction goes today.
    stage = structured_analysis.get("stage") or ""

    context = SIEContext(
    company_name=structured_analysis.get("company_name") or "",
    industry=structured_analysis.get("industry") or "",
    business_model=structured_analysis.get("business_model") or "",
    company_stage=stage,
    funding_stage=stage,
)
    return assemble_sie_analysis(
        context=context,
        market_analysis=market_analysis,
        team_analysis=founder_analysis,
        product_analysis=product_analysis,
        execution_analysis=execution_analysis,
        traction_analysis=traction_analysis,
        financial_analysis=financial_analysis,
        readiness=readiness,
        analysis_context=build_provenance_context(
            company_text=company_text,
            search_query=search_query,
            research_brief=research_brief,
            sources=sources,
            analysis_type=analysis_type,
            evidence_sources=evidence_sources,
        ),
    )


def get_pillar_score(pillar):
    return pillar.score if pillar else None


def assemble_multi_source_text(
    website_text: str | None = None,
    pdf_text: str | None = None,
    user_text: str | None = None,
) -> str:
    """
    Unified Multi-Source Analyze Startup: joins whichever evidence
    sources were actually supplied into ONE labeled company_text blob --
    this is the entire "Evidence/Input Assembly" step. Only sections that
    were actually supplied are included (no empty "=== Pitch Deck ==="
    header when no deck was given). No LLM call, no summarization, no
    second pipeline -- the result is handed to run_due_diligence()
    exactly like any other company_text always has been; the labeling is
    what lets source identity survive into the model's own evidence
    rationale (it can say "the pitch deck states..." vs "the website
    states...") without touching evidence-extraction prompts or the
    Evidence/DimensionEvidence schema, the same way build_enriched_text()
    below already separates "Original Company Information" from
    "Additional Research Context" today.
    """
    sections: list[str] = []

    if website_text:
        sections.append(f"=== Company Website ===\n{website_text}")

    if pdf_text:
        sections.append(f"=== Pitch Deck ===\n{pdf_text}")

    if user_text:
        sections.append(f"=== Additional Company Information ===\n{user_text}")

    return "\n\n".join(sections)


def build_enriched_text(company_text: str, research_context: str) -> str:
    """
    Combine raw company_text with the research brief exactly as
    run_due_diligence() has always done. Factored out so the reliability
    harness (app/reliability/) can freeze one enriched_text and reuse it
    across repeated scoring runs without re-deriving it.
    """
    return f"""
Original Company Information:
{company_text}

Additional Research Context:
{research_context}
"""


def analyze_pillars_from_enriched_text(enriched_text: str) -> dict:
    """
    Run the six independent SIE pillar analyses against already-enriched
    text, without calling live research.

    This is the seam the frozen-evidence reliability harness
    (app/reliability/) uses to repeatedly score the SAME evidence: it
    calls this function directly instead of run_due_diligence(), so no
    live Tavily search or research-enrichment LLM call happens per
    scoring run. Production behavior is unchanged -- run_due_diligence()
    below still always builds enriched_text from live research first and
    calls this same function; nothing here changes what production does
    by default.
    """
    return {
        "founder_analysis": analyze_founders(enriched_text),
        "market_analysis": analyze_market(enriched_text),
        "product_analysis": analyze_product(enriched_text),
        "execution_analysis": analyze_execution(enriched_text),
        "traction_analysis": analyze_traction(enriched_text),
        "financial_analysis": analyze_financials(enriched_text),
    }


def run_due_diligence(
    company_text,
    analysis_type: str = "public",
    evidence_sources: list[str] | None = None,
):
    # analysis_type / evidence_sources are provenance/display metadata
    # only (see build_provenance_context above) -- they flow straight
    # through to AnalysisContext and never influence research, pillar
    # analysis, or scoring. Defaults keep every pre-existing caller
    # (text, website, calibration, the CLI) behaving exactly as before;
    # only /analyze-pdf and /analyze pass non-default values.
    research_result = enrich_research(company_text)

    research_context = research_result["research_brief"]
    sources = research_result["sources"]
    search_query = research_result["search_query"]

    enriched_text = build_enriched_text(company_text, research_context)

    summary = summarize_company(enriched_text)
    risk_analysis = analyze_risks(enriched_text)
    competitor_analysis = analyze_competitors(enriched_text)
    memo = generate_investment_memo(enriched_text)
    structured_analysis = generate_structured_analysis(enriched_text)

    pillar_results = analyze_pillars_from_enriched_text(enriched_text)
    founder_analysis = pillar_results["founder_analysis"]
    market_analysis = pillar_results["market_analysis"]
    product_analysis = pillar_results["product_analysis"]
    execution_analysis = pillar_results["execution_analysis"]
    traction_analysis = pillar_results["traction_analysis"]
    financial_analysis = pillar_results["financial_analysis"]

    initial_readiness = None

    sie_analysis = build_sie_methodology_analysis(
        structured_analysis=structured_analysis,
        readiness=initial_readiness,
        founder_analysis=founder_analysis,
        market_analysis=market_analysis,
        product_analysis=product_analysis,
        execution_analysis=execution_analysis,
        traction_analysis=traction_analysis,
        financial_analysis=financial_analysis,
        company_text=company_text,
        search_query=search_query,
        research_brief=research_context,
        sources=sources,
        analysis_type=analysis_type,
        evidence_sources=evidence_sources,
    )

    market_score = get_pillar_score(sie_analysis.market)
    team_score = get_pillar_score(sie_analysis.team)
    product_score = get_pillar_score(sie_analysis.product)
    execution_score = get_pillar_score(sie_analysis.execution)
    traction_score = get_pillar_score(sie_analysis.traction)
    financial_score = get_pillar_score(sie_analysis.financial_health)
    overall_score = sie_analysis.startup_intelligence_score

    readiness = generate_readiness_score(
        market_score,
        team_score,
        product_score,
        execution_score,
        traction_score,
        financial_score,
        overall_score,
    )

    sie_analysis = build_sie_methodology_analysis(
        structured_analysis=structured_analysis,
        readiness=readiness,
        founder_analysis=founder_analysis,
        market_analysis=market_analysis,
        product_analysis=product_analysis,
        execution_analysis=execution_analysis,
        traction_analysis=traction_analysis,
        financial_analysis=financial_analysis,
        company_text=company_text,
        search_query=search_query,
        research_brief=research_context,
        sources=sources,
        analysis_type=analysis_type,
        evidence_sources=evidence_sources,
    )

    overall_score = sie_analysis.startup_intelligence_score

    # SPS V3 Canonical Activation: sps_v3_enabled() now defaults ON
    # (SPS_ENGINE_VERSION unset -> V3; explicit "v2_1" -> legacy-only).
    # NOTHING above this line changes either way -- the V2.1 pipeline
    # that produced overall_score/investment_score/readiness runs
    # unconditionally, completely unaffected by this flag; it is not
    # replaced, only supplemented. When enabled (the default), this makes
    # exactly ONE additional LLM call (a classification pass over
    # evidence V2.1 already extracted -- no new research, no new Tavily
    # call) and can only ADD sie_analysis.sps_v3; it never modifies
    # market_score/team_score/.../overall_score or any other field
    # already assembled above. See docs/methodology/
    # SPS_V3_CANONICAL_ACTIVATION.md for the full activation record.
    if sps_v3_enabled():
        sie_analysis.sps_v3 = compute_sps_v3_assessment(
            sie_analysis,
            id_seed=(structured_analysis.get("company_name") or "STARTUP")[:40],
        )

    investment_score = {
        "market_score": market_score,
        "team_score": team_score,
        "product_score": product_score,
        "competition_score": execution_score,
        "traction_score": traction_score,
        "financial_score": financial_score,
        "overall_score": overall_score,
        "recommendation": None,
    }

    return {
        "summary": summary,
        "risk_analysis": risk_analysis,
        "competitor_analysis": competitor_analysis,
        "memo": memo,
        "structured_analysis": structured_analysis,
        "investment_score": investment_score,
        "readiness": readiness,
        "readiness_score": readiness.get("readiness_score"),
        "readiness_summary": readiness.get("readiness_summary"),
        "founder_analysis": founder_analysis,
        "market_analysis": market_analysis,
        "sources": sources,
        "traction_analysis": traction_analysis,
        "market_score": market_score,
        "team_score": team_score,
        "product_score": product_score,
        "competition_score": execution_score,
        "traction_score": traction_score,
        "financial_score": financial_score,
        "overall_score": overall_score,
        "recommendation": None,
        "sie_analysis": sie_analysis,
    }