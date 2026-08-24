# SIE Methodology v2 — PASS B Diagnostic Report

**Diagnostic only. No methodology, weight, anchor, or code change was made in this pass.**
Canonical scores (targeted-PASS-A-rerun where revised, else original PASS A) were finalized and
written to disk before `expected_quality_tier` was read for the first time — see
`run_metadata.json` for the exact provenance chain. Holdout companies (Fab.com, Rdio, Homejoy,
DoorDash, Zenefits) were never opened. `future_outcome` and `benchmark_notes` were never read.

---

## Part 1 — Revealed tiers and distribution

| Bin (constructed) | Companies | Count |
|---|---|---|
| Elite | Figma | 1 |
| Strong | Stripe (*Strong/Elite*), Shopify, Airbnb | 3 |
| Promising | Ginkgo Bioworks (*Promising/High-Uncertainty*), Instacart, Warby Parker | 3 |
| Average | Shyp, Quibi, Oscar Health (all *Average/Mixed*), Bonobos, Meetup | 5 |
| Weak | Jawbone, Beepi | 2 |
| Special-Stress | Tesla Motors (*Strong Thesis/Weak Near-Term Execution*) | 1 |

The benchmark's own labels are frequently hedged/compound (`Average/Mixed`, `Promising/
High-Uncertainty`, Tesla's explicit `special stress case` framing) — the portfolio was evidently
*not* built to produce clean, confident tier assignments, which matters for how hard any given
inversion should be read (see Part 10).

## Consolidated table (canonical, sorted by SPS)

| Company | Snapshot | Stage | SPS | Pillars scored | Coverage | Flags | PSC | Expected tier |
|---|---|---|---:|---:|---:|---:|---:|---|
| Stripe | 2016-11-25 | Series D | 67.0 | 5/6 | 42.9% | 11 | 1 | Strong / Elite |
| Figma | 2020-04-30 | Series D | 66.9 | 5/6 | 42.9% | 10 | 1 | Elite |
| Shopify | 2013-12-12 | Series C | 63.2 | 4/6 | 35.7% | 13 | 2 | Strong |
| Ginkgo Bioworks | 2017-12-14 | Series D | 63.1 | 4/6 | 32.1% | 14 | 2 | Promising / High-Uncertainty |
| Airbnb | 2011-07-24 | Series B | 62.6 | 5/6 | 32.1% | 13 | 1 | Strong |
| Instacart | 2013-07-10 | Series A | 61.0 | 4/6 | 39.3% | 13 | 2 | Promising |
| Warby Parker | 2011-09-20 | Series A | 60.9 | 4/6 | 35.7% | 14 | 2 | Promising |
| Shyp | 2015-04-21 | Series B | 58.1 | 4/6 | 32.1% | 15 | 2 | Average / Mixed |
| Quibi | 2019-10-03 | Pre-launch | 57.6 | 5/6 | 42.9% | 7 | 1 | Average / Mixed, High Risk |
| Oscar Health | 2016-02-22 | Series C | 53.6 | 4/6 | 25.0% | 17 | 2 | Average / Mixed |
| Jawbone | 2014-09-15 | Series F-eq. | 53.0 | 4/6 | 35.7% | 12 | 2 | Weak |
| Bonobos | 2012-04-12 | Growth rd. | 52.8 | 4/6 | 35.7% | 13 | 2 | Average |
| Beepi | 2015-12-15 | Series C | 51.7 | 3/6 | 21.4% | 17 | 3 | Weak |
| Meetup | 2008-07-23 | Series B | 51.6 | 5/6 | 28.6% | 15 | 1 | Average |
| Tesla Motors | 2009-05-19 | Strategic rd. | 50.9 | 5/6 | 50.0% | 10 | 1 | **Strong Thesis / Weak Near-Term Execution** |

("PSC" = number of pillars entirely suppressed, i.e. Partial Structural Coverage count.)

---

## Part 2 — Ordinal discrimination

- **Cross-tier pairwise concordance: 91 comparable pairs (Tesla excluded, held off the linear
  ladder), 5 inverted → 94.5% concordant.**
- **No severe inversions.** All 5 are boundary-adjacent and small: the largest is 1.4 points
  (Jawbone over Meetup) on a 0–100 scale; two of the five are 0.1-point effective ties.
- **Tier means/medians (see `inversion_analysis.json` for the full ladder):**

| Tier | n | mean | median | min | max |
|---|---:|---:|---:|---:|---:|
| Elite | 1 | 66.90 | 66.90 | 66.9 | 66.9 |
| Strong | 3 | 64.27 | 63.20 | 62.6 | 67.0 |
| Promising | 3 | 61.67 | 61.00 | 60.9 | 63.1 |
| Average | 5 | 54.74 | 53.60 | 51.6 | 58.1 |
| Weak | 2 | 52.35 | 52.35 | 51.7 | 53.0 |
| Special-Stress | 1 | 50.90 | 50.90 | 50.9 | 50.9 |

- **Adjacent-tier mean gaps:** Elite→Strong 2.6, Strong→Promising 2.6, **Promising→Average 6.9**
  (the one genuinely wide gap in the whole ladder), Average→Weak 2.4, Weak→Special 1.5.
- **Overlap:** Strong's range (62.6–67.0) fully contains Elite's single value (66.9). Promising's
  range (60.9–63.1) overlaps Strong's bottom (Ginkgo 63.1 vs. Airbnb 62.6). Average's range
  (51.6–58.1) fully contains Weak's range (51.7–53.0). Only the Promising/Average boundary shows
  clean separation with no overlap.
- **Within-tier dispersion is comparable to or larger than between-tier separation** at every
  boundary except Promising→Average — e.g. Average's own spread (6.5 points) exceeds its 2.4-point
  gap from Weak's mean. This is the core of the compression finding in Part 4.

**Bottom line: SIE ranks higher-quality historical snapshots above lower-quality ones correctly in
the large majority of cases (94.5% concordance, zero severe inversions), but tier *boundaries* are
not crisply separated — adjacent tiers overlap almost everywhere except one boundary.**

---

## Part 3 — Company-level disagreement analysis

Two inversions are large enough to be worth a full trace; the other three (≤0.2 points) are noted
briefly as measurement noise. Tesla, though not a ladder inversion, gets the deepest trace because
it is the most informative single finding in this pass.

### Jawbone (Weak, 53.0) > Meetup (Average, 51.6) — gap 1.4

- **SPS → pillars:** Jawbone: Market 5.25, Team **6.33**, Product 4.56, Execution 5.0 (Traction/FH
  suppressed). Meetup: Market 4.0, Team 5.44, Product 5.0, Execution 6.0, **Financial Health 6.0**
  (Traction suppressed).
- **Pillars → dimensions:** Jawbone's Team score leans on "shipped multiple product generations"
  (speakers, then wearables), which the original PASS A analyst *explicitly flagged as reused*
  across Technical Capability (7), Execution Track Record (6), and Product Execution (6) — one fact
  populating three nominally-independent dimensions. Meetup, by contrast, is the only company in
  the entire portfolio with real, dated, disclosed monthly cash sales ($558,576) and a working
  organizer-subscription revenue model (85% of income) — genuinely rare, hard financial evidence —
  yet this only reaches the *Financial Health* pillar, which carries just a 0.10 weight.
- **Evidence:** Jawbone also has real, direct *negative* evidence (19% vs. Fitbit's 68% market
  share) that correctly drags Competitive Intensity to 3 — but this is one of five Market
  sub-dimensions and gets diluted by Market Size (6) and Market Growth (6).
- **Root cause classification: C (evidence reuse inflating Team/Execution) + K (legitimate
  ambiguity — neither label is clearly wrong on frozen evidence) + F (possible Market Size
  dimension-definition overlap with "is this venture-scale," discussed further at Meetup below).**
- Note on the benchmark label itself: Meetup's own Market Size dimension was scored 4/10 on real,
  direct evidence ("a genuinely useful, durable niche... not an obviously venture-scale category
  ceiling"). Whether a *market-size* dimension should independently penalize "not venture-scale" —
  a judgment that arguably belongs to the overall investment recommendation, not one Market
  sub-dimension — is a legitimate open question, not a scoring bug. Flagged for later definitional
  review, not a proposed fix here.

### Ginkgo Bioworks (Promising, 63.1) > Airbnb (Strong, 62.6) — gap 0.5

- **Pillars:** Ginkgo Team 6.81 vs. Airbnb Team 5.75; both Product/Execution close (6.0 vs 6.44/6.0).
- **Dimensions:** Ginkgo's Team pillar is driven by genuinely distinct, well-evidenced facts —
  Founder-Market Fit 8 (five MIT PhDs, explicit domain-relevant credentials), Technical Capability 8
  (platform ambition), Business Capability 4 (real, explicit negative: "has this team commercialized
  a platform business before remained an open question"), Execution Track Record 7 (sophisticated
  investor syndicate) — not an artifact of reuse. Airbnb's Team pillar, by contrast, has only 2 of 5
  dimensions scored (Founder-Market Fit and Execution Track Record); Technical Capability, Business
  Capability, and Leadership are all Unavailable because the 2011-era contemporaneous press record
  simply didn't carry founder-background detail the way Ginkgo's 2017 academic-credential coverage
  did.
- **Root cause classification: F (a real evidence-availability bias — academically-credentialed
  deeptech founders are more easily documented in contemporaneous press than founders whose
  domain-fit is real but not credential-shaped) + K (legitimate ambiguity — a 0.5-point gap between
  a "Strong" and a "Promising/High-Uncertainty" label is genuinely close).** This is a real,
  reportable finding, not a scoring bug — worth tracking as calibration work continues, since it
  could systematically favor pedigree-heavy teams over unconventional ones purely as a function of
  what got written about them at the time.

### The three negligible cases (≤0.2 points)

Jawbone > Bonobos (+0.2), Beepi > Meetup (+0.1), Stripe > Figma (+0.1) — all effectively ties.
Stripe/Figma is additionally explained by Stripe's own label straddling `Strong/Elite`. Not traced
further; treating a 0.1-point gap as a meaningful disagreement would be fabricating precision the
scale doesn't have.

### Tesla Motors — the most important finding in PASS B (not a ladder inversion, but scores below the entire Weak tier)

- **SPS 50.9 — the lowest in the portfolio — despite having the HIGHEST overall evidence coverage
  of any of the 15 companies (50.0%, vs. a portfolio median of 35.7%).** This single fact rules out
  "sparse evidence" as the explanation for Tesla's score; the opposite is true — Tesla has *unusually
  abundant* evidence, and that evidence is genuinely negative.
- **Trace:** The November 2008 – May 2009 near-bankruptcy episode (~$9M cash, 18% workforce cut,
  emergency $40M convertible debt, "crucial" $50M Daimler rescue) is real, well-sourced, and
  legitimately relevant to Leadership (3), Execution Track Record (6, framed positively — shipped
  despite adversity), Product Execution (5), **Operational Execution (2)**, Strategic Execution (6,
  the Daimler deal), **Burn Efficiency (1)**, and **Runway (2)** — seven dimensions, all drawing at
  least partly on the same underlying narrative.
- **This is a genuine finding, distinct from ordinary evidence-reuse:** when one dramatic historical
  event is the dominant available fact for a company, the weighted-average architecture — which
  assumes reasonably independent dimension judgments — mechanically amplifies that single
  narrative's influence across roughly a quarter of the company's total weighted score. The Burn
  Efficiency/Runway Hybrid-mode repair (this session's prior turn) is *what made this visible*: under
  the old pure-Deterministic mode, Burn Efficiency and Runway were silently excluded, and the crisis
  narrative's influence was smaller.
- **Is the ranking wrong?** On frozen-snapshot evidence, Tesla in May 2009 had a real *shipped*
  product (rare in this portfolio), real paying customers who pre-paid deposits, and a credible new
  strategic partnership — arguably stronger Product/Team evidence than either Weak-tier company
  (Beepi, Jawbone) had. Placing Tesla below both is a legitimate methodology observation worth
  surfacing, not obviously "correct" just because the underlying facts are severe.
- **Root cause classification: I (aggregation behavior — non-independent evidence reused across
  many weighted dimensions, mechanically amplifying one narrative) + K (legitimate ambiguity about
  whether a "special stress case" company belongs on the same linear scale as ordinary snapshots at
  all).** This is NOT evidence the benchmark label is wrong (see Part 10) — the label itself already
  anticipates this ambiguity by flagging Tesla as a special case.

---

## Part 4 — Compression diagnosis

**Answer: a combination, dominated by (5) sparse evidence and (3) missing anchors for the
Deterministic Traction/Financial-Health dimensions, with a secondary (6) aggregation-renormalization
effect. NOT primarily (4) constrained-LLM compression.**

Evidence for ruling out LLM-behavior compression as the primary cause: dimension-level scores from
Constrained-LLM-mode dimensions show real spread *wherever evidence exists* — Leadership ranges 3
(Tesla) to 9 (Quibi); Differentiation ranges 4 (Jawbone) to 8 (Figma/Tesla); Competitive Intensity
ranges 3 to 7. The LLM-driven dimensions are not the flattening force.

Evidence for sparse evidence + missing anchors as the dominant cause:
- **Retention: 0/15 scored, anywhere, ever.** **Growth Velocity: 0/15 scored** despite one company
  (Shopify) having genuinely clean, real, dated evidence blocked purely by a missing conversion
  function. **Customer Growth and Revenue Growth: 0/15 scored.** The entire five-dimension
  Deterministic core — designed to be the methodology's most objective, most discriminating layer —
  contributes *nothing* to any of the 15 companies' scores in this run.
- **Traction pillar: fully suppressed for 13 of 15 companies (87%).** Financial Health: fully
  suppressed for 10 of 15 (67%) even after the targeted repair (down from 14/15 pre-repair).
- Across all 420 dimension-instances scored in PASS A/targeted-rerun, sub-3 scores are extremely
  rare (only Tesla's Operational Execution=2, Burn Efficiency=1, Runway=2, and Bonobos'/Meetup's
  Competitive Intensity/Market Size=3-4 approach that range) — most scored dimensions cluster
  4–8, consistent with sparse-but-real evidence producing moderate rather than extreme judgments,
  not with an LLM refusing to differentiate.
- **Aggregation:** when 1–3 of 6 pillars are silently excluded per company, the remaining pillars'
  weights renormalize upward — mathematically correct and unbiased, but it means every company is
  effectively scored on a different, inconsistent subset of the intended methodology, which narrows
  the achievable range by construction, independent of any single weight being wrong.

**CALIBRATION problem, not a STRUCTURAL methodology problem.** The pillar architecture, weight
structure, and missing-evidence rules are behaving exactly as designed. They are being fed a
historically evidence-sparse portfolio and lack numeric anchors (Growth Velocity's conversion
function, non-SaaS Unit Economics anchors, qualitative Burn Efficiency/Runway bands) that would let
more of the real available evidence convert into scores. No redesign is indicated by this finding —
see Part 12, item 15 for the explicit verdict.

---

## Part 5 — Pillar discrimination

| Pillar | Availability (Elite→Special) | Mean by tier | Obvious inversions | Discriminates? | Compressed? | Missingness-dominated? |
|---|---|---|---|---|---|---|
| **Market** | 15/15 (100%) all tiers | 6.25 / 6.37 / 6.08 / 5.12 / 5.25 / 5.50 | Strong's mean (6.37) slightly exceeds Elite's single value (6.25) — n=1 artifact, not a pattern | Yes, in the upper half; weak in the lower half (Average/Weak/Special cluster 5.1–5.5) | Lower-half only | No — full coverage |
| **Team** | 15/15 (100%) all tiers | 6.50 / 6.24 / 5.91 / 5.66 / 5.29 / 5.12 | None material; smooth monotonic decline | Yes — cleanest monotonic trend of any pillar | Mild at the bottom (Weak≈Special) | No |
| **Product** | 15/15 (100%) all tiers | 7.62 / 6.26 / **6.44** / 5.62 / 5.28 / 7.00 | **Promising's mean (6.44) exceeds Strong's (6.26)** — real, n=3 each, not noise | Moderate — real signal, one real inversion | Mild | No |
| **Execution** | 14/15 (93%) | 7.00 / 6.67 / 6.28 / 6.25 / 5.00 / 4.33 | Promising≈Average (6.28 vs 6.25) — negligible | Yes, reasonably monotonic; correctly places Tesla lowest | Mild | Mostly no (only Beepi's Execution fully suppressed) |
| **Traction** | **2/15 (13%)** | 6.00 / 7.00(n=1) / — / — / — / — | Uncomputable — 13 of 15 companies have zero data | **Contributes essentially nothing** | N/A | **Yes — completely dominated by missingness** |
| **Financial Health** | **5/15 (33%)** | — / 7.00(n=1) / — / 4.00(n=3) / — / 1.55(n=1) | None — where available, the pattern is *sharply and correctly* ordered (Stripe 7.0 > Meetup 6.0 > Oscar Health/Quibi 3.0 each > Tesla 1.55) | **The single sharpest discriminator in the methodology when available** | **No — the opposite: least compressed of any pillar** | **Yes — availability, not scoring quality, is the problem** |

**Traction and Financial Health, as instructed, get special attention:** neither pillar should be
read as "not working" — the *scoring*, where evidence exists, is fine (Financial Health is in fact
the best discriminator in the entire methodology). The problem is exclusively that historical public
evidence for these two pillars is rare in this portfolio, especially pre-2015. This is a coverage
finding, not a reason to remove either pillar, per the explicit instruction.

---

## Part 6 — Dimension discrimination

**Strongly discriminative** (real, evidence-grounded spread where scored):
- **Competitive Intensity** (3–7 across the portfolio, well-populated, 11/15)
- **Differentiation** (4–8, well-populated, 10/15)
- **Leadership** (3–9, but only 2/15 scored — high signal, very low coverage)
- **Burn Efficiency / Runway where scored** (1–7, but only 5/15 combined — see Part 5)

**Weakly discriminative / compressed despite good coverage:**
- **Market Size** (15/15 scored, but 13 of 15 land in a tight 5–7 band; only Meetup's explicit
  "not venture-scale" evidence produces a real outlier at 4)
- **Customer Value** (mostly 5–7, thin spread despite near-full availability)
- **Founder-Market Fit** — the neutral-default convention (score 5 when evidence is genuinely
  silent, not negative) produces a visible cluster of exact 5s across the portfolio (Airbnb,
  Beepi, Bonobos, Figma, Shopify, Meetup all score exactly 5), which is methodologically correct
  behavior but mechanically compresses this dimension's apparent variance.

**Excessively unavailable (near-zero coverage):**
- Retention (0/15), Growth Velocity (0/15), Customer Growth (0/15), Revenue Growth (0/15) —
  the entire Deterministic core, see Part 4/8.
- Go-to-Market Execution — almost always `usually_private_unavailable` (CAC data is structurally
  rare in historical public sources); only Bonobos, Meetup, Shyp scored.
- Leadership (2/15), Business Capability (sparse), Usability (sparse — Stripe 8, Shyp 6, Warby
  Parker 7 are nearly the only scored instances), Operational Execution (sparse — Instacart 6,
  Tesla 2 stand out as nearly the only scored instances).

**Suspiciously influential / redundant (evidence-reuse risk):**
- **Tesla's crisis narrative**, reused across Leadership, Operational/Product/Strategic Execution,
  Burn Efficiency, and Runway — the standout case (see Part 3).
- **Jawbone's "shipped multiple product generations"** fact, reused across Technical Capability,
  Execution Track Record, and Product Execution — self-flagged by the original PASS A analyst.
- **Technical Capability vs. Product Execution** show a structural redundancy *risk* even where the
  definitions are conceptually sound ("can they" vs. "did they, how well") — in practice, when the
  only available evidence is "they built and shipped a complex thing" (Ginkgo, Tesla, Jawbone,
  Figma), both dimensions end up scored from the same single fact, viewed from two angles rather
  than two independently corroborated ones.

**No dimension was found to be simply "noisy" (random/unexplainable variance) — every scored value
traces cleanly back to a specific, citable piece of evidence.** This is itself worth reporting: the
compression and inversion patterns above are evidence-availability and evidence-reuse artifacts, not
signs of erratic scoring behavior.

---

## Part 7 — Coverage/confidence interaction (critical section)

**Question: are low-evidence SPS values simply less reliable, or is the quality scoring itself
systematically wrong?**

**Finding: low-evidence SPS values are less reliable — there is no evidence the scoring logic
itself is systematically wrong.**

- Portfolio median `overall_coverage_pct` = 35.7%.
- **4 of the 5 inversion pairs involve at least one company below the portfolio median coverage**
  (Meetup 28.6%, Ginkgo 32.1%, Airbnb 32.1%, Beepi 21.4% — Jawbone sits exactly at the median,
  35.7%). The two negligible (0.1-point) "inversions" among well-covered companies (Stripe 42.9%,
  Figma 42.9%) are true ties, not real disagreements.
- **Market-pillar confidence is "Low" for 3 of the 4 companies central to the two real inversions**
  (Jawbone, Meetup, Ginkgo); Airbnb's Market confidence is "Medium," but Airbnb's overall thinness
  (only 2 of 5 Team dimensions scored, 3 fully Unavailable) is the better explanatory factor there.
- **The cleanest counter-example supporting this conclusion is Tesla:** the company with the
  *highest* coverage (50.0%) produces the *most extreme* score in the portfolio (50.9, lowest
  overall) — precisely because that score rests on unusually abundant, high-confidence, well-sourced
  evidence (much of it "High"-confidence), not thin or ambiguous evidence. High coverage there
  produces a confidently extreme, defensible result, not noise.
- **Beepi and Oscar Health** — the two lowest-coverage companies in the portfolio (21.4% and 25.0%)
  — both land in tier-consistent positions (Weak and Average respectively) despite their thinness.
  Their placement is correct, but it should be read as *fragile-correct* rather than *robustly*
  correct: a handful of different evidence draws could plausibly move either company's score by
  several points without changing the underlying facts.

**Practical conclusion for future work: coverage and confidence are meaningful reliability signals
that should be surfaced alongside SPS (which the SPS display architecture already does via coverage%
and pillar confidence) — the disagreements observed in PASS B are concentrated in the
low-coverage/low-confidence half of the portfolio, not spread evenly, which is exactly what a
well-functioning (if evidence-starved) methodology should look like.**

---

## Part 8 — Anchor calibration candidates

See `anchor_calibration_candidates.json` for the full structured registry. Summary, in priority
order:

1. **Growth Velocity / Customer Growth / Revenue Growth** — missing rate-to-score conversion
   function; single highest-leverage fix (one conversion function likely unlocks all three).
2. **Unit Economics, non-SaaS families** — 7 companies have real evidence blocked purely by missing
   family-specific anchors; Financial Health's proven-sharpest-discriminator status makes this a
   high-value target.
3. **Burn Efficiency / Runway qualitative severity bands** — functioning directionally, but the
   exact numbers chosen in this rerun have no FROZEN check against them; needs either a
   second-analyst cross-check or a larger crisis-case sample.
4. **Retention** — flagged separately: likely a structural evidence-era limitation, not a fixable
   anchor gap, for a historical portfolio this old.

No new numeric thresholds are proposed here, per instruction.

---

## Part 9 — Weight diagnosis

**No weight change is currently justified by PASS B evidence.**

- Pairwise rank-order concordance is 94.5% with zero severe inversions — there is no clear empirical
  signal that any pillar or dimension weight is producing systematically wrong rankings.
- The Execution pillar's recently-frozen equal .25/.25/.25/.25 weighting (from the prior spec
  repair) shows a clean, reasonably monotonic tier trend in this data (Elite 7.0 > Strong 6.67 >
  Promising 6.28 ≈ Average 6.25 > Weak 5.0 > Special 4.33) — no evidence surfaced here to challenge
  that recent, deliberately conservative decision.
- **Financial Health's low pillar weight (.10) sits in real tension with its status as the sharpest
  available discriminator** — but this is a *worth-watching* observation, not a justified change:
  the .10 weight was a considered decision reflecting the pillar's endemic evidence scarcity, and
  PASS B's own finding is that the scarcity (not the weight) is the active constraint. Revisit once
  Financial Health coverage materially improves via anchor calibration (Part 8, priority 2) — not
  before.
- **Traction's .15 weight is functionally inert for 87% of this portfolio**, but again this traces
  to evidence absence, not to the weight itself being conceptually wrong.
- Per the explicit instruction against overfitting: none of these observations rises to "clear
  conceptual AND empirical reason" for a change on a 15-company sample. Flagged for attention, not
  acted on.

---

## Part 10 — Benchmark-label challenge

Every one of the 15 tiers was reviewed against the frozen snapshot text alone (no future outcome
consulted). **No label appears clearly wrong or unsupported.** Several labels are already
hedged/compound in ways that show real benchmark-design discipline (Tesla's explicit "special stress
case" framing, "Average/Mixed," "Promising/High-Uncertainty") — the benchmark was evidently built to
resist overconfident labeling, which is worth noting explicitly rather than assuming the labels are
naive ground truth to be defended.

**One mild, non-decisive candidate worth surfacing:** **Bonobos ("Average")**. The frozen record
shows a fairly uncommon, real positive signal — a major incumbent retailer (Nordstrom) choosing to
both *invest in* and *nationally distribute* the product, a landmark strategic validation not seen
elsewhere in this portfolio — that could plausibly support "Promising" instead of "Average." This is
presented as a defensible alternative reading, not an assertion that the existing label is wrong.

**Airbnb ("Strong," not "Elite") and Instacart ("Promising," not "Average" or "Strong") both read as
appropriately conservative given only what was knowable at their respective snapshot dates** (real,
contemporaneously-known regulatory/legitimacy risk for Airbnb in 2011; genuine single-city, pre-
revenue thinness for Instacart in 2013, offset by a specific, credible domain-expert investor
signal) — neither looks like it needed hindsight to justify.

**No label was silently forced to match SIE's score, and no score was adjusted to match a label** —
the two real inversions found in Part 3 (Jawbone/Meetup, Ginkgo/Airbnb) were traced to specific
methodology/evidence causes and reported as such, not resolved by re-arguing the benchmark.

---

## Part 12 — Final diagnosis

**1. Final SPS ranking (highest to lowest):** Stripe (67.0) · Figma (66.9) · Shopify (63.2) ·
Ginkgo Bioworks (63.1) · Airbnb (62.6) · Instacart (61.0) · Warby Parker (60.9) · Shyp (58.1) ·
Quibi (57.6) · Oscar Health (53.6) · Jawbone (53.0) · Bonobos (52.8) · Beepi (51.7) · Meetup (51.6) ·
Tesla Motors (50.9).

**2. Expected tier for each:** see the consolidated table above.

**3. Tier-level SPS statistics:** see Part 2 table (means 66.90 / 64.27 / 61.67 / 54.74 / 52.35 /
50.90 for Elite/Strong/Promising/Average/Weak/Special-Stress).

**4. Cross-tier inversions:** 5 of 91 comparable pairs (5.5%), 94.5% concordance.

**5. Most severe inversion:** Jawbone (Weak, 53.0) over Meetup (Average, 51.6), a 1.4-point gap —
still not severe in absolute terms. No inversion anywhere exceeds 1.4 points.

**6. Rank-order discrimination assessment: Good.** SIE ranks higher-quality historical snapshots
above lower-quality ones in the large majority of cases, with no severe inversions and a clear,
mostly-monotonic tier-mean trend.

**7. SPS compression: mostly cosmetic, with one caveat.** Ordinal ranking works; adjacent-tier
boundaries overlap in raw SPS terms almost everywhere except Promising→Average. This is compression
of *scale*, not failure of *ranking* — but it does mean SPS point-values alone (without the
coverage/confidence context already displayed) would overstate precision at tier boundaries.

**8. Top 10 scoring/calibration problems, in priority order:**
  1. Deterministic growth dimensions (Growth Velocity/Customer Growth/Revenue Growth) — 0/15
     scored, missing conversion function.
  2. Traction pillar suppressed for 13/15 companies.
  3. Financial Health suppressed for 10/15 companies despite being the sharpest available
     discriminator.
  4. Non-SaaS Unit Economics anchors missing for 7 companies with real evidence.
  5. Burn Efficiency/Runway qualitative severity bands unvalidated against a second analyst.
  6. Tesla's single-narrative evidence reuse across 7 dimensions, mechanically amplifying one crisis
     story's weight in the aggregate.
  7. Jawbone's evidence-reuse (shipped-generations fact) across Team/Execution dimensions.
  8. Team-pillar credential-availability bias (academically-credentialed founders more easily
     evidenced than unconventional ones — Ginkgo vs. Airbnb).
  9. Market Size dimension possibly conflating "large market" with "venture-scale opportunity"
     (Meetup case).
  10. Retention structurally near-unusable for pre-2015 historical snapshots — likely permanent for
      older benchmarks, not a calibration target.

**9. Dimensions most needing anchor calibration:** Growth Velocity / Customer Growth / Revenue
Growth (highest leverage) > non-SaaS Unit Economics families > Burn Efficiency/Runway severity
bands. (Retention explicitly excluded — evidence-era limitation, not an anchor problem.)

**10. Pillars performing well:** Team (cleanest monotonic trend, full coverage), Market (strong in
the upper half, full coverage), Financial Health (sharpest discrimination wherever available —
performing *very* well qualitatively, just rarely available).

**11. Pillars performing poorly (on coverage, not on scoring quality):** Traction (13/15
suppressed), Financial Health (10/15 suppressed, despite item 10 above — both true at once: excellent
when present, absent most of the time).

**12. Impact of evidence coverage:** Real and directionally consistent — 4 of 5 inversions involve
below-median-coverage companies; the highest-coverage company (Tesla) produced the most extreme,
best-evidenced score in the portfolio.

**13. Impact of confidence:** Real but secondary to raw coverage — Low Market-pillar confidence
co-occurs with 3 of the 4 companies central to the two real inversions, but overall pillar thinness
(count of scored dimensions) is the stronger predictor than the confidence label alone.

**14. Benchmark labels that should be challenged:** None decisively. Bonobos ("Average") is the one
mild, defensible alternative-reading candidate (arguably "Promising" given the Nordstrom deal). No
other label looks unsupported by the frozen snapshot.

**15. Structural methodology defect revealed: NO.** Every finding in this pass traces to evidence
sparsity, missing numeric anchors, or evidence-reuse across dimensions that are individually
well-defined — not to a wrong pillar architecture, a wrong missing-evidence framework, or a wrong
aggregation rule. The one aggregation-adjacent finding (Tesla's cross-dimension evidence reuse) is a
real phenomenon worth further thought, but it is a consequence of thin historical source material
concentrating around one event, not a flaw in the weighted-average mechanism itself.

**16. Weight change currently justified: NO.** See Part 9 — no pillar or dimension weight has both
a clear conceptual and a clear empirical case for change; two items (Financial Health's weight,
Team's credential-availability bias) are flagged as worth revisiting once anchor calibration
improves coverage, not acted on now.

**17. Is anchor calibration alone likely sufficient?** **Likely yes, for the near term.** The
dominant problems identified (Parts 4, 7, 8) are coverage- and anchor-shaped, not architecture-
shaped. The one item that isn't a pure anchor problem — evidence reuse across nominally-independent
dimensions (Tesla, Jawbone) — doesn't require redesigning dimensions; it's a reasoning-discipline
issue for the scoring process, addressable by evidence-attribution guidance rather than a structural
change.

**18. Exact recommended scope of the next calibration step:** Numeric anchor calibration limited to
the four items in Part 8, prioritized in the order given (growth conversion function → non-SaaS Unit
Economics anchors → Burn Efficiency/Runway severity bands), explicitly excluding Retention. This
should be done against a broader evidence base than these 15 companies alone, to avoid overfitting
anchors to this specific calibration set — consistent with Part 9's overfitting guard.

---

### Verdicts

**PASS B COMPLETE: YES**
**HOLDOUT QUARANTINE PRESERVED: YES**
**FUTURE OUTCOMES REMAIN BLINDED: YES**
**METHODOLOGY REMAINED FROZEN DURING PASS B: YES**
**STRUCTURAL REDESIGN REQUIRED: NO**
**READY FOR NUMERICAL ANCHOR CALIBRATION: YES**

No calibration was performed. No future outcome was revealed. No holdout was scored. No methodology
change was made. No commit was made.
