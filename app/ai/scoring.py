from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in scoring response.")

    return json.loads(match.group(0))


def generate_investment_score(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst scoring startup investment opportunities. Return only valid JSON."
            },
            {
                "role": "user",
                "content": f"""
Score this startup as an investment opportunity.

Startup:
{company_text}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not wrap the JSON in triple backticks.

Return exactly this structure:
{{
  "overall_score": 0,
  "market_score": 0,
  "competition_score": 0,
  "risk_score": 0,
  "product_score": 0,
  "recommendation": "string"
}}

overall_score should be 0 to 100.
market_score, competition_score, risk_score, and product_score should be 0 to 10.
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return parse_json_from_response(content)

    except Exception:
        return {
            "overall_score": 0,
            "market_score": 0,
            "competition_score": 0,
            "risk_score": 0,
            "product_score": 0,
            "recommendation": "Unable to parse scoring output"
        }