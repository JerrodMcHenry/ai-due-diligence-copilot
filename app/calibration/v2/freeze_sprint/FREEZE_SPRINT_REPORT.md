# Methodology v2 — Final Pre-Holdout Freeze Sprint Report

Artifacts: `PART1_2_evidence_concentration.md`, `PART3_expansion_design.md`,
`expansion_companies/*.json` (4 new snapshots + scored records), `expansion_aggregate.json`, this
report. Nothing in `app/benchmarks/`, `app/calibration/v2/pass_a|pass_b|calibration_rerun|
anchor_calibration`, or the canonical specification was modified.

---

## Part 1 & 2 — Evidence concentration (full detail in `PART1_2_evidence_concentration.md`)

**Solution adopted: Evidence Independence Metadata (EIM).** Dimensions sharing an
`evidence_event_id` within one pillar are grouped; a new `effective_independent_dimensions` count
and a new, parallel `independent_coverage_pct` metric are computed alongside the existing
`coverage_pct` (which is unchanged); a pillar can only reach **High** confidence if
`independent_coverage_pct` also clears the same bar the existing rule already applies to raw
coverage; genuinely semantically-duplicative pairs get an explicit
`possible_semantic_duplication: true` tag. **Zero effect on dimension score, pillar score, SPS,
Partial Structural Coverage, ranking eligibility, or the existing `diligence_flag_count` metric.**
Stress-tested against Tesla, Shopify, and Oscar Health: all three show zero score/SPS change and
zero confidence-label change (none were near the High-confidence gate this refinement narrows), but
all three now carry real, correct, previously-invisible concentration metadata.

**New finding from the expansion (Part 5) that belongs here too:** every one of the 3 new
companies where both Customer Growth and Growth Velocity were scored (Dollar Shave Club, Peloton,
Lemonade) shows the identical pattern already found for Shopify — the two dimensions cite the same
underlying series every time both are scoreable. This is not a Shopify-specific fluke; it is a
**systemic property of how these two dimensions are currently evidenced** whenever a real growth
series exists at all. This is now the single most well-evidenced `possible_semantic_duplication`
pattern in the whole system (4 independent instances) and is the strongest candidate for a future
dimension-definition review — not performed in this sprint, which is not authorized to touch
dimension definitions, but flagged as the top priority for whenever that review is authorized.

## Part 3 — Expansion design (full detail in `PART3_expansion_design.md`)

9-company target list designed; **4 executed this sprint** (Etsy — marketplace; Dollar Shave Club —
commerce/DTC; Peloton — hardware; Lemonade — insurance), chosen to maximize family coverage per
company within a realistic single-session research budget. Enterprise SaaS, consumer, and
deeptech/partnership growth remain explicitly untested — a named, honest scope limit, not a
fabricated evidence gap.

## Part 4 — Anti-contamination protocol

For each of the 4 companies: a historical cutoff date was fixed at the funding-round announcement
date *before* any evidence beyond "a round exists around this date" was gathered; only sources dated
at or before that cutoff were used for scoring (one exception per company follows this program's
established fact-date-vs-report-date rule — Lemonade's loss ratio, sourced to a 2019 article that
explicitly reports an end-of-2017 fact, exactly analogous to Meetup's and Jawbone's evidence-repair
precedent). No company was selected because its outcome was already known to fit a desired score —
selection criterion was business-model/anchor-family fit only, recorded before evidence-gathering
began (see `PART3_expansion_design.md`). No diagnostic expected-quality-tier was assigned to any of
the 4 companies in this sprint — not required for the anchor-validation objective, and skipped to
avoid any unnecessary proximity to outcome-adjacent research.

## Part 5 — Execution results

| Company | Family(ies) exercised | SPS | Traction pillar |
|---|---|---:|---|
| Etsy (2012-05-09) | Marketplace growth, marketplace Unit Economics | 69.2 | 7.0 (Engagement only — Customer Growth/Growth Velocity withheld, see below) |
| Dollar Shave Club (2015-06-22) | Commerce/DTC growth, Growth Velocity window-caution | 66.9 | 8.0 (Customer Growth 8, Growth Velocity 8) |
| Peloton (2016-06-18) | Hardware growth, hardware Unit Economics (rejection case) | 68.0 | 8.57 (Customer Growth 8, Growth Velocity 9) |
| Lemonade (2017-12-19) | Insurance growth, insurance Unit Economics (2nd real case), Growth Velocity window-caution | 56.8 | 7.43 (Customer Growth 8, Growth Velocity 7); Financial Health 2.0 |

**Etsy's marketplace family logic was exercised but did not produce a Customer Growth/Growth
Velocity score** — the only available prior-period comparison point was a stated 2010 *projection*,
not a confirmed actual, and the anchor's own same-metric-confirmed-actual discipline correctly
withheld a score rather than mix a projection with a 2012 actual. This is reported as a genuine
evidence gap in this specific snapshot, not a flaw in the family design (which correctly identified
GMV/transacting-count, not raw seller count, as the right unit before running into the evidence
limit).

**Peloton's hardware Unit Economics case is a clean validation of the anchor's symmetry**: a vague,
undetailed, self-serving "claims profitability" statement was correctly withheld exactly the same
way vague negative narratives (Jawbone, Meetup) were withheld earlier in this program — the rule
does not treat flattering unverified claims more leniently than unflattering ones.

**Lemonade's Growth Velocity case is the clearest real-world trigger of Part 1's short-window
caution rule** — a literal 6-month-window CAGR calculation produces an implausible extrapolated
rate, and the design's own stated caution (dampen rather than report at face value) was actually
invoked, not just theorized.

---

## Part 6 — Anchor validation (updated classifications)

| Anchor | Prior classification | New evidence this sprint | Updated classification |
|---|---|---|---|
| Growth Velocity / Customer Growth **architecture** (floor-gate, annualize, scale-tier bands, short-window caution) | KEEP PROVISIONAL | Tested on 3 more real companies across 2 more families (Commerce/DTC, Hardware), including the short-window caution rule actually firing correctly twice (DSC, Lemonade) | **FREEZE** |
| Growth Velocity / Customer Growth **exact scale-tier cutoffs** | KEEP PROVISIONAL | Only tested at "large" scale (Shopify, DSC, Peloton, Lemonade all well above floor); enterprise SaaS, consumer, and deeptech scales remain untested | **FREEZE AS PROVISIONAL** — safe to ship, does not block v2, may be refined as more scale diversity is added |
| Insurance Unit Economics qualitative-disclosure threshold | KEEP PROVISIONAL | Now tested twice (Oscar Health qualitative-only, Lemonade quantitative loss-ratio); the two results behave sensibly relative to each other (more severe/specific evidence scored lower, as it should) | **FREEZE AS PROVISIONAL** — meaningfully strengthened, no longer the single weakest link |
| Commerce/DTC and Hardware Unit Economics "insufficient combination" rules | Untested | Both correctly withheld a score from weak/vague evidence in real tests (DSC: no margin data at all; Peloton: vague unverified positive claim) — the *withholding* logic is validated even with no positive test case yet | **FREEZE AS PROVISIONAL** |
| Marketplace Unit Economics / Customer Growth family selection logic | Untested | Etsy exercised the "which unit is correct" reasoning correctly but could not produce a score due to a projection-vs-actual evidence gap | **KEEP PROVISIONAL (unchanged)** — genuinely the least-improved family this round, honestly reported rather than papered over |
| Qualitative Burn Efficiency / Runway band architectures | FREEZE (calibration rerun) | No new crisis-level test case appeared among the 4 companies this sprint (none had a distress narrative) | **FREEZE (unchanged)** |
| Marketplace take-rate-alone-insufficient rule; commerce/DTC thesis-not-outcome rule | FREEZE (calibration rerun) | Unchanged — no new test case this sprint | **FREEZE (unchanged)** |

**No anchor is classified REJECT.** Nothing tested this sprint was found indefensible; every rule
either performed exactly as designed (including two rules whose *withholding* behavior, not a
score, was the correct and validated outcome) or remains honestly under-tested without being unsafe.

---

## Part 7 — Stop condition check

- Structural contradiction: **none found.**
- Clearly indefensible anchor: **none found** — including after deliberately testing the symmetry
  concern (does the system reward vague positive claims more leniently than vague negative ones —
  no, confirmed via Peloton).
- Severe business-model bias: **none found** — the 4 new companies, spanning 3 different business
  models, all produced sensible, non-extreme, evidence-proportionate SPS values (56.8-69.2), with no
  floor or ceiling artifacts.
- Materially broken ordinal discrimination: **not applicable to this sprint's design** (no tier
  labels were assigned to the new companies), and the original 15-company ordinal results are
  untouched by anything in this sprint.
- Unacceptable scoring instability: **none found** — the two window-caution invocations (DSC,
  Lemonade) demonstrate the architecture correctly self-moderating rather than producing unstable
  output.

**This sprint converges. Per the explicit instruction, "more data would be nice" and "an anchor
being under-tested" are not, by themselves, sufficient reasons to keep iterating — and neither
condition that WOULD justify continuing (a structural contradiction, an indefensible anchor, severe
bias, broken discrimination, or instability) was found.**

---

## Part 8 — Final freeze recommendation

**1. Evidence-concentration solution:** Evidence Independence Metadata (EIM) — see Part 1/2 above.

**2-6. Effect on scores/coverage/confidence/eligibility:** No effect on dimension score, pillar
score, or SPS (2, 3). No effect on evidence coverage's existing definition — a new, parallel,
additive metric only (5). Confidence: one narrow refinement to the High-confidence gate only (4).
No effect on ranking eligibility (6).

**7. Tesla under the new semantics:** Financial Health score/SPS unchanged (1.55 / 50.9); now
carries `concentration_ratio: 0.5` and `independent_coverage_pct: 25%` (vs. raw 50%) metadata,
correctly flagging that its Financial Health score rests on one event, not two independent ones.

**8. Shopify under the new semantics:** Traction score/SPS unchanged (6.43 / 63.4); now carries the
same concentration metadata plus an explicit `possible_semantic_duplication: true` tag — the
strongest such flag in the system, now corroborated by 3 more real-world instances of the identical
pattern found in this sprint's expansion.

**9. Oscar Health under the new semantics:** Financial Health score/SPS unchanged (3.0 / 53.6); same
concentration metadata added.

**10. New calibration snapshots added:** 4 — Etsy (2012-05-09), Dollar Shave Club (2015-06-22),
Peloton (2016-06-18), Lemonade (2017-12-19). Diagnostic-only; not merged into the canonical
`app/benchmarks/` portfolio in this sprint.

**11. Anchor families exercised:** Commerce/DTC growth (real score), Hardware growth (real score),
Insurance growth (real score), Marketplace growth (family logic exercised, no score produced),
Insurance Unit Economics (2nd real case), Hardware Unit Economics (withholding validated), Commerce/
DTC Unit Economics (withholding validated, evidence absent), Marketplace Unit Economics (family
logic exercised, no score produced), Growth Velocity's short-window caution rule (2 real triggers).

**12. Anchor families still untested:** Enterprise SaaS growth, Consumer growth, Deeptech/
partnership growth, Revenue Growth at any scale (still zero real examples anywhere across 19
companies total now examined in this program).

**13. Anchors classified FREEZE:** Growth Velocity/Customer Growth architecture; qualitative Burn
Efficiency band architecture; qualitative Runway band architecture; marketplace
take-rate-alone-insufficient rule; commerce/DTC thesis-not-outcome rule.

**14. Anchors classified FREEZE AS PROVISIONAL:** Growth Velocity/Customer Growth exact scale-tier
cutoffs; insurance Unit Economics qualitative-disclosure threshold; commerce/DTC and hardware Unit
Economics insufficient-combination rules; qualitative Burn Efficiency/Runway exact
score-within-band placement (unchanged from the calibration rerun).

**15. Anchors classified REJECT:** none.

**16. New ordinal-discrimination results:** not applicable — no tiers were assigned to the 4 new
companies in this sprint (deliberately out of scope; see Part 4). The original 15-company results
(94.5% concordance, 5/91 inversions) are untouched.

**17. Severe new inversions:** none — not applicable, same reason as #16.

**18. Business-model bias discovered:** none. The 4 new companies' SPS values (56.8-69.2) are
sensible and evidence-proportionate; Lemonade's markedly lower score is directly, defensibly
explained by its severe, quantified loss ratio, not by any structural disadvantage of the insurance
family's anchor design.

**19. Scoring instability discovered:** none — the two window-caution invocations are evidence the
system is *stable under stress*, not unstable.

**20. Exact remaining blockers to methodology freeze:** none that block a v2 freeze. Two items
remain genuinely open for *future* refinement, not blocking: (a) the marketplace family's Customer
Growth/Unit Economics anchors are still only exercised at the "family logic is correct" level, never
at the "produced a real score" level; (b) the Customer-Growth/Growth-Velocity semantic-duplication
pattern, now confirmed systemic across 4 companies, is flagged for a future dimension-definition
review that this sprint is not authorized to perform.

---

### Verdicts

**EVIDENCE-CONCENTRATION SEMANTICS RESOLVED: YES**
**STRUCTURAL METHODOLOGY STABLE: YES**
**ALL ANCHORS EITHER FROZEN OR SAFELY PROVISIONAL: YES**
**FURTHER CALIBRATION REQUIRED BEFORE HOLDOUT: NO**
**METHODOLOGY V2 READY TO FREEZE: YES**
**READY FOR HOLDOUT VALIDATION: YES**

Per instruction: stopping here. No holdout scored. No further calibration iteration proposed —
none of the five conditions that would justify one (structural contradiction, indefensible anchor,
severe bias, broken discrimination, instability) was found. No production code modified. No commit
made.
