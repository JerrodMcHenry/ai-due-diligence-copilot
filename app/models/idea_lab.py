"""
Idea Lab / Venture Simulator V1 -- request/response contracts.

VentureAssumptions is deliberately a plain, permissive structure (every
field optional, no cross-field validation beyond basic type/range bounds)
-- Part 6/Part 4's explicit requirement that "unknown must remain
unknown" and "do not manufacture defaults". Provenance is structural, not
a per-field tag: everything under `validation` is a founder-REPORTED
OBSERVATION; every other group is a MODELED ASSUMPTION. See
app/ai/vps_scoring.py's own docstring for the full reasoning.

None of these models are reused from app/models/startup.py or
app/models/scoring.py on purpose -- VPS is not SPS, a modeled venture is
not a canonical Startup, and mixing the two model families would make it
easy to accidentally leak one into a response shaped for the other.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarketAssumptions(BaseModel):
    market_description: str | None = None
    estimated_market_size: str | None = None  # "Small" | "Medium" | "Large" | "Very Large"
    competition_intensity: str | None = None  # "Low" | "Medium" | "High"


class ProblemSolutionAssumptions(BaseModel):
    problem_statement: str | None = None
    solution_description: str | None = None
    differentiation: str | None = None


class FounderAssumptions(BaseModel):
    founder_count: int | None = Field(default=None, ge=0, le=20)
    relevant_domain_experience_years: float | None = Field(default=None, ge=0, le=60)
    has_technical_cofounder: bool | None = None
    has_business_cofounder: bool | None = None


class GtmAssumptions(BaseModel):
    primary_acquisition_strategy: str | None = None
    expected_cac: float | None = Field(default=None, ge=0)


class EconomicsAssumptions(BaseModel):
    pricing_model: str | None = None
    price_point: float | None = Field(default=None, ge=0)
    expected_gross_margin_pct: float | None = Field(default=None, ge=0, le=100)


class ValidationObservations(BaseModel):
    """
    Founder-REPORTED OBSERVATIONS, not modeled assumptions -- the one
    group of fields VPS's Validation category scores from. Still
    self-reported (Idea Lab does not verify these against any external
    source in V1 -- see the Phase 6 report's "externally verified
    evidence" discussion), but epistemically distinct from a projection
    like "we expect 15% monthly growth".
    """
    customer_interviews: int | None = Field(default=None, ge=0, le=100_000)
    waitlist_signups: int | None = Field(default=None, ge=0, le=10_000_000)
    paying_customers: int | None = Field(default=None, ge=0, le=10_000_000)
    monthly_revenue: float | None = Field(default=None, ge=0)


class CapitalAssumptions(BaseModel):
    starting_capital: float | None = Field(default=None, ge=0)
    monthly_burn: float | None = Field(default=None, ge=0)


class VentureAssumptions(BaseModel):
    target_customer: str | None = None
    market: MarketAssumptions = Field(default_factory=MarketAssumptions)
    problem_solution: ProblemSolutionAssumptions = Field(default_factory=ProblemSolutionAssumptions)
    founder: FounderAssumptions = Field(default_factory=FounderAssumptions)
    gtm: GtmAssumptions = Field(default_factory=GtmAssumptions)
    economics: EconomicsAssumptions = Field(default_factory=EconomicsAssumptions)
    validation: ValidationObservations = Field(default_factory=ValidationObservations)
    capital: CapitalAssumptions = Field(default_factory=CapitalAssumptions)


class VPSCategoryResult(BaseModel):
    key: str
    label: str
    score: float | None = None
    basis: list[str] = Field(default_factory=list)


class VPSResult(BaseModel):
    vps: float | None = None
    label: str
    categories: list[VPSCategoryResult]
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    validation_gaps: list[str] = Field(default_factory=list)
    next_milestones: list[str] = Field(default_factory=list)


class CreateVentureRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    industry: str | None = Field(default=None, max_length=200)
    business_model: str | None = Field(default=None, max_length=200)
    target_customer: str | None = Field(default=None, max_length=500)
    stage: str | None = Field(default=None, max_length=50)  # Idea | Researching | Validating | Building | Launched
    assumptions: VentureAssumptions = Field(default_factory=VentureAssumptions)


class UpdateVentureRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    industry: str | None = Field(default=None, max_length=200)
    business_model: str | None = Field(default=None, max_length=200)
    target_customer: str | None = Field(default=None, max_length=500)
    stage: str | None = Field(default=None, max_length=50)
    assumptions: VentureAssumptions = Field(default_factory=VentureAssumptions)


class VentureResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    industry: str | None = None
    business_model: str | None = None
    target_customer: str | None = None
    stage: str | None = None
    assumptions: VentureAssumptions
    model_result: VPSResult | None = None
    created_at: datetime
    updated_at: datetime


class VentureSummary(BaseModel):
    """List-view shape -- deliberately excludes the full assumptions/
    category breakdown (mirrors DiscoveryResult/SavedStartupEntry's own
    "flat summary for a list, not the whole detail payload" pattern)."""
    id: int
    name: str
    stage: str | None = None
    vps: float | None = None
    updated_at: datetime


class ScenarioCompareRequest(BaseModel):
    """
    Part 11: current scenario vs. a modified one -- deliberately NOT
    /compare's canonical-startup endpoint (this never touches startups/
    analyses, and a modeled venture must never be addressable through
    that endpoint at all). Both assumption sets are scored with the exact
    same compute_vps() the venture's own persisted model_result uses, so
    "Current" here always matches what's actually stored -- this endpoint
    doesn't mutate the venture, it just runs the scorer twice.
    """
    current_assumptions: VentureAssumptions
    modified_assumptions: VentureAssumptions


class ScenarioCompareResponse(BaseModel):
    current: VPSResult
    modified: VPSResult


# ---------------------------------------------------------------------------
# Phase 6.1 -- AI-Assisted Idea Setup. These models represent a DRAFT the
# founder must explicitly review and confirm -- they are never persisted
# directly and never feed compute_vps() on their own (see
# app/ai/idea_structuring.py). Every leaf value carries its own
# provenance so the UI can render "Based on your description" /
# "Modeled assumption" / "Not provided yet" instead of presenting
# everything with equal, unearned confidence.
#
# Validation fields use the SAME DraftTextField/DraftNumberField shapes
# as every other group, but are held to a stricter contract enforced in
# Python, not just by prompting: see
# idea_structuring.py::_apply_validation_safety_filter, which forcibly
# nulls any validation field whose provenance isn't "user_provided" AND
# independently verified against the founder's own submitted text. The
# LLM's own claim of "user_provided" is never trusted by itself.
# ---------------------------------------------------------------------------

DraftProvenance = Literal["user_provided", "ai_inferred", "unknown"]


class DraftTextField(BaseModel):
    value: str | None = None
    provenance: DraftProvenance = "unknown"
    # Only meaningful when provenance == "user_provided" -- a substring
    # the model claims is quoted/paraphrased-from the founder's own
    # description, used to verify (not just trust) that claim. See
    # idea_structuring.py's own docstring.
    source_quote: str | None = None


class DraftNumberField(BaseModel):
    value: float | None = None
    provenance: DraftProvenance = "unknown"
    source_quote: str | None = None


class DraftBoolField(BaseModel):
    value: bool | None = None
    provenance: DraftProvenance = "unknown"
    source_quote: str | None = None


class DraftMarketAssumptions(BaseModel):
    market_description: DraftTextField = Field(default_factory=DraftTextField)
    estimated_market_size: DraftTextField = Field(default_factory=DraftTextField)
    competition_intensity: DraftTextField = Field(default_factory=DraftTextField)


class DraftProblemSolutionAssumptions(BaseModel):
    problem_statement: DraftTextField = Field(default_factory=DraftTextField)
    solution_description: DraftTextField = Field(default_factory=DraftTextField)
    differentiation: DraftTextField = Field(default_factory=DraftTextField)


class DraftFounderAssumptions(BaseModel):
    founder_count: DraftNumberField = Field(default_factory=DraftNumberField)
    relevant_domain_experience_years: DraftNumberField = Field(default_factory=DraftNumberField)
    has_technical_cofounder: DraftBoolField = Field(default_factory=DraftBoolField)
    has_business_cofounder: DraftBoolField = Field(default_factory=DraftBoolField)


class DraftGtmAssumptions(BaseModel):
    primary_acquisition_strategy: DraftTextField = Field(default_factory=DraftTextField)
    expected_cac: DraftNumberField = Field(default_factory=DraftNumberField)


class DraftEconomicsAssumptions(BaseModel):
    pricing_model: DraftTextField = Field(default_factory=DraftTextField)
    price_point: DraftNumberField = Field(default_factory=DraftNumberField)
    expected_gross_margin_pct: DraftNumberField = Field(default_factory=DraftNumberField)


class DraftValidationObservations(BaseModel):
    """
    AI MUST NEVER infer any field here (Phase 6.1's core safety rule).
    Pydantic alone can't enforce "only user_provided allowed" -- that
    would make a legitimate `unknown` value impossible to express with
    the same type -- so this stays structurally identical to the other
    groups, and the actual enforcement is
    idea_structuring.py::_apply_validation_safety_filter, which runs on
    EVERY response before it ever reaches this model, regardless of what
    the LLM returned.
    """
    customer_interviews: DraftNumberField = Field(default_factory=DraftNumberField)
    waitlist_signups: DraftNumberField = Field(default_factory=DraftNumberField)
    paying_customers: DraftNumberField = Field(default_factory=DraftNumberField)
    monthly_revenue: DraftNumberField = Field(default_factory=DraftNumberField)


class DraftCapitalAssumptions(BaseModel):
    starting_capital: DraftNumberField = Field(default_factory=DraftNumberField)
    monthly_burn: DraftNumberField = Field(default_factory=DraftNumberField)


class VentureDraft(BaseModel):
    name: DraftTextField = Field(default_factory=DraftTextField)
    industry: DraftTextField = Field(default_factory=DraftTextField)
    business_model: DraftTextField = Field(default_factory=DraftTextField)
    target_customer: DraftTextField = Field(default_factory=DraftTextField)
    stage: DraftTextField = Field(default_factory=DraftTextField)
    market: DraftMarketAssumptions = Field(default_factory=DraftMarketAssumptions)
    problem_solution: DraftProblemSolutionAssumptions = Field(default_factory=DraftProblemSolutionAssumptions)
    founder: DraftFounderAssumptions = Field(default_factory=DraftFounderAssumptions)
    gtm: DraftGtmAssumptions = Field(default_factory=DraftGtmAssumptions)
    economics: DraftEconomicsAssumptions = Field(default_factory=DraftEconomicsAssumptions)
    validation: DraftValidationObservations = Field(default_factory=DraftValidationObservations)
    capital: DraftCapitalAssumptions = Field(default_factory=DraftCapitalAssumptions)


class StructureIdeaRequest(BaseModel):
    # Bounded well below MAX_COMPANY_TEXT_LENGTH (analyze's own 50,000 --
    # see app/models/startup.py) -- this is a short idea pitch, not a
    # pasted document; a generous ceiling here is about rejecting a
    # pathological paste cleanly (Part 3's "oversized input -> clean
    # 4xx"), not accommodating long-form text.
    description: str = Field(min_length=1, max_length=4000)


class StructureIdeaResponse(BaseModel):
    draft: VentureDraft
