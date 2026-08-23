"""
Stage 1 of the two-stage pillar pipeline (SIE Evidence/Scoring
Separation sprint): what evidence exists, and how is it classified.

This stage NEVER produces a numeric score. It determines, per scoring
dimension: evidence_status, confidence, quoted evidence, extracted
signals, missing_information, and a classification rationale -- plus
the pillar-level narrative fields (summary, strengths, weaknesses, the
pillar's own extra fields like tam/sam/som). The scoring stage
(app/ai/pillar_scoring.py) consumes this object; it cannot rediscover
different evidence, because it is never shown the raw text again.

Correction here is scoped per dimension (Phase 5): if one dimension's
evidence assessment fails validation, only that dimension is resent for
correction. Every other dimension's EvidenceAnalysis object is the
exact same Python object returned from the first parse -- never
touched, so it cannot be altered by an unrelated correction.
"""

from typing import Any

from app.ai.scoring import get_scoring_dimensions
from app.ai.scoring_methodology import SCORING_METHODOLOGY
from app.models.evidence_analysis import EvidenceAnalysis, PillarEvidenceAnalysis

from app.ai.pillar_shared import (
    QUANTITATIVE_DISCLOSURE_TERMS,
    call_analysis_model,
    get_methodology_by_name,
    parse_json_from_response,
)


# Shown once per dimension -- only the ONE block matching that
# dimension's own evidence_requirement, never all three. This is the
# structural half of the Phase 5 enum-confusion fix: a dimension whose
# requirement is "Inferred" never sees the word "Public" in its own
# evidence-assessment instructions at all.
EVIDENCE_REQUIREMENT_RULES = {
    "Public": """
PUBLIC EVIDENCE REQUIREMENT

- Score using verifiable public facts or facts explicitly included in the supplied startup information.
- Exact quantitative metrics are not required.
- Valid public evidence may include: market category, customer segments, known
  competitors, founder history, shipped product, product behavior, pricing,
  integrations, funding history, customer adoption, credible period-appropriate
  public research.
- Use evidence_status "Observed" when direct facts support the assessment.
- Use evidence_status "Inferred" when multiple credible public signals support it.
- Do not mark this dimension Unavailable merely because exact quantitative
  metrics are absent. Public dimensions must not be marked Unavailable.""",
    "Inferred": """
INFERRED EVIDENCE REQUIREMENT

- Use evidence_status "Inferred" when at least two credible and independent
  signals support a reasonable conclusion.
- Confidence should usually be Low or Medium.
- The rationale must identify the signals and explain the inference.
- Exact quantitative metrics are not required when credible qualitative
  signals are sufficient.
- Do not mark this dimension Unavailable merely because quantitative metrics
  are absent -- qualitative signals are enough if at least two exist.
- Do not infer performance from brand reputation alone.
- Do not use hindsight or future company outcomes.""",
    "Private": """
PRIVATE EVIDENCE REQUIREMENT

- Use evidence_status "Observed" or "Inferred" only when relevant internal
  metrics or explicitly disclosed operating data are available.
- If the required private evidence is genuinely unavailable, use
  evidence_status "Unavailable", confidence "Low", empty evidence, and list
  the exact missing information.
- Private evidence commonly includes: runway, burn, cash balance, internal
  forecasts, private CAC, private LTV, private unit economics, undisclosed
  retention metrics.
- Publicly observable financial evidence may still be used when available,
  including disclosed revenue, pricing, funding history, revenue model,
  margins, capital efficiency, customer concentration, retention, or churn.
- Do not penalize the company because private information is unavailable.""",
}


def format_dimension_evidence_instructions(pillar: str) -> str:
    """
    Evidence-classification instructions per dimension: question,
    description, stage guidance, the ONE matching evidence-requirement
    block, evidence priority, and strong/weak signals. Deliberately
    excludes score bands and benchmark examples -- those are scoring-
    stage concerns this stage should never see, so nothing here can
    nudge a number.
    """
    methodology = SCORING_METHODOLOGY.get(pillar, [])

    sections: list[str] = []

    for dimension in methodology:
        section = f"""
==================================================
Dimension: {dimension.name}

Question:
{dimension.question}

Description:
{dimension.description}

Stage Guidance:
{dimension.stage_guidance}
{EVIDENCE_REQUIREMENT_RULES[dimension.evidence_requirement]}

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

        sections.append(section)

    return "\n".join(sections)


def format_dimension_placeholder(name: str) -> str:
    return (
        f'      {{\n'
        f'        "dimension": "{name}",\n'
        f'        "evidence_status": "Unavailable",\n'
        f'        "confidence": "Low",\n'
        f'        "evidence": [],\n'
        f'        "signals": [],\n'
        f'        "missing_information": [],\n'
        f'        "recommendations": [],\n'
        f'        "rationale": "Explain what evidence exists (or does not) '
        f'and why."\n'
        f'      }}'
    )


def build_evidence_prompt(
    pillar: str,
    company_text: str,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
) -> str:
    extra_fields = extra_fields or {}
    extra_rules = extra_rules or []

    extra_fields_json = "".join(
        f'  "{field_name}": "Brief string only. {description}",\n'
        for field_name, description in extra_fields.items()
    )

    extra_rules_text = "\n".join(f"- {rule}" for rule in extra_rules)

    dimension_names = [name for name, _ in get_scoring_dimensions(pillar)]
    dimension_placeholders = ",\n".join(
        format_dimension_placeholder(name) for name in dimension_names
    )

    return f"""
You are assessing what evidence exists for the SIE {pillar} Intelligence
Methodology. You are NOT scoring anything yet -- this step only
determines what is known, not what it is worth.

Startup and research context:

{company_text}

For each dimension below, determine:

1. evidence_status: "Observed" (direct facts support it), "Inferred"
   (at least two credible independent signals support it), or
   "Unavailable" (cannot be responsibly assessed under its evidence
   requirement).
2. confidence: Low, Medium, or High, in the evidence itself.
3. evidence: direct quotes or close paraphrases of the supporting facts.
   Empty if Unavailable.
4. signals: short, structured facts distinct from the quoted evidence
   above (e.g. "MRR grew $18K to $61K in two quarters" rather than a
   full quoted sentence). Empty if Unavailable.
5. missing_information: what specific information would be needed if
   Unavailable. Empty otherwise.
6. recommendations: the next diligence step to fill a gap, if any.
7. rationale: why this evidence_status and confidence were assigned.

{format_dimension_evidence_instructions(pillar)}

==================================================
GENERAL RULES
==================================================

- Do not invent facts. Every piece of evidence must be traceable to the
  supplied text.
- Missing information is not evidence of weak performance -- do not
  imply a judgment about how good or bad this looks. That happens in a
  separate step you are not performing here.
- Do not assign a numeric score anywhere in this response. There is no
  score field in the required output.
- Observed and Inferred dimensions must have non-empty evidence;
  Inferred additionally needs at least two evidence items.
- Unavailable dimensions must have empty evidence and non-empty
  missing_information.
- When the startup information specifies a historical evaluation
  period, use only evidence available at or before that period.

Return ONLY valid JSON with this exact structure:

{{
  "summary": "Evidence-based {pillar.lower()} summary (no score talk).",
  "confidence": "Low",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "recommendations": [],
  "stage_hint": "Brief company stage (e.g. Series A) if evident from the text, else empty string. This is a fact-finding observation, not a judgment.",
{extra_fields_json}  "dimensions": [
{dimension_placeholders}
  ]
}}

- Extra fields outside "dimensions" must always be strings, not objects.
- Return valid JSON only. No markdown. No triple backticks.

Additional pillar rules:

{extra_rules_text}
"""


def build_dimension_correction_prompt(
    pillar: str,
    dimension: EvidenceAnalysis,
    validation_errors: list[str],
) -> str:
    """
    Scoped correction for exactly one dimension's evidence assessment.
    Only this dimension's own rubric text and its own validation errors
    are included -- no other dimension's data is sent, so nothing else
    can be altered by this call.
    """
    methodology_by_name = get_methodology_by_name(pillar)
    dim_config = methodology_by_name.get(dimension.dimension)

    formatted_errors = "\n".join(f"- {error}" for error in validation_errors)

    rubric = ""
    if dim_config is not None:
        rubric = f"""
Question:
{dim_config.question}

Description:
{dim_config.description}

Stage Guidance:
{dim_config.stage_guidance}
{EVIDENCE_REQUIREMENT_RULES[dim_config.evidence_requirement]}
"""

    return f"""
Your previous evidence assessment for exactly one dimension --
"{dimension.dimension}" -- had a problem. Re-assess ONLY this dimension.

{rubric}

Validation errors on your previous assessment of this dimension:

{formatted_errors}

Correction rules:

- Before leaving this dimension Unavailable, search the supplied company
  information again for relevant qualitative evidence.
- Do not create evidence merely to avoid an Unavailable result.
- If no relevant evidence truly exists after re-examination, preserve
  evidence_status "Unavailable".
- Do not assign a numeric score -- there is no score field here.

Return ONLY this dimension's corrected JSON object, nothing else:

{{
  "dimension": "{dimension.dimension}",
  "evidence_status": "Unavailable",
  "confidence": "Low",
  "evidence": [],
  "signals": [],
  "missing_information": [],
  "recommendations": [],
  "rationale": ""
}}
"""


# --- Public Evidence Validation Consistency Fix ---
#
# The unconditional "Public dimensions may not be marked Unavailable"
# rule below and the correction prompt's own "preserve Unavailable if
# no relevant evidence truly exists" escape hatch used to contradict
# each other for every Public dimension. The investigation (Market
# Size / Market Growth / Product Usability, frozen NovaLedger evidence)
# found: correction fired on every Public+Unavailable result for these
# three dimensions across two 10-run experiments and resolved it 0% of
# the time -- because it was never actually constrained to resolve
# anything, only asked to reconsider.
#
# These two structures narrow the unconditional rule to a deterministic,
# per-dimension distinction, without adding a second LLM judgment layer
# and without touching any other Public dimension's behavior.

# Dimensions whose OWN methodology text explicitly says a specific hard
# figure must NOT be required (Market Size: "Do not punish missing TAM
# alone" / TAM deprioritized to last in evidence_priority; Market
# Growth: evidence_priority never lists an exact growth-rate figure at
# all, only category/budget/urgency signals and company growth as
# supporting evidence). If a listed dimension is Unavailable and its
# own `missing_information` cites ONLY these excused gaps, that is the
# model's own stated reason contradicting its own methodology -- flagged
# so the existing correction pass reconsiders it. Any other missing
# information (something genuinely required and absent) is never
# flagged by this dict.
EXCUSABLE_MISSING_INFORMATION: dict[str, tuple[str, ...]] = {
    "Market Size": (
        "tam", "sam", "som", "total addressable market",
        "addressable market size", "market size figure",
        "market size number", "market size data",
        "quantified market size", "exact market size",
        "specific market size",
    ),
    "Market Growth": (
        "cagr", "growth rate", "exact growth", "growth percentage",
        "market-wide growth data", "growth figures",
        "quantified growth", "specific growth rate",
        "market growth rate",
    ),
}

# Dimensions with investigated, acknowledged methodology ambiguity about
# what counts as sufficient evidence -- currently only Product/Usability
# (its evidence_priority asks for usability-research concepts -- time to
# value, activation, user satisfaction -- that essentially never appear
# in public material for a private company; common_mistakes sanctions
# retention as a proxy without saying whether that proxy alone is
# sufficient). Until methodology calibration resolves this, Unavailable
# is a legitimate outcome here and is never treated as a validation
# error. This is not a methodology change: the methodology text itself
# is untouched. It is the validator no longer contradicting the
# correction step's own judgment on a dimension already known to be
# genuinely ambiguous, rather than forcing every result through a
# reconsideration pass that has no principled way to resolve it.
AMBIGUOUS_UNAVAILABLE_DIMENSIONS = {"Usability"}


def validate_dimension_evidence(
    pillar: str,
    dimension: EvidenceAnalysis,
    company_text: str,
) -> list[str]:
    """
    Validate one dimension's evidence assessment. No score is involved
    at this stage -- these are exclusively evidence-recognition and
    evidence-classification checks.
    """
    methodology_by_name = get_methodology_by_name(pillar)
    dim_config = methodology_by_name.get(dimension.dimension)

    errors: list[str] = []

    if dim_config is None:
        errors.append(f"{dimension.dimension}: unknown scoring dimension.")
        return errors

    requirement = dim_config.evidence_requirement
    status = dimension.evidence_status
    evidence = dimension.evidence or []
    missing_information = dimension.missing_information or []

    if status == "Unavailable":
        if dimension.confidence != "Low":
            errors.append(
                f"{dimension.dimension}: Unavailable evidence must use "
                f"Low confidence."
            )
        if evidence:
            errors.append(
                f"{dimension.dimension}: Unavailable evidence must use "
                f"an empty evidence list."
            )
        if not missing_information:
            errors.append(
                f"{dimension.dimension}: Unavailable evidence must list "
                f"missing information."
            )

    elif status in {"Observed", "Inferred"}:
        if not evidence:
            errors.append(
                f"{dimension.dimension}: {status} evidence requires "
                f"supporting evidence."
            )
        if status == "Inferred" and len(evidence) < 2:
            errors.append(
                f"{dimension.dimension}: Inferred evidence requires at "
                f"least two credible supporting signals."
            )

    else:
        errors.append(
            f"{dimension.dimension}: invalid evidence_status {status!r}."
        )

    if requirement == "Public" and status == "Unavailable":
        if dimension.dimension in AMBIGUOUS_UNAVAILABLE_DIMENSIONS:
            # Acknowledged methodology ambiguity -- Unavailable is
            # legitimate here. Not flagged.
            pass
        else:
            exemption_terms = EXCUSABLE_MISSING_INFORMATION.get(
                dimension.dimension
            )
            missing_lower = [m.lower() for m in missing_information]

            excused = bool(
                exemption_terms
                and missing_lower
                and all(
                    any(term in item for term in exemption_terms)
                    for item in missing_lower
                )
            )

            if excused:
                errors.append(
                    f"{dimension.dimension}: marked Unavailable, but the "
                    f"only missing information cited "
                    f"({'; '.join(missing_information)}) is exactly what "
                    f"this dimension's own methodology says must NOT be "
                    f"required on its own. Re-examine using the "
                    f"qualitative/inferential evidence this dimension's "
                    f"methodology explicitly permits instead of the "
                    f"figure you cited as missing."
                )
            elif exemption_terms is None:
                # No known exemption for this Public dimension --
                # existing strict rule, unchanged.
                errors.append(
                    f"{dimension.dimension}: Public dimensions must be "
                    f"assessed using the supplied company information. "
                    f"Public dimensions may not be marked Unavailable."
                )
            # else: this dimension has an exemption list, but the cited
            # missing information includes something beyond it -- a
            # genuine gap, not the excused figure alone. Not flagged.

    if requirement in {"Inferred", "Private"} and status == "Unavailable":
        company_text_lower = company_text.lower()
        disclosed_signals = sorted(
            {
                term
                for term in QUANTITATIVE_DISCLOSURE_TERMS
                if term in company_text_lower
            }
        )
        if len(disclosed_signals) >= 2:
            errors.append(
                f"{dimension.dimension}: marked Unavailable, but the "
                f"supplied company information appears to explicitly "
                f"disclose relevant signals "
                f"({', '.join(disclosed_signals[:5])}). Re-examine this "
                f"dimension specifically before leaving it Unavailable. "
                f"Preserve Unavailable only if none of this evidence "
                f"actually supports this specific dimension."
            )

    if requirement == "Private" and status in {"Observed", "Inferred"}:
        private_evidence_terms = (
            "arr", "burn", "cac", "cash", "churn", "customer concentration",
            "gross margin", "grr", "ltv", "margin", "mrr", "nrr",
            "retention", "revenue", "runway",
        )
        combined = " ".join(
            [dimension.rationale.lower()]
            + [str(item).lower() for item in evidence]
        )
        if not any(term in combined for term in private_evidence_terms):
            errors.append(
                f"{dimension.dimension}: Private dimensions require "
                f"explicitly disclosed internal or financial evidence "
                f"before being marked Observed or Inferred."
            )

    return errors


def extract_pillar_evidence(
    pillar: str,
    company_text: str,
    system_content: str,
    extra_fields: dict[str, str] | None = None,
    extra_rules: list[str] | None = None,
) -> tuple[PillarEvidenceAnalysis, dict[str, Any], set[str]]:
    """
    Run the evidence-extraction stage for one pillar.

    Returns (pillar_evidence, narrative_fields, corrected_dimension_names).
    narrative_fields holds the pillar-level summary/confidence/strengths/
    weaknesses/evidence/recommendations/extra-fields the result_model
    also needs. corrected_dimension_names records which dimensions (if
    any) required a scoped correction pass, for observability only.
    """
    expected_dimensions = [name for name, _ in get_scoring_dimensions(pillar)]

    prompt = build_evidence_prompt(
        pillar=pillar,
        company_text=company_text,
        extra_fields=extra_fields,
        extra_rules=extra_rules,
    )

    content = call_analysis_model(
        system_content=system_content,
        user_content=prompt,
        temperature=0.0,
    )

    data = parse_json_from_response(content)

    dimensions_data = data.pop("dimensions", [])
    narrative_fields = dict(data)

    dimensions: dict[str, EvidenceAnalysis] = {}
    for entry in dimensions_data:
        try:
            dim = EvidenceAnalysis(**entry)
        except Exception:
            continue
        dimensions[dim.dimension] = dim

    # Any dimension the model failed to return at all starts as a
    # structurally-empty Unavailable placeholder, exactly like a
    # dimension that was returned but genuinely has no evidence -- both
    # get the same chance at scoped correction below.
    for name in expected_dimensions:
        if name not in dimensions:
            dimensions[name] = EvidenceAnalysis(
                dimension=name,
                evidence_status="Unavailable",
                confidence="Low",
                missing_information=["Not returned by the model."],
            )

    corrected_names: set[str] = set()

    for name in expected_dimensions:
        dim = dimensions[name]
        errors = validate_dimension_evidence(pillar, dim, company_text)

        if not errors:
            continue

        correction_prompt = build_dimension_correction_prompt(
            pillar=pillar,
            dimension=dim,
            validation_errors=errors,
        )

        try:
            corrected_content = call_analysis_model(
                system_content=system_content,
                user_content=correction_prompt,
                temperature=0.0,
            )
            corrected_data = parse_json_from_response(corrected_content)
            corrected_dim = EvidenceAnalysis(**corrected_data)

            if corrected_dim.dimension != name:
                # Guard against the model returning the wrong dimension's
                # name -- never let a mislabeled correction overwrite a
                # different dimension's slot.
                corrected_dim.dimension = name

            dimensions[name] = corrected_dim
            corrected_names.add(name)

            remaining_errors = validate_dimension_evidence(
                pillar, corrected_dim, company_text
            )
            if remaining_errors:
                print(
                    f"\nWARNING: Corrected evidence for {pillar}/{name} "
                    f"still has validation issues: {remaining_errors}. "
                    f"Keeping the corrected response as-is (it is still "
                    f"the model's best assessment after reconsideration) "
                    f"-- not forcing a different value."
                )

        except Exception as correction_error:
            print(
                f"\nWARNING: Evidence correction for {pillar}/{name} "
                f"returned an unusable response ({correction_error}). "
                f"Keeping the original assessment for this dimension "
                f"only -- every other dimension is unaffected."
            )

    pillar_evidence = PillarEvidenceAnalysis(
        pillar=pillar,
        dimensions=[dimensions[name] for name in expected_dimensions],
    )

    return pillar_evidence, narrative_fields, corrected_names
