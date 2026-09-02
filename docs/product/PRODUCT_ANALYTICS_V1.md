# Product Analytics & Growth Measurement V1 — Phase 28

Status: implemented, tested, live-verified against the running backend and
frontend. Not committed, not deployed. This document is the canonical
record of what was measured, why, and exactly where the privacy/firewall
boundaries live.

## 1. Measurement thesis

SIE's private founder loop (Capture, Actions, Weekly Review, Simulate),
Fundraising Simulator, and Shareable Venture Snapshot are all now real,
live product surfaces (Phases 23-27) — but every claim about whether they
actually drive activation, retention, and distribution has so far rested
on live-testing narrative, not measurement. This phase builds the minimum
trustworthy event layer to answer eight specific questions (Phase 28's
own mission statement) and nothing broader — no BI system, no data
warehouse, no experimentation platform.

## 2. Architecture discovered (Part 1)

Re-confirmed, directly, before writing any code: `lib/api/analytics.ts`
and the backend's `/analytics`, `/top-startups`, `/top-improving-startups`
endpoints remain platform-wide **aggregate startup rankings** analytics —
a completely different concern, unchanged since Phase 22 first drew this
distinction. **No per-founder behavioral event mechanism existed anywhere
in this codebase before this phase.** `PRODUCT_EVENT_TAXONOMY_V1.md`
(Phase 24) was genuinely specification-only, as its own status line said.

Two pieces of existing architecture turned out to be directly reusable
and were NOT rebuilt:

- **Admin authorization.** `app/auth.py::require_admin()` /
  `RequireAdmin` already existed (Phase 7.1A), built on a server-side
  `ADMIN_USER_IDS` env-var allowlist, already used to gate claim-approval
  endpoints. This phase's one admin endpoint (`GET /admin/analytics`)
  reuses it verbatim — no new RBAC system, no admin table, no admin flag
  on `users`.
- **Test-data marking.** Every automated test that creates a real user
  row already uses a `zztest_`-prefixed `user_id` (confirmed via direct
  grep: 21 of 45 files in `app/tests/` before this phase touched
  anything). This phase's report queries reuse that exact, already-
  established convention rather than inventing an environment/marker
  system.

## 3. Events selected

Six server-logged founder events, three snapshot-lifecycle events (two
server, two client — see Section 6), and one attribution field carried on
an existing event. Every one is logged from exactly one call site in
`app/api.py`, inside the same transaction as the real state change it
represents:

| Event | Fires when | Never fires on |
|---|---|---|
| `venture_created` | `POST /ventures` succeeds | — |
| `action_created` | `POST /ventures/{id}/missions` succeeds | opening "Create your own action", a NextMoves suggestion rendering |
| `action_completed` | mission status transitions to `completed` | a `dismissed` transition |
| `learning_recorded` | `POST .../missions/{id}/learning` succeeds | a Capture (never calls this endpoint — see Section 5) |
| `capture_recorded` | `POST /ventures/{id}/capture` succeeds | — |
| `venture_model_updated` | `PUT /ventures/{id}` succeeds AND assumptions actually changed | a no-op save, a pure rename |
| `snapshot_enabled` | share settings transition `false → true` | a double-submit while already enabled |
| `snapshot_disabled` | share settings transition `true → false` | a double-submit while already disabled |
| `snapshot_viewed_publicly` | `GET /ventures/share/{public_id}` resolves a real, enabled venture | a 404 (disabled/unknown id) |
| `snapshot_link_copied` | the founder's own clipboard write genuinely succeeds | the Copy Link button merely being clicked |
| `snapshot_cta_clicked` | a recipient clicks "Model your own venture" on a real, resolvable snapshot | a click against an unknown public id |

Plus **attribution**, not a twelfth event: `venture_created` optionally
carries `source="snapshot"` + `share_public_id` when (and only when) the
founder arrived via a real snapshot's own CTA link — see Section 14.

## 4. Events rejected/deferred

- **`capture_started`, `structured_interpretation_reviewed`,
  `model_update_initiated`** — pure intent/funnel-diagnostic events with
  no product question in this phase's own list depending on them. Never
  built.
- **`weekly_review_viewed`, `weekly_review_record_capture_clicked`,
  `weekly_review_action_started`** — the directive's own Part 11 core
  metric list never asks for Weekly Review usage; `weekly_review_action_started`
  is fully subsumed by `action_created` (the resulting mission creation)
  regardless. Deferred.
- **`learn_disclosure_opened`, `playbook_viewed`** — explicitly named
  non-qualifying even in the original Phase 24 taxonomy; still no product
  question needs them.
- **`simulation_previewed`** — explicitly non-qualifying by design
  (Fundraising Simulator and Simulate V1 previews are ephemeral;
  Part 7's own instruction).
- **`simulation_applied` as a DISTINCT event** — Simulate-Apply and the
  Fundraising Simulator's own "Apply" both reach `PUT /ventures/{id}`
  through the exact same code path a manual assumption edit or a
  capture's "Update my model" does. Distinguishing them would require a
  new `source` signal on `UpdateVentureRequest` this phase judged
  unnecessary complexity for zero additional product-question coverage —
  `venture_model_updated` already captures the real underlying fact (the
  model changed) uniformly. Deferred, documented as a real limitation
  (Section 21).
- **`snapshot_previewed`** — Part 11's own metric list never asks for
  preview counts; the founder's own preview endpoint
  (`GET /ventures/{id}/share/preview`) is unauthenticated-adjacent but
  called on every panel expand, which would make this a very high-volume,
  low-value event. Deferred.
- **`venture_creation_started_from_snapshot`** — fully subsumed by
  `snapshot_cta_clicked` (there is no real intermediate state between the
  click and landing on `/idea-lab/new`).
- **The entire real-startup/SPS-track event set** (`founder_action_created`,
  etc., from the original Phase 24 taxonomy) — none of this phase's eight
  product questions concern the SPS track; Phases 25-27 never touched it
  either. Deferred in full, not re-litigated here.

## 5. Event semantics (Part 3, the details that mattered)

- **`learning_recorded` vs. `capture_recorded` never double-fire for the
  same real action.** A Universal Capture (Phase 23) writes
  `learning_recorded_at` directly inside its own atomic INSERT
  (`capture_venture_observation()`) and never calls
  `record_venture_mission_learning_for_owner()` at all — the two events
  are structurally, not just conventionally, mutually exclusive. Verified
  directly: `test_learning_recorded_fires_for_ordinary_mission_reflection_only`
  performs a real capture immediately after a real reflection and asserts
  the reflection count stays at exactly 1.
- **`action_completed` fires only on the real transition to `completed`.**
  A `dismissed` transition — real, deliberate founder behavior, but not a
  building outcome — never logs it. Verified live and in tests.
- **`venture_model_updated` reuses the exact same "did assumptions
  actually change" condition** the existing `venture_model_updates`
  history write already used (Phase 16/26) — literally the same `if`
  branch, not a second, possibly-drifting definition. This is why a pure
  rename (Phase 26) never logs this event: identical assumptions means
  the whole branch, history AND analytics, is skipped.

## 6. Event ownership (Part 4 — server vs. client)

Every event representing a **successful persisted state change** is
logged server-side, inside the same request that made the change:
`venture_created`, `action_created`, `action_completed`,
`learning_recorded`, `capture_recorded`, `venture_model_updated`,
`snapshot_enabled`, `snapshot_disabled`, `snapshot_viewed_publicly`.

Exactly two are client-triggered, both genuinely requiring frontend
knowledge a backend transaction can't see:

- **`snapshot_link_copied`** — only the browser knows whether
  `navigator.clipboard.writeText()` actually succeeded. Logged via a
  narrow, purpose-built `POST /ventures/{id}/share/link-copied` (owner-
  auth required) called only inside the `try` block's success path, never
  the `catch`.
- **`snapshot_cta_clicked`** — only the browser knows the recipient
  clicked the link before navigating away. Logged via
  `POST /ventures/share/{public_id}/cta-clicked` (public, no auth —
  matches the public snapshot route's own precedent), fire-and-forget,
  never blocking navigation.

**Deliberately NOT one generic "log any client event" endpoint** — that
would be exactly the "arbitrary event explorer" the directive forbids,
and a real abuse surface on the public one. Each endpoint accepts an
**empty body**: the event name and every field are decided entirely
server-side from the URL path and auth context.

## 7. Privacy model

Allowlisted, per event, at the call site — never a generic metadata
dump:

- `action_created` → `{mission_source}` (an existing closed enum:
  `vps_guidance` / `founder_created` / `pitch_deck_coach`) — never
  title/description.
- `capture_recorded` → `{category}` (the founder's existing optional
  chip selection) — never the captured text. Signal-count/outcome-class
  classification (`captureSignals.ts`) is deliberately **not**
  duplicated server-side to enrich this metadata — it's a frontend-only
  concern; see Section 21's limitation.
- `venture_model_updated` → `{vps_delta_bucket: "increased"|"decreased"|"unchanged"|"unknown"}`
  — never the raw score (matching the original Phase 24 taxonomy's own
  precedent).
- Every other event → `{}` — nothing to log beyond the fact itself.
- `venture_created`'s `source`/`share_public_id` are a closed, tiny,
  server-validated pairing (Section 14), never a URL, referrer, or user
  agent.

**No fingerprinting.** A public snapshot visitor is never assigned an
identity of any kind — `snapshot_viewed_publicly` and
`snapshot_cta_clicked` both carry `user_id = NULL` always, by
construction (there is no code path that could set it). No cookie, no
device fingerprint, no IP-based tracking was added anywhere.

## 8. Event persistence

One new, append-only table, `product_events` — four narrowly-scoped
columns beyond the surrogate key: `event_name`, `user_id` (nullable),
`venture_id` (nullable), `share_public_id` (nullable), `source`
(nullable), `metadata` (JSONB, allowlisted per Section 7), `created_at`.
No FK constraints to `users`/`modeled_ventures` (deliberately — Part 19's
"analytics must fail open" guarantee would be undermined by a hard FK
failure on an ordinary `DELETE /ventures/{id}`). No `UPDATE`/`DELETE`
function was ever written for this table — genuinely append-only.
`log_product_event()` validates `event_name` against a fixed, closed
Python set (`_ALL_EVENT_NAMES`) before ever reaching SQL.

## 9. Activation definition (Part 8)

Investigated honestly, as directed. Phase 22's original definition ("a
new venture reaches a populated Next-Step recommendation in the first
session") was tested against the real implementation and **rejected as
too weak**: `_build_model_result()` always runs synchronously at
creation, so every venture that successfully creates gets *some*
`model_result`/recommendation immediately — that definition would make
activation ≈100% regardless of whether the founder ever did anything
real.

**Implemented instead:** a venture is **activated** if it performs ≥1
qualifying building event (the same set the North Star uses — Section
11) within **24 hours** of its own `venture_created` timestamp.
Venture-level (no session infrastructure exists anywhere in this
codebase), anchored on two real, already-logged timestamps, and requires
genuine founder-initiated follow-through rather than passively receiving
a recommendation SIE computed on its own.

## 10. Retention definition (Part 9)

**Venture-level**, explicitly labeled as such in every report field
(`cohort_unit: "venture"`) — a single founder can own multiple ventures,
and every prior Phase 22-27 metric already treats a venture as the unit
of analysis, not a founder. Cohorted on `venture_created` (not a separate
activation-timestamp row) — a deliberate V1 simplification that keeps the
retention query a single readable CTE chain instead of introducing a
second cohort-anchor concept; documented here rather than silently
assumed.

**W1** (the primary metric) = among ventures that (a) were created
between 14 and `lookback_days` ago (so their day-7-to-13 window has
actually elapsed) and (b) activated per Section 9's definition, what
fraction performed ≥1 qualifying event during days 7-13 after creation.
D1/D7/D30 are simpler cumulative point checks over the same activated
cohort. All four hand-validated exactly (Section 18).

## 11. North Star

Unchanged from Phase 24's own definition: **Weekly Active Building
Venture** = a distinct venture with ≥1 qualifying event in the trailing
window. Qualifying set, decided explicitly (Part 7's own open question):
`action_created`, `action_completed`, `learning_recorded`,
`capture_recorded`, `venture_model_updated`. **`venture_created` is
explicitly excluded** — creation is activation, not ongoing building, a
deliberate distinction this phase draws and documents rather than
conflating the two. Explicitly excluded, matching Part 7 verbatim: login,
page views, VPS/Weekly-Review/Learn/Playbook views, any snapshot
view/preview/link-copy, unapplied simulation previews.

## 12. Meaningful-building-days definition (Part 10)

No browser-session infrastructure exists or was built. Instead: distinct
`(venture_id, calendar_day)` pairs with ≥1 qualifying event in the
window — "3 meaningful building days" for a founder who captured Tuesday,
completed an action Wednesday, and updated their model Friday, exactly
the directive's own worked example. Reported both as a raw total and per-
active-venture. This is honest about what's actually known (which days
real building happened) rather than pretending a "session" concept this
codebase has no way to measure.

## 13. Distribution metrics

Share Activation Rate, Snapshot Links Copied, Public Snapshot Views,
Snapshot CTA Clicks (+ click rate), Ventures Created From Snapshot (+
conversion rate) — all six of Part 11's named distribution metrics,
computed in `get_distribution_report()`. Share Activation Rate's
denominator is deliberately **activated ventures in the window**, not
all-time venture count (Part 25's own worked examples pair share
activation against retained/activated ventures) — a venture that never
really got going is not a fair denominator for "did the founder choose to
share."

## 14. Attribution architecture (Part 17)

`/v/{publicId}`'s own CTA (`SnapshotCtaLink.tsx`) links to
`/idea-lab/new?ref=snapshot&share={publicId}` — the SAME opaque
`public_id` the recipient is already looking at, forwarded one hop; not
new information leakage (the directive's own reasoning, applied exactly:
"do not build cross-site tracking, do not fingerprint" — this forwards
nothing the visitor didn't already have). `NewVentureForm.tsx` reads
these via `useSearchParams()` once at mount and passes them through
`CreateVentureRequest`'s two new, **analytics-only** optional fields
(`source`, `share_public_id`) — never persisted onto the venture row
itself; `modeled_ventures` gained no new column for this. The backend
independently re-validates the pairing before trusting it:
`source="snapshot"` is only ever recorded on the resulting
`venture_created` event when a real, non-empty `share_public_id`
accompanies it — a client claiming attribution without naming an actual
public id it would have to have seen is silently downgraded to organic.
Live-verified end to end (Section 19).

## 15. Dashboard/reporting architecture (Part 13)

`GET /admin/analytics` (backend) + `/admin/analytics` (frontend,
`AdminAnalyticsView.tsx`) — the smallest safe internal surface. The
frontend page only proves "signed in" (`auth.protect()`, identical to
every other protected page); **real authorization is entirely backend-
side**, via the existing `RequireAdmin` dependency. A signed-in non-admin
sees a real "Access denied" state driven by an actual 403 response, never
a client-side admin guess. Deliberately plain: label/value rows, no
charts, no color-coded gauges ("operational, not beautiful. We need
truth, not another polished product surface" — the directive's own
words). Supports 7/30/90-day windows.

## 16. Test-data behavior (Part 16)

Reuses the existing `zztest_` user-id convention exactly (Section 2) —
no new environment/marker system. The exclusion SQL fragment checks both
directions: an event's own `user_id` being `zztest_`-prefixed, OR (for
anonymous public-view events with no `user_id` at all) the venture it's
attributed to belonging to a `zztest_` user. Live-verified two ways: (a)
`test_zztest_users_excluded_from_reports` directly proves the exclusion
fragment filters out a real, freshly-created `zztest_`-owned venture's
very-real capture event; (b) the hand-calculated fixture test
(`test_hand_calculated_fixture_matches_reported_metrics`) needed an
explicit `exclude_test_users=False` + `venture_ids` scoping override
(present ONLY for that one test) to validate the raw arithmetic
independent of the exclusion filter and independent of any other
real/test data already in this shared dev database — documenting, by
construction, that production reporting always defaults to excluding
test data and never accidentally scopes to a subset.

## 17. Failure behavior (Part 19)

**Fail open, everywhere, defense in depth at two layers.** Layer one:
`log_product_event()` itself wraps its own `INSERT` in a `try`/`except`
that only prints, never raises. Layer two: every one of the 9 call sites
in `app/api.py` goes through a second wrapper, `_log_event_safe()`, which
catches even a failure *inside this codebase's own analytics layer*
(e.g. a raised `ValueError` from an unrecognized event name) before it
could ever reach the founder as a 500. **Live-verified, not just
asserted**: `test_analytics_insert_failure_does_not_block_capture`
replaces `log_product_event` with a function that unconditionally raises,
then confirms a real Capture through the real endpoint still returns 200.

## 18. Hand-validated fixtures (Part 24)

Four backdated ventures (direct SQL `INSERT`s with controlled
`created_at`, not real elapsed time — the only deterministic way to
exercise multi-day window logic in a test):

- **V1**: created day −20; a qualifying event at day −19.5 (activates,
  well inside the 24h window); a second qualifying event at day −12
  (inside the day-7-13 retention window) → **retained**.
- **V2**: created day −20; activates at day −19.5; nothing further →
  **not retained**.
- **V3**: created day −20; activates at day −19.5; a qualifying event at
  day −12 → **retained**. Also: sharing enabled, 4 public views, 1 CTA
  click.
- **V4**: created day −20; **no** qualifying event ever → correctly
  excluded from the retention cohort entirely (retention is defined only
  over activated ventures).

Hand-calculated: `ventures_created=4`, `activated=3`,
`activation_rate=0.75`, `activated_cohort_size=3`, `w1_retention=2/3
(0.6667)`, `snapshots_enabled=1`, `share_activation_rate=1/3 (0.3333)`,
`public_snapshot_views=4`, `snapshot_cta_clicks=1`,
`snapshot_cta_click_rate=0.25`.

**Reported result: exact match on every value**, verified by direct
equality/near-equality assertion against `get_activation_report()`,
`get_retention_report()`, and `get_distribution_report()`'s real output
(`test_hand_calculated_fixture_matches_reported_metrics`, passing).

## 19. Live walkthroughs (Part 22)

All performed against the running app, real dev Clerk session (not
`zztest_`), real database:

| # | Walkthrough | Result |
|---|---|---|
| A | Create venture | `venture_created` logged, `source=NULL` (organic) |
| B | Start Action | `action_created` logged, `metadata={"mission_source":"vps_guidance"}` |
| C | Capture | Exactly one `capture_recorded`; raw row inspected directly, no founder text present |
| D | Complete Action | `action_completed` logged exactly once |
| E | Explicit model update | `venture_model_updated` logged, `vps_delta_bucket="decreased"` (VPS genuinely moved 6.5→5.0) |
| H | Enable snapshot | `snapshot_enabled` logged with the real `share_public_id` |
| I | Copy link | Endpoint verified directly (real browser clipboard write blocked by this automation environment's "document not focused" restriction — a known, documented limitation of the test harness, not the product; the endpoint itself, called the same way the button calls it, returned `{"logged": true}`) |
| J | Open public snapshot | `snapshot_viewed_publicly` logged, `user_id=NULL` |
| K | Click CTA | Real navigation to `/idea-lab/new?ref=snapshot&share={id}`; `snapshot_cta_clicked` logged, `user_id=NULL` |
| L | Create venture through snapshot path | New venture's `venture_created` row directly inspected: `source="snapshot"`, `share_public_id` matching exactly |
| — | Full event sequence for the source venture | All 9 events for one real venture queried directly and shown in Section-19-adjacent order: capture → action_created → action_completed → capture → venture_model_updated → snapshot_enabled → snapshot_link_copied → snapshot_viewed_publicly → snapshot_cta_clicked — every one exactly once |
| — | Admin dashboard | Real numbers rendered live after the walkthrough above: North Star=1, Captures=2, Actions completed=1, Snapshots enabled=1, Public views=14 (aggregate across this and Phase 27's own real testing, correctly, within the 7-day window), CTA clicks=1, Ventures created from snapshot=1, CTA click rate=7.1%, conversion rate=7.1% — all internally consistent |
| — | Zero-data state | Verified before any live traffic existed: every count 0, every rate `"Not enough data"` (`null`), no divide-by-zero, no fabricated trend |

Not independently re-verified live this phase (already fully covered by
the automated suite, Section 18/re-run in Section 24): F (Weekly Review —
deliberately not instrumented, Section 4), G (snapshot preview —
deliberately not instrumented, Section 4), M (disable — covered by
`test_snapshot_enable_disable_fire_only_on_real_transitions`), N
(refresh/no-duplication — architecturally guaranteed, since every
mutation event lives inside a POST/PUT/PATCH handler a GET reload can
never re-trigger; also directly tested), O (analytics failure — Section
17, live-tested via the automated suite rather than a manual browser
simulation, since inducing a real DB failure live is impractical and the
automated test exercises the identical code path).

## 20. Product decision guide

Reproduced from the directive, unmodified — this phase measures, it does
not yet have enough real (non-test) traffic to render a verdict:

- High activation + low retention → private loop isn't sticky enough.
- High retention + low share activation → snapshot/share proposition
  weak.
- High sharing + low snapshot views → founders share in low-reach
  contexts, or distribution mechanics are weak.
- High views + low CTA → the artifact doesn't make SIE compelling enough.
- High CTA + low venture creation → onboarding friction.
- High creation + low activation → onboarding/product-value problem.
- High activation + retention + distribution together → real evidence to
  support further network/distribution investment.

## 21. Limitations

- `simulation_applied` is not a distinct event — folded into
  `venture_model_updated` (Section 4). A future phase wanting to compare
  Simulate-driven vs. manually-edited model changes would need a new
  `source` signal on the update request.
- `capture_recorded`'s metadata carries only `category`, never
  `signal_count`/`outcome_class` — that classification
  (`captureSignals.ts`) is frontend-only and was deliberately not
  duplicated server-side (Section 7).
- Retention is cohorted on `venture_created`, not a separate activation-
  timestamp row (Section 10) — a deliberate V1 simplification.
- No timezone precision is claimed or possessed: every timestamp
  comparison happens in server (Postgres `NOW()`, effectively UTC) time,
  stated explicitly in the admin dashboard's own subtitle, never
  presented as founder-local time.
- Weekly Review usage and snapshot-preview counts are not measured at
  all (Section 4) — deliberately, since no product question in this
  phase's own scope depends on them; a future phase could add them
  cheaply using the exact same `log_product_event()` machinery.
- `snapshot_link_copied`'s real browser clipboard write could not be
  exercised end-to-end through this session's own browser-automation
  harness (a "document not focused" restriction of that environment, not
  the product) — the endpoint itself was verified directly instead
  (Section 19).
- No metrics exist yet with statistically meaningful (non-test, non-this-
  session's-own-live-testing) volume — every number in this phase's own
  live walkthrough is this session's own real testing traffic, honestly
  small. This is expected and correct for a brand-new instrumentation
  layer, not a limitation of the layer itself.

## 22. Next recommendation

Let the instrumentation run untouched against real founder traffic for at
least one full W1 window (14+ days) before drawing any conclusion from
Section 20's decision guide — there is not yet enough real (non-test)
data for any of those seven patterns to mean anything. The next
deliberate product decision should be data-driven off this phase's own
`GET /admin/analytics`, not off another round of live-testing narrative.
