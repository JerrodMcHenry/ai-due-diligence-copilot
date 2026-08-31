"""
Phase 10.9, Part 6: promoted to production -- see
app/ai/sps_v3_engine/evaluators.py (the authoritative copy of all 27
deterministic evaluators). Re-exported here so every existing calibration
import and all 76 calibration tests keep working unchanged.

The production copy's function signatures are typed against the new
production `EvidenceBundle` (app.ai.sps_v3_engine.evidence_bundle)
instead of this package's own `SyntheticCompany`
(app.calibration.sps_v3.company) -- harmless, since every evaluator was
always duck-typed on `.evidence`/`.negative_signals`/`.stage` only, never
on an isinstance check against either class (verified before this move).
SyntheticCompany itself is completely untouched by this phase.
"""

from app.ai.sps_v3_engine.evaluators import *  # noqa: F401,F403
from app.ai.sps_v3_engine.evaluators import (  # noqa: F401
    ALL_EVALUATORS,
    DIMENSION_PILLARS,
    PILLAR_WEIGHTS,
    evaluate_all_dimensions,
    evaluate_all_dimensions_with_staleness_report,
)
