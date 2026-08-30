# SPS V3 Calibration Dataset

Phase 10.8H. **CALIBRATION — NOT VALIDATION.** Every company named in
this document is explicitly designated to *influence* V3 parameter
selection in a future phase. None of them may ever be used as, or
compared against, a blind-validation result. This document is a design
and roster-assembly artifact: it selects and characterizes the
calibration cohort and defines the calibration methodology; it does
**not** run any company through any pipeline, does **not** gather or
record actual evidence, and does **not** set or change any parameter
value. Evidence-gathering and parameter tuning are both explicitly
deferred to a later phase (Part 17's own instruction).

---

## 1. Architecture Freeze Verification

`docs/methodology/SPS_V3_RULEBOOK.md` (as amended by Phase 10.8G's Part
6A) is treated as fixed for this phase. Nothing in this document
proposes a change to the evidence ontology, substantive-signal
architecture, provenance architecture, conflict architecture, the
Strength/Coverage/Confidence separation, pillar structure, aggregation
architecture, or unknown/negative-evidence semantics. Confirmed via
`git diff` at the end of this phase (Section 24 below) — zero changes
to any file under `docs/methodology/` or the non-registry parts of
`app/calibration/sps_v3/`.

---

## 2. Uncalibrated Parameter Inventory

All 27 parameters currently registered in
`app/calibration/sps_v3/registry.py`, read directly from the live
registry (not retyped from memory):

| Parameter ID | Provisional value | Candidate range | Affects | Semantic meaning | Sensitivity observed (10.8F/G) | Calibration data required | Risk if too high | Risk if too low | Priority |
|---|---|---|---|---|---|---|---|---|---|
| `band.single_signal` | 5.5 | 5.0-6.0 | All 21 Category-B dimensions | Score for a "credible but ordinary" (1-signal) classification | **Highest measured** — 4.8-pt SPS spread across range on Profile A | Real single-signal-evidenced companies at each stage, paired with expert "is this genuinely ordinary" judgment | Compresses discrimination upward, everything looks decent | Compresses downward, punishes companies with only 1 real fact | **P0** |
| `band.multiple_signals` | 7.5 | 7.0-8.0 | Same | Score for a 2-3-signal classification | Moderate — 3.3-pt spread | Same, at the 2-3-signal tier | Same direction, smaller magnitude | Same direction, smaller magnitude | **P1** |
| `band.comprehensive` | 9.5 | 9.0-10.0 | Same | Score for a 4+-signal classification | Lowest measured — 0.5-1.2-pt spread (rarely reached) | Genuinely exceptional, densely-evidenced real companies | Makes 90+ nearly unreachable | Makes "exceptional" too easy | **P1** |
| `band.negative_signal` | 2.0 | 0.0-4.0 | Same | Score when negative evidence is present | **Directly controls 0-19 reachability** (proven: 2.0→floor 20.0, 1.0→floor 10.0) | Real companies with documented, specific negative signals (declines, departures, shutdowns) | Understates real weakness | 0-2 band becomes indistinguishable from "unavailable" territory | **P0** |
| `gate.min_dimensions_per_pillar` | 2 | 1-3 | Pillar publishability | Minimum scorable dimensions for a pillar to publish | Not yet measured | Real pillars with exactly 1, 2, 3 scorable dimensions | A single strong/weak dimension can represent a whole pillar | Pillars with genuinely adequate (but not abundant) evidence get needlessly withheld | **P1** |
| `gate.min_publishable_pillars` | 4 | 3-5 | SPS publishability | Minimum publishable pillars for SPS to exist at all | Structural (binary) | Real companies at the margin of 3/4/5 publishable pillars, across stages | SPS computed from too few pillars, misleadingly definitive | SPS withheld unnecessarily, especially for early-stage companies | **P0** |
| `gate.min_critical_pillars_present` | 2 | 1-3 | SPS publishability | How many of {Market, Team, Product} must publish | Structural | Real companies where exactly 1 vs. 2 vs. 3 of these three publish | Weak protection against a single-critical-pillar SPS | Over-withholds for companies with genuinely thin Market/Team public evidence (privacy-conscious founders) | **P0** |
| `gate.overall_coverage_floor_pct` | 35 | 20-50 | SPS publishability | Minimum overall weighted coverage to publish SPS | **Proven binary switch** (Part 33: 20/35 identical, 50 blocks entirely) | The full calibration/holdout cohort's actual coverage distribution | Withholds SPS for legitimately-assessable companies | Publishes SPS built on too little real evidence (the original "94/12%" failure mode) | **P0** |
| `gate.min_pillar_coverage_pct` | 40 | 25-55 | Pillar publishability | Minimum pillar-level coverage to publish that pillar | Not yet measured | Same cohort, per-pillar coverage distribution | Withholds individual pillars unnecessarily | Publishes thin pillars | **P1** |
| `traction.current_scale.seed.arr_ordinary_ceiling` | $100K | $50K-$250K | Current Scale @ Seed | ARR below this = ordinary-low | Not yet measured | Real Seed-stage ARR distribution (needs expert "is this genuinely strong for Seed" judgment) | Seed companies look artificially strong | Seed companies look artificially weak | **P1** |
| `traction.current_scale.seed.arr_strong_ceiling` | $1M | $500K-$2M | Current Scale @ Seed | ARR below this = strong; above = exceptional-for-stage | Not yet measured | Same | Same | Same | **P1** |
| `traction.current_scale.series_a.arr_ordinary_ceiling` | $1M | $500K-$2M | Current Scale @ Series A | Same pattern | Not yet measured | Series A ARR distribution | Same | Same | **P1** |
| `traction.current_scale.series_a.arr_strong_ceiling` | $5M | $3M-$10M | Current Scale @ Series A | Same | Not yet measured | Same | Same | Same | **P1** |
| `traction.current_scale.growth.arr_ordinary_ceiling` | $10M | $5M-$20M | Current Scale @ Growth | Same | Not yet measured | Growth-stage ARR distribution | Same | Same | **P1** |
| `traction.current_scale.growth.arr_strong_ceiling` | $50M | $25M-$100M | Current Scale @ Growth | Same | Not yet measured | Same | Same | Same | **P1** |
| `traction.growth_trajectory.strong_yoy_pct` | 100% | 50%-200% | Growth Trajectory | YoY growth for STRONG | Not yet measured | Real two-point YoY growth distribution, by stage | Punishes genuinely good growth as merely ordinary | Rewards mediocre growth as strong | **P1** |
| `traction.growth_trajectory.exceptional_yoy_pct` | 300% | 150%-500% | Growth Trajectory | YoY growth for EXCEPTIONAL | Not yet measured | Same | Makes exceptional growth unreachable | Cheapens "exceptional" | **P1** |
| `traction.growth_trajectory.decline_negative_threshold_pct` | 0% | fixed | Growth Trajectory | Any negative YoY triggers negative-evidence band | Conceptually fixed, not really a tunable range | N/A — this is a definitional threshold (decline = decline), not calibration-sensitive in the usual sense | N/A | N/A | **P2** |
| `finhealth.capital_efficiency.strong_burn_to_revenue_ratio` | 1.0 | 0.5-1.5 | Capital Efficiency | Burn/revenue ratio for STRONG | Not yet measured | Real disclosed burn/revenue pairs (founder-provided or rare public disclosures) | Punishes reasonable burn as ordinary | Rewards poor capital efficiency as strong | **P1** |
| `finhealth.capital_efficiency.exceptional_burn_to_revenue_ratio` | 0.3 | 0.1-0.6 | Capital Efficiency | Same, for EXCEPTIONAL | Not yet measured | Same | Same | Same | **P1** |
| `finhealth.capital_efficiency.severe_constraint_months_runway` | 3 | 1-6 | Capital Efficiency | Runway below this = negative evidence | Not yet measured | Real disclosed runway figures, ideally including some genuinely distressed companies | Fails to flag real near-term risk | Over-flags normal early-stage runway as distress | **P1** |
| `freshness.structural_fact.stale_after_months` | 600 | 240-1200 | All STRUCTURAL_FACT observations | When founder/funding history "expires" | Not yet measured; conceptually near-irrelevant at any value in range | Minimal — this class is designed to almost never trigger | Nearly none (founder history genuinely doesn't go stale) | Nearly none | **P2** |
| `freshness.historical_fact.stale_after_months` | 36 | 18-60 | Market/competitive/product-capability observations | When market-level facts "expire" | Not yet measured | Real market-size/competitive-landscape observations at varying ages | Discards still-useful market context | Uses outdated market framing as current | **P2** |
| `freshness.recent_performance.stale_after_months` | 18 | 9-24 | Customer count/retention/contracts | When performance facts "expire" | Not yet measured | Real dated customer/retention observations | Discards still-relevant recent performance | Uses outdated performance as current | **P2** |
| `freshness.current_state.stale_after_months` | 12 | 6-18 | Revenue/cash/burn/runway | When financial-state facts "expire" | Not yet measured | Real dated financial disclosures | Discards recent-enough financial state | Uses stale financials as if current | **P2** |
| `band.no_signal` | 0 | fixed | N/A | Placeholder, never scores numerically | N/A | N/A | N/A | N/A | not applicable (not a real lever) |
| `confidence.min_grade_for_high` | 0 | fixed | N/A | Placeholder/documentation marker, unused numerically | N/A | N/A | N/A | N/A | not applicable (not a real lever) |

### Priority summary

- **P0 (5 parameters):** `band.single_signal`, `band.negative_signal`,
  `gate.min_publishable_pillars`, `gate.min_critical_pillars_present`,
  `gate.overall_coverage_floor_pct` — these materially control whether
  SPS exists at all and where most real companies will land within it.
- **P1 (17 parameters):** the remaining score bands, pillar-level gates,
  and every Traction/Financial-Health stage-relative threshold — real,
  measurable effects on individual dimensions/stages, but none proven
  (yet) to swing overall SPS as dramatically as the P0 set.
- **P2 (4 parameters + 2 non-levers):** the 4 freshness thresholds
  (real but, by design, meant to rarely bind) and 2 placeholder
  parameters that are not real calibration targets at all.

---

## 3. Calibration Objectives

Explicitly, calibration succeeds when the following are true — **none
of which is "make a specific company score a specific number":**

1. **Meaningful discrimination**: two real companies an informed reader
   would confidently rank differently produce SPS values that are also
   confidently different, not within noise of each other.
2. **Stage fairness**: an exceptional Seed company can outscore a
   mediocre Series B+ company; a weak Growth-stage company does not
   score well merely by virtue of scale.
3. **No evidence-abundance bias**: two companies with equivalent
   underlying substance but very different amounts of public coverage
   should not diverge in Strength (Coverage may differ; Strength should
   not) — directly testable using the Training/Holdout cohort's
   deliberate inclusion of both evidence-rich and sparse-evidence real
   companies (Section 4).
4. **No famous-company bias**: a company's public profile/brand
   recognition should not itself move any threshold decision — checked
   by including both well-known and lesser-known companies in every
   strength tier, and by never justifying a threshold choice by
   reference to what a specific well-known company should score.
5. **No artificial middle clustering**: the eventual calibrated
   thresholds should not recreate V2.1's central finding (Phase 10.8's
   63-76 compression) — checked via the same distribution diagnostics
   Phase 10.8 already established (range, bucket counts, per-pillar
   stdev).
6. **Usable upper and lower tails**: given genuinely extreme real
   evidence, both tails should be reachable — already proven possible
   architecturally by 10.8F/G's synthetic saturation tests; calibration
   determines whether real evidence realistically reaches them, not
   whether the mechanism can.
7. **Reasonable score stability**: small, immaterial evidence
   differences between very similar real companies should not produce
   large score swings — checked via the boundary-case design (Section
   10).
8. **Reasonable sensitivity to genuinely new evidence**: adding a real,
   substantive new fact to a company's evidence set should visibly move
   the relevant dimension — the inverse of clustering.
9. **Resistance to single-classification errors**: already
   architecturally bounded (10.8G's classification-error sensitivity
   test: max 1.4-point pillar impact) — calibration should not choose
   band values so far apart that this bound grows uncomfortably large.
10. **Appropriate withholding**: companies with genuinely thin evidence
    should be withheld, not scored mediocre — checked directly via the
    sparse-evidence companies deliberately included in the cohort.
11. **Coherent threshold transitions**: a threshold should separate
    materially different real company states, not create an arbitrary
    cliff between two companies that are substantively similar —
    checked via the boundary-case design (Section 10).

**Explicit non-objective, restated because it is the single easiest
principle to violate under real-company pressure:** SPS is not, and
must never be calibrated as, a probability of startup success, survival,
or fundraising outcome. Outcome data (Section 11) informs a separate,
cautious, correlational sanity check — never a target function.

---

## 4. Calibration Cohort Design

Every company below is **newly selected for this phase** — none
overlaps with the 36-company Leakage Register
(`SPS_V3_CALIBRATION_LEAKAGE_REGISTER.md`), confirmed by direct
cross-check. **Facts below (stage, funding history, operating status)
reflect general knowledge as of this document's authoring and are
explicitly flagged for re-verification via live research immediately
before evidence-gathering begins in the next phase** — this document
selects and characterizes candidates, it does not certify their current
status.

### Full roster (31 companies)

| # | Company | Stage (hypothesis) | Sector | Strength-profile hypothesis | Split |
|---|---|---|---|---|---|
| 1 | *(TBD — current YC or equivalent accelerator batch, distinct from F25)* | Pre-Seed | TBD | Exceptional-for-stage candidate | Training |
| 2 | *(TBD — same sourcing, second candidate)* | Idea/Pre-Seed | TBD | Sparse-evidence candidate | Holdout |
| 3 | Cursor (Anysphere) | Series A/B | AI / dev tools | Very strong, evidence-rich | Training |
| 4 | Modal Labs | Seed/Series A | AI infra / dev tools | Ordinary-to-strong, sparser public evidence | Training |
| 5 | Middesk | Series A/B | Fintech infra | Ordinary, B2B-sparse evidence | Holdout |
| 6 | Speak | Series B | AI / consumer | Strong, evidence-rich | Training |
| 7 | Metronome | Series B/C | B2B SaaS | Strong, ordinary-team/strong-traction candidate | Training |
| 8 | Clay | Series B | B2B SaaS | Strong, high-growth candidate | Holdout |
| 9 | Harvey AI | Series B/C | AI / legal vertical | Elite-team/strong-evidence candidate | Training |
| 10 | Together AI | Series B | AI infra | Strong, capital-efficient candidate to verify | Training |
| 11 | Whatnot | Series D/E | Marketplace / consumer | High-growth, evidence-rich | Holdout |
| 12 | Perplexity AI | Series C/D | AI / consumer | Very strong, high-funding candidate (unit-economics scrutiny case) | Training |
| 13 | Glean | Series D | AI / enterprise | Strong, evidence-rich | Training |
| 14 | Mercury | Series B/C | Fintech | Strong, capital-efficient candidate to verify | Holdout |
| 15 | Webflow | Series C | B2B SaaS | Strong, ordinary-growth candidate | Training |
| 16 | Scale AI | Series F+ | AI | Very strong, evidence-rich, high-funding | Holdout |
| 17 | Hugging Face | Series D | AI infra / dev tools | Strong, community-evidence-rich candidate | Training |
| 18 | Flexport | Series E/Growth | Logistics | **Distressed/mixed** — real documented 2022-23 leadership/layoff struggles | Training |
| 19 | Gusto | Growth | B2B SaaS (HR/payroll) | Ordinary-to-strong, mature | Holdout |
| 20 | Airwallex | Growth | Fintech | Strong, mature | Training |
| 21 | Carta | Growth | B2B SaaS | **Mixed/ordinary** — real documented 2023 struggles | Training |
| 22 | Instacart | Growth (public) | Marketplace / consumer | Ordinary/mature, profitable-slower-growth candidate | Holdout |
| 23 | ZipRecruiter | Growth (public) | B2B SaaS (HR tech) | Profitable, slower-growth candidate | Training |
| 24 | Discord | Growth | Consumer | Strong, high-evidence, monetization-mixed candidate | Holdout |
| 25 | Convoy | Growth (defunct) | Logistics | **Failed/shutdown** (Oct 2023) | Training |
| 26 | Olive AI | Growth (defunct) | Healthcare / AI | **Failed/wound-down** (2023) | Training |
| 27 | Katerra | Growth (defunct) | Construction tech / hardware | **Failed/bankrupt** (2021) | Holdout |
| 28 | Quibi | Growth (defunct) | Media / consumer | **Failed/shutdown** (2020) | Training |
| 29 | Bird | Growth (defunct) | Micromobility / hardware | **Failed/bankrupt** (Dec 2023) | Holdout |
| 30 | Mailchimp | Growth, **historical AS-OF 2020-01-01** | B2B SaaS | Capital-efficient/profitable, bootstrapped — historical-snapshot methodology test case (Section 9) | Training |
| 31 | *(reserved slot — a second historical AS-OF case, sector TBD, to balance the historical-snapshot sub-cohort)* | TBD | TBD | TBD | Holdout |

**Split counts: Training = 19, Holdout = 12** (including the 2 reserved
pre-seed/TBD slots and the 1 reserved historical-case slot, all
explicitly unresolved pending live sourcing at execution time).

---

## 5. Stage Distribution

| Stage | Training | Holdout | Total |
|---|---|---|---|
| Idea/Pre-Seed | 1 (TBD) | 1 (TBD) | 2 |
| Seed | 1 | 0 | 1 |
| Series A | 2 | 1 | 3 |
| Series B+ | 6 | 5 | 11 |
| Growth | 8 | 6 | 14 |

**Documented limitation, stated honestly rather than papered over**:
Seed-stage representation is thin (1 company) relative to Series B+/
Growth (25 combined). This mirrors a real, structural sourcing
difficulty already documented in Phase 10.8's own cohort-selection
work: genuinely verifiable, real, well-documented Seed-stage companies
are much harder to identify with confidence from general knowledge than
later-stage ones, and true Pre-Seed/Idea-stage companies are hardest of
all (hence the two reserved TBD slots, to be filled the same way Phase
10.8 filled its Group C — a live, current accelerator-batch lookup, not
a guess). **This is flagged as a real dataset limitation for the next
phase to address, not resolved here.**

---

## 6. Sector Distribution

| Sector | Count |
|---|---|
| AI / AI infra | 7 (Cursor, Modal Labs, Together AI, Perplexity, Glean, Hugging Face, Harvey AI) |
| B2B SaaS | 6 (Metronome, Clay, Webflow, Gusto, Carta, ZipRecruiter) |
| Fintech | 3 (Middesk, Mercury, Airwallex) |
| Marketplace / consumer | 4 (Whatnot, Instacart, Discord, Quibi) |
| Logistics | 2 (Flexport, Convoy) |
| Healthcare / AI vertical | 1 (Olive AI) |
| Hardware / deep tech / construction | 2 (Katerra, Bird) |
| Legal AI vertical | 1 (Harvey AI, also counted under AI) |
| B2B SaaS (historical) | 1 (Mailchimp) |

**Documented limitation:** AI/AI-infra is deliberately the largest
single sector, reflecting real 2024-2026 startup-formation
concentration, not a sampling artifact this document should correct —
forcing artificial sector parity (per Part 5's own instruction, "do not
force equal sector representation if it creates artificial sampling")
would misrepresent the real startup landscape more than it would help.
Healthcare/biotech and pure hardware/deep-tech are the thinnest
categories (1-2 companies each) — a genuine, acknowledged limitation:
both sectors often have real evidence that is either highly regulated/
non-public (biotech clinical data) or capital-structure-heavy in ways
this cohort does not yet stress-test well. Flagged for the next phase
to consider expanding if capacity allows.

---

## 7. Strength-Profile Distribution

| Profile | Companies |
|---|---|
| Very strong / evidence-rich | Cursor, Perplexity, Glean, Scale AI, Harvey AI |
| Ordinary | Metronome, Webflow, Gusto, Middesk |
| Weak / distressed (real, documented, operating) | Flexport, Carta |
| Failed / shutdown | Convoy, Olive AI, Katerra, Quibi, Bird |
| High-growth | Whatnot, Perplexity, Discord |
| Profitable / slower-growth | ZipRecruiter, Instacart |
| Highly funded, unit-economics scrutiny warranted | Perplexity, Scale AI |
| Capital-efficient | Together AI (to verify), Mercury (to verify), Mailchimp (historical) |
| Elite-team / traction-TBD | Harvey AI, Cursor |
| Ordinary-team / strong-traction candidate | Metronome |
| Sparse-public-evidence | Middesk, Modal Labs, (TBD pre-seed slots) |
| Evidence-rich | Cursor, Discord, Hugging Face, Whatnot |

Every required category from Part 4's instruction is represented by at
least one real company; several profiles are hypotheses to be confirmed
(not asserted) once actual evidence is gathered — marked "to verify"
where the strength-profile label is a reasonable expectation rather
than an established fact.

---

## 8. Historical/As-Of-Date Methodology

For every calibration company, an explicit **assessment/as-of date** is
recorded. For the 30 currently-operating-or-recently-defunct companies,
this is simply "current as of dataset assembly" (subject to
re-verification at execution time, Section 4's disclaimer). For
**Mailchimp**, an explicit historical snapshot is used: **as-of
2020-01-01**, deliberately chosen to sit before its December 2021
acquisition by Intuit. Evidence gathered for this company at execution
time must be filtered to only what a researcher could have found
published on or before that date — this is the concrete test case for
whether the methodology's historical-snapshot discipline (Section 9's
hindsight-leakage safeguards) is actually followable, not just
theoretically designed.

The reserved second historical slot (#31) is intended to add a
**failed** or **struggling** historical case (as opposed to Mailchimp's
successful-outcome case), to test hindsight-leakage discipline in both
directions — deliberately left unfilled pending a specific, well-
documented candidate whose pre-outcome public evidence is genuinely
separable from its later, known outcome.

---

## 9. Hindsight-Leakage Safeguards

**The core rule, stated once and applied to every calibration company
with a known outcome (the 5 failed companies, Mailchimp, and any
company whose current status is already public knowledge):** evidence
gathered for scoring must be filtered to what was knowable as of the
assessment date, never what is knowable now.

Concretely, for the 5 failed companies (Convoy, Olive AI, Katerra,
Quibi, Bird), this document recommends the **current-state assessment
be run first** (their evidence as it exists today, which will naturally
include their shutdown — an explicit, disclosed negative fact, not a
leakage problem, since "this company shut down" IS current-state public
information) — this mirrors Phase 10.8's own explicit, adopted
current-state choice ("Current-State vs. Point-in-Time," accepted for a
first validation pass). **A true pre-outcome, as-of-date snapshot for
any of these 5 is optional, harder, and NOT required for this cohort's
primary purpose** — but if attempted for one or more of them in the
execution phase, the as-of date must be chosen and evidence filtered
BEFORE that date, with the same discipline as Mailchimp's case, and the
outcome itself (the shutdown) must never appear in that snapshot's
evidence set.

**Explicit prohibition, restated for enforceability:** a company that
eventually failed must not receive negative evidence dated after, or
implying knowledge of, its failure when assessed at an earlier as-of
date. A company that eventually succeeded (Mailchimp) must not receive
positive evidence that depends on knowing the eventual acquisition
(e.g., "this company was valuable enough to be acquired for $12B" must
never appear in the 2020-01-01 snapshot's evidence).

---

## 10. Boundary Case Design

For each **P0** parameter (Section 2), the calibration cohort must
include at least one real company landing near each candidate threshold
once actual evidence is gathered. This document pre-identifies *which*
companies are the most likely candidates to land near a boundary,
without asserting they will:

- **`gate.overall_coverage_floor_pct` (20-50%)**: Middesk and Modal
  Labs (sparse-public-evidence hypotheses) are the best candidates to
  test whether they land above or below whatever floor is eventually
  chosen — deliberately included for exactly this reason.
- **`band.negative_signal` (0-4)**: the 5 failed companies collectively
  provide the real negative-evidence density needed to determine
  whether 2.0 (current provisional) or a different value best separates
  "genuinely failed" from "merely thin evidence."
- **`gate.min_publishable_pillars` / `gate.min_critical_pillars_present`**:
  the 2 pre-seed/idea-stage TBD slots are the most likely real
  candidates to test the boundary of "just barely enough pillars" vs.
  "not enough," since early-stage companies naturally have the fewest
  assessable pillars.
- **Traction/Financial-Health stage bands**: every company was assigned
  a stage-hypothesis specifically so that, once real ARR/growth/burn
  figures are gathered, the cohort spans a genuine distribution around
  each stage's candidate ceiling — this cannot be fully confirmed until
  evidence exists, but the stage/sector spread was deliberately built
  wide enough (Section 5-6) to make it plausible.

This section does not claim boundary cases are guaranteed — only that
the cohort was deliberately shaped to make finding them likely once
evidence-gathering happens.

---

## 11. Outcome-Data Handling

For the 5 failed companies and Mailchimp, outcome data is recorded
**separately** from the evidence set used for scoring, in the manifest
(Section 20) under a distinct `outcome_data` field never merged into
`canonical_evidence`:

| Company | Outcome | Outcome date |
|---|---|---|
| Convoy | Shut down | October 2023 |
| Olive AI | Wound down / assets sold | 2023 |
| Katerra | Bankruptcy (Chapter 11) | 2021 |
| Quibi | Shut down | December 2020 |
| Bird | Bankruptcy (Chapter 11) | December 2023 |
| Mailchimp | Acquired by Intuit (~$12B) | November 2021 |

**Explicit rule, per Part 7:** this outcome data may be used in a
future phase for a cautious, descriptive, correlational sanity check
only (e.g. "do companies the methodology would score in the bottom
tier overrepresent this failed-company set relative to the strong tier")
— it must never be inserted into any company's evidence set, and must
never become an optimization target. SPS remains a strength assessment,
not an outcome predictor.

---

## 12. Expert-Reference Design

Experts (a role for a future phase, not filled in this document) will
be asked structured, non-circular questions, never "what SPS should
this get":

- For a given dimension and company: is the available evidence
  sufficient to assess it at all (mirrors `AvailabilityStatus`
  directly)?
- For a given dimension: does the evidence support NO_SIGNAL /
  SINGLE_SIGNAL-equivalent / MULTIPLE_SIGNALS-equivalent /
  COMPREHENSIVE-equivalent, described in plain language matching each
  tier's Rulebook definition (Part 7's worked examples), not as a
  number?
- Given two carefully matched companies (same stage, similar sector),
  which demonstrates stronger evidence on a named dimension? (Feeds
  Section 13's pairwise design directly.)
- Is a specific stage-relative signal (e.g. "$400K ARR at Seed")
  meaningfully strong, ordinary, or weak, in the expert's own
  professional judgment — used to sanity-check candidate
  `traction.current_scale.*` thresholds without ever asking for a
  specific dollar cutoff directly (asking for a cutoff invites exactly
  the "convenient bucket" anti-pattern Part 10 warns against).
- Would two specific cases reasonably fall in *meaningfully different*
  bands, or does the expert see them as substantively similar despite
  a threshold currently splitting them? (Directly informs boundary-case
  resolution, Section 10.)

---

## 13. Pairwise-Comparison Design

Where cohort companies are reasonably matched (same stage, comparable
sector), pairwise comparisons are preferred over absolute judgments,
per Part 9's own instruction. Pre-identified matched pairs from this
cohort, for a future phase's actual comparison work:

| Pair | Matched on | Comparison questions |
|---|---|---|
| Cursor vs. Modal Labs | Similar stage, both AI/dev-tools | Which shows stronger Traction evidence? Which shows stronger Team evidence? |
| Perplexity vs. Glean | Both Series C/D AI, both enterprise-adjacent | Which shows stronger Product differentiation? Stronger Market evidence? |
| Metronome vs. Clay | Both Series B B2B SaaS | Which shows stronger Execution evidence? |
| Gusto vs. ZipRecruiter | Both mature HR-adjacent B2B SaaS | Which shows stronger Financial Health evidence (to the extent public)? |
| Convoy vs. Katerra | Both real, documented failures, different sectors | Does the methodology's negative-evidence classification treat both consistently, or does sector affect the outcome inappropriately? |

Pairwise judgments inform parameter selection in the next phase by
answering: "does the current-provisional-value ranking agree with the
pairwise judgment?" — a mismatch is evidence the parameter needs
adjustment; agreement is evidence it doesn't, independent of either
company's absolute score.

---

## 14. Synthetic-Suite Integration

The 10.8F/G synthetic suite (64 tests, `app/calibration/sps_v3/tests/`)
remains the **mandatory regression gate** for any future parameter
change: unknown firewall, redundancy/fame attack, negative-evidence
tests, stage tests, renormalization tests, upper/lower-tail tests,
determinism tests, and trace reconstruction must all continue passing
after any candidate parameter value is applied, in the next phase,
before that value is considered viable — this document does not modify
or weaken any existing synthetic test, and none should be weakened
later merely to accommodate a convenient real-company outcome.

---

## 15. Calibration/Training Split

**Group A — Training (18 companies, listed in Section 4).** May
directly influence parameter selection — if a candidate threshold value
produces a nonsensical result against a Training-set company (e.g.
scoring a documented, severe failure as "strong"), that is direct
evidence the threshold needs adjustment.

---

## 16. Calibration Holdout Split

**Group B — Holdout (13 companies, listed in Section 4).** Must **not**
individually influence parameter tuning. Once a full candidate
parameter set is chosen using only the Training set, it is checked
against the Holdout set purely to detect overfitting — a large,
systematic divergence in behavior between Training and Holdout results
(not merely one company looking odd) is the signal to revisit, not to
directly re-tune against a specific Holdout company's result (which
would collapse the split's purpose entirely).

Both splits deliberately span the same stage/sector/strength-profile
diversity (Sections 5-7), not a "hard cases in Training, easy cases in
Holdout" split, so that Holdout genuinely tests generalization rather
than testing an artificially easier subset.

---

## 17. Recommended Sample Sizes

| Set | Recommended size | Justification |
|---|---|---|
| Calibration/Training | 19 (this phase) — future phase may expand toward 25-30 if manual evidence-review capacity allows | 5 stages × ~6-8 strength-profile archetypes cannot each get independent replication at n=19, but P0 parameters (5 of them) are the ones that most need real-company pressure-testing, and 19 companies deliberately spread across every stage/profile gives each P0 parameter multiple real data points without requiring exhaustive per-cell replication |
| Calibration Holdout | 12 (this phase) | Roughly 40% the size of Training, consistent with holdout conventions in similar low-N calibration settings — large enough to detect systematic (not single-company) overfitting, small enough that the manual evidence-review cost (Section 14's requirement that every company have full canonical observations, provenance, etc. — not a name + a website) stays proportionate |
| Future blind validation | **Not sized here — Section not started, per explicit instruction.** Phase 10.8's own prior blind cohort (25 companies) is the closest precedent and a reasonable starting reference for a future phase's own sizing decision, not a commitment made in this document. |

**Explicit statistical-power disclaimer:** n=19/12 supports directional,
qualitative calibration judgments (does this threshold produce sensible
behavior on real companies) and boundary-case checks — it does **not**
support claims of statistical significance for any specific threshold
value, and no future phase should present a calibrated parameter as
statistically validated at this sample size. This mirrors Phase 10.8's
own explicit n≈25-30 disclaimer for the original blind validation.

---

## 18. Public vs. Private Evidence Strategy

This cohort is designed as a **public-only evidence assessment**
cohort, for the same reason Phase 10.8's blind validation was
public-only: no founder/data-room access exists for any of these 31
companies (calibration development has no relationship with any of
them). This is an intentional, honest scope boundary, not an oversight:
**calibration of the currently-provisional Financial-Health/Traction
thresholds specifically will be limited by how much of that evidence is
genuinely public** — consistent with 10.8B/10.8E's own finding that
Financial Health is structurally the least publicly-assessable pillar.
**A separate, future founder/private-data-enriched calibration pass is
recommended but explicitly out of scope here** — this document does not
attempt to simulate or fabricate private data for any company, which
would violate the "no fabricated evidence" discipline this entire
engagement has maintained since Phase 10.8. Public-only companies must
never be penalized in Strength for private information being
unavailable — already an architectural guarantee (Rulebook Parts 7-8),
re-confirmed as a design constraint on this cohort, not something this
cohort itself needs to re-test.

---

## 19. Dataset Limitations

- Seed and Idea/Pre-Seed stage representation is thin (Section 5),
  with 2 slots explicitly unfilled pending live sourcing.
- Healthcare/biotech and pure hardware/deep-tech sectors are
  under-represented (1-2 companies each, Section 6).
- Every non-historical company's "current" facts (stage, funding,
  operating status) are stated from general knowledge as of this
  document's authoring and require live re-verification before
  evidence-gathering (Section 4's disclaimer) — this document is a
  roster design, not a verified fact sheet.
- Only one true historical AS-OF case (Mailchimp) is fully specified;
  a second (failed-outcome) historical case is reserved but unfilled.
- No private/founder-provided evidence is included anywhere in this
  cohort (Section 18) — Financial Health and parts of Traction
  calibration will be evidence-limited by design.
- Sample size (Section 17) supports directional calibration judgment
  only, not statistical validation of any specific threshold.

---

## 20. Dataset Manifest Architecture

A machine-readable manifest, `app/calibration/sps_v3/calibration_manifest.json`,
accompanies this document. Its schema (illustrated, not exhaustively
repeated here — see the file itself):

```
{
  "manifest_version": "10.8H-v1",
  "frozen": false,               // becomes true only once a future
                                  // phase confirms the roster after
                                  // live re-verification -- NOT frozen
                                  // by this document alone
  "purpose": "CALIBRATION -- NOT VALIDATION",
  "companies": [
    {
      "company_id": "CAL-001",
      "name": "Cursor (Anysphere)",
      "split": "TRAINING",
      "stage_hypothesis": "SERIES_A_B",
      "sector": "AI_DEV_TOOLS",
      "strength_profile_hypothesis": "VERY_STRONG_EVIDENCE_RICH",
      "as_of_date": null,          // null = current-state; a real
                                    // ISO date for historical cases
      "requires_live_reverification": true,
      "canonical_evidence": null,  // NOT populated by this phase
      "outcome_data": null,        // populated only for the 6
                                    // known-outcome companies, kept
                                    // structurally separate from
                                    // canonical_evidence
      "notes": "..."
    },
    ...
  ]
}
```

**No `desired_sps` field exists anywhere in this schema, on principle**
— the manifest cannot express a target score even by accident, which is
the concrete, structural enforcement of Part 17's prohibition, not just
a written rule.

---

*(Sections 21-24 are addressed in the accompanying chat report, not
duplicated in file form, since they are cross-cutting summaries rather
than new design content.)*
