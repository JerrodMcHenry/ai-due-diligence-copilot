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
        raise ValueError("No JSON object found in market analysis response.")

    return json.loads(match.group(0))


def analyze_market(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a disciplined venture capital market analyst. You do not invent market size numbers."
            },
            {
                "role": "user",
                "content": f"""
Analyze the market opportunity for this startup using only the information provided below.

Startup and research context:
{company_text}

Rules:
- Do not invent TAM, SAM, SOM, market size, market share, revenue, transaction volume, customer counts, or growth rates.
- Do not estimate numbers unless they are explicitly stated in the provided context.
- For TAM, SAM, and SOM:

Only return values if they are explicitly stated in the provided context.

Do not derive, calculate, estimate, or infer TAM, SAM, or SOM from market share, revenue, payment volume, customer count, or other metrics.

If not explicitly provided, return UNKNOWN.
- If you make a qualitative assessment, label it as an inference.
- Be conservative and evidence-based.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations outside the JSON.

Return exactly this JSON structure:

{{
    "tam": "UNKNOWN or directly supported value only",
    "sam": "UNKNOWN or directly supported value only",
    "som": "UNKNOWN or directly supported value only",
    "growth_rate": "UNKNOWN or directly supported value only",
    "market_summary": "Evidence-based summary. Clearly separate verified facts from inferences."
}}
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return parse_json_from_response(content)
    except Exception:
        return {
            "tam": "UNKNOWN",
            "sam": "UNKNOWN",
            "som": "UNKNOWN",
            "growth_rate": "UNKNOWN",
            "market_summary": "Unable to parse market analysis"
        }