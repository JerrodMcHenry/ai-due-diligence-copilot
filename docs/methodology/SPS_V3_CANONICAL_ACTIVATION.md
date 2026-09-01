# SPS V3 Canonical Activation

Status: SPS V3 is now the **default** engine for the additive `sps_v3`
assessment computed on every new canonical startup analysis. V2.1
(`startup_intelligence_score` and everything that reads it) is
**unchanged and still runs unconditionally** on every analysis, exactly
as before this phase — this activation did not replace V2.1, it flipped
which engine computes `sps_v3` by default. See
`docs/methodology/SPS_V3_PRODUCTION_INTEGRATION_10_9.md` for the full
architecture this phase activated (unchanged by this phase).

## 1. What changed

One function, `app/ai/sps_v3_adapter.py::sps_v3_enabled()`:

```python
# Before: return os.getenv("SPS_ENGINE_VERSION", "v2_1").strip().lower() == "v3"
# After:
return os.getenv("SPS_ENGINE_VERSION", "v3").strip().lower() != "v2_1"
```

`SPS_ENGINE_VERSION` unset (the normal case, in every environment today)
now selects V3. Explicitly setting `SPS_ENGINE_VERSION=v2_1` forces
legacy (V3-off) behavior — the rollback switch, unchanged in mechanism
from Phase 10.9, just with the default flipped. Any other explicit value
also falls back to legacy (fails closed toward previously-shipped
behavior).

A corresponding comment in `app/workflows/due_diligence_workflow.py` was
updated to describe the new default; no logic there changed.

## 2. What did NOT change

- Zero SPS V3 methodology files touched (`app/ai/sps_v3_engine/*`,
  `app/ai/sps_v3_adapter.py`'s classification/scoring logic, evidence
  ontology, observation types, canonical-signal dedup, negative-evidence
  handling, Unknown firewall, Coverage/Confidence calculation,
  aggregation, provenance, freshness, conflict handling, scoring bands,
  publishability rules).
- Zero VPS files touched.
- Zero dashboard files touched — every consuming surface (Startup
  Profile's `SPSV3ScoreSection`, Compare's `sps_v3` passthrough) was
  already built in Phase 10.9 to activate automatically whenever
  `methodology.sps_v3` is non-null; flipping the backend default is
  sufficient to light it up, no frontend change required.
- Zero historical rows touched. `sps_v3` remains `None` on every
  analysis produced before this activation (or produced with the
  explicit legacy override) — never backfilled, never recomputed.
- Zero database schema change (methodology stays a single JSONB column,
  as established in Phase 10.9).

## 3. Rollback

```
SPS_ENGINE_VERSION=v2_1
```

forces the pre-activation behavior (V2.1 only, `sps_v3` stays `None` on
every new analysis) for emergency rollback or isolated testing. No other
mechanism exists or is needed — this remains intentionally a single
boolean environment variable, not a flag platform.

## 4. Version identifiers

- V3: `sps_v3.engine_version = "SPS_V3_10_9H"`, `sps_v3.scoring_version =
  "sps_v3.10_9.1"` — both live inside the `sps_v3` sub-object, unchanged
  by this phase.
- V2.1: `analysis_context.methodology_version` (the pre-existing
  `METHODOLOGY_VERSION` constant) — a completely separate field, on a
  completely separate part of the record, untouched by this phase and
  unaffected by whether `sps_v3` is present.

## 5. Shared-surface decisions (minimum safe changes)

| Surface | Class | Decision |
|---|---|---|
| Startup Profile | **A** — use V3 now | Already wired (Phase 10.9's `SPSV3ScoreSection`); activates automatically now that the flag defaults on. No code change. |
| Rankings / Discovery / Search | **B** — legacy for compatibility | `get_rankings()`/`discover_startups()`/`search_analyses()` read `methodology->>'startup_intelligence_score'` (V2.1) exclusively, verified by reading the live queries. **Not rewired to branch on `sps_v3`** — per this phase's own explicit instruction (no existing safe V3-aware ranking migration path; a null/tri-state SPS cannot be sorted numerically without a real ranking redesign, deferred). |
| Compare | **C** — mixed/version-aware | Already correctly implemented (`ComparisonStartup.sps_v3` passthrough, `ComparisonHeader.tsx` shows a "Limited"/"Not enough evidence" badge instead of a numeric ring whenever `assessment_state !== "sufficient"`). Verified live in code; no change. |
| Saved Startups | **B** — legacy for compatibility | `SavedStartupEntry.overall_score` is V2.1-only; no `sps_v3` field exists on this list-row shape. No change — this is a flat list view, not a details experience. |
| Historical trends (`score_history`) | **B** — legacy for compatibility | Confirmed: purely V2.1 flat-column schema (`market_score`...`overall_score`), no `sps_v3` awareness, no schema for it. Left untouched — building V3-aware history is explicitly out of scope for this phase. |
| Founder startup views | **B** — legacy for compatibility | Reads the same canonical `methodology` as Startup Profile but has no dedicated `sps_v3` rendering; unaffected either way (V2.1 fields unchanged). No change. |

## 6. Known, honest limitation carried forward from Phase 10.9

The V3 adapter (`classify_evidence_for_v3`) covers **9 of 27 dimensions**
— it does not populate Financial Health or the 4 quantitative Traction
dimensions (current_scale, growth_trajectory, retention_engagement,
capital_efficiency), by original, documented design (Section 7/20 of the
10.9 doc). This means **most new analyses will land in `limited` or
`insufficient`, not `sufficient`**, until a future phase builds a
structured-numeric extraction adapter for those dimensions — verified
live in this phase's own activation test (see Section 7 below):
`assessment_state: "limited"`, `coverage_pct: 26.0%`, Traction and
Financial Health both `coverage_pct: 0.0`. This is not a defect
introduced by this activation; it is the same adapter, doing the same
thing it was built to do, now running by default instead of behind an
opt-in flag.

## 7. Live activation verification (this phase)

Ran one real, unmodified `/analyze` request (real OpenAI + Tavily, no
`SPS_ENGINE_VERSION` set) against the local backend:

- `startup_intelligence_score` (V2.1): `68.1` — computed exactly as
  before, completely unaffected.
- `sps_v3` present: `true`, `engine_version: "SPS_V3_10_9H"`,
  `assessment_state: "limited"`, `overall_score: null` (never `0`),
  `coverage_pct: 26.0`, `withhold_reason: "Overall coverage 26.0% < 35%
  floor"`. Team pillar individually publishable (strength 8.61, 45%
  coverage); Traction and Financial Health honestly `null`/0% coverage.
- Persistence round-trip: `save_analysis()` → `get_startup_by_name()` →
  `StartupProfileResponse(**row)` correctly reconstructs `sps_v3` from
  the stored JSONB with zero migration, `overall_score` still `None`
  (never coerced to `0`), `assessment_state` intact.
- Legacy override verified in an isolated process:
  `SPS_ENGINE_VERSION=v2_1` → `sps_v3_enabled()` returns `False`.
  Default (no env var) in a separate fresh process → `sps_v3_enabled()`
  returns `True`. The local development shell was left with no
  `SPS_ENGINE_VERSION` set afterward.

Test data (`ZZ Activation Check Co`, analysis id 8878, startup id 33092,
user `zztest_sps_activation_user`) was deleted after verification.

## 8. Deployment requirement

**None required to enable this activation.** `render.yaml` sets no
`SPS_ENGINE_VERSION` today, so the next deploy of this code will
automatically default to V3 with zero configuration change. If the team
wants to defer activation in production specifically, add
`SPS_ENGINE_VERSION=v2_1` to the Render service's environment variables
**before** deploying this change. This phase did not deploy and did not
modify any remote configuration.
