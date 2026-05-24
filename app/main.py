from workflows.due_diligence_workflow import run_due_diligence


def load_company_data(filepath):

    try:
        with open(filepath, "r") as file:
            return file.read()
    
    except FileNotFoundError:
        print("Error: file not found. Please check the file path")
        return None

def save_output(filename, content):
    with open(f"app/outputs/{filename}", "w") as file:
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

def build_structured_report(structured_analysis):
    risks = "\n".join(f"- {risk}" for risk in structured_analysis["key_risks"])
    strengths = "\n".join(f"- {strength}" for strength in structured_analysis["strengths"])
    
    return f"""
# Structured Startup Analysis

## Company Name
{structured_analysis["company_name"]}

## Summary
{structured_analysis["summary"]}

## Key Risks
{risks}

## Strengths
{strengths}

## Recommendation
{structured_analysis["recommendation"]}
"""
def main():

    filepath = input("Enter company filepath: ")

    company_text = load_company_data(filepath)

    if company_text is None:
        return

    results = run_due_diligence(company_text)

    summary = results["summary"]
    risk_analysis = results["risk_analysis"]
    memo = results["memo"]
    structured_analysis = results["structured_analysis"]

    report = build_report(summary, risk_analysis, memo)
    structured_report = build_structured_report(structured_analysis)

    save_output("summary.txt", summary)
    save_output("risk_analysis.txt", risk_analysis)
    save_output("memo.txt", memo)
    save_output("structured_analysis.txt", str(structured_analysis))
    save_output("due_diligence_report.md", report)
    save_output("structured_report.md", structured_report)


    print("\nCOMPANY SUMMARY:\n")
    print(summary)

    print("\nRISK ANALYSIS:\n")
    print(risk_analysis)

    print("\nINVESTMENT MEMO\n")
    print(memo)

    print("\nSTRUCTURED ANALYSIS:\n")
    print(structured_analysis)

    print("\nFULL REPORT GENERATED")

main()