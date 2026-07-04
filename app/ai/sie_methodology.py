import json
import re
from openai import OpenAI
from models.startup import SIEMethodologyAnalysis

client = OpenAI()


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def generate_sie_methodology_analysis(enriched_text: str) -> SIEMethodologyAnalysis:
    prompt = f"""
You are the Startup Intelligence Engine.

Analyze the startup using the SIE Intelligence Methodology.

Return ONLY valid JSON.

Use this exact structure:

{{
  "context": {{
    "company_name": null,
    "industry": null,
    "business_model": null,
    "company_stage": null,
    "funding_stage": null
  }},
  "market": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "team": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "product": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "execution": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "traction": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "financial_health": {{
    "score": null,
    "confidence": "Low",
    "summary": null,
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "startup_intelligence_score": null,
  "milestone_readiness_score": null,
  "momentum_score": null,
  "confidence_score": null,
  "executive_coaching_summary": null,
  "next_actions": []
}}

Rules:
- Scores must be 0 to 100.
- Confidence must be only Low, Medium, or High.
- Evidence must cite facts from the provided company information or research context.
- Strengths must be specific.
- Weaknesses must be specific.
- Recommendations must be actionable.
- If information is missing, say what is missing.
- Do not invent fake metrics.
- Keep each list to 3 to 5 items.

Startup information:
{enriched_text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a rigorous startup analyst. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    data = extract_json(content)

    return SIEMethodologyAnalysis(**data)