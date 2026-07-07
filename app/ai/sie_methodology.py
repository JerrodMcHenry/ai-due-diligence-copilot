import json
import re
from openai import OpenAI

from models.startup import SIEMethodologyAnalysis
from ai.scorecard import build_startup_scorecard


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
    "company_name": "",
    "industry": "",
    "business_model": "",
    "company_stage": "",
    "funding_stage": ""
  }},
  "market": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "team": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "product": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "execution": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "traction": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "financial_health": {{
    "confidence": "Low",
    "summary": "",
    "evidence": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": []
  }},
  "executive_coaching_summary": "",
  "next_actions": []
}}

Rules:
- Do not generate scores.
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
            {
                "role": "system",
                "content": "You are a rigorous startup analyst. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    data = extract_json(content)

    methodology = SIEMethodologyAnalysis(**data)

    scorecard = build_startup_scorecard(methodology)

    methodology.startup_scorecard = scorecard
    methodology.startup_intelligence_score = scorecard.overall_score

    methodology.market.score = scorecard.market.score
    methodology.team.score = scorecard.team.score
    methodology.product.score = scorecard.product.score
    methodology.execution.score = scorecard.execution.score
    methodology.traction.score = scorecard.traction.score
    methodology.financial_health.score = scorecard.financial_health.score

    methodology.market.score_breakdown = scorecard.market
    methodology.team.score_breakdown = scorecard.team
    methodology.product.score_breakdown = scorecard.product
    methodology.execution.score_breakdown = scorecard.execution
    methodology.traction.score_breakdown = scorecard.traction
    methodology.financial_health.score_breakdown = scorecard.financial_health

    return methodology