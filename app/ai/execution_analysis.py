from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.analysis import ExecutionAnalysisResult

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in execution analysis response.")

    return json.loads(match.group(0))


def analyze_execution(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup execution quality. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": f"""
Analyze execution quality for this startup using the SIE Execution Intelligence methodology.

Startup:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Overall evidence-based assessment of startup execution.",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "gtm_execution": "Assessment of go-to-market execution.",
  "product_execution": "Assessment of product execution and delivery.",
  "operational_execution": "Assessment of operational maturity and ability to scale.",
  "strategic_execution": "Assessment of strategic focus, prioritization, and milestone discipline."
}}

Rules:
- Confidence must be only Low, Medium, or High.
- Strengths should be specific bullets, not long paragraphs.
- Weaknesses should be specific bullets, not long paragraphs.
- Evidence should cite facts from the provided startup information.
- Recommendations should be actionable.
- Do not invent milestones, hiring, partnerships, or customer metrics.
- If execution details are missing, say what is missing.
"""
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)
        return ExecutionAnalysisResult(**data)

    except Exception:
        return ExecutionAnalysisResult(
            summary="Unable to parse execution analysis",
            confidence="Low",
            gtm_execution="Unable to parse execution analysis",
            product_execution="Unable to parse execution analysis",
            operational_execution="Unable to parse execution analysis",
            strategic_execution="Unable to parse execution analysis",
        )