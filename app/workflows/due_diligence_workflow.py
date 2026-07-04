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
from models.startup import SIEMethodologyAnalysis, SIEContext, PillarAnalysis


def build_sie_methodology_analysis(
    structured_analysis,
    investment_score,
    readiness,
    founder_analysis,
    market_analysis,
    traction_analysis,
    risk_analysis,
):
    
    founder_summary = founder_analysis.get("overall_assessment") if isinstance(founder_analysis, dict) else None
    traction_summary = traction_analysis.get("overall_traction") if isinstance(traction_analysis, dict) else None

    return SIEMethodologyAnalysis(
        context=SIEContext(
            company_name=structured_analysis.get("company_name"),
            industry=structured_analysis.get("industry"),
            business_model=structured_analysis.get("business_model"),
            company_stage=structured_analysis.get("stage"),
            funding_stage=structured_analysis.get("funding_stage"),
        ),
        market=PillarAnalysis(
            score=investment_score.get("market_score"),
            confidence=market_analysis.confidence,
            summary=market_analysis.summary,
            evidence=market_analysis.evidence,
            strengths=market_analysis.strengths,
            weaknesses=market_analysis.weaknesses,
            recommendations=market_analysis.recommendations,
),
        team=PillarAnalysis(
            score=investment_score.get("team_score"),
            confidence="Medium",
            summary=founder_summary,
            evidence=[
                founder_analysis.get("founder_strengths"),
                founder_analysis.get("domain_expertise"),
                founder_analysis.get("fundraising_signal"),
            ] if isinstance(founder_analysis, dict) else [],
            strengths=[
                founder_analysis.get("founder_strengths")
            ] if isinstance(founder_analysis, dict) and founder_analysis.get("founder_strengths") else [],
            weaknesses=[
                founder_analysis.get("execution_risk")
            ] if isinstance(founder_analysis, dict) and founder_analysis.get("execution_risk") else [],
            recommendations=[
                "Strengthen evidence of founder-market fit, execution history, and ability to scale go-to-market."
            ],
        ),
        product=PillarAnalysis(
            score=investment_score.get("product_score"),
            confidence="Medium",
            summary=structured_analysis.get("summary"),
            evidence=structured_analysis.get("strengths", []),
            strengths=structured_analysis.get("strengths", []),
            weaknesses=structured_analysis.get("key_risks", []),
            recommendations=[
                "Clarify product differentiation, customer value proposition, and defensibility."
            ],
        ),
        execution=PillarAnalysis(
            score=investment_score.get("competition_score"),
            confidence="Medium",
            summary="Execution risk is inferred from competitive pressure, operational risk, and ability to differentiate.",
            evidence=[risk_analysis] if isinstance(risk_analysis, str) else [],
            weaknesses=structured_analysis.get("key_risks", []),
            recommendations=[
                "Create a clearer execution roadmap tied to milestones, hiring needs, go-to-market strategy, and product delivery."
            ],
        ),
        traction=PillarAnalysis(
            score=investment_score.get("traction_score"),
            confidence="Medium",
            summary=traction_summary,
            evidence=[
                traction_analysis.get("custoner_signals") or traction_analysis.get("customer_signals"),
                traction_analysis.get("growth_signals"),
                traction_analysis.get("partnership_signals"),
                traction_analysis.get("fundraising_signals"),
            ] if isinstance(traction_analysis, dict) else [],
            strengths=[
                traction_analysis.get("overall_traction")
            ] if isinstance(traction_analysis, dict) and traction_analysis.get("overall_traction") else [],
            weaknesses=[
                traction_analysis.get("adoption_risk")
            ] if isinstance(traction_analysis, dict) and traction_analysis.get("adoption_risk") else [],
            recommendations=[
                "Track customer growth, retention, churn, revenue growth, and sales efficiency more explicitly."
            ],
        ),
        financial_health=PillarAnalysis(
            score=investment_score.get("financial_score"),
            confidence="Low",
            summary="Financial health is based on limited available revenue and business model information.",
            evidence=[
                f"Overall financial score: {investment_score.get('financial_score')}",
                f"Business model: {structured_analysis.get('business_model')}",
            ],
            weaknesses=[
                "Runway, burn rate, gross margin, CAC, LTV, churn, and revenue quality are missing or incomplete."
            ],
            recommendations=[
                "Collect burn rate, runway, gross margin, CAC, LTV, churn, expansion revenue, and revenue concentration."
            ],
        ),
        startup_intelligence_score=investment_score.get("overall_score"),
        milestone_readiness_score=readiness.get("readiness_score"),
        momentum_score=None,
        confidence_score=75.0,
        executive_coaching_summary=readiness.get("readiness_summary"),
        next_actions=readiness.get("strengths", []) + readiness.get("weaknesses", []),
    )

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

    sie_analysis = build_sie_methodology_analysis(
    structured_analysis=structured_analysis,
    investment_score=investment_score,
    readiness=readiness,
    founder_analysis=founder_analysis,
    market_analysis=market_analysis,
    traction_analysis=traction_analysis,
    risk_analysis=risk_analysis,
)

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
        "sie_analysis": sie_analysis
        
}