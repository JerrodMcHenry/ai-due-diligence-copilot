# SIE Methodology v2 — Implementation Gap Analysis (Phase 1)

Produced before any code was modified, per instruction. Canonical target:
`app/docs/SIE_Methodology_v2_Specification.md` (commit `438d17c`).

## Production pipeline trace (v1, as it exists today)

```
POST /analyze-startup | /analyze-pdf | /analyze-website  (app/api.py)
  -> run_due_diligence(company_text)  (app/workflows/due_diligence_workflow.py)
       -> enrich_research()                         (app/ai/research_enrichment.py, Tavily)
       -> build_enriched_text()
       -> summarize/risk/competitor/memo/structured_analysis  (5 unrelated LLM calls)
       -> analyze_pillars_from_enriched_text()
            -> analyze_market/founders/product/execution/traction/financials()
                 -> analyze_pillar(pillar, text, result_model, extra_fields, extra_rules)
                      -> extract_pillar_evidence()   (app/ai/evidence_extraction.py, stage 1: evidence only, no score)
                      -> score_pillar_evidence()     (app/ai/pillar_scoring.py, stage 2: scores normalized evidence)
                      -> finalize_pillar_score()     (app/ai/scoring.py: weighted avg over scored set)
       -> build_sie_methodology_analysis()  [PASS 1, readiness=None]
            -> assemble_sie_analysis()      (app/workflows/sie_assembler.py)
                 -> calculate_investment_score()  (app/ai/investment_score.py: SPS)
                 -> build_startup_scorecard()      (app/ai/scorecard.py: parallel SPS calc, then overwritten)
       -> generate_readiness_score()  (app/ai/readiness_score.py, separate LLM call, prose only)
       -> build_sie_methodology_analysis()  [PASS 2, readiness=readiness]  (re-assembles only to inject readiness text)
  -> save_analysis() / save_score_history()  (app/database/db.py)
```

Migrations run unconditionally at import time in `app/api.py` (`create_tables`,
`add_analysis_columns`, `add_scoring_columns`, `add_benchmarking_columns`,
`add_company_name_column`, `add_readiness_columns`, `add_methodology_column`,
`create_score_history_table`). The `analyses.methodology` column (JSONB) is the only
structured/versioned column — every other provenance field lives inside that JSON blob via
`AnalysisContext`, not as a separate DB column.

## Gap table

| Component | Current (v1) behavior | Required (v2) behavior | Files affected | Migration risk | Backward-compat concern |
|---|---|---|---|---|---|
| Dimension count/list | 30 dims, 5 per pillar uniformly. Includes **Execution Velocity** (Execution), **Commercial Validation** (Traction), **Fundraising Readiness** (Financial Health, scored) | 28 dims: Market 5/Team 5/Product 5/Execution **4**/Traction 5/Financial Health **4**. Execution Velocity removed (absorbed into Product Execution's roadmap-velocity evidence). Commercial Validation removed, replaced by new **Growth Velocity**. Fundraising Readiness demoted to unscored narrative flag | `app/ai/scoring_methodology.py` (SCORING_METHODOLOGY), `app/ai/scoring.py` (SIE_SCORING_CONFIG, duplicate of the above — see below) | Medium — existing stored analyses (JSONB) keep their old dimension names; new analyses use the new list. No backfill. | Frontend renders `subscores` generically by name (`PillarWorkspace.tsx`) — a removed dimension simply stops appearing in new analyses; old stored analyses still render their old subscores unchanged. No type break. |
| **Duplicated weight source** (pre-existing v1 issue, not v2-caused) | `SCORING_METHODOLOGY` (scoring_methodology.py, rich rubric+weight) and `SIE_SCORING_CONFIG` (scoring.py, name+weight only) are two independently-maintained dicts with the same 30 names/weights | Single authoritative source, per Phase 2's explicit instruction | `app/ai/scoring.py` | Low | None — `get_scoring_dimensions()`'s return shape is unchanged, only its implementation |
| Execution weights | .20 each × 5 (incl. Execution Velocity) | .25 each × 4 (frozen conservative default, Part 3) | `app/ai/scoring_methodology.py`, `app/ai/scoring.py` | Low | None |
| Traction weights/membership | Customer Growth .20 / Revenue Growth .20 / Retention .20 / Engagement .20 / Commercial Validation .20 | Retention .25 / Revenue Growth .25 / Growth Velocity .20 / Customer Growth .15 / Engagement .15 | same | Low | None |
| Financial Health weights/membership | Revenue Quality .20 / Unit Economics .20 / Burn Efficiency .20 / Runway .20 / Fundraising Readiness .20 | Runway .30 / Unit Economics .25 / Burn Efficiency .25 / Revenue Quality .20 (+ non-linear runway-floor cap, structural rule frozen, exact threshold CALIBRATION REQUIRED) | same | Low | None |
| Evidence-status enum | 3 states: `Observed / Inferred / Unavailable` (`app/models/scoring.py::EvidenceStatus`) | 9 states (Part 4): Not Expected By Stage, Not Applicable, Optional But Unavailable, Usually-Private And Unavailable, Expected But Unavailable, Research Failure, Explicit Management Refusal, Conflicting Evidence, Mixed Evidence | `app/models/evidence_analysis.py`, `app/models/scoring.py`, new `app/ai/sie_v2_evidence_semantics.py` | **High if the existing enum is replaced.** **Low if implemented additively** (new parallel field, existing 3-value field untouched) — chosen approach, see below. | `PillarWorkspace.tsx`'s `EVIDENCE_STATUS_BADGE_CLASSES` only styles `Observed/Inferred/Unavailable`; a raw enum swap would render new v2 states with an unstyled fallback class. **Decision: keep `evidence_status` as-is (its arithmetic treatment already matches v2 exactly — Unavailable is excluded from scoring either way), add v2's finer state as a new, additive `missing_evidence_state` field the frontend can adopt later without being required to.** |
| Pillar/overall coverage metric | Weight-fraction (`calculate_evidence_coverage`: covered weight ÷ total weight) | Dimension-count fraction over the in-scope (stage-applicable) set — Part 5 explicitly warns these are two different denominators sharing a name | `app/ai/scoring.py` | Low | `evidence_coverage` field on `PillarScoreBreakdown` keeps its existing meaning (additive field for the new metric, not a silent semantic change to the old one — avoids quietly breaking any consumer reading that number today) |
| Scoring-mode classification | None — every dimension goes through the identical 2-stage LLM pipeline, no deterministic/computed path exists | 5 Deterministic / 15 Hybrid / 8 Constrained LLM (Part 8) | `app/ai/sie_v2_methodology.py` (new), `app/ai/scoring_methodology.py` (mode tags), pillar wrapper modules for the 5 Deterministic dims | Medium — Deterministic dimensions need real Python conversion functions; several are explicitly CALIBRATION REQUIRED per the frozen spec itself (see Phase 5 finding below) | None — result shape (`Subscore`) unchanged; a Deterministic dimension's `score` is simply computed in Python instead of by the LLM scorer, same field |
| Unit Economics | SaaS-only definition, `evidence_requirement="Public"` (spec itself flags this as a mistag) | Business-model-agnostic, 6 evidence families, SaaS anchors FROZEN-scoped, others CALIBRATION REQUIRED; `evidence_requirement` corrected to Private | `app/ai/scoring_methodology.py`, `app/ai/financial_analysis.py`, new `app/ai/sie_v2_anchors.py` | Low | None |
| Burn Efficiency / Runway | Deterministic-in-spirit but actually just prose-anchored LLM dimensions (no real Python computation path exists in v1 either) | Hybrid: quantitative when computable, qualitative fallback per FROZEN band architecture (calibration-program-derived) otherwise | `app/ai/scoring_methodology.py`, `app/ai/financial_analysis.py`, `app/ai/sie_v2_anchors.py` | Low | None |
| Customer Demand | Broad definition incl. revenue/retention/expansion signals | Narrowed to pre-revenue/pre-Traction only; Not Applicable at Series A+ once real Traction exists, determined by actual maturity not round label | `app/ai/scoring_methodology.py`, new `app/ai/sie_v2_anchors.py` (lifecycle resolver) | Low | None |
| Growth Velocity | Does not exist in production at all (only inside `app/calibration/v2/scorer.py`, calibration-only) | New Deterministic dimension in Traction; requires materiality floor + CAGR + scale-tier bands (Growth Velocity/Customer Growth architecture is FROZEN per the calibration program; exact scale-tier cutoffs are FROZEN AS PROVISIONAL) | new `app/ai/sie_v2_anchors.py`, `app/ai/traction_analysis.py` | Medium — requires structured numeric facts (counts/dates) the current evidence-extraction stage does not explicitly extract as structured data today (see "Structured fact extraction" gap below) | None |
| Structured fact extraction | `evidence_extraction.py` extracts free-text `evidence`/`signals` (strings), not typed numeric facts (count, unit, period) | Deterministic dimensions need typed inputs (two dated counts, a unit, a window) to compute a real CAGR | `app/ai/evidence_extraction.py` (new optional structured-fact fields), `app/ai/sie_v2_anchors.py` | **This is a genuine, honestly-reported implementation gap** — full natural-language-to-structured-fact extraction robust enough for production is a larger scope than this phase can safely build and verify. **Scoped-down approach taken**: `sie_v2_anchors.py`'s conversion functions accept already-typed inputs and are fully unit-tested against synthetic and calibration-program inputs; a best-effort regex/heuristic extractor pulls simple `"X -> Y over Z months"`-shaped facts from the existing `signals` list where present, falling through to `CALIBRATION_ANCHOR_REQUIRED`/Unavailable (never a fabricated number) when it cannot. Reported explicitly as v2.1-scoped hardening, not silently glossed over. | None |
| Provenance | `AnalysisContext` already has `methodology_version, scoring_version, model_identifier, prompt_version, company_text_hash, search_query, research_brief_snapshot, source_snapshot, analyzed_at` — but `methodology_version` is **never actually set** (`build_provenance_context()` omits it, so it silently stays at its Pydantic default `"1.0"` even for v1 analyses today) | Must be explicitly stamped `"v2-spec-2026-08-23"`, plus a new anchor-registry-version field | `app/workflows/due_diligence_workflow.py`, `app/models/analysis_context.py` | Low | None — additive field, existing consumers unaffected |
| Aggregation (dimension→pillar, pillar→SPS) | Already scored-set-only, already renormalizes, already excludes `None`/`Unavailable` with no defaulting — **this already matches v2 Part 4/9's core requirement** | Same logic, updated weights/dimension list (see above); Partial Structural Coverage is new | `app/ai/scoring.py`, `app/ai/investment_score.py`, `app/ai/scorecard.py`, new `app/ai/sie_v2_evidence_semantics.py` (PSC detector) | Low | None |
| Pre-existing v1 bug (unrelated to v2, noted not fixed) | `investment_score.py` and `scorecard.py` define **different** score-band recommendation thresholds; `scorecard.py`'s own computed score/recommendation are silently discarded and overwritten by `investment_score.py`'s in `sie_assembler.py` | N/A — out of scope for this methodology implementation | — | — | Flagged for a future, separately-scoped cleanup; not touched here per "do not redesign" |
| Evidence Independence Metadata | Does not exist | Metadata-only (independent_coverage_pct, concentration flag, semantic-duplication flag); explicitly may be left as v2.1 debt if non-trivial | new `app/ai/sie_v2_evidence_semantics.py` | Low if scoped to data-model + a pure-Python post-hoc computation over already-produced Subscores (chosen approach); High if it required new LLM-side evidence-event tagging (deferred, reported as debt) | None — additive |

## Anchors the frozen spec itself marks underspecified (Phase 5 stop-and-report)

Per Phase 5's explicit instruction, these are **not improvised** — the frozen spec (Part 11) and
the calibration program's own artifacts are used as the only source for provisional numbers; where
neither exists, the dimension stays `CALIBRATION_ANCHOR_REQUIRED`/Unavailable rather than inventing
a threshold:

- Customer Growth / Revenue Growth conversion function: **exists** as the calibration program's
  FROZEN architecture (floor → CAGR → scale-tiered bands) — implemented from
  `app/calibration/v2/freeze_sprint/PART1_2...` and `anchor_calibration/phase1/ANCHOR_DESIGN.md`.
  Exact scale-tier cutoffs: FROZEN AS PROVISIONAL, implemented and flagged as such.
- Burn Efficiency / Runway qualitative bands: FROZEN architecture (5-tier / 6-tier), exact
  within-band placement FROZEN AS PROVISIONAL — implemented and flagged.
- Non-SaaS Unit Economics numeric thresholds: **not implemented as numbers** — only the SaaS
  family has a FROZEN numeric anchor; the other 5 families remain qualitative-judgment /
  `CALIBRATION_ANCHOR_REQUIRED`, exactly as the spec itself states, no number invented.
- Partial Structural Coverage trigger threshold, SPS-suppression coverage floor, ranking-tier
  boundaries: **no calibration-program value exists for any of these** (Part 11 lists them as
  still open). Implemented with the most literal, non-invented reading available (PSC triggers on
  ANY entirely-unavailable pillar — a threshold of "1", the floor of the possible range, not a
  tuned number) and explicitly flagged in code comments and this report as provisional pending a
  real threshold decision, not a silent invention.

## Implementation approach decided from this analysis

1. One new canonical config module (`app/ai/sie_v2_methodology.py`) is the single source of truth
   for dimension list, weights, modes, and anchor status — replacing the `scoring.py` /
   `scoring_methodology.py` duplication (Phase 2).
2. v2's finer evidence semantics are layered **additively** on top of the existing, working
   3-state pipeline rather than replacing it — this is the lowest-risk path that satisfies Part 4's
   *arithmetic* requirement (which the current code already meets) while adding the *reporting*
   granularity Part 4 also wants, without a frontend-breaking enum swap.
3. Deterministic dimensions get real Python scoring functions, called from the pillar wrapper
   modules after the existing LLM evidence/scoring stages run — not a replacement of the LLM stages
   for the other 23 dimensions.
