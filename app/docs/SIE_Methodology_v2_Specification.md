# SIE Methodology v2 — Canonical Specification

**Status: THE authoritative specification.** Not a design exploration, not a proposal — this
document consolidates and, wherever it conflicts with an earlier design document, **supersedes**
`SIE_Methodology_v2_Audit.md`, `SIE_Methodology_v2_Scoring_Semantics.md`,
`SIE_Methodology_v2_Missing_Evidence_Adversarial_Review.md`,
`SIE_Methodology_v2_Final_Scoring_Decisions.md`, the Structural Change Decision Memo (delivered in
conversation only, never persisted as a file), and the Calibration Execution Readiness Review. Those
documents are not deleted or edited — they remain historical design records, and Part 13 below
indexes exactly what this specification changed or resolved relative to each of them. **Where any
prior Methodology v2 document conflicts with this one, this document wins.**

No production code modified by writing this document. No benchmark record modified. No holdout
company inspected or scored. No calibration run. Nothing committed. This is specification only.

Canonical pillar weights (out of scope for this document, unchanged): Market **.20**, Team **.20**,
Product **.20**, Execution **.15**, Traction **.15**, Financial Health **.10**.

---

## Part 1 — Source-of-truth hierarchy

1. **This document** — canonical, current.
2. `SIE_Methodology_v2_Final_Scoring_Decisions.md` — canonical on every point it addresses that this
   document does not explicitly revise (ranking architecture, SPS-range rejection, the
   disclosure-risk narrow trigger, mixed-vs-conflicting definitions).
3. `SIE_Methodology_v2_Missing_Evidence_Adversarial_Review.md` — canonical on the rejection of the
   below-average-default mechanism; superseded on anything Final Scoring Decisions later revised.
4. `SIE_Methodology_v2_Scoring_Semantics.md` — canonical only where not contradicted by documents
   2–3 above or this document; its below-average-default language (Parts 3, 4, 10) is explicitly
   **dead** — see Part 4 below and Part 13's supersession table.
5. The Structural Change Decision Memo (conversation-only) — canonical on the 7 "narrow, don't
   merge" dimension-boundary decisions and the Commercial Validation/Fundraising Readiness
   dispositions; **its content is now fully absorbed into Part 2 and Part 7 of this document**,
   closing the durability gap the Readiness Review flagged (a decision that only ever existed in
   conversation history is no longer load-bearing on its own — this document is its permanent home).
6. `SIE_Methodology_v2_Audit.md` — the original 30-dimension audit; canonical only for material
   never revisited by anything above (e.g., the benchmark-portfolio design, the SPS-distribution
   philosophy). Its Part 1 merge/remove recommendations for the 9 dimensions later kept separate are
   **dead** — see Part 13.
7. Calibration Execution Readiness Review — not a design document; it is the diagnostic that this
   specification exists to resolve. Its findings are addressed point-by-point throughout.

---

## Part 2 — Canonical dimension architecture

### Execution Velocity: resolved

Re-running the six stress tests against each option:

- **(A) One "Execution Velocity" dimension** — fails all four previously-identified stress tests
  (no materiality floor, no scale-awareness, undefined pre-revenue, wrong window for long sales
  cycles). **Rejected**, confirmed.
- **(B) Two dimensions (Growth Velocity + Execution Tempo)** — the Scoring Semantics proposal.
  Re-examined here against **Product Execution's existing evidence scope**, which already includes
  *"roadmap velocity"* as a named evidence-priority item (Audit doc Part 1, item 17). A standalone
  "Execution Tempo" dimension for pre-revenue companies (shipping cadence, iteration speed,
  milestone frequency) would score from evidence that is **already inside Product Execution's own
  definition** — the same evidence-duplication pattern the Structural Change Decision Memo spent
  its entire review eliminating, now reappearing between two Execution-pillar dimensions instead of
  across pillars. **Rejected on conceptual-integrity grounds**, not merely to preserve a dimension
  count.
- **(C) Only Growth Velocity survives, rescoped** — **ADOPTED.** Growth Velocity is a derived,
  Traction-shaped construct (a normalized rate computed from Customer Growth and Revenue Growth
  facts), not an Execution-pillar construct (which asks about company *behavior/capability* — GTM
  motion quality, delivery quality, operational discipline, strategic soundness — not about the
  *rate of change* of an outcome those behaviors produce). It is **moved into the Traction pillar**
  as a fifth dimension. For pre-revenue companies, where Growth Velocity is structurally N/A (no
  growth curve exists to normalize), the execution-speed signal that a separate "Tempo" dimension
  would have tried to capture is **absorbed into Product Execution's existing "roadmap velocity"
  evidence-priority item** — no new dimension required, no evidence duplicated.
- **(D) Only Execution Tempo** — rejected; discards the deterministic-when-applicable signal Growth
  Velocity provides for the majority of companies that do have growth data, in favor of keeping only
  the harder-to-reproduce LLM-judgment half.
- **(E) Neither** — rejected; would silently drop a real, calibratable signal (growth rate relative
  to company age) that the deterministic-dimension program specifically identified as a strong
  candidate.

**Growth Velocity, resolved scope:** deterministic-when-applicable; requires a minimum absolute-scale
floor below which it is **N/A** rather than scored (closes the 2→6-vs-100→300 problem — the 2→6
case does not clear the floor, the 100→300 case does); requires a business-model-aware measurement
window drawn from the company's own `business_model` field (closes the enterprise-long-sales-cycle
problem — a 12-month window for enterprise, shorter for PLG); and treats expansion-driven ARR growth
and logo-driven customer-count growth as **distinguishable inputs**, not one blended ratio (closes
the $100k→$300k-vs-$5M→$15M problem only partially — see Part 11, this specific normalization
function is **CALIBRATION REQUIRED**, not fully specified here, because no defensible scale-adjustment
formula exists yet without real population data).

### Final dimension list, by pillar

**28 scored dimensions total.** Fundraising Readiness remains unscored (demoted to an unscored
narrative flag) — no reason found to reverse this. Commercial Validation remains removed — no
reason found to reverse this.

**Market (5, pillar weight .20):** Market Size · Market Growth · Market Timing · Competitive
Intensity · Customer Demand.

**Team (5, pillar weight .20):** Founder-Market Fit · Technical Capability · Business Capability ·
Leadership · Execution Track Record.

**Product (5, pillar weight .20):** Customer Value · Differentiation · Usability · Defensibility ·
Adoption Potential.

**Execution (4, pillar weight .15):** Go-to-Market Execution · Product Execution · Operational
Execution · Strategic Execution. *(Reduced from 5 — Growth Velocity relocated to Traction, no
replacement dimension created.)*

**Traction (5, pillar weight .15):** Customer Growth · Revenue Growth · Retention · Engagement ·
**Growth Velocity** *(new arrival, relocated from Execution)*.

**Financial Health (4, pillar weight .10):** Revenue Quality · Unit Economics · Burn Efficiency ·
Runway.

`5 + 5 + 5 + 4 + 5 + 4 = 28.` This resolves the Readiness Review's 28-vs-29 conflict at 28 — the
same total the Decision Memo originally proposed, but via a different, more conceptually honest
route (relocation + absorption, not a same-pillar duplicate dimension).

---

## Part 3 — Dimension weights: Execution, Traction, and Financial Health, resolved

Pillar weights unchanged (out of scope). Both internal-weight conflicts identified by the Readiness
Review are resolved below as final structural decisions — **weights are FROZEN; the numeric score
anchors and thresholds that feed the score each dimension contributes remain governed by Part 7 and
Part 11 (mostly CALIBRATION REQUIRED). These are different questions and must not be conflated.**

### Traction

Investment question: *"Is the company demonstrating durable, economically meaningful adoption and
growth?"* Mapping the question's own clauses to dimensions: "adoption" → Customer Growth;
"economically meaningful" → Revenue Growth; "durable" → Retention (primary) and Engagement
(leading-indicator); "growth" (named explicitly, as a pace/rate concept distinct from adoption) →
Growth Velocity.

| Dimension | Weight | Reasoning |
|---|---|---|
| **Retention** | **.25** | Widest-used, hardest-to-fake outcome-predictive signal for durability; the methodology's own text already treats it as stronger PMF evidence than surface usage metrics. |
| **Revenue Growth** | **.25** | The direct answer to "economically meaningful" — money, not just logos. |
| **Growth Velocity** | **.20** | Directly answers the question's explicit "growth" (pace) clause, but weighted below the two primary-evidence dimensions because it is *derived* from Customer Growth/Revenue Growth facts, not an independent evidence source — full independent weight here would double-count the same underlying facts a third time. |
| **Customer Growth** | **.15** | Real adoption signal, but structurally coupled to Revenue Growth via ACV (a standing, accepted "tolerable structural coupling," not removed) — kept meaningful but below Revenue Growth to avoid over-weighting one growth concept twice. |
| **Engagement** | **.15** | Catches the "zombie account" pattern (renewing but not using) nothing else in the pillar catches — real, distinct, but a secondary durability signal relative to Retention itself. |

Sum: 1.00.

### Execution

Four dimensions remain after Growth Velocity's relocation to Traction (Part 2): Go-to-Market
Execution, Product Execution, Operational Execution, Strategic Execution.

| Dimension | Weight | Reasoning |
|---|---|---|
| **Go-to-Market Execution** | **.25** | Frozen equal, not derived. |
| **Product Execution** | **.25** | Frozen equal, not derived. |
| **Operational Execution** | **.25** | Frozen equal, not derived. |
| **Strategic Execution** | **.25** | Frozen equal, not derived. |

Sum: 1.00.

**This is a deliberately conservative default, not a derived allocation, and the distinction
matters.** A structural review of this pillar's investment question ("is the company executing
effectively across acquiring customers, delivering the product, running efficient operations, and
making sound strategic choices?") produced a reasoned case for unequal weighting — elevating
Go-to-Market Execution as the most directly predictive of whether growth is achievable at all, and
reducing Strategic Execution as the weakest-grounded, most narrative-dependent of the four (per its
own Part 7 entry). **That case was not adopted.** We do not currently have sufficient empirical
evidence to justify precise unequal weighting among these four dimensions with confidence, and
equal weighting is adopted instead as the conservative v2 structural default — not because equal
weighting has been economically demonstrated to be correct, but because no calibration data yet
exists to prefer one specific unequal allocation over another, and an unjustified precise-looking
number would itself be a form of fake precision. **These weights are FROZEN for Methodology v2
calibration and must not be silently adjusted. They remain open to future revision if calibration
evidence demonstrates a material problem with equal weighting** (e.g., if one of the four dimensions
proves systematically uninformative or misleading relative to the others once real outcomes can be
checked) — that revision, if it happens, is itself a calibration-driven structural decision for a
future pass, not a standing invitation to tune now.

### Financial Health

Investment question: *"Can the company finance and sustain its growth long enough to create
enterprise value?"* Mapping: "finance... long enough" → Runway (the direct, near-term survival
question); "sustain its growth" → Burn Efficiency (spend proportional to growth) and Unit Economics
(whether growth is economically sound per-unit); "create enterprise value" → Revenue Quality
(durable revenue is what ultimately compounds into enterprise value, but is one step further from
the question's central survival/sustainability emphasis than the other three).

| Dimension | Weight | Reasoning |
|---|---|---|
| **Runway** | **.30** | Directly answers the question's leading clause ("finance... long enough"); also carries a supplementary **non-linear structural rule** below. |
| **Unit Economics** | **.25** | Directly answers "sustain its growth" from the per-unit-economics angle. |
| **Burn Efficiency** | **.25** | Directly answers "sustain its growth" from the spend-discipline angle. |
| **Revenue Quality** | **.20** | Real, but one inferential step removed from the specific survival/sustainability framing this pillar's investment question emphasizes. |

Sum: 1.00.

**Non-linear runway-floor rule (structural, not a weight change):** if Runway's dimension score
falls below a critical threshold (existential near-term cash risk), the Financial Health *pillar*
score is capped regardless of the other three dimensions' scores — a linear weighted average would
let strong Unit Economics/Burn Efficiency/Revenue Quality scores mathematically offset a company
that is genuinely about to run out of cash, which is not a defensible investment read. **The
existence of this rule is FROZEN. Its exact trigger threshold is CALIBRATION REQUIRED (Part 11).**

---

## Part 4 — Canonical missing-evidence semantics

**Governing rule, absolute: unknown must not become weak.** No dimension, pillar, or the overall
SPS may ever substitute a below-average default value for a dimension that lacks evidence, for any
reason. **The below-average-default mechanism described in `SIE_Methodology_v2_Scoring_Semantics.md`
Parts 3, 4, and 10 (items 5, 7, 8) is SUPERSEDED and REJECTED in full. No implementation may exhibit
that behavior. This is not a revision — it is the closure of a defect that document's own successor
identified and this document permanently locks shut.**

### The nine canonical states

| State | Denominator treatment | Diligence flag | Confidence | Disclosure risk |
|---|---|---|---|---|
| **Not Expected By Stage** | Excluded entirely — never enters the in-scope set for this stage | None | N/A | No |
| **Not Applicable** (business model has no such construct) | Excluded entirely — never enters the in-scope set | None | N/A | No |
| **Optional But Unavailable** (stage permits absence, presence would be a bonus) | Excluded from the scored set; remains in the in-scope set for coverage reporting | Minimal or none, per Part 7's per-dimension stage table | N/A | No |
| **Usually-Private And Unavailable** | Excluded from the scored set; remains in the in-scope set for coverage reporting | Standard — "not disclosed, recommend requesting directly" | N/A | No |
| **Expected But Unavailable** | **Identical arithmetic treatment to Usually-Private** — excluded from the scored set, remains in-scope for coverage | **Elevated** — "atypical absence at this stage, verify" | N/A | No |
| **Research Failure** (SIE's own search missed available evidence) | Excluded from the scored set; remains in-scope for coverage | System-facing "research completeness note," **never** a company-facing diligence flag | N/A | No |
| **Explicit Management Refusal** | Excluded from the scored set; remains in-scope for coverage | Elevated — "explicitly declined, atypical, warrants scrutiny" | N/A | **Yes — the only trigger** |
| **Conflicting Evidence** | If a clearly more-credible source exists: scored from that source, included in the scored set. If credibility is genuinely ambiguous: treated as Unavailable (Expected-But-Unavailable arithmetic), excluded from the scored set | Verification flag — "sources disagree, reconcile before relying on either figure" | Capped Low if scored; N/A if excluded | No |
| **Mixed Evidence** | Always scored, always in the scored set | Tension flag — names the specific tension | Medium–High, never automatically Low | No |

**The load-bearing resolution, stated with zero ambiguity:** *Usually-Private-And-Unavailable* and
*Expected-But-Unavailable* receive **identical treatment in every arithmetic operation** — identical
exclusion from the scored set, identical exclusion from the weighted-average numerator and
denominator, identical non-contribution to the dimension's own score. **They differ in exactly one
place: diligence-flag severity, and nowhere else.** This is the direct, final closure of the
Adversarial Review's Cases 1/2 finding (an elite-but-quiet company and a weak-but-hiding company are
observationally identical, so treating "expected but missing" as a distinct, penalized arithmetic
category was a category error, not a tuning problem).

### Exactly which dimensions enter the denominator

For a given pillar at a given company stage:

1. Start from the pillar's full dimension list (per Part 2).
2. Remove any dimension in state **Not Expected By Stage** or **Not Applicable** — these never enter
   the **in-scope set**.
3. Within the in-scope set, a dimension enters the **scored set** only if it resolved to a real
   number — i.e., it is Mixed Evidence, Conflicting-Evidence-resolved-to-a-source, or genuinely has
   direct/inferred evidence supporting a score (per the original seven-case table's cases 1–3,
   carried forward unchanged from Scoring Semantics Part 2).
4. Every other in-scope dimension (Optional-But-Unavailable, Usually-Private, Expected-But-
   Unavailable, Research-Failure, Refusal, Conflicting-unresolved) is **excluded from the scored
   set**.

### Exactly when weights are renormalized

Pillar weighted average = weighted sum over the **scored set only**, with each scored dimension's
weight (Part 3, or the existing production weights for pillars not revised here) renormalized to sum
to 1 across the scored set. **Renormalization happens only across the scored set — never across the
full dimension list, and never with a substituted default value standing in for an excluded
dimension.** This is arithmetically identical to "plain renormalization" *for the scored set as
now correctly defined* — the fix is not a new renormalization formula, it is the corrected
membership rule for what counts as "scored" (see the state table above; the fix lives in Part 4's
state definitions, not in a special aggregation formula).

### How stage expectations interact with aggregation

Stage determines the **in-scope set** (step 2 above) before evidence is even examined — a dimension
that is Not-Expected-By-Stage is never a candidate for scoring at all, regardless of what evidence
might exist. Stage also determines which of the five Unavailable sub-types applies when a dimension
that *is* in-scope turns up no evidence (Optional vs. Usually-Private vs. Expected — the exact
mapping is Part 7's per-dimension stage table, inherited unchanged from Scoring Semantics Part 3
except for its stale case-6 language, which is corrected by this document).

---

## Part 5 — Quality, Confidence, Coverage, Disclosure Risk: canonical, three levels

### Quality

- **Dimension level:** the 1–10 score — what the evidence found, at face value, supports about this
  specific question. Never discounted for absent evidence elsewhere.
- **Pillar level:** the weighted average over the scored set (Part 4), using pillar-internal weights
  (Part 3 for Traction/Financial Health; existing production weights elsewhere, unrevised here).
- **Overall level (SPS):** the weighted average over the six pillars, using the frozen
  `PILLAR_WEIGHTS`, applying the identical scored-set logic one level up (a pillar that is entirely
  Unavailable is excluded from the SPS weighted average exactly as a dimension is excluded from a
  pillar average — no below-average default at this level either).

### Confidence

- **Dimension level:** rule-gated High/Medium/Low per the frozen model (Scoring Semantics Part 8,
  unrevised): coverage adequacy, direct-vs-inferred mix, source agreement, recency, stage-
  appropriateness, source credibility.
- **Pillar level:** **not a numeric average of dimension confidences** (that would manufacture fake
  precision via aggregation of an already-ordinal quantity). Rule: pillar confidence is **High**
  only if every dimension in the scored set is High confidence *and* the scored-set coverage
  (scored ÷ in-scope) clears a majority bar; **Low** if most scored dimensions are Low or coverage is
  thin; **Medium** otherwise. Ordinal, rule-gated — consistent with the dimension-level model's own
  design philosophy, not a new mechanism.
- **Overall level:** the identical ordinal rule applied one level up across the six pillars.

### Evidence Coverage

**Two genuinely different denominators share this name — implementers must not conflate them:**
- **Dimension-level coverage:** fraction of that dimension's own defined evidence-priority items
  actually found (substantive, credible — not raw source volume, per the PR-flooding fix). This is
  the finer-grained, "how much of what we look for did we find" measure.
- **Pillar-level and overall-level coverage:** fraction of the **in-scope dimension set** that
  reached the **scored set** (a dimension-count fraction, not an evidence-item fraction). Reported
  against the stage-appropriate in-scope denominator (Part 4), never the fixed full dimension count
  — this is the load-bearing anti-bias mechanism preventing early-stage companies from being
  structurally penalized in coverage for lacking dimensions that were never expected of them.

### Disclosure Risk

- **Dimension level:** binary — was an explicit refusal observed for this specific metric, yes or
  no. The **only** trigger; never inferred from silence, research failure, hedged answers, or
  unverifiable claims (Part 4's state table).
- **Pillar level:** whether any dimension in the pillar carries a refusal flag — reported as a
  count/list, never scored, never averaged.
- **Overall level:** the aggregate list across all six pillars, feeding the profile's Diligence Flags
  count and, per the frozen ranking contract (Part 10), potentially the ranking tier — **never SPS,
  never confidence, at any level.**

No fake precision is introduced anywhere in this section — every quantity above is either a real
count/fraction with an honest denominator, or an ordinal rule-gated category, never an invented
numeric formula.

---

## Part 6 — Universal 0–10 scale: frozen semantic backbone

The prompt's suggested framework (5 = credible/stage-appropriate-but-undifferentiated, 7 = clearly
strong, 9 = exceptional, 10 = extraordinary) is **directionally right but incomplete** — it says
nothing about 0, 1–2, 3–4, 6–7, or 8, and critically, it does not address the single most dangerous
gap: **nothing in that framework distinguishes a low score earned by genuine negative evidence from
a low score assigned merely because evidence is thin.** Left unaddressed, a scorer under time
pressure could reach for a low number as a stand-in for "I don't know," which silently reintroduces
the exact unknown-becomes-weak collapse Part 4 exists to prevent, just at the scale-semantics layer
instead of the aggregation layer. This document closes that gap explicitly below. Adopted, with
this correction:

| Score | Meaning |
|---|---|
| **0** | Reserved for **direct, evidence-backed disqualifying findings** (e.g., a proven fraud, an active disqualifying regulatory action) — requires the *same* evidentiary rigor a 10 would require, just in the negative direction. **Never used as a stand-in for absent evidence.** If evidence is absent, the correct state is Unavailable (Part 4), never a 0. |
| **1–2** | Materially weak — **direct evidence** of a significant problem relative to stage expectations. Not "we found nothing positive"; specifically "we found something negative." |
| **3–4** | Below stage-appropriate expectations — real evidence exists and it is genuinely subpar, not merely thin. |
| **5** | **Stage-appropriate / neutral** — the center of the scale. Evidence found is consistent with what's normal and expected for a company at this stage; neither a notable strength nor a notable weakness. Deliberately not a "passing" or "failing" grade — it means *unremarkable, as expected*. |
| **6–7** | Good — clearly above stage-appropriate expectations, real positive signal, no notable gaps. |
| **8** | Very strong — evidence a skeptical reviewer would find compelling with few reservations. |
| **9** | Exceptional — evidence that would be difficult to argue against; rare. |
| **10** | Extraordinary / category-defining — reserved, should almost never occur even for genuinely elite companies, since it requires near-total, high-confidence evidence with essentially zero ambiguity across the entire dimension. Consistent with the SPS-distribution philosophy already established (Audit doc Part 8: overall scores near 100 should almost never occur). |

**This is stage-aware by construction, not as an afterthought:** "5" means the same *conceptual*
thing (stage-appropriate-neutral) for a Pre-Seed company and a Series B company, even though the
concrete evidence that earns a 5 differs enormously between them — the universal backbone tells a
scorer what the number *means*; the dimension-specific anchors (Part 7) tell a scorer what evidence
*earns* that number at that dimension, at that stage. **These two layers are independent and both
required — this backbone does not replace dimension-specific anchors, and dimension-specific anchors
without this backbone would leave "5" meaning something different on every dimension, defeating
cross-dimension comparability.**

---

## Part 7 — Dimension execution contracts

All 28 dimensions. `Anchors` column: **FROZEN** (real, numeric, already exists) or **CALIBRATION
REQUIRED** (qualitative bands exist or are newly specified here, but numeric thresholds are not
invented without benchmark support). `Benchmark coverage`: drawn from the Calibration Execution
Readiness Review's Part 2/7 findings.

### Market (.20)

**Market Size** — Pillar: Market. *Definition:* realistic venture-scale addressable market if the
company executes. *Investment question:* "How big can this become?" *Evidence scope:* customer-
segment size, buyer-budget category, named expansion paths, comparable market categories. *Must not
use:* TAM/SAM/SOM figures alone as a substitute for the above — absence of a TAM figure is never
itself a negative signal. *Stage:* all stages, confidence-scaled. *Mode:* **Hybrid.** *Missing-
evidence:* per Part 4 state table. *Weight:* .25 (within-pillar). *Scale:* per Part 6. *Anchors:*
**CALIBRATION REQUIRED** (qualitative bands exist, unrevised). *Coverage:* sufficient (12/15).

**Market Growth** — *Definition:* category growth, explicitly not company growth. *Investment
question:* "Is the pie itself expanding?" *Evidence scope:* category-level growth data, buyer-budget
expansion, secular tailwinds named with a mechanism, not just a label ("AI" alone is not evidence).
*Must not use:* the company's own revenue/customer growth rate as primary evidence (that's Traction's
domain — using it here double-counts). *Stage:* all. *Mode:* **Constrained LLM.** *Weight:* .20.
*Anchors:* CALIBRATION REQUIRED. *Coverage:* thin (~4/15).

**Market Timing** — *Definition:* whether now is the adoption-ready moment, distinct from whether the
category is growing. *Investment question:* "Why now, specifically?" *Evidence scope:* named trigger
events (regulatory shift, technology inflection, platform change) with evidence buyers are already
acting on it. *Must not use:* founder "why now" narrative alone as proof. *Stage:* all. *Mode:*
**Constrained LLM.** *Weight:* .20. *Anchors:* CALIBRATION REQUIRED. *Coverage:* thin.

**Competitive Intensity** — *Definition:* whether the company can win given the whole competitive
landscape (distribution power, incumbent scale, capital intensity of the fight) — distinct from
whether the product itself is different or defensible. *Investment question:* "Can they win the
market, not just the product comparison?" *Evidence scope:* named competitors, distribution/scale
asymmetry, win/loss evidence where available. *Must not use:* "is the product different" (that's
Differentiation) or "can the difference be copied" (that's Defensibility) — this partition is
structural and must be enforced. *Stage:* all. *Mode:* **Hybrid.** *Weight:* .15. *Anchors:*
CALIBRATION REQUIRED — partition-boundary validation explicitly deferred to calibration. *Coverage:*
thin (6/15).

**Customer Demand** — *Definition:* pre-revenue/pre-Traction demand signal only (LOIs, waitlist,
pilot interest). *Investment question:* "Is there real pull before there's real revenue?" *Evidence
scope:* unconverted interest signals. *Must not use:* paying-customer/revenue/retention evidence —
that is Traction's domain exclusively; using it here is the confirmed double-counting this
dimension was narrowed to eliminate. *Stage (revised, clarified lifecycle role):*
- **Pre-Seed: Expected** when customer-demand validation is reasonably possible for a company at
  this stage (i.e., not itself gated on having zero evidence available — a Pre-Seed company with no
  disclosed LOI/waitlist activity at all genuinely has nothing to show here yet, in which case
  standard stage-appropriate absence applies).
- **Seed: Expected** *as long as* realized Traction has not yet superseded demand-validation
  evidence as the more informative signal.
- **Series A+: Not Applicable** once realized Traction provides the appropriate downstream evidence
  — this is a clean exit from the pillar's in-scope set for that company, not an ongoing
  "optional/superseded" ambiguity.

**Determined by actual company maturity and evidence state, never mechanically by the financing-round
label alone.** A company nominally labeled "Series A" that is, on the evidence, still operationally
pre-Traction (no disclosed customer/revenue data, single-market/pre-scale) should be evaluated under
the Seed rule above, not defaulted to Not-Applicable merely because of its round name. The exclusion
boundary against realized-Traction evidence (above) is unchanged and must still be enforced whichever
stage rule applies — this dimension never re-scores what Traction already owns. *Mode:* **Hybrid.**
*Weight:* .20. *Anchors:* CALIBRATION REQUIRED (newly narrowed scope, no prior anchor text existed).
*Coverage:* thin; largely explained by benchmark composition (most calibration-set records are past
the dimension's relevant lifecycle window under either the label-based or maturity-based reading) —
flagged as a benchmark limitation, not solely a specification gap.

### Team (.20)

**Founder-Market Fit** — *Definition:* founders' prior domain insight/experience, independent of
what the company has since achieved. *Evidence scope:* prior operator/buyer roles, prior founder
success, direct domain credibility. *Must not use:* execution outcomes since founding (that's
Execution Track Record). *Stage:* all, highest-weighted at earliest stages by design. *Mode:*
**Constrained LLM.** *Weight:* .25. *Anchors:* CALIBRATION REQUIRED. *Coverage:* sufficient (11/15).

**Technical Capability** — *Definition:* ability to build/scale relative to product complexity — a
capability-ceiling question, not a delivery-quality question. *Evidence scope:* technical founder
presence, shipped-product complexity, integration depth. *Must not use:* roadmap cadence/delivery
quality — that is Product Execution's domain; the boundary is *"can they"* (here) vs. *"did they, how
well"* (Product Execution). *Stage:* all. *Mode:* **Hybrid.** *Weight:* .20. *Anchors:* CALIBRATION
REQUIRED. *Coverage:* ~10/15.

**Business Capability** — *Definition:* founder/team commercial *background* only. *Evidence scope:*
prior sales/ops leadership roles, stated pricing-strategy clarity, commercial hiring. *Must not use:*
revenue/GTM outcomes — that is GTM Execution's exclusive domain; this dimension answers "can they,"
not "did it happen." *Stage:* stage-conditional, gradient from Optional (Pre-Seed) to Expected
(Series A+). *Mode:* **Hybrid.** *Weight:* .20. *Anchors:* CALIBRATION REQUIRED (newly narrowed, no
prior anchor text). *Coverage:* thin.

**Leadership** — *Definition:* ability to lead, hire, scale an organization. *Evidence scope:* prior
leadership roles, hiring success, executive-team depth. *Stage:* **Not Expected at Pre-Seed**
(clean exclusion, not a gap); Optional at Seed; Expected Series A+. *Mode:* **Constrained LLM.*
*Weight:* .20. *Anchors:* CALIBRATION REQUIRED. *Coverage:* ~5/15.

**Execution Track Record** — *Definition:* qualitative milestone-achievement pattern *within this
venture* — product shipped, fundraise progress, pivots-with-learning. *Must not use:* the
prior-founder/prior-exit signal (moved exclusively to Founder-Market Fit) or raw growth rate (moved
exclusively to Growth Velocity in Traction). *Stage:* all. *Mode:* **Constrained LLM.** *Weight:*
.15. *Anchors:* CALIBRATION REQUIRED (newly narrowed). *Coverage:* thin.

### Product (.20)

**Customer Value** — *Definition:* pain severity and ROI evidence. *Evidence scope:* stated
cost/time saved, workflow displaced, pain-severity narrative. *Must not use:* NRR/churn as primary
evidence — that is Retention's domain; use only pain-severity and ROI-specific evidence distinct
from the retention number itself. *Stage:* all, pillar-anchor dimension by design. *Mode:*
**Hybrid.** *Weight:* .25. *Anchors:* CALIBRATION REQUIRED (boundary against Retention newly
enforced). *Coverage:* ~8/15.

**Differentiation** — *Definition:* is the product meaningfully different *today*, present-tense
comparison against named alternatives. *Must not use:* durability-of-difference evidence (that's
Defensibility) or market-structure/distribution evidence (that's Competitive Intensity) — this
three-way partition is structural, deliberately preserving three genuinely distinct investment
questions the Decision Memo confirmed should not be merged (the Betamax pattern: differentiated and
defensible products can still lose to distribution power; commodity products can still win on
distribution). *Stage:* all. *Mode:* **Constrained LLM.** *Weight:* .20. *Anchors:* CALIBRATION
REQUIRED — partition validation explicitly deferred. *Coverage:* ~8/15.

**Usability** — *Definition:* narrowly, adoption *friction* — how much effort a new customer expends
to reach first value. Distinct from Customer Value (whether the value is worth having) and
Defensibility (whether it's hard to leave). *Evidence scope, in priority order:* direct
(time-to-value/activation) → strong proxy (self-serve availability, stated implementation timeline)
→ weak proxy (unverified ease claims, capped confidence). *Must not use:* retention/churn as a
usability proxy — the single explicit evidence-leak this redesign closes; Retention is scored
independently and never borrowed here. *Stage:* all. *Mode:* **Hybrid.** *Weight:* .15. *Anchors:*
CALIBRATION REQUIRED (fully redesigned, first operational anchor text). *Coverage:* thin.

**Defensibility** — *Definition:* the durability *mechanism* — why the difference can't be copied
over time (switching costs, data accumulation, network-effect type). *Must not use:* present-tense
differentiation evidence (Differentiation's domain) or market-structure evidence (Competitive
Intensity's domain). *Stage:* all. *Mode:* **Constrained LLM.** *Weight:* .20. *Anchors:*
CALIBRATION REQUIRED. *Coverage:* ~7/15.

**Adoption Potential** — *Definition:* structural expansion *surface* — named adjacent use-cases,
teams, or geographies not yet penetrated. *Must not use:* realized NRR/expansion-revenue evidence —
that is Retention's domain; this dimension asks about headroom, not what's already been captured.
*Stage:* all. *Mode:* **Hybrid.** *Weight:* .20. *Anchors:* CALIBRATION REQUIRED (newly narrowed).
*Coverage:* thin.

### Execution (.15)

**Go-to-Market Execution** — *Definition:* repeatable customer-acquisition motion. *Evidence scope:*
CAC/payback when disclosed, pipeline quality, sales-cycle/conversion. *Stage:* Not Expected Pre-Seed;
gradient to Usually-Private at scale (CAC data is rarely public even late). *Mode:* **Hybrid.**
*Weight:* .25 (frozen conservative default — see Part 3's Execution weight-derivation discussion;
not economically derived). *Anchors:* **FROZEN — partial** (CAC payback <12mo = excellent, existing
production benchmark text). *Coverage:* 5/15.

**Product Execution** — *Definition:* delivery quality and cadence — including, for pre-revenue
companies, shipping/iteration speed (the population "Execution Tempo" would have served — folded in
here per Part 2, not a separate dimension). *Evidence scope:* shipped milestones, reliability,
integration depth, **roadmap velocity** (this item now explicitly carries the pre-revenue
execution-speed signal). *Must not use:* capability-ceiling evidence (Technical Capability's domain)
— boundary is *"did they, how well"* (here) vs. *"can they"* (Technical Capability). *Stage:* all.
*Mode:* **Hybrid.** *Weight:* .25 (frozen conservative default — see Part 3). *Anchors:* CALIBRATION
REQUIRED (roadmap-velocity absorption is new). *Coverage:* ~10/15.

**Operational Execution** — *Definition:* non-financial operational/process discipline (hiring plan
quality, org structure, ownership clarity). *Must not use:* burn/margin data as a substitute when
process evidence is absent — the "defer to financial metrics" escape hatch from the original
methodology text is explicitly removed; if non-financial process evidence is absent, this dimension
is Unavailable, not silently re-scored from Burn Efficiency's numbers. *Stage:* Not Expected
Pre-Seed; Usually-Private at scale. *Mode:* **Hybrid.** *Weight:* .25 (frozen conservative default —
see Part 3). *Anchors:* CALIBRATION REQUIRED (escape-hatch removal is new). *Coverage:* 4/15.

**Strategic Execution** — *Definition:* specific strategic choices — wedge selection, sequencing,
capital allocation. *Must not use:* generic "decision quality" language — that evidence belongs
exclusively to Leadership; this dimension is about the *choices*, not who made them. *Stage:* all.
*Mode:* **Constrained LLM** — flagged as the weakest-grounded surviving dimension in the entire
methodology; almost no real evidence exists for it pre-Series-B regardless of this narrowing.
*Weight:* .25 (frozen conservative default — see Part 3). *Anchors:* CALIBRATION REQUIRED.
*Coverage:* weak.

### Traction (.15)

**Customer Growth** — *Definition:* customer-count time series relative to stage. *Mode:*
**Deterministic.** *Stage:* Not Expected Pre-Seed (score normally if present anyway), gradient to
Expected. *Weight:* .15. *Anchors:* **FROZEN — partial** (existing numeric example: "42 accounts
strong for Series A"; **no general formula for converting a growth rate into a 1–10 score exists —
CALIBRATION REQUIRED for that conversion function**). *Coverage:* 6/15, mostly single-point not
series.

**Revenue Growth** — *Definition:* ARR/MRR time series. *Mode:* **Deterministic.** *Stage:* same
gradient. *Weight:* .25. *Anchors:* **FROZEN — partial**, same conversion-function gap. *Coverage:*
thin.

**Retention** — *Definition:* NRR/GRR/churn. *Mode:* **Deterministic.** *Stage:* Not Expected
Pre-Seed/early-Seed, Expected Series A+. *Weight:* .25. *Anchors:* **FROZEN — the best-anchored
dimension in the entire methodology** (NRR>130%=9–10, GRR>90%=strong, logo churn<1.5%/mo=strong,
all explicit). *Coverage:* **0/15 — mechanism-testable only, not anchor-testable, per current
portfolio.*

**Engagement** — *Definition:* real usage telemetry only. *Must not use:* Retention/NRR as a
substitute when telemetry is absent — the free-substitution rule is explicitly removed; if no real
usage evidence exists, this dimension is Unavailable, never silently re-scored from Retention's
number. *Mode:* **Hybrid.** *Stage:* Not Expected Pre-Seed, gradient. *Weight:* .15. *Anchors:*
CALIBRATION REQUIRED. *Coverage:* 0/15.

**Growth Velocity** *(relocated, Part 2)* — *Definition:* growth rate normalized by company age/
stage, materiality-floor-gated, business-model-window-aware. *Must not use:* raw ratios below the
materiality floor (structurally N/A, not scored). *Mode:* **Deterministic when applicable** (pure
computation, no LLM step, when the floor and evidence requirements are met); **N/A** (not Hybrid) for
pre-revenue companies. *Stage:* N/A Pre-Seed by construction. *Weight:* .20. *Anchors:*
**CALIBRATION REQUIRED in full** — materiality floor, business-model window function, and the
expansion-vs-logo-growth distinguishing logic are all unspecified pending real data. *Coverage:*
0/15.

### Financial Health (.10)

**Revenue Quality** — *Definition:* customer-concentration and contract-durability only; NRR/GRR
component is *derived* from Retention's own extracted value, not re-elicited independently. *Mode:*
**Hybrid.** *Stage:* Not Applicable in most cases Pre-Seed, gradient. *Weight:* .20. *Anchors:*
CALIBRATION REQUIRED (newly narrowed). *Coverage:* 3/15.

**Unit Economics** — *Definition (business-model-agnostic, revised):* **does the company earn
sufficient economic value from a typical customer/transaction/unit relative to the cost required to
acquire and serve it, and does that relationship appear durable?** This replaces the prior
SaaS-specific framing ("gross margin, CAC payback, LTV:CAC") as *the* definition — those remain
valid evidence, but only as one business-model family among several, not as the universal anchor.
*Investment question:* "Does a typical unit of this business make economic sense, and will it keep
making sense?" *Evidence families (still one dimension, not split by business model):*
- **SaaS/subscription:** gross margin, CAC payback period, LTV:CAC ratio.
- **Marketplace/take-rate:** take-rate %, gross-vs-net revenue distinction, per-transaction
  servicing cost (inspection, delivery, financing, support).
- **Insurance/underwriting:** loss ratio (claims paid ÷ premiums earned), combined ratio, claims
  trend.
- **Hardware/manufacturing:** per-unit COGS vs. unit price (gross margin per unit) — explicitly
  *not* the SaaS CAC-payback framing, which does not transfer cleanly to hardware sales-cycle
  dynamics.
- **Commerce/DTC**, where distinct from marketplace or hardware: landed cost vs. price, contribution
  margin after fulfillment.
- **R&D-partnership / program-fee / deeptech:** program fee vs. cost-to-deliver the program —
  flagged explicitly as the least standardized family, likely to remain closer to qualitative
  judgment than the others even after this redefinition.

*Must not use:* one family's evidence as if it were universal (e.g., do not expect or require
gross-margin/CAC-payback figures from an insurer or a deeptech R&D-partnership company — absence of
SaaS-shaped evidence there is not itself informative).

*Mode:* **Deterministic** where a business-model-appropriate computation exists from disclosed
figures; the mode itself is unchanged, only the evidence scope is generalized. *Stage:* Not Expected
Pre-Seed; Usually-Private in practice even at scale (evidence tier corrected from Public to Private
per the Audit doc's mistag finding). *Weight:* .25. *Anchors:* **FROZEN, SaaS family only**
(margin>80%=excellent, payback<12mo=excellent, LTV:CAC>3x=strong — these remain exactly as written,
but are now explicitly scoped to the SaaS/subscription evidence family, never applied to a
marketplace, insurance, hardware, or R&D-partnership company). **Numeric anchors for every other
family are CALIBRATION REQUIRED** — no new thresholds are invented here for marketplace take-rate,
loss-ratio, per-unit-COGS, or program-fee economics; only the evidence families themselves are
specified. *Coverage:* 2/15 (both SaaS-family-anchor-compatible; several additional companies in the
calibration set carry real non-SaaS-family evidence that was not previously recognized as
in-scope for this dimension).

**Burn Efficiency** — *Definition:* is capital being spent efficiently relative to the progress it
is producing? *Mode changed: Deterministic → **Hybrid**.* When defensible revenue/output-relative
metrics exist (a burn multiple computable from disclosed spend and growth), that computation anchors
the judgment directly — this covers high-burn/extraordinary-growth, high-burn/weak-growth, and
low-burn/weak-growth cases cleanly, exactly as the prior Deterministic design intended. When such a
computation is not possible — capital-intensive pre-revenue hardware/manufacturing, pre-revenue
biotech/deeptech, or any company where the causal driver of spend is capex/R&D-infrastructure rather
than revenue-generating operations — permit constrained qualitative evaluation of: spend relative to
stated milestones/output, capital intensity appropriate to the business model, general operating
efficiency signals, and financing consumption relative to demonstrated progress. **This dimension
must not become Runway.** A documented cash crisis is legitimate *context* for judging whether spend
has been efficient, but "how long until cash runs out" is Runway's question exclusively, never
scored or restated here. *Stage:* Usually-Private throughout. *Weight:* .25. *Anchors:* **CALIBRATION
REQUIRED** for both the deterministic burn-multiple threshold (the Audit doc's proposed <1.5x-strong
figure was never validated) and the qualitative-fallback evidence bands — neither is invented here.
*Coverage:* 1/15 under the deterministic path; the Hybrid mode change makes additional
capital-intensive/pre-revenue records in the calibration set potentially scoreable on
re-examination, not yet re-scored.

**Runway** — *Definition:* does the company have enough cash to reach its next major milestone,
plus the non-linear floor-cap rule (Part 3)? *Mode changed: Deterministic → **Hybrid**.* When cash
position and burn rate permit a defensible months-of-runway calculation, that calculation is the
primary anchor, exactly as the prior Deterministic design intended (18mo=healthy, 24mo=strong,
<6mo=critical, all explicit and unchanged). When an exact calculation is not possible but strong,
direct evidence establishes a severe or comfortable financing position, permit constrained
qualitative judgment from evidence such as: documented near-insolvency, emergency/rescue financing,
imminent inability to meet obligations, or clearly substantial cash reserves relative to known
operating needs. **Missing evidence remains missing evidence** — the absence of public cash data is
never itself grounds to infer distress; qualitative judgment requires *strong direct evidence* of
the financing position, not the mere absence of a number. *Stage:* gradable at every stage. *Weight:*
.30. *Anchors:* **FROZEN for the linear component** (18mo=healthy, 24mo=strong, <6mo=critical);
**the qualitative-fallback evidence bands and the floor-cap trigger threshold are both CALIBRATION
REQUIRED** — the floor-cap rule's existence remains structural/frozen (Part 3), its exact number is
not, and no new qualitative-fallback threshold is invented here. *Coverage:* 1/15 under the
deterministic path; the Hybrid mode change makes the one severe-distress record in the calibration
set (previously blocked on a missing precise burn-rate figure despite strong direct crisis evidence)
potentially scoreable on re-examination, not yet re-scored.

---

## Part 8 — Deterministic / Hybrid / Constrained-LLM reclassification

Reconciled against the final 28-dimension architecture (Part 2), not the old 30-dimension list the
original reliability program (6/11/13) was built against.

**Deterministic (5):** Customer Growth, Revenue Growth, Retention, Growth Velocity, Unit Economics.
*Why:* each is computable from extracted, countable facts with no judgment step required once
evidence exists — determinism is appropriate here because the underlying construct genuinely reduces
to arithmetic on real numbers (a growth rate, a ratio, a count of months), not because
reproducibility is merely desirable. Growth Velocity is included despite needing further calibration
work (Part 11) because its *architecture* is deterministic — what's unresolved is the conversion
function's exact parameters, not whether a human judgment step belongs in the pipeline (it doesn't).
Unit Economics keeps its Deterministic classification under the business-model-agnostic redefinition
(Part 7) — the *mode* is unchanged, only the evidence families that feed the same computational
approach were generalized beyond SaaS.

**Hybrid (15):** Market Size, Competitive Intensity, Customer Demand, Technical Capability, Business
Capability, Customer Value, Usability, Adoption Potential, GTM Execution, Product Execution,
Operational Execution, Engagement, Revenue Quality, **Burn Efficiency, Runway**. *Why:* each has a
genuine deterministic core (a named fact, a countable signal, a disclosed number when available)
that a judgment layer must still interpret in context — none of these reduce cleanly to arithmetic
the way the Deterministic group does, but none are pure narrative judgment either. **Burn Efficiency
and Runway moved here from Deterministic** following the post-PASS-A structural review: both retain
their deterministic computation as the *primary* path when defensible revenue/burn-relative data
exists, but now permit constrained qualitative judgment when it doesn't (capital-intensive
pre-revenue companies, documented financing crises without a precise burn-rate figure) — the
architecture is no longer "compute or fail," it is "compute when possible, judge narrowly and
explicitly when not," which is definitionally Hybrid, not Deterministic.

**Constrained LLM (8):** Market Growth, Market Timing, Founder-Market Fit, Leadership, Execution
Track Record, Differentiation, Defensibility, Strategic Execution. *Why:* each asks an irreducibly
qualitative question — category-tailwind causality, adoption-timing plausibility, founder pedigree
relevance, leadership capacity, milestone-pattern narrative, competitive-differentiation narrative,
moat-mechanism plausibility, strategic-choice soundness — none of which has a defensible numeric
formula, now or with more calibration data. **Determinism is deliberately not forced onto any of
these eight merely because reproducibility would be convenient; the underlying constructs are not
measurable facts, they are judgments about facts, and pretending otherwise would manufacture fake
precision exactly as Parts 5 and 6 forbid.**

`5 + 15 + 8 = 28.` ✓ (Revised from the original 7/13/8 split — see Part 13 for the supersession
entry recording this change and its cause.)

---

## Part 9 — Aggregation contract

### Dimension → Pillar

1. Compute the in-scope set (Part 4, step 2) for this company's stage.
2. For every in-scope dimension, resolve its state (Part 4's nine-state table).
3. The **scored set** = in-scope dimensions that resolved to a real number.
4. **Unavailable** dimensions (any of the five Unavailable sub-types) contribute nothing to the
   numerator or denominator — no default, no substitution, confirmed dead per Part 4.
5. **N/A** dimensions (Not Expected By Stage, Not Applicable) were never in-scope and are likewise
   absent from numerator and denominator.
6. Pillar score = weighted average over the scored set, weights renormalized to sum to 1 across the
   scored set using Part 3's structural weights (Traction, Financial Health) or existing production
   weights (other four pillars, unrevised here).
7. Pillar confidence = the ordinal rule from Part 5 (High only if all scored dimensions High and
   coverage clears a majority bar; otherwise Medium/Low).
8. Pillar coverage = |scored set| ÷ |in-scope set| (dimension-count fraction, Part 5's
   pillar-level definition — distinct from any individual dimension's own evidence-item coverage).

### Pillar → SPS

1. Apply the identical scored/in-scope logic one level up across the six pillars, using the frozen
   `PILLAR_WEIGHTS`.
2. An entirely-Unavailable pillar (rare — realistically only Financial Health for a genuinely
   pre-revenue, pre-spend company) is excluded from the SPS weighted average exactly as an
   Unavailable dimension is excluded from a pillar average — **no pillar-level below-average
   default either.**
3. **When SPS displays:** normally, as a point number, whenever overall coverage clears the display
   floor (item 4).
4. **When SPS suppresses:** below a minimum overall-coverage floor — the *principle* is FROZEN
   (Final Scoring Decisions Part 3), the *exact numeric floor* is **CALIBRATION REQUIRED**, not
   invented here.
5. **What accompanies SPS, always:** Confidence (categorical), Evidence Coverage (numeric % +
   derived category), Ranking Eligibility (Part 10), Diligence Flags (count + list), Disclosure Risk
   (if any) — per the canonical header (Final Scoring Decisions Part 7), unrevised.
6. **Partial Structural Coverage — a new SPS display state.** This is **not a different SPS
   formula** — the quality SPS remains computed only from the defensibly scored set under the
   canonical aggregation rules above, unchanged and unpenalized. It is a **display-layer label**
   communicating that one or more *entire pillars* are structurally absent from the analysis, as
   distinct from ordinary dimension-level incompleteness within populated pillars (which item 3's
   normal display, carrying Confidence/Coverage labeling, already handles). The trigger considers
   **whole-pillar availability specifically, not raw dimension-count coverage** — a company missing
   several dimensions spread thinly across all six pillars is a different, less severe case than one
   where entire pillars have zero scored dimensions, even if the two might show similar raw coverage
   percentages. **The exact triggering threshold (how many/which pillars entirely absent) is
   CALIBRATION REQUIRED**, not invented here. When triggered, the SPS number itself is displayed
   unchanged — this label is purely additive alongside Confidence/Coverage/Diligence Flags, never a
   mathematical adjustment, never a coverage penalty subtracted from the score. **Ranking eligibility
   remains governed entirely separately**, by the existing evidence/pillar eligibility architecture
   (Part 10) — Partial Structural Coverage is a profile-page display concept, not a new ranking rule.

---

## Part 10 — Ranking contract

Architecture, FROZEN, restated precisely: **eligibility gate → evidence/completeness tier → raw SPS
ranking within a comparable tier.** SPS is never mathematically adjusted for confidence or coverage
at any stage of this pipeline — "quality ≠ certainty" is preserved entirely by **segmentation**
(gating and tiering), never by subtraction or multiplication against the score.

1. **Eligibility gate:** a company must clear a minimum in-scope-pillar-representation bar and a
   minimum stage-adjusted coverage bar (Final Scoring Decisions Part 2) to appear in comparative
   rankings at all. Below the gate: not ranked, still has a profile page (Part 9, item 3–4 governs
   whether that profile shows a point SPS or is suppressed).
2. **Evidence/completeness tier:** among eligible companies, assign a tier from
   confidence/coverage/inferred-evidence-share. Tier count and boundaries: **CALIBRATION REQUIRED.**
3. **Raw SPS ranking within a tier:** legitimate, since within a tier evidence quality is
   comparable — a like-for-like comparison.
4. **Explicit management refusal** (the sole disclosure-risk trigger) may cap a company's ranking
   tier or attach an explicit ranking-page caveat — **it must never modify the company's SPS.** This
   is unchanged from the prior final decision and is restated here as canonical, not reopened.

---

## Part 11 — Calibration-required registry

Everything below is *legitimately* deferred to the benchmark portfolio — not a loophole for
reopening structural decisions. Each row states exactly what the benchmark is supposed to determine.

| Item | What benchmark evidence determines |
|---|---|
| Dimension-specific score anchors for the ~19 dimensions marked CALIBRATION REQUIRED in Part 7 | The concrete evidence patterns that separate adjacent score bands (e.g., what distinguishes a 6 from a 7 on Market Size) — requires seeing real evidence at multiple quality levels, which the benchmark portfolio (spanning Very Weak to Elite) is designed to provide |
| Customer Growth / Revenue Growth conversion function (growth rate → 1–10 score) | No formula for this exists at all currently, only directional examples; needs real companies at known quality tiers to fit a defensible mapping |
| Growth Velocity's materiality floor, business-model window function, expansion-vs-logo distinguishing logic | All three stress-test-driven requirements (Part 2) are specified conceptually but have no numeric parameters; needs real multi-period growth data across business models, which the current 15-company set does not yet provide (0/15 coverage) |
| Burn Efficiency's deterministic-path threshold (Audit doc's proposed <1.5x, unvalidated) *and* its qualitative-fallback evidence bands (new, post-Hybrid-mode-change) | Whether the <1.5x figure, or a different one, correctly separates efficient from inefficient companies when a burn multiple is computable; separately, what qualitative evidence patterns should distinguish score bands when it isn't |
| Runway's non-linear floor-cap trigger threshold *and* its qualitative-fallback evidence bands (new, post-Hybrid-mode-change) | What months-of-runway level should be treated as existential vs. merely tight — a judgment call needing real distressed-company evidence (Tesla's crisis-event data point is informative but singular); separately, what qualitative crisis-severity evidence should map to which score when no precise months-figure is computable |
| Unit Economics' non-SaaS business-model-family numeric anchors (marketplace take-rate, insurance loss/combined ratio, hardware per-unit margin, R&D-partnership program economics) | The concrete thresholds within each newly-recognized evidence family — only the SaaS family (margin>80%, payback<12mo, LTV:CAC>3x) has a validated anchor today; the other five families are conceptually scoped (Part 7) but numerically unset |
| Partial Structural Coverage's triggering threshold (how many/which whole pillars must be entirely absent) | The point at which whole-pillar absence should surface the distinct display label rather than ordinary coverage/confidence labeling — needs real examples of both partial-pillar and whole-pillar-absent records to set defensibly |
| Ranking-tier count and boundaries | How many tiers are useful, and where confidence/coverage naturally cluster into them, given the actual distribution of evidence quality across a real company population |
| SPS-suppression coverage floor | The exact minimum-coverage percentage below which a point SPS becomes misleading rather than merely imprecise |
| Ranking-eligibility thresholds (pillar-representation fraction, coverage fraction, load-bearing pillar list, max-inferred-evidence share) | All five explicitly deferred in Final Scoring Decisions Part 2, unchanged here |
| Confidence-model's "majority of evidence-priority items" bar (Part 5's pillar-confidence rule) | What fraction actually distinguishes reliably-High from Medium pillar confidence, empirically |
| The three evidence-partition boundaries (Differentiation/Defensibility/Competitive Intensity) actually decorrelating scores in practice | Whether the partition, as specified in Part 7, produces genuinely divergent scores for companies designed to test the Betamax pattern, or whether it needs further tightening |

**Explicitly NOT on this list, because they are structural and now resolved:** the missing-evidence
state machine (Part 4), the dimension architecture and count (Part 2), the Traction/Financial Health
weight allocation (Part 3), the universal scale backbone (Part 6), the deterministic/hybrid/LLM
classification (Part 8), the aggregation mechanism (Part 9), and the ranking architecture (Part 10).
None of these should be revisited by calibration results short of a genuine new counterexample
surfacing (mirroring how the below-average-default mechanism was itself overturned) — calibration
tunes numbers within a frozen architecture; it does not redesign the architecture.

---

## Part 12 — Reproducibility contract

Given identical frozen evidence and an identical methodology version:

- **Deterministic dimensions must produce identical scores**, full stop — any variance here is a
  bug, not an acceptable tolerance, since these dimensions are pure computation once their (still
  CALIBRATION REQUIRED, per Part 11) conversion functions are fixed.
- **Hybrid dimensions should remain tightly bounded** — the deterministic core should reproduce
  exactly; the judgment layer's variance should be small. **Exact numeric tolerance: CALIBRATION /
  RELIABILITY REQUIRED** — this is precisely what the existing frozen-evidence reliability harness
  (`app/reliability/`) already measures for the prior architecture, and should be re-run against this
  specification once implemented, not invented here.
- **Constrained-LLM dimensions should be reproducible within an explicit tolerance** — a real,
  named number (e.g., "±1 point in 90% of repeated runs"), but that number must come from actually
  running the reliability harness against this specification's dimensions, not from this document
  guessing at LLM consistency. **CALIBRATION / RELIABILITY REQUIRED.**
- **Evidence-status classification should be stable** — the same evidence should resolve to the
  same one of Part 4's nine states on repeated runs; this is a correctness requirement, not a
  tolerance question, and should be zero-variance.
- **Missing evidence should resolve identically** — same requirement, zero variance, since Part 4's
  state machine is now a deterministic classification given the same evidence.
- **Aggregation must be deterministic** — Part 9's formulas are pure arithmetic over the scored set;
  given identical dimension-level outputs, the pillar and SPS outputs must be bit-for-bit identical,
  zero tolerance, no calibration needed (this is a code-correctness property, not a methodology
  question).

---

## Part 13 — Documentation debt: superseded decisions

| Superseded item | Where it lived | What supersedes it |
|---|---|---|
| Original Audit doc Part 1 MERGE/REMOVE recommendations for Differentiation, Defensibility, Competitive Intensity, Customer Demand, Adoption Potential, Business Capability, Execution Track Record, Operational Execution, Strategic Execution | `SIE_Methodology_v2_Audit.md` Part 1 | Structural Change Decision Memo's reversal, now absorbed permanently into Part 7 of this document |
| Below-average-default missing-evidence mechanism ("Case 6") | `SIE_Methodology_v2_Scoring_Semantics.md` Parts 3, 4, 10 (items 5, 7, 8) | `SIE_Methodology_v2_Missing_Evidence_Adversarial_Review.md`, permanently closed by this document's Part 4 |
| Even-split Traction weights (.25/.25/.25/.25) | Structural Change Decision Memo | This document's Part 3 |
| Even-split Financial Health weights (.25/.25/.25/.25) | Structural Change Decision Memo | This document's Part 3 |
| Execution Velocity as a single dimension, weight .20, inside Execution pillar | Structural Change Decision Memo; `SIE_Methodology_v2_Scoring_Semantics.md` Part 7's two-dimension split proposal | This document's Part 2 (Growth Velocity only, relocated to Traction) |
| 28-dimension count as previously stated (ambiguous after the unreconciled Velocity split) | Multiple documents | This document's Part 2, explicitly re-derived at 28 via a different route |
| Stage-conditional matrix's case-6 default language | `SIE_Methodology_v2_Scoring_Semantics.md` Part 3's table legend and per-cell text | This document's Part 4 — the matrix's *stage-applicability* content is still valid and carried forward into Part 7's per-dimension stage notes; only its stale aggregation-behavior language is dead |
| "Confidence-adjusted SPS" and "coverage-penalized SPS" as ranking mechanisms | Considered and rejected in `SIE_Methodology_v2_Final_Scoring_Decisions.md` Part 1 | Never adopted; restated as dead here for completeness |
| Undocumented Execution-pillar weights (.20 each, summing to .80 after Growth Velocity's relocation) | This document's own Part 2/3, prior revision | This document's Part 3 — frozen at .25 each as a conservative default, explicitly not an economically-derived allocation (see Part 3's own reasoning) |
| Unit Economics defined solely by SaaS evidence (gross margin, CAC payback, LTV:CAC) as if universal | This document's own Part 7, prior revision | This document's Part 7 — business-model-agnostic conceptual definition with explicit evidence families; the SaaS figures survive scoped to the SaaS family only |
| Burn Efficiency and Runway classified Deterministic without a qualitative fallback | This document's own Part 7/8, prior revision | This document's Part 7/8 — both reclassified Hybrid; Deterministic (7)/Hybrid (13) split becomes Deterministic (5)/Hybrid (15) |
| Customer Demand's stage rule left as "optional, superseded" without a clean exit condition, and left mechanically bound to a company's financing-round label | This document's own Part 7, prior revision | This document's Part 7 — explicit Pre-Seed/Seed Expected, Series A+ Not-Applicable lifecycle, determined by actual maturity/evidence state, not the round label alone |
| SPS display had only two states (normal / suppressed) with no distinction for whole-pillar absence | This document's own Part 9, prior revision | This document's Part 9 — new "Partial Structural Coverage" display label added, purely additive, no SPS math change |
| Evidence reuse across dimensions within one pillar had no metadata treatment, risking "N dimensions scored" being read as "N independent pieces of evidence" | Surfaced by the calibration rerun (`app/calibration/v2/calibration_rerun/`), resolved by the freeze sprint | This document's Part 15, item 6 — Evidence Independence Metadata (EIM), a metadata-only rule; no score/SPS/pillar-math change |
| Numerical anchors for Growth Velocity, Customer Growth, Revenue Growth, non-SaaS Unit Economics, and Burn Efficiency/Runway qualitative bands were entirely CALIBRATION REQUIRED with no anchor design | Part 11's registry, prior revision | This document's Part 15, items 7-8 — anchor designs classified FROZEN or FROZEN AS PROVISIONAL following Anchor Calibration Phase 1, the calibration rerun, and the freeze sprint's 4-company targeted expansion; none rejected |

The five historical documents are unedited and remain the design record of *how* these decisions
were reached — this document is the record of *what* was decided. **This table now also records
this document's own internal revisions** (the seven rows above), consistent with the instruction that
prior versions of a still-canonical document remain traceable rather than silently overwritten.

---

## Part 14 — Final readiness review

1. **Final scored dimension count:** 28.
2. **Final dimensions by pillar:** Market (5) — Market Size, Market Growth, Market Timing,
   Competitive Intensity, Customer Demand. Team (5) — Founder-Market Fit, Technical Capability,
   Business Capability, Leadership, Execution Track Record. Product (5) — Customer Value,
   Differentiation, Usability, Defensibility, Adoption Potential. Execution (4) — Go-to-Market
   Execution, Product Execution, Operational Execution, Strategic Execution. Traction (5) —
   Customer Growth, Revenue Growth, Retention, Engagement, Growth Velocity. Financial Health (4) —
   Revenue Quality, Unit Economics, Burn Efficiency, Runway.
3. **Final structural dimension weights:** Execution — Go-to-Market Execution .25 / Product
   Execution .25 / Operational Execution .25 / Strategic Execution .25 (frozen conservative default,
   explicitly not economically derived — see Part 3). Traction — Retention .25 / Revenue Growth .25
   / Growth Velocity .20 / Customer Growth .15 / Engagement .15. Financial Health — Runway .30 / Unit
   Economics .25 / Burn Efficiency .25 / Revenue Quality .20 (plus the non-linear runway-floor cap
   rule). Market, Team, and Product's internal weights unrevised (out of scope for this pass).
4. **Final scoring-mode classification:** 5 Deterministic, 15 Hybrid, 8 Constrained LLM (Part 8) —
   revised from the original 7/13/8 split following the post-PASS-A reclassification of Burn
   Efficiency and Runway to Hybrid.
5. **Canonical missing-evidence rule:** unknown must never become weak; nine canonical states (Part
   4); Usually-Private and Expected-But-Unavailable are arithmetically identical, differing only in
   flag severity; below-average-default is permanently dead.
6. **Canonical aggregation rule:** scored-set-only weighted averages at both dimension→pillar and
   pillar→SPS levels, zero defaults for excluded members, ordinal (not averaged) confidence
   propagation (Part 9).
7. **Universal 0–10 semantics:** frozen backbone, Part 6 — 5 is stage-relative-neutral, 0 is reserved
   for evidence-backed disqualifying findings and never a stand-in for absence.
8. **Calibration-required items:** the full registry in Part 11 as originally scoped at the time of
   this Readiness Review. **Superseded by Part 15, items 7-8**: following the completed calibration
   program, the growth-conversion architecture, the Burn Efficiency/Runway qualitative bands, and two
   of the five Unit Economics withholding rules are now classified FROZEN or FROZEN AS PROVISIONAL,
   not merely CALIBRATION REQUIRED — see Part 15 for the current, authoritative anchor status. Items
   not mentioned in Part 15 (ranking/suppression/eligibility numeric boundaries, reliability
   tolerances, the Partial Structural Coverage triggering threshold) remain CALIBRATION REQUIRED as
   originally stated here.
9. **Superseded decisions:** Part 13's table, fifteen items (eight from the original consolidation
   pass, seven recording this document's own post-PASS-A and post-calibration-program structural
   revisions).
10. **Remaining true structural unknowns:** none identified that rise to the level of blocking
    implementation — every open item found during this pass resolved to either a firm structural
    decision (this document) or a legitimately calibration-dependent numeric value (Part 11). The
    one soft caveat: the four pillars not revisited in this pass (Market, Team, Product's internal
    weights) were never flagged as conflicted by the Readiness Review and are presumed structurally
    sound by inheritance from the original production methodology — this document does not
    re-derive them from an investment question the way Part 3 did for Traction/Financial Health, and
    a future pass could choose to do so for full consistency, though nothing found here requires it.
11. **Is another methodology-design pass necessary?** No, for structural purposes. A future pass
    *is* necessary once real calibration data exists, but its scope is populating Part 11's
    registry, not revisiting this document's architecture, per Part 11's explicit boundary.

## METHODOLOGY V2 STRUCTURALLY FROZEN: **YES**

## METHODOLOGY V2 READY FOR BLIND NUMERICAL CALIBRATION: **YES**

Every remaining unknown identified across this entire review-and-resolution sequence is now either
resolved as a structural decision in this document, or is explicitly named in Part 11 as the kind of
numeric threshold the benchmark portfolio exists to determine — nothing left open requires inventing
methodology mid-calibration. Blind calibration (the three-pass protocol from the Readiness Review:
score blind to `expected_quality_tier`, then reveal and analyze disagreement, then validate against
`future_outcome` only after methodology is frozen — which it now is) may begin against the 15-company
calibration set once explicitly authorized, using this document as the sole scoring specification.

---

## Part 15 — Calibration program closure: pre-holdout freeze checkpoint

This part records the outcome of the full blind-calibration program (PASS A → targeted PASS A
rerun → PASS B → Anchor Calibration Phase 1 → the calibration rerun → the final pre-holdout freeze
sprint) as an explicit, citable checkpoint for PASS C. It documents *what was decided and found*; it
does not itself decide anything new — every substantive change referenced here was authorized and
made in the corresponding calibration-program turn, in the artifacts named below, not in this edit.

**1. Methodology version:** `v2-spec-2026-08-23` (this document), scored throughout calibration under
contract `v2-calibration-rerun-2026-08-23` (see `app/calibration/v2/calibration_rerun/run_contract.json`).

**2. Final 28 scored dimensions:** unchanged from Part 14, item 2 — Market (5), Team (5), Product (5),
Execution (4), Traction (5), Financial Health (4).

**3. Frozen pillar weights:** Market **.20**, Team **.20**, Product **.20**, Execution **.15**,
Traction **.15**, Financial Health **.10** (Part 3). Unchanged throughout the entire calibration
program — PASS B found no empirical case for a weight change (94.5% cross-tier concordance on the
15-company set), and the freeze sprint's expansion likewise surfaced none; see Part 9 of the
calibration-rerun report and Part 9 of the Phase-1 report for the explicit no-change reasoning.

**4. Frozen internal dimension weights (all six pillars, for completeness — Part 14 item 3 stated
only the three pillars revised during this program):**
- Market: Market Size **.25**, Market Growth **.20**, Market Timing **.20**, Competitive Intensity
  **.15**, Customer Demand **.20**.
- Team: Founder-Market Fit **.25**, Technical Capability **.20**, Business Capability **.20**,
  Leadership **.20**, Execution Track Record **.15**.
- Product: Customer Value **.25**, Differentiation **.20**, Usability **.15**, Defensibility **.20**,
  Adoption Potential **.20**.
- Execution: Go-to-Market Execution **.25**, Product Execution **.25**, Operational Execution **.25**,
  Strategic Execution **.25** (frozen conservative default, Part 3).
- Traction: Retention **.25**, Revenue Growth **.25**, Growth Velocity **.20**, Customer Growth **.15**,
  Engagement **.15**.
- Financial Health: Runway **.30**, Unit Economics **.25**, Burn Efficiency **.25**, Revenue Quality
  **.20**.

**5. Final scoring modes:** unchanged from Part 14, item 4 — 5 Deterministic, 15 Hybrid, 8 Constrained
LLM.

**6. Evidence-concentration semantics (new this checkpoint — Evidence Independence Metadata, "EIM"):**
When a real-world fact/event is cited by two or more *scored* dimensions within the same pillar for
the same company, the aggregation layer's *output metadata* — never its score — should additionally
report: (a) `effective_independent_dimensions`, the count of distinct underlying evidence-events
among that pillar's scored dimensions, which is ≤ the raw scored-dimension count; (b) a parallel
`independent_coverage_pct` metric, computed alongside (not replacing) the existing `coverage_pct`;
(c) a pillar may reach **High** confidence only if `independent_coverage_pct`, not merely raw
coverage, also clears the existing 0.6 gate; (d) dimension pairs whose shared evidence is thin enough
that the two scores are, in substance, a restatement of one fact (not merely two legitimate angles
on it) should carry an explicit `possible_semantic_duplication: true` tag. **This affects presentation
metadata only — dimension score, pillar score, SPS, Partial Structural Coverage, ranking eligibility,
and the existing `diligence_flag_count` metric are explicitly and permanently unaffected.** Full
design, the four-way evidence classification it rests on, and stress tests against Tesla, Shopify,
and Oscar Health live in `app/calibration/v2/freeze_sprint/PART1_2_evidence_concentration.md`. This
is a specification-level rule (a *should*, describing what the aggregation output ought to expose),
not yet an implemented code change — no aggregation code in this repository computes EIM fields
today; implementing it is future, separately-authorized work.

**7. Anchors classified FROZEN** (safe, adequately tested, no further validation required before
release):
- Growth Velocity / Customer Growth conversion architecture (materiality floor → annualized CAGR →
  scale-tiered bands, including the short-window dampening rule) — tested across 4 companies and 3
  business-model families (SMB SaaS/platform, commerce/DTC, hardware) in the freeze sprint, with the
  short-window rule itself twice actually invoked, not merely defined.
- Qualitative Burn Efficiency band architecture (5-tier: poor/weak/credible/strong/exceptional).
- Qualitative Runway band architecture (6-tier, including the near-insolvency-unresolved vs.
  near-insolvency-just-addressed distinction).
- Marketplace Unit Economics "take-rate alone is insufficient" withholding rule.
- Commerce/DTC Unit Economics "thesis is not outcome" withholding rule.

**8. Anchors classified FROZEN AS PROVISIONAL** (safe enough to ship in v2; explicitly lower-confidence
and calibration-limited; do not block v2 release or holdout validation; may be refined by future
benchmark expansion without another structural review):
- Growth Velocity / Customer Growth exact scale-tier absolute cutoffs (architecture is FROZEN per
  item 7; the specific numeric tier boundaries are tested only at "large" scale and only for 3 of 8
  named business-model families).
- Insurance Unit Economics qualitative-disclosure threshold (tested twice — Oscar Health's
  qualitative-only case and Lemonade's quantified 166%-loss-ratio case — behaving sensibly relative
  to each other, but still a two-data-point rule).
- Commerce/DTC and hardware Unit Economics "insufficient combination" withholding rules (the
  *withholding* behavior is validated by real test cases; neither family has yet produced an actual
  positive score).
- Qualitative Burn Efficiency and Runway exact score-within-band placement (the band *architecture*
  is FROZEN per item 7; the precise number chosen within a band remains single-analyst judgment,
  not cross-validated by a second scorer).
- Marketplace Unit Economics / Customer Growth family-selection logic (correctly identifies the
  right unit — GMV or transacting-count over raw participant count — but has not yet produced an
  actual score in any tested case; the genuinely least-improved family in this program).

No anchor was classified REJECT at any point in this program.

**9. Known limitation, explicitly carried forward, NOT resolved before holdout:** Customer Growth
and Growth Velocity, whenever both are scoreable for the same company, have in every tested instance
(Shopify, Dollar Shave Club, Peloton, Lemonade — 4 for 4) cited the identical underlying growth
series. This is flagged under item 6's `possible_semantic_duplication` tag and is the top candidate
for a future dimension-definition review. **This document's dimension architecture is not being
changed to address it before holdout validation** — per this program's explicit scope boundary,
dimension definitions were out of scope for the freeze sprint, and no structural or empirical case
was found rising to the bar (Part 7 of the freeze-sprint report) that would justify reopening
dimension architecture now. It is recorded here so PASS C and any future methodology-design pass
inherit it as a known, not a rediscovered, issue.

**10. Holdout integrity:** the five holdout companies (Fab.com, Rdio, Homejoy, DoorDash, Zenefits)
have never been opened, read, scored, or referenced by content (only by name, in quarantine
confirmations) at any point across this entire calibration program — PASS A, the targeted rerun,
PASS B, Anchor Calibration Phase 1, the calibration rerun, and the freeze sprint. `future_outcome`
and `benchmark_notes` were never inspected for any calibration-set company either. Enforcement
mechanism: `app/calibration/v2/blind_loader.py`'s manifest-driven `set == "calibration"` filter,
which raises `HoldoutAccessError` on any holdout-file load attempt, guarded by the 7 passing tests in
`app/calibration/v2/test_blind_loader.py`.

**11. Calibration program artifact index** (all diagnostic-only; none feed the production scoring
pipeline in `app/ai/` or `app/workflows/`):
- `app/calibration/v2/pass_a/` — blind scoring (blind_inputs, results, aggregate, run_metadata).
- `app/calibration/v2/pass_a/targeted_rerun/` — post-repair targeted rescoring with full provenance.
- `app/calibration/v2/pass_b/` — tier reveal and disagreement diagnostics.
- `app/calibration/v2/anchor_calibration/phase1/` — first anchor-design pass and its simulation.
- `app/calibration/v2/calibration_rerun/` — full 15-company rerun under one frozen contract, plus
  the evidence-event provenance registry and reproducibility spot-check.
- `app/calibration/v2/freeze_sprint/` — evidence-concentration resolution, the 4-company targeted
  benchmark expansion, and the anchor FREEZE/FREEZE-AS-PROVISIONAL/REJECT audit.
- `app/calibration/freeze_manifest.json` — the machine-readable checkpoint summary (this Part 15 in
  structured form).

## METHODOLOGY V2 CALIBRATION PROGRAM CLOSED: **YES**

## HOLDOUT SET UNTOUCHED THROUGHOUT CALIBRATION: **YES**

## READY FOR PASS C HOLDOUT VALIDATION: **YES**

This checkpoint records a completed, internally consistent calibration program. It authorizes
nothing by itself — PASS C (holdout scoring against `future_outcome`) still requires its own
separate, explicit authorization before any holdout file is opened.
