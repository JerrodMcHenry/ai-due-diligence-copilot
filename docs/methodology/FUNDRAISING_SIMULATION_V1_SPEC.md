# Fundraising Simulation V1 — Specification & Math Validation (Phase 21A)

Status: this document specifies a **deterministic, LLM-free, database-independent
cap-table math engine** built and validated in Phase 21A. It is **not yet wired
into any founder-facing UI**. Nothing described here changes VPS, SPS, Founder
Actions, Founder Progress, Build V3, Learn, or Simulate V1 — this engine is
new and additive, isolated to `dashboard/lib/fundraising/`.

**Product boundary (read this first):** every result this engine produces is
**a scenario model based on the assumptions the caller provides** — not a
prediction, not legal advice, not tax advice, not investment advice, and not
a substitute for actual financing documents. Real-world financing outcomes
depend on the specific legal documents signed, negotiated definitions,
jurisdiction, existing capitalization details this engine does not model, and
professional (legal/tax) advice. See "Limitations" below.

## 1. Why this exists

A future Fundraising Simulator needs founders to be able to model "if I raise
a SAFE at this cap, then a priced round at that valuation, what do I and my
investors end up owning?" Ownership and dilution math is exactly the kind of
calculation where a wrong answer is worse than no answer — an approximate
percentage that *looks* plausible can mislead a founder into a bad financing
decision. Phase 21A's mandate was to validate the math **before** building
any UI on top of it.

## 2. Existing architecture investigated (Part 2)

A direct repository search (`grep` across `app/` and `dashboard/` for SAFE,
valuation cap, option pool, dilution, cap table, pre-money, post-money, priced
round) turned up **zero existing fundraising/cap-table calculation logic**
anywhere in the product, confirmed by three independent checks:

- **Backend (`app/`):** the only match was an unrelated calibration-fixture
  string describing a company's product ("cap table/equity management
  platform for startups and investors") inside
  `app/calibration/sps_v3/calibration_evidence.py` — not code.
- **`app/ai/fundraising_readiness.py`** (Phase 8) is a distinct, unrelated
  feature: a deterministic "how prepared/defensible is this evidence" score
  computed from existing SPS pillar scores, confidence, and evidence
  coverage. Its own docstring explicitly states it does not compute cap
  tables or valuations. The dashboard route
  `app/founder/startups/[startupId]/fundraising` (confirmed present during
  this phase's build check) renders `FundraisingReadinessView`, i.e. this
  same Phase 8 feature — not cap-table math. Zero overlap with this spec.
- **Frontend (`dashboard/`):** the only matches were
  `dashboard/content/playbooks/data.ts`'s educational "cap-table" Playbook
  (which explicitly says "the numbers below are simple illustrative
  examples, not a real cap table") and its resource-map entry and test —
  purely educational content, zero calculation logic. A comment in
  `dashboard/content/concepts/data.ts` (Learn V1) already anticipated "a
  future SAFE/valuation/dilution concept" as a later addition — nothing
  built yet.

Conclusion: this phase builds new, isolated architecture. Nothing is
duplicated, and nothing existing needed to change.

## 3. Sources researched (Part 3)

The primary, authoritative source for this specification is Y Combinator's
own **Post-Money SAFE User Guide, version 1.2 (February 2023)** — fetched and
read in full from https://www.ycombinator.com/documents /
https://www.ycombinator.com/safe during this phase. YC created the post-money
SAFE in 2018 specifically to make SAFE ownership independently determinable
(see §5 below on why pre-money SAFEs are excluded), and its templates remain,
as of a 2026 web search performed during this phase, the current market
standard: "If you're raising a SAFE round in 2026, this is almost certainly
the version you're signing... it's what most lawyers and platforms default
to now." Per that same search, Carta data for 2024 shows SAFEs made up ~86%
of pre-seed and ~two-thirds of seed deals, with 61% of 2024 SAFEs using a cap
only, 30% cap+discount (a combined structure YC's own current templates no
longer offer as a single document — see §5), 8% discount-only, 1% neither.

The User Guide's own worked examples (Quick Start Guide simple dilution
example; Appendix II, Example 1's multi-SAFE + Series A + option-pool
scenario) are used directly as this engine's external cross-check and two of
its three golden cases (§10).

Standard priced-round mechanics (pre-money + new money = post-money; new
investor % = new money / post-money) are textbook/market-standard and are
additionally the directive's own worked example, used as golden case #1.

MFN SAFE mechanics were researched only at the level of YC's own Appendix I
description (an amendment-triggering mechanism, not a direct conversion
formula) — sufficient for V1's scope decision to document but not implement
MFN conversion (§5).

## 4. V1 supported instruments

1. **Post-money SAFE, valuation cap only** — the current YC "Standard"
   template and, per the research above, the dominant real-world SAFE
   structure. Fully implemented and validated (§8, §10).
2. **Multiple simultaneous post-money SAFEs**, potentially with different
   caps — implemented and validated against YC's own worked example.
3. **Priced equity round** — pre-money valuation + new money, standard
   dilution mechanics. Implemented and validated.
4. **Option pool / option-pool expansion**, specified as an **absolute new
   share count** added as part of a priced round. Implemented and
   validated, including who bears the dilution (§9).
5. **SAFE conversion into a priced round**, single transaction: SAFEs
   convert via the Company Capitalization method, new round shares are
   issued, option pool expansion (if any) is applied — all in one traceable
   result. Implemented and validated.
6. **Sequential rounds** (SAFE → Seed → Series A, etc.) — a round's own
   output cap table is valid input to the next round; no special-casing
   required. Validated (fixture J).
7. **Runway** (cash ÷ monthly burn) — deliberately separate from ownership
   math (§10, fixture K).

## 5. Explicitly unsupported (never silently approximated)

- **Pre-money (legacy, pre-2018) SAFEs.** YC's own User Guide (Example 2)
  demonstrates that a pre-money SAFE's dilution is **not independently
  determinable** without also knowing the eventual option-pool increase
  *and* the total amount raised on other convertible securities at
  conversion — i.e. it is inherently non-deterministic in isolation. This
  is exactly why YC created the post-money SAFE, and exactly why this V1
  engine (which requires determinism, §11) excludes it rather than
  approximating it.
- **Discount-only and MFN-only SAFEs, at conversion time.** These are
  recognized *input shapes* (`SafeInput.discountPercent`,
  `valuationCapCents: null`) so the type system doesn't pretend they don't
  exist, but `computeSafeConversion()` explicitly rejects them with a
  `FinancingError` rather than inventing conversion math not verified
  against a primary-source worked example this phase. Also note: YC's
  *current* templates (per Appendix I of the User Guide) offer Cap-only,
  Discount-only, or MFN-only as **separate documents** — the combined
  Cap+Discount template was removed in YC's own v1.1 (2021), even though
  30% of 2024 Carta SAFEs reportedly still combine cap and discount via
  other providers' documents. Combined cap+discount is therefore also
  unsupported in V1.
- Convertible notes, debt instruments, warrants.
- Tranched financings, secondaries, complex/participating liquidation
  preferences, pay-to-play, recapitalizations, anti-dilution provisions.
- Tax/QSBS treatment, and any legal interpretation of financing documents.
- **Option pool sized as a "target % of post-money cap table."** This is a
  common real-world specification method, but computing it requires a
  simultaneous circular solve against price-per-share (both depend on each
  other). V1 only accepts the pool increase as an absolute share count,
  deferred to Phase 21B or later — see §16 and Limitations.
- **The "SAFE converts at the better of cap price or the round's own price"
  comparison**, beyond a documented defensive warning. See §8's discussion
  of `priceWarnings`.

## 6. Canonical input model (Part 6)

Typed, in-memory TypeScript only (`dashboard/lib/fundraising/types.ts`) — no
persistence, no database tables, no API routes added this phase.

```ts
type Cents = bigint;     // money, always integer cents
type Shares = bigint;    // share counts, always integer

interface StakeholderPosition { id, name, kind, shares }
interface CapTableState { label, stakeholders: StakeholderPosition[] }
interface SafeInput { id, holderName, investmentCents, valuationCapCents, discountPercent }
interface PricedRoundInput { id, name, preMoneyValuationCents, newMoneyCents, optionPoolIncreaseShares, newInvestorName }
interface RunwayInput { cashOnHandCents, monthlyBurnCents }
```

`CapTableState.stakeholders` is the single source of truth; total shares is
always *derived* as their sum, never tracked separately — this is what makes
the ownership invariant (§11) hold **by construction**, not by a post-hoc
tolerance check.

## 7. Numeric precision strategy (Part 17)

No external decimal/bignumber dependency was added — the codebase has an
established zero-dependency convention for pure `lib/*` modules
(`lib/simulate/*.ts`), and none of `dashboard/package.json`'s existing
dependencies provide exact decimal arithmetic. Instead,
`dashboard/lib/fundraising/rational.ts` implements a hand-rolled, native
**BigInt-based exact rational type**: `{ num: bigint, den: bigint }`, always
reduced to lowest terms, never a floating-point `number`.

Money is always integer cents; share counts are always integer shares;
ownership fractions and prices-per-share are always exact `Rational`s.
Floating point never touches a value used in cap-table math anywhere in this
engine.

Rounding happens in exactly two, explicit, documented places:

1. **Share issuance floors** (truncates toward zero) — `toFlooredShares()`.
   Verified to match YC's own worked-example numbers exactly (e.g.
   1,176,470.588... floors to 1,176,470, matching the User Guide).
2. **Percentage/decimal display strings round half-up** at a caller-chosen
   number of decimal places, applied **only** at final formatting — never
   to an intermediate value used in further calculation.

One compatibility note: this repository's `tsconfig.json` targets `ES2017`,
which does not support the `123n` BigInt literal syntax under `tsc`'s
type-checker (`TS2737`) even though the `esnext` lib provides the `BigInt`
type. Every literal in this module and its consumers uses the `BigInt(123)`
constructor call form instead — identical runtime semantics, no tsconfig
change required (a target bump was judged out of scope: it would affect the
whole Next.js build, not just this phase). Confirmed clean under `tsc
--noEmit` and `next build` (§14).

## 8. Priced-round math (Part 8)

```
postMoneyValuationCents = preMoneyValuationCents + newMoneyCents
pricePerShare = preMoneyValuationCents / (preRoundShares + optionPoolIncreaseShares)
newInvestorShares = floor(newMoneyCents / pricePerShare)
newInvestorOwnership = newInvestorShares / (preRoundShares + optionPoolIncreaseShares + newInvestorShares)
```

Algebraically, with no option pool increase, `newInvestorOwnership` reduces
exactly to `newMoneyCents / postMoneyValuationCents` — confirmed both
algebraically and by golden case #1 ($8M pre + $2M → $10M post, exactly 20%,
the directive's own worked example).

## 9. Dilution (Part 9)

Two distinct, never-conflated quantities, both computed by
`computeDilution()`:

- **Percentage-point change**: `after% − before%` (e.g. 25% → 20% is "5
  percentage points").
- **Percentage dilution**: `(before% − after%) / before%` (e.g. 25% → 20% is
  "20% dilution" — a fifth of the original stake is gone).

Fixture G shows: with **no** option pool increase, a plain new-money round
dilutes every pre-round holder (founders and any existing pool alike) at an
**identical percentage-dilution rate** — nobody bears extra dilution because
nothing about the pool changed.

## 10. SAFE math (Parts 10, 11) — "Company Capitalization" method

Formula, from YC's Post-Money SAFE User Guide, self-referential because
Company Capitalization must include the SAFEs' own as-converted shares:

```
For each SAFE:      capOwnership = investmentCents / valuationCapCents
totalSafeCapOwnership = sum(capOwnership across all outstanding SAFEs)
CompanyCapitalization = floor( PreSafeShares / (1 − totalSafeCapOwnership) )
Each SAFE's shares     = floor( CompanyCapitalization × its own capOwnership )
```

`computeSafeConversion()` implements exactly this and is used both
standalone (estimating "what would this SAFE be worth if it converted right
now," matching YC's own Quick Start Guide illustration — fixture D) and as
the first step of a SAFE-triggering priced round (fixture F).

**External cross-check (Part 22) / Golden Case #2** — YC's Post-Money SAFE
User Guide, Appendix II, Example 1: pre-safe cap table of 10,000,000 shares
(Founders 9,250,000 + Outstanding Options 300,000 + Promised Options 350,000
+ Unissued Pool 100,000), two SAFEs (Investor A $200K/$4M cap = 5% implied,
Investor B $800K/$8M cap = 10% implied).

| Quantity | YC's published result | This engine's result | Difference |
|---|---|---|---|
| Company Capitalization | 11,764,705 | 11,764,705 | 0 |
| Investor A shares | 588,235 | 588,235 | 0 |
| Investor B shares | 1,176,470 | 1,176,470 | 0 |

Exact match — no tuning was needed to reach this; the formula above was
implemented directly from the primary source and matched on the first run.
`fundraising.test.ts::test_E_external_cross_check_multiple_safes` asserts
against these externally-published numbers by name, not against the
engine's own formula reproduced in isolation.

**Documented limitation:** for a cap-only SAFE, if a triggering round prices
at or below the SAFE's own valuation cap, general SAFE-market convention
gives the investor the better of the cap price or the round's own price —
but the exact comparison formula for that case was not found in a
primary-source worked example during this phase's research (Appendix II's
example doesn't exercise it: the $15M Series A pre-money there is well above
both SAFE caps). Rather than invent an unverified formula, the engine
converts using the cap price as documented above and **flags** the edge case
via `priceWarnings` in `runSafeConversionAndPricedRound()`'s result — never
silently returns a share count that hasn't been independently verified. Any
production reliance on this specific edge case should be re-verified against
primary sources before shipping.

## 11. Multiple SAFEs, SAFE conversion at a priced round (Parts 11, 12)

Both directly validated by the external cross-check above (§10) and by
golden case #3 (§13, a from-scratch, fully clean fixture combining SAFE +
option pool + priced round in one traceable transaction).

## 12. Option pools (Part 13) — who bears the dilution

Two distinct mechanics, both implemented and both tested (fixture H):

- **Pre-existing option pool** (issued options, promised options, or an
  unissued pool that already existed before any SAFE was issued) is
  included in `PreSafeShares`, and therefore **is** included in Company
  Capitalization — SAFE holders are not diluted by pre-round option grants,
  matching YC's own Appendix II example (the 300,000 + 350,000 + 100,000
  pool-related rows are part of the 10,000,000 pre-safe base).
- **A NEW option-pool increase created as part of the triggering priced
  round** is added to the price-per-share denominator **after** Company
  Capitalization (and therefore each SAFE's share count) is already fixed.
  Fixture H proves this directly: running the identical SAFE through two
  otherwise-identical rounds — one with no pool increase, one with a
  1,111,111-share increase — produces **the exact same SAFE share count
  (1,111,111) in both cases**, while founders' final ownership percentage
  differs materially between the two scenarios. Founders (and other
  pre-existing non-SAFE holders) bear the new pool's dilution; the
  converting SAFE does not.

## 13. Golden cases (Part 21)

**Golden Case #1 — simple priced round** (fixture B, the directive's own
worked example): $8M pre-money + $2M new money → $10M post-money; price/share
$1.00; new investor 2,000,000 shares = exactly 20.00%; founders diluted from
100% to exactly 80.00% (20 percentage points, 20% dilution).

**Golden Case #2 — multi-SAFE conversion into a priced Series A** (fixtures
E+F): the YC Appendix II Example 1 pre-safe cap table and two SAFEs (§10),
converting via Company Capitalization to 588,235 / 1,176,470 shares exactly
matching YC's own published numbers, then a clean $1.00/share Series A layered
on top ($11,764,705 pre-money chosen so price/share lands exactly on $1.00) —
new lead investor gets exactly 3,000,000 shares; final fully diluted total
exactly 14,764,705 shares.

**Golden Case #3 — SAFE + option pool + priced round, zero flooring anywhere**
(fixture I, independently constructed with numbers chosen so every step is an
exact integer, demonstrating full end-to-end traceability with no rounding
ambiguity):

1. Founders 9,000,000 shares (100%).
2. SAFE: $1,000,000 / $10M cap → 10% implied. Company Capitalization =
   9,000,000 / 0.9 = **10,000,000 exactly**. SAFE shares = 10,000,000 × 10% =
   **1,000,000 exactly**.
3. Priced round: option pool increase 1,000,000 shares (absolute). Pre-money
   $22,000,000 ÷ (10,000,000 + 1,000,000) = **$2.00/share exactly**. New
   money $5,000,000 ÷ $2.00 = **2,500,000 shares exactly**.
4. Final cap table: 9,000,000 (founders) + 1,000,000 (SAFE) + 1,000,000
   (pool) + 2,500,000 (new investor) = **13,500,000 shares**, summing to
   exactly 100% by construction. Founders 2/3 (66.67% displayed), SAFE and
   pool each 7.41%, new investor 18.52%.

All three golden cases, plus the external cross-check, are asserted in
`dashboard/tests/fundraising.test.ts`.

## 14. Ownership invariant, traceability, error handling (Parts 18, 19, 23)

**Invariant:** because `totalShares()` is always the *sum* of stakeholder
shares (never a separately tracked field), every `CapTableState` this engine
produces sums to **exactly** 100% ownership — not "within tolerance," an
exact identity by construction.
`capTable.ts::assertOwnershipInvariant()` additionally checks this
explicitly (and checks for negative shares / empty cap tables), so a
hand-built or malformed fixture is caught rather than silently trusted —
verified by fixture M, including two deliberately-malformed inputs that must
throw.

**Traceability:** every engine function returns a rich result object
exposing every intermediate quantity (Company Capitalization, each SAFE's
own capOwnership/conversionShares/capPricePerShare, price-per-share,
pre/post-round share counts, per-stakeholder dilution rows) — never just a
final percentage.

**Error handling:** `errors.ts` + per-function guards reject, with a named
`FinancingError`, every nonsensical state the directive enumerates: negative
or zero investment/valuation, SAFEs summing to ≥100% implied ownership,
negative option-pool-increase shares, a cap table with zero/negative shares,
discount-only/MFN-only SAFEs at conversion, and out-of-range discounts.
Fixture L exercises each case explicitly — nothing is silently clamped or
normalized. Confirmed by `npx tsc --noEmit` (zero errors project-wide) and
`npm run lint` (zero warnings) after implementation.

## 15. Runway (Part 15)

`runway.ts::computeRunway()` is deliberately isolated from every
ownership/cap-table function above — it takes only cash-on-hand and monthly
burn, both required non-negative, and returns `cash / burn` as an exact
`Rational` number of months (fixture K: $500,000 ÷ $62,500/mo = exactly 8
months). Zero burn returns `isInfinite: true` rather than throwing (a
legitimate, if rare, state) rather than dividing by zero. Burn is always
treated as flat/constant — this module never predicts future burn.

## 16. Sequential rounds (Part 14)

No event framework was built. A round's `PricedRoundResult.postRoundState`
is simply valid input to the next round's `preRoundState` parameter — proven
by fixture J (Seed → Series A chained with no special-casing) and by golden
case #2 (SAFE conversion's resulting state directly feeds the next priced
round). This satisfies the directive's "architect for sequencing without
requiring a rewrite" without introducing a generalized state-machine.

## 17. Required Learn concepts for Phase 21B (Part 16)

Not implemented this phase (spec only, per the directive). A future Learn
module should cover, at minimum: SAFE, valuation cap, discount, pre-/
post-money valuation, dilution (percentage-point vs. percentage — see §9),
option pool, option-pool expansion, priced round, fully diluted ownership,
Company Capitalization (the SAFE-conversion mechanic specifically), and
pro-rata rights (conceptually only — not modeled by this engine). Candidate
reuse target: `dashboard/content/concepts/data.ts` already anticipates this
addition per its own existing comment (see §2).

## 18. Limitations

- Option pool increase must be supplied as an absolute share count, not a
  target post-financing percentage (§5) — deferred.
- The cap-vs-round-price "better of" comparison for a SAFE converting at or
  below its own cap is flagged, not resolved, pending further primary-source
  verification (§10).
- Pro-rata rights are not modeled as an executable mechanic (only
  conceptually documented, per the directive's own scope).
- Discount-only, MFN-only, and combined cap+discount SAFEs are recognized
  input shapes but rejected at conversion (§5).
- No persistence: this engine has no database tables and is not called from
  any API route or UI yet.

## 19. Phase 21B integration recommendation

The engine (`dashboard/lib/fundraising/*.ts`) is ready to be called from a
UI layer as-is: it is pure, synchronous, typed, and requires no backend
changes (no new API routes, no new database tables). A recommended
integration path is a client-side "Fundraising Simulator" page under
`dashboard/app/founder/...` that collects `CapTableState` +
`SafeInput[]`/`PricedRoundInput` from simple forms and renders the
`PricedRoundResult`/`SafePlusPricedRoundResult` objects' full intermediate
breakdown (never just a final percentage), paired with the Learn concepts in
§17 and the product-boundary disclaimer at the top of this document. Phase
21B should also resolve, or explicitly re-confirm as out of scope, the two
flagged limitations in §18 before any founder-facing launch.
