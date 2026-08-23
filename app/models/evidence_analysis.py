"""
Typed intermediate representation between raw enriched text and scoring
(SIE Evidence/Scoring Separation sprint).

This is deliberately the ONLY new model this sprint introduces. It
reuses ConfidenceLevel and EvidenceStatus from app.models.scoring rather
than redefining them, and the final scored output continues to be the
existing Subscore/PillarScoreBreakdown models -- this type exists only
to make the intermediate "what evidence exists, before scoring" step
inspectable, not to duplicate anything scoring already owns.

CRITICAL: EvidenceAnalysis carries no numeric score. That is the whole
point -- it is the object the evidence-extraction stage produces and the
scoring stage consumes, and a score cannot leak backward into it.
"""

from pydantic import BaseModel, Field

from app.models.scoring import ConfidenceLevel, EvidenceStatus


class EvidenceAnalysis(BaseModel):
    """One scoring dimension's evidence assessment -- no score."""

    dimension: str = ""

    evidence_status: EvidenceStatus = "Unavailable"

    confidence: ConfidenceLevel = "Low"

    # Quoted/paraphrased facts supporting the assessment -- same shape
    # as Subscore.evidence, so it can be copied forward unchanged.
    evidence: list[str] = Field(default_factory=list)

    # Short, structured facts distinct from the quoted evidence above
    # (e.g. "MRR grew $18K to $61K in two quarters" rather than a full
    # quoted sentence). This is what Subscore.signals is populated from.
    signals: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(default_factory=list)

    # Next diligence step when evidence is missing/thin. Kept here (not
    # invented as a scoring-stage concept) since "what should we go find
    # out" is a direct consequence of what evidence does/doesn't exist.
    recommendations: list[str] = Field(default_factory=list)

    # Why this evidence_status/confidence was assigned -- an evidence-
    # classification rationale, distinct from the scoring stage's own
    # rationale for why a specific number follows from this evidence.
    # Keeping the two separate is what makes it possible to tell
    # classification drift (this field changing) apart from numeric-
    # scoring drift (only the scoring stage's rationale changing) in the
    # reliability harness.
    rationale: str = ""


class PillarEvidenceAnalysis(BaseModel):
    """All of one pillar's dimension-level evidence assessments."""

    pillar: str = ""

    dimensions: list[EvidenceAnalysis] = Field(default_factory=list)

    def get(self, dimension_name: str) -> EvidenceAnalysis | None:
        for dimension in self.dimensions:
            if dimension.dimension == dimension_name:
                return dimension
        return None
