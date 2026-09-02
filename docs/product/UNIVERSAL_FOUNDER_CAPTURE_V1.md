# Universal Founder Capture & Evidence Loop V1 — Phase 23

Status: implemented, tested, live-verified against the running backend and
frontend. Not committed, not deployed. This document is the canonical
record of what was built, why, and exactly where the VPS/SPS firewall
lives.

## 1. Mission recap

Give a founder a legitimate reason to return to SIE the moment something
happens while building their company — "I need to put this in SIE," not "I
should update my model." Phase 22's own audit named this the highest-
leverage, lowest-risk next investment (P0-1): unify and elevate evidence
capture across both founder tracks, reusing existing architecture rather
than building a third.

## 2. Architecture reused (Part 1's investigation, answered)

**1. What existing persistence can be reused?** Everything. The entire
feature is built on two tables that already existed before this phase:
`venture_missions` (Idea Lab) and `founder_updates` (real Startup
Workspace). Neither table's schema, CHECK constraints, or existing rows
were changed.

**2. Is there already a generic founder-update/evidence record?** Yes, on
both tracks, independently: `venture_missions.learning_summary` (verbatim
free text, tied to a mission) and `founder_updates` (a standalone,
already-generic title/type/optional-pillar/optional-metric/description
record explicitly documented as "founder-reported... never changes your
SPS"). `founder_updates`' own form already asked "What happened?" before
this phase touched anything.

**3. Can universal capture be represented honestly using existing
records?** Yes. On the venture track, a capture is exactly the same shape
a mission's create → learning → complete sequence already produces — see
Section 3. On the startup track, a capture *is* a `founder_updates` row,
unchanged.

**4. What information is currently lost?** Nothing new is lost. The
pre-existing gap (Phase 22's own finding) was that capture was either
gated behind an active mission (venture track) or undiscoverable/unprompted
(startup track) — a placement and discoverability gap, not a persistence
gap.

**5. Is new persistence actually necessary?** **No.** Zero new tables were
created.

## 3. Persistence decision

One new, small, additive backend function:
`app/database/db.py::capture_venture_observation()`. It performs **one
atomic INSERT** into the existing `venture_missions` table with
`mission_type='other'`, `source='founder_created'` (both already-valid
CHECK-constraint values — no migration), `related_category` set to the
founder's chosen capture category (the same free-text, unvalidated display
label column `create_venture_mission()` already uses for exactly this
purpose), and `status`/`learning_summary`/`learning_recorded_at`/
`completed_at` all set directly at insert time. This produces a row
**indistinguishable** from one the existing create → record-learning →
complete mission flow could have produced by hand — it is a composition of
existing semantics, not a new one.

One new, equally small endpoint: `POST /ventures/{venture_id}/capture`,
returning the same `VentureMissionResponse` every mission endpoint already
returns. No new response model, no new event type, no new table.

**Why one atomic call instead of three sequential ones (create, then
record-learning, then complete)?** Purely for reliability: a capture's
learning text is known at creation time (unlike an ordinary mission, which
is created active and reflected on later), so collapsing three round trips
into one avoids a real partial-failure mode (e.g. a mission created but the
learning-record call failing, leaving an empty "active" mission with no
learning behind). This is the one place this phase added code the existing
mission endpoints didn't already have — everything else is direct reuse.

**Real-startup track: zero backend changes.** `founder_updates` needed no
schema or endpoint change at all — the existing create/edit endpoints were
reused exactly as they were.

## 4. Capture semantics

Founder-facing entry point (`CaptureWhatHappened.tsx`, Idea Lab; the
existing `RecentUpdates.tsx` form, real startups): one required field —
"What happened?" — plus an optional category chip (customer conversation /
customer-revenue / product / experiment / fundraising / market-competitor /
team / other). No title is ever asked separately; the venture-track title
is derived from the first line of the founder's own text
(`app/api.py::_derive_capture_title()`), capped to the existing 300-char
title column limit shared with every other mission.

## 5. Original-observation preservation (Part 4, non-negotiable)

The founder's text is written verbatim into `learning_summary` and never
altered, summarized, or rewritten anywhere in this phase's code. Every
"saved" view shows a dedicated **"YOU RECORDED"** block quoting it exactly.
`get_venture_history()` (unmodified) already surfaces `learning_summary`
verbatim in its `learning_recorded` event — this phase adds no second
copy, no paraphrase, and no AI rewrite path.

## 6. Interpretation semantics (Part 5)

`dashboard/lib/captureSignals.ts` is a small, **deterministic, zero-AI**
heuristic parser — explicitly not a new AI agent, per the directive's own
instruction. Same input always produces the same output; no network call,
no LLM, no randomness (`test_extraction_is_pure_and_deterministic` proves
this directly). It recognizes a conservative set of patterns:

- Interview/conversation counts ("talked to six", "spoke with 10") → proposes `validation.customer_interviews` (a **delta**, added to the current value, never an overwrite).
- A `$N/month` or `$N/year` figure, split by nearby wording into **positive** ("would pay", "signed... at $X/month" — proposes `economics.price_point`), **negative** ("none would pay", "wouldn't pay" — informational only, never inverts into a proposed price), and **neutral** (a bare figure with neither cue — informational only).
- "Signed"/"closed"/"new customer" phrasing → proposes `validation.paying_customers` (a **+1 delta**).
- Six informational-only categories with no safe field mapping: churn, product milestones, fundraising mentions, market/competitor mentions, experiment outcomes, and problem confirmations — real signals, always shown, **never** presented as an editable model field.

Every field-mapped proposal carries the exact source phrase it came from,
so a founder can see why SIE suggested it, never a bare unexplained number.
A note with no recognizable pattern (the directive's own "Sarah" example)
returns zero signals — never a fabricated one.

**A future phase may swap this module for real LLM-based extraction**
without changing anything else in this phase's UI or firewall: every
caller depends only on `ProposedSignal[]`'s shape, never on how it was
produced.

## 7. Founder confirmation (Part 6)

Field-mapped signals render as a checklist (default-checked), each showing
the exact "current → proposed" value — e.g. "Price point: $63,000/month →
$500/month" — before anything is applied. A founder can uncheck any signal
before choosing "Update my model," which is the only action that applies
them. Informational-only signals render as plain text with no checkbox
(nothing to confirm, since nothing will ever be applied from them). No
spreadsheet, no schema dump, no raw JSON, anywhere in this UI.

## 8. THE MODEL-UPDATE FIREWALL (Part 7/9)

This is the phase's central guarantee, and it required **zero new backend
mutation logic** because the existing pathway already enforced it exactly
right:

- **"Save what happened"** → `POST /ventures/{id}/capture` → one
  `venture_missions` INSERT. Never calls `compute_vps()`. Never calls
  `update_modeled_venture_for_user()`. No code path from this endpoint to a
  score, full stop — the same guarantee `create_venture_mission()`,
  `record_venture_mission_learning_for_owner()`, and
  `update_venture_mission_status_for_owner()` already carried individually.
- **"Update my model"** → the exact same `PUT /ventures/{id}`
  (`updateVenture()`) every other model-changing UI in this codebase
  already uses (the manual assumption editor, Apply & Save, and
  `MissionsSection`'s own "Update my model"). `CaptureWhatHappened.tsx`
  merges only the founder-checked proposed values into a copy of the
  **current** assumptions and sends that — the backend then independently
  decides whether assumptions actually changed and, only if so, computes
  VPS via `_build_model_result()` and writes one `venture_model_updates`
  row via the endpoint's own existing "before/after, only on real change"
  logic. This phase added no new call site to `compute_vps()` anywhere.
- **`related_mission_id`** — already a field on `UpdateVentureRequest`
  (added before this phase, for `MissionsSection`'s own flow) — is set to
  the capture's own mission id, so the resulting history event links back
  to the exact observation that prompted it. Verified live: the resulting
  "Model updated" history entry shows `Reason: "<the founder's own
  captured text>"`.

Live-verified: saving three different observations in sequence left VPS at
6.5 every time; only the explicit "Update my model" clicks changed it (to
6.9, then unchanged at 6.9, then unchanged at 6.9 again) — see Section 12.

**Real-startup track:** `founder_updates` was never wired into SPS or the
re-analysis pipeline, and this phase made no change to that. See Section
10.

## 9. Negative-evidence behavior (Part 10)

Live-verified with "We spoke with 10 customers and none would pay
$500/month": saved cleanly, surfaced as a neutral "Pricing resistance
around $500/mo" signal (never punitive language), and an explicit "Update
my model" click applied the interview-count delta with **honest, neutral**
"Venture Potential Score did not materially change" copy — the exact
required framing for a non-moving score (Part 9's own worked example).
`captureSignals.test.ts` explicitly asserts no punitive vocabulary
("fail", "bad", "lost progress", "penalty", "setback") ever appears in
generated signal labels.

## 10. Real-startup distinction (Part 14)

**Founder-reported update** (`founder_updates`) and **SPS-scoring
evidence** (the analysis pipeline's own evidence extraction, run only via
"Re-analyze") remain two fully separate things, unchanged by this phase.
`RecentUpdates.tsx` gained exactly two changes: it was moved earlier in
`FounderStartupWorkspaceView.tsx` (ahead of Actions/Milestones, matching
the venture track's STATUS → PRIORITY → CAPTURE → ACTION ordering), and its
title field now shows a live, read-only "SIE noticed: …" hint using the
same `captureSignals.ts` module — informational only, never auto-filling
`update_type` or the metric fields, never submitted on the founder's
behalf. SPS methodology, the evidence pipeline, and Re-analyze are
untouched.

## 11. History integration (Part 12)

**Zero new UI.** A capture's three resulting `venture_missions` field
changes (`created_at`, `learning_recorded_at`+`learning_summary`,
`completed_at`) flow through `get_venture_history()`'s existing,
unmodified source-to-event mapping into the exact same `action_added` /
`learning_recorded` / `action_completed` events an ordinary mission
already produces, rendered by the existing `VentureProgress`/history
timeline with no code changes there at all. Live-verified: all three
events appear together under "TODAY," followed by the linked "Model
updated" event once "Update my model" was used.

## 12. Live acceptance walkthroughs (Part 18) — all verified against the running app

| Walkthrough | Result |
|---|---|
| A. Customer interview ("Talked to six restaurant owners…") | Verbatim preserved; proposed 6 interviews + $500/mo positive price signal + informational problem-confirmation; nothing applied before confirmation; save alone left VPS at 6.5; "Update my model" → VPS 6.5 → 6.9 with honest category deltas (Problem & Solution +1.0, GTM Feasibility −2.5, Validation +2.5); history shows all 4 linked events. |
| B. Positive commercial ("We signed our first customer at $299/month.") | Correctly read the *current* price ($500/mo, set by walkthrough A) and proposed $299/mo; correctly proposed paying_customers 186 → 187 (a +1 delta on the real current value); "Update my model" → VPS 6.9 → 6.9, correctly rendered as "did not materially change." |
| C. Negative evidence ("We spoke with 10 customers and none would pay $500/month.") | Saved cleanly; interview count correctly incremented on top of the real running total (6 → 16); pricing resistance shown as informational-only, no inverted price proposal; explicit update applied with neutral, non-punitive "did not materially change" copy. |
| D. Unstructured note ("Had a great conversation with Sarah…") | Saved; exact copy "No structured signals found in this note -- that's fine. It's still saved."; zero fabricated signals; no "Update my model" affordance shown (correctly absent — nothing to apply). |
| E. Mobile (~390px) | Full capture completed in a genuine 390px same-origin iframe viewport (real media-query evaluation, not a simulated container). No horizontal overflow at any step (chooser, writing, saved). Verified in both light and dark. |

Real-startup track: verified live on a real verified-membership startup —
`RecentUpdates` now renders ahead of Actions/Milestones, the "SIE noticed:
$299/mo pricing signal, New paying customer" hint appeared live while
typing, and the saved row still reads "Founder reported" with `update_type`
left exactly as the founder chose ("Other" — untouched by the hint).

## 13. Weekly Review readiness (Part 15)

No new work needed. `get_venture_history()` already returns everything a
future weekly review needs from this phase's captures: which events
happened and when, the founder's own verbatim text on every
`learning_recorded` event, and — when a capture led to a model update — the
before/after VPS, the category deltas, and the `related_mission_id`
trail back to the originating observation. Nothing added by this phase
narrows or reshapes that data; a capture is simply more of the same event
types `get_venture_history()` already assembled before this phase existed.

## 14. Metrics instrumentation (Part 16)

**Analytics infrastructure found:** none for per-founder behavioral
events (`lib/api/analytics.ts` is platform-wide aggregate analytics —
rankings/top-startups — a different concern entirely; confirmed during
Phase 22's own audit and re-confirmed here). **No new instrumentation was
added this phase** — building even a "minimal" event logger would itself
be new architecture, and the directive's own Part 16 explicitly allows
documenting the minimal recommendation instead when no infrastructure
exists. Recommended, minimal event set for a future lightweight logger
(unchanged from Phase 22's own recommendation, now concretely mappable
onto this phase's real endpoints): capture started (textarea focused),
observation saved (`POST /ventures/{id}/capture` success), structured
interpretation reviewed (a proposed signal's checkbox toggled), model
update initiated (`handleUpdateModel` invoked), model update applied
(`PUT /ventures/{id}` success from that flow). Each is a single
event-type + timestamp + venture/startup id — never simulation or capture
*content* logged, consistent with this codebase's existing
Fundraising-Simulator-era precedent of never persisting sensitive founder
content in a metrics path.

## 15. Limitations

- The heuristic parser is intentionally conservative — it will miss many
  legitimate signals a human (or a future LLM) would catch. This is a
  deliberate accuracy-over-cleverness tradeoff, not an oversight.
- Field-mapped proposals cover exactly three `VentureAssumptions` fields
  (`validation.customer_interviews`, `validation.paying_customers`,
  `economics.price_point`). Other assumption fields (retention, gross
  margin, CAC, etc.) are not yet reachable from a capture's structured
  review — a founder can still update them manually via "Edit the full
  model," unaffected by this phase.
- The real-startup track's signal hint is informational-only by design
  (Section 10) — it does not yet offer one-click autofill of
  `update_type`/metric fields the way the venture track's checklist does.
  A reasonable, explicitly out-of-scope follow-on.
- No metrics instrumentation exists yet (Section 14) — Phase 22's P0-3 is
  still open.
