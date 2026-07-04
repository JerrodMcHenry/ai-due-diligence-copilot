from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import FounderAnalysisResult

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in founder analysis response.")

    return json.loads(match.group(0))


def analyze_founders(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup founding teams. Return only valid JSON."
            },
            {
                "role": "user",
                "content": f"""
Analyze the founding team for this startup.

Startup:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Overall evidence-based assessment of the founding team.",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "founder_market_fit": "Assessment of founder-market fit.",
  "fundraising_signal": "Assessment of the team's fundraising signal."
}}

Rules:
- Confidence must be only Low, Medium, or High.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Do not invent founder credentials.
- If founder details are missing, say what is missing.
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)

        # Temporary backward compatibility
        data["founder_strengths"] = "; ".join(data.get("strengths", []))
        data["domain_expertise"] = data.get("founder_market_fit")
        data["execution_risk"] = "; ".join(data.get("weaknesses", []))
        data["overall_assessment"] = data.get("summary")

        return FounderAnalysisResult(**data)

    except Exception:
        return FounderAnalysisResult(
            summary="Unable to parse founder analysis",
            confidence="Low",
            founder_market_fit="Unable to parse founder analysis",
            fundraising_signal="Unable to parse founder analysis",
        )