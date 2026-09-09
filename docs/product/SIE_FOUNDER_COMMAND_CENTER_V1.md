# SIE Founder Command Center V1 — Product Design

Phase 38A. This is a design document, not an implementation. No code, schema, or migration accompanies it.
Every claim about "what exists today" was verified by reading the actual model/component files named inline
— nothing here is assumed from the architecture's own aspirations.

---

## 1. Executive thesis

SIE already asks a founder to do real work: model assumptions, run tests, record evidence, make decisions,
track finances, plan hires, model fundraising, and submit to an evidence-based analysis. Today that work
pays off *locally* — each system (Build, Finance, Fundraising, Analyze) answers its own question well. It
does not yet pay off *centrally*. Nothing currently looks across all four systems and tells the founder,
in one sentence, what to actually pay attention to today.

The Command Center is that one sentence, backed by a page. Its job is not to summarize SIE. Its job is to
answer, using only what SIE has actually persisted about *this* company, "what deserves your attention
right now, and why." Everything else on the page is progressive disclosure in service of that one answer.

## 2. Why Command Center exists

Build already has a working version of this idea for its own system alone: `CurrentQuestionCard.tsx`
(`GET /ventures/{id}/recommendation`) computes one active question, deterministically, from persisted
missions/evidence/decisions, and a parallel `company_intelligence` summary ("what SIE knows / still
figuring out / what changed"). This has been Overview's hero since Phase 34E and is proof the pattern
works. What it cannot do — by design, not by oversight — is reason about Finance, Fundraising, or Analyze
at all. A venture can have six weeks of runway and a hiring decision pending, and the Build recommendation
will still confidently suggest a customer interview, because it has never been shown the cash number.

The Command Center is the layer above the four systems that is allowed to see all of them at once and
decide which one currently matters most.

## 3. Why not generic AI

A founder can already open ChatGPT and ask "what should I focus on this week?" Generic AI can brainstorm,
explain frameworks, and produce startup advice. It cannot do the one thing this document is about: reason
over *this specific company's own accumulated, structured history* — which evidence contradicted which,
which decision the founder actually made and why, what the modeled cash-out date becomes under a specific
planned hire, which evaluation dimension SIE's own analysis still has no evidence for. Reconstructing that
context in a fresh chat, every time, is real, repeated work a founder would have to redo from memory. SIE
already has it stored, structured, and query-able. The Command Center's entire value proposition is
"you never have to re-explain your company to get today's answer" — nothing else.

## 4. Founder jobs-to-be-done

1. What matters most right now?
2. Why does it matter?
3. What does SIE actually know?
4. What is still uncertain?
5. What should I do next?
6. What changed since last time?
7. What important decisions are approaching?
8. How do my evidence and financial constraints affect those decisions?

These map directly to the six sub-sections in §27's hierarchy; nothing in this document invents an
additional job.

## 5. Current Overview audit

Read `VentureWorkspace.tsx`'s Overview `TabPanel` end to end. Actual rendered sections, top to bottom:

| # | Section | Component | Verdict | Why |
|---|---|---|---|
| 1 | Venture identity (name, description, who it's for, how it makes money, biggest unknowns) | `VentureIdentity` | **KEEP** | Genuinely orienting context; cheap, calm, not competing for the founder's decision attention. |
| 2 | Graduation banner ("You're now building X as a startup") | `VentureGraduationBanner` | **KEEP** | Real, rare, state-changing event; correctly non-prominent (`variant="subtle"`). |
| 3 | **"What matters now"** (current question / testing / decision / outcome) | `CurrentQuestionCard` | **ADAPT** | This is 80% of the Command Center already. It needs to become *cross-system-aware*, not rebuilt. See §9. |
| 4 | "Ready to make this a startup?" (graduation suggestion) | `VentureGraduationAction` | **KEEP, but demote further if 38B crowds the page** | Real, rare, already correctly gated on real evidence (`isEligibleForGraduationSuggestion`). |
| 5 | "What SIE knows / Still figuring out / What changed" | `CompanyIntelligenceState` | **ADAPT** | Exactly the right idea, Build-only today. Extend the *pattern*, not necessarily this exact component, per §16-18. |
| 6 | "Working on something else? Add it →" (secondary mission entry) | inline in `VentureWorkspace.tsx` | **KEEP** | Correctly de-emphasized already; not a Command Center concern. |

**Not present today, and correctly absent:** no SPS ring, no pillar cards, no Fundraising Readiness score,
no financial dashboard, no public-profile status. Confirms 37D's own "Overview stays score-free" doctrine
already holds and should keep holding — see §17-18.

**What Overview does NOT do today:** know that Finance exists, know a hire is planned, know what Analyze's
structural coverage says, distinguish "important" from "urgent," or say anything about money at all.

## 6. Information hierarchy

Four sections, one dominant:

1. **What matters now** (dominant — priority, why, primary action; §27 detail)
2. **Current context** (progressive disclosure — what SIE knows / still uncertain, stage-appropriate)
3. **Upcoming decisions** (secondary, max 2-3 items; only when real ones exist)
4. **What changed** (folded into #1's "why," not a separate always-visible section — see §18)

This is a trim of the existing four-section Overview, not an addition. "What changed" stays alive as a
*fact type* (§18) fed into "why this matters," rather than surviving as its own permanent block — today it
is its own block only because nothing yet decides whether it is the most important thing to say.

## 7. Prioritization model

No score. A short, ordered, deterministic pass over candidate signals, each tagged with a **type**
(§8) and a **domain** (build / finance / fundraising / analyze / decision). The first candidate that
survives, in this order, wins:

1. **Critical financial constraint** — a modeled or known cash-depletion date inside a short, concrete
   horizon (not a fixed universal number — see §9's own refusal to invent "12 months is safe"). Always wins
   over a Build learning priority, because a company that runs out of cash cannot act on anything else it
   learns.
2. **Decision-dominant contradiction actively blocking Build's own recommendation** — i.e. exactly what
   `BuildRecommendation.blocking_evidence` already flags today. If Build itself cannot recommend a next
   step because two pieces of evidence disagree, that disagreement *is* the priority.
3. **A pending, consequential decision with a known financial or evidence consequence** — e.g. a planned
   hire whose start date is approaching and whose modeled effect on runway is already computable
   (`HireImpactPreview`/`ProjectedMonthWithPlan` already exist for this).
4. **Material plan-vs-actual divergence** — `pending_reconciliation` (already computed, Finance) shows a
   planned item whose real outcome hasn't been recorded against the latest snapshot.
5. **Build's own current recommendation** (`BuildRecommendation.question_text`) — the default, most common
   case: no financial emergency, no contradiction, no pending decision consequence outranks it.
6. **Stale unresolved decision awaiting an outcome** — a decision was made, enough time has plausibly
   passed, and no outcome evidence exists yet (§13 staleness).
7. **No urgent issue** — every above check comes back empty (§26).

**Finance overrides Build** only at tier 1 (a real depletion horizon), never merely because Finance data
exists (§22's profitable-company requirement). **An imminent decision overrides an experiment** at tier 3,
specifically because the decision already has a computed consequence, not because decisions are inherently
more important than learning. **Insufficient data becomes the priority itself** only for a genuinely
empty company (§19) — that state is `question_text` from Build's own existing `_fallback_recommendation()`
(already the behavior when `model_result` is absent), reframed as the Command Center's own \#1 fact.

**Tie-breaking**: financial > decision-consequence > contradiction > default recommendation > staleness.
Within a tier, most-recently-changed wins (matches `what_changed`'s own recency-ordering already built for
Build).

## 8. Urgency model

Four internal states (not exposed as jargon labels to the founder — see §29):

- **CRITICAL** — tier 1 (short-horizon cash depletion).
- **TIME-SENSITIVE** — tier 3/4 (a decision or divergence with a near-term date attached).
- **PRIMARY LEARNING PRIORITY** — tier 2/5 (Build's own current recommendation, contradiction or not).
- **MONITOR / NO URGENT ACTION** — tier 6/7.

`UPCOMING DECISION` (§16) is not a fifth urgency state — it is a *secondary section*, populated regardless
of what wins the primary slot, capped at 2-3 items.

## 9. Cross-system intelligence rules

Only combinations defensible from data that is **persisted today** are in scope for 38B/38C. Each is
labeled with its Repository Reality classification from §38.

- **FINANCE → overrides BUILD** (EXISTS NOW): `DerivedFinancialMetrics.runway_months` + `net_burn_cents`
  are already computed on every `GET /ventures/{id}/financials` call. A short runway is a fact the priority
  model can read immediately.
- **BUILD + FINANCE** (REQUIRES SMALL CONNECTION): "your evidence hasn't resolved retention, and the
  planned engineering hire moves modeled depletion from October to July" — both halves already exist
  (`BuildRecommendation.blocking_evidence` / `still_figuring_out`, and `ProjectedMonthWithPlan.depleted`
  compared against baseline `ProjectedMonth.depleted`). No new computation, just one function that reads
  both responses and picks the sharper one.
- **DECISION + FINANCE** (REQUIRES SMALL CONNECTION): a hire decision's modeled consequence is already
  computable (`HireImpactPreview`) at the moment the decision is being considered.
- **BUILD + ANALYZE** (REQUIRES SMALL CONNECTION, use sparingly — see §17): "your own evidence has
  strengthened traction, while SIE's last analysis still shows low structural coverage for execution" is
  defensible because `structural_coverage.pillars_unavailable_entirely` is a real, already-computed field.
- **BUILD/FINANCE + FUNDRAISING** (**NOT DEFENSIBLE TODAY**): confirmed by reading
  `FundraisingSimulator.tsx` and grepping the entire backend — SAFE/priced-round/dilution modeling makes
  **zero** persistence calls; it is ephemeral, client-only state, gone on refresh. There is no `POST` for a
  scenario, no stored SAFE terms, nothing a backend-computed Command Center could read. Any "the modeled
  SAFE extends runway by X" statement would have to be invented or re-derived from nothing. **This
  combination requires new infrastructure (persisting a chosen/saved fundraising scenario) before it can
  exist at all** — deferred, not attempted.

## 10. Build integration

Build is the **primary source of "what matters"** in the common case (tier 5). The Command Center reuses
`GET /ventures/{id}/recommendation` verbatim — `current_question`, `recommendation.blocking_evidence`,
`company_intelligence` — rather than recomputing anything. Build only loses the top slot when a higher tier
(financial, decision-consequence) is present.

## 11. Finance integration

Finance contributes the tier-1/tier-3/tier-4 escalation checks (§7) and, when it is not the primary
priority, one line of "current context" (e.g. current runway) — never a dashboard. Reuses
`DerivedFinancialMetrics`, `pending_reconciliation`, `HireImpactPreview`/`ProjectedMonthWithPlan` exactly
as they exist; no new financial computation.

## 12. Fundraising integration

**None in 38B/38C.** Per §9, nothing is persisted to reason over. The only legitimate Command Center
behavior today is a plain link ("Model financing →" to the Fundraising tab) when a fundraising-adjacent
signal exists elsewhere (e.g. Fundraising Readiness flags a gap) — never a fabricated "your SAFE would..."
statement. Revisit only after a future phase decides whether to persist chosen fundraising scenarios (out
of scope here, and explicitly not decided in this document).

## 13. Analyze boundary

Analyze may contribute **only**: (a) low overall evidence coverage as one line of context, (b) a *named*,
specific unresolved evaluation dimension already flagged by `structural_coverage`, (c) a material mismatch
between the founder's own Build evidence and what the analysis could see (§9's BUILD+ANALYZE case). SPS
itself (the number) **never** appears in the primary priority or its reasoning. "SPS is 62, therefore do
X" and any framing that treats SPS movement as company progress are explicitly out — matching §17's own
illegitimate-use list exactly. Fundraising Readiness (a distinct, already-deterministic assessment — see
`app/ai/fundraising_readiness.py`) may be referenced the same limited way Analyze is: a real gap it already
computed, never its 0-100 number as a headline.

## 14. Decision integration

`VentureDecisionResponse` already persists `sie_recommendation` and `founder_choice` side by side, forever,
append-only (`supersedes_decision_id` for explicit reversal — nothing is ever edited or deleted). This is
sufficient, **today**, to support:

- An unresolved decision (interpretation ready, no decision recorded) appears via `awaitingDecisionMission`
  — already built.
- A decision awaiting an outcome becomes a candidate for the Upcoming Decisions section (§16) or, if stale
  enough, a tier-6 priority (§7, §13 staleness).
- **Founder disagreement is structurally already safe**: because `founder_choice` is stored independently
  of `sie_recommendation` — never overwriting it — a founder who chose against SIE's advice has that choice
  as the new ground truth for every subsequent computation. Nothing needs to be built to make SIE "respect"
  the choice; the schema already only ever reads `founder_choice` going forward (see `OutcomeState` binding
  to `mostRecentDecision.founder_choice`, not to `sie_recommendation`). What must be *designed carefully* is
  the copy: never re-surface the original recommendation as unfinished business (§25).

## 15. Evidence/contradiction behavior

Reuses Phase 34G-A's model exactly, unmodified: a contradiction is never resolved by evidence volume, only
by an explicit founder resolution (`resolve_venture_evidence_for_owner`, already wired to
`BlockingEvidencePanel`/`BlockingEvidenceRow` in `CurrentQuestionCard.tsx`). The Command Center's own
priority model (§7 tier 2) simply *reads* `blocking_evidence` — it introduces no new contradiction logic.
Later "supporting" evidence never silently outvotes a live contradiction; only an explicit founder
resolution removes it from `blocking_evidence` (via `superseded_by_id`), and it remains fully visible in
venture History regardless.

## 16. "What SIE Knows" model

Reuses `build_company_intelligence_summary()`'s own discipline exactly: every bullet is a verbatim, already
-recorded statement (evidence statement, snapshot fact, decision choice) — never a rephrasing, never an
inference dressed as a fact. Extended (not replaced) to admit Finance facts using the same discipline:
a Finance-sourced bullet is the snapshot's own recorded number, not a projection. Capped (mirrors
`_KNOWS_BULLET_CAP`) so it never becomes a dump. Provenance is signaled through **plain phrasing**, never a
jargon tag: "You reported 8 renewals" (founder-said), "SIE's cash math shows 3 months of runway"
(calculated) — no visible "Founder reported" / "Calculated" badges beyond what `RecentUpdates.tsx` already
does elsewhere; the sentence itself carries the provenance.

## 17. "What SIE Doesn't Know" model

This is `still_figuring_out` from the *same* existing summary, unchanged. Ordering: most decision-relevant
first (whatever the current priority's own reasoning names), capped at the same small number Build already
uses. Directly tied to the primary action — the uncertainty named here should be the same one the "next
best action" is designed to resolve, or the page is incoherent.

## 18. "What Changed" model

Persisted state that exists **today** to support this, verified directly: the most recent completed
mission's own `interpretation_summary` + `interpretation_generated_at`; the single most recent
`VentureEvidence.recorded_at`; the most recent `VentureDecisionResponse.founder_choice` +
`decided_at`. Extend with: the most recent `FinancialSnapshotResponse.recorded_at` vs. the prior one (a
real, comparable delta — e.g. "cash dropped by $12,000 since your last update"), and — only when it
changes the priority itself — "your priority changed because [fact]." **No new history infrastructure is
proposed.** "What changed" is not a permanent block; it is the evidentiary backbone of "why this matters
now" (§6) and only becomes its own visible line when it is *the reason* the priority is what it is.

## 19. Next Best Action model

Every action must resolve to a real destination (§15/action-destination) and be phrased as a concrete
instruction, never a category ("talk to customers"). Sourced, in priority order, from: `BuildRecommendation
.what_to_do`/`recommended_test_title` (already concrete — e.g. "Interview 20+ target customers to validate
the problem is real" per the venture-stage template), a Finance-comparison prompt ("Compare the planned
hire starting in October vs. January before committing" — directly expressible from
`HireImpactPreview` called twice), or a decision-recording prompt ("Record what happened with the
[decision] you made on [date]"). No autonomous agent — every action is a link into an existing capture
surface, never something SIE does on the founder's behalf.

## 20. Upcoming Decisions model

Secondary section, maximum 2-3 items, populated only from real persisted state: a `HirePlanResponse` whose
`start_date` is approaching and `status == "planned"`; a decision (`VentureDecisionResponse`) with no
outcome evidence yet; a `pending_reconciliation` item. Never a task manager — no due dates invented, no
generic to-dos, nothing the founder didn't already create by using Build/Finance/decisions.

## 21. Traceability

"Why SIE is focusing here ▾" — a disclosure, not a citation engine — expands to the literal facts that fed
the priority decision, e.g.: *"8 renewals recorded · 1 churn recorded · planned hire +$18,750/mo · modeled
depletion moved July ← October."* Every line is a direct field read (evidence statements, snapshot deltas,
projection dates) — no synthesis, no new prose generation, so it can never say something the underlying
data doesn't literally support.

## 22. Staleness

Minimum viable behavior only, no notification system:

- Finance snapshot >60 days old: the "current context" line says "as of [date]" plainly rather than
  presenting it as current; a financial escalation (§9) is not computed from data this old without saying
  so.
- Evidence/analysis age: `structural_coverage`/evidence dates already carry their own timestamp; the
  Command Center surfaces the date whenever it uses the fact, never hides it.
- A hire's `start_date` has passed with no reconciliation: this **is** already a tier-4 priority candidate
  (`pending_reconciliation`), not a separate staleness feature.
- A decision with no outcome after a plausible interval (e.g. 30+ days): becomes a tier-6 candidate or an
  Upcoming Decisions item, never silently dropped.

## 23. Missing-data behavior

| State | Behavior |
|---|---|
| Build data, no Finance | Priority comes from Build alone; no Finance line appears (not "Finance: unknown"). |
| Finance, no Build evidence | Priority may be financial (if a real constraint exists) or an honest "no Build evidence yet" learning prompt (§19, empty-company path); never a fabricated Build question. |
| Analysis, no Finance | Analyze may contribute a boundary-limited line (§13); no financial escalation is possible or attempted. |
| Nothing but a company description | The existing `_fallback_recommendation()` path — already the honest "model a few assumptions" state. |
| No analysis at all | Analyze contributes nothing; this is the ordinary, majority case (confirmed by this session's own repeated finding that most ventures have zero or one analysis) and must never read as broken. |

No fake zeros, no guessed numbers, anywhere — matches every prior phase's own doctrine.

## 24. Stage/context adaptation

Reuses `resolveVentureState()`'s existing four buckets (Idea/Validation/Building/Operating — Phase 34F,
confirmed live in Phase 37E) as the *framing* for the same priority engine, not a second engine. An
Operating-stage company with real revenue/expenses is far more likely to surface a tier-1/3/4 financial
signal (because the data exists to compute one); an Idea-stage company almost always surfaces tier-5/7
(because Finance/Decision data usually doesn't exist yet). The stage bucket is a **consequence** of what
data exists, not a separate branch the design has to special-case.

## 25. Desktop wireframe

```
--------------------------------------------------------------
FridgeChef                                    Building Stage
--------------------------------------------------------------

WHAT MATTERS NOW

Understand why one customer churned while eight renewed.

Your retention evidence is mixed — most customers stayed, one
left, and you haven't recorded why.

  [ Interview the churned customer and one who renewed,      ]
  [ using the same five questions, and record what differs.  ]

Why SIE is focusing here ▾
  · 8 renewals recorded · 1 churn recorded · no reason on file
--------------------------------------------------------------

CURRENT CONTEXT

What SIE knows                    Still figuring out
✓ 9 paying customers              — why the one customer churned
✓ $7,500 MRR                      — whether retention differs by
✓ 8 of 9 renewed                    plan or segment
✓ $450K cash · $50K/mo burn
--------------------------------------------------------------

UPCOMING DECISIONS  (only if real ones exist)

· Planned hire: Senior Engineer, starts Oct 1 — moves modeled
  cash-out from Mar 2027 to Dec 2026        [Review in Finance →]
--------------------------------------------------------------
```

Above the fold (no scroll on a standard laptop): "What matters now" through the primary action button.
Everything below is one scroll, four sections maximum, matching §27's constraint.

## 26. Mobile wireframe

```
FridgeChef
Building Stage
----------------------
WHAT MATTERS NOW

Understand why one
customer churned while
eight renewed.

Your retention evidence
is mixed.

[ Interview the churned
  customer and one who
  renewed, same five
  questions. ]

Why focusing here ▾
----------------------
CURRENT CONTEXT
(collapsed by default,
tap to expand)
----------------------
UPCOMING DECISIONS
· Planned hire — Oct 1
  [Review →]
----------------------
```

Single column throughout (matches every other mobile pattern already established across Overview/Finance/
Analyze this session); "Current Context" collapses by default on narrow viewports specifically because it
is the progressive-disclosure tier, not the primary answer.

## 27. Founder-facing copy examples

**Early venture (no evidence yet):**
> **What matters now** — Find out whether the problem is real for an actual customer.
> **Why** — Right now this is your own best guess about what parents struggle with — nobody outside your
> head has confirmed it yet.
> **Next** — Talk to 5 target customers about the problem itself. Don't mention your solution yet.

**Paying-customer venture:**
> **What matters now** — Understand why one customer churned while eight renewed.
> **Why** — Your evidence is mixed: most customers stayed, but you don't yet know what made the one who
> left different.
> **Next** — Interview the churned customer and one who renewed, using the same five questions.

**Short-runway venture:**
> **What matters now** — Your modeled cash runs out in 6 weeks at the current burn rate.
> **Why** — At $50,000/month spend and $180,000 in the bank, that's the math today — before anything else
> you're working on.
> **Next** — Decide what to cut or raise before anything else. [Review your cash plan →]

**Profitable venture:**
> **What matters now** — Understand why one customer churned while eight renewed.
> **Why** — Your cash position is solid, so this is a learning priority, not a financial one — but it's
> still the biggest open question in what you know about this company.
> **Next** — Interview the churned customer and one who renewed.
> *(No financial urgency language appears anywhere — Finance contributes nothing here beyond staying
> silent, per §22.)*

**Fundraising venture:**
> **What matters now** — Your customer willingness-to-pay evidence is still thin.
> **Why** — If you're preparing to raise, investors will ask about this directly, and SIE doesn't yet have
> evidence to back it up.
> **Next** — Record pricing conversations with your next 5 prospects, including any pushback on price.
> *(No SAFE/dilution number appears — per §12, nothing is persisted to compute one.)*

**Contradictory-evidence venture:**
> **What matters now** — Your last two tests disagree about pricing.
> **Why** — One conversation suggested $99/month works; the most recent one pushed back hard on that price.
> Both are still "live" — nothing has resolved which one reflects reality.
> **Next** — Talk to three more prospects specifically about price before deciding.

**Planned-hire venture:**
> **What matters now** — A planned hire changes your cash timeline meaningfully.
> **Why** — Adding this role moves your modeled cash-out date from March to December.
> **Next** — Compare hiring in October vs. January before committing. [Compare in Finance →]

**No-urgent-action venture:**
> **No urgent issue right now, based on what SIE knows about FridgeChef.**
> Your most useful next step: confirm whether the two customers who mentioned "family size" as a factor
> represent a real pattern worth designing around.
> *(Deliberately not a green checkmark or health score — see §26.)*

## 28. Intelligence contract

```
CommandCenterState {
  primary_priority: string          // one sentence, founder-facing
  priority_type: "financial" | "contradiction" | "decision_consequence"
                 | "plan_divergence" | "build_recommendation"
                 | "stale_decision" | "no_urgent_action"
  urgency: "critical" | "time_sensitive" | "primary_learning" | "monitor"
  why: string                       // 1-3 sentences, plain language
  supporting_facts: Fact[]          // verbatim, sourced (§21 traceability)
  unresolved_questions: string[]    // capped, from still_figuring_out
  recommended_action: {
    label: string
    destination: "build_capture" | "finance" | "finance_scenarios"
                 | "fundraising" | "analyze" | "decision_outcome"
  }
  what_changed: string | null       // only when it explains the priority
  upcoming_decisions: Decision[]    // max 2-3, may be empty
}

Fact {
  statement: string
  source_domain: "build" | "finance" | "analyze" | "decision"
  source_ref: { table: string, id: number }   // for traceability only, never shown raw
}
```

| Field | Meaning | Allowed source systems | Deterministic? | AI-generated? | Persisted or derived? | Required? | Fallback |
|---|---|---|---|---|---|---|---|
| `primary_priority` | The one sentence | Build/Finance/Decision (Fundraising/Analyze contribute facts, never own this) | Yes | No (template-filled from facts, same discipline as `build_recommendation.py`) | Derived, fresh every load | Required | `_fallback_recommendation()`'s existing empty-state text |
| `priority_type` | Which tier won (§7) | all | Yes | No | Derived | Required | `"no_urgent_action"` |
| `urgency` | §8 bucket | derived from `priority_type` | Yes | No | Derived | Required | `"monitor"` |
| `why` | Plain-language reasoning | same as priority | Yes | Possibly AI-*phrased* only (§29), never AI-*decided* | Derived | Required | template sentence from `why_it_matters` |
| `supporting_facts` | Traceability | Build/Finance/Analyze/Decision | Yes | No | Derived (read-only, never persisted) | Required (may be empty for the empty-company case) | `[]` |
| `unresolved_questions` | §17 | Build (today), Analyze boundary (§13) | Yes | No | Derived | Optional | `[]` |
| `recommended_action` | §19 | Build/Finance/Decision | Yes | No | Derived | Required | link to Build's own recommended test |
| `what_changed` | §18 | Build/Finance/Decision | Yes | No | Derived | Optional | `null` |
| `upcoming_decisions` | §20 | Finance (hire plans), Decision | Yes | No | Derived | Optional | `[]` |

## 29. AI boundary

**No AI is required to compute priority, urgency, facts, or the action.** Every existing analog
(`build_recommendation.py`, `financial_engine.py`, `fundraising_readiness.py`) is already deterministic,
template-driven, zero-LLM — confirmed by reading each module's own header comment, not assumed. The
Command Center's priority/urgency/fact-selection logic should follow the identical discipline: pure
functions over already-persisted rows, reproducible, free, and impossible to hallucinate.

**Where AI *could* help, and shouldn't be assumed necessary:** phrasing variety for the "why" sentence, if
the same template-filled sentence ever feels repetitive across many ventures. This is a nice-to-have
polish layer, strictly *after* deterministic selection, never a replacement for it — and 38B should ship
without it and see whether the template sentences (§27's own examples) are actually good enough first.
Failure behavior if ever added: the template sentence is always the fallback, never a blank state. Cost:
zero calls in 38B. Reproducibility: total, since nothing about *which* fact/priority to show would ever
depend on AI output.

## 30. Repository reality matrix

| Proposed fact/behavior | Status |
|---|---|
| Build current question / recommendation / blocking evidence | **EXISTS NOW** |
| Build "what SIE knows / still figuring / what changed" | **EXISTS NOW** |
| Finance runway/burn/derived metrics | **EXISTS NOW** |
| Finance plan-vs-actual reconciliation | **EXISTS NOW** |
| Hire-plan modeled cash-out shift | **EXISTS NOW** (`HireImpactPreview`) |
| Decision recommendation-vs-choice history | **EXISTS NOW** |
| Build + Finance combined priority statement | **REQUIRES SMALL CONNECTION** (one function, two existing reads) |
| Decision + Finance consequence statement | **REQUIRES SMALL CONNECTION** |
| Build + Analyze coverage-gap statement | **REQUIRES SMALL CONNECTION** (bounded per §13) |
| Financial staleness framing | **REQUIRES SMALL CONNECTION** (compare two existing dates) |
| Fundraising-modeled consequence in Command Center | **REQUIRES NEW INFRASTRUCTURE** (nothing persisted today — §9, §12) |
| Public-profile completion state in Command Center | **NOT DEFENSIBLE** (§32) |
| A new "Founder Priority Score" | **NOT DEFENSIBLE** (explicitly forbidden, §7/§43) |
| AI-generated recommendations without deterministic backing | **NOT DEFENSIBLE** (§29) |

## 31. Monetization thesis

**Free value**: initial company setup, one Build recommendation, basic evidence capture — the same
free tier that already exists today (nothing here proposes gating existing free capability).

**Paid-worthy behaviors, specifically**: cross-system priority (§9) is the single most defensible paid
behavior — it is the one thing that provably cannot be reconstructed in a single generic-AI prompt, because
it requires the founder's own accumulated evidence, decisions, and financial history, all cross-referenced.
Longitudinal "what changed" (§18) across months is paid-worthy for the same reason: a founder can't get "my
priority changed because of what I recorded three months ago" out of a stateless chat. Decision/outcome
history and hire-consequence modeling are paid-worthy because they represent real, structured founder work
already invested. Fundraising scenario modeling, if ever persisted, would be an obvious future paid tier —
not proposed here.

## 32. Repeat-use thesis

- **Tomorrow**: to see whether yesterday's recorded result changed the priority.
- **Before hiring**: to see the modeled consequence before committing (already computable today).
- **After a customer churns**: the priority should visibly react to newly-recorded evidence.
- **Before fundraising**: to see the Build+Analyze evidence-gap framing (§9), even without Fundraising
  integration itself.
- **After changing pricing**: a founder recording a pricing test result expects the next-question logic to
  visibly move — proving the loop is alive, not a static dashboard.

If the only honest answer were "to check a dashboard," this design would fail §37's own test; it doesn't,
because every return trip corresponds to a real state change SIE already tracks.

## 33. Generic-AI replacement test

| Capability | Replaceable by one ChatGPT prompt? | Why/why not |
|---|---|---|
| "What should I focus on?" (no history) | Yes | Generic startup advice needs no company state. |
| "What should I focus on, given my last 3 tests, my decision history, and my current cash position?" | **No** | Requires reconstructing structured, dated, contradiction-aware history a founder cannot paste in reliably or completely. |
| Contradiction-aware evidence weighting (§15) | **No** | Requires the append-only, non-editable evidence ledger itself. |
| Hire-consequence modeling | **No** | Requires the persisted financial engine's own projection math. |
| "Why is SIE telling me this?" traceability (§21) | **No** | Requires literal, dated, sourced facts a chat transcript doesn't retain structure for. |

The accumulated state — not the sentence-generation — is the moat, exactly per §37's own framing.

## 34. Simplicity audit

Removed relative to a "summarize everything" instinct: no pillar cards, no SPS ring, no financial
dashboard, no six competing recommendation cards, no public-profile status, no fundraising scenario
summary (nothing persisted to summarize). Kept: exactly one priority, one why, one action, with the
existing Build "what SIE knows" pattern as the only secondary section. Every kept element serves
Understand/Decide/Act/Learn directly; nothing is kept merely because it already exists elsewhere in SIE.

## 35. Risks / blind spots

- **Template-sentence fatigue**: if the "why" sentence reads formulaic across many ventures, founders may
  tune it out — the AI-boundary escape hatch (§29) exists specifically for this, deliberately deferred.
- **Under-populated companies look the same as broken ones**: the empty-state copy (§27) must be tested
  live to confirm it reads as "SIE is ready to help" rather than "nothing works yet."
- **Financial escalation false negatives**: if a founder's Finance snapshot is stale (§22), a real cash
  emergency could be silently missed rather than flagged as stale-and-possibly-wrong. The staleness framing
  must never simply omit the number.
- **Cross-system connective code becoming a second source of truth**: every §9 connection must call the
  existing endpoints/functions directly, never re-derive Finance or Build facts independently.

## 36. 10/10 product-direction critique

| Category | Assessment |
|---|---|
| Immediate clarity | Strong — one priority, one why, one action, above the fold. |
| Founder usefulness | Strong for Build+Finance; honestly limited for Fundraising until infrastructure exists. |
| Repeat-use value | Strong — tied to real state changes, not a calendar nudge. |
| Differentiation from generic AI | Strong — grounded in accumulated, structured, non-reconstructable state. |
| Trustworthiness | Strong — traceability (§21) makes every claim checkable; fact/inference/recommendation types (§6 of the directive) are kept distinct throughout. |
| Actionability | Strong — every action names a concrete task and a destination. |
| Simplicity | Strong — four sections max, one dominant. |
| Stage adaptability | Strong — a consequence of what data exists, not a special-cased branch. |
| Financial usefulness | Moderate-to-strong for Build+Finance; explicitly absent for Fundraising (honest, not a gap hidden by scope). |
| Longitudinal value | Strong today for Build; Finance's own snapshot history makes the same possible with a small connection. |
| Monetization potential | Strong — cross-system priority and longitudinal change are both genuinely hard to replicate outside SIE. |

No category scores weak enough to require revising the design before proceeding. **PASS.**

## 37. Recommended implementation sequence

- **38B — smallest useful Command Center vertical slice**: reuse `GET /ventures/{id}/recommendation`
  unmodified; add exactly one new read that layers Finance's tier-1 escalation check (`runway_months`
  crossed against a short, explicit horizon) on top of it, with Build as the fallback priority. Ship the
  four-section hierarchy (§6) replacing today's separate `CurrentQuestionCard` +
  `CompanyIntelligenceState` stack on Overview. No Fundraising, no Analyze integration yet.
- **38C — cross-system intelligence**: add the Build+Finance combined statement (hire-consequence framing),
  Decision+Finance consequence statements, Upcoming Decisions section, and the bounded Build+Analyze
  coverage-gap statement (§13). Still zero AI, zero new tables.
- **38D — decision/outcome integration depth**: staleness handling for undecided outcomes, founder-
  disagreement copy handling (§14/§25), plan-vs-actual (`pending_reconciliation`) surfaced as its own
  tier-4 candidate.
- **Deferred, no phase assigned**: Fundraising cross-system integration, pending a future, separate
  decision about whether to persist chosen fundraising scenarios at all.

## 38. Exact 38B scope

1. One new backend read (or one new lightweight endpoint) that: calls the existing Build recommendation
   logic, calls the existing Finance derived-metrics read, and applies the tier-1/tier-5/tier-7 subset of
   §7's priority ordering only (financial-critical, Build-default, no-urgent-action) — tiers 2-4/6 (which
   need the Build+Finance/Decision *connections*) are explicitly 38C.
2. One new Overview section replacing `CurrentQuestionCard` + `CompanyIntelligenceState`'s combined visual
   footprint with the four-section hierarchy from §6, using the copy patterns from §27.
3. The traceability disclosure (§21), since it is a pure read of facts already being fetched.

## 39. Phase 38B implementation (as built)

38B shipped the smallest useful vertical slice described in §38, entirely client-side. No new backend
endpoint was needed: `CommandCenter.tsx` calls the two existing, already-tested reads
(`GET /ventures/{id}/recommendation` via `CurrentQuestionCard`'s own unchanged fetch, `GET /ventures/{id}
/financials` via `getVentureFinancials()`, the same function `FundraisingSimulator.tsx` already calls) and
combines them with one small, pure, client-side comparison. No backend file was touched.

**Architecture chosen**: a new component, `dashboard/components/idea-lab/CommandCenter.tsx`, replaces the
old two-piece Overview stack (`CurrentQuestionCard` rendered directly + a private `CompanyIntelligenceState`
function inside `VentureWorkspace.tsx`). It wraps `CurrentQuestionCard` unmodified in its internals — every
testing/decision/outcome/contradiction-resolution interaction still lives exactly where it did — and adds
a `heading` prop (default `"What matters now"`, passed as `null` when Finance is occupying that slot
instead) so the same heading text is never rendered twice. `CompanyIntelligenceState`'s own content (the
"what SIE knows / still figuring out / what changed" summary, plus the VPS-category disclosure) moved into
`CommandCenter.tsx`'s own "Current context" section verbatim — not reimplemented, not duplicated.

**Priority contract (as built, 38B subset only)**: a small pure function,
`dashboard/lib/build/commandCenterPriority.ts::isFinancialConstraintActive(derived)`, returns `true` only
when `derived.status === "out_of_cash"`. This is intentionally narrower than the full `CommandCenterState`
contract sketched in §28 — 38B does not need `priority_type`/`urgency` as first-class fields, because
exactly two outcomes exist: the financial card renders, or it doesn't and `CurrentQuestionCard` owns the
slot. Tiers 2-4/6 from §7 (contradiction-as-priority, decision-consequence, plan-divergence, staleness)
were **not** implemented — they require the Build+Finance/Decision *connections* explicitly deferred to
38C.

### Financial override rule decision (Section 22 gate)

Read `app/ai/financial_engine.py::compute_derived_metrics()` directly before writing any override logic.
It produces exactly five `status` values (`insufficient_data`, `cash_flow_positive`, `break_even`,
`burning`, `out_of_cash`) and no runway-months threshold anywhere in the codebase — confirmed by also
reading `FinanceOverview.tsx`'s own `STATUS_COPY` mapping, which gives `"burning"` the same visual tone
regardless of how many months of runway remain. **No existing methodology establishes a "short runway"
cutoff at any number of months.** Per Section 22's own instruction, none was invented. The only condition
treated as a financial override is `status === "out_of_cash"` (cash at or below zero while burn is
positive) — an objective fact already labeled distinctly by the existing engine, not a threshold this
phase chose. `"burning"` with any amount of runway, however small, deliberately does **not** override
Build — this is asserted by an explicit unit test (`test_burning_with_any_runway_is_not_a_constraint`).

### Source mapping

| Command Center element | Source |
|---|---|
| Build priority, "why", primary action, traceability-free content | `GET /ventures/{id}/recommendation` (unmodified) |
| "Current context" (what SIE knows / still figuring out / what changed) | Same recommendation response's `company_intelligence` field (unmodified) |
| Financial priority card, its "why", its traceability | `GET /ventures/{id}/financials` → `derived` + `latest_snapshot` (unmodified) |
| VPS-category disclosure ("See the full breakdown by category") | `venture.model_result`, passed down from `VentureWorkspace.tsx` (unmodified) |

### UI behavior

- **Financial constraint active**: a red-tinted `BaseCard` renders first, with the "WHAT MATTERS NOW" eyebrow,
  a plain-language cash/burn sentence naming the actual snapshot date, a "Review your cash plan →" button
  linking to `?tab=finance`, and a "Why SIE is focusing here ▾" disclosure. `CurrentQuestionCard` renders
  immediately below with `heading={null}` — its own body (recommendation/testing/decision/outcome state)
  is completely unaffected.
- **No financial constraint**: `CurrentQuestionCard` renders with its own `"What matters now"` heading,
  byte-identical to its pre-38B behavior.
- **Current context**: renders whenever Build has any accumulated intelligence or a model exists — identical
  condition to the old `CompanyIntelligenceState`'s own gate, just relocated.
- **Finance fetch failure**: degrades silently (no error banner) — Finance is an optional, silent input to
  the priority decision, never a required one blocking the page.

### Test results

New test file `dashboard/tests/commandCenterPriority.test.ts` (registered as `npm run
test:commandCenterPriority`, included in the aggregate `npm test`): 6/6 passed, covering `null`,
`insufficient_data`, `cash_flow_positive` (Case C), `break_even`, `burning` with runway (the explicit
no-invented-threshold case), and `out_of_cash` (Case D). Full existing frontend suite (16 test files, all
pre-38B tests included) re-run: all passing, confirming the `CurrentQuestionCard`/`CompanyIntelligenceState`
refactor introduced zero behavioral regression. Backend suite unaffected (no backend file touched);
`test_venture_graduation`/`test_idea_lab`/`test_founder_workspace` re-run as a spot-check: 69/69 passing.
`tsc --noEmit`, `eslint`, and `next build` all clean.

### Live walkthrough results

- **ClaimPilot** (evidence-bearing venture, cash-flow data not yet financially constrained): Build's own
  "Define what specifically differentiates your solution from alternatives" priority rendered under the
  shared "What matters now" heading — confirmed byte-identical framing to pre-38B. The full interaction
  loop was exercised live end-to-end: the recommended-test button correctly hit the existing idempotency
  contract (`create_venture_mission`'s own dedup on an identical `vps_guidance` title, Phase 10.7 — not a
  38B regression, verified by reading that function directly), and a genuine custom test
  ("38B walkthrough test question") was created via `POST /ventures/893/missions` (200), correctly flipped
  the page into `TestingState` with the "What matters now" heading and the "What happened? / Record result"
  capture form intact, then was cleaned up (dismissed) after verification.
- **FridgeChef Renamed Private** (`venture_id=8212`), Finance set to cash=$0/burn=$5,000/mo
  (`status="out_of_cash"`): the financial priority card rendered correctly — "Your cash trajectory needs
  attention," the exact snapshot-dated sentence, a working "Review your cash plan →" link (confirmed
  destination `?tab=finance`), and a traceability disclosure that expanded to the literal cash/burn/
  snapshot-date/status facts. Build's own card rendered immediately below with no heading, exactly as
  designed.
- **Same venture, Finance changed to cash=$150,000/revenue=$10,000/mo/spend=$5,000/mo**
  (`status="cash_flow_positive"`): confirmed live that the financial card **disappeared entirely** and
  Build's own default priority rendered alone under the "What matters now" heading — Finance correctly
  contributed zero manufactured urgency (Case C).

### Known limitations

- Runway-based (non-zero-cash) financial escalation does not exist yet — deliberate, per the Section 22
  gate; a company burning cash with, say, 2 weeks of runway left but a positive cash balance will not
  trigger the financial card. This is the correct, honest behavior given no existing methodology
  establishes that threshold, not an oversight.
- No cross-system statements (Build+Finance, Decision+Finance, Build+Analyze) — 38C's own scope.
- No Upcoming Decisions section — 38C's own scope, per the directive's own explicit exclusion.
- The `resize_window` browser-automation tool continues to report success without actually changing
  `window.innerWidth` in this environment (confirmed again this phase — the same limitation documented in
  every prior phase this session). 38B's own layout is a single linear stack with no grid/table changes, so
  responsive risk from this phase's own work is low, but a true narrow-viewport screenshot was not obtained.

### Exact 38C boundary

38C inherits, unimplemented: contradiction-as-priority (tier 2), decision-consequence statements (tier 3),
plan-vs-actual divergence (tier 4), stale-undecided-outcome handling (tier 6), the Upcoming Decisions
section, and any Build+Finance/Decision+Finance/Build+Analyze cross-system statement. 38B's own
`isFinancialConstraintActive()` function and `CommandCenter.tsx` component are the extension points 38C
should build onto — not replace.
4. No Upcoming Decisions section yet (needs the Decision/Finance connections deferred to 38C) — its
   absence in 38B should render as nothing shown, not an empty placeholder.

No AI. No new table. No new score. No Fundraising touch.
