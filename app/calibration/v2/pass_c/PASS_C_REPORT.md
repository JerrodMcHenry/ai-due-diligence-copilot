# SIE Methodology v2 — PASS C Holdout Validation Report

Frozen checkpoint: commit `438d17c`, methodology `v2-spec-2026-08-23`. Full provenance chain
(pre-access hashes/mtimes → blind scoring → frozen/hashed blind results → tier reveal → structural
generalization → future-outcome reveal → failure analysis) lives in `app/calibration/v2/pass_c/`.
No prior calibration artifact was modified. No score was altered after Phase C2's freeze.

---

## 1–5. Per-company blind results

| Company | Blind SPS | Market | Team | Product | Execution | Traction | Fin. Health | Coverage | Confidence flags | Expected tier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Zenefits | **66.3** | 6.62 | 6.0 | 7.0 | 7.0 | — | — | 35.7% | PSC×2 | Strong (at-the-time) — hindsight-divergence test case |
| Homejoy | 58.2 | 7.0 | 5.5 | 7.0 | 5.0 | — | 3.0 | 35.7% | PSC×1 | Promising (flagged unit-economics/retention risk) |
| DoorDash | 46.8 | 4.88 | 4.17 | 5.0 | — | — | — | 21.4% | PSC×3 | Promising |
| Rdio | 46.7 | 5.0 | 5.0 | 4.0 | — | — | — | 21.4% | PSC×3 | Average / Mixed |
| Fab.com | 31.8 | 3.42 | 2.57 | 4.0 | 3.0 | — | 2.55 | 39.3% | PSC×1 | Very Weak / Failed |

(PSC = Partial Structural Coverage count — pillars entirely suppressed.)

## 6–9. Ordering, concordance, inversions

**Blind SPS ranking:** Zenefits (66.3) > Homejoy (58.2) > DoorDash (46.8) > Rdio (46.7) > Fab.com (31.8).

**Expected tier ordering:** Zenefits (Strong) > {Homejoy, DoorDash} (Promising, tied) > Rdio
(Average/Mixed) > Fab.com (Very Weak/Failed).

**Pairwise concordance: 9/9 cross-tier-eligible pairs concordant (100%), 0 inversions, 0 severe
inversions.** Full raw pair list in `tier_evaluation/tier_evaluation.json`. Per instruction, this is
reported alongside the raw pairs, not as a standalone headline: n=5 (9 pairs) is small enough that
one flipped comparison would move the figure to 88.9%, and one of the 9 "concordant" pairs
(DoorDash vs. Rdio, 46.8 vs. 46.7) is a practical tie, not real discrimination.

**No inversions of any kind occurred** — every higher-expected-tier company scored at or above every
lower-expected-tier company it was compared against.

## 10. Business-model generalization

Five distinct business models (DTC-pivot e-commerce, subscription streaming, services marketplace,
three-sided delivery marketplace, freemium-SaaS-plus-insurance-commission), none appearing in the
15-company calibration set or the 4-company targeted expansion. None produced a nonsensical,
unrepresentable, or structurally broken result.

## 11. Provisional-anchor behavior

Growth Velocity/Customer Growth were never simultaneously exercisable for any holdout (no valid
growth series existed anywhere in the set; Zenefits' actual-vs-guidance revenue pair was correctly
withheld, consistent with the Etsy/Peloton precedent). Homejoy's marketplace/services-labor-cost
Unit Economics judgment and Fab.com's qualitative Burn Efficiency/Runway bands both behaved
sensibly — no absurd, extreme, or degenerate output anywhere.

## 12. Missing-evidence behavior

Handled honestly throughout: DoorDash and Rdio's low coverage (21.4% each) did not produce
misleadingly extreme scores in either direction — both land in the middle of the range, grounded in
real cited evidence, not inflated or crushed by the missingness itself. No case of inferring private
weakness from absence.

## 13. Evidence-concentration findings

**Two real, significant instances found and reported (not fixed):**
- **Zenefits' Product pillar (7.0) is 100% derived from one sentence**, split across three
  dimensions (Customer Value, Differentiation, Usability) — the single most concentrated case found
  anywhere across this entire program, exceeding both Tesla's and Shopify's prior record cases.
- **Fab.com's Financial Health pillar (2.55) is 100% derived from one event pattern**
  (shortfall-plus-layoffs), split across Burn Efficiency and Runway.

Both are classified as the already-specified evidence-concentration phenomenon (Evidence
Independence Metadata, designed in the freeze sprint but not yet implemented in code) manifesting in
its most extreme forms yet observed — not a new category of problem, but a real increase in the
priority of implementing that metadata layer.

## 14. Customer Growth / Growth Velocity overlap findings

**Did not manifest in this holdout run** — neither dimension was ever simultaneously scoreable for
any of the 5 companies. The known limitation is real (confirmed structurally present in the
methodology) but had no opportunity to distort a holdout result this time.

## 15. Future-outcome retrospective findings (full detail in `outcome_evaluation/`)

- **Fab.com** (failed 2015) and **Rdio** (bankrupt 2015, explicitly "unable to close the funding and
  scale gap with Spotify") — both show direct, strong validation: the specific risk factors driving
  their low blind scores are the same factors the outcome record names as the proximate cause of
  failure.
- **Homejoy** (shut down 2015, citing "poor retention... undermined its economics" among other
  causes) — partial validation: the blind Unit Economics score and the explicit flagging of missing
  Retention evidence both anticipated the economics/retention driver; a separate legal
  (worker-misclassification) driver had no footprint in the available evidence and is not held
  against the score.
- **DoorDash** (became a $60B+ IPO) and **Zenefits** (compliance scandal, valuation collapse) — both
  illustrate the "do not punish for unknowable future events" principle from opposite directions:
  DoorDash's cautious score reflected genuinely thin, cautionary snapshot-date evidence in a crowded
  field where several similarly-positioned rivals did not achieve the same outcome; Zenefits' high
  score accurately reflected genuinely strong public information, with the scandal stemming from an
  internal, concealed practice invisible to any public-evidence methodology.

## 16. Every meaningful disagreement and root cause

Seven disagreements traced in full in `failure_analysis/failure_analysis.json`, classified: 2×E
(evidence concentration — Zenefits' Product, Fab.com's Financial Health), 1×B (sparse evidence —
the DoorDash/Rdio near-tie), 1×D (provisional-anchor limitation — Homejoy's Unit Economics
admission-threshold closeness), 2×J+K (unknowable future events with a logged, non-punitive
dimension-scope observation — DoorDash's and Zenefits' outcome divergence), 1×J+K (Homejoy's
worker-misclassification blind spot).

## 17. Structural defect discovered?

**No.** Zero findings were classified I (genuine structural methodology defect). Every disagreement
traces to evidence sparsity, an already-known provisional anchor's limitation, the already-specified
(if unimplemented) evidence-concentration phenomenon, or genuinely unknowable future events.

## 18. Calibration limitation discovered?

**Yes, reconfirmed, nothing new in kind:** the same limitations already logged at the pre-holdout
freeze (evidence sparsity for Traction/Financial Health, provisional anchor thresholds, the
Customer-Growth/Growth-Velocity dimension overlap) all held up as *known and bounded* — none
worsened qualitatively, though the Zenefits Product-pillar case is a new *maximum severity* data
point for the evidence-concentration limitation specifically.

## 19. Future Methodology v2.1 issues to log

1. Implement Evidence Independence Metadata (already specified, not yet coded) — priority raised by
   Zenefits' 100%-concentrated Product pillar.
2. Consider whether a governance/compliance-integrity-adjacent dimension, or an explicit documented
   scope boundary, belongs in a future architecture conversation — raised by Zenefits' and
   Homejoy's outcome divergence, logged as a topic, not a proposal.
3. The Customer-Growth/Growth-Velocity overlap remains unresolved and unexercised by this holdout
   run — still the top dimension-definition-review candidate whenever that review is authorized.

## 20. Safe to implement?

Discussed in the verdicts below.

---

### Verdicts

**PASS C COMPLETE: YES**
**PRE-HOLDOUT FREEZE INTEGRITY PRESERVED: YES**
**BLIND SCORING COMPLETED BEFORE TIER REVEAL: YES**
**BLIND TIER EVALUATION COMPLETED BEFORE FUTURE-OUTCOME REVEAL: YES**
**HOLDOUT ORDINAL DISCRIMINATION ACCEPTABLE: YES**
**BUSINESS-MODEL GENERALIZATION ACCEPTABLE: YES**
**MISSING-EVIDENCE BEHAVIOR ACCEPTABLE: YES**
**PROVISIONAL ANCHOR BEHAVIOR ACCEPTABLE: YES**
**STRUCTURAL METHODOLOGY DEFECT DISCOVERED: NO**

**PASS C RESULT: PASS**

**METHODOLOGY V2 SAFE TO IMPLEMENT: YES**

Per the frozen pass/fail criteria: ordinal discrimination is directionally sensible (9/9 concordant,
zero inversions); no clearly weak company received an obviously elite assessment (Fab.com scored
lowest by a wide margin); no clearly strong company was systematically crushed (Zenefits scored
highest); provisional anchors generalized without absurd behavior; missing evidence was represented
honestly (low-coverage companies were not misleadingly extreme); confidence/coverage appropriately
communicated uncertainty (DoorDash's thin-evidence case is legible as low-confidence, not a false
prediction); no business model exposed a fundamental contradiction; every observed error is
calibration-sized (sparse evidence, provisional-anchor closeness, evidence concentration) rather
than architecture-sized. No numeric threshold was invented after seeing results — these are the
qualitative criteria stated before this pass began.

---

## STOP

PASS C RESULT = PASS. Per instruction: no recalibration, no methodology change, no Methodology v2.1
work begun, no production code modified, no commit made. Stopping here.
