from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import ProductAnalysisResult

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in product analysis response.")

    return json.loads(match.group(0))


def analyze_product(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup product quality and defensibility. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": f"""
Analyze the product for this startup using the SIE Product Intelligence methodology.

Startup:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Overall evidence-based assessment of the product.",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "customer_value": "Assessment of how clearly the product solves an important customer problem.",
  "technical_defensibility": "Assessment of technical differentiation, proprietary technology, AI capability, integrations, or defensibility.",
  "ease_of_adoption": "Assessment of how easy it is for target customers to adopt and use the product.",
  "product_maturity": "Assessment of product completeness, reliability, roadmap maturity, and readiness for scale."
}}

Rules:
- Confidence must be only Low, Medium, or High.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Do not invent product features.
- If product details are missing, say what is missing.
"""
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)
        return ProductAnalysisResult(**data)

    except Exception:
        return ProductAnalysisResult(
            summary="Unable to parse product analysis",
            confidence="Low",
            customer_value="Unable to parse product analysis",
            technical_defensibility="Unable to parse product analysis",
            ease_of_adoption="Unable to parse product analysis",
            product_maturity="Unable to parse product analysis",
        )