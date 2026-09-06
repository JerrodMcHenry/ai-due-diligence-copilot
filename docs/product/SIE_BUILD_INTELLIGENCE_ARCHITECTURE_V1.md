# SIE Build Intelligence Architecture V1

**Status:** Architecture + contract specification only. No code changed in this phase (34C). Builds on
`docs/product/SIE_BUILD_METHODOLOGY_V1.md` (34B) — read that first; this document does not re-derive the
methodology, only the minimum persistence/API architecture to make one loop durable.

**Governing rule:** no table exists merely because the methodology contains a noun. A new persisted entity
is justified only when durable identity, relationships, querying, provenance, history, lifecycle,
integrity, or future reasoning cannot be safely represented by existing infrastructure. Every recommendation
below states which test it passes.

Every statement is labeled **CURRENT SYSTEM FACT** (verified against real code/schema this session) or
**RECOMMENDATION** (proposed, not built).

---

## A. Current architecture audit

### Backend

| Subsystem | What enters | What's derived | What persists | What's discarded | Survives reload | Queryable later | Provenance retained | Append-only? |
|---|---|---|---|---|---|---|---|---|
| `modeled_ventures` (`db.py:2946`) | founder-typed/AI-drafted fields | `model_result` (VPS JSONB, hidden from UI per 34A) | Whole row, `assumptions`/`model_result` as JSONB blobs | Nothing — full snapshot kept, but as one blob, not per-field history | Yes | Only as current-state; no per-field history in this table itself | No (JSONB has no per-field provenance) | **No** — `assumptions`/`model_result` overwritten on every `UPDATE` |
| `venture_missions` (`db.py:3290`) | title, description, mission_type, source, related_category, resource_ref | — | Whole row | Nothing | Yes | Yes (by venture_id, status, mission_type) | `source` (`vps_guidance`/`founder_created`) — coarse, table-level provenance only | **Partially** — `status`/`learning_summary`/`completed_at` are updated in place, but `completed_at` is set-forward-only and never cleared (`update_venture_mission_status_for_owner`) |
| `venture_model_updates` (`db.py:3653`) | full before/after `assumptions` + `categories` JSONB, before/after VPS | — | Whole row, `related_mission_id` FK | Nothing | Yes | Yes (by venture_id, by related_mission_id) | No per-field provenance, but full historical snapshot pair | **Yes** — pure INSERT, never updated |
| Venture history endpoint (`GET /ventures/{id}/history`, `app/api.py`) | reads the three tables above | Synthesizes a unified, newest-first event feed (`venture_created`, `action_added`, `learning_recorded`, `action_completed`, `model_updated`) with a category-change diff and an assumption-field diff (`_diff_assumption_changes`, a fixed curated field list) | Nothing new — read-only view | — | N/A (computed) | Inherits whatever the source rows have | N/A |
| Graduation (`venture_graduations`, `db.py:4799`) | `trigger` (`suggested`/`manual`), `company_name`, `connect_existing_startup_id` | — | Whole row, `UNIQUE(venture_id)` | Nothing | Yes | Yes | `trigger` — real, working Decision-shaped provenance (§ below) | **Yes** — one row, never mutated after creation (all-or-nothing) |
| Startup linkage | `venture_graduations.startup_id` FK | — | — | — | Yes | Yes | — | — |
| Recommendation logic (`vps_guidance.py::_next_milestones()`, `_validation_gaps()`) | reads `assumptions` + computed `categories` | A ranked candidate list, recomputed fresh on every call | **Nothing** — pure function, zero persistence | The entire ranking rationale, every time | No — regenerated from current state each call | No — no historical record of what was recommended last week | N/A — deterministic but stateless | N/A |
| Retained VPS internals (`vps_scoring.py::compute_vps`) | `assumptions` dict | `vps`, `categories[].score/basis`, `sole_uncorroborated_category` | Only as `modeled_ventures.model_result` (current snapshot) and `venture_model_updates.before/after_categories` (historical snapshot pairs) | — | Yes (in both forms above) | Yes, historically, via `venture_model_updates` | — | Historical form is append-only; current form is overwrite |
| Observation/evidence-like persistence | founder free text (`capture_venture_observation`) | **Nothing** — the raw text is stored verbatim as `venture_missions.learning_summary`; no classification survives the request | `learning_summary` (raw text only) | **The entire evidence classification** (see § E) | Raw text survives; classification does not | Raw text is queryable; classification is not | Raw text only | Same as `venture_missions` |
| AI/extraction calls in Build | `idea_structuring.py::structure_idea()` (onboarding only) | `VentureDraft` with per-field provenance | Only after founder confirms → becomes `modeled_ventures.assumptions` (provenance is then dropped — the saved venture has no `DraftProvenance` anywhere) | **All provenance tags, the instant a venture is created** | The values survive; the *provenance* does not | No | Exists only transiently, pre-save | N/A |
| Provenance models | `DraftProvenance` (`user_provided`/`ai_inferred`/`unknown`) | — | **Nowhere** — UI-only, exists only during the onboarding review screen's lifetime | Dropped on `POST /ventures` | No | No | This is the single clearest "provenance discarded at the door" finding in the whole audit | N/A |
| Analytics/event infrastructure (`docs/product/PRODUCT_EVENT_TAXONOMY_V1.md`, `_log_event_safe`) | discrete named events (`capture_recorded`, `venture_graduated`, etc.) | — | An events table (outside this audit's direct scope, but confirmed to exist and already log venture-scoped events with metadata) | — | Yes | Yes, but analytics-shaped (counts/funnels), not intelligence-shaped (not designed for "what did we believe then") | Minimal (event name + metadata only) | **Yes**, append-only by design |

### Frontend

| Subsystem | What enters | What's derived | Persisted (server) | Discarded | Reused how |
|---|---|---|---|---|---|
| `CaptureWhatHappened.tsx` | founder free text + optional category chip | Calls `extractCaptureSignals()`; renders checkboxes for field-mapped signals, plain list for informational | `learning_summary` (raw text) via `POST /ventures/{id}/capture`; assumption deltas via `PUT /ventures/{id}` if founder applies signals | The `ProposedSignal[]` array itself — recomputed client-side on next view, never sent to the server as structured data | **Directly reusable** as the founder-facing capture surface; needs one new call after existing `handleSave`/`handleUpdateModel` to persist confirmed evidence |
| `captureSignals.ts::extractCaptureSignals()` | raw text | `ProposedSignal[]` — `id, label, sourceQuote, fieldPath?, proposedValue?, polarity, actionRelevant?, suggestedActionTitle?` | Not itself — see above | Everything, every render | **Reuse unchanged.** 100% deterministic regex, zero AI call, zero network call, zero randomness — see § E for full audit. |
| `MissionsSection.tsx` (mission system) | pendingMission, validation-field draft | `primaryMission`, `activeMissions`, category-change explanation on model update | `venture_missions` rows via existing endpoints | The category-change explanation object (`CategoryChange[]`) — recomputed each render from before/after category arrays already in memory, never persisted itself | **Reuse unchanged** for Test lifecycle UI; its "Update my model" flow is the existing founder-confirms-evidence gesture, generalizable |
| `WeeklyReview.tsx` | `VentureHistoryResponse` | `buildWeeklyReview()` — did/learned/changed/strongest-movement summary, windowed to 7 days | Nothing new (pure view) | The windowed aggregation itself (recomputed each load — cheap, fine to keep recomputing) | **Reuse unchanged**; natural home for surfacing Outcome check-in prompts later (34D+) |
| `VentureProgress.tsx` / `VentureHistory` | `VentureHistoryResponse` | Grouped, dated event list + summary stats | Nothing new (pure view) | — | **Reuse unchanged**; needs two new event-type cases (`decision_recorded`, evidence-as-outcome) once those exist |
| Current Overview (`VentureWorkspace.tsx`) | venture, model_result, history | `PrimaryCommandCard` Case A/B | — | — | **Reuse unchanged this phase** (explicit non-goal, §Q) |
| Current Model infrastructure (`VentureUnderstandingPanel.tsx`, 34A) | `model_result.categories` | know/believe/don't-know per category | — | — | **Reuse unchanged this phase** |
| Current What-If infrastructure | assumptions | `scenarioInsights.ts` output | — | — | **Reuse unchanged this phase** (explicit non-goal; deferred removal per 34B §16) |
| `ventureKnowledge.ts` | `VPSCategoryResult[]` | `CategoryKnowledge[]` (isEvidenceBased/hasSignal/facts) | — | — | Not directly reused by this phase's slice, but its provenance rule (`validation` = evidence, others = assumption) is the exact rule the new `venture_evidence.provenance` classification generalizes |
| Recommendation resolver (`resolveIdeaLabNextStep.ts`) | `VPSResult` | one of `add_assumptions`/`work_on_milestone`/`ready_for_real_startup` | — | — | **Adapt**: its Case A/B *shape* is exactly right (§ below); its input source changes from raw `next_milestones` to the new `current_question` field (§16) |
| `missionSuggestions.ts` | exact milestone string | `{relatedCategory, missionType, why}` | — | — | **Reuse as a fallback/template library** for `why_it_matters` copy; the new architecture also allows a dynamically-composed `why` (§14) |

**Summary of the audit's single most important finding:** the system already performs real evidence
classification (`captureSignals.ts`) and real provenance classification (`idea_structuring.py`) — and
*discards both, on schedule, every time*. This phase's job is not inventing classification logic; it is
giving already-working classification logic somewhere to live.

---

## B. LedgerFlow trace matrix

Tracing the directive's exact vertical slice, step by step.

| Step | Methodology object (34B) | Existing frontend | Existing backend | Existing table | Current API | Persists today? | Survives reload? | Provenance survives? | Queryable later? | Reuse unchanged? | Needs adaptation? | Genuinely new? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| "AI software helping finance teams collect overdue invoices" | Venture (current understanding) | `VentureWorkspace.tsx`, `VentureDraftReview.tsx` | `create_modeled_venture` | `modeled_ventures` | `POST /ventures` | Yes | Yes | Partial (provenance dropped at save, see §A) | Yes | Yes | No | No |
| "Will qualified controllers actually pay?" | Unknown / Question | none today as a durable object — only ever a freshly-computed `next_milestones` string | `_next_milestones()` | none (stateless) | embedded in `GET /ventures/{id}` via `model_result.next_milestones` | **No** | **No** — recomputed fresh, so the *specific wording SIE used* on Day 1 is not guaranteed to reappear identically on Day 6 if assumptions changed in between | No | **No** | No | Yes | **Yes** — needs a stable anchor (§C recommends: two new nullable columns on `venture_missions`, not a new table) |
| "Offer a paid pilot to 5 qualified controllers" | Test | `MissionsSection.tsx` create-mission flow | `create_venture_mission` | `venture_missions` | `POST /ventures/{id}/missions` | Yes | Yes | `source` only (coarse) | Yes | **Yes**, structurally | Yes — needs `question_text`/`why_it_matters` columns, widened `mission_type` | No |
| "Offered the pilot to five controllers. Two accepted at $500/month." | Result (raw) | `CaptureWhatHappened.tsx` / `MissionsSection`'s reflection field | `record_venture_mission_learning_for_owner` | `venture_missions.learning_summary` | `PUT` (mission reflection) or `POST /ventures/{id}/capture` | Yes (as raw text) | Yes | Founder-said, but untyped | Yes (full-text only) | Yes | No | No |
| "2 of 5 qualified prospects accepted a $500/month paid pilot" | Evidence | `captureSignals.ts::extractCaptureSignals()` (produces `ProposedSignal`) | none | **none** | none | **No** | **No** | Computed but never saved | **No** | Extraction logic yes; persistence no | Yes — needs founder-confirmation step to write to a new table | **Yes — new table** (§C) |
| "Initial transactional evidence supports willingness to pay... does not establish repeatable acquisition..." | Interpretation | none | none | none | none | **No** | **No** | N/A | **No** | Shape exists (`scenarioInsights.ts`, scoped to What-If only) | Yes — generalize the shape to real evidence | **New columns**, not a new table (§C) |
| "Continue the paid pilots and test whether customers use and retain the product" | SIE Recommendation | `missionSuggestions.ts`'s `why` field (fixed-string precedent only) | `_next_milestones()` (stateless) | none | none | **No** | **No** | N/A | **No** | Partial precedent | Yes | Partially new (composition logic), no new storage beyond Interpretation columns |
| "Proceed with the two paid pilots before investing heavily in a larger build" | Decision | none as a generic object; `GraduateVentureRequest.trigger` is the one working narrow precedent | none generic; `create_venture_graduation` is the one working narrow precedent | none generic; `venture_graduations` is the one working narrow precedent | none generic; `POST /ventures/{id}/graduate` is the one working narrow precedent | **No** (generically) | **No** | N/A | **No** | Pattern yes, table no | Generalize the pattern | **Yes — new table** (§C) |
| "One customer renewed. One customer churned." (60 days later) | Outcome | `CaptureWhatHappened.tsx` (as a generic capture, today with no link back to the original decision) | `capture_venture_observation` | `venture_missions` (as an unrelated new row) | `POST /ventures/{id}/capture` | Partially — as an unlinked capture | Yes, but **disconnected from the Decision it followed** | Founder-said, untyped | Yes, but not queryable *as* an outcome of that decision | No linkage exists today | Yes | **No new table** — modeled as `venture_evidence` with `evidence_type='longitudinal_outcome'` and a `related_decision_id` FK (§C) |
| "Initial willingness-to-pay evidence exists, but retention evidence is mixed" | Interpretation (updated) | none | none | none | none | No | No | N/A | No | Same as above | Same as above | Same as above |
| "Can LedgerFlow deliver enough recurring value...?" | Next Unknown | none as a durable object | `_next_milestones()` | none | none | No | No | N/A | No | Same as first Unknown row | Yes | Same as first Unknown row |

**Conclusion of the trace:** five of eleven steps already persist correctly today (Venture, Test-creation,
raw Result text, the graduation-shaped Decision precedent, and — trivially — nothing needed for the
already-stateless recommendation logic). Six steps have no durable representation at all today. Of those
six, exactly **two require genuinely new tables** (Evidence, Decision); the rest are additive columns on
`venture_missions` or are represented as typed rows in the new Evidence table (Outcome, Unknown-as-derived).

---

## C. Persistence gap analysis and architecture options (§12 of the directive)

### Options compared

| | A: dedicated tables for everything | B: one generic typed event table | C: hybrid (chosen) | D: minimal extension only |
|---|---|---|---|---|
| Implementation complexity | High — 5 new tables, 5 new model files, 5×CRUD | Medium — 1 new table, but every consumer must interpret a polymorphic payload | **Low-medium** — 2 new tables, additive columns elsewhere | Lowest, but fails the acceptance test (below) |
| Migration risk | Highest surface area | Medium (one migration, but schema-inside-JSON risk) | **Low** — additive only, no existing column touched | Lowest |
| Queryability | Best (real FKs, real indexes) | Poor (payload contents aren't indexable without extra work) | **Good** where it matters (Evidence, Decision have real FKs); acceptable elsewhere | Poor — no way to query "all evidence for this question" at all |
| Integrity | Best (per-type CHECK constraints) | Weakest (a generic payload can't enforce per-type invariants at the DB layer) | **Good** — CHECK constraints on the two new tables' typed columns | Weak |
| Provenance | Best | Requires payload discipline, easy to erode over time | **Good** | Poor |
| Correction/history | Best | Awkward (superseding an event inside a generic table needs its own convention) | **Good** — explicit `superseded_by_id`/append-only pattern, mirrors `venture_model_updates`' existing discipline | Poor |
| AI reasoning usability | Best | Requires the AI layer to parse arbitrary payload shapes | **Good** | Poor |
| Frontend consumption | Straightforward | Requires a switch/discriminated-union everywhere | **Straightforward** | Straightforward but incomplete |
| Longitudinal intelligence | Best supported | Supported with discipline | **Supported** — this is the actual bar (§ acceptance test) | **Fails** — no stable question/evidence identity survives |
| Future org/accelerator reporting | Best | Workable | **Workable** — real FKs make future aggregation queries straightforward | Poor |
| Eventual Startup Profile connection | Clean | Clean | **Clean** — same firewall discipline as VPS/SPS (34B §15) applies regardless of table count | Clean but data too thin to be useful |
| Risk of premature abstraction | **Highest** — Hypothesis/Unknown/Interpretation/Outcome tables would sit mostly empty/unused relative to their schema in a single-question V1 slice | Low risk of premature abstraction, high risk of *under*-abstraction (loses type safety) | **Lowest realistic risk** — new tables exist only where the trace matrix (§B) proved they're needed | None (too minimal) |

### Recommended: **Option C — Hybrid**

Dedicated tables only where the trace matrix (§B) showed genuine need (stable identity referenced by
multiple later steps, correction/history requirements, many-relationship potential): **Evidence** and
**Decision**. Everything else extends existing infrastructure:

- **Question/Unknown**: not a table. Two new nullable columns on `venture_missions`
  (`question_text`, `why_it_matters`) give the *current test's* targeted question stable identity for the
  duration of that test — exactly what the reload test (§N) requires — without a `hypotheses` table that
  would sit nearly empty in a single-active-question V1. Past questions remain queryable forever because
  past `venture_missions` rows are themselves immutable-once-set on this column and already permanently
  retained.
- **Interpretation**: not a table. Three new nullable columns on `venture_missions`
  (`interpretation_summary`, `interpretation_limitations`, `interpretation_generated_at`) — a test has
  exactly one live interpretation cycle in V1's single-question slice; folding it in avoids a table whose
  only relationship is a 1:1 back-reference to the row that already exists.
- **Outcome**: not a table. Represented as a `venture_evidence` row with `evidence_type =
  'longitudinal_outcome'` and a new `related_decision_id` FK — an outcome *is* evidence, definitionally
  (34B §13), so giving it a separate table would violate the governing rule directly.
- **Recommendation**: not persisted as its own object in V1 — computed at request time from
  `question_text`/`why_it_matters` (already persisted) plus the ranking logic (§I), same statelessness
  `_next_milestones()` already has today. If a future phase needs to audit "what did SIE recommend, even
  when the founder never started that test," promote this to a column later — YAGNI for V1.

This passes every row of the options table above without the abstraction risk of Option A or the
type-safety loss of Option B, and is the only option (besides A) that survives the reload/longitudinal
test in §N.

---

## D. Recommended minimum architecture

### D.1 `venture_missions` — additive columns (Test + folded Question + folded Interpretation)

**CURRENT SYSTEM FACT:** table already exists (`db.py:3290`), full schema quoted in §A.

**RECOMMENDATION** — additive migration only, no existing column touched, no existing row invalidated:

```sql
ALTER TABLE venture_missions
    ADD COLUMN question_text TEXT,
    ADD COLUMN why_it_matters TEXT,
    ADD COLUMN interpretation_summary TEXT,
    ADD COLUMN interpretation_limitations TEXT,
    ADD COLUMN interpretation_generated_at TIMESTAMP;

ALTER TABLE venture_missions
    DROP CONSTRAINT venture_missions_mission_type_check,
    ADD CONSTRAINT venture_missions_mission_type_check CHECK (mission_type IN (
        'customer_discovery', 'validation', 'pricing', 'gtm', 'product', 'founder', 'economics',
        -- widened per 34B §10's test taxonomy — additive, no existing value invalidated:
        'problem_interview', 'prototype_test', 'landing_page_test', 'willingness_to_pay_test',
        'paid_pilot', 'pre_sale', 'outbound_test', 'pricing_test', 'channel_test',
        'retention_observation', 'competitive_research', 'unit_economics', 'other'
    ));
```

All four existing NOT NULL/CHECK/default behaviors are untouched. `question_text`/`why_it_matters` are set
once, at mission creation, from the recommendation that prompted it (or left NULL for an ad-hoc
`founder_created` mission with no specific question behind it — allowed, matches §13's "founder can
proceed however they want"). `interpretation_*` columns are set once evidence is confirmed against this
mission (§D.2) and may be updated (not appended) if *additional* evidence arrives for the *same still-open*
test before it completes — this is the one place in the new schema where in-place update, not
append-only, is correct, because it mirrors `venture_missions.learning_summary`'s own existing
update-in-place semantics for the same underlying reason (a reflection can be revised before the mission
completes).

### D.2 `venture_evidence` — new table

**RECOMMENDATION**, genuinely new (§B, §C):

```sql
CREATE TABLE venture_evidence (
    id SERIAL PRIMARY KEY,
    venture_id INTEGER NOT NULL REFERENCES modeled_ventures(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id),
    related_mission_id INTEGER REFERENCES venture_missions(id) ON DELETE SET NULL,
    related_decision_id INTEGER REFERENCES venture_decisions(id) ON DELETE SET NULL,
    evidence_type TEXT NOT NULL CHECK (evidence_type IN (
        'founder_claim', 'reported_preference', 'observed_behavior',
        'commitment', 'transaction', 'longitudinal_outcome', 'external_source'
    )),
    statement TEXT NOT NULL,
    provenance TEXT NOT NULL CHECK (provenance IN (
        'founder_said', 'founder_observed', 'sie_inferred', 'sie_calculated', 'external_source'
    )),
    source_quote TEXT,
    structured_field_path TEXT,
    structured_value NUMERIC,
    relationship TEXT CHECK (relationship IN ('supports', 'contradicts', 'mixed', 'neutral')),
    founder_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    superseded_by_id INTEGER REFERENCES venture_evidence(id) ON DELETE SET NULL,
    occurred_at TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX venture_evidence_venture_idx ON venture_evidence (venture_id, recorded_at DESC);
CREATE INDEX venture_evidence_mission_idx ON venture_evidence (related_mission_id);
```

**Mapping to `captureSignals.ts::ProposedSignal`** (already-computed shape, § A finding): `label` →
`statement`, `sourceQuote` → `source_quote`, `fieldPath` → `structured_field_path`, `proposedValue` →
`structured_value`. `polarity`/`actionRelevant` remain frontend-only presentation concerns (they help the
founder *decide whether to confirm*, but once confirmed the row's `evidence_type` + `relationship` capture
what matters durably — no need to persist polarity itself). Every `founder_confirmed = true` row is exactly
one signal the founder explicitly accepted; a signal the founder never checked is simply never inserted —
"nothing becomes canonical merely because extraction found it" (33B, quoting `missionSuggestions.ts`'s own
established discipline) extends cleanly to Evidence.

**Correction, never destruction:** a founder correcting evidence inserts a **new** row and sets the old
row's `superseded_by_id` to point at it — mirrors `venture_model_updates`' full-snapshot-per-change
discipline and `update_venture_mission_status_for_owner`'s "set forward, never clear" pattern. The old row
is never deleted or edited in place.

### D.3 `venture_decisions` — new table

**RECOMMENDATION**, genuinely new (§B, §C):

```sql
CREATE TABLE venture_decisions (
    id SERIAL PRIMARY KEY,
    venture_id INTEGER NOT NULL REFERENCES modeled_ventures(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id),
    related_mission_id INTEGER REFERENCES venture_missions(id) ON DELETE SET NULL,
    sie_recommendation TEXT NOT NULL,
    sie_reasoning TEXT NOT NULL,
    founder_choice TEXT NOT NULL,        -- free text in V1 (see note); a closed enum is a safe additive
                                          -- CHECK to add later once the vocabulary (34B §10) stabilizes in
                                          -- real usage -- adding a CHECK constraint later is a zero-risk
                                          -- additive migration; starting with one and having to widen it
                                          -- under real founder language is the riskier order.
    founder_rationale TEXT,
    evidence_ids INTEGER[] NOT NULL DEFAULT '{}',
    supersedes_decision_id INTEGER REFERENCES venture_decisions(id) ON DELETE SET NULL,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX venture_decisions_venture_idx ON venture_decisions (venture_id, decided_at DESC);
```

`evidence_ids INTEGER[]` (a plain Postgres array, not a join table) is deliberate: this is a short,
immutable-once-decided list with no need for its own queryable attributes — the same "avoid a join table
that adds nothing" judgment already made once in this codebase's own design history is being reapplied,
not invented fresh. A reversal is a **new** row with `supersedes_decision_id` set, exactly mirroring
`venture_evidence.superseded_by_id` — one correction pattern, used twice, not two different ones.

**Precedent this generalizes:** `GraduateVentureRequest.trigger` (`suggested`/`manual`) is the working,
narrower ancestor of `sie_recommendation` vs. `founder_choice` — `venture_graduations` itself is left
completely unchanged; this is a new, general-purpose table, not a rename of the existing one.

### D.4 Not built (explicit)

- No `hypotheses` table (§C).
- No `unknowns` table (§C).
- No `interpretations` table (§C — folded into `venture_missions`).
- No `outcomes` table (§C — folded into `venture_evidence`).
- No scheduler/reminder infrastructure (§K/§L).
- No new score, no confidence percentage anywhere in any new column.

---

## E. Capture signals — deep audit (§5 of the directive)

**CURRENT SYSTEM FACT**, fully verified by reading `dashboard/lib/captureSignals.ts` (387 lines) end to end:

- **Exact signal types detected today:** interview/conversation counts, dollar-per-month/year price
  mentions (split positive/negative/neutral by nearby willingness-to-pay language), new-paying-customer
  mentions (both a fixed-phrase pattern and a "N more customers signed up" counted pattern), countable
  churn (with a matching +/- delta mechanic to new-customer counting), an explicit retention percentage
  (with nearby trend-word polarity), and six purely informational patterns (churn mention, complaint/
  friction, product milestone, fundraising mention, competitor mention, experiment result) — the first of
  which (churn) is suppressed when a *countable* churn signal already matched the same note, to avoid
  showing the same real event twice.
- **How extraction works:** pure regular-expression matching against the founder's raw text, with a
  windowed proximity check (looking 20-60 characters around a match) to decide polarity/sign. No tokenizer,
  no ML model.
- **Deterministic vs. AI-generated:** **100% deterministic.** Zero LLM call, zero network call, zero
  randomness anywhere in this file. This is a materially important finding for §14 (AI boundaries):
  building on this pipeline adds **no new AI system** by construction — it is regex, the same class of
  mechanism `vps_guidance.py`'s own template generation already uses.
- **Where classification disappears:** confirmed at the render layer. `CaptureWhatHappened.tsx` calls
  `extractCaptureSignals(text)` fresh every time the "saved" step renders; the resulting `ProposedSignal[]`
  lives only in React state (`signals`) for the current component lifetime and is never sent to any
  endpoint as structured data — only the raw `text` (via `POST /ventures/{id}/capture`) and, if a
  field-mapped signal is applied, the resulting *already-merged* assumption value (via `PUT
  /ventures/{id}`) survive.
- **Can signals become the start of the canonical Evidence pipeline?** **Yes, directly, with no rework** —
  see the field-mapping table in §D.2. The shape is already correct; it needs one new call to persist it.
- **Missing metadata:** `evidence_type` (§4 of 34B's taxonomy is not classified today — every signal is
  presentation-flat), `provenance` (today conflated: everything is implicitly `founder_said`, with no
  `sie_inferred` distinction even though the extraction itself *is* an SIE inference over the founder's raw
  text), `sample_size`/`segment` (never captured), and any link to *which question/test* this evidence
  bears on (today evidence is venture-scoped only, never question-scoped).
- **Founder confirmation that already exists:** the checkbox UI (`checkedSignalIds`, a `Set<string>`) is a
  real, working founder-confirmation gesture — a signal is only ever applied to `VentureAssumptions` if the
  founder explicitly checked it (`hasSelectedFieldSignals`) and then clicked "Update my model." This is
  directly reusable as the Evidence-confirmation UI (§18) with zero redesign — it just needs to write to
  `venture_evidence` in addition to (not instead of) its current `PUT /ventures/{id}` behavior.
- **Can incorrect extraction be corrected?** Not today in any structural sense — a founder can simply not
  check a wrong signal (silent rejection, fine), but there's no "this label is wrong, here's the right one"
  correction path. §D.2's `superseded_by_id` mechanism is the recommended fix, applied at the Evidence
  layer once it exists (correcting a *confirmed* piece of evidence, not the ephemeral proposal).
- **Adapt vs. replace:** **adapt.** No technical reason exists to build a second extraction system. The
  only change needed is a destination for the output.

---

## F. Missions/actions — deep audit (§6 of the directive)

Can `venture_missions` become the persisted Test concept? **Yes**, per the trace matrix (§B) and the
column-by-column check below.

| Required Test capability (34B §2.4 / this phase §6) | Representable today? | How |
|---|---|---|
| Question being tested | **No** | New: `question_text` column (§D.1) |
| Related hypothesis/unknown | **N/A in V1** — no Hypothesis table exists or is recommended (§C); the question column itself is the anchor | — |
| Why the test matters | **No** | New: `why_it_matters` column (§D.1) |
| Instructions | Partially | `description` column already exists and is free text; sufficient |
| What to record | **No**, not structured | Recommend: encode as part of `description`/`why_it_matters` copy in V1 (a template string per `test_type`, mirroring `missionSuggestions.ts`'s existing per-milestone template pattern) rather than a new column — this is presentation copy, not state, and doesn't need its own field yet |
| Status | **Yes** | `status` (`active`/`completed`/`dismissed`) already exists and already means exactly this |
| started_at | **Yes** | `created_at` already serves this (a mission's creation *is* the test starting, in the current one-step-creation UX) |
| completed_at | **Yes** | Already exists, already set-forward-only |
| Result | Partially | `learning_summary` already holds the raw result text; **no structured result field exists** — not needed as a new column per §C (structured result *is* the Evidence rows it produces) |
| Relationship to evidence | **No** | New: `venture_evidence.related_mission_id` FK (§D.2) — the relationship lives on Evidence, not on the Test, since one Test can produce many Evidence rows |
| Relationship to eventual decision | **No** | New: `venture_decisions.related_mission_id` FK (§D.3) |

**Recommendation:** adapt `venture_missions` with the five additive columns in §D.1 plus the widened
`mission_type` CHECK. **No new Tests table.**

---

## G. Hypothesis + Unknown persistence (§7 of the directive)

Evaluated against the five listed alternatives:

- **A (dedicated table):** rejected for V1 — the trace matrix (§B) shows a single active question per test
  is sufficient for the required loop; a dedicated table would carry stable identity, relationships, and
  lifecycle largely unused in a V1 with one live question per venture at a time.
- **B (typed venture-understanding/event records):** rejected — this is Option B's generic-event-table risk
  (§C) applied narrowly; adds a discriminated-union burden for a concept that, in V1, has exactly one
  reasonable shape (a question string + why it matters).
- **C (structured data attached to existing venture/model history):** **chosen**, in the specific form of
  §D.1's additive `venture_missions` columns — the "existing history" being extended is the Test's own row,
  which already has the right lifecycle and ownership scoping.
- **D (derivation from assumptions + evidence):** partially adopted — the *next* question (after the
  current one resolves) is still derived fresh each time from assumptions + accumulated Evidence, exactly
  as `_next_milestones()` already does (§I) — no persistence needed for a not-yet-selected candidate
  question.
- **E (other):** not needed; C+D together cover every requirement in §7 without a new table.

**What this gives up, honestly:** true multi-hypothesis tracking (several open questions with independent
lifecycles, evidence linked across many of them simultaneously) is **not** supported by this V1 design —
only the single question currently being tested has durable identity. This is an explicit, acceptable V1
limitation (§Q), not an oversight: the directive's own LedgerFlow slice never requires more than one live
question at a time, and adding multi-hypothesis tracking later is a straightforward promotion (add a real
`hypotheses` table, backfill `venture_missions.question_text` values as seed rows) rather than a rewrite.

---

## H. Evidence and Interpretation persistence — recommendation restated

Covered fully in §C/§D.2/§E. Restated here only to answer the directive's explicit required fields
checklist (§8):

| Required field | Present in `venture_evidence`? |
|---|---|
| venture_id | Yes |
| evidence identity | Yes (`id`) |
| evidence type | Yes (`evidence_type`, 7-value CHECK, 34B §4 taxonomy) |
| statement/observation | Yes (`statement`) |
| source/provenance | Yes (`provenance`, 5-value CHECK, 34B §14 vocabulary) |
| founder-confirmed status | Yes (`founder_confirmed`) |
| occurred_at / recorded_at | Yes, both, distinct columns |
| quantitative data when relevant | Yes (`structured_value`, nullable) |
| segment/context when relevant | **Not in V1** — no `segment` column; explicit V1 gap (§Q), additive to add later |
| relationship to question when known | Yes, via `related_mission_id` (the question's stable anchor, §D.1) |
| supports/contradicts/informs relationship | Yes (`relationship`) |
| extraction provenance if SIE-extracted | Yes — `provenance = 'sie_inferred'` plus `source_quote` for verification, mirroring `idea_structuring.py::_quote_is_verifiable()`'s exact discipline |
| correction without destroying history | Yes (`superseded_by_id`) |

**No Evidence Score exists anywhere in this design.** `structured_value` is a raw observation (a count, a
percentage, a dollar figure) — never a derived strength/confidence number.

---

## I. Recommendation engine V1 contract (§15 of the directive — design only, not implemented)

**Input (conceptual, not a literal function signature):** current venture understanding (`assumptions` +
`categories`), the current open question if one exists (`venture_missions.question_text` for the latest
non-completed mission, if any), all `venture_evidence` rows for the venture ordered by `recorded_at`, any
`relationship = 'contradicts'` rows (contradiction flag), the most recent `venture_decisions` row, and any
`evidence_type = 'longitudinal_outcome'` rows (recent outcomes).

**Deterministic vs. AI:**
- **Deterministic (extend `_next_milestones()`'s existing tiering, §34B §7/§9):** selecting *which*
  candidate question ranks highest, given the criteria in 34B §7 (decision relevance, uncertainty, cost of
  being wrong, evidence gap, testability, sequencing, stage). This requires no new AI call — it is the
  same style of `candidates: list[tuple[int, str]]` priority-tier mechanism already in production.
- **Templated (extend `missionSuggestions.ts`'s existing per-milestone `why` pattern):** the `WHY IT
  MATTERS` / `WHY THIS TEST` / `WHAT TO RECORD` copy for a *known* candidate question — fixed strings keyed
  by test_type, exactly as today, no AI call.
- **Requires existing AI capability (reused, not new):** only the `WHAT RESULT WOULD BE INFORMATIVE` /
  `WHAT THIS WILL NOT PROVE` fields for a genuinely novel question SIE proposes that isn't already in the
  fixed template library (e.g. the ERP-integration hypothesis that emerged mid-walkthrough in 34B §19) —
  here, a short, constrained prompt against the venture's own assumptions + evidence is the same class of
  call `idea_structuring.py` already makes (structured JSON output, temperature 0, no free-associating).
  **This is not a new AI system** — it is the existing "structure founder-facing text from structured
  inputs" capability, redirected at a new output shape.

**Output shape (locked, matches 34B §9 and this phase §15 verbatim):**

```
MOST IMPORTANT QUESTION
WHY IT MATTERS
RECOMMENDED TEST
WHY THIS TEST
WHAT TO RECORD
WHAT RESULT WOULD BE INFORMATIVE
WHAT THIS WILL NOT PROVE
[founder alternatives: dismiss / choose a different test / proceed without testing]
```

No score. No probability. No "venture strength" number anywhere in this contract.

---

## J. API contract (§16 of the directive — design only, not implemented)

Ten conceptual capabilities requested; mapped to **three new endpoints** plus **additive fields on two
existing ones**, avoiding endpoint explosion.

| Capability | Endpoint | New or existing? |
|---|---|---|
| 1. Fetch current intelligence state | `GET /ventures/{id}` | **Existing**, response gains `current_question: {mission_id, question_text, why_it_matters} \| null` and `recommendation: {...§I shape} \| null` |
| 2. Start/accept a recommended test | `POST /ventures/{id}/missions` | **Existing**, request body gains optional `question_text`, `why_it_matters` |
| 3. Submit test result | `PATCH /ventures/{id}/missions/{mission_id}` | **New**, body `{result_text: string}` — mirrors `record_venture_mission_learning_for_owner`'s existing shape, additionally triggers extraction (client-side, free) and returns candidate evidence for confirmation |
| 4. Extract candidate evidence | *(none needed)* | **Not an API call** — `extractCaptureSignals()` already runs client-side for free (§E) |
| 5. Founder confirms/corrects evidence | `POST /ventures/{id}/evidence` | **New**, body `{mission_id?, statement, evidence_type, structured_field_path?, structured_value?, relationship?, source_quote?}`, response includes generated `interpretation_summary`/`interpretation_limitations` written onto the mission row in the same transaction |
| 6. Persist interpretation | *(folded into #5's response/side-effect)* | Not a separate call |
| 7. Present SIE recommendation | *(folded into #1)* | Not a separate call |
| 8. Record founder decision | `POST /ventures/{id}/decisions` | **New**, body `{mission_id?, sie_recommendation, sie_reasoning, founder_choice, founder_rationale?, evidence_ids: number[]}` |
| 9. Record later outcome/check-in | `POST /ventures/{id}/evidence` (same as #5) | **Reused**, with `evidence_type: 'longitudinal_outcome'` and a new optional `related_decision_id` in the body |
| 10. Compute next highest-value question | *(folded into #1)* | Not a separate call |

**Example shapes (illustrative, not final Pydantic models):**

```jsonc
// GET /ventures/{id} — additive fields only, everything else unchanged
{
  "...existing VentureResponse fields...": "...",
  "current_question": {
    "mission_id": 501,
    "question_text": "Will qualified controllers actually pay for a dedicated solution?",
    "why_it_matters": "Willingness to pay is a different, stronger signal than interest."
  },
  "recommendation": null // present only when no current_question exists
}

// PATCH /ventures/{id}/missions/{mission_id}
// request:
{ "result_text": "Offered the pilot to five controllers. Two accepted at $500/month." }
// response:
{
  "mission": { "...": "unchanged venture_missions shape, learning_summary now set" },
  "candidate_evidence": [
    { "id": "price-positive-0", "label": "$500/mo pricing signal", "sourceQuote": "...", "fieldPath": "economics.price_point", "proposedValue": 500, "polarity": "positive" }
  ]
}

// POST /ventures/{id}/evidence
// request:
{
  "mission_id": 501,
  "statement": "2 of 5 qualified prospects accepted a $500/month paid pilot",
  "evidence_type": "commitment",
  "structured_field_path": "economics.price_point",
  "structured_value": 500,
  "relationship": "supports"
}
// response:
{
  "evidence": { "id": 9001, "...": "full venture_evidence row" },
  "interpretation_summary": "Initial transactional evidence supports willingness to pay among the tested prospects.",
  "interpretation_limitations": "This does not establish repeatable acquisition, broader segment demand, sustained usage, retention, or scalable economics."
}

// POST /ventures/{id}/decisions
// request:
{
  "mission_id": 501,
  "sie_recommendation": "Continue the paid pilots and test whether customers actually use and retain the product.",
  "sie_reasoning": "Willingness-to-pay evidence is early but real; the next open question is retention, not acquisition.",
  "founder_choice": "proceed_with_pilots",
  "evidence_ids": [9001]
}
// response: full venture_decisions row
```

---

## K. Transaction + integrity rules (§17 of the directive)

| Invariant | Enforcement mechanism |
|---|---|
| Evidence cannot attach to another user's venture | Same SQL-level JOIN+WHERE ownership pattern already used by every existing mutation (`update_venture_mission_status_for_owner`'s `FROM modeled_ventures v ... WHERE v.user_id = :user_id`) — reused verbatim for `venture_evidence`/`venture_decisions` inserts, never an app-level "check then trust" pattern |
| Decision cannot attach to another user's test | Same pattern, applied to `related_mission_id` — the INSERT's own `WHERE` clause must join through `venture_missions` → `modeled_ventures` → `user_id`, structurally identical to the existing mission-ownership check |
| Outcome cannot attach to an unrelated decision | `related_decision_id` FK is only ever set server-side, from a `decision_id` the same ownership-scoped lookup already validated in the same request — never accepted as an unchecked client-supplied foreign key across owners |
| Confirmation is idempotent | Reuse `create_venture_mission()`'s existing `source_ref`-based UNIQUE-partial-index dedup pattern: a confirmed-evidence insert derives a deterministic `source_ref`-equivalent from `(mission_id, statement, evidence_type)` and is inserted `ON CONFLICT DO NOTHING` (or an equivalent existing-row-return), not blindly re-inserted |
| Retries do not create duplicate evidence | Same mechanism as above |
| Founder corrections preserve audit history | `superseded_by_id`/`supersedes_decision_id` — never `UPDATE ... SET statement = ...` on an existing row |
| Deleting/editing current venture state does not erase historical evidence | `venture_evidence.venture_id` is `ON DELETE CASCADE` only for the venture itself being deleted (matches existing `venture_missions`/`venture_model_updates` behavior); an ordinary `PUT /ventures/{id}` assumption edit never touches `venture_evidence` rows at all — they are a separate table, not a JSONB blob that could be silently overwritten |
| AI extraction failure does not destroy founder-entered result | `extractCaptureSignals()` runs client-side (§E) — a failure there literally cannot affect the `result_text` already accepted by `PATCH .../missions/{id}` in the prior, separate request; the two are not in the same transaction because they are not even the same request |
| Partial failure cannot create a completed test with lost result/evidence | `PATCH .../missions/{id}` (submit result) and `POST .../evidence` (confirm evidence) are deliberately **separate requests**, each independently atomic — a mission is never marked `completed` as a side effect of submitting a result; completion remains the founder's own explicit action via the existing `update_venture_mission_status_for_owner` path, unchanged. This mirrors the existing, deliberate separation between `record_venture_mission_learning_for_owner` (reflection) and `update_venture_mission_status_for_owner` (completion) — "a founder can reflect without completing, or complete without reflecting," extended to "a founder can record a result without yet confirming evidence." |

**Atomic operations:** each single INSERT (`venture_evidence`, `venture_decisions`) is atomic by virtue of
being one `engine.begin()` block, matching every existing write function's own pattern. No multi-table
distributed transaction is required anywhere in this design — the explicit lesson from Graduation's own
Phase 31A hardening (cited in 34B) was to avoid exactly that risk by keeping each unit of work to one
table's own transaction wherever possible; this design follows the same discipline by keeping Evidence and
Decision as independent single-table writes rather than one large multi-table transaction per founder
action.

---

## L. Frontend contract — minimum Phase 34D slice, not a redesign (§18 of the directive)

**Explicit non-goals restated:** no Idea Lab redesign, no new global navigation, no removal of Model/What-If,
no visual polish pass. The slice below is additive UI inside the *existing* Overview tab (or a temporary,
clearly-labeled internal test surface if even that is judged too invasive for 34D — left as a 34D
implementation decision, not fixed here).

Minimum functional blocks, matching the directive's own list exactly:

1. **CURRENT QUESTION** — plain text, from `GET /ventures/{id}`'s new `current_question.question_text`.
2. **WHY IT MATTERS** — `current_question.why_it_matters`.
3. **RECOMMENDED TEST** — from `recommendation` when no `current_question` exists yet.
4. **START TEST** — calls existing `POST /ventures/{id}/missions` with the new optional fields populated.
5. **RECORD RESULT** — a single textarea, calls the new `PATCH /ventures/{id}/missions/{id}`.
6. **REVIEW EXTRACTED EVIDENCE** — renders `candidate_evidence` from #5's response using the *exact
   existing* `CaptureWhatHappened.tsx` checkbox pattern (§E) — not a new component design, a reuse of the
   existing one against a new response shape.
7. **WHAT WE LEARNED** — `interpretation_summary` + `interpretation_limitations` from `POST
   /ventures/{id}/evidence`'s response.
8. **SIE RECOMMENDS** — `sie_recommendation`/`sie_reasoning`, computed server-side.
9. **YOUR DECISION** — a small closed set of buttons (proceed / revise / pause / dismiss, per 34B §10's
   vocabulary) that calls `POST /ventures/{id}/decisions`.

No new top-level navigation. No removal of anything existing.

---

## M. Migration plan

All additive; no destructive migration anywhere in this design.

1. `ALTER TABLE venture_missions ADD COLUMN ...` (5 nullable columns) + widen `mission_type` CHECK — safe,
   backward-compatible, every existing row is valid post-migration with the new columns simply NULL.
2. `CREATE TABLE venture_evidence (...)` — new table, no interaction with existing data until rows are
   inserted.
3. `CREATE TABLE venture_decisions (...)` — same.
4. Both new tables follow this codebase's own existing migration convention exactly: an idempotent
   `create_*_table()` function guarded by `IF NOT EXISTS`, called once at API startup inside a `try/except`
   (per `CLAUDE.md`'s own documented convention — "new columns are added by writing a new
   `add_*_columns()` function... wrapped in try/except so re-running is safe").
5. No backfill required — every new column/table starts empty; the reload/longitudinal test (§N) only needs
   to hold for ventures created *after* this migration, which is the correct, minimal bar for a V1 slice.

---

## N. Reload / longitudinal acceptance test

Tracing the directive's exact Day 1/5/6/60 scenario against the recommended architecture:

- **Day 1:** `GET /ventures/{id}` returns `recommendation` (no `current_question` yet). Founder starts the
  test → `POST /ventures/{id}/missions` with `question_text`/`why_it_matters` set → **PASS**, row exists in
  `venture_missions`, survives any reload because it's a normal committed Postgres row.
- **Day 5:** `GET /ventures/{id}` now returns `current_question` populated from the same row (queried by
  `status = 'active'`, most recent) → **PASS**. Founder records "2/5 accepted at $500" →
  `PATCH .../missions/{id}` sets `learning_summary`, returns `candidate_evidence` (computed client-side,
  free) → founder confirms → `POST /ventures/{id}/evidence` persists the row, and the response's
  `interpretation_summary`/`interpretation_limitations` are written onto `venture_missions` in the same
  request → **PASS**, all three (result text, evidence row, interpretation) are separately committed rows.
- **Day 6:** Founder returns. `GET /ventures/{id}` reflects the same `interpretation_summary` (unchanged,
  read from the column, not regenerated) and a `recommendation` now computed from the presence of new
  Evidence → **PASS**. Founder decides "proceed with pilots" → `POST /ventures/{id}/decisions` → **PASS**,
  committed row references `mission_id` and `evidence_ids`.
- **Day 60:** Founder returns, records "one renewed, one churned" as a new `POST /ventures/{id}/evidence`
  call with `evidence_type: 'longitudinal_outcome'` and `related_decision_id` set to the Day-6 decision →
  **PASS**. `GET /ventures/{id}` can now compute a *new* `recommendation` ("test whether LedgerFlow can
  deliver enough recurring value...") from the full accumulated Evidence set, while the original question,
  test, result, evidence, interpretation, recommendation, and decision from Days 1-6 all remain queryable,
  unmodified, in their original rows.

**RELOAD SURVIVAL: PASS.** Every fact the directive requires to survive (original question, test, result,
evidence, interpretation, recommendation, founder decision, outcome) is a committed row in Postgres by the
time the browser closes at each step — none of it depends on client-side state, session storage, or
in-memory computation that a reload would lose.

---

## O. ChatGPT-with-forms test (§20 of the directive)

**After six months, what does SIE know that a fresh chatbot prompt does not automatically know?**

A durable, queryable graph: every `venture_evidence` row linked to the `venture_missions` row (question)
that prompted it, in turn linked to the `venture_decisions` row it informed, in turn linked to the later
`venture_evidence` row (outcome) that followed from that decision — with `provenance` and `evidence_type`
preserved on every node, and nothing overwritten in place. A fresh chatbot session has none of this: it has
no memory of what was specifically tested, no typed distinction between a founder's claim and a founder's
transaction, no record of what SIE recommended six weeks ago versus what it would say fresh today, and no
way to notice that a Day-60 churn event specifically confirms a hypothesis raised on Day 20 (34B §19's
ERP-integration example) rather than being a generic new fact.

**This design does not merely store conversation summaries or generated advice** — every object in §D has
real foreign keys to the objects it relates to, and the recommendation engine (§I) reads that graph, not a
transcript. **Passes.**

---

## P. Future compatibility (§21 of the directive) — not built now

- **Venture → Startup graduation:** unaffected; `venture_graduations` untouched. A graduated venture's
  accumulated `venture_evidence`/`venture_decisions` rows remain queryable by `venture_id` after
  graduation, available as future Founder Workspace provenance context (34B §15) without any schema change
  needed to enable that later.
- **Startup Profile / Founder Workspace:** no schema change required now; the FK design (`venture_id` on
  every new table) is already sufficient for a future read-only join from a Founder Workspace view.
- **Investor readiness:** not built; the Decision/Evidence graph is a plausible future input, not touched
  now.
- **Organization/accelerator reporting:** the real FKs and `evidence_type`/`provenance` CHECK constraints
  (rather than a generic JSON payload) mean a future aggregate query ("how many ventures reached
  TRANSACTION-level evidence within 90 days") is a straightforward `SELECT`, not a schema change — this is
  the concrete benefit of choosing Option C over Option B (§C), realized without building the reporting
  feature itself.
- **External evidence:** `evidence_type = 'external_source'` and `provenance = 'external_source'` already
  exist in the CHECK constraints (§D.2) as reserved values — no source is wired up to produce them in V1.
- **Deterministic financial tools (runway, hiring scenarios):** unaffected; lives entirely in
  `directConsequences.ts`-style pure functions per 34B §16, no relationship to this schema.
- **Future longitudinal analysis:** the append-only, FK-linked design is the entire point — nothing further
  needs to be pre-built to enable it later.

**Nothing above is built in this phase.** These are compatibility notes, not commitments.

---

## Q. Explicit non-goals of this document and of Phase 34D

- No multi-hypothesis tracking (only one live question per venture in V1, §G).
- No `segment`/sample-size structured fields on Evidence in V1 (§H) — `statement` free text carries this
  informally until real usage shows it's worth a column.
- No scheduler/reminder system for Outcome check-ins — manual, founder-initiated only.
- No closed CHECK-constrained vocabulary for `founder_choice` yet — free text, tightened later once real
  usage is observed (§D.3).
- No removal of What-If, Model tab, or any existing Idea Lab surface.
- No new score, confidence percentage, or probability anywhere.
- No new AI system — every AI touchpoint reuses `idea_structuring.py`'s existing structured-JSON-output
  pattern, redirected at new content.
- No changes to SPS, Analyze, fundraising math, or VPS internals.

---

## Phase 34D implementation plan (§23 of the directive)

One LedgerFlow vertical slice only. Kept intentionally small.

**FILES LIKELY MODIFIED**
- `app/database/db.py` — add `add_venture_intelligence_columns()` (the `venture_missions` ALTER), add
  `create_venture_evidence_table()`, `create_venture_decisions_table()`, plus the corresponding
  create/list/get functions for each new table, following the exact `*_for_owner` ownership-scoped pattern
  already used throughout this file.
- `app/api.py` — call the three new migration functions at startup (same try/except pattern as every
  existing `add_*_columns()` call); extend `GET /ventures/{id}` response with `current_question`/
  `recommendation`; add the three new endpoints (§J).
- `app/models/idea_lab.py` — add `VentureEvidence`, `VentureDecision` Pydantic response models; extend
  `VentureMissionResponse`/`CreateMissionRequest` with the new optional fields.
- `dashboard/types/ideaLab.ts` — mirror the above (project convention: backend Pydantic changes require a
  matching hand-written TypeScript type update, per `CLAUDE.md`).
- `dashboard/lib/api/ideaLab.ts` — add the three new client functions.
- `dashboard/components/idea-lab/CaptureWhatHappened.tsx` — extend to call the new evidence-confirmation
  endpoint after the existing signal-checkbox flow, reusing its UI unchanged.
- `dashboard/components/idea-lab/MissionsSection.tsx` — extend mission creation to pass through
  `question_text`/`why_it_matters` when starting a recommended test.

**FILES LIKELY CREATED**
- `app/ai/build_recommendation.py` — the deterministic ranking + templated copy composition described in
  §I (extends, does not replace, `vps_guidance.py`'s existing `_next_milestones()` logic).
- `dashboard/components/idea-lab/CurrentQuestionCard.tsx` (or equivalent minimal component; naming is a
  34D decision) — renders §L's nine blocks.
- One new backend test file mirroring existing conventions (e.g. `app/tests/test_build_intelligence_loop.py`)
  covering the ownership/idempotency/append-only invariants in §K.
- One new frontend test file (e.g. `dashboard/tests/buildIntelligenceLoop.test.ts`) covering the
  evidence-mapping logic (`ProposedSignal` → confirmed evidence payload) as a pure function, matching this
  repo's existing plain-node test convention.

**DATABASE MIGRATIONS**
- `ALTER TABLE venture_missions ADD COLUMN ...` (§D.1).
- `CREATE TABLE venture_evidence (...)` (§D.2).
- `CREATE TABLE venture_decisions (...)` (§D.3).

**BACKEND MODELS**
- `VentureEvidence`, `CreateEvidenceRequest`, `VentureDecision`, `CreateDecisionRequest` (Pydantic).
- Extended `VentureMissionResponse`, `CreateMissionRequest`.
- Extended `VentureResponse` (or a small additive response model) carrying `current_question`/
  `recommendation`.

**DATABASE FUNCTIONS**
- `create_venture_evidence`, `list_venture_evidence_for_owner`, `supersede_venture_evidence`.
- `create_venture_decision`, `list_venture_decisions_for_owner`.
- `add_venture_intelligence_columns` (the additive `venture_missions` migration).

**API ENDPOINTS**
- `PATCH /ventures/{id}/missions/{mission_id}` (submit result).
- `POST /ventures/{id}/evidence` (confirm evidence; also used for outcomes).
- `POST /ventures/{id}/decisions` (record decision).
- `GET /ventures/{id}` extended (current_question, recommendation).
- `POST /ventures/{id}/missions` extended (question_text, why_it_matters).

**FRONTEND COMPONENTS**
- One new card component for the current-question/test/evidence/decision slice (§L).
- `CaptureWhatHappened.tsx` extended, not replaced.

**CLIENT FUNCTIONS**
- `submitMissionResult`, `createVentureEvidence`, `createVentureDecision` in `dashboard/lib/api/ideaLab.ts`.

**TESTS**
- Backend: ownership-scoping test per new table (mirroring existing `test_venture_*` conventions),
  idempotent-evidence-confirmation test, append-only/`superseded_by_id` test, decision-reversal test.
- Frontend: pure-function test mapping a `ProposedSignal` to a `CreateEvidenceRequest` payload; no
  component-rendering test framework exists in this repo today and none should be introduced solely for
  this slice (matches this repo's own established testing convention, confirmed across 34A/34B/34C audits).

**Explicit scope boundary:** Phase 34D implements exactly this slice for missions/evidence/decisions on one
question at a time. It does not build multi-hypothesis tracking, a recommendation-quality feedback loop,
scheduled check-ins, external evidence ingestion, or any UI beyond the nine blocks in §L.

---

## IMPLEMENTATION APPENDIX (Phase 34D)

**Status:** Implemented and live-tested (LedgerFlow + a second, unrelated "DocSync" venture). This
appendix records what actually shipped against this document's own predictions above — read it as a diff,
not a restatement.

### What matched the proposal exactly

- Two new tables (`venture_evidence`, `venture_decisions`), additive `venture_missions` columns
  (`question_text`, `why_it_matters`, `interpretation_summary`, `interpretation_limitations`,
  `interpretation_generated_at`), no `Hypothesis`/`Unknown`/`Outcome` table — exactly the "Option C Hybrid"
  this doc recommended.
- Ownership enforced at the SQL join level (`JOIN modeled_ventures v ... WHERE v.user_id = :user_id`) on
  every new list/create function, mirroring `list_venture_missions_for_owner`'s existing pattern — never
  app-level check-then-trust.
- Idempotency via a client-supplied `idempotency_key` column + partial unique index + `ON CONFLICT ...
  DO NOTHING` + fallback select, on both new tables — mirrors `create_venture_mission`'s existing
  `source_ref` dedup.
- Append-only correction: `superseded_by_id` (evidence) / `supersedes_decision_id` (decisions), both
  self-referencing FKs; a correction is a new row, the old row's content is never edited in place.
- `captureSignals.ts` reused completely unchanged as the sole extraction engine; a second extraction system
  was never built.
- `app/ai/build_recommendation.py` is zero-LLM, template/rule-driven, matching `vps_guidance.py`'s existing
  discipline — confirmed by `test_evidence_and_decision_never_change_vps_or_assumptions` and by the fact the
  module has no OpenAI/Tavily import at all.
- Canonical provenance vocabulary implemented as a lowercase-snake-case CHECK constraint
  (`founder_said`/`founder_observed`/`sie_inferred`/`sie_calculated`/`external_source`/`still_unknown`);
  every signal the founder confirms through the UI is written as `founder_observed`, never a stronger claim.

### Where the implementation deviated, and why

- **No `PATCH /ventures/{id}/missions/{mission_id}` endpoint was added.** The pre-existing
  `POST /ventures/{venture_id}/missions/{mission_id}/learning` endpoint
  (`record_venture_mission_learning_for_owner`) already does exactly the "submit a result" job. Reusing it
  instead of adding a parallel endpoint is a direct application of this doc's own "adapt before inventing"
  governing rule.
- **Outcome ("what happened afterward?") is not a separate concept in the API** — it is a normal
  `POST /ventures/{id}/evidence` call with `evidence_type="longitudinal_outcome"` and
  `related_decision_id` set instead of `related_mission_id`. The founder-facing UI (`OutcomeState` in
  `CurrentQuestionCard.tsx`) makes this feel like a distinct moment; the backend does not need to know it is
  one.
- **"SIE's recommendation before a decision" and "the next question once nothing is active" turned out to
  be the same computation.** `build_intelligence_state(venture_name, model_result, active_mission,
  evidence_rows)` returns `{current_question, recommendation}` with exactly one populated at a time — there
  is one recommendation engine, not two, which this doc left open as a question and 34D resolved by
  building it once.
- **`GET /ventures/{venture_id}/recommendation`** was added as a small dedicated read endpoint (not
  predicted above) rather than folding `current_question`/`recommendation` onto the main venture response,
  because `CurrentQuestionCard.tsx` needed to refresh this slice independently of the rest of the Overview
  tab's data without over-fetching.
- **Evidence/decision writes stay in `app/api.py`, not a new router file** — consistent with this codebase's
  existing convention of one flat `api.py` rather than per-feature routers.

### Files actually touched (see the Phase 34D final report for the complete list)

Backend: `app/models/venture_missions.py`, `app/database/db.py`, `app/api.py`,
`app/ai/build_recommendation.py` (new), `app/tests/test_build_intelligence_loop.py` (new).
Frontend: `dashboard/types/ideaLab.ts`, `dashboard/lib/api/index.ts`,
`dashboard/lib/api/buildIntelligence.ts` (new), `dashboard/lib/build/evidenceMapping.ts` (new),
`dashboard/components/idea-lab/CurrentQuestionCard.tsx` (new),
`dashboard/app/idea-lab/[id]/VentureWorkspace.tsx`, `dashboard/tests/buildIntelligenceLoop.test.ts` (new).

### Verified live (not just unit-tested)

Two full loops were run against the live dev server and Postgres, not just the automated suite: LedgerFlow
(`Will qualified controllers actually pay for a dedicated solution?` → confirmed transaction + interview
evidence → interpretation/limitations → recommendation shifted to
`Will customers actually use and retain LedgerFlow?` → founder decision recorded → mixed outcome
(`one renewed, one churned`, relationship tagged `Mixed -- some of both`) → next recommendation correctly
became a retention-driver question, not a reversion to generic discovery), and a second, vocabulary-disjoint
venture ("DocSync," a developer-tool API-docs product) proving the same mechanics produce sensible guidance
with zero shared business vocabulary, including a founder decision that explicitly disagreed with SIE's
recommendation (with rationale), both preserved separately in `venture_decisions`. All of this was
re-verified after a full page reload at each step (server-derived state, no client-only memory).
