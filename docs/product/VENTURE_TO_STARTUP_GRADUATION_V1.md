# Venture → Startup Graduation V1

**Status:** Implemented and integrity-hardened (Phase 31A), not yet deployed.
**Scope:** Closes the single largest structural seam Phase 30's audit identified — `modeled_ventures`
and `startups`/`analyses` had zero database relationship. This is the smallest safe, explicit mechanism
that lets a founder create (or connect) a real Startup from an existing Venture without losing the
Venture's accumulated intelligence.

**Explicitly out of scope** (see Phase 30/31 directives): this is not a migration system, not automatic
graduation, not a new lifecycle score, not VPS-threshold-based, not a Founder Workspace redesign, and not
Investor Readiness V1. The founder always explicitly chooses to graduate.

---

## 1. Architecture — what actually exists

Before this phase, the only bridge between a modeled Venture and a real Startup was
`lib/ventureToStartupHandoff.ts`: a same-tab `sessionStorage` stash of the venture's free-text
`description`, read once by `/analyze`. No database relationship existed. `startups` itself has no
content columns beyond `id, canonical_name, normalized_name, created_at` — every real fact about a
company lives on `analyses` rows.

This phase adds exactly one new table:

```sql
CREATE TABLE venture_graduations (
    id SERIAL PRIMARY KEY,
    venture_id INTEGER NOT NULL UNIQUE REFERENCES modeled_ventures(id) ON DELETE CASCADE,
    startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trigger TEXT NOT NULL CHECK (trigger IN ('suggested', 'manual')),
    connected_existing_startup BOOLEAN NOT NULL DEFAULT FALSE,
    fields_transferred_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`UNIQUE(venture_id)` is the entire duplicate-protection mechanism (see §7). It is a pure relationship +
provenance record — it never carries venture content, VPS data, or evidence.

A venture graduates into a startup through the **existing** membership system, not a new one:
`create_venture_graduation()` calls the codebase's own `create_startup_claim()` (with a new
`verification_method='venture_graduation'`) followed by `approve_startup_claim(claim_id,
admin_user_id=<the founder's own user_id>)`. This is a **self-approval**, safe specifically because
provenance is unambiguous — the startup row was just created, in the same request, from this exact
user's own venture, so no competing/false claim can exist. `approve_startup_claim()` remains the only
function in the codebase that writes `startup_memberships` (enforced by
`test_no_new_membership_write_path`, a repo-wide static-analysis test); graduation adds zero new write
paths to that invariant.

## 1A. Phase 31A — Graduation Integrity & Acceptance Hardening

A follow-up audit-and-fix pass, performed before commit, on the exact write sequence above. Found two
real atomicity gaps and one real database-invariant gap; fixed all three with the smallest changes the
existing architecture supports (no distributed transaction framework, no new table).

**Finding #1 — orphan startup + permanent lockout.** The original write sequence created the `startups`
row in one transaction and granted membership in later, separate transactions. A crash in between left an
orphan startup with no durable trace of who created it or why. A retry under the same company name found
that orphan, saw the founder wasn't yet a member of it, and raised `StartupNameCollisionError` —
**permanently locking the founder out of ever graduating under that exact name again**, since their own
abandoned attempt blocked their own retry with no way to recover it.

*Fix:* `resolve_startup_for_graduation()` now inserts the new `startups` row **and** a pending
`startup_claims` row (`verification_method='venture_graduation'`) in the **same transaction**. A retry can
now always prove "this is provably my own prior attempt" (a venture-graduation-tagged claim from this
exact `user_id` exists for this exact `startup_id`) apart from "this is really someone else's company" (no
such claim exists) — recoverable in the first case, still a hard collision in the second. Verified: an
orphan from user A's own crashed attempt still blocks a *different* user (`test_orphan_from_one_user_still_blocks_a_different_user`).

**Finding #2 — graduated-but-inaccessible.** The `venture_graduations` linkage row was inserted *before*
membership was granted (claim + self-approve, each its own transaction). A crash strictly between those
two steps left a venture that read as `graduated=true` with **no actual `startup_memberships` row** — the
founder would see "Open Startup Profile" but get a 404 opening it, and no retry ever repaired it, since the
API's own "already graduated" fast path never re-checked membership.

*Fix:* reordered — `create_venture_graduation()` now calls the new, idempotent, self-healing
`_ensure_graduation_membership()` **before** inserting the linkage row, not after. This makes "linkage
exists but membership doesn't" structurally unreachable (the linkage insert is only ever attempted once
membership has already committed), rather than a state that has to be detected and repaired on read. The
one remaining window — a crash between the membership commit and the linkage commit — always self-heals
on a plain retry, because a retry's `resolve_startup_for_graduation()` call finds membership already
granted and just inserts the linkage row it never got to the first time.

**Finding #3 — a startup could receive graduation links from two different ventures.** The original schema
had `UNIQUE(venture_id)` but nothing on `startup_id`, so "connect an existing startup" could, in principle,
attach a second, unrelated venture to a startup that already had an originating venture —
`get_venture_graduation_by_startup()` would then pick one of two equally-valid rows arbitrarily for the
Founder Workspace's "Created from your X venture" acknowledgment.

*Fix:* additive migration `add_venture_graduations_startup_unique_constraint()` adds
`UNIQUE(startup_id)`. A violation is caught and translated into a clean `StartupAlreadyGraduatedError` →
`409`, the same pattern `StartupNameCollisionError` already established.

**A fourth bug was found and fixed by this hardening pass's own adversarial testing, not by inspection:**
the original concurrent-insert-race recovery code in `resolve_startup_for_graduation()` re-queried using
the *same* connection whose `INSERT` had just failed — but Postgres aborts an entire transaction the
instant any statement inside it fails, refusing every further command until a rollback happens. Under a
genuine two-request race (proven with real `threading` + FastAPI's threadpool, not a sequential retry),
this always raised a second, worse `InFailedSqlTransaction` error instead of ever actually recovering.
Fixed by letting the `IntegrityError` propagate out of the `with engine.begin()` block (triggering
SQLAlchemy's own rollback-on-exception) before retrying in a genuinely fresh transaction. Verified with a
dedicated stress script (8 threads × 20 iterations racing the same brand-new company name, zero errors,
always exactly one startup) in addition to the committed
`test_parallel_graduation_requests_converge_to_one_relationship`.

**Aggregate test-health finding (unrelated to graduation logic, found while validating the above):**
running the full `pytest app/tests/` suite together (as opposed to file-by-file) produced ~200–300
failures having nothing to do with graduation. Root cause, confirmed by reproduction on a genuinely fresh
database: `test_analyze_unified.py` set a FastAPI `dependency_overrides[get_current_user]` override as
bare **module-level** code, intended (per its own docstring) to last "for its own process lifetime" —
true for a standalone `python -m` run, but pytest imports every test module during collection **before
running any test in any file**, so the override was silently active for the entire rest of the suite the
instant that module was collected, regardless of file execution order. This overrode every other test
file's own carefully-constructed per-user JWT identity with one fixed fake identity — exactly the
scenario `test_founder_reanalysis.py`'s own docstring assumed couldn't happen. Fixed by moving the
override into `setup_module()`/`teardown_module()` (standard pytest/xUnit hooks, scoped to only that
module's own test execution), with `main()` calling both explicitly so the file's standalone entry point
is unaffected. This single fix took the full suite from **322 failed / 503 passed → 41 failed / 800
passed**; a second, identical fix (the same bare-module-level pattern was *also* poisoning execution
order via collection, independent of which file ran first) closed the gap further. The remaining 25
failures (`test_analyze_unified.py` ×9, `test_discovery.py` ×14, `test_idea_structuring.py` ×1,
`test_startup_entity_migration.py` ×1) were each independently reproduced standalone, on a fresh
database, on unmodified `main` — genuinely pre-existing, unrelated to graduation, left alone per this
phase's own explicit scope boundary.

## 2. Semantics

Graduation is entirely founder-initiated. SIE may *suggest* it (a deterministic, evidence-based
suggestion — see §3) but never performs it silently. Two backend endpoints, both behind the same
`_require_owned_venture` gate every other `/ventures/{id}/*` endpoint uses:

- `GET /ventures/{venture_id}/graduation` — current graduation status (never graduated, or the linked
  startup's id/name/connection-type/timestamp).
- `POST /ventures/{venture_id}/graduate` — creates the graduation. Idempotent (see §7).

## 3. Eligibility — deterministic, no AI, no VPS, no new score

`dashboard/lib/journey/resolveGraduationEligibility.ts`:

```ts
isEligibleForGraduationSuggestion(validation) =
  (validation.paying_customers > 0) || (validation.monthly_revenue > 0)
```

Both fields are the venture's own founder-**reported observations** (`VentureAssumptions.validation`) —
never a modeled assumption, never VPS, never an LLM call. This is a *suggestion*, not a gate: the manual
"Create a Startup Profile" path is always reachable regardless of eligibility (quietly, inside Explore,
when not eligible; prominently, right after the primary next-step card, when eligible).

## 4. The review step

Nothing is created by opening the review screen (`GraduateVentureReview.tsx`) — only by pressing its own
submit button. The founder:

- chooses the company name themselves (pre-filled with the venture's own name, editable — SIE never
  assigns a company name);
- sees exactly what text will pre-fill `/analyze`'s "Additional Company Information" field before
  submitting (§5);
- may instead choose **Connect a startup I already have**, if they already own one (§8).

## 5. Data Transfer Contract

`startups` has no columns to receive `VentureAssumptions` directly, so there is no safe way to write
venture content straight into a Startup record without either fabricating an analysis or inventing new
columns. The mechanism is instead an extension of the **existing** stash-then-review-then-submit
mechanism `lib/ventureToStartupHandoff.ts` already used for the bare description: a structured, labeled
summary is built client-side (`buildGraduationSummaryText()`), stashed into the same `sessionStorage` key,
and the founder edits or deletes any of it before submitting through the **unchanged** `/analyze`
pipeline, which independently re-derives its own Public/Inferred/Private evidence from scratch — exactly
as it does for any other submission. Creating the startup+membership itself never creates an analysis.

Field classification reuses VPS's own existing structural distinction (`validation.*` = founder-reported
**observation**; everything else = **modeled assumption**) rather than inventing a second provenance
system:

| Classification | Fields | Treatment in the pre-fill text |
|---|---|---|
| **SAFE, direct** | `description`, `target_customer`, `problem_solution.*`, all of `validation.*` | Included unlabeled |
| **REVIEW required** | `market.*`, `founder.*`, `gtm.*`, `economics.*`, `industry`, `business_model`, `stage` | Included, explicitly prefixed "Modeled assumptions from Idea Lab (not yet verified — edit or remove anything below)" |
| **Never transferred** | VPS score/categories/guidance, `capital.*` (starting capital, monthly burn), all internal operating history (missions, captures, model-update history) | Never appears anywhere in the pre-fill |

A field that is `null`/unset is simply omitted — never rendered as `"null"`, `"None"`, or a fabricated
default. Verified by `tests/graduationSummary.test.ts` (all-null venture → empty string, zero fields
counted).

## 6. Provenance preservation

No second provenance system was built. The pre-fill text is a *convenience starting point the founder can
edit or delete*, not evidence in itself — `/analyze`'s own unmodified pipeline (Public/Inferred/Private
tagging, evidence validation, correction pass) is the sole source of truth for the resulting Startup's
intelligence. A modeled assumption never becomes a "fact" through graduation: it can only become evidence
if the founder re-affirms it inside the text `/analyze` actually processes, at which point it is subject
to the exact same evidence rules as anything else submitted there.

## 7. Relationship, linkage & duplicate protection

`venture_graduations.venture_id UNIQUE` is the database-level guarantee — not a disabled button, not a
client-side check. `create_venture_graduation()` uses `INSERT ... ON CONFLICT (venture_id) DO NOTHING`;
a conflict returns `None`, and the API endpoint re-reads the existing row and returns it instead of
erroring. This makes every one of the following behave identically (all covered by
`app/tests/test_venture_graduation.py`):

| Scenario | Result |
|---|---|
| Double-click | Second request finds the first's row already committed (or races safely into the same `ON CONFLICT`); exactly one membership row either way (`test_double_click_race_creates_one_membership`) |
| Two parallel tabs | Same as above |
| Refresh mid-flow | `GET /graduation` shows the persisted state; nothing to resubmit |
| Back-button resubmit | Same idempotent `POST` handling |
| Direct repeated API call | `test_graduation_is_idempotent_on_repeat` — second call with a *different* company name still returns the *original* startup |
| Already graduated | UI shows "Open Startup Profile", never "Create" again |
| Cross-user venture id | `_require_owned_venture` 404s before any graduation logic runs (`test_other_users_venture_cannot_be_graduated`) |
| Cross-user startup connect | Ownership is checked directly against `startup_memberships`; a non-member 404s (`test_connect_existing_startup_not_owned_is_rejected`) |
| Deleted target | `ON DELETE CASCADE` on both FKs means a deleted venture or startup removes the graduation row cleanly, never an orphan |
| Partial DB failure | Both the claim-creation and self-approval happen inside `approve_startup_claim()`'s own single transaction; the graduation row's own `INSERT` is a separate, prior transaction — a failure between them leaves a `venture_graduations` row with no membership, which the next `GET/POST` would surface honestly as `graduated=true` without workspace access. Not fully atomic across both writes; see Limitations. |

## 8. Connect an existing Startup

Implemented **only** for the one case existing architecture makes genuinely safe: the founder already
holds an approved `startup_memberships` row on a startup with the exact matching name. There is no fuzzy
matching, no AI-assisted merge, and no automatic attach based on name similarity — `resolve_startup_for_
graduation()` raises `StartupNameCollisionError` (surfaced as `409`) the instant a name collides with a
startup the founder does **not** already own, rather than ever attaching to it. The review screen instead
lets the founder pick from their own `GET /me/startups` list directly (`GraduateVentureReview.tsx`) — no
name-matching involved at all for this path.

## 9. History continuity

Venture History is not migrated, duplicated, or altered. The Venture remains the historical record of how
the idea got here; the Startup becomes the canonical forward-looking record. The only new fact is the
linkage itself (`venture_graduations`), which both a `GET /ventures/{id}/graduation` (venture side) and
`get_venture_graduation_by_startup()` (startup side, surfaced as `FounderStartupWorkspace.graduated_from_
venture`) can query. A unified timeline across both is explicitly future work — not attempted here.

## 10. VPS / SPS firewall

- **VPS**: `create_venture_graduation()` never touches `modeled_ventures.assumptions` or `.model_result`.
  Verified directly (`test_graduation_never_mutates_venture_model_result`: assumptions and model_result
  are read before and after graduation and asserted byte-identical).
- **SPS**: graduation creates a `startups` row and a membership — **never** an `analyses` row. Verified
  directly (`test_graduation_never_creates_an_analysis_row`: zero `analyses` rows for the new startup
  immediately after graduation). `get_founder_startup_workspace()` already renders a membership-only,
  zero-analysis startup correctly (`methodology`/`created_at` stay `None`) — no backend change was needed
  there at all.

## 11. UX

- **Not yet graduated, not eligible**: a quiet text link inside "Explore" only (`Create a Startup Profile
  from this venture →`).
- **Not yet graduated, eligible** (real paying customers or revenue reported): a moderately prominent card
  directly after the primary "what should I do next?" step, before Venture Overview.
- **Already graduated**: a persistent, small "Operating startup: *Name* was created from this venture."
  banner directly under "Where things stand" — never buried, never removed.
- **Startup side**: one restrained "Created from your *Venture* venture" line, linking back to the
  venture's own page — shown once, never repeated elsewhere on the Founder Workspace page.
- Post-graduation, the founder is redirected straight into `/analyze?startup_id={id}` — the **existing**
  Phase 7.2.1 "Deterministic Founder Re-analysis" mechanism, reused as-is. One real bug was fixed to make
  this correct: `AnalyzeStartupForm.tsx` used to skip the venture-description pre-fill entirely whenever
  `?startup_id=` was present (a now-stale assumption from before graduation existed, when that flow only
  meant "re-analyze the same existing startup"). Removing that early-return costs nothing for ordinary
  re-analysis, since the stash-consume function already no-ops when nothing was stashed.

## 12. Analytics

Four new event names, added to the existing closed `_ALL_EVENT_NAMES` set (`app/database/db.py`) — no
free-form event names, no private content in metadata:

- `graduation_prompt_shown` — fires once per mount, only when the prominent (eligible) suggestion is
  actually rendered.
- `graduation_started` — fires when the founder opens the review screen (whether or not they complete it).
- `venture_graduated` — fires only once the graduation row is actually persisted (or the connect-existing
  path completes); metadata carries only `trigger` (`suggested`/`manual`) and
  `connected_existing_startup` (boolean).
- `startup_opened_from_venture` — fires when the founder clicks "Open Startup Profile" from the venture
  side of an already-graduated venture.

All four route through the existing `_log_event_safe()` fail-open wrapper — an analytics outage can never
block graduation itself.

## 13. Copy audit

Avoided throughout: "you're ready," "graduated" (as founder-facing praise), "congratulations," "VPS
qualifies you." Used instead: "Create Startup Profile," "Connect a startup I already have," "Real
evidence, not just a model," "Operating startup." The founder always types (or edits) the company name —
SIE never assigns one.

## 14. Tests

- `app/tests/test_venture_graduation.py` — 25 backend tests. The original 16 (status checks, cross-user
  authorization both directions, idempotency, the double-click race, name-collision blocking,
  connect-existing (owned and not-owned), the VPS firewall, the SPS firewall, Founder Workspace
  provenance display) plus 9 added by Phase 31A's own adversarial hardening: simulated-crash recovery at
  each write-sequence boundary (orphan-startup retry, cross-user orphan still blocked, membership-granted-
  but-unlinked retry), 5 repeated `POST`s never duplicating anything, a true concurrent-race test (real
  `threading` + FastAPI's threadpool, not sequential retries), connecting an already-graduated startup
  blocked (database invariant #3), live verification the `UNIQUE` indexes actually exist in the schema,
  and both FK-cascade directions (deleting the venture preserves the startup/membership; deleting the
  startup preserves the venture).
- A standalone stress script (not committed — ad hoc verification): 8 threads × 20 iterations racing the
  same brand-new company name, zero errors, always exactly one startup — the real-concurrency proof for
  finding #4 (see §1A).
- `dashboard/tests/graduationEligibility.test.ts` — 6 tests for the pure eligibility function (null,
  zero, negative, and real-evidence cases).
- `dashboard/tests/graduationSummary.test.ts` — 6 tests for the Data Transfer Contract's text builder
  (unknown-stays-unknown, no `null`/`undefined` leakage, capital never included, validation fields
  unlabeled, review fields explicitly labeled, description counted correctly).
- Full existing regression re-run clean: startup claims, startup membership, founder workspace, founder
  actions, founder evidence (including `test_no_new_membership_write_path`), founder re-analysis, venture
  history, venture share, fundraising readiness, product analytics — all pass individually against both
  the normal dev database and a genuinely fresh one.
- **Full-suite clean-database run** (Phase 31A's own aggregate-health fix applied, see §1A): two
  consecutive runs against a freshly created, empty database produced **identical results both times** —
  25 failed / 800 passed, 0 flaky/non-deterministic tests. All 25 remaining failures were independently
  reproduced standalone, on a fresh database, on unmodified `main` — confirmed pre-existing and unrelated
  to graduation (`test_analyze_unified.py` ×9, `test_discovery.py` ×14, `test_idea_structuring.py` ×1,
  `test_startup_entity_migration.py` ×1).
- Frontend: `npx tsc --noEmit` clean, `npx eslint .` clean, `npm run build` succeeds, and the complete
  `npm test` chain (11 suites, 200 tests) passes.

## 15. Limitations

- **The two remaining transaction boundaries are self-healing, not atomic.** `venture_graduations`'
  insert and the membership grant are still two separate Postgres transactions (an existing-architecture
  constraint — claim creation and approval are themselves two of this codebase's established building
  blocks, never unified into one transaction anywhere else either). Phase 31A's fix is ordering +
  idempotent retry, not a distributed transaction: membership is granted BEFORE the linkage row, so
  "graduated but no real access" is no longer reachable at all, and the one remaining window (a crash
  between the membership commit and the linkage commit) always self-heals on a plain retry of the same
  endpoint — see §1A for the full analysis and the tests that prove it.
- **"Connect an existing Startup" only covers the already-owned, exact-name-match case.** A founder whose
  venture should logically link to a startup they don't yet have membership on has no path here — they
  would need to claim that startup first (the existing `/startup-claims` flow), then use Connect. This is
  the deliberate, documented boundary of what's safe without fuzzy matching or AI (Part 13).
  Cross-referenced with `docs/product/SIE_PRODUCT_END_STATE_AND_NETWORK_ARCHITECTURE.md`'s own graduation
  discussion.
- **No unified Venture+Startup timeline.** Venture History and SPS History remain two separate views,
  linked only by the one-line acknowledgment on each side. Building a single combined timeline is
  explicitly future work, not attempted here (Part 8's own scope boundary).
- **Live browser walkthroughs were not performed.** This environment's browser automation has no
  authenticated Clerk session available for this app, and creating one is outside this phase's
  permissions. All 10 required scenarios (idea-only, validating, operating/suggestion, graduation,
  repeat, reload/persistence, cross-user both directions, unknown-data, VPS firewall, SPS firewall) are
  instead verified through the FastAPI `TestClient` JWT-mocking harness used throughout this codebase's
  existing test suite (§14), which exercises the identical backend code path a real browser session would
  hit. Frontend rendering correctness is verified via `tsc`, `eslint`, and a full production `next build`,
  not a live rendered screenshot. Documented honestly rather than fabricated, consistent with this
  engagement's prior mobile-viewport limitation record (Phase 29C).
- **Mobile/dark-mode live rendering checks were not performed**, for the same authentication-access reason
  above. Every new component reuses this codebase's existing `BaseCard`/`Button` primitives and Tailwind
  token classes exclusively (no new colors, no new breakpoints, no custom CSS) — the same components
  already verified responsive/theme-aware elsewhere in the app — but this is a design-consistency argument,
  not a substitute for an actual rendered check.

## 16. What this enables next

With a real Venture↔Startup edge now persisted and queryable in both directions, future work (explicitly
not started here) can build: a unified founder timeline spanning both records, an Investor Readiness
system that can see a startup's full originating context, and eventually the "network flywheel" Phase 30
described — none of which required guessing at this phase's own schema, since `venture_graduations` was
designed as a stable join table from the outset (`UNIQUE(venture_id)`, indexed `startup_id`).
