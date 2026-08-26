"""
Phase 8 -- Fundraising Readiness V1. Response contract only -- see
app/ai/fundraising_readiness.py's own module docstring for the full
design record (why this exists as a separate, deterministic assessment
rather than exposing the legacy readiness_score, and the exact formula
behind readiness_score below).

Its own file for the same reason app/models/founder_action.py is its own
file: Fundraising Readiness is a distinct concern from canonical Startup
Intelligence (SPS) -- this model never reuses startup_intelligence_score
or any Methodology v2 scoring type.
"""

from pydantic import BaseModel, Field


class PillarReadinessOut(BaseModel):
    pillar: str
    label: str
    score: float | None = None
    confidence: str
    evidence_coverage: float
    weight: float
    # 0-10 scale; None when the pillar has no score at all (Unavailable)
    # -- never a fabricated 0. See
    # app.ai.fundraising_readiness.compute_pillar_readiness()'s own
    # docstring for the exact formula this comes from.
    readiness_contribution: float | None = None
    top_strength: str | None = None
    top_weakness: str | None = None


class ReadinessGapOut(BaseModel):
    category: str
    pillar: str | None = None
    issue: str
    why_it_matters: str
    recommended_next_step: str
    # The exact text used as the founder_actions dedup/provenance key if
    # this gap is added to the Action Plan (source='fundraising_gap') --
    # see app/api.py's add-to-plan endpoint.
    source_text: str


class ChecklistItemOut(BaseModel):
    category: str
    status: str
    note: str


class FundraisingReadinessResponse(BaseModel):
    startup_id: int
    canonical_name: str
    has_canonical_analysis: bool
    stage_label: str
    stage_recognized: bool
    # 0-100, or None when has_canonical_analysis is False -- never a
    # fabricated score for an unanalyzed startup.
    readiness_score: float | None = None
    readiness_band: str | None = None
    pillar_readiness: list[PillarReadinessOut] = Field(default_factory=list)
    gaps: list[ReadinessGapOut] = Field(default_factory=list)
    investor_questions: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItemOut] = Field(default_factory=list)
    has_pitch_deck: bool
    pitch_deck_note: str
    # Context only -- current SPS, shown so the page can explain the
    # distinction rather than pretend readiness doesn't relate to it at
    # all. Never blended into readiness_score.
    current_sps: float | None = None
    analyzed_at: str | None = None
