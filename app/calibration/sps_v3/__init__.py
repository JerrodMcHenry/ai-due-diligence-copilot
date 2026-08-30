"""
Phase 10.8F -- SPS V3 isolated experimental calibration harness.

EXPERIMENTAL / CALIBRATION CODE ONLY. Nothing under this package is
imported by, or importable into, any production code path
(app/api.py, app/workflows/, app/ai/analyze_pillar.py, etc.). It exists
solely to convert the design proposed in docs/methodology/
SPS_V3_RULEBOOK.md and SPS_V3_CALIBRATION_PLAN.md into executable,
deterministic, pure-Python behavior and attack it with synthetic
(never real-company) evidence, before any production V3 engineering
begins.

Zero database access. Zero network calls. Zero LLM calls. Zero
environment-variable dependency. Pure, deterministic Python.
"""
