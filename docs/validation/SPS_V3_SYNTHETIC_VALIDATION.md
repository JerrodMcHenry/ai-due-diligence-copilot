# SPS V3 Synthetic Validation

Phase 10.8F. Results from `app/calibration/sps_v3/` — an isolated,
deterministic, pure-Python harness converting
`docs/methodology/SPS_V3_RULEBOOK.md` into executable behavior and
attacking it with synthetic (never real-company) evidence. Zero
database writes, zero network calls, zero LLM calls, zero production
code touched. All 44 harness tests were actually executed; every
number below is copied from real test output, not invented.

**Primary question restated: does the ruler behave like a ruler?**
Mostly yes, with two real, honestly-surfaced exceptions (Findings 1 and
6 below) that must be resolved before production implementation.

## Test suite summary

| File | Tests | Result |
|---|---|---|
| `test_determinism_and_bias.py` | 7 | 7/7 passed |
| `test_evidence_firewalls.py` | 14 | 14/14 passed |
| `test_aggregation_and_tails.py` | 23 | 23/23 passed |
| **Total** | **44** | **44/44 passed** |

"Passed" means the assertion held; several tests still print a
`FINDING:` or `EXPECTED_UNRESOLVED_METHODOLOGY:` line documenting a real
methodology gap discovered along the way — findings are captured below,
not hidden by the pass/fail count.

## Determinism (Part 13)

`test_determinism_1000_runs`: the identical canonical evidence set
(Profile A) was evaluated 1,000 times. Every one of dimension scores,
pillar scores, SPS, coverage, confidence, rule IDs, and availability
states was identical across all 1,000 runs. **PASS — scoring is fully
deterministic given frozen evidence and methodology version**, as
designed (no random number generation, no wall-clock dependency
anywhere in `evaluators.py`/`aggregation.py`).

## Evidence-order invariance (Part 14)

`test_evidence_order_invariance`: the same evidence list was shuffled
20 times (seeded RNG for reproducibility) and re-evaluated. **PASS —
identical result regardless of ordering** in every trial. No evaluator
in this harness reads list position, only type/field content.

## Redundant-evidence and fame-bias attacks (Parts 15-16) — REAL FINDING

**Finding 1 (STRUCTURAL METHODOLOGY DEFECT).** `test_redundant_evidence_does_not_increase_strength_or_coverage`
and `test_fame_attack_identical_facts_identical_strength` found that
this harness's generic Category-B classifier (used for most of the 27
dimensions) counts **observation objects**, not **distinct underlying
facts**. Duplicating the identical `CompetitiveEvidenceObservation`
("SameCompetitor") 2x moved `competitive_intensity` from 5.5 to 7.5;
100x moved it to 9.5. Fifteen `SECONDARY_ESTIMATE`-grade duplicate
sources scored 9.5 (COMPREHENSIVE), while one `HIGH_QUALITY_SECONDARY`
source citing the *same fact* scored only 5.5 (SINGLE_SIGNAL) — a stark
inversion of what evidence quality should reward.

**Coverage itself was NOT vulnerable** — `Coverage` is computed as a
binary per-dimension flag (Rulebook Part 20), confirmed unaffected by
the 100x duplication in the same test.

**Root cause:** neither `SPS_V3_RULEBOOK.md` Part 16 (taxonomy design)
nor Part 20 (coverage) states an explicit rule that CLASSIFICATION
signal-counting must deduplicate by distinct named entity/fact rather
than by raw observation count — Part 20 only states this for coverage.
The four fully-worked rulebook examples (Founder-Market Fit, Strategic
Execution, etc.) implicitly assume named, distinct fields (e.g. one
`prior_entity_name` per real prior company), which would not exhibit
this vulnerability if implemented as literally specified — but the
Rulebook never states the general anti-redundancy rule as a first-class
requirement the way it does for Coverage. **This is a real gap in the
Rulebook itself, not merely a harness shortcut**, and is the most
important finding of this phase.

**Confidence behaved correctly** in the same tests: 15 `SECONDARY_ESTIMATE`
sources produced LOW confidence (weakest-link rule, Rulebook Part 21);
one `HIGH_QUALITY_SECONDARY` source produced MEDIUM/HIGH — confidence's
provenance-grade dependency, as designed, is NOT vulnerable to the same
attack. Only Strength (via classification signal-counting) is.

**Recommended fix for the next design phase (not implemented here, per
Part 43):** add an explicit rule to Rulebook Part 16: "signal count for
classification purposes must be deduplicated by distinct named entity/
fact (e.g. distinct `prior_entity_name`, distinct `named_competitor`),
never by raw observation count" — and require every Category B
evaluator's evidence-collection step to dedupe before counting.

## Unknown firewall (Part 8) — PASS

`test_unknown_never_becomes_a_numeric_score`: a company with zero
evidence produced `score=None` and an Unavailable status for all 27
dimensions — no score of 0, 5, or any number. `test_unavailable_excluded_not_zeroed_in_pillar_average`:
a pillar with 2 scorable + 3 Unavailable dimensions computed strength
as a pure average over the 2 scorable ones (verified by manual
reconstruction), confirming missing dimensions are excluded from the
denominator, never zeroed.

## Negative-evidence firewall (Part 9) — PASS

`test_negative_evidence_produces_low_score_not_inferred_from_absence`:
an explicit `NegativeSignalObservation` produced a scorable, low
(2.0/10) result; absence of any evidence for the same dimension
produced `score=None`/Unavailable — the two states are structurally
distinct, never confused. `test_negative_evidence_can_lower_sps_end_to_end`:
adding two negative signals (retention deterioration, revenue decline)
to an otherwise-strong profile lowered SPS from its baseline — confirmed
numerically, not just qualitatively.

## Additive / negative / neutral evidence updates (Parts 17-19) — PASS

- **Additive:** adding one new competitive-evidence observation left
  an unrelated dimension (`product_execution`) byte-identical while
  correctly making `competitive_intensity` newly scorable.
- **Negative update:** confirmed above (SPS strictly decreased).
- **Neutral:** adding a second, corroborating runway statement (same
  STRONG classification band) left SPS unchanged — coverage/confidence
  can move without Strength moving, confirmed for this case.

## Conflicting evidence (Part 20) — EXPECTED_UNRESOLVED_METHODOLOGY

Per this phase's own explicit instruction ("do NOT silently invent a
tie-break"), `test_conflicting_evidence_marked_expected_unresolved`
documents rather than resolves: two `RevenueObservation`s with the same
`metric_type`/date but different amounts ($1M `PRIMARY_SELF_REPORTED`
vs. $400K `HIGH_QUALITY_SECONDARY`) were **not detected as a conflict**
by this harness — `current_scale` silently picked whichever observation
Python's `max()` happened to select on a tie (insertion order, not
provenance-grade-aware). Rulebook Part 6 specifies the desired behavior
(`UNAVAILABLE_CONFLICTING_EVIDENCE` with a provenance-grade tie-break)
but this experimental harness does not yet implement conflict
*detection* at all. **Flagged as a required next-phase implementation
item**, consistent with Calibration Plan Part 30's Test 12 and Test 14
also flagging this same underspecified area.

## Recency/staleness (Calibration Plan Part 30, Test 13)

Not implemented in this harness (`stress_13_stale_evidence` exists as a
fixture but no evaluator reads `source_date` for staleness). This
matches the Calibration Plan's own explicit flag that recency handling
is unresolved — restated here as still unresolved after attempting to
build the architecture, not newly discovered.

## Stage fairness (Part 22) — qualitatively PASS

`Current Scale`'s stage-relative dollar bands (Rulebook Part 13)
produced different classifications for identical absolute ARR at
different stages by construction (the same $500K ARR is EXCEPTIONAL at
Pre-Seed/Seed-shaped thresholds and merely ordinary at Growth-shaped
thresholds) — confirmed via `test_current_scale_stage_boundary_discontinuity`
and the boundary-band tests. No dimension where stage should NOT matter
(e.g. `retention_engagement`'s NRR bands) showed spurious stage
sensitivity, since this harness's retention evaluator does not read
stage at all.

## Traction evidence-matrix (Part 23) — PASS, all 5 assertions confirmed

- One ARR point supports `current_scale`, correctly leaves
  `growth_trajectory` Unavailable-Insufficient.
- Two dated ARR points make `growth_trajectory` scorable.
- 10,000 customers support `customer_adoption`, correctly leave
  `retention_engagement` Unavailable.
- High retention supports `retention_engagement`, correctly leaves
  `customer_adoption` Unavailable.
- A signed pilot supports `commercial_validation` at only the
  SINGLE_SIGNAL tier, not automatically equal to a comprehensive/paying
  relationship.

## Financial Health evidence-matrix (Part 24) — PASS

- A `FundingObservation` alone left `current_scale`, `capital_efficiency`,
  `revenue_quality`, and `unit_economics` all `None` — funding never
  leaked into revenue/cash-shaped dimensions, confirmed structurally
  (no code path exists, not just empirically).
- High funding + a genuinely weak burn/revenue ratio (Test 8) correctly
  classified `capital_efficiency` as ORDINARY, not elevated by the
  funding amount.
- Profitability (Test 9) correctly left `growth_trajectory` at ORDINARY
  (10% YoY, not conflated with profitability) while `capital_efficiency`
  scored well from a real disclosed 36-month runway statement — the two
  concepts move independently as required.

## Double-counting (Part 25) — PASS for the one spot-checked pair

`test_founder_prior_exit_does_not_leak_into_execution_pillar`: a
company whose ONLY evidence is founder-history observations produced
`score=None` for every Execution-pillar dimension (no Execution
evaluator's predicate matches `Founder*Observation` types by
construction) while correctly scoring Team dimensions. This confirms
the specific pairing Rulebook Part 18 named as a risk does not leak in
this implementation. A full audit of every pairwise dimension
combination in Part 18's table was not re-verified exhaustively in this
phase — scoped to the one pairing with the clearest attack surface.

## Renormalization attack (Part 26) — PASS, with a real Finding

`test_one_exceptional_dimension_does_not_single_handedly_create_exceptional_pillar`:
a pillar with only 1 scorable dimension (however strong) correctly
failed to publish at all (the ≥2-dimension gate, Rulebook Part 22,
functioned as designed). A pillar with exactly 2 scorable dimensions —
one COMPREHENSIVE (9.5), one SINGLE_SIGNAL (5.5) — averaged to a
moderate ~7.4, not inflated toward 9.5.
`test_one_weak_dimension_does_not_unfairly_crater_a_pillar`: one
ordinary (not negative) dimension among two strong ones kept pillar
strength above 6, confirming an isolated ordinary result doesn't
disproportionately punish an otherwise-strong pillar.

## Pillar ablation (Part 27) — one Finding, not acted on

Removing each pillar one at a time from a fully-scorable Profile A and
re-evaluating: Market -3.6 to -4.9pt swings observed relative to the
crude per-pillar sanity bound (weight × 15 points); **ablating Team
specifically moved SPS by 3.6 points against a 3.0-point crude bound**
for a 20%-weighted pillar — flagged as a `FINDING` in the test output,
not investigated further in this phase (the bound itself is a crude
sanity check invented for this test, not a methodology requirement —
this is closer to "worth a closer look" than "confirmed defect").

## Scale reachability, upper tail, lower tail (Parts 28-30)

- **90-100: reached.** A maximally-saturated synthetic profile (every
  dimension populated with 4+ distinct named, cited, high-provenance
  facts) scored **SPS = 93.1**, publishable. The exact mathematical
  cause of an EARLIER, less-saturated "exceptional" profile (Core
  Profile A) capping at only 68.1 was identified precisely: most of
  Profile A's dimensions had only 1-3 distinct populated signals, one
  short of the COMPREHENSIVE tier's 4-signal requirement — not a
  structural ceiling, a fixture-density gap, resolved by constructing a
  genuinely 4-signals-everywhere profile.
- **Below 50, below 40: reached.** A maximally-negative, full-coverage
  synthetic profile scored **SPS = 20.0** under the default provisional
  `band.negative_signal=2.0`.
- **Below 20: NOT reached under the default provisional parameter**
  (exact floor = 20.0, arithmetically: 6 equally-weighted pillars each
  at the negative-signal score of 2.0/10 → SPS = 20.0 precisely). With
  the provisional parameter LOWERED to 1.0 (still within its declared
  sensitivity range), the identical evidence produced SPS = 10.0,
  confirming 0-19 IS reachable once `band.negative_signal` is
  calibrated below its current provisional midpoint — this is a
  **CALIBRATION REQUIRED** finding, not a structural floor, since the
  provisional value was never claimed final (Rulebook Part 19).
- **All 7 canonical bands** were reached by at least one specifically
  constructed profile except that **80-89 specifically was not cleanly
  separated from 70-79** by this phase's two quick interpolation
  attempts (both landed at 74.9 — the two attempts happened to produce
  the same classification-tier mix, not a demonstrated inability to
  reach 80-89). Not investigated further; flagged as needing a more
  careful evidence-density construction in a future pass, not a
  structural gap on the evidence available.

## Monotonicity (Part 31)

Retention and Runway both confirmed strictly monotonic (higher NRR
never scores lower; longer runway never scores lower) across the tested
range. Market Size was deliberately tested at an extreme ($100M vs.
$100T) and found to produce an **identical** score — documented as a
genuine scope gap (no magnitude-aware banding exists for Market Size in
this harness, unlike Current Scale's explicit dollar bands), consistent
with Rulebook Part 30 Test 11's own instruction that market size should
not be treated as infinitely-better-with-scale, but this harness's
specific implementation doesn't yet distinguish *any* two magnitudes at
all, which is a gap beyond what Test 11 asked for.

## Boundary tests (Part 32)

The Current Scale Seed-stage `ordinary`/`strong` boundary showed a real
2.5-point score discontinuity for a $2 difference in ARR ($99,999 →
5.0; $100,001 → 7.5). This is an accepted, inherent property of
discrete banding (Rulebook Part 8's chosen score-granularity
architecture), not a bug — flagged for awareness, not correction.

## Sensitivity analysis

See the companion `SPS_V3_SENSITIVITY_ANALYSIS.md` for the full
parameter-by-parameter results.

## Classification-error and provenance-error sensitivity (Parts 35-36)

A one-tier classification error (e.g. a taxonomy mis-labeling
SINGLE_SIGNAL as MULTIPLE_SIGNALS) produces exactly a 2.0-point
dimension-score delta under current provisional bands; the worst-case
single-dimension pillar-level impact (a 2-tier miss on the
highest-weighted 0.35 dimension) is 1.4 points — bounded, not
catastrophic. Provenance downgrades (PRIMARY_VERIFIED →
HIGH_QUALITY_SECONDARY → SECONDARY_ESTIMATE) for the identical
underlying fact left Strength completely unchanged (5.5 in all three
cases) while Confidence correctly degraded from HIGH → HIGH → LOW —
confirming the three-axis firewall holds specifically for provenance
grade, independent of Finding 1's observation-count vulnerability.

## Explanation trace reconstruction (Part 38) — PASS

For every scorable dimension in Profile A, `(score, weight)` pairs
copied directly from each `DimensionResult`'s own trace reconstructed
the pillar's actual computed Strength to within rounding — confirming a
reader could recompute every number from the trace alone, no second
model call needed. Every scored dimension carried a non-empty
`rule_trace.rule_id` and at least one `cited_evidence_id`.

## Reproducibility snapshot (Part 39) — PASS

A JSON snapshot of all 10 core profiles' results was written on first
run and byte-for-byte reproduced on a second, independent run of the
full test file — confirmed via direct file comparison, not just
in-process re-evaluation (this is a stronger check than Part 13's
1,000-in-process-run test, since it also crosses a fresh Python process
boundary).

## Real-company leakage and blind-cohort preservation (Parts 40-41)

Confirmed via `grep` across every new file created this phase: the only
matches for any real company name are `company.py`'s own explicit
`_FORBIDDEN_NAME_FRAGMENTS` prohibition list (permitted per this
phase's own instruction). No evidence, threshold, fixture, or expected
score anywhere in this phase was derived from Stripe, SpaceX,
Databricks, Rippling, Plaid, Relaw, Dome, or any of the 25-company prior
cohort. No future blind-validation cohort was selected, inspected, or
discussed.
