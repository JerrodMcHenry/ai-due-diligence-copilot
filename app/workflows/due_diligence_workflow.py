from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo
from ai.structured_analysis import generate_structured_analysis
from ai.competitor_anlalysis import analyze_competitors
from ai.scoring import generate_investment_score
from ai.founder_analysis import analyze_founders

def run_due_diligence(company_text):

    summary = summarize_company(company_text)

    risk_analysis = analyze_risks(company_text)

    competitor_analysis = analyze_competitors(company_text)

    memo = generate_investment_memo(company_text)

    structured_analysis = generate_structured_analysis(company_text)

    investment_score = generate_investment_score(company_text)

    founder_analysis = analyze_founders(company_text)

    return {
        "summary": summary,
        "risk_analysis": risk_analysis,
        "competitor_analysis": competitor_analysis,
        "memo": memo,
        "structured_analysis": structured_analysis,
        "investment_score": investment_score,
        "founder_analysis": founder_analysis
        
    }