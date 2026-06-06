from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_market(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst specializing in market sizing."
            },
            {
                "role": "user",
                "content": f"""
Analyze the market opportunity for this startup.

Startup:
{company_text}

Return ONLY valid JSON:

{{
    "tam": "string",
    "sam": "string",
    "som": "string",
    "growth_rate": "string",
    "market_summary": "string"
}}
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "tam": "Unknown",
            "sam": "Unknown",
            "som": "Unknown",
            "growth_rate": "Unknown",
            "market_summary": "Unable to parse market analysis"
        }