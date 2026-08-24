# SIE Methodology v2 — Scoring Semantics & Missing-Evidence Design

**Status: design document only.** No code changed, no calibration run, no expected scores
changed, nothing committed. Builds on `SIE_Methodology_v2_Audit.md` and the Structural Change
Decision Memo (directionally approved, not yet implemented). This document resolves the
mathematical/semantic behavior of the methodology that must be settled *before* any structural
dimension changes are implemented.

---

## Part 1 — What a dimension score means

**Recommended interpretation: a refined version of (C), not (A) or (B) in isolation.**

- **(A) alone — "demonstrated quality based only on available evidence"** — correctly prevents
  confabulation, but taken literally it conflates "we don't know" with "it's mediocre": a company
  that simply discloses little would score low even if the *reason* for low disclosure is neutral
  (early stage, privacy norm) rather than informative of weakness. That conflation is exactly the
  failure mode the NovaLedger forensic audit and the Public Evidence Validation Consistency Fix
  were built to fight.
- **(B) alone — "estimated underlying startup quality"** — invites exactly the confabulation this
  system's entire reliability program has worked to eliminate: extrapolating a number beyond what
  the evidence actually supports.
- **(D) — combination** — true in a trivial sense, but not an actionable definition on its own.

**Recommended definition:** *A dimension score is the analyst's calibrated estimate of
investment-relevant quality on that specific dimension, strictly bounded by what the evidence
actually observed can support at face value — it is not itself discounted for the possibility
that better evidence exists elsewhere. That discounting is a separate axis (confidence), never
smuggled into the number.*

Operational test for whether a proposed score is legitimate under this definition: **if you handed
a skeptical human only the cited evidence and the rationale, would they conclude this specific
number — not a higher one, not a lower one — is the right read of *that evidence*?** If yes, the
score is legitimate regardless of how much or how little evidence exists. If the score is being
pulled down merely because there isn't *more* evidence (not because the evidence itself is
unfavorable), that is a confidence problem being misfiled as a score problem, and is exactly the
defect Part 2 below designs against.

### The five axes, defined as non-overlapping

| Axis | Answers | Independent of |
|---|---|---|
| **Score (1–10)** | "What does the cited evidence, at face value, indicate about quality?" | How much evidence exists, how reliable it is, whether more could exist elsewhere |
| **Evidence coverage (%)** | "What fraction of this dimension's defined evidence surface (its `evidence_priority` list) was actually found?" | Whether what was found was favorable or unfavorable; whether it was reliable |
| **Evidence quality** | "How credible/well-sourced is what was found?" (audited figure > founder-stated metric > inferred proxy > vague claim) | Whether the underlying fact is good or bad news for the company |
| **Confidence** | "How much should an investor trust the score that was produced?" — a function of coverage × evidence quality × source agreement × stage-appropriateness (full model, Part 8) | The company's actual quality — a company can have a reliable, high-confidence score of 2 (verified terrible metrics) or an unreliable, low-confidence score of 8 |
| **Unavailable** | A binary *state*, not a score or a confidence level: "no evidence exists to numerically anchor any score on this dimension." | — |

A concrete failure this separation prevents: today, `evidence_coverage` exists only as a
**pillar-level** aggregate (`PillarScoreBreakdown.evidence_coverage`), not per-dimension. A pillar
reporting 60% coverage could mean either "every dimension is 60% covered" or "three dimensions are
100% covered and two are 0%" — the current schema cannot distinguish these, and they mean very
different things for an investor deciding what to ask about next. **Recommend adding a per-dimension
coverage field**, not just pillar-level, as a design requirement (not implemented here).

---

## Part 2 — Missing evidence: seven cases, explicit rules

| # | Case | Score | Confidence | Unavailable | Exclude from denominator | Diligence flag |
|---|---|---|---|---|---|---|
| 1 | Evidence exists, weak (one vague signal) | **Yes** — real number, likely low, reflecting the weak evidence at face value | Low | No | No | Only if the weakness itself is notable (e.g., evasion) |
| 2 | Evidence exists, mixed (conflicting signals) | **Yes** — real number reflecting the net read; rationale must show the tension explicitly | Medium (evidence is legible even if not univocal — not automatically Low) | No | No | **Yes, always** — mixed signals are exactly what a human diligence team should be pointed at |
| 3 | Evidence exists, strong | **Yes** — high number | High | No | No | No (unless implausibly strong — separate rare "verify" flag) |
| 4 | Doesn't exist because too early (stage says not yet expected) | **No** | N/A | Yes — sub-type **"Not Yet Applicable / Stage-Excluded"** | **Yes, cleanly, no penalty** | No — this is expected, not a gap |
| 5 | Probably exists but is private | **No** | N/A | Yes — sub-type **"Private — Not Disclosed"** | From the raw score average, yes; but the pillar-level confidence/completeness signal must reflect it (Part 4) | **Yes** — "not disclosed, recommend requesting directly" |
| 6 | Should exist at this stage, cannot be found | **No** | N/A | Yes — sub-type **"Expected But Missing — Red Flag"** | **No — must NOT vanish for free** (Part 4's core fix) | **Yes, elevated severity** |
| 7 | Genuinely not applicable (business model has no such construct) | **No** | N/A | Yes — sub-type **"Not Applicable — Business Model"** | **Yes, cleanly, no penalty** | No — nothing was hidden or too-early, the construct doesn't exist |

The critical distinction the current architecture collapses: **cases 4, 5, and 7 are all legitimately
"no information," but case 6 is itself informative** (an anomaly — evidence that should exist at
this stage and doesn't is weak negative evidence on its own). Treating all four identically, as a
single generic "Unavailable → excluded from denominator," is the root of the exploit below.

### The renormalization exploit — concrete numerical proof

Take proposed v2 Traction weights (Customer Growth .25 / Revenue Growth .25 / Retention .25 /
Engagement .25) and the current renormalization rule (weights of non-null subscores rescaled to
sum to 1; null subscores simply vanish).

**Version A — honest disclosure.** A Series A company discloses NRR data showing real churn
problems. Customer Growth 8, Revenue Growth 7, Retention 3 (real, disclosed weakness), Engagement 6.

```
Pillar score = (8×.25 + 7×.25 + 3×.25 + 6×.25) = 24/4 = 6.0
```

**Version B — identical company, but Retention data simply never disclosed** (case 6: Series A,
where Retention is Expected per Part 3 — an unexplained gap, not a legitimate absence). Retention
→ Unavailable → excluded, weights renormalize over the remaining 3 dimensions to .333 each.

```
Pillar score = (8 + 7 + 6) / 3 = 21/3 = 7.0
```

**Version B scores a full point higher than Version A, for hiding a weakness rather than
disclosing it.** This is not a corner case — it is a guaranteed property of the arithmetic: removing
any below-average data point from an average always raises the average. Any dimension whose true
score would be below the pillar's post-exclusion mean is, under pure renormalization, *more*
valuable to the company's SPS when suppressed than when disclosed. This holds across every pillar
using this aggregation method, not just Traction, and it is precisely the failure mode the
question asks about — confirmed, not hypothetical.

A second, sharper version of the same proof: a pillar with **one** scored dimension at 9 and four
Unavailable renders identically to a pillar where all five dimensions scored 9 — full pillar score,
with no visible signal that four-fifths of the evidence is simply missing. This is addressed
directly in Part 4.

---

## Part 3 — Stage-conditionality matrix (11 dimensions × 4 stages)

Status legend: **Expected** (absence is anomalous) · **Optional** (absence is normal, presence is
a bonus) · **Usually private** (data likely exists but disclosure is atypical at this stage
regardless of company quality) · **Not expected** (construct not yet meaningful) · **N/A**
(structurally doesn't apply, rare at pillar-dimension level, mostly a business-model property).

| Dimension | Pre-Seed | Seed | Series A | Series B+ |
|---|---|---|---|---|
| **Leadership** | Not expected → case 4, clean exclusion, no penalty | Optional → light case 4/6 blend, minimal flag if absent | Expected → case 6 if absent, real flag | Expected → case 6, elevated severity |
| **Business Capability** *(narrowed to background/pedigree)* | Optional → score if present (even thin, e.g. "ex-VP Sales"), light exclusion if absent | Optional-leaning-Expected → light flag if absent | Expected → case 6 | Expected → case 6, elevated |
| **GTM Execution** | Not expected → case 4, clean exclusion | Optional → light case 4/6 | Expected → case 6 | Expected, but gradient toward **Usually private** (CAC/payback rarely disclosed even at scale) unless a data-room-tier evidence source is present |
| **Customer Growth** | Not expected (methodology's own text: "customers not required") → case 4, but score normally if present | Optional → light flag if absent | Expected → case 6 | Expected → case 6, elevated |
| **Revenue Growth** | Not expected ("revenue is optional") → case 4 | Optional → light flag | Expected → case 6, meaningful flag | Expected → case 6, elevated, verging on disqualifying |
| **Retention** | Not expected (rarely anything to retain yet) → case 4 | Optional (methodology's own text: "retention may be unavailable") → light case 4 | Expected ("retention is critical") → case 6 | Expected → case 6, elevated |
| **Engagement** | Not expected (no usage infra yet) → case 4; qualitative early feedback scoreable at low-medium confidence if present | Optional → light case 4/6 | Expected, telemetry-gated (no free Retention-substitution per decision memo) → case 6 if genuinely nothing | Expected → case 6, elevated |
| **Revenue Quality** *(narrowed to concentration/durability)* | Not applicable in most cases (rarely revenue yet) → case 4/7 blend | Optional → light flag | Expected → case 6 | Expected, leaning case 6 over case 5 (concentration risk is usually knowable to management even pre-disclosure) |
| **Unit Economics** | Not expected ("unit economics may be unknown") → case 4 | Optional (directional signals expected) → light case 4/6 | Expected in principle, but **Usually private** in practice (case 5 default) unless data-room evidence present | Expected, gradient case 5→6 as rounds get later/more institutional |
| **Operational Execution** | Not expected ("lightweight ops acceptable") → case 4 | Optional, but rarely externally evidenced → lean case 5 | Expected, **Usually private** (case 5 primarily) | Expected, gradient case 5→6 |
| **Execution Velocity** *(post-Part-7 redesign — see below)* | **Not Applicable — Pre-Metric** (no growth curve exists to normalize; distinct from "not expected," since it structurally cannot be computed, not merely absent) → clean exclusion, no flag; score **Execution Tempo** instead (Part 7) | Optional → compute if any growth signal exists, else clean exclusion | Expected — should almost never be genuinely missing once Customer/Revenue Growth are scored (it's derived from them); a gap here is a system-consistency check, not a company red flag | Expected, same logic |

**Rule for "scoring behavior," stated once instead of per cell:** case 4/7 cells → exclude
cleanly, no penalty, no flag (Part 2). Case 5 cells → exclude from the raw score average but count
toward a pillar-level confidence/completeness discount and generate a request-directly flag (Part
2, Part 4). Case 6 cells → do **not** vanish from the denominator; contribute a below-average
default value per Part 4's mechanism, and generate an elevated-severity flag.

---

## Part 4 — Pillar score aggregation: five approaches, stress-tested

### 1. Current weight renormalization (existing `app/ai/scoring.py` behavior)
Weights of scored subscores rescaled to sum to 1; missing subscores vanish. **Fails the exploit
test in Part 2** (6.0 honest vs. 7.0 hidden) and the single-strong-dimension test (one 9 among four
Unavailable renders identically to five 9s).

### 2. No renormalization (missing = treated as 0)
Fixes the exploit in the wrong direction: a genuinely Pre-Seed company where Retention/Engagement
are correctly Not-Yet-Applicable (case 4) would have those dimensions scored as the *worst possible
outcome* rather than excluded. Example: one real dimension at 9, four case-4-legitimate absences,
weights .25 each → `9×.25 + 0+0+0+0 = 2.25`. This would make every Pre-Seed company's Traction
pillar near-zero regardless of quality — punishing legitimate absence exactly as hard as the
version-1 exploit rewards illegitimate absence. Rejected.

### 3. Coverage-adjusted scoring (raw weighted average × a coverage-based discount factor)
Applying a modest discount (e.g., `score × (0.5 + 0.5×coverage)`) to the Part 2 exploit example:
Version A (4/4 scored, 100% coverage) stays 6.0. Version B (3/4 scored, 75% coverage, discount
`0.5+0.5×0.75=0.875`) → `7.0 × 0.875 = 6.125` — still *higher* than the honest disclosure. **A
coverage discount alone reduces but does not close the exploit**, and closing it fully would
require an aggressively steep discount curve that risks over-punishing legitimate case-4/5 absences
that carry no negative information. Coverage-adjustment is valuable as a **reported signal**, not
as the primary mechanism preventing the exploit.

### 4. Stage-specific expected-dimension denominator — **recommended primary mechanism**
Define, per Part 3's matrix, which dimensions are *expected* to be scoreable at this stage. The
denominator is drawn only from that expected set:
- **Case 4/7 dimensions** are removed from both numerator and denominator — no penalty, since they
  were never expected (this is the one place plain exclusion is correct).
- **Case 5 dimensions** are excluded from the raw score average (nothing to numerically anchor a
  score to) but do **not** silently disappear from the pillar's *reported* completeness — this is a
  reporting fix, not a scoring fix (Part 5).
- **Case 6 dimensions** (expected, unexplained absence) remain in the weighted average and
  contribute an explicit **below-average default value**, sourced from that dimension's own
  low-band anchor (e.g., near the `score_3_4` band), rather than vanishing.

Re-running the Part 2 exploit with this rule: Version B's missing Retention (Series A, Expected →
case 6) contributes a default of, say, 4.0 (a defensible "unexplained gap" floor, not zero, since
absence alone does not prove the worst outcome):

```
Pillar score = (8 + 7 + 4 + 6) / 4 = 25/4 = 6.25
```

Now **worse for the company than the honest disclosure's 6.0 is close, and Version B (6.25) is no
longer strictly better than a mid-range honest disclosure** — the incentive to hide is removed.
**The exact constant (4.0, or "score_3_4 band midpoint") is a placeholder, not a derived value — it
needs benchmark-portfolio calibration before being finalized. The mechanism (case-6 defaults to a
below-pillar-average value instead of vanishing) is the confident recommendation; the specific
number is explicitly flagged as needing real data, not invented precision.**

### 5. Bayesian / prior-based treatment
Replace the fixed case-6 default with a stage/pillar-specific prior mean (e.g., "Series A SaaS
Retention has historical population mean μ"), with pillar confidence discounted by how much
prior-substitution occurred. Strictly better than approach 4 *if* real priors exist — but they
don't yet (the 20-company benchmark portfolio is designed, not built or scored). Implementing this
today would mean inventing priors and dressing them as statistics — exactly the fake-precision risk
the task warns against. **Recommend as the explicit v3 upgrade path once real calibration data
exists, not now.**

### Recommendation
Adopt **approach 4** now (stage-aware denominator + case-6 below-average defaults), supplemented by
**approach 3's reporting value** (coverage reported transparently alongside the score, even though
it isn't the scoring mechanism) — not approach 3's discount as the primary defense. Approach 5 is
the principled future upgrade once real population data exists.

---

## Part 5 — Overall SPS semantics

The identical exploit exists one level up: if an entire pillar is Unavailable and its weight is
renormalized away across the remaining five, a pillar that would have been a genuine drag (case-6
style: expected but entirely missing) silently benefits the company exactly as in Part 4. **The
same fix pattern applies at the pillar level** — do not blanket-renormalize pillar weights;
distinguish an entirely-missing pillar that is stage-appropriate (rare — realistically only
Financial Health, for a company with genuinely $0 revenue/spend) from one that is stage-inappropriate
(a severe anomaly deserving a below-average default contribution, not silent exclusion).

**Should SPS still be produced if an entire pillar is Unavailable?** Yes — refusing all output is
unhelpful for a diligence tool — but only with the case-6-style default-contribution rule applied
at the pillar level (not renormalization), plus a mandatory, visually prominent "Incomplete
Analysis" indicator distinct from the number itself.

**Minimum evidence threshold before displaying an SPS at all?** Recommend **yes**, as a design
principle: below some floor of overall completeness (e.g., "fewer than half of the six pillars have
any scored dimensions at all"), the system should refuse to display one consolidated SPS number and
instead show only the pillars that do have data plus an explicit "insufficient evidence for an
overall score" message. **The exact threshold is a product decision, not a value this document can
derive from data that doesn't exist yet — flagging the principle as confident, the specific cutoff
as provisional.**

**SPS should be accompanied by all four of the following, kept explicitly distinct:**

| Concept | Answers | Distinct from the others because |
|---|---|---|
| **Confidence** | "If a score exists, how much should we trust it?" (Part 8) | A quality-of-*evidence* measure, not a completeness measure |
| **Evidence coverage** | "What fraction of the defined evidence surface did we actually find?" | A completeness-of-*search* measure, independent of favorability or reliability |
| **Completeness** | "Did the SIE pipeline actually attempt every pillar/dimension?" | A *pipeline-execution* measure (today near-always 100%, since every stage always runs) — kept distinct so a future partial-pipeline-failure (an API timeout skipping a whole pillar) is visibly different from a company that legitimately has no evidence for a pillar. Today's architecture conflates these because it has no failure mode that produces incompleteness; the distinction is a forward-looking design requirement, not a current gap in behavior. |
| **Diligence warnings/flags** | Discrete, human-readable action items (from Part 2's cases 2, 5, 6, and any detected internal conflict) | Never a score modifier — accompanies the number, never silently changes it |

---

## Part 6 — Weight redistribution: audited, not assumed equal

### Traction — what investment question is this pillar answering?
*"Is there real, durable commercial proof this business works, right now, given this company's
actual business model?"* Four sub-questions: is the customer base growing (Customer Growth), is
that growth becoming money (Revenue Growth), do customers stay and expand once acquired (Retention),
do customers actually derive active value rather than just remaining under contract (Engagement).

**Equal .25/.25/.25/.25 is not well justified.** Two specific problems:
1. Customer Growth and Revenue Growth are structurally coupled (via ACV — flagged in the decision
   memo as pair #8, "tolerable structural coupling," not removed). Giving both a full independent
   quarter-weight (.50 combined) risks over-weighting what is substantially one underlying growth
   signal relative to Retention and Engagement, which are more diagnostic and less correlated with
   each other.
2. Retention/NRR is widely treated by SaaS and growth-stage investors as the single most
   outcome-predictive Traction signal in practice (echoed in the methodology's own text: "retention
   can be stronger evidence of product-market fit than surface-level usage metrics") — this argues
   for weighting it *above* the other three, not equal to them.

**Proposed reallocation** (directional judgment, explicitly provisional pending the benchmark
portfolio): **Retention .30 / Revenue Growth .25 / Customer Growth .20 / Engagement .25.** Retention
elevated as the most outcome-predictive, hardest-to-fake signal; Customer Growth reduced slightly to
avoid double-weighting the growth concept alongside Revenue Growth; Engagement kept meaningful (it
catches the "zombie account" pattern nothing else in the pillar catches) rather than treated as a
minor afterthought.

### Financial Health — what investment question is this pillar answering?
*"Can this company survive and scale efficiently on the capital it has or can raise?"* Four
sub-questions: is revenue durable enough to build on (Revenue Quality), are the underlying unit
economics attractive (Unit Economics), is capital spent efficiently (Burn Efficiency), is there
enough runway to reach the next proof point (Runway).

Unlike Traction, these four are more genuinely co-equal legs of one construct — none obviously
dominates in the way Retention dominates Traction assessment. **But Runway deserves special
treatment, not because it should carry a larger linear weight alone, but because it is
qualitatively different: a critically short runway is an existential, near-term constraint that
should not be fully offset by strong scores elsewhere** (great unit economics do not fix a company
that runs out of cash in four months). This argues for a **non-linear "runway floor" rule**
alongside a modest weight increase: if Runway scores below a critical threshold (e.g., corresponding
to under ~6 months of cash), cap the whole Financial Health pillar score regardless of the other
three dimensions, rather than letting a simple weighted average dilute an existential risk into
"pretty good on average."

**Proposed reallocation:** **Runway .30 / Revenue Quality .25 / Unit Economics .25 / Burn Efficiency
.20**, plus the non-linear runway-floor cap as a supplementary rule (not a simple weight change —
flagged as a structurally different kind of recommendation, needing its own design pass before
implementation, not just a number to plug in).

Both reallocations above are **provisional and explicitly not derived from real data** — this
document proposes the *reasoning* (what question each pillar answers, why equal weighting doesn't
follow from that question) as the confident part, and the *exact numbers* as needing benchmark
validation (Part 10, item 16).

---

## Part 7 — Execution Velocity: challenging the deterministic proposal

Testing "growth rate normalized by company age" against the six specified scenarios:

- **2 → 6 customers vs. 100 → 300 customers** — both are a 3× ratio, but the first is statistically
  noise (one deal closing) and the second is a genuinely strong signal. A pure percentage formula
  with no absolute-scale/materiality floor cannot distinguish them and would score both identically.
  **This is a real, disqualifying flaw in the formula as literally stated**, not a minor tuning
  issue.
- **$100k → $300k ARR vs. $5M → $15M ARR** — same 3× ratio, but the second represents an order of
  magnitude harder operational execution challenge (real sales/CS infrastructure vs. one lucky
  contract). A pure ratio has no scale-awareness and would treat these as equivalent, which is
  wrong.
- **ARR growth vs. customer-count growth divergence** — ARR could grow 3× on flat customer count via
  expansion/upsell (a genuinely *different and arguably stronger* execution story — proof of an
  expansion motion) than the same ratio driven by new-logo growth. A single blended "velocity"
  number flattens a distinction worth keeping.
- **Pre-revenue company shipping product rapidly** — the formula is **undefined**: there is no
  growth curve to normalize. Yet execution speed (shipping cadence, iteration velocity,
  learning-loop speed) is a real, legitimate, and often *central* differentiator at exactly this
  stage. The formula doesn't fail gracefully here — it has nothing to compute, for a population
  where the underlying construct matters most.
- **Enterprise company, long sales cycles** — a single quarter or month of flat customer count
  followed by a step-change when several 9-month deals close simultaneously would read, under a
  fixed short-window normalization, as noisy/volatile rather than as the appropriate steady pace for
  that business model. A one-size-fits-all measurement window is wrong for this population.

**Conclusion: the pure deterministic formula, as proposed, fails four independent stress tests**
(materiality floor, scale-awareness, undefined for pre-revenue companies, window mismatch by
business model). This is a genuine reversal of the earlier recommendation to convert Execution
Velocity into a single deterministic dimension.

**Recommendation: split into two constructs**, not one dimension with one formula:

1. **"Growth Velocity"** (Traction-adjacent) — deterministic *when applicable*, but only once
   properly scoped: an explicit minimum absolute-scale floor below which it scores Not
   Applicable/Not Yet Meaningful rather than a number (closing the 2→6 vs. 100→300 problem), a
   business-model-aware measurement window drawn from the company's own `business_model` field
   already available in the structured analysis (closing the enterprise-sales-cycle problem), and
   explicit handling for expansion-driven vs. logo-driven growth as distinguishable inputs rather
   than one blended ratio.
2. **"Execution Tempo"** (Execution pillar) — constrained LLM, exclusively for companies where no
   growth curve exists yet (pre-revenue/pre-customer): shipping cadence, milestone frequency,
   learning-loop speed. This is the *only* scored "velocity" signal for that population, rather than
   leaving the dimension silently Unavailable at exactly the stage it matters most.

This is not a removal and not a simple deterministic conversion — it is a split, with each half
getting the architecture appropriate to the population it actually applies to.

---

## Part 8 — Confidence model

**Explicitly rejected: a numeric weighted formula** (e.g., `confidence = 0.3×coverage +
0.2×recency + ...`). This looks rigorous but isn't — the coefficients would be invented, not
derived, and would present fake precision exactly as the task warns against.

**Recommended: a simple, ordinal, rule-gated model**, keeping the existing High/Medium/Low
categorical scheme but making its inputs explicit and auditable (today this is very likely a single
undifferentiated LLM judgment call, not derived from named factors — worth flagging as a current
gap).

**Confidence = High** requires **all** of:
- Evidence coverage for this dimension meets a meaningful bar (a majority of its defined
  `evidence_priority` items found, not a single fact).
- At least one piece of **direct** (not purely inferred) evidence.
- **No unresolved conflict** between sources on a key fact.
- Evidence is **reasonably recent** relative to how fast that metric moves (a 3-year-old MRR figure
  should not support High confidence even if it was once direct evidence) — this requires the
  normalized fact model's `period` field (proposed in the structural audit, Part 6) to actually be
  populated, which is not guaranteed by today's extraction pipeline; flagging as a dependency, not
  assuming it exists.
- Evidence **meets or exceeds** what Part 3's stage-conditional matrix expects at this stage (High
  confidence should not be achievable on thin, below-expectation evidence just because it happens to
  be internally consistent).

**Confidence = Medium**: some but not all of the above hold — partial coverage, or entirely inferred
evidence with no direct anchor, or a minor unresolved gap — but nothing actively contradicts, and
real evidence exists.

**Confidence = Low**: a single weak signal, entirely inferred with no direct anchor, actively
conflicting sources, or meaningfully stale evidence.

**Unavailable is never a confidence level** — restating Part 1's core distinction, since collapsing
"very low confidence" and "Unavailable" into each other is precisely the ambiguity this whole
document exists to remove.

---

## Part 9 — Ten adversarial scenarios

For each: what SIE **should** conclude, and which Part 1–8 mechanism the scenario specifically
tests.

1. **Brilliant pre-seed startup, almost no measurable traction.** Traction mostly Not-Yet-Applicable
   (case 4) — excluded without penalty; the read should lean on Market/Team/Product's thesis-level
   dimensions. *Tests: does stage-conditional exclusion (Part 3/4) actually prevent early-stage
   traction absence from tanking the score the way a Series A gap would.*
2. **Mediocre startup, extremely complete public data.** High coverage/confidence, but mediocre
   scores — completeness of evidence must never be mistaken for quality of evidence. *Tests whether
   score and coverage/confidence stay properly decorrelated (Part 1's central claim).*
3. **High-growth startup, terrible retention.** Growth dimensions score high, Retention scores low,
   and the tension must generate an explicit "growth masking a retention problem" flag rather than
   being smoothed into one comfortable-looking average. *Tests whether the mixed-signal flag (Part 2,
   case 2) fires for genuinely dangerous tension, not just decoratively.*
4. **Low-growth startup, exceptional retention.** Should not automatically read as weak — this can be
   a legitimately good, capital-efficient, under-marketed or niche business; Market Size/Growth
   should carry the "ceiling vs. GTM problem" question, not Traction's growth dimensions alone.
   *Tests whether the methodology avoids treating growth as the only thing that matters.*
5. **Differentiated product, no moat.** Differentiation scores well, Defensibility scores poorly —
   the divergence *is* the finding ("interesting today, easily replicated"). *Directly validates the
   decision memo's reversal to keep Differentiation and Defensibility separate rather than merged.*
6. **Defensible product, brutal incumbent competition.** Defensibility scores well, Competitive
   Intensity scores poorly/moderately — a real moat does not guarantee a win against incumbent
   distribution power (the Betamax pattern). *Validates keeping Competitive Intensity distinct from
   Defensibility.*
7. **Capital-efficient company growing slowly.** Financial Health dimensions score well; Traction
   scores modestly; the overall read should credit this as a genuinely different, sometimes very
   fundable profile rather than automatically "weak." *Surfaces a downstream question: Financial
   Health's lower pillar weight (0.10) vs. Traction's (0.15) structurally disadvantages this profile
   by design — worth flagging to the pillar-weight owners even though PILLAR_WEIGHTS is out of scope
   here.*
8. **High-burn company growing extraordinarily fast.** Growth dimensions score high; Burn Efficiency
   must be scored on its own independent evidence (growth-per-dollar-spent) and should **not**
   inherit a high score merely because growth is impressive. *Tests whether growth-dimension
   strength inappropriately leaks into Burn Efficiency's judgment — a cross-pillar version of the
   double-counting discipline from the decision memo.*
9. **Elite founders, weak current execution.** Founder-Market Fit/Technical Capability (background,
   Team) score high; Execution Track Record/Product Execution/GTM Execution (outcomes) score
   low/mixed — this divergence is a legitimate, important finding ("great pedigree, hasn't yet
   translated into results"), not a contradiction to be smoothed away. *Directly validates the
   decision memo's "capability vs. did-it-happen" boundary discipline.*
10. **Unknown founders, extraordinary execution.** Founder-Market Fit may legitimately score low or
    Unavailable (nothing to cite — correctly, not punitively); Execution Track Record/Traction/Product
    Execution should score high — results should not be dragged down by pedigree's high (.25) weight
    within Team. *Tests whether the methodology can recognize "results override pedigree," avoiding
    structural credentialism bias.*

---

## Part 10 — Final recommendation

1. **Dimension score definition:** the analyst's calibrated estimate of investment-relevant quality
   on that dimension, strictly bounded by what the observed evidence supports at face value —
   never discounted for the possibility that more evidence exists elsewhere (that's confidence's
   job).
2. **Confidence definition:** how much to trust a score that was produced — an ordinal, rule-gated
   High/Medium/Low derived from coverage, direct-vs-inferred evidence, source agreement, recency,
   and stage-appropriateness (Part 8) — never a numeric formula, never a proxy for company quality.
3. **Evidence coverage definition:** the fraction of a dimension's defined evidence surface that was
   actually found — a completeness-of-search measure, independent of favorability or reliability;
   needs a **per-dimension**, not just per-pillar, field.
4. **Unavailable definition:** a binary state ("no evidence exists to anchor any score"), never a
   confidence level, with four sub-types (Not Yet Applicable/Stage-Excluded, Private—Not Disclosed,
   Expected But Missing—Red Flag, Not Applicable—Business Model) that must be handled differently at
   aggregation time (Part 2/4).
5. **Missing-evidence decision rules:** the seven-case table in Part 2 — case 6 (expected but
   missing) is the only case that should not vanish for free; cases 4 and 7 should vanish cleanly;
   case 5 should vanish from the raw score but not from reported completeness.
6. **Stage-conditional matrix:** Part 3's 11×4 table — status varies meaningfully by
   dimension/stage; "Unavailable" alone is never a sufficient description of the behavior.
7. **Pillar aggregation design:** stage-aware expected-dimension denominator (Part 4, approach 4) —
   case-4/7 dimensions excluded cleanly; case-6 dimensions contribute a below-average default
   instead of vanishing. Exact default constants need benchmark calibration.
8. **SPS aggregation design:** the identical fix applied one level up across pillars (Part 5); SPS
   still produced when a pillar is entirely missing, but with the same default-contribution logic
   plus a mandatory "Incomplete Analysis" indicator.
9. **Minimum evidence requirements:** a hard floor below which no single SPS number is displayed —
   principle recommended, exact threshold explicitly left as a product decision pending real data.
10. **Recommended Traction weights (provisional):** Retention .30 / Revenue Growth .25 / Customer
    Growth .20 / Engagement .25 — not equal, because Retention is the pillar's most
    outcome-predictive signal and Customer/Revenue Growth are structurally coupled.
11. **Recommended Financial Health weights (provisional):** Runway .30 / Revenue Quality .25 / Unit
    Economics .25 / Burn Efficiency .20, plus a non-linear "runway floor" cap rule — Runway is
    qualitatively different (existential/near-term) from the other three, not just a fourth equal
    input.
12. **Execution Velocity decision:** **not** a single deterministic dimension as originally proposed
    — split into "Growth Velocity" (deterministic-when-applicable, with a materiality floor and
    business-model-aware window) and "Execution Tempo" (constrained LLM, for pre-revenue companies
    where no growth curve exists to compute from).
13. **Adversarial-test findings:** all ten scenarios (Part 9) map to a specific mechanism from Parts
    1–8; each is a direct test of a decision-memo reversal or a Part 1–8 design choice, not a
    generic stress test — several (5, 6, 9, 10) specifically validate *not* merging dimensions the
    original audit proposed merging.
14. **Remaining unresolved methodology questions:**
    - Exact numeric defaults for case-6 penalty-floors (Part 4) and the minimum-evidence display
      threshold (Part 5) — both explicitly deferred to benchmark-portfolio calibration.
    - Whether Financial Health's structurally lower pillar weight (0.10 vs. Traction's 0.15)
      appropriately or inappropriately disadvantages capital-efficient, slow-growth companies
      (scenario 7) — a PILLAR_WEIGHTS-level question, out of scope for this document but surfaced
      for the weight owners.
    - Whether the "runway floor" non-linear cap (item 11) should generalize to any other dimension
      with existential/threshold characteristics, or is genuinely unique to Runway — not analyzed
      here.
    - Whether per-dimension evidence coverage (item 3) and fact-level recency tracking (Part 8) are
      feasible with the current evidence-extraction architecture without a larger schema change.
15. **Methodology v2 structural changes now safe to implement** (from the prior decision memo, none
    of which depend on unresolved numeric constants above): the retags (Market Size, Market Growth,
    Market Timing, Unit Economics), the single-line evidence-leak fixes (Usability↔Retention,
    Execution Track Record↔Founder-Market Fit), removal of Commercial Validation, demotion of
    Fundraising Readiness to an unscored flag, and the seven-cluster evidence-boundary narrowings
    (Differentiation/Defensibility/Competitive Intensity; Business Capability/GTM; Execution Track
    Record; Operational Execution; Strategic Execution; Customer Demand; Adoption Potential) — these
    are all evidence-scoping changes, independent of the aggregation-math questions this document
    raises.
16. **Changes that must wait for benchmark calibration:** the case-6 penalty-floor default values
    (Part 4), the minimum-evidence display threshold (Part 5), the exact Traction and Financial
    Health weight numbers (Part 6 — the *reasoning* is confident, the *numbers* are not), the
    Growth Velocity materiality floor and window parameters (Part 7), and confirmation that the
    Differentiation/Defensibility/Competitive Intensity evidence partition actually decorrelates
    scores in practice rather than just relocating the correlation (carried over from the decision
    memo).
