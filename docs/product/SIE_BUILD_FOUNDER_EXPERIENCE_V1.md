# SIE Build Founder Experience V1

**Status:** Implemented (Phase 34E). Builds on `docs/product/SIE_BUILD_METHODOLOGY_V1.md` (34B),
`docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md` (34C, with a 34D-A implementation appendix), and
the live Phase 34D/34D-A intelligence loop. This document is a UX/information-architecture record, not a
new methodology — no scoring, evidence, or recommendation logic changed in this phase.

---

## 1. The founder mental model

Before this phase, opening a venture surfaced up to seven stacked, only-loosely-related surfaces on one
tab (a status card, a graduation banner, a "what should I do next?" recommendation card, an explanatory
sentence, a universal capture box, an actions list, a "what to consider next" list, a second graduation
action, and finally the Phase 34D intelligence loop) — three of which (the recommendation card, the actions
list, and the capture box) independently tried to answer "what should I do?" using different, sometimes
disagreeing logic. A first-time founder had no way to know which one to trust, or that "Your Actions" and
"What happened?" were two halves of the same idea.

The product now commits to one mental model, stated once and reused everywhere:

> SIE helps me figure out what matters, do something about it, learn from what happened, and decide what
> to do next.

Concretely, every venture page now answers, in this order and never more than one at a time:
**WHAT MATTERS NOW → WHY → WHAT SHOULD I DO → (once something is active) WHAT HAPPENED → WHAT DID WE LEARN
→ WHAT DOES SIE RECOMMEND → WHAT DO YOU WANT TO DO → (later) WHAT HAPPENED AFTERWARD.** This is exactly
Phase 34D's `CurrentQuestionCard`, now promoted to be the one place that answers "what should I do?" — see
§4.

## 2. Information architecture

**Before:** Overview / Model / What-If / Fundraising / History (five tabs).

**After:** Overview / Fundraising / History (three tabs).

The phase's own working hypothesis was a fourth tab, "Validate." It was deliberately not built. Everything
a "Validate" tab would hold — the current question, the recommended test, recording a result — is Overview's
own hero card. A separate tab repeating that content would be exactly the visual duplication the acceptance
standard forbids (a founder would see the same question in two places and have to guess which was current),
not a genuinely different founder job. "What matters now" already lives where a founder looks first.

## 3. Model — retired as a primary destination

**What happened to it:** The Model tab is gone. Its two pieces of content did not disappear:

- The plain-language summary (idea / who it's for / how it makes money / biggest unknowns) is now folded
  into a single **Venture Identity** card at the top of Overview, merged with the old "Where things stand"
  card it used to duplicate (both showed the same "still figuring out" list, in two different card styles,
  on two different tabs).
- The full assumption editor (every accordion, every field) is unchanged and moved into a collapsed,
  contextual **"Edit venture details"** disclosure on Overview, reachable either by expanding it directly or
  by a small "Edit venture details" button on the Venture Identity card. Nothing about the editor's fields,
  validation, or save behavior changed.
- The six-category "what SIE believes/knows" grid (`VentureUnderstandingPanel`) is preserved byte-for-byte,
  now reachable via a "See the full breakdown by category" disclosure under a new, concise "What SIE
  understands so far" summary (§6) — never shown as six cards by default.

**Why:** The founder had repeatedly asked, in effect, "what are we modeling for?" — a venture model is real,
useful internal context, but it never had its own founder job distinct from "understand the venture" (now
served by Venture Identity + the concise understanding summary) or "correct something" (now a contextual
edit action, not a destination). Removing it as a primary nav item, while keeping every field and every byte
of underlying data, is the fix.

## 4. What-If — hidden from primary navigation

**What happened to it:** The What-If tab is gone from primary navigation. `WhatIfPanel.tsx`,
`ScenarioComparison.tsx`, `CustomScenarioForm.tsx`, and `whatIfScenarios.ts` are all untouched and still in
the codebase — none are wired into `VentureWorkspace.tsx` anymore. The backend `compareVentureScenarios`
endpoint is untouched.

**Why:** Every scenario What-If ever offered ("What if 5 customers agree to pay?", "What if competition
intensifies?") is generic causal simulation over modeled assumptions — exactly the pre-evidence,
pre-Phase-34D worldview the SIE Build methodology has moved past. It is not a specialized deterministic
tool (that's Fundraising's job — dilution, ownership, runway, burn are all still fully present and
untouched) and it is not evidence-driven (that's the intelligence loop's job). Once evidence exists,
What-If's own hypothetical assumption tweaks would routinely disagree with what the intelligence loop
already knows from real founder-confirmed results, which is a worse failure mode than simply not showing
it. Nothing about it was replaced with a new AI scenario tool, per the directive's own explicit prohibition.

## 5. Overview — the new home

Top-to-bottom hierarchy, exactly one instance of each idea:

1. **Venture Identity** — stage, who it's for, how it makes money, biggest unknowns, "Edit venture details."
2. **Graduation banner** (only once graduated).
3. **What matters now** — `CurrentQuestionCard`, the intelligence-loop hero (§6). The one "raised"-variant
   card on the page, by construction the most visually prominent thing on Overview.
4. **Ready to turn this into a real startup?** — only when the deterministic `vps_guidance` resolver says
   the modeled venture looks solid; the one job the retired `PrimaryCommandCard` did that the loop doesn't.
5. **What SIE understands so far** — concise, not the six-category grid (§3, §6).
6. **Most recent: …** — one line, linking to History; not a restatement of History's own detail.
7. **Graduation action** (quiet link, or a prominent suggestion once real evidence exists).
8. **"Other things you're tracking"** — collapsed by default (§7).
9. **"Edit venture details"** — collapsed by default (§3).

## 6. The intelligence loop is the hero

`CurrentQuestionCard.tsx`'s own internal logic is completely unchanged from Phase 34D/34D-A — every state
(active test, awaiting decision, evidence confirmation, interpretation, recommendation, decision, outcome)
still progressively reveals exactly as before, one at a time, never all at once. What changed is its
standing on the page: it is no longer "an additional, self-contained surface" living alongside a separate,
older recommendation system — it is now the *only* place Overview claims "this is what to do," and its
"Build loop" badge (internal-sounding, added no founder value) is gone.

## 7. Actions/missions — merged, not two unrelated systems

**How simplified:** "Your Actions" (`MissionsSection`), "What happened?" (`CaptureWhatHappened`), and "What
to consider next" (`NextMoves`) now live together under one disclosure, **"Other things you're tracking,"**
collapsed by default, with one intro sentence explaining what it's for: *"Working on something outside SIE's
current question above? Track it here, or log anything else that happened."* None of the three components'
own internal logic, API calls, or data changed — `venture_missions`, the capture/model-update firewall, and
milestone suggestions are exactly as Phase 10/23/33 built them. Only their framing and their neighbor (the
intelligence loop, not each other) changed.

## 8. Current understanding

Covered in §3/§5/§6: a concise "What SIE understands so far" (flattened, real `basis` facts, capped at six
bullets, no score, no grading) with the full six-category breakdown one click away. "Edit venture details"
is the one, clearly-labeled correction entry point.

## 9. History — Learning History

**How changed:** History (`WeeklyReview` + `VentureProgress`, both otherwise untouched) now includes two
additional, already-persisted event types read straight from Phase 34D's own tables:

- `decision_recorded` — SIE's recommendation and the founder's own choice, always shown as the two separate
  facts Phase 34D's `venture_decisions` table always keeps separate, never collapsed into one line.
- `outcome_recorded` — the founder's own "what happened afterward" text, with its relationship tag rendered
  in the same plain language (`RELATIONSHIP_LABELS`) as the live loop.

This required one additive backend change: `get_venture_history()` now also reads
`list_venture_decisions_for_owner()`/`list_venture_evidence_for_owner()` (both already existed for Phase
34D's own endpoints) and appends events for undelivered decisions and non-superseded outcomes. No new
table, no new persistence — this is the "reduce duplication, don't build the future longitudinal product"
instruction taken literally: reuse what already exists, add nothing new to store.

## 10. Fundraising — unchanged role

Fundraising remains a full primary tab. Its math (`FundraisingSimulator`, dilution/ownership/runway/SAFE
modeling) is completely untouched — it is exactly the kind of specialized, deterministic tool the directive
asks to preserve. Its placement (third tab, after Overview) already keeps it from being pushed on a
pre-traction founder who hasn't opened it; nothing about its visibility or entry points changed.

## 11. Graduation — unchanged role, clarified boundary

Graduation (`useVentureGraduation`, `VentureGraduationBanner`/`Action`, `GraduateVentureReview`) is
completely unmodified — still founder-initiated, still with no score threshold, still reading
`isEligibleForGraduationSuggestion()` over real reported validation numbers. Its placement in the new
Overview hierarchy (banner near the top once graduated; a contextual action lower down otherwise) makes the
IDEA LAB (figure out and develop the venture) vs. MY STARTUPS (operate a real, founder-managed startup)
boundary a natural reading-order fact rather than something a founder has to infer.

## 12. My Ideas — one new, low-cost signal

**Changes:** Venture cards now show a two-line current-question preview (`venture.current_question`,
sourced from the venture's own active Phase 34D mission) when one exists, so "what should I continue?" is
answerable from the list without opening every venture. This required one new backend field, filled by one
bulk query (`list_active_questions_for_user`) across every venture a user owns — never one query per card.
No VPS/score information was ever shown on these cards (Phase 34A already removed that), so there was
nothing obsolete to remove here.

## 13. New venture flow

The onboarding flow's name-requirement fix (an explicit "decided"/"undecided" state gating Create Venture)
and progressive-disclosure structure (plain summary first, the full seven-section model collapsed by
default) were both already in place from earlier phases and remain unchanged. This phase's one fix: the
initial idea-description textarea and its submit button were the one remaining 14px/`text-sm` reading
surface in the entire creation flow — bumped to 16px/`text-base` with comfortable line-height, matching
every other long-form field in the app.

## 14. Readability standard

The dominant readability problem this phase found was never font size in isolation (an earlier phase,
31C-B/31C-C, had already established a 16px body-text / 14px metadata floor across the app) — it was
**density**: too many cards, several answering the same question, stacked on one tab. The fix applied
throughout this document is structural: one hero, one concise understanding summary (not six grading
cards), one secondary disclosure for everything else, one contextual edit entry point. Where a genuine
font-size gap remained (the new-venture textarea, §13), it was fixed directly rather than left as an
exception.

## 15. Deferred / not built this phase

- **Mobile/tablet live pixel verification (390/768/1024px).** The available browser-automation tooling's
  window-resize control did not actually change the connected tab's reported viewport in this session
  (`window.innerWidth` stayed fixed at 1920px across repeated resize calls) — this is a documented tooling
  limitation, not a claim that responsive behavior was verified pixel-by-pixel. Every new/changed layout in
  this phase reuses the same responsive primitives (`flex-wrap`, `grid ... sm:grid-cols-2`, the existing
  `overflow-x-auto` tab bar) already used and audited at these breakpoints in Phase 31C/33, and no new
  fixed-width or non-wrapping element was introduced.
- **A UI to correct/supersede a piece of confirmed evidence or a decision.** The backend primitive
  (`supersede_venture_evidence_for_owner`) has existed since Phase 34D and remains correct and unused — no
  founder-facing "correct this" affordance was in scope for this phase either.
- **A single unified activity feed merging "Other things you're tracking" into History's own timeline.**
  Both surfaces already read from the same underlying facts; a deeper merge is future scope, not required
  to make History "clearly about venture learning" today.
