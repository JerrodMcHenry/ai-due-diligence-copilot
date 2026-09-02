# Weekly Founder Review V1 — Phase 24

Status: implemented, tested, live-verified against the running backend and
frontend. Not committed, not deployed.

## 1. Architecture reused

Everything is assembled from data that already existed before this phase:

- `GET /ventures/{id}/history` (Phase 16, extended in Phase 23) — the sole
  data source. No new endpoint was added this phase (route count is
  unchanged at 67 from Phase 23).
- `venture_model_updates.before_assumptions`/`after_assumptions` — these
  JSONB columns already existed (Phase 16) and were already selected by
  `list_venture_model_updates_for_owner()`; this phase is the first time
  either is *exposed* through the API, as a small curated diff (see
  Section 5), not the full blob.
- `resolveIdeaLabNextStep()` (Phase 10.10) — reused verbatim for "What
  still needs proving" / "Focus next." No new recommendation logic.
- `suggestionForMilestone()` / the `onStartMission` → `setPendingMission`
  → `MissionsSection` mission-creation pathway (Phase 10.7 onward) —
  reused verbatim for the review's "Make this an action" callback. No
  second mission-creation code path exists anywhere in this phase's code.
- `categoryChangeExplain.ts`'s neutral-framing precedent — this phase's
  own strongest-movement copy follows the same non-punitive pattern
  already established there and in Phase 23's model-update UI.

**`app/database/db.py` required zero changes.** Every fact the review
needs was already queryable through functions that existed before this
phase.

## 2. Review-window definition

**"Last 7 days," a rolling window ending now** — never "this week" or any
other calendar-week framing, because no timezone infrastructure exists in
this repository (confirmed again this phase; unchanged since Phase 22's
own audit). The founder-facing label is the literal string `"Last 7 days"`
(`REVIEW_WINDOW_LABEL` in `buildWeeklyReview.ts`), matching the directive's
own explicit requirement never to imply calendar semantics that don't
exist.

## 3. Fact classification

| Section | Class | Source |
|---|---|---|
| What you did (counts) | **B. Derived fact** | Deterministic aggregation over real `venture_missions`/`venture_model_updates` events, in-window |
| What you learned | **A. Fact** | `learning_summary`, verbatim, never rewritten |
| What changed — VPS | **A. Fact** (each update's before/after) + **B. Derived fact** (first-of-window → last-of-window across multiple updates) | `venture_model_updates.before_vps`/`after_vps` |
| What changed — assumption fields | **B. Derived fact** | New `_diff_assumption_changes()`, same "only if changed" rule as the existing category diff |
| Strongest movement | **B. Derived fact** | Same first→last aggregation, applied to `category_changes` |
| What still needs proving | **C. Deterministic interpretation** | `resolveIdeaLabNextStep()`, unmodified, called with current (not historical) `model_result` |
| Focus next / CTA | **C. Deterministic interpretation** | Same resolver + existing mission-creation pathway |

**No AI-generated interpretation (class D) exists anywhere in this
feature.** No LLM call was added. Per the directive's own instruction,
class D was not added without a demonstrated gap that A–C couldn't
honestly cover — and none was found; every section the directive asked
for was fully coverable deterministically.

## 4. Aggregation semantics

`dashboard/lib/journey/buildWeeklyReview.ts` is a pure function:
`(VentureHistoryResponse, now, windowDays) → WeeklyReviewData`. Given the
backend always returns events newest-first, the module reverses the
in-window subset once to get chronological order, then for every
multi-value field (VPS, each assumption field, each category) takes the
**first-in-window "before" paired with the last-in-window "after"** — an
honest week-start-to-week-end comparison even across several model
updates in the same window, never a fabricated running total and never
silently picking just the most recent update.

## 5. Double-count prevention

This was the directive's own named central concern, and it required real
engineering. A Universal Capture (Phase 23) writes `venture_missions.
created_at`, `.learning_recorded_at`, and `.completed_at` **in one atomic
INSERT**, so all three resulting history events (`action_added`,
`learning_recorded`, `action_completed`) carry the **exact same**
`occurred_at`. An ordinary mission's three lifecycle events, by contrast,
always happen at genuinely different moments in real founder behavior.
`classifyMissions()` uses this structural fact — not a `mission_type`/
`source` flag, which `get_venture_history()` doesn't expose — to bucket
every mission_id in the window as either a **capture** (counted once,
under "observations captured") or **ordinary** (its completion counted
under "actions completed," its learning — if any — counted separately
under "learnings recorded"). A capture's learning is never also counted
as a separate "learning recorded." Live-verified on real accumulated data
(Section 8): 6 real captures on ApexGrid across two sessions correctly
read as "6 observations captured," never inflating "actions completed" or
"learnings recorded."

## 6. Learning semantics

Every quote under "What you learned" is `learning_summary` reproduced
character-for-character, sourced from either an ordinary mission's
reflection or a capture — both preserved identically, since both are
equally real founder text. Capped at the 3 most recent (newest-first,
matching the directive's "prefer the most meaningful/recent few" over
dumping every note). No summarization, no AI rewrite, no "SIE concluded"
framing anywhere.

## 7. Model-change semantics

"What changed" separates three genuinely different things, never
conflated: the plain VPS number (`vpsChange`), the curated assumption
field diffs (`assumptionChanges` — price point, gross margin, customer
interviews, waitlist signups, paying customers, monthly revenue,
retention), and the category-level "strongest movement." If assumptions
changed but VPS did not move materially (< 0.05, the same epsilon the
backend's own category diff uses), the review says exactly "Your venture
model changed, while Venture Potential Score remained X" — live-verified
via `test_assumptions_changed_but_vps_did_not` and observed directly in
Phase 23's own live walkthrough ("Venture Potential Score 6.9 → 6.9 …
did not materially change").

## 8. Negative-learning behavior

Live-verified end to end on a real venture (RevGuard AI): captured "We
spoke with 10 customers and none would pay $500/month," clicked "Update
my model," and watched VPS genuinely fall 6.1 → 5.8. The review reported
this plainly (`Venture Potential Score 6.1 → 5.8`) and framed the
strongest movement as "Validation moved from 4.5 → 3.0 after your
assumptions changed" — neutral phrasing regardless of direction, with no
punitive vocabulary anywhere in the codebase for this feature (asserted
directly in `test_negative_vps_change_has_no_punitive_language` and by
construction — this module never generates free-text sentences of its
own beyond field labels and values).

## 9. Current-priority reuse

"What still needs proving" and "Focus next" call `resolveIdeaLabNextStep()`
with the venture's **current** `model_result` — never a historical
snapshot from earlier in the window — so the priority shown is always
today's real priority, not a stale one from Monday. No new recommendation
engine was written.

## 10. Action handoff

The "Make this an action" button reuses the exact same
`onStartMission`/`setPendingMission` callback `IdeaLabNextStep` already
uses one section above it in `VentureWorkspace.tsx` — literally the same
function reference, passed down as a prop, not a second implementation.
When the current priority already has an active mission
(`missionedMilestones.includes(...)`, the same signal `IdeaLabNextStep`
already checks), the button is omitted rather than offering duplicate
work — live-verified on ApexGrid, where the button correctly did not
appear because that milestone was already actioned.

## 11. Empty/quiet states

Two genuinely distinct states, each live-verified:

- **Brand-new** (`isBrandNew`): the venture's entire history is nothing
  beyond its own creation. Copy: "Your venture history is just getting
  started," pointing at the existing What Matters Now / Actions / Capture
  surfaces — never a giant empty analytics panel.
- **Quiet week** (`hasActivityInWindow === false`, but not brand-new): an
  established venture with zero in-window activity. Copy: "No building
  activity has been recorded here yet," followed by the current focus —
  never "you fell behind," never a streak/shame framing. This exact
  scenario is proven by
  `test_quiet_week_on_an_established_venture_is_not_brand_new`; a live
  fixture aged past 7 days wasn't available in the current dataset at
  test time (every existing venture's most recent activity fell inside
  the rolling window), so this state's live-app rendering rests on the
  deterministic unit test rather than a fresh click-through — the same
  `buildWeeklyReview()` function the UI calls, exercised with a real
  `VentureHistoryResponse` shape.

## 12. Real-startup decision (deferred, Part 17)

**Deferred, not built.** The real Startup Workspace has no unified
timeline to assemble a review from — `founder_actions`, `founder_updates`,
and `startup_milestones` are three separate tables with no combined
chronological view, a gap Phase 22's own audit named explicitly and
Phase 23 left open by design (`RecentUpdates.tsx`'s own docstring: "the
private foundation for a later unified Startup Timeline… not that
timeline itself"). Building a review here would require either (a) real
new backend work to assemble that timeline first, or (b) a second,
parallel review-building function reading three disjoint tables directly
— both of which risk exactly the "force both tracks into a weaker shared
implementation" outcome the directive explicitly forbids. Deferred until
the real-startup track has its own unified history, matching what the
venture track already had before this phase started.

## 13. Instrumentation decision (Part 18)

No per-founder behavioral analytics infrastructure exists in this
repository (re-confirmed this phase; `lib/api/analytics.ts` remains
platform-wide aggregate analytics, a different concern). Building even a
minimal event logger this phase would itself be new architecture the
directive explicitly warns against ("do not let instrumentation hijack
this phase"). Per Part 18's own instruction, the minimal event taxonomy is
documented instead of built — see
`docs/product/PRODUCT_EVENT_TAXONOMY_V1.md`.

## 14. North-star readiness

The event taxonomy document defines exactly which events would qualify a
venture as a "Weekly Active Building Venture" (Phase 22's own north star)
and which would not — page views, passive score renders, Learn/Playbook
reads, and unsaved simulation previews are explicitly excluded, matching
Phase 22's own definition precisely. Nothing about this phase's
implementation forecloses that calculation once event logging exists:
every qualifying event this phase's UI produces already has a real,
named, persisted counterpart (a `venture_missions` row, a
`venture_model_updates` row) an event logger could hook.

## 15. Limitations

- `GET /ventures/{id}/history` returns full, unpaginated history; this
  phase filters client-side to the last 7 days. For a very long-lived
  venture this means fetching more data than the review needs — a real,
  known scaling limitation, not addressed this phase (matches the
  directive's own "do not build a reporting suite" instruction; revisit
  if it becomes a real problem).
- The curated assumption-field diff list (Section 7) covers 7 fields
  across `validation`/`economics` — the same practical scope Phase 23's
  own capture-signal proposals already used. Other assumption fields
  (team, market, GTM strategy text, etc.) have no single-line honest diff
  and are not shown.
- The real-startup track has no equivalent review yet (Section 12).
- No metrics instrumentation exists yet (Section 13) — Phase 22's P0-3 is
  still open; this phase produces the taxonomy, not the logger.
- "Quiet week on an established venture" was verified via unit test only
  this session, not a fresh live click-through (Section 11) — the
  underlying function is identical either way.
