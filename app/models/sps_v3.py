"""
Phase 10.9, Part 5 -- SPS V3 canonical contract.

This is the ONLY new top-level concept added to SIEMethodologyAnalysis
(app/models/startup.py) for V3 production integration: a single optional
field, `sps_v3`, carrying everything the three-axis (Strength/Coverage/
Confidence) V3 assessment produces. Nothing here replaces or reinterprets
`startup_intelligence_score` / `startup_scorecard` (V2.1, frozen) -- a
record with `sps_v3=None` is a normal V2.1-only analysis, exactly as
every historical record already is; V3 is additive, never a silent
reinterpretation (Phase 10.9 Part 3).

`overall_score` below is `float | None` -- None means "not enough
evidence to responsibly publish an overall score," and MUST NEVER be
read as, or defaulted to, zero anywhere downstream (Phase 10.9 Part 13).
This is the field V2.1's own `startup_intelligence_score` (a non-nullable
float defaulting to 0.0, see app/models/startup.py) cannot safely be
reused for -- see docs/methodology/SPS_V3_PRODUCTION_INTEGRATION_10_9.md
Section 2 for the full reasoning.
"""

from pydantic import BaseModel, Field
from typing import Literal


SPSV3ConfidenceLevel = Literal["Low", "Medium", "High"]

# Phase 10.9 Part 2/12: the three deterministic UX states, computed by
# app.ai.sps_v3_engine.aggregation.classify_ux_state() and carried
# through unchanged -- this field is a direct copy of that function's
# output, never re-derived independently by any other layer.
SPSV3AssessmentState = Literal["sufficient", "limited", "insufficient"]


class SPSV3PillarResult(BaseModel):
    pillar: str = ""

    # None means this pillar itself did not clear its own coverage floor
    # -- never a fabricated/defaulted number (Phase 10.9 Part 2/15).
    strength: float | None = None

    coverage_pct: float = 0.0
    confidence: SPSV3ConfidenceLevel = "Low"

    # Whether THIS pillar (independent of the overall SPS) is
    # individually publishable -- the basis for the LIMITED state's
    # partial pillar display (Phase 10.9 Part 2).
    publishable: bool = False

    withhold_reason: str | None = None


class SPSV3Assessment(BaseModel):
    # Distinct from V2.1's analysis_context.methodology_version /
    # scoring_version (app/ai/sie_v2_methodology.py, scoring_methodology.py)
    # by design -- Phase 10.9 Part 28 explicitly forbids reusing a V2.1
    # version string for V3.
    engine_version: str = ""
    scoring_version: str = ""

    # The published Startup Power Score under the V3 methodology. None
    # is a legitimate, common, and EXPECTED value -- it means
    # assessment_state != "sufficient", never that the startup scored 0.
    overall_score: float | None = None

    coverage_pct: float = 0.0
    confidence: SPSV3ConfidenceLevel = "Low"

    assessment_state: SPSV3AssessmentState = "insufficient"
    withhold_reason: str | None = None

    pillars: dict[str, SPSV3PillarResult] = Field(default_factory=dict)

    # ISO-8601 timestamp of when this assessment was computed -- distinct
    # from the analysis's own created_at (persistence layer), since a
    # future explicit reanalysis (Phase 10.9 Part 25) could recompute
    # sps_v3 against evidence gathered at a different time than the rest
    # of the analysis, even though that path isn't built in this phase.
    computed_at: str = ""
