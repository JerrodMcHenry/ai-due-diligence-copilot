"""
Phase 10.9, Part 6: promoted to production -- see
app/ai/sps_v3_engine/factory.py (the authoritative copy of the typed
evidence builder helpers). Re-exported here so every existing calibration
import (profiles.py, calibration_evidence.py, and all test files) keeps
working unchanged. Pure builder functions over types.py -- no dependency
on the calibration harness's SyntheticCompany, so this was a pure
relocation, not a fork.
"""

from app.ai.sps_v3_engine.factory import *  # noqa: F401,F403
from app.ai.sps_v3_engine.factory import _next_id  # noqa: F401 -- underscore-prefixed, not covered by import *
