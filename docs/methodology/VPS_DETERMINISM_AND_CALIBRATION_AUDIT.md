# VPS Determinism, Reproducibility & Calibration Audit (Phase 29A)

**Status:** Fixed and regression-tested. Read this before touching `app/ai/vps_scoring.py`,
`app/ai/vps_guidance.py`, or `app/ai/idea_structuring.py` again.

## 1. The reported problem

The same founder description, entered multiple times with no changes, produced materially
different Venture Potential Scores (VPS) — observed live as ~8.0 vs ~6.5 for the same idea, an
evidence-poor description with almost no commercial information. This is a P0 trust problem: a
scoring product whose score isn't reproducible for identical input cannot be trusted for anything
built on top of it (Path to Stronger, calibration ladders, before/after comparisons, Weekly
Review deltas).

This document is the full trace: root cause, live reproduction (pre- and post-fix), the fix
itself, the calibration ladder used to validate it, the transparency change it required, the
product decision on pre-creation VPS display, and the invariants now permanently protected by
regression tests.

## 2. Pipeline traced (current source, not prior docs)

For a raw founder description, the path to a persisted VPS is:

1. `POST /ventures/structure-idea` → `app/ai/idea_structuring.py::structure_idea()` — one LLM
   call (`temperature=0`) that turns free text into a `VentureDraft`: every leaf field carries a
   `value` plus a three-valued `provenance` (`user_provided` / `ai_inferred` / `unknown`).
   Stateless — no database write.
2. The dashboard's review screen (`VentureDraftReview.tsx`) shows the draft for founder
   correction, then `draftToAssumptions()` flattens it to a plain `VentureAssumptions` dict
   (values only, provenance dropped) on `POST /ventures`.
3. `app/api.py::_build_model_result()` — the sole call site that turns assumptions into a score:
   `compute_vps(assumptions)` then `generate_guidance(assumptions, vps_result)`. Neither function
   calls an LLM; both are pure Python over the assumptions dict.
4. `compute_vps()` (`app/ai/vps_scoring.py`) scores 6 independent categories (market_potential
   0.20, problem_solution 0.20, founder_readiness 0.15, gtm_feasibility 0.15, economic_potential
   0.10, validation 0.20), each `None` when none of its own fields are set, then aggregates with a
   weighted average **renormalized around whichever categories are scored** — deliberately modeled
   on SIE Methodology v2's `finalize_pillar_score` so an Unavailable category doesn't drag the
   score down.

VPS is architecturally isolated from SIE Methodology v2 / SPS: `vps_scoring.py` and
`vps_guidance.py` import nothing from `app/ai/scoring.py`, `scoring_methodology.py`, or
`investment_score.py`, and no SIE pillar module (`market_analysis.py`, `founder_analysis.py`,
etc.) or the calibration suite imports anything from `vps_scoring.py` or `idea_structuring.py` —
confirmed by direct grep across both directions, not just by docstring claim (Section 8).

## 3. Live reproduction — pre-fix

20 real (non-mocked) calls to `structure_idea()` against the exact fixture:

> "I want to start a hair loss company for men and women with our special serum"

Every one of the 20 real structuring calls left `market`, `founder`, `gtm`, `economic_potential`,
and `validation` **honestly Unknown** — the LLM did not fabricate stronger or weaker evidence
run-to-run for this thin description. `problem_solution` was the only category ever scored, in
all 20 runs, using only the description's own content.

The LLM's own paraphrase of `differentiation` varied trivially between runs at `temperature=0` — a
well-documented characteristic of hosted LLM inference (floating-point non-associativity in
batched GPU execution), not a prompt or sampling defect:

- **"Special serum"** (14 characters) — 15 of 20 runs
- **"Use of a special serum"** (23 characters) — 5 of 20 runs

`_score_problem_solution()`'s own differentiation bonus tiers (`len(differentiation) > 20` → +1.5,
`> 80` → +2.0) meant this single two-word restatement of the *same fact* crossed a scoring
threshold. Because `problem_solution` was the **only** scored category, the old renormalization
(`weighted_sum / sum_of_scored_weights`) gave that one category 100% of the effective weight —
its own 1.5-point swing became VPS's entire swing:

| Metric | Value |
|---|---|
| Runs | 20 |
| Unique VPS values | 2 (6.5 × 15, 8.0 × 5) |
| Unique canonical models (by scored fields) | 3 distinct `differentiation` wordings, collapsing to 2 distinct problem_solution scores |
| VPS min / max / mean | 6.5 / 8.0 / 6.875 |

This was **not averaged away** — every one of the 20 raw runs, and the full field-by-field diff,
is preserved in the reproduction script's output for inspection (`vps_repro_results.json` in this
phase's working notes).

## 4. Isolating structuring from scoring

Before touching any code, `compute_vps()` was tested in isolation: the **same** canonical
assumptions dict (captured from one real structuring run) was scored 100 times.

**Result: 100/100 identical, byte-for-byte results.** `compute_vps()` itself was already provably
pure — no randomness, no LLM call, no I/O, no ordering or time dependency anywhere in the scoring
math. This immediately ruled out scoring nondeterminism and localized the defect to the
*interaction* between structuring's real (LLM-inherent) output variance and the aggregation
formula's sensitivity to it — a **calibration defect**, not a bug in the arithmetic.

## 5. Field-variability finding

Across the 20 real runs, only `problem_solution.differentiation` varied in a score-affecting way;
`problem_solution.problem_statement` and `.solution_description` varied in wording between a
handful of runs too (e.g. "Hair loss in men and women" vs. "Hair loss affects men and women") but
never crossed a scoring threshold. Every other field, across all 20 runs and all 8 top-level
groups (`market`, `founder`, `gtm`, `economics`, `validation`, `capital`), was uniformly `None`
(Unknown) — the LLM never invented a market size, competitive intensity, founder count, GTM
strategy, price point, or validation evidence for a description that provides none of that.

## 6. Provenance classification check

No evidence was found of the *same* information being classified differently across runs (e.g.
`user_provided` in one run, `ai_inferred` in another, for the same fact). The variance was purely
in the LLM's wording of an already-consistently-classified field
(`problem_solution.differentiation`, consistently `ai_inferred` in all 20 runs) — a paraphrase
problem, not a provenance-classification problem.

## 7. Reconstructing the observed 8.0

For the 5 runs that produced VPS 8.0:

- `problem_solution` was the only scored category (weight 0.20).
- Its subscore, with the longer differentiation phrasing crossing the `> 20` character bonus
  threshold: **8.0** (out of 10).
- Old aggregation: `weighted_sum / total_weight = (8.0 × 0.20) / 0.20 = 8.0`.

**Is an 8.0 for this evidence-poor description consistent with intended VPS methodology? No.**
This is a calculation-correctness / methodology-calibration distinction, not a bug in the
arithmetic: the weighted-average-with-renormalization formula was executed exactly as written and
exactly as SIE Methodology v2's own `finalize_pillar_score` executes it — but applying that
"don't let an unavailable dimension drag the average down" discipline to a case where **5 of 6**
categories are unavailable means one category effectively becomes the entire score. The formula
was calculating correctly; the methodology it was calculating was not calibrated for the case
where all but one category is unknown and that one category is a modeled guess, not evidence.

## 8. Root cause classification

**D — Methodology calibration defect**, with structuring contributing a secondary, defense-in-depth
concern (Section 10):

- **A. Structuring nondeterminism** — Present but not the primary cause: the LLM's paraphrase
  varies at `temperature=0` (expected LLM behavior), but every one of the 20 runs correctly
  classified `market`/`founder`/`gtm`/`economics`/`validation` as Unknown for this description — it
  did not randomly invent stronger or weaker evidence.
- **B. Provenance nondeterminism** — Not found (Section 6).
- **C. Scoring nondeterminism** — Ruled out directly: 100/100 identical outputs for one fixed
  canonical model (Section 4).
- **D. Methodology calibration defect** — **Confirmed, primary cause.** The renormalization scheme
  let a single, uncorroborated modeled assumption (never checked against a second independent
  category or any real evidence) single-handedly set VPS, with the aggregate as sensitive to that
  category's own internal scoring noise as if it were the whole model.
- **E. Review-screen transparency defect** — Confirmed as a secondary, fix-induced concern (once D
  is fixed, a founder can see one category scored high while the overall VPS sits at neutral,
  which needs a short explanation — Part 13, Section 11).
- **F. Multiple defects** — D is primary; the structuring prompt was also hardened defensively
  (Section 10) even though it was not the direct cause of the reported bug.

## 9. Calibration ladder (Part 8)

Built on the *same* underlying hair-loss venture, escalating only real evidence (never widening
scope to a different business), tested for strict monotonicity without hard-coding target values:

| Fixture | Description | Scored categories | VPS (post-fix) |
|---|---|---|---|
| A — idea only | Base fixture, nothing else | problem_solution only | **5.0** |
| B — customer discovery | + 20 customer interviews | problem_solution, validation | **5.2** |
| C — early validation | + 5 paying customers, pricing set | problem_solution, validation, economics | **5.6** |
| D — early traction | + $3K MRR, 90% retention, GTM channel | problem_solution, validation, economics, gtm | **5.7** |
| E — stronger operating business | + $60K MRR (3x growth), 120 paying customers, 75% margin | problem_solution, validation, economics, gtm | **7.6** |

`5.0 < 5.2 < 5.6 < 5.7 < 7.6` — strictly monotonic. Before the fix, A (8.0, on the unlucky
paraphrase) sat *above* B (5.2): real customer-discovery evidence lowered the score relative to a
bare idea with no evidence at all — exactly backwards. Enforced permanently by
`test_calibration_ladder_is_strictly_monotonic` and
`test_customer_discovery_no_longer_scores_below_idea_only`
(`app/tests/test_vps_determinism_and_calibration.py`).

Several alternative fixes were tried and rejected before this one, because none produced strict
monotonicity without either fragility or hard-coding: a linear blend toward neutral by "coverage"
fraction failed to invert A vs. B at any tested weight; power-law confidence scaling
(`coverage^p`) only achieved monotonicity at `p=4` with razor-thin margins (curve-fitting, which
the directive this phase followed explicitly forbade); a hard ceiling cap tied to category
coverage created a tie between D and E (which have identical category *coverage* despite very
different evidence *magnitude*). The dampening fix below was the only approach tried that both
fixed the exact reported bug and produced a non-fragile, principled ladder.

## 10. The fix

### 10a. Scoring fix — `app/ai/vps_scoring.py::compute_vps()`

When `validation` (the one category built entirely from founder-**reported observations** — see
this module's own docstring) is Unavailable **and** exactly one other (modeled-assumption)
category is scored, that lone, uncorroborated category's contribution to the aggregate is replaced
by the neutral anchor (5.0 — the same starting point every category scorer itself begins from)
rather than its own raw score:

- **Category-level `score`/`basis` are completely unchanged** — a founder still sees exactly what
  was assumed and why, at its own real value.
- Only the **aggregate VPS** this one category would otherwise have single-handedly set is
  affected.
- The moment a **second** independent category is scored — whether a second modeled assumption or
  real validation evidence — normal renormalization resumes exactly as before this phase. This is
  deliberately narrow: not a general dampening of sparse models, and it does not touch any case
  where 2+ categories are scored or where validation alone is scored (Invariant E: real evidence
  and modeled assumptions stay structurally distinct — see
  `test_sole_validation_category_is_not_dampened`).

No new extraction architecture, second AI agent, or replacement of the venture model was
introduced. No case was "solved" by forcing fields to Unknown that weren't already Unknown.

### 10b. Structuring fix — `app/ai/idea_structuring.py` (defense-in-depth, secondary)

The `SYSTEM_PROMPT` was tightened with an explicit paragraph: a bare one- or two-sentence idea
description gives no genuine basis for `estimated_market_size`, `competition_intensity`,
`primary_acquisition_strategy`, `expected_cac`, pricing fields, or any founder field, even though a
plausible-sounding value is easy to invent for a recognizable business category — "ai_inferred" is
earned only when the description itself gives a real, specific, pointable-to reason for a
particular value. A second paragraph requires internally consistent structuring: the same
description must not infer some of a group's fields while leaving others Unknown based on how the
text happens to be worded round-trip to round-trip.

This was **not** the cause of the reported bug (Section 8) — market/founder/gtm/economics were
already uniformly Unknown across all 20 real pre-fix runs for this fixture — but it closes a
related failure mode the audit surfaced while tracing the pipeline, and is verified to introduce
no regression: `test_idea_structuring.py` — 20/21 passed before and after this change, the sole
remaining failure (`test_oversized_and_empty_input_rejected`) pre-existing and unrelated (confirmed
present on `main` since before this phase, out of scope here).

## 11. Review-screen transparency (Part 13)

**Confirmed necessary and implemented.** The fix itself creates a new, narrow transparency gap: a
founder can now see one category (e.g. `problem_solution: 6.5`) displayed in the category
breakdown while the overall VPS shown above it sits at 5.0 — correct, but confusing without
explanation.

`compute_vps()` now returns `sole_uncorroborated_category: bool`, true exactly when the dampening
branch fired, so the frontend never re-derives this rule itself. Both VPS-displaying surfaces show
one restrained sentence, only when the flag is true, never a dump of the internal model:

- `VPSResultPanel.tsx` (post-creation, full breakdown): *"Only one part of your model is scored so
  far, and nothing here has been independently validated yet — so this score reflects that it's a
  single, uncorroborated assumption, not the category score shown below. A second modeled category
  or real evidence... will let it reflect what you've actually described."*
- `VentureDraftReview.tsx`'s `VpsPreview` (pre-creation): *"Right now this is based on a single,
  uncorroborated guess about your idea — that's why it sits at the neutral starting point rather
  than higher or lower."*

The existing Unknown / modeled-assumption / evidence visual distinction (provenance badges,
"We don't know this yet" for null categories, the pre-existing "What does this score mean?"
disclosure) is unchanged — this is one additional, conditional sentence, not a redesign of the
panel.

## 12. Pre-creation VPS decision (Part 14)

**Decision: Option B — keep the pre-creation preview, visually subordinate, plus the new
Section 11 note when it applies.**

This was already the standing design from a prior phase (Build V3, Part 14; see
`VentureDraftReview.tsx`'s own code comment on `VpsPreview`), not something this phase needed to
introduce: the preview shows one plain number, explicitly framed as "not a verdict," explicitly
states "nothing here to maximize before creating your venture," fails silently on error, and never
blocks venture creation. It deliberately does **not** reuse `VPSResultPanel`'s full category
breakdown, Path to Stronger, or playbook links — exactly to avoid competing with the review flow
or inviting a founder to "optimize the create flow around maximizing VPS."

This phase's fix directly *improves* this surface's honesty without any further redesign: the same
hair-loss fixture that could show a pre-fix, unlucky 8.0 during review now correctly shows 5.0 —
more consistent with "not a verdict." The only change made here is Section 11's one-line note,
scoped to the exact condition this audit found confusing. Options A (no change at all — insufficient,
leaves the new transparency gap unaddressed), C (heavier uncertainty framing throughout — not
warranted, the existing framing already covers the general case), D (defer VPS until venture
creation — rejected: removes a real, low-cost signal a founder can act on during review, and the
existing design already avoids the failure mode a full removal would be trying to prevent), and E
were all considered; B plus the targeted Section 11 addition was the minimal, sufficient
resolution.

## 13. Post-fix verification

### 13a. Fresh live reproduction (Part 15) — the primary empirical test

20 **fresh, real, non-mocked** `structure_idea()` calls against the exact same fixture, run after
both fixes were in place (not a re-score of the original pre-fix captures — this is new live data):

| Metric | Pre-fix | Post-fix |
|---|---|---|
| Runs | 20 | 20 |
| Unique VPS values | 2 (6.5, 8.0) | **1 (5.0)** |
| VPS min / max / mean | 6.5 / 8.0 / 6.875 | **5.0 / 5.0 / 5.0** |
| Unique canonical models observed | 3 differentiation wordings | still varies in wording (LLM inference is still inherently non-deterministic at the text level) |

The differentiation *wording* still varies run-to-run (an unavoidable LLM characteristic, per
Invariant A's own framing — LLM text generation, not `compute_vps()`), but it can no longer move
VPS, because it is the sole uncorroborated category for this fixture. **100% identical VPS across
20 fresh live runs.**

Additionally, re-scoring the original 20 real pre-fix captures with the new `compute_vps()`
(no new API calls needed) also produced 100% identical VPS = 5.0, confirming the fix generalizes
across every real variant actually observed, not just the fresh batch.

### 13b. Scoring-purity regression (Part 4/11), reconfirmed

- One fixed canonical model × 100 executions → 1 unique result (`test_identical_model_produces_byte_identical_result_x100`).
- A rich, fully-populated 6-category model × 100 executions → 1 unique result
  (`test_rich_multi_category_model_still_perfectly_deterministic`).

### 13c. Firewall regression (Part 17) — nothing outside VPS's own scope was touched

| System | Check | Result |
|---|---|---|
| SIE Methodology v2 / SPS | Zero import coupling (`vps_scoring.py`, `vps_guidance.py`, `idea_structuring.py` vs. every SIE pillar module, `scoring.py`, `investment_score.py`, `readiness_score.py`, the calibration suite) | Confirmed via direct grep in both directions — no matches |
| SPS calibration suite | `python -m app.calibration.run_calibration` | 1 case (stripe_series_a) ran, **failed against its expected range** — pre-existing and architecturally unrelated (zero import coupling above); this phase changed nothing this suite's pipeline reads, and Part 17 explicitly forbids modifying SPS/Methodology math here regardless |
| Fundraising Simulator, Simulate, Weekly Review, Founder Playbooks, Founder Journey, Learn concepts, Founder Beta nav, Capture signals | `npm run test` (full frontend suite) | **157/157 passed**, zero regression |
| Rename / share enable-disable / capture-without-model-update / action & mission lifecycle / reflection | `test_venture_history.py`, `test_venture_share.py`, `test_founder_missions.py`, `test_idea_lab.py`, `test_founder_actions.py`, `test_founder_evidence.py`, `test_product_analytics.py` | **12/12, 18/18, 27/27, 27/27, 32/32, 37/37, 18/18** — all passed unchanged |
| TypeScript, lint, production build | `npx tsc --noEmit`, `npm run lint`, `npm run build` | All clean |
| VPS's own pre-existing calibration suite | `test_vps_intelligence_reset.py` | **16/16** unchanged |
| Idea structuring provenance suite | `test_idea_structuring.py` | 20/21 — sole failure pre-existing, unrelated, confirmed present before this phase |

## 14. Remaining limitations

- LLM text generation (the exact wording of a paraphrase) remains inherently non-deterministic at
  `temperature=0` — this is expected, documented, hosted-LLM behavior, not something any
  application-level fix can or should eliminate. What this phase guarantees is that this variance
  can no longer, by itself, move VPS for a sparse model — not that the LLM's raw text output is
  byte-identical run to run.
  - **Scope of what this actually protects:** the dampening fix only removes the *aggregate's*
    sensitivity to paraphrase noise when a category is the sole scored, uncorroborated one. A
    two-category model (e.g. `problem_solution` + `market`) is still exposed to the same
    within-category scoring-threshold sensitivity the original bug exploited — it is just no
    longer amplified to 100% of the aggregate's weight. A future audit that finds *this* residual
    sensitivity material should treat it as a new, separately-scoped calibration question, not
    reopen this fix.
  - **A dependent process elsewhere in this pipeline could reintroduce similar sensitivity in
    the future** (e.g. a new category scorer with its own sharp character-length threshold) — this
    phase's regression suite protects the exact mechanism found, not every conceivable future
    variant of it.
- The calibration ladder (Section 9) was built and verified on one venture archetype (the reported
  hair-loss fixture, escalated through realistic evidence). It was not re-derived from a second,
  unrelated venture concept — the directive's own instruction was to fix the exact reported defect
  using this fixture, not to conduct a wider VPS calibration program (VPS remains explicitly
  uncalibrated V1 per `vps_scoring.py`'s own docstring, unlike SPS).
- The SPS calibration suite's single-case failure (Section 13c) was diagnosed as pre-existing via
  architectural isolation (zero import coupling) rather than via a controlled before/after run on a
  clean stash, to avoid the cost of a second full real-API calibration pass for a system this
  phase's directive explicitly forbids modifying. If a future phase touches SIE Methodology v2
  scoring, this pre-existing gap should be revisited on its own terms.

## 15. Invariants now permanently protected

All in `app/tests/test_vps_determinism_and_calibration.py` (13 tests) plus the pre-existing
`test_vps_intelligence_reset.py` (16 tests, unchanged):

1. Identical canonical model → byte-identical `compute_vps()` output across 100 executions.
2. A trivial paraphrase of the same underlying fact (the exact reported mechanism) never changes VPS.
3. All 3 distinct canonical models actually observed live during the pre-fix audit now produce identical VPS.
4. A sole **validation** category (real evidence) is never dampened — reports its own real score, not neutral.
5. Once 2+ categories are scored, ordinary renormalization applies unchanged (the fix doesn't over-apply).
6. The calibration ladder (A–E, escalating real evidence on one venture) is strictly monotonic.
7. Real customer-discovery evidence never scores below the same idea with zero evidence.
8. A rich, fully-populated 6-category model remains perfectly deterministic across 100 executions.
9. `sole_uncorroborated_category` is `True` exactly for the dampened case.
10. `sole_uncorroborated_category` is `False` when validation alone is scored.
11. `sole_uncorroborated_category` is `False` once 2+ categories are scored.
12. `sole_uncorroborated_category` is `False` when nothing is scored at all (`vps=None`, not conflated with the dampened case).
13. The new field round-trips safely through the `VPSResult` Pydantic contract, defaulting to `False` for legacy-shaped data.

Plus the pre-existing suite's own 16 tests (canonical fixture ordering, dimension-level-10
reachability, validation scale/retention/growth behavior, the ApexGrid regression case) — confirmed
unchanged and still passing after this phase's edits.
