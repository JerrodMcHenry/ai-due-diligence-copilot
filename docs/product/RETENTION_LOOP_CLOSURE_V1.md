# Retention Loop Closure V1 — Phase 26

Status: implemented, tested, live-verified against the running backend and
frontend. Not committed, not deployed. This document is the canonical
record of what was built, why, and exactly where the VPS/SPS/history
firewalls hold, closing the three P0 gaps Phase 25's Founder Retention
Loop Acceptance audit identified.

## 1. Phase 25 problems

Phase 25 (`FOUNDER_RETENTION_LOOP_ACCEPTANCE.md`) rated the private founder
loop ACCEPTABLE, NOT YET STRONG and named exactly three P0 blockers:

1. **Capture dead-ends.** A signal without a mapped canonical field (the
   worked example: "Customer cancelled because onboarding took too
   long.") produced a signal chip and no follow-up of any kind — the
   founder had no way to know SIE had done anything useful with real,
   important information.
2. **No cross-session memory narration.** SIE persisted real history but
   never told a returning founder "here's what you were doing" — every
   fact had to be reconstructed by scrolling.
3. **"Untitled venture" by default.** Both fresh test ventures defaulted
   to a generic name with no founder decision behind it.

## 2. Root causes

1. `CaptureWhatHappened.tsx`'s "saved" view only ever rendered a
   follow-up CTA (`Update my model...`) when at least one **field-mapped**
   signal existed. Informational-only signals (`captureSignals.ts`'s own
   `INFORMATIONAL_PATTERNS`) rendered as plain bullet text with nothing
   after them — not a bug in the parser, a missing outcome class in the
   UI built on top of it.
2. The workspace had real continuity data (`recentLearning`,
   `history.events`) but nowhere synthesized "current action + latest
   learning + latest model change" into one place a returning founder
   would see without scrolling past several other sections.
3. Two independent gaps, both confirmed by investigation, not assumed:
   (a) `VentureDraftReview.tsx`'s "What's your venture called?" field was
   real and pre-fillable, but purely optional with only a placeholder
   hint — trivially skippable with zero signal that anything was left
   undecided; (b) `idea_structuring.py`'s system prompt allowed
   `"ai_inferred"` for `name` like any other top-level field, a live risk
   of the LLM inventing a brand name the founder never said (not
   triggered in Phase 25's own fixtures, but a real latent risk
   confirmed by inspecting `_TOP_LEVEL_FIELDS`/`_sanitize_field`).

## 3. Fixes chosen

All three fixes extend existing architecture. No new table, no new
endpoint, no new score, no new recommendation engine, no new AI agent.

1. **Capture outcome classes** (`captureSignals.ts` + `CaptureWhatHappened.tsx`):
   every save now resolves to one of three honest outcome classes
   (Section 5) and always shows a "what this means" line plus at most two
   restrained CTAs.
2. **"Where things stand"** (`VentureWorkspace.tsx`): a new compact strip,
   assembled entirely from data already in hand, replacing (not
   duplicating) Phase 13's old standalone "Recent Learning" card.
3. **Explicit naming decision** (`VentureDraftReview.tsx` +
   `idea_structuring.py`): the founder must type a name or explicitly say
   they don't have one before Create Venture is enabled; the backend
   prompt/sanitizer now forbid inventing one.
4. **Rename** (`VentureWorkspace.tsx` + existing `PUT /ventures/{id}`):
   a minimal, isolated rename affordance, added because Part 15's own
   investigation found no rename path existed at all.

## 4. Architecture reused

- `POST /ventures/{id}/capture`, `venture_missions`, and the entire VPS
  firewall from Phase 23 — completely unchanged. No new backend
  persistence or endpoint for Objective 1.
- The exact same `setPendingMission` / `MissionsSection` pendingMission-
  consumption effect that `IdeaLabNextStep`, `NextMoves`, and
  `WeeklyReview` already call for "Make this an action" — `CaptureWhatHappened`
  is now a fourth caller of the same pathway, not a second one.
- `GET /ventures/{id}/history` (Phase 16/23/24) — the sole data source for
  "Where things stand"'s latest-model-change line, via a new small pure
  function (`resolveLatestModelChange.ts`) that mirrors
  `resolveRecentLearning.ts`'s own shape exactly.
- `PUT /ventures/{id}` (`update_venture`) — the exact same endpoint every
  other save on the venture page already uses, reused unmodified for
  rename. Its own existing assumptions-only diff (`previous.get("assumptions")
  != assumptions_dict`) is what makes a pure rename safe (Section 10) —
  no new logic was needed there at all.
- `validation.retention_pct` — an existing `VentureAssumptions` field,
  already scored (`vps_scoring.py`) and already one of the seven fields
  `_diff_assumption_changes()` diffs for Weekly Review — `captureSignals.ts`
  simply never proposed a value for it before this phase.
- `validation.paying_customers`'s existing +1 delta mechanic (the "new
  paying customer" signal) — extended to accept a **negative** delta for
  a countable churn mention, the same mechanic in the opposite direction,
  not a new one.

## 5. Capture outcome semantics

Every successfully saved capture now ends in exactly one of three
outcome classes, computed in `CaptureWhatHappened.tsx` from
`captureSignals.ts`'s own signal classification:

| Class | Condition | "What this means" copy | CTA |
|---|---|---|---|
| A. MODEL-RELEVANT | ≥1 field-mapped signal | "We found information that could update your venture model." | Update my model (unchanged from Phase 23) |
| B. ACTION-RELEVANT | no field-mapped signal, ≥1 informational signal marked `actionRelevant` | "This doesn't change your model yet, but it may be worth investigating." | Make this an action: `<deterministic title>` |
| C. LEARNING-ONLY | zero signals, or only non-actionable informational signals | "Saved. There isn't enough here to change your model yet." | none beyond "Your current focus" |

Classes are not mutually exclusive UI states — a note can carry both a
field-mapped and an action-relevant signal, in which case both CTAs
render (still capped at two, per the directive's own "avoid CTA
explosion" instruction). `pendingActionSignals` tracks, per capture
session, which action-relevant signals the founder has already turned
into an action, so the button becomes "Added to your actions ✓" rather
than staying clickable indefinitely.

`captureSignals.ts` gained two new field-mapped signal producers and one
new informational category:

- **Countable churn** (`extractChurnCountSignals`): "Three customers
  churned this month." → a **negative** delta on the already-existing
  `validation.paying_customers` field (`-3`), symmetric with the existing
  `+1` new-customer signal. Requires a number word/digit AND a churn verb
  in direct proximity, the identical discipline `extractInterviewSignals`
  already used — a bare "the customer churned" never matches here.
- **Retention percentage** (`extractRetentionSignal`): "Retention dropped
  to 82%." → a direct replacement value on `validation.retention_pct`
  (like price_point, an observed rate, never a delta), with polarity read
  from nearby trend words (dropped/fell → negative; rose/improved →
  positive; neither → neutral).
- **Complaint/friction** (a new `INFORMATIONAL_PATTERNS` entry): "Five
  customers complained about onboarding." → its own distinct,
  action-relevant signal, never mislabeled as churn (no customer was said
  to have left).

`ProposedSignal` gained two new optional fields: `actionRelevant?:
boolean` and `suggestedActionTitle?: string`, present only on
informational signals worth investigating (unquantified churn,
complaint/friction, and the pre-existing experiment-result category —
now also marked action-relevant). A shipped milestone, a fundraising
mention, a competitor mention, and a problem confirmation remain
Class C (learning-only) — real, but not calling for their own action.

## 6. Churn behavior — the directive's own investigation

Phase 25's dead-end example was **not** a parser gap in the sense of
"churn isn't recognized" — it always was. The dead end was structural:
an unquantified churn mention has no safe number to turn into a delta,
and the UI had no outcome for a signal in that shape. Root-caused and
fixed as follows, differentiating exactly the three examples the
directive named:

| Input | Outcome | Why |
|---|---|---|
| "Customer cancelled because onboarding took too long." | Class B — action-relevant, no field change | No count to safely decrement by; the founder is pointed at investigating it instead of silence |
| "Three customers churned this month." | Class A — `paying_customers` 187 → 184 | A real, countable number exists; reuses the existing delta mechanic, just negative |
| "Retention dropped to 82%." | Class A — `retention_pct` Unknown → 82% | An explicit percentage maps directly onto an existing, already-scored field |
| "Five customers complained about onboarding." | Class B — action-relevant, distinct from churn | Real negative signal, but nobody was said to have left — conflating it with churn would misrepresent what was observed |

No field was added to satisfy a test — `validation.retention_pct` and
the negative-delta extension of `validation.paying_customers` were both
already-legitimate, already-scored parts of the canonical model before
this phase; the fix was proposing values for what already existed.

## 7. Continuity behavior

"Where things stand" (`VentureWorkspace.tsx`) is a small, deterministic
strip rendered directly after "What Matters Now," assembled entirely from
data three existing sources already produce:

- **Current action** — lifted from `MissionsSection`'s own
  `activeMissions[0]` via a new `onPrimaryMissionChanged` callback,
  mirroring the exact pattern `onRecentLearningChanged` already used.
  Links to `#your-missions` (an anchor that already existed).
- **Most recent learning** — the exact same `recentLearning` state
  Phase 13's old standalone card rendered; that card was removed, its one
  fact folded in here instead (Part 11's own "merging redundant surfaces"
  preference, and a direct fix for Phase 25's own documented duplication
  finding against the Weekly Review's "What you learned" list).
- **Latest model update** — a new pure function,
  `resolveLatestModelChange.ts`, that finds the single most recent
  `model_updated` event in `history.events` (already newest-first from
  the backend) and reports its before/after VPS plus the first curated
  assumption diff. Unlike `buildWeeklyReview.ts`'s own 7-day-windowed
  aggregation, this is unwindowed — "since your last model update," not
  "this week."

Renders nothing at all when there is truly nothing beyond the current
priority to report (a brand-new venture) — `IdeaLabNextStep` directly
above already fully owns that state.

**Part 10's own instruction, honored exactly:** no session/login
timestamp exists anywhere in this codebase, so nothing here ever says
"since your last visit." Every label is "current," "most recent," or
"latest" — each backed by a real persisted timestamp, never an inferred
one.

Live-verified on ApexGrid (venture 1067, real multi-session history):
rendered "Most recent learning: 'An investor told us our market may be
too narrow.' · Sep 1, 2026" and "Latest model update: VPS 6.9 → 6.9,
Customer interviews: 6 → 16" correctly, with comprehension well under 15
seconds.

## 8. Naming behavior

`VentureDraftReview.tsx`'s existing "What's your venture called?" field
(Phase 10.11) is unchanged in placement and prefill logic. What changed:
a new `nameDecision` state (`"decided" | "undecided"`) starts
`"undecided"` only when SIE found no real name to prefill. While
undecided, "Create Venture" is disabled and an explicit "I don't have a
name yet" link is shown beside the field. Typing anything into the field
IS the decision (no extra click required); clicking the link is the
other valid decision. When SIE DID safely extract a real name (the
"ClaimPilot helps..." case), the field is prefilled and `nameDecision`
starts `"decided"` — no extra step for a founder whose description
already names their company.

`idea_structuring.py`'s system prompt and `_sanitize_draft()` both gained
a `name`-specific carve-out: `allow_inferred=False` for this one
top-level field (previously all five top-level fields shared
`allow_inferred=True`), plus an explicit prompt instruction that `name`
must never be `"ai_inferred"`. **A real regression was found and fixed
during this phase's own live testing** — see Section 14.

## 9. Rename behavior

Investigated first, per Part 15's explicit instruction: no rename path
existed anywhere in the codebase before this phase (`VentureBasicsAccordion`
had no `name`/`onName` prop; `hasUnsavedChanges` only diffed
`assumptions`). The fix is deliberately isolated from every other
editable field on the page: a "Rename" button in the page header opens a
small inline editor; on save, it calls `PUT /ventures/{id}` with `name`
changed and **every other field taken directly from `venture`'s own
last-saved snapshot** (`venture.description`/`.industry`/
`.business_model`/`.target_customer`/`.stage`/`.assumptions`) — never
from the `draft`/`industry`/`businessModel`/`stage` component state a
founder might have mid-edited elsewhere on the page. This guarantees a
rename can never accidentally persist an unrelated unsaved edit sitting
in "Edit the full model."

## 10. Score/history firewalls

- **Rename never changes VPS or writes model-change history.** The
  existing `update_venture()` handler only calls `create_venture_model_update()`
  when `previous.get("assumptions") != assumptions_dict` — since a rename
  call sends `venture.assumptions` byte-identical to what's already
  saved, this condition is false and no history row is written.
  `_build_model_result()` is still called (as it is on every save), but a
  deterministic scorer given identical input produces identical output —
  live-verified: VPS stayed exactly 6.9 → 6.9 and `MODEL UPDATES` stayed
  at 3 (not 4) across a real rename on ApexGrid.
- **Rename never creates an Action.** `handleRenameVenture()` calls
  `updateVenture()` directly — it never touches `setPendingMission` or
  any mission-creation pathway. Live-verified: `ACTIONS COMPLETED`
  unchanged (7) and active-mission count unchanged (0) across the rename.
- **Rename never touches SPS.** The rename path is entirely inside the
  Idea Lab / modeled-venture track (`modeled_ventures`,
  `PUT /ventures/{id}`) — the real-startup/SPS track
  (`founder_actions`/`founder_updates`/`startup_milestones`,
  `PUT /startups/{id}`) has no code path from this feature at all.
- **Capture-save alone never changes VPS.** Unmodified from Phase 23 —
  `POST /ventures/{id}/capture` has no code path to `compute_vps()` or
  `update_modeled_venture_for_user()`. Live-verified across every new
  capture example this phase (churn, countable churn, retention,
  unstructured): VPS unchanged until the founder's own explicit "Update
  my model" click.
- **Capture never auto-creates an Action.** "Make this an action" is a
  founder click, not a save-time side effect — live-verified: the churn
  capture on ApexGrid showed the button and stayed at "0 active" until
  clicked; only after the click did a new, separate mission row appear.
- **No duplicate/fake history.** A capture and a founder-triggered action
  from that capture are two distinct `venture_missions` rows (verified
  directly via `GET /ventures/{id}/missions`: mission 893, the capture
  itself, `status="completed"`; mission 894, the action, `status="active"`
  — never the same row, never double-counted).

## 11. Live walkthroughs (all verified against the running app)

| Walkthrough | Result |
|---|---|
| A. Model-relevant ("We signed our first customer at $299/month.") | Both signals proposed with correct current→proposed values; VPS unchanged until explicit "Update my model"; mobile-verified at 390px |
| B. Churn ("Customer cancelled because onboarding took too long.") | Class B outcome; "Make this an action: Investigate why this customer churned" button; clicking it created a real, separate active mission; current priority stayed visible throughout; VPS unchanged (6.9 → 6.9) |
| C. Quantified retention ("Retention dropped to 82%.") | Class A outcome; "Retention: Unknown → 82%"; "Update my model" applied it and VPS genuinely moved 6.9 → 6.6 (Validation −1.0), honestly reported |
| C′. Countable churn ("Three customers churned this month.") | Class A outcome; "Paying customers: 187 → 184" — correctly differentiated from the unquantified case above |
| D. Unstructured ("Had a useful conversation with Sarah about onboarding...") | Class C outcome: "Saved. There isn't enough here to change your model yet." — no signals section, no CTA beyond current-focus line |
| E. Returning founder (ApexGrid, real multi-session history) | "Where things stand" rendered current action (none active, correctly omitted), most recent learning, and latest model update (VPS 6.9 → 6.9, Customer interviews 6 → 16) — understood in well under 15 seconds |
| F. New venture with name ("ClaimPilot helps medical practices...") | Name field prefilled "ClaimPilot" with real provenance; survived creation, workspace header, and reload |
| G. New venture without name (handyman idea) | Name field empty, "Create Venture" disabled until "I don't have a name yet" clicked; venture created as "Untitled venture" — an explicit, deliberate outcome, not a silent default |
| H. Rename (ApexGrid → "ApexGrid Energy") | Persisted across reload; VPS unchanged (6.9 → 6.9); `MODEL UPDATES` unchanged (3); `ACTIONS COMPLETED`/active unchanged (7/0) |
| I. Mobile (~390px) | Capture writing + after-capture outcome (checklist, "what this means," restrained CTA, current-focus line) all genuinely usable with no horizontal overflow; new-venture describe screen clean |

## 12. Rerun of Phase 25 gate

**Persona A (first-time founder):** a fresh venture created without a
name correctly required an explicit decision rather than silently
becoming "Untitled venture"; the resulting Day-1 action remained clear
and idea-stage-appropriate. No regression.

**Persona B (early active founder):** the churn dead-end is fixed — a
churn capture now always ends in a visible, honest outcome. The
stage-aware recommendation ("Prove customer acquisition works
repeatably...") is unchanged, since `resolveIdeaLabNextStep()` itself was
never modified — Part 8's own "no new recommendation engine" instruction
held throughout.

**Persona C (advanced founder, ApexGrid):** no beginner-only regression —
the same rich workspace (VPS breakdown, Actions, Weekly Review, Simulate,
Fundraising Simulator) renders correctly with the new "Where things
stand" strip added and the old duplicate "Recent Learning" card removed.
Fundraising Simulator and Simulate tabs load with zero console errors and
were not touched by any change this phase. Accumulated history (6+
observations, 3+ model updates, real VPS trajectory) remains fully
coherent alongside three brand-new events (a churn capture, a retention
capture, a countable-churn capture) added live during this phase's own
testing.

## 13. Distribution-readiness decision

See the final report delivered in chat for the explicit YES/NO answer
and reasoning (Part 20/21). Not duplicated here to avoid two
sources of truth for the same verdict.

## 14. Limitations and bugs found this phase

- **A real regression was found and fixed during this phase's own live
  testing, not by the offline test suite.** The first version of the
  `idea_structuring.py` prompt change (Section 8) — an emphatic
  paragraph re-explaining when `name` could be `"user_provided"` —
  made the model over-conservative: a live test against
  "ClaimPilot helps medical practices reduce insurance claim denials."
  returned `name: unknown` instead of correctly extracting "ClaimPilot."
  Confirmed via a direct before/after comparison against the prior
  prompt (git `HEAD`), which correctly extracted it. Fixed by shortening
  the added instruction to a single sentence that doesn't redefine
  `"user_provided"`'s existing meaning, only adds the one exception
  (never `"ai_inferred"`) — re-verified live end-to-end afterward
  (Walkthrough F). This is exactly the kind of defect the directive's
  own "run all of these" live-acceptance requirement exists to catch;
  the mocked-LLM backend test suite (`test_idea_structuring.py`) could
  not have caught it, since it substitutes a fake LLM response and never
  exercises the real prompt text.
- `_sanitize_field`'s `allow_inferred=False` code-level enforcement for
  `name` (independent of prompt wording) still fully applied throughout
  — even with the regressed prompt above, an `"ai_inferred"` name claim
  would have been stripped to `unknown` rather than reaching the founder
  as an invented brand name. The live bug found was the prompt being
  over-conservative (false negative on a real name), not under-
  conservative (never observed an invented name at any point this
  phase).
- Countable churn's negative delta is clamped at zero
  (`Math.max(0, current + delta)`) — a churn count larger than the
  known paying-customer total floors at 0 rather than going negative;
  not expected in realistic use, but a deliberate guard.
- The action-relevant → "Make this an action" title set is small and
  fixed (three deterministic titles: churn, complaint, experiment) —
  matching `captureSignals.ts`'s own existing conservative-over-clever
  precedent, not an attempt to cover every possible informational
  signal shape.
- One pre-existing, unrelated backend test failure
  (`test_oversized_and_empty_input_rejected`, expecting HTTP 422 for an
  oversized description, currently returns 200) was confirmed present on
  `main` before this phase's own changes (verified via `git stash`) —
  not touched or fixed this phase, out of the three P0 objectives'
  scope.
- Fundraising Simulator and Simulate remain completely untouched by this
  phase, as directed — verified via live spot-check (Fundraising tab
  loads correctly on ApexGrid, zero console errors) rather than a full
  re-walkthrough, since no code in either module was modified.
