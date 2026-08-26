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
