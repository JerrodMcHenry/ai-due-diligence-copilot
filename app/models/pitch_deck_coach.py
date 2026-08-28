"""
Phase 10.8 -- Pitch Deck Coach V1. Request/response contracts.

Deliberately its own file, its own table (pitch_deck_reviews), its own AI
module (app/ai/pitch_deck_coaching.py) -- Pitch Deck Coach is NOT a new
SPS methodology. Nothing here reuses SIEMethodologyAnalysis, PillarAnalysis,
app/models/scoring.py, or app/ai/scoring_methodology.py, and a
PitchDeckReview has no FK, field, or query path into startups, analyses,
startup_memberships, or score_history. See
app/ai/pitch_deck_coaching.py's own module docstring for the full
architectural boundary and grounding/anti-fabrication design.

Part 14's decision: there is deliberately no numeric field anywhere in
this file. `readiness_label` is the only aggregate judgment surfaced, and
it is a small fixed vocabulary (DeckReadinessLabel), computed
deterministically in app/ai/pitch_deck_coaching.py from the already-
validated `sections` classification -- never an LLM-generated number.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SectionStatus = Literal["missing", "unclear", "effective"]

# Part 6's own list, plus "other" for content the deck genuinely contains
# that doesn't map onto one of these -- never forced into a false fit.
SectionCategory = Literal[
    "cover",
    "problem",
    "solution",
    "product",
    "market",
    "business_model",
    "traction",
    "gtm",
    "competition",
    "team",
    "financials",
    "ask",
    "other",
]

DeckReadinessLabel = Literal["Early Draft", "Developing", "Getting Clear", "Pitch Ready"]


class DeckStoryField(BaseModel):
    """
    One piece of "the story your deck tells" (Part 5). `found=False` is a
    legitimate, expected outcome -- `summary` then carries an honest
    "we couldn't find..." sentence (see Part 5's own worked example for
    THE ASK), never a manufactured guess. `page_refs` is only ever
    populated when found=True, and only with pages whose text was
    independently verified to support the summary (see
    pitch_deck_coaching.py's grounding pass).
    """
    found: bool
    summary: str
    page_refs: list[int] = Field(default_factory=list)


class DeckStory(BaseModel):
    company: DeckStoryField
    customer: DeckStoryField
    problem: DeckStoryField
    solution: DeckStoryField
    business: DeckStoryField
    proof: DeckStoryField
    ask: DeckStoryField


class DeckSectionCoaching(BaseModel):
    """
    One investor question the deck may or may not answer well -- NOT
    necessarily one literal slide (Part 6: "Competition may legitimately
    be communicated inside another slide... evaluate whether the investor
    question is answered, not merely whether a slide title exists").
    `page_refs` names the real, verified PDF pages this judgment rests on
    -- empty when status is "missing".
    """
    category: SectionCategory
    label: str
    status: SectionStatus
    page_refs: list[int] = Field(default_factory=list)
    what_its_saying: str | None = None
    whats_working: str | None = None
    may_confuse: str | None = None
    # Part 8's investor-lens layer. Always populated, for every section,
    # regardless of status -- this is fixed educational copy per category
    # (see INVESTOR_LENS in pitch_deck_coaching.py), not a claim about
    # this specific deck, so it carries no grounding requirement.
    why_investors_care: str
    try_this: str | None = None


class PriorityFix(BaseModel):
    """Part 9. related_category always names a section this codebase
    itself classified missing/unclear -- enforced in
    pitch_deck_coaching.py, not merely requested of the model."""
    title: str
    issue: str
    why_it_matters: str
    try_this: str
    related_category: SectionCategory


class DeckStrength(BaseModel):
    """Part 10. related_category always names a section this codebase
    itself classified effective."""
    title: str
    why_it_works: str
    related_category: SectionCategory


class OpenQuestion(BaseModel):
    """Part 11. related_category always names a section classified
    missing or unclear -- an open question can never be manufactured
    about a section the deck actually handled well."""
    question: str
    related_category: SectionCategory


class PrepQuestion(BaseModel):
    """
    Part 12. Framed as POSSIBLE investor questions, never as actual
    investor feedback (Part 13) -- enforced at render time by the
    frontend's fixed "Possible investor question" label, never by
    trusting question text alone to carry that framing.
    """
    question: str
    related_category: SectionCategory


class PitchDeckReviewResponse(BaseModel):
    id: int
    deck_filename: str
    page_count: int
    readiness_label: DeckReadinessLabel
    story: DeckStory
    sections: list[DeckSectionCoaching]
    top_fixes: list[PriorityFix]
    strengths: list[DeckStrength]
    open_questions: list[OpenQuestion]
    prep_questions: list[PrepQuestion]
    created_at: datetime


class PitchDeckReviewSummary(BaseModel):
    """List-view shape (GET /pitch-deck-reviews) -- Part 17's "multiple
    reviews can coexist" -- deliberately light, no full coaching payload."""
    id: int
    deck_filename: str
    readiness_label: DeckReadinessLabel
    created_at: datetime
