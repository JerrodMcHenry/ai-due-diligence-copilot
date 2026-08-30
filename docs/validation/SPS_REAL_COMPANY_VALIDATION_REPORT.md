# SPS Real-Company Validation Report

Phase 10.11.1. This is an empirical validation study, not a methodology
change. Nothing in Methodology v2, `scoring_methodology.py`,
`scoring.py`, `vps_scoring.py`, Rankings, or Discovery was modified to
produce this report.

**Status: FINAL.** The frozen inputs (cohort selection, hypotheses,
input procedure, isolation strategy) were fixed before any company was
scored. The run is complete (25/30 companies; 5 permanent website-
ingestion failures, documented above). All results below are final and
have not been altered, filtered, or cherry-picked after the fact.

## Executive Summary

_(Filled in last, after the full run and analysis are complete.)_

## Methodology Version Under Test

- `METHODOLOGY_VERSION` = `v2-spec-2026-08-23`
- `ANCHOR_REGISTRY_VERSION` = `v2-anchor-registry-2026-08-23`
- `SCORING_VERSION` (pillar aggregation formula) = `2.0`
- `PILLAR_ANALYSIS_MODEL` = `gpt-4.1-mini`
- `PILLAR_PROMPT_VERSION` = `2.0`
- Pillar weights (`app/ai/scoring_methodology.py::PILLAR_WEIGHTS`):
  market 0.20, team 0.20, product 0.20, execution 0.15, traction 0.15,
  financial_health 0.10.

These are read directly from the running code, not hand-copied from
memory — see `app/ai/sie_v2_methodology.py` and
`app/ai/scoring_methodology.py`.

## Validation Architecture Discovered (Part 2)

`app/calibration/` already exists as this repo's calibration/benchmark
harness (`run_calibration.py`), and it establishes the exact pattern this
validation reuses rather than reinventing:

- `run_due_diligence(company_text, analysis_type, evidence_sources)`
  (`app/workflows/due_diligence_workflow.py`) is a **pure function** with
  respect to persistence — it runs research enrichment (Tavily), all six
  pillar analyses, summary/risk/memo/structured-analysis/competitor
  calls, and assembles the final `SIEMethodologyAnalysis`, but never
  calls `save_analysis()`, `save_score_history()`, or
  `get_or_create_startup()`. Those persistence calls live exclusively in
  `app/api.py`'s `POST /analyze` endpoint, one layer above.
- `run_calibration.py` already calls `run_due_diligence()` directly and
  serializes the full result to a JSON report file — zero database
  writes. This validation's runner
  (`app/calibration/validation_2026_08/run_validation_cohort.py`) is the
  same pattern, extended to loop a 30-company cohort and add
  group-comparison analysis afterward, not a parallel scoring system.
- Website ingestion (`app/website_scrapper.py::extract_text_from_website`)
  is the same hardened, SSRF-safe function `POST /analyze` uses for a
  website-only submission. This validation calls it directly, exactly the
  same way, for every company.
- No existing "score-distribution test" existed before this phase; the
  closest prior art was the pass/fail-range calibration suite (n=1,
  Stripe only) and the ad-hoc collection of analyses already sitting in
  the dev database from earlier phases' manual testing.

## Cohort Selection, Ex-Ante Hypotheses, Input Procedure

See the frozen manifest: `docs/validation/SPS_REAL_COMPANY_VALIDATION_COHORT.md`
(written and frozen before any company below was run).

**Input procedure (Part 7):** every company received exactly one input —
its real public website URL — passed through
`extract_text_from_website()` then `run_due_diligence(..., analysis_type="public",
evidence_sources=["website", "public_research"])`, identically to how
`POST /analyze` treats a website-only submission from any real user.
No company received hand-written supplemental text. `public_research`
(Tavily) ran automatically and identically for every company, since
`enrich_research()` always runs inside `run_due_diligence()` regardless
of input source.

**Isolation (Part 8):** `run_validation_cohort.py` imports nothing from
`app.database.db` — grep-verified. No canonical `startups` or `analyses`
row was created for any of the 30 companies. Every result lives only in
`app/calibration/validation_2026_08/raw_results_summary.json` and
`raw_results/*.json` on disk.

## Existing Database Baseline, Before This Validation (Part 3)

The raw `analyses` table contains 82 rows with a non-null `overall_score`,
but the great majority are repeated re-runs of a small number of
**fictional/placeholder test companies** used during earlier development
phases (e.g. "FlowAI" appears ~35 times, "AureliusFlow Technologies" ~7
times, "ScaleOps"/"ScaleOps AI", "NovaLedger", "AtlasGrid", "TalentFlow",
"FinPilot", "HealthOS", "CyberShield", "EcoGrid" — none of these are real
companies; they were calibration/dev fixtures, not analyses of real
businesses). These were excluded from the baseline below, which reflects
the actual **canonical startup universe** — i.e. exactly what
`get_rankings()` returns, the same query Explore/Rankings itself uses —
plus the one calibration benchmark (Stripe) run repeatedly during
methodology tuning.

**Canonical startups currently in Rankings (9 rows, 8 real companies + 1
degenerate test row):**

| Company | Stage | SPS | Market | Team | Product | Execution | Traction | Financial Health |
|---|---|---|---|---|---|---|---|---|
| Ramp Business Corporation | Growth | 79 | 8.1 (Medium, 80%) | 8.1 (Medium, 100%) | 7.7 (Medium, 100%) | 7.2 (Medium, 100%) | 8.1 (Medium, 55%) | 8.0 (Medium, 75%) |
| Vanta, Inc. | Growth | 79 | 8.6 (High, 80%) | 7.6 (Medium, 100%) | 7.3 (Medium, 100%) | 8.0 (Medium, 100%) | 7.8 (Low, 30%) | 8.0 (Medium, 45%) |
| Brex, Inc. | Growth | 73 | 7.8 (Medium, 80%) | 7.4 (Medium, 100%) | 6.9 (Low, 100%) | 7.2 (Medium, 100%) | 7.0 (Low, 15%) | 7.6 (Medium, 45%) |
| X (formerly Twitter) | Growth | 73 | 7.0 (Low, 20%) | 7.0 (Medium, 75%) | 7.4 (Medium, 65%) | 7.2 (Medium, 100%) | 8.0 (Low, 15%) | 7.0 (Medium, 45%) |
| Airtable | Growth | 71 | 7.0 (Low, 20%) | 6.2 (Medium, 75%) | 7.0 (Medium, 100%) | 7.2 (Medium, 100%) | 8.0 (Low, 15%) | 8.0 (Medium, 45%) |
| Retool | Growth | 71 | 8.0 (Medium, 45%) | 7.0 (Medium, 100%) | 6.1 (Low, 65%) | 7.2 (Medium, 100%) | 7.0 (Low, 15%) | 7.6 (Medium, 45%) |
| LiveCheck Inc. | Seed | 70 | 7.0 (Low, 20%) | 6.8 (Medium, 75%) | 6.7 (Medium, 65%) | 7.2 (Medium, 100%) | 7.0 (Low, 15%) | 7.4 (Medium, 45%) |
| Linear | Growth | 69 | 7.0 (Medium, 80%) | 6.9 (Medium, 75%) | 7.0 (Medium, 100%) | 7.2 (Medium, 100%) | 5.0 (Low, 15%) | 8.6 (Medium, 45%) |
| Example Domain | Idea | 0 | — (all Unavailable, literal example.com placeholder — excluded from stats below as not a real company) |

**Descriptive statistics (n=8 real companies, Example Domain excluded):**

- count: 8
- minimum: 69
- maximum: 79
- mean: 73.12
- median: 72.0
- standard deviation (population): 3.62
- 25th percentile: 70.75
- 75th percentile: 74.5
- range: 10

**Bucket counts (observational only, not methodology bands):**

| Bucket | Count |
|---|---|
| <40 | 0 |
| 40-49.9 | 0 |
| 50-59.9 | 0 |
| 60-69.9 | 1 |
| 70-79.9 | 7 |
| 80-89.9 | 0 |
| 90+ | 0 |

**Is the existing distribution compressed? Yes, severely.** 7 of the 8
real canonical companies land in a single 10-point bucket (70-79.9), and
the entire real-company range is only 10 points wide (69-79). This
matches the phase's own stated premise. One early, striking pattern
worth flagging before the validation cohort even runs: the **Execution**
pillar is 7.2 for 7 of these 8 companies — not merely similar, identical
to one decimal place across companies as different as a fintech
infrastructure company, a design-collaboration tool, and a social
network. This is investigated properly in the Pillar Discrimination
section below once the 30-company cohort's execution scores are in.

## Current-State vs. Point-in-Time (Part 18)

This validation is **current-state**, not point-in-time. Every company is
analyzed based on whatever `enrich_research()` (Tavily) and the target
website return *today* (2026-08-28) — including, for a handful of Group B
companies (WeWork, Peloton, Bumble, Clubhouse, Better.com, Bolt, Gopuff,
Away), publicly available information about real, already-occurred
difficulty, restructuring, or decline. This is stated explicitly per the
phase's own instruction: no company here is being scored "as if it were
still 2019/2021," and no attempt is made to reconstruct a historical
snapshot. This is the simpler, acceptable-for-V1 choice the phase itself
allows.

## Famous-Company / Public-Data Bias (Part 17)

This is a real, structural limitation of any evidence-based scoring
system that relies on public research, and it is documented honestly
here rather than hidden. `enrich_research()` runs the same Tavily search
process for every company, but the RESULTS of that search are
necessarily a function of how much has been publicly written about a
company. A company like Notion, Figma, or Peloton has years of press
coverage, funding announcements, customer case studies, and (for public
companies) SEC filings; a Y Combinator Fall 2025 company that launched
weeks before this validation was run has almost none, by construction —
not because it is a worse company, but because it has not existed in
public view long enough to accumulate the same evidentiary record.

**What SIE is actually measuring, honestly stated:** a combination of
(1) genuine company substance as reflected in its own public materials,
and (2) how much independently-verifiable public information exists
about the company at all. These are correlated with real company quality
(strong companies often do generate more public evidence over time) but
they are not the same thing, and the gap between them is largest for the
youngest companies. This is examined empirically in the Evidence/
Confidence section below once results are in — specifically, whether
Group C's low evidence coverage is doing most of the work in separating
it from Groups A/B, versus genuine pillar-level differences that would
hold even with equal evidence.

## Run Outcome (Part 9)

30 companies were attempted. **25 completed**, **5 failed at the website-
extraction stage**, all with HTTP errors from the target site's own bot
protection, confirmed reproducible on a second attempt (the runner's
resume logic automatically retried every "failed" row after an unrelated
infrastructure interruption restarted the process mid-run):

| Company | Group | Error |
|---|---|---|
| Toast, Inc. | A | HTTP 403 (both the original product-subdomain URL and the corrected canonical root domain) |
| Chime | A | HTTP 403 |
| Bolt | B | HTTP 429 |
| Gopuff | B | HTTP 403 |
| WeWork | B | HTTP 403 |

No substitute companies were added and no other company was re-run to
compensate. Per Part 1, these are reported as permanent, honest pipeline
limitations, not worked around further (no proxy, no header-spoofing, no
alternate scraper attempted). Final completed cohort: **8/10 Group A,
7/10 Group B, 10/10 Group C — 25 companies total.**

## Full Results Table (Part 9)

Ordered by SPS, descending:

| SPS | Group | Company | Stage (extracted) | Recommendation |
|---|---|---|---|---|
| 76.0 | A | Rippling | Growth | Promising but Needs Diligence |
| 73.9 | A | Klaviyo | Growth | Promising but Needs Diligence |
| 73.1 | A | Abnormal Security | Growth | Promising but Needs Diligence |
| 72.5 | C | Relaw | Seed | Promising but Needs Diligence |
| 71.2 | C | Bravi | Series A | Promising but Needs Diligence |
| 70.8 | A | Figma | Growth | Promising but Needs Diligence |
| 70.5 | C | Sourcebot | Seed | Promising but Needs Diligence |
| 69.9 | A | Notion Labs | Growth | Speculative |
| 69.8 | B | Bumble Inc. | Growth | Speculative |
| 69.6 | C | Rivet | Seed | Speculative |
| 69.5 | A | Faire | Growth | Speculative |
| 69.5 | C | LunaBill | Series A | Speculative |
| 69.2 | C | Openroll | Seed | Speculative |
| 69.1 | B | Loom | Series B+ | Speculative |
| 69.1 | C | Fixpoint | Seed | Speculative |
| 68.5 | A | Deel | Growth | Speculative |
| 68.5 | B | Peloton Interactive | Growth | Speculative |
| 68.2 | B | Plaid | Growth | Speculative |
| 68.1 | C | Denki | Seed | Speculative |
| 67.9 | B | Away | Growth | Speculative |
| 67.7 | A | Databricks | Growth | Speculative |
| 67.2 | B | Better.com | Growth | Speculative |
| 65.6 | C | Bear AI | Seed | Speculative |
| 64.9 | B | Clubhouse | Growth | Speculative |
| 63.0 | C | Dome | Growth (extracted — see Stage Fairness note) | Speculative |

Raw per-company JSON (all pillar subscores, evidence, confidence) is in
`app/calibration/validation_2026_08/raw_results/*.json`; the machine-
readable summary powering every table in this report is
`raw_results_summary.json` and the derived stats are in
`analysis_output.json`.

## Overall SPS Distribution (Part 10)

- n = 25
- min = 63.0, max = 76.0, **range = 13.0**
- mean = 69.33, median = 69.2
- population stdev = 2.72
- p25 = 68.1, p75 = 70.5 (interquartile range = 2.4)

**Buckets (observational, not methodology bands):**

| Bucket | Count |
|---|---|
| <40 | 0 |
| 40-49.9 | 0 |
| 50-59.9 | 0 |
| 60-69.9 | 18 |
| 70-79.9 | 7 |
| 80-89.9 | 0 |
| 90+ | 0 |

18 of 25 companies (72%) — spanning everything from a pre-seed YC F25
company to a $100B+ AI infrastructure leader to a public NASDAQ company —
land inside a single 10-point bucket. This is a *more* severe compression
than the 8-company pre-validation baseline (which already showed 7/8 in
one bucket): a 3x larger, deliberately diversified real-company cohort
did not widen the distribution, it widened by only 3 points on the low
end (69→63) and stayed essentially flat on the high end (79→76).

## Expected-Group Distributions (Part 11)

| Group | n | min | max | mean | median | stdev |
|---|---|---|---|---|---|---|
| A (strong, hypothesis) | 8 | 67.7 | 76.0 | 71.17 | 70.35 | 2.70 |
| B (mixed, hypothesis) | 7 | 64.9 | 69.8 | 67.94 | 68.20 | 1.46 |
| C (early/weak, hypothesis) | 10 | 63.0 | 72.5 | 68.83 | 69.35 | 2.61 |

Group A does score highest on average, as hypothesized. But **Group C
outscores Group B on both mean (68.83 vs 67.94) and median (69.35 vs
68.20)** — the exact opposite of the ex-ante ordering (A > B > C). Group
B, hypothesized as "developing/mixed," in practice contains several
real, mature, well-evidenced companies (Plaid, Peloton, Bumble) that
should plausibly outscore pre-seed YC companies and did not.

## Group Separation and Rank Correlation (Part 11-12)

Pairwise dominance — fraction of (x, y) pairs across two groups where x's
SPS exceeds y's:

| Comparison | P(x > y) |
|---|---|
| P(A > B) | 0.848 |
| P(A > C) | 0.694 |
| P(B > C) | **0.307** |

A beats B and A beats C most of the time — a real, directionally-correct
signal for Group A. But **P(B > C) = 0.307 means Group C beat Group B in
69% of head-to-head pairs** — a clean inversion of the ex-ante hypothesis
between those two groups.

**Spearman rank correlation** between ex-ante group ordinal (A=3, B=2,
C=1) and actual SPS across all 25 companies: **ρ = 0.274**. At n=25 this
is a weak positive correlation — better than chance, far short of what
would be needed to say SPS reliably recovers the hypothesis ordering. Per
Part 11's own instruction, this is reported without overstating its
significance: ρ=0.274 is directionally consistent with *some* real
signal (mostly carried by Group A's edge), not evidence of strong,
reliable group separation.

## Score Compression Analysis (Part 12)

Where the compression originates, traced through the pipeline:

1. **Pillar-level compression is the direct cause.** Every one of the six
   pillars has a population stdev under 0.8 on a 0-10 scale across 25
   very different companies (see Pillar Discrimination below). A
   weighted average of six already-compressed inputs cannot produce an
   uncompressed output — this is arithmetic, not a separate bug.
2. **`calculate_base_score()` (`app/ai/investment_score.py`) is a pure
   renormalized weighted average of pillar `score` values.** There is no
   multiplicative or non-linear step anywhere in the aggregation that
   could re-expand small pillar differences into large SPS differences.
   `get_adjustments()` returns `[]` unconditionally (documented stub) —
   confirmed unchanged, confirmed not invoked with any effect in any of
   the 25 runs.
3. **The pillar-level compression itself traces to score-band anchor
   language, not to any one company's evidence.** Every pillar's score
   distribution clusters tightly around a "Medium" band regardless of
   whether the subject is a pre-seed YC company or a $100B+ growth-stage
   leader — visible directly in the by-group pillar means below, which
   differ by well under 1 point pillar-to-pillar between Group A and
   Group C in five of six pillars.
4. **Execution is the most compressed of all six pillars** (stdev=0.31,
   median identical at 7.2 across all three groups) — consistent with
   the pre-validation baseline's observation, and consistent with the
   hypothesis that Execution's heavy reliance on **Inferred** dimensions
   (3 of 4: Go-to-Market, Product, Strategic Execution) produces
   anchor language that both Databricks and a pre-seed YC company
   satisfy almost identically, because "Inferred" dimensions are scored
   from plausible narrative inference rather than hard evidence that
   would actually differ between a mature company and an early one.

This is a scoring-anchor and evidence-architecture finding, not a data-
quality finding — the same six-pillar engine, given genuinely different
real companies with genuinely different amounts of public evidence, still
produced pillar scores that vary by under 1 point on average between the
strongest and weakest hypothesis groups.

## Pillar Discrimination (Part 13)

| Pillar | min | max | mean | median | stdev | Group A mean | Group B mean | Group C mean |
|---|---|---|---|---|---|---|---|---|
| Market | 5.9 | 8.8 | 7.20 | 7.0 | 0.58 | 7.51 | 7.17 | 6.96 |
| Team | 6.0 | 7.3 | 6.40 | 6.2 | 0.45 | 6.38 | 6.27 | 6.51 |
| Product | 5.7 | 7.7 | 6.82 | 6.8 | 0.48 | 7.01 | 6.74 | 6.71 |
| Execution | 6.2 | 8.0 | 7.16 | 7.2 | **0.31** | 7.29 | 7.00 | 7.18 |
| Traction | 6.0 | 8.0 | 7.04 | 7.0 | 0.60 | 7.25 | 6.71 | 7.10 |
| Financial Health | 6.0 | 8.4 | 7.20 | 7.4 | 0.76 | 7.58 | 7.00 | 7.04 |

Observations:

- **Execution is the least discriminating pillar by a wide margin**
  (stdev 0.31 vs 0.45-0.76 for the other five) — confirms the pre-
  validation hypothesis. It also shows the *weakest* group ordering of
  any pillar: Group C's execution mean (7.18) is essentially tied with
  Group A's (7.29), both well above Group B's (7.00).
- **Team is the second most compressed pillar** (stdev 0.45) and shows
  **no group ordering at all** — Group C's team mean (6.51) is the
  *highest* of the three groups, ahead of both A (6.38) and B (6.27).
  This is a genuine surprise: hypothesis-Group-A founders (Notion,
  Figma, Databricks, Rippling, Deel, etc. — well-documented, frequently-
  profiled repeat/notable founders) did not score higher on Team than
  first-time YC F25 founders with far less public track record.
- **Financial Health is the least-compressed pillar** (stdev 0.76) and
  the only one where Group A meaningfully leads both other groups
  (7.58 vs 7.00/7.04) — the one pillar behaving closest to hypothesis.
- **Market and Traction show a correct but very small A>B>C-ish gradient**
  in mean, but the gaps (0.2-0.5 points on a 10-point scale) are too
  small relative to the pillars' own stdev to call this reliable
  separation rather than noise.
- No pillar had any `Unavailable` (null) scores across all 25 companies
  — evidence requirements were satisfiable for every pillar on every
  company, including the least-evidenced Group C companies. Compression
  is not being caused by missing/null subscores.

## Stage Fairness (Part 14)

SPS by extracted company stage (not hypothesis group):

| Stage (extracted) | n | mean | median | min | max |
|---|---|---|---|---|---|
| Series A | 2 | 70.3 | 70.3 | 69.5 | 71.2 |
| Growth | 15 | 69.3 | 68.5 | 63.0 | 76.0 |
| Seed | 7 | 69.2 | 69.2 | 65.6 | 72.5 |
| Series B+ | 1 | 69.1 | 69.1 | 69.1 | 69.1 |

Seed-stage companies (mean 69.2) score essentially identically to
Growth-stage companies (mean 69.3) — a 0.1-point difference. Read one
way, this is a positive stage-fairness finding: SIE is **not**
systematically penalizing early-stage companies for being early, which
was a real risk this validation was designed to catch. Read the other
way, it is the same compression finding restated by stage instead of by
hypothesis group: stage, like hypothesis group, does not meaningfully
move SPS in this run. The two readings aren't in tension — "doesn't
unfairly penalize early stage" and "doesn't discriminate on maturity at
all" are the same flat line viewed from different angles, and this
validation cannot cleanly separate "fair" from "insensitive" with only
25 companies concentrated in Growth/Seed.

One extraction anomaly worth flagging under this heading rather than
under Context Extraction alone: **Dome** (a real YC Fall 2025 pre-seed
company, per the frozen manifest) had its stage extracted as **"Growth"**
by the pipeline — clearly wrong for a company weeks out of a pre-seed
accelerator batch. It nonetheless scored the *lowest* SPS in the entire
cohort (63.0), so the mis-extraction did not inflate its score in this
instance, but it does mean the "Growth" stage-fairness row above is
contaminated by at least one genuinely-Seed company being counted as
Growth. **LunaBill** and **Bravi** (both YC F25) were extracted as
"Series A" for the same underlying reason — likely the model inferring
stage from funding-round language on the company's own site rather than
true a true company stage lookup.

## Evidence / Confidence Analysis (Part 15)

Confirmed architectural fact restated with real data: `calculate_base_score()`
uses only pillar `score` values; confidence (High/Medium/Low) and
evidence_coverage are computed and stored per pillar but **never** feed
into the SPS number itself. This validation's data is consistent with
that: the check for "SPS ≥ 75 AND ≥ 3 Low-confidence pillars" — a case
that would be hard to defend if it existed — returned **zero** matches
across all 25 companies. No company in this cohort achieved a high score
riding on mostly-unreliable pillars, largely because no company achieved
a high score at all (max = 76.0) and because most companies carry 1-3
Low-confidence pillars regardless of where they land.

Average per-pillar evidence coverage ranged from 53.3% (the observed
floor for several companies across all three groups, both real unicorns
like Peloton/Plaid/Clubhouse and pre-seed companies like Rivet/Openroll/
Fixpoint) up to 73.3% (Sourcebot). There is **no clean relationship**
between evidence coverage and SPS in this data — Sourcebot (highest
coverage, 73.3%) and several 53.3%-coverage companies land within a few
points of each other. This suggests evidence coverage in its current
form is not the primary driver of the compression either; the pillar
score anchors themselves (Score Compression Analysis, above) are the
more direct cause. Per the phase's explicit instruction, this finding is
reported as a description of current architecture, not a recommendation
that SPS incorporate confidence — that judgment belongs in the
Recommendations section below, and even there only as a candidate for
further investigation, not a prescribed fix.

## Outlier Review (Part 16)

**Five negative surprises** (companies scoring notably lower than their
ex-ante hypothesis would predict):

1. **Databricks (Group A, SPS 67.7)** — one of the most valuable, most
   publicly documented private AI-infrastructure companies in the world,
   landed in the bottom third of the entire 25-company field, below
   *six* of the ten Group C (pre-seed/seed) companies. **Classification:
   SCORING ANCHOR ISSUE, STAGE-AWARENESS ISSUE.** Databricks' pillar
   scores individually look reasonable (all "Medium" band) but the
   anchor language evidently caps well-evidenced growth companies at
   roughly the same band a seed company can also reach.
2. **Notion Labs (Group A, SPS 69.9)** — scored below Bumble, Relaw,
   Bravi, Sourcebot, and Rivet — effectively all of Group C.
   **Classification: SCORING ANCHOR ISSUE.**
3. **Deel (Group A, SPS 68.5)** and **Plaid (Group B, SPS 68.2)** — both
   mature, category-defining, heavily-evidenced companies, both landed
   below multiple pre-seed YC companies. **Classification: SCORING
   ANCHOR ISSUE.**
4. **Clubhouse (Group B, SPS 64.9)** — near the bottom of the field.
   Partially explainable (Clubhouse's real-world decline from its 2021
   peak is well documented, and this validation is deliberately current-
   state), but its score is close enough to several Group C companies
   that "well-documented decline" and "thin pre-seed evidence" are
   landing in the same SPS neighborhood for very different underlying
   reasons. **Classification: EXPECTED HYPOTHESIS PARTIALLY RIGHT +
   SCORING ANCHOR ISSUE** (current-state decline is real signal; the
   anchor compression is what pulls it so close to Group C).
5. **Dome (Group C, SPS 63.0, the cohort minimum)** — the single lowest
   score in the entire validation, but its stage was mis-extracted as
   "Growth" rather than pre-seed (see Stage Fairness). **Classification:
   CONTEXT EXTRACTION ISSUE.** Flagged as a negative surprise because a
   mis-classified pre-seed company being scored as if mature and still
   landing at the bottom is a different (and arguably worse) failure
   mode than simply scoring a genuine pre-seed company low.

**Five positive surprises** (companies scoring notably higher than their
ex-ante hypothesis would predict):

1. **Relaw (Group C, SPS 72.5)** — the 4th-highest score in the entire
   cohort, ahead of 6 of 8 Group A companies. A real, currently-operating
   YC F25 legal-tech company with (per its own evidence coverage, 72.5%,
   the second-highest in the cohort) an unusually strong public web
   presence for a pre-seed company. **Classification: INPUT QUALITY
   ISSUE (in Relaw's favor) + PUBLIC DATA LIMITATION** — Relaw's website
   evidently gave the pipeline more to work with than most of its YC
   batch-mates, which is a legitimate difference in company presentation,
   not an error, but it does mean the score partly reflects marketing-
   page thoroughness rather than only business substance.
2. **Bravi (Group C, SPS 71.2)** — 5th-highest overall, ahead of 6 of 8
   Group A companies. **Classification: SCORING ANCHOR ISSUE** (same
   anchor-compression mechanism pulling a young company up toward the
   same band as mature companies, rather than Bravi being uniquely
   over-evidenced).
3. **Sourcebot (Group C, SPS 70.5)** — ahead of Notion Labs, Deel, and
   Databricks. Sourcebot had the single highest average evidence
   coverage in the entire cohort (73.3%) despite being pre-seed — a
   developer-tools company with an unusually documentation-rich public
   site. **Classification: INPUT QUALITY ISSUE + PUBLIC DATA LIMITATION.**
4. **Rivet (Group C, SPS 69.6)** — indistinguishable from Faire and just
   behind Notion Labs, both Group A. **Classification: SCORING ANCHOR
   ISSUE.**
5. **Bumble Inc. (Group B, SPS 69.8)** — despite well-documented public
   headwinds (declining user growth, stock performance), scored
   competitively, ahead of 5 of 8 Group A companies. **Classification:
   SCORING ANCHOR ISSUE** — consistent with the broader finding that the
   anchors compress almost everything toward the same mid-60s/low-70s
   band regardless of real underlying differences in either direction.

**Cross-cutting read:** 6 of these 10 outliers are independently
classified as SCORING ANCHOR ISSUE — by far the dominant single cause in
this data — with INPUT QUALITY ISSUE / PUBLIC DATA LIMITATION and
CONTEXT EXTRACTION ISSUE as secondary, narrower causes affecting specific
companies. No outlier in this review was best explained by
PILLAR-ANALYSIS-implementation bugs, WEIGHTING ISSUE, or
CONFIDENCE-EVIDENCE ISSUE specifically — those remain possible
contributors but are not what the evidence here points to first.

## Limitations of This Validation (Part 17-18)

- **Famous-company / public-data bias is real but did not resolve in the
  expected direction.** Group A companies do have the most public
  evidence on average, and Group A does score highest on average — but
  the compression is severe enough that this advantage translates into
  only a ~3-point mean gap over Group C, not a wide, obviously-separated
  band. If anything, this run shows the anchor-compression effect is
  currently *stronger* than the public-data-bias effect: even companies
  with a large public-evidence advantage don't pull far ahead.
- **n=25 per pillar/n=7-10 per group is a genuinely small sample.** Every
  statistic above (especially Spearman ρ=0.274 and the by-stage means)
  should be read as suggestive, not conclusive. This validation was
  explicitly designed as a first empirical pass, not a final verdict.
- **Current-state, not point-in-time (declared above, restated here as a
  limitation):** Clubhouse's, WeWork's (failed to fetch), Better.com's,
  and Peloton's scores reflect 2026-08-28 public information about
  companies with well-documented post-peak difficulty, not a snapshot
  from their respective growth peaks. This is an accepted, documented
  choice for this first validation, not an oversight.
- **5 of 30 companies (all from Groups A and B) could not be scored at
  all** due to bot-protected websites, shrinking Group B in particular to
  7 companies — the smallest of the three groups — which further widens
  the confidence interval around any Group-B-specific statistic.
- **Stage and hypothesis-group are correlated but not identical** (see
  the two Context Extraction mis-labels above), which slightly
  contaminates the by-stage table.

## Potential Methodology Issues — Categorized, Not Implemented (Part 19)

Per the phase's explicit instruction, nothing below has been implemented.
Each is categorized using the fixed taxonomy, with the observed failure,
affected company count, pillar(s), why current behavior looks wrong, the
supporting evidence, and an explicit overfitting-risk note.

1. **HIGH-PRIORITY METHODOLOGY ISSUE — Score-band anchor compression
   across most pillars.**
   - Observed failure: 18/25 companies (72%) land in a single 10-point
     SPS bucket (60-69.9); pillar-level stdev is under 0.8 on a 0-10
     scale for every pillar; Execution stdev is 0.31.
   - Company count: 25/25 (universal pattern, not isolated).
   - Pillar(s): all six, most severely Execution, then Team.
   - Why current behavior seems wrong: a $100B+ growth-stage AI
     infrastructure leader (Databricks) and a pre-seed company weeks out
     of an accelerator (Dome, Rivet, etc.) should not routinely land
     within a few points of each other on Execution or Team.
   - Supporting evidence: Pillar Discrimination and Score Compression
     sections above, both derived directly from this run's data.
   - Overfitting risk: **high if "fixed" using only this cohort.** Any
     anchor-language change should be re-validated against a second,
     independently-selected cohort before being trusted, to avoid tuning
     anchors to this specific 25-company sample's idiosyncrasies.

2. **NEEDS MORE DATA — Group B underperforming Group C.**
   - Observed failure: Group B mean (67.94) and median (68.20) both
     below Group C (68.83 / 69.35); P(B>C)=0.307.
   - Company count: 7 vs 10 (both small).
   - Pillar(s): most visible in Traction (Group B mean 6.71, lowest of
     the three groups).
   - Why current behavior seems wrong: several Group B companies (Plaid,
     Peloton, Bumble) are large, mature, well-evidenced businesses that
     plausibly should outscore pre-seed companies on Traction
     specifically.
   - Supporting evidence: Group Separation section above.
   - Overfitting risk: **low priority to act on right now** — n=7 for
     Group B (after the 3 website-extraction failures) is too small to
     distinguish "real methodology gap" from "unlucky small sample."
     Recommend re-running with a larger, restored Group B before treating
     this as confirmed.

3. **POSSIBLE METHODOLOGY ISSUE — Team pillar shows no group ordering.**
   - Observed failure: Group C's Team mean (6.51) is the highest of the
     three groups, ahead of Group A (6.38).
   - Company count: 25/25 contribute to the comparison.
   - Pillar(s): Team only.
   - Why current behavior seems wrong: Group A's founders are, on
     average, more publicly documented (funding announcements, press
     profiles, prior-company track records) — if Team scoring rewards
     evidenced accomplishment, Group A should lead here more than it
     does.
   - Supporting evidence: Pillar Discrimination table above.
   - Overfitting risk: **medium** — could reflect a genuine methodology
     property (YC vets founders before admission, so "Team" evidence
     quality may be more uniform across YC F25 companies than assumed)
     rather than a flaw; needs qualitative review of a few Team pillar
     outputs before concluding anything.

4. **LIKELY INPUT-INGESTION ISSUE — Company-stage extraction errors for
   at least 2 of 10 Group C companies (Dome, and to a lesser extent
   LunaBill/Bravi).**
   - Observed failure: Dome (real pre-seed YC F25 company) extracted as
     stage "Growth"; LunaBill and Bravi (also YC F25) extracted as
     "Series A."
   - Company count: 3/25 confirmed, possibly more not visibly wrong.
   - Pillar(s): stage extraction is upstream of all six pillars, so this
     could quietly affect any stage-conditioned scoring guidance.
   - Why current behavior seems wrong: verified against the frozen
     cohort manifest and each company's own real, current funding status.
   - Supporting evidence: Stage Fairness section above.
   - Overfitting risk: **low** — this is a factual extraction accuracy
     issue, independently checkable against public information, not a
     scoring-philosophy judgment call.

5. **LIKELY ANALYSIS ISSUE — Website-scraper failure rate on well-known
   brands (5/30, 16.7%).**
   - Observed failure: Toast, Chime, Bolt, Gopuff, WeWork all returned
     HTTP 403/429 to `extract_text_from_website()`.
   - Company count: 5/30.
   - Pillar(s): none directly (upstream of pillar analysis entirely) —
     but it means SIE currently cannot analyze several large, real,
     well-known companies from their own website at all.
   - Why current behavior seems wrong: these are legitimate companies
     with normal public websites; the failures are the scraper being
     blocked by bot protection, not anything about the companies.
   - Supporting evidence: reproducible on retry for all 5, confirmed via
     the runner's automatic resume-retry.
   - Overfitting risk: **low** — this is a product-robustness gap
     (consider a fallback ingestion path, e.g. accepting pasted text or
     a PDF when website scraping fails) rather than a scoring-tuning
     question at all.

## Recommendations — Not Implemented (Part 19)

These are recommendations for future phases, explicitly not acted on in
this validation:

1. Investigate and likely loosen/re-anchor score-band language for
   Execution and Team specifically, since they show the least
   discrimination — but only after a second independent cohort confirms
   this isn't specific to these 25 companies.
2. Consider a stage-aware or evidence-volume-aware scoring adjustment
   *if* a second validation round confirms the anchor-compression finding
   holds — explicitly not proposed as confirmed-needed from this single
   run alone.
3. Add a fallback ingestion path (pasted text / PDF upload prompt) when
   website scraping fails, to close the 16.7% real-company coverage gap
   observed here.
4. Fix the stage-extraction accuracy issue for early-stage companies
   (Dome, LunaBill, Bravi) as a straightforward correctness fix,
   independent of any scoring-anchor work.
5. Re-run this same validation protocol with a second, independently-
   selected ~30-company cohort before making any scoring change, to
   distinguish genuine methodology findings from this-sample-specific
   noise — especially for the Group B < Group C finding (n=7 vs n=10).

## Homepage Decision (Part 22)

**SPS distribution is not yet sufficiently validated for a representative
high/middle/low marketing preview.** The data does not support it:

- The full observed range is 13 points (63.0-76.0) across 25 real,
  deliberately diverse companies — there is no natural "high" example in
  this cohort that looks meaningfully different from a natural "middle"
  example; the highest score (Rippling, 76.0) sits only 2.1 points above
  the next company and is followed immediately by three real pre-seed YC
  companies within another 1.4 points.
- No company scored below 63.0 or above 76.0 anywhere in this run — there
  is no natural "low" example either, in the sense a homepage preview
  would want (something visibly, defensibly weaker).
- Presenting any 3 of these 25 companies as "here's what high/medium/low
  SPS looks like" would overstate how differentiated the underlying
  scores actually are, which is precisely the failure mode Part 22 warns
  against.

This is reported honestly as a **negative validation finding**, per the
phase's own framing: "the experiment is valuable even if SPS performs
badly." No homepage change is recommended or made in this phase.

## Test / Regression Verification (Part 24)

- `git status --porcelain -- app/` shows only new, additive files under
  `app/calibration/validation_2026_08/` (the runner, cohort, analyzer,
  and their output JSON) — zero modifications to any existing file in
  `app/`.
- Zero modifications to `app/ai/scoring_methodology.py`,
  `app/ai/scoring.py`, `app/ai/investment_score.py`,
  `app/ai/vps_scoring.py` (VPS), `app/ai/readiness_score.py`
  (Fundraising Readiness), any Rankings/Discovery query, or any dashboard
  file — confirmed by the same `git status` check plus direct inspection
  of each file's diff (none exists).
- `test_backend_authentication` (14/14) and `test_security_hardening`
  (24/24) were re-run mid-validation as regression spot-checks — both
  fully passing, unaffected by the read-only validation harness.
- Live-observed during the run: `get_rankings()` continued returning
  exactly the same 9 rows (8 real canonical companies + the "Example
  Domain" placeholder) throughout all 30 attempted company analyses —
  direct, empirical confirmation that the isolated harness wrote zero
  rows to the canonical `startups`/`analyses` tables.

## Executive Summary

A blind, frozen, 30-company cohort of real companies (10 hypothesized
strong/evidenced, 10 hypothesized mixed, 10 hypothesized early/weak, all
real, none fabricated, none removed after scoring) was run through the
unmodified production SIE pipeline. 25 completed (5 failed at website-
ingestion due to bot-protected sites, a genuine, documented product
limitation, not a scoring issue). 

**The core finding is severe, universal score compression**: 25 real
companies ranging from a pre-seed YC company to a $100B+ AI
infrastructure leader to multiple public companies produced SPS scores
spanning only 13 points (63.0-76.0), with 72% of them landing in one
10-point bucket. Group A (hypothesized strongest) does score highest on
average, and the highest-ever SPS in this run is a Group A company —
there is *some* real signal. But group separation is weak (Spearman
ρ=0.274) and, most strikingly, Group C (hypothesized weakest, all real
pre-seed/seed YC F25 companies) **out-scored Group B (hypothesized
mixed) on both mean and median**, the opposite of the ex-ante hypothesis
between those two groups.

The compression traces most directly to pillar-level scoring anchors —
particularly Execution and Team, the two least-discriminating pillars —
not to evidence/confidence handling (which is confirmed architecturally
inert to the SPS number, and empirically shows no clean relationship to
score in this data either) and not to missing data (no pillar had a
single `Unavailable` score across all 25 companies). Stage fairness is
mixed-to-acceptable: SPS does not penalize earlier-stage companies, but
that is largely because SPS doesn't discriminate much on maturity at all
in its current form. No catastrophic counterexamples were found (no
extremely low- or high-quality company scored wildly outside this narrow
band), but the narrow band itself is the finding.

Per the phase's own framing, this is a successful, honest validation
precisely because it surfaced a real problem rather than a flattering
distribution. No methodology, scoring, or homepage change has been made.
The homepage representative-range preview is explicitly **not**
recommended at this time. Full findings, root-cause classification, and
non-implemented recommendations are above.
