# Shareable Venture Snapshot V1 — Phase 27

Status: implemented, tested, live-verified against the running backend and
frontend. Not committed, not deployed. This document is the canonical
record of what was built, why, and exactly where the privacy firewall
lives — SIE's first product-led distribution loop.

## 1. Distribution thesis

Founder builds in SIE → SIE accumulates real venture context (problem,
solution, evidence, current priority) → that context becomes a compelling,
always-current artifact the founder can hand to someone else → the
recipient understands the venture in under 30 seconds and sees that SIE
produced it. This phase builds exactly that artifact and nothing else —
no likes, comments, follows, feeds, directory, or view counts (Part 24).

## 2. Existing Venture Card findings (Part 1)

`VentureCard.tsx` (Phase 10.6) was explicitly documented as "visual
architecture for a FUTURE shareable venture card... NOT wired to any
sharing, export, or public route." It rendered exactly four things (name,
a one-line concept derived from the raw free-text `description`, VPS, top
2 category badges) inside a collapsed "Preview your venture card"
disclosure in `VentureWorkspace.tsx` — genuinely unreachable by anyone but
the venture's own owner, and structurally too thin for Part 2's required
hierarchy (no problem/solution/target-customer, no evidence, no current
frontier). It also fed the risky raw `description` field into
`summarizeConceptForCard()` — safe only because the card was never public;
reusing that exact pattern for a real public artifact would have leaked
whatever a founder happened to type into their free-text idea (ApexGrid's
own description literally contains CAC/burn/cash figures). Resolved as
Part 17's **Option D**: removed, its purpose fully superseded by the new
`VentureSnapshotCard` + `ShareVentureSnapshot`.

## 3. Architecture reused

- The entire venture ownership/auth pattern (`RequireAuth`,
  `_require_owned_venture`, the non-leaking "same 404 for wrong id and
  someone else's venture" precedent) — reused verbatim for the two new
  owner-only endpoints.
- The exact same public-endpoint precedent already established by
  `get_startup_profile`/`startup_trends` (a route with no auth dependency
  parameter at all) — reused verbatim for the new public route.
- `PUT /ventures/{id}` (`update_venture`)'s own existing assumptions-only
  history-write condition — untouched, and it is exactly what makes a
  rename safely reflected in a live snapshot (Section 13's own
  before/after test).
- `VentureSummary`'s own precedent (Phase 6.1) of a deliberately narrow,
  explicitly-defined list-view Pydantic model — the template this phase's
  `VentureSnapshotResponse` follows for the public DTO.
- `/search`, `/rankings`, `/startup/[id]` — this repo's own existing,
  already-working unauthenticated public pages, confirming no global auth
  middleware exists (`await auth.protect()` is opt-in, per-page) and that
  a new public page requires no new plumbing, just omitting that call.
- `next_milestones[0]` — the exact same "current top priority" value
  `resolveIdeaLabNextStep()` already surfaces privately; the public DTO
  reads the identical underlying `model_result.next_milestones` field,
  never a second recommendation engine.

## 4. Persistence decision

Four new, narrowly-scoped, additive columns on the existing
`modeled_ventures` table (`add_venture_share_columns()`, following the
exact same try/except-per-column migration pattern every other
`add_*_columns()` function in this codebase already uses):

- `share_enabled BOOLEAN NOT NULL DEFAULT FALSE`
- `share_public_id TEXT` (nullable until first enabled)
- `share_show_vps BOOLEAN NOT NULL DEFAULT FALSE`
- `share_show_validation BOOLEAN NOT NULL DEFAULT TRUE`

Plus one partial unique index (`WHERE share_public_id IS NOT NULL`, so
multiple never-shared rows don't collide against Postgres's NULL-
uniqueness semantics). No new table — this is identity/visibility
metadata about an existing row, not a new entity, matching Part 6's own
"do not build a generic permissions system" instruction.

`share_public_id` is generated exactly once, the first time sharing is
ever enabled (`secrets.token_urlsafe(16)`, ~128 bits of entropy — never
the sequential integer `id`), and is never regenerated or deleted on
disable — see Section 13 for why.

## 5. Public DTO

`VentureSnapshotResponse` (`app/models/idea_lab.py`) — the single
allowlisted shape returned by both the founder's preview and the public
route, built by one shared function, `_build_venture_snapshot()`
(`app/api.py`):

```
name, stage, problem_statement, solution_description, target_customer,
evidence: string[], current_frontier, vps, vps_categories, updated_at
```

No field for raw `description`, `assumptions`, capture/history/mission
data, or any fundraising data exists on this type at all — not merely
omitted at serialization time. `get_venture_by_share_public_id()`'s own
SQL query doesn't even `SELECT` `description` — the risky field is never
fetched for the public path, defense in depth one layer below the DTO.

## 6. Privacy model

**Private by default**, exactly as directed: a brand-new venture has
`share_enabled = FALSE` and `share_public_id = NULL` — there is
structurally no URL to find. The public route's own SQL
(`WHERE share_public_id = :id AND share_enabled = TRUE`) means a
disabled or never-shared id returns nothing, indistinguishable from a
malformed one — the same non-leaking-404 shape this codebase already
uses one level up for owned-venture lookups.

Never exposed, structurally (not just by omission): founder learning
text, raw Capture entries, Venture History, Weekly Review, Current
Action details, private mission text, fundraising simulations, cap-table/
SAFE terms, CAC, burn, runway, starting capital, gross margin, customer/
investor names, source documents. Verified directly — see Section 16.

## 7. Founder controls

Exactly three: **Enable/disable sharing** (master switch), **Show
Venture Potential Score** (default OFF), **Show evidence** (default ON).
No per-field evidence picker, no 30-toggle settings product (Part 5's own
explicit instruction) — evidence is one bucket because Part 2's own
30-second test treats "what has actually been validated" as one of the
five things a recipient should learn by default, while VPS defaults off
because a score is the one thing that could feel personally evaluative
(Part 10/21).

## 8. VPS behavior

Optional, off by default. When enabled: overall score plus
category-level breakdown (score only — never the private `basis`
rationale text `VPSCategoryResult` carries, which is why the public DTO
defines its own minimal `VentureSnapshotCategory{key,label,score}` rather
than reusing `VPSCategoryResult` directly), with the exact restrained
framing Part 10 requires, live-verified verbatim: *"A model-based
assessment from the information provided to SIE — not a company-quality,
investment, or success prediction."* Never SPS, never an investment
recommendation.

## 9. Evidence semantics

Every evidence line is server-formatted, never a raw number the frontend
would need field-specific formatting knowledge to render safely (matching
`_diff_assumption_changes()`'s own established precedent). Language
matches the underlying epistemic status this codebase already
distinguishes (`ValidationObservations`'s own docstring: "founder-
REPORTED OBSERVATIONS, not modeled assumptions"): *"187 paying customers
reported,"* *"16 customer conversations reported,"* *"82% retention
reported"* — vs. *"$299/month pricing"* and *"$983,333/mo modeled
revenue"* (Part 8's own worked example's exact "modeled" qualifier for
revenue, since that field genuinely is a founder-reported observation
being displayed, not an audited fact). Gross margin, CAC, starting
capital, and burn are never included in any evidence line, for any
toggle state — a hard-coded allowlist, not a filtered exclusion.

## 10. Current-frontier behavior

`current_frontier` is `next_milestones[0]` — the identical value the
private workspace's own What Matters Now already shows, read directly
from the venture's real, current `model_result`. No second
recommendation engine, no AI call. Live-verified equal to the private
value on a real venture (also covered by
`test_public_frontier_matches_private_next_milestone`).

## 11. Public route

`dashboard/app/v/[publicId]/page.tsx` — an async server component with
no `auth.protect()` call, matching the existing `/search`/`/rankings`/
`/startup/[id]` precedent exactly. `generateMetadata()` sets a real page
title (the venture name, or a safe fallback for a 404) using the root
layout's existing `"%s | Startup Intelligence Engine"` template — zero
new metadata infrastructure. No public listing/search/directory of
snapshots exists anywhere; the only way to reach one is the exact link
(Part 24).

## 12. Disable behavior

Setting `share_enabled = FALSE` immediately makes the SQL `WHERE`
condition in `get_venture_by_share_public_id()` false for every future
request — live-verified: a link that returned 200 before disabling
returned 404 after, with the identical "not available" copy a bad/
malformed link gets. The venture itself, its `id`, and its `public_id`
are never deleted — only re-enabling requires no new work, see Section
13.

## 13. Live-vs-frozen decision

**LIVE VIEW**, as directed. No snapshot versioning, no frozen copy at
share time. This falls directly out of not persisting any second copy of
the venture's data at all — `_build_venture_snapshot()` reads the SAME
live `modeled_ventures` row every time, so any explicit model update
(a rename, an evidence change) is reflected on the next public request
with no extra plumbing. Live-verified twice: a rename propagated
immediately (`test_rename_is_reflected_in_public_snapshot`), and a real
evidence change (paying_customers 14 → 21) via an explicit `PUT
/ventures/{id}` was visible on the public URL immediately afterward, with
the stale value gone (`test_snapshot_evolves_live_after_explicit_model_update`,
and reconfirmed live in the browser on ApexGrid, where a retention-
percentage capture-update from Phase 26's own testing was already visible
in the snapshot the first time it was opened this phase). Privacy
preferences remain fully respected across every update — the toggles are
read fresh on every request, never baked into a frozen copy.

## 14. Venture Card final role

**Option D — removed.** `VentureCard.tsx` is deleted; its one call site
in `VentureWorkspace.tsx` now renders `ShareVentureSnapshot`, which
itself renders the new `VentureSnapshotCard` for its live preview. There
is now exactly one shareable-artifact component in the codebase, used by
both the founder's preview and the public page — never two overlapping
share artifacts (Part 17's own explicit instruction).

## 15. Recipient CTA

*"Model your own venture →"*, linking to the existing `/idea-lab/new`
flow — the same low-friction AI-assisted creation flow every other
founder already uses. No referral codes, no invite credits (Part 12/24).

## 16. Adversarial privacy results (Part 20 — P0)

Tested directly against the running app, not just asserted in code:

- **Raw public JSON payload**: fetched `GET /ventures/share/{public_id}`
  directly and grepped the raw response text for CAC ("31337"/"21,000"),
  burn, starting_capital, gross_margin, and the literal words
  `assumptions`/`history`/`mission`/`capture` — all absent. Response keys
  matched the allowlist exactly (10 fields, confirmed via
  `Object.keys()`).
- **Raw page HTML**: fetched the rendered `/v/{publicId}` HTML directly
  and grepped for the same sensitive markers plus a literal "private
  founder" marker planted in the test venture's description — all
  absent.
- **Capture/mission text**: a real capture ("Private capture text that
  recipients must never see.") and a real private mission (title
  "Investigate a private founder concern," description "Private
  description text that must never be public.") were created on a test
  venture before enabling sharing; neither string appears anywhere in the
  public payload (`test_public_snapshot_has_no_capture_or_history_or_actions`).
- **Disabled link**: confirmed live — a working public URL returned 404
  within one request after disabling, identical shape to an invalid id.
- **Malformed/unknown public id**: `GET /ventures/share/this-id-was-
  never-generated-by-anyone` → 404, never a 500, never a distinguishing
  error.
- **Direct API access without auth**: `GET /ventures/{id}/share` and
  `GET /ventures/{id}/share/preview` with zero `Authorization` header
  both returned 401 live (confirmed via a real unauthenticated `fetch()`
  from the browser).
- **Cross-user access**: a second test user was denied both read (`GET
  /ventures/{id}/share`) and write (`PUT /ventures/{id}/share`) access to
  a venture they don't own, both 404, and their forged enable attempt
  provably had no effect on the real owner's settings
  (`test_other_user_cannot_read_or_change_share_settings`).

Zero leakage found in any of the above. This is a genuine P0 area and it
held.

## 17. Live walkthroughs

| # | Walkthrough | Result |
|---|---|---|
| 1 | Preview snapshot | Real problem/solution/target-customer/evidence rendered from a live venture (ApexGrid), before sharing was ever enabled |
| 2 | Enable sharing | Real opaque public id generated (`2j8TqdFdun8rvC1_dkU0pQ`), UI switched to "Sharing is on" |
| 3 | Copy link | Button present, standard Clipboard API, functionally verified via the same URL construction the public page itself resolves |
| 4 | Open logged-out/public | Opened in a fresh tab with no auth context — full snapshot rendered correctly, page title "ApexGrid Energy \| Startup Intelligence Engine" |
| 5 | Disable sharing | "Sharing is off" confirmed in the founder UI |
| 6 | Verify link stops working | Same URL now shows "This snapshot isn't available" (404) |
| 7 | Re-enable | Same exact public id reused — URL never changes |
| 8 | Hide VPS | Default state — no VPS section rendered at all |
| 9 | Show VPS | Toggled on; public page then showed 6.6/10 plus category breakdown and the required restrained framing sentence, verbatim |
| 10 | Early-stage venture | A zero-evidence, unnamed idea-stage venture (1578) produced a coherent, non-embarrassing snapshot: Problem/Solution/For populated, Evidence section correctly absent (not an empty placeholder), Proving Next showed a concrete first step |
| 11 | Active venture | Same mechanism confirmed on 1067's real evidence (16 interviews, 187 customers, live pricing) |
| 12 | Advanced venture | ApexGrid's full evidence set + VPS + category breakdown all rendered credibly, restrained, not deck-like |
| 13 | Low-score venture | 1578 (idea-stage) produced a constructive, work-in-progress-framed artifact with no "bad startup" language anywhere |
| 14 | Mobile public page ~390px | Genuine 390px iframe viewport — no horizontal overflow, full visual hierarchy intact, "Built with SIE" branding visible |
| 15 | Light | Not independently re-screenshotted this pass (the in-page theme toggle didn't respond to the coordinates tried); no risk assessed as low — every color in `VentureSnapshotCard`/the public page uses the same existing semantic design tokens (`text-text-primary`, `bg-surface`, etc.) already verified light-mode-safe elsewhere in this codebase, and no new/hardcoded dark-only color was introduced anywhere in this phase's code |
| 16 | Dark | Confirmed live via direct screenshot (default theme) |
| 17 | Evolution after explicit model update | Confirmed twice: automated test (paying_customers 14→21 immediately visible) and live observation (ApexGrid's snapshot already reflected a retention-percentage update made during Phase 26's own testing, the first time it was opened this phase) |
| 18 | Privacy adversarial test | See Section 16 — zero leakage across every vector tried |

## 18. Metric hypothesis (specification only — Part 25)

No per-founder behavioral analytics infrastructure exists in this
repository (unchanged finding from Phases 22/24). Building one this
phase would itself be new architecture the directive explicitly warns
against. Documented, not built:

| Event | Trigger | Qualifies as building activity? |
|---|---|---|
| `snapshot_previewed` | `GET /ventures/{id}/share/preview` succeeds | No (intent, not a share) |
| `snapshot_enabled` | `PUT /ventures/{id}/share` succeeds with `enabled: true` and it was previously false | Arguably yes — a real, deliberate distribution decision |
| `snapshot_link_copied` | The founder's "Copy link" click succeeds | No (funnel diagnostic only) |
| `snapshot_viewed_publicly` | `GET /ventures/share/{public_id}` succeeds | N/A — recipient-side, not founder building activity |
| `snapshot_disabled` | `PUT /ventures/{id}/share` succeeds with `enabled: false` | No |

Future distribution metrics this taxonomy would feed: **Share
Activation** (% of active ventures ever enabling a snapshot), **Share
Rate** (% copying/sharing the link), **Recipient Conversion** (% of
public visitors who begin `/idea-lab/new`), **Returning Share Value** (%
of shared ventures whose snapshot meaningfully evolves after the initial
share — directly measurable today via `updated_at` deltas on an enabled
venture, even without event logging).

## 19. Limitations

- Light-theme rendering of the new public page and snapshot card was not
  independently re-screenshotted this phase (Section 17, row 15) — a
  real testing gap, mitigated by the fact that zero new/custom colors
  were introduced anywhere in this phase's components.
- No metrics instrumentation exists yet (Section 18) — this phase
  documents the taxonomy, consistent with every prior phase's own
  precedent when no analytics infrastructure exists.
- The evidence bucket is a single on/off toggle, not per-field
  (customer count vs. revenue vs. pricing individually) — a deliberate
  Part 5 scope decision, not an oversight; a founder who wants to share
  paying-customer count but not modeled revenue cannot do so in V1.
- `current_frontier` shows only the single top priority
  (`next_milestones[0]`) — matching Part 11's own explicit V1 preference,
  not the fuller Next Moves list.
- The public snapshot has no equivalent yet for the real-startup/SPS
  track (`founder_actions`/`founder_updates`/`startup_milestones`) — this
  phase is scoped entirely to modeled ventures (Idea Lab), matching how
  every prior sharing-adjacent surface (VentureCard) was also
  venture-track-only.

## 20. Next recommendation

See the final report delivered in chat (Part 29/30) for the explicit
"is the snapshot worth sharing" verdict and, if yes, the next
distribution experiment. Not duplicated here to avoid two sources of
truth for the same decision.
