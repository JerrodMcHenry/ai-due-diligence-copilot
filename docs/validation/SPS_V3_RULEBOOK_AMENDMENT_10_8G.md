# SPS V3 Rulebook Amendment — Phase 10.8G

Narrow methodology correction, scoped only to the defect and three
unresolved-methodology items Phase 10.8F identified. No production
code, V2.1, API, database, or frontend was touched. No real company was
used. No blind cohort was selected. No score band, dimension weight,
pillar weight, or overall coverage floor was calibrated.

## Defect

Phase 10.8F's redundant-evidence and fame-bias attacks found that
duplicating the identical substantive fact through repeated sources
inflated a dimension's score:

- 1x → 5.5, 2x → 7.5, 100x → 9.5 (same fact, `competitive_intensity`).
- 15 `SECONDARY_ESTIMATE`-grade duplicate sources (9.5, COMPREHENSIVE)
  beat 1 `HIGH_QUALITY_SECONDARY` source citing the identical fact (5.5,
  SINGLE_SIGNAL) — an inversion of what evidence quality should reward.

## Root cause

The Category B classification pattern (Rulebook Part 16) counted **raw
observation objects**, not **distinct underlying facts**. Part 20
already stated Coverage must deduplicate ("100 sources → 100x coverage"
was explicitly forbidden and, confirmed by re-test, never actually
happened); no equivalent rule existed for Strength's classification
step. This was a genuine gap in the Rulebook itself, not merely an
implementation shortcut — the four fully-worked dimension examples
(Founder-Market Fit, Strategic Execution, etc.) implicitly assumed
named, distinct facts would be counted, but the general pattern powering
all 27 dimensions never stated this as a requirement.

## Rulebook change

Added **Part 6A** to `docs/methodology/SPS_V3_RULEBOOK.md` (inserted
after Part 6, before Part 7 — no existing section renumbered or
rewritten):

1. **Substantive signal vs. source record** — a formal distinction
   between "what a source said" and "the underlying fact."
2. **Signal identity** — `(metric_type, entity, period)` for
   quantitative observations, `(type, subject, classification)` for
   qualitative ones; deliberately excludes the reported *value*, so
   agreeing observations collapse to one signal and disagreeing ones
   become a conflict, both keyed the same way.
3. **Strength deduplication rule** — classification signal-counting
   operates on unique resolved signals, never raw observation count;
   this is now stated as a first-class requirement of Part 16, inherited
   automatically by all 27 dimensions.
4. **Source independence and corroboration** — a four-value
   classification (`SAME_ORIGIN` / `DERIVATIVE` / `UNKNOWN_ORIGIN` /
   `INDEPENDENT`); only `INDEPENDENT`, distinct-origin observations may
   raise Confidence by one tier; any number of the other three
   contributes zero.
5. **Source lineage** — one optional `origin_id` field, deliberately
   minimal (not a citation graph), per Part 7's "keep V1 implementable"
   instruction.
6. **Provenance precedence** — a three-tier order for conflict
   resolution (`PRIMARY_VERIFIED` > {`PRIMARY_SELF_REPORTED`,
   `HIGH_QUALITY_SECONDARY`, `DERIVED`} > `SECONDARY_ESTIMATE` >
   `UNVERIFIED`); a strictly higher tier wins; **same-tier disagreement
   (including self-report vs. high-quality-secondary) is never
   auto-resolved**, exactly per this phase's explicit instruction.
7. **Conflict model** — `CONFLICT_DETECTED` / `CONFLICT_RESOLVED_BY_PRECEDENCE`;
   an unresolved conflict excludes the signal from scoring and Coverage
   entirely, never averaged, never resolved by list order.
8. **Recency/staleness architecture** — four evidence-type freshness
   classes (`STRUCTURAL_FACT`, `HISTORICAL_FACT`, `RECENT_PERFORMANCE`,
   `CURRENT_STATE`), each with one provisional (`CALIBRATION REQUIRED`)
   staleness threshold; stale `CURRENT_STATE`/`RECENT_PERFORMANCE`
   evidence is excluded from scoring but never deleted and never
   converted to negative evidence; `STRUCTURAL_FACT` never goes stale.

## Experimental implementation change

New files under `app/calibration/sps_v3/` (isolated, zero production
impact, confirmed below):

- `signals.py` — `_signal_key()`, `_values_agree()`,
  `_resolve_conflict_precedence()`, `build_canonical_signals()`,
  `_count_independent()`, the `CanonicalSignal` type.
- `freshness.py` — `FreshnessClass`, `Freshness`, `freshness_class_for()`,
  `evaluate_freshness()`.
- `registry.py` — 4 new provisional parameters
  (`freshness.<class>.stale_after_months`), all `CALIBRATION_REQUIRED`.
- `types.py` — added `origin_id` and `source_independence` fields to
  `EvidenceBase` (both optional/defaulted, fully backward compatible
  with every existing 10.8F fixture), plus `SourceIndependence` and
  `ConflictStatus` enums.
- `evaluators.py` — `_generic_b_classification`/`_build_b_result` now
  route every Category B dimension's evidence through
  `build_canonical_signals()` before counting; `confidence_from_canonical_signals()`
  implements the corroboration rule; `current_scale`, `growth_trajectory`,
  `retention_engagement`, and `capital_efficiency` (the bespoke
  quantitative evaluators) were rewritten to resolve conflicts via
  precedence instead of `max()`/list-index selection; `apply_staleness_filter()`
  applies freshness centrally in `evaluate_all_dimensions()`, which now
  accepts an optional, explicit `reference_date` (never wall-clock —
  `None` preserves exact 10.8F behavior for any caller that doesn't pass
  one).
- **Two genuine implementation bugs found and fixed** (not new to this
  phase's defect, but caught while touching this code): none this
  round — the two bugs fixed were in 10.8F itself; this phase's changes
  were reviewed for the same order-dependence pattern and all `max()`/
  `[-1]` selections in the touched functions were replaced with
  canonical-signal-based, content-derived resolution.

## Before / after behavior

| Test | Before (10.8F) | After (10.8G) |
|---|---|---|
| 1x vs. 100x identical fact | 5.5 → 9.5 (defect) | 5.5 → 5.5 (fixed) |
| 15 low-grade vs. 1 high-grade source | 9.5 vs. 5.5 (inverted) | 5.5 vs. 5.5 (identical Strength; Confidence correctly still differs by grade, not volume) |
| Coverage under 100x duplication | Unaffected (was already correct) | Unaffected (confirmed still correct) |
| Conflicting same-date, same-tier observations | Silently resolved via `max()`'s insertion-order tie-break | `UNAVAILABLE_CONFLICTING_EVIDENCE`, confirmed identical across all 6 permutations of a 3-way conflict and both orderings of a 2-way tie |
| Self-report vs. high-quality-secondary disagreement | Undefined/untested | Explicit: same tier, `CONFLICT_DETECTED`, never auto-resolved |
| `PRIMARY_VERIFIED` vs. contradictory `SECONDARY_ESTIMATE` | Undefined/untested | Explicit: `PRIMARY_VERIFIED` wins by precedence |
| Stale 7-year-old CURRENT_STATE revenue figure | Always used, no staleness concept existed | Excluded from scoring (with an explicit `reference_date`); falls to `UNAVAILABLE_NO_EVIDENCE`, never becomes negative |
| Founder history decades old | N/A (no staleness concept) | Confirmed never staleness-filtered (`STRUCTURAL_FACT`) |

**Full-cohort regression:** of the 10 core profiles, only Profile A's
SPS changed (68.1 → 66.8) — the one profile whose fixture happened to
contain near-duplicate evidence (repeated competitor citations). Every
other profile (B, C, D, E, F, G, H, I, J) is byte-identical to its
10.8F pre-amendment result, confirming the fix is narrowly targeted and
did not perturb unrelated scoring behavior.

## Market Size finding (Part 13) — CALIBRATION REQUIRED, not a bug

10.8F found Market Size magnitude-insensitive ($100M and $100T score
identically). Investigated only as far as this phase's scope allows:
Market Size was **always designed** (Rulebook Part 9) as a
signal-count/taxonomy-based dimension (`segment_breadth`,
`cited_estimate_present`, `buyer_budget_signal`), unlike Current Scale,
which was deliberately given magnitude-aware stage-relative dollar
bands. The magnitude-insensitivity is therefore **not** a deviation
from the Rulebook's own design intent — it is a genuine, undecided
design question (should Market Size gain a magnitude-aware taxonomy
field, analogous to Current Scale's bands?) that was never resolved
either way. **Classification: CALIBRATION REQUIRED** (a new taxonomy
field would need its own thresholds) **with a secondary open design
question** (whether such a field belongs in Market Size at all) — not
an IMPLEMENTATION BUG, not a RULEBOOK TRANSCRIPTION ISSUE, and not a
STRUCTURAL METHODOLOGY DEFECT, since the current behavior matches what
was actually specified. Not redesigned or calibrated in this phase, per
explicit instruction.

## Team-ablation finding (Part 14) — expected weighted renormalization, not a concern

10.8F flagged that ablating Team moved SPS by more than a crude,
self-invented 3.0-point sanity bound. Investigated fully this phase:
the exact arithmetic is now traced. In the post-amendment Profile A,
pillar strengths are Market 6.20, **Team 7.62**, Product 6.00, Execution
6.50, Traction 7.30, Financial Health 6.50; overall weighted-strength
average is 6.684 (→ SPS 66.8). Team's own strength (7.62) is
**above** that average — removing any above-average pillar and
renormalizing over the rest necessarily pulls the recomputed average
**down**, by an amount that is a direct, unavoidable function of
`(pillar_strength − remaining_weighted_average) × weight/(1−weight)`.
Recomputing by hand: ablating Team yields a renormalized SPS of exactly
64.5, a 2.3-point move — fully and precisely explained by this formula,
with no unexplained residual. **This is EXPECTED weighted
renormalization, not a real aggregation concern.** The original
3.0-point "sanity bound" was an arbitrary heuristic invented for one
test, not a methodology requirement; it is retired as a check (the
underlying math is now proven correct by direct computation instead).
No aggregation change is required or recommended.

## Remaining unresolved calibration questions

Carried forward, updated, in `docs/validation/SPS_V3_CALIBRATION_OPEN_QUESTIONS.md`.
Headline items still open after this amendment:

- The 4 new freshness thresholds (`stale_after_months` per class) are
  new `CALIBRATION_REQUIRED` parameters — architecture is decided,
  exact months are not.
- Whether the "borderline" zone (75% of the stale threshold) is the
  right ratio, or should itself be a separate calibrated parameter.
- Whether Market Size should gain a magnitude-aware taxonomy field (a
  genuine open design question, not merely a numeric calibration one).
- Every item already carried forward from 10.8F that this phase was
  explicitly told not to touch (score bands, dimension/pillar weights,
  overall coverage floor, stage numeric thresholds) remains exactly as
  it was.
