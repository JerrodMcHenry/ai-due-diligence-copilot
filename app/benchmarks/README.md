# SIE Methodology v2 — Historical Benchmark Portfolio

**Status: benchmark assets only.** No production scoring code modified, no methodology
implementation changed, no expected scores changed, no company run through the live SIE pipeline,
nothing committed. This document is the human-readable companion to the structured records under
`app/benchmarks/companies/*.json` and the index in `app/benchmarks/manifest.json`.

**Evidence repair round 1 (2026-08-23):** following a pre-scoring audit, targeted evidence repair
was performed on 8 of the 15 calibration records — Jawbone (replaced an unflagged, undated
market-share claim with a properly-dated NPD-sourced figure), Meetup (added leaked-shareholder-
document figures for the exact snapshot month), Warby Parker (removed unconfirmed sales/units
figures traced only to undated retrospective content; replaced with a verified donation-volume
figure from a proper contemporaneous source), Tesla (resolved an orphan citation by re-sourcing two
facts to genuinely contemporaneous articles; removed one unverifiable price figure), Bonobos (repair
attempted, no qualifying new source found — reported honestly, not padded), Beepi, Quibi, and Shyp
(enrichments extracted from already-cited sources, no new sourcing risk introduced). Full details are
in each record's `benchmark_notes.evidence_repair_log`. No `expected_quality_tier` was changed by
this round; two records (Jawbone, Warby Parker) carry an explicit tier-questionability flag for
separate adjudication. The five holdout companies were not touched.

---

## Part 1 — Review of the originally proposed portfolio

The ~20-company list proposed in `app/docs/SIE_Methodology_v2_Audit.md` (Part 7) was **not**
accepted as-is. It failed several of the review criteria it was itself supposed to satisfy:

- **Excessive concentration in famous successful companies.** 10 of the original 20 (Airbnb,
  Slack, DoorDash, Stripe, Figma, Databricks, Shopify, Snowflake, Datadog, and an ambiguous Tesla)
  sat in "Strong" or above — a 50% concentration in famous winners.
- **Insufficient failed/mediocre companies.** Only 2 of 20 were tiered "Very Weak/Failed"
  (Quibi, Fab.com), and both were companies famous largely *because* of how they turned out, not
  companies that were genuinely obscure at their snapshot.
- **Hindsight bias baked into company selection itself, not just company description.** Every
  company on the original list is a company most people have heard of — meaning it is famous
  either for succeeding spectacularly or for failing spectacularly (with heavy contemporaneous
  media attention in both directions, itself partly a function of founder fame). This is
  unrepresentative of the population SIE will actually be run against, which is overwhelmingly
  obscure, thinly-covered companies.
- **Original tier assignments for several companies uncritically assumed the eventual outcome.**
  DoorDash was labeled "Strong" purely because it later became a category leader, without
  weighing a real, contemporaneously-visible caution signal (a flat valuation between its Series B
  and Series C). Quibi was labeled "Very Weak" pre-launch, which is itself hindsight-tainted — a
  $1.75B raise from nearly every major Hollywood studio is not "very weak" evidence at the time,
  whatever it became.

**Changes made:**
- Cut the elite/breakout cluster from 6 companies to 2 (Figma, Stripe), keeping exactly enough
  positive-control anchors to test the scoring ceiling without dominating the portfolio.
- Added five companies not on the original list, all real, sourced, but meaningfully less
  famous than the ones they supplement: **Beepi, Zenefits, Shyp, Meetup, Rdio.**
- Reclassified DoorDash from "Strong" to "Promising" based on a real, contemporaneously-visible
  signal (flat Series B→C valuation) that a disciplined at-the-time analyst should have weighed.
- Reclassified Quibi from "Very Weak" to "Average/Mixed, High Risk" — real contemporaneous
  skepticism existed, but so did an extraordinary capital commitment from sophisticated investors;
  forcing "Very Weak" pre-launch would itself be hindsight bias.
- Added **Zenefits** specifically as a hindsight-divergence stress case: at its snapshot, every
  available signal pointed Strong; the compliance scandal that later sank the company was not
  prominently visible in the sources reviewed. This is the single most important addition for
  testing whether the frozen "no hindsight" discipline actually holds up against a real case where
  investors — and by extension, a contemporaneous SIE — would plausibly have been fooled.
- Removed Meetup's originally-claimed "2011" snapshot (incorrect — its actual Series B was 2008)
  and corrected several other dates/round-labels discovered during research (see individual
  records' `benchmark_notes`).

Resulting tier distribution (20 companies): Very Weak/Failed 1, Weak 2, Average/Mixed 6, Promising
5, Strong 2, Strong/Elite 1, Elite 1, plus one special-case record (Tesla) that intentionally
doesn't map cleanly onto the standard ladder. Average/Mixed is deliberately the largest bucket,
consistent with the SPS-distribution philosophy (`SIE_Methodology_v2_Audit.md`, Part 8) that this
band should sit near the population mode for real venture-backed companies, not be a rare middle
ground.

---

## Part 2 — Historical snapshot integrity

Every record carries a specific `snapshot_date` and `snapshot_stage`. Each record's
`historical_evidence` block is restricted to facts that were publicly knowable **at or before**
that date. Anything that happened afterward — including the company's eventual fate — lives
exclusively in the separate `future_outcome` block, which is structurally isolated from
`historical_evidence` in the schema (see Part 4) so it cannot be accidentally treated as scoreable
input. Sources that are themselves retrospective (published after the snapshot date) are marked
with an explicit `note` in the `sources` array when they were used only to corroborate a fact or to
populate `future_outcome` — never as the basis for a `historical_evidence` claim about the
snapshot period itself.

---

## Part 3 — Quality tiers

Tiers were assigned by asking, for each company: *what could a genuinely skilled investor,
working only from evidence available at or before the snapshot date, reasonably have concluded?*
— not "what do we now know happened." Two records make this discipline explicit and load-bearing
rather than incidental:

- **Zenefits** is tiered **Strong (at-the-time)**, explicitly not degraded for its later scandal,
  because the scandal was not part of the contemporaneous evidence base reviewed.
- **Tesla** is tiered as a genuinely mixed special case (**Strong Thesis / Weak Near-Term
  Execution**) rather than forced onto the standard ladder, because its near-bankruptcy episode
  was real, severe, and contemporaneously visible, while its long-term thesis and already-shipped
  product were simultaneously real positive signals — collapsing this into one tier would discard
  genuine, important tension rather than resolve it honestly.

No company was tiered "Elite" or "Very Weak" purely on the strength of its eventual outcome; see
each record's `benchmark_notes.known_ambiguities` for the specific reasoning behind borderline
calls (Homejoy, Quibi, DoorDash in particular).

---

## Part 4 — Benchmark record schema

Each file under `app/benchmarks/companies/` follows this structure:

```
company_name              string
snapshot_date              ISO date — the evaluation point
snapshot_stage              string — funding stage / company phase at that date
industry                    string
business_model               string
expected_quality_tier         string — broad tier only, no numeric SPS
calibration_set              "calibration" | "holdout"

historical_evidence:          object, PRE-SNAPSHOT-ONLY facts, one field per SIE pillar
  company                      general company/founding facts
  market
  team
  product
  execution
  traction
  financial

normalized_facts:             array of {metric, value, unit, period, source, source_type,
                               confidence} — the quantifiable subset of historical_evidence,
                               using the fact schema proposed in SIE_Methodology_v2_Audit.md
                               Part 6, kept deliberately sparse: only populated where a real,
                               countable figure was found, not forced for every dimension.

sources:                      array of {title, url, published, note?} — note is used specifically
                               to flag when a source is post-snapshot and was used only for
                               future_outcome or fact cross-checking, not historical narrative.

future_outcome:                object, STRUCTURALLY SEPARATE from historical_evidence
  outcome_type
  outcome_summary
  outcome_date

benchmark_notes:
  why_included                what this record specifically stress-tests
  known_ambiguities            genuine judgment calls this record deliberately does not resolve
  evidence_limitations         what could not be found, and what that implies for expected
                                coverage/confidence on this record
```

`normalized_facts` is the schema's one addition beyond the originally requested fields, directly
incorporating the fact model designed in `SIE_Methodology_v2_Audit.md` Part 6
(`metric/value/unit/period/source/source_type/confidence`) — proposed because several records
contain genuinely countable figures (funding amounts, valuations, merchant counts, market-share
percentages) that are wasteful to leave buried in prose only, and because this is exactly the
shape a future deterministic-scoring layer would need to consume. It was kept intentionally
minimal — populated only where a real figure exists, not engineered as a required field, per the
instruction not to overengineer the schema.

**No `expected_sps` field exists anywhere in this schema**, by design — see Part 9.

---

## Part 5 — Evidence collection protocol

**Prioritized, and used:** contemporaneous funding announcements and press coverage (TechCrunch,
Forbes, CNBC, CNN Money, industry trade press), company press releases issued at or near the
snapshot date, and aggregator sites (Crunchbase, PitchBook, CB Insights) *only* when cross-checked
against or consistent with primary press coverage for the specific dollar/date figures they report.

**Avoided:** retrospective "how it all started" narrative pieces written after a company's outcome
was known, current company marketing pages (which describe present-day scale, not the snapshot
period), and unsourced aggregator claims not corroborated by any primary article.

**How this was actually enforced in practice, not just stated as a rule:** every record's
`sources` array explicitly flags any post-snapshot source with a `note` explaining why it was used
(almost always: corroborating a figure, or populating `future_outcome`) and confirming it was
**not** used to write the `historical_evidence` narrative. Several records (Homejoy, Quibi,
Instacart, Warby Parker, Airbnb) carry an explicit `benchmark_notes.known_ambiguities` or
`evidence_limitations` note flagging hindsight-leakage risk specifically, because these are
well-known companies where most current web content about them is colored by their later fame —
sourcing for those records was deliberately restricted to the specific dated announcement coverage
of the snapshot event itself, not general "history of X" content.

**Conflicting historical evidence:** none of the 20 records encountered a genuine primary-source
factual conflict (e.g., two contemporaneous sources reporting different dollar figures for the same
round) during collection. Where a figure came from a single, less-authoritative source (an
aggregator rather than a primary news article), it is marked `"confidence": "Medium"` or `"Low"` in
`normalized_facts` rather than presented with false certainty — this is the mechanism this
portfolio uses to represent evidentiary uncertainty, consistent with the Conflicting-vs-Mixed-
Evidence design frozen in `SIE_Methodology_v2_Final_Scoring_Decisions.md` Part 5. Should a genuine
conflict be found during future evidence expansion, the rule from that document applies: never
average the disagreeing figures — record both, cite both sources, and flag it explicitly.

---

## Part 6 — Portfolio construction

See `manifest.json` for the full company-by-company index, and each `companies/*.json` record for
per-company snapshot, tier, evidence-availability assessment (`benchmark_notes`), and likely-
difficult SIE dimensions. Summary of the difficult-dimension patterns across the portfolio:

- **Traction and Financial Health are the most consistently evidence-thin pillars** across nearly
  every record except Shopify, Warby Parker, and Airbnb (which have real disclosed usage figures)
  — this is intentional and representative of what SIE will actually encounter in real analyses,
  not a flaw in the portfolio.
- **Ginkgo Bioworks** is the portfolio's dedicated non-SaaS stress test — no MRR/ARR/NRR-shaped
  evidence exists for it at all, testing whether the methodology degrades gracefully for a
  fundamentally different business-model shape rather than defaulting everything to low confidence.
- **Zenefits and Quibi** are the dedicated hindsight-discipline stress tests, from opposite
  directions (an elite team with no visible red flags that later failed, versus an elite team with
  real, contemporaneously visible red flags whose outcome was genuinely uncertain either way).
- **Tesla** is the dedicated capital-intensity/hardware stress test, and the one record expected to
  produce genuinely divergent pillar scores (strong Market/Product, weak Execution/Financial
  Health) rather than a single coherent read.

No company proposed in the revised list was dropped for lack of available evidence — all 20
records were built from real, cited, dated sources. No evidence was fabricated.

---

## Part 7 — Calibration and holdout split

**15 calibration (75%) / 5 holdout (25%)**, within the requested 70-80/20-30 range.

**Holdout set:** Fab.com (Very Weak), Rdio (Average/Mixed), Homejoy (Promising, nuanced),
DoorDash (Promising, corrected from an original "Strong" hindsight-bias mislabel), Zenefits
(Strong-at-the-time, the hindsight-divergence special case).

**Why these five:** the holdout set was chosen to (a) span multiple quality tiers, not cluster in
one, satisfying the explicit requirement that both sets contain multiple quality levels, and (b)
deliberately include the single most important stress case in the whole portfolio (Zenefits) —
holding it out specifically so its result is used only to *validate* whether the frozen semantics
correctly avoid hindsight-based scoring, never to *tune* toward a desired outcome for it. The
holdout companies will not be consulted when setting anchor language, score-band thresholds,
pillar weights, or any other numeric constant during calibration — they are reserved entirely for
the final validation pass after those decisions are made from the calibration set alone.

---

## Part 8 — Success criteria (defined before any scoring)

**Directional correctness, not narrow interval-matching:**
- Failed/Weak companies (Fab.com, Beepi, Jawbone) should generally score below Strong/Elite
  companies (Stripe, Figma, Shopify, Airbnb) — a coarse, high-confidence expectation.
- Elite-tier snapshots should generally land near the top of the portfolio's own score
  distribution — not at a pre-specified numeric floor.
- Adjacent tiers (e.g., Promising vs. Average) may legitimately overlap; exact ordering within a
  tier is explicitly **not** a success criterion.
- The methodology must not systematically punish early-stage companies (Instacart, Warby Parker,
  Ginkgo) for having thin Traction/Financial-Health evidence relative to later-stage companies —
  this should be visible as appropriately handled stage-conditionality (Unavailable/excluded, not
  penalized), not as uniformly lower scores for early-stage records.
- Missing public information (the majority of Traction/Financial-Health fields across this
  portfolio) should show up as reduced confidence and coverage, never as an artificially
  suppressed quality score — directly testing the frozen decision from
  `SIE_Methodology_v2_Missing_Evidence_Adversarial_Review.md` and
  `SIE_Methodology_v2_Final_Scoring_Decisions.md`.
- High evidence availability (Shopify, Airbnb, Warby Parker) should not itself produce a higher
  score than a similarly-strong but thinner-evidenced company — it should produce higher
  *confidence*, a structurally distinct claim.
- **Zenefits specifically should score Strong at its snapshot** — a low score here would indicate
  the methodology is (incorrectly) leaking future-outcome knowledge into the scoring, which is the
  single sharpest failure this portfolio is built to catch.

**Metrics to compute once scoring exists (not computed here):**
- Tier-order accuracy — does the portfolio's overall score ranking respect the coarse tier
  ordering (Weak < Average < Promising < Strong < Elite), allowing adjacent-tier overlap.
- Pairwise ranking accuracy — for clearly-separated pairs (e.g., Fab.com vs. Stripe), is the
  higher-tier company scored higher; near-tier pairs are not held to this standard.
- Spearman rank correlation between assigned tier (ordinalized) and resulting score, computed
  portfolio-wide, as a single summary statistic — meaningful here specifically because tiers are
  ordinal, not because an exact numeric target exists.
- Score distribution shape — does Average/Mixed cluster near the population mode as the SPS
  distribution philosophy predicts, or does the methodology compress everything into a narrow
  band (the exact failure mode the Stripe diagnostic in `SIE_Methodology_v2_Audit.md` identified).
- Stage bias — do early-stage records (Instacart, Warby Parker, Homejoy, Ginkgo) score
  systematically lower than later-stage records purely as a function of stage, independent of
  tier.
- Evidence-coverage bias — does score correlate with coverage % across the portfolio in a way that
  suggests coverage is leaking into the score rather than staying confined to confidence (the
  exact defect rejected in the prior adversarial review).
- Confidence calibration — do the Weak/thin-evidence records (Beepi, Shyp, Rdio) correctly receive
  Low/Medium confidence, and do the well-evidenced records (Shopify, Airbnb) correctly receive
  higher confidence, independent of their score.

**Explicitly not a success criterion:** every company landing inside a narrow, exact SPS interval.
This portfolio validates *architecture and direction*, not point-precision.

---

## Part 9 — Expected SPS philosophy (hypotheses, not targets)

The naive ladder suggested for evaluation —

```
failed/very weak → <40
weak             → 40s
average/mixed    → 50s
promising        → 60s
strong           → 70s
exceptional      → 80s
elite            → 90+
```

— is **rejected as a rigid target** but is a reasonable *starting hypothesis for band shape*,
with one specific, deliberate challenge: **90+ should be treated as extraordinarily rare even
among this portfolio's own Elite-tier companies, not as the expected home for Figma and Stripe.**

Reasoning, consistent with the SPS distribution philosophy already established in
`SIE_Methodology_v2_Audit.md` Part 8: even Figma and Stripe's snapshots, while genuinely strong on
nearly every available signal, are missing hard revenue/NRR/margin figures at their respective
snapshot dates in the sources reviewed — meaning even the portfolio's best-evidenced "obviously
great" companies should not automatically clear a 90 threshold, because 90+ was defined
independently (before this portfolio existed) as requiring near-total, high-confidence evidence
across essentially every dimension, which even Figma and Stripe's records do not fully provide.
**If, after scoring, Figma or Stripe land in the 90s, that is itself a finding worth investigating
— it would suggest either the band definitions are too generous or the scoring is over-crediting
strong-but-incomplete evidence — not an automatic confirmation the methodology is working
correctly.** This is precisely why Part 8's success criteria are directional (does Elite rank near
the top) rather than interval-based (must land in the 80s) — the exact band edges are exactly what
calibration against this portfolio should determine, not what this document should assume in
advance.

The one band this document does assert with higher confidence, because it follows directly from
already-frozen design decisions rather than needing calibration: **Average/Mixed should be the
widest, most densely populated band**, not a narrow midpoint — consistent with both the SPS
distribution philosophy and this portfolio's own tier distribution (6 of 20 companies, the largest
single bucket, sit in Average/Mixed).

---

## Part 10 — Deliverables report

**1. Final company list (20):** Fab.com, Beepi, Zenefits, Homejoy, Jawbone, Shyp, Bonobos, Meetup,
Rdio, Oscar Health, Instacart, Warby Parker, Ginkgo Bioworks, Quibi, Airbnb, DoorDash, Stripe,
Shopify, Tesla Motors, Figma.

**2. Snapshot date/stage:** see `manifest.json` and each company's `companies/*.json` record.

**3. Quality-tier distribution:** Very Weak/Failed 1 · Weak 2 · Average/Mixed 6 · Promising 5 ·
Strong 2 · Strong/Elite 1 · Elite 1 · special-case 1 (Tesla).

**4. Industry distribution:** 15 distinct industry categories across 20 companies (e-commerce/DTC,
auto marketplace, HR/insurance SaaS, home services, wearables/hardware, on-demand logistics,
consumer/community, music streaming, grocery delivery, healthtech/insurtech, travel marketplace,
fintech infrastructure, deeptech/biotech, auto/climate hardware, design SaaS) — no single industry
holds more than 3 records.

**5. Calibration/holdout split:** 15 calibration (75%) / 5 holdout (25%); see Part 7.

**6. Benchmark schema:** see Part 4 and any `companies/*.json` record directly.

**7. Evidence collection rules:** see Part 5.

**8. Hindsight controls:** structural separation of `historical_evidence` from `future_outcome` in
every record; explicit source-level flags on any post-snapshot material; two dedicated hindsight-
divergence stress cases (Zenefits, Quibi); one corrected hindsight-bias mislabel from the original
audit (DoorDash, Strong → Promising).

**9. Success metrics:** see Part 8 — directional/tier-order/correlation-based, no narrow exact-SPS
requirement.

**10. Hypothesized SPS tier bands:** the naive 40/50/60/70/80/90 ladder as a *starting hypothesis
for band shape only*, with an explicit, standing challenge that 90+ should be rare even for this
portfolio's Elite records given real evidence gaps that persist even in its best-evidenced cases —
see Part 9.

**11. Companies rejected/replaced and why:** Databricks, Snowflake, Datadog removed (redundant
elite-tier concentration alongside Figma/Stripe); Jawbone, Fab.com, Homejoy, Instacart, Warby
Parker, Ginkgo Bioworks, Airbnb, Shopify, Tesla, DoorDash, Stripe, Figma, Oscar Health, Quibi
retained from the original list (with DoorDash's and Quibi's tiers corrected); Beepi, Zenefits,
Shyp, Meetup, Rdio added as replacements to reduce fame-concentration and add genuine failed/mixed
diversity. No company was dropped for lack of available evidence — every proposed replacement was
successfully sourced.

**12. Evidence gaps:** documented per-record in each `benchmark_notes.evidence_limitations` field.
Portfolio-wide pattern: Traction and Financial Health are the most consistently thin pillars
(expected and representative, not a defect); several funding-amount figures for older/smaller
rounds (Bonobos, Warby Parker, Meetup, Rdio) rely on aggregator sourcing rather than primary news
articles and are marked Medium/Low confidence accordingly rather than overstated.

**13. Exact files created:**
- `app/benchmarks/README.md` (this file)
- `app/benchmarks/manifest.json`
- `app/benchmarks/companies/fab_com.json`
- `app/benchmarks/companies/beepi.json`
- `app/benchmarks/companies/zenefits.json`
- `app/benchmarks/companies/homejoy.json`
- `app/benchmarks/companies/jawbone.json`
- `app/benchmarks/companies/shyp.json`
- `app/benchmarks/companies/bonobos.json`
- `app/benchmarks/companies/meetup.json`
- `app/benchmarks/companies/rdio.json`
- `app/benchmarks/companies/oscar_health.json`
- `app/benchmarks/companies/instacart.json`
- `app/benchmarks/companies/warby_parker.json`
- `app/benchmarks/companies/ginkgo_bioworks.json`
- `app/benchmarks/companies/quibi.json`
- `app/benchmarks/companies/airbnb.json`
- `app/benchmarks/companies/doordash.json`
- `app/benchmarks/companies/stripe.json`
- `app/benchmarks/companies/shopify.json`
- `app/benchmarks/companies/tesla.json`
- `app/benchmarks/companies/figma.json`

---

## Readiness

**BENCHMARK PORTFOLIO READY FOR EVIDENCE COLLECTION: YES.** All 20 records are built from real,
cited, dated sources; evidence collection for this initial pass is complete. (Further evidence
enrichment — e.g., specialist trade-press research for Zenefits per its own `known_ambiguities`
note — remains possible but is not required to proceed.)

**BENCHMARK PORTFOLIO READY FOR SCORING: NO.** No company in this portfolio has been run through
the SIE pipeline, live or otherwise, per the governing constraint of this task. Scoring readiness
is a separate, later decision requiring explicit authorization to run the pipeline — this
portfolio's construction does not itself constitute that authorization.
