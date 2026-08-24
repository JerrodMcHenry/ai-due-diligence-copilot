# SIE Methodology v2 — Calibration & Scoring Design Audit

**Status: design document only. No code changed, no calibration run, no expected scores
changed, nothing committed.** This audits the methodology as encoded in
`app/ai/scoring_methodology.py` (30 `ScoringDimension` entries, `SCORING_VERSION = "1.0"`)
against the goal of making SIE defensible, calibrated, stage-aware, and capable of
distinguishing weak from elite startups. Canonical pillar weights (Market .20, Team .20,
Product .20, Execution .15, Traction .15, Financial Health .10) are **not** revisited here —
they are out of scope and were ratified separately.

Ground truth used: the full text of every `ScoringDimension` in `scoring_methodology.py`
(read in full for this audit), and the stored Stripe Series A calibration fixture
(`app/calibration/reports/stripe_series_a.json`, `app/calibration/expected_scores.py`).

---

## Part 1 — Full 30-dimension audit

For each dimension: what it measures, what evidence is realistically obtainable, whether the
`evidence_requirement` tag matches reality, whether the dimension can be objectively anchored,
its recommended scoring architecture, and a keep/revise/merge/split/conditional/remove call.
Architecture classification reuses the categories established in the prior Numerical Scoring
Stability investigation: **Deterministic** (computable from extracted facts, no LLM judgment
needed), **Hybrid** (deterministic core + LLM judgment layer), **LLM** (irreducibly qualitative).

### Market (Size .25 / Growth .20 / Timing .20 / Competitive Intensity .15 / Customer Demand .20)

**1. Market Size** — *Public, w.25*
Measures realistic venture-scale addressable market. Evidence actually available: buyer-segment
size, budget category, expansion paths — all *inferential*, not documentary. The description
itself says "infer... from customer segment, buyer budget," which contradicts the **Public** tag.
This is the same tag/reality mismatch the Public Evidence Validation Consistency Fix already
patched for symptoms — the root cause (wrong tag) remains. Overlaps Market Growth (both cite
"large recurring spend category") and Competitive Intensity (wedge-to-market narrative).
Missing-evidence-as-weakness risk: **high**. Anchorable: partial (segment/category can be
tiered; "credible expansion" stays qualitative). **Architecture: Hybrid. Recommendation: REVISE**
— retag Public → Inferred; keep weight.

**2. Market Growth** — *Public, w.20*
Measures category growth, explicitly *not* company growth — but the only evidence usually
present in `company_text` or Tavily results *is* company growth or generic trend language ("AI
adoption"). `evidence_priority` lists "company growth as supporting evidence" fourth, directly
undercutting the dimension's own instruction not to conflate the two. This is the confirmed
mechanism behind double-counting pair #1 (§2). Third-party category-growth data (Gartner/IDC-style)
is almost never present in the inputs this system receives. Missing-evidence risk: **high**.
Realistic as tagged: **no**. Anchorable: no (no quantitative bar exists; a rate threshold would be
fake precision without a cited source). **Architecture: LLM. Recommendation: REVISE** — define an
explicit lower-confidence "proxy-derived" path (macro trend words + company growth, capped below
what a cited report would justify) instead of forcing Unavailable, while tightening the boundary
against Traction so the same growth number isn't independently re-scored twice.

**3. Market Timing** — *Public, w.20*
Measures "is now the right moment." Explicitly warns against trusting founder "why now" narrative
as proof — but that narrative is nearly the only evidence usually available, so the dimension is
structurally torn between its own instruction and its own evidence supply. Heavy overlap with
Market Growth (same tailwind) and Customer Demand (urgency). Not objectively anchorable — pure
adjective ladder. **Architecture: LLM. Recommendation: MERGE candidate** — fold into Market Growth
as "Market Growth & Timing," or at minimum retag Inferred and shrink weight.

**4. Competitive Intensity** — *Public, w.15*
Measures whether the company can win despite competitors. Best-written anti-bias framing in the
Market pillar ("do not penalize simply because competitors exist"). Win/loss data is rarely
public; competitor identification usually is (via Tavily), so this is *more* evidence-available
than Timing/Growth. Near-total conceptual overlap with Product/Differentiation and
Product/Defensibility — all three ask a version of "why won't a competitor win instead" from
three pillar angles. This is the clearest triple-overlap in the methodology (double-counting
pairs #4/#5, §2). **Architecture: Hybrid. Recommendation: MERGE/CONSOLIDATE** into a single
"Competitive Position" construct with Differentiation and Defensibility (§2).

**5. Customer Demand** — *Inferred, w.20*
Measures whether customers genuinely want the product, using paying customers/revenue
growth/retention/expansion/usage as evidence — i.e., exactly Traction's evidence set, restated
under Market. Correctly tagged Inferred and well-evidenced when data exists, but this is the
single most severe double-counting offender in the methodology (pair #2, §2): it re-rewards facts
Traction already scores, at a full 20% Market weight on top of Traction's own weight for the same
facts. **Architecture: Hybrid. Recommendation: MERGE/REMOVE** — remove as an independent Market
subscore, or narrow strictly to pre-revenue demand signal (LOIs, waitlist, pilot conversion) so it
stops re-scoring post-revenue metrics Traction already owns.

### Team (Founder-Market Fit .25 / Technical Capability .20 / Business Capability .20 / Leadership .20 / Execution Track Record .15)

**6. Founder-Market Fit** — *Public, w.25*
Measures founders' domain insight/experience. Genuinely one of the most Public-evidence-friendly
dimensions (bios, prior companies are usually searchable) — correctly tagged and correctly the
pillar's highest-weighted dimension. Moderate overlap with Execution Track Record (repeat-founder
signal appears in both — pair #6, §2). Missing-evidence risk: low-medium; when genuinely
Unavailable (thin public profile) that is itself a legitimate weak signal, not a false negative.
Anchorable: partial (prior-founder/prior-exit are checkable booleans; "deep customer insight" is
qualitative). **Architecture: Hybrid. Recommendation: KEEP**, tighten anchors (§4).

**7. Technical Capability** — *Inferred, w.20*
Measures build/scale ability relative to product complexity. Correctly tagged; good explicit
anti-AI-hype-inflation warning (rare in the methodology, worth replicating elsewhere). Moderate,
unnamed-but-real overlap with Product/Product Execution ("shipped, reliable, integrated" appears
in both). Anchorable: partial (shipped-feature/integration counts are countable; "reliability"
isn't without uptime data). **Architecture: Hybrid. Recommendation: KEEP**, but explicitly
distinguish from Product Execution in both descriptions: Technical Capability = "can they,"
Product Execution = "did they, how well."

**8. Business Capability** — *Inferred, w.20*
Measures commercial/operational company-building capability via "GTM learning, revenue execution,
pricing, unit economics, operating discipline" — a direct restatement of GTM Execution's and Unit
Economics' evidence sets, applied to the Team pillar instead. This is the exact NovaLedger
forensic-audit failure mode (revenue/customer growth disclosed, dimension still Unavailable) —
already partially mitigated by the Public Evidence Validation Consistency Fix, but the root cause
is architectural (asking the model to infer *capability* from *outcomes*, a causal-inference step
it can't reliably make: strong growth could reflect a hot market, not team skill), not just a
validator bug. Confirmed double-counting pair #7, §2. Not objectively anchorable.
**Architecture: LLM. Recommendation: MERGE** into GTM Execution + Unit Economics' evidentiary
base, narrowing Business Capability to non-outcome signals only (pricing-strategy clarity,
commercial hiring, stated GTM thesis) — or **REMOVE** and redistribute weight to Founder-Market
Fit and Leadership if narrowing isn't practical.

**9. Leadership** — *Inferred, w.20*
Measures ability to lead/hire/scale. Already reasonably stage-gated in its own text ("do not
over-penalize missing org charts at early stages") — one of the better-designed dimensions as
written. Low-moderate overlap with Founder-Market Fit and Strategic Execution (pair #12, §2).
Missing-evidence risk: medium at pre-seed/seed (single-founder companies genuinely have nothing
to observe yet — legitimately Unavailable, not weak). Anchorable: partial (team size, exec-hire
count, hire tenure are countable; "decision quality" is not). **Architecture: Hybrid.
Recommendation: KEEP**, made explicitly **CONDITIONAL** at pre-seed (§3).

**10. Execution Track Record** — *Inferred, w.15*
Measures demonstrated milestone achievement — again nearly identical facts to Traction (Revenue
Growth, Customer Growth) and Execution/Execution Velocity, viewed as "has *this team* executed"
rather than "is *the business* growing." Confirmed double-counting pair #6 (with Founder-Market
Fit, via the repeat-founder signal) and an unnamed-but-real overlap with Execution Velocity.
**Architecture: Hybrid. Recommendation: MERGE** with Execution/Execution Velocity (near-duplicate
question asked from two pillars); remove from Team and redistribute its 0.15 weight to
Founder-Market Fit and Leadership, the genuinely Team-specific dimensions.

### Product (Customer Value .25 / Differentiation .20 / Usability .15 / Defensibility .20 / Adoption Potential .20)

**11. Customer Value** — *Inferred, w.25*
Measures pain severity/ROI/measurable value. Correctly the pillar's top-weighted dimension
("does it matter" is the right anchor question). Evidence (ROI, retention, expansion) overlaps
Traction/Retention and Financial/Revenue Quality. Anchorable: partial (ROI%/retention numbers are
quantifiable when disclosed; "mission-critical" is qualitative). **Architecture: Hybrid.
Recommendation: KEEP** as the pillar anchor, but stop re-listing NRR/churn as primary evidence
(that belongs to Retention) — ask instead for pain-severity/ROI-specific evidence (cost/time
saved, workflow displaced) distinct from the retention number itself.

**12. Differentiation** — *Public, w.20*
Measures meaningful difference from alternatives via customer-recognized advantage — same
evidence set as Competitive Intensity, from the product's side. Good anti-bias note (AI ≠
differentiation). Confirmed double-counting pair #4, §2. Missing-evidence risk: high — proving
customers *recognize* a difference needs interviews, which public pipelines never have; "Public"
is realistic only for the wedge *claim*, not proof customers care. Not objectively anchorable.
**Architecture: LLM. Recommendation: MERGE** into a single "Competitive Position" dimension with
Competitive Intensity (and Defensibility, below) — see §2 — or sharply narrow to
feature-level distinctiveness only.

**13. Usability** — *Public, w.15*
Flagged by the requester for dedicated resolution — full treatment in Part 5. Measures onboarding
friction; the tag/reality mismatch (Public, but time-to-value/activation data is almost never
public) is its core defect, already confirmed unstable in the prior investigation.
**Architecture: currently LLM, should become Hybrid post-redesign. Recommendation: REDEFINE (§5).**

**14. Defensibility** — *Inferred, w.20*
Measures moat durability (switching costs, data, lock-in, network effects). Well-written, good
"patents not required" anti-bias note. Same evidentiary set as Differentiation and Competitive
Intensity, applied a third time. Confirmed double-counting pair #5, §2. Not objectively
anchorable (durability-over-time is inherently a judgment call). **Architecture: LLM.
Recommendation:** if the three-way Competitive Position merge (§2) is adopted, Defensibility is
the "durability over time" angle within it; if the three stay separate, **MERGE** with the other
two.

**15. Adoption Potential** — *Inferred, w.20*
Measures whether adoption can scale across users/teams/markets, using expansion
revenue/churn/multi-seat usage — near-identical to the Traction pillar wholesale. Confirmed
double-counting pair #3, §2 — when Traction data exists this dimension is trivially derivable
from it, which is precisely the problem: the same facts get scored twice under different pillar
labels. Anchorable: yes (same numeric levers as Traction). **Architecture: Hybrid, but should be
derived from Traction's already-extracted facts rather than independently re-extracted.
Recommendation: MERGE/REMOVE** — replace with a narrower "expansion surface" question (how many
distinct use-cases/teams/geographies could this product plausibly reach, independent of current
metrics), which is genuinely product-specific and not already owned by Traction.

### Execution (GTM .20 / Product Execution .20 / Operational Execution .20 / Strategic Execution .20 / Execution Velocity .20)

Note: unlike Market/Product/Team, Execution has no primary/secondary weighting — all five
dimensions sit flat at 20%. Traction and Financial Health share this flat pattern. This is a
design inconsistency worth flagging on its own (Item 12, Part 10) — every other pillar signals
"this sub-question matters most," Execution/Traction/Financial Health don't.

**16. Go-to-Market Execution** — *Inferred, w.20*
Measures repeatable customer acquisition (CAC payback, pipeline, sales cycle). This data is
genuinely Private-tier in reality (CAC/payback almost never public), so "Inferred" splits the
difference but still overclaims availability pre-Series-B. Confirmed double-counting pair #7,
§2. Well-anchored when data exists (explicit numeric benchmark: "CAC payback under 12 months is
excellent"). **Architecture: Deterministic-when-available / Hybrid otherwise. Recommendation:
KEEP** as the authoritative "can the team sell" dimension; absorb Business Capability's
overlapping claim on this evidence (§2).

**17. Product Execution** — *Inferred, w.20*
Measures delivery quality (shipped product, reliability, customer outcomes). Reasonable overlap
with Technical Capability (Team) and Customer Value (Product) — not one of the 12 named pairs but
a real sibling relationship. Anchorable: partial (feature/integration counts yes; "reliability"
without uptime data no). **Architecture: Hybrid. Recommendation: KEEP**, but cross-reference
Technical Capability explicitly: Product Execution = cadence/delivery, Technical Capability =
capability ceiling.

**18. Operational Execution** — *Private, w.20*
Measures burn discipline, margins, hiring, process — literally the same facts as
Financial/Burn Efficiency and Financial/Unit Economics, viewed from an "execution" lens. Its own
guidance ("don't over-penalize missing process detail if financial metrics are strong") admits
it's parasitic on Financial Health's data. Confirmed double-counting pair #11, §2. Correctly
tagged Private (so Unavailable is legitimately common — appropriate as tagged) but redundant.
Well-anchored (burn multiple, gross margin — same anchors as Financial pillar).
**Architecture: Deterministic-when-available. Recommendation: MERGE/REMOVE** — fold into
Burn Efficiency; if Execution needs a distinct "operational discipline" signal, narrow it to
hiring-plan/process maturity only, explicitly excluding burn/margin.

**19. Strategic Execution** — *Inferred, w.20*
Measures strategic soundness (positioning, sequencing, wedge, use of capital). Evidence
(competitive-response strategy, capital-allocation rationale) is essentially never disclosed
pre-Series-B — one of the weakest-grounded dimensions in the methodology. Overlaps
Competitive Intensity (wedge) and Leadership (decision quality) — confirmed pair #12, §2. Not
objectively anchorable; "coherent," "logical expansion" are vague even by this methodology's own
adjective-ladder standard. **Architecture: LLM. Recommendation: MERGE** with Leadership (per pair
#12) or **REMOVE** and redistribute weight — without direct evidence this dimension is mostly the
model narrating a wedge story it already extracted for Competitive Intensity.

**20. Execution Velocity** — *Inferred, w.20*
Measures speed relative to stage via revenue/customer growth rate and hiring momentum — a
restatement of Traction's growth metrics plus Team's Execution Track Record. Confirmed
double-counting adjacency with Traction/Revenue Growth, Traction/Customer Growth, and pair #6's
cluster. Fully derivable as **growth-rate normalized by company age** — a computable ratio, not
an independently-elicited LLM judgment. **Architecture: Deterministic (once derived).
Recommendation: REVISE** into a derived metric from already-extracted Traction facts + company
age; removes both the duplication and the instability in one move.

### Traction (Customer Growth .20 / Revenue Growth .20 / Retention .20 / Engagement .20 / Commercial Validation .20)

**21. Customer Growth** — *Public, w.20* — established deterministic candidate.
Genuinely often disclosed, correctly tagged, well-anchored (explicit example: "42 enterprise
accounts can be very strong for Series A"). One of the two or three best-designed dimensions in
the whole methodology as written. Overlaps Market Growth (pair #1) and Revenue Growth (pair #8).
**Architecture: Deterministic. Recommendation: KEEP.**

**22. Revenue Growth** — *Public, w.20* — deterministic candidate.
Same treatment; mathematically close to Customer Growth when ACV is roughly stable (Revenue
Growth ≈ Customer Growth × ACV growth) — confirmed pair #8, §2, but a *structural* coupling, not
a design flaw, since both remain individually meaningful. **Architecture: Deterministic.
Recommendation: KEEP**, but consider blended scoring (weighted by ACV volatility) rather than two
fully independent 20% weights measuring largely one underlying growth curve.

**23. Retention** — *Public, w.20* — deterministic candidate.
The single best-anchored dimension in the entire methodology (explicit numeric thresholds:
NRR>130% excellent, GRR>90% strong, logo churn<1.5%/mo strong). Confirmed pair #9 is on
inspection the **weakest** of the 12 named pairs — Retention (do they stay) and Usability (is it
easy to start) are causally related but not the same measurement. The real leak is narrower:
Usability's own `common_mistakes` explicitly instructs "do not ignore retention as a usability
proxy," directly telling the model to reuse Retention's number as Usability evidence.
**Architecture: Deterministic. Recommendation: KEEP** unchanged as the reference dimension;
**REMOVE** the retention-as-usability-proxy language (§5) to close the actual leak without
touching either dimension's core design.

**24. Engagement** — *Inferred, w.20*
Measures usage depth/frequency. Correctly tagged Inferred, and by explicit design substitutes
Retention/NRR when usage telemetry is absent ("retention, expansion... can substitute") — which is
most of the time, making Engagement functionally a second read of Retention for the majority of
inputs. This is the substitution *rule itself* creating a silent double-count, distinct from
Usability's overt one. Not objectively anchorable once reduced to the proxy case.
**Architecture: LLM when real usage data exists, redundant-deterministic when it doesn't.
Recommendation: CONDITIONAL/MERGE** — make Engagement explicitly conditional on true usage
evidence; if absent, mark Unavailable rather than silently borrowing Retention's number a second
time, or merge into Retention as one "Stickiness" dimension.

**25. Commercial Validation** — *Inferred, w.20*
Measures convincing commercial proof — but its qualifying evidence (paying customers = Customer
Growth, renewals = Retention, unit economics = Financial Health, ACV/pricing = Revenue Growth) is
a near-total roll-up of the rest of the pillar plus Financial Health, scored a second time at full
20% weight. It is almost structurally impossible for this to disagree with the pillar's other four
subscores, since it's built from the same facts — which is exactly why it should not be an
independently-elicited dimension. **Architecture: should be a derived composite, not
LLM-prompted. Recommendation: REMOVE** as independently elicited; redistribute its 20% weight
across Customer Growth/Revenue Growth/Retention, since empirically it adds no orthogonal
information — it restates the pillar's own summary.

### Financial Health (Revenue Quality .20 / Unit Economics .20 / Burn Efficiency .20 / Runway .20 / Fundraising Readiness .20)

**26. Revenue Quality** — *Inferred, w.20*
Measures durability/recurringness (NRR/GRR/concentration) — the same numeric evidence as
Traction/Retention, viewed through a "financial durability" instead of "customer behavior" lens
(both dimensions even use "132% NRR" as their canonical `benchmark_examples` string, verbatim).
Real, close sibling overlap, though not one of the 12 named pairs. Well-anchored (thresholds
transfer directly from Retention). **Architecture: Deterministic-when-available. Recommendation:
REVISE** — narrow to the genuinely distinct input (customer concentration, contract-term
durability) and derive the NRR/GRR component from Traction/Retention's already-extracted number.

**27. Unit Economics** — *Public, w.20* — deterministic candidate, **but mistagged**.
Best-anchored dimension alongside Retention (margin>80% excellent, payback<12mo excellent,
LTV:CAC>3x strong) — but CAC/margin data is almost never actually public pre-Series-B; this
mirrors the Market Size mistag pattern exactly. High-severity finding: this dimension was very
likely **not** in scope of the already-shipped Public Evidence Validation Consistency Fix (which
covered Market Size, Market Growth, Usability), meaning it may still be hitting the hard
Public+Unavailable rejection in production for a dimension whose real evidence tier is
Private/Inferred. Confirmed overlap with GTM Execution (CAC payback appears in both
`benchmark_examples`, verbatim) and Burn Efficiency (margin). **Architecture: Deterministic.
Recommendation: REVISE** — retag Public → Private (or at minimum Inferred); flag as a
high-priority follow-up audit against live production data, same category as the shipped fix.

**28. Burn Efficiency** — *Private, w.20* — deterministic candidate, correctly tagged.
Confirmed pair #11 (with Operational Execution, §2). **Architecture: Deterministic.
Recommendation: KEEP** as the canonical burn-efficiency dimension; absorb Operational Execution's
overlapping burn/margin content here.

**29. Runway** — *Public, w.20* — deterministic candidate, correctly tagged (months of
cash/burn is usually stated or computable). Confirmed pair #10, but on inspection this is the
**second** of the 12 pairs that is mostly a legitimate proxy relationship rather than true
double-counting: Runway is a hard computable fact; Fundraising Readiness treats it as one input
among many (growth, team, market), not as its primary construct. **Architecture: Deterministic.
Recommendation: KEEP**; tighten Fundraising Readiness's description to explicitly treat Runway's
own score as an input rather than re-deriving a runway sub-judgment.

**30. Fundraising Readiness** — *Inferred, w.20*
Measures whether the company is positioned to raise its next round, using growth, retention,
team, market, and use of funds as evidence — an explicit roll-up of nearly every other pillar's
output. Structurally similar to Commercial Validation's problem: it is closer to "a second,
narrower opinion on the whole SPS" than a fifth co-equal Financial Health input. Not objectively
anchorable by design (inherently holistic). **Architecture: LLM, but structurally redundant.
Recommendation: CONDITIONAL/REVISE** — either (a) reframe as a genuinely distinct "investor
narrative quality" judgment, decoupled from re-deriving Growth/Retention/Team facts, or (b) demote
from a Financial Health pillar subscore to a standalone investability-narrative flag on the final
SPS output.

---

## Part 2 — Double-counting audit: the 12 named pairs

| # | Pair | Verdict | Mechanism |
|---|------|---------|-----------|
| 1 | Market Growth vs Customer Growth | **Confirmed, moderate** | Market Growth's `evidence_priority` explicitly allows "company growth as supporting evidence," so Customer Growth's own number leaks into Market Growth's score under a different label. |
| 2 | Customer Demand vs Traction | **Confirmed, severe** | Customer Demand's evidence set (paying customers, revenue growth, retention, expansion) *is* Traction's evidence set, scored again at 20% Market weight. |
| 3 | Adoption Potential vs Traction | **Confirmed, severe** | Same mechanism as #2 — expansion revenue/churn/multi-seat usage are Traction facts re-scored under Product. |
| 4 | Differentiation vs Competitive Intensity | **Confirmed, severe** | Both ask "why does this company win vs. alternatives" from Product vs. Market angles, using overlapping wedge/customer-recognition evidence. |
| 5 | Defensibility vs Competitive Intensity | **Confirmed, severe** | Both cite switching costs, lock-in, and distribution advantage as primary evidence — three-way cluster with #4. |
| 6 | Founder-Market Fit vs Execution Track Record | **Confirmed, moderate** | Repeat-founder / prior-exit signal is explicitly a strong-signal in both dimensions' lists. |
| 7 | Business Capability vs GTM Execution | **Confirmed, severe** | Business Capability's own description names GTM learning, revenue execution, pricing, and unit economics as its evidence — GTM Execution's and Unit Economics' domains verbatim. |
| 8 | Revenue Growth vs Customer Growth | **Confirmed, structural (tolerable)** | Mathematically coupled via ACV, not a design flaw — both individually meaningful; recommend blended scoring, not removal. |
| 9 | Retention vs Product Usability | **Partially confirmed — legitimate proxy, one leak** | Causally related (poor usability → churn) but not the same measurement. The actual leak is a single guidance line in Usability telling the model to reuse Retention's number as Usability evidence. |
| 10 | Runway vs Fundraising Readiness | **Mostly legitimate** | Runway is one of several inputs to Fundraising Readiness's holistic judgment, not a duplicate construct. Needs only a boundary clarification. |
| 11 | Operational Execution vs Burn Efficiency | **Confirmed, severe** | Operational Execution's own guidance admits it defers to financial metrics when process detail is missing — it's parasitic on Burn Efficiency's evidence. |
| 12 | Strategic Execution vs Leadership | **Confirmed, severe** | Both use decision-quality and positioning as primary evidence, without genuinely distinct source facts for either. |

**Net finding: 8 of 12 pairs are confirmed severe/moderate double-counting, 1 is a tolerable
structural coupling, 2 are mostly legitimate proxy relationships needing only description
tightening, 0 are unfounded.** This is a strong, unambiguous signal that the methodology has real,
fixable double-counting, concentrated in three clusters: (a) Market/Product "why do they win"
(pairs 4, 5, and Competitive Intensity itself), (b) Team/Execution "did/can this team execute"
(pairs 6, 7, 12, plus unnamed Execution Track Record ↔ Execution Velocity), and (c) cross-pillar
Traction leakage into Market and Product (pairs 1, 2, 3).

---

## Part 3 — Stage-aware methodology evaluation

The existing `stage_guidance` text is directionally reasonable per-dimension but does not
currently gate *whether a dimension counts toward the pillar average at all* — a dimension that
is legitimately unknowable at a given stage is still nominally part of a 5-way (or in
Market's case, unequal) weighted average, and only the evidence/scoring separation architecture's
`evidence_status: Unavailable` + confidence machinery softens this, not stage awareness itself.

**Dimensions that should become explicitly CONDITIONAL — Unavailable is the *correct*, expected
outcome, excluded from the pillar denominator entirely rather than defaulting to a suppressed
score or an under-weighted average:**

| Dimension | Conditional at | Legitimate proxy when unavailable |
|---|---|---|
| Leadership | Pre-Seed | Founder clarity/decision quality substitutes; org chart is meaningless pre-hire |
| Retention | Pre-Seed, often Seed | None legitimate — methodology's own text already says "may be unavailable" |
| Engagement | Pre-Seed | Qualitative early-user feedback, capped confidence |
| GTM Execution | Pre-Seed | Founder-led discovery narrative, capped confidence |
| Business Capability *(if retained, §1 item 8)* | Pre-Seed | Founder commercial instinct only |
| Unit Economics | Pre-Seed, often Seed | Directional signal only per methodology's own `stage_guidance` |
| Operational Execution *(if retained)* | Pre-Seed | Lightweight-ops acceptable per own text |
| Fundraising Readiness | Pre-Seed | Team/market/insight only, per own `stage_guidance` |
| Commercial Validation *(if retained)* | Pre-Seed | LOIs/paid pilots only |

**Stage pattern by pillar, summarized:**

- **Market** — all five dimensions are nominally gradeable at every stage (the pillar is explicitly
  designed to be inferable from thesis alone pre-revenue), but confidence should scale down hard
  at Pre-Seed/Seed since almost everything is inference-on-inference. No dimension here should be
  excluded; all should be *confidence-capped* rather than conditional.
- **Team** — Founder-Market Fit is gradeable at every stage and should be the highest-confidence
  Team dimension pre-revenue. Leadership, Business Capability, and Execution Track Record are
  legitimately thin-to-absent at Pre-Seed and should be conditional, not scored low.
- **Product** — Customer Value and Differentiation are gradeable early (thesis-level); Usability,
  Defensibility, and Adoption Potential require at least an MVP and should be confidence-capped,
  not conditional, at Pre-Seed (a prototype-level answer is possible, just low-confidence).
- **Execution** — Strategic Execution and Product Execution are gradeable early; GTM Execution and
  Operational Execution are legitimately conditional at Pre-Seed; Execution Velocity (once
  converted to a derived metric, §1 item 20) is mechanically unavailable before there's a growth
  curve to measure, which is itself a correct exclusion, not a defect.
- **Traction** — Customer Growth and Revenue Growth are conditional at Pre-Seed by the
  methodology's own text ("customers are not required," "revenue is optional") — this is the one
  pillar where the existing text already gets stage-conditionality mostly right; Retention and
  Engagement should be added to that same conditional treatment (currently they degrade to
  low-confidence scores rather than clean exclusion).
- **Financial Health** — Revenue Quality, Unit Economics, and Fundraising Readiness are legitimately
  conditional at Pre-Seed/Seed; Burn Efficiency and Runway remain gradeable at every stage (every
  funded company has *some* cash position and burn rate, even if small).

**Absence should reduce score, reduce confidence, or be excluded — the recommended rule:**
if the *methodology's own stage_guidance* says a stage doesn't require the evidence (e.g., "revenue
is optional" at Pre-Seed), absence must be **excluded** (denominator adjustment, zero score impact).
If the stage_guidance expects the evidence but it's absent, that is a legitimate confidence-reducing
signal, not an automatic score reduction — the current architecture already distinguishes
`evidence_status` from score reasonably well post-Evidence/Scoring-Separation-Sprint; the gap is
that pillar-level aggregation doesn't yet know the difference between "this dimension doesn't apply
at this stage" and "this dimension applies but nothing was found," which is precisely the coverage
issue surfaced concretely in the Stripe diagnostic (§9, Execution pillar).

No stage-specific *weights* are proposed here, per the constraint — this section defines
*exclusion/confidence logic*, not weight schedules.

---

## Part 4 — Score anchors for all 30 dimensions

Existing bands are 5-tier (9-10 / 7-8 / 5-6 / 3-4 / 0-2). The requested scheme splits the top band
(9 vs. 10) and raises the floor (1-2 instead of 0-2, since a scored dimension by definition has
*some* evidence — true 0 would mean actively disqualifying evidence, which is rare enough that
collapsing it into 1-2 is more honest). Quantitative thresholds are given only where the
methodology's own `benchmark_examples` already establish a number, or where a number is genuinely
verifiable; everywhere else the anchor stays qualitative and says so explicitly, per the
instruction not to fake precision.

**Legend: 🔢 = quantitative anchor available/appropriate · 🗣️ = qualitative only, quantitative
precision would be fake.**

### Market
- **Market Size** 🗣️ — 1-2: single-city/single-buyer niche, no plausible expansion path. 3-4:
  narrow segment, one budget category, no adjacent workflow. 5-6: moderate segment or large-but-
  uncapturable market. 7-8: large segment (enterprise/SMB budget category) + ≥1 credible adjacent
  expansion path named. 9: multiple credible expansion paths into adjacent large categories. 10:
  category-defining platform trajectory with proof of expansion already underway (not just
  claimed) — reserve for companies actively expanding into a second large category.
- **Market Growth** 🗣️ — 1-2: declining category. 3-4: flat, no named driver. 5-6: stable, vague
  tailwind claim. 7-8: ≥1 concrete external driver named (regulation, platform shift, labor cost)
  *and* buyer-budget evidence, not company growth alone. 9: multiple independent drivers +
  third-party corroboration. 10: category consensus growth narrative with company already riding it
  at scale — very rare for this system's typical (pre-Series-B) inputs.
- **Market Timing** 🗣️ — same 5-tier structure as Growth; 9/10 split should require *both* an
  external inflection point *and* evidence customers are already acting on it (not just that they
  should).
- **Competitive Intensity** 🗣️ — 1-2: commodity, no wedge, powerful incumbents, no opening. 3-4:
  crowded, unclear positioning. 5-6: some differentiation, durability unproven. 7-8: named wedge +
  ≥1 switching-cost/lock-in signal. 9: wedge validated by customer win/loss evidence. 10: category
  leadership already established despite competition — reserve for later-stage companies only.
- **Customer Demand** 🔢/🗣️ hybrid — anchors should literally borrow Traction's own numeric
  thresholds (NRR, churn, customer count growth) once this dimension is scoped down per §1 item 5,
  rather than maintaining a separate ladder.

### Team
- **Founder-Market Fit** 🗣️ — 1-2: no domain connection. 3-4: generic background. 5-6: some
  relevant experience, not clearly advantaged. 7-8: direct operator/buyer experience in the target
  market. 9: direct experience + prior founder success. 10: direct experience + prior successful
  exit *in the same or adjacent domain* — the conjunction, not either alone, should gate 10.
- **Technical Capability** 🗣️ — 1-2: no technical founder, outsourced core product. 3-4: unproven
  claims. 5-6: adequate, some complexity risk. 7-8: technical founder + shipped complex product. 9:
  proven at meaningful scale/reliability. 10: technical capability itself is a competitive moat
  (e.g., infra performance others can't match) — rare, requires third-party corroboration.
- **Business Capability** *(pending §1 item 8 disposition)* 🗣️ — if retained in narrowed form
  (pricing/hiring signals only, not outcomes): 1-2 through 10 ladder keyed to pricing-strategy
  clarity and commercial-hire count, not to revenue outcomes (which belong to GTM Execution).
- **Leadership** 🗣️ — 1-2: dysfunction evidence. 3-4: no hiring evidence at a stage where it's
  expected. 5-6: adequate. 7-8: hiring success + clear ownership. 9: executive team depth. 10:
  demonstrated organization-building at meaningful scale (>50 employees) with retention of senior
  hires — quantifiable at Series B+ only.
- **Execution Track Record** *(pending §1 item 10 merge)* 🔢 once merged into Execution Velocity:
  milestone-hit-rate becomes a countable ratio.

### Product
- **Customer Value** 🔢/🗣️ hybrid — 1-2: no stated ROI, nice-to-have. 3-4: unclear pain. 5-6:
  plausible value, unproven. 7-8: stated ROI/time-or-cost-saved figure + retention corroboration.
  9: ROI figure independently corroborated (customer quote/case study). 10: mission-critical status
  demonstrated by customers unable to churn without material business disruption (evidenced, not
  claimed).
- **Differentiation / Competitive Intensity / Defensibility** — if merged (§2) into "Competitive
  Position," a single ladder: 1-2 commodity/no wedge; 3-4 feature parity; 5-6 some differentiation,
  durability unproven; 7-8 wedge + ≥1 durable-moat signal (switching cost, data, lock-in); 9 moat
  validated by win/loss evidence; 10 moat strengthening measurably with scale (e.g., unit economics
  improving as volume grows). If kept separate, each retains its own §1 ladder but must not reuse
  the same evidence to justify the same band twice — the exact failure mode confirmed in the
  Stripe Product-pillar diagnostic (§9).
- **Usability** — deferred to §5 (redesign changes what is anchored).
- **Adoption Potential** *(pending §1 item 15 narrowing)* — once scoped to "expansion surface" only:
  1-2 single use-case, no expansion path named; 7-8 ≥2 credible adjacent use-cases/teams named; 9-10
  requires at least one adjacent use-case already in active pilot, not just plausible.

### Execution
- **GTM Execution** 🔢 — CAC payback already has methodology-native thresholds (<12mo excellent).
  1-2: no repeatable motion. 5-6: some traction, unclear efficiency. 7-8: CAC payback <18mo or
  clear ICP + repeatable channel. 9: CAC payback <12mo. 10: CAC payback <12mo *and* efficient at
  increasing scale (payback not degrading as spend grows) — the "at increasing scale" clause is
  what should separate 9 from 10 industry-wide.
- **Product Execution** 🗣️ — ladder keyed to shipped-milestone cadence and named reliability
  incidents (or their explicit absence), not vibes.
- **Operational Execution** *(pending §1 item 18 merge)* — inherits Burn Efficiency's anchors once
  merged.
- **Strategic Execution** *(pending §1 item 19 disposition)* — if retained, keep qualitative only;
  this is the dimension where fake precision would be most damaging, since no reliable public
  signal exists to anchor a number against.
- **Execution Velocity** 🔢 once derived (§1 item 20): growth-rate-per-month-since-founding,
  banded against stage-appropriate benchmarks (e.g., 15%+ MoM growth strong at Seed, 10%+ strong at
  Series A) — these bands should be sourced from the benchmark portfolio (§7), not invented here.

### Traction
- **Customer Growth** 🔢 — already well-anchored; extend the existing "42 enterprise accounts is
  strong for Series A" style example into a proper 6-band ladder using percentile bands from the
  benchmark portfolio (§7) once built, rather than a single anecdote.
- **Revenue Growth** 🔢 — same treatment; existing "3.5x MRR in 12 months" example becomes the 9-10
  boundary once corroborated against the portfolio.
- **Retention** 🔢 — already the best-anchored dimension; adopt as-is, just split 9 vs 10 (e.g.,
  NRR 130-150% = 9, NRR >150% sustained across ≥2 quarters = 10).
- **Engagement** *(pending §1 item 24 disposition)* — if kept distinct from Retention, anchors must
  be usage-telemetry-specific (DAU/WAU ratio, workflow-completion rate) and explicitly forbidden
  from citing NRR/churn, to enforce the boundary this audit recommends.
- **Commercial Validation** *(pending §1 item 25 removal)* — n/a if removed as recommended.

### Financial Health
- **Revenue Quality** 🔢 *(pending §1 item 26 narrowing)* — concentration-risk-specific anchors
  (e.g., top-customer <20% of revenue = strong) once decoupled from Retention's NRR/GRR.
- **Unit Economics** 🔢 — already well-anchored (margin>80%, payback<12mo, LTV:CAC>3x); split 9 vs
  10 using LTV:CAC (3-5x = 7-8, 5x+ with sound assumptions = 9, 5x+ independently validated/audited
  = 10).
- **Burn Efficiency** 🔢 — burn-multiple thresholds already implied by `benchmark_examples`; make
  explicit: burn multiple <1.5x = 9-10, 1.5-2.5x = 7-8, >2.5x with weak growth = 3-4.
- **Runway** 🔢 — already fully quantitative in the existing text (18+ months = healthy, 24+ =
  strong, <6 = critical); adopt directly, add 10 = 24+ months *and* a credible path to
  profitability without needing that runway, which is a meaningfully stronger case than runway
  alone.
- **Fundraising Readiness** *(pending §1 item 30 disposition)* 🗣️ — if retained, keep entirely
  qualitative; this is a narrative-quality judgment by design and should not pretend otherwise.

---

## Part 5 — Product Usability: resolution

**What SIE should actually measure.** The current definition conflates several genuinely
different constructs under one name: product capability (does it work), ease-of-implementation
(how hard to set up), time-to-value (how fast to first payoff), actual usability (day-to-day UX),
customer satisfaction, retention, and adoption. The `common_mistakes` list even explicitly tells
the model to use retention as a Usability proxy — folding a *outcome* metric (do they stay) into a
dimension that should measure a *process* property (is it easy to start).

**Recommendation: redefine narrowly to "adoption friction" — specifically, the process property
of how much effort a new customer must expend to reach first value.** This is distinct from:
- Customer Value (Product) — *whether* the value is worth having, not how hard it is to get to.
- Defensibility (Product) — whether it's hard to *leave*, not hard to *start*.
- Retention (Traction) — whether they *stay*, an outcome partly caused by usability but not the
  same measurement (explicitly stop citing it as Usability evidence, §1 item 23/§2 pair 9).

**Evidence hierarchy, direct → proxy, in priority order:**
1. **Direct** (rare, Private-tier): stated time-to-value, onboarding duration, activation rate.
2. **Strong proxy** (Inferred-tier): self-serve availability, documented API/integration surface,
   named implementation timeline in company materials ("go live in days, not months").
3. **Weak proxy** (low-confidence Inferred): qualitative claims of ease ("simple," "intuitive")
   without corroboration — should cap confidence at Medium regardless of how emphatic the language.
4. **Explicitly excluded as evidence**: retention/churn numbers (belongs to Retention), NPS/CSAT
   scores used alone without onboarding-specific context (these measure overall satisfaction, a
   broader construct than adoption friction specifically).

**Recommendation: retag Public → Inferred** (direct time-to-value/activation data is essentially
never public pre-Series-B; the strong-proxy tier is where most real scoring will actually happen)
and adopt a formal **proxy hierarchy**, not a redefinition that discards the dimension or merges
it elsewhere — Usability survives as a genuinely distinct, valuable question once its evidence
boundary against Retention is enforced and its tag matches its real evidence tier.

---

## Part 6 — Normalized fact model (design only, not implemented)

Schema for the facts a future deterministic/hybrid scoring layer would consume, independent of
which LLM call originally surfaced them:

```
Fact {
  metric: str            # e.g. "nrr", "gross_margin_pct", "cac_payback_months",
                          #      "customer_count", "monthly_burn_usd", "runway_months"
  value: float | str      # numeric where possible; str for categorical facts (e.g. business_model)
  unit: str | null        # "percent", "usd", "months", "count", null for categorical
  period: str | null      # ISO period the fact describes, e.g. "2025-Q3", "trailing_12mo"
  source: str             # verbatim quote or citation the fact was extracted from
  source_type: EvidenceSourceType   # reuse AnalysisContext.EvidenceSourceType — company_description,
                                     # website, public_research, pitch_deck, founder_questionnaire,
                                     # founder_metrics, financial_documents, data_room, investor_notes
  confidence: "High" | "Medium" | "Low"
  extracted_for_dimension: str      # which ScoringDimension this fact was pulled while evaluating,
                                     # so the same fact can be traced across the dimensions that
                                     # legitimately reuse it (e.g., nrr feeding both Retention and,
                                     # post-narrowing, Revenue Quality) without re-extraction
}
```

**Facts required by each deterministic/hybrid candidate** (the 17 dimensions classified
Deterministic or Hybrid in §1 — the 13 pure-LLM dimensions have no fact-model dependency by
definition):

| Dimension | Required facts |
|---|---|
| Customer Growth *(Traction)* | `customer_count` @ ≥2 periods, `business_model` (for ACV-adjusted banding) |
| Revenue Growth *(Traction)* | `mrr`/`arr` @ ≥2 periods, `acv` if available |
| Retention *(Traction)* | `nrr`, `grr`, `logo_churn_rate`, cohort `period` |
| Unit Economics *(Financial Health)* | `gross_margin_pct`, `cac`, `cac_payback_months`, `ltv_cac_ratio` |
| Burn Efficiency *(Financial Health)* | `monthly_burn_usd`, `mrr`/`arr`, `burn_multiple` (derived) |
| Runway *(Financial Health)* | `cash_on_hand_usd`, `monthly_burn_usd`, `runway_months` (derived) |
| Execution Velocity *(Execution, post-derivation)* | `mrr`/`arr` growth rate, `company_age_months` |
| GTM Execution *(Execution)* | `cac`, `cac_payback_months`, `sales_cycle_days`, `pipeline_conversion_rate` |
| Revenue Quality *(Financial Health, post-narrowing)* | `customer_concentration_pct`, `contract_term_months` |
| Market Size *(Market)* | `customer_segment_size_estimate`, `buyer_budget_category`, named `expansion_paths[]` |
| Customer Demand *(Market, pending §1 disposition)* | derived from Traction facts once scoped down, not independently extracted |
| Adoption Potential *(Product, post-narrowing)* | named `adjacent_use_cases[]`, `pilot_status` per use case |
| Product Execution *(Execution)* | `shipped_milestones[]`, `reported_incidents[]` |
| Technical Capability *(Team)* | `integration_count`, `technical_founder: bool`, `product_complexity_tier` |
| Founder-Market Fit *(Team)* | `prior_founder: bool`, `prior_exit: bool`, `domain_operator_years` |
| Leadership *(Team)* | `exec_hire_count`, `team_size`, `senior_hire_retention` |
| Business Capability *(Team, post-narrowing)* | `commercial_hire_count`, `pricing_model_defined: bool` |

This schema is additive over `AnalysisContext`'s existing provenance fields — a `Fact` naturally
carries the same `source_type`/`confidence` vocabulary already established there, so building the
deterministic layer later would not require inventing a second provenance model.

---

## Part 7 — Benchmark portfolio (design only, no scores assigned)

Twenty companies, each pinned to a **historical snapshot** — evaluated only on what was
knowable/disclosed at that point in time, never on what the company became later. No SPS assigned.

| # | Company | Snapshot | Industry | Tier | Why it belongs |
|---|---|---|---|---|---|
| 1 | Quibi | Pre-launch, 2018-19 (Series A/B) | Media/streaming | Very weak / failed | Red flags visible *then*, not just in hindsight: ~$1.75B raised pre-launch, mobile-only constraint, unclear differentiation vs. YouTube/TikTok, leadership with no short-form video track record. Gradeable as weak without hindsight. |
| 2 | Fab.com | Series D, 2013 | E-commerce/flash-sales | Very weak / failed | Contemporaneous reporting already flagged unit-economics concerns and repeated business-model pivots before the collapse. |
| 3 | Jawbone | Series F/G, 2014 | Hardware/wearables | Weak | Publicly known margin/inventory problems and intensifying Fitbit/Apple competition, visible in the press at the time. |
| 4 | Homejoy | Seed/Series A, 2013 | Marketplace/home services | Weak | 1099-contractor legal exposure and thin gig-marketplace retention were known risk categories even then. |
| 5 | Bonobos | Series B, 2012 | DTC apparel | Average | Decent growth, capital-intensive model, unclear defensibility versus the broader DTC wave — a genuinely mid-tier outcome (later acquired, not a breakout). |
| 6 | Meetup | Series B-ish, 2011 | Consumer/community | Average | Steady but unspectacular growth; small venture-scale ceiling relative to typical VC expectations. |
| 7 | Instacart | Series A, 2013 | Marketplace/grocery | Promising | Strong early pull, clear wedge, but gig-labor unit-economics questions already openly present — genuinely promising-with-real-open-questions. |
| 8 | Warby Parker | Series A, 2011 | DTC/eyewear | Promising | Strong differentiation and brand, clear customer value, moderate rather than massive market ceiling. |
| 9 | Airbnb | Series B, 2011 | Marketplace | Strong | Growth and network effects clearly visible; regulatory/legitimacy risk still genuinely open at the time — strong, not yet obviously elite. |
| 10 | Slack | Series B/C, 2015 | Enterprise SaaS | Strong | Extremely fast bottoms-up adoption and word-of-mouth; enterprise monetization-at-scale still an open question then. |
| 11 | DoorDash | Series C, 2016-17 | Marketplace/logistics | Strong | Strong growth, openly thin margins, crowded competitive field (Postmates, Caviar, UberEats) — a real strong-but-contested case. |
| 12 | Stripe | Series C, 2016 | Fintech infra | Elite private | A *second* Stripe snapshot at a later stage than the existing Series A fixture — useful to test whether the methodology correctly tracks one company's *own* trajectory over time. |
| 13 | Figma | Series D, 2020 | Design/SaaS | Elite private | Extremely high NRR, category-defining PLG motion, clear moat via real-time collaboration + file-format lock-in. |
| 14 | Databricks | Series G, 2019-20 | Data/AI infra | Elite private | Enterprise-grade retention, category leadership in the lakehouse space, strong technical moat. |
| 15 | Shopify | Series C, 2013 (pre-2015 IPO) | E-commerce infra | Breakout/public-quality | Clear massive-market trajectory, strong developer/partner ecosystem moat, proven multi-segment expansion already visible pre-IPO. |
| 16 | Snowflake | Series F, 2019 (pre-2020 IPO) | Data cloud infra | Breakout/public-quality | Publicly discussed 150%+ NRR, enterprise land-and-expand proven at real scale. |
| 17 | Datadog | Series D, 2018 (pre-2019 IPO) | Observability SaaS | Breakout/public-quality | Proven usage-based expansion motion, strong technical differentiation, pre-IPO. |
| 18 | Ginkgo Bioworks | Series D, 2019 (pre-SPAC) | Deeptech/synthetic biology | Promising / high-uncertainty | Long R&D horizon, platform/IP-moat thesis, real strategic-partnership revenue but high burn — stress-tests SIE against a company where SaaS-style metrics don't apply. |
| 19 | Oscar Health | Series C, 2016 | Healthtech/insurtech | Weak-to-average | Regulatory complexity and mixed early loss-ratio execution were already publicly flagged — a healthtech/regulated-industry stress test. |
| 20 | Tesla | Late-private, 2009-10 (post-Roadster, pre-IPO) | Hardware/climate/automotive | Strong thesis / weak near-term execution | Massive market thesis, enormous capital intensity, genuinely severe near-term execution risk (post-near-bankruptcy) — a hardware/capital-intensity stress test very different from the SaaS-dominated rest of the list. |

**Coverage check:** spans all 7 requested tiers, 4+ funding stages (Seed through late-private/pre-IPO
Series G), and industries beyond SaaS (marketplace, DTC/retail, hardware, fintech, healthtech,
deeptech, climate/automotive, media). Recommended as the eventual replacement for the current
single-fixture `stripe_series_a` calibration suite, once Methodology v2 changes are implemented
(§10, Item 18).

---

## Part 8 — SPS distribution philosophy

Defined independently of any single benchmark result, before the Stripe diagnostic below.

- **0-39 — Not fundable.** Fundamentally broken thesis or active disqualifying evidence. Should be
  rare within a *curated* startup-analysis dataset (most inputs reaching this system already
  cleared some bar to be analyzed at all) but common in an *unfiltered* population of all
  registered startups.
- **40-49 — Weak.** Real concerns in ≥2 pillars; fundable only by conviction-stage/pre-seed
  investors, not institutional capital at the stage claimed.
- **50-59 — Below average.** "Average" here means average *among venture-funded companies*, an
  already-optimistic, pre-filtered population — not average among all businesses. This band should
  be close to the **mode** of the distribution among funded companies, since most venture-backed
  companies plateau or fail rather than break out.
- **60-69 — Above average.** Solid, fundable, several strong pillars, no major red flags — where
  the bulk of "reasonable to invest in" companies should cluster.
- **70-79 — Genuinely strong.** Clear category-competitive company, multiple pillars at 8+. Should
  be uncommon — roughly 15-20% of a real venture-stage dataset, reserved for companies an
  experienced investor would actively compete to fund.
- **80-89 — Elite.** Breakout-trajectory companies. Should be rare — low single-digit percent of
  any real population — reserved for Airbnb/Stripe/Snowflake-caliber evidence *at the snapshot
  stage*, not in hindsight.
- **90-100 — Extraordinary / category-defining.** Should be exceedingly rare, near-zero in any
  realistic sample. **100 should almost never occur in practice** — it would require top-band,
  fully-evidenced 9-10 scores on all 30 dimensions with zero ambiguity, and some dimension will
  almost always legitimately land at Inferred-confidence or genuinely mixed evidence even for the
  best real companies. A methodology that regularly produces 90+ scores is very likely miscalibrated,
  not describing unusually good companies.

**Does the current methodology compress strong companies into the 70s? Yes — structurally, not
just anecdotally.** Take Stripe's own expected pillar ranges (`expected_scores.py`): weighting the
*floor* of every pillar's expected range by `PILLAR_WEIGHTS` produces an overall floor of ~76.5;
weighting the *ceiling* of every range produces ~92. The specified overall target band (82-88) is
narrower than what the pillar ranges alone imply, meaning the fixture's author implicitly assumed
several pillars would land near the top of their ranges *simultaneously* — but nothing in the
scoring architecture makes that correlated outcome likely. Six independently-scored pillars, each
individually allowed to land at a defensible-but-imperfect 7-8, mathematically cannot reach the 80s
in aggregate unless nearly every pillar independently hits 9+, which — given how many dimensions
are capped at Inferred rather than Observed confidence even for excellent companies — will be rare
by design, not by miscalibration. This is a general property of weighted-averaging six imperfect
inputs, and it holds before looking at any single benchmark result — the Stripe diagnostic below
confirms it concretely rather than being the source of the finding.

---

## Part 9 — Stripe diagnostic

*(Performed after, and independent of, the methodology design above — per the "Stripe is a
diagnostic, not the specification" instruction.)* Actual: Market 8.1, Team 8.4, Product 7.6,
Execution 8.0, Traction 7.6, Financial Health 7.0, Overall **78.3**. Expected: overall 82.0-88.0
(**below floor**); per-pillar floors: market 7.5, team 8.0, product 8.0, execution 7.5,
traction 7.5 (allow_unavailable), financial_health 7.0 (allow_unavailable).

**Only one pillar is actually below its own expected floor: Product (7.6 vs. 8.0).** Every other
pillar lands *within* its expected range, but at the low end.

| Pillar | Subscore | Score | Classification |
|---|---|---|---|
| Market (8.1, in range) | Market Size 8.0, Market Growth 8.0, Timing 9.0, Customer Demand 8.0 | — | Appropriate |
| | Competitive Intensity | 7.0 | Appropriate — genuinely intense competition, correctly moderated |
| Team (8.4, in range) | Founder-Market Fit 8.0, Technical Capability 9.0 | — | Appropriate |
| | Business Capability, Leadership, Execution Track Record | null | Insufficient evidence / public-data bias (2010-era private-company record genuinely thin) **and** unrealistic evidence requirement — per §1 items 8/10, these ask for facts (GTM/growth data) that *were* present elsewhere in the record but don't flow through under these dimensions' own framing. Renormalization over the 2 surviving strong subscores kept the pillar score high despite 45% coverage — a "renormalization saved it" case, not a suppressor. |
| **Product (7.6, below floor)** | Customer Value 8.0, Usability 8.0, Adoption Potential 8.0 | — | Appropriate |
| | **Differentiation 7.0, Defensibility 7.0** | 7.0/7.0 | **Confirmed suppressor.** Both cite the same underlying evidence (developer-first APIs, network effects, workflow lock-in) and independently apply the same stage-appropriate "still emerging, not yet fully durable" hedge — exactly the mechanism identified in §2, pairs 4/5. One conservative judgment about lock-in durability gets compounded into two subscores, pulling the pillar average down twice for one underlying fact. |
| Execution (8.0, in range, low end) | Product Execution 8.0, Strategic Execution 8.0 | — | Appropriate |
| | GTM Execution, Operational Execution, Execution Velocity | null | Insufficient evidence / public-data bias (CAC, burn, hiring data genuinely Private-tier for 2010 Stripe) combined with unrealistic evidence requirement (§1 item 16/18). 40% coverage, yet the score (8.0) looks identical in confidence terms to a fully-covered 8.0 — the reported `confidence: "Medium"` label doesn't feed back into how much the SPS weighting trusts this number. |
| Traction (7.6, in range, low end) | Customer Growth 8.0, Revenue Growth 8.0, Commercial Validation 8.0 | — | Appropriate (though Commercial Validation adds no orthogonal information, §1 item 25) |
| | **Retention 7.0, Engagement 7.0** | 7.0/7.0 | Mild suppressor via overlap: no hard churn number exists, so both dimensions independently apply the same "no hard number, but strong word-of-mouth/lock-in" hedge — exactly the Engagement-as-Retention-proxy mechanism predicted in §1 item 24. |
| Financial Health (7.0, at floor) | Revenue Quality 7.0, Unit Economics 7.0, Runway 7.0 | — | Appropriate — genuinely inferred from funding size/margin-expectation language, no hard numbers exist to do better. Runway 7.0 derived from bare $18M raise size alone is a fairly generous inference; borderline anchor judgment, not clearly wrong. |
| | Burn Efficiency, Fundraising Readiness | null | Appropriate — Private-tier data genuinely absent pre-Series-B-disclosure. |

**Verdict.** The 78.3-vs-82-88 gap is *not* Stripe being under-evidenced in the way NovaLedger's
forensic audit found (a case of genuinely-disclosed evidence being wrongly marked Unavailable) —
per-subscore judgments here are almost all individually defensible. Instead:

1. **Product's below-floor score traces cleanly to the confirmed Differentiation/Defensibility
   double-count (§2, pairs 4/5)** — a concrete, real-data instance of the architectural finding,
   not a Stripe-specific accident.
2. **The other five pillars cluster at the low end of their ranges simultaneously**, which is
   exactly the compression pattern predicted structurally in §8 before this diagnostic was run —
   six independently-conservative-but-reasonable pillar scores cannot reach an 80s aggregate.
3. **Low evidence coverage (40-45%) in Team and Execution doesn't visibly hurt those pillars'
   scores** because renormalization quietly drops the null subscores from the weighted average —
   which means a company scored on 45% of its Team evidence and one scored on 100% of it can post
   an identical Team score, a genuine reliability gap (not accuracy gap) worth fixing.

Per the governing instruction, nothing here should change *because* Stripe missed its range — items
1 and 3 are independently justified by §2 and the general architecture review, and would be
recommended even if Stripe had landed inside its target band.

---

## Part 10 — Final Methodology v2 recommendation

Items (1)-(10) are pointers into the sections above, which already constitute the complete
deliverable for those items; they are not repeated here. Items (11)-(18) are the synthesis.

1. Complete 30-dimension audit → Part 1.
2. Double-counting findings → Part 2 (8/12 pairs confirmed severe/moderate).
3. Stage-specific methodology problems → Part 3.
4. Product Usability redesign → Part 5.
5. Proposed score anchors, all 30 dimensions → Part 4.
6. Deterministic/hybrid/LLM classification → restated below.
7. Normalized facts required → Part 6.
8. Benchmark portfolio → Part 7.
9. SPS distribution philosophy → Part 8.
10. Stripe under-scoring diagnosis → Part 9.

**Architecture classification (restated, 30 dimensions):**
- **Deterministic (6):** Customer Growth, Revenue Growth, Retention, Unit Economics, Burn
  Efficiency, Runway.
- **Hybrid (11):** Market Size, Customer Demand, Adoption Potential, GTM Execution, Product
  Execution, Operational Execution, Execution Velocity, Engagement, Commercial Validation, Revenue
  Quality, Fundraising Readiness.
- **LLM-judgment (13):** Market Growth, Market Timing, Competitive Intensity, Founder-Market Fit,
  Technical Capability, Business Capability, Leadership, Execution Track Record, Customer Value,
  Differentiation, Usability *(pre-redesign)*, Defensibility, Strategic Execution.

**11. Critical changes (structural, high-confidence, should happen first):**
- Retag `evidence_requirement`: Market Size (Public→Inferred), Unit Economics (Public→Private/
  Inferred), Differentiation and Competitive Intensity (Public→Inferred) — the same category of
  fix as the already-shipped Public Evidence Validation Consistency Fix, extended to the two
  dimensions it likely missed.
- Resolve the Market/Product "Competitive Position" triple-overlap (Differentiation, Defensibility,
  Competitive Intensity) — directly implicated in the Stripe Product-pillar suppression (§9).
- Remove or narrow the Traction-duplicating dimensions: Customer Demand (Market), Adoption
  Potential (Product), Commercial Validation (Traction); close the Engagement→Retention silent
  proxy leak.
- Remove or merge the Team/Execution duplicate cluster: Business Capability, Execution Track
  Record, Strategic Execution vs. GTM Execution, Leadership, Execution Velocity.
- Merge Operational Execution into Burn Efficiency.

**12. High-value changes (clear benefit, less urgent):**
- Redefine Product Usability per Part 5 (adoption-friction scope, proxy hierarchy, retag).
- Make Leadership, Retention, Engagement, GTM Execution, Business Capability, Unit Economics, and
  Fundraising Readiness explicitly conditional-by-stage per Part 3 (denominator exclusion, not
  score suppression).
- Convert Execution Velocity and blended Customer/Revenue Growth into genuinely computed/
  deterministic scores using the normalized fact model (Part 6).
- Add an evidence-coverage-weighted confidence discount to pillar aggregation, so a pillar score
  built on 40% subscore coverage (as Stripe's Execution and Team pillars were, §9) doesn't carry
  the same weight in the final SPS as one built on 100% coverage.

**13. Optional improvements:**
- Quantitative anchor tightening for the LLM-judgment dimensions where a real threshold exists
  (Part 4), leaving genuinely qualitative dimensions honestly qualitative.
- Build out and run the 20-company benchmark portfolio (Part 7) as a live, ongoing calibration
  suite, replacing the single-fixture Stripe-only calibration.
- Split the flat 20%-per-dimension weighting in Execution, Traction, and Financial Health into a
  primary/secondary structure, matching how Market/Product/Team already signal a top dimension —
  purely for methodological consistency, not urgent.

**14. Dimensions that should remain unchanged:** Retention (already best-anchored dimension in the
methodology), Runway (already fully quantitative), Founder-Market Fit (correctly tagged and
weighted), Customer Growth and Revenue Growth (structurally sound, pending only the blending
note), Customer Value (correct pillar anchor), Technical Capability (well-scoped, good anti-bias
framing), Product Execution (well-scoped once its Technical Capability boundary is clarified).

**15. Expected reliability impact:** removing the 8 confirmed double-counting pairs and fixing the
2-4 evidence-requirement mistags should materially reduce the flip-rate/variance already measured
by the reliability harness (`app/reliability/`), since two dimensions independently re-scoring one
fact compound each other's sampling variance rather than cancel it. Deterministic conversion of 6
(potentially 8+ once Execution Velocity and blended Growth are converted) dimensions removes LLM
sampling variance from those entirely — a direct, measurable improvement testable against the
existing frozen-evidence harness once implemented.

**16. Expected explainability impact:** consolidating near-duplicate dimensions means each
surviving dimension's rationale maps to a genuinely distinct, non-overlapping fact set. Today, two
dimensions citing near-identical evidence for near-identical scores (as Differentiation and
Defensibility did for Stripe, §9) reads to a sophisticated investor as either redundant or
suspicious — post-consolidation, every subscore should be traceable to evidence no other subscore
also claims.

**17. Expected inference-cost impact:** net dimension count would drop from 30 toward roughly
22-24 (merging/removing ~6-8), cutting evidence-extraction and scoring prompt size/call volume
proportionally within each affected pillar. Deterministic conversion of 6 (up to ~8-10 once
Execution Velocity and blended Growth convert) removes their scoring-stage LLM cost entirely. Net
effect: likely a **15-25% inference-cost reduction**, not an added burden — this redesign is
cost-neutral-to-negative alongside the reliability and explainability gains.

**18. Proposed implementation order:**
1. Evidence-requirement retagging (Market Size, Unit Economics, Differentiation, Competitive
   Intensity) — lowest-risk, pure metadata change; unblocks the existing Public Evidence
   Validation Consistency Fix's exemption logic for two more dimensions.
2. Remove the Usability→Retention proxy-leak guidance line — single-line edit, closes pair #9's
   actual leak without touching either dimension's design.
3. Merge/remove the 8 confirmed double-counting dimensions (Customer Demand, Adoption Potential,
   Commercial Validation, Business Capability, Execution Track Record, Strategic Execution,
   Operational Execution; tighten Engagement) — the single largest reliability/explainability win;
   redistribute freed weight to surviving sibling dimensions per each item's Part 1/2 detail.
4. Stage-conditional exclusion logic (Part 3) for the ~9 flagged dimensions — reuses the
   evidence/scoring separation architecture already built in the prior sprint.
5. Deterministic conversion of the 6 established candidates plus Execution Velocity and blended
   Growth, using the normalized fact model (Part 6).
6. Product Usability redesign (Part 5) — most novel change; sequenced after the above so it
   inherits the cleaner evidence-requirement conventions rather than needing its own bespoke fix.
7. Evidence-coverage confidence discount on pillar aggregation.
8. Anchor-tightening pass (Part 4) across all surviving dimensions.
9. Build and run the 20-company benchmark portfolio (Part 7) as the new calibration suite,
   replacing the single-fixture Stripe-only calibration.
10. Only then, revisit SPS distribution/band definitions (Part 8) if the portfolio results show
    compression persists after everything above — not before, and not because any single benchmark
    missed its range.
