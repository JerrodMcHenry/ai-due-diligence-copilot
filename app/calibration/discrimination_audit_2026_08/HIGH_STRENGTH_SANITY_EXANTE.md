# V2.1 High-Strength Sanity Check — Ex-Ante Record

**Recorded: 2026-08-29, before any of the three companies below were run
through the pipeline.**

Three companies were selected as intentionally strong sanity cases to
test whether Methodology V2.1's upper SPS range (80+, 85+) is
practically reachable for genuinely exceptional, extremely
well-documented real companies:

1. **Stripe** — stripe.com
2. **Canva** — canva.com
3. **SpaceX** — spacex.com

Rationale for selection: all three are among the most publicly
documented, highest-performing private technology companies in the
world (extensive press coverage, disclosed funding/valuation history,
well-known founders, large publicly-described customer/usage bases) —
if V2.1's upper range is reachable at all from public-information input,
these are among the most favorable real-world cases available. This is
a deliberate selection FOR strength, not a representative or random
sample, and its result says nothing about typical-company discrimination
(that remains Phase 10.8C's job with an independently-selected cohort).

**No numeric SPS expectation is recorded here or anywhere supplied to
the pipeline.** No score, score range, or pillar-level expectation was
written down before running, per this test's own instruction. Whatever
each company scores is preserved and reported as-is; this document will
not be edited after the run to add a prediction retroactively.

No methodology, scoring, anchor, confidence-cap, research, evidence, or
weight code is modified by this test. The runner instruments the
existing, unmodified V2.1 pipeline (via monkeypatched observation
wrappers around `apply_confidence_score_cap` and `apply_provenance_guard`
that call straight through to the real, unmodified functions) purely to
record pre-cap/post-cap scores and provenance-guard activity for
reporting -- it changes no return value and no production behavior.

Results are isolated: zero database writes, same pattern as
`app/calibration/validation_2026_08/` and
`app/calibration/discrimination_audit_2026_08/diagnostic_replay_v2_1.py`.
