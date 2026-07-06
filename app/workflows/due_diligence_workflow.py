from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo
from ai.structured_analysis import generate_structured_analysis
from ai.competitor_anlalysis import analyze_competitors

from ai.founder_analysis import analyze_founders
from ai.market_analysis import analyze_market
from ai.research_enrichment import enrich_research
from ai.traction_analysis import analyze_traction
from ai.readiness_score import generate_readiness_score
from ai.product_analysis import analyze_product
from ai.execution_analysis import analyze_execution
from ai.financial_analysis import analyze_financials

from models.startup import SIEContext
from workflows.sie_assembler import assemble_sie_analysis


def build_sie_methodology_analysis(
    structured_analysis,
    readiness,
    founder_analysis,
    market_analysis,
    product_analysis,
    execution_analysis,
    traction_analysis,
    financial_analysis,
):
    context = SIEContext(
        company_name=structured_analysis.get("company_name"),
        industry=structured_analysis.get("industry"),
        business_model=structured_analysis.get("business_model"),
        company_stage=structured_analysis.get("stage"),
        funding_stage=structured_analysis.get("funding_stage"),
    )

    return assemble_sie_analysis(
        context=context,
        market_analysis=market_analysis,
        team_analysis=founder_analysis,
        product_analysis=product_analysis,
        execution_analysis=execution_analysis,
        traction_analysis=traction_analysis,
        financial_analysis=financial_analysis,
        scores={},
        readiness=readiness,
    )


def get_pillar_score(pillar):
    return pillar.score if pillar else None


def run_due_diligence(company_text):
    research_result = enrich_research(company_text)

    research_context = research_result["research_brief"]
    sources = research_result["sources"]

    enriched_text = f"""
Original Company Information:
{company_text}

Additional Research Context:
{research_context}
"""

    summary = summarize_company(enriched_text)
    risk_analysis = analyze_risks(enriched_text)
    competitor_analysis = analyze_competitors(enriched_text)
    memo = generate_investment_memo(enriched_text)
    structured_analysis = generate_structured_analysis(enriched_text)

    founder_analysis = analyze_founders(enriched_text)
    market_analysis = analyze_market(enriched_text)
    product_analysis = analyze_product(enriched_text)
    execution_analysis = analyze_execution(enriched_text)
    traction_analysis = analyze_traction(enriched_text)
    financial_analysis = analyze_financials(enriched_text)

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