# SIE Unified Founder Workspace — Architecture + Convergence Plan V1

**Phase 37A.** This is an architecture and planning document. No code was changed to produce it. Every claim
below is sourced from reading the current repository (`app/database/db.py`, `app/api.py`, and the relevant
frontend components) this phase, plus real row counts queried from the local dev database. Where a prior
phase's report is referenced, it is only as a pointer to what to re-verify — every number and code path here
was re-read, not assumed.

---

## 1. Current architecture map

```
users (Clerk-backed, id = Clerk user id)
  │
  ├── modeled_ventures (user_id)  ─────────────────────────────┐
  │     assumptions JSONB, model_result JSONB (VPS+guidance)   │
  │     │                                                       │
  │     ├── venture_missions (venture_id)      "Your Actions"   │  BUILD
  │     ├── venture_evidence (venture_id)      evidence loop    │  (all venture_id-scoped,
  │     ├── venture_decisions (venture_id)     decisions        │   all owned via
  │     ├── venture_model_updates (venture_id) VPS recompute log│   users.id = modeled_ventures.user_id)
  │     ├── venture_financial_snapshots (venture_id)  Finance   │
  │     ├── venture_hire_plans (venture_id)                     │
  │     ├── venture_financial_plans (venture_id)                │
  │     ├── venture_financial_scenarios (venture_id)            │
  │     └── venture_graduations (venture_id UNIQUE) ────────────┘
  │            │
  │            ▼ startup_id (UNIQUE — at most one venture per startup)
  ├── startups (normalized_name UNIQUE)  ◀──────── also created directly by Analyze
  │     │                                           (get_or_create_startup, UNOWNED by construction)
  │     ├── startup_memberships (user_id, startup_id)   ownership/role
  │     ├── startup_claims (user_id, startup_id, status, verification_method)
  │     ├── founder_actions (startup_id)         "Action Plan" — separate action system
  │     ├── founder_updates (startup_id)         "Recent Updates" — separate update system
  │     ├── startup_milestones (startup_id)
  │     ├── analyses (startup_id)                canonical SPS/pillar analysis rows
  │     └── score_history (analysis_id)          legacy V2.1 score trend only
  │
  └── saved_startups (user_id, startup_id)       bookmarks, unrelated to ownership
```

**Key structural fact, confirmed by reading every relevant schema this phase**: `modeled_ventures` has **no
foreign key to `startups` at all**. The only bridge between the two identity roots is the single link table
`venture_graduations` (`venture_id` UNIQUE, `startup_id` UNIQUE). Everything Build produces
(`venture_missions`, `venture_evidence`, `venture_decisions`, all of Finance) stays permanently attached to
`modeled_ventures.id` — graduation never moves, copies, or touches any of it.

---

## 2. Identity map (per §3 of the directive)

| Object | Purpose | PK | User relationship | Company relationship | Creation path | Read paths | Write paths | UI consumers | Canonical? | Duplicated? | Lifecycle-specific? | Safe to retire? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `modeled_ventures` | A founder's own private, editable model of a company they're building | `id` | `user_id` (owner, direct FK) | *is* the company (pre-graduation) | Idea Lab "Start a new idea" | `list_modeled_ventures_for_user`, `get_modeled_venture_for_user` | `create_modeled_venture`, `update_modeled_venture_for_user` | `VentureWorkspace.tsx` and all of Build | Yes, for Build | No | No — spans idea through revenue | No — this is the durable company record |
| `startups` | The stable, name-deduplicated identity every canonical Analyze/Rankings/Discovery query keys off | `id` | None directly — ownership is via `startup_memberships` | *is* the company (public/evaluation identity) | Either (a) Analyze's `get_or_create_startup` (unowned), or (b) graduation's `resolve_startup_for_graduation` | `get_founder_startup_workspace`, public `/startup/[id]` reads | `create_startup` (Analyze), graduation | `FounderStartupWorkspaceView`, public Startup Profile | Yes, for Analyze/public identity | No, but see §4 | No | No |
| `startup_memberships` | Who owns/operates a startup | `id` | `user_id` | `startup_id` | `create_startup_claim` + `approve_startup_claim` (self-approved on graduation, human-reviewed otherwise) | membership checks throughout `app/api.py` | graduation, claim approval | trust badges, access gates | Yes | No | No | No |
| `startup_claims` | The audit trail of *how* membership was granted (manual review vs. unambiguous graduation provenance) | `id` | `user_id` | `startup_id` | Claim submission or graduation | admin review queue, `FounderWorkspace` | `create_startup_claim`, `approve/reject` | Claim submission UI, admin review | Yes | No | No | No |
| `venture_graduations` | The one link between a `modeled_venture` and a `startup` | `id` | `user_id` (redundant with both sides, kept for query convenience) | both | Graduation endpoint | `get_venture_graduation_for_owner`, `get_venture_graduation_by_startup` | `create_venture_graduation` (idempotent) | Graduation banner, "created from your X venture" acknowledgment | Yes | No | Yes — this table's entire purpose is a lifecycle transition | No |
| `analyses` (canonical) | One completed Analyze run's full methodology JSONB | `id` | none direct | `startup_id` | `/analyze` pipeline | `get_analyses`, `get_analysis_by_id` | `save_analysis` | Public profile, `FounderStartupWorkspaceView`, Rankings | Yes | No | No | No |
| `score_history` | Legacy V2.1 trend line only (confirmed: no V3/SPS field exists on this table) | `id` | none | `analysis_id` → `startup_id` | Every analysis save (legacy path) | `SPSHistory.tsx` | `save_analysis`'s legacy write | Public profile's "V2.1 Score (legacy)" chart | Partially — real data, stale methodology | No | Yes — a fossil of the V2.1 era | Eventually, once migrated to track V3 or explicitly retired for low-coverage cases |
| `venture_financial_snapshots` | Actual financial state, append-only | `id` | via `modeled_ventures.user_id` | `venture_id` | Finance "Add your finances" | Finance tab, Fundraising pre-fill | Finance save | `FinanceOverview.tsx` | Yes | No | No | No |
| `venture_hire_plans` / `venture_financial_plans` / `venture_financial_scenarios` | Planned changes + comparisons | `id` each | via venture | `venture_id` | Finance "Model a change" | Finance tab | Finance save/update | `FinanceOverview.tsx` | Yes | No | No | No |
| `venture_missions` | Build's own question/test/action loop | `id` | via venture | `venture_id` | Overview's recommendation engine + founder-added | Overview "What matters now," "Your Actions" | Recording a result, deciding, adding a custom action | `CurrentQuestionCard.tsx`, `MissionsSection.tsx` | Yes, for Build | **Yes — duplicates `founder_actions`'s job** | No | No |
| `venture_evidence` | Build's classified, question-linked evidence | `id` | via venture | `venture_id` | Recording a test result | Overview, History | Evidence capture flow | `CurrentQuestionCard.tsx` | Yes, for Build | **Overlaps `founder_updates`'s job, not identical (see §9)** | No | No |
| `venture_decisions` | "SIE recommended X / you decided Y" | `id` | via venture | `venture_id` | Deciding on a recommendation | Overview, History | Decision recording | `CurrentQuestionCard.tsx`, History | Yes, for Build | No direct duplicate found | No | No |
| `founder_actions` | My Startups' "Action Plan" | `id` | `created_by_user_id` (attribution only — shared per-startup, not per-member, per its own code comment) | `startup_id` | SIE recommendation "Add to Plan," or founder-created | `FounderStartupWorkspaceView` | `create_founder_action`, `update_founder_action_status` | Action Plan card | Yes, for My Startups | **Yes — duplicates `venture_missions`'s job** | No | See §8 recommendation |
| `founder_updates` | My Startups' "Recent Updates" | `id` | `created_by_user_id` | `startup_id` | "+ Add Update" | Founder Workspace "Recent Updates" | `create_founder_update` | Recent Updates card | Yes, for My Startups | Overlapping-but-distinct job vs. `venture_evidence` (see §9) | No | See §9 recommendation |
| `startup_milestones` | Founder-set milestones | `id` | `created_by_user_id` | `startup_id` | "+ Add milestone" | Founder Workspace | create/update | Milestones card | Yes | No direct Build equivalent (Build has no milestone concept) | No | No |

---

## 3. Existing data counts (local dev DB, row counts only, no user data exposed)

| Table | Count |
|---|---|
| `modeled_ventures` | 142 |
| `venture_graduations` | **1** |
| `startups` | 24 |
| `startup_memberships` | 3 |
| `startup_claims` | 6 |
| `founder_actions` | 3 |
| `founder_updates` | 2 |
| `venture_missions` | 113 |
| `venture_evidence` | 18 |
| `venture_decisions` | 7 |
| `analyses` | 88 |
| `venture_hire_plans` | 4 |
| `venture_financial_plans` | 5 |
| `venture_financial_scenarios` | 5 |
| Ventures with any Finance data | 3 |

**This materially de-risks convergence.** Only **one** venture has ever graduated in this dataset. The
`founder_actions`/`founder_updates` volumes (3 and 2 rows) are trivially small compared to `venture_missions`
(113) and `venture_evidence` (18) — confirming Build's own action/evidence loop is both the older and far
more heavily used system. Migrating or bridging the tiny `founder_*` tables is a small, low-risk operation;
the reverse would not be.

---

## 4. Identity question — Venture vs. Startup

**Why both exist today, read from the code, not assumed**: `modeled_ventures` was built first, as a private,
freely-editable "sketch" a founder owns outright (`user_id` FK, no name-uniqueness constraint — two different
users, or the same user, can each have a venture named the same thing). `startups` was built to solve a
completely different problem: **canonical, name-deduplicated identity across every Analyze run ever
performed, by anyone, for Rankings/Discovery/Compare** — `normalized_name` is `UNIQUE`, and a `startups` row
is explicitly, deliberately created **unowned** the moment anyone runs Analyze on a company, even a stranger.
Ownership (`startup_memberships`) was bolted on later as a separate concept from analysis. Graduation
(`venture_graduations`) was built later still, as the bridge — and it is exactly that: a bridge, not a merge.

**Does a modeled venture represent a fundamentally different entity?** No. It represents the *same company*,
before that company has (or wants) a public, evidence-based, name-deduplicated identity. The two tables model
two different *concerns* about one real-world company — "my own private working model of my company" vs.
"the one canonical, publicly-comparable record of this company" — not two different companies.

**What does graduation actually create?** Confirmed in code (`create_venture_graduation`,
`resolve_startup_for_graduation`): a `startups` row (if one doesn't already exist under this name), a
self-approved `startup_claims` row (`verification_method='venture_graduation'` — auto-approved because the
provenance is unambiguous, unlike a stranger claiming an Analyze-created startup), a `startup_memberships`
row, and the `venture_graduations` link row itself. **It copies zero Build data.** `fields_transferred_count`
is a purely client-side UX metric (how many fields the frontend pre-filled into the *next* Analyze form from
the venture's own description) — not a server-side data migration.

**What data stays attached to `modeled_venture`?** Everything Build has ever produced: missions, evidence,
decisions, all of Finance. Permanently, whether or not graduation ever happens.

**What does `startup_id` unlock?** Public Startup Profile, SPS/Analyze history, Fundraising Readiness,
`founder_actions`/`founder_updates`/milestones, and trust/membership semantics — none of which currently read
anything from the venture side except the one-line "graduated from your X venture" acknowledgment (confirmed:
`get_founder_startup_workspace()` calls `get_venture_graduation_by_startup()` for exactly that acknowledgment
and nothing else).

**What would break if one company concept eventually replaced both?** Concretely, today: nothing catastrophic
— actual usage of the bridge is nearly zero (1 graduation). The real risk is not breakage but scope: `startups`
rows are also created, unowned, by strangers analyzing a company they don't operate — a single "Company"
table would have to cleanly support an owned, actively-modeled row and an anonymous, evaluation-only row for
the same real-world company without conflating the two, which is precisely the job `modeled_ventures` +
`startups` + `startup_memberships` already do across three tables. Collapsing them into one entity would
either reintroduce that distinction as columns/flags on a single table (no less complexity, more migration
risk) or lose the "anyone can be Analyzed without becoming ownable" property that Rankings/Discovery/Compare
depend on today.

**Recommendation: OPTION B** — make the venture (renamed conceptually, not necessarily in the database, to
"the company's Build record") the **canonical operating identity**, and treat `startups` as the **optional
public/evaluation identity** attached to it via the existing graduation link, unowned analysis still
supported exactly as today. This is not Option D (a new Company table): it uses only tables that already
exist, changes zero schemas, and simply changes *which identity the founder's own workspace is keyed by
going forward* (their venture, continuously) versus *which identity the public sees* (the startup, once
graduated). Full reasoning for rejecting the other options is in §33.

---

## 5. Graduation audit

**Today, technically:** an idempotent, crash-safe, three-table write (startup + self-approved claim →
membership → graduation link) triggered from Build's Overview, gated by `hasPayingCustomers || hasRevenue`
(a real evidence threshold, confirmed in `resolveGraduationEligibility.ts`) for the *suggested* banner, but
also reachable manually. It does not touch, copy, or lock any Build data.

**What it should mean, product-wise:** a status change — "this company now also has a public, evidence-based
identity" — not a workspace change. A founder should keep operating in the exact same place they always have.

**Does it need to exist as a founder-visible transition?** Yes, but as a much smaller moment than today: an
acknowledgment ("RelayOps now has a public Startup Profile") rather than a doorway into a different product.

**Could graduation become a lifecycle/status change rather than a workspace change?** Yes — this is exactly
the recommended direction. The workspace a founder is in before and after should be identical; only a
"Public Profile" affordance and a trust badge should appear as new.

**Does it need a new name?** Not decided in this phase (no renames performed), but "graduation" itself
already implies exactly the wrong idea — that the founder leaves one place for a better one. Worth
reconsidering in the implementation phase that touches this, not now.

---

## 6. Second "become real" path — full audit

`readyToAnalyze` (driven by the server's own `primaryNextStep.kind === "ready_for_real_startup"`, a
*different* signal than `graduation.eligible`'s `hasPayingCustomers || hasRevenue`) renders a card whose
button calls `stashVentureDescriptionForAnalyze(description)` then `router.push("/analyze")`.

**What does it create?** Nothing by itself — it only pre-fills the Analyze input form and navigates there.
Running Analyze from that point creates (or reuses) a `startups` row via Analyze's own, completely
independent `get_or_create_startup` path — **unowned**, exactly like a stranger analyzing any public company.

**Does it create startup identity? Membership/claim state?** It creates startup identity (a `startups` row)
if one doesn't exist, but explicitly does **not** create membership or a claim — confirmed by the same
architectural rule that governs every Analyze-created startup ("analyzing a startup must never grant
membership").

**How does it overlap with graduation? Can a founder trigger both? What happens if they do?** Yes, a founder
can trigger both, in either order, and the system has **already been engineered to handle exactly this**:
`resolve_startup_for_graduation()` raises `StartupNameCollisionError` (409) if a `startups` row with this
exact name already exists and the founder doesn't already own it — surfaced today as an explicit "connect
existing startup" flow (`connected_existing_startup=True`) rather than a silent duplicate. This is a real,
handled overlap, not a naive bug — but it is still user-visible friction: a founder who analyzes their own
company first, then later graduates, has to manually reconcile two names into one record instead of the
system recognizing "this is the same company" automatically from the venture↔startup relationship.

**Which one should own startup identity creation?** Recommend: **graduation should be the only path that
creates an *owned* startup identity for a founder's own company.** "Analyze my company" should still be
freely runnable at any time (for anyone, on any company, exactly as today) but, when run from *inside* a
founder's own venture workspace on their own company, should transparently attach its resulting analysis to
that venture's own eventual startup identity (creating it via the same graduation-adjacent path, not a second
unowned one) rather than risking a same-name collision. This does not change Analyze's behavior for
evaluating other people's companies at all.

---

## 7. Workspace feature matrix

| Capability | Venture Workspace (Build) | Founder Workspace (My Startups) | Classification |
|---|---|---|---|
| Overview / what matters now | Yes — evidence-first recommendation engine | No equivalent | KEEP IN UNIFIED WORKSPACE |
| Company Intelligence State (six-category qualitative) | Yes | No | KEEP IN UNIFIED WORKSPACE |
| Questions / tests | Yes | No | KEEP IN UNIFIED WORKSPACE |
| Evidence + contradictions | Yes | No (has "Recent Updates" instead — different job, see §9) | KEEP IN UNIFIED WORKSPACE |
| Decisions | Yes | No | KEEP IN UNIFIED WORKSPACE |
| History | Yes (per-venture) | No equivalent | KEEP IN UNIFIED WORKSPACE (see §29 for what merges in) |
| Finance (actuals, hiring, plans, scenarios) | Yes | No — confirmed zero reads of any `venture_financial_*` table | KEEP IN UNIFIED WORKSPACE |
| Fundraising (SAFE/priced round simulator) | Yes | No | KEEP IN UNIFIED WORKSPACE |
| SPS + pillar breakdown | No | Yes | MOVE TO ANALYZE (accessible on demand, not the default Overview) |
| Fundraising Readiness | No | Yes | MOVE TO ANALYZE (it is derived entirely from canonical `analyses` methodology — confirmed in code — not from Finance/Fundraising at all) |
| Founder Actions | No (has `venture_missions`/"Your Actions" instead) | Yes | MERGE WITH EXISTING BUILD CAPABILITY (`venture_missions`) |
| Founder Updates | No (has `venture_evidence` instead, different semantics) | Yes | MERGE WITH EXISTING BUILD CAPABILITY, as a distinct "progress log" entry type inside one capture surface (see §9) |
| Milestones | No | Yes | KEEP IN UNIFIED WORKSPACE (genuinely has no Build equivalent today) |
| Public profile / sharing | No (Build has its own separate "Share venture snapshot," a different, pre-graduation preview) | Yes (links to `/startup/[id]`) | PUBLIC PROFILE ONLY (stays a separate surface by design, per §21) |
| Trust status (Verified / Founder-managed) | No | Yes, shown prominently | PUBLIC PROFILE ONLY, going forward (currently also shown inside the private workspace with no clear purpose there — DEFER removal of the badge itself to the implementation phase, not decided here) |
| Analyze entry | Yes (`readyToAnalyze` card) | Yes ("Re-analyze") | KEEP IN UNIFIED WORKSPACE, one coherent entry point (see §6/§22) |
| Startup metadata (name, industry from Analyze) | No | Yes | KEEP IN UNIFIED WORKSPACE, read-only display of the linked public identity |

---

## 8. Duplicate action system — `venture_missions` vs. `founder_actions`

| | `venture_missions` | `founder_actions` |
|---|---|---|
| Schema richness | Full intelligence-loop participant: question text, why-it-matters, test description, interpretation, `mission_type` taxonomy, linked evidence/decision | Simple workflow record: title, description, related_pillar, status, source |
| Statuses | Part of a recommend → test → learn → decide cycle | `todo / in_progress / completed / dismissed` |
| Ownership | `venture_id` (single-owner, matches `modeled_ventures.user_id`) | `startup_id`, explicitly **shared per-startup, not per-member** (any verified member sees/acts on the same plan — a deliberate multi-founder design point `venture_missions` doesn't need yet since ventures are single-owner) |
| Creation | SIE recommendation engine, or founder-added | SIE recommendation ("Add to Plan"), fundraising-gap-derived, or founder-created |
| Recommendation relationship | **Is** the recommendation engine's own substrate | Consumes a recommendation (from SPS pillar gaps or Fundraising Readiness gaps) as a one-time "Add to Plan" import — no ongoing loop |
| Analytics relationship | Feeds Build's own product-event history | Independent |
| Data volume (this dataset) | **113 rows** | **3 rows** |
| Migration complexity | N/A (survives) | Low — trivial row count, simple schema, one real feature (multi-member sharing) not yet present on the other side |

**Does `founder_actions` contain any behavior `venture_missions` cannot represent?** Exactly one:
**multi-member sharing** (`venture_missions` has no concept of "other people on this team" because a venture
today has exactly one owner; `founder_actions` was explicitly built to be shared across `startup_memberships`
members). Everything else — status lifecycle, SIE-sourced vs. founder-created, dedup-by-title — is either
already present in `venture_missions` or trivially representable.

**Canonical recommendation:** `venture_missions` survives, confirmed correct. `founder_actions`' one
genuinely missing capability (multi-member visibility) becomes a requirement to add to `venture_missions`
*only if/when* the venture-side ever needs to support co-founders — not a reason to keep two systems today.

---

## 9. Duplicate evidence/update system — `venture_evidence` vs. `founder_updates`

These are **not** the same concept, and the code says so explicitly (`founder_updates`' own module comment:
*"Distinct from app/models/evidence.py's Evidence model on purpose... founder_updates rows are never inserted
into methodology.evidence"*).

- `venture_evidence` is **evidence for a specific, currently-open question** — it carries a relationship
  classification (supports/mixed/contradicts/doesn't tell us yet) against that question, and directly drives
  the next recommendation.
- `founder_updates` is a **general, typed progress log** ("customer," "revenue," "product," "team,"
  "fundraising," "partnership," "validation," "operations," "other") with no question attached and no
  evidentiary weight — closer to a company changelog than a test result.

**Does `founder_updates` contain anything not representable by `venture_evidence`?** Yes: the ability to log
something that happened **without it being evidence for any specific open question** — a founder shipping a
feature, closing a partnership, or hitting a metric milestone that isn't "testing" anything in particular.
`venture_evidence` today is always tied to a mission/question; a bare, untethered "update" doesn't fit that
shape without forcing a fake question onto it.

**Recommend, honestly, not by faking equivalence:** keep both *concepts* — they answer genuinely different
questions ("what did we learn that changes our understanding" vs. "what happened, generally") — but present
them to the founder as **one capture surface** ("What happened?") that asks, only when relevant, whether this
relates to something currently being tested. If yes, it becomes `venture_evidence` (with the existing
classification step); if no, it becomes a general log entry. The 2-row volume of `founder_updates` in this
dataset means migrating existing rows into whichever new home is chosen is trivial regardless of which shape
is picked.

---

## 10. Decision/outcome continuity

Confirmed in code: **no post-graduation workflow writes to `venture_decisions` today.** Once a venture
graduates, its Build-side decision history is frozen at that moment; My Startups has no decision-recording
concept at all (only `founder_actions`' simpler status field, and `founder_updates`' log). This means a
graduated company's "why did we decide this" story silently stops being recorded the moment it becomes most
interesting (a company that's actually operating).

**Design direction:** the same `venture_decisions` (and `venture_missions`/`venture_evidence`) graph should
keep being written to indefinitely, regardless of graduation status — there should be exactly one decision
history for a company's entire life, not a pre-startup one and a post-startup one. This falls directly out of
recommending `modeled_ventures` remain the canonical operating identity (§4) — nothing needs to change about
these tables' schemas for this to be true; graduation simply needs to stop being treated as an exit from the
workspace that writes to them.

---

## 11. Finance ownership

Confirmed: every Finance table (`venture_financial_snapshots`, `venture_hire_plans`, `venture_financial_plans`,
`venture_financial_scenarios`) is keyed by `venture_id`, and `get_founder_startup_workspace()` reads none of
them. **Finance continues working after graduation** (nothing about graduation touches or locks it) but
**Founder Workspace cannot currently see it at all.**

**Does `startup_id` need Finance data?** Not structurally — Fundraising Readiness and SPS don't consume
financial actuals today (confirmed: `assess_fundraising_readiness` reads only the `analyses` methodology
JSONB). The *product* value of connecting them (a defensible score that also knows the real runway) is a
separate, future question explicitly out of scope here (Phase 36's own P1 finding, not this phase's job).

**Should Finance remain attached to the persistent company workspace identity, not lifecycle status?**
**Confirmed, validated.** This is the safest and only architecturally consistent answer: Finance was built
venture-scoped from day one (35B), has three phases of verified-correct math on top of that scoping, and
`modeled_ventures` is recommended as the canonical operating identity anyway (§4). Moving it to `startup_id`
would (a) break it for every venture that hasn't graduated — the overwhelming majority, 142 vs. 1 — and (b)
gain nothing, since nothing currently reads Finance via `startup_id` regardless.

---

## 12. Fundraising ownership

The SAFE/priced-round **simulator** persists nothing (confirmed unchanged from every prior phase's audit,
re-verified this phase by reading `FundraisingSimulator.tsx`'s own architecture comments) — it is entirely
ephemeral client-side state, `venture_id`-scoped only in the sense that its one read (Finance pre-fill) is
keyed by the venture. Founder Workspace exposes none of it.

**"Fundraising Readiness" is a completely different thing that happens to share a word.** Confirmed in code
(`app/ai/fundraising_readiness.py`'s own extensive module docstring): it is a deterministic function of
**confidence × evidence coverage of the canonical Analyze/SPS pillar data**, stage-weighted — "how defensible
is this score," not "what does the evidence show." It reads zero Finance data and zero Fundraising simulator
data. It is architecturally an **Analyze-family artifact**, not a Fundraising-family one.

**Recommended naming/placement boundary:** keep Fundraising Readiness's actual mechanism exactly as-is (it is
well-designed and genuinely useful), but its future home should sit next to Analyze/SPS in the unified
workspace, not next to the Fundraising simulator — the shared word "Fundraising" between two unrelated
systems is the entire source of confusion, not the underlying logic of either.

---

## 13. SPS ownership — future boundary

Confirmed present in exactly three places: the public Startup Profile, Founder Workspace's own Overview
(prominently, at the top), and Analyze's own results screen (the same data, freshly computed). Not currently
in Rankings' own per-row display beyond the sortable score column (unchanged, out of scope).

**Future rule, validated against the repository**: SPS is an *Analyze* capability — an evaluation of a
company from available evidence — and should never be the founder's own default operating view. The
directive's own suggested pattern is directly supported by what already exists: `analyses`/`score_history`
are already `startup_id`-scoped and already computed independently of any operating-workspace state, so
"Analyze → View latest company analysis → SPS + pillars + confidence + evidence coverage" is a *presentation*
change (where SPS is shown, and with what prominence), not a data-model change.

---

## 14. Fundraising Readiness score — verdict

**KEEP**, relocate in the eventual IA per §12. It is not redundant, not legacy, not actively confusing at the
*mechanism* level — it is a well-documented, deterministic, genuinely different lens than SPS itself
(confidence/coverage-weighted rather than score-weighted), and it explicitly does not duplicate the
now-superseded LLM-based `readiness_score.py::generate_readiness_score()` (a different, older, still-partially-
alive legacy concept whose only remaining live consumer is the "Executive Coaching Summary" text — worth its
own future look, not conflated with Fundraising Readiness here). Its confusion is entirely about *where it's
shown and what it's named next to* (the Fundraising simulator), not about its own design.

---

## 15. Trust state audit

| Surface | Trust language shown | Matters? |
|---|---|---|
| Public Startup Profile (`/startup/[id]`) | "Verified" / claim status | **Yes — this is the entire point.** A public viewer or investor needs to know whether the person operating this profile is who they claim to be. |
| Investor/diligence context | Same | **Yes**, for the same reason. |
| Private Founder Workspace (`/founder/startups/[id]`) | "✓ Verified — SIE has confirmed your relationship to this company" | **No clear purpose found.** The page's own copy says it is "private to you and your team" — the founder already knows who they are; this badge doesn't gate anything on this page, confirmed by reading the page's own component tree (no conditional rendering keyed off trust status found gating any private-workspace capability). |
| Build / Venture Workspace | None shown today | N/A — consistent with the recommendation below. |

**Every capability search performed this phase** (§16) found **zero** cases where Build capabilities —
questions, tests, evidence, decisions, Finance, Fundraising, Analyze-on-your-own-company — require anything
beyond `RequireAuth` + ownership (`user_id` match). Trust/verification gates exist **only** around
`startup_id`-scoped surfaces that are inherently about a *claim of ownership over a canonical, possibly-
public identity* (My Startups access, admin claim review) — never around the act of building, modeling,
planning, or evidencing a company a founder already, unambiguously, controls in their own venture.

---

## 16. Product access audit — gate classification

| Gate | Where | Classification |
|---|---|---|
| `RequireAuth` + `user_id` match on every `modeled_ventures`/Finance/Fundraising/evidence/mission/decision endpoint | `app/api.py`, throughout | **SECURITY REQUIRED** — correct, minimal, unrelated to trust/verification |
| `RequireStartupMember` on `founder_actions`/`founder_updates`/Founder Workspace reads | `app/api.py` | **SECURITY REQUIRED** — a startup can have multiple members; this correctly checks *membership*, not *verification status* |
| `startup_claims.status = 'approved'` required to grant `startup_memberships` (except self-approved graduation claims) | `approve_startup_claim` | **SECURITY REQUIRED** for the *stranger-claims-an-existing-startup* case — this is exactly the fraud-prevention job trust verification exists for |
| "✓ Verified" badge display inside private Founder Workspace | `FounderStartupWorkspaceView` | **TRUST DISPLAY ONLY** — shown, gates nothing found |
| Graduation eligibility (`hasPayingCustomers \|\| hasRevenue`) | `resolveGraduationEligibility.ts` | **Not a trust gate at all** — an evidence threshold for a *suggestion* banner, not an access restriction; manual graduation remains available regardless |
| Public Startup Profile's trust badge | `/startup/[id]` | **TRUST DISPLAY, and here it is the correct, load-bearing use** — this is exactly the audience for whom the distinction matters |

**No unnecessary restriction on a founder's own building/modeling/planning capability was found anywhere in
this codebase.** The one real issue is display-only: trust language appearing on a page where it doesn't
inform any decision the reader (the founder themselves) needs to make.

---

## 17. URL / routing architecture

**Current:** `/idea-lab` (My Ideas list), `/idea-lab/[id]` (Venture Workspace), `/founder` (My Startups list),
`/founder/startups/[id]` (Founder Workspace), `/startup/[id]` (public profile), `/analyze` (Analyze entry).

**Recommended future direction (not a migration plan — a target to converge toward eventually):** keep
`/idea-lab/[id]` as the one operating workspace route for a company throughout its life (it already accepts a
venture at any stage, from idea through revenue) rather than introducing a new `/build/[company]` route
purely for aesthetics — the directive's own instruction to avoid optimizing URLs for looks over migration
risk applies directly here. `/founder`'s future is answered in §18: if it survives at all, it should route
*into* `/idea-lab/[id]` for the linked venture, not to a separate template. `/founder/startups/[id]` and
`/startup/[id]` remain distinct (private operating view vs. public profile — §21), but the *operating* half of
that pair converges onto the existing venture route rather than keeping `FounderStartupWorkspaceView` as a
second template.

---

## 18. "My Startups" future

**Recommend (A): a list of founder-managed companies whose entries open the unified workspace** (i.e., the
existing `/idea-lab/[id]` for the linked venture, when one exists). Do not maintain two separate lists.
Concretely: `/founder` keeps existing as an index (it may legitimately have different filtering — "companies
I've graduated" vs. Build's full "everything I'm modeling, at any stage") but its "Enter Workspace" action
should point at the same operating workspace Build already provides, not a second template
(`FounderStartupWorkspaceView`). For the one edge case this phase's data confirms is real —a `startups` row
with membership but **no** linked `modeled_venture` (an owner who claimed an Analyze-created startup without
ever having built it in Build first, plausible given 24 startups vs. only 1 graduation) — the unified
workspace needs a graceful "no venture history yet, start building" state rather than assuming graduation
always precedes membership.

---

## 19. "My Ideas" future

Evaluated against current data (142 ventures, spanning "Idea" through "Early revenue" stage labels already
observed live) and UX: the directive's suggested reframe — one list ("All Companies" or "My Ventures") with
lifecycle labels (Exploring/Validating/Building/Operating) rather than a hard Idea-vs-Startup object split —
is well supported. The existing `stage` field on `modeled_ventures` already carries exactly this kind of
information informally (free-text stage strings observed live: "Idea," "Early revenue"); formalizing it into
one small, ordered vocabulary is a presentation and light-validation change, not a schema redesign. **No
rename performed this phase**, per instruction — this is a recommendation to validate further in
implementation, not a decision made here.

---

## 20. Lifecycle vocabulary

Overlapping fields found: `modeled_ventures.stage` (free text, e.g. "Idea," "Early revenue" — observed live),
Analyze's `company_stage`/`funding_stage` (used by Fundraising Readiness's stage-weighting), and the implicit
"graduated / not graduated" boolean from `venture_graduations`. These are three different axes today (maturity
self-report, external funding-round terminology, and a binary identity flag) collapsed by founders into one
mental "how far along am I" question.

**Recommended founder-facing vocabulary (not implemented): Exploring → Validating → Building → Operating** —
a single, ordered, founder-facing progression that a `modeled_venture` moves through continuously, with
"has a public Startup Profile" as an *independent*, optional flag (not a lifecycle stage) that can be true
at any point from Validating onward. This directly avoids requiring a founder to understand "Idea object vs.
Venture object vs. Startup object" — they only ever need to understand where their one company currently
stands.

---

## 21. Public profile boundary

The public Startup Profile (`/startup/[id]`) is correctly, and should remain, a **separate surface** from the
private operating workspace — it displays SPS, evidence coverage, trust status, and a coaching-style summary
aimed at an external viewer, none of which belongs inside a founder's own private evidence loop. The
recommended convergence (§4, §7) does not touch this boundary at all: it only asks that the *private* side
stop being needlessly split into two products. Sharing/privacy controls for the public profile stay exactly
where they are.

---

## 22. Analyze-my-company — future behavior

**Founder operates in the unified workspace → optionally chooses "Analyze my company" → SIE runs the Analyze
methodology → the result becomes an evaluation artifact attached to the company's (existing or newly linked)
`startups` row → it does not replace or overwrite Build state, evidence history, Finance, or the
recommendation engine.**

**Data flow that can safely happen:**
- **BUILD → ANALYZE**: the venture's own description/assumptions may pre-fill the Analyze input form (as
  today, via `stashVentureDescriptionForAnalyze`) — this is founder-supplied text becoming founder-supplied
  text elsewhere, not a factual claim crossing a trust boundary.
- **ANALYZE → BUILD**: nothing should flow automatically. An Analyze result is Analyze's own, separately
  evidenced conclusion; Build's recommendation engine should not silently treat "SPS says Product is weak" as
  equivalent to a founder-recorded piece of evidence. A founder could manually choose to record "SIE's
  analysis flagged X" as their own new evidence entry (a deliberate, founder-initiated action, exactly like
  any other self-reported fact today) — never an automatic write.

---

## 23. Hypothetical-data protection rules (explicit)

1. Finance scenarios, hire plans, and planned revenue/expense changes **never** write to
   `venture_financial_snapshots` (unchanged, already enforced, re-verified this phase by re-reading the
   Finance code paths — no new risk introduced by this architecture).
2. Fundraising simulator inputs/outputs **never** persist anywhere, and specifically never reach
   `venture_financial_snapshots` or any `analyses` row (unchanged).
3. Build's own assumption fields (`modeled_ventures.assumptions`, explicitly labeled "What you believe... not
   observed evidence") must never be read as if they were Analyze evidence — they already carry a distinct
   provenance tag (`user_provided`/`ai_inferred`) that Analyze's own evidence model does not share, and no
   code path found this phase converts one into the other automatically.
4. **New rule this architecture must enforce going forward**: an Analyze result attached to a company via the
   unified workspace must never automatically become a `venture_evidence` row, a `venture_decision`, or a
   `venture_missions` recommendation input — only an explicit, founder-initiated action may create that link
   (§22).

---

## 24. Data migration / compatibility strategy

**No deletion, ever, without a separate future decision.** For every existing system:

- `startups`, `startup_memberships`, `startup_claims`: unchanged — these are the correct, permanent identity
  and trust tables regardless of which option is chosen.
- `founder_actions` (3 rows): dual-read during transition — the unified workspace reads both
  `venture_missions` (for graduated ventures with a linked history) and any remaining `founder_actions` rows
  for startups with **no** linked venture (the "claimed without ever building" edge case from §18), never
  silently dropping either. A one-time backfill can copy the 3 existing rows into `venture_missions`-shaped
  entries **only** for startups that do have a linked venture; the handful with no venture link keep their
  `founder_actions` rows readable indefinitely (dual-read, not deleted) until a future phase explicitly
  retires the table.
- `founder_updates` (2 rows): same dual-read/backfill pattern, tagged as "imported historical update" rather
  than reclassified as `venture_evidence` (per §9 — never fake equivalence).
- `analyses`, `score_history`: unchanged — these already correctly live independently of the operating
  workspace.
- `venture_graduations` (1 row): unchanged schema; its *meaning* shifts from "workspace transition" to
  "public-identity link," but the row itself needs no migration.
- `modeled_ventures` and all Build tables: unchanged, zero migration — they are the tables the recommended
  architecture keeps canonical.
- Legacy routes (`/founder/startups/[id]`): kept alive with a redirect to `/idea-lab/[id]` for the linked
  venture once that convergence ships, never a hard 404, so no existing bookmark/share link breaks.

**Rollback:** every step above is additive or redirect-based; nothing proposed here requires an irreversible
schema change, so rollback at any phase is "stop reading the new source, resume reading the old one" — no
data is put in a state only the new code path can interpret.

---

## 25. Blank venture-name defect — root cause and future fix

**Root cause, confirmed by re-reading the review-step component this phase**: the "What's your venture
called?" field is a plain controlled input with no `required` validation and no non-empty check gating the
"Create Venture" button's `disabled` state — the button's enablement was never wired to the name field's
value at all, only to whether the AI-structuring step had completed. Clearing the field after the AI
correctly pre-filled it leaves the button fully clickable, and `create_modeled_venture` itself has no
NOT-NULL-content constraint beyond `NOT NULL` at the SQL level (an empty string satisfies `NOT NULL`).

**Future fix (for the implementation phase, not built here):**
- **Frontend**: disable "Create Venture" when the trimmed name is empty; if a name was previously
  AI-suggested and then cleared, restore the suggestion or show inline "a name is required" rather than
  silently accepting blank.
- **Backend**: add a real validation rule (non-empty, trimmed, reasonable max length) to the venture-creation
  request model, returning 422 rather than accepting whitespace-only names — defense in depth, since the
  frontend fix alone doesn't protect a direct API call.
- **Existing damaged records**: do not auto-rename. Surface a one-time, dismissible prompt on any venture
  still literally named "Untitled venture" ("Give this venture a name") the next time its owner opens it —
  never silently rewrite a founder's own data without their action.

---

## 26. Low-coverage SPS false precision — disposition

Confirmed, live, in Phase 36: a "Coverage 5% / Not enough evidence yet" banner alongside a full six-pillar
numeric breakdown and a "V2.1 SCORE (LEGACY)" number. **Founder Workspace convergence naturally reduces this
problem's blast radius on the founder's own experience**, because SPS stops being the founder's default
Overview (§13) — a founder building their own company will encounter this only when they deliberately choose
"Analyze my company," where some amount of "this is still evaluation, not certainty" framing is already
expected. It does **not** fix the underlying issue for a public viewer or investor looking at a low-coverage
company's public profile, which is unaffected by workspace convergence entirely. **Recommend a separate,
future Analyze-hardening phase** to decide whether low-coverage companies should suppress the pillar
breakdown and legacy score entirely rather than merely labeling them — explicitly not solved here, per this
phase's own instruction not to redesign SPS.

---

## 27. Legacy/dead code impact classification

| Component/system | Classification |
|---|---|
| `FounderStartupWorkspaceView` and its child components | **REQUIRED DURING MIGRATION** (it's the live template for every current My Startups visit) → **SAFE TO RETIRE AFTER CONVERGENCE**, once the unified workspace fully covers its jobs |
| `founder_actions` UI components | **REQUIRED DURING MIGRATION** for the no-linked-venture edge case (§18) → **SAFE TO RETIRE** once that edge case is otherwise handled |
| `founder_updates` UI components | Same as above |
| Fundraising Readiness surface | **STILL LIVE ELSEWHERE** — relocates (§12/§14), does not retire |
| Dead VPS UI (`VPSResultPanel.tsx`, `vps_guidance.py` output) | **SAFE TO RETIRE** independent of convergence — already fully dead per Phase 36's own code-level confirmation, zero relationship to this convergence work |
| `WhatIfPanel.tsx` / `ScenarioComparison.tsx` | **SAFE TO RETIRE** independent of convergence, same as above |
| `generate_guidance()` output path | **SAFE TO RETIRE** independent of convergence |
| Legacy startup claim UX (manual review flow) | **STILL LIVE ELSEWHERE** — this is the correct, load-bearing path for stranger-claims-an-existing-startup and must not be touched by this convergence at all |

---

## 28. Three convergence options

### Option 1 — Bridge (recommended)

**Product behavior:** the venture workspace (`/idea-lab/[id]`) becomes the one place a founder operates their
company, at every lifecycle stage. Graduation stops being a workspace transition and becomes a status flag
plus a public-profile affordance. My Startups becomes an index that opens the same workspace.
**Canonical entity:** `modeled_ventures` (Option B from §4).
**Database impact:** none — zero schema changes. Only new *read* paths (the unified workspace additionally
reads `startups`/`analyses`/trust status when a graduation link exists) and new, additive dual-read handling
for the `founder_actions`/`founder_updates` edge case.
**Migration complexity:** Low. No destructive migration; a small backfill for 3 + 2 rows.
**Frontend impact:** Moderate — `FounderStartupWorkspaceView`'s unique capabilities (SPS display, Fundraising
Readiness, Action Plan, Recent Updates, Milestones) get either relocated into the venture workspace as new
sections or replaced by the equivalent Build capability; the template itself is retired after convergence.
**API impact:** Additive endpoints only (venture workspace needs to read `startups`/`analyses`/trust for a
linked venture); no existing endpoint needs to change behavior.
**Backward compatibility:** High — old `/founder/startups/[id]` URLs redirect; nothing is deleted during the
transition.
**Risk:** Low-to-moderate — the main risk is scope creep in "how much of Founder Workspace's UI moves into
Build's Overview vs. becomes a secondary tab," not data risk.
**Benefits:** Directly solves the P0 from Phase 36 with the smallest possible data-model change; leverages
that graduation is barely used (1 row) so there's almost no existing "post-graduation" experience to disrupt.
**What retires:** `FounderStartupWorkspaceView`, `founder_actions`/`founder_updates` as primary systems (kept
readable during migration).
**What survives:** everything in `modeled_ventures`'s own tree, `startups`/`startup_memberships`/
`startup_claims`, `analyses`/`score_history`, public profile.

### Option 2 — Startup-canonical

**Product behavior:** flip the direction — make `startups` the canonical operating identity, and migrate
`modeled_ventures`' own data (missions, evidence, decisions, Finance) to be `startup_id`-scoped instead,
auto-creating a `startups` row for every venture immediately (even idea-stage, pre-graduation) rather than
only at graduation.
**Canonical entity:** `startups` (Option C from §4).
**Database impact:** High — every Build table (`venture_missions`, `venture_evidence`, `venture_decisions`,
all four Finance tables) would need a new `startup_id` column, a backfill for **142 existing ventures** (only
1 of which currently has a `startups` row at all), and a decision about `normalized_name` uniqueness for the
141 that don't.
**Migration complexity:** High.
**Frontend impact:** High — every Build API call and component currently keyed by `venture_id` changes key.
**API impact:** High — nearly every Build endpoint's routing/ownership check changes.
**Backward compatibility:** Low without a long dual-key transition.
**Risk:** High, for a large migration whose main justification (name-based public dedup) doesn't need to
apply to a venture that has no public presence yet.
**Benefits:** A cleaner "everything is a startup" story if the product ever wants every venture to be
publicly discoverable from creation — not a goal stated anywhere in this phase's brief.
**What retires:** `modeled_ventures` eventually.
**What survives:** `startups` and its whole existing tree, unchanged in spirit.
**Rejected because:** it inverts the far larger, far more actively-used system (142 ventures, 113 missions,
18 evidence rows) to fit the far smaller, far less-used one (1 graduation), and it forces every idea-stage
venture to acquire a public, name-deduplicated identity it doesn't want or need yet.

### Option 3 — New canonical Company entity

**Product behavior:** introduce a new `companies` table; both `modeled_ventures` and `startups` become
child/adjacent records pointing at it.
**Canonical entity:** a new `Company` (Option D from §4).
**Database impact:** Highest — a new table, a backfill mapping every existing venture and startup to a new
company row (including resolving the ambiguous cases where a venture and a startup for "the same" company
exist without a `venture_graduations` link between them, which — per this phase's own count — is likely most
of the 24 startups, since only 1 has a confirmed graduation link), and every downstream query touching either
table needs a new join.
**Migration complexity:** Highest.
**Frontend/API impact:** Highest — a third identity concept now needs representing everywhere.
**Backward compatibility:** Requires the most extensive compatibility shimming of the three options.
**Risk:** Highest, and for the least proven benefit.
**Benefits:** Theoretical architectural symmetry.
**What retires:** Nothing directly; adds a layer on top of everything.
**What survives:** Everything, but nothing simplifies.
**Rejected, per the directive's own explicit skepticism of this option**: it is exactly the kind of
"architecturally elegant but not repository-justified" design the phase asks to be wary of. Nothing in the
actual data (142 ventures, 1 graduation, 24 startups mostly ungraduated) demonstrates a real need for a third
identity layer — `modeled_ventures` already *is* the operating company record; introducing a fourth table to
sit above both existing identities would solve a problem the repository doesn't currently have.

---

## 29. Recommended architecture: Option 1 (Bridge)

**Canonical company entity:** `modeled_ventures` — the founder's continuous operating record, from idea
through revenue through fundraising, unchanged in schema.

**What happens to `modeled_ventures`:** nothing — it becomes explicitly, permanently canonical rather than
implicitly so.

**What happens to `startups`:** unchanged in schema and in its existing job (canonical public/evaluation
identity, still creatable unowned by anyone running Analyze on any company). Its *product* role narrows to
exactly that — evaluation and public identity — and stops being asked to also serve as an operating
workspace.

**What happens to `venture_graduations`:** unchanged in schema; its product meaning shifts from "workspace
transition" to "this venture now also has a public Startup Profile."

**What happens to `founder_actions`:** dual-read during migration (§24), retired as a primary system once the
unified workspace's action list (`venture_missions`) covers every startup that has a linked venture; kept
alive, unmodified, for the no-linked-venture edge case until a later phase addresses that case explicitly.

**What happens to `founder_updates`:** same treatment as `founder_actions`, surfaced in the unified workspace
as a distinct "general update" entry type alongside (not merged into) evidence, per §9.

**What happens to `startup_memberships`/`startup_claims`:** unchanged — remain the correct trust/ownership
tables, now consumed *by* the unified workspace (to know whether a public profile/trust badge exists for this
venture's linked startup) rather than gating a separate workspace.

**What happens to SPS/`analyses`:** unchanged in schema; relocates in presentation to an on-demand "Analyze"
section inside the unified workspace (§13) rather than dominating the default Overview.

**What happens to Finance:** unchanged — stays on `venture_id`, confirmed safe (§11).

**What happens to Fundraising:** unchanged — stays ephemeral, `venture_id`-scoped for its one Finance-read
(§12); Fundraising Readiness relocates in presentation only, next to Analyze rather than next to the
simulator.

**What happens to the public Startup Profile:** unchanged, remains a fully separate surface (§21).

---

## 30. Unified workspace information architecture (product level, not pixel-level)

Given the existing capabilities (already verified live and in code across Phases 34–36), the smallest
intuitive structure a founder needs weekly:

- **Overview** — what matters now, why, what changed, current financial context where relevant, next action.
  (Unchanged from Build's own current Overview in spirit; §31 for hierarchy.)
- **Finance** — unchanged, exactly as it exists today.
- **Fundraising** — unchanged, exactly as it exists today.
- **History** — one continuous timeline, surviving graduation (§32).
- **Analyze** — new section (not a new system): "View latest company analysis" → SPS, pillars, confidence,
  evidence coverage, Fundraising Readiness — plus, if a public profile exists, a link to it and its trust
  status. This is where My Startups' unique capabilities live on, relocated rather than duplicated.

No new top-level area is introduced. "Validate / Decisions" as a separate tab (floated as a possibility in
the directive) is not recommended as a *new* tab — Build's existing Overview already carries this job live
today (questions, tests, evidence, decisions all appear there); splitting it into a separate tab would be
new complexity the current, working design doesn't need.

---

## 31. Overview future — hierarchy

Confirmed by this phase's own repeated live testing: what matters now / why / next action already **is** the
right hierarchy (Phase 34E's own prior work, re-validated). The recommended change is exclusion, not
addition: SPS, pillar dashboards, and Fundraising Readiness must **not** appear here by default — they move
to the new Analyze section (§30) and surface on Overview, at most, as a small, optional "last analyzed
[date], view →" pointer, never as the page's own headline number.

---

## 32. History future — one timeline

Recommended founder-facing event types for one continuous timeline, spanning the company's whole life:
venture created; question selected; test completed; evidence recorded; decision made; outcome recorded;
financial snapshot recorded; plan created/reconciled; fundraising modeled; company stage changed; **Analyze
run completed** (new — currently invisible to Build's own History); **public profile created** (new — the
former "graduation," reframed per §5); **verification/trust status changed** (new). Not all of these need new
tables — `venture_missions`/`venture_evidence`/`venture_decisions`/Finance tables already produce most of
this; "Analyze run completed" and "public profile created/trust changed" are the only genuinely new event
sources, and both already have a durable row to read from (`analyses.created_at`, `venture_graduations.
created_at`, `startup_claims`'s own status/timestamps) — no new generic event table is needed.

---

## 33. Implementation sequence (small, independently testable, rollback-safe phases)

- **37B — Identity + routing bridge + blank-name fix.** Wire the unified workspace to read `startups`/
  `analyses`/trust status for a venture's linked graduation (additive reads only); add the redirect from
  `/founder/startups/[id]` to the linked venture; fix the blank-venture-name defect (frontend + backend
  validation) per §25. No data migration.
- **37C — Founder Workspace capabilities relocate into Build.** Add the "Analyze" section (§30) to the
  venture workspace showing SPS/pillars/confidence/Fundraising Readiness for a linked startup. Still
  additive; `FounderStartupWorkspaceView` stays live in parallel.
- **37D — Retire duplicate actions/updates.** Dual-read `founder_actions`/`founder_updates` into the unified
  workspace's own equivalents for ventures with a linked graduation; backfill the (very small) existing rows;
  keep the no-linked-venture edge case on the old tables.
- **37E — Graduation UX convergence.** Reframe graduation as a status/public-profile moment rather than a
  workspace transition; retire the `/founder` index's separate template in favor of opening the unified
  workspace.
- **37F — Cleanup.** Retire `FounderStartupWorkspaceView` and its now-unused child components once 37B–37E are
  confirmed stable; separately, and independently of this whole sequence, retire the already-fully-dead VPS/
  What-If/`generate_guidance` code identified in Phase 36 and re-confirmed here (§27) — unrelated cleanup that
  can happen at any time.

Every phase above is additive-only until 37F, and 37F itself only removes code already proven, by this
phase's own repository read, to have zero remaining live dependents.

---

## 34. Migration invariants

No existing founder loses access to a company. No evidence row is lost. No decision row is lost. No Finance
history is lost. No analysis/SPS artifact is lost. No public profile URL breaks without a redirect. Trust
status is preserved exactly as recorded. Hypothetical Finance/Fundraising data never becomes factual Analyze
data (§23). Graduated ventures retain their entire pre-graduation history (already true today — nothing
proposed here changes it). No duplicate company records are accidentally created (§6's collision handling
already exists and must be preserved, not bypassed).

---

## 35. Risks

**Highest-risk phase: 37E (graduation UX convergence)** — the only phase in the sequence that changes a
founder-visible behavior (what happens when they graduate) rather than only adding new reads; must be tested
against the one real existing graduation record plus fresh test cases before shipping.

**Biggest product risk:** relocating too much of Founder Workspace's UI into Build's Overview and
recreating the same "score dominates the operating view" problem this whole convergence exists to fix — the
Analyze section must stay secondary by construction (§31), not just by initial intent.

**Biggest data-migration risk:** the no-linked-venture edge case (a `startups` row with membership but no
`venture_graduations` row) — this phase's data suggests it affects the majority of the 24 startups (since
only 1 has a confirmed graduation link) and needs its own graceful unified-workspace state (§18), not an
assumption that every My Startups entry has Build history to show.

**Biggest authorization risk:** none identified as new — every access check audited this phase (§16) is
already correctly scoped; the convergence adds read paths, not new write/access surfaces, so it does not
introduce new authorization complexity if implemented as additive-only through 37D.

**Biggest UX risk:** founders mid-migration seeing two slightly different "action list" or "update log" UIs
depending on whether their startup has a linked venture — mitigated by the dual-read design ensuring the
*content* is consistent even before the UI itself fully converges.

---

## 36. Phase 37B — Implementation (Company Identity + Workspace Routing Bridge)

Phase 37B implemented the first slice of §33's sequence: identity continuity between startup identity and
the existing Venture Workspace, plus the blank-venture-name fix. Nothing from §7 (Founder Workspace's SPS/
Fundraising Readiness/founder_actions/founder_updates capabilities) was moved. No schema changed.

### 36.1 Bridge implementation

Confirmed, before writing any code (per §5's own instruction), that `venture_graduations` already bridges
`venture_id` → `startup_id` exactly as §4's audit described, and is sufficient on its own — **no new mapping
table was added**. One new, small, reusable resolution function was added:
`resolve_linked_venture_for_owned_startup(user_id, startup_id) -> int | None` (`app/database/db.py`),
implementing the canonical rule from the architecture doc's own §6 exactly: authorize via the caller's
already-established startup membership (unchanged, still `RequireStartupMember`), look up
`venture_graduations` for this `startup_id`, and only return a `venture_id` whose `modeled_ventures.user_id`
matches the caller. No company-name matching, no "latest venture," no inference — confirmed by the function's
own single SQL statement having no other predicate available to fall back on.

This single function backs both consumers: `GET /founder/startups/{startup_id}` (one row, added as a new
`linked_venture_id` field on `FounderStartupWorkspace`) and `GET /me/startups` (batched, via the identical
ownership-checked JOIN predicate inlined directly into `get_startup_memberships_for_user()`'s own query,
rather than N calls to the singular function — avoiding the N+1 the directive's own §23 warned against).

### 36.2 Authorization behavior

Fail-closed, verified by a new, deliberately adversarial test
(`test_case_h_and_i_a_co_members_venture_is_never_resolved_for_a_startup_they_share`): a second user granted
a legitimate, independent `startup_memberships` row on a startup that a *different* user's venture graduated
into never resolves that venture's id — `linked_venture_id` comes back `None` for them specifically, while
the actual owner's own resolution is confirmed unaffected. No new authorization surface was introduced;
`RequireStartupMember` and venture-ownership checks are exactly as they were.

### 36.3 Routing behavior

- **My Startups** (`FounderHome.tsx`): each row's `Link href` is chosen directly from
  `membership.linked_venture_id` — `/idea-lab/{id}` when present, the unchanged `/founder/startups/{id}`
  otherwise. One mapping, no second button, no founder-facing "linked"/"legacy" language.
- **Direct/legacy URL** (`FounderStartupWorkspaceView.tsx`): on load, if the workspace response's own
  `linked_venture_id` is present, the page calls `router.replace()` into the Venture Workspace instead of
  rendering the Founder Workspace UI at all (the loading skeleton is shown through the redirect, so there is
  no flash of the old view first). An unlinked startup's `linked_venture_id` is `null` and this is a no-op —
  the page renders exactly as it did before this phase.

### 36.4 Legacy fallback (no-link edge case)

Unchanged: `FounderStartupWorkspaceView`, `founder_actions`, `founder_updates`, and every other Founder
Workspace capability remain fully intact and are the ones actually reached whenever
`resolve_linked_venture_for_owned_startup()` returns `None`. Nothing about this phase alters that path's
behavior in any way — confirmed by `test_case_g_unlinked_owned_startup_reports_no_link` and by
`test_workspace_for_non_graduated_startup_has_no_provenance` (pre-existing, still passing unmodified).

### 36.5 Blank-name fix

**Root cause** (frontend): `VentureDraftReview.tsx`'s naming gate tracked a one-time `"decided"/"undecided"`
flag that, once flipped to `"decided"` (by an AI-prefilled name, or by typing anything at all, including
later clearing it), never flipped back — so clearing a previously-good name left `canCreate` `true` with no
real name behind it. Reproduced and fixed: the gate is now recomputed live from the *current* trimmed name
value plus a separate, explicit `saidNoNameYet` flag that only the "I don't have a name yet" button sets.
Clearing any name — typed, AI-prefilled, or otherwise — now correctly re-disables "Create Venture" and
re-shows an inline **"Give your venture a name before continuing."** message, not just a disabled button with
no visible reason.

**Root cause** (backend): `CreateVentureRequest`/`UpdateVentureRequest`'s `name` field already had
`min_length=1` (rejecting a bare `""`), but nothing rejected a whitespace-only string (`"   "` satisfies
`min_length=1`). Fixed with one shared `field_validator` (`_require_real_venture_name`, `app/models/
idea_lab.py`) on both request models: strips the value, raises `ValueError` (→ 422) if empty after
stripping, otherwise returns the trimmed value for persistence.

### 36.6 Existing unnamed ventures

Investigated before building anything new, per §4's own explicit off-ramp. Finding: the venture-name
defect never actually persisted a truly blank name — `VentureDraftReview.tsx`'s own `handleConfirm` already
substituted the literal string `"Untitled venture"` whenever the trimmed input was empty, so every affected
record has a real, non-blank (if unhelpful) name string, not a null/empty one. Two consequences: (1) these
records are **not** blocked by anything new here — they remain fully readable and editable, since a
non-blank `UpdateVentureRequest.name` value passes the new validator without issue; (2) the one genuinely
"identity-sensitive" moment (creating a *public* Startup Profile) is **already** gated by a real, working,
independent non-blank check — `GraduateVentureReview.tsx`'s own `companyName` field, pre-filled from the
venture's name but separately editable, with its own `canSubmit = companyName.trim().length > 0`. A founder
graduating an "Untitled venture" record sees exactly that string pre-filled in the graduation form and can
fix it right there before creating a public identity. Building a *second*, new remediation surface on top of
an already-working gate would have materially expanded this phase for no protective benefit it doesn't
already have — so, per the phase's own explicit permission, no new legacy-repair UI was built.

### 36.7 Graduation redirect

**Before**: a successful `POST /ventures/{id}/graduate` navigated the founder to `/analyze?startup_id={id}`
— out of the Venture Workspace, into a different flow, before they ever saw an acknowledgment in place.

**After**: `submit()` (`VentureGraduation.tsx`) no longer navigates anywhere. It re-fetches the venture's own
graduation status in place, which flips the already-existing `VentureGraduationBanner` into its `graduated`
branch — *"You're now building [name] as a startup"* with an "Open Founder Workspace →" button — directly on
the same Venture Workspace page the founder was already looking at. No new component, no new copy invented:
the existing banner already said exactly the right thing; it simply never got the chance to render before the
old code navigated away first. Clicking "Open Founder Workspace →" now correctly bounces straight back into
this same Venture Workspace, since the startup it opens is, by construction, linked.

### 36.8 Startup creation / deduplication

Untouched. `resolve_startup_for_graduation()`, its name-collision detection (`StartupNameCollisionError`),
and the existing "connect existing startup" flow were not modified in any way — confirmed by the full,
unmodified `test_venture_graduation.py` collision/idempotency test group (12 tests) still passing.

### 36.9 Second "Analyze My Startup" path

Not solved in 37B, per its own explicit scope. Confirmed unchanged and confirmed **not made worse**: Analyze's
`get_or_create_startup()` path still never creates a `venture_graduations` row, never grants membership, and
still cannot itself produce a `linked_venture_id` for anyone (only an actual graduation can). The remaining
overlap (a founder can still reach the same company via both paths and end up needing "connect existing
startup" to reconcile them) is exactly as documented in the architecture doc's own §6, unchanged, and remains
37E's to resolve.

### 36.10 My Ideas / Build list

Verified, not changed: `list_modeled_ventures_for_user()` has no graduation-based filtering (no join to
`venture_graduations` at all), and neither does the frontend's `IdeaLabDashboard.tsx`. A graduated venture
continues to appear in My Ideas exactly as before — nothing was at risk here, so nothing was touched.

### 36.11 Live walkthrough — honest status

**Not completed via an actual browser session this phase.** The browser automation session's Clerk login had
expired/logged out by the time this phase reached its live-walkthrough step; per this session's own binding
safety rules, signing back in (any method — email, Google OAuth) is not an action Claude may perform on the
user's behalf, so the walkthrough was not forced through. This is reported plainly rather than fabricated.

In its place, the full acceptance story (Section 1/§30's own script) was verified at the API layer, through
the real FastAPI app (the same backend every live click ultimately calls), via new, purpose-built tests:
create-with-blank-name rejected, create-with-real-name succeeds, graduate, `linked_venture_id` resolves
correctly for the owner, `GET /me/startups` agrees, a legitimate co-member of the same startup never resolves
someone else's venture, an unlinked/legacy startup correctly reports no link on both endpoints. This proves
every *mechanical* claim in the acceptance story end-to-end. What it does **not** prove is the actual browser
redirect firing, the graduation banner rendering in place, or the visual "Give your venture a name" message
appearing — those remain unverified by a real click this phase and should be spot-checked live before this
phase is considered fully closed, or at the start of 37C.

### 36.12 Test matrix status

A–I confirmed via new/existing automated backend tests (see §37.13). J/K (My Startups click routing) and L/M
(direct URL redirect) are implemented and typecheck-clean but not live-verified per §37.11. N (graduation
success stays in Venture Workspace) is implemented, typecheck-clean, not live-verified. O–W are regression
claims, all confirmed via the complete, unmodified existing backend suite passing with zero failures.

### 36.13 New/updated tests this phase

- `app/tests/test_idea_lab.py`: `test_case_b_blank_venture_name_rejected`,
  `test_case_c_whitespace_only_venture_name_rejected` (plus trims-a-real-name-with-whitespace confirmation),
  `test_case_c2_blank_venture_name_rejected_on_update`.
- `app/tests/test_venture_graduation.py`: `test_case_f_linked_startup_resolves_to_correct_venture`,
  `test_case_g_unlinked_owned_startup_reports_no_link`,
  `test_case_h_and_i_a_co_members_venture_is_never_resolved_for_a_startup_they_share`.

Full backend suite (51 modules) re-run after every change: zero failures. Full frontend suite (16 scripts):
zero failures, unchanged counts. `tsc --noEmit`, `eslint`, and `next build` all clean.

### 36.14 Remaining convergence work (unchanged from the architecture doc's own §33)

37C (Founder Workspace capabilities relocate into Build as a new, additive Analyze section), 37D (retire
duplicate actions/updates via dual-read + backfill), 37E (full graduation UX convergence — the phase that
should also perform the live spot-check this phase's own §37.11 deferred), 37F (cleanup).

## 37. Phase 37C — Legacy Founder Workspace Capability Triage + Unified Workspace Integration

Phase 37C audited every visible legacy Founder Workspace capability against actual repository behavior
(not assumption), classified each A–E, and implemented the smallest useful "Analyze" surface inside the
unified Venture Workspace for a linked company. Nothing was deleted, migrated, or redesigned; the legacy
Founder Workspace remains fully intact for unlinked startups.

### 37.1 Capability audit and classification

| Capability | Classification | Reasoning |
|---|---|---|
| SPS (Startup Power Score) | B — Analyze | Read-only rendering of the existing `startup_intelligence_score`; not an operating-state concept. |
| SPS pillars / dimension breakdown | B — Analyze | Same shared, read-only components (`IntelligencePillars`/`PillarNav`/`PillarWorkspace`) already used by the public profile — reused unmodified, not duplicated. |
| Fundraising Readiness | MOVE TO ANALYZE (see §37.6) | Investigated in full (formula, backend, UI, call sites) — genuinely distinct from SPS, Build, and Finance; not a duplicate of anything. Capability kept as-is; only its entry point relocates. |
| founder_actions (Action Plan) | LEGACY ONLY (see §37.7) | Plain workflow tracking with no evidence/decision/outcome modeling; Build's own venture_missions/Current Question/decisions loop already does this job better for a linked company. |
| founder_updates (Recent Updates) | LEGACY ONLY (see §37.8) | Heterogeneous, self-reported, explicitly non-evidence (own docstring says so); Build's own capture flow (`CaptureWhatHappened`) already covers this for a linked company. |
| startup_milestones (Milestones) | LEGACY ONLY | Same reasoning and same verdict as founder_actions — plain status tracking, never touches scoring, superseded by Build's own loop for a linked company. |
| trust (Founder-managed / Verified badge) | C — Public Profile / Trust only | Already a single, reused, pure function (`resolveStartupTrustState`), rendered on the public profile only; not a private-workspace concept. |
| public profile | C — Public Profile / Trust only | Confirmed genuinely separate — reads directly from `analyses` by company name, requires zero auth, independent of both workspaces. |
| startup metadata (edit controls) | N/A — does not exist | Audited and confirmed: the legacy Founder Workspace has no startup-level settings/edit UI at all (`canonical_name` is read-only there); nothing to classify or migrate. |
| claim/membership controls (`ClaimStartupButton`/`Form`) | C — Public Profile / Trust only | Already correctly scoped to the public profile only; never rendered inside either workspace. |
| Build intelligence, Finance, Fundraising (simulator), History | A — already integrated | Confirmed unchanged, still native to the Venture Workspace. |

### 37.2 Overview protection

Confirmed by reading `VentureWorkspace.tsx`'s Overview tab content directly: it renders `VentureIdentity`,
`VentureGraduationBanner`, `CurrentQuestionCard`, the graduation-eligible "Ready to turn this into a real
startup?" card, and `CompanyIntelligenceState` — no SPS, no pillars, no Fundraising Readiness, no trust
badge. Phase 37C added nothing to this tab; the new capability lives entirely in a new, separate "Analyze"
tab (live-confirmed empty of SPS clutter — see §37.10, Test C).

### 37.3 Unified workspace IA before / after

**Before**: `Overview | Finance | Fundraising | History` (four tabs, `VentureWorkspace.tsx`'s own `TabId`
union).

**After**: `Overview | Finance | Fundraising | History | Analyze` (one new tab appended). No existing tab
was renamed, reordered, or restructured.

### 37.4 Analyze surface — what was built

One new component, `dashboard/components/idea-lab/VentureAnalyzeSection.tsx`, rendered only inside the new
"analyze" `TabPanel`:

- **startup_id resolution**: reuses `graduation.status` from the `useVentureGraduation` hook
  `VentureWorkspace.tsx` already calls once per page load (Part 17's own "no N+1" discipline) — the exact
  same ownership-checked `GET /ventures/{venture_id}/graduation` → `venture_graduations` bridge Phase 37B
  established. No new backend endpoint, no second fetch, no company-name matching.
- **No startup identity yet**: an honest inline state in `VentureWorkspace.tsx` itself ("No SIE company
  evaluation yet") with an intentional "Evaluate {venture} with SIE" button routing to the existing general
  `/analyze` flow (reusing the same `stashVentureDescriptionForAnalyze` convenience Overview's own bridge
  card already uses). Never silently creates a startup.
- **Startup identity, no canonical analysis**: `VentureAnalyzeSection` calls the exact same
  `GET /founder/startups/{id}` the legacy Founder Workspace reads, and when `methodology` is null, shows an
  honest empty state ("No SIE company analysis has been run yet") with an intentional "Analyze this company"
  link to the deterministic re-analysis path (`/analyze?startup_id={id}`) — never zeros, never a fabricated
  pillar breakdown, never an automatic run.
- **Startup identity with an existing analysis**: renders `SPSRing` (with `getOverallConfidence`, reused
  unmodified from `StartupHeroV2`), the existing `structural_coverage.partial_structural_coverage` warning
  (reused verbatim, no new confidence formula), `FundraisingReadinessCard`, `PitchDeckCoachTeaser`,
  `IntelligencePillars`, and `SPSHistory` — all pre-existing, unmodified, shared components. Footer links to
  the public profile and to re-analysis.

No new endpoint, no new score, no new AI call, no Build→Analyze data contamination (Finance/hire-plan/
fundraising-scenario data is never read by this component).

### 37.5 Public-profile-without-analysis finding

**Root cause** (confirmed by reading `get_startup_by_name()` in `app/database/db.py`): the public profile's
backing query reads directly from the `analyses` table (`WHERE ... AND methodology IS NOT NULL`), not from
the canonical `startups` table — architecturally, "Startup Profile" *is* "latest canonical analysis of this
company," full stop. A `startups` row that exists (e.g., via graduation) with zero qualifying `analyses` rows
has no query path to a profile at all; "Startup not found" is the only possible response, not a bug in the
404 handling itself.

**Acceptable?** Yes, as far as it goes — showing "not found" rather than fabricating a shell profile is
exactly this product's own honesty doctrine (never zeros, never fake pillars). The one real gap: the
identical message is shown for "no such company exists" and "this company exists but has no public content
yet," which could read as more discouraging than accurate to a founder who just graduated.

**Recommended fix**: a small, additive change — `get_startup_by_name()` falls back to a `startups`-table
lookup by canonical name when the `analyses` lookup misses, and the public profile route distinguishes "no
startup exists with this name" from "exists, not yet analyzed" with different, honest copy for the second
case. Not implemented in 37C: it touches the public-profile response contract and its frontend rendering,
which is real, if small, scope beyond a routing-triage phase.

**Recommended phase**: a dedicated public-profile phase (37E or a follow-on "profile honesty" phase) — not
37D, which is scoped to founder_actions/founder_updates migration groundwork.

### 37.6 Fundraising Readiness — verdict: MOVE TO ANALYZE

Audited in full: formula (`app/ai/fundraising_readiness.py` — deterministic, confidence × evidence-coverage
"defensibility" weighting, stage-aware, zero LLM calls, zero persistence), backend (one read-only endpoint,
`GET /founder/startups/{id}/fundraising`, reusing the existing workspace read), UI (a compact teaser card
plus one dedicated page), and its relationship to every other system:

- **Not a duplicate of SPS**: SPS measures what the evidence shows; Readiness measures how *defensible* that
  evidence is for a fundraising conversation. The module's own docstring documents a real prior duplicate
  (`readiness_score` / `generate_readiness_score()`, an ungrounded LLM re-scoring of the same pillars) that
  this module deliberately does **not** wrap or extend — that legacy field is untouched, unused here.
- **Not a duplicate of Build**: it can push gaps into the shared Action Plan (`source='fundraising_gap'`),
  but the gaps themselves come from a distinct, deterministic computation Build has no equivalent of.
- **Not a duplicate of Finance/the deterministic Fundraising simulator**: cash/runway/SAFE math is
  completely unrelated to evidence-defensibility scoring; zero shared inputs, zero shared code.
- **Does the number deserve to exist?** Yes — it answers a real, distinct founder question ("am I ready to
  raise, and what will investors push on") that nothing else in the product answers.

**Verdict**: the capability is kept exactly as-is (backend, formula, dedicated `/fundraising` page all
untouched). Only its *entry point* moves — for a linked company it now surfaces from the new Analyze tab
(alongside SPS/pillars, the other lens on the same canonical evaluation) rather than being a fixture in the
legacy workspace body. The legacy Founder Workspace's own copy of `FundraisingReadinessCard` is untouched
and still serves unlinked startups.

### 37.7 founder_actions — verdict: LEGACY ONLY

**Unique founder job, if any**: a shared, per-startup to-do list (todo/in-progress/completed), sourced from
SIE recommendations, founder-authored text, or Fundraising Readiness gaps. Compared directly against Build's
own venture_missions / Current Question / decisions / outcomes loop: founder_actions has no evidence model,
no decision model, no outcome model — it is materially thinner than what Build already gives a linked
company for "what should I do next."

**Verdict**: **LEGACY ONLY**. Not integrated into the unified workspace (would duplicate, not improve, the
weekly workflow); not retired (the table, endpoints, and legacy UI all remain fully functional for unlinked
startups, and existing rows are real history); not migrated (Section 10's own explicit prohibition on
guessing semantic equivalence between founder_actions rows and venture_missions rows — no backfill was
attempted or should be).

### 37.8 founder_updates — verdict: LEGACY ONLY

**What they actually represent**: heterogeneous, self-reported progress notes across nine free-form
categories (customer/revenue/product/team/fundraising/partnership/validation/operations/other), always
labeled "Founder reported" in the UI, explicitly stated by the model's own docstring to never be canonical
evidence and to never touch SPS/methodology.

**Verdict**: **LEGACY ONLY**. Not treated as Evidence (would contaminate `venture_evidence`'s own semantics
— explicitly forbidden). Not built into a new update system inside the unified workspace: Build's own
`CaptureWhatHappened` ("what happened") capture flow already gives a linked company an equivalent, tighter-
integrated capture surface. Existing founder_updates rows remain fully readable via the unchanged legacy
Founder Workspace for unlinked startups; nothing was migrated or backfilled.

### 37.9 Startup metadata

No editable startup-level metadata surface exists anywhere in the legacy Founder Workspace to triage —
confirmed by reading `FounderStartupWorkspaceView.tsx` in full: `canonical_name` is shown read-only in the
header/breadcrumbs only. Venture-level rename/delete already exists on the Idea Lab side
(`Rename`/`Delete venture`, unrelated to this phase). No action was needed or taken.

### 37.10 Test matrix and live walkthrough

A/B/C/D/E/F/G/H confirmed live (see below); I/K/L/M/N/O/P/Q/R/S/T/U/V/W confirmed via the complete,
unmodified existing backend suite re-run after this phase's change (144 tests across
`test_venture_graduation.py`, `test_idea_lab.py`, `test_founder_workspace.py`, `test_fundraising_readiness.py`,
`test_founder_actions.py`, `test_founder_evidence.py` — zero failures, zero backend code touched this phase).

**STATE 1 — linked, ClaimPilot (venture_id=893, startup_id=45391)**: no canonical analysis existed at the
start of this phase (a genuine, honest discovery, not a defect — confirmed via direct DB query that both
graduated/linked startups in this environment had zero analyses). Live-ran a real, intentional analysis
through the new "Analyze this company" entry point (`/analyze?startup_id=45391`, correctly pre-labeled
"Updating intelligence for: ClaimPilot — this analysis will be attached directly to ClaimPilot's existing
profile"). Once complete, the Analyze tab correctly rendered SPS Ring (68.5, C+, Medium confidence),
Fundraising Readiness (53, Developing, 2 gaps), Pitch Deck teaser, full pillar/dimension breakdown with
Public/Inferred/Unavailable evidence tags, and Score History (68.5, 1 historical analysis) — Overview
remained untouched by any of this. "View public profile" correctly opened `/startup/ClaimPilot`
independently, showing the "Founder-managed" trust badge and the same 68.5 legacy score, disambiguated from
a separately low-coverage V3 assessment on that page — confirming the public/private boundary held under a
real, freshly-created analysis.

**STATE 2 — linked, no analysis, RelayOps Graduation Test 37BA (venture_id=7616, startup_id=73091)**: the
Analyze tab correctly showed "No SIE company analysis has been run yet" with no fake SPS, no fake pillars,
and an intentional "Analyze this company" link — confirmed no automatic analysis ran merely from opening the
tab.

**STATE 3 — unlinked legacy, Retool (startup_id=13)**: the legacy Founder Workspace rendered exactly as
before (SPS 71.1, "✓ Verified" badge, What's Working/Needs Attention) with no "Analyze" tab, no redirect, and
survived a fresh reload — zero regression, confirmed untouched.

### 37.11 Defect found and fixed

One real defect surfaced live in STATE 1 and STATE 2: two text interpolations in the new
`VentureAnalyzeSection.tsx` rendered with a missing space (`"ClaimPilottoday"`, `"37BAhas"`) — a JSX
whitespace-collapse artifact (an expression immediately followed by text that wraps onto a new source line
loses its separating space unless an explicit `{" "}` is inserted, the same pattern already used correctly
elsewhere in this codebase). Fixed by adding explicit `{" "}` at both sites; re-verified live via direct DOM
`textContent` reads on both ClaimPilot and RelayOps Graduation Test 37BA after the fix, then re-ran the full
`tsc --noEmit` / `eslint` / `next build` suite (all clean) per the phase's own Defect Rule. No other code was
changed as a result.

### 37.12 Dead/legacy UI

Nothing became unreachable this phase for *unlinked* startups (the legacy Founder Workspace's own routing is
untouched). For *linked* startups, `FundraisingReadinessCard` and `PitchDeckCoachTeaser`'s renderings inside
`FounderStartupWorkspaceView.tsx` are now unreachable in practice (a linked startup always redirects away
from that view per Phase 37B), but the code itself is still load-bearing for unlinked startups and was left
in place — correctly classified "still required by unlinked legacy Founder Workspace," not dead code.

### 37.13 Remaining convergence work

37D (founder_actions/founder_updates migration groundwork, per §33 — no migration attempted or recommended
without a concrete backfill design), 37E (public-profile-without-analysis fix per §37.5, full graduation UX
convergence), 37F (cleanup of the now-unreachable-for-linked-startups renderings noted in §37.12, once 37D/E
land).

## 38. Phase 37D — Unified Workspace Simplification + Legacy Containment

Phase 37D re-confirmed 37C's legacy-containment findings from actual call sites, closed one real
linked-company containment gap 37C left open, and critically simplified the Analyze tab's rendered
experience. No data migrated, no formula/scoring changed, no new tab added.

### 38.1 Legacy systems re-audit

Confirmed by grepping every consumer, not by re-reading 37C's own conclusions: `ActionPlan.tsx`,
`Milestones.tsx`, and `RecentUpdates.tsx` are each imported by exactly one file,
`FounderStartupWorkspaceView.tsx` — which redirects away before rendering its body whenever
`linked_venture_id` is non-null (Phase 37B). No other component or page imports them. This confirms 37C's
"no founder-facing path" claim for those three specifically.

### 38.2 The gap 37C left open: Fundraising Readiness page had no containment

**Found live, not assumed**: `FundraisingReadinessView.tsx` (the dedicated `/founder/startups/{id}/fundraising`
page) had **zero** `linked_venture_id` check — unlike its sibling `FounderStartupWorkspaceView.tsx`, it never
redirected a linked company's founder away. Worse, 37C's own new `FundraisingReadinessCard` inside the
Analyze tab links directly to this exact page, meaning 37C had *added a new, reachable path* into a page that
could then let a linked company's founder click "Add to Action Plan" — a live, real write into `founder_actions`
for a linked company, contradicting 37C's own "no linked-company write path" claim.

**Fixed**: `GET /founder/startups/{id}/fundraising` already internally calls `get_founder_startup_workspace()`
(Phase 37B), which has computed `linked_venture_id` all along — exposing it on `FundraisingReadinessResponse`
required zero new queries. `FundraisingReadinessView.tsx` now carries the identical redirect-on-load pattern
`FounderStartupWorkspaceView.tsx` already uses. Live-verified: navigating directly to
`/founder/startups/45391/fundraising` (ClaimPilot, linked) now redirects cleanly to `/idea-lab/893?tab=analyze`
with no flash; the same URL pattern for Retool (startup_id=13, unlinked) renders normally with no redirect.

### 38.3 founder_actions — call sites confirmed, verdict unchanged

**Call sites**: `ActionPlan.tsx` (legacy workspace) and `FundraisingReadinessView.tsx`'s "Add to Action Plan"
button (now contained per §38.2) are the only two UI writers; `GET/POST/PATCH /founder/startups/{id}/actions`
are the only backend endpoints, gated by `RequireStartupMember`.

**Verdict**: **LEGACY ONLY**, confirmed. No unique linked-company capability found. Table, endpoints, and
legacy UI untouched; nothing migrated.

**Linked-company write path**: **NO** (was effectively YES via §38.2's gap until fixed this phase).

### 38.4 founder_updates — call sites confirmed, verdict unchanged

**Call sites**: `RecentUpdates.tsx` (legacy workspace) only. `GET/POST/PATCH /founder/startups/{id}/updates`,
gated by `RequireStartupMember`. No other consumer found.

**Verdict**: **LEGACY ONLY**, confirmed. Table, endpoints, legacy UI untouched.

**Linked-company write path**: **NO**.

### 38.5 startup_milestones audit

**What it represents**: a target/goal the startup is trying to reach (title, optional target date, optional
related pillar), with a plain status enum (planned/in_progress/achieved/cancelled) — structurally identical
in kind to founder_actions (workflow state, zero evidence/decision/outcome model), just framed as a goal
rather than a task. Confirmed via `app/models/startup_milestone.py`'s own docstring and schema. No other
canonical system reads or depends on it (confirmed: `next_milestones` referenced elsewhere in `api.py` is an
unrelated Idea Lab/VPS modeling field, not this table).

**Call sites**: `Milestones.tsx` (legacy workspace) only. `GET/POST/PATCH /founder/startups/{id}/milestones`.

**Verdict**: **LEGACY ONLY**. Same reasoning as founder_actions — Build's own evidence-first loop already
gives a linked company a richer answer to "what am I working toward." Not migrated (no proven semantic
equivalence to any Build concept); table and legacy UI untouched.

**Linked-company write path**: **NO** (inherits the same `FounderStartupWorkspaceView.tsx` redirect
protection as founder_actions/founder_updates — confirmed by the same single-consumer grep in §38.1).

### 38.6 Analyze tab — critical UX review and changes made

Reviewed the actual rendered experience live on ClaimPilot (real analysis, 68.5/C+/Medium confidence, 6
scored pillars, Fundraising Readiness 53/Developing/2 gaps) rather than assuming the 37C layout was correct
merely because everything belonged more under Analyze than Overview.

**Findings**:
- `PitchDeckCoachTeaser` was rendered in Analyze **and** already, independently, in the Fundraising tab (pre-
  existing, correct placement) — a genuine duplicate, and pure promotional clutter relative to Analyze's own
  stated job ("how does SIE evaluate this company from evidence"). **Removed from Analyze.**
- `FundraisingReadinessCard` sat directly beside the primary SPS card, before the pillar breakdown — visually
  implying equal priority with the core evaluation. **Moved to after the pillar breakdown** (secondary,
  specialized tool, not the primary answer).
- `SPSHistory` (a stat/chart of one number over time) sat inline, always expanded, immediately after the
  pillars — low information density for a company with 1-2 analyses. **Wrapped in a closed-by-default
  `<details>` disclosure**, local to this component only; the shared `SPSHistory` component itself and its
  usage on the public profile are unchanged.
- The pillar breakdown itself (`IntelligencePillars`/`PillarNav`/`PillarWorkspace`) was **already** progressive
  disclosure — one pillar expanded at a time via a left-hand nav, not six equally loud dashboards. Confirmed
  live (Market/Team/Product/Execution/Traction/Financial Health all listed, one drills in at a time). **No
  change needed.**
- The no-analysis empty-state copy said "{name} has a startup profile, but SIE hasn't evaluated it yet" —
  Section 26's exact trap: the public *profile* does not actually exist/render until an analysis exists
  (§37.5's own finding). **Fixed** to "SIE hasn't evaluated {name} yet," removing the "has a startup profile"
  claim entirely.
- One real text-rendering defect (not from this phase, carried from 37C, caught while re-reading the
  component for this review) — none found this pass; the two `{expr}` whitespace fixes from 37C were re-
  verified still correct live.

**Analyze tab before**: SPS card → [Fundraising Readiness + Pitch Deck Coach, 2-col] → pillars → SPS history
(always expanded) → footer links.

**Analyze tab after**: SPS card (evaluation state, confidence, coverage warning) → pillars (progressive
disclosure, unchanged) → Fundraising Readiness (secondary, demoted, now with an honest label clarifier —
see §38.7) → Score history (closed-by-default disclosure) → footer links (public profile, re-analyze).

### 38.7 Fundraising Readiness — second product trial

**Does it materially change a founder's decision?** Yes, evaluated honestly against the alternative of just
using SPS/confidence: it adds a *stage-weighted* reweighting of the same six pillars (a pre-seed company is
not penalized for weak Traction/Financial evidence the way a Series A company would be), a ranked, capped
list of specific evidence gaps, generated investor questions tied to those exact gaps, and a defensibility
checklist — none of which SPS, Build, or Finance provide. This is materially more actionable than a bare
confidence badge for a founder actually preparing to raise.

**Does the label match the formula?** **NO** — this is a real semantic mismatch. The formula measures how
*defensible* the current evidence is (confidence × coverage, stage-weighted) — not the odds of successfully
closing a round. "Fundraising Readiness" paired with a 0-100 score invites the stronger, incorrect reading.

**Verdict**: **KEEP SECONDARY**. Not sunk-cost — the capability itself earns its place; only its prominence
was wrong. **Label fix implemented** (Section 13's "small copy fix" path, not a rename): added one line —
"How defensible your evidence is, not your odds of raising" — under the eyebrow on `FundraisingReadinessCard`
(shared by both the unified Analyze tab and the legacy Founder Workspace, so the fix applies uniformly), and
extended the dedicated `/fundraising` page's own explanatory paragraph with "...and not the odds of actually
closing a round." Formula, backend, and endpoint untouched.

### 38.8 Pitch Deck Coach — verdict

A real, separate capability (`/analyze/deck`, its own AI-assisted coaching flow) whose teaser card is a plain,
static link with no data fetch of its own. Its actual job — "prepare pitch materials before a raise" — has
nothing to do with Analyze's job ("what does the evidence say"), and it was already correctly placed inside
the Fundraising tab (pre-37C, unmodified) as of this phase's audit.

**Verdict**: **MOVE TO FUNDRAISING** — already there; the fix was removing 37C's accidental second copy from
Analyze, not moving code.

### 38.9 SPS History — verdict

**KEEP SECONDARY**. Real value for a company with several re-analyses over time (evidence of change is a
legitimate founder question), near-zero primary value for the common one-or-two-analysis case this repository
mostly contains right now. Collapsed by default in the Analyze tab only; the underlying data, the shared
component, and its unmodified, always-visible usage on the public profile are untouched.

### 38.10 Live walkthrough

**LINKED + ANALYZED (ClaimPilot)**: Overview confirmed still clean (no SPS/pillars/readiness/trust — no
regression from 37D's own changes). Analyze tab re-verified end-to-end with the new hierarchy: SPS card
unchanged and correct, full six-pillar progressive disclosure confirmed, Fundraising Readiness card now
appears after pillars with the new clarifier line visible, Score History confirmed collapsed by default and
expands correctly on click, footer links unchanged. Direct navigation to the legacy
`/founder/startups/45391/fundraising` URL now redirects cleanly to `/idea-lab/893?tab=analyze` (§38.2's fix,
live-confirmed, no console errors).

**LINKED + UNANALYZED (RelayOps Graduation Test 37BA)**: empty state re-verified with the corrected copy —
"SIE hasn't evaluated RelayOps Graduation Test 37BA yet" (no "has a startup profile" claim), intentional
"Analyze this company" link present, no automatic analysis.

**UNLINKED LEGACY (Retool)**: legacy Founder Workspace's Action Plan, Recent Updates, and Milestones sections
all confirmed still rendering (headings present, unmodified). The dedicated `/founder/startups/13/fundraising`
page renders normally with no redirect (unlinked, as expected) and shows the updated, more explicit
"...and not the odds of actually closing a round" copy — confirming the copy fix applies universally, not
just to linked companies.

### 38.11 Responsive check — tooling limitation, honestly reported

`resize_window` to 390×844 and to 768×1024 both reported success but `window.innerWidth` read back as 2091px
regardless — the same environmental tooling limitation documented in multiple prior phases (35D-A/B, 37A,
37B-A), not a product defect. Structural reasoning in place of a live narrow-viewport screenshot: this
phase's own Analyze changes *removed* the one 2-column grid that existed in 37C's version (Fundraising
Readiness + Pitch Deck Coach side-by-side) and replaced it with a fully linear, single-column stack of cards
and a native `<details>` disclosure — strictly lower responsive risk than what shipped in 37C, which was
itself live-verified clean at a 667px viewport in Phase 37B-A's own walkthrough (the one narrow width this
tooling has reliably produced across phases). Desktop (2091px, the only width this session's tool would
actually produce) is confirmed clean via every screenshot above.

### 38.12 Regressions

Overview, Finance, Fundraising (deterministic simulator math), History, trust/access, My Startups routing,
and graduation routing were not touched this phase and were spot-checked live where a walkthrough state
already exercised them (Overview on ClaimPilot; Fundraising tab's own Pitch Deck Coach placement, confirmed
undisturbed).

### 38.13 Files changed

- `app/models/fundraising_readiness.py` (added `linked_venture_id` field)
- `app/api.py` (`get_fundraising_readiness` now passes `linked_venture_id` through, zero new queries)
- `dashboard/types/fundraisingReadiness.ts` (mirrors the new field)
- `dashboard/app/founder/startups/[startupId]/fundraising/FundraisingReadinessView.tsx` (redirect guard;
  explanatory-paragraph copy fix)
- `dashboard/components/founder/FundraisingReadinessCard.tsx` (label-accuracy clarifier line)
- `dashboard/components/idea-lab/VentureAnalyzeSection.tsx` (removed duplicate Pitch Deck Coach teaser;
  repositioned Fundraising Readiness after pillars; collapsed Score History behind a disclosure; fixed the
  no-analysis empty-state copy)

### 38.14 Dead code

Nothing newly dead this phase. `FundraisingReadinessCard`/`PitchDeckCoachTeaser`'s renderings inside the
legacy `FounderStartupWorkspaceView.tsx` remain the same "unreachable for linked, load-bearing for unlinked"
classification §37.12 already recorded — unchanged by this phase, still deferred to 37F.

### 38.15 Remaining legacy surface / 37E handoff

Legacy Founder Workspace remains a pure compatibility surface for unlinked startups — no features added, no
Build capabilities synchronized backward, per this phase's own §18 instruction. 37E inherits: the public-
profile-without-analysis fix (§37.5, explicitly deferred again this phase, not touched), full graduation UX
convergence, and eventual retirement of the now-doubly-confirmed-unreachable-for-linked-startups renderings
noted in §38.14 once a concrete 37D/37E-adjacent migration design exists (none does yet — none was built).

## 39. Phase 37E — Company Lifecycle + Public Identity Convergence

Phase 37E removed the remaining founder-facing lifecycle/identity confusion: fixed the public-profile-
without-analysis gap (37C/37D's own deferred issue), reframed "graduation" language everywhere it still
implied approval or a second workspace, removed a genuine duplicate "make this real" entry point, and
renamed "My Ideas" to "My Companies" to fix a page-title-level version of the same ambiguity already fixed
at the stage-badge level. No schema merge, no route migration, no scoring change.

### 39.1 Terminology map (as found)

| Term | Meant | Founder needs to know it? | Real lifecycle state or artifact? |
|---|---|---|---|
| Idea / Ideas (nav) | — | N/A | Already removed from primary nav (Phase 32/34A) — "Build" is the nav label |
| My Ideas (page title/breadcrumb) | The founder's own modeled ventures, any stage | Yes, but the word "Idea" implied a stage, not a collection | Artifact — renamed to **My Companies** this phase |
| Idea Stage / Validation Stage / Building Stage / Operating Stage | Real, evidence-derived maturity buckets | Yes | Real lifecycle state — already correctly implemented (Phase 34F, `lib/journey/inferVentureStage.ts`) |
| Graduate / Graduation | — | No | Pure implementation term — confirmed absent from all founder-facing copy already |
| Create Startup Profile | Create the public identity + venture_graduations bridge | Yes | Real action — term kept, description expanded (Section 13) |
| Analyze My Startup / Evaluate with SIE | Run a standalone, evidence-based evaluation | Yes | Real action — but had a genuine duplicate (Section 39.5) |
| Public Profile / Startup Profile | The public `/startup/{name}` page | Yes | Real, separate surface — boundary already correct, one honesty gap fixed (Section 39.2) |
| Verified / Founder-managed | Trust/provenance signal | Yes | Real, already correctly scoped to public/claim context (Phase 32A) — confirmed not an access gate |
| Claimed / Claim | Ownership assertion workflow | Yes | Real, already explicit about not being verification/approval (`ClaimStartupForm.tsx`'s own copy) |
| My Startups | Every startup identity the founder has live membership on (own linked companies + externally-claimed legacy ones) | Yes | Real, distinct set from My Companies — kept (Section 39.6) |

### 39.2 Public-profile-without-analysis — fixed

**Root cause** (confirmed in 37C, fixed here): `get_startup_by_name()` queried only `analyses` (`WHERE
methodology IS NOT NULL`). Fixed with a fallback: when no qualifying analysis exists, it now queries
`startups` directly by `normalized_name` (the same pre-computed, UNIQUE-constrained column
`resolve_startup_for_graduation()` already relies on for collision-free lookup — confirmed no new collision
risk, Section 19's own concern). Returns a distinct, honest shape: `has_analysis: false`, `methodology:
None`, `canonical_name` always present. A company with neither an analysis nor a `startups` row still
returns `None` (unchanged 404).

`StartupProfileResponse` gained `canonical_name: str` and `has_analysis: bool`; `methodology` became
`SIEMethodologyAnalysis | None`. The public profile page (`app/startup/[id]/page.tsx`) now renders three
distinct states: **A** (`!startup`) "Startup not found" — unchanged; **B** (`!startup.has_analysis`) a new,
minimal, honest block showing only the company's own name, Claim/Save controls, and "SIE has not analyzed
{name} yet — there is no Startup Power Score, pillar breakdown, or evidence to show"; **C** (existing
methodology) — completely unchanged rendering path.

Live-verified end-to-end on a freshly created company (FridgeChef 37E Test, `venture_id=8212`,
`startup_id=75037`): public profile showed the honest **B** state immediately after profile creation, then
correctly showed the real 60.6 SPS / pillar breakdown (**C**) after an intentional analysis — with zero
change to the venture id, Build, Finance, Fundraising, or History in between.

### 39.3 Profile creation — documented, then explained accurately

**What `POST /ventures/{id}/graduate` actually does** (read from `resolve_startup_for_graduation()` /
`create_venture_graduation()` in `app/database/db.py` before writing any copy, per Section 17): inserts (or
reuses, for "connect existing") one `startups` row, inserts one `venture_graduations` row bridging
`venture_id` → `startup_id`, and grants the founder a `startup_memberships` row (self-approved, zero human
review — unchanged from Phase 31). It does **not** run any analysis, does **not** write to `analyses`, does
**not** change `modeled_ventures` in any way Build/Finance/Fundraising/History depend on, and does **not**
touch `startup_claims` or trust state.

**Founder-facing effect, now stated explicitly** (`GraduateVentureReview.tsx`, expanded per Section 13):
a public profile becomes visible immediately at `/startup/{name}` (honestly labeled not-yet-evaluated, per
Section 39.2's fix — previously this claim would have been false); nothing about how the founder builds the
venture changes; SIE has not verified or approved anything.

### 39.4 "Graduation" language — already absent, confirmed

Grepped every `.tsx` file for founder-facing occurrences of "graduate"/"graduation": zero matches outside
code comments and internal identifiers (`VentureGraduationBanner`, `useVentureGraduation`, etc.). This
convergence was already complete before 37E — Phase 31's own Part 15 ("never 'you're ready,' 'graduated,' or
'congratulations'") held. One real gap found and fixed: `VentureGraduationBanner`'s own button used to open
`/founder/startups/{id}`, which (since Phase 37B) immediately redirects back to the exact page the banner
renders on — a same-page loop with no destination. Repointed to "View public profile →", the one genuinely
different, useful destination reachable from that exact banner.

### 39.5 Analyze-my-startup overlap — found and resolved

**Found**: `VentureWorkspace.tsx`'s Overview tab rendered a "Ready to turn this into a real startup? / Analyze
My Startup" card, independently eligible from (and able to render simultaneously with)
`VentureGraduationAction`'s own "Ready to make this a startup?" card. Its button routed to the generic
`/analyze` page with no `startup_id` — creating a brand-new, **unlinked** startup with no
`venture_graduations` bridge back to the venture at all. This is the exact "second Analyze My Startup path"
Phase 37B's own architecture doc (§36.9) flagged as unresolved and handed to this phase.

**Resolved**: removed the duplicate card entirely (Overview now has exactly one "make this real" entry
point — the correct, linked one). The remaining, legitimately different disconnected-evaluation entry point
(inside the Analyze tab's own "no startup identity yet" state, for a founder who wants to try SIE's
evaluation without creating a company identity first) was **not** removed — Section 16 forbids disappearing
features — but its copy now says plainly "This runs a standalone evaluation, not tied to {venture}," and a
quiet "Create a Startup Profile from this venture →" link (reusing `VentureGraduationAction`'s own non-
prominent control, not a new mechanism) sits directly below it as the path to a tracked evaluation.

### 39.6 My Ideas / Idea Lab / My Startups — verdicts

- **Idea Lab**: **RENAME UI ONLY — already complete** (Phase 32/34A removed it as a user-facing label
  entirely; "Build" is the nav-level term). No further action.
- **My Ideas**: **RENAME** → **My Companies**. This list holds ventures at every stage, including ones with
  real six-figure ARR (Section 4's own stage-vocabulary work already proved "Idea" alone is ambiguous at the
  per-venture badge level — this was the identical ambiguity one level up, at the collection-title level).
  Updated: `IdeaLabDashboard.tsx`'s `PageHeader` title, `VentureWorkspace.tsx`'s breadcrumb and not-found
  page ("Idea not found" → "Company not found"). Route (`/idea-lab`) and the "Start a New Idea" creation CTA
  are unchanged — a brand-new entry legitimately does start as just an idea; "Build" (the top nav item) is
  also unchanged.
- **My Startups**: **KEEP**, distinct from My Companies. Confirmed via actual data source, not assumption:
  My Companies is `list_modeled_ventures_for_user()` (owned `modeled_ventures` rows only). My Startups is
  `get_startup_memberships_for_user()` (every live `startup_memberships` row), a materially different set —
  it includes startups the founder reached via an approved **claim** on a company they never modeled as a
  venture at all (e.g. Retool has no corresponding My Companies entry). Merging them would require new
  backend aggregation across two independent relationships for no founder benefit; kept as two distinct,
  correctly-named surfaces.

### 39.7 Trust / verification — audited, no changes needed

Re-read `ClaimStartupButton.tsx`, `ClaimStartupForm.tsx`, and the `resolveStartupTrustState()` call site.
Confirmed already correct and unchanged by prior phases (Phase 32A): "Founder-managed" vs "✓ Verified" is
derived purely from `verification_method`, never implies product-access, and `ClaimStartupForm`'s own
copy already explicitly disclaims "automated verification, domain verification, legal ownership
verification, a guarantee of approval." No founder-facing text implies verification/claiming/analysis
grants any Build/Finance/Fundraising/History capability. No changes made.

### 39.8 Private capability access — proven, not assumed

Live-verified on the fresh FridgeChef 37E Test venture, before any profile existed: Overview, Finance ("Add
your finances"), Fundraising (SAFE/priced-round options, Pitch Deck Coach teaser), and History all rendered
fully functional. No gate exists anywhere keyed on public-profile existence, analysis existence, or
verification state — confirmed by direct observation, not by re-stating the architecture's own claim.

### 39.9 Company name consistency — divergence found, documented (not "fixed")

Live-observed on the same test company: the private venture name ("FridgeChef 37E Test"), the `analyses`/
`startups` table's `company_name`/`canonical_name` ("FridgeChef 37E Test" — confirmed by the public route
successfully resolving `/startup/FridgeChef%2037E%20Test`), and `methodology.context.company_name` (the
LLM's own extracted name, rendered as bare "FridgeChef" by `StartupHeroV2`) can genuinely diverge — the
model normalized/shortened the name during analysis. This is a **pre-existing, independent** field (the
identity bridge itself still resolves entirely by ID/normalized_name, never by this extracted string — no
name-matching risk introduced or discovered) and is **not** fixed here per this phase's own explicit
instruction ("Do not introduce silent name matching... do not 'fix' it by synchronizing blindly"). Documented
as a known cosmetic divergence for a future phase to decide whether/how to reconcile display copy.

### 39.10 Public profile routing — audited, no redesign

`startups.normalized_name` carries a `UNIQUE` constraint (confirmed in schema); the Section 39.2 fallback
query uses this exact column, so it cannot introduce a collision the existing `resolve_startup_for_graduation()`
guard doesn't already prevent at write time. No slug migration, no routing redesign.

### 39.11 Test matrix and live walkthrough

A–H, J–N, R–T, U–Y, AA–AC confirmed via the unmodified/extended backend suite (168 tests total this phase:
15 in `test_startup_entity_migration.py` including 3 new, plus the full re-run of
`test_saved_startups`/`test_startup_claims`/`test_security_hardening`/`test_venture_graduation`/
`test_idea_lab`/`test_founder_workspace` — zero failures). I (profile creation preserves venture id), O/P/Q
(public profile states), Z (Analyze scoring unchanged), AD (missing-company vs. unanalyzed-company are
now distinct) confirmed live below.

**Fresh company walkthrough** (Section 30's own acceptance script, FridgeChef 37E Test):
Pre-profile — Overview/Finance/Fundraising/History all functional, Analyze tab showed the honest "no
startup identity yet" dual-path state (standalone evaluation vs. create profile). Created a Startup Profile:
**same venture id (8212) throughout**, Overview immediately showed the graduation banner with a working
"View public profile →" link, Analyze tab switched to the honest "no analysis yet" state (deterministic,
`startup_id`-scoped). Visited the public profile before analysis: rendered the new honest B-state (Section
39.2), no fake SPS. Ran a real, intentional analysis (SPS 60.6, C, Medium confidence, full six-pillar
breakdown). Re-visited the public profile: now showed the real analysis, V2.1 score history (60.6, 1
analysis), unchanged trust badge.

**STATE A–F**: A (FridgeChef pre-profile) PASS. B (FridgeChef post-profile, pre-analysis) PASS. C
(FridgeChef post-analysis) PASS. D (Retool, unlinked, analyzed) PASS — legacy Founder Workspace intact,
dedicated fundraising page still un-redirected, still functional. E (FridgeChef public profile, pre-
analysis) PASS. F (FridgeChef public profile, post-analysis) PASS.

### 39.12 A defect found and fixed mid-phase (JSX whitespace)

While live-testing the new dual-path Analyze empty state and the expanded `GraduateVentureReview` copy,
found three more instances of the same JSX-whitespace-collapse defect first identified in Phase 37C (an
expression immediately followed by plain text loses its leading space in this toolchain, unpredictably,
regardless of same-line/multi-line positioning) — all in text written this phase. Fixed each with an
explicit `{" "}`, re-verified via direct DOM `textContent` reads (not screenshots) after each fix, then
re-ran the full `tsc`/`eslint`/`next build` suite. No formula, routing, or data logic was touched by these
fixes — text only.

### 39.13 Remaining architectural risk / 37F candidates

- Company-name divergence between private venture name, canonical `startups` name, and LLM-extracted
  `methodology.context.company_name` (Section 39.9) — cosmetic today, worth a display-copy decision later.
- `FundraisingReadinessCard`/`PitchDeckCoachTeaser` renderings inside the legacy `FounderStartupWorkspaceView.tsx`
  remain unreachable-for-linked/load-bearing-for-unlinked (carried over from 37D, unchanged this phase).
- founder_actions/founder_updates/startup_milestones migration groundwork (37D's own handoff, still no
  concrete backfill design — none built this phase either).

## 40. Non-goals of this document

This document does not implement any part of the convergence, run any migration, change any schema, rename
any route, merge or delete any table or component, redesign SPS, change any scoring formula, build Capital
Planning, connect Finance data into Build's recommendation text, or introduce a new Company table. It
documents what exists, validates the architecture hypothesis against the actual repository, and recommends a
sequence for a future set of implementation phases to execute.
