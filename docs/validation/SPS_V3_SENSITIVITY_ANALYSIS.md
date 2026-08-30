# SPS V3 Sensitivity Analysis

Phase 10.8F. Every number below is copied directly from actual
`app/calibration/sps_v3/tests/test_aggregation_and_tails.py` output
(Parts 33-34), re-run and confirmed reproducible before this document
was written. No production pillar weight was changed — Part 34's
weight-perturbation test restores `PILLAR_WEIGHTS` in a `finally` block
and this restoration was explicitly asserted, not merely assumed.

## Purpose

Not to choose final values — to identify **which** provisional
constants actually move outcomes enough to matter, so the eventual
calibration effort (Calibration Plan Part 27-28) is prioritized
correctly rather than spending equal effort on every parameter.

## Publishability gate: `gate.overall_coverage_floor_pct`

Baseline 35 (provisional), tested range 20-50, against Core Profile D
(ordinary/high-coverage):

| Floor value | Publishable | SPS |
|---|---|---|
| 20 | Yes | 56.7 |
| 35 (baseline) | Yes | 56.7 |
| 50 | **No** | — |

**Finding: this parameter is a hard binary switch, not a gradual dial**
— it either permits Profile D's actual 48% coverage or it doesn't; the
score itself never moves, only publishability does. This means
calibrating this single number is high-leverage (it decides whether an
entire company category can be shown an SPS at all) and should be
prioritized in Calibration Plan Part 28's synthetic-boundary-fixture
pass before any other publishability-adjacent parameter.

## Score-band midpoints: `band.single_signal` / `band.multiple_signals` / `band.comprehensive`

Tested against Core Profile A (exceptional/high-coverage), full
declared sensitivity range for each:

| Parameter | Range | Low-end SPS | Baseline SPS | High-end SPS | Spread |
|---|---|---|---|---|---|
| `band.single_signal` | 5.0-6.0 | 65.7 | 68.1 | 70.5 | **4.8** |
| `band.multiple_signals` | 7.0-8.0 | 66.7 | 68.1 | 69.5 | **2.8** |
| `band.comprehensive` | 9.0-10.0 | 67.5 | 68.1 | 68.7 | **1.2** |

**Finding: `band.single_signal` is the single most SPS-sensitive
parameter measured in this phase** — nearly 4x more impactful than
`band.comprehensive` across their respective declared ranges, on this
profile. This is because most of Profile A's 27 dimensions land in the
SINGLE_SIGNAL tier (a direct consequence of Finding 1 in the synthetic
validation report — the classifier's 4-signal bar for COMPREHENSIVE is
rarely cleared by realistic, non-duplicated evidence density), so this
one parameter's exact value disproportionately determines typical-case
SPS. **This elevates `band.single_signal` to the highest-priority
calibration target**, ahead of `band.comprehensive`, which intuitively
seems like it should matter more but empirically moves outcomes less
because it's reached less often.

## Pillar weight perturbation (Financial Health, ±50% relative)

Baseline 10%, tested at 5% and 20% (renormalizing the other five
pillars proportionally to preserve a 1.0 sum), against Core Profiles
A/D/E:

| FH weight | Profile A SPS | Profile D SPS | Profile E SPS |
|---|---|---|---|
| 5% (halved) | 68.3 | 56.8 | 45.0 |
| 10% (baseline) | 68.1 | 56.7 | 45.0 |
| 20% (doubled) | 67.8 | 56.5 | 45.0 |

**Finding: pillar-weight sensitivity is very low** — even doubling
Financial Health's weight moved every tested profile's SPS by at most
0.3 points. This is a genuinely reassuring result: it means the
methodology's overall behavior is **not fragile with respect to the
exact pillar weights**, which supports Rulebook Part 24's decision to
leave them unchanged rather than re-litigate them — there was no
evidence the weights matter much even before this test, and now there
is direct evidence they don't move outcomes much within a plausible
perturbation range. This test result is a reason for confidence, not
concern.

## Classification-error sensitivity

A one-tier classification miss (e.g. SINGLE_SIGNAL mis-classified as
MULTIPLE_SIGNALS) produces a fixed 2.0-point dimension-score delta
under baseline provisional bands (both adjacent gaps happen to be
identical: 7.5-5.5=2.0 and 9.5-7.5=2.0). The worst-case single-dimension
pillar-level impact — a 2-tier miss on the single highest-weighted
dimension in the entire methodology (0.35, shared by Founder-Market
Fit-shaped and Capital-Efficiency-shaped dimensions) — is **1.4 points**
at the pillar level. **Finding: no single plausible AI classification
mistake can swing a pillar score dramatically** — this is a positive
result for robustness against the exact kind of error V3's whole
architecture exists to make less consequential than V2.1's free-form
numeric judgment.

## Provenance-grade sensitivity

Strength was **completely unchanged** (5.5 in all three cases) across
PRIMARY_VERIFIED → HIGH_QUALITY_SECONDARY → SECONDARY_ESTIMATE for the
identical underlying fact; Confidence correctly degraded HIGH → HIGH →
LOW. **Finding: provenance grade cleanly affects only Confidence, never
Strength** — this specific firewall holds robustly, in contrast to
Finding 1's redundant-evidence vulnerability (which is about
observation *count*, not observation *grade*) — the two are different
mechanisms and only one of them is currently vulnerable.

## Priority ranking for future calibration effort

Based on measured sensitivity, highest to lowest priority:

1. **`gate.overall_coverage_floor_pct`** — binary publish/withhold
   switch, needs careful boundary-case calibration (Calibration Plan
   Part 28).
2. **`band.single_signal`** — highest per-point SPS sensitivity of any
   score-band parameter measured; also the tier most real evidence
   lands in given the current classifier design (compounding the
   priority).
3. **`band.multiple_signals`** — moderate sensitivity.
4. **`band.comprehensive`** — lowest measured sensitivity, largely
   because it's the least-frequently-reached tier under realistic
   (non-Finding-1-exploiting) evidence density.
5. **Pillar weights** — measured as low-sensitivity; not a calibration
   priority based on this evidence.
6. **Classification-error and provenance-grade robustness** — both
   measured as bounded/well-behaved; not calibration priorities, more
   a confirmation the architecture is sound on these two axes.

This ranking is itself provisional (measured against only 2-3 synthetic
profiles, not the eventual real blind cohort) and should be re-run once
Finding 1 (redundant-evidence vulnerability) is fixed, since fixing it
will change how often each classification tier is actually reached and
could reorder this priority list.
