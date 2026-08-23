# SIE Reliability Harness

A standalone regression harness (not unit tests) for measuring whether the
six-pillar SIE scoring system produces reproducible results when given the
SAME evidence twice, isolated from research/enrichment nondeterminism.

This is the `app/calibration/` suite's companion, not a replacement for it:

- **calibration** answers "is this score in a reasonable absolute range for
  a known company?" (single run per benchmark, wide range checks).
- **reliability** answers "does re-scoring the exact same evidence produce
  materially the same result?" (N repeated runs of one frozen input,
  variance/flip-rate checks).

## Structure

- `frozen_evidence.py` -- `FrozenEvidencePacket` dataclass + JSON load/save.
- `fixtures/` -- captured frozen evidence packets (company_text, search
  query, research brief, sources, and the exact enriched_text that was fed
  to pillar analysis).
- `capture_frozen_evidence.py` -- one-off script that calls live research
  enrichment ONCE to build a fixture. Not part of the repeated-run loop.
- `harness.py` -- `score_frozen_evidence()`, the seam that scores a frozen
  packet's enriched_text via `analyze_pillars_from_enriched_text()`
  (`app/workflows/due_diligence_workflow.py`) without calling live research.
- `stats.py` -- variance / range / flip-rate computation over N runs.
- `run_reliability_harness.py` -- runs a fixture N times, saves the full
  raw results, prints a gate pass/fail summary.
- `reports/` -- full JSON output from each harness run, for later
  comparison (e.g. before/after a reliability fix).

## Running

```bash
# One-time: capture a frozen evidence packet (calls OpenAI + Tavily once)
python -m app.reliability.capture_frozen_evidence novaledger

# Repeated: score the frozen packet N times (no live research calls)
python -m app.reliability.run_reliability_harness novaledger --runs 10 --label before
```

## Reliability gates (initial)

| Metric | Gate |
| --- | --- |
| Overall SPS range | <= 1.0 (target <= 0.5) |
| Pillar score range | <= 0.2 (0-10 scale) |
| Evidence-status flip rate | 0% Scored <-> Unavailable flips |
| Pillar-confidence flip rate | 0 category flips |
| Null/Unavailable pillar flip rate | 0 flips |

These are diagnostic thresholds for the reliability sprint, not
methodology/calibration thresholds -- do not use this harness to justify
changing pillar weights, subscore weights, or score bands.
