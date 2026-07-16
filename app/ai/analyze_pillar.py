import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from ai.scoring import (
    finalize_pillar_score,
    get_scoring_dimensions,
)
from ai.scoring_methodology import SCORING_METHODOLOGY


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def parse_json_from_response(content: str) -> dict:
    """
    Parse a JSON object from the model response.

    The model is instructed to return JSON only, but this fallback
    handles responses that accidentally include surrounding text.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        content,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            "No JSON object found in pillar analysis response."
        )

    return json.loads(
        match.group(0)
    )


def format_subscores_for_prompt(
    pillar: str,
) -> str:
    """
    Build the required JSON schema for every configured subscore.

    The initial values are examples of the required shape. The model
    must replace them based on the available evidence.
    """
    dimensions = get_scoring_dimensions(
        pillar
    )

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


def format_scoring_methodology(
    pillar: str,
) -> str:
    """
    Convert the structured SIE methodology into instructions that the
    model can apply dimension by dimension.
    """
    methodology = SCORING_METHODOLOGY.get(
        pillar
    )

    if not methodology:
        return (
            "No pillar-specific methodology available."
        )

    sections: list[str] = []

    for dimension in methodology:
        section = f"""
==================================================
Dimension: {dimension.name}
Weight: {dimension.weight}

Evidence Requirement:
{dimension.evidence_requirement}

Question:
{dimension.question}

Description:
{dimension.description}

Stage Guidance:
{dimension.stage_guidance}

Score Guidance:

9-10:
{dimension.score_9_10}

7-8:
{dimension.score_7_8}

5-6:
{dimension.score_5_6}

3-4:
{dimension.score_3_4}

0-2:
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

        sections.append(
            section
        )

    return "\n".join(
        sections
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
        extra_fields_json += (
            f'  "{field_name}": '
            f'"Brief string only. {description}",\n'
        )

    extra_rules_text = "\n".join(
        f"- {rule}"
        for rule in extra_rules
    )

    return f"""
Analyze this startup using the SIE {pillar} Intelligence Methodology.

Startup and research context:

{company_text}

SIE Scoring Methodology:

{format_scoring_methodology(pillar)}

You MUST evaluate every scoring dimension using the methodology above.

For EACH scoring dimension:

1. Read the Evidence Requirement.
2. Read the Question.
3. Apply the Description.
4. Apply the Stage Guidance.
5. Compare the available evidence against the Score Guidance.
6. Prioritize evidence according to Evidence Priority.
7. Consider the Strong Signals and Weak Signals.
8. Avoid the listed Common Mistakes.
9. Use Benchmark Examples only when genuinely comparable.
10. Consider the Diligence Questions before finalizing the assessment.
11. Assign either:
    - a numeric score from 0 to 10 for Observed or Inferred evidence, or
    - null for Unavailable evidence.
12. Write a rationale explaining exactly how the evidence maps to the methodology.

==================================================
EVIDENCE REQUIREMENT RULES
==================================================

Each scoring dimension has one Evidence Requirement:

PUBLIC

- Score using verifiable public facts or facts explicitly included in the supplied startup information.
- Exact quantitative metrics are not required.
- Valid public evidence may include:
  - market category
  - customer segments
  - known competitors
  - founder history
  - shipped product
  - product behavior
  - pricing
  - integrations
  - funding history
  - customer adoption
  - credible period-appropriate public research
- Use evidence_status "Observed" when direct facts support the score.
- Use evidence_status "Inferred" when multiple credible public signals support the conclusion.
- Do not mark a Public dimension Unavailable merely because exact quantitative metrics are absent.

INFERRED

- Score when at least two credible and independent signals support a reasonable conclusion.
- Use evidence_status "Inferred".
- Confidence should usually be Low or Medium.
- The rationale must identify the signals and explain the inference.
- Do not require exact quantitative metrics when credible qualitative signals are sufficient.
- Do not mark an Inferred dimension Unavailable merely because exact quantitative metrics are absent.
- Do not infer performance from brand reputation alone.
- Do not use hindsight or future company outcomes.

PRIVATE

- Score only when relevant internal metrics or explicitly disclosed operating data are available.
- If the required private evidence is unavailable:
  - use evidence_status "Unavailable"
  - use score null
  - use confidence "Low"
  - leave evidence empty unless it documents the absence
  - list the exact missing information
- Private dimensions commonly include:
  - runway
  - burn
  - cash balance
  - internal forecasts
  - private CAC
  - private LTV
  - private unit economics
  - undisclosed retention metrics

==================================================
EVIDENCE STATUS RULES
==================================================

OBSERVED

- Direct evidence supports the assessment.
- score must be numeric from 0 to 10.
- confidence may be Low, Medium, or High.
- evidence must contain facts supporting the score.

INFERRED

- Multiple credible signals support a reasonable estimate.
- score must be numeric from 0 to 10.
- confidence should usually be Low or Medium.
- the rationale must clearly explain the inference.
- evidence must contain the signals used.

UNAVAILABLE

- The dimension cannot be responsibly evaluated under its Evidence Requirement.
- score must be null.
- confidence must be Low.
- missing_information must identify the evidence required.
- recommendations should explain the next diligence step.
- never use a placeholder numeric score.

Missing information is not evidence of weak performance.

Only assign a low numeric score when affirmative evidence supports weak performance, poor execution, or material risk.

==================================================
PUBLIC ANALYSIS RULES
==================================================

This is currently a public startup intelligence analysis.

Private founder metrics are usually not observable from public evidence.

For Private dimensions, return score null and evidence_status "Unavailable" unless direct or explicitly disclosed evidence is provided.

Do not penalize the company because private information is unavailable.

Publicly observable financial evidence may still be used when available, including:

- disclosed revenue
- disclosed pricing
- disclosed funding history
- disclosed revenue model
- disclosed margins
- disclosed capital efficiency
- disclosed customer concentration
- disclosed retention or churn

==================================================
CALIBRATION TIME-BOUNDARY RULE
==================================================

When the startup information specifies a historical evaluation period:

- Use only evidence available at or before that period.
- Do not use later growth.
- Do not use later products.
- Do not use later funding rounds.
- Do not use later customers.
- Do not use later valuation.
- Do not use eventual outcomes.
- Do not justify an early-stage score using hindsight.
- Every evidence item must be traceable to the supplied startup information or period-appropriate research.

==================================================
GENERAL SCORING PRINCIPLES
==================================================

- Score intrinsic startup quality, not pitch quality.
- Score performance separately from confidence.
- Evaluate the company relative to its stage.
- If stage is not explicitly stated, infer it from:
  - funding
  - revenue
  - customer count
  - team size
  - product maturity
  - go-to-market maturity
- Strong qualitative evidence can support a high score for Public and Inferred dimensions.
- Do not require quantitative metrics for dimensions that can be responsibly assessed using public facts or credible inference.
- Do not invent facts.
- Do not use missing evidence as proof of weakness.
- The summary, rationale, evidence, and score must be internally consistent.
- The weighted pillar score must logically match the written assessment.

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

==================================================
OUTPUT CONSISTENCY REQUIREMENTS
==================================================

- The summary and subscores must agree.
- Do not describe a pillar as strong and then assign weak scores without explaining the contradiction.
- Do not assign low scores solely because information is missing.
- Every strength must be evidence-based.
- Every weakness must be evidence-based.
- Every recommendation must be actionable.
- Pillar confidence must be Low, Medium, or High.
- Subscore confidence must be Low, Medium, or High.
- evidence_status must be only Observed, Inferred, or Unavailable.
- Observed and Inferred subscores must use numeric scores from 0 to 10.
- Unavailable subscores must use score null.
- Never use placeholder numeric scores for unavailable evidence.
- For Unavailable subscores, missing_information must not be empty.
- For Observed and Inferred subscores, evidence must not be empty.
- Extra fields outside score_breakdown must always be strings, not objects.
- Only score_breakdown.subscores may contain score, weight, rationale, evidence, recommendations, confidence, evidence_status, and missing_information.
- Return valid JSON only.
- Do not include markdown.
- Do not wrap JSON in triple backticks.

Additional pillar rules:

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
                    "You evaluate intrinsic startup quality, not pitch quality. "
                    "You apply each scoring dimension's Public, Inferred, or Private evidence requirement exactly. "
                    "You distinguish observed evidence, reasonable inference, and unavailable information. "
                    "Unavailable private information must produce a null score rather than a placeholder score. "
                    "Public and Inferred dimensions may be scored using credible qualitative evidence. "
                    "You do not use hindsight during historical calibration. "
                    "You return only valid JSON."
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

    content = (
        response.choices[0].message.content
        or ""
    )

    try:
        data = parse_json_from_response(
            content
        )

        result = result_model(
            **data
        )

        if result.score_breakdown:
            result.score_breakdown = (
                finalize_pillar_score(
                    result.score_breakdown
                )
            )

        return result

    except Exception as error:
        print(
            f"\n\nERROR IN {pillar.upper()} ANALYSIS"
        )
        print(
            error
        )
        print(
            content
        )
        raise