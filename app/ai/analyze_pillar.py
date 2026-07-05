from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from ai.scoring import get_scoring_dimensions

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in pillar analysis response.")

    return json.loads(match.group(0))


def format_subscores_for_prompt(pillar: str) -> str:
    dimensions = get_scoring_dimensions(pillar)

    return "\n".join(
        f'      {{\n'
        f'        "name": "{name}",\n'
        f'        "score": 0,\n'
        f'        "weight": {weight},\n'
        f'        "rationale": "Why this score was assigned.",\n'
        f'        "evidence": [],\n'
        f'        "recommendations": []\n'
        f'      }}'
        for name, weight in dimensions
    )


def build_pillar_prompt(
    pillar: str,
    company_text: str,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
) -> str:
    extra_fields = extra_fields or {}
    extra_rules = extra_rules or []

    extra_fields_json = ""
    for field_name, description in extra_fields.items():
        extra_fields_json += f'  "{field_name}": "{description}",\n'

    extra_rules_text = "\n".join(f"- {rule}" for rule in extra_rules)

    return f"""
Analyze this startup using the SIE {pillar} Intelligence methodology.

Startup and research context:
{company_text}

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Evidence-based {pillar.lower()} assessment.",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
{extra_fields_json}  "score_breakdown": {{
    "pillar": "{pillar}",
    "confidence": "Low",
    "scoring_summary": "Brief explanation of how the {pillar.lower()} score was determined.",
    "subscores": [
{format_subscores_for_prompt(pillar)}
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
- Do not invent facts.
- If information is missing, say what is missing.
- Each subscore score must be from 0 to 10.
- Each subscore must include rationale, evidence, and recommendations.
- Do not include markdown.
- Do not wrap the JSON in triple backticks.
{extra_rules_text}
"""


def analyze_pillar(
    pillar: str,
    company_text: str,
    result_model,
    system_message: str | None = None,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_message
                or (
                    "You are a disciplined venture capital analyst. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": build_pillar_prompt(
                    pillar=pillar,
                    company_text=company_text,
                    extra_fields=extra_fields,
                    extra_rules=extra_rules,
                ),
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)
        return result_model(**data)

    except Exception:
        return result_model(
            summary=f"Unable to parse {pillar.lower()} analysis",
            confidence="Low",
        )