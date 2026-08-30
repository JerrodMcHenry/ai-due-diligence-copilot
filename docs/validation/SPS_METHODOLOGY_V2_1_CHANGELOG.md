# SPS Methodology V2.1 Changelog

Phase 10.8B. This document records what changed between Methodology V2
(`v2-spec-2026-08-23`, `v2-anchor-registry-2026-08-23`, prompt version
`2.0`) and Methodology V2.1 (`v2.1-spec-2026-08-29`,
`v2.1-anchor-registry-2026-08-29`, prompt version `2.1`), why, and what
was deliberately left unchanged. It exists alongside, and does not
replace, `docs/validation/SPS_REAL_COMPANY_VALIDATION_REPORT.md` (Phase
10.8's blind validation) and `docs/validation/SPS_DISCRIMINATION_AUDIT.md`
(Phase 10.8A's diagnostic audit) -- both remain frozen, historical
records of V2's behavior and are not retroactively reinterpreted here.

**Pillar weights are unchanged**: market 0.20 / team 0.20 / product 0.20
/ execution 0.15 / traction 0.15 / financial_health 0.10. Phase 10.8A
found no evidence implicating the weighting scheme, and Phase 10.8B's
own instructions (Part 12) froze it absent new evidence -- none was
found.

## 1. What blind validation and the audit found

Summarized from the two frozen prior-phase artifacts (full detail
there, not repeated here):

- Phase 10.8: 25 real companies scored 63.0-76.0 (SPS), a 13-point range,
  with weak expected-group separation (Spearman ρ=0.274) and Group C
  (hypothesized weakest) outscoring Group B (hypothesized mixed) on
  both mean and median.
- Phase 10.8A traced this to (among other things): an explicit scoring
  rule telling the model not to lower a score for sparse evidence; a
  Team/Execution mid-band floor with 100% of examined subscores landing
  in {5,6,7,8}; confidence/evidence-coverage never discounting SPS; and
  two specific companies (Rippling, Plaid) whose Financial Health
  evidence cited numbers not present in either company's own research
  brief.

## 2. Full-cohort correctness check (Phase 10.8B, Part 2)

Before any methodology change, the two highest-severity Phase 10.8A
findings were extended from the original 6-diagnostic-company sample to
all 25 completed companies in the frozen Phase 10.8 cohort.

### 2A. Financial evidence fabrication -- full-cohort prevalence

An automated, then manually spot-checked, numeric-traceability check
(`app/calibration/discrimination_audit_2026_08/`) compared every
quantitative claim (dollar figures, percentages, ratios, multiples) in
every Financial Health subscore's evidence/rationale against that
company's own stored `research_brief_snapshot` -- the only research
material persisted per company.

**Result: 18 of 25 companies (72%) had at least one Financial Health
subscore citing a specific number that does not appear anywhere in that
company's own research brief.** This is far more prevalent than Phase
10.8A's 3-of-6 diagnostic finding suggested. Burn Efficiency was the
dominant offender, followed by Revenue Quality. Manual spot-checks (3 of
18 flagged cases: Databricks, Loom, Bravi) confirmed the automated
check's precision -- all three were genuine, unambiguous fabrications,
not false positives from a differently-worded but real figure:

- **Databricks**: Revenue Quality claimed "NRR above 100%" -- no NRR
  figure of any kind appears in Databricks' research brief.
- **Loom**: Burn Efficiency claimed "$2M ARR against $5M funding, CAC of
  $500, 150 customers" -- Loom's own brief states it raised $203.6M
  total funding (not $5M) and serves 400,000 companies (not 150). The
  fabricated figures are not just unsupported, they are wrong by orders
  of magnitude relative to the correct figures sitting in the same
  brief.
- **Bravi**: Burn Efficiency claimed "$5M ARR with 200 customers, 85%
  retention, 50% YoY growth, $10M funding" -- none of these appear in
  Bravi's brief, which instead describes unrelated customer-facing
  marketing claims ("$20M in potential revenue uncovered" for Bravi's
  own customers, not Bravi's revenue).

A repeating cluster of boilerplate-looking figures ($5M cash, $400K
monthly burn, $10M funding, 20-50% growth, 90-120% NRR-shaped
percentages) recurred across many unrelated real companies of wildly
different real scale -- strong evidence the model was pattern-completing
a generic "healthy seed/Series A SaaS" narrative rather than grounding
in each company's actual evidence.

### 2B. Public-dimension resolution -- full-cohort prevalence

Every dimension tagged `evidence_requirement="Public"` was checked
across all 25 companies for its resolved/Unavailable rate:

| Dimension | Pillar | % Unavailable (n=25) |
|---|---|---|
| Founder-Market Fit | Team | 88% |
| Market Growth | Market | 64% |
| Market Timing | Market | 64% |
| Competitive Intensity | Market | 64% |
| Market Size | Market | 60% |
| Differentiation | Product | 52% |
| Usability | Product | 48% |
| Runway | Financial Health | 100% |

**This is not unique to Founder-Market Fit** -- every non-Deterministic
Public dimension in the methodology was Unavailable in roughly half to
nearly all real companies, including extremely well-documented ones.
(Customer Growth/Revenue Growth/Retention/Growth Velocity are also
Public but additionally Deterministic, and their 100% Unavailable rate
is the separately-understood structured-facts mechanism, Section 2C
below -- not re-litigated here.)

**Root-cause finding, not assumed:** `app/ai/evidence_extraction.py`
already contains a prior "Public Evidence Validation Consistency Fix"
(committed 2026-08-24, before Phase 10.8's validation ran) that flags
"Public dimensions may not be marked Unavailable" as a validation error
and forces a scoped correction pass. This mechanism was already active
during Phase 10.8 -- the 48-88% Unavailable rates measured are the
*residual* failure rate after that correction pass already ran and
still failed to find evidence. Re-asking the same model to reconsider
the same thin research material a second time cannot manufacture
evidence that was never fetched in the first place. Tracing further
upstream: `app/ai/research_enrichment.py`'s `enrich_research()` ran
**exactly one generic, LLM-generated "company overview" Tavily search**
(`search_depth="basic", max_results=5`) feeding all 30 dimensions across
six pillars. A single overview-style query's top-5 results are
dominated by product/marketing facts and rarely surface founder
history, competitive-landscape specifics, or funding/financial detail --
this is an **input-sourcing gap**, not a prompt-compliance failure by
the already-correct evidence-extraction rule.

### 2C. Structural coverage ceilings (confirmed exact, from Phase 10.8A)

Restated from the discrimination audit for completeness: Traction
evidence_coverage was exactly 15.0% for 25/25 companies (4 of 5 Traction
dimensions are Deterministic and require a dated two-point structured
series essentially never present in website-scraped text); Financial
Health was exactly 45.0% for 25/25 (Runway, now also identified as a
Public-resolution failure per 2B above, plus Unit Economics'
Deterministic requirement); Execution was exactly 100.0% for 25/25
(ruling out coverage as Execution's compression driver at all -- see
Section 4 below). These are exact structural constants, not sampling
noise, and per Part 5's explicit instruction, the Deterministic
fail-closed contract itself was **not** weakened to inflate coverage --
see Section 5.

## 3. Fix: evidence fabrication (Part 3) -- `app/ai/evidence_provenance.py`

**New module**, wired into `app/ai/evidence_extraction.py::extract_pillar_evidence()`
immediately after all model calls for a pillar complete (so no
correction prompt can talk the guard out of its check). Deterministic,
Python-side, no LLM call:

- `find_unsupported_numeric_claims(evidence, source_text)` -- extracts
  every dollar/percentage/ratio/multiple-shaped token quoted in a
  dimension's evidence and signals, and checks whether each one (after
  normalizing whitespace/commas/case) appears anywhere in the actual
  text the model was given for this analysis.
- `strip_unsupported_evidence(...)` -- drops (never edits) any evidence
  bullet containing an unsupported number. A bullet mixing one real and
  one invented number is dropped in full; there is no way to know which
  half a downstream reader should trust.
- `apply_provenance_guard(dimensions, company_text)` -- if a dimension
  still has traceable evidence left after stripping, it keeps its
  evidence_status but is downgraded to Low confidence (part of its
  original justification was invented) and its rationale is annotated.
  If nothing traceable survives, the dimension is forced to
  **Unavailable** -- a fabricated-only justification is not a real
  assessment, and Unavailable is the same honest fallback the rest of
  the pipeline (weighted-average renormalization,
  `app/ai/scoring.py::calculate_weighted_score`) already knows how to
  handle.

This targets quantitative fabrication specifically (the confirmed,
dominant, and most damaging Phase 10.8 failure mode) -- it does not
attempt to verify qualitative claims without numbers, which remain
governed by the existing evidence-classification rules.

**Known limitation, stated honestly:** the guard can only check against
the research material actually persisted -- the condensed
`research_brief_snapshot` -- because the pipeline does not currently
retain the raw scraped website text or raw Tavily search results
alongside an analysis. A number that was genuinely present in the raw
source but dropped during brief condensation would be (incorrectly)
flagged as unsupported. This is a real, acknowledged architectural gap,
not something this phase's scope covers fixing (see Section 12,
Remaining Limitations).

## 4. Fix: Public-dimension resolution (Part 4) -- `app/ai/research_enrichment.py`

`enrich_research()` was rewritten from one generic Tavily search to
**four targeted searches**, generated by a single LLM call
(`extract_search_queries()`) so the added cost is three extra Tavily
calls per analysis, not three extra LLM calls:

1. `overview` -- the original generic company/product query (unchanged intent).
2. `market_and_competitors` -- market size/growth signals and named competitors.
3. `founders_and_leadership` -- founders'/leadership's prior companies and background.
4. `financial_and_funding` -- funding history, valuation, investors, disclosed metrics.

All four result sets are merged (deduplicated by source URL) into one
combined, category-labeled research text, which is then fed -- with the
same existing fact/assumption-separation rules, unchanged -- into the
brief-generation prompt, which was updated with one added instruction:
explicitly include any surfaced founder/leadership background in the
brief, not just financial/product facts.

This directly targets the root cause identified in Section 2B (a
single generic search cannot surface category-specific evidence) rather
than re-tuning the already-correct evidence-extraction validation rule
again. Per Part 4's explicit instruction, this does **not** force every
Public dimension to score -- a company with genuinely no public founder
history will still, correctly, leave Founder-Market Fit Unavailable;
this fix only ensures the research actually looked in the right place
before concluding that.

A `extract_legacy_search_query()` fail-safe path preserves the original
single-query behavior if the new multi-query extraction call returns
nothing usable, so a malformed LLM response degrades to V2's prior
behavior rather than searching nothing.

**Known cost/latency tradeoff, stated honestly:** this triples the
number of Tavily calls per analysis (1 → 4, `search_depth="basic"`,
`max_results=5` kept unchanged per query to bound the increase) and adds
one Tavily round-trip's worth of latency per added query. This was not
load-tested in this phase; Section 12 flags it as something Phase 10.8C
or a dedicated ops check should measure before wider rollout.

## 5. Structural coverage ceilings (Part 5) -- deliberately NOT changed

Per Part 5's explicit instruction, the Deterministic fail-closed
contract (`app/ai/analyze_pillar.py::apply_deterministic_overrides`) was
**not** weakened. Traction's four Deterministic dimensions and Financial
Health's Unit Economics genuinely require a disclosed, dated two-point
series; website-sourced input rarely if ever contains one, and a
company that hasn't disclosed one should not have Python inventing a
score for it. This is not a bug to fix by loosening the requirement --
it is the fail-closed principle from the v2 spec working exactly as
designed, and Phase 10.8A already reasoned through why removing it would
trade a coverage problem for a correctness problem (see "What Should Not
Change" there). Runway's near-total unavailability, in contrast, **was**
addressed -- as a Public-dimension resolution problem (Section 4), since
Runway is not Deterministic and its evidence can legitimately come from
disclosed funding announcements the research step simply wasn't finding.

## 6. Anchor redesign (Part 6) and inference-floor removal (Part 7)

**`app/ai/pillar_scoring.py`**: the v2.0 scoring rule "do not lower a
score merely because little evidence was given" is removed. It is
replaced with an explicit rule distinguishing evidence *status* from
evidence *strength*:

- Thin evidence (Inferred, Low confidence) defaults to the lower half of
  whichever band it qualitatively fits, not the band's midpoint.
- "Little evidence was given" and "the evidence given is weak" are
  named as different findings that should usually produce different
  scores -- one specific, hard-to-fake fact can still score well even
  if it's the only fact available; generic narrative that could describe
  any company at this stage should not default upward merely because
  nothing contradicts it.
- **A score of 7+ now requires evidence specific enough that a
  reasonable investor would treat it as a real signal** (a named figure,
  a named outcome, a named prior history) -- generic narrative caps at 6
  regardless of tone.

**`app/ai/scoring_methodology.py`**: all 5 Team dimensions and all 4
Execution dimensions had their `score_9_10` through `score_0_2` band
text and `stage_guidance` rewritten (9 of the methodology's 28
dimensions; Market/Product/Traction/Financial Health dimensions were
**not** rewritten in this phase -- see Section 12). The new pattern,
applied consistently:

- **9-10**: exceptional AND specifically evidenced (a named fact),
  clearly exceeding the stage's norm.
- **7-8**: strong for this stage AND backed by one specific, checkable
  fact -- not general positive narrative.
- **5-6**: a plausible, generic positive impression with no specific
  fact distinguishing it from an average company at this stage.
- **3-4**: a meaningful, evidenced gap for this stage, or the only
  positive evidence is an unverified self-description.
- **0-2**: evidence *affirmatively* shows weakness or contradiction --
  never assigned merely for missing evidence (missing evidence is an
  evidence-status/Unavailable question, decided in Stage 1, not a
  scoring-stage question).

`stage_guidance` text for every one of these 9 dimensions was rewritten
to name a concrete, checkable expectation at each stage (e.g. Execution
Track Record, Pre-seed: "a shipped prototype/MVP that real users have
touched," not "prototype or MVP progress") rather than a generic
maturity description, directly addressing Part 8/9's stage-relative
requirement.

## 7. Confidence/evidence architecture decision (Part 11)

**Decision: Option C ("confidence remains separate but low-evidence
claims cannot reach high anchors"), implemented as a deterministic
Python post-processing step**, not a prompt-only request and not a
multiplication of SPS by confidence (both explicitly rejected by Part
11).

`app/ai/scoring.py::apply_confidence_score_cap()`:

```
CONFIDENCE_SCORE_CAPS = {"Low": 6.0, "Medium": 8.5, "High": 10.0}
```

Applied to every LLM-scored subscore (before the Deterministic override,
which replaces Deterministic-named subscores' score AND confidence
unconditionally regardless of ordering, so the two mechanisms never
conflict). Never raises a score, never touches `score=None`, never
touches a High-confidence dimension. `High` confidence at the pillar
level already requires ≥80% weighted coverage AND ≥40% Observed-status
weight (`calculate_pillar_confidence`, unchanged) -- so the cap
structurally ties "can this dimension reach 9-10" to the same coverage/
observed-evidence bar the pillar-level confidence label already uses,
rather than inventing a second, disconnected threshold.

This directly targets Part 11's stated principle: "an 85 SPS built
primarily from low-confidence inference is not credible" -- a Low-
confidence dimension can still contribute a real, meaningful score (up
to 6.0, the "credible but ordinary" band), it just cannot alone claim
"exceptional."

## 8. Pillar weights (Part 12)

Unchanged. `PILLAR_WEIGHTS` in `app/ai/scoring_methodology.py` still
reads market 0.20 / team 0.20 / product 0.20 / execution 0.15 /
traction 0.15 / financial_health 0.10, asserted directly by a new
regression test (`test_pillar_weights_unchanged`,
`app/tests/test_methodology_v2_1.py`).

## 9. Methodology versioning (Part 17)

- `METHODOLOGY_VERSION` (`app/ai/sie_v2_methodology.py`):
  `v2-spec-2026-08-23` → `v2.1-spec-2026-08-29`.
- `ANCHOR_REGISTRY_VERSION` (same file): `v2-anchor-registry-2026-08-23`
  → `v2.1-anchor-registry-2026-08-29`.
- `PILLAR_PROMPT_VERSION` (`app/ai/pillar_shared.py`): `2.0` → `2.1`.
- `SCORING_VERSION` (`app/ai/scoring_methodology.py`): **left at `2.0`,
  deliberately.** Its own docstring scopes it specifically to
  `PILLAR_WEIGHTS` and the pillar→SPS aggregation formula
  (`calculate_base_score`) -- neither changed in this phase. Bumping it
  would overstate what changed; the three version bumps above already
  capture every real change (dimension anchor text, scoring-stage
  prompt rules, and the new evidence-provenance/confidence-cap
  mechanisms).

Every analysis already stamps `analysis_context.methodology_version`,
`anchor_registry_version`, `scoring_version`, and `prompt_version` at
analysis time (`app/workflows/due_diligence_workflow.py`, confirmed
during Phase 10.8's validation architecture review) -- this metadata
already exists and required no new plumbing. **No historical analysis
was rewritten.** Every analysis produced under V2 (including all 25 in
the frozen Phase 10.8 cohort, and the 8 real companies in the canonical
database) keeps its original `v2-spec-2026-08-23` stamp permanently;
only analyses run from this point forward will carry the V2.1 stamps.

## 10. Tests added (Part 16)

`app/tests/test_methodology_v2_1.py`, 21 tests, all passing, zero LLM
calls:

- Unsupported financial number rejection ("fast-growing" must not
  become "$20M ARR"; "well funded" must not become "$80M cash balance").
- Supported financial number preservation (a number present in the
  source text is never stripped).
- An explicit derived calculation (a ratio computed from two supported
  inputs) is still flagged if the ratio itself was never supplied
  verbatim -- documented as an intentional limitation of a token-level
  guard, not a bug (Section 12).
- `apply_provenance_guard`: forces Unavailable when nothing survives,
  downgrades confidence when partially supported, leaves fully-
  supported dimensions byte-identical, skips already-Unavailable
  dimensions, and is deterministic across repeated calls.
- Confidence-score-cap: Low/Medium/High ceilings enforced correctly,
  never raises a score, never touches an unscored dimension.
- Synthetic scale-reachability fixtures (Part 13): very-weak,
  exceptional, mixed, stage-relative-early-exceptional, and mature-weak
  profiles, confirming the 0-100 scale can represent the full spectrum
  under the new mechanics when the underlying subscores warrant it
  (all synthetic, none written into canonical product data).
- SPS bounded 0-100 (`clamp_score`).
- Pillar weights unchanged (exact-equality assertion against the
  frozen dict).

**Existing test-suite regressions found and fixed** (both were
pre-existing test fixtures whose mock evidence cited a number not
present in their own mock `company_text` -- exactly the kind of gap the
new provenance guard is designed to catch, so the fixtures were updated
to be internally consistent rather than the guard being weakened):
`app/tests/test_evidence_scoring_pipeline.py` (added "33% year-over-year"
to `COMPANY_TEXT`) and `app/tests/test_scoped_correction.py` (same fix).
One version-string assertion was updated to match the new
`METHODOLOGY_VERSION`
(`app/tests/test_sie_v2_methodology.py::test_methodology_version_stamped`)
-- an expected, deliberate consequence of Section 9's honest version
bump, not a defect.

## 11. Diagnostic replay (Part 14)

The six Phase 10.8A diagnostic companies (Rippling, Databricks, Plaid,
Clubhouse, Relaw, Dome) were re-run through the V2.1 pipeline via
`app/calibration/discrimination_audit_2026_08/diagnostic_replay_v2_1.py`
(same zero-database-write isolation pattern as the Phase 10.8 harness,
writing to a new `diagnostic_replay_v2_1/` directory -- the frozen V2
`raw_results/` was never opened for writing). **This is explicitly not a
blind validation** -- these six companies directly shaped several V2.1
changes above, so their results are diagnostic/regression evidence only,
never validation evidence. See the accompanying final report for the
resulting V2-vs-V2.1 comparison table.

## 12. Remaining limitations, stated honestly

- **Anchor rewrite scope**: only Team (5 dimensions) and Execution (4
  dimensions) had their score bands rewritten this phase -- the two
  pillars Phase 10.8A's audit specifically implicated. Market, Product,
  Traction, and Financial Health dimensions still carry their original
  V2 band text (though all LLM-scored dimensions, regardless of pillar,
  now benefit from the rewritten general scoring rule in
  `pillar_scoring.py` and the confidence-score cap). A full 28-dimension
  anchor pass was out of scope for this single phase and would itself
  carry meaningful overfitting risk if tuned only against this cohort.
- **Evidence-provenance guard is a token-level check**, not a semantic
  one: it can catch "this specific number was never supplied" but
  cannot verify a number is *correct*, cannot catch a fabricated claim
  with no digits in it, and (per Section 3) can only check against the
  condensed research brief actually persisted, not the raw source
  material, which is a real architectural gap this phase did not close.
- **Research-enrichment cost/latency increase** (1 → 4 Tavily calls per
  analysis) was not load-tested or cost-modeled in this phase.
- **Financial evidence fabrication prevalence (72%) was measured
  against the frozen, now-historical V2 cohort** -- this phase's fixes
  (Sections 3 and 4) have not yet been validated against a new blind
  cohort to confirm they actually reduce this rate in practice; that is
  exactly what Phase 10.8C's new cohort is for, and this phase does not
  claim otherwise.
- **The diagnostic replay (Section 11) is not evidence V2.1 "works"** --
  restated because it is the single easiest thing for this document to
  be misread as. A real answer requires Phase 10.8C's new, independently
  selected, frozen cohort.
