# Finance / Fundraising V2 — Product Direction Proposal

**Status:** Proposal only (Phase 34F, Section 9). Nothing in this document is implemented. No math, no UI,
no new endpoint was built this phase. This exists so the next phase can be scoped deliberately.

## 1. The governing rule

> **SIE MAY MODEL DEFENSIBLE ARITHMETIC. SIE MUST NOT PRESENT SPECULATIVE CAUSAL OUTCOMES AS
> CALCULATIONS.**

Every capability below is scoped to pass this test before it is proposed: *"If you raise $2M at a $10M
pre-money valuation, here is the resulting ownership"* and *"If monthly burn rises from $50K to $80K,
runway changes from X months to Y months"* are calculations — deterministic arithmetic over numbers the
founder supplied. *"If you hire a cofounder, your probability of success increases by 20%"* is not, and
nothing below proposes anything shaped like it.

## 2. What already exists (audited, not proposed)

`dashboard/lib/fundraising/` already implements real, tested, defensible arithmetic:

- `safe.ts` — SAFE conversion, single and multiple SAFEs converting together.
- `pricedRound.ts` — a full priced round including option-pool increase (pre-money vs. post-money
  option-pool effects are already modeled — `applyOptionPoolIncrease`), SAFE→priced-round conversion, and
  dilution rows.
- `capTable.ts` — ownership breakdown/percentages, with an asserted invariant (shares always sum correctly)
  so the math cannot silently drift.
- `runway.ts` — cash ÷ monthly burn, with an explicit `isInfinite` case (zero burn) rather than a
  divide-by-zero or fabricated number.
- `FundraisingScenarioCompare.tsx` — already compares two financing-structure results side by side
  (capital raised, founder ownership/dilution, final runway).
- `PathChooser.tsx` — already offers "Raise my first money," "Issue a SAFE," "Model multiple SAFEs," "Raise
  a priced round," "Model SAFE → Seed."

This is a genuinely strong foundation — most of the directive's own checklist (first SAFE, multiple SAFEs,
SAFE→priced conversion, priced round, ownership/dilution, option pool) is **already built**, not proposed
here again.

## 3. What is missing (the actual gap this proposal addresses)

- **Bridge financing** — no model for a bridge note/extension between rounds.
- **Hiring impact on runway** — `computeRunway()` takes a single flat `monthlyBurnCents`; there is no way
  to add a prospective hire's fully-loaded cost and see the resulting runway change.
- **Revenue impact on runway** — no net-burn calculation (burn − revenue); `runway.ts`'s own docstring is
  explicit that it "never predicts future burn," which is correct restraint, but it also has no mechanism
  today to accept a *current, known* revenue figure and net it against burn.
- **Raise-size planning for 12/18/24 months** — the inverse of runway (given a target runway length and
  current/projected burn, what raise size achieves it) does not exist; today a founder can only check the
  runway *implied by* a number they already chose, not work backward from a target.
- **A unifying "financial decision" framing** — the existing tools are five capable but separate
  calculators (SAFE, priced round, cap table, runway, one scenario-compare), not yet organized around the
  founder decisions they serve.

## 4. Proposed conceptual organization

Reusing the directive's own five groupings, mapped onto what exists vs. what's new:

| Group | Existing | New this proposal |
|---|---|---|
| **Plan Your Raise** | — | Raise-size planning (target runway → suggested raise), bridge financing |
| **Model the Deal** | SAFE, multiple SAFEs, SAFE→priced, priced round | — |
| **Understand Ownership** | Cap table, dilution, option pool | — |
| **Understand Runway** | Cash/burn ÷ runway | Hiring impact, revenue impact (net burn) |
| **Compare Options** | Two-financing-structure compare | Extend to compare *runway/hiring* scenarios too, not only financing structures |

## 5. Prioritized order for a future implementation phase

1. **Hiring impact on runway.** Smallest addition (one more input to an existing, working calculation:
   `monthlyBurnCents + newHireMonthlyCostCents`), immediately useful, and the clearest "improves a real
   founder decision" case (should I make this hire now or wait?) per the Product Capability Rule.
2. **Revenue impact on runway (net burn).** Equally small arithmetic (`monthlyBurnCents − monthlyRevenueCents`,
   floored at a reasonable minimum so burn never goes negative in a way that implies infinite runway from a
   single good month) — directly improves spend/raise timing decisions.
3. **Raise-size planning (12/18/24 months).** Inverse of the now-extended runway calculation
   (`targetMonths × netMonthlyBurnCents`, presented for the three standard horizons at once) — this is the
   single most-requested-shape founder question ("how much should I even raise?") and is now cheap once
   #1/#2 exist.
4. **Bridge financing.** A genuinely new instrument (likely modeled as a SAFE variant with a shorter
   expected timeline and often a maturity/interest framing, or as its own small module reusing
   `safe.ts`'s conversion mechanics where the terms allow) — more design work than #1-3, hence lower in the
   order despite being explicitly requested.
5. **Extend Compare Options** to let a founder compare two *runway* scenarios (e.g., "hire now" vs. "wait 6
   months") side by side, the same way `FundraisingScenarioCompare.tsx` already compares two financing
   structures — natural once #1/#2 exist, and directly serves the Product Capability Rule (a comparison
   only justified because it improves a real spend/hire/raise decision, not because "more calculators" is
   inherently better).

## 6. Additional financial-modeling blind spots identified (not yet prioritized)

- **Multiple hires modeled together** (a hiring plan, not just one hypothetical hire) — a natural extension
  of #1 above, deferred since #1 alone already answers the single-decision case.
- **Seasonal or ramping revenue** (vs. this proposal's flat monthly figure) — real, but adds real complexity
  for a benefit that's speculative until #2 (flat revenue netting) is proven useful in practice.
- **Convertible debt** (distinct from a SAFE — carries actual interest and a maturity date with real legal
  consequences) — a different instrument from bridge financing's likely SAFE-shaped treatment; flagged as
  its own future question, not folded into #4.
- **Tax/1099 or payroll-burden nuance on hiring cost** — real cost drivers a "fully-loaded cost" figure in
  #1 would need to account for; proposed as an input the founder supplies directly (a number they already
  know or estimate) rather than something SIE calculates on their behalf, to avoid fabricating precision SIE
  has no basis for.

## 7. Explicit non-goals (per the governing rule)

None of the following should ever be built as part of this direction, because none of them are defensible
arithmetic:

- A "probability of successfully raising" prediction.
- A "recommended valuation" number presented as fact rather than a founder-supplied input to a calculation.
- Any causal link from an operating decision (hiring, pricing, marketing spend) to a success/failure
  likelihood.
- A single combined "financial health score" — this would be a new score, explicitly prohibited this phase
  and inconsistent with the doctrine's own "no new score" rule generally.
