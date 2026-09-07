# Venture → Startup → Founder Workspace Architecture Audit V1

**Status:** Audit only (Phase 34F, Section 8). No refactor, no migration, no data change in this phase.
Every claim below is verified against the live schema/code, not inferred.

**The product principle this audit is answering:** the founder thinks "this is my company." They should
not need to understand that SIE internally represents that company as different database entities at
different points in its lifecycle.

## 1. What actually exists today (verified against the live schema)

```
modeled_ventures  (id, user_id, name, assumptions, model_result, share_*, ...)
   ├─ venture_missions / venture_evidence / venture_decisions      (Phase 34D loop -- founder-private)
   ├─ venture_model_updates                                        (assumption-change history)
   └─ venture_graduations (venture_id UNIQUE, startup_id UNIQUE)  ──┐
                                                                     │
startups  (id, canonical_name, normalized_name)  ◄───────────────────┘
   ├─ startup_memberships (user_id, startup_id, role)   -- many-to-many, NOT single-owner
   ├─ analyses / analysis_runs                          -- SPS, versioned, re-runnable
   ├─ founder_actions / founder_updates / startup_milestones
   ├─ startup_claims                                    -- "this is my company" claim-to-membership
   └─ saved_startups                                    -- any user's personal watchlist entry
```

`modeled_ventures` is **single-owner** (`user_id` directly on the row, no membership table — a Venture
belongs to exactly one Clerk user, always). `startups` is **shared and canonical** (keyed by
`normalized_name`, so two different users describing "the same real company" resolve to one row) with a
real many-to-many membership table supporting more than one member and a `role` field. `venture_graduations`
is the one-to-one bridge, created exactly once per venture, never overwritten.

## 2. Why Startup exists separately from Venture (verified reasons, not assumed)

1. **Canonical, cross-user identity.** `startups.normalized_name` is unique — this is the mechanism that
   lets rankings, search, and public discovery treat "Acme Inc" as one entity regardless of who analyzed
   it or how many times. `modeled_ventures` has no such uniqueness; two ventures can share a name, and
   that's fine — they're private drafts.
2. **Multi-membership.** `startup_memberships` genuinely supports more than one member per startup
   (`role` field, unique per `(user_id, startup_id)`) — a cofounder or investor can hold a membership on the
   same startup a founder graduated. `modeled_ventures` has no such concept; it is not designed to be
   co-owned.
3. **Versioned, re-runnable analysis.** `analyses`/`analysis_runs` are their own append-only history,
   designed to be re-computed (re-analysis) and compared over time against one canonical identity — this is
   a different lifecycle from `venture_model_updates`, which tracks a single founder's own private
   assumption edits.
4. **A genuinely different audience.** `app/ai/investor_workspace.py` and the public `/startup/[id]`,
   `/rankings`, `/search` surfaces are built to be read by people who are **not** the founder (investors,
   the public). A `modeled_venture` is never publicly discoverable by name; a `startup` is designed to be.

None of these four reasons is "founders need to earn features by graduating" — they are all real,
independent technical/product reasons `startups` needs to be a canonical, shared entity distinct from a
private, single-owner venture draft.

## 3. Which distinctions are database concerns vs. user-facing concepts

- **Database concern only, safe to hide from the founder:** the fact that `modeled_ventures.id` and
  `startups.id` are different primary keys, joined by `venture_graduations`. A founder does not need to know
  this exists; the UI can (and, per Phase 34E/34F, mostly does) present "your company" as one continuous
  thing.
- **Real, user-facing concept, not just a database artifact:** the distinction between "my own private
  workspace" (Venture — evidence, decisions, drafts, nothing public unless I explicitly enable sharing) and
  "the canonical, potentially multi-person, potentially publicly-discoverable record of this company"
  (Startup). This is not an implementation detail a founder can be shielded from forever — a founder who
  invites a cofounder, appears in rankings, or is analyzed by an investor genuinely needs to understand that
  something changed. The mistake Phase 34F corrects is presenting that transition as an *unlock* ("graduate
  to get real tools") rather than as what it actually is (this company became visible/shareable/multi-person).

## 4. Can one continuous workspace span Idea → Validation → Building → Operating without forcing a separate founder product?

**At the data level, largely yes already.** Nothing is deleted at graduation (`test_deleting_venture_cascades_link_but_preserves_startup`/`test_deleting_startup_cascades_link_but_preserves_venture` — both already-passing regression tests confirm this); the venture's own evidence/decisions/history survive untouched forever, graduated or not. The remaining gap is **presentation**, not data: `/idea-lab/[id]` (the Venture workspace) and `/founder/startups/[id]` (the Founder Workspace) are two separate pages today, and a founder must navigate between them manually via the graduation banner's "Open Founder Workspace →" link.

**Recommendation (future phase, not this one):** rather than collapsing the two database entities (see §6
for why that's the wrong move), evolve the *founder-facing* surface toward one continuous page per company
that internally resolves whichever of {venture-only, venture+startup} exists for that company and renders
accordingly — Idea/Validation/Building stages read from `modeled_ventures` + Phase 34D's tables exactly as
today; once `venture_graduations` exists, the same page gains the startup-scoped tools (SPS, founder
updates, fundraising-readiness-gaps) as additional sections rather than a separate destination. This is a
UI/routing unification, not a schema migration — genuinely migration-compatible.

## 5. Should Startup Profile become an optional public/shareable representation rather than an unlocked founder workspace?

**Yes, and this is worth stating precisely, because two different things currently share the word
"unlock":**

1. **Startup Profile** (the public, canonical, potentially-multi-analyst representation — `/startup/[id]`,
   rankings, search) is correctly understood as an *optional, shareable representation* a company can have,
   not a tier of founder access. A founder should be able to think of it the same way they already think of
   `modeled_ventures.share_enabled` (Phase 27's own venture-level public snapshot) — visibility a founder
   opts into, not a reward.
2. **Founder Workspace** (`/founder/startups/[id]`, its fundraising-readiness-gap tracker, founder updates,
   milestones) is a genuinely different, currently startup-scoped *tool set*, not "the same Build tools,
   unlocked." Some of it (fundraising-readiness-gaps, specifically) is legitimately dependent on a real SPS
   existing — `get_fundraising_readiness()` reads `methodology["startup_intelligence_score"]` directly, so
   it cannot exist before an `analyses` row does. That is a genuine technical prerequisite, not an artificial
   maturity gate (see the doctrine document's own §8/Section 12 audit).

The corrective framing for a future phase: stop presenting "Startup Profile" and "Founder Workspace" as one
bundled reward for graduating. They are two separate things — an optional public representation, and a
startup-scoped tool set some of which has a real data dependency on SPS existing.

## 6. What happens to existing graduation data?

Nothing changes this phase. `venture_graduations` remains the historical, one-to-one bridge record. **Do not
collapse `modeled_ventures` and `startups` into one table** — they have genuinely different constraints
(single-owner vs. multi-member), genuinely different consumers (a dozen tables already reference each
independently, per §1's diagram), and genuinely different lifecycles (a re-runnable analysis history vs. a
single founder's private draft history). A destructive merge would require rewriting every one of those
consumers simultaneously and would break the multi-membership/public-discovery guarantees `startups` exists
to provide. The recommended direction (§4) achieves the founder-facing "one company" feeling without this
risk.

## 7. How should SPS work for ventures that have not "graduated"?

**It already can, today, via one existing bridge — but disconnected from Phase 34D's own evidence.** `POST
/analyze` requires only authentication (confirmed in the doctrine document's §8 gate audit) — nothing about
it requires graduation. The existing "Ready to turn this into a real startup?" bridge card
(`VentureWorkspace.tsx`, unchanged this phase) already routes exactly this way: it stashes the venture's own
description and sends the founder to Analyze, which computes a full SPS completely independent of whether
the venture ever graduates. This already satisfies the doctrine's letter — SPS is not gated by stage.

**The real limitation, worth flagging for a future phase:** Analyze's own evidence-scoring pipeline
(`app/ai/analyze_pillar.py`) has no way to read Phase 34D's `venture_evidence`/`venture_decisions` rows —
a founder who has confirmed real evidence through the Build loop must re-describe it in prose to Analyze to
have SPS reflect it. Feeding confirmed venture evidence into SPS's own evidence pipeline as a genuine
evidence source (never a shortcut around SPS's own methodology or evidence-quality rules) would make "one
company, one history, one intelligence system" true at the evidence level, not just the navigational level.
This is a real, identified opportunity — explicitly **not** implemented or further designed in this phase.

## 8. Which existing Startup functionality should eventually become available directly from the Venture workspace?

Candidates, roughly in order of how independent they are of a real SPS/canonical-identity requirement (and
therefore how safe they'd be to generalize down to the Venture level first):

1. **Founder updates** (narrative log entries) — no structural dependency on SPS; could plausibly become a
   Venture-level capability with no data-model change beyond a new table scoped by `venture_id` instead of
   `startup_id`.
2. **Startup milestones** — similar; largely independent of SPS.
3. **Fundraising-readiness-gap tracking** — genuinely SPS-dependent (§5) as currently designed; would need
   either a real SPS to exist for the venture (via the Analyze bridge, §7) or a redesigned, evidence-based
   (not SPS-pillar-based) readiness check scoped to Phase 34D's own evidence instead.
4. **Public Startup Profile / rankings / multi-member access** — these should very likely **not** become
   available pre-graduation; they are exactly the canonical/shared/public capabilities §2 explains Startup
   exists to provide, and a private Venture draft should not become publicly discoverable by name without
   the founder's explicit choice.

## 9. Summary recommendation

- Do not migrate or collapse the schema now.
- Treat this as a presentation problem to solve in a dedicated future phase: one continuous founder-facing
  page per company, internally resolving venture-only vs. venture+startup state, is preferred over any
  destructive rewrite.
- Treat "Startup Profile" as an optional public representation, not an unlocked tier.
- Treat "Founder Workspace" tools individually — some (updates, milestones) are safe to generalize to the
  Venture level early; some (fundraising-readiness) are genuinely SPS-dependent and should stay that way
  until/unless SPS itself becomes computable from Phase 34D evidence directly.
- The highest-value single next step, if a future phase pursues this, is feeding confirmed venture evidence
  into Analyze's own evidence pipeline — this does more to make "one company, one history" true than any
  navigation change would.
