"""
Phase 7.4 -- Founder Evidence + Milestones V1. Request/response
contracts only -- see app/database/db.py's own Phase 7.4 section for the
founder_updates table and its own statement of what this table is
(founder-REPORTED operational record) and is not (never canonical
evidence, never inserted into methodology.evidence, never a score).

Its own file for the same reason app/models/founder_action.py is its own
file: founder-reported "what actually happened" is a distinct concern
from "what the startup intends to do next" (FounderAction) and from
canonical, LLM-extracted Evidence (app/models/evidence.py).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

FounderUpdateType = Literal[
    "customer", "revenue", "product", "team", "fundraising",
    "partnership", "validation", "operations", "other",
]

# Mirrors SIEMethodologyAnalysis's six pillar field names exactly
# (app/models/startup.py), same as FOUNDER_ACTION_PILLARS in
# app/models/founder_action.py -- the only valid values for
# related_pillar.
FOUNDER_UPDATE_PILLARS = frozenset(
    {"market", "team", "product", "execution", "traction", "financial_health"}
)


class FounderUpdate(BaseModel):
    """GET/POST/PATCH .../updates row shape. Every field here is
    FOUNDER-REPORTED -- see this file's own module docstring. The
    frontend is responsible for labeling these "Founder reported"; this
    model carries no separate verification/confidence field precisely
    because founder_updates has no verification concept at all (unlike
    app/models/evidence.py's Evidence, which does)."""
    id: int
    startup_id: int
    created_by_user_id: str
    update_type: FounderUpdateType
    title: str
    description: str | None = None
    related_pillar: str | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    metric_unit: str | None = None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


class _FounderUpdateFields(BaseModel):
    """Shared field validation between create and edit requests -- see
    subclasses below for why they're not just one model."""
    update_type: FounderUpdateType = "other"
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    related_pillar: str | None = None
    occurred_at: datetime
    # Part 9: all three present or all three absent -- a metric_value
    # with no metric_name (or vice versa) is meaningless and rejected
    # here rather than silently stored half-populated.
    metric_name: str | None = Field(default=None, max_length=60)
    metric_value: float | None = None
    metric_unit: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def _metric_fields_are_all_or_nothing(self) -> "_FounderUpdateFields":
        provided = [self.metric_name, self.metric_value, self.metric_unit]
        if any(v is not None for v in provided) and not all(v is not None for v in provided):
            raise ValueError(
                "metric_name, metric_value, and metric_unit must be supplied together, or all omitted."
            )
        return self


class CreateFounderUpdateRequest(_FounderUpdateFields):
    pass


class UpdateFounderUpdateRequest(_FounderUpdateFields):
    """Full-field correction (Part 13: "If updates need correction,
    PATCH is sufficient") -- every editable field is supplied on every
    call, same shape as create, mirroring
    update_founder_update()'s own docstring in app/database/db.py."""
    pass
