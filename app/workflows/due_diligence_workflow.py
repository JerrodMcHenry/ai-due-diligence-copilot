from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo
from ai.structured_analysis import generate_structured_analysis

def run_due_diligence(company_text):

    summary = summarize_company(company_text)

    risk_analysis = analyze_risks(company_text)

    memo = generate_investment_memo(company_text)

    structured_analysis = generate_structured_analysis(company_text)

    return {
        "summary": summary,
        "risk_analysis": risk_analysis,
        "memo": memo,
        "structured_analysis": structured_analysis
        
    }