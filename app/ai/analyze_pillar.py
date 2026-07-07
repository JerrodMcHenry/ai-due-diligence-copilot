import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from ai.scoring import get_scoring_dimensions, finalize_pillar_score
from ai.scoring_methodology import SCORING_METHODOLOGY

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
        f'        "rationale": "Explain how the evidence maps to the SIE Scoring Methodology.",\n'
        f'        "evidence": [],\n'
        f'        "recommendations": []\n'
        f'      }}'
        for name, weight in dimensions
    )


def format_scoring_methodology(pillar: str) -> str:
    methodology = SCORING_METHODOLOGY.get(pillar)

    if not methodology:
        return "No pillar-specific methodology available."

    sections = []

    for dimension in methodology:
        section = f"""
Dimension: {dimension.name}
Weight: {dimension.weight}

Question:
{dimension.question}

Description:
{dimension.description}

Score guidance:
9-10: {dimension.score_9_10}
7-8: {dimension.score_7_8}
5-6: {dimension.score_5_6}
3-4: {dimension.score_3_4}
0-2: {dimension.score_0_2}

Strong signals:
"""

        for signal in dimension.strong_signals:
            section += f"- {signal}\n"

        section += "\nWeak signals:\n"

        for signal in dimension.weak_signals:
            section += f"- {signal}\n"

        sections.append(section)

    return "\n".join(sections)

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
        extra_fields_json += (
    f'  "{field_name}": "Brief string only. {description}",\n'
)

    extra_rules_text = "\n".join(f"- {rule}" for rule in extra_rules)

    return f"""
Analyze this startup using the SIE {pillar} Intelligence methodology.

Startup and research context:
{company_text}

SIE Scoring Methodology:
{format_scoring_methodology(pillar)}

Apply the SIE Scoring Methodology exactly.

Important scoring rules:
- Score business quality, not pitch-deck completeness.
- Missing information lowers confidence, not the score by itself.
- Only assign low scores when evidence shows weak performance.
- Strong objective operating metrics should outweigh missing secondary details.
- Evaluate the company relative to its stage.
- If stage is not explicitly stated, infer it from revenue, customer count, funding round, product maturity, and GTM maturity.
- Use the methodology above before assigning every subscore.
- Explain how the evidence supports each score.

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

Investor evaluation principles:
- You are evaluating intrinsic startup quality.
- You are not grading documentation quality.
- Unknown does not mean weak.
- Low confidence does not automatically mean a low score.
- Revenue, revenue growth, retention, churn, paying customers, gross margin, CAC payback, LTV:CAC, runway, founder experience, product adoption, and enterprise adoption are high-value evidence.
- TAM estimates, market reports, vision statements, and pitch claims are lower-value evidence.
- Strong retention should increase confidence in product quality, customer value, execution, and commercial validation.
- Strong founder experience should increase confidence in execution, hiring, fundraising, and strategic capability.
- Deep workflow integrations can be a source of defensibility.
- Do not assume patents are required for defensibility.

Stage-aware evaluation:
- Pre-seed: prioritize founder quality, problem insight, customer discovery, MVP quality, and early validation.
- Seed: prioritize early PMF, paying customers, retention signals, product maturity, and GTM learning.
- Series A: prioritize repeatable revenue growth, scalable GTM, retention, unit economics, product maturity, and execution quality.
- Series B+: prioritize operational excellence, financial efficiency, market leadership, scalability, and competitive moat.

Scoring scale:
- 9-10: Exceptional for this stage.
- 7-8: Strong for this stage.
- 5-6: Average or mixed for this stage.
- 3-4: Weak, with evidence-supported concerns.
- 0-2: Very weak, little validation, or evidence of poor performance.

Consistency requirements:
- The summary and subscores must agree.
- Do not describe a pillar as strong and then assign weak scores.
- Do not assign low scores solely because information is missing.
- Every weakness must be evidence-based.
- Every recommendation must be actionable.
- Confidence must be Low, Medium, or High.
- Scores must be 0 to 10.
- Never return null scores.
- Do not invent facts.
- Return valid JSON only.
- Do not include markdown.
- Do not wrap JSON in triple backticks.
- Extra fields outside score_breakdown must always be strings, not objects.
- Only score_breakdown.subscores may contain score, weight, rationale, evidence, and recommendations.
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
                    "You are a General Partner at a top-tier venture capital firm. "
                    "You evaluate intrinsic business quality, not pitch quality. "
                    "You distinguish missing evidence from poor business performance. "
                    "You score companies relative to their stage. "
                    "You apply the SIE Scoring Methodology exactly. "
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
        temperature=0.2,
    )

    content = response.choices[0].message.content

    try:
        data = parse_json_from_response(content)
        result = result_model(**data)

        if result.score_breakdown:
            result.score_breakdown = finalize_pillar_score(
                result.score_breakdown
            )

        return result

    except Exception as e:
        print(f"\n\nERROR IN {pillar.upper()} ANALYSIS")
        print(e)
        print(content)
        raise