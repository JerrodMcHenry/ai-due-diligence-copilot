from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo
from ai.structured_analysis import generate_structured_analysis
from ai.competitor_anlalysis import analyze_competitors
from ai.scoring import generate_investment_score
from ai.founder_analysis import analyze_founders
from ai.market_analysis import analyze_market
from ai.research_enrichment import enrich_research


def run_due_diligence(company_text):

    research_context = enrich_research(company_text)

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

    founder_analysis = analyze_founders(enriched_text)

    market_analysis = analyze_market(enriched_text)

    return {
        "summary": summary,
        "risk_analysis": risk_analysis,
        "competitor_analysis": competitor_analysis,
        "memo": memo,
        "structured_analysis": structured_analysis,
        "investment_score": investment_score,
        "founder_analysis": founder_analysis,
        "market_analysis": market_analysis
    }