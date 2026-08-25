from pydantic import BaseModel, Field, field_validator
from typing import Literal

from app.models.scoring import StartupIntelligenceScore, PillarScoreBreakdown
from app.models.evidence import Evidence
from app.models.analysis_context import AnalysisContext
from datetime import datetime


ConfidenceLevel = Literal["Low", "Medium", "High"]

# MVP hardening: bounds on oversized/empty input. Pydantic rejects a
# violating request with a 422 before the route body (and the real,
# multi-minute, paid pipeline call) ever runs. 50,000 characters is a
# generous ceiling for a company description -- comfortably above any
# real submission seen in testing (a few thousand characters) -- meant
# to stop a pathological paste (an entire scraped site, a whole PDF's
# raw text, etc.), not to constrain legitimate use. Pulled out to a
# constant (Unified Multi-Source Analyze Startup) so POST /analyze can
# reuse the exact same bound when validating its raw company_text form
# field via this same model, rather than duplicating the number.
MAX_COMPANY_TEXT_LENGTH = 50_000


class StartupAnalysisRequest(BaseModel):
    company_text: str = Field(min_length=1, max_length=MAX_COMPANY_TEXT_LENGTH)


class WebsiteAnalysisRequest(BaseModel):
    # Website / URL Ingestion: bounds obviously-invalid input with a fast
    # 422 before any network I/O -- the real security validation (scheme
    # allow-list, private-network rejection, DNS-rebinding-safe pinning,
    # bounded redirects/response size) happens in
    # app/website_scrapper.py, which is the one place that knowledge
    # should live. 2048 chars is a generous ceiling for a URL (well above
    # any real company website URL, including ones with query strings),
    # meant to reject a pathological paste, not to constrain real use.
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def _must_look_like_a_url(cls, value: str) -> str:
        trimmed = value.strip()

        if not trimmed.lower().startswith(("http://", "https://")):
            raise ValueError("Website URL must start with http:// or https://")

        return trimmed


class PillarAnalysis(BaseModel):
    score: float | None = None
    confidence: ConfidenceLevel = "Low"
    summary: str = ""
    evidence: list[Evidence | str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    score_breakdown: PillarScoreBreakdown = Field(default_factory=PillarScoreBreakdown)


class SIEContext(BaseModel):
    company_name: str = ""
    industry: str = ""
    business_model: str = ""
    company_stage: str = ""
    funding_stage: str = ""


class PartialStructuralCoverage(BaseModel):
    """
    SIE Methodology v2, Part 9 item 6 (Blocker 3 fix, post-implementation
    review): a purely additive, DISPLAY-ONLY label for whole-pillar evidence
    absence. Computed by
    app.ai.sie_v2_evidence_semantics.compute_partial_structural_coverage()
    from each pillar's already-existing final score (None == that pillar had
    zero scored dimensions). Never a math adjustment to SPS -- startup_
    intelligence_score is computed identically whether or not this field is
    populated. field is None (not this model's zero-value) on every analysis
    that predates this field, so historical JSONB records are never silently
    reinterpreted as "fully covered."
    """

    partial_structural_coverage: bool = False
    pillars_unavailable_entirely: list[str] = Field(default_factory=list)
    note: str = ""


class SIEMethodologyAnalysis(BaseModel):
    context: SIEContext = Field(default_factory=SIEContext)

    analysis_context: AnalysisContext | None = None

    market: PillarAnalysis = Field(default_factory=PillarAnalysis)
    team: PillarAnalysis = Field(default_factory=PillarAnalysis)
    product: PillarAnalysis = Field(default_factory=PillarAnalysis)
    execution: PillarAnalysis = Field(default_factory=PillarAnalysis)
    traction: PillarAnalysis = Field(default_factory=PillarAnalysis)
    financial_health: PillarAnalysis = Field(default_factory=PillarAnalysis)

    startup_intelligence_score: float = 0.0
    startup_scorecard: StartupIntelligenceScore = Field(default_factory=StartupIntelligenceScore)

    milestone_readiness_score: float = 0.0
    momentum_score: float = 0.0
    confidence_score: float = 0.0

    # None (not PartialStructuralCoverage()'s own zero-value) is the
    # backward-compatible default: a record stored before this field existed
    # decodes to None here, never to a fabricated "fully covered" reading.
    structural_coverage: PartialStructuralCoverage | None = None

    executive_coaching_summary: str = ""
    next_actions: list[str] = Field(default_factory=list)
    


class StartupAnalysisResponse(BaseModel):
    context: SIEContext = Field(default_factory=SIEContext)
    startup_scorecard: StartupIntelligenceScore = Field(default_factory=StartupIntelligenceScore)
    methodology: SIEMethodologyAnalysis = Field(default_factory=SIEMethodologyAnalysis)


class UpdateAnalysisRequest(BaseModel):
    methodology: SIEMethodologyAnalysis

class StartupProfileResponse(BaseModel):
    id: int
    # Saved Startups (Watchlist Phase 1): the canonical Startup FK
    # (analyses.startup_id), additive alongside the existing analysis-id
    # `id` field above -- see get_startup_by_name()'s docstring. None only
    # for historical rows that predate both the write path and its
    # backfill; the frontend Save control hides itself when this is None
    # rather than guessing an id to save.
    startup_id: int | None = None
    created_at: datetime
    methodology: SIEMethodologyAnalysis


class SavedStartupEntry(BaseModel):
    """
    Saved Startups (Watchlist Phase 1) list-row shape -- see
    get_saved_startups_for_user()'s docstring. Deliberately flat and
    minimal (mirrors RankingEntry's shape, not the full nested
    SIEMethodologyAnalysis) since this is a list view, not a second
    startup-details experience; every field here is read fresh from the
    startup's current latest canonical analysis on every request, never
    copied into saved_startups itself. industry/stage/overall_score/
    latest_analysis_at are None when the saved startup currently has no
    canonical analysis -- never fabricated.
    """
    startup_id: int
    company_name: str
    industry: str | None = None
    stage: str | None = None
    overall_score: float | None = None
    latest_analysis_at: datetime | None = None
    saved_at: datetime


class SavedStartupStatus(BaseModel):
    saved: bool