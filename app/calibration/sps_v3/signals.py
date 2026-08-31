"""
Phase 10.9, Part 6: promoted to production -- see
app/ai/sps_v3_engine/signals.py (the authoritative copy). Re-exported
here so every existing calibration import and all 76 calibration tests
keep working unchanged. Signal deduplication/conflict-resolution logic
(Phase 10.8G) is unchanged by this move.
"""

from app.ai.sps_v3_engine.signals import *  # noqa: F401,F403
from app.ai.sps_v3_engine.signals import _signal_key  # noqa: F401 -- underscore-prefixed, not covered by import *
