from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import FinancialAnalysisResult

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in financial analysis response.")

    return json.loads(match.group(0))


def analyze_financials(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup financial health. Return only valid JSON."
            },
            {
                "role": "user",
                "content": f"""
Analyze the financial health of this startup using the SIE Financial Intelligence methodology.

Startup:

{company_text}

Return ONLY valid JSON.

{{
    "summary": "",
    "confidence": "Low",

    "strengths": [],
    "weaknesses": [],
    "evidence": [],
    "recommendations": [],

    "revenue_quality": "",
    "pricing_model": "",
    "unit_economics": "",
    "burn_rate": "",
    "runway": "",
    "capital_efficiency": "",
    "fundraising_readiness": ""
}}

Rules:

- Confidence must be Low, Medium, or High.
- Never invent financial metrics.
- If burn, runway, CAC, LTV, margins, or funding are unavailable, explicitly state UNKNOWN.
- Separate verified facts from inference.
- Recommendations must be actionable.
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)
        return FinancialAnalysisResult(**data)

    except Exception:
        return FinancialAnalysisResult(
            summary="Unable to parse financial analysis.",
            confidence="Low",
            revenue_quality="UNKNOWN",
            pricing_model="UNKNOWN",
            unit_economics="UNKNOWN",
            burn_rate="UNKNOWN",
            runway="UNKNOWN",
            capital_efficiency="UNKNOWN",
            fundraising_readiness="UNKNOWN",
        )