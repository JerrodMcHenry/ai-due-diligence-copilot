# SIE Financial Decision Engine V2

**Status:** Audit + design only (Phase 35A). No code was changed to produce this document. Every claim below
about "what exists" was verified by reading the actual file cited, not inferred from an earlier report.
Nothing here modifies SPS, Analyze, the existing Fundraising Simulator's math, or Build intelligence — see
§19/§20 for what those future connections should look like when a later phase builds them.

## 1. Product purpose

Help a founder make consequential, real-money company decisions — how much runway they have, whether they
can afford a hire, how much to raise, what a SAFE or priced round does to ownership — using their own actual
company numbers, calculated deterministically, remembered across sessions. Not a calculator collection: a
system organized around the specific decisions in §9, each answerable from persisted company state plus
explicit founder assumptions.

## 2. Why Finance belongs in SIE

The same reason Build does (`docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md` §1-§2): a generic AI chat has no
memory of a company's actual cash, no persisted cap table, and applies no deterministic rule consistently
across sessions. A founder who asks ChatGPT "can I afford this hire?" gets a plausible-sounding answer built
from whatever they retype that day. SIE, done right, holds the company's real numbers and produces the same
arithmetic answer every time, remembers what was modeled last month, and can compare that to what actually
happened.

## 3. Why not just use generic AI

Every Finance capability in this document must pass the test in §24 before it's in scope. The failure modes
this document explicitly rejects, per the directive: explaining financial concepts (any AI already does
this), generic fundraising advice, AI-estimated numbers presented as calculations, guessing company
valuation, predicting startup success, fabricated probabilities, or a bag of unrelated calculators with no
persisted state connecting them.

---

## 4. Existing repository inventory

Read end to end for this phase: `dashboard/lib/fundraising/{types,rational,errors,capTable,safe,pricedRound,runway}.ts`
(the calculation engine, Phase 21A), `dashboard/lib/fundraisingUi/{types,startingCapTable,runScenario,chainScenario,formatUi}.ts`
(the UI-facing translation layer, Phase 21B), `dashboard/components/fundraising/*.tsx` (10 components, 1,105
lines), `dashboard/tests/{fundraising,fundraisingUi}.test.ts` (871 lines, 30 test functions), `app/api.py`
(grepped for every fundraising/SAFE/cap-table/runway reference), `app/models/fundraising_readiness.py` +
`app/ai/fundraising_readiness.py` (a same-named but unrelated system), `app/ai/financial_analysis.py` (the
SPS Financial Health pillar), `app/ai/vps_guidance.py`/`vps_scoring.py` (how `capital`/`validation.monthly_revenue`
are actually used), `dashboard/types/ideaLab.ts` (`VentureAssumptions.capital`/`.validation`/`.economics`),
`dashboard/lib/simulate/directConsequences.ts` (the one existing deterministic financial calculation outside
the fundraising engine).

**The single most important finding of this audit: there are THREE unconnected "financial" systems in this
codebase today, and none of them talk to each other.**

| System | Where | Persisted? | What it actually is |
|---|---|---|---|
| Fundraising Simulator (cap table / SAFE / priced round / runway math) | `dashboard/lib/fundraising*`, `components/fundraising/*` | **No — 100% client-side, ephemeral React state. Confirmed: zero backend routes; `grep`ing `app/api.py` for fundraising/SAFE/cap-table finds nothing but an unrelated Action-Plan constant.** | A rigorous, well-tested, deterministic calculation engine with no persistence layer at all. |
| Fundraising Readiness | `app/ai/fundraising_readiness.py`, `app/models/fundraising_readiness.py` | No (recomputed fresh every request from already-stored pillar analysis) | A **score**-based (0-100) assessment of how *defensible* a canonical Startup's SPS pillar scores are for a fundraising conversation. Has nothing to do with cap tables, SAFEs, runway math, or cash. Confusingly similar name, unrelated system. |
| SPS Financial Health pillar | `app/ai/financial_analysis.py` | Yes, as part of the Startup's stored pillar analysis | An **LLM-judged qualitative assessment** of runway/burn/unit economics from free text evidence — explicitly NOT a calculation (`analyze_pillar()`'s own generic LLM-call machinery, temperature 0, JSON output, but still a language-model judgment, not arithmetic on stored numbers). |

None of these three should be confused with each other in this document or in a future implementation. **A
fourth, much thinner thing exists too:** `VentureAssumptions.capital = {starting_capital, monthly_burn}` and
`VentureAssumptions.validation.monthly_revenue` — two persisted numbers on the founder's own Venture, but
they are used ONLY as a single text line fed into the hidden VPS-scoring prompt (`vps_guidance.py:70-72`,
`_has_meaningful_commercial_scale()`) — never for a runway calculation, never read by the Fundraising
Simulator, never connected to Build's recommendation engine (confirmed directly: this is the exact gap
`docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md`'s Case I test proves — setting these fields to an extreme
"critical runway" value produces a byte-identical recommendation before and after).

### 4.1 Inventory table

| Area | WHAT EXISTS | Partial? | UI-only? | Backend-only? | Tested? | Unused? | Duplicated? | Missing |
|---|---|---|---|---|---|---|---|---|
| SAFE (single, valuation cap) | `safe.ts::computeSafeConversion()` — Y Combinator Post-Money SAFE "Company Capitalization" method, cited to the official v1.2 User Guide, cross-checked against its own Appendix II worked example | — | — | — | Yes (`fundraising.test.ts`) | No | No | Pre-money SAFEs entirely absent (type system has no such shape) |
| SAFE discount / MFN | `SafeInput.discountPercent` field exists in the type | **Partial — recognized shape, explicitly rejected at conversion** (`validateSafeForConversion()` throws if `valuationCapCents` is null) | The UI (`UiSafeTerm`) doesn't even collect a discount — `runScenario.ts::buildSafeInputs()` hardcodes `discountPercent: null` | — | No (nothing to test — unreachable) | Effectively yes | No | Discount-only/MFN-only SAFE conversion math (no primary-source-verified formula found during Phase 21A's own research, documented honestly rather than guessed) |
| Multiple SAFEs → one round | `computeSafeConversion()` takes `safes: SafeInput[]`, solves the self-referential "Company Capitalization" equation across all of them at once | — | — | — | Yes | No | No | — |
| Priced round (no SAFEs) | `pricedRound.ts::runSimplePricedRound()` | — | — | — | Yes | No | No | — |
| SAFE(s) + triggering priced round | `pricedRound.ts::runSafeConversionAndPricedRound()` | Partial — defensively **blocks** (does not silently compute) the case where a SAFE's cap-implied price beats the round's own price, since no primary source was found for the correct resolution | — | — | Yes | No | No | The blocked case's actual conversion formula |
| Sequential rounds (Round 2 on top of Round 1's result) | `chainScenario.ts::chainOwnershipFromResult()` | **Partial, by design** — re-derives the next round's starting point from 2-decimal-rounded DISPLAY percentages, not the engine's exact rational fraction. A single round's own math is always exact; only the hand-off between rounds loses precision | — | — | Yes | No | No | An exact, persisted multi-round timeline |
| Option pool | `PricedRoundInput.optionPoolIncreaseShares` (absolute share count) | **Partial** — V1 explicitly does NOT solve "target X% pool post-money" (a circular solve with price-per-share); the UI's `optionPoolIncreasePercentOfCurrent` is sugar over the PRE-round total only | — | — | Yes | No | No | Post-money target-percentage pool solve |
| Dilution (point change vs. % dilution) | `pricedRound.ts::computeDilution()` — correctly distinguishes the two, never conflates them | — | — | — | Yes | No | No | — |
| Cap table / ownership invariant | `capTable.ts` — total shares always DERIVED (never tracked separately), an explicit `assertOwnershipInvariant()` | — | — | — | Yes | No | No | — |
| Bridge round | — | — | — | — | — | — | — | **Entirely absent.** No type, no UI, no test, no mention anywhere in the fundraising code. |
| Runway | `runway.ts::computeRunway()` — `cashOnHandCents / monthlyBurnCents`, nothing else | **Severely partial** — burn is "a single caller-supplied constant, held flat" (the module's own comment); no revenue/expense breakdown feeds it, no dated changes, no month-by-month projection | Also exists as a bolt-on before/after-financing comparison inside the Fundraising Simulator's own UI, using numbers the founder retypes into that scenario (never read from any persisted venture state) | — | Yes | No | **Yes, sort of** — this deterministic runway and the SPS Financial Health pillar's *LLM-judged* "runway" dimension are two entirely different, unconnected concepts sharing a name | Monthly cash-flow projection; connection to persisted `capital.starting_capital`/`monthly_burn`; revenue/expense line items |
| Burn | Same single constant as runway above | Severely partial | Same | — | Indirectly | No | No | Payroll/contractor/software/marketing/rent/other line items; any structural connection between "burn" and actual expense categories |
| Hiring | — | — | — | — | — | — | — | **Entirely absent.** No type, table, UI, or test anywhere models a hire's cost or start date. |
| Revenue (recurring vs. non-recurring) | `VentureAssumptions.validation.monthly_revenue` (a single flat number) | Severely partial | — | Persisted (Venture JSONB) | Not finance-tested | Effectively (never read by any financial calculation) | — | Any recurring/non-recurring split, growth-rate modeling, or connection to runway |
| Scenario comparison | `FundraisingScenarioCompare.tsx` — exactly two scenarios, capital/founder-ownership/runway only, explicitly never declares a winner ("Part 21/26: no recommendation, no score") | Partial — fixed at 2, not N-way; no burn/hiring/expense rows; nothing persisted | Yes (pure props, no storage) | — | Not separately tested (covered via `fundraisingUi.test.ts`'s underlying `runScenario` calls) | No | No | Persistence, N-way comparison, non-ownership metrics |
| Cash/financial state persistence | — | — | — | — | — | — | — | **No table, no model, no endpoint anywhere persists a founder's cash, expenses, or financing history.** The entire fundraising engine is recomputed from scratch every time the component mounts. |
| Fundraising Readiness (score) | `app/ai/fundraising_readiness.py` | — | — | Backend-only, computed fresh per request, zero persistence | Yes (`test_fundraising_readiness.py`, 44 tests) | No | No | Unrelated to this phase's scope except as a naming collision to avoid |
| SPS Financial Health pillar | `app/ai/financial_analysis.py` | — | — | Backend, persisted as part of pillar analysis | Yes (via calibration suite) | No | No | Not a calculation engine at all — LLM judgment over evidence text |

### 4.2 What is already strong (do not break)

- The bigint/`Rational` arithmetic discipline (`rational.ts`) — money is always integer cents, shares always
  integer counts, percentages always exact fractions, NEVER a floating-point `number`. This is exactly the
  "no fake precision" rule the 35A directive re-states in §2 — the codebase already enforces it at the type
  level for everything it currently models.
- The YC Post-Money SAFE citation discipline: the engine names its exact primary source (User Guide v1.2)
  and cross-checks against that source's own worked example in a golden test, rather than a plausible-looking
  formula nobody verified.
- The ownership invariant (`assertOwnershipInvariant`) — total ownership sums to exactly 100% by
  construction, checked, not assumed.
- The 4-step wizard UX (chooser → ownership → terms → result) — the user has specifically called this out as
  one of SIE's strongest existing interactions. It should be **extended**, never replaced.
- The "block, don't guess" discipline for the one case Phase 21A couldn't verify (SAFE cap beats round
  price) — a defensible, honest failure mode.
- `FundraisingDisclaimer`'s copy is already exactly right for §15/§16 of this phase's directive: "You don't
  need to raise money... this is here for when it becomes relevant to you" — no verification gate, no stage
  gate, already true today.

---

## 5. Existing fundraising engine assessment

**Strong and correct for what it covers; covers a narrow slice of real fundraising structures.** Post-money
SAFE with a cap: solid, cited, tested. Everything else in the SAFE/round space (discount/MFN SAFEs, bridge
notes, pre-money SAFEs, target-percentage option pools, exact multi-round chaining) is either explicitly
unsupported-and-documented or silently absent. The engine's own discipline of "document the gap rather than
guess" (Phase 21A's own precedent) is exactly the discipline this phase's V2 design should continue.

## 6. Existing runway/burn assessment

**The weakest link, architecturally.** Three unrelated notions of "runway" exist (deterministic in the
Fundraising Simulator scoped to one scenario; a hidden VPS text line; an LLM-judged SPS pillar dimension),
and none of them read from or write to a persisted, single source of truth for a company's actual cash
position. There is no month-by-month projection anywhere. This is precisely the gap V2 should close first
(§25 P0).

## 7. Existing cap-table assessment

Genuinely solid ownership math (§4.2). The gap is entirely about WHAT FEEDS IT (no persisted starting cap
table — a founder re-enters starting ownership percentages from scratch every time they open the
simulator) and WHAT HAPPENS AFTER (a completed round's result is never saved; "model another round" is a
lossy, in-memory convenience, not a real financing history).

## 8. Existing scenario infrastructure assessment

`FundraisingScenarioCompare` proves the RIGHT interaction pattern already exists in this codebase (compare
two plans side by side, name the concrete differences, never declare a winner) — it just needs to (a)
generalize beyond exactly 2 scenarios, (b) generalize beyond cap-table-only metrics to include burn/runway/
hiring, and (c) persist. The separate, Venture-side "What-If" system (`dashboard/lib/simulate/*.ts`,
`WhatIfPanel.tsx`) is a DIFFERENT, qualitative, VPS-category-preview mechanism — Phase 34B/34G's own
documents (`SIE_BUILD_METHODOLOGY_V1.md` §16, §18) already flagged it for eventual removal from primary Build
navigation and explicitly forbid resurrecting it as the basis for financial scenarios. **V2's scenario system
should be built new, modeled on `FundraisingScenarioCompare`'s discipline, not on Venture What-If's.**

---

## 9. Founder financial decision taxonomy

Organized around founder questions, per the directive's own instruction not to organize around calculators.

| Question | In scope for V2? | Why |
|---|---|---|
| How much runway do I have? | **Yes — P0** | The foundational question everything else depends on. |
| When does cash run out? | **Yes — P0** | Same calculation, dated. |
| What is driving burn? | **Yes — P0** | Requires the expense-category breakdown (§10). |
| What happens if expenses/revenue change? | **Yes — P0/P1** | The scenario system (§16) applied to the runway engine. |
| Can I afford this hire? / this hiring plan? | **Yes — P0** | §17. |
| When can I make the hire? | **Yes — P1** | A raise-size/timing question (§19) applied to a hire. |
| How does hiring affect runway? | **Yes — P0** | Same engine, one line item. |
| What happens if the start date moves? | **Yes — P0** (the monthly-projection engine makes this free) | |
| Fully-loaded cost? | **Yes — P0** | A hiring-model field (§17). |
| How much should I raise for 12/18/24 months? | **Yes — P1** | §19, "raise-size planning." |
| When should I begin fundraising? | **Yes, carefully — P1** | §20 — calculable ONLY from an explicit founder-stated runway buffer, never a duration prediction. |
| What does the round do to runway/ownership? | **Yes — P0** | Existing engine + persisted cash. |
| What financing structure am I modeling? | **Yes — P0/P1** | SAFE/priced/bridge (§18). |
| Founder ownership after financing? | **Yes — P0** | Existing engine, extended with persistence. |
| SAFE conversion / priced round / option-pool impact | **Yes — P0** | Already built; needs persistence + minor extension. |
| Dilution compounding across rounds | **Yes — P1** | Needs the exact (non-lossy) multi-round chain (§8's gap). |
| SAFE vs. priced round / bridge vs. priced / smaller vs. larger raise | **Yes — P1** | The generalized scenario-comparison system (§16). |
| Raise now vs. later (explicit assumptions) | **Yes — P1** | Same. |
| Multiple SAFE scenarios / different valuations | **Yes — P0/P1** | Already substantially built. |
| Hire now vs. later / one vs. three | **Yes — P0/P1** | The hiring model + scenario compare. |
| Cut burn / increase marketing spend | **Yes — P1** | Expense-category editing + projection. |
| Lose a customer / add recurring revenue / revenue grows slower | **Yes — P1** | Revenue assumption fields (§10) + projection. |
| Delay fundraising | **Yes — P1** | Timing (§20) as a scenario. |
| Change founder salary / contractor spend | **Yes — P1/P2** | Expense-category editing; P2 if it requires a dedicated "founder comp" concept beyond a generic expense line. |
| Full accounting reconciliation, tax, payroll processing | **No — P3/out of scope** | §19 (not accounting software). |
| AI-predicted valuation / success probability | **No — never in scope** | §2's governing rule. |

---

## 10. Financial state model

**Minimum persisted state, evaluated field by field against the directive's own checklist:**

- **Cash:** `cash_on_hand_cents` (integer cents, matching the existing engine's own unit discipline),
  `as_of_date`. One current value, not a ledger — this is not accounting software (§19).
- **Revenue:** `monthly_recurring_revenue_cents` (current, actual), optionally
  `monthly_non_recurring_revenue_cents`. Growth assumptions (e.g. "+8%/month") are NEVER stored here — they
  belong exclusively to a scenario (§16), never to the actual/current state (§5 of the directive, and §12
  below).
- **Expenses, by category** (minimum viable set, not a full chart of accounts): `payroll_cents`,
  `contractors_cents`, `software_cents`, `marketing_cents`, `rent_cents`, `professional_services_cents`,
  `other_cents`. Each a current-month actual.
- **Burn:** **calculated, not stored** — `sum(expenses) - revenue`, always derived, per the directive's own
  suggestion ("runway should generally be calculated from financial state rather than manually treated as
  truth"). A founder MAY also directly state a single "monthly burn" figure when they don't want to break it
  into categories (mirrors `VentureAssumptions.capital.monthly_burn`'s existing shape) — stored with
  provenance `founder_entered` and flagged as a coarser input than the category breakdown, never silently
  preferred over it if both exist.
- **Runway:** never stored — always computed from the state above (§13).
- **Team / hiring plan:** a list of planned-hire rows — `role`, `monthly_fully_loaded_cost_cents` (salary +
  payroll burden, pre-computed once at entry per §17, not recomputed from a raw salary + %burden pair on
  every read — simpler, and matches the directive's own "fully-loaded cost" framing as the atomic input),
  `start_date`, `one_time_cost_cents` (recruiting/equipment, optional), `status` (`planned` | `committed` |
  `active` | `cancelled`).
- **Financing:** existing SAFEs (reuse `SafeInput`'s exact shape), existing priced rounds (reuse
  `PricedRoundInput`'s exact shape, extended with a `closed_date`), current option pool size, planned (not
  yet closed) financing as a first-class distinct list from closed financing.

**Explicitly NOT modeled (§19's boundary):** invoices, bank reconciliation, payroll tax withholding,
accounts payable/receivable aging, multi-entity consolidation, GAAP revenue recognition nuance. If a
proposed field mainly helps reconcile a bookkeeping record rather than answer one of §9's questions, it does
not belong here.

## 11. Provenance model

Six values, directly reusing the vocabulary Phase 34D/34G-A already established for Build evidence
(`FOUNDER_SAID`/`FOUNDER_OBSERVED`/`SIE_INFERRED`/`SIE_CALCULATED`/`EXTERNAL_SOURCE`/`STILL_UNKNOWN`) with
two Finance-specific additions, since the directive names concepts Build's vocabulary doesn't quite cover:

| Value | Means | Example |
|---|---|---|
| `FOUNDER_ENTERED` (≈ Build's `FOUNDER_SAID`/`FOUNDER_OBSERVED` collapsed — Finance doesn't need the claim/observation distinction Build does, since every actual is a direct entry) | The founder typed this as a current fact. | "Current cash: $600,000." |
| `SIE_CALCULATED` | Deterministic arithmetic from other stored values. | Burn = expenses − revenue. Runway = cash ÷ burn. |
| `ASSUMPTION` | An explicit, scenario-scoped hypothetical the founder is testing, never treated as current fact. | "MRR grows 10%/month" (§ example from the directive, reproduced exactly). |
| `PLANNED` | A decision the founder intends to execute but hasn't yet (a hire not yet started, financing not yet closed). | "Hire a senior engineer starting Nov 1." |
| `HISTORICAL_ACTUAL` | A past actual, retained after time passes — the same row that was once `FOUNDER_ENTERED` "current," now read historically. | "Cash on March 1 was $610,000." |
| `EXTERNAL_SOURCE` | Reserved, matching Build's own reserved value — no integration produces this in V2. | — |

**The governing rule, restated exactly as the directive states it:** a forecast is never treated as an
actual. `monthly_recurring_revenue_cents` (current, `FOUNDER_ENTERED`) and a scenario's "MRR grows 10%
monthly" (`ASSUMPTION`, scoped to one scenario object, never written back to the actual state) are
different kinds of information and must never share a column, a table, or a rendering treatment that could
blur them. This is the same firewall discipline `vps_scoring.py`'s own module docstring already enforces for
`validation` (observed) vs. every other assumption group (modeled) — Finance V2 should follow the identical
pattern, not invent a new one.

---

## 12. Runway methodology

Extend, don't replace, `runway.ts::computeRunway()` — its cash÷burn arithmetic is correct and stays exactly
as-is for the single-number case. The extension is a **monthly cash-flow projection**, because a company's
`VentureAssumptions.capital`-shaped "one constant burn number" cannot honestly answer "what happens if this
hire starts in month 4" (directive §6/§7).

**Projection shape**, per the directive's own example:

```
Month 1: starting_cash, revenue, expenses (sum of active line items THIS month), net_burn, ending_cash
Month 2: ending_cash(1) as starting_cash, ... (each line item re-evaluated against its own effective date)
...
```

Each expense/revenue/hiring line item carries an **effective date range** (a planned hire's cost only
applies from its `start_date` onward; a financing event injects `new_money_cents` into `ending_cash` in the
month it closes). This is what makes hiring dates, financing dates, and dated cost changes modelable without
"fake precision" — the projection is exact arithmetic given the stated dated assumptions, never a smoothing
or trend-fit.

**Determine whether the existing engine can support this:** `runway.ts` cannot, as written — it takes a
single flat `RunwayInput{cashOnHandCents, monthlyBurnCents}`. The projection is a genuinely new function
(`projectMonthlyCashFlow()`, illustrative name) that CALLS `computeRunway()` per month (or reimplements the
one-line division inline, since it's trivial) rather than replacing it — `computeRunway()` remains the
correct tool for "what's my runway right now, flat," and the projection is the correct tool for "what
happens over time as dated things change." Both stay pure functions, `Rational`/cents throughout, zero
floating point.

## 13. Hiring methodology

A planned hire is a **projection line item**, not a new subsystem (directive §7: "do not build HR
software"). Fields: `role` (display only), `monthly_fully_loaded_cost_cents` (the ONE number the projection
needs — computed once at entry from salary + payroll-burden %, or entered directly for a contractor with no
burden), `start_date`, `one_time_cost_cents` (applied once, in the start month, e.g. equipment/recruiting
fees), `status`.

**Deterministic answer to "can I afford this hire?"**: run the monthly projection twice — once without the
hire, once with it added at its `start_date` — and report the resulting runway difference, exactly as the
directive's own worked example does (10 months → 6.8 months). Multiple hires are simply multiple line items
in the same projection; "hire one now vs. three now" is the same projection run with a different subset of
planned-hire rows active — no separate mechanism needed. Founder salary changes are represented identically
(a compensation-line item with an effective-date change, not a new concept).

## 14. Fundraising methodology

**Preserve exactly:** the post-money SAFE conversion math (`safe.ts`), the priced-round math
(`pricedRound.ts`), the ownership invariant (`capTable.ts`), the "block rather than guess" behavior for the
one unverified SAFE-cap-vs-round-price case. None of this needs to change — it needs a persistence layer put
underneath it (§22).

**Extend:**
- **Multi-round chaining, exactly** (not the current lossy display-rounding hand-off, §4.2/§8): once
  financing events are persisted rows (§22) rather than transient UI state, "the next round's starting cap
  table" is simply "the last persisted `CapTableState`," carried at full `Rational`/bigint precision — the
  lossy conversion in `chainScenario.ts` becomes unnecessary once there's a real row to read from instead of
  a rounded display string.
- **Discount-only/MFN SAFEs:** still explicitly out of scope for V2 unless a primary-source-verified formula
  is found (same honest-gap discipline as V1) — do not guess a formula to make the type system's existing
  `discountPercent` field "useful."
- **Bridge:** minimum useful model per the directive's own instruction not to build exotic structures nobody
  needs. A bridge is, mechanically, a SAFE or a small convertible note with a shorter expected time-to-next-
  round — **V2 should model it as a SAFE with an explicit `intendedAsBridge: true` flag purely for labeling
  and runway-timing framing**, not a new conversion formula. If real founder usage later shows bridge notes
  need genuinely different math (e.g. a maturity date with interest), that is a V3 decision made from real
  usage data, not guessed now.

## 15. Raise-size methodology

New, deterministic, and exactly bounded to what's calculable (directive §9):

```
required_capital = (desired_runway_months × projected_monthly_net_burn_at_target_state) − current_cash
```

where `projected_monthly_net_burn_at_target_state` comes from the SAME monthly projection engine (§12),
evaluated at the point after all stated planned changes (a hiring plan, a cost cut) have taken effect — never
today's burn extrapolated blindly forward if the founder has already told SIE burn will change. Output is
labeled, per the directive's own explicit structure requirement, in four distinct blocks:

```
CURRENT ACTUALS       — cash, today's burn, sourced from persisted financial state
PLANNED CHANGES       — the hiring/cost items the founder has entered as PLANNED
SCENARIO ASSUMPTIONS  — anything hypothetical only for this calculation (e.g. "assume no revenue growth")
CALCULATED RESULT     — the required capital number, labeled "a modeled capital requirement under these
                         assumptions," never "you should raise exactly $X"
```

## 16. Scenario methodology

Generalize `FundraisingScenarioCompare`'s existing, correct discipline (compare named plans, never declare a
winner) into a reusable, **persisted** Financial Scenario object:

- A scenario is a **named, saved snapshot of proposed changes** against the current financial state — a set
  of hypothetical planned-hire rows, hypothetical financing events, and/or hypothetical revenue/expense
  assumptions — never a mutation of the actual state.
- Running a scenario produces: ending cash, monthly burn trajectory, runway, ownership/dilution (only when
  the scenario includes a financing event), capital required (only when the scenario is a raise-size
  question), and the scenario's own stated assumptions, restated back to the founder (§17's "show the
  criteria" requirement).
- N-way comparison, not fixed at 2 — `FundraisingScenarioCompare`'s table-row pattern generalizes cleanly to
  additional columns.

## 17. Decision comparison methodology

Organize comparisons around a NAMED founder decision (directive's own "Plan A / Plan B / Plan C" framing),
where each plan is one Financial Scenario (§16). The comparison surface shows the relevant consequences
(ending cash, runway, burn, ownership where applicable) side by side, restates each plan's own defining
assumption, and **never declares a universal winner** — extending, not inventing, `FundraisingScenarioCompare`'s
existing "here's what changes" framing. A future SIE intelligence layer MAY contextualize the tradeoff
(§18/19) — explicitly deferred, not built in V2.

## 18. Actual vs. plan vs. scenario rules

Three states, never blurred (directive §5's own worked example, generalized):

- **ACTUAL** — `FOUNDER_ENTERED`/`HISTORICAL_ACTUAL` current financial state. What SIE treats as true today.
- **PLAN** — `PLANNED` items the founder intends to execute (a hire not yet started, a financing round not
  yet closed) — real intent, not yet real cash movement. Included in projections by default (a founder
  planning to hire presumably wants to see that hire's effect), but always visually distinguished from
  ACTUAL.
- **SCENARIO** — `ASSUMPTION`-tagged hypotheticals scoped to one named, saved comparison, never merged into
  ACTUAL or PLAN unless the founder explicitly "commits" a scenario (an explicit action, mirroring Build's
  own "founder confirms before anything becomes canonical" discipline, §13 of the architecture doc).

## 19. Future Build-intelligence connection (design only)

Per the directive's own example, reproduced and extended: Build knows "repeatable acquisition remains
unresolved" (a Company Intelligence fact, `docs/product/SIE_INTELLIGENCE_ADVANTAGE_V1.md` §7). Finance
calculates "hiring 3 sales reps drops runway from 10.1 to 6.0 months" (a deterministic result, §13). Neither
system touches the other's math. A FUTURE phase could have a thin, deterministic connector surface a single
sentence like "this plan reduces the time available to resolve the acquisition question from ~10 months to
~6" — but the exact wording of that sentence, and whether it needs any AI synthesis at all (versus a fixed
template keyed off which Build stage is currently unresolved), is a decision for that future phase, not this
one. **Nothing here is implemented; Build's evidence/recommendation code and Finance's financial-state code
remain completely unaware of each other after 35A.**

## 20. Future Analyze/SPS connection (design only)

Potential future flow, exactly as the directive frames it: `FINANCIAL STATE → ACTUAL/ASSUMPTION PROVENANCE →
ANALYZE → FINANCIAL HEALTH → SPS`. What could safely flow: a persisted, `HISTORICAL_ACTUAL`-provenance cash/
burn/runway figure, IF a venture later graduates to a canonical Startup (mirrors the existing
Build→Analyze provenance-context idea already documented in `SIE_INTELLIGENCE_ADVANTAGE_V1.md` §11 — never
an input to the SPS scoring FORMULA itself, only citable context, same firewall `SIE_BUILD_METHODOLOGY_V1.md`
§15 already establishes for Build evidence generally). What must stay scenario-only, permanently: every
`ASSUMPTION`-tagged number, and every `PLANNED` item that hasn't actually happened yet. **Contamination
risk, named explicitly:** if a scenario's hypothetical burn number were ever read by Analyze as if it were
`financial_analysis.py`'s already-real evidence, a hypothetical would silently become canonical company
truth — exactly what the directive's §14 warns against. The correct guard, when this connection is
eventually built, is the same provenance-filtering discipline `app/api.py` already applies for Build evidence
(`superseded_by_id IS NULL`-style filtering, generalized to `provenance != 'ASSUMPTION' AND provenance !=
'PLANNED'`) — not a new mechanism.

## 21. Continuous-company architecture

Per Phase 34F's own doctrine (`SIE_FOUNDER_PRODUCT_DOCTRINE_V1.md` — "stage changes guidance, evidence
changes confidence, verification changes trust, none determine feature access"), Finance must attach to the
founder's **Venture** (the continuous workspace, from idea onward), never gated behind a canonical Startup
entity or graduation. This is both the safer and the already-established direction: `modeled_ventures` is
already the durable, user-owned row every other Build concept (missions, evidence, decisions) attaches to
via `venture_id`; Finance tables should follow the exact same `venture_id` foreign-key pattern, not invent a
parallel ownership model. A venture that later graduates to a Startup keeps its full financial history
(mirrors `venture_evidence`/`venture_decisions` already surviving graduation untouched, per
`SIE_BUILD_METHODOLOGY_V1.md` §14).

---

## 22. UX / information architecture

**Audited first, per the directive's own instruction not to assume the current tab must stay as-is.** Today:
one "Fundraising" tab inside `VentureWorkspace.tsx`, containing the entire 4-step wizard. This works well
for its one job (a single cap-table scenario) but has no room for runway/hiring/scenario-comparison without
becoming cluttered.

**Recommended reorganization** (illustrative structure, per the directive's own framing) — a **Finance**
tab, replacing "Fundraising" as the top-level label, with the existing wizard becoming one section of it
rather than the whole tab:

```
FINANCE
  OVERVIEW      — current cash, monthly revenue, monthly spend, net burn, runway (the new, P0 surface)
  PLAN          — hiring, operating changes, raise-size planning (P0/P1)
  FUNDRAISING   — the EXISTING wizard (chooser → ownership → terms → result), unchanged, just relocated
                  one level down instead of being the entire tab
  SCENARIOS     — compare saved plans (generalized FundraisingScenarioCompare)
  OWNERSHIP     — persisted cap table / dilution over time (reads the same engine, now backed by real rows)
```

Five sub-areas, not five separate top-level tabs (avoiding "too many tabs," per the directive's own
warning) — a single "Finance" tab with an internal sub-nav, matching the density `VentureWorkspace.tsx`
already uses for Overview/Fundraising/History today. **Progressive disclosure for Idea Stage (§16 of the
directive):** OVERVIEW shows "Add cash and monthly spending when you have them" (mirroring
`FundraisingDisclaimer`'s existing tone) rather than a blank multi-field form; FUNDRAISING keeps its existing,
already-good chooser-first flow, which already requires nothing but curiosity to start. Stage changes what's
shown/explained by default, never what's accessible — full compliance with §15.

## 23. Keep Fundraising's current strength

What makes it work, precisely: (1) the chooser step asks one plain-language question ("SAFE, priced round,
or both?") before any numbers, (2) the ownership builder is a separate, focused step from the terms step, so
a founder is never filling in ten fields on one screen, (3) the result screen shows a `trace` — a short,
labeled list of exactly what happened at each calculation step — which is the existing precedent for
"explain the math, don't just show the number." **Keep this wizard exactly as-is**, relocate it under the new
Finance/Fundraising sub-tab, and reuse its `trace`/`ScenarioResult` shape as the template for how the new
runway/hiring/raise-size surfaces should explain their own results.

---

## 24. Data architecture options

Three options evaluated, mirroring the framing `SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md` §C already used
successfully for Build:

| | A: dedicated table per concept | B: one generic financial-event table | C: hybrid (recommended) |
|---|---|---|---|
| Tables | `financial_state`, `planned_hires`, `financial_scenarios`, `financing_events` (4+) | 1 polymorphic table | 3: `venture_financial_state`, `venture_financial_line_items`, `venture_financial_scenarios` |
| Complexity | Highest | Lowest schema surface, highest query-time complexity | Moderate |
| Queryability | Best | Poor (payload-shaped) | Good |
| Matches existing convention | — | No (Build explicitly rejected this shape too, §C of its own doc) | **Yes — same reasoning Build already used** |
| Risk of premature abstraction | Moderate (a full `financing_events` table for a V2 that reuses Build's own SAFE/round types almost verbatim may be overkill) | Low abstraction risk, high type-safety loss | Lowest realistic risk |

## 25. Recommended architecture

**Three new tables, all `venture_id`-scoped, following `venture_evidence`'s exact ownership-join pattern
(`JOIN modeled_ventures v ON v.id = ... WHERE v.user_id = :user_id`):**

1. **`venture_financial_state`** — one row per venture (or a small append-only history of "as-of" snapshots,
   mirroring `venture_model_updates`' own before/after-snapshot precedent rather than update-in-place, since
   the directive's §23 explicitly wants "what was our burn 6 months ago" answerable later). Columns: cash,
   revenue fields, expense-category fields (§10), `as_of_date`, `provenance`, `recorded_at`.
2. **`venture_financial_line_items`** — planned hires, planned/closed financing events (SAFEs, priced
   rounds), and scenario-scoped hypothetical line items, distinguished by a `kind` column
   (`planned_hire`/`safe`/`priced_round`/`scenario_assumption`) and a `status`
   (`planned`/`committed`/`closed`/`scenario_only`) — one flexible-but-typed table rather than four nearly-
   identical ones, since all four share the same shape (an effective date, a cash-flow-relevant amount, a
   provenance/status). This is the ONE place a Build-style "one generic table" (Option B) is actually the
   right call, because unlike Build's Evidence/Decision (which needed real FKs to many other objects), these
   rows only ever need to be summed by date and filtered by status — exactly the shape Option B handles
   well.
3. **`venture_financial_scenarios`** — a named, saved scenario: `venture_id`, `name`, `description`, a JSONB
   `line_item_overrides` (which `venture_financial_line_items` rows this scenario adds/removes/modifies,
   relative to the actual state), `created_at`. Kept as one JSONB payload rather than exploded further,
   because a scenario is fundamentally "a labeled diff," and Build's own `venture_model_updates` already
   established that a before/after diff is fine to store as JSONB when it's read as a whole, never queried
   field-by-field (`SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md` §A's own precedent for that table).

**Reused verbatim from the existing engine, unmodified:** `dashboard/lib/fundraising/*.ts`'s types
(`SafeInput`, `PricedRoundInput`, `CapTableState`) become the in-memory shapes a persisted
`venture_financial_line_items` row is converted to/from — the calculation engine itself needs zero changes;
only its inputs/outputs gain a database home, exactly Build's own finding that its evidence-classification
logic (`captureSignals.ts`) needed nowhere to persist, not new logic (`SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md`
§A's "the system already performs real classification and discards it" finding, restated here for Finance).

**Passes the reload/history/scenario test:** a persisted `venture_financial_state` row survives reload
(direct DB read); `venture_financial_line_items` gives hiring/financing plans stable identity across
sessions; `venture_financial_scenarios` lets a saved comparison be reopened later, unlike today's
component-local `ScenarioDraft` state which vanishes on navigation.

## 26. New tables proposed

`venture_financial_state`, `venture_financial_line_items`, `venture_financial_scenarios` (§25). Illustrative
names, not final — a future implementation phase should validate them against real migration/query
ergonomics before committing.

## 27. Existing tables reused

`modeled_ventures` (the `venture_id` FK target, unchanged). `VentureAssumptions.capital`/`.validation` stay
exactly as they are — they remain the hidden VPS-scoring inputs they already are; V2's own financial state is
a NEW, separate, richer store, not a migration of those two fields (migrating them would risk silently
changing what VPS's existing text-assembly reads, which is explicitly out of scope, §28's "do not modify
existing financial math").

## 28. Migrations eventually required (not run in this phase)

Three `CREATE TABLE IF NOT EXISTS` additions (§25), following this codebase's own idempotent
`create_*_table()`-called-at-startup-in-a-try/except convention (`CLAUDE.md`'s own documented pattern) — zero
`ALTER TABLE` on any existing table, zero destructive migration, matching Build's own "additive only"
precedent (`SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md` §M).

## 29. Testing strategy

Mirror the existing, working two-layer split exactly: **pure-function tests** for the calculation engine
(extending `fundraising.test.ts`'s own convention — the monthly-projection function, raise-size formula, and
hiring-impact function should all be zero-import, plain-Node-testable pure functions, same discipline
`rational.ts`/`safe.ts` already have), and **API/ownership tests** (mirroring `test_build_intelligence_loop.py`'s
own `_auth_headers`/`_patched_auth`/ownership-scoping conventions) for the new persistence endpoints. Golden
test cases should include the exact worked examples in this document (§30) and the directive's own Cases
A-J, run once real endpoints exist.

## 30. Risks

- **Contamination risk (§20):** a scenario's hypothetical becoming canonical truth if a future Analyze
  connection is built carelessly. Mitigated by the provenance-filtering pattern already proven in Build.
- **Precision risk:** any temptation to store money as a JS `number` instead of integer cents/bigint would
  silently reintroduce the exact class of bug this codebase's existing engine already eliminated — the new
  tables must store cents as integers (`BIGINT` columns), never `NUMERIC`/`FLOAT`.
- **Scope creep toward accounting software (§19):** the expense-category list must stay fixed and small; a
  request for a full chart of accounts, AP/AR, or multi-entity support should be declined per this document's
  own boundary.
- **False precision in the monthly projection:** a 24-month projection built on today's numbers can look
  more authoritative than it is; every projection surface must carry the same "modeled, not predicted"
  framing `FundraisingDisclaimer` already established.
- **Confusable naming:** "Fundraising Readiness" (a score) and "Fundraising" (the cap-table engine) already
  share a name and are unrelated systems — a future Finance tab must not make this worse by introducing a
  third, similarly-named thing without a clearly distinct label.

## 31. Deferred scope (explicitly out of V2)

Full accounting/bookkeeping, tax modeling, payroll processing, enterprise FP&A, AI-generated long-range
forecasts, discount/MFN SAFE conversion math (until a verified formula exists), exotic financing structures
beyond SAFE/priced-round/simple-bridge, a target-percentage (post-money) option-pool solve, Build→Finance and
Finance→Analyze connections (§19/§20 — designed, not built), any new score.

---

## 32. Required product walkthroughs (Cases A-J)

Each case states what today's engine can ALREADY calculate (verified by reading the code, not assumed) and
what V2's addition specifically contributes.

**Case A — Idea-stage SAFE.** "$500K on a $5M post-money SAFE." **Today:** fully calculable right now via
`estimateStandaloneSafeOwnership()` — a $500K/$5M SAFE implies 10% ownership if converted today,
`isEstimateOnly: true`. Zero setup required beyond the wizard's own 3 steps. **V2 adds:** persistence (this
SAFE is remembered next session) and the ability to later model it actually converting into a real priced
round using the exact figure, not a re-typed one.

**Case B — Early-revenue runway.** Cash $500K, MRR $20K, expenses $70K/mo. **Today:** NOT calculable
anywhere as a persisted, revenue-aware figure — the existing `computeRunway()` only takes a flat burn number;
a founder would have to manually compute $70K − $20K = $50K burn themselves before entering it into the
Fundraising Simulator's own runway add-on. **V2 calculates:** burn = $50K/mo (derived, §10), runway = 10
months (`computeRunway`, extended by nothing — this one already works once burn is derived correctly).

**Case C — Hiring decision.** Two hires, +$30K/mo, starting in 3 months. **Today:** not calculable at all
(no hiring concept exists anywhere). **V2 calculates:** the monthly projection (§12) with the hire's
`start_date` offset by 3 months, showing runway unaffected for months 1-3 and shortened from month 4 onward
— the exact "what happens if the start date moves" case the directive names in §6.

**Case D — Raise size.** 18 months of runway desired after hiring. **Today:** not calculable (no raise-size
formula exists). **V2 calculates:** via §15's formula, using the post-hire projected burn.

**Case E — SAFE + priced round.** Multiple existing SAFEs, a new $3M priced Seed. **Today:** fully
calculable right now via `runSafeConversionAndPricedRound()` — this is the strongest existing capability in
the whole system. **V2 adds:** persistence of the existing SAFEs (today they must be re-typed from scratch
every session) and an EXACT (non-lossy) carry-forward of the resulting cap table for any future round,
replacing `chainScenario.ts`'s current display-rounding hand-off.

**Case F — Bridge.** **Today:** not modeled at all. **V2 models:** per §14, as a labeled SAFE
(`intendedAsBridge: true`) — the underlying conversion math is unchanged; only framing/labeling and
runway-timing context (e.g. "this bridge is intended to extend runway to your next raise") differ. Required
assumption: the founder still supplies a cap (or the bridge remains an un-converted estimate, same as any
other SAFE today).

**Case G — Revenue downside.** MRR falls 20%. **Today:** not modeled (no revenue-assumption mechanism
exists in the fundraising engine; `directConsequences.ts` only computes price×customers forward, never a
decline scenario, and isn't connected to runway at all). **V2 models:** as a `SCENARIO` (§18) revenue
assumption feeding the monthly projection — the UI must show "ASSUMPTION: MRR falls 20%" (§8 of the
directive), never imply SIE predicted the decline.

**Case H — Cost cut.** Reduce opex by $20K/mo. **Today:** not modeled. **V2 models:** an expense-category
edit in a named scenario, run through the same projection engine — mechanically identical to Case C, just a
negative line item instead of a positive one.

**Case I — Hiring timing.** Hire now vs. in 4 months. **Today:** not modeled. **V2 models:** two named
scenarios (§16/§17) differing only in one line item's `start_date`, compared via the generalized
`FundraisingScenarioCompare`.

**Case J — Financing-path comparison.** $1M SAFE now vs. $3M priced round, founder-entered terms. **Today:**
each side is individually calculable (the SAFE via `estimateStandaloneSafeOwnership()`, the round via
`runSimplePricedRound()`) but never shown side by side, and never with a shared runway consequence. **V2
shows:** both as named scenarios in the generalized comparison (§16/§17), explicitly NOT implying the two
options are economically equivalent when their assumptions differ (e.g. different assumed timing, different
implied valuation) — the comparison table states each scenario's own defining assumption alongside its
result, exactly as §17 requires.

---

## 33. Prioritization

The directive's own hypothesis, checked against this audit's findings — **broadly confirmed, with two
corrections** (marked below) reflecting what the code audit actually found.

**P0 — required for a coherent financial decision engine**
1. Financial state persistence (§10, §25) — genuinely the P0 foundation; nothing else works without it.
2. Burn + runway, calculated from state (§12) — mostly new work; the existing `computeRunway()` divide is
   reused but the burn INPUT side (revenue/expense breakdown) is new.
3. Monthly cash-flow projection (§12) — **new, not in the original hypothesis's wording, but required to
   make hiring-date/financing-date modeling honest** (directive §6's own explicit ask) — promoted to P0
   because Cases C/D/G/H/I above all depend on it.
4. Hiring impact (§13) — depends on #3.
5. Preserve/extend existing SAFE + priced-round engine (§14) — **correction: this is nearly DONE already**,
   lower net-new effort than the hypothesis implies; the P0 work here is persistence (§25), not new math.
6. Scenario comparison (§16/§17) — generalize the already-working `FundraisingScenarioCompare` pattern.

**P1 — high-value next capability**
7. Raise-size planning (§15).
8. Option-pool planning improvements (target-percentage post-money solve) — genuinely deferred-worthy;
   nobody has asked for it yet per this audit, and it requires a real circular solve, not a quick add.
9. Bridge modeling (§14) — **correction: cheaper than the hypothesis implies** once SAFEs are persisted, since
   it's a label plus timing framing, not new conversion math — could plausibly move to P0 if a real founder
   need surfaces, but staying P1 is the conservative, audit-driven call absent that signal.
10. Revenue/cost scenarios (§16, Cases G/H).
11. Financing-path comparison (§17, Case J).

**P2 — useful later**
12. Richer financial history (§23's "what was our burn 6 months ago" — the append-only
    `venture_financial_state` snapshot pattern already supports this once #1 exists; P2 reflects UI/query
    work, not data-model work).
13. Planned hiring roadmap (a dedicated view beyond individual line items).
14. Founder compensation modeling (a dedicated concept beyond a generic expense line, only if real usage
    shows the generic line item is insufficient).
15. Lightweight milestone-based capital planning.

**P3 — defer / out of scope**
16-20. Full accounting, tax, payroll, enterprise FP&A, AI-generated long-range forecasts — unchanged from
the hypothesis; this audit found no reason to reconsider any of these.

---

## 34. Phase 35B — Implemented architecture (financial state + runway engine V1)

**Status: Implemented and live-tested.** This section documents what actually shipped, as a diff against §4-§33's design above, exactly matching the discipline `SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md`'s own "Implementation Appendix" already established for Build.

### 34.1 Financial-state schema

One new table, `venture_financial_snapshots` — `id`, `venture_id` (FK → `modeled_ventures`, `ON DELETE CASCADE`), `user_id`, `as_of_date` (DATE, required), ten nullable `BIGINT` money columns (`cash_balance_cents`, `monthly_recurring_revenue_cents`, `monthly_non_recurring_revenue_cents`, `payroll_cents`, `contractors_cents`, `software_cents`, `marketing_cents`, `rent_cents`, `professional_services_cents`, `other_expenses_cents`), `recorded_at`. No `net_burn`/`runway` columns — both are always calculated (§35.6/§35.7), never stored, per the directive's own explicit instruction. This is the exact §25 design, unchanged (three tables were proposed there; only the first, `venture_financial_state`, was needed for this phase's scope — `venture_financial_line_items`/`venture_financial_scenarios` remain future work, §35.13).

### 34.2 Money representation

- **DB storage unit:** integer cents, `BIGINT`.
- **API representation:** integer cents, `int | None` on every Pydantic field (`app/models/venture_financials.py`) — the API speaks the exact same unit as the database, zero conversion at that boundary.
- **TypeScript representation:** plain `number` cents (`dashboard/types/finance.ts`) — a deliberate, documented departure from the fundraising engine's `bigint` convention (`dashboard/lib/finance/money.ts`'s own docstring explains why: Finance only adds/subtracts money, never multiplies/divides share counts, so plain-number precision is exact up to far more than any real company's cash balance, and avoids bigint's JSON-serialization awkwardness across a real network boundary the fundraising engine never crosses).
- **Calculation representation:** integer cents throughout (`app/ai/financial_engine.py`); the one division (cash ÷ burn, for runway months) uses `fractions.Fraction` for an exact intermediate result, rounded to one decimal only at the final output step — mirrors `dashboard/lib/fundraising/rational.ts`'s own "exact arithmetic, round only for display" rule.
- **Display formatting:** `dashboard/lib/finance/money.ts::formatWholeDollars()` — whole-dollar, comma-grouped ("$500,000"), matching `fundraisingUi/formatUi.ts`'s own existing convention.

### 34.3 History semantics

**Option A from §12 of the directive: append-only snapshots.** Every save is a `POST` that INSERTs a new row; there is no UPDATE path anywhere in `app/database/db.py` for this table. "Current state" is simply the most recent row by `(as_of_date DESC, recorded_at DESC)` — computed at read time, never a separately-maintained "current" pointer that could drift. Live-verified (§35.14): updating cash from $500,000 to $450,000 with a later `as_of_date` produced a second row; `GET /ventures/{id}/financials/history` returned both, the original completely unedited.

### 34.4 Unknown vs. zero semantics

Every money field is independently nullable. `NULL` means "unknown" and is never treated as zero anywhere in `financial_engine.py`: `_sum_or_none()` returns `None` (poisons the result) the instant any input to a sum is `None` — summing an unknown quantity with known ones is not itself knowable. An explicit `0` is a real, known value and sums normally. This is enforced identically whether the `0` came from a founder actively typing it or from the frontend form's own pre-filled default (§35.5) — the backend cannot tell the difference and doesn't need to, because by the time a value reaches the API it is already an explicit choice, not an assumption the backend made on the founder's behalf.

### 34.5 Editing UX and the zero-default decision

`Current cash` and `Recurring revenue` have **no pre-filled default** — blank until the founder types something, because these are the two numbers every founder should state consciously, even as an explicit `$0`. The **other eight fields** (other revenue, all seven expense categories) default to `"0"` **only when adding a venture's first-ever snapshot** — a founder who has no marketing spend, no rent, and no contractors shouldn't have to type `0` into three separate boxes to get a real burn number. Editing an *existing* snapshot always pre-fills the founder's own last-entered values, including a genuine blank for anything they previously left unknown — never re-applying the "first snapshot" zero-default over real prior data. This is the resolution to the directive's own tension between §15 ("unknown is not zero") and §16 ("do not require every category to be filled") — one is a backend invariant, the other is a frontend affordance, and neither compromises the other.

### 34.6 Burn formula

`net_burn_cents = total_monthly_expenses_cents − total_monthly_revenue_cents`, where each total is `_sum_or_none()` over its own fields (§35.4). Positive = burning cash, negative = generating cash, exactly `0` = break-even. `None` whenever revenue or expenses (or both) are unknown — never a partial sum that silently assumed a missing category was zero.

### 34.7 Runway formula

Only defined when `net_burn_cents > 0` **and** cash is known:

- `net_burn_cents < 0` → `status = "cash_flow_positive"`, `runway_months = None` (never a finite countdown for a profitable snapshot, per the directive's own explicit Case D/E requirement).
- `net_burn_cents == 0` → `status = "break_even"`, `runway_months = None`.
- `net_burn_cents > 0`, `cash_balance_cents == None` → `status = "burning"`, `runway_months = None` (cannot calculate without a cash figure — never guessed).
- `net_burn_cents > 0`, `cash_balance_cents <= 0` → `status = "out_of_cash"`, `runway_months = 0.0`.
- `net_burn_cents > 0`, `cash_balance_cents > 0` → `status = "burning"`, `runway_months = round(float(Fraction(cash, burn)), 1)`.

No status is ever named "infinite runway" — the founder-facing copy (`STATUS_COPY` in `FinanceOverview.tsx`) says "Cash-flow positive at the current snapshot" / "Break-even at the current snapshot" / "Out of cash at the current snapshot" instead, exactly per the directive's own preferred wording.

### 34.8 Cash-flow-positive behavior (§7/§8 worked example, live-verified)

Live-tested on MacroFlow (venture 4074, §35.14): revenue $80,000, expenses $70,000 → `net_burn_cents = -$10,000`, `status = "cash_flow_positive"`, headline "Runway" cell renders `—` with the caption "Cash-flow positive at the current snapshot," and the Cash Outlook table shows cash rising $10,000/month for 12 visible months with "Continues growing steadily beyond month 12 at this rate" — never a negative number, never an "infinite" claim.

### 34.9 Monthly projection methodology

`project_monthly_cash_flow(snapshot, as_of_date, horizon_months=24)` — holds the current snapshot's total revenue and total expenses flat for every projected month (no growth, no seasonality, no AI estimate of anything), computing `starting_cash → net_cash_change → ending_cash` month by month with pure stdlib calendar-month arithmetic (no `dateutil` dependency; `_add_months()` clamps day-of-month for shorter target months exactly as every calendar library does). Returns `[]` (never a guessed value) when cash, revenue, or expenses are unknown. **Termination rule, exactly as required (§9 of the directive):** stops early, with the terminal month flagged `depleted: true` and cash floored at `$0` (never negative), the first month a burning company's cash would go to or below zero; otherwise runs the full `horizon_months` and stops — bounded specifically so a profitable company never gets a meaningless endless table. `DEFAULT_PROJECTION_HORIZON_MONTHS = 24`, chosen as a reasonable 2-year planning window per the directive's own instruction to pick "a reasonable maximum horizon." Architected, per the directive's own instruction, so a future phase can extend it with dated line items (a hire starting mid-projection, a financing event) without changing this function's signature or return shape — today's call simply has no such items to apply yet.

### 34.10 Canonical-state doctrine

**FINANCE STATE (`venture_financial_snapshots`) is now the canonical actual snapshot for a venture's cash/revenue/expenses.** Nothing else in the codebase reads or writes this table. `VentureAssumptions.capital.{starting_capital,monthly_burn}` remains exactly what it already was — a hidden, coarse input to the VPS-scoring text assembly (`vps_guidance.py`) — untouched, not migrated, not deprecated in this phase (deprecating it is a future decision once real usage shows the richer Finance state should replace it there too, out of scope for 35B's "boring foundation" mandate).

### 34.11 Fundraising boundary — documented, not integrated

**Confirmed, exactly as predicted in §4 of this document:** `dashboard/lib/fundraising/runway.ts::computeRunway()` is a single flat `cash ÷ burn` division scoped to one Fundraising Simulator scenario, with both inputs re-typed by the founder into that scenario's own ephemeral form — it does not read `venture_financial_snapshots`, and this phase did not wire it to. **The two systems can, in principle, disagree today** (a founder could type different cash/burn numbers into the Fundraising Simulator's runway add-on than what's saved in Finance) — this is a known, accepted, temporary state, not a bug: forcing integration now risked exactly the regression the directive explicitly forbade (§18/§19: "we must not break Fundraising to satisfy Finance"). **The established direction, not yet built:** a future phase should have the Fundraising Simulator's own runway add-on default its `cash on hand`/`monthly burn` fields from the latest `venture_financial_snapshots` row when one exists (founder-editable, never silently overridden) — a `GET`-time pre-fill, not a schema merge, so the two systems' math never actually shares code, only an optional starting value. **Finance is the canonical system for actual company financial state going forward**; Fundraising Simulator remains the canonical system for hypothetical financing-scenario math — this boundary is permanent, not a placeholder.

### 34.12 Authorization model

Identical to every other Build endpoint: `_require_owned_venture()` (an ownership-scoped `SELECT`, no separate check) gates all three endpoints, and every SQL statement itself re-scopes via `JOIN modeled_ventures v ON v.id = vfs.venture_id WHERE v.user_id = :user_id` — never a "fetch, check in Python, then mutate" pattern. No stage/verification/graduation/evidence-quantity/SPS gate anywhere (§2 of the directive) — live-verified implicitly by every walkthrough step running against an Idea-stage venture with no graduation, no verification, no fundraising-readiness score computed.

### 34.13 Limitations (honest, not exhaustive)

- No hiring, scenario, or fundraising-persistence concepts exist yet — by design, this phase's own explicit scope guard.
- The projection assumes the current snapshot's revenue/expenses forever; it cannot yet represent a dated future change (a planned hire, a cost cut) — that is `venture_financial_line_items`, future work (§25).
- Fundraising Simulator and Finance can show different runway numbers for the same venture until the pre-fill connection in §35.11 is built.
- No dedicated Finance History UI exists — the data is fully queryable (`GET .../financials/history`) and tested, but nothing renders it yet (explicitly deferred, §13 of the directive).
- `VentureAssumptions.capital` remains a second, much thinner, disconnected financial input on the same venture — not reconciled with the new table in this phase.

### 34.14 Live walkthrough (MacroFlow, venture 4074)

1. **Empty state:** "Add your current cash, revenue, and monthly spending to calculate burn and runway." + "Add financial snapshot" — no fake `$0` metrics.
2. **Added:** cash $500,000; MRR $20,000; payroll $40,000, software $5,000, marketing $10,000, other $15,000 (contractors/rent/professional services left at their first-snapshot `$0` default).
3. **Confirmed:** Revenue $20,000, Spend $70,000, Net burn $50,000/mo, Runway **10 months** — exact match to the directive's own worked example.
4. **Reloaded:** identical values returned (same snapshot, same deterministic computation).
5. **Updated cash to $450,000** with a later `as_of_date` (Oct 1 vs. Sep 7): new current state showed Runway **9 months**; `GET .../financials/history` confirmed BOTH rows present, the original $500,000 row completely unedited.
6. **Changed revenue to $80,000** (expenses still $70,000): `status = "cash_flow_positive"`, Runway rendered `—` with "Cash-flow positive at the current snapshot," Cash Outlook showed cash rising $10,000/month with no negative or "infinite" display.
7. **Opened Fundraising:** rendered exactly as before this phase — chooser step, all five path options, disclaimer — zero regression.

### 34.15 Next implementation phase

A **35C** phase scoped to `venture_financial_line_items` (§25) — planned hires and financing events as dated projection inputs — is the natural next step, following the same "one new table, reuse the existing pure calculation layer" pattern this phase established. The Fundraising Simulator pre-fill connection (§35.11) is a small, low-risk candidate to bundle into that same phase or run standalone first.

## 35. Architectural requirements (carried into any future implementation phase)

Deterministic math; pure functions where possible (extending, not replacing, `rational.ts`/`safe.ts`/
`pricedRound.ts`/`runway.ts`); explicit assumptions, always labeled as such in the UI; no hidden AI
calculations anywhere in the financial math; scenarios kept structurally separate from canonical actuals
(§18); persisted financial state AND persisted scenarios (§25); reload survival; history (§23); testability
(§29, mirroring existing conventions); ownership/authorization scoped by `venture_id` exactly like every
existing Build table; venture-continuous access (§21) with no verification gate and no stage gate (§15/§16
of the directive); no new score anywhere.
