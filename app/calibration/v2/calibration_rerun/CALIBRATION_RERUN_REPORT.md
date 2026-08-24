# Methodology v2 — Calibration Rerun Report

Frozen contract: `run_contract.json`. Per-company merged results: `results/*.json`. Aggregate:
`aggregate_results.json`. Full provenance/reproducibility/sensitivity detail in the sibling JSON
files in this directory. PASS A, the targeted rerun, PASS B, and Phase 1 artifacts are all
unmodified — this is a fifth, separate artifact set.

---

## Part 7 — Calibration quality

- **Improved numerical executability:** yes, narrowly — 3 of the ~79 previously-unscored
  `CALIBRATION_ANCHOR_REQUIRED` cells across Growth Velocity/Customer Growth/Revenue
  Growth/Unit Economics became scoreable (Shopify ×2, Oscar Health ×1).
- **Improved coverage:** yes, narrowly — Traction pillar coverage 2/15 → 3/15 companies;
  Financial Health's *dimension-level* coverage improved for Oscar Health specifically (1/4 → 2/4
  scored dims), though the company-level Financial-Health-suppressed count is unchanged (still
  10/15 companies with no Financial Health score at all).
- **Preserved ordinal discrimination:** yes, exactly — 94.5% concordance, 5/91 inversions,
  identical to PASS B, confirmed by independent recomputation from the merged canonical files
  (zero mismatches against Phase 1's simulation).
- **Improved absolute scale usefulness:** marginal — SPS range is unchanged (50.9–67.0); only 2 of
  15 companies' SPS moved, by 0.0 and 0.2 points respectively.
- **Score inflation:** none observed — no company's SPS moved by more than 0.2 points.
- **Floor effects:** none observed — no dimension is clustering at 0-1 as a default; Tesla's
  Burn Efficiency=1 reflects genuinely severe evidence, not a floor artifact.
- **New inversions:** none.
- **Business-model bias:** the one clear risk signal is that **every family actually tested by
  this portfolio happens to be either SaaS/subscription-adjacent (already FROZEN pre-Phase-1) or
  the single SMB-SaaS/platform and single insurance case** — 6 of 8 Unit Economics families and 7
  of 8 Customer Growth families remain completely untested by any company in this benchmark set.
  This is not evidence of *actual* bias in the anchors (no company was scored unfairly relative to
  another family in this run), but it is a real coverage gap in what has been validated — flagged
  explicitly rather than assumed away.

**Per instruction, none of the above was used to declare an anchor "good" — every anchor's
justification lives in Phase 1's `ANCHOR_DESIGN.md`, written before this portfolio's benchmark
effect was known; this section reports the effect, not the reason.**

---

## Part 10 — Evidence-reuse diagnosis

Using `provenance/evidence_event_registry.json`: **the issue is material, and it is a mix of both
categories, distinguishable by a concrete criterion — cross-pillar spread vs. within-pillar weight
concentration.**

- **5 of 15 evidence events (Tesla's cash crisis, Shopify's merchant growth, Instacart's Webvan
  contrast, Airbnb's acquisition, Jawbone's shipped-generations) show CORRELATED EVIDENCE
  AMPLIFICATION** — each concentrates roughly half or more of one pillar's scored weight onto a
  single underlying fact, for that company.
- **7 events (Tesla's Roadster-shipped, Meetup's subscription revenue, Ginkgo's MIT founders,
  Quibi's executive credentials, Shyp's expansion timeline, Stripe's valuation-and-credit, Figma's
  pandemic trigger) read as LEGITIMATE MULTI-DIMENSIONAL EVIDENCE** — the same fact genuinely
  informs distinct questions, and its influence is diluted across multiple pillars rather than
  concentrated in one.
- **The single most severe case remains Tesla's cash-crisis event**, where Burn Efficiency and
  Runway together consume 55% of Financial Health's scored weight from one narrative — this is
  *worse*, not better, now that Burn Efficiency/Runway actually produce numbers (under pure
  Deterministic mode, before the earlier spec repair, this pillar would simply have been
  suppressed for Tesla, silently avoiding the concentration rather than resolving it).
- **New this phase: Oscar Health's underwriting-loss fact now double-cites across Burn Efficiency
  and Unit Economics**, both within Financial Health — a direct, freshly-introduced instance of the
  same pattern, confirmed numerically inert only by coincidence (see `oscar_sensitivity.json`), not
  by design.

**Narrowest safeguard worth testing first (proposed, not implemented):** a **pillar-level
same-event double-citation flag** — when two or more scored dimensions *within the same pillar* for
the same company cite the same evidence-event ID, surface a "single-fact pillar" indicator on that
pillar's output (alongside the existing Partial Structural Coverage flag), without changing any
score or weight. This is deliberately narrower than the four broader options listed in Phase 1: it
targets exactly the within-pillar concentration pattern this registry shows is the actually-risky
subset, leaves legitimate cross-pillar reuse untouched, and requires no new math — only the
evidence-event tagging already produced in this run's provenance registry. Broader options (a
correlation-weighted discount, an independent-citation confidence penalty, an automatic
second-review trigger) remain on the table for later, larger design work, not this phase.

---

## Part 12 — Final decision

**1. Companies scored:** 15 (all calibration companies; holdouts never touched).

**2. Scoreable dimensions before vs. after:** 65 scored pillar-instances → still 65 pillar-instances
scored, but at the *dimension* level: 3 additional individual dimension cells now carry a score
(Shopify Customer Growth, Shopify Growth Velocity, Oscar Health Unit Economics) that were previously
`CALIBRATION_ANCHOR_REQUIRED`/unscored.

**3. Pillar availability before vs. after:** Traction: 2/15 → 3/15 companies with a real score.
Financial Health: unchanged at 5/15 companies with a real score (Oscar Health was already one of
the 5; it simply gained a second scored dimension inside that pillar). All other pillars unchanged
(100% availability throughout, as before).

**4. SPS before vs. after:** Shopify 63.2 → 63.4 (+0.2). Oscar Health 53.6 → 53.6 (+0.0). All other
13 companies unchanged.

**5. SPS range:** 50.9–67.0, unchanged.

**6. Tier concordance:** 94.5%, unchanged from PASS B.

**7. Inversion count:** 5/91, unchanged from PASS B — identical set of 5 inversions.

**8. Most severe inversion:** unchanged — Jawbone (Weak, 53.0) over Meetup (Average, 51.6), 1.4
points. No inversion anywhere exceeds 1.4 points.

**9. Reproducibility results:** 7/7 exact matches on a spread spot-check across Constrained-LLM,
Hybrid, and Phase-1-anchor dimensions (including one deliberately ambiguous case); Deterministic
dimensions reproduce exactly by construction, confirmed for both of Shopify's newly-scored cells.
Caveat stated explicitly: this measures single-analyst consistency, not automated-pipeline
stochastic variance.

**10. Evidence-reuse findings:** 5 of 15 registered evidence events show correlated
within-pillar amplification (most severe: Tesla's Financial Health, now 55%-concentrated on one
event); 7 read as legitimate cross-pillar multi-dimensional evidence; 2 are borderline. A narrow,
specific future safeguard (a same-pillar double-citation flag) is proposed, not implemented.

**11. Anchors ready to freeze:** Burn Efficiency band architecture, Runway band architecture,
the marketplace take-rate-alone-insufficient rule, the commerce/DTC thesis-is-not-outcome rule.

**12. Anchors still provisional:** Growth Velocity/Customer Growth scale-tier absolute cutoffs
(all families except the one tested), Burn Efficiency/Runway exact score-within-band placement,
the insurance Unit Economics qualitative-disclosure threshold.

**13. Anchors rejected:** none — every threshold proposed in Phase 1 survived this rerun's
blind-defensibility check; nothing was found indefensible enough to discard.

**14. Does Oscar's insurance anchor survive sensitivity analysis?** Survives, but only in the
narrow sense of "changed nothing when tested" — SPS, tier position, and inversion count are
byte-identical whether the rule is applied or withheld, so it introduces zero risk *in this specific
run*. This is explicitly not the same as validating the rule (see `oscar_sensitivity.json`); it
remains KEEP PROVISIONAL per Part 8.

**15. Is compression still a material problem?** Marginally reduced (Traction's coverage improved
one company), but still the dominant unresolved issue: Traction remains suppressed for 12/15
companies, Financial Health for 10/15, and the entire growth-shaped Deterministic core (Growth
Velocity, Customer Growth, Revenue Growth) is scored for only one company each, at most. Compression
remains a coverage/anchor problem, not a structural one — consistent with every prior pass in this
program.

**16. Structural methodology changes required:** **NO.** Nothing in this rerun surfaced a pillar,
weight, dimension-definition, missing-evidence, or aggregation-rule problem — every finding traces
to evidence sparsity or to the newly-visible, now-more-precisely-diagnosed evidence-reuse pattern,
which is a *measurement* finding (Part 3/10), not by itself proof the aggregation architecture needs
to change.

**17. Would another calibration iteration likely add meaningful information?** **Yes, but not by
repeating this exact exercise on these same 15 companies** — this portfolio has now been examined
about as thoroughly as its evidence supports (nearly every available growth-series, Unit-Economics,
and financial-distress fact has already been located and scored or explicitly rejected). The next
iteration's value comes from a **broader company sample**, specifically one that actually tests the
7 untested Customer-Growth/Unit-Economics business-model families and produces a second real Runway/
Burn-Efficiency crisis case to validate exact score-within-band placement — not from re-deriving
these same 15 companies' scores again.

**18. Exact next step:** expand the benchmark sample (not the anchor design) to cover at least one
additional company per untested business-model family before freezing the remaining provisional
anchors — this is a benchmark-portfolio task, not a further anchor-design or rerun task, and would
need separate authorization to touch `app/benchmarks/`.

---

### Verdicts

**CALIBRATION RERUN COMPLETE: YES**
**ORDINAL DISCRIMINATION ACCEPTABLE: YES**
**REPRODUCIBILITY ACCEPTABLE: YES** (with the explicit single-analyst-vs-automated-pipeline caveat stated in `reproducibility_check.json`)
**EVIDENCE-REUSE SAFEGUARD REQUIRED BEFORE V2: YES** — specifically the narrow, proposed same-pillar double-citation flag; not a full aggregation redesign
**NUMERICAL ANCHORS READY TO FREEZE: PARTIAL** — 4 anchor rules (Burn Efficiency and Runway band architectures, the marketplace and commerce/DTC withholding rules) are ready; the rest remain provisional pending a broader benchmark sample
**ANOTHER CALIBRATION ITERATION REQUIRED: YES** — but scoped to benchmark-portfolio expansion, not another anchor-design or rerun pass on these 15 companies
**READY FOR HOLDOUT VALIDATION: NO** — not yet: the provisional anchors and the flagged evidence-reuse pattern should be resolved (or at minimum the safeguard tested) before holdout evidence is spent on a still-partially-provisional contract

Holdouts were not scored. Future outcomes were not revealed. No methodology, weight, or production
code was modified. No commit was made.
