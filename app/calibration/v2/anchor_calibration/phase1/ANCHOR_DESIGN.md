# Methodology v2 — Numerical Anchor Calibration, Phase 1

Diagnostic design document. The canonical specification is NOT modified in this phase. Nothing
here is frozen; everything is a proposal pending review. Architecture, weights, dimension
definitions, missing-evidence semantics, confidence semantics, and ranking logic are all
unchanged — this phase only proposes evidence-to-score conversion functions for dimensions PASS B
showed cannot currently execute numerically.

---

## Part 1 — Growth Velocity

**What it measures, numerically:** an annualized, business-model-scale-aware growth *rate* —
distinct from Customer Growth's more literal "does this series look healthy for the stage" read.
Two companies with identical percentage growth at different absolute scales should NOT receive the
same score, because sustaining a given percentage growth rate becomes objectively harder (and more
economically meaningful) as the base grows.

**Architecture — three steps:**

1. **Materiality floor gate.** If the *starting* value (or, for a very young metric, the ending
   value) sits below the business-model-appropriate floor defined in Part 2/3's family tables, the
   dimension is structurally **Not Applicable** — not scored, not defaulted, not penalized. A
   2→6-customer jump is excluded here, categorically, regardless of its 200% growth rate: a base of
   2 is not economically meaningful evidence for any business model in these families.

2. **Annualize the rate.** Compute CAGR = `(end/start)^(1/years) − 1` using the *actual* measurement
   window in years, not raw percentage growth. This makes a 6-month window and a 3-year window
   comparable and prevents a short-window spike from being scored as if it were a sustained rate.
   Windows shorter than ~2 quarters are usable but flagged lower-confidence, since a single-quarter
   read is more exposed to one-off noise.

3. **Scale-tiered CAGR-to-score bands.** Bucket the *starting* scale into the same
   business-model-aware tiers used for Customer Growth/Revenue Growth (Part 2/3), then apply a
   CAGR band appropriate to that tier — the required CAGR to reach a given score band is
   **highest at the smallest (post-floor) tier and lowest at the largest tier**:

   | Scale tier (illustrative, SaaS/platform customer-count family) | Weak (3-4) | Credible (5) | Strong (6-7) | Exceptional (8-10) |
   |---|---|---|---|---|
   | Tier 1 — near-floor | CAGR <50% | 50–150% | 150–400% | >400% |
   | Tier 2 — small | CAGR <35% | 35–100% | 100–250% | >250% |
   | Tier 3 — medium | CAGR <20% | 20–60% | 60–150% | >150% |
   | Tier 4 — large/at-scale | CAGR <15% | 15–40% | 40–100% | >100% |

   Each business-model family (Part 2) gets its own tier boundaries in absolute-scale terms; the
   CAGR bands above are the *shape* that transfers across families, not the absolute tier cutoffs.

**Stress-test walkthrough:**

| Case | Materiality floor | Tier | CAGR (illustrative window) | Result |
|---|---|---|---|---|
| 2 → 6 customers | **Fails floor** | — | — | Not Applicable — never scored, regardless of the 200% growth rate |
| 100 → 300 customers | Clears (consumer/SMB) | Tier 1–2 | depends on window | Strong-to-exceptional *only* at the small-tier bar, which is deliberately high |
| 1,000 → 3,000 customers | Clears | Tier 2–3 | same 200% growth | Scores **higher** than the 100→300 case at the same 200% rate, because Tier 2–3's bar for "exceptional" is lower — correctly rewards harder-to-sustain growth at larger scale |
| $100k → $300k ARR | Clears (small-B2B floor) | Tier 1–2 | 200% | Strong, not automatically exceptional — small-base percentage swings are dampened |
| $5M → $15M ARR | Clears easily | Tier 4 | 200% | **Exceptional** — 200% CAGR at $5M+ ARR is genuinely rare and is scored as such |
| Identical % growth, radically different scale | — | — | — | Deliberately scored differently by design (see $100k/$5M rows above) — this is the central design goal, not an edge case to patch |
| Very high growth from a trivial base | Usually fails the floor, or lands in Tier 1 where the bar is highest | — | — | Dampened or excluded, never rewarded as equivalent to large-scale growth |
| Slower growth from a large base (e.g. $5M→$6M, 20% CAGR) | Clears | Tier 4 | 20% | **Credible (5)**, not penalized — Tier 4's own bar treats 15–40% as a real, valuable signal |

**Simplest defensible architecture, stated plainly:** floor-gate → annualize → scale-tiered bands.
No other inputs are needed. Anything more elaborate (e.g. weighting by category-specific growth
norms, competitive benchmarking) would add precision the historical evidence in this portfolio
cannot support and risks overfitting to the one company (Shopify) that actually tests it.

---

## Part 2 — Customer Growth (business-model-aware anchors)

**Core principle: "customer count" is not one thing.** Before any threshold is applied, the anchor
system must first ask whether customer count is even the *appropriate unit* for the business model.

| Family | Is customer count the right primary unit? | Floor (illustrative) | Small tier | Medium tier | Large tier | Notes |
|---|---|---|---|---|---|---|
| **Enterprise SaaS** | Weak primary — a handful of large logos can matter more than raw count | ~10 logos | 10–50 | 50–200 | 200+ | Logo count should be paired with revenue-per-logo when available; count alone is directional only |
| **SMB SaaS / platform** | **Strong primary** — economics scale roughly linearly with count | ~500–1,000 | 1k–10k | 10k–100k | 100k+ | Shopify's merchant count is the canonical example of this family |
| **Consumer** | Primary, but needs a high floor to escape noise/virality artifacts | ~10,000 | 10k–100k | 100k–1M | 1M+ | Below the floor, apparent growth is often statistically meaningless |
| **Marketplace** | **Ambiguous unit** — must specify demand-side vs. supply-side; a single undifferentiated "customer" figure is not defensible | ~10,000 (demand side) | — | — | — | Prefer transacting-buyer count or GMV as primary; raw participant count as supporting only |
| **Commerce/DTC** | Primary (unique buyers or units sold) | ~1,000 | 1k–10k | 10k–100k | 100k+ | Lower floor than consumer software given lower per-purchase stakes/frequency |
| **Insurance** | **Weak primary alone** — policyholder count without premium/risk context is close to meaningless | ~1,000 policies | — | — | — | Should be paired with premium volume or loss-ratio evidence; count alone supports only a capped, low-confidence read |
| **Hardware/manufacturing** | Primary (units shipped/sold), floor depends heavily on price point | ~50–100 (high-ticket) to ~5,000–10,000 (low-ticket) | — | — | — | No single floor across the family — must be set per price tier |
| **Deeptech / partnership-driven** | **Often the wrong unit entirely** | N/A | — | — | — | Program/partnership count or contract value is the appropriate unit; a raw "customer count" reading should default to Not Applicable rather than be forced |

**Scoring:** once the family and floor are established, apply the same annualized-CAGR,
scale-tiered band logic as Growth Velocity (Part 1) — Customer Growth and Growth Velocity share a
conversion mechanism but answer slightly different questions (Customer Growth: does this series
look healthy for the company's stage; Growth Velocity: how does the rate itself compare once
normalized). They are expected to produce close-but-not-identical scores on the same evidence — see
the Shopify simulation in Part 8.

---

## Part 3 — Revenue Growth (stage-aware anchors)

Same floor-gate → annualize → scale-tiered-band architecture as Growth Velocity, applied to a
revenue metric instead of a count metric, with three additional rules specific to revenue:

1. **Metric consistency is mandatory.** Two revenue-shaped figures may only be compared if they are
   the *same* metric (e.g., both net revenue, both GAAP revenue, both ARR) measured the *same* way.
   A gross-transaction-value figure and a net-take-rate figure — even both "revenue-ish" — are not
   comparable and must not be forced into a rate calculation (this is not a hypothetical: it is
   exactly the Beepi 2014-net-fee-revenue vs. 2015-gross-transaction-value case, which correctly
   stays unscored).
2. **Sequential vs. YoY:** prefer YoY or CAGR-annualized comparisons over raw sequential
   (quarter-over-quarter) growth, which is far more exposed to seasonality; a sequential figure may
   be used only with an explicit seasonality caveat and a confidence discount.
3. **Scale tiers (illustrative, general B2B/platform revenue):**

   | Tier | Floor | Range |
   |---|---|---|
   | Tier 1 — very early revenue | ~$25k ARR/annualized | $25k–$250k |
   | Tier 2 — small | | $250k–$2M |
   | Tier 3 — meaningful scale | | $2M–$20M |
   | Tier 4 — large | | $20M+ |

   Same CAGR-band shape as Growth Velocity's table (high bar at Tier 1, low bar at Tier 4): high
   percentage growth from a tiny base (e.g. $25k→$75k, 200%) is dampened relative to the same 200%
   from a $20M base, which would be scored exceptional.

**Applied to this portfolio:** no company has a clean, same-metric, two-point revenue series in the
permitted evidence (Shopify's is GMV, explicitly distinct from revenue; Beepi's two figures are
non-comparable metrics; Meetup has only one point within the permitted window). Revenue Growth
therefore remains **0/15 scoreable even after this anchor design** — an honest result, not a
shortfall of the design (see Part 8).

---

## Part 4 — Unit Economics: business-model-specific evidence-to-score families

One dimension, six evidence families. Each family defines primary metrics (required for anything
above a capped/low-confidence read), supporting metrics (strengthen or weaken a primary-metric-based
read but cannot alone produce one), and explicit insufficient combinations.

| Family | Primary metric(s) | Supporting metric(s) | Weak (1-2) | Credible (5) | Strong (6-7) | Exceptional (8-10) | Explicitly insufficient |
|---|---|---|---|---|---|---|---|
| **SaaS/subscription** | Gross margin, CAC payback, LTV:CAC (FROZEN, unchanged from the prior repair) | Net revenue retention | margin<50% or payback>24mo | margin 50-70%, payback 12-24mo | margin 70-80%, payback 6-12mo, LTV:CAC 2-3x | margin>80%, payback<12mo, LTV:CAC>3x (FROZEN) | A stated business-model description with no margin/payback figures at all |
| **Marketplace/take-rate** | Take rate combined with **at least one** cost-side or margin-sustainability signal | Gross-vs-net revenue distinction, category-typical-take-rate context | Take rate disclosed as declining/under competitive pressure with no offsetting signal | Take rate within a stated-normal range for the category, no cost data | Take rate above category norm **and** an explicit statement of positive/improving contribution margin | Rare in early-stage evidence; would require quantified, positive per-unit contribution margin | **Take rate alone, with zero cost-side or sustainability signal** (revenue-capture rate is not the same question as unit profitability) |
| **Insurance/underwriting** | Loss ratio or combined ratio (quantitative) | Explicit, company-specific qualitative loss/margin-trend disclosure | Explicit disclosure of "significant losses" or a stated combined ratio >100% with no improvement signal | No score is assigned by default (this is a Deterministic-style dimension; ambiguity should return Unavailable, not neutral) | Loss ratio in a normal range, or explicit trend toward improvement | Loss/combined ratio disclosed below typical thresholds, or explicit "approaching/at breakeven underwriting" language | Generic industry commentary not specific to the company |
| **Hardware/manufacturing** | Per-unit gross margin | Manufacturing-cost trajectory, component-cost disclosures | Explicit negative per-unit margin, or a stated structural cost problem | Margin data absent | Positive, disclosed per-unit margin at a normal level for the category | Disclosed margin materially above category norm with a stated durability reason (e.g. vertical integration) | A structural design/thesis claim with no realized margin evidence |
| **Commerce/DTC** | Realized gross margin or disclosed price-point advantage vs. a named incumbent's cost structure | Value-chain-compression thesis (supporting only) | Explicit disclosure of thin/negative margin | Margin data absent | Disclosed margin structurally favorable to a stated incumbent comparison | Quantified margin advantage with disclosed figures | **A stated intent/thesis to bypass a cost structure, with no evidence the thesis is actually realized** — intent is not outcome |
| **R&D-partnership/deeptech** | Disclosed program fee, contract value, or program-level economics | Program/partner count, deal-structure description | Explicit disclosure of below-typical program economics | Program-economics data absent | Disclosed program fees/contract terms at a normal-or-better level for the category | Multiple large, disclosed program contracts with favorable terms | **Zero program-economics disclosure of any kind** (the common case for early deeptech companies) |

**Applied to this portfolio (Part 8 detail):** only **Oscar Health** clears its family's bar
(insurance/underwriting: an explicit, company-specific, dated disclosure of "significant
underwriting losses as the company scaled" satisfies the qualitative-fallback requirement). Beepi
(take-rate alone, no cost signal), Warby Parker (thesis, not outcome), Ginkgo and Quibi and Shyp and
Instacart (no qualifying evidence under any family) remain correctly unscored — the anchor families
do not manufacture scores where the evidence genuinely doesn't support one.

---

## Part 5 — Burn Efficiency (Hybrid anchors)

**A. Quantitative anchor (preferred when both inputs exist):** burn multiple = net burn ÷ net new
ARR (or the closest available growth-output metric), over a consistent trailing window.

| Burn multiple | Score |
|---|---|
| >5x | Clearly poor (1-2) |
| 3-5x | Weak (3-4) |
| 2-3x | Credible (5) |
| 1.5-2x | Strong (6-7) |
| <1x | Exceptional (8-10) |

This is a standard, widely-used startup-finance heuristic, not a number invented for this portfolio.
**It is unused by all 15 companies** — none has both a burn figure and a growth-output figure in the
same period within permitted evidence. Flagged honestly as a defined-but-currently-inert anchor.

**B. Qualitative fallback bands** (used only when strong direct evidence exists — never from
ambiguous or hedged source language):

| Band | Score | Evidence required |
|---|---|---|
| Clearly poor | 1-2 | Documented crisis directly attributable to spend: emergency financing required to continue operating, or workforce cuts explicitly driven by cash constraints |
| Weak | 3-4 | Explicit, company-specific, non-hedged disclosure that costs/losses are growing materially faster than the value created (e.g. explicit "significant losses...as it scaled" language, or a large committed pre-revenue spend plan with no demand validation) |
| Credible | 5 | An explicit signal that spend appears reasonably matched to milestones, with no crisis and no inefficiency language — **not** a default for absent evidence |
| Strong | 6-7 | Credible, disclosed evidence of spend control or efficiency improvement while maintaining progress |
| Exceptional | 8-10 | Disclosed burn multiple <1x, or explicit "profitable/near-profitable while scaling" language |

**Explicit exclusions (do not qualify, regardless of band):** a large fundraise in isolation; a
fundraising shortfall without a stated cause; any source language the record itself flags as
ambiguous or two-directional (Jawbone's, Meetup's own self-described ambiguity). **Runway boundary:**
Burn Efficiency asks "is spending efficient," never "how long until cash runs out" — cash-position
and months-of-runway evidence belongs exclusively to Runway (Part 6), even when it appears in the
same source passage.

---

## Part 6 — Runway (Hybrid anchors)

**A. Quantitative anchor (preferred):** months of runway = cash on hand ÷ monthly net burn.
FROZEN linear bands (already established in the prior spec repair, formalized here): <6mo=1-2,
6-12mo=3-4, 12-18mo=5, 18-24mo=6-7, >24mo=8-10. **Unused by all 15 companies** — none has both a
cash figure and a burn-rate figure simultaneously (Tesla has cash, not burn rate; no other company
has either).

**B. Qualitative fallback bands:**

| Band | Score | Evidence required |
|---|---|---|
| Clearly poor, unresolved | 1 | Documented near-insolvency with the crisis still open as of the snapshot date |
| Clearly poor, just addressed | 2 | Documented near-insolvency **and** emergency financing that closed at or immediately before the snapshot date, with no disclosed resulting cash/burn figures — fragility demonstrated, immediate crisis addressed but resilience unproven |
| Weak | 3-4 | A direct, non-hedged claim about financing inadequacy (not merely a shortfall vs. an ambition, and not source-flagged ambiguous language) |
| Credible | 5 | An explicit, direct claim that financing position is adequate-but-unremarkable — not a default for absent evidence |
| Strong | 6-7 | Concrete, credible evidence of committed access to capital beyond ordinary equity that is not yet drawn (e.g. an institutional revolving credit facility) |
| Exceptional | 8-10 | Explicit, quantified cash reserves disclosed as large **relative to a known, disclosed burn rate or spend plan** — not a large raise viewed in isolation |

**Explicit rule: fundraising amount alone never implies financial health.** A $1B raise with a
disclosed $600M/year spend plan and no revenue (Quibi) does NOT qualify for Strong/Exceptional under
this system — the disclosed spend plan actively works against, not for, a "substantial reserves"
read, and the case doesn't cleanly fit Weak/Poor either (no direct adequacy claim). It stays
unscored, by design, not by oversight.

---

## Part 7 — Universal 0-10 scale mapping

Every anchor family above is expressed directly in the frozen universal semantics (0=reserved for
disqualifying findings only; 1-2 materially weak; 3-4 below expectations; 5=stage-relative-neutral;
6-7 good; 8-9 very strong/exceptional; 10=extraordinary/reserved) — no family introduces its own
0-10 meaning. The design goal throughout is **same evidence pattern → same score logic**, not
**known company → desired score**: every band above is defined by the *shape and directness* of the
evidence required, before any specific company's evidence was matched against it. Part 10 documents
the overfitting check performed on each threshold.

---

## Part 9 — Tier effect (see `tier_effect_analysis.json` for the full numeric comparison)

Applying these anchors to the 15 companies' frozen evidence changes exactly **one SPS value**
(Shopify: 63.2 → 63.4) and **one pillar's coverage without changing its score** (Oscar Health's
Financial Health: coverage 25%→50%, score unchanged at 3.0, because the newly-added Unit Economics
evidence happens to corroborate rather than contradict the existing Burn Efficiency read). No new
inversions are created; no existing inversion is resolved; the portfolio's SPS range (50.9-67.0) is
unchanged. Traction pillar coverage improves modestly (2/15 → 3/15 companies with any Traction
score). This is a small, evidence-driven effect, not a benchmark-fit-driven one — every anchor
decision above was justified on economic/methodological grounds *before* being checked against this
portfolio (see Part 10), and the resulting benchmark effect is reported here only as a
consequence, never as the reason for a threshold choice.

---

## Part 10 — Overfitting guard

Every numeric threshold above was tested against: *"Would I defend this threshold if the company
names and expected tiers were hidden?"*

- **Growth Velocity/Customer Growth/Revenue Growth CAGR bands:** defensible as stated — they draw on
  well-known startup-growth-benchmark shapes (higher bar at larger scale), not on Shopify's specific
  48.6% CAGR. **Not provisional**, but the *absolute scale-tier cutoffs* (e.g., "10k-100k = medium"
  for SMB SaaS) are illustrative and should be checked against a broader company sample before
  freezing — flagged **provisional on the exact tier boundaries**, not on the architecture.
- **Unit Economics family definitions:** defensible — built from standard, publicly-documented
  unit-economics concepts per industry (SaaS margin/payback/LTV:CAC, insurance loss ratios,
  marketplace take rates), not reverse-engineered from any of the 15 companies' actual numbers.
  **Not provisional.**
- **Burn Efficiency/Runway quantitative anchors (burn multiple, months-of-runway bands):**
  standard, externally-documented startup-finance heuristics. **Not provisional**, though genuinely
  untested against this portfolio (0/15 usage) — their validity rests on external convention, not
  on any evidence from this dataset.
- **Burn Efficiency/Runway qualitative bands:** the band *shapes* (poor/weak/credible/strong/
  exceptional, gated on directness of evidence) are defensible in the abstract. **However, the
  exact score-within-band choices already made in the targeted PASS A rerun (Tesla=1/2, Oscar
  Health=3, Quibi=3, Stripe=7) were single-analyst judgments, not independently re-derived here —
  flagged explicitly as provisional pending a second analyst or a larger crisis-case sample**, per
  the PASS B finding that already identified this exact gap.
- **Insurance/underwriting qualitative-disclosure threshold** (allowing "significant losses...as it
  scaled" to score, without a number): this is the newest, least-tested judgment call in this whole
  document. I would defend it blind (a direct, dated, company-specific disclosure is meaningfully
  different from a vague narrative), but flag it **provisional** — it is the specific threshold that
  newly unlocked Oscar Health's score, and a threshold that unlocks exactly one company's evidence
  deserves the most scrutiny before being treated as settled.

---

## Part 11 — Evidence-reuse issue (analysis only — no safeguard implemented)

**Classification: primarily correlated-dimension amplification arising from evidence scarcity, with
a genuine legitimate-multi-dimensional-evidence component — not excessive reuse from sloppy
allocation, and not a prompt/evidence-allocation bug.**

The two concrete cases (Tesla's crisis narrative touching 7 dimensions; the new Oscar Health
Unit-Economics/Burn-Efficiency double-citation of the same underwriting-loss disclosure) both involve
evidence that is *genuinely, independently relevant* to each dimension it touches under the current
dimension definitions — this is not evidence being stretched to fill gaps. The problem is structural:
when a single dominant historical fact is the *only* substantial evidence available for a company,
its legitimate relevance to N dimensions mechanically concentrates that one fact's influence across
N/28 of the weighted score, in an aggregation architecture that implicitly assumes dimension
judgments are drawn from materially independent evidence.

**Possible future safeguards (proposed, not implemented, not evaluated for adoption):**

1. **Evidence-fact tagging with a correlation discount** — tag each dimension's citation with a
   normalized reference to its underlying source fact(s); when multiple dimensions for one company
   cite the same fact, discount their combined effective weight proportionally. Highest-fidelity
   option; highest implementation complexity; risk of penalizing companies whose evidence is
   concentrated but still genuinely multi-relevant.
2. **A transparency-first "concentrated evidence" flag** — surface (not mathematically adjust) any
   company where a disproportionate share of scored dimensions trace to one underlying event,
   analogous to the existing Partial Structural Coverage display state. Lower risk, lower fidelity.
3. **Independent-citation requirement with a confidence penalty** — if a dimension's evidence
   citation duplicates another dimension's citation for the same company, cap that dimension's
   confidence rather than adjusting its score. Uses machinery that already exists (the confidence
   field) rather than adding new math.
4. **Automatic second-review trigger** — flag any company where one event drives more than a stated
   share of scored dimensions for mandatory secondary review before its SPS is treated as final.

No recommendation is made among these; this is deliberately left as an open design question for a
future, separately-authorized turn.
