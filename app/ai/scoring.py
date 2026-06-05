from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_investment_score(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst scoring startup investment opportunities."
            },
            {
                "role": "user",
                "content": f"""
Score this startup as an investment opportunity.

Startup:
{company_text}

Return ONLY valid JSON with these fields:
{{
  "overall_score": 0,
  "market_score": 0,
  "competition_score": 0,
  "risk_score": 0,
  "product_score": 0,
  "recommendation": "string"
}}

Scores should be 0 to 100 for overall_score and 0 to 10 for category scores.
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "overall_score": 0,
            "market_score": 0,
            "competition_score": 0,
            "risk_score": 0,
            "product_score": 0,
            "recommendation": "Unable to parse scoring output"
        }