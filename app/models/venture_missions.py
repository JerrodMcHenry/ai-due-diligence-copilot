"""
Phase 10.7 -- Founder Missions V1 -- request/response contracts.

A venture_missions row is an ACTIVITY, never evidence. Nothing in this
file, and no endpoint that uses it, can carry a validation number into
VentureAssumptions -- a mission has a free-text `learning_summary` and
nothing else structured. An explicit change to VentureAssumptions.
validation still only ever happens through UpdateVentureRequest (see
app/models/idea_lab.py), the same path a manual edit already used before
this phase existed.

Deliberately its own module, not added to idea_lab.py -- a mission is
conceptually adjacent to a modeled venture but is not part of its scored
model, and keeping the files separate makes it visually obvious that
nothing here feeds compute_vps().
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MissionType = Literal[
    "customer_discovery",
    "validation",
    "pricing",
    "gtm",
    "product",
    "founder",
    "economics",
    # Phase 34D -- SIE Build Intelligence Loop V1. Widened per the accepted
    # architecture (docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md
    # §D.1) to cover the fuller test taxonomy
    # (docs/product/SIE_BUILD_METHODOLOGY_V1.md §10) a Test can now
    # represent -- purely additive, every existing row's mission_type
    # remains valid.
    "problem_interview",
    "prototype_test",
    "landing_page_test",
    "willingness_to_pay_test",
    "paid_pilot",
    "pre_sale",
    "outbound_test",
    "pricing_test",
    "channel_test",
    "retention_observation",
    "competitive_research",
    "unit_economics",
    "other",
]

MissionSource = Literal["vps_guidance", "founder_created", "pitch_deck_coach"]

MissionStatus = Literal["active", "completed", "dismissed"]


class CreateMissionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    mission_type: MissionType = "other"
    # Free text, deliberately not constrained to VPS_CATEGORIES (app/ai/
    # vps_scoring.py) at the Pydantic layer -- this is a display label for
    # the mission, not a foreign key into the scoring engine, and a
    # founder-created mission may not map to any VPS category at all.
    related_category: str | None = Field(default=None, max_length=50)
    source: MissionSource = "founder_created"
    # Phase 11, Part 14: a playbook slug the CALLER already resolved
    # (dashboard/lib/playbooks/resourceMap.ts) -- this endpoint never
    # looks one up itself, and never validates it against the playbook
    # catalog (that catalog is frontend-only content, per
    # dashboard/content/playbooks/'s own module boundary). None is the
    # correct, common value for every mission with no obvious playbook
    # fit -- never fabricated.
    resource_ref: str | None = Field(default=None, max_length=100)
    # Phase 34D -- SIE Build Intelligence Loop V1. The specific unknown
    # this Test targets, and why it matters -- both optional (a founder's
    # own ad-hoc action may have neither), both immutable once set (see
    # add_venture_intelligence_columns() in app/database/db.py). Together
    # these give "the question this test was answering" a stable, durable
    # anchor without a separate Hypothesis/Unknown table -- see
    # docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md §D.1/§G for
    # the full reasoning.
    question_text: str | None = Field(default=None, max_length=500)
    why_it_matters: str | None = Field(default=None, max_length=1000)


class UpdateMissionStatusRequest(BaseModel):
    status: MissionStatus


class RecordMissionLearningRequest(BaseModel):
    learning_summary: str = Field(min_length=1, max_length=4000)


# Phase 23 -- Universal Founder Capture V1. "What happened?" -- the
# founder's own words are the ONLY required field. `title` is never
# asked of the founder separately (see app/api.py::capture_observation()
# for how it's derived); `category` is the same free-text, unvalidated
# display label venture_missions.related_category already is everywhere
# else (never a foreign key into VPS_CATEGORIES). This is a request
# shape, not a new persistence shape -- it maps directly onto
# db.capture_venture_observation()'s existing venture_missions columns.
class CaptureObservationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    category: str | None = Field(default=None, max_length=50)


class VentureMissionResponse(BaseModel):
    id: int
    venture_id: int
    created_by_user_id: str
    title: str
    description: str | None = None
    mission_type: str
    related_category: str | None = None
    source: str
    source_ref: str | None = None
    status: str
    learning_summary: str | None = None
    learning_recorded_at: datetime | None = None
    resource_ref: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    # Phase 34D -- SIE Build Intelligence Loop V1. See CreateMissionRequest's
    # own comment for question_text/why_it_matters. interpretation_* is
    # written once confirmed Evidence exists for this mission (see
    # app/ai/build_recommendation.py::generate_interpretation()) and may be
    # UPDATED (not appended) if further evidence arrives before the mission
    # completes -- the one place in this phase's design where in-place
    # update is correct, mirroring learning_summary's own existing
    # update-in-place semantics for the identical reason.
    question_text: str | None = None
    why_it_matters: str | None = None
    interpretation_summary: str | None = None
    interpretation_limitations: str | None = None
    interpretation_generated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Phase 34D -- SIE Build Intelligence Loop V1. Evidence + Decision contracts.
# See docs/product/SIE_BUILD_METHODOLOGY_V1.md (canonical methodology) and
# docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md §D.2/§D.3 (accepted
# schema) -- this file implements that schema exactly, not a competing
# design.
# ---------------------------------------------------------------------------

EvidenceType = Literal[
    "founder_claim",
    "reported_preference",
    "observed_behavior",
    "commitment",
    "transaction",
    "longitudinal_outcome",
    "external_source",
]

# The canonical six-value provenance vocabulary (SIE_BUILD_METHODOLOGY_V1.md
# §14). EXTERNAL_SOURCE and STILL_UNKNOWN are reserved -- no code path in
# this phase produces either (no external data integration exists yet;
# "still unknown" describes the ABSENCE of evidence, never an Evidence row
# itself), but both are valid enum values so a future phase can use them
# without a migration.
Provenance = Literal[
    "founder_said",
    "founder_observed",
    "sie_inferred",
    "sie_calculated",
    "external_source",
    "still_unknown",
]

EvidenceRelationship = Literal["supports", "contradicts", "mixed", "neutral"]


class CreateEvidenceRequest(BaseModel):
    related_mission_id: int | None = None
    related_decision_id: int | None = None
    evidence_type: EvidenceType
    statement: str = Field(min_length=1, max_length=2000)
    provenance: Provenance
    source_quote: str | None = Field(default=None, max_length=2000)
    structured_field_path: str | None = Field(default=None, max_length=100)
    structured_value: float | None = None
    relationship: EvidenceRelationship | None = None
    occurred_at: datetime | None = None
    # Phase 34D §17 (idempotency): optional, client-generated. When
    # provided and a row with the same key already exists for this
    # venture, that existing row is returned unchanged rather than a
    # duplicate being inserted -- see create_venture_evidence()'s own
    # docstring in app/database/db.py.
    idempotency_key: str | None = Field(default=None, max_length=100)


# Phase 34G-A §3/§6. Founder-explicit resolution: "this result was
# incorrect / has been superseded / applied to a different segment / was
# before a major product change" are all, deliberately, the SAME
# underlying action in V1 -- a short, founder-written note explaining why
# a specific old piece of evidence should no longer be treated as the
# current picture. Never a large evidence-management system -- one field,
# one action, reusing the existing append-only superseded_by_id mechanic
# (app/database/db.py::resolve_venture_evidence_for_owner()).
class ResolveEvidenceRequest(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=1000)


class VentureEvidenceResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    related_mission_id: int | None = None
    related_decision_id: int | None = None
    evidence_type: str
    statement: str
    provenance: str
    source_quote: str | None = None
    structured_field_path: str | None = None
    structured_value: float | None = None
    relationship: str | None = None
    founder_confirmed: bool
    superseded_by_id: int | None = None
    occurred_at: datetime | None = None
    recorded_at: datetime


class CreateDecisionRequest(BaseModel):
    related_mission_id: int | None = None
    sie_recommendation: str = Field(min_length=1, max_length=2000)
    sie_reasoning: str = Field(min_length=1, max_length=2000)
    founder_choice: str = Field(min_length=1, max_length=500)
    founder_rationale: str | None = Field(default=None, max_length=2000)
    evidence_ids: list[int] = Field(default_factory=list)
    # Set when this Decision reverses/revises an earlier one -- the prior
    # row is never edited or deleted (§18 append-only history).
    supersedes_decision_id: int | None = None
    idempotency_key: str | None = Field(default=None, max_length=100)


class VentureDecisionResponse(BaseModel):
    id: int
    venture_id: int
    user_id: str
    related_mission_id: int | None = None
    sie_recommendation: str
    sie_reasoning: str
    founder_choice: str
    founder_rationale: str | None = None
    evidence_ids: list[int]
    supersedes_decision_id: int | None = None
    decided_at: datetime


class CurrentQuestion(BaseModel):
    mission_id: int
    question_text: str
    why_it_matters: str | None = None


class BlockingEvidenceItem(BaseModel):
    """
    Phase 34G-A §2/§3. One specific evidence row currently pinning the
    recommendation at its stage because it contradicts (or is tagged
    mixed against) other evidence at the same stage -- never the full
    evidence history, only the rows a founder-facing "was this
    addressed?" affordance should render next to. Resolving one (via
    `POST /ventures/{id}/evidence/{evidence_id}/resolve`) does not edit
    or delete it -- see `resolve_venture_evidence_for_owner()` in
    app/database/db.py.
    """
    id: int
    statement: str
    relationship: str


class BuildRecommendation(BaseModel):
    question_text: str
    why_it_matters: str
    recommended_test_type: MissionType
    recommended_test_title: str
    what_to_do: str
    what_to_record: str
    what_result_would_be_informative: str
    what_this_will_not_prove: str
    # Phase 34G-A §2/§3/§10. Non-empty exactly when a live, unresolved
    # contradiction/mixed tension is what's pinning this recommendation --
    # see BlockingEvidenceItem. Empty list (never omitted) when nothing is
    # blocking, so the frontend never has to special-case a missing field.
    blocking_evidence: list[BlockingEvidenceItem] = Field(default_factory=list)


class CompanyIntelligenceSummary(BaseModel):
    """
    Phase 34G -- SIE Intelligence Advantage V1, §10-13. A concise,
    evidence-driven "what SIE knows / what SIE is still figuring out /
    what changed recently" summary -- see
    app/ai/build_recommendation.py::build_company_intelligence_summary()
    for exactly how each list is derived (always from already-persisted
    rows, never invented, never a score). Any list may be empty --
    state-dependent rendering on the frontend means an empty section is
    simply not shown (§18: a brand-new venture should not need to render
    every section).
    """
    what_sie_knows: list[str] = Field(default_factory=list)
    still_figuring_out: list[str] = Field(default_factory=list)
    what_changed: list[str] = Field(default_factory=list)


class BuildRecommendationResponse(BaseModel):
    """
    GET /ventures/{venture_id}/recommendation. Deliberately its own small
    read-only endpoint rather than fields bolted onto VentureResponse
    (app/models/idea_lab.py) -- VentureResponse is unpacked from a plain
    dict at three call sites (create/get/update) in app/api.py, and this
    keeps that existing, working shape completely untouched. `current_question`
    is None exactly when no active mission carries a question_text right
    now; `recommendation` is None exactly when a question IS currently
    active (there is nothing new to recommend until it resolves).
    `company_intelligence` (Phase 34G) is computed in the same call --
    no second round-trip -- from the same evidence/mission rows already
    fetched to answer the recommendation question.
    """
    current_question: CurrentQuestion | None = None
    recommendation: BuildRecommendation | None = None
    company_intelligence: CompanyIntelligenceSummary = Field(default_factory=CompanyIntelligenceSummary)
