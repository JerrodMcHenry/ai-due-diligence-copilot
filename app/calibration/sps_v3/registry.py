"""
Phase 10.9, Part 6: promoted to production -- see
app/ai/sps_v3_engine/registry.py (the authoritative copy) and this
package's types.py for the full re-export rationale. Re-exported here so
every existing calibration import and all 76 calibration tests keep
working unchanged. The registry's 24 provisional parameters (Phase 10.8J)
are unchanged by this move -- this is a relocation, not a recalibration.
"""

from app.ai.sps_v3_engine.registry import *  # noqa: F401,F403
from app.ai.sps_v3_engine.registry import DEFAULT_REGISTRY  # noqa: F401
