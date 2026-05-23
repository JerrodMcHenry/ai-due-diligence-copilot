from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo

def load_company_data(filepath):

    with open(filepath, "r") as file:
        return file.read()

def save_output(filename, content):
    with open(f"ai-due-diligence-copilot/app/outputs/{filename}", "w") as file:
        file.write(content)

def build_report(summary, risk_analysis, memo):

    return f"""
# AI Due Diligence Report

## Company Summary

{summary}

## Risk Analysis
{risk_analysis}

##Investment Memo

{memo}
"""
    
def main():

    filepath = "ai-due-diligence-copilot/app/data/sample_company.txt"

    company_text = load_company_data(filepath)

    summary = summarize_company(company_text)

    risk_analysis = analyze_risks(company_text)

    memo = generate_investment_memo(company_text)

    report = build_report(summary, risk_analysis, memo)

    save_output("summary.txt", summary)
    save_output("risk_analysis.txt", risk_analysis)
    save_output("memo.txt", memo)
    save_output("due_diligence_report.md", report)

    print("\nCOMPANY SUMMARY:\n")
    print(summary)

    print("\nRISK ANALYSIS:\n")
    print(risk_analysis)

    print("\nINVESTMENT MEMO\n")
    print(memo)

    print("\nFULL REPORT GENERATED")

main()