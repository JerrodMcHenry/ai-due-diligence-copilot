# SPS V3 Production Integration (Phase 10.9)

Status: V3 is now real, integrated, additive production code -- behind a
feature flag, OFF by default. V2.1 remains the sole engine that runs by
default and is untouched by this phase. This document is the durable
record of what was built; see the chat-delivered Phase 10.9 final report
for the complete 43-item summary and verdict block.

## 1. Product contract

- **SPS = Strength**: how strong are the startup fundamentals we can
  responsibly evaluate.
- **Coverage = Completeness**: how much of the weighted methodology we
  could responsibly evaluate.
- **Confidence = Evidence trust**: how trustworthy is the evidence behind
  the assessment.

Three structurally independent numbers (inherited unchanged from Phase
10.8's `app/ai/sps_v3_engine/aggregation.py`, promoted to production this
phase -- Section 6 below). Confidence never multiplies into Strength.
Unknown never lowers Strength, always lowers Coverage. Negative evidence
can lower Strength. More information does not automatically raise SPS --
it raises Coverage, and MAY raise or lower SPS depending on what the new
evidence says.

## 2. Why `sps_v3` is a new field, not a reuse of `startup_intelligence_score`

`SIEMethodologyAnalysis.startup_intelligence_score` (V2.1) is `float = 0.0`
-- non-nullable, defaulting to zero. Tracing `calculate_base_score()`
(`app/ai/investment_score.py`) confirms this is a REAL, currently-latent
pattern: a hypothetical V2.1 analysis with zero scorable pillars would
already compute `0.0` there, indistinguishable from a genuinely
zero-scoring company. This phase does not touch that function (V2.1 is
frozen) -- but it is exactly why V3's own overall score could not safely
reuse that field. `app/models/sps_v3.py`'s `SPSV3Assessment.overall_score`
is `float | None = None`, and every consumer (adapter, persistence, API,
frontend) was built to keep None distinct from 0 end-to-end -- verified
by a real, live pipeline run in Section 9.

## 3. Historical preservation

Nothing about V2.1's fields, computation, or persistence changed.
`sps_v3` is purely additive: `None` on every historical record and on
every analysis produced while `SPS_ENGINE_VERSION` is unset (the
production default). No backfill, no reinterpretation, no migration
touches an existing row's `methodology` JSONB.

## 4. Architecture audited before any code was written

```
POST /analyze (app/api.py)
  -> run_due_diligence() (app/workflows/due_diligence_workflow.py)
       -> enrich_research()                    [V2.1, unchanged]
       -> six pillar analyses (analyze_pillar)  [V2.1, unchanged, LLM-scored]
       -> build_sie_methodology_analysis()      [V2.1, unchanged]
            -> assemble_sie_analysis()          [V2.1, unchanged]
                 -> calculate_investment_score() [V2.1, unchanged -- the
                    non-nullable, 0.0-defaulting startup_intelligence_score]
       -> generate_readiness_score()            [V2.1, unchanged]
       -> IF sps_v3_enabled(): compute_sps_v3_assessment()  [NEW, Part 6-9]
            -> classify_evidence_for_v3()  (one LLM classification call,
               zero new research)
            -> EvidenceBundle -> evaluate_all_dimensions() -> evaluate_sps()
               -> classify_ux_state()      [app/ai/sps_v3_engine, all frozen
                  deterministic logic from Phase 10.8F-J]
       -> sie_analysis.sps_v3 = <result or None>
  -> save_analysis()  [unchanged INSERT -- methodology JSONB carries
     sps_v3 automatically, no new column]
  -> StartupAnalysisResponse(methodology=sie_analysis)
```

Key findings from the audit (before any edit was made):
- `startup_intelligence_score` is assumed non-null in exactly one
  place that matters for ranking: `get_rankings()`/`discover_startups()`/
  `search_analyses()` (`app/database/db.py`) filter
  `methodology->>'startup_intelligence_score' IS NOT NULL` -- true for
  every analysis today (V2.1 always produces a real number), so this
  phase's V3 addition changes nothing about who appears in Rankings.
- `startup_scorecard.overall_score` (a SECOND, already-nullable score
  field on `SIEMethodologyAnalysis`) is force-overwritten to equal
  `investment_score.overall_score` in `assemble_sie_analysis()` -- so its
  nullability is currently dead in practice. Noted, not touched (V2.1 is
  frozen).
- Every canonical read path (`get_startup_by_name`, `search_analyses`,
  `get_rankings`, `discover_startups`, `get_startups_for_comparison`)
  reads directly from the `methodology` JSONB column -- there is no
  dedicated SQL column per pillar/score field beyond the legacy flat
  columns (`overall_score`, `market_score`, etc.), which are written but
  no longer read by any canonical query. This is precisely the existing
  precedent this phase followed for `sps_v3` (Section 6).
- Rankings/Search/Discovery: this phase does NOT extend these queries to
  independently rank on `sps_v3`. See Section 10 for why this is a
  deliberate, scoped decision, not an oversight.

## 5. Canonical domain model

`SIEMethodologyAnalysis` (`app/models/startup.py`) gained exactly one new
field: `sps_v3: SPSV3Assessment | None = None`
(`app/models/sps_v3.py`). `SPSV3Assessment` carries `engine_version`,
`scoring_version` (both distinct from V2.1's own version constants --
Part 28), `overall_score: float | None`, `coverage_pct`, `confidence`,
`assessment_state: "sufficient" | "limited" | "insufficient"`,
`withhold_reason`, and a `pillars: dict[str, SPSV3PillarResult]` (each
with its own `strength: float | None`, `coverage_pct`, `confidence`,
`publishable`, `withhold_reason`). `ComparisonStartup` gained the same
field for Compare (Section 12).

## 6. V3 engine promotion (no duplication)

The deterministic engine built across Phases 10.8F-10.8J lived only in
`app/calibration/sps_v3/`. It is now split:

- **`app/ai/sps_v3_engine/`** (NEW, production): `types.py`, `registry.py`,
  `signals.py`, `freshness.py`, `evaluators.py` (all 27 dimensions,
  unmodified), `aggregation.py` (including `classify_ux_state`,
  Phase 10.8J), `factory.py`, and one genuinely new file,
  `evidence_bundle.py` -- a production-appropriate replacement for the
  calibration harness's `SyntheticCompany` with the identical duck-typed
  interface (`.evidence`, `.negative_signals`, `.stage`) but none of its
  SYNTH_/CAL_-prefix naming validation, which exists only to keep
  synthetic test fixtures from naming a real company and would be
  nonsense applied to an actual production startup.
- **`app/calibration/sps_v3/{types,registry,signals,freshness,evaluators,
  aggregation,factory}.py`**: now thin re-export shims
  (`from app.ai.sps_v3_engine.X import *`) so every existing calibration
  import and all 76 Phase 10.8 tests keep working, unchanged, forever.
  Verified: re-ran all 76 tests and `run_calibration.py` after the move
  -- byte-identical results to before the promotion.

Not one evaluator's logic, not one aggregation formula, not one
provisional parameter value changed in this phase. `evaluate_all_dimensions`,
`evaluate_sps`, `classify_ux_state` are called by production exactly as
frozen by Phase 10.8J.

## 7. Evidence adapter -- scope and honest limitations

`app/ai/sps_v3_adapter.py`. Full module docstring covers the design in
detail; summarized here:

- **Zero new research, zero new evidence gathering** (Part 8). The
  adapter only re-reads the six `PillarAnalysis` objects V2.1 already
  computed for this exact analysis.
- **One LLM call**, gated behind the same feature flag, explicitly a
  CLASSIFICATION step (Part 7-permitted: "extract facts, normalize facts,
  classify evidence") over text V2.1 already extracted and already
  marked `evidence_status == "Observed"` (never `"Inferred"` -- an LLM
  judgment call is not a verified fact for V3 purposes). Its output
  schema has no score-shaped field anywhere; the model cannot express a
  numeric judgment even if it tried. Every actual number in `sps_v3` is
  produced exclusively by the frozen deterministic engine.
- **Firewall**: every classified claim carries a `verbatim_quote`, which
  is re-verified (case/whitespace-normalized substring check) against
  the source text after the call returns. A claim whose quote can't be
  found is dropped, never kept on trust -- mirrors
  `app/ai/evidence_provenance.py`'s existing "verify, don't just prompt"
  discipline. One real, malformed-field bug was found and fixed during
  live testing (Section 9) with no fabrication risk: the model
  occasionally emits an explicit `null` for a boolean field instead of
  omitting it; the schema now accepts `bool | None` and coerces `None`
  to `False`, never to a fabricated `True`. Per-pillar parsing means one
  malformed claim in one pillar can no longer discard every other
  pillar's valid claims (fixed in the same pass).
- **Scope: 9 of 27 dimensions**, across all 6 pillars except Financial
  Health: Market (`competitive_intensity`, `customer_demand`), Team
  (`founder_market_fit`, `execution_track_record_team`), Product
  (`customer_value`, `differentiation`), Execution (`product_execution`,
  `gtm_execution`), Traction (`commercial_validation`). These are the
  dimensions whose required observation fields (a named competitor, a
  founder's role, a shipped capability label, a contract type) are
  safely groundable in a verbatim quote without inventing a number. The
  4 Category-A quantitative dimensions (`current_scale`,
  `growth_trajectory`, `retention_engagement`, `capital_efficiency`) and
  2 further Category-B ones needing a precise number
  (`revenue_quality`, `customer_adoption`) are deliberately left
  UNKNOWN by this v1 adapter -- V2.1's evidence is free-text
  (`Evidence.statement`), and mechanically parsing a specific dollar
  figure or percentage out of narrative text without a dedicated,
  carefully-validated structured-numeric extraction step would risk
  exactly the numeric fabrication Part 10 exists to prevent. This is why
  Financial Health showed `coverage_pct: 0.0` in every test run in this
  phase -- an honest limitation of THIS adapter's scope, not a
  methodology defect (the engine itself scores Financial Health
  correctly whenever it IS given qualifying evidence; the calibration
  suite's synthetic fixtures prove this).
- **Named next step, not built here**: a dedicated structured-numeric
  extraction adapter for the 6 excluded dimensions, with its own
  validation discipline analogous to `evidence_provenance.py`'s numeric
  guard. Explicitly out of scope for this phase (Part 8/26).

## 8. LLM boundary

Made structurally, not just procedurally, obvious: the extraction
schema in `sps_v3_adapter.py` (`_CompetitorClaim`, `_ContractClaim`,
etc.) has no field that could hold a 0-10 or 0-100 score anywhere. The
system prompt states this explicitly ("there is no score field in your
output schema"). Every number in the final `SPSV3Assessment` traces to
`app/ai/sps_v3_engine/evaluators.py` and `aggregation.py` -- unmodified,
deterministic Python, not a model call.

## 9. Live, real verification (not just canned tests)

Ran the real, unmodified `run_due_diligence()` end to end against live
OpenAI + Tavily, `SPS_ENGINE_VERSION=v3`, for a realistic pre-seed
fintech company description. Result: V2.1's `overall_score` computed
normally (64.5, completely unaffected), and `sps_v3` produced a correct,
honest `insufficient` assessment (`coverage_pct: 9.0`, `overall_score:
null`) with two individually-strong-but-not-independently-publishable
pillars (Team 9.5, Execution 9.5, both driven by real, grounded
quotes about the founders' Stripe/QuickBooks backgrounds and a shipped
capability) and four pillars honestly `Unknown`. This is the first real
bug this phase found (the boolean-null crash, Section 7) -- caught and
fixed by this exact live run, not by the canned unit tests alone.

Also verified, live, against the real local Postgres instance: a full
`save_analysis()` -> `get_startup_by_name()` -> `StartupProfileResponse(
**startup)` round trip correctly reconstructs a populated `sps_v3` field
from the stored JSONB with zero schema migration (Section 11). Test row
and its `startups` entry were deleted after verification.

## 10. Rankings / Discovery / Search -- scoped, not extended, this phase

Because V3 runs ADDITIVELY alongside V2.1 (never instead of it) in this
integration phase, every analysis that has a `sps_v3` assessment ALSO
has a real, non-null V2.1 `startup_intelligence_score` by construction.
`get_rankings()`, `discover_startups()`, and `search_analyses()`
therefore already include every V3-assessed startup today, ranked
exactly as before -- Part 19's "LIMITED/INSUFFICIENT excluded from
numerical ordering" requirement has no live case to violate it, since
there is currently no startup with a V3 assessment and no V2.1 score.
This phase deliberately did NOT rewrite these three production-critical
queries to independently branch on `sps_v3.assessment_state`, because
that branching logic only becomes meaningful once a future phase makes
V3 the primary/sole engine (explicitly out of scope here -- Part 29).
Extending them now, with no real data able to exercise the new branch,
would be speculative surface area against the phase's own "do not
overbuild" instruction. `get_analytics()` similarly stays untouched;
`get_sps_v3_analytics()` (Section 13) is a new, separate, additive
endpoint for V3-specific counts instead.

## 11. Persistence

**No schema migration.** `methodology` is already a JSONB column;
`SIEMethodologyAnalysis.model_dump(mode="json")` (unchanged call site in
`app/api.py`'s `/analyze`) automatically serializes the new `sps_v3`
field exactly like every other nested Pydantic field V2.1 already
stores (evidence, subscores, `structural_coverage`, etc.) -- none of
which have dedicated SQL columns either. This mirrors the codebase's own
established pattern, not a new one. Verified via a real round-trip
(Section 9). `add_sps_v3_columns()` was considered and deliberately not
written -- there is nothing it would add that JSONB storage doesn't
already provide, and the codebase's own convention (every V2.1
richer-than-a-flat-column structure) already lives in JSONB only.

## 12. API contract

- **SPS null vs. zero**: `SPSV3Assessment.overall_score: float | None`,
  enforced end to end -- adapter, model, persistence, `ComparisonStartup`
  passthrough, frontend types. Verified live (Section 9): a real
  `insufficient` assessment serializes as `"overall_score": null`, never
  `0`.
- **Coverage/Confidence/assessment_state**: all three are top-level
  fields on `SPSV3Assessment`, never nested inside a narrative summary a
  client would have to parse.
- **`GET /compare`**: `ComparisonStartup.sps_v3` is a pure passthrough
  (re-validated through the Pydantic model, not hand-picked fields) of
  the stored JSONB -- `None` whenever the startup's latest analysis has
  no V3 assessment. Compare never manufactures comparability: a
  `sufficient` startup and a `null`-sps_v3 startup are shown exactly as
  they are, side by side, with no substituted value.
- **`GET /analytics/sps-v3`** (NEW, Section 13): counts of
  sufficient/limited/insufficient among the latest V3-assessed analysis
  per startup, plus the average overall_score among `sufficient` ones
  only (never averaging in a null).

## 13. Analytics

`get_sps_v3_analytics()` / `GET /analytics/sps-v3` (`app/database/db.py`,
`app/api.py`) -- deliberately separate from `get_analytics()`, which
describes the canonical V2.1 population and is unchanged. Verified live
against the real DB: `{"total_v3_assessed": 0, "sufficient": 0,
"limited": 0, "insufficient": 0, "average_sufficient_overall_score": null}`
on the current (V3-flag-off) database, as expected.

## 14. Startup Profile / SPSRing / three UX states

- **`SPSRing`** (`dashboard/components/sps/`): `score` widened to
  `number | null`. `null` now renders a distinct dashed track and "—"
  center label (`RingSVG.tsx`, `RingCenter.tsx`) -- structurally
  incapable of being confused with a real, low, or zero score, because
  the null branch never reaches `normalizeSPS`/`getSPSMetadata` (which
  would otherwise band a coerced 0 into the "F / needs attention"
  danger-red styling). Two PRE-EXISTING `?? 0` coercions were found and
  fixed during this audit (`ComparisonHeader.tsx`, `InvestorWorkspaceView.tsx`)
  -- both were live, reachable paths (`overall_score`/`current_sps` are
  typed nullable), not hypothetical. A third (`DiscoveryResultCard.tsx`)
  was audited and left as-is: its `?? 0` is provably unreachable (the
  underlying query enforces `startup_intelligence_score IS NOT NULL`),
  already documented as such before this phase.
- **`SPSV3ScoreSection`** (NEW, `dashboard/components/startup/`): the
  three-state renderer. `StartupHeroV2` uses it when
  `methodology.sps_v3` is present, and falls back to the exact,
  unmodified pre-existing V2.1 ring otherwise -- meaning every analysis
  produced today (flag off) renders byte-for-byte identically to before
  this phase.
  - **SUFFICIENT**: the SPSRing, driven by `sps_v3.overall_score`, plus
    Coverage/Confidence badges.
  - **LIMITED**: no ring. "Limited public assessment" heading, a list of
    individually-publishable pillars with their own strength, a list of
    pillars explicitly labeled "Not enough evidence," Coverage/Confidence
    badges.
  - **INSUFFICIENT**: no ring, no empty visual placeholder standing in
    for one. "Not enough evidence yet" plus Coverage.

## 15. Coverage / Confidence UX copy

Implemented as `title` tooltips on the shared `CoverageConfidenceBadges`
component (`SPSV3ScoreSection.tsx`), reused identically across all three
states so the two concepts are always explained the same way:
- Coverage: "Coverage shows how much of the startup we know enough about
  to evaluate. It is not a quality score -- a higher number just means
  we could responsibly assess more of the company."
- Confidence: "Confidence reflects the quality, recency, and
  corroboration of the evidence behind this assessment -- not the
  likelihood the company succeeds."

## 16. Founder claim / enrichment path

Not built this phase (Part 18 explicitly scopes this out beyond a design
note). The existing Startup Claim architecture
(`ClaimStartupButton.tsx`, `startup_claims` table) is unchanged and is
the correct integration point for a future phase to add a "Know this
company? Claim this startup to add verified information and improve
assessment coverage" CTA on LIMITED/INSUFFICIENT profiles -- explicitly
message it as raising Coverage, and possibly raising OR lowering SPS,
never as a guaranteed score improvement, matching the Phase 10.8J
Founder-Enriched design (`SPS_V3_SIMPLIFICATION_10_8J.md` Section 13-14).

## 17. VPS / Readiness firewalls

Re-verified via `git diff --stat` immediately before writing this
document: `app/ai/vps_scoring.py`, `app/ai/vps_guidance.py`,
`app/ai/readiness_score.py`, `app/ai/fundraising_readiness.py` all show
**zero diff, zero status** for this phase. Nothing in
`sps_v3_adapter.py` or `sps_v3_engine/` imports from, or is imported by,
any of those four files.

## 18. Feature flag

`SPS_ENGINE_VERSION` (`app/ai/sps_v3_adapter.py::sps_v3_enabled()`) --
one environment variable, default `"v2_1"` (V3 off). Setting it to
`"v3"` additively computes `sps_v3` alongside the always-on V2.1
pipeline; it changes nothing else. Deliberately not a flag platform --
Part 29 explicitly asked for the smallest defensible mechanism.

## 19. Migration strategy

No bulk rewrite, no automatic rescoring. Historical and current V2.1
analyses are untouched. A future explicit re-analysis (the existing
Phase 7.2.1 founder re-analysis path, `startup_id` passed to
`POST /analyze`) run while the flag is on will produce a NEW analysis
row with `sps_v3` populated -- `save_analysis()`'s existing INSERT-only
behavior (never UPDATE) already guarantees the prior record is
preserved, unmodified by this phase.

## 20. Known limitations (honest accounting)

1. Adapter covers 9/27 dimensions (Section 7) -- Financial Health has no
   safely-classifiable dimension in this v1 adapter and will show 0%
   coverage for essentially every company until a structured-numeric
   extraction step is built (explicitly out of scope this phase).
2. Real-world negative evidence (e.g. a company's well-known financial
   distress) will not automatically surface in `sps_v3` unless it
   appears as `"Observed"`-status evidence within V2.1's own pillar
   output -- the adapter does not independently search for or infer
   negative signals.
3. Rankings/Discovery/Search do not yet independently branch on
   `assessment_state` (Section 10) -- correct and sufficient for this
   phase's "V3 alongside V2.1" architecture, but will need real
   attention whenever a future phase makes V3 primary.
4. `_ExtractionResult` (the pillar-keyed schema container) is defined
   but no longer directly instantiated (parsing is per-pillar,
   Section 7) -- kept as living schema documentation; harmless, flagged
   here for transparency rather than silently left in.

None of these are structural defects in the methodology itself (the
frozen `app/ai/sps_v3_engine/` logic, carried over verbatim from Phase
10.8J) -- they are honestly-scoped v1 integration-adapter and
rollout-sequencing limitations, consistent with Part 8's explicit
instruction not to build a bigger evidence pipeline in this phase.
