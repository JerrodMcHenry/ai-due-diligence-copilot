from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import MarketAnalysisResult

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
                "content": (
                    "You are a disciplined venture capital market analyst. "
                    "You do not invent market size numbers. Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""
Analyze the market opportunity for this startup using the SIE Market Intelligence methodology.

Startup and research context:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Evidence-based market summary. Clearly separate verified facts from inferences.",
  "confidence": "Low",
  "tam": "UNKNOWN or directly supported value only",
  "sam": "UNKNOWN or directly supported value only",
  "som": "UNKNOWN or directly supported value only",
  "growth_rate": "UNKNOWN or directly supported value only",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "score_breakdown": {{
    "pillar": "Market",
    "confidence": "Low",
    "scoring_summary": "Brief explanation of how the market score was determined.",
    "subscores": [
      {{
        "name": "Market Size",
        "score": 0,
        "weight": 0.25,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Market Growth",
        "score": 0,
        "weight": 0.20,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Market Timing",
        "score": 0,
        "weight": 0.20,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Competitive Intensity",
        "score": 0,
        "weight": 0.15,
        "rationale": "Why this score was assigned.",
        "evidence": [],
        "recommendations": []
      }},
      {{
        "name": "Customer Demand",
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
- Do not invent TAM, SAM, SOM, market size, market share, revenue, transaction volume, customer counts, or growth rates.
- Do not estimate numbers unless they are explicitly stated in the provided context.
- For TAM, SAM, and SOM, only return values if they are explicitly stated in the provided context.
- Do not derive, calculate, estimate, or infer TAM, SAM, or SOM from market share, revenue, payment volume, customer count, or other metrics.
- If TAM, SAM, SOM, or growth_rate is not explicitly provided, return UNKNOWN.
- If you make a qualitative assessment, label it as an inference.
- Be conservative and evidence-based.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Market subscores must use exactly these names and weights:
  - Market Size: 0.25
  - Market Growth: 0.20
  - Market Timing: 0.20
  - Competitive Intensity: 0.15
  - Customer Demand: 0.20
- Each subscore score must be from 0 to 10.
- Each subscore must include rationale, evidence, and recommendations.
- Do not include markdown.
- Do not wrap the JSON in triple backticks.
""",
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)

        if "market_summary" not in data:
            data["market_summary"] = data.get("summary")

        return MarketAnalysisResult(**data)

    except Exception:
        return MarketAnalysisResult(
            summary="Unable to parse market analysis",
            confidence="Low",
            tam="UNKNOWN",
            sam="UNKNOWN",
            som="UNKNOWN",
            growth_rate="UNKNOWN",
        )