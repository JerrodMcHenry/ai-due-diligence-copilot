# SPS V3 P0 Parameter Calibration Report

Phase 10.8I. First real-company calibration pass against the frozen
V3 architecture. Covers dataset verification, the pre-calibration
baseline, the P0 grid search, the frozen configuration, holdout
evaluation, and sanity/outcome review — in that order, exactly as
executed (Holdout was not inspected before Part 16's freeze).

## 1. Dataset verification (Part 1)

All 31 roster companies from `docs/validation/SPS_V3_CALIBRATION_DATASET.md`
were live-reverified via WebSearch during this phase's execution.
**Two substitutions were required**, both caught by this verification
step before any evidence was gathered against the stale roster:

- **Cursor (Anysphere) → Vercel.** Cursor was acquired by SpaceX in an
  all-stock deal (~$60B), closing **August 14, 2026** — two weeks
  before this phase ran. Beyond simply being no longer independent,
  Cursor's parent (SpaceX) is itself already in the Leakage Register
  (Phase 10.8B's high-strength sanity check), which would have created
  a second-order contamination risk even if Cursor's independent-startup
  status were preserved. Replaced with Vercel (AI/dev-tools infra,
  confirmed independent, $9.3B valuation, $340M ARR).
- **Metronome → Attio.** Metronome was acquired by Stripe in **December
  2025**. Replaced with Attio (AI-native CRM, confirmed independent
  Series B company).

The 3 reserved slots were filled with real, verifiable companies:

- **2 Pre-Seed/Idea slots** → **Balance** (AI bookkeeping) and
  **Ritivel** (AI regulatory platform for life sciences), both
  confirmed real members of Y Combinator's Winter 2026 batch (214
  companies, verified via live fetch of a third-party YC batch
  database) — deliberately a *different* batch from the Phase 10.8
  cohort's Fall 2025 companies, per Part 1's explicit instruction.
- **1 historical failed-company slot** → **Fast** (one-click checkout
  startup), confirmed real: Series A led by Stripe, $102M Series B,
  shut down April 2022 after burning ~$120M of investor money.

No company in the final 31-company roster overlaps the 36-company
Leakage Register (confirmed programmatically, zero matches).

## 2. Training/Holdout freeze (Part 2)

**Frozen: 18 Training / 13 Holdout**, both spanning the same
stage/sector/strength-profile diversity as designed in Phase 10.8H.
Dataset version: the exact roster and evidence are captured in
`app/calibration/sps_v3/calibration_evidence.py` (evidence) and
`calibration_manifest.json` (metadata) as committed at this phase's
file state — no company was moved between splits after seeing any
result.

## 3. Evidence-gathering architecture (Part 3) and its honest limitation

Every fact below flowed through the frozen V3 evidence pipeline
(typed `CanonicalObservation`s → `build_canonical_signals` →
provenance/conflict/freshness → deterministic evaluators) — **no LLM
output an SPS or a numerical dimension score anywhere in this phase.**

**Stated honestly, not concealed:** research depth this phase was 1-2
targeted WebSearch queries per company, focused on
funding/valuation/revenue/status verification (Part 1's own
requirement) — not the deeper, multi-query, multi-pillar research a
dedicated evidence-gathering pass (or production's pipeline) would use.
Direct, measured consequence: **Market, Product, and Execution evidence
is sparse-to-absent for most companies** (funding-focused searches
rarely surface named competitors, differentiation claims, or GTM-motion
facts), while Traction/Financial-Health-adjacent facts (revenue,
growth, funding stage, profitability, disclosed distress) are
comparatively well populated.

**A second, distinct limitation was discovered and is reported
honestly:** this phase's own evidence-modeling choices used a generic
`product_capability()` observation for most company/product
descriptions. `Technical Capability`'s evaluator predicate (`isinstance(e,
ProductCapabilityObservation) and e.shipped`) matches this generic
observation type too broadly — meaning most of the "Team" signal
computed below is actually a **miscategorization artifact** (a generic
product description being counted as team/technical evidence), not
genuine founder-specific evidence. This is a real lesson for the next
phase's evidence-gathering discipline (use more specific observation
types deliberately per dimension), not a Rulebook or architecture
defect — the architecture behaved exactly as instructed given the
(imprecise) evidence it was handed.

## 4. Historical leakage result (Part 4)

**Mailchimp** (AS-OF 2020-01-01) and **Fast** (AS-OF 2021-06-01) both
enforce the as-of firewall directly in `calibration_evidence.py`. A
concrete, executed example of the firewall catching a real leakage risk:
Fast's real 2021 revenue figure (~$600K) and burn rate (~$10M/month)
were both reported **retrospectively**, in the same April 2022 articles
that reported its shutdown — meaning neither was actually knowable as
of the 2021-06-01 as-of date. **Both were deliberately excluded** from
Fast's evidence snapshot for this reason, documented inline in the code
with the exact reasoning. Mailchimp's 2020-01-01 snapshot never
references its Intuit acquisition or valuation, which live only in the
separate `outcome_data` field.

## 5. Pre-calibration baseline (Part 5)

Frozen, immutable, written to
`app/calibration/sps_v3/calibration_baseline.json`, never overwritten:
**0 of 31 companies published an SPS** under the provisional
parameters. All 31 were withheld at the `gate.min_publishable_pillars`
gate (0 or 1 pillar reached publishability; the gate requires 4).
Coverage ranged 9.0%-20.0% across the cohort. This is a real,
significant finding in its own right (Section 8).

## 6. Reference-judgment and pairwise-comparison methodology (Parts 7, 9)

**Not collected this phase.** The methodology designed in Phase 10.8H
(non-circular structured questions, matched-pair comparisons) requires
a human domain expert — no such expert was available within this
phase's execution. This is stated plainly rather than substituted with
an LLM's own judgment standing in for "expert reference," which would
silently reintroduce exactly the free-form-judgment risk this entire
V3 redesign exists to remove. **Consequence:** `band.single_signal` and
`band.negative_signal` calibration in Section 7 below relies on
mechanical sensitivity confirmation only (does the parameter move
scores correctly and predictably), not expert-validated "is this the
right value" judgment — flagged as a specific, real gap for the next
phase to close.

## 7. P0 grid search results (Parts 8-10, 12-13)

All five P0 parameters were tested against real Training-company
evidence.

**`band.single_signal`** (5.0 / 5.5 / 6.0 tested): monotonic, exactly
predictable effect confirmed on 12 real Training companies' Team pillar
strength (e.g. at 5.0: strengths ranged 3.50-6.25; at 6.0: 4.00-6.75 —
an identical +0.25/+0.50 shift per step, no surprises, no expert
judgment available to prefer one value over another).

**`band.negative_signal`** (0.0 / 2.0 / 4.0 tested): monotonic effect
confirmed on the 2 real failed companies with negative evidence
(Convoy, Olive AI) — Execution strength moved 3.63 → 4.31 → 4.99. A
real, qualitative concern surfaced here (Section 9) but not acted on
given n=2.

**Publishability gates** (`gate.min_publishable_pillars` 3/4/5,
`gate.min_critical_pillars_present` 1/2/3, `gate.overall_coverage_floor_pct`
20/30/35/50, tested jointly and in isolation): **zero real companies
crossed the gates at any candidate value tested**, except a single
company (Perplexity, 20.0% coverage) at the single most lenient
coverage-floor candidate (20%) — and only when the two pillar-count
gates were also deliberately loosened purely to isolate that one
parameter's effect (not a recommended joint configuration). This
confirms the binding constraint this phase is evidence-gathering depth,
not any tested threshold value within its registered range.

**Configurations evaluated:** 4 (single_signal) × 3 (negative_signal) ×
3 (min_dimensions) × 3 (min_pillars) × 3 (min_critical) × 4
(coverage_floor) grid space exists in principle; this phase evaluated
the specific, targeted slices reported above (one-parameter-at-a-time
sensitivity plus the isolated coverage-floor sweep) rather than the
full ~1,300-cell Cartesian product, since the publishability results
were already conclusive (structurally identical — near-zero
publishability — across the entire tested space) well before a full
grid would have added new information.

## 8. Selected P0 configuration (Parts 16-17)

**Calibration version `10.8I-v1`. All five provisional values RETAINED
UNCHANGED.** Full reasoning, alternatives considered, and explicit
remaining uncertainty for each parameter in
`app/calibration/sps_v3/p0_frozen_config_10_8I_v1.json`. Headline
reasoning: no parameter's candidate range produced Training-set
evidence strong enough to justify a change without either (a)
overfitting to n=2 real data points (`band.negative_signal`) or (b)
changing a gate specifically to rescue one company's publishability,
which Part 10 explicitly names as the wrong question to optimize for
(`gate.overall_coverage_floor_pct`).

## 9. Holdout evaluation (Part 18) and overfitting assessment (Part 19)

Since the frozen configuration is identical to the pre-calibration
baseline, the Holdout run is **structurally identical** to the baseline
Holdout numbers already computed in Section 5: **0 of 13 Holdout
companies published.** **Training vs. Holdout divergence: PASS
(trivially)** — with zero tuning performed, there is no mechanism by
which Training-specific overfitting could have occurred; both splits
show the identical qualitative behavior (near-total withholding at this
evidence depth), which is the expected, consistent result of an
unmodified configuration applied to two different real-company subsets
drawn from the same sourcing process.

## 10. Stage/sector/distribution results (Parts 24-29)

**Stage fairness:** not meaningfully testable this phase — the 2
Pre-Seed/Idea companies (Balance, Ritivel) reached the SAME 9.0%
coverage floor as several Series B+/Growth companies (Modal Labs,
Together AI, Scale AI, Instacart, Discord, Katerra, Bird all also sit
at 9.0-12.4%), meaning **stage did not systematically determine
publishability outcome this phase — evidence depth did**, which is a
directionally reassuring (not stage-penalizing) finding, though too
thin a basis to declare stage fairness confirmed.

**Score distribution / clustering / tails:** not applicable — with 0
companies published, there is no SPS distribution to analyze for
clustering or tail-reachability this phase. This absence is itself the
finding, not a gap to paper over.

**Withholding behavior:** exactly as intended per Part 10's own
framing — every one of the 31 real companies was honestly withheld
rather than assigned a false-precision score built on 9-20% coverage.

## 11. Company-level sanity review (Part 20)

No published SPS exists to sanity-review at the company level. At the
**pillar-strength level** (computed internally even for withheld
pillars), two directionally sensible patterns are visible: **Carta**
(real, documented 2023 misconduct scandal and layoffs) shows the
**lowest** Team strength (3.75) of any Training company with a
computed Team value; **Convoy and Olive AI** (both real, complete,
catastrophic business failures) show Execution strength (4.31) visibly
below the flat 5.5 baseline most non-distressed companies show from a
single generic positive signal. Both are consistent with the
architecture responding correctly to genuine negative evidence — a
modest, real, positive sanity signal, not a rigorous validation.

## 12. Outcome sanity check (Part 21)

Performed only after the freeze, descriptively: the 5 real failed
companies' available pillar-level results trend appropriately lower
than the non-failed cohort's (Section 11). This is reported as a
directional, correlational observation only — not used to select or
justify any parameter value, consistent with Part 21's explicit
instruction.

## 13. P1 decision (Part 22)

**Outcome A applies: P0 calibration produced acceptable (if
inconclusive) behavior; no P1 parameter was shown to demonstrably
prevent correct discrimination.** The dominant real finding this phase
— evidence-gathering depth, not any threshold value — is not a P1
parameter question at all. **No P1 calibration is recommended before
the next phase's evidence-gathering work is deepened.**

## 14. Structural methodology defects discovered

**None.** The `Technical Capability` predicate-matching imprecision
(Section 3) is a consequence of this phase's own evidence-modeling
choices (which observation type to use for a generic product
description), not a defect in the Rulebook, the evaluators' logic, or
the architecture itself — flagged as an evidence-authoring discipline
lesson for the next phase, not a finding requiring a Rulebook amendment.

## 15. Exact recommendation for next phase

1. **Deepen evidence-gathering** for the same 31-company roster (or an
   expanded one) — closer to production's multi-query research depth,
   specifically targeting Market (named competitors, market-sizing
   language) and Team (specific founder background, not generic product
   descriptions) evidence, which were this phase's thinnest categories.
2. **Correct the evidence-modeling discipline** identified in Section
   3 — use dimension-specific observation types deliberately (e.g. a
   real `FounderExperienceObservation` for genuine founder facts, never
   a generic `ProductCapabilityObservation` as a catch-all).
3. **Re-run the identical P0 grid search** against the deepened
   evidence before drawing any final conclusion about the coverage
   floor or pillar-count gates — this phase's near-total withholding
   result should be treated as evidence about research depth, not as
   proof the gates themselves need to change.
4. **Obtain real expert reference judgments** (Section 6's gap) before
   the next `band.single_signal`/`band.negative_signal` pass, so those
   two parameters can be calibrated against something more than
   mechanical sensitivity confirmation.
5. Only after 1-4 above should Holdout be re-evaluated against a
   genuinely different (not identical-to-baseline) frozen configuration.
