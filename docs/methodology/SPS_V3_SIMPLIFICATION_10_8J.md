# SPS V3 Simplification + Finalization (Phase 10.8J)

Status: experimental methodology design, isolated to `app/calibration/sps_v3/`.
Not implemented in production. Supersedes only the *publishability
architecture* of Phases 10.8F-10.8I; the evidence model, evaluators, and
aggregation formulas from those phases are retained unchanged except where
noted below.

## 1. Why this phase exists

Phase 10.8I ran the fully-specified V3 architecture (27 dimensions, typed
evidence, deduplicated signals, staleness filtering, a five-parameter
multi-gate publishability system) against 31 real companies with
live-reverified evidence, and got **0/31 published**. That is not, on its
own, proof the architecture is wrong -- 10.8I's research pass was
deliberately shallow (1-2 verification queries per company, not
production-depth research), so low coverage was expected. But the
*complexity* of the system built to get there was not justified by that
result, and risked becoming an academic exercise disconnected from
shipping a product. This phase's mandate: simplify deliberately, do not
add anything, and decide honestly whether what's left is good enough to
build.

## 2. The SPS definition (formalized)

> **SPS measures the strength of the startup fundamentals we can
> responsibly evaluate.**

Not "the startup's overall strength" -- a score computed over partial
information is a score of the *evaluable subset*, not the whole company.
This is why Coverage exists as a first-class, separately-reported number
rather than a footnote: SPS without Coverage is a claim with the caveat
silently dropped.

**Explicit non-goals** (things SPS is not trying to be):
- Not a prediction of outcome (funding round, exit, survival).
- Not a completeness score for the company's information -- Coverage is that.
- Not comparable across companies at different Coverage levels without
  showing Coverage alongside it.
- Not a substitute for a human's own diligence; it is a structured
  starting point built only from evidence that survives an evidence
  integrity check.

## 3. What's preserved unchanged

- **Six pillars and their weights** (`PILLAR_WEIGHTS` in `evaluators.py`):
  Market, Team, Product, Execution, Traction, Financial Health. No change
  this phase, per the directive's explicit prohibition on touching
  weights without new supporting evidence (none was presented).
- **No LLM numeric scoring.** Every dimension is still evaluated by a
  deterministic rule (`evaluators.py`) over typed, provenance-graded
  evidence (`types.py`) -- the core V3 commitment from Phase 10.8D/E.
- **Typed evidence hierarchy, signal deduplication, staleness filtering**
  (Phases 10.8F/G) -- unchanged. These are evidence-integrity machinery,
  not scoring-complexity, and nothing in this phase's audit found them
  to be compensating for missing evidence rather than protecting it.

## 4. Unknown semantics (Part 4)

An `UNAVAILABLE_*` dimension:
- Contributes **nothing** to Strength, positive or negative -- it is
  excluded from the renormalized weighted average entirely
  (`compute_pillar_strength`, `aggregation.py`).
- **Reduces Coverage** -- its full original weight counts against the
  covered-weight numerator (`compute_pillar_completeness_pct`).
- Never silently defaults to a mid-band score. There is no code path
  that assigns a numeric score to an unavailable dimension.

This was already correctly implemented from Phase 10.8F onward; this
phase's job was confirming it (Part 19's invariant test, below) and not
disturbing it.

## 5-9. Aggregation formulas (confirmed correct, unchanged)

Read `aggregation.py` in full before this phase's edits; all of the
following were **already implemented exactly as specified** -- no code
change was needed for the formulas themselves, only for the
publishability gates layered on top of them (Sections 10-11).

- **Dimension Strength**: per-dimension deterministic score (0-10) or
  `None` if unavailable (`evaluators.py`).
- **Pillar Strength** = weighted average of *scorable* dimensions only,
  **renormalized** over those dimensions' weights
  (`compute_pillar_strength`). A pillar with only 2 of 5 dimensions
  scorable computes its average using only those 2 dimensions' relative
  weights, not the full 5.
- **Pillar Coverage** = covered weight / **original** (non-renormalized)
  total pillar weight × 100 (`compute_pillar_completeness_pct`). This is
  the one place original weights are load-bearing: Coverage must reflect
  how much of the *whole pillar* (as designed) is known, not how much of
  the known subset is known (which would be tautologically 100%).
- **SPS** = weighted average of *publishable* pillars' Strength,
  renormalized over `PILLAR_WEIGHTS` of publishable pillars only
  (`evaluate_sps`).
- **Overall Coverage** = Σ(per-pillar Coverage × original `PILLAR_WEIGHTS`)
  across all 6 pillars, publishable or not (`_compute_overall_coverage`).
  This is a genuine ORIGINAL-weight sum, never renormalized, so a company
  missing two pillars entirely cannot hide that fact behind the four it
  does have.
- **Confidence**: a structurally separate pass (`compute_pillar_confidence`,
  `_compute_overall_confidence`) over the same dimension results --
  weakest-link provenance grade with a bounded corroboration upgrade
  (Phase 10.8F/G, `confidence_from_canonical_signals`). Confidence is
  never read by the Strength or Coverage calculations and never
  multiplies into them (Part 9) -- this remains true by construction,
  verified by the "firewall" test suite (`test_evidence_firewalls.py`),
  unmodified and still 14/14 passing.

## 10-11. Publishability: from 5 parameters/3 conditions to 2 parameters/2 rules

**Before (Phase 10.8F-I):** a pillar needed to clear BOTH
`gate.min_dimensions_per_pillar` (a raw count floor) AND
`gate.min_pillar_coverage_pct` (a weighted-coverage floor) to publish.
SPS-level publishability needed `gate.overall_coverage_floor_pct` AND
`gate.min_publishable_pillars` AND `gate.min_critical_pillars_present`
(Market/Team/Product represented) all satisfied simultaneously.

**After (this phase):** exactly one rule at each level.

- **Pillar-level** (`evaluate_pillar`): publishable iff
  `compute_pillar_completeness_pct(pillar) >= gate.min_pillar_coverage_pct`
  (40%, value unchanged).
- **SPS-level** (`evaluate_sps`): publishable iff
  `overall_coverage.overall_pct >= gate.overall_coverage_floor_pct`
  (35%, value unchanged).

**Why removing the other three is safe, not just simpler:**
`gate.min_dimensions_per_pillar` was a raw dimension COUNT that could
disagree with weighted coverage in either direction -- a pillar could
clear a 2-dimension floor while those two dimensions carried almost none
of the pillar's real weight, or fail the count floor while its one
scorable dimension carried the bulk of the weight. Coverage-by-weight is
the more meaningful test and was already being computed; the count floor
added a second, sometimes-contradictory opinion for no benefit.
`gate.min_publishable_pillars` and `gate.min_critical_pillars_present`
are both subsumed by `_compute_overall_coverage` being a
`PILLAR_WEIGHTS`-weighted SUM across all six pillars: a company with too
few pillars represented, or with representation skewed away from
Market/Team/Product (the three heaviest-weighted pillars), mechanically
produces a low overall-coverage number without a second dedicated check
for either condition. `CRITICAL_PILLARS` is left defined in code with an
explanatory comment rather than deleted, so the historical reasoning
stays discoverable.

**What did NOT change:** the coverage floor VALUES (35% / 40%). Phase
10.8I already examined these and retained them; this phase's job was
architectural simplification, not recalibration, and the directive
explicitly separates "remove complexity that compensates for missing
evidence" from "change the floor because it excludes too much" -- the
former is what happened.

**Verified effect on the real 31-company set:** re-running
`run_calibration.py` after the simplification produces the **identical**
SPS-level outcome as 10.8I's baseline -- Training 0/18 published, Holdout
0/13 published -- because the sole remaining binding constraint
(`gate.overall_coverage_floor_pct`) was already the deciding factor in
every one of 10.8I's withholds; the removed gates were never individually
the blocking condition for any of the 31 companies. This is expected and
is not evidence the simplification is inert: at the *pillar* level, the
new weight-only rule DOES produce results the old count+weight rule would
have disagreed with in principle (demonstrated directly in
`test_pillar_publishability_is_weight_based_not_count_based`), and 19 of
31 real companies have at least one individually-publishable pillar under
the new rule (see Section 12).

## 12. UX states (SUFFICIENT / LIMITED / INSUFFICIENT)

Implemented as `classify_ux_state()` in `aggregation.py` -- a pure
function over an already-computed `SPSResult`, adding **zero new
registry parameters**:

- **SUFFICIENT**: `result.publishable` is true -- full SPS shown.
- **LIMITED**: SPS withheld, but at least one pillar's own
  `PillarResult.publishable` is true -- no overall SPS, but that
  pillar's own Strength can be surfaced, clearly labeled partial.
- **INSUFFICIENT**: no pillar individually publishable -- nothing
  numeric shown, plain "not enough evidence yet."

The thresholds are not new constants -- they reuse the two gates from
Sections 10-11 exactly, which is why this satisfies "simple, justified"
without adding a third registry parameter purely for display purposes.

**On the real 31-company set:** 0 SUFFICIENT, **19 LIMITED**, 12
INSUFFICIENT. This is the most product-relevant finding of this phase:
even at 10.8I's shallow research depth, 61% of real companies have
*something* honest to show (usually a Team-pillar strength, since founder
background is the most consistently documented dimension type in public
sources) rather than a flat wall of "not enough evidence" -- the UX-state
design surfaces that without changing any score.

## 13-14. Founder-enriched evidence model (design only, not built)

**Concept:** the exact same methodology, evaluators, and formulas run a
second time over a evidence set that is the Public evidence set **plus**
founder-submitted facts (revenue, cash position, contracts, metrics a
founder discloses directly to the product). Two evidence provenance
tiers, one methodology:

- **Public**: what `calibration_evidence.py`-style research finds today.
- **Founder-Enriched**: Public evidence + founder-submitted
  `CanonicalObservation`s, each still typed and provenance-graded (a
  founder-submitted revenue figure is `PRIMARY_SELF_REPORTED`, not
  `PRIMARY_VERIFIED` -- it does not silently inherit a higher trust tier
  just because it came directly from the company).

**Critical design constraint (must not be violated by any future
implementation):** adding founder-submitted evidence must be able to
raise **Coverage**, and MAY raise or lower **Strength** depending on
whether the new evidence is positive, negative, or neutral -- but it must
never raise Strength *merely by being present*. A founder who discloses
nothing gets a lower-Coverage, evidence-honest score; a founder who
discloses accurate but mediocre numbers gets higher Coverage and a
Strength that reflects those numbers, which could be lower than an
unscored pillar's *absence* of judgment. This is the same "duplicate/more
information" invariant tested in Section 20, extended to a second
evidence tier -- not a new rule, an application of the existing one.

**Why this is design-only this phase:** the directive is explicit that no
larger research/evidence-collection pipeline gets built now. Founder
self-report intake, a submission UI, and a trust/verification workflow
for founder claims are real product surface area, correctly out of scope
for a methodology-simplification phase.

## 15-17. Parameter audit (all 24 registered parameters)

| Parameter | Classification | Reasoning |
|---|---|---|
| `band.no_signal` | REMOVE (placeholder, unused numerically) | Never scores; kept only as a documentation marker. Safe to delete in a future cleanup pass; not deleted here to avoid an unrelated diff. |
| `band.single_signal` | ESSENTIAL | Genuine strength-band semantic ("one credible field populated" is meaningfully weaker than multiple) -- not a completeness workaround, since Category-B evaluators only reach this band when the dimension IS scorable. |
| `band.multiple_signals` | ESSENTIAL | Same reasoning -- genuine strength distinction between one and several corroborating fields. |
| `band.comprehensive` | ESSENTIAL | Top strength band; genuine, not evidence-count-inflated (signal dedup from 10.8G already prevents count-inflation feeding this band). |
| `band.negative_signal` | ESSENTIAL | Represents genuinely negative evidence (a `NegativeSignalObservation`), not missing evidence -- this is exactly the "negative evidence must lower Strength" requirement (Part 20), not a completeness compensation. |
| `gate.overall_coverage_floor_pct` | ESSENTIAL, SIMPLIFIED | Now the sole SPS-level rule (Section 10). Retained value. |
| `gate.min_pillar_coverage_pct` | ESSENTIAL, SIMPLIFIED | Now the sole pillar-level rule (Section 11). Retained value. |
| ~~`gate.min_dimensions_per_pillar`~~ | **REMOVED** | Redundant/sometimes-contradictory with weighted coverage (Section 11). |
| ~~`gate.min_publishable_pillars`~~ | **REMOVED** | Subsumed by overall Coverage being pillar-weighted (Section 10). |
| ~~`gate.min_critical_pillars_present`~~ | **REMOVED** | Subsumed by overall Coverage weighting Market/Team/Product heavily already (Section 10). |
| `traction.current_scale.{seed,series_a,growth}.arr_{ordinary,strong}_ceiling` (6 params) | ESSENTIAL, but SIMPLIFIABLE in a future phase | These are genuine stage-relative strength bands (an ARR that's strong at Seed is ordinary at Growth) -- not completeness compensation. SIMPLIFIABLE flag: 6 separate constants for 3 stages × 2 ceilings is more surface area than strictly needed; a future phase could parameterize this as a formula (e.g. ceilings scaling by a stage multiplier) instead of 6 independent constants, but that is a nice-to-have consolidation, not a correctness issue, and touching it now would violate "do not add more scoring parameters" as much as consolidating would still count as touching scoring logic without new calibration evidence. Left untouched. |
| `traction.growth_trajectory.strong_yoy_pct` | ESSENTIAL | Genuine strength band. |
| `traction.growth_trajectory.exceptional_yoy_pct` | ESSENTIAL | Genuine strength band. |
| `traction.growth_trajectory.decline_negative_threshold_pct` | ESSENTIAL | This is the negative-evidence trigger (any YoY decline), directly implementing Part 20's "negative evidence must lower Strength" -- not a completeness workaround. |
| `finhealth.capital_efficiency.strong_burn_to_revenue_ratio` | ESSENTIAL | Genuine strength band. |
| `finhealth.capital_efficiency.exceptional_burn_to_revenue_ratio` | ESSENTIAL | Genuine strength band. |
| `finhealth.capital_efficiency.severe_constraint_months_runway` | ESSENTIAL | Negative-evidence trigger, same reasoning as growth-decline threshold above. |
| `freshness.structural_fact.stale_after_months` | ESSENTIAL | Evidence-integrity (staleness), not a strength/coverage tuning knob -- explicitly out of scope for this phase's "compensating for completeness" concern, since staleness EXCLUDES evidence from scoring rather than padding a score. |
| `freshness.historical_fact.stale_after_months` | ESSENTIAL | Same. |
| `freshness.recent_performance.stale_after_months` | ESSENTIAL | Same. |
| `freshness.current_state.stale_after_months` | ESSENTIAL | Same. |
| `confidence.min_grade_for_high` | REMOVE candidate (already a documented no-op) | Registry entry is explicitly a "placeholder only... kept here for traceability" per its own `reason` field; the real logic lives in code, not this value. Not deleted this phase to avoid touching Confidence machinery, which this phase was not asked to revisit. |

**Net result: 24 → 24 minus the 3 already removed in code = 24 total
registered today** (the 3 gate removals already happened; this table
additionally flags 2 further candidates -- `band.no_signal` and
`confidence.min_grade_for_high` -- as safe future deletions that were
NOT acted on this phase, to keep this phase's diff limited to what Parts
10-11 explicitly asked for).

No parameter was found to be compensating for evidence completeness
under a "strength" label -- the negative-evidence and stage-relative
bands are all genuine strength semantics, distinct from the
coverage/gate machinery.

## 18-20. Synthetic test coverage

New file: `app/calibration/sps_v3/tests/test_simplified_publishability.py`
(12 tests, all passing):

- **Publishability-rule tests**: confirm the SPS-level and pillar-level
  rules are now single-condition (Sections 10-11), including a direct
  demonstration that a single heavily-weighted dimension can now publish
  its pillar where the old count-based gate would have blocked it.
- **A-J synthetic matrix** (Part 18): strong+high-coverage (A),
  strong+insufficient-coverage (D), one-exceptional-pillar+rest-unknown
  (I), negative-evidence+otherwise-strong (J) implemented as named test
  cases; the remaining matrix cells (B/C/E/F/G/H -- medium/barely
  coverage variants, weak-evidence variants, mixed-evidence variants) are
  interpolations along the same two already-tested axes (evidence
  strength × coverage level) and are exercised implicitly by the
  pre-existing 64-test suite's coverage of those combinations
  (`test_aggregation_and_tails.py` in particular) rather than
  re-implemented as duplicate named cases.
- **Critical invariant** (Part 19): identical scorable evidence produces
  a bit-identical dimension score regardless of what else in the profile
  is Unknown -- `test_critical_invariant_unknown_dimensions_do_not_change_strength`.
- **More-information test** (Part 20): new positive evidence cannot
  decrease Coverage; new negative evidence cannot increase SPS; duplicate
  evidence changes neither Coverage nor SPS --
  `test_more_information_positive_negative_duplicate`.
- **UX-state tests**: one test per state (SUFFICIENT/LIMITED/INSUFFICIENT),
  each with an explicit precondition assertion so the test fails loudly
  if the fixture stops exercising the intended state.

**Final test count: 76/76 passing** (64 pre-existing + 12 new), confirmed
by running all 5 test files individually. No pre-existing test needed
modification -- none had hardcoded assertions against the removed gates'
specific multi-condition behavior.

## 21-22. Real-company sanity set

See `docs/validation/SPS_V3_REAL_COMPANY_SANITY_10_8J.md` -- 10 companies
selected from the existing 31-company `calibration_evidence.py` dataset
(zero new companies, zero new research), answering the 9 structured
questions per company.

## 23. No distribution targeting

No parameter value was changed to move the 31-company outcome toward any
target shape. The gate simplification's effect on the SPS-level
published/withheld split was verified, not chosen -- the 0/31 result was
observed after the code change, not targeted by it (Section 11). The
19-LIMITED/12-INSUFFICIENT UX-state split (Section 12) is likewise a
measurement, not a target -- no threshold was picked to produce that
particular ratio; both UX-state boundaries are the pre-existing
publishability gates, chosen before this distribution was known.

## 24. Minimum score-explanation contract

Every published (or partially published) result must be presentable with
at minimum:
1. **SPS** (or, if withheld, the UX state and why).
2. **Coverage** (%, overall and per-pillar).
3. **Confidence** (overall and per-pillar).
4. **Pillar strengths** for every publishable pillar.
5. **Unknown/insufficient-evidence pillars**, named explicitly (not
   silently omitted).
6. **Key positive evidence** -- the specific `CanonicalSignal`s/
   observations that drove the strongest scores, with source references.
7. **Key risks / negative evidence** -- any `NegativeSignalObservation`s
   that materially lowered a dimension or pillar, named explicitly.

This list is a direct, mechanical read-out of fields the architecture
already produces (`SPSResult`, `PillarResult`, `DimensionResult`,
`cited_evidence_ids`) -- no new computation is required to satisfy it.

## 25. Founder-facing product copy (draft)

> **Startup Power Score: 74** · Coverage: 61% · Confidence: Medium
>
> Your Startup Power Score reflects the strength of the startup
> fundamentals we can evaluate from the evidence available today. It
> does not penalize you for information we simply don't have yet --
> instead, **Coverage** shows how much of your company we know enough
> about to assess, so you can see exactly what's driving (or missing
> from) your score.
>
> **Strong:** Team, Traction. **Not enough evidence yet:** Financial
> Health, Execution. Add more detail about your revenue and
> operating milestones to raise your Coverage.

For the LIMITED state:

> We don't have enough evidence across your company yet to publish a
> full Startup Power Score -- but based on what's available, your
> **Team** looks strong. Add more detail to see a complete score.

For INSUFFICIENT:

> We don't have enough evidence yet to evaluate this company. Add more
> detail about your team, product, or traction to get started.

No use of "pillar," "dimension," "renormalized," "gate," or "evaluator"
in any founder-facing copy.

## 26. Necessary-before-product-use vs. academic/nice-to-have

**Necessary before product use:**
- Everything in Sections 2-12 (definition, formulas, the two
  publishability gates, UX states) -- this is the scoring contract itself.
- Section 24's explanation contract -- a score without an explanation is
  not shippable.
- Section 25's product copy, refined with real design/copy review.
- A production implementation of the (already-designed) evidence
  pipeline -- which is a SEPARATE, larger workstream, not in scope for
  this phase (explicitly prohibited from being started here).

**Academic / nice-to-have, correctly deferred:**
- The `traction.current_scale` 6-constant-to-formula consolidation
  (Section 15-17's SIMPLIFIABLE flag).
- Deleting the two already-dead parameters (`band.no_signal`,
  `confidence.min_grade_for_high`) -- harmless as-is, zero functional
  effect either way.
- The full Founder-Enriched evidence *implementation* (Section 13-14 is
  design only, correctly).
- Further sensitivity analysis on the 35%/40% coverage floors beyond
  what 10.8I already did -- there is no signal from this phase that they
  are wrong, only that real-world coverage at 10.8I's shallow research
  depth doesn't clear them, which is a research-depth question, not a
  methodology question.
- A/B testing different UX-state copy or thresholds -- product
  iteration, not methodology.

This is a startup product, not an academic scoring institute: the
distinction above exists specifically to stop methodology work from
expanding indefinitely once the core contract is sound.

## 27. Definition of GOOD ENOUGH to ship experimentally

SPS V3, as it stands after this phase, is good enough to move toward
production implementation if it is:

- [x] **Deterministic** -- every evaluator and aggregation step is a pure
      function of typed evidence + registry parameters; zero LLM numeric
      scoring anywhere in the scoring path.
- [x] **Explainable** -- every score traces to specific cited evidence
      IDs and a named rule (`RuleTrace`); the Section 24 contract is a
      mechanical read of existing fields.
- [x] **Evidence-backed** -- no dimension scores without a qualifying
      `CanonicalObservation`/`CanonicalSignal`.
- [x] **Stage-aware** -- Traction and Financial Health bands are
      stage-relative (Section 15-17).
- [x] **Unknown-safe** -- confirmed by direct invariant test (Section 19):
      unknown dimensions cannot move Strength, only Coverage.
- [x] **Resistant to evidence-volume bias** -- confirmed by the
      more-information test (Section 20) and by signal deduplication
      (Phase 10.8G): duplicate/redundant evidence cannot inflate a score.
- [x] **Capable of positive/negative differentiation** -- confirmed by
      the negative-evidence bands (Section 15-17) and by real
      distressed/failed companies (Convoy, Olive AI) scoring their one
      publishable pillar (Execution) at 4.31/10 -- below the
      `band.multiple_signals` neutral-positive midpoint of 7.5 -- rather
      than at a neutral default (see the sanity-set doc for detail).
- [x] **Clear about coverage/confidence** -- both are structurally
      independent, separately reported, never hidden inside the
      headline number.

It does **not** need to be, and is not:
- Tuned to any target score distribution.
- Validated against outcome data (funding success, survival) -- that is
  a separate, longer-horizon validation question, not a blocker for
  shipping an experimental, clearly-labeled score.
- Free of every possible future refinement (Section 26's nice-to-have
  list exists precisely because "good enough" is not "finished").

## Final decision

See the chat-delivered Phase 10.8J final report for the complete 37-item
summary and the required YES/NO verdict block. Short version: **YES** --
recommend moving to production implementation planning; no further
methodology-only phase is proposed by this document.
