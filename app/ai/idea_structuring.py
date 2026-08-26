"""
Idea Lab Phase 6.1 -- AI-Assisted Idea Setup.

Converts a founder's free-text idea description into a DRAFT structured
venture model (VentureDraft, see app/models/idea_lab.py) that the founder
reviews and edits before anything is created. This module NEVER:

- computes VPS (that's exclusively app/ai/vps_scoring.py::compute_vps),
- writes to the database,
- creates a Startup/Analysis,
- scores or judges the idea in any way.

Its only job is translating natural language into a structured,
provenance-tagged draft -- see structure_idea()'s own docstring for the
two-layer safety design that keeps validation/observation fields from
ever being fabricated, which is the one part of this module that matters
methodologically.

Follows this repo's existing simple JSON-mode LLM pattern (see
app/ai/structured_analysis.py) rather than analyze_pillar.py's heavier
evidence-validation machinery -- this is a much lower-stakes drafting
task with no evidence corpus to validate against, and Part 4 explicitly
wants this to stay simple.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Every field in this shape maps 1:1 onto VentureDraft (app/models/
# idea_lab.py). Giving the LLM the literal JSON shape (rather than a prose
# description of it) is deliberate -- it leaves nothing about the nesting
# or field names to the model's own judgment, which is exactly where a
# free-form instruction could quietly drift.
_RESPONSE_SHAPE = """
{
  "name": {"value": string|null, "provenance": "user_provided"|"ai_inferred"|"unknown", "source_quote": string|null},
  "industry": {same shape},
  "business_model": {same shape},
  "target_customer": {same shape},
  "stage": {same shape},
  "market": {
    "market_description": {same shape},
    "estimated_market_size": {same shape, value must be one of "Small","Medium","Large","Very Large" or null},
    "competition_intensity": {same shape, value must be one of "Low","Medium","High" or null}
  },
  "problem_solution": {
    "problem_statement": {same shape},
    "solution_description": {same shape},
    "differentiation": {same shape}
  },
  "founder": {
    "founder_count": {same shape, value is a number or null},
    "relevant_domain_experience_years": {same shape, value is a number or null},
    "has_technical_cofounder": {same shape, value is true/false/null},
    "has_business_cofounder": {same shape, value is true/false/null}
  },
  "gtm": {
    "primary_acquisition_strategy": {same shape},
    "expected_cac": {same shape, value is a number or null}
  },
  "economics": {
    "pricing_model": {same shape},
    "price_point": {same shape, value is a number or null},
    "expected_gross_margin_pct": {same shape, value is a number 0-100 or null}
  },
  "validation": {
    "customer_interviews": {same shape, value is a number or null},
    "waitlist_signups": {same shape, value is a number or null},
    "paying_customers": {same shape, value is a number or null},
    "monthly_revenue": {same shape, value is a number or null}
  },
  "capital": {
    "starting_capital": {same shape, value is a number or null},
    "monthly_burn": {same shape, value is a number or null}
  }
}
"""

SYSTEM_PROMPT = f"""You translate a founder's informal, natural-language description of a
startup idea into a structured DRAFT. You do not evaluate, score, or judge
the idea in any way -- never comment on whether it is good, viable, or
likely to succeed. Your only job is structuring what was said.

For every field, classify it into exactly one of three categories and
report that as "provenance":

- "user_provided": the founder DIRECTLY STATED this fact or something a
  reasonable person would call the same fact in different words. When you
  use this, "source_quote" MUST be a short, near-verbatim quote or close
  paraphrase copied from the founder's own text that supports it.
- "ai_inferred": you are proposing a REASONABLE MODELING ASSUMPTION that
  the founder did not state, based on common patterns for this kind of
  business (e.g. a typical business model for the category described).
  This is a guess offered for the founder to review and edit -- label it
  as such, never as fact.
- "unknown": the founder's description gives you nothing to go on for
  this field. Prefer this over guessing. A null value with "unknown" is
  always safer than an invented one.

When in doubt between "ai_inferred" and "unknown", choose "unknown".
Never fabricate specific numbers (dollar amounts, percentages, years of
experience, customer counts) that the founder did not state or strongly
imply -- if you cannot point to real textual support, the field is
"unknown", not a guessed number.

THE "validation" GROUP IS DIFFERENT FROM EVERY OTHER GROUP. It represents
REAL-WORLD VALIDATION: customer interviews actually conducted, a waitlist
that actually exists, customers actually paying, revenue actually
collected. You MUST NOT set "ai_inferred" for ANY field in "validation",
ever, under any circumstance, even if the business idea makes such
validation seem likely or typical. A field in "validation" may ONLY be
"user_provided" (with a real source_quote proving the founder said it
explicitly) or "unknown". If the founder did not explicitly state a
concrete number or fact about interviews, waitlist, paying customers, or
revenue, every one of those fields must be "unknown" with a null value --
regardless of how confident you are in your prediction. This rule
overrides any general instinct to be helpful or complete.

Each validation field has a STRICT, NARROW definition -- do not round a
weaker signal up into a stronger one:
- "customer_interviews": the number of people the founder has actually
  talked to / interviewed about the problem. Stated interest, expressed
  willingness to pay, or a verbal "yes I'd use this" from those
  conversations does NOT make them "paying_customers" -- it stays
  customer_interviews (or is simply not captured in a numeric field at
  all if it's not a count of people talked to).
- "waitlist_signups": the number of people who actually signed up to a
  waitlist or mailing list. Interest expressed in conversation is not a
  waitlist signup.
- "paying_customers": the number of customers who have ACTUALLY
  transacted -- money has actually changed hands, or they are on an
  active paid subscription right now. Someone who "said they would pay",
  "agreed to pay", "is interested at $X/month", or signed a non-binding
  LOI is NOT a paying customer -- that is expressed willingness, a
  weaker and different signal, and must NOT be entered here. If the only
  evidence is willingness-to-pay language, "paying_customers" stays
  unknown/null.
- "monthly_revenue": actual dollars already collected per month, not a
  projection, target, or expected future number ("we plan to reach
  $1M ARR" is a projection, not observed revenue -- unknown/null).

Return ONLY valid JSON matching this exact shape (no prose, no markdown
fences):
{_RESPONSE_SHAPE}
"""


class IdeaStructuringError(Exception):
    """Raised for any LLM/parsing failure -- app/api.py catches this and
    returns a generic, safe error, never the raw underlying exception."""


def _call_llm(description: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Founder's idea description:\n{description}"},
            ],
        )
        content = response.choices[0].message.content
    except Exception as error:
        raise IdeaStructuringError("LLM request failed") from error

    if not content:
        raise IdeaStructuringError("Empty LLM response")

    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise IdeaStructuringError("LLM response was not valid JSON") from error


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _quote_is_verifiable(source_quote: str | None, description: str) -> bool:
    """
    The actual enforcement mechanism, not just a prompt instruction: a
    "user_provided" claim is only honored if its source_quote is a real
    substring of what the founder actually wrote (case/whitespace
    normalized). This catches the LLM claiming "user_provided" without
    real textual support -- the one failure mode a prompt alone cannot
    prevent, since the model could simply mislabel provenance while
    still fabricating a quote-shaped string. A quote that doesn't
    literally appear is the tell.
    """
    if not source_quote or not source_quote.strip():
        return False

    return _normalize_text(source_quote) in _normalize_text(description)


def _sanitize_field(field: dict | None, description: str, *, allow_inferred: bool) -> dict:
    """
    Applied to EVERY leaf field, not just validation -- but the
    allow_inferred=False path (used exclusively for the validation group)
    is the one that carries Phase 6.1's core safety guarantee: no matter
    what the LLM returned, a validation field survives this function with
    a non-null value ONLY if it claimed "user_provided" AND that claim's
    source_quote is independently verified against the founder's actual
    submitted text. "ai_inferred" is not just discouraged for validation
    -- it is programmatically impossible to reach this function's output.
    """
    if not isinstance(field, dict):
        return {"value": None, "provenance": "unknown", "source_quote": None}

    provenance = field.get("provenance")
    value = field.get("value")
    source_quote = field.get("source_quote")

    if provenance == "user_provided" and _quote_is_verifiable(source_quote, description):
        return {"value": value, "provenance": "user_provided", "source_quote": source_quote}

    if allow_inferred and provenance == "ai_inferred" and value is not None:
        return {"value": value, "provenance": "ai_inferred", "source_quote": None}

    # Every other outcome -- including an unverifiable "user_provided"
    # claim, or ANY "ai_inferred"/other value on a validation field --
    # collapses to unknown/null. This is a fail-closed default, not an
    # edge case: it's what happens whenever the LLM's own claim can't be
    # independently substantiated.
    return {"value": None, "provenance": "unknown", "source_quote": None}


_ASSUMPTION_GROUPS = {
    "market": ["market_description", "estimated_market_size", "competition_intensity"],
    "problem_solution": ["problem_statement", "solution_description", "differentiation"],
    "founder": [
        "founder_count",
        "relevant_domain_experience_years",
        "has_technical_cofounder",
        "has_business_cofounder",
    ],
    "gtm": ["primary_acquisition_strategy", "expected_cac"],
    "economics": ["pricing_model", "price_point", "expected_gross_margin_pct"],
    "capital": ["starting_capital", "monthly_burn"],
}

_VALIDATION_FIELDS = ["customer_interviews", "waitlist_signups", "paying_customers", "monthly_revenue"]

_TOP_LEVEL_FIELDS = ["name", "industry", "business_model", "target_customer", "stage"]


def _sanitize_draft(raw: dict, description: str) -> dict:
    sanitized: dict = {}

    for field_name in _TOP_LEVEL_FIELDS:
        sanitized[field_name] = _sanitize_field(raw.get(field_name), description, allow_inferred=True)

    for group_name, field_names in _ASSUMPTION_GROUPS.items():
        group_raw = raw.get(group_name) if isinstance(raw.get(group_name), dict) else {}
        sanitized[group_name] = {
            field_name: _sanitize_field(group_raw.get(field_name), description, allow_inferred=True)
            for field_name in field_names
        }

    # The one group where allow_inferred=False -- see _sanitize_field's
    # own docstring. This is what makes fabricated validation
    # structurally unreachable regardless of what the LLM returned.
    validation_raw = raw.get("validation") if isinstance(raw.get("validation"), dict) else {}
    sanitized["validation"] = {
        field_name: _sanitize_field(validation_raw.get(field_name), description, allow_inferred=False)
        for field_name in _VALIDATION_FIELDS
    }

    return sanitized


def structure_idea(description: str) -> dict:
    """
    Returns a dict matching VentureDraft's shape (app/models/idea_lab.py),
    already passed through _sanitize_draft() -- by the time this returns,
    it is IMPOSSIBLE for any validation field to carry a fabricated or
    unverified value, independent of anything the LLM did or didn't
    follow correctly in the prompt. Raises IdeaStructuringError on any
    LLM/parsing failure; app/api.py is responsible for turning that into
    a safe, generic HTTP error.
    """
    raw = _call_llm(description)

    if not isinstance(raw, dict):
        raise IdeaStructuringError("LLM response was not a JSON object")

    return _sanitize_draft(raw, description)
