"""
Phase 10.9, Part 6: the deterministic V3 engine (this module included) was
promoted to production at app/ai/sps_v3_engine/ -- see that package's own
module docstrings for the full architecture. This file is now a thin
re-export shim so every existing calibration import
(`from app.calibration.sps_v3.types import X`) and all 76 calibration
tests (Phases 10.8F-10.8J, frozen) keep working completely unchanged.
There is no calibration-specific content in the original types.py this
file replaces -- it was pure evidence taxonomy with no dependency on the
calibration harness's SyntheticCompany/leakage-checking machinery, so the
promotion is a pure relocation, not a fork. The one authoritative copy of
every type now lives in app.ai.sps_v3_engine.types.
"""

from app.ai.sps_v3_engine.types import *  # noqa: F401,F403
