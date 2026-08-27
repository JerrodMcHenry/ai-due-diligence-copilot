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
    "other",
]

MissionSource = Literal["vps_guidance", "founder_created"]

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


class UpdateMissionStatusRequest(BaseModel):
    status: MissionStatus


class RecordMissionLearningRequest(BaseModel):
    learning_summary: str = Field(min_length=1, max_length=4000)


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
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
