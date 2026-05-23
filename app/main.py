from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks
from ai.memo_generator import generate_investment_memo

def load_company_data():

    with open("ai-due-diligence-copilot/app/data/sample_company.txt", "r") as file:
        return file.read()
    
def main():

    company_text = load_company_data()

    summary = summarize_company(company_text)

    risk_analysis = analyze_risks(company_text)

    memo = generate_investment_memo(company_text)

    print("\nCOMPANY SUMMARY:\n")
    print(summary)

    print("\nRISK ANALYSIS:\n")
    print(risk_analysis)

    print("\nINVESTMENT MEMO\n")
    print(memo)

main()