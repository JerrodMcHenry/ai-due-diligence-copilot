# SIE Committed Plan → Actual → Learning Architecture V1

Phase 38D was a pure design phase — §§1-31 below reflect that original, nothing-implemented state and are
left unmodified. **Phase 38D-A (§32) has since implemented commitment persistence + frozen expectation, and
Phase 38D-B (§33) has implemented deterministic expected-vs-actual comparison.** Founder explanation, learning,
and Command Center integration remain unimplemented, per 38D-B's own explicit scope guards (§33).

The original §§1-31 audited answer to one question: what is the smallest durable schema that lets SIE
truthfully compare "what a founder expected" against "what actually happened," months later, without
reconstructing history from today's state?

## 1. Product purpose

Phase 38C shipped a real Plan × Actual comparison (`findRevenueTargetDivergence`), but it compares an
actual snapshot against the **live, currently-mutable** `venture_financial_plans` row — not against what
the founder expected at the moment they committed to a plan. If that row is edited after the fact (Phase
35C's own hire-plan comment confirms plan rows are deliberately update-in-place, "an actively-edited
draft"), the comparison silently starts using the new value with no memory of the original one. This is not
a bug in 38C — 38C was correctly scoped to what already existed — but it is a real limitation this phase
exists to name and close.

The fix is not a bigger comparison engine. It is remembering one new kind of fact: **the founder explicitly
said "this is what I'm doing," and here is exactly what SIE expected at that moment.** Everything else
(scenarios, live plans, actual snapshots) already exists and stays exactly as it is.

## 2. Repository audit

### Finance

- **`venture_financial_snapshots`** (`app/database/db.py::create_venture_financial_snapshots_table`) —
  append-only, confirmed directly from `create_venture_financial_snapshot`'s own docstring: "Always an
  INSERT -- there is no update path for this table." Ordered `(as_of_date DESC, recorded_at DESC)`; "latest"
  is always a live ORDER BY, never a separate current-state row. This is already a correct, sufficient
  actual-state ledger — confirmed in §8, no new actuals table needed.
- **`venture_hire_plans`** (Phase 35C) — deliberately **mutable, update-in-place**. The table's own creation
  comment is explicit: "UPDATE-IN-PLACE, deliberately... a planned hire is an ACTIVELY-EDITED DRAFT the
  founder is still shaping... not an immutable observation already made." `status` lifecycle:
  `planned → cancelled/actualized`. Has `last_reconciled_snapshot_id` (added Phase 35D, nullable FK to a
  snapshot) tracking which snapshot a reconciliation question was already answered against.
- **`venture_financial_plans`** (Phase 35D; `revenue_target` / `expense_change`) — same mutability
  discipline, same status lifecycle, same `last_reconciled_snapshot_id`. `amount_cents` means an ABSOLUTE
  monthly figure for `revenue_target`, a SIGNED recurring delta for `expense_change`
  (`CreateFinancialPlanRequest`'s own docstring) — the asymmetry Phase 38C already exploited by scoping its
  own divergence check to `revenue_target` only.
- **`venture_financial_scenarios`** — confirmed, directly from its own table-creation comment, to be "a
  NAMED SELECTION of plan ids, never a frozen copy of actual state... a scenario's numeric result is always
  recomputed live, at read time, against whatever the LATEST actual snapshot and the SELECTED plans' CURRENT
  values currently say." Deletable with "no history obligation." This is the single most important audit
  finding: **scenarios are architecturally incapable of ever becoming historical truth, by design** — which
  is correct and must not change. It is also exactly why 38C's own divergence check (which reads a live
  plan row, not a scenario) inherits the same live-recompute problem one level down.
- **`financial_engine.py`** — `compute_derived_metrics()` (actual-state derivation from a snapshot; five
  `status` values; no versioning concept at all) and `project_monthly_cash_flow()` (the scenario projection
  engine; `DEFAULT_PROJECTION_HORIZON_MONTHS = 24`). **No calculation-version concept exists anywhere in this
  file** — confirmed by grepping for `version` — a real, previously-unaddressed gap this phase must name
  (§7).
- **`ScenarioProjectedMonth`** (`app/models/venture_financial_plans.py`) — the exact monthly shape a
  scenario projection already produces: `month_index, date, starting_cash_cents, revenue_cents,
  expenses_cents, plan_expense_impact_cents, plan_revenue_active, active_plan_item_ids,
  net_cash_change_cents, ending_cash_cents, depleted`. This shape already exists, is already stable, and is
  already what founders read on screen today — the natural Expected State shape (§25), not a new invention.
- **Reconciliation** (`list_pending_reconciliation_for_owner`, `POST /ventures/{id}/financials/reconcile`,
  Phase 35D) — confirmed to be purely date/status-based: "has this plan's start_date passed and not yet
  reconciled against the latest snapshot." Answering "included" sets `status='actualized'` +
  `last_reconciled_snapshot_id`; it computes **zero** numeric planned-vs-actual divergence. Cannot be reused
  for comparison — it is a nudge-to-update-status mechanism, not a comparison engine.

### Decisions

- **`venture_decisions`** (Phase 34D) — already separates `sie_recommendation`/`sie_reasoning` from
  `founder_choice`/`founder_rationale`, exactly the founder-authority discipline §14 requires. Already has
  `supersedes_decision_id` (self-FK, append-only reversal: "a NEW row, never an edit to the old one") and
  `related_mission_id` (Build only — **confirmed, again, no FK to any Finance entity exists**, matching
  Phase 38C's own finding). `evidence_ids` is a plain Postgres array, the same array-of-ids pattern
  `venture_financial_scenarios.hire_plan_ids` independently reuses.

### Build

- **`venture_evidence`** — `evidence_type` is CHECK-constrained to a **specific, already-meaningful
  vocabulary**: `founder_claim, reported_preference, observed_behavior, commitment, transaction,
  longitudinal_outcome, external_source`. Reading `SIE_BUILD_METHODOLOGY_V1.md` §4 directly: `COMMITMENT`
  means "a real but non-monetary or conditional commitment" **from a prospect/customer** ("two signed
  LOIs"); `TRANSACTION` means a customer has actually paid; `LONGITUDINAL OUTCOME` means one of those
  observed again later. **These words already mean something specific and different from a founder's own
  operating-plan commitment.** Reusing this table/vocabulary for Finance would silently overload
  `evidence_type='commitment'` — corrupting the evidence-strength reasoning that specifically depends on
  `commitment`/`transaction` meaning customer behavior ("a single Transaction outweighs ten Reported
  Preferences," §4). **Rejected reuse — see §12.**
- The "Outcome = a `venture_evidence` row with `evidence_type='longitudinal_outcome'` and
  `related_decision_id` set, no separate table" pattern (confirmed in that table's own creation comment) is
  a useful **precedent for architecture style** (reuse a typed row over inventing a table) but not a
  reusable **table**, for the reason above.
- **`venture_missions.learning_summary`** — confirmed (via Phase 35C's own hire-plan comment, which cites it
  directly) to be an **update-in-place reflection field living on an otherwise mostly-immutable row**. This
  is the precedent this phase reuses for `founder_explanation` (§12) — the pattern already exists in this
  codebase, just not yet in Finance.

### Command Center (38B/38C)

- `isFinancialConstraintActive` (38B) and `findRevenueTargetDivergence`/`findStaleFinanceContext` (38C) are
  all pure, deterministic, client-side functions over already-fetched data — no new fetch, no AI. This
  phase's own comparison function (§8/§20) is designed to follow the identical style: pure, deterministic,
  computed at read time from data already on hand.
- 38C's own module comments in `commandCenterCrossSystem.ts` already document the Plan Baseline Problem for
  `expense_change` plans in detail — this phase's `plan_snapshot` + `expected_monthly` freeze (§6) is the
  direct resolution to that problem (see Case K, §27).

### Fundraising

- `app/models/fundraising_readiness.py` has **no scenario or commitment persistence concept at all** — it
  is a computed-only readiness score/checklist (`PillarReadinessOut`, `ReadinessGapOut`, `ChecklistItemOut`).
  Confirms Fundraising is genuinely ephemeral today; there is nothing existing to protect from corruption,
  and nothing to migrate. Addressed as a forward-compatibility question only, §19 — **not implemented.**

No existing "commit to a plan" UX/copy was found anywhere in `dashboard/components/idea-lab/` — this is
genuinely greenfield product surface, not a rename of something already shipped.

## 3. Scenario vs. Commitment doctrine (non-negotiable, confirmed against the audit)

**Scenario** (exists, unchanged): a hypothetical, freely-editable, freely-deletable named selection of plan
ids. Its numeric result is always recomputed live. It must never become historical truth merely by being
modeled — confirmed as already true by `venture_financial_scenarios`' own design, not something this phase
needs to enforce.

**Committed Plan** (new): an explicit founder action — never automatic — that freezes SIE's expectation at
a specific moment. A commitment does not replace or freeze the underlying scenario/plan rows (those stay
exactly as mutable as they are today); it freezes a **copy** of what they implied, at that moment, alongside
the computed consequence of that copy.

## 4. Object definitions

| Object | Means | Does NOT mean | Exists today? | Needs persistence? | Needs FK identity? | Derivable? |
|---|---|---|---|---|---|---|
| Scenario | hypothetical named plan-id selection | committed truth | Yes (`venture_financial_scenarios`) | Already persisted | Already has it | Its numeric result, yes (unchanged) |
| Committed Plan | explicit founder decision to proceed, with a frozen expectation | a scenario; a live plan row | No | **Yes — the one new object** | Yes | No — this is the thing that must NOT be derivable later |
| Decision | SIE recommendation vs. founder choice, kept separate | the committed plan itself | Yes (`venture_decisions`) | Already persisted | Gets one new optional inbound FK from Committed Plan | No |
| Expected State | the frozen monthly projection at commit time | a live/recomputed projection | Its *shape* exists (`ScenarioProjectedMonth`); its *frozen instance* does not | Yes, embedded in the Committed Plan row | No — it's a value, not an entity | No (that's the point) |
| Actual State | real financial reality over time | an estimate/interpolation | Yes (`venture_financial_snapshots`) | Already persisted, unchanged | No new FK — aligned by calendar month at read time (§10) | N/A (source of truth) |
| Variance | plain arithmetic difference, expected vs. actual | an explanation; a cause | No, and should not | **No — always derived, never stored** | N/A | Yes, always |
| Interpretation | (Build's own term) SIE's hypothesis-strength narrative | a Finance concept | Yes, but scoped to Build only | N/A to Finance | N/A | N/A — **not built for Finance, deliberately** |
| Outcome | (Build's own term) a Transaction/Commitment observed again later | a Finance concept | Yes, but scoped to Build only (`evidence_type='longitudinal_outcome'`) | N/A to Finance | N/A | For Finance, "outcome" is just Variance once an aligned actual exists — no new object |
| Learning | the founder's own explanation of a variance | SIE's inference about the variance | No | Yes — one small mutable field | No | No — must be captured, not guessed |

**Objects required (new): exactly one entity (Committed Plan) plus one field-pair on it (`founder_explanation`
/ `explanation_recorded_at`).** Not eight. Interpretation and Outcome are deliberately *not* built for
Finance — building them would mean inventing an AI-narrative object 38C's own directive already forbade
("no AI synthesis," "no causal claims") and would collide with Build's own, already-meaningful use of those
words.

## 5. What must be frozen (A/B/C/D)

| Candidate field | Classification | Reasoning |
|---|---|---|
| Commitment timestamp | **A** — necessary | The anchor for everything else |
| Underlying financial snapshot id | **A** — necessary | "What reality looked like" when the projection was computed |
| Included plan ids | **A** — necessary | Traceability: which specific rows were committed |
| Plan **values** at commitment (salary, amount, category, dates) | **A** — necessary, NOT derivable later | See §6: plan rows are confirmed mutable; a reference alone is unsafe |
| Projected monthly revenue/expenses/burn/cash | **A** — necessary | This *is* the expectation |
| Expected depletion month | **B** — safely derivable | Already implicit in `expected_monthly[].ending_cash_cents`/`depleted`; no separate field |
| Expected category-level expenses | **D** — unnecessary for V1 | The existing engine's own projection has no per-category output at all (`ScenarioProjectedMonth` has none) — building this would mean inventing new projection granularity, not freezing an existing one |
| Expected hire costs | **A**, but covered | Already inside the frozen plan-value snapshot and the aggregate `expected_monthly.expenses_cents` |
| Scenario name | **A**, small, denormalized | A scenario can be deleted with "no history obligation" (existing, correct); its name must be copied, not just referenced, or a later-deleted scenario silently loses its label |
| Projection horizon | **A** — necessary | Needed to know how far the frozen array extends |

Direct answers:
- **Hire plan edited after commitment?** Reconstruction still possible — the commitment's own frozen copy
  of that plan's values was never a live reference.
- **Expense plan edited after commitment?** Same answer, same mechanism.
- **Underlying snapshot later changes (a newer one arrives)?** Irrelevant to the frozen expectation; only
  the *actual* side of a future comparison ever reads newer snapshots.
- **Projection logic changes in a future release?** Irrelevant — the expectation was computed once, at
  commit time, and is never recomputed. `calculation_version` records which era's math produced it (§7), it
  does not protect against a recompute that this design never performs.

## 6. Model versioning problem

Confirmed: both `venture_hire_plans` and `venture_financial_plans` are **deliberately mutable**, by explicit
design decision documented in their own table-creation comments (35C: "an actively-edited draft"). A
commitment that referenced these rows by id alone, without freezing their values, would silently drift.

- **Option A — freeze plan inputs at commitment.** Cheap (a handful of scalars per included plan, bounded
  array). Solves Case C/E completely. Requires zero change to the existing, already-tested mutable-plan
  behavior.
- **Option B — make committed plans immutable/versioned** (add versioning columns to the existing plan
  tables). Rejected: contradicts Phase 35C's own explicit design rationale for those tables, and doesn't
  cleanly answer "committed to what" when multiple plans/hires are committed together as one expectation.
- **Option C — freeze only calculated expected outputs**, not raw inputs. Answers "what did I expect
  financially" but not "why" — a founder six months later seeing "$68K expected burn" with zero visibility
  into which hire/what salary produced it is a materially worse, less trustworthy product.
- **Option D — hybrid: freeze both plan-input values and calculated outputs, in the same row.**
  **Recommended.** This is exactly what the proposed `plan_snapshot` + `expected_monthly` pair already does
  — not a fourth idea, but the natural shape of Option A once "freeze plan inputs" is read literally
  alongside "and also freeze what they computed to."

## 7. Calculation versioning

No versioning concept exists in `financial_engine.py` today. Recommended: preserve the **calculated
expectation outputs always** (never recomputed, so they cannot silently mutate regardless of engine
changes) plus a single hand-bumped **`calculation_version`** string constant (e.g.
`PROJECTION_CALCULATION_VERSION = "v1"`, defined beside `DEFAULT_PROJECTION_HORIZON_MONTHS`), incremented
only when the projection *math* itself changes. Not a migration framework, not automatic inference, not a
trigger for recomputing anything historical — its only job is letting a future reader know which era's math
produced a given frozen number, in case that ever matters for an honest disclosure.

## 8. Actual state

Confirmed sufficient as-is: `venture_financial_snapshots`, append-only, already fully queryable via
`list_venture_financial_snapshots_for_owner`. **No new actuals table.**

Association to a commitment: **comparison on demand**, not an explicit FK, not fuzzy matching, not a
founder-selected actual. Given a commitment's `expected_monthly[]` (each entry carries a calendar `date`),
a pure read-time function finds, for a given expected month, the actual snapshot whose `as_of_date` falls in
that same calendar month (§10) and computes `compute_derived_metrics()` on it. No linkage is ever persisted
between a commitment and a snapshot — this mirrors the exact style Phase 38C's own
`findRevenueTargetDivergence`/`findStaleFinanceContext` already use (pure functions over already-fetched
data), and naturally supports comparing against many later snapshots over time without new rows.

## 9. Comparison semantics — what today's data actually supports

| Comparison | Supported? | Why |
|---|---|---|
| Expected monthly revenue vs. actual | **Yes** | `expected_monthly[i].revenue_cents` vs. `compute_derived_metrics(aligned_snapshot).total_monthly_revenue_cents` |
| Expected total expenses vs. actual | **Yes** | `expected_monthly[i].expenses_cents` vs. `.total_monthly_expenses_cents` |
| Expected burn vs. actual burn | **Yes**, with a sign note | `net_cash_change_cents` (expected, positive=growing) vs. `net_burn_cents` (actual, positive=burning) — a sign flip, not a data gap |
| Expected cash balance at month N vs. actual | **Yes** | `expected_monthly[i].ending_cash_cents` vs. aligned snapshot's `cash_balance_cents` |
| Expected payroll vs. actual payroll | **Partial, later phase** | No per-category field in `expected_monthly` (§5: D); would compare the frozen `plan_snapshot` hire-cost value directly against the actual `payroll_cents` field — possible, not core V1 |
| Expected hire start vs. actualized hire date | **Partial, not proposed** | `venture_hire_plans.status` reaches `'actualized'` via reconciliation, but there is no separate "actual start date" field distinct from the original `start_date` — adding one would be new clutter (§5: D) the existing binary already substantially answers |

Nothing here claims a comparison the data cannot honestly support.

## 10. Time alignment

**Rule: calendar-month match on the snapshot's own `as_of_date`, latest snapshot wins.** For an expected
month whose `date` falls in calendar month M, the matching actual is the most recent recorded snapshot whose
`as_of_date` also falls in month M — the identical "latest wins" doctrine `get_latest_venture_financial_snapshot_for_owner`
already uses everywhere else in Finance. If no snapshot exists in month M, **no comparison is offered for
that month** — silence, never interpolation, never an estimate. Month-end-only and founder-selected-period
alignment were considered and rejected as unnecessary V1 UX complexity on top of an already-explainable
rule.

## 11. Variance is not learning

Enforced structurally, not by convention alone: `expected_monthly`/`plan_snapshot` (arithmetic inputs,
frozen, never touched again) and `founder_explanation` (free text, always founder-authored) are two
different fields with two different write paths, and the **variance itself is never persisted at all** —
it is always a read-time arithmetic diff, exactly mirroring 38C's own "plain inequality, no invented
materiality threshold" discipline. No third field for "SIE interpretation" is created, because no such
object is built (§4/§12) — there is nothing for SIE to write an inference into, by construction.

## 12. Learning capture

**Not** `venture_evidence`. Its `evidence_type` vocabulary (`commitment`, `transaction`,
`longitudinal_outcome`) already carries a specific, load-bearing meaning inside the Build hypothesis loop
(customer/market behavior, per `SIE_BUILD_METHODOLOGY_V1.md` §4) — reusing it for a founder's own financial
commitment would silently overload a term whose specificity the evidence-strength reasoning depends on.

Instead: a single mutable **`founder_explanation TEXT` / `explanation_recorded_at TIMESTAMP`** pair, living
directly on the Committed Plan row, updated in place. This is not a new pattern — it is the same
update-in-place reflection field `venture_missions.learning_summary` already established (cited directly by
Phase 35C's own hire-plan comment as its own precedent). One row, one clearly-scoped mutable field,
everything else on that row frozen.

## 13. Decision × Finance bridge

Phase 38C confirmed no structural FK exists from `venture_decisions` to any Finance entity. The Committed
Plan closes this gap with **one new nullable column on the new table** — `related_decision_id INTEGER
REFERENCES venture_decisions(id) ON DELETE SET NULL` — the identical shape `venture_evidence.related_decision_id`
already uses. Set only when a founder commits a plan as part of an explicit Decision (SIE recommended
something, the founder chose something, and that choice became this commitment). It is never inferred,
never required, and — because the FK lives on the Finance side, not on `venture_decisions` itself — an
ordinary Build-only decision (Case S) requires zero schema awareness of Finance at all. No text matching
anywhere.

## 14. Founder authority model

Five facts, five homes, never rewritten into each other:

| Fact | Lives in | Mutable? |
|---|---|---|
| SIE recommendation/reasoning | `venture_decisions.sie_recommendation`/`sie_reasoning` | No (unchanged) |
| Founder's actual choice | `venture_decisions.founder_choice` | No (unchanged) |
| What was committed + expected | Committed Plan's `plan_snapshot`/`expected_monthly` | No (frozen at write) |
| What actually happened | `venture_financial_snapshots` | No (append-only, unchanged) |
| Why the variance happened | Committed Plan's `founder_explanation` | Yes — the one exception |

The schema makes "the founder followed SIE's recommendation" **unrepresentable** as a stored fact — it can
only ever be reconstructed by a reader comparing two independent text fields side by side, which is exactly
what a display layer should do, never what a write path should assume.

## 15. Plan edits after commitment

**Answer: A — the original commitment remains historical; a new commitment supersedes it.** Directly
mirrors `venture_decisions.supersedes_decision_id`'s own shipped, tested, append-only pattern:
`supersedes_commitment_id INTEGER REFERENCES venture_financial_commitments(id) ON DELETE SET NULL`. Editing
the underlying `venture_hire_plans`/`venture_financial_plans` row never automatically creates or supersedes
a commitment — per §4's "no automatic commitment," the founder must take an explicit new commit action.

## 16. Abandoned / reversed commitments

Minimum lifecycle: `status CHECK IN ('active', 'superseded', 'abandoned')`. `active` = the current standing
commitment (of however many independent commitments exist, §17); `superseded` = set automatically, exactly
once, when a new commitment names it via `supersedes_commitment_id`; `abandoned` = the founder directly says
"not doing this" with no replacement. No row is ever deleted in any of these transitions.

## 17. Multiple commitments

**Independent commitment events, not one giant operating-plan object.** A single "current operating plan"
row would force an all-or-nothing commit that doesn't match how founders actually decide things — a hire in
October, a marketing spend decided separately in November, on unrelated timelines. Independent rows, each
with its own `committed_at`/status/supersede chain, directly satisfy Case N ("no giant mutable blob") while
still allowing one commitment to bundle several plan ids together when the founder genuinely commits to a
whole scenario at once (§18).

## 18. Scenario commitment scope

**Both A (whole scenario) and B (single item) are supported by the same shape, with no extra mode.**
`hire_plan_ids`/`financial_plan_ids` arrays on the commitment row (mirroring `venture_financial_scenarios`'
own array precedent exactly) hold whichever ids the founder actually commits — the full set from a chosen
scenario, or just one. `scenario_id`/`scenario_name` are populated only for traceability when a scenario was
the source; nothing requires it.

## 19. Fundraising boundary

**Yes, compatible — as a sibling, not a shared table.** A future `venture_fundraising_commitments` table
could reuse the identical *doctrine* (explicit founder action, frozen expectation, append-only supersede
chain, optional `related_decision_id`) without reusing the *schema*. Fundraising's own "expected state"
isn't a monthly cash-flow projection at all — it's terms/dilution/round composition, a structurally
different shape than `expected_monthly`. Forcing it into this table's JSONB shape would be exactly the
"Fundraising requirements distort the Finance design" trap named in the directive's own stop conditions.
**Nothing about Fundraising is persisted in this phase.**

## 20. Command Center future behavior (design only)

| Founder-facing sentence | Exact persisted facts |
|---|---|
| "You planned monthly burn of $50K after the October hire. Latest actual burn is $68K." | `commitment.plan_snapshot[hire].start_date` (October) + `expected_monthly[i].net_cash_change_cents` (sign-flipped, $50K) vs. `compute_derived_metrics(aligned_snapshot).net_burn_cents` ($68K) |
| "You chose to proceed with the hire despite SIE's recommendation to wait." | `commitment.related_decision_id → venture_decisions.sie_recommendation` ("wait") vs. `.founder_choice` ("proceed") — read directly, never inferred |
| "Your original revenue target was $30K MRR. Latest actual is $22K." | `commitment.expected_monthly[i].revenue_cents` ($30K, frozen) vs. `compute_derived_metrics(aligned_snapshot).total_monthly_revenue_cents` ($22K) — the same sentence Phase 38C already renders today, upgraded from a live plan value to a frozen commitment value |

Every sentence traces to a named, already-defined field. No new computation is invented for display.

## 21. Generic AI test

| Field | AI would recall reliably? | Materially improves a future decision? | Persist? |
|---|---|---|---|
| `committed_at`, `source_snapshot_id`, `plan_snapshot`, `expected_monthly`, `calculation_version`, `scenario_name`, `related_decision_id`, `supersedes_commitment_id`, `status` | No — exact historical numbers/ids only this database has | Yes — every sentence in §20 depends on them | **Yes** |
| `founder_explanation` | No — the founder's own words, said once | Yes — this is what closes the trust loop in §11/§14 | **Yes** |
| Category-level expected expenses, actualized-vs-planned hire date, fundraising terms | (moot) | Fails "materially improves at V1 scope," or requires net-new computation | **No** — see §5/§9/§19 |

## 22. FP&A boundary

SIE is **not** becoming: a double-entry ledger, a chart of accounts, departmental budgeting, multi-entity
consolidation, payroll, invoicing/AR/AP, or automated bookkeeping reconciliation beyond the existing binary
"is this now included" nudge. The entire new surface is **one append-only table** recording "the founder
committed to this financial expectation on this date," plus one read-time comparison function. A future
proposal for category-level budgets, multi-scenario blending, or automated variance categorization is FP&A
territory and should be rejected under this same doctrine.

## 23. Architecture options

**Option A — new `venture_financial_commitments` table**, freezing both plan-input values and computed
outputs in one row, with optional FKs to a scenario and a decision.
- Schema complexity: low-medium (one new table, reuses every existing FK target).
- Historical integrity: high (immutable by convention; only `founder_explanation`/`status` ever change).
- Query complexity: low (one row already contains identity + expectation; comparison reads it plus a
  snapshot query).
- Founder UX: one clear action ("Commit to this plan").
- Compatibility with current Finance: high — zero changes to `venture_hire_plans`/`venture_financial_plans`/
  `venture_financial_scenarios`.
- Compatibility with Build decisions: clean, optional, one-directional FK (Case S safe).
- Fundraising compatibility: sibling-table pattern, doctrine shared, schema not (§19).
- Migration risk: low — pure addition, starts empty, old ventures correctly show nothing.
- FP&A drift risk: low.

**Option B — version the existing plan entities** (add versioning/freeze columns directly to
`venture_hire_plans`/`venture_financial_plans`).
- Schema complexity: medium-high — touches two existing, already-tested, real-data tables.
- Historical integrity: medium — solves a single plan's own history but not the founder's actual mental
  model at commitment time, which is "the whole picture" (hire + expense + revenue target together).
- Query complexity: high — reconstructing "what I expected" means re-deriving a projection from a bag of
  frozen individual-row-versions instead of reading one pre-computed row.
- Founder UX: ambiguous — unclear what a single "commit" action would even apply to.
- Compatibility with current Finance: **directly contradicts** Phase 35C's own documented rationale for
  keeping these tables update-in-place ("not refactoring working hire persistence merely for theoretical
  purity" — the same argument applies here).
- Migration risk: higher — touches hot, already-tested tables.
- FP&A drift risk: higher — this is the direction that starts to resemble real version-control/ledger
  software.
- **Rejected.**

**Option C — generic decision-event / event-sourcing table** (one `venture_events` table, JSON payload,
`event_type` discriminator, meant to eventually cover Finance, Fundraising, and anything else).
- Schema complexity: low on paper, high in practice — no typed columns, no referential integrity on the
  interesting fields, every consumer must independently know every `event_type`'s shape.
- Query complexity: high — JSON-path queries in place of normal SQL predicates.
- Compatibility: superficially unifies everything, which is precisely the trap.
- **Rejected — matches the directive's own explicit stop condition: "generic JSON event sourcing becomes
  the answer to everything."**

**Recommended: Option A.**

## 24. Minimum schema (proposed, not created)

```
venture_financial_commitments
  id                          SERIAL PRIMARY KEY
  venture_id                  INTEGER NOT NULL REFERENCES modeled_ventures(id) ON DELETE CASCADE
  user_id                     TEXT NOT NULL REFERENCES users(id)
  committed_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  source_snapshot_id          INTEGER REFERENCES venture_financial_snapshots(id) ON DELETE SET NULL
  scenario_id                 INTEGER REFERENCES venture_financial_scenarios(id) ON DELETE SET NULL
  scenario_name               TEXT                -- denormalized freeze; survives scenario deletion
  hire_plan_ids                INTEGER[] NOT NULL DEFAULT '{}'
  financial_plan_ids          INTEGER[] NOT NULL DEFAULT '{}'
  plan_snapshot                JSONB NOT NULL DEFAULT '[]'   -- frozen plan-input values, §6/§24 below
  calculation_version          TEXT NOT NULL
  projection_start             DATE NOT NULL
  projection_horizon_months    INTEGER NOT NULL
  expected_monthly              JSONB NOT NULL      -- frozen ScenarioProjectedMonth[], §25
  related_decision_id           INTEGER REFERENCES venture_decisions(id) ON DELETE SET NULL
  status                        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','abandoned'))
  supersedes_commitment_id      INTEGER REFERENCES venture_financial_commitments(id) ON DELETE SET NULL
  founder_rationale             TEXT                -- captured AT commit time ("why I'm doing this")
  founder_explanation           TEXT                -- captured LATER, update-in-place ("why the variance happened")
  explanation_recorded_at       TIMESTAMP
  idempotency_key                TEXT                -- same dedup precedent as venture_decisions/venture_evidence
```

Indexes: `(venture_id, committed_at DESC)`; unique `idempotency_key WHERE idempotency_key IS NOT NULL`
(identical pattern to `venture_decisions`/`venture_evidence`).

**Exactly one new table.** `plan_snapshot`/`expected_monthly` are the one deliberate JSONB exception to
"prefer normalized references" — justified because both are written exactly once, never queried by a SQL
predicate (every anticipated read is "give me the whole frozen array for commitment #N, then compare in
application code," exactly like Command Center's own client-side comparison style), and normalizing them
into a child table would be the "five tables for one workflow" anti-pattern this phase's own stop conditions
warn against.

## 25. Expected-state shape

Reuse `ScenarioProjectedMonth` **verbatim** as the shape of each `expected_monthly` array entry: `month_index,
date, starting_cash_cents, revenue_cents, expenses_cents, plan_expense_impact_cents, plan_revenue_active,
active_plan_item_ids, net_cash_change_cents, ending_cash_cents, depleted`. No new shape is invented — this
is already exactly what founders read on screen in a live scenario preview today, so it is already known to
be sufficient for the comparisons founders actually use (§9).

`plan_snapshot` entries are smaller and simpler: `{id, kind: "hire"|"financial", label, start_date,
category?, amount_cents? | annual_salary_cents? + burden_percent?}` — just enough of each included row's own
input values to answer "what exactly was I committing to," never re-deriving anything the engine already
computes into `expected_monthly`.

## 26. Provenance

| Fact | Provenance | Where |
|---|---|---|
| Founder-entered plan inputs (live) | founder-entered | `venture_hire_plans`/`venture_financial_plans` (unchanged) |
| Founder-entered plan inputs (frozen copy) | founder-entered, frozen | `plan_snapshot` |
| SIE-calculated expected outputs | sie_calculated | `expected_monthly`, tagged `calculation_version` |
| Actual financial snapshot | founder-entered | `venture_financial_snapshots` (unchanged) |
| Calculated variance | sie_calculated | **never persisted** — always a read-time value |
| Founder explanation | founder-said | `founder_explanation` |
| SIE interpretation | — | **not built** — no object exists to attribute provenance to |

## 27. Test matrix

| Case | Result |
|---|---|
| A. Model three scenarios, commit none | **PASS** — scenarios stay purely in `venture_financial_scenarios`; no commitment row is ever created; no durable expectation history |
| B. Commit one hire plan | **PASS** — a commitment row freezes `plan_snapshot`/`expected_monthly`; recoverable unchanged six months later |
| C. Edit the underlying hire afterward | **PASS** — the live plan row changes (as designed); the frozen copy on the commitment does not, because it was never a live reference |
| D. Change mind, recommit | **PASS** — new row with `supersedes_commitment_id`; old row flips to `status='superseded'`; both permanently queryable |
| E. Financial engine changes later | **PASS** — historical `expected_monthly` is never recomputed; new commitments simply get a new `calculation_version` |
| F. New actual snapshot arrives | **PASS** — comparison reads the unchanged commitment + the new snapshot; no old inputs are reconstructed |
| G. Actual matches expectation | **PASS** — plain-inequality variance check yields zero difference; no fake problem manufactured (mirrors 38C's own discipline) |
| H. Actual differs | **PASS** — a plain arithmetic variance is visible; no causal explanation is invented anywhere in the schema |
| I. Founder explains variance | **PASS** — written to `founder_explanation`, structurally separate from the frozen arithmetic fields |
| J. Revenue target committed | **PASS** — frozen `expected_monthly.revenue_cents` supports the exact comparison 38C already renders, now against a frozen rather than live value |
| K. Expense change committed | **PASS** — `expected_monthly.expenses_cents` freezes the *computed, baseline-inclusive* consequence of the delta, not the raw delta itself, sidestepping the Plan Baseline Problem 38C identified without ever reconstructing a historical baseline |
| L. Hire actualized | **PASS** — `venture_hire_plans.status` flips via the existing reconciliation flow; the frozen commitment and the live actual snapshot are read from two structurally distinct sources, never summed — no double counting |
| M. Commitment abandoned | **PASS** — `status='abandoned'`, row never deleted |
| N. Multiple commitments over time | **PASS** — independent rows, no giant mutable blob (§17) |
| O. No Finance data | **PASS** — the commit action requires a `source_snapshot_id`; blocked with the same "no snapshot exists yet" guard `/financials/reconcile` already uses — no fake actual, no fake commitment |
| P. Unknown financial values | **PASS** — `compute_derived_metrics` already returns `None` for unknown fields (NULL≠zero, unchanged); `expected_monthly` faithfully embeds nulls where the source snapshot had them |
| Q. Different user | **PASS** — every read/write follows the identical ownership-scoped JOIN-on-`modeled_ventures.user_id` pattern already used by every other Finance function |
| R. Fundraising scenario | **PASS (as a design answer)** — sibling-table compatibility explained in §19; nothing implemented |
| S. Build decision unrelated to Finance | **PASS** — the new FK lives on the commitment, not on `venture_decisions`; an ordinary decision needs zero awareness of Finance |
| T. Founder rejects SIE recommendation, commits anyway | **PASS** — `venture_decisions` already independently stores both `sie_recommendation` and `founder_choice`; the commitment merely references that row via `related_decision_id`; neither field is ever rewritten |

All twenty cases pass without forcing the architecture.

## 28. LedgerFlow walkthrough

**Day 1.** Existing snapshot `S1` (cash $500K, MRR $20K, expenses $70K). Founder models two hire plans —
`H_A` (Engineer, start October, $180K salary, 25% burden, `status='planned'`) and `H_B` (start January,
`status='planned'`) — and two scenarios, "Plan A" (`hire_plan_ids=[H_A]`) and "Plan B" (`hire_plan_ids=[H_B]`).
SIE computes both live via `GET .../scenarios/{id}` — nothing persisted yet (Case A).

Founder chooses Plan A. Two rows are created:
- `D1` (`venture_decisions`): `sie_recommendation="Delay hiring until Q1"`, `founder_choice="Proceed with
  October hire"`.
- `C1` (`venture_financial_commitments`): `source_snapshot_id=S1.id`, `scenario_id`/`scenario_name="Plan A"`,
  `hire_plan_ids=[H_A]`, `plan_snapshot=[{id:H_A, kind:"hire", role:"Engineer", start_date:"Oct",
  annual_salary_cents:18_000_000, burden_percent:0.25}]`, `expected_monthly=[...frozen 24-month
  projection from S1+H_A...]`, `calculation_version="v1"`, `related_decision_id=D1.id`, `status="active"`,
  `founder_rationale="Engineering velocity matters more than runway right now"`.

**Day 30.** Founder edits `H_A` (say, bumps the salary). `H_A` updates in place, as designed. `C1.plan_snapshot`
and `C1.expected_monthly` are untouched — they still say $180K/October (Case C).

**Day 60.** New snapshot `S2` recorded (cash $390K, MRR $25K, expenses $92K).

**Day 61.** SIE compares, read-time only: finds `C1`'s `expected_monthly` entry whose `date` falls in S2's
calendar month, computes `compute_derived_metrics(S2)`, diffs the two — e.g. "$17K above plan" — writes
nothing. Founder explains: `C1.founder_explanation="We accelerated the second engineering hire after closing
the enterprise pilot."`, `explanation_recorded_at=Day 61` — the one field on `C1` that ever changes again.

**Day 120.** Founder commits to a separate marketing increase. A **new**, independent commitment `C2` is
created (`financial_plan_ids=[the marketing plan]`, its own fresh `source_snapshot_id`/`expected_monthly`).
`C2` does not supersede `C1` — they are about different decisions (Case N). Had the founder instead reversed
the *hire* decision, that would produce `C3` with `supersedes_commitment_id=C1.id`, flipping `C1.status` to
`'superseded'` — not what happens here.

**What exists at the end:** `S1`, `S2` (snapshots, unchanged, append-only); `H_A` (mutated once), `H_B`
(untouched, Plan B never committed); two scenarios (untouched, still hypothetical); `D1` (untouched); `C1`
(mutated exactly once — `founder_explanation` only); `C2` (independent, new).

**What the Command Center could truthfully say:** "You committed to hiring an engineer starting October at
$180K/year (Day 1). Your latest actual snapshot (Day 60) shows expenses $17K above what you expected for
that month. You explained: 'We accelerated the second engineering hire after closing the enterprise pilot.'
You also committed to a marketing increase (Day 120), not yet compared against any actual." Every clause
maps to a named field above — nothing is invented for this sentence.

The architecture explains this walkthrough with no ad hoc mechanism. **Not rejected.**

## 29. FP&A boundary

See §22 — restated here per the required document outline: this schema is one append-only commitment table
plus a read-time comparison function, nothing resembling a ledger, chart of accounts, or budgeting system.

## 30. Recommended implementation sequence

- **38D-A — Commitment persistence + frozen expectation.** New table, "Commit to this plan" action (compute
  `expected_monthly` once via the existing `project_monthly_cash_flow`, freeze `plan_snapshot`, store),
  list/get, supersede/abandon actions. Visible founder value on its own: SIE now remembers exactly what was
  committed and expected, even before any comparison UI exists.
- **38D-B — Expected vs. actual comparison.** A pure, read-time comparison function (same style as
  `commandCenterCrossSystem.ts`), calendar-month aligned (§10), surfaced wherever Command Center/Finance
  history already renders. Visible value: "here's how reality diverged from what you committed to" — the
  gap 38C exposed, closed.
- **38D-C — Founder explanation capture.** UI + endpoint to set `founder_explanation`/
  `explanation_recorded_at`, displayed alongside the variance. Visible value: closes the learning loop.

Each stage ships independent, visible founder value; none requires the next to be useful.

## 31. Stop conditions checked

| Condition | Triggered? |
|---|---|
| More than 2-3 new tables for V1 | No — exactly one |
| Copying the entire Finance database | No |
| Plan history cannot be preserved safely | No — §6 resolves it |
| Expected-state semantics ambiguous | No — reuses `ScenarioProjectedMonth` verbatim |
| Time alignment cannot be made explainable | No — calendar-month, latest-wins (§10) |
| Decision × Finance requires text matching | No — one clean optional FK (§13) |
| Architecture starts resembling FP&A | No — explicitly bounded (§22) |
| Fundraising requirements distort the Finance design | No — sibling-table doctrine only (§19) |
| Generic JSON event sourcing becomes the answer to everything | No — Option C explicitly rejected (§23) |

No stop condition triggers. The architecture is cleared for a future implementation phase — this phase
itself implements nothing.

## 32. Phase 38D-A implementation (as built)

Implements exactly the MODEL → COMPARE → COMMIT slice from §30's own sequencing — commitment persistence
and frozen expectation only. Expected-vs-actual comparison (38D-B) and founder explanation (38D-C) remain
unimplemented; nothing in Command Center, Build, Analyze, SPS, or Fundraising was touched.

### Final schema

One new table, `venture_financial_commitments` (`app/database/db.py::create_venture_financial_commitments_table`),
exactly as proposed in §24 with one deliberate narrowing: `founder_explanation`/`explanation_recorded_at`
were **not** added as columns yet — per the 38D-A directive's own "creation is the important operation"
instruction, adding a column with no code path that ever sets it would itself be the "improvise additional
schema" the directive forbids. `status`/`supersedes_commitment_id` exist in the schema (matching §16's
lifecycle) but no endpoint in this phase ever sets them to anything but `status='active'` — supersede/abandon
actions are correctly deferred, not needed to safely create a commitment.

```
venture_financial_commitments
  id, venture_id, user_id, committed_at,
  source_snapshot_id  -- NOT NULL, ON DELETE RESTRICT (snapshots are never deleted; §8)
  scenario_id, scenario_name,          -- nullable; scenario_name denormalized so a later-deleted scenario doesn't lose its label
  hire_plan_ids, financial_plan_ids,   -- INTEGER[]; only the ids ACTUALLY included after status filtering (§21)
  plan_snapshot JSONB,                 -- frozen input values, §6
  calculation_version,
  projection_start, projection_horizon_months,
  expected_monthly JSONB,              -- frozen ScenarioProjectedMonth[], §25 -- NEVER recomputed on read
  related_decision_id,                 -- nullable, §13
  status ('active'|'superseded'|'abandoned'), supersedes_commitment_id,  -- schema present, no writer yet
  founder_rationale,
  idempotency_key                      -- unique partial index, excluded from every SELECT column list (matches venture_decisions' own convention)
```

### Immutability rules

`create_venture_financial_commitment()` (`app/database/db.py`) is the ONLY write path — there is no
UPDATE/DELETE function for this table anywhere in the codebase, and no PATCH/DELETE endpoint. Once a row
exists, `plan_snapshot`, `expected_monthly`, `calculation_version`, `source_snapshot_id`, and `committed_at`
are never touched again by any code path. `get_venture_financial_commitment_for_owner()`'s own docstring
states the load-bearing guarantee directly: a GET must never depend on the current state of
`venture_hire_plans`/`venture_financial_plans`/`venture_financial_snapshots`. Verified structurally in
`test_case_k_reading_a_commitment_never_recomputes_the_projection` (monkeypatches `api.project_monthly_cash_flow`
to raise, confirms GET still succeeds) and empirically in the live walkthrough below.

### Source snapshot semantics

`source_snapshot_id` is `NOT NULL, ON DELETE RESTRICT` — a commitment cannot exist without a real snapshot
(§8), and since snapshots have no delete path in this codebase at all, `RESTRICT` simply makes that
guarantee explicit rather than relying on `SET NULL` silently fighting a `NOT NULL` constraint. The
commit endpoint fetches `get_latest_venture_financial_snapshot_for_owner()` once, at commit time, and never
re-reads it afterward — a later, newer snapshot (Case J) has zero effect on an existing commitment.

### plan_snapshot shape

Per-item fields as proposed in §25, built by a new `_plan_snapshot_item()` helper (`app/api.py`): hire items
carry `role, employment_type, annual_salary_cents, burden_percent, monthly_cost_cents, one_time_cost_cents`;
`revenue_target`/`expense_change` items carry `category, amount_cents`. Every item also carries `id, kind,
label, start_date, end_date` for traceability. `PlanSnapshotItem` (`app/models/venture_financial_commitments.py`)
is the Pydantic contract; `dashboard/types/finance.ts::PlanSnapshotItem` mirrors it by hand, per this repo's
own convention.

### expected_monthly shape

`ScenarioProjectedMonth` reused verbatim, as §25 specified — no new shape. Frozen via
`project_monthly_cash_flow()`, called exactly once at commit time with `DEFAULT_PROJECTION_HORIZON_MONTHS`
(24) and the plan items already active at that moment.

### Calculation version

`FINANCIAL_PROJECTION_CALCULATION_VERSION = "1"` (`app/ai/financial_engine.py`, beside
`DEFAULT_PROJECTION_HORIZON_MONTHS`), stamped onto every commitment at creation. Bumped by hand only if
`project_monthly_cash_flow()`'s own math changes; never read back to trigger a recompute.

### What gets frozen (§21 of the 38D-A directive — plan status agreement)

The commit endpoint reuses the EXACT SAME `status == "planned"` filter the live scenario engine already
applies (`hire_plan_items_for_projection`/`financial_plan_items_for_projection`'s own internal filter,
identical to `_build_scenario_response`'s explicit one) before building `plan_snapshot` and computing
`expected_monthly` — a cancelled or actualized plan is silently excluded from both, exactly as the live
scenario engine already excludes it (Cases T/U). `hire_plan_ids`/`financial_plan_ids` on the stored row
reflect only the ids that survived this filter, so they always agree with `plan_snapshot`'s own membership.

### API

Three endpoints, following the exact conventions of the adjacent scenario/decision endpoints:

- `POST /ventures/{venture_id}/financial-commitments` — accepts either `scenario_id` (resolved server-side
  into its own current `hire_plan_ids`/`financial_plan_ids`, never a client-supplied copy) or explicit
  `hire_plan_ids`/`financial_plan_ids` directly (§4/§18: both scenario- and individual-plan commitment are
  supported by the same shape, exactly as designed) — `CreateFinancialCommitmentRequest`'s own validator
  rejects supplying both or neither. Every referenced id (hire, plan, decision) is re-validated as belonging
  to this venture/user, identical discipline to `create_scenario()`'s own validation. Blocks with 404 when no
  snapshot exists (§8) and with 422 when the projection can't be honestly calculated (§20, NULL≠0) — in
  neither case is any row written.
- `GET /ventures/{venture_id}/financial-commitments` — full history, most recent first.
- `GET /ventures/{venture_id}/financial-commitments/{id}` — the stored row exactly, no recomputation.

No PATCH, no DELETE.

### UX

Placed inside the existing `ScenariosSection`/"Compare plans" area of `FinanceOverview.tsx` — no new tab, no
new page, per §14 of the directive. Each scenario card gained a `ScenarioCard` sub-component with:

- A "Commit to this plan" button and the exact supporting copy the directive specified.
- A disabled-while-`submitting` guard (Case V: a double-click while a request is in flight cannot fire a
  second one) plus a per-attempt `idempotency_key` so even a resent network request collapses to the same
  row — never two genuinely separate later clicks (§16, verified by
  `test_repeat_commitments_with_no_idempotency_key_are_both_real`).
- An inline confirmation panel on success ("Operating plan committed... Committed projection: $X in N
  months") built entirely from the POST response — no JSON dump, no new fetch.
- An informational "Committed" badge with the same summary, shown on every subsequent load by cross-referencing
  `listFinancialCommitments()` against each scenario's own id — purely a display of already-fetched history,
  not a gate: the button still reads "Commit to this plan again" and remains fully clickable (§16).

Individual-plan commitment (option B) has a working backend endpoint but **no frontend entry point in this
phase** — per §4's own allowance ("if only scenario commitment is implemented, document that clearly").
Scenario commitment was judged sufficient UI surface for the smallest useful V1 slice; a future phase can add
a "Commit" action to a single row in `PlannedChangesSection` without any backend change.

### Authorization

Every new function follows the identical ownership-scoped pattern already used by every other Finance
function in `db.py` — no new access-control mechanism was invented. Verified directly:
`test_case_n_different_user_cannot_read_a_commitment`, `test_case_op_different_user_cannot_commit_a_foreign_scenario_or_plan`,
`test_case_r_foreign_related_decision_id_is_rejected`.

### Tests

New file `app/tests/test_venture_financial_commitments.py` (registered via the same `python -m
app.tests.test_venture_financial_commitments` convention as every other backend test file): 21/21 passing,
covering Cases A through U plus two dedicated idempotency tests. Full spot-check of adjacent suites
(`test_venture_scenarios`, `test_venture_financials`, `test_venture_hire_plans`, `test_build_intelligence_loop`,
`test_venture_graduation`, `test_idea_lab`, `test_founder_workspace`) all passing — zero regression. Frontend:
`tsc --noEmit`, `eslint`, and `next build` all clean; full `npm test` (18 files) passing.

### Live walkthrough

On `venture_id=8212` ("FridgeChef Renamed Private"), the same standing demo venture Phase 38C established:
created a hire plan and a scenario bundling it with the venture's existing `revenue_target` plan, then
clicked the real "Commit to this plan" button in the running UI. The confirmation panel rendered
("Operating plan committed... Committed projection: $519,540 in 24 months"). Reloaded the page — the
informational "Committed" badge persisted with the identical figure. Edited the underlying hire's salary
($120K → $250K) and the revenue target's amount ($30K → $90K) directly against the live, running backend;
re-read the commitment via the API and confirmed `plan_snapshot`/`expected_monthly`/`committed_at`/
`calculation_version` were byte-for-byte identical before and after. Reloading the actual page then showed
the live scenario preview correctly recalculated to the new, higher figures while the "Committed" card
directly below it kept showing the original, unchanged $519,540 — the two numbers visibly diverging
side-by-side on the same screen, which is the plainest possible proof of the invariant this phase exists to
protect. Recorded a newer financial snapshot and confirmed via the API that the commitment's own
`source_snapshot_id` and `expected_monthly[0].starting_cash_cents` remained pinned to the original snapshot.
Afterward, reverted the edited plan values and removed the walkthrough-only newer snapshot to restore
venture 8212 to Phase 38C's own established Command Center demo state, then reconfirmed live that both of
38C's cross-system statements (stale snapshot + revenue divergence) still render correctly — no regression
to that phase's fixture. The new hire plan, scenario, and commitment created during this walkthrough were
left in place as a standing demonstration of the new feature.

### Limitations

- `founder_explanation` has no column yet — deferred to 38D-C, per this phase's own scope guard.
- No expected-vs-actual comparison surface exists yet (38D-B) — a commitment can be created and read back,
  but nothing yet tells a founder how it compares to what actually happened.
- Individual-plan commitment has no UI entry point (documented above), though the backend and tests fully
  cover it.
- A true browser-level double-click race (two near-simultaneous physical clicks) was not separately
  reproduced; confidence instead comes from the `disabled={submitting}` guard read directly in the
  component plus the backend idempotency test, which is the same standard of proof this session has used for
  analogous UI-guard claims in prior phases.

## 33. Phase 38D-B implementation (as built)

Implements the OBSERVE step from §30's own sequencing — deterministic expected-vs-actual comparison only.
No new persisted concept, no table, no AI, no explanation, no recommendation. `founder_explanation` and any
notion of "why" remain 38D-C's own scope, untouched.

### Comparison contract

A new pure module, `app/ai/commitment_comparison.py::build_commitment_comparison()`, takes a raw
`venture_financial_commitments` row plus the venture's full snapshot history and returns, at read time only:

```
FinancialCommitmentComparisonResponse
  commitment_id, committed_at, source_snapshot_id, scenario_name, calculation_version
  months: MonthComparison[]
    month_index, date, actual_snapshot_id, actual_as_of_date
    cash / revenue / expenses / net_cash_change: { expected, actual, variance }
  latest_comparable_month
  comparison_status: "awaiting_actuals" | "partially_observed" | "observed"
```

Nothing here is persisted. No table was added — confirmed by re-running `app.api` import after this phase's
changes and observing no new `CREATE TABLE` line.

### Actual-source rules

EXPECTED comes exclusively from the commitment's own already-frozen `expected_monthly` (Phase 38D-A) — never
regenerated, never re-reading the scenario, live plan rows, or the financial engine. ACTUAL comes exclusively
from `venture_financial_snapshots` via `compute_derived_metrics()`, the same function every other actual-state
read in this codebase already uses — never inferred from a plan's own `status` (a hire becoming `'actualized'`
establishes nothing about the canonical financial snapshot, per §4 of the directive).

### Month alignment

Calendar-month match: for each expected month, find snapshots whose `as_of_date` falls in the exact same
`(year, month)`. No nearest/previous/next/interpolation. When multiple snapshots exist in the same month, the
winner is `(as_of_date DESC, recorded_at DESC)` — the identical tie-break
`get_latest_venture_financial_snapshot_for_owner()` already uses, reused verbatim rather than inventing a new
rule (§18).

**Additional eligibility rule (§20):** a snapshot must also have `as_of_date >= commitment.committed_at`'s own
date. Audited why this is necessary: `project_monthly_cash_flow()`'s own month_index=1 is always exactly one
calendar month after the source snapshot's `as_of_date` (`_add_months(as_of_date, 1)`, confirmed directly by
reading the function and by a dedicated regression test, §33's own Case Y below) — and since the commit
endpoint always uses the LATEST snapshot as its source, no snapshot already existing at commit time can ever
coincide with month_index=1's own calendar month *unless* it was entered (or backdated) after the fact. A
backdated snapshot dated before the commitment itself cannot honestly represent a realized result of a plan
that did not yet exist — exactly the directive's own December 20/December 5 example. This rule is applied to
EVERY expected month, not just the first: a founder who deliberates a long time before committing accepts
that comparison starts counting from the moment of commitment forward (documented tradeoff, see LIMITATIONS).

### Comparable metrics

| Metric | Expected source | Actual source | Included? |
|---|---|---|---|
| Cash | `ending_cash_cents` | `cash_balance_cents` | Yes — same semantic meaning, a point-in-time balance |
| Revenue | `revenue_cents` | `total_monthly_revenue_cents` (derived) | Yes |
| Expenses | `expenses_cents` | `total_monthly_expenses_cents` (derived) | Yes |
| Net cash change | `net_cash_change_cents` | computed fresh as `actual_revenue - actual_expenses` | Yes, but NOT via `compute_derived_metrics()`'s own `net_burn_cents` — that field uses the OPPOSITE sign convention (`expenses - revenue`, positive = burning); reusing it directly would have silently flipped a sign. Computed identically to the expected side's own formula instead. |

### Excluded metrics and why

- **Runway** — per the directive's own default recommendation, confirmed correct by audit: `ScenarioProjectedMonth`
  has no runway field at all on the expected side, and `runway_months` on the actual side is a forward-looking
  derived quantity computed from the CURRENT snapshot's own trajectory — there is no honest "expected runway at
  month N" to compare against. Excluded entirely.
- **plan_expense_impact_cents / plan_revenue_active / active_plan_item_ids / depleted / starting_cash_cents** —
  structural projection metadata (which plans were active, whether the plan itself depletes) with no actual-side
  equivalent; not comparable metrics, excluded from the comparison (though `date`/`month_index` remain as
  context fields).

### Variance semantics

`variance = actual - expected`, sign preserved, always. Verified: an expense overrun produces a POSITIVE
variance, a cash shortfall produces a NEGATIVE variance (both directly asserted in tests). No qualitative
language anywhere in the response or the UI — a plain signed dollar figure only (e.g. `+$2,980`, `-$63,000`).

### Missing-data behavior

`expected` is never null (a commitment can only be created when every frozen month's inputs were already
fully known — 38D-A's own 422 guard). `actual`/`variance` are null exactly when no eligible snapshot exists
for that month, OR an eligible snapshot exists but that specific field was never recorded on it (independently
per metric — a snapshot with cash but no revenue still lets cash compare while revenue and net_cash_change
stay null). Never a fabricated zero.

### Comparison status

Three states, describing DATA AVAILABILITY only: `awaiting_actuals` (zero months observed), `partially_observed`
(some but not all), `observed` (every projected month has a matching actual). No `on_track`/`healthy`/
performance-judgment state was created — none was needed, and the directive explicitly forbade inventing one
without an existing accepted precedent.

### API

One new endpoint: `GET /ventures/{venture_id}/financial-commitments/{commitment_id}/comparison`. Reuses the
exact two ownership-scoped reads every other Finance endpoint already uses
(`get_venture_financial_commitment_for_owner`, `list_venture_financial_snapshots_for_owner`) — no new database
function was written for this phase. No POST, no PATCH, no persistence.

### UX

Lives inside the same "Committed"/confirmation panel `FinanceOverview.tsx`'s `ScenarioCard` already renders
(38D-A) — no new tab, no History/Analyze/Overview detour (§14). A new `CommitmentComparisonSection` fetches
the comparison once the commitment exists and renders:

- `awaiting_actuals`: "Waiting for actuals..." plus the directive's own specified copy pointing at the
  existing "Update cash & monthly finances" action.
- Otherwise: the latest observed month's own Cash/Revenue/Expenses table (Expected/Actual/Difference columns,
  a plain signed dollar figure, no words), with earlier observed months tucked behind a "See earlier observed
  months (N) ▾" progressive disclosure — never every month of a 24-month projection dumped at once (§15).
  `net_cash_change` is part of the API contract and tested, but deliberately left out of the V1 table to match
  the directive's own three-metric UX example exactly and avoid a redundant fourth row.

### Authorization

Identical ownership-scoped pattern as every other Finance/commitment endpoint — verified directly
(`test_api_ownership_blocks_user_b`). No verification/graduation/analysis/public-profile gate of any kind.

### Tests

New file `app/tests/test_commitment_comparison.py`: 23/23 passing, two layers —
15 direct pure-function unit tests (month alignment, the pre-commit exclusion rule, multi-snapshot tie-break
including a same-as_of_date `recorded_at` tie-break, null propagation per metric, the first-projection-month
regression proving `_add_months` semantics directly) and 8 API-level integration tests (authorization,
awaiting/partially-observed status through the real endpoint, a structural no-recompute proof, cash-flow-positive
and out-of-cash neutral-arithmetic cases, and a full re-verification of 38D-A's own source-mutation immutability
guarantee now that a comparison read-path exists alongside it). Full regression spot-check
(`test_venture_financial_commitments`, `test_venture_scenarios`, `test_venture_financials`,
`test_venture_hire_plans`, `test_build_intelligence_loop`, `test_venture_graduation`, `test_idea_lab`,
`test_founder_workspace`) all passing — zero regression. Frontend: `tsc --noEmit`, `eslint`, `next build`, and
the full `npm test` suite all clean.

A real bug was caught and fixed during test-writing: the first implementation of `_as_date()` used
`isinstance(value, date)` to detect an already-converted date, which silently also matches `datetime` (a
`datetime` is itself a subclass of `date` in Python) — `commitment["committed_at"]` (a real `datetime`) was
passed through unconverted and then failed to compare against a plain `date`. Fixed by checking
`isinstance(value, datetime)` first. Caught by the very first pure-function test run, before any live
verification — exactly the value of writing the unit-test layer first.

### Live walkthrough

On the same `venture_id=8212` fixture, using the standing 38D-A commitment (id=35, "38D-A Walkthrough Plan"):
confirmed the frozen commitment panel still rendered with its original $519,540 projection untouched, then
confirmed the "Expected vs. actual" section correctly showed "Waiting for actuals" (no eligible snapshot yet).
Computed September 2026's expected values by hand from the frozen `expected_monthly` (cash $204,960, revenue
$30,000, expenses $15,020), added a real financial snapshot dated September 20, 2026 (chosen specifically to
satisfy both the calendar-month match AND the `>= committed_at` rule, since the commitment's own September
2026 committed_at postdates its June-sourced month 1/2), and confirmed the live UI table showed exactly the
hand-computed variances (-$24,960 / -$5,000 / +$2,980) — verified via direct DOM read, not a screenshot alone.
Added a second September snapshot (Sept 28, different values) and confirmed, both via the API and the live
re-rendered UI, that the LATER `as_of_date` deterministically won, replacing the comparison with newly
hand-verified variances (+$5,040 / +$2,000 / +$980). Reloaded to confirm persistence. Edited the underlying
hire's salary from $120K to $600K directly against the live backend and confirmed via the API that every
expected-side value across every month was byte-identical before and after, while the actual side was also
correctly untouched (a plan edit alone establishes nothing about canonical actuals). Afterward, removed both
walkthrough-only snapshots and reverted the hire's salary, then reconfirmed live that the commitment's
comparison correctly returned to "Waiting for actuals" and that Phase 38C's own standing Command Center demo
on this venture (stale snapshot + revenue divergence) still rendered with no regression.

### Limitations

- **Early-month unobservability**: because the `>= committed_at` eligibility rule applies to every month, a
  commitment made well after its own source snapshot has expected months that can NEVER be observed (any
  snapshot dated in those calendar months necessarily predates the commitment). This is a deliberate,
  documented tradeoff favoring "never show a data point that could be mistaken for pre-decision history" over
  completeness — not an oversight.
- `net_cash_change` exists in the API but has no UI row in this phase (documented above).
- No comparison surface exists anywhere outside Finance (Command Center integration is explicitly out of
  scope, per the directive's own §26).
- No founder explanation, no interpretation, no recommendation anywhere in this phase's own code — by design.
