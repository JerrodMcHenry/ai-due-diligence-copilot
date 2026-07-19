import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.ai.scoring import (
    finalize_pillar_score,
    get_scoring_dimensions,
)
from app.ai.scoring_methodology import SCORING_METHODOLOGY


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def parse_json_from_response(content: str) -> dict[str, Any]:
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
    Build the required JSON shape for all configured subscores.

    Values are placeholders that the model must replace.
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
    Convert the structured SIE methodology into pillar-specific
    instructions that the model can evaluate dimension by dimension.
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
- Exact quantitative metrics are not required when credible qualitative signals are sufficient.
- Do not mark an Inferred dimension Unavailable merely because quantitative metrics are absent.
- Do not infer performance from brand reputation alone.
- Do not use hindsight or future company outcomes.

PRIVATE

- Score only when relevant internal metrics or explicitly disclosed operating data are available.
- If the required private evidence is unavailable:
  - use evidence_status "Unavailable"
  - use score null
  - use confidence "Low"
  - leave evidence empty
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
- evidence must be empty.
- missing_information must identify the evidence required.
- recommendations should describe the next diligence step.
- never use a placeholder numeric score.

Missing information is not evidence of weak performance.

Only assign a low numeric score when affirmative evidence supports weak
performance, poor execution, or material risk.

==================================================
PUBLIC ANALYSIS RULES
==================================================

This is currently a public startup intelligence analysis.

Private founder metrics are usually not observable from public evidence.

For Private dimensions, return score null and evidence_status "Unavailable"
unless relevant internal or explicitly disclosed evidence is provided.

Do not penalize the company because private information is unavailable.

Publicly observable financial evidence may still be used when available,
including:

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
- Every evidence item must be traceable to the supplied startup information
  or period-appropriate research.

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
- Strong qualitative evidence can support a high score for Public and
  Inferred dimensions.
- Do not require quantitative metrics for dimensions that can be responsibly
  assessed using public facts or credible inference.
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
- Do not describe a pillar as strong and then assign weak scores without
  explaining the contradiction.
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
- For Unavailable subscores, evidence must be empty.
- For Observed and Inferred subscores, evidence must not be empty.
- Extra fields outside score_breakdown must always be strings, not objects.
- Only score_breakdown.subscores may contain score, weight, rationale,
  evidence, recommendations, confidence, evidence_status, and
  missing_information.
- Return valid JSON only.
- Do not include markdown.
- Do not wrap JSON in triple backticks.

Additional pillar rules:

{extra_rules_text}
"""


def get_methodology_by_name(
    pillar: str,
) -> dict[str, Any]:
    """
    Return the configured scoring dimensions indexed by dimension name.
    """
    return {
        dimension.name: dimension
        for dimension in SCORING_METHODOLOGY.get(
            pillar,
            [],
        )
    }


def validate_dimension_names(
    pillar: str,
    score_breakdown,
) -> list[str]:
    """
    Validate that the response contains every configured dimension
    exactly once and does not introduce unknown dimensions.
    """
    methodology_by_name = get_methodology_by_name(
        pillar
    )

    expected_names = set(
        methodology_by_name
    )

    returned_names = [
        subscore.name
        for subscore in score_breakdown.subscores
    ]

    returned_name_set = set(
        returned_names
    )

    errors: list[str] = []

    missing_names = expected_names - returned_name_set
    unknown_names = returned_name_set - expected_names

    if missing_names:
        errors.append(
            "Missing scoring dimensions: "
            + ", ".join(
                sorted(missing_names)
            )
        )

    if unknown_names:
        errors.append(
            "Unknown scoring dimensions: "
            + ", ".join(
                sorted(unknown_names)
            )
        )

    if len(returned_names) != len(returned_name_set):
        errors.append(
            "Duplicate scoring dimensions were returned."
        )

    return errors


def validate_evidence_requirements(
    pillar: str,
    score_breakdown,
) -> list[str]:
    """
    Validate model output against methodology requirements.

    This does not calculate scores. It rejects structurally invalid
    or internally contradictory subscore output.
    """
    methodology_by_name = get_methodology_by_name(
        pillar
    )

    errors = validate_dimension_names(
        pillar=pillar,
        score_breakdown=score_breakdown,
    )

    for subscore in score_breakdown.subscores:
        dimension = methodology_by_name.get(
            subscore.name
        )

        if dimension is None:
            continue

        requirement = dimension.evidence_requirement
        status = subscore.evidence_status
        score = subscore.score
        evidence = subscore.evidence or []
        missing_information = (
            subscore.missing_information or []
        )
        rationale = (
            subscore.rationale or ""
        ).strip()

        rationale_lower = rationale.lower()

        if abs(
            subscore.weight - dimension.weight
        ) > 0.0001:
            errors.append(
                f"{subscore.name}: returned weight "
                f"{subscore.weight} does not match configured "
                f"weight {dimension.weight}."
            )

        if score is not None and not 0 <= score <= 10:
            errors.append(
                f"{subscore.name}: score must be between 0 and 10."
            )

        if status == "Unavailable":
            if score is not None:
                errors.append(
                    f"{subscore.name}: Unavailable evidence must use "
                    f"score null."
                )

            if subscore.confidence != "Low":
                errors.append(
                    f"{subscore.name}: Unavailable evidence must use "
                    f"Low confidence."
                )

            if evidence:
                errors.append(
                    f"{subscore.name}: Unavailable evidence must use "
                    f"an empty evidence list."
                )

            if not missing_information:
                errors.append(
                    f"{subscore.name}: Unavailable evidence must list "
                    f"missing information."
                )

        elif status in {"Observed", "Inferred"}:
            if score is None:
                errors.append(
                    f"{subscore.name}: {status} evidence requires a "
                    f"numeric score."
                )

            if not evidence:
                errors.append(
                    f"{subscore.name}: {status} evidence requires "
                    f"supporting evidence."
                )

            if status == "Inferred" and len(evidence) < 2:
                errors.append(
                    f"{subscore.name}: Inferred evidence requires at "
                    f"least two credible supporting signals."
                )

        else:
            errors.append(
                f"{subscore.name}: invalid evidence_status "
                f"{status!r}."
            )

    

        if (
            requirement == "Public"
            and status == "Unavailable"
):
            errors.append(
                f"{subscore.name}: Public dimensions must receive a numeric "
                f"score using the supplied company information. Public "
                f"dimensions may not be marked Unavailable."
    )


        if (
            requirement == "Private"
            and status in {"Observed", "Inferred"}
        ):
            private_evidence_terms = (
                "arr",
                "burn",
                "cac",
                "cash",
                "churn",
                "customer concentration",
                "gross margin",
                "grr",
                "ltv",
                "margin",
                "mrr",
                "nrr",
                "retention",
                "revenue",
                "runway",
            )

            combined_private_evidence = " ".join(
                [
                    rationale_lower,
                    *(
                        str(item).lower()
                        for item in evidence
                    ),
                ]
            )

            contains_private_evidence = any(
                term in combined_private_evidence
                for term in private_evidence_terms
            )

            if not contains_private_evidence:
                errors.append(
                    f"{subscore.name}: Private dimensions require "
                    f"explicitly disclosed internal or financial "
                    f"evidence before receiving a numeric score."
                )

    return errors


def build_correction_prompt(
    original_prompt: str,
    original_content: str,
    validation_errors: list[str],
) -> str:
    """
    Build one correction request for outputs that violate the
    methodology or response contract.
    """
    formatted_errors = "\n".join(
        f"- {error}"
        for error in validation_errors
    )

    return f"""
The previous response violated the SIE methodology or output contract.

Validation errors:

{formatted_errors}

Return a corrected version of the entire JSON object.

Correction rules:

- Before leaving a Public or Inferred dimension Unavailable, search the
  supplied company information again for relevant qualitative evidence.
- Company-provided facts count as supplied evidence.
- Exact numerical metrics are not required for Public dimensions.
- An Inferred dimension may be scored when at least two concrete signals
  support a limited conclusion.
- Do not create evidence merely to avoid an Unavailable result.
- If no relevant evidence truly exists after re-evaluation, preserve null.
- Preserve all valid dimensions, scores, evidence, and fields.
- Correct only the dimensions involved in validation errors.
- Do not remove any configured scoring dimensions.
- Do not add new scoring dimensions.
- Preserve the configured name and weight for every dimension.
- Public dimensions may be scored from credible public qualitative evidence.
- Inferred dimensions must receive a numeric score when at least two credible
  and independent signals support an assessment.
- Exact quantitative metrics are not required for Public or Inferred
  dimensions.
- Private dimensions must remain null when relevant internal evidence is
  unavailable.
- Unavailable dimensions must have:
  - score null
  - confidence Low
  - an empty evidence list
  - non-empty missing_information
- Observed and Inferred dimensions must have:
  - a numeric score from 0 to 10
  - non-empty evidence
- Do not use hindsight.
- Do not invent facts.
- Return valid JSON only.
- Do not include markdown.

Original analysis request:

{original_prompt}

Previous JSON response:

{original_content}
"""


def call_analysis_model(
    system_content: str,
    user_content: str,
    temperature: float,
) -> str:
    """
    Make one model call and return response text.
    """
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        temperature=temperature,
    )

    return (
        response.choices[0].message.content
        or ""
    )


def print_raw_subscores(
    pillar: str,
    score_breakdown,
) -> None:
    """
    Temporary calibration logging.

    Remove or replace with structured logging after calibration.
    """
    print(
        "\n" + "=" * 70
    )
    print(
        f"{pillar.upper()} RAW SUBSCORES"
    )
    print(
        "=" * 70
    )

    for subscore in score_breakdown.subscores:
        print(
            f"{subscore.name:<30}"
            f" Score: {str(subscore.score):<5}"
            f" | Evidence: {subscore.evidence_status:<11}"
            f" | Confidence: {subscore.confidence}"
        )

    print(
        "=" * 70 + "\n"
    )


def analyze_pillar(
    pillar: str,
    company_text: str,
    result_model,
    system_message: str | None = None,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
):
    system_content = system_message or (
        "You are a General Partner at a top-tier venture capital firm. "
        "You evaluate intrinsic startup quality, not pitch quality. "
        "You apply each scoring dimension's Public, Inferred, or Private "
        "evidence requirement exactly. "
        "Public and Inferred dimensions may be scored using credible "
        "qualitative evidence. "
        "Unavailable private information must produce a null score. "
        "You do not use hindsight during historical calibration. "
        "Return only valid JSON."
    )

    user_prompt = build_pillar_prompt(
        pillar=pillar,
        company_text=company_text,
        extra_fields=extra_fields,
        extra_rules=extra_rules,
    )

    content = call_analysis_model(
        system_content=system_content,
        user_content=user_prompt,
        temperature=0.0,
    )

    latest_content = content

    try:
        data = parse_json_from_response(content)

        result = result_model(**data)

        validation_errors = validate_evidence_requirements(
            pillar=pillar,
            score_breakdown=result.score_breakdown,
        )

        if validation_errors:
            correction_prompt = build_correction_prompt(
                original_prompt=user_prompt,
                original_content=content,
                validation_errors=validation_errors,
            )

            corrected_content = call_analysis_model(
                system_content=system_content,
                user_content=correction_prompt,
                temperature=0.0,
            )

            latest_content = corrected_content

            corrected_data = parse_json_from_response(
                corrected_content
            )

            result = result_model(**corrected_data)

            remaining_errors = validate_evidence_requirements(
                pillar=pillar,
                score_breakdown=result.score_breakdown,
            )

            if remaining_errors:
                print(
                    f"\nWARNING: Corrected {pillar} analysis still "
                    "has validation issues:"
                )

                for validation_error in remaining_errors:
                    print(f"- {validation_error}")

        print_raw_subscores(
            pillar=pillar,
            score_breakdown=result.score_breakdown,
        )

        result.score_breakdown = finalize_pillar_score(
            result.score_breakdown
        )

        return result

    except Exception as error:
        print(
            f"\n\nERROR IN {pillar.upper()} ANALYSIS"
        )
        print(error)
        print(latest_content)
        raise