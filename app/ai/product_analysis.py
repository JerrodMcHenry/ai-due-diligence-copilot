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
                "content": (
                    "You are a venture capital analyst evaluating startup "
                    "product quality and defensibility. Return only valid JSON."
                ),
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
  "product_maturity": "Assessment of product completeness, reliability, roadmap maturity, and readiness for scale.",
  "score_breakdown": {{
    "pillar": "Product",
    "confidence": "Low",
    "scoring_summary": "Brief explanation of how the product score was determined.",
    "subscores": [
      {{
        "name": "Customer Value",
        "score": 0,
        "weight": 0.25,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Differentiation",
        "score": 0,
        "weight": 0.20,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Usability",
        "score": 0,
        "weight": 0.15,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Defensibility",
        "score": 0,
        "weight": 0.20,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Adoption Potential",
        "score": 0,
        "weight": 0.20,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }}
    ]
  }}
}}

Rules:
- Confidence must be only Low, Medium, or High.
- Score breakdown confidence must also be only Low, Medium, or High.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Do not invent product features.
- If product details are missing, say what is missing.
- Product subscores must use exactly these names and weights:
  - Customer Value: 0.25
  - Differentiation: 0.20
  - Usability: 0.15
  - Defensibility: 0.20
  - Adoption Potential: 0.20
- Each subscore score must be from 0 to 10.
- Each subscore must include rationale, evidence, and recommendations.
- Do not include markdown.
- Do not wrap the JSON in triple backticks.
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