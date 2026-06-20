from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo
from ai.structured_analysis import generate_structured_analysis
from ai.competitor_anlalysis import analyze_competitors
from ai.scoring import generate_investment_score
from ai.founder_analysis import analyze_founders
from ai.market_analysis import analyze_market
from ai.research_enrichment import enrich_research
from ai.traction_analysis import analyze_traction
from ai.readiness_score import generate_readiness_score

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

    investment_score = generate_investment_score(enriched_text)

    readiness = generate_readiness_score(
        investment_score.get("market_score"),
        investment_score.get("team_score"),
        investment_score.get("product_score"),
        investment_score.get("competition_score"),
        investment_score.get("traction_score"),
        investment_score.get("financial_score"),
        investment_score.get("overall_score")
    )

    founder_analysis = analyze_founders(enriched_text)

    market_analysis = analyze_market(enriched_text)

    traction_analysis = analyze_traction(enriched_text)



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

        "market_score": investment_score.get("market_score"),
        "team_score": investment_score.get("team_score"),
        "product_score": investment_score.get("product_score"),
        "competition_score": investment_score.get("competition_score"),
        "traction_score": investment_score.get("traction_score"),
        "financial_score": investment_score.get("financial_score"),
        "overall_score": investment_score.get("overall_score"),
        "recommendation": investment_score.get("recommendation"),
        
}