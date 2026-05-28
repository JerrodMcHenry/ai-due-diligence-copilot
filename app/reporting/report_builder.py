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