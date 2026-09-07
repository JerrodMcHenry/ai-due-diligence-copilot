# SIE Intelligence Advantage V1

**Status:** Implemented (Phase 34G — SIE Intelligence Advantage V1; hardened by Phase 34G-A — Intelligence
Resolution + Learning Integrity Hardening, which fixed the two real gaps 34G's own live walkthrough
surfaced — see §22, which supersedes the specific Stage 6 finding in §14 and the capture-gap finding in §14
Stage 3). This document is the canonical answer
to "why would a founder use SIE instead of just asking ChatGPT or Claude?" It does not introduce a new
score, a new AI subsystem, Finance V2, or a Build → Analyze integration — see §11–§12 for what those
connections will look like when they are built, and `docs/product/SIE_FOUNDER_PRODUCT_DOCTRINE_V1.md` for
the access-vs-guidance rule this document assumes throughout.

## 1. Why SIE exists alongside a generic AI chat

A founder can already paste their situation into ChatGPT or Claude and get a thoughtful, well-written
answer. That answer can be smarter, better-written, and more current than anything SIE generates — SIE does
not compete on prose quality, and this document does not claim otherwise (Phase 34G §17's own instruction:
"do NOT claim generic AI is incapable of reasoning; that would be dishonest").

What a generic AI conversation cannot do, structurally, is:

- **Remember what actually happened last time**, as typed, provenanced facts — not as whatever the founder
  chooses to re-paste into a fresh conversation.
- **Refuse to average away a real contradiction** into a single, comfortable-sounding conclusion. A
  conversational model, asked "9 customers, 8 renewing, 1 early churn — what next?", will very naturally
  say "retention looks healthy, focus on acquisition." SIE's evidence rows do not merge; a live contradiction
  stays visible as long as it is live (§7, §14 — including a case, discovered during this phase's own live
  walkthrough, where that refusal to average is a genuine cost, not just a feature: see §14's Stage 6).
- **Apply the same sequencing rule every time**, deterministically, instead of a plausible-sounding
  argument that could point a different direction on a different day for the same facts.
- **Know what it doesn't know**, precisely — which specific uncertainty is unresolved, not a generic "you
  should validate more."

None of "better prompts," "nicer responses," "generic startup advice," or "SIE remembers your startup" (as
a shallow transcript log) are the advantage. The advantage is what accumulates and what that accumulation is
allowed to change: **STATE + EVIDENCE + HISTORY + METHODOLOGY + PRIORITIZATION + DETERMINISTIC COMPUTATION +
DECISIONS + OUTCOMES**, feeding a recommendation engine a generic chat has no equivalent of.

## 2. The product advantage doctrine

> **EVERY RETURN VISIT TO SIE SHOULD BECOME MORE VALUABLE BECAUSE SIE KNOWS MORE ABOUT THE COMPANY THAN IT
> DID BEFORE.**

Concretely, in Build: each time a founder confirms evidence, records a decision, or logs a test outcome,
the NEXT recommendation is computed from that accumulated, structured evidence set — not regenerated from
scratch, and not dependent on the founder re-explaining anything. The Compounding Intelligence Walkthrough
in §14 is the internal proof this actually happens, stage by stage, on one venture.

## 3. The feature filter

Before building anything under this doctrine, a feature must answer yes to at least one of:

1. Does it require **accumulated state** (something SIE persisted from a previous session)?
2. Does it require **structured, provenanced evidence** (not just free text)?
3. Does it require **deterministic computation** SIE can do faster/more reliably than a founder reasoning
   by hand?
4. Does it **combine multiple pieces of intelligence** a founder would otherwise have to hold in their head
   at once?

| Feature | Filter answer | Why |
|---|---|---|
| "Ask SIE anything" free-form chat box | **LOW** — fails all four | A generic AI chat does this equally well; nothing here depends on THIS venture's stored evidence. |
| A nicer-sounding rewrite of existing advice | **LOW** | Prose quality, not intelligence advantage — the underlying recommendation is unchanged. |
| Recommendation sequencing from confirmed evidence (§4) | **HIGH** — 1, 2, 3, 4 | Requires the persisted evidence rows, a deterministic funnel order, and combines every stage's state into one answer. |
| Company Intelligence State (§6) | **HIGH** — 1, 2, 4 | Summarizes exactly the accumulated evidence and history driving the current recommendation. |
| Declining information value (§5) | **HIGH** — 1, 3 | Requires knowing how much evidence already exists and a deterministic threshold, not a fresh judgment call each time. |

This phase deliberately did **not** build a generic AI coach, chatbot, or "ask SIE anything" box — it fails
the filter on every count.

## 4. Recommendation sequencing methodology

### 4.1 The funnel

The directive's conceptual funnel is CUSTOMER CLARITY → PROBLEM EVIDENCE → WORKFLOW/SOLUTION EVIDENCE →
WILLINGNESS TO COMMIT/PAY → TRANSACTION EVIDENCE → VALUE REALIZATION/USAGE → RETENTION → REPEATABLE
ACQUISITION → SCALING. `app/ai/build_recommendation.py` implements this as five stages —
`customer_clarity` (checked separately, before the funnel), then
`_FUNNEL_ORDER = ["problem_evidence", "commitment_evidence", "transaction_evidence", "retention"]`, plus a
terminal `"growth"` bucket:

- **problem_evidence** ← `founder_claim` / `reported_preference` evidence (workflow/solution evidence and
  willingness-to-commit both collapse into the next stage — see §4.4 for why).
- **commitment_evidence** ← `commitment` / `observed_behavior` evidence.
- **transaction_evidence** ← `transaction` evidence.
- **retention** ← `longitudinal_outcome` evidence.
- **growth** (terminal) ← reached once retention has been affirmatively resolved. Repeatable acquisition
  and scaling both collapse here — see §4.4.

This is a deliberate collapse of nine directive-conceptual stages into five, because that is exactly as
much distinction as the EXISTING evidence-type taxonomy (`founder_claim` / `reported_preference` /
`observed_behavior` / `commitment` / `transaction` / `longitudinal_outcome`) can support without either
reading a founder's own business vocabulary out of their free text (forbidden — see the genericity rule
established in Phase 34D and re-tested in §13) or adding new structured fields (out of scope for this
phase).

### 4.2 The two-pass algorithm

For each stage, `_relationship_mix()` reduces that stage's confirmed evidence rows to one of: no evidence
yet, `"supports"`, `"contradicts"`, `"mixed"` (both present, or an explicit mixed flag), or `"insufficient"`
(rows exist but are all neutral).

1. **Pass 1 — contradiction check, in funnel order.** The first stage with `"contradicts"` or `"mixed"`
   wins outright, regardless of what supporting evidence exists downstream. A real, live tension is never
   silently bypassed just because later evidence looks fine.
2. **Pass 2 — furthest resolved stage.** If no stage failed Pass 1, find the LATEST stage with `"supports"`
   evidence and advance one step past it. Later evidence presupposes earlier stages: if a founder recorded
   a transaction, they necessarily also solved the earlier problem/commitment stages, even if those weren't
   separately, explicitly re-confirmed. This is what makes the transaction-evidence test case (below) work
   correctly without requiring interview evidence to be re-recorded at every stage.

### 4.3 Declining information value (Section 9)

`_problem_evidence_strength()` sums `structured_value` for supporting rows whose
`structured_field_path == "validation.customer_interviews"`, and compares the total against
`_STRONG_INTERVIEW_COUNT = 10` (an internal constant, mirroring `vps_guidance.py`'s own `STRENGTH_THRESHOLD`
precedent — never surfaced as a founder-facing number, never a score). Below the threshold, SIE keeps
recommending more interviews; at or above it, it advances — an 11th interview is unlikely to change the
decision, so continuing to recommend interviews would be a lower-value use of founder time than testing the
next stage. This volume-based refinement is scoped to `problem_evidence` only, because it is the only stage
whose directive test case (Case C) specifically required it; every other stage advances on any supporting
evidence, per that stage's own test case.

This mechanism is real and load-bearing, but narrow — see §14 Stage 6 for a case it does NOT cover
(overwhelming supporting evidence after a stage has already gone `"mixed"`), documented honestly rather
than faked.

### 4.4 Documented architectural gaps

- **Repeatable acquisition vs. scaling (Cases G/H).** Indistinguishable given the current evidence
  taxonomy — both produce the same `"growth"` recommendation. Distinguishing them would require either a
  new structured "acquisition channel" field or reading business vocabulary out of free text (forbidden).
  `test_sequencing_case_h_repeatable_acquisition_documented_gap` asserts this identity directly, rather than
  hiding it.
- **Financial constraints (Case I).** `FundraisingSimulator` is pure client-side and ephemeral — nothing it
  computes is ever persisted to `venture_evidence`, so no financial-urgency signal reaches the
  recommendation engine at all today. `test_sequencing_case_i_financial_constraint_documented_gap` asserts
  the recommendation is byte-identical before and after setting a critical burn/capital scenario, proving
  the gap is real rather than assumed.
- **Segment-specific contradictions (Case J).** The generic mixed-evidence mechanism (§4.2 Pass 1) correctly
  preserves the tension, but cannot literally name "enterprise vs. SMB" — that would require a new
  structured segment tag, out of scope for this phase.

## 5. Evidence maturity

Every evidence row carries an `evidence_type` (which maturity class the observation belongs to) and a
`provenance` (`founder_said` / `founder_observed` / `sie_inferred` / `sie_calculated` / `external_source` /
`still_unknown`). These are stored, structural distinctions, not a score:

- `founder_claim` / `reported_preference` — someone said something (a belief, a stated preference). "10
  people said they'd buy" lives here.
- `observed_behavior` / `commitment` — someone did something, or explicitly committed to something.
- `transaction` — money actually changed hands. "10 said they'd buy" can never become this without a
  distinct, separately-confirmed transaction row — the funnel stages are structurally different tuples of
  `evidence_type`, so the sequencing algorithm itself cannot conflate them (§13 Case D/E exercise this
  boundary directly).
- `longitudinal_outcome` — what happened afterward, over time (renewal, churn). "2 customers paid once"
  cannot, by itself, establish this — a longitudinal_outcome row requires its own separate confirmation; a
  transaction row alone never advances the funnel past `transaction_evidence`.

No numeric evidence score exists anywhere in this system — maturity is a category, read directly off the
`evidence_type` of the rows that exist, never blended into a number.

## 6. Contradictory evidence behavior

`_relationship_mix()` (§4.2) is the single mechanism that prevents evidence from being averaged into a
false consensus, applied uniformly to every funnel stage, not just outcomes (this generalizes the
mixed-evidence handling introduced for outcomes in Phase 34D to the whole funnel). The worked example from
the directive — enterprise controllers retain, SMB controllers churn — is exactly what a `"mixed"` result
represents: both a `supports` row and a `contradicts` row persist, verbatim, in "What SIE knows" (§7);
neither is edited, summarized away, or netted into a single sentiment. See §14 Stage 5 for this behavior
exercised live.

## 7. Company Intelligence State

`build_company_intelligence_summary()` (`app/ai/build_recommendation.py`) derives three founder-facing
sections purely from already-persisted rows — no new AI call, no new score, no database-field dump, and no
re-creation of the six-category Model tab (`VentureUnderstandingPanel`, still available one click away via
"See the full breakdown by category"):

- **What SIE knows** — confirmed evidence statements, shown verbatim, weakest-to-strongest, capped at 6.
  Deliberately conservative wording is the evidence rows' own wording, not an inference SIE adds on top —
  "Two customers have paid $1,500/month," never "Controllers will pay $1,500/month."
- **Still figuring out** — the most recently completed mission's `interpretation_limitations`, split into
  bullets. This is a real, documented limitation (§14 Stage 4): it is tied to mission-completion events, not
  recomputed from the live evidence set on every page load (a deliberate cost/performance choice, §10), so
  it can visibly lag the true funnel position between mission completions.
- **What changed recently** — the most recent mission's `question_text → interpretation_summary`, plus the
  latest decision's `founder_choice`, capped at 3. Built only from actual persisted rows; nothing here is
  invented copy.

All three sections render only when there is something real to show — a brand-new venture with no evidence
and no history shows none of them (§9), rather than three empty boxes.

## 8. Declining information value, restated as a behavior

Section 4.3's mechanism is the "minimum robust mechanism necessary" this phase implements for it: a single
internal count threshold, scoped to the one stage whose test case required it, rather than a generalized
scoring system across every stage. §14 Stage 6 documents the boundary of this approach honestly — it does
not (yet) cover a stage that has already gone `"mixed"` and later receives overwhelming new supporting
evidence.

## 9. Overview UX

The Overview hierarchy (`VentureWorkspace.tsx`) now reads top to bottom as: VENTURE IDENTITY/STAGE → WHAT
MATTERS NOW → WHY IT MATTERS → WHAT TO DO NEXT → WHAT SIE KNOWS → STILL FIGURING OUT → WHAT CHANGED
RECENTLY → secondary actions (the six-category breakdown, "working on something else," venture-context
form). The 34E-era `WhatSieUnderstands` VPS-category block and its separate "Most recent: X → See full
history" one-liner are replaced by a single `CompanyIntelligenceState` card (§7) as the default view, with
the old six-category view preserved as an opt-in disclosure. State-dependent rendering means a brand-new
venture (§14 Stage 1) shows none of "What changed recently" — there is nothing yet to report — rather than
an empty section with a heading and no content.

## 10. Performance and AI cost

Every mechanism in this phase — sequencing, declining information value, company intelligence summarization
— is deterministic Python with zero LLM calls, matching `app/ai/vps_guidance.py`'s own existing discipline.
No new AI subsystem, and no new AI call, was added. `GET /ventures/{id}/recommendation` computes all of it
synchronously from rows already fetched for that request; nothing here triggers regeneration on page load
beyond the query cost already present before this phase.

## 11. Future connection — Build → Analyze

**Not built in this phase.** SPS/Analyze scoring is untouched — no Build evidence flows into it yet. The
intended future connection: BUILD EVIDENCE → COMPANY INTELLIGENCE → ANALYZE → SPS + EVIDENCE CONFIDENCE. In
that future phase, a Startup Profile's SPS computation would stay exactly as it is today (§ of
`SIE_FOUNDER_PRODUCT_DOCTRINE_V1.md`: "SPS is an assessment of the venture as currently described"), while
a separate, additive evidence-confidence signal — drawn from the same evidence-maturity categories described
in §5 — would tell a reader how much to trust the inputs behind that score. Not implemented here.

## 12. Future connection — Build → Finance

**Not built in this phase; no Finance V2 work occurred.** The intended future connection: DETERMINISTIC
FINANCIAL MODEL + BUILD INTELLIGENCE = CONTEXTUAL DECISION SUPPORT. Worked example: a runway calculation
("hiring a $120K/year engineer cuts runway from 14 months to 9") must remain pure, deterministic arithmetic,
unaffected by anything in Build — but the CONTEXTUAL FRAMING of that number could draw on Company
Intelligence: "runway would drop to 9 months while repeatable acquisition is still unresolved" reads
differently than the same 9-month number on a venture with a proven acquisition channel. The math never
becomes probabilistic or AI-derived; only the surrounding interpretation would draw on stored evidence. This
is exactly the gap named in Case I (§4.4) — today, nothing in Fundraising persists to `venture_evidence`, so
this connection has no data to draw on yet even if built.

## 13. Test matrix (Cases A–J)

All ten cases are implemented as deterministic fixtures in `app/tests/test_build_intelligence_loop.py` and
pass (33/33 in that module, 271/271 across the full backend regression suite as of this phase).

| Case | Evidence state | Expected priority | Result |
|---|---|---|---|
| A | Vague macroeconomic idea, no customer, no evidence | CUSTOMER CLARITY | PASS — `_fallback_recommendation`'s target-customer check fires before the funnel is ever consulted; never recommends interviewing an undefined customer. |
| B | Customer defined (investment research analysts), no problem evidence | PROBLEM EVIDENCE | PASS — funnel starts at `problem_evidence`, mix=None. |
| C | 15 interviews, 12 supporting, no behavioral/commitment evidence | Advance to WORKFLOW/SOLUTION TESTING | PASS — `_problem_evidence_strength` ≥ 10 triggers advance past `problem_evidence`. |
| D | 5 tested prototype, 4 repeatedly complete workflow, no one paid | WILLINGNESS TO COMMIT/PAY | PASS — Pass 2 finds `commitment_evidence` as the latest resolved stage and advances to `transaction_evidence`, with no separately-recorded interview evidence required. |
| E | 3 qualified customers paid for pilots | VALUE REALIZATION/RETENTION | PASS — advances to `retention`; does not recommend hypothetical willingness-to-pay interviews. |
| F | 3 paid, 2 renewed, 1 churned, segment/usage difference not understood | UNDERSTAND RETENTION DIFFERENCE | PASS — `retention` stage_mix = `"mixed"`; both statements preserved verbatim; never concludes "retention validated." |
| G | 10 paying, strong usage/renewal, all founder-led sales, no repeatable channel | REPEATABLE ACQUISITION | PASS — advances to `"growth"`. |
| H | Repeatable-acquisition evidence exists, retention healthy, economics/scaling uncertainty remains | SCALING/appropriate constraint | Documented gap (§4.4) — identical output to Case G, asserted directly by test, not hidden. |
| I | Paying customers exist, runway critically short | Recognize the financial constraint | Documented gap (§4.4) — recommendation unchanged before/after setting burn/capital, asserted directly by test. |
| J | Enterprise customers retain, SMB customers churn | Understand the segment-specific difference | PASS via the generic mixed mechanism (§6) — preserves the tension; cannot yet literally name the segment. |

## 14. Compounding Intelligence Walkthrough

Live-tested end to end on venture **MacroFlow** (id 4074, "I want to create a product that streamlines
macroeconomic data. A Macrobond but cooler."), through the actual running app — evidence for Stages 2 and
4–6 was confirmed through `POST /ventures/{id}/evidence`, the same and only endpoint the UI's own evidence
confirmation controls call (per that endpoint's own docstring in `app/api.py`: "the ONLY way a
venture_evidence row is ever created"). Stage 3 additionally used, then honestly documented a gap in, the
free-text "What happened?" capture flow — see below.

### Stage 1 — Bare idea

- **What SIE knew before:** Nothing — no target customer, no evidence.
- **New evidence:** Founder set `target_customer = "Investment research analysts"`.
- **What changed:** `build_intelligence_state()`'s explicit customer-clarity check, which runs before the
  funnel is ever consulted, now passes.
- **New highest-value uncertainty:** Whether the newly-defined customer actually experiences the problem.
- **Why the old question is no longer primary:** Customer clarity was the ONLY blocking unknown; once
  resolved, it cannot recur as the top question.
- **New recommended action:** "Do MacroFlow's target customers actually experience this problem?" — talk
  directly to potential customers before pitching any solution.

### Stage 2 — Problem evidence (10 interviews)

- **What SIE knew before:** Target customer defined; no problem evidence.
- **New evidence:** Confirmed row — `reported_preference`, `supports`, statement "10 customer
  conversations," `structured_field_path = validation.customer_interviews`, `structured_value = 10`.
- **What changed:** `_problem_evidence_strength` returned `"strong"` (10 ≥ `_STRONG_INTERVIEW_COUNT`); the
  algorithm advanced one stage past `problem_evidence`.
- **New highest-value uncertainty:** Whether target customers will meaningfully engage with an actual
  solution, not just report pain in an interview.
- **Why the old question is no longer primary:** 10 supporting interviews met the declining-information-
  value threshold (§4.3) — an 11th interview is unlikely to change the decision.
- **New recommended action:** "Will MacroFlow's target customers meaningfully engage with a real solution?"

### Stage 3 — Commitment/workflow-engagement evidence (prototype usage)

- **What SIE knew before:** Strong problem evidence. Recommendation asked about solution engagement.
- **New evidence, attempted via free text first:** "Gave 5 analysts a working prototype... 4 of the 5 came
  back and used it again on their own within the week... repeatedly completing the core workflow without
  prompting." `captureSignals.ts` extracted **zero** candidate signals from this text — confirmed by reading
  the module: it recognizes interview counts, price mentions, new/churned customer counts, and retention
  percentages, and nothing else. **This is a real, honest gap in the capture layer**, not a simulated one —
  the note saved as an unconfirmed `founder_claim` (no relationship, no structured field), which on its own
  would NOT have advanced the funnel. The same fact was then confirmed through the actual evidence API as
  `observed_behavior` / `supports`, to exercise the (separately, automated-test-covered) sequencing logic.
- **What changed:** `commitment_evidence` stage_mix flipped to `"supports"`; the algorithm advanced one
  stage to `transaction_evidence`.
- **New highest-value uncertainty:** Whether engaged prospects will actually pay.
- **Why the old question is no longer primary:** Repeated, unprompted voluntary reuse by 4/5 test users is
  real engagement evidence; re-testing "will people engage" again is now lower-value than testing conversion
  to a real transaction.
- **New recommended action:** "Will MacroFlow's engaged prospects actually pay?"
- **Remaining gap (see §16):** a founder using ONLY the free-text capture box for this kind of result would
  see their note saved but NOT see the recommendation advance — a real product gap, out of scope for what
  34G was asked to build (sequencing logic against the EXISTING taxonomy, not expanding
  `captureSignals.ts`'s pattern library).
- **UPDATE (Phase 34G-A):** fixed. A structured fallback classifier now appears in the exact "nothing was
  recognized" moment this stage hit — see §22.3. The founder can now say what a result showed in plain
  language and have it become real, structured, funnel-advancing evidence, without any new regex or AI
  extraction.

### Stage 4 — Transaction evidence (3 paid pilots)

- **What SIE knew before:** Problem + commitment evidence resolved. Recommendation asked about payment.
- **New evidence:** `transaction` / `supports`, "3 pilot customers paid $500/month each to start using
  MacroFlow."
- **What changed:** `transaction_evidence` stage_mix flipped to `"supports"`; advanced to `retention`.
- **New highest-value uncertainty:** Whether customers actually use and retain the product over time.
- **Why the old question is no longer primary:** A real transaction is not the same claim as proven
  retention (the directive's own explicit prohibition: "2 customers paid once" must never automatically
  establish retention) — SIE advances to a distinct question rather than declaring victory.
- **New recommended action:** "Track whether the customers you already have keep using and paying over the
  next few weeks."
- **Observed limitation:** "Still figuring out" (§7) stayed unchanged from Stages 2–3, since it is tied to
  the most recently *completed mission's* interpretation text, not recomputed live from the evidence set
  used for the recommendation itself — a real, documented staleness between the two (§7, §10 tradeoff).

### Stage 5 — Mixed retention evidence (2 renew, 1 churn)

- **What SIE knew before:** Transaction evidence resolved. Recommendation asked about usage/retention,
  mix=None.
- **New evidence:** Two `longitudinal_outcome` rows — `supports`, "2 of the 3 pilot customers renewed for a
  second month at the same $500/month price"; `contradicts`, "1 of the 3 pilot customers churned after the
  first month, citing low usage."
- **What changed:** `retention` stage_mix computed as `"mixed"`. Pass 1 of the algorithm caught this
  immediately — the funnel does NOT advance to `"growth"` despite retention having some supporting evidence.
- **New highest-value uncertainty:** "What's driving the difference between MacroFlow customers who stay and
  those who don't?" — reframed toward the causal/segment difference, not toward re-testing willingness to
  pay or declaring retention solved.
- **Why the old question is no longer primary:** The old question produced a genuine contradiction, which
  must be preserved rather than averaged into "customers like the product." Both statements render verbatim,
  side by side, in "What SIE knows" — never blended into a single retention percentage.
- **New recommended action:** Keep tracking who stays and who leaves, and why — aimed explicitly at
  explaining the split, matching Case F's required behavior exactly.

### Stage 6 — Stronger, larger, later retention cohort (9 customers, 8 renewing 3 months, founder-led)

- **What SIE knew before:** Mixed retention evidence from Stage 5.
- **New evidence:** `longitudinal_outcome` / `supports`, "Grew to 9 paying customers total. 8 of the 9 have
  renewed every month for 3 straight months at $500/month, all sourced through the founder personally
  reaching out to analysts one at a time — no repeatable channel yet."
- **Actual, live-tested result:** The recommendation **did not change**. It stayed at "What's driving the
  difference between MacroFlow customers who stay and those who don't?" — the directive's own hoped-for
  Stage 6 outcome (advance toward repeatable acquisition) was **not** reached.
- **Why:** `_relationship_mix()` treats a stage as `"mixed"` the instant both a supporting and a
  contradicting row exist, with no volume, ratio, or recency override — by design, because that is exactly
  what Case F (§13) requires (2 supports / 1 contradicts must stay `"mixed"`, never resolve to "retention
  validated"). Any asymmetry-ratio override large enough to let Stage 6's 8-vs-1 clear the mixed state would
  need a threshold with no principled value that doesn't also risk silently resolving Case F's own required
  mixed state — exactly the "no numerical formula, no uncertainty score" the directive itself prohibits.
- **A real, already-partially-built path forward, discovered during this phase:** `venture_evidence` already
  has a `superseded_by_id` column and a `supersede_venture_evidence_for_owner()` function
  (`app/database/db.py`), from an earlier phase, and the recommendation engine already filters superseded
  rows out of its evidence set (`app/api.py`, evidence fetch for both the recommendation and mission-
  interpretation paths). If a founder could explicitly mark the old churn row as explained/superseded once
  later evidence made it clearly no longer decision-relevant, the mixed state would correctly clear. **No
  such API route or UI affordance exists today** (confirmed: no `/supersede` route is registered) — this is
  backend-only, unreachable by any founder action, and was deliberately NOT invoked directly to force Stage
  6 to "pass," since doing so would misrepresent what today's product can actually do.
- **This is the sharpest finding of the whole walkthrough:** a generic AI, given "9 customers, 8 renewing
  3 months, 1 early churn," would almost certainly say "retention looks healthy, focus on acquisition" —
  exactly the false-consensus averaging the directive prohibits. SIE's refusal to do that is a genuine,
  structural safety property, even though — honestly — it currently comes at the cost of not yet advancing
  the funnel the way Stage 6 hoped for. Both halves of that sentence are true and both are recorded here.
- **UPDATE (Phase 34G-A):** fixed, without weakening the refusal above. The founder-explicit resolution
  mechanism this update predicted (§22.2) is now built and live-retested on this exact venture: the
  recommendation stayed correctly pinned at retention — 8-vs-1 did NOT numerically clear the tension — until
  the founder explicitly marked the old churn row resolved ("an early pilot glitch before we fixed
  onboarding"), at which point the recommendation advanced to "Can MacroFlow acquire new customers beyond
  however you found the first ones?" The original churn row is still in the database, statement unedited,
  now pointing at the resolution note via `superseded_by_id` — EXISTS and CURRENTLY DECISION-DOMINANT are
  now two different, honestly distinguished facts (§22.1).

## 15. Generic AI comparison (internal acceptance test)

For each stage above, the specific stored facts that changed the recommendation, and what a fresh generic
AI conversation would have needed re-explained to reach the same conclusion:

| Stage | Facts SIE used without re-explanation | What a fresh chat would need re-pasted |
|---|---|---|
| 2 | 10 confirmed, structured interview rows | The full interview count and that it was "enough" |
| 3 | Confirmed prototype-engagement evidence, on top of the interview count | Both facts, plus a judgment call on whether engagement supersedes more interviews |
| 4 | Confirmed transaction evidence, on top of engagement | All three prior facts, plus the same judgment call repeated |
| 5 | Two specific, individually-attributed outcome rows (2 renew, 1 churn) | Everything above, plus explicit instruction not to average the churn away |
| 6 | The full sequence of 6 confirmed evidence rows spanning 4 stages | Everything above — and even then, a generic chat has no structural mechanism preventing it from smoothing the churn into "retention is fine" |

This is offered as an internal acceptance check, not marketing copy: it does not claim a generic AI cannot
reason about these facts if given them — only that SIE already has them, structured and provenanced,
without the founder re-typing anything, and applies the same rule to them every time.

## 16. Founder autonomy

Nothing in this phase changes the reject / work-on-something-else / record-disagreement / proceed-anyway /
change-direction affordances already present in the Build loop. Sequencing methodology is advisory: SIE
explains why it thinks a given question is highest-value, but the founder can choose "Or do something else"
at any stage, and a founder may pursue fundraising, hiring, or any other action before SIE would recommend
it — SIE explains the tradeoff (§12's future Finance connection is exactly this pattern), it never blocks.

## 17. Readability

The Company Intelligence card (§7, §9) uses plain sentences at normal body text size, no methodology jargon
(no "problem_evidence," "reported_preference," or "stage_mix" in any founder-facing copy), no six-card dense
grid, and no score of any kind. Verified visually via browser screenshot at 100% zoom during this phase's
live testing (§18).

## 18. Live acceptance testing

All four required live states were exercised on real running instances during this phase, each confirmed to
change the Overview meaningfully and for a visible, explainable reason, with no score and no chatbot
introduced at any point:

1. **Bare venture** — MacroFlow, Stage 1 (§14).
2. **Meaningful accumulated evidence** — MacroFlow, Stages 2–3 (§14).
3. **Paying customers** — MacroFlow, Stage 4 (§14).
4. **Mixed/contradictory outcome evidence** — MacroFlow, Stage 5 (§14).

## 19. Regression

Full backend suite (271/271 across `test_build_intelligence_loop`, `test_founder_missions`,
`test_founder_evidence`, `test_founder_workspace`, `test_venture_graduation`, `test_venture_history`,
`test_venture_share`, `test_idea_lab`, `test_fundraising_readiness`, `test_saved_startups`, and all four VPS
suites), full frontend suite (232/232), clean `npx tsc --noEmit`, clean `npm run lint`, clean `npm run
build` — all run after the live walkthrough's database mutations, confirming nothing in this phase disturbed
existing scoring, evidence persistence, sharing, graduation, or history behavior.

## 20. Known limitations (honest, not exhaustive)

- **Declining information value is scoped to `problem_evidence` only** (§4.3) — no other stage has a
  volume-based override, by design, but this means Stage 6-shaped situations (§14) are not yet handled.
- **"Still figuring out" lags true funnel position** between mission-completion events (§7, §14 Stage 4).
- ~~The free-text capture flow cannot yet turn a workflow-engagement observation into structured,
  funnel-advancing evidence~~ — **fixed, Phase 34G-A, §22.3** (structured fallback classifier).
- ~~No mechanism exists for a founder to mark old contradicting evidence as resolved/superseded~~ — **fixed,
  Phase 34G-A, §22.2** (`POST /ventures/{id}/evidence/{evidence_id}/resolve`).
- **Cases H and I (§4.4, §13) are genuine, unresolved architectural gaps**, not implementation bugs — closing
  them requires either new structured fields or persisting Fundraising data, both out of scope here. Still
  true after Phase 34G-A.
- **New in Phase 34G-A, see §22.4/§22.5:** segment-specific and temporal/product-state contradiction
  attribution remain genuinely unsupported by the schema — a founder can EXPLAIN a segment or
  before/after distinction in a resolution note's free text, but SIE cannot structurally represent or reason
  over "this applies to segment X only" as a first-class fact.
- **New in Phase 34G-A:** a stage that has already gone `"mixed"` has no automatic path back to `"supports"`
  no matter how much LATER evidence accumulates — only an explicit founder resolution clears it (by design,
  §22.1/§22.2). A founder who never notices the "Was this addressed?" affordance stays pinned indefinitely.

## 21. Acceptance verdict

**PASS.** This phase's recommendation engine changes for visible, evidence-grounded reasons at every stage
of a live walkthrough; contradictory evidence is preserved rather than averaged (including in the one case,
Stage 6, where that discipline came at a real cost, documented rather than hidden); evidence maturity
distinctions are structurally enforced by the funnel's own stage-to-evidence-type mapping, not by policy;
no score, confidence number, or new AI subsystem was introduced anywhere; and every gap the current
architecture cannot yet close is named specifically rather than faked.

**Superseded in part by Phase 34G-A (§22):** the Stage 6 cost named above ("the funnel does not yet advance
the way Stage 6 hoped for") is fixed as of Phase 34G-A — see §22.2 and §14 Stage 6's own update note.

---

## 22. Phase 34G-A — Intelligence Resolution + Learning Integrity Hardening

**Status:** Implemented. This section documents the corrective phase that ran immediately after §1–§21
above, triggered by two violations of the core product promise that Phase 34G's OWN live walkthrough
surfaced (§14 Stage 3 and Stage 6): a single earlier contradiction could pin a venture on the same question
indefinitely regardless of later evidence, and a meaningful founder result could be saved successfully while
silently failing to affect the recommendation at all. Both are exactly the shape of failure that would make
a founder conclude "SIE isn't actually learning" — unacceptable per the product's own governing doctrine
(§2).

### 22.1 The governing distinction: EXISTS vs. CURRENTLY DECISION-DOMINANT

The rule from §6 stands unmodified: **contradictory evidence must never be silently erased or averaged
away.** Phase 34G-A adds the other half of the same rule, made necessary by Stage 6's own finding:
**contradictory evidence does not automatically remain decision-dominant forever.**

These are reconciled by distinguishing two different facts about one evidence row, rather than by voting:

- **EXISTS** — the row is a real, permanent part of company history. It is never edited, never deleted,
  always queryable (`GET /ventures/{id}/evidence` returns every row regardless of state).
- **CURRENTLY DECISION-DOMINANT** — the row is part of the evidence set the recommendation engine currently
  reasons over (`superseded_by_id IS NULL`, the exact filter `app/api.py` has applied since Phase 34D).

A row can be EXISTS=true, DECISION-DOMINANT=false at the same time — that is precisely what "resolved" means
in this design. **No majority vote, no numeric threshold, no evidence score decides this.** The only thing
that moves a row from decision-dominant to historical is an explicit founder action (§22.2).

### 22.2 Evidence resolution mechanism

Four conceptual categories were named in the corrective directive — UNRESOLVED CONTRADICTION, BOUNDED/
EXPLAINED CONTRADICTION, SUPERSEDED EVIDENCE, HISTORICAL CONTRADICTION. Rather than building four separate
mechanisms (explicitly forbidden — "do not build a large evidence-management system"), V1 implements **one**
founder-facing action that covers all four, because the underlying state transition is identical in every
case: *a specific old evidence row should no longer be treated as the current picture, for a reason the
founder states in their own words.*

- **Endpoint:** `POST /ventures/{venture_id}/evidence/{evidence_id}/resolve`, body `{resolution_note}`.
- **Mechanism:** `resolve_venture_evidence_for_owner()` (`app/database/db.py`) creates a new
  `venture_evidence` row (the founder's own note, `evidence_type` inherited from the row being resolved so
  it stays in the same funnel stage, `relationship = NULL` — a note ABOUT a resolution is not itself new
  supporting/contradicting evidence) and points the OLD row's `superseded_by_id` at it, in one transaction.
  This is the exact `superseded_by_id` mechanic the Phase 34D architecture already specified for evidence
  correction — Phase 34G-A is its first real caller, not a new mechanism.
- **What clears:** because `app/api.py`'s recommendation and company-intelligence code already filters to
  `superseded_by_id IS NULL`, resolving a row automatically and immediately removes it from
  `_relationship_mix()`'s computation — no change to the sequencing algorithm itself was needed once the
  resolution endpoint existed.
- **Where it's surfaced:** `BuildRecommendation.blocking_evidence` (new field) carries exactly the specific
  row(s) with `relationship` in `contradicts`/`mixed` that are pinning the CURRENT stage — never the full
  evidence history, never every past contradiction. `CurrentQuestionCard.tsx`'s new `BlockingEvidencePanel`
  renders a "Was this addressed?" affordance next to each one; clicking it asks for a short, founder-written
  reason before calling the endpoint. The `why_it_matters` copy for any stage pinned by a contradiction gets
  one shared, added sentence naming this path exists — see `_RESOLUTION_PATH_ADDENDUM` in
  `app/ai/build_recommendation.py`.
- **Idempotent and safe:** resolving an already-resolved row returns 404, never a duplicate resolution or a
  double-supersession chain.

### 22.3 Structured-capture fallback (fixing the silent non-learning gap)

The Stage 3 gap (§14) was that `captureSignals.ts`'s deterministic regex has no pattern for
workflow-engagement/commitment results, so a founder's real, meaningful note produced zero candidate
signals — and the only visible option was "Save this as-is," which silently created an unclassified,
funnel-inert `founder_claim` row with no indication anything had gone differently than a normal confirmation.

**Fix, per the directive's own explicit guidance ("do not create brittle regex... if a safer existing
mechanism exists"):** no new regex, no new AI extraction. `captureSignals.ts` is untouched. Instead,
`CandidateEvidenceReview` (`CurrentQuestionCard.tsx`) now shows a small structured-fallback picker exactly
when zero signals were extracted:

1. Revised copy states plainly that nothing here will change what SIE recommends **unless** the founder
   classifies it themselves — never letting the founder believe intelligence advanced when it didn't.
2. A plain-language picker reusing the EXISTING `EVIDENCE_TYPE_LABELS` vocabulary ("Someone actually did
   something," "Someone agreed to / committed to something," "Money actually changed hands," "This is what
   happened afterward, over time," etc. — the same six categories the checkbox-confirmation flow already
   uses) plus the EXISTING `RelationshipPicker` (supports/mixed/contradicts/doesn't tell us yet — the
   mandatory-explicit-choice control from Phase 34D-A, unmodified).
3. Confirming calls the EXISTING `toRawTextEvidencePayload(text, evidenceType, relationship)` function
   (`lib/build/evidenceMapping.ts`) — already generic over every evidence type, already wired to
   `POST /ventures/{id}/evidence`. No new payload shape, no new backend code.
4. The founder can still decline to classify ("Just save the note as unclassified text") — that path is
   unchanged and still produces an inert, honestly-unclassified `founder_claim` row, now with clearer copy
   that this is what's happening.

This closes the exact gap for all four remaining funnel stages at once (problem/commitment/transaction/
retention) — see the frontend test cases in `dashboard/tests/buildIntelligenceLoop.test.ts` (Cases H–L, §11
of the directive) proving each stage's evidence shape is representable this way, and Case L proving the
unclassified path still carries no relationship (so it can never masquerade as resolved evidence).

### 22.4 Segment-specific resolution — still a documented gap, not fabricated

Per the directive's own explicit instruction ("if the current schema cannot reliably represent segment/
context attribution, do not fake it"): **no `segment` column exists on `venture_evidence`, and none was
added.** A founder can *explain* a segment distinction in a resolution note's free text ("this was SMB, our
focus is now enterprise") — real, honest, human-readable — but SIE cannot structurally query "show me
retention broken out by segment," cannot automatically recognize two rows as segment-related without the
founder saying so, and cannot prevent a founder from writing a segment claim that isn't actually true. Test
Case E (`test_resolution_case_e_segment_specificity_is_a_documented_gap`) asserts this limitation directly:
the API response for both a raw evidence row and a resolution note is checked to carry no `segment` field at
all. **The missing infrastructure, precisely:** a `segment TEXT` (or similar) column on `venture_evidence`,
plus sequencing logic that could reason per-segment rather than per-venture — genuinely new, out of scope
here.

### 22.5 Temporal / product-state resolution — same treatment

Identical shape and identical honesty: a founder can explain "this was before we fixed onboarding" in a
resolution note (exactly what the live Stage 6 retest used, §14), but SIE has no structured concept of a
"product version" or "before/after" boundary, and cannot automatically recognize that a later row postdates
a real product change versus just being a later data point. **The missing infrastructure:** a
`product_version`-like tag, or a founder-settable "we changed something material here" marker evidence rows
could be compared against — not built, not faked.

### 22.6 "Still figuring out" now agrees with the recommendation (§9 fix)

Root cause: `still_figuring_out` (`build_company_intelligence_summary()`) was previously derived from the
most recently *completed mission's* own `interpretation_limitations` text — a source that does not update
when evidence is confirmed outside a mission's own result-recording flow (exactly what happened for every
evidence row added via the direct API during the 34G live walkthrough, and what will keep happening for any
resolution note).

**Fix:** `still_figuring_out` is now derived from the SAME `_determine_focus_stage()` computation that
drives the primary recommendation, on the SAME `evidence_rows`, called from within
`build_company_intelligence_summary()` itself — not passed across a separate, potentially-stale channel. A
fixed, plain-language phrase table (`_STAGE_UNRESOLVED_PHRASE`, `_STAGE_TENSION_PHRASE`) renders "what's
still open" for the current stage and every stage after it in funnel order, leading with the SPECIFIC named
tension when a contradiction is what's pinning the stage. The two surfaces cannot disagree about *why*
nothing is shown either — both check the identical `evidence_rows`/`target_customer` early-exit conditions.
A related, adjacent staleness in `what_changed` (it also only reflected mission-completion events) was fixed
the same way: the single most-recently-recorded evidence row across the whole venture is now surfaced there
too, whenever it postdates the latest mission's own interpretation — which is what makes a resolution note
itself show up in "What changed recently," confirmed live (§22.7).

### 22.7 Live retest: Stage 6, replayed against the fix

Re-run on the exact same venture (MacroFlow, id 4074) and the exact same evidence rows Phase 34G's
walkthrough left behind (2 renewed / 1 churned / then 8-of-9 renewing 3 straight months), against the
now-hardened backend:

1. **Before resolution:** recommendation correctly stayed pinned at "What's driving the difference between
   MacroFlow customers who stay and those who don't?" — the 8-vs-1 volume did **not** numerically clear the
   tension (Outcome B: "remains on retention... but clearly tells the founder what specific information is
   required to resolve it" — confirmed via the live-rendered `why_it_matters` addendum and the
   `BlockingEvidencePanel` naming the specific churn row).
2. **Founder action:** clicked "Was this addressed?" next to the churn row, wrote "This was an early pilot
   glitch before we fixed onboarding — 8 of 9 later customers have retained for 3 straight months," clicked
   "Mark resolved."
3. **After resolution:** recommendation advanced to "Can MacroFlow acquire new customers beyond however you
   found the first ones?" (Outcome A: the funnel correctly progressed once the founder explicitly judged the
   contradiction resolved).
4. **Verified via direct database read:** the original churn row (id 287) still exists, its `statement`
   column byte-identical to what was originally recorded, now with `superseded_by_id` pointing at the new
   resolution-note row (id 569, `evidence_type = longitudinal_outcome` inherited, `relationship = NULL`).
   Nothing was edited or deleted.
5. **"Still figuring out" and "what changed recently" both updated correctly**, live: the tension phrase
   disappeared from "still figuring out" (replaced by "Repeatable acquisition beyond how you found the first
   customers"), and "what changed recently" led with the resolution note itself.

**Neither bad outcome occurred:** the system did not majority-vote the churn away on its own, and it did not
remain permanently pinned with no way forward. The founder got a real, working path to resolution and used
it, and the record of what actually happened (a genuine early churn) was never erased.
