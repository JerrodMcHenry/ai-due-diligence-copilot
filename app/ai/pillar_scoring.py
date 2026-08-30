"""
Stage 2 of the two-stage pillar pipeline (SIE Evidence/Scoring
Separation sprint): what does the already-normalized evidence mean
under the current SIE methodology.

This stage receives the dimension's rubric (question, stage guidance,
score bands, benchmark examples, weight) and the EvidenceAnalysis
object stage 1 already produced and validated -- evidence_status,
confidence, evidence, signals, rationale. It does NOT receive the raw
company_text/research corpus again (Phase 4): the scorer judges the
normalized evidence, it does not rediscover evidence. It also never
sees "Public"/"Inferred"/"Private" evidence-requirement language and is
never asked to output evidence_status -- both are already decided and
are simply carried forward by Python. This is the structural half of
removing the evidence_requirement / evidence_status enum confusion:
the field that caused it isn't part of this stage's vocabulary at all.

Unavailable dimensions are never sent to the scorer -- Python already
knows their score is None; asking the model would just reopen a
question stage 1 already settled and risk it silently re-deciding
evidence status through the back door.

Correction here, like evidence extraction, is scoped per dimension.
"""

from app.models.evidence_analysis import PillarEvidenceAnalysis

from app.ai.pillar_shared import (
    call_analysis_model,
    get_methodology_by_name,
    parse_json_from_response,
)


def format_dimension_rubric(pillar: str, dimension_name: str) -> str:
    dim_config = get_methodology_by_name(pillar).get(dimension_name)

    if dim_config is None:
        return ""

    section = f"""
==================================================
Dimension: {dim_config.name}
Weight: {dim_config.weight}

Question:
{dim_config.question}

Stage Guidance:
{dim_config.stage_guidance}

Score Guidance:

9-10:
{dim_config.score_9_10}

7-8:
{dim_config.score_7_8}

5-6:
{dim_config.score_5_6}

3-4:
{dim_config.score_3_4}

0-2:
{dim_config.score_0_2}

Strong Signals:
"""
    for item in dim_config.strong_signals:
        section += f"- {item}\n"

    section += "\nWeak Signals:\n"
    for item in dim_config.weak_signals:
        section += f"- {item}\n"

    section += "\nBenchmark Examples:\n"
    if dim_config.benchmark_examples:
        for item in dim_config.benchmark_examples:
            section += f"- {item}\n"
    else:
        section += "- None specified.\n"

    return section


def format_normalized_evidence(evidence) -> str:
    """
    The already-decided evidence for one dimension, exactly as
    produced (and validated, and possibly corrected) by stage 1. This
    is all the raw-text access the scorer gets for this dimension.
    """
    lines = [
        f"Evidence status (already decided, do not re-derive): {evidence.evidence_status}",
        f"Evidence confidence (already decided): {evidence.confidence}",
    ]

    lines.append("Evidence:")
    for item in evidence.evidence:
        lines.append(f"- {item}")

    if evidence.signals:
        lines.append("Extracted signals:")
        for item in evidence.signals:
            lines.append(f"- {item}")

    lines.append(f"Evidence classification rationale: {evidence.rationale}")

    return "\n".join(lines)


def build_scoring_prompt(
    pillar: str,
    pillar_evidence: PillarEvidenceAnalysis,
    stage: str,
) -> str:
    scoreable = [
        d for d in pillar_evidence.dimensions
        if d.evidence_status != "Unavailable"
    ]

    if not scoreable:
        return ""

    stage_line = (
        f"The company's stage is: {stage}. Apply each dimension's Stage "
        f"Guidance accordingly."
        if stage
        else "The company's stage was not determined. Apply Stage "
        "Guidance conservatively."
    )

    sections = []
    placeholders = []

    for dim in scoreable:
        sections.append(
            format_dimension_rubric(pillar, dim.dimension)
            + "\n"
            + format_normalized_evidence(dim)
        )
        placeholders.append(
            f'      {{\n'
            f'        "dimension": "{dim.dimension}",\n'
            f'        "score": null,\n'
            f'        "rationale": "Explain why this evidence maps to '
            f'this specific score under the methodology above."\n'
            f'      }}'
        )

    return f"""
You are scoring the {pillar} pillar of a startup, using ONLY the
already-classified evidence below for each dimension. The evidence has
already been assessed -- your job is to judge what it is WORTH under
the SIE methodology, not to look for more evidence or to reconsider
whether evidence exists.

{stage_line}

{"".join(sections)}

==================================================
SCORING RULES
==================================================

- Assign a numeric score from 0 to 10 for every dimension listed above
  (every dimension here already has usable evidence -- none of them are
  Unavailable).
- Use the Score Guidance bands as anchors; do not default to the
  midpoint of a band without justification in your rationale.
- Score intrinsic startup quality, not pitch quality.
- The rationale must explain how the SPECIFIC evidence given maps to
  the specific number chosen -- reference the evidence or signals shown.
- Do not invent facts beyond what was given to you.
- Do not use hindsight or later outcomes.
- Evidence strength, not just evidence status, decides where within a
  band you land (Methodology V2.1, Part 7 -- revised from v2.0, which
  told you not to lower a score for sparse evidence; that produced a
  measured mid-band floor across real companies and has been removed):
    * evidence_status "Unavailable" is never sent to you -- not a
      concern here.
    * evidence_status "Inferred" with Low confidence means the evidence
      is thin -- credible, but not enough on its own to demonstrate
      real strength. Default to the LOWER half of whichever band the
      evidence qualitatively fits (e.g. a thin-but-positive signal
      belongs at 5, not 6; a thin-but-mixed signal belongs at 3-4, not
      5-6) unless something in the evidence specifically justifies going
      higher.
    * evidence_status "Observed", or "Inferred" with Medium/High
      confidence, can use the full band its qualitative content
      supports, including the top of that band when the evidence is
      genuinely specific (named figures, named outcomes, named prior
      history) rather than generic narrative.
    * "Little evidence was given" and "the evidence given is weak" are
      different findings and should usually produce different scores --
      thin-but-genuinely-strong evidence (e.g. one specific, credible,
      hard-to-fake fact) can still score well; thin-and-generic evidence
      (a claim any company's marketing page could make) should not
      default upward merely because nothing affirmatively contradicts
      it.
    * A score of 7 or higher requires evidence specific enough that a
      reasonable investor would consider it a real signal, not merely
      plausible-sounding narrative. If the evidence for this dimension
      is generic enough that it could describe most companies at this
      stage, the ceiling for this dimension is 6, regardless of how
      positive its tone is.

Return ONLY valid JSON with this exact structure:

{{
  "scores": [
{",".join(placeholders)}
  ]
}}

Return valid JSON only. No markdown. No triple backticks.
"""


def build_score_correction_prompt(
    pillar: str,
    dimension_name: str,
    evidence,
    validation_errors: list[str],
) -> str:
    formatted_errors = "\n".join(f"- {error}" for error in validation_errors)

    return f"""
Your previous score for exactly one dimension -- "{dimension_name}" --
had a problem. Re-score ONLY this dimension.

{format_dimension_rubric(pillar, dimension_name)}

{format_normalized_evidence(evidence)}

Validation errors on your previous score for this dimension:

{formatted_errors}

Return ONLY this dimension's corrected JSON object, nothing else:

{{
  "dimension": "{dimension_name}",
  "score": 0,
  "rationale": ""
}}
"""


def validate_dimension_score(
    dimension_name: str,
    score: float | None,
) -> list[str]:
    """
    Scoring-stage validation is deliberately minimal: evidence_status,
    evidence, and missing_information were already validated in stage
    1 and are not re-decided here. Only the number itself is checked.
    """
    errors: list[str] = []

    if score is None:
        errors.append(
            f"{dimension_name}: this dimension has usable evidence and "
            f"must receive a numeric score, not null."
        )
    elif not 0 <= score <= 10:
        errors.append(
            f"{dimension_name}: score must be between 0 and 10."
        )

    return errors


def score_pillar_evidence(
    pillar: str,
    pillar_evidence: PillarEvidenceAnalysis,
    system_content: str,
    stage: str = "",
) -> tuple[dict[str, tuple[float, str]], set[str]]:
    """
    Run the scoring stage for one pillar's already-normalized evidence.

    Returns ({dimension_name: (score, rationale)}, corrected_dimension_names).
    Only dimensions with usable evidence appear in the result; Unavailable
    dimensions are never sent to the model and never appear here.
    """
    scoreable_names = [
        d.dimension for d in pillar_evidence.dimensions
        if d.evidence_status != "Unavailable"
    ]

    if not scoreable_names:
        return {}, set()

    prompt = build_scoring_prompt(pillar, pillar_evidence, stage)

    content = call_analysis_model(
        system_content=system_content,
        user_content=prompt,
        temperature=0.0,
    )

    data = parse_json_from_response(content)
    entries = data.get("scores", [])

    scores: dict[str, tuple[float, str]] = {}
    for entry in entries:
        name = entry.get("dimension")
        if name in scoreable_names:
            scores[name] = (entry.get("score"), entry.get("rationale", ""))

    evidence_by_name = {d.dimension: d for d in pillar_evidence.dimensions}
    corrected_names: set[str] = set()

    for name in scoreable_names:
        score, rationale = scores.get(name, (None, ""))
        errors = validate_dimension_score(name, score)

        if not errors:
            continue

        correction_prompt = build_score_correction_prompt(
            pillar=pillar,
            dimension_name=name,
            evidence=evidence_by_name[name],
            validation_errors=errors,
        )

        try:
            corrected_content = call_analysis_model(
                system_content=system_content,
                user_content=correction_prompt,
                temperature=0.0,
            )
            corrected_data = parse_json_from_response(corrected_content)
            corrected_score = corrected_data.get("score")
            corrected_rationale = corrected_data.get("rationale", rationale)

            remaining_errors = validate_dimension_score(name, corrected_score)

            if remaining_errors:
                print(
                    f"\nWARNING: Corrected score for {pillar}/{name} still "
                    f"has validation issues: {remaining_errors}. Leaving "
                    f"this dimension unscored (null) rather than accepting "
                    f"an invalid number."
                )
                scores[name] = (None, corrected_rationale)
            else:
                scores[name] = (corrected_score, corrected_rationale)

            corrected_names.add(name)

        except Exception as correction_error:
            print(
                f"\nWARNING: Score correction for {pillar}/{name} returned "
                f"an unusable response ({correction_error}). Leaving this "
                f"dimension unscored (null) -- every other dimension is "
                f"unaffected."
            )
            scores[name] = (None, rationale)

    return scores, corrected_names
