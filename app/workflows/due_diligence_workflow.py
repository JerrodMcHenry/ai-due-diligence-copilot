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


def build_provenance_context(
    company_text: str = "",
    search_query: str = "",
    research_brief: str = "",
    sources: list | None = None,
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
    """
    return AnalysisContext(
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
        ),
    )


def get_pillar_score(pillar):
    return pillar.score if pillar else None


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


def run_due_diligence(company_text):
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
    )

    overall_score = sie_analysis.startup_intelligence_score

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