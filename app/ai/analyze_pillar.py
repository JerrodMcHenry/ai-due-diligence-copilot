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

    return ",\n".join(
        f'      {{\n'
        f'        "name": "{name}",\n'
        f'        "score": null,\n'
        f'        "weight": {weight},\n'
        f'        "confidence": "Low",\n'
        f'        "evidence_status": "Unavailable",\n'
        f'        "rationale": "Explain how the available evidence maps to the SIE Scoring Methodology.",\n'
        f'        "evidence": [],\n'
        f'        "recommendations": [],\n'
        f'        "missing_information": []\n'
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
==================================================
Dimension: {dimension.name}
Weight: {dimension.weight}

Question:
{dimension.question}

Description:
{dimension.description}

Stage Guidance:
{dimension.stage_guidance}

Score Guidance

9-10
{dimension.score_9_10}

7-8
{dimension.score_7_8}

5-6
{dimension.score_5_6}

3-4
{dimension.score_3_4}

0-2
{dimension.score_0_2}

Evidence Priority:
"""

        for item in dimension.evidence_priority:
            section += f"- {item}\n"

        section += "\nStrong Signals:\n"

        for item in dimension.strong_signals:
            section += f"- {item}\n"

        section += "\nWeak Signals:\n"

        for item in dimension.weak_signals:
            section += f"- {item}\n"

        section += "\nCommon Mistakes:\n"

        for item in dimension.common_mistakes:
            section += f"- {item}\n"

        section += "\nBenchmark Examples:\n"

        if dimension.benchmark_examples:
            for item in dimension.benchmark_examples:
                section += f"- {item}\n"
        else:
            section += "- None specified.\n"

        section += "\nDiligence Questions:\n"

        if dimension.diligence_questions:
            for item in dimension.diligence_questions:
                section += f"- {item}\n"
        else:
            section += "- None specified.\n"

        section += "\n"

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

You MUST evaluate every scoring dimension using the SIE Scoring Methodology above.

For EACH scoring dimension:

1. Read the Question.
2. Apply the Description.
3. Apply the Stage Guidance.
4. Compare the company against the Score Guidance.
5. Prioritize evidence according to Evidence Priority.
6. Avoid the listed Common Mistakes.
7. Use Benchmark Examples when comparable.
8. Consider the Diligence Questions before assigning the score.
9. Assign either:
   - a numeric score from 0 to 10 for Observed or Inferred evidence, or
   - null for Unavailable evidence.
10. Write a rationale explaining how the evidence maps to the methodology.

General principles:

EVIDENCE STATUS RULES

For every subscore, assign exactly one evidence_status:

Observed:
- Direct evidence supports the assessment.
- Examples: disclosed revenue, retention, customer count, founder history, product behavior, or verified operating metrics.
- score must be a number from 0 to 10.

Inferred:
- Multiple credible indirect signals support a reasonable estimate.
- The rationale must identify the signals and clearly state that the assessment is inferred.
- score must be a number from 0 to 10.
- confidence should usually be Low or Medium.

Unavailable:
- The dimension cannot be responsibly evaluated from the available evidence.
- score must be null.
- confidence must be Low.
- evidence should be empty unless it documents why the information is unavailable.
- missing_information must identify the evidence required.
- Do not substitute 0, 3, 5, 6, or any other placeholder score.

Missing information is not weak performance.
Only assign a low numeric score when affirmative evidence supports weak performance.

PUBLIC ANALYSIS RULES

This is a public startup intelligence analysis.

Private founder metrics are usually not observable from public evidence.

For the following dimensions, use evidence_status "Unavailable" and score null unless direct or credible public evidence is provided:

- Unit Economics
- Burn Efficiency
- Runway
- private CAC or LTV metrics
- private cash balance
- private operating forecasts

Do not penalize the company because these private metrics are unavailable.

Publicly observable financial evidence such as disclosed revenue, pricing, funding history, revenue model, public margins, or documented capital efficiency may still be scored when available.

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



Consistency requirements:
- The summary and subscores must agree.
- Do not describe a pillar as strong and then assign weak scores.
- Do not assign low scores solely because information is missing.
- Every weakness must be evidence-based.
- Every recommendation must be actionable.
- Confidence must be Low, Medium, or High.
- Observed and Inferred subscores must use numeric scores from 0 to 10.
- Unavailable subscores must use score null.
- Never use a placeholder numeric score for unavailable evidence.
- evidence_status must be only Observed, Inferred, or Unavailable.
- Subscore confidence must be only Low, Medium, or High.
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
    "You distinguish observed evidence, reasonable inference, and unavailable information. "
    "Unavailable information must produce a null score rather than a placeholder score. "
    "You score companies relative to their stage and apply the SIE Scoring Methodology exactly. "
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