"""
Low-level helpers shared by the evidence-extraction stage
(app/ai/evidence_extraction.py), the scoring stage
(app/ai/pillar_scoring.py), and the orchestrator (app/ai/analyze_pillar.py).

Pulled into its own module so the two pipeline stages can both depend on
it without depending on each other or on the orchestrator, avoiding a
circular import.
"""

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.ai.scoring_methodology import SCORING_METHODOLOGY


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# Provenance constants (SIE Scoring Reliability sprint, Phase 5; kept
# here as the single source of truth after the Evidence/Scoring
# Separation sprint split analyze_pillar.py into multiple files).
#
# PILLAR_ANALYSIS_MODEL is the model every pillar-pipeline call actually
# uses -- stamped onto every new analysis's analysis_context.model_identifier.
#
# PILLAR_PROMPT_VERSION identifies the current prompt architecture.
# Bumped for this sprint since the pipeline is now two stages instead of
# one, a materially different prompt shape from v1.0.
PILLAR_ANALYSIS_MODEL = "gpt-4.1-mini"
PILLAR_PROMPT_VERSION = "2.0"


# Deterministic terms indicating the supplied company information likely
# contains a concrete, disclosed quantitative or operational signal.
# Used only to decide whether an Inferred or Private dimension marked
# Unavailable deserves a second look via scoped correction -- never to
# assign a score or evidence_status directly. See
# app/ai/evidence_extraction.py::validate_dimension_evidence.
QUANTITATIVE_DISCLOSURE_TERMS = (
    "arr",
    "burn",
    "cac",
    "cash",
    "churn",
    "customer concentration",
    "customers",
    "funding",
    "gross margin",
    "grr",
    "ltv",
    "margin",
    "mrr",
    "nrr",
    "raised",
    "retention",
    "revenue",
    "runway",
    "series a",
    "series b",
    "series c",
    "shipped",
)


def call_analysis_model(
    system_content: str,
    user_content: str,
    temperature: float,
) -> str:
    """Make one model call and return response text."""
    response = client.chat.completions.create(
        model=PILLAR_ANALYSIS_MODEL,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content or ""


def parse_json_from_response(content: str) -> dict[str, Any]:
    """
    Parse a JSON object from a model response.

    The model is instructed to return JSON only, but this fallback
    handles responses that accidentally include surrounding text.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in model response.")

    return json.loads(match.group(0))


def get_methodology_by_name(pillar: str) -> dict[str, Any]:
    """Return the configured scoring dimensions indexed by dimension name."""
    return {
        dimension.name: dimension
        for dimension in SCORING_METHODOLOGY.get(pillar, [])
    }
