# Freeze Sprint — Part 1 & 2: Evidence Concentration Semantics

No pillar, dimension, weight, missing-evidence, confidence, or SPS *formula* is changed by this
document. What follows is a proposed **metadata layer**, evaluated against the eight candidate
safeguards, then stress-tested.

## Four-way classification

| Category | Definition | Test |
|---|---|---|
| **A. Legitimate multi-dimensional evidence** | One real fact genuinely answers 2+ *distinct* investment questions; if the fact had come out differently, the affected dimensions could plausibly have diverged. | Could this fact's two "readings" have pointed in different directions? |
| **B. Correlated evidence concentration** | Legitimate, non-duplicative evidence, but concentrated enough that one pillar's score rests on fewer genuinely independent inputs than its scored-dimension count implies. | Are the questions distinct, but is most of a pillar's weight riding on one narrative? |
| **C. Duplicated semantic scoring** | The dimensions are conceptually distinct on paper, but the *available evidence* is too thin/generic to actually disentangle them — both scores are, in substance, a restatement of the same one-line fact. | Strip the dimension labels — are the two scores actually answering the same question with different words? |
| **D. Genuinely independent corroborating evidence** | Different facts, no relationship. The default, unflagged case. | — |

## Reclassifying the calibration-rerun findings under this framework

| Event | Dimensions | Reclassification | Why |
|---|---|---|---|
| Tesla cash crisis | Burn Efficiency + Runway | **B** | "Is spending efficient" and "how long until cash runs out" can genuinely diverge (efficient-but-short-runway; inefficient-but-cash-rich) — not duplicative, just concentrated. |
| **Shopify merchant growth** | Customer Growth + Growth Velocity | **C** (upgraded from B in the calibration rerun) | Both scores are derived from the *identical two data points* via closely related math (7 vs. 6, adjacent bands) — in practice this is one growth judgment expressed twice, not two independently-arrived-at readings. |
| **Oscar Health underwriting losses** | Burn Efficiency + Unit Economics | **Borderline B/C, business-model-specific** | For an insurance company specifically, "burn" is structurally driven by underwriting losses — company-wide capital efficiency and per-policy economics may not be as separable as the dimension definitions assume for this business model. Flagged, not resolved. |
| Instacart Webvan contrast | Operational Execution + Strategic Execution | **B** | "How you operate" and "what bet you made" are genuinely different lenses on one decision. |
| Airbnb acquisition | Product Execution + Strategic Execution + Adoption Potential | **A** | Delivery quality, strategic wisdom, and resulting expansion surface are three genuinely distinct, potentially-divergent questions. |
| Jawbone shipped-generations | Technical Capability + Execution Track Record + Product Execution | **C** | A single generic "shipped multiple generations" sentence with no complexity/quality/cadence detail — self-flagged by the original PASS A analyst as indistinguishable across all three uses. |
| All other registered 2-event reuse cases (Ginkgo, Quibi, Stripe, Meetup, Shyp, Figma) | — | **A** | Distinct questions, no mathematical near-identity between the resulting scores. |

**Net result: 2 confirmed Category C cases (Shopify, Jawbone), 1 borderline B/C (Oscar Health), 3
clean B cases, the remaining ~7 events clean A.**

## Safeguard evaluation (the 8 candidates)

| # | Candidate | Verdict | Why |
|---|---|---|---|
| 1 | Provenance-only warning | **Incorporated, insufficient alone** | Necessary but not sufficient — the instruction explicitly requires SIE not *present* concentrated evidence as independent, which needs a computed distinction, not just a footnote. |
| 2 | Pillar confidence cap | **Incorporated in narrow form** | A blanket cap is crude; a *targeted* refinement to the High-confidence gate specifically is adopted (see below). |
| 3 | Pillar evidence-coverage adjustment | **Adopted — core of the design** | A parallel `independent_coverage_pct` metric, computed alongside (not replacing) the existing `coverage_pct`. |
| 4 | Maximum independent-evidence concentration rule | **Rejected** | This is a hard numeric threshold with no principled cutoff available — exactly the "arbitrary numeric penalty" the instructions forbid. |
| 5 | Same-event contribution cap | **Rejected** | Implies discounting a dimension's *score* contribution because its evidence is shared — directly conflicts with "do not reduce a quality score merely because evidence is correlated." |
| 6 | Effective-dimension-count concept | **Adopted — core of the design** | Distinct evidence-events, not raw scored-dimension count, is the unit that should drive coverage/confidence-of-corroboration metrics. |
| 7 | No numerical penalty, explicit concentration metadata only | **Adopted as the framing principle** | The whole design is metadata/confidence-facing, never score-facing. |
| 8 | Superior minimal design | **This document** | A synthesis of #1, #3, #6, #7, plus a narrow #2 refinement — nothing from #4/#5. |

## The adopted design: Evidence Independence Metadata (EIM)

For each pillar, per company, among its **scored** dimensions:

1. Group dimensions by shared `evidence_event_id` (unrelated dimensions are singleton groups).
2. `effective_independent_dimensions` = count of *distinct groups*, not raw scored-dimension count.
3. `concentration_ratio` = 1 − (effective_independent_dimensions / scored_dimensions_count) —
   descriptive only, never multiplied into any score.
4. **New, parallel metric**: `independent_coverage_pct` = effective_independent_dimensions ÷
   in-scope-dimension-count, computed *alongside* the existing `coverage_pct` (raw scored ÷
   in-scope), which is left completely unchanged in its own definition.
5. **One targeted confidence refinement**: a pillar may only reach **High** confidence if
   `independent_coverage_pct` — not just raw `coverage_pct` — also clears the same 0.6 bar already
   used in the existing High-confidence gate. Medium and Low bands, and every other part of the
   existing confidence formula, are untouched. This prevents (but does not currently retroactively
   change) a pillar being called "High confidence" on the strength of one concentrated event
   answering questions worth the majority of its scored dimensions.
6. **Semantic-duplication flag**: Category-C event groups (Shopify, Jawbone) get an explicit
   `possible_semantic_duplication: true` tag at the dimension-pair level — surfaced for a future
   *dimension-definition* review, which this sprint is not authorized to perform, rather than
   silently resolved here.
7. **Explicitly NOT touched**: dimension score, pillar score, SPS, Partial Structural Coverage,
   ranking eligibility/tier, and the existing `diligence_flag_count` metric (concentration is a
   *reliability-of-corroboration* signal, a different kind of thing from *evidence-absence*, and
   folding it into the existing diligence-flag count would conflate the two).

## Stress test

| Company / pillar | scored dims | effective independent | concentration ratio | raw coverage | independent coverage | Confidence label change? | Score/SPS change? |
|---|---|---|---|---|---|---|---|
| Tesla / Financial Health | 2 (BE, Runway) | 1 | 0.5 | 50% | 25% | None — already Medium, not near the High gate | **None.** 1.55 / 50.9 unchanged |
| Shopify / Traction | 2 (Cust. Growth, Growth Vel.) | 1 | 0.5 | 40% | 20% | None — raw coverage (40%) already below the 60% High-gate threshold | **None.** 6.43 / 63.4 unchanged. Additionally flagged `possible_semantic_duplication: true`. |
| Oscar Health / Financial Health | 2 (BE, UE) | 1 | 0.5 | 50% | 25% | None — already Low | **None.** 3.0 / 53.6 unchanged |

**In all three stress-test cases, the mechanism changes zero scores and zero confidence labels** —
in this specific 15-company portfolio, no pillar anywhere currently reaches raw High confidence, so
the new High-confidence gate refinement is *real but currently inert here*, exactly like several
Phase 1 anchors were honestly reported as inert. It is not vacuous: it would engage the moment any
pillar's confidence is about to cross into High on the strength of a concentrated event — precisely
the failure mode it exists to prevent — and the new `independent_coverage_pct` / concentration flags
are visible, real, non-inert metadata additions in all three cases today.

## Five synthetic examples

1. **Clearly legitimate (A):** A disclosed 3-year enterprise contract renewal at 2x the original
   value informs both **Retention** (a hard renewal data point) and **Revenue Quality** (contract
   durability/expansion). Had the renewal instead come at a discount, Retention would still register
   positively ("they renewed") while Revenue Quality might register concern (pricing-power erosion)
   — genuine divergence potential.
2. **Clearly legitimate (A):** A CEO who previously ran a $500M-revenue division at a Fortune 500
   company in the same industry informs both **Founder-Market Fit** (domain insight) and **Business
   Capability** (proven large-scale operating ability) — a great domain expert is not automatically
   a great operator, so these can diverge even from one credential.
3. **Clearly duplicative (C):** A one-line press blurb — "the company shipped its product on
   schedule," with no complexity, quality, or cadence detail — used for both **Technical Capability**
   and **Product Execution**. Nothing in the evidence actually distinguishes "can they build" from
   "did they deliver well"; both scores restate one sentence.
4. **Clearly duplicative (C):** A growth figure disclosed only as "grew from 1,000 to 4,000 users in
   one year," mathematically transformed two ways (literal read for **Customer Growth**, annualized
   rate for **Growth Velocity**) — the Shopify pattern exactly: one arithmetic fact, two labels.
5. **Ambiguous:** "Raised $50M at a $500M valuation, up from $200M" used for both **Execution Track
   Record** (a fundraising milestone) and a stretched **Runway** read ("adequate financing"). Whether
   this is legitimate (milestone vs. financing-adequacy are different questions) or duplicative (both
   reduce to "raising money is good") cannot be determined from surface features alone — this is
   exactly the real-world pattern behind the Oscar Health borderline case, and is precisely why the
   design surfaces a flag for review rather than auto-adjudicating.

## Part 2 — Explicit effect checklist

| Affected? | Component | Answer |
|---|---|---|
| ❌ | Dimension score | Not affected |
| ❌ | Pillar score | Not affected |
| ❌ | SPS | Not affected |
| ✅ (additive) | Evidence coverage | A new, parallel `independent_coverage_pct` metric is added; the existing `coverage_pct` is unchanged in definition |
| ✅ (narrow) | Confidence | Only the High-confidence gate gains one additional necessary condition; Medium/Low logic and every other rule is untouched |
| ❌ | Completeness / Partial Structural Coverage | Not affected — PSC is about whole-pillar absence, an unrelated concept |
| ❌ | Ranking eligibility / tier | Not affected |
| ✅ (new, separate) | Diligence flags | A new `concentration_flag` metadata field is introduced; the existing `diligence_flag_count` metric is untouched and not merged with it |

**Quality ≠ certainty is preserved throughout: a company is never judged "worse" because its
evidence happens to be correlated — it is only ever described more precisely.**
