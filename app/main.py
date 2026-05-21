from ai.summarize import summarize_company

def load_company_data():

    with open("ai-due-diligence-copilot/app/data/sample_company.txt", "r") as file:
        return file.read()
    
def main():

    company_text = load_company_data()

    summary = summarize_company(company_text)

    print("\nCOMPANY SUMMARY:\n")
    print(summary)

main()