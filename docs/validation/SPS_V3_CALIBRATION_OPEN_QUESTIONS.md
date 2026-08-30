# SPS V3 Calibration Open Questions

**Updated in Phase 10.8G** — see `SPS_V3_RULEBOOK_AMENDMENT_10_8G.md`
for full detail. Status changes from this update, listed once here and
not re-litigated in the body below:

- **Finding 4 (redundant-evidence/fame-bias, STRUCTURAL METHODOLOGY
  DEFECT): RESOLVED.** Fixed via Rulebook Part 6A + `signals.py`'s
  canonical-signal deduplication. Re-tested: 1x/2x/10x/100x identical
  fact now produces identical Strength; 15 low-grade vs. 1 high-grade
  source now produces identical Strength (Confidence still correctly
  differs by grade).
- **Unresolved Item 1 (conflicting-evidence detection/tie-break,
  RULEBOOK CONTRADICTION): RESOLVED.** Explicit provenance-precedence
  tiers + order-independent resolution added; confirmed order-invariant
  across all permutations of both a 3-way and a 2-way conflict.
- **Unresolved Item 3 (self-report vs. high-quality-secondary
  precedence, RULEBOOK CONTRADICTION): RESOLVED.** Explicitly defined as
  same-tier, never auto-resolved (Provenance Matrix C confirms
  self-report beats a lower-tier estimate by precedence; Matrix E
  confirms two same-tier independent sources genuinely conflict).
- **Unresolved Item 2 (recency/staleness): PARTIALLY RESOLVED.**
  Architecture and evidence-type freshness classes now exist and are
  tested; the 4 specific `stale_after_months` values remain
  CALIBRATION_REQUIRED (new items 14-15 below).
- **Market Size magnitude-insensitivity: newly classified.** CALIBRATION
  REQUIRED / open design question, not a bug — see the amendment doc's
  own section.
- **Team-ablation finding: RESOLVED, no action needed.** Confirmed as
  expected weighted-renormalization arithmetic by direct hand
  computation (2.3-point move, fully explained); the original
  3.0-point bound was an arbitrary test heuristic, retired.

Everything below this line is the original 10.8F document, preserved
as historical record except for the status annotations above.

---

Phase 10.8F. Every finding below is classified exactly once, using the
required taxonomy (IMPLEMENTATION BUG / RULEBOOK CONTRADICTION /
CALIBRATION REQUIRED / STRUCTURAL METHODOLOGY DEFECT / EXPECTED
WITHHOLDING / ACCEPTABLE BEHAVIOR), per Part 42. Per Part 43, nothing
below has been fixed except the two items explicitly marked
IMPLEMENTATION BUG (FIXED) — everything else is a recommendation for
the next design/calibration phase, not acted on here.

---

## RULEBOOK-DEFINED BEHAVIOR (working as specified, no action needed)

- Deterministic scoring given frozen evidence (Part 13: 1,000/1,000
  identical runs).
- Evidence-order invariance (Part 14: 20/20 shuffles identical).
- Unknown-firewall semantics (Part 8): null score, excluded from
  denominators, never zeroed.
- Negative-evidence firewall (Part 9): distinct from missing evidence,
  produces low but non-null scores.
- Three-axis separation for provenance grade specifically (Part 36):
  Strength unchanged across grade changes, Confidence correctly moves.
- Traction's evidence-type discipline (Part 23): scale/growth/adoption/
  retention/commercial-validation each require their own distinct
  evidence, none substitutes for another.
- Financial Health's type discipline (Part 24): funding never becomes
  revenue or cash; profitability and growth vary independently.
- Explanation-trace reconstructability (Part 38): every score is
  reconstructable from its own trace without a second model call.
- Reproducibility snapshot (Part 39): byte-identical across independent
  process runs.

## PROVISIONAL EXPERIMENTAL PARAMETERS (never presented as approved)

Every value in `app/calibration/sps_v3/registry.py` — 20 parameters
total, spanning score-band midpoints, publishability gate thresholds,
Traction stage-relative dollar bands, and Financial Health ratio
thresholds. All carry `status=CALIBRATION_REQUIRED` in the registry
itself; see `SPS_V3_SENSITIVITY_ANALYSIS.md` for which of these actually
move outcomes enough to prioritize.

## UNRESOLVED METHODOLOGY (documented, not invented a resolution for)

1. **Conflicting-evidence detection and tie-break** (Rulebook Part 6,
   Calibration Plan Part 30 Tests 12/14). This harness does not detect
   two disagreeing observations of the same field at all — it silently
   picks one via `max()`'s tie-break behavior, which is insertion-order-
   dependent, not provenance-grade-aware. **Classification: RULEBOOK
   CONTRADICTION** — the Rulebook states a clear intended behavior
   (`UNAVAILABLE_CONFLICTING_EVIDENCE` with a grade-based tie-break) that
   was never actually implemented in this pass, and worse, the
   *fallback* behavior (silent, order-dependent selection) directly
   violates Non-Negotiable Principle 4 ("identical evidence + identical
   methodology version should produce identical SPS") in a subtle way:
   if the two conflicting observations were extracted in a different
   order on a re-run (e.g. a different LLM provider ordering its output
   differently), the *selected* observation — and therefore the score —
   could differ, even though the same two facts were presented. This
   must be fixed before production, not left as a known gap.
2. **Recency/staleness handling** (Calibration Plan Part 30 Test 13).
   No evaluator in this harness reads `source_date` for staleness at
   all. **Classification: CALIBRATION REQUIRED / needs a design
   decision**, not yet even a provisional parameter exists for it —
   this is a step behind the other unresolved items, which at least
   have a placeholder value.
3. **Self-report vs. high-quality-secondary provenance tie-break**
   (Calibration Plan Part 30 Test 14). Rulebook Part 6 lists
   `PRIMARY_SELF_REPORTED` above `SECONDARY_ESTIMATE` but does not state
   its rank relative to `HIGH_QUALITY_SECONDARY` when the two disagree
   on the same fact. **Classification: RULEBOOK CONTRADICTION** (a real
   gap in an otherwise-ordered list) — needs one additional sentence in
   Part 6, not a redesign.

## STRUCTURAL METHODOLOGY DEFECTS (must be resolved before production)

4. **Redundant-evidence / fame-bias vulnerability in classification
   signal-counting** (Parts 15-16, the single most important finding of
   this phase). Duplicating an identical fact inflated a dimension's
   score from 5.5 to 9.5 (100x duplication) and beat a single
   high-quality source citing the same fact (9.5 vs. 5.5, inverted).
   **Classification: STRUCTURAL METHODOLOGY DEFECT.** Full detail and
   recommended fix in `SPS_V3_SYNTHETIC_VALIDATION.md`'s Finding 1.
   Root cause: the Rulebook never states, as a first-class rule
   (parallel to Part 20's coverage-deduplication rule), that
   classification signal-counting must deduplicate by distinct named
   entity/fact rather than by raw observation count. This is a rulebook
   gap with a real, demonstrated consequence, not merely a theoretical
   risk — it must be closed (an explicit dedup rule added to Part 16)
   before any production V3 implementation, because it reproduces
   exactly the evidence-abundance bias the entire V2→V3 redesign exists
   to eliminate.

## IMPLEMENTATION BUGS (found and fixed this phase, per Part 43's allowance)

5. **`eval_growth_trajectory` negative-evidence override ordering bug**
   — the original code checked `negs` only inside the
   "fewer-than-two-observations" branch, so an explicit negative signal
   was silently ignored whenever 2+ revenue observations also happened
   to be present. **Classification: IMPLEMENTATION BUG (FIXED)** — moved
   the negative-evidence check to the top of the function, unconditional.
6. **`eval_capital_efficiency` negative-evidence override ordering bug**
   — same pattern: the `runway_stmt` branch fired before the `negs`
   check, so a disclosed-but-contradicted runway figure could mask an
   independently-cited negative signal. **Classification: IMPLEMENTATION
   BUG (FIXED)** — same fix pattern applied.

Both were caught by the Lower-Tail Attack (Part 30) producing an
unexpectedly high SPS (a "STRONG" Growth Trajectory classification
despite an explicit negative signal being present in the fixture) —
exactly the kind of defect this phase's adversarial testing exists to
surface. Both are narrow, mechanical ordering bugs in this experimental
harness's Python, not defects in the Rulebook's own design (the
Rulebook's Part 13/17 both already state negative evidence must
override, unconditionally — the harness code just didn't implement that
correctly on first pass).

## CALIBRATION REQUIRED (values, not architecture, need real data)

7. Every score-band midpoint (`band.single_signal`,
   `band.multiple_signals`, `band.comprehensive`, `band.negative_signal`)
   — see sensitivity analysis for priority ranking.
8. Every publishability gate threshold (`gate.min_dimensions_per_pillar`,
   `gate.min_publishable_pillars`, `gate.min_critical_pillars_present`,
   `gate.overall_coverage_floor_pct`, `gate.min_pillar_coverage_pct`).
9. Every Traction Current-Scale stage-relative dollar band (6 pairs, one
   per stage-group/metric — only Seed/Series A/Growth were modeled in
   this harness; Idea, Pre-Seed, and Series B+ were collapsed onto
   adjacent stages' bands as a scoping simplification, itself a
   CALIBRATION REQUIRED item for whether that collapsing is
   appropriate).
10. Growth Trajectory's YoY thresholds (`strong_yoy_pct`,
    `exceptional_yoy_pct`) and the decline-negative-evidence threshold.
11. Capital Efficiency's burn/revenue ratio thresholds and the
    severe-cash-constraint runway-months threshold.
12. `band.negative_signal`'s exact value directly determines whether the
    0-19 SPS band is reachable at all (demonstrated: 2.0 → floor exactly
    20.0; 1.0 → floor 10.0, reaching 0-19) — this is now known to be a
    **high-priority** calibration item given its direct, measured effect
    on scale reachability, not merely a generic placeholder.
13. Market Size has no magnitude-aware banding at all in this harness
    (a $100M and a $100T market score identically) — needs either a
    dedicated dollar-threshold design (mirroring Current Scale's
    pattern) or an explicit rulebook decision that Market Size should
    remain magnitude-insensitive by design (unlikely to be the right
    call, but not yet decided either way). Reclassified in Phase 10.8G
    as an explicit design question, not a defect — see the amendment
    document.
14. **(New in Phase 10.8G)** The four `freshness.<class>.stale_after_months`
    values (STRUCTURAL_FACT=600, HISTORICAL_FACT=36, RECENT_PERFORMANCE=18,
    CURRENT_STATE=12, all provisional) — architecture decided, exact
    thresholds not calibrated.
15. **(New in Phase 10.8G)** The "borderline" freshness zone is fixed at
    75% of `stale_after_months` as an implementation simplification, not
    a separately calibrated parameter — whether it deserves its own
    tunable ratio is an open question for the next calibration pass.

## EXPECTED WITHHOLDING (working as intended, not a defect)

- Every adversarial Part-12 stress profile that resolved to
  `publishable=False` because it deliberately populated only 1-3
  pillars (these fixtures were built narrow, on purpose, to test
  specific dimension-level mechanics — see
  `SPS_V3_SYNTHETIC_VALIDATION.md`'s note that most Part-12 profiles
  are dimension-level, not full-SPS-level, test fixtures).
- Core Profiles B, C, F, G, H correctly withheld SPS for genuinely
  insufficient pillar coverage (as designed by their own stated
  purpose — e.g. Profile C is explicitly named
  "exceptional/insufficient coverage" and its whole point is to
  confirm withholding, not to produce a number).

## ACCEPTABLE BEHAVIOR (real property, not a bug, not calibration-blocking)

- The Current-Scale stage-boundary discontinuity (a 2.5-point score
  jump for a $2 ARR difference at the exact threshold) — an inherent,
  accepted property of discrete banding (Rulebook Part 8's own
  granularity decision), not a defect.
- Low pillar-weight sensitivity (Financial Health ±50% relative moved
  SPS by at most 0.3 points on tested profiles) — reassuring, not
  concerning; supports leaving pillar weights unchanged.
- Bounded classification-error impact (max 1.4 points at the pillar
  level for a 2-tier miss on the highest-weighted dimension) —
  confirms the architecture is reasonably robust to plausible AI
  classification mistakes, a direct design goal of moving away from
  free-form LLM numeric scoring.

## Remaining open questions for the next phase

1. Once Finding 4 (redundant-evidence dedup) is fixed, does the
   Sensitivity Analysis's priority ranking change? (Explicitly flagged
   there as likely, not re-tested in this phase.)
2. Is the 70-79/80-89 band separation genuinely achievable with more
   careful evidence-density construction, or does it reveal a second,
   smaller version of Finding 4's classification-tier compression?
   (This phase's two quick interpolation attempts both landed at 74.9 —
   inconclusive, not investigated further.)
3. Should Idea, Pre-Seed, and Series B+ get their own genuinely distinct
   Current-Scale stage bands, or is collapsing them onto adjacent
   stages (Seed and Growth respectively, as this harness does) an
   acceptable simplification even in production?
4. What is the right conflicting-evidence tie-break rule (Unresolved
   Item 1) — always prefer higher provenance grade, or something more
   nuanced when grades are equal?
5. Does recency/staleness (Unresolved Item 2) need a decay formula, a
   hard cutoff, or should it remain deliberately unmodeled for facts
   that don't meaningfully change over time (e.g. founder history)
   while being modeled for facts that do (e.g. revenue)?
