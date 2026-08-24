from pydantic import BaseModel, Field
from typing import Literal

from app.models.scoring import StartupIntelligenceScore, PillarScoreBreakdown
from app.models.evidence import Evidence
from app.models.analysis_context import AnalysisContext
from datetime import datetime


ConfidenceLevel = Literal["Low", "Medium", "High"]


class StartupAnalysisRequest(BaseModel):
    # MVP hardening: bounds on oversized/empty input. Pydantic rejects a
    # violating request with a 422 before the route body (and the real,
    # multi-minute, paid pipeline call) ever runs. 50,000 characters is a
    # generous ceiling for a company description -- comfortably above any
    # real submission seen in testing (a few thousand characters) -- meant
    # to stop a pathological paste (an entire scraped site, a whole PDF's
    # raw text, etc.), not to constrain legitimate use.
    company_text: str = Field(min_length=1, max_length=50_000)


class WebsiteAnalysisRequest(BaseModel):
    url: str


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
    created_at: datetime
    methodology: SIEMethodologyAnalysis