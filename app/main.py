from ai.summarize import summarize_company
from ai.risk_analysis import analyze_risks

def load_company_data():

    with open("app/data/sample_company.txt", "r") as file:
        return file.read()
    
def main():

    company_text = load_company_data()

    summary = summarize_company(company_text)

    risk_analysis = analyze_risks(company_text)

    print("\nCOMPANY SUMMARY:\n")
    print(summary)

    print("\nRISK ANALYSIS:\n")
    print(risk_analysis)

main()