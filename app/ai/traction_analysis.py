from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import TractionAnalysisResult

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in traction analysis response.")

    return json.loads(match.group(0))


def analyze_traction(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup traction. Return only valid JSON."
            },
            {
                "role": "user",
                "content": f"""
Analyze evidence of traction for this startup.

Startup:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Overall evidence-based assessment of startup traction.",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "customer_growth": "Assessment of customer adoption and customer growth.",
  "revenue_growth": "Assessment of revenue traction and revenue growth.",
  "fundraising_signal": "Assessment of fundraising traction or investor validation."
}}

Rules:
- Confidence must be only Low, Medium, or High.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Do not invent customers.
- Do not invent revenue.
- Do not invent fundraising.
- If evidence is unavailable, say what is missing.
"""
            }
        ],
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)

        # Temporary backward compatibility
        data["customer_signals"] = data.get("customer_growth")
        data["custoner_signals"] = data.get("customer_growth")
        data["growth_signals"] = data.get("revenue_growth")
        data["fundraising_signals"] = data.get("fundraising_signal")
        data["adoption_risk"] = "; ".join(data.get("weaknesses", []))
        data["overall_traction"] = data.get("summary")

        return TractionAnalysisResult(**data)

    except Exception:
        return TractionAnalysisResult(
            summary="Unable to parse traction analysis",
            confidence="Low",
            customer_growth="Unable to parse traction analysis",
            revenue_growth="Unable to parse traction analysis",
            fundraising_signal="Unable to parse traction analysis",
        )