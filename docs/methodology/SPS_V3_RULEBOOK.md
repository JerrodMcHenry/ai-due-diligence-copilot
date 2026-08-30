# SPS V3 Rulebook

Phase 10.8E. **Design only — no production code, V2.1 behavior, or
historical score was touched to produce this document.** This document
treats `docs/methodology/SPS_METHODOLOGY_V3_DESIGN.md` (Phase 10.8D) as
a proposal to be stress-tested, not as settled fact — several 10.8D
proposals are revised or reversed below, with reasoning. See
`SPS_V3_CALIBRATION_PLAN.md` (companion document) for calibration
philosophy, dataset design, and synthetic stress tests.

**Non-negotiable rule governing every decision below:** a hardcoded
constant is not automatically more defensible than an LLM judgment.
Every threshold that lacks empirical justification is marked
**CALIBRATION REQUIRED** rather than presented as settled.

---

## Part 1 — Auditing 10.8D's Proposed Constants

| 10.8D rule | Classification | Reasoning |
|---|---|---|
| Overall coverage ≥35% for publishability | **ARBITRARY — reject the number, keep the concept** | 10.8D's own justification ("chosen so structural ceiling alone doesn't pass") was circular — the number was picked to produce a desired outcome, exactly what this phase's non-negotiable rule forbids. The *existence* of a coverage floor is sound; 35% specifically is unjustified. → **CALIBRATION REQUIRED.** |
| Pillar coverage ≥40% | **PLAUSIBLE BUT NEEDS CALIBRATION** | Reused from V2.1's existing Medium-confidence coverage threshold for continuity, but V2.1's own threshold was never independently calibrated either — borrowing an uncalibrated number doesn't make it calibrated. Concept (a pillar needs a coverage floor to publish) is sound. |
| ≥2 scorable dimensions per pillar | **JUSTIFIED NOW (concept); CALIBRATION REQUIRED (the number 2)** | The concept — one dimension must never stand in for a whole pillar — follows directly from Part 13's own worked concern and needs no further justification. Why 2 and not 3 is unjustified. |
| ≥4 of 6 publishable pillars for SPS | **PLAUSIBLE BUT NEEDS CALIBRATION** | Same pattern — concept sound (an SPS resting on 2 of 6 pillars is not a defensible average), exact count arbitrary. |
| Market + Team specifically mandatory | **REVISED — partially rejected** | On rechallenge, this introduces an *undiscussed* new risk 10.8D missed: a stealth-mode, privacy-conscious, or simply press-shy founding team could have a genuinely strong company but weak public Founder-Market-Fit evidence, and would now be structurally blocked from ever receiving an SPS regardless of how strong Market/Product/Execution are. Mandating specific named pillars risks becoming exactly the "evidence-abundance bias" this whole project is trying to fight, aimed at a different axis (press visibility of founders vs. press visibility of the company generally). **Revised recommendation:** replace "Market AND Team both required" with "at least 2 of {Market, Team, Product} required" — still enforces that SPS isn't computed from Execution/Traction/Financial-Health alone, without hard-coding that founders specifically must be publicly documented. |
| Confidence-not-Low as a hard publishability gate | **CONCEPTUALLY WRONG** | This directly contradicts 10.8D's own Part 12 philosophy ("report honestly rather than distort... a low-confidence 90 is not hidden, it is published with its label"). Using confidence as a hard block is a form of distortion-by-withholding, the exact thing Part 12 argued against for score capping. **Rejected outright** — see Part 22 below for the replacement (coverage-only gate + mandatory confidence labeling, no separate confidence gate). |
| 80+/85+/90+/95+ multi-pillar high-score gates | **REJECTED as largely redundant, real risk of creating a new artificial ceiling** | See Part 25 below — full reasoning. |
| <60/<50/<40/<20 negative-evidence-location gates (e.g. "<40 requires negative evidence specifically in Market/Team/Execution") | **CONCEPTUALLY WRONG** | Arbitrarily treats Financial-Health-only negative evidence (e.g. disclosed near-term insolvency) as incapable of independently justifying a low score — a real counterexample 10.8D didn't consider (severe cash constraint can be existential regardless of which pillar it's filed under). **Rejected** — see Part 26. |
| Pillar renormalization over scorable dimensions | **JUSTIFIED NOW** | Unchanged from V2.1, already proven not to violate Non-Negotiable Principle 6 (adding evidence can still pull an average down). No reason found to change it. |
| Overall SPS renormalization over scorable pillars | **JUSTIFIED NOW** | Same reasoning, one level up. |
| 1 Category C dimension (Strategic Execution) | **REVISED — decomposed successfully, moved to B** | See Part 34. |
| 3 Category D dimensions (Usability, Operational Execution, Burn Efficiency/Runway) | **RESOLVED** | See Part 35 — REDESIGN, SPLIT, and MERGE respectively, not left as open placeholders. |

---

## Part 2-3 — Dimension Inventory and Challenge (summary; full matrix in Part 36)

Every one of V2.1's 28 dimensions was run through the ten-question
challenge (real characteristic? independent? observable? distinguishable
from unknown? stage-relative? double-counts? weight defensible? keep/
redesign/split/merge/remove?). Results, by pillar, with only the
dimensions whose verdict changed from a simple "keep as Category B"
discussed in prose here — the full inventory (all 28 in, final ~26 out)
is Part 36's table.

**Market (5→5, all KEEP, Category B):** all five pass the independence
test (size, growth, timing, competitive intensity, and demand are
genuinely distinct questions) and none double-count each other once
each has its own required taxonomy fields (Part 9).

**Team (5→5, all KEEP, Category B):** Founder-Market Fit, Technical
Capability, Business Capability, Leadership, and Execution Track Record
remain independent — the challenge did surface real overlap risk
between Execution Track Record (Team) and the Execution pillar's own
dimensions (both ask "has this team shipped/delivered"), resolved in
Part 18's double-counting rule: Team's Execution Track Record asks
*whether the team, historically, across any venture*, has hit
milestones (a team-quality signal); the Execution pillar's dimensions
ask whether *this specific company* is executing well *now* — genuinely
different questions about potentially the same underlying facts, kept
distinct with an explicit rule preventing one fact set from mapping to
the same taxonomy outcome in both places.

**Product (5→4, one REDESIGN):** Customer Value, Differentiation,
Defensibility, and Adoption Potential KEEP as Category B. **Usability
is REDESIGNED** (renamed, evidence source changed) — see Part 35.

**Execution (4→3, one SPLIT + one moved B):** Go-to-Market Execution
and Product Execution KEEP as Category B. **Strategic Execution moves
from Category C to Category B** (Part 34). **Operational Execution is
SPLIT** — its quantitative half moves to Financial Health, its
qualitative half survives in Execution renamed "Operating Discipline"
(Part 35).

**Traction (5→5, full REDESIGN, concept-driven not just relabeled):**
Customer Growth/Revenue Growth/Retention/Growth Velocity/Engagement are
replaced by Current Scale/Growth Trajectory/Customer Adoption/Retention-
Engagement/Commercial Validation — same count, materially different
concepts (Part 13).

**Financial Health (4→3, two MERGED, one KEPT):** Revenue Quality KEEPS
(Category B). Unit Economics KEEPS (Category A, unchanged, still
fail-closed). **Burn Efficiency and Runway MERGE** into one Deterministic
"Capital Efficiency" dimension (Part 35), plus Operational Execution's
quantitative half arrives here as a new consideration folded into the
same Capital Efficiency evaluator rather than a separate dimension
(avoiding re-creating the double-counting Part 18 flags).

**Net dimension count: 28 → 26** (Product -1, Execution -1 net despite
a split, Financial Health -1 net despite an inbound half-dimension).
Full accounting in Part 36/37.

---

## Part 4 — Strongly Typed Canonical Evidence

10.8D's generic `CanonicalObservation` (a single shape with `value: Any`)
is rejected as exactly the "untyped dumping ground" this phase warns
against — `Any` makes invalid states easy to represent (nothing stops a
`RevenueObservation`-shaped claim from being missing a currency, or a
`FounderExperienceObservation` from having a numeric `value` that means
nothing). V3 instead defines one shared base and per-domain typed
subclasses.

### Shared base (all fields required unless marked optional)

```
EvidenceBase:
  source_excerpt: str                    # literal supporting text
  source_reference: str | None           # URL/title, optional only if
                                           # source_excerpt alone is
                                           # sufficient for provenance
  source_date: date | None                # when the SOURCE was published/
                                           # updated, not the fact's own date
  provenance_status: ACCEPTED | REJECTED_UNTRACEABLE | REJECTED_CONTRADICTED
  direct_or_derived: DIRECT | DERIVED
  derivation: str | None                  # REQUIRED if DERIVED, else must be None
  extraction_confidence: LOW | MEDIUM | HIGH   # LLM's own confidence in
                                                 # having read the source
                                                 # correctly -- distinct from
                                                 # Assessment Confidence
```

### Typed subclasses (illustrative set — not exhaustive; the pattern
generalizes to any new evidence type without touching the base)

**`RevenueObservation`**
- Required: `amount: Decimal`, `currency: Currency` (ISO 4217 enum, not
  free string), `metric_type: ARR | MRR | ANNUAL_REVENUE | QUARTERLY_REVENUE | BOOKINGS | GMV`, `as_of_date: date`.
- Optional: `growth_context: str | None` (free text only for the
  explanation trace, never consumed by scoring logic).
- Invalid states made unrepresentable: `metric_type` is a closed enum —
  there is no way to construct a `RevenueObservation` where "ARR" and
  "bookings" are ambiguous, because they are different enum values, not
  free strings that might collide (directly implements Part 5's "ARR vs
  bookings vs GMV must never be conflated" rule at the type level, not
  just a documentation convention).
- Multiple coexist: yes — one company may have many `RevenueObservation`s
  at different dates/metric_types; evaluators select the subset they
  need (e.g. Growth Trajectory needs two same-`metric_type` observations
  at different dates; Current Scale accepts any single one).
- Conflicts: two observations with the same `metric_type` and same
  `as_of_date` but different `amount` → `provenance_status` review
  required, surfaced as `UNAVAILABLE_CONFLICTING_EVIDENCE` for any
  evaluator that would otherwise consume both.

**`CustomerCountObservation`**
- Required: `count: int`, `customer_type: PAYING | PILOT | SIGNED_CONTRACT_UNPAID | FREEMIUM_ACTIVE`, `as_of_date: date`.
- `customer_type` is the type-level enforcement of Part 5's "pilot vs.
  paying customer" and "signed contract vs. customer" rules — an
  evaluator for Commercial Validation may accept `SIGNED_CONTRACT_UNPAID`
  where an evaluator for Current Scale requires `PAYING`, and the schema
  makes it impossible to silently blend the two.

**`RetentionObservation`**
- Required: one of `nrr_pct: Decimal`, `grr_pct: Decimal`,
  `logo_churn_pct: Decimal` (at least one; a bare "retention is good" with
  no figure of any kind is not representable as this type at all — it
  would instead be a qualitative signal feeding a Category B taxonomy
  field, never this type).
- Optional: `period: MONTHLY | ANNUAL`.

**`FundingObservation`**
- Required: `amount: Decimal`, `currency: Currency`, `round_label: PRE_SEED | SEED | SERIES_A | SERIES_B | SERIES_C_PLUS | GROWTH_PE | IPO | UNDISCLOSED`, `announced_date: date`.
- Explicitly does NOT have a `revenue_equivalent` or any field that could
  let an evaluator treat funding as revenue — Part 5's "never treat
  funding as financial health automatically" is enforced by simply never
  giving `FundingObservation` a code path into the Revenue Quality or
  Capital Efficiency evaluators except as the denominator input to a
  runway-style calculation (cash raised, not revenue).

**`CashObservation`** / **`BurnObservation`**
- `CashObservation`: `amount`, `currency`, `as_of_date`.
- `BurnObservation`: `amount`, `currency`, `period: MONTHLY | ANNUAL`,
  `as_of_date`.
- Kept as two separate types (not one "financial figure" blob) because
  Capital Efficiency's evaluator (Part 14) needs both independently and
  must never accept one standing in for the other.

**`MarketSizeObservation`** / **`MarketGrowthObservation`**
- `MarketSizeObservation`: `amount`, `currency`, `market_label: str`
  (the named segment, e.g. "US SMB payroll software"), `estimate_source_type: THIRD_PARTY_RESEARCH | COMPANY_STATED | ANALYST_ESTIMATE`.
- `estimate_source_type` matters for Provenance Grades (Part 6) — a
  `COMPANY_STATED` market-size claim is weighted differently than a
  `THIRD_PARTY_RESEARCH` one, without needing a second confidence field
  bolted on.

**`FounderExperienceObservation`**
- Required: `founder_role: str`, `experience_type: DIRECT_DOMAIN | ADJACENT_DOMAIN | UNRELATED_DOMAIN | REPEAT_FOUNDER | PRIOR_EXIT`, `prior_entity_name: str | None` (required when `experience_type` implies a specific prior company, e.g. `REPEAT_FOUNDER`).
- `prior_entity_name` being a named, checkable fact (not just a category
  label) is what makes this type resistant to the exact SpaceX-defect
  pattern — an evaluator can require `prior_entity_name` to be populated
  before crediting `REPEAT_FOUNDER`, closing the gap where a free-form
  judgment could wrongly decide "not enough" despite a named fact sitting
  in the source text.

**`FounderOutcomeObservation`** — separate from `FounderExperienceObservation`
because "founder worked at X" and "founder's prior company had outcome Y"
are different facts (Part 5's "valuation vs. revenue" discipline applied
to founder history): `outcome_type: ACQUIRED | IPO | SHUT_DOWN | STILL_OPERATING | UNKNOWN`, `prior_entity_name: str`.

**`ProductCapabilityObservation`**, **`CustomerEvidenceObservation`**,
**`CompetitiveEvidenceObservation`**, **`PartnershipObservation`**,
**`CommercialContractObservation`** — same design discipline applied
(closed enums for the ambiguity-prone fields, named entities required
where the claim implies one, explicit `as_of_date`); full field lists
omitted here for length but follow the exact pattern demonstrated above,
to be finalized during implementation, not invented here as filler.

**Common invalid-state prevention pattern across every type:** no
observation type has a bare `metric: str` + `value: Any` shape anywhere
— every ambiguity-prone axis (metric type, customer type, round label,
experience type, outcome type) is a closed enum, not a string, so a
malformed or ambiguous extraction fails typed validation immediately
rather than silently entering the canonical layer as an untyped blob an
evaluator might misinterpret.

---

## Part 5 — Evidence Normalization

Deterministic, pre-scoring normalization rules, applied at the
provenance-verification step before an observation is accepted:

| Raw form | Normalized to |
|---|---|
| "$10M", "$10 million", "10,000,000 USD" | `amount=10000000, currency=USD` — a fixed currency-parsing table (symbols, "million"/"M"/"billion"/"B" suffixes, ISO codes), never an LLM-estimated number |
| "2025 ARR" | `metric_type=ARR, as_of_date=2025-12-31` (or the specific stated date if narrower) — never conflated with "monthly revenue" or "annualized run rate," which are different `metric_type` enum values entirely, not synonyms |
| "annualized run rate" | `metric_type=ARR` **only if** the source explicitly frames it as an annualized figure; otherwise rejected as ambiguous rather than guessed |
| "customers" vs. "users" | Distinct fields (`CustomerCountObservation.customer_type` vs. a separate `UserCountObservation`) — never merged, since a free user and a paying customer are different facts for Traction's Customer Adoption dimension |
| "bookings" vs. "revenue" | Distinct `metric_type` enum values on `RevenueObservation` — an evaluator requiring revenue must not silently accept bookings |
| "GMV" vs. "revenue" | Distinct `metric_type` — GMV normalizes to its own value, never coerced into a revenue-shaped field, since a marketplace's GMV materially overstates its actual revenue |
| "funding" vs. "cash" | Distinct observation types (`FundingObservation` vs. `CashObservation`) — a $50M raise eighteen months ago is not current cash on hand, and no evaluator may treat them as interchangeable |
| "valuation" vs. "revenue" | No shared type at all — valuation is not currently modeled as a scoring input anywhere in V3 (it is marketing/context only, consistent with Non-Negotiable Principle 4: a company should not score higher merely because investors valued it highly, which is closer to reputation than to demonstrated evidence) |
| "signed contract" vs. "paying customer" | Distinct `customer_type` enum values, with Commercial Validation (Part 13) explicitly allowed to credit `SIGNED_CONTRACT_UNPAID` differently (typically lower) than `PAYING` |
| "pilot" vs. "paying customer" | Same mechanism — `PILOT` is its own enum value, never silently promoted to `PAYING` |
| "estimated" vs. "company-reported" figures | Captured by `estimate_source_type` (Market types) or `direct_or_derived` (all types) — an evaluator may weight `COMPANY_STATED`/`DIRECT` more heavily than a third-party estimate, or less heavily, per its own versioned rule, but the distinction is never lost by normalization |

**General principle enforced by the type system (Part 4), not just this
table:** normalization can only map surface-form variation (currency
symbols, date formats, unit suffixes) onto an already-existing typed
field — it can never bridge two *semantically different* concepts (ARR
vs. bookings, funding vs. cash, valuation vs. revenue). Any extraction
that would require such a bridge is rejected at the typed-parsing step,
not silently resolved by an LLM's best guess.

---

## Part 6 — Provenance Grades

```
PRIMARY_VERIFIED        -- a filing, contract, or dataset directly
                            reviewed (rare for public-only analyses;
                            the primary path once founder-provided
                            data/data-rooms exist, Phase 10.8D Part 23)
PRIMARY_SELF_REPORTED    -- the company's own website/press release/
                            blog states the fact directly
HIGH_QUALITY_SECONDARY   -- a specific, named third-party source
                            (a named research firm's report, a named
                            journalist's reporting with specifics)
                            states the fact
SECONDARY_ESTIMATE       -- a third-party estimate without primary
                            sourcing (e.g. an aggregator's guessed
                            valuation/revenue figure)
DERIVED                  -- computed from two or more ACCEPTED
                            observations, never from raw source text
                            directly
UNVERIFIED               -- extracted but not yet checked, or checked
                            and found untraceable -- never reaches the
                            canonical layer (REJECTED_UNTRACEABLE)
```

**What each grade may support:**

| Grade | Supports scoring | Supports classification | Context only |
|---|---|---|---|
| PRIMARY_VERIFIED | Yes | Yes | — |
| PRIMARY_SELF_REPORTED | Yes | Yes | — |
| HIGH_QUALITY_SECONDARY | Yes | Yes | — |
| SECONDARY_ESTIMATE | No (never alone) | Yes, with `extraction_confidence` capped at MEDIUM | — |
| DERIVED | Yes, only if every input observation is itself scoring-eligible | Yes | — |
| UNVERIFIED | No | No | Never reaches canonical layer |

**Conflicting sources rule:** when two ACCEPTED observations of the same
field materially disagree, the HIGHER provenance grade is used for
scoring **only if** the grades genuinely differ (`PRIMARY_SELF_REPORTED`
over `SECONDARY_ESTIMATE`); if grades are equal, the field becomes
`UNAVAILABLE_CONFLICTING_EVIDENCE` rather than picking one arbitrarily or
averaging them (averaging two disagreeing numbers invents a third number
neither source stated — exactly the fabrication pattern this whole
redesign exists to prevent).

**Explicit anti-bias rule, directly answering this Part's own
instruction:** provenance grade is a property of the *source*, not of
how many sources exist. A famous company having ten `SECONDARY_ESTIMATE`
articles repeating the same unverified number does not upgrade that
number's grade — ten weak sources remain weak, they do not average into
one strong one. This is the specific, concrete mechanism preventing
evidence-abundance bias from leaking into provenance (as opposed to
Part 20's separate mechanism preventing it from leaking into Coverage).

---

## Part 6A — 10.8G Amendment: Substantive Signal Identity, Deduplication, Corroboration, and Conflict Resolution

**Added in Phase 10.8G**, in direct response to a structural defect
10.8F's harness discovered: the generic Category B classification
pattern described in Part 16 counted raw `CanonicalObservation`
objects, not distinct underlying facts, allowing 100 duplicate sources
of the identical fact to inflate a dimension's score from 5.5 to 9.5,
and allowing 15 low-grade duplicate sources to outscore 1 high-grade
source citing the same fact. This section is the fix, and it amends
Part 16 (and interacts with Parts 6, 9, 19) rather than replacing them.

### Substantive signal vs. source record

A **source record** is one `CanonicalObservation` — one thing one
source said. A **substantive signal** is the underlying startup fact
being evaluated: "customer_count = 10,000 at date X," "ARR = $5M for
period Y," "founder has 8 years of payments experience." Ten articles
repeating "the company has 10,000 customers" are ten source records
supporting **one** substantive signal, not ten independent strength
signals — this was always the intent of the taxonomy design in Part
16's worked examples (each names a *specific fact*, e.g. one named
prior company for `REPEAT_FOUNDER`), but Part 16 never stated the
general deduplication rule this requires, which is the actual gap.

### Signal identity (deduplication key)

A signal's identity is computed from **what is being measured**, never
from the reported value itself:

- **Quantitative observations:** `(metric_type, entity, period)` — e.g.
  a `RevenueObservation`'s identity is `(ARR, "COMPANY", "2025-01-01")`.
  Two observations sharing this key with the **same** value are
  corroboration of one signal. Two observations sharing this key with
  **different** values are a conflict (see below) — the value is
  deliberately excluded from the identity key so this distinction is
  possible at all. Two observations with **different** periods (e.g.
  ARR 2024 vs. ARR 2025) are always distinct signals, never merged —
  this is what lets Growth Trajectory's two-point requirement keep
  working correctly.
- **Qualitative observations:** `(dimension-relevant type, subject,
  classification/fact)` — e.g. a `FounderExperienceObservation`'s
  identity is `(founder_role, experience_type, prior_entity_name)`; a
  `CompetitiveEvidenceObservation`'s identity is keyed on
  `named_competitor`. Because the classification is already part of the
  identity, two qualitative observations sharing a signal identity are
  definitionally the same claim (no separate conflict path is needed
  for qualitative facts in this V1 design — text-level nuance beyond
  the modeled fields is out of scope, consistent with Part 7's "keep V1
  implementable" instruction).
- **Deduplication is never by exact source text.** Different wording
  describing the identical fact (e.g. "the company has 10,000
  customers" vs. "10K customers, per the company") must produce the
  same signal identity — this is why identity is computed from the
  already-extracted TYPED fields, never from `source_excerpt` string
  matching, which would fail on trivial rewording.

### Strength deduplication rule (amends Part 16)

**Classification signal-counting for every Category B dimension must
operate on the count of unique, resolved `CanonicalSignal`s, never on
the count of raw observations.** One source supporting fact X and 100
sources supporting the identical fact X must produce identical
Strength. This is now a first-class requirement of Part 16's taxonomy
pattern, not an implicit assumption — every dimension's rulebook
(Parts 9-14) inherits it automatically since they all route through
this shared mechanism.

### Coverage deduplication (confirms Part 20, no change needed)

Part 20 already stated coverage is computed per-dimension as a binary
flag ("does this dimension have at least the minimum resolved signal
count"), never per-observation — this was already correct and is
unaffected by the Strength fix; both now consistently key off the same
underlying `CanonicalSignal` concept.

### Source independence and corroboration (Confidence only)

Confidence, unlike Strength, MAY legitimately reflect genuine
corroboration — but "genuine" is a narrow, explicit classification, not
"more than one source exists":

```
SAME_ORIGIN      -- explicitly the same origin as another accepted
                     observation of this signal (e.g. two quotes of
                     the identical press release)
DERIVATIVE       -- a downstream repetition of another source (a blog
                     citing a wire report) -- distinct origin_id is not
                     required, but it adds no new independent evidence
UNKNOWN_ORIGIN   -- origin not established -- the conservative DEFAULT;
                     never counted as independent corroboration, so a
                     duplicate cannot claim independence merely by
                     omitting origin metadata
INDEPENDENT      -- a genuinely separate original observation of the
                     same fact (e.g. a company's own disclosure AND an
                     unrelated audited filing independently reporting
                     the same figure)
```

**Rule:** only observations explicitly marked `INDEPENDENT` (with
distinct origins) count toward a corroboration bonus, and only for
Confidence, never for Strength or Coverage. Two or more genuinely
independent, corroborating observations of the same signal may raise
that signal's confidence by one tier above what its single strongest
observation's provenance grade alone would produce. Any number of
`SAME_ORIGIN`/`DERIVATIVE`/`UNKNOWN_ORIGIN` repetitions — however many —
contributes zero additional confidence, closing the exact vector the
100x-duplication and 15-low-grade-sources findings exploited.

### Source lineage (minimal, V1-implementable)

Per Part 7's own "keep V1 implementable" instruction, lineage is a
single optional `origin_id` field on every observation — not a citation
graph. Observations sharing a non-null `origin_id` are definitionally
the same original report, however many times it was re-quoted. This is
the minimum metadata needed to distinguish "one press release, quoted
20 times" from "20 independently-reported facts," and no more.

### Provenance precedence (resolves the self-report vs. high-quality-secondary gap)

**No universal rule that one provenance grade always wins.** Instead, a
three-tier precedence order governs conflict resolution specifically
(distinct from the confidence-grade mapping in Part 21):

```
Tier 3: PRIMARY_VERIFIED
Tier 2: PRIMARY_SELF_REPORTED, HIGH_QUALITY_SECONDARY, DERIVED  (equal rank)
Tier 1: SECONDARY_ESTIMATE
Tier 0: UNVERIFIED
```

A strictly higher tier deterministically wins a conflict against a
lower tier (e.g. `PRIMARY_VERIFIED` beats a contradictory
`SECONDARY_ESTIMATE`; a company's own `PRIMARY_SELF_REPORTED` claim
beats a contradictory `SECONDARY_ESTIMATE`). **Within the same tier —
critically, `PRIMARY_SELF_REPORTED` vs. `HIGH_QUALITY_SECONDARY` — there
is no automatic winner**, exactly as this phase's own instruction
requires: a company's self-report contradicted by an independent
high-quality secondary source (e.g. an audited filing) is a genuine,
unresolved conflict, not something precedence should paper over.
Precedence is based on directness/verification-tier, never on brand
prestige or claim recency (a deliberate rejection of "the New York
Times outranks a smaller outlet" as a methodology principle).

### Conflict model

Two observations sharing a signal identity **conflict** when their
reported values differ (quantitative) — never merely because two
sources exist. `CONFLICT_DETECTED` is the resulting availability state
when no precedence tier resolves the disagreement;
`CONFLICT_RESOLVED_BY_PRECEDENCE` when a strictly higher tier exists.
An unresolved conflict makes the affected signal unusable for
scoring — excluded from both the positive-evidence count and Coverage,
confidence forced to the floor for anything that would have depended on
it — never averaged, never resolved by which observation happened to
be extracted or listed first (the specific, forbidden pattern Part 10
names).

### Conflict resolution is never order-dependent

Given the identical evidence set in **any** ordering, the accepted
signal, its classification, score, confidence, and coverage
contribution must all be identical. Conflict resolution must be
computed from a canonicalized, content-derived sort (e.g. by
`observation_id` as a stable tie-break within a precedence tier), never
from list/insertion order, and never from a bare `max()`/`min()` over
unsorted input, which silently reintroduces order-dependence on ties.

### Recency / staleness architecture

Four evidence-type freshness classes, assigned by observation TYPE (not
chosen per-instance):

```
STRUCTURAL_FACT      -- founder history, funding events -- remains
                         relevant for years; effectively never stale
                         within any realistic analysis horizon
HISTORICAL_FACT       -- market-size/growth estimates, competitive
                         landscape, product capability claims -- stale
                         slowly
RECENT_PERFORMANCE     -- customer count, retention, commercial
                         contracts -- moderate staleness
CURRENT_STATE          -- revenue, cash, burn, disclosed runway --
                         stales quickly
```

Each class has one provisional `stale_after_months` threshold
(explicitly `CALIBRATION REQUIRED`, per this document's own established
pattern — new parameters, not a recalibration of any parameter this
phase was told not to touch). A "borderline" zone begins at 75% of that
threshold.

### Staleness behavior

- **STRUCTURAL_FACT** observations are never staleness-filtered.
- **CURRENT_STATE / RECENT_PERFORMANCE** observations, once STALE, are
  excluded from the positive-evidence view used for scoring (they no
  longer support a "current state" classification) — but they are
  never deleted, and never converted into negative evidence. A stale,
  strongly positive fact simply stops counting toward Strength; it does
  not become evidence of weakness. If nothing else supports the
  dimension, it correctly falls to `UNAVAILABLE_NO_EVIDENCE` (or
  `UNAVAILABLE_INSUFFICIENT` for two-point dimensions), the same honest
  fallback the rest of the methodology already uses for genuinely
  missing evidence.
- **HISTORICAL_FACT** observations are staleness-tracked but with a
  long threshold, reflecting that market-level facts change more slowly
  than company-level ones.

---

## Part 7 — Rulebook Format

Every dimension's rulebook uses this exact 18-field structure. Four
dimensions are written out in full below as worked examples (one per
pillar-family: a Public/Market-style dimension, a Team dimension
directly demonstrating the SpaceX-defect fix, a redesigned Traction
dimension, and the newly-decomposed former-Category-C Strategic
Execution); the remaining ~22 dimensions follow the identical structure
and are summarized in the compact tables of Parts 9-14, with full
prose write-ups deferred to implementation (stated honestly as a scoping
decision, not hidden).

### Worked example 1 — Market / Competitive Intensity

*(chosen because this is one of the two dimensions directly implicated
in the SpaceX defect — Part 9 discusses both)*

```
DIMENSION NAME: Competitive Intensity
PURPOSE: Assess whether the company can realistically win given its
  competitive landscape.
WHY IT MATTERS: A large market with an entrenched, well-resourced
  incumbent and no differentiation is a materially weaker opportunity
  than the same market with fragmented or weak competitors.
STAGE APPLICABILITY: All stages; the BAR for "differentiated" rises
  with stage (Part 15).
EVIDENCE INPUTS: CompetitiveEvidenceObservation (named_competitor,
  competitor_type: DIRECT | ADJACENT | SUBSTITUTE), ProductCapability
  Observation (for differentiation cross-reference).
MINIMUM SCORABLE EVIDENCE: At least one named competitor OR at least
  one explicit, named differentiation claim relative to an unnamed but
  described competitive landscape.
AVAILABILITY CONDITIONS: UNAVAILABLE_NO_EVIDENCE if zero named
  competitors AND zero differentiation claims exist anywhere in
  accepted evidence -- this is the exact gate that failed for SpaceX in
  V2.1 (four named competitors existed in the source text and were
  discarded); V3's mechanical "is at least one CompetitiveEvidence
  Observation ACCEPTED" check cannot reproduce that failure mode,
  because it is a count check on typed objects, not a free judgment
  call.
POSITIVE SIGNALS: >=2 named DIRECT competitors + >=1 named
  differentiator = STRONG classification. 1 named competitor, no
  differentiator = ORDINARY. Named category leadership claim with
  supporting evidence (e.g. named market-share statement from a
  HIGH_QUALITY_SECONDARY source) = EXCEPTIONAL.
NEGATIVE SIGNALS: Explicit disclosed loss of a named deal/customer to a
  named competitor; explicit disclosed price-war or margin-compression
  signal attributed to competition.
CONTROLLED CLASSIFICATIONS: {NO_SIGNAL, ORDINARY, STRONG, EXCEPTIONAL,
  NEGATIVE_SIGNAL_PRESENT} -- five labels, not a free score.
DETERMINISTIC SCORE MAPPING: NO_SIGNAL -> UNAVAILABLE (not a number).
  ORDINARY -> band[5,6] (provisional structure; exact value CALIBRATION
  REQUIRED). STRONG -> band[7,8] (CALIBRATION REQUIRED). EXCEPTIONAL ->
  band[9,10] (CALIBRATION REQUIRED). NEGATIVE_SIGNAL_PRESENT -> band[0,4]
  (CALIBRATION REQUIRED), overriding a simultaneously-positive
  classification if both are present (negative evidence is never
  averaged against positive evidence into a mid-band number).
CONFIDENCE DETERMINATION: HIGH if >=1 HIGH_QUALITY_SECONDARY or
  PRIMARY_VERIFIED observation; MEDIUM if only PRIMARY_SELF_REPORTED/
  DERIVED; LOW if only SECONDARY_ESTIMATE.
COVERAGE DETERMINATION: this dimension's full configured weight counts
  toward pillar coverage whenever availability is not
  UNAVAILABLE_NO_EVIDENCE (Part 20 -- coverage is binary per dimension,
  not partial-credit for classification confidence).
CONFLICT HANDLING: two observations disagreeing on whether a named
  competitor is DIRECT vs. ADJACENT -> use the HIGHER-provenance-grade
  source per Part 6; equal grades -> classify at the more conservative
  (ADJACENT) level rather than guessing.
EXPLANATION OUTPUT: names every cited CompetitiveEvidenceObservation and
  ProductCapabilityObservation, the resulting classification label, the
  rule ID, and the score.
BOUNDARY CASES: a company operating in a genuinely novel category with
  no true competitors (rare) -- NO_SIGNAL would incorrectly suggest
  "unassessed" when the true state might be "no competition exists,"
  which is itself a signal. CALIBRATION REQUIRED: whether a sixth label
  (NO_DIRECT_COMPETITION_CLAIMED, requiring explicit sourced support)
  is needed.
CALIBRATION REQUIRED: exact score bands per classification label (all
  four bands above); whether the boundary-case sixth label is needed.
KNOWN LIMITATIONS: relies on the research/retrieval step actually
  surfacing named competitors -- a genuine retrieval failure (distinct
  from a classification failure) still produces UNAVAILABLE, correctly,
  but the underlying cause (nothing found vs. nothing exists) remains
  outside this dimension's own ability to distinguish; that
  distinction is Evidence Coverage's job (Part 20), not this rulebook's.
```

### Worked example 2 — Team / Founder-Market Fit

```
DIMENSION NAME: Founder-Market Fit
PURPOSE: Assess whether the founding team has direct, evidenced insight
  into or experience with the specific market/problem.
WHY IT MATTERS: Founders with genuine domain depth make fewer
  foundational mistakes and are more credible to the exact customers
  the company needs.
STAGE APPLICABILITY: Weighted most heavily in the overall Team score at
  Pre-Seed/Seed (Part 15's stage table); still assessed but
  proportionally less determinative at Growth, where Leadership and
  Execution Track Record carry more of the pillar's signal.
EVIDENCE INPUTS: FounderExperienceObservation, FounderOutcomeObservation.
MINIMUM SCORABLE EVIDENCE: At least one FounderExperienceObservation
  with experience_type != UNRELATED_DOMAIN, OR at least one
  FounderOutcomeObservation for a named prior entity.
AVAILABILITY CONDITIONS: UNAVAILABLE_NO_EVIDENCE only if literally zero
  FounderExperienceObservation/FounderOutcomeObservation objects were
  accepted for any founder. This is the mechanical fix for the SpaceX
  defect: Musk's PayPal/Tesla/Boring-Company history would extract as
  multiple FounderOutcomeObservation(prior_entity_name=...) objects;
  the availability check is "did at least one such typed object get
  accepted," not "does the model feel this constitutes enough insight
  into aerospace specifically" -- the latter question, which is what
  produced the V2.1 failure, is answered by the CLASSIFICATION step
  below, not the availability gate.
POSITIVE SIGNALS: experience_type=DIRECT_DOMAIN with a named prior
  entity; REPEAT_FOUNDER with a named prior entity; PRIOR_EXIT with a
  named acquirer or IPO event.
NEGATIVE SIGNALS: FounderOutcomeObservation(outcome_type=SHUT_DOWN) for
  a directly-relevant prior venture, if the source explicitly attributes
  the shutdown to founder-caused factors (never inferred from the mere
  fact of a shutdown, which could reflect market timing, not founder
  quality) -- CALIBRATION REQUIRED for exactly how this attribution is
  established without over-crediting speculation.
CONTROLLED CLASSIFICATIONS: {NO_RELEVANT_EXPERIENCE, ADJACENT_EXPERIENCE,
  DIRECT_EXPERIENCE, DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME}. Four labels
  -- deliberately not the arbitrary NONE/ADJACENT/DIRECT/DEEP set
  floated illustratively in the phase prompt, because "DEEP" as a fifth
  label would need its own inclusion criteria distinct from
  DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME and none was found that wasn't
  already captured by requiring a named prior outcome.
DETERMINISTIC SCORE MAPPING: NO_RELEVANT_EXPERIENCE -> UNAVAILABLE (not
  a low score -- absence of domain background is not itself negative
  evidence unless a negative signal, above, is also present).
  ADJACENT_EXPERIENCE -> band[5,6] (CALIBRATION REQUIRED). DIRECT_
  EXPERIENCE -> band[7,8] (CALIBRATION REQUIRED). DIRECT_EXPERIENCE_
  WITH_PRIOR_OUTCOME -> band[9,10] (CALIBRATION REQUIRED).
CONFIDENCE DETERMINATION: HIGH if the named prior entity/outcome is
  corroborated by a HIGH_QUALITY_SECONDARY source (e.g. a named
  acquisition reported by a named outlet); MEDIUM if PRIMARY_SELF_
  REPORTED only.
COVERAGE DETERMINATION: full dimension weight counts whenever not
  UNAVAILABLE_NO_EVIDENCE.
CONFLICT HANDLING: a founder's self-reported bio conflicting with an
  independent source about role/tenure at a named prior company ->
  classify at the more conservative experience_type, flag
  UNAVAILABLE_CONFLICTING_EVIDENCE only if the conflict is about
  WHETHER the experience happened at all, not merely its exact tenure
  length.
EXPLANATION OUTPUT: names every founder, every cited prior entity, the
  classification, rule ID, and score.
BOUNDARY CASES: a founder with DIRECT_DOMAIN experience in a genuinely
  different but analogous market (e.g. built payments infrastructure,
  now building healthcare-payments infrastructure) -- classified
  ADJACENT_EXPERIENCE by default; CALIBRATION REQUIRED on whether a
  documented, specific analogy (not just topical similarity) should
  earn DIRECT_EXPERIENCE instead.
CALIBRATION REQUIRED: all four score bands; the analogous-market
  boundary case; the negative-signal attribution standard.
KNOWN LIMITATIONS: still depends on research/retrieval surfacing
  founder history at all -- V2.1's four-query research architecture
  (already shipped) is assumed to feed this, and this rulebook does not
  re-solve retrieval, only classification.
```

### Worked example 3 — Traction / Current Scale (new, redesigned)

```
DIMENSION NAME: Current Scale
PURPOSE: Assess the company's demonstrated absolute level of activity
  (revenue, GMV, or user/customer count) at a point in time.
WHY IT MATTERS: Scale, independent of trajectory, is real evidence of
  demonstrated commercial pull -- this is the exact concept the old
  "Customer Growth/Revenue Growth" Deterministic dimensions could not
  credit from a single disclosed figure, producing the 15%-coverage-
  for-25/25-companies structural ceiling (Phase 10.8B finding).
STAGE APPLICABILITY: What counts as "strong" scale is entirely
  stage-relative (Part 15) -- $500K ARR is exceptional at Seed and
  ordinary at Series B+.
EVIDENCE INPUTS: RevenueObservation (any metric_type), 
  CustomerCountObservation(customer_type=PAYING).
MINIMUM SCORABLE EVIDENCE: exactly ONE dated, ACCEPTED
  RevenueObservation OR CustomerCountObservation -- deliberately not
  requiring two points, since this dimension explicitly does NOT claim
  to measure growth (Growth Trajectory, below, owns that and correctly
  keeps the two-point requirement).
AVAILABILITY CONDITIONS: UNAVAILABLE_NO_EVIDENCE if zero qualifying
  observations exist; UNAVAILABLE_PRIVATE_INFORMATION is not applicable
  here since scale, when disclosed at all, is disclosed publicly by
  definition (a company that discloses nothing about its scale
  correctly falls to NO_EVIDENCE, not a private-information carve-out).
POSITIVE SIGNALS: a disclosed revenue/GMV/customer figure that, per the
  stage table (Part 15), exceeds the "ordinary for this stage" band.
NEGATIVE SIGNALS: none native to this dimension -- Current Scale
  measures a snapshot, not direction; decline is Growth Trajectory's
  negative-evidence territory, not this dimension's (Part 18's
  double-counting rule: a disclosed revenue DECLINE populates Growth
  Trajectory's negative field, not Current Scale's, even though both
  dimensions consume the same underlying RevenueObservation type).
CONTROLLED CLASSIFICATIONS: N/A -- this is a genuinely quantitative
  dimension (Category A once one real observation exists), not a
  taxonomy-classification dimension.
DETERMINISTIC SCORE MAPPING: stage-relative absolute-value bands (e.g.
  Seed: <$100K ARR = ordinary-low, $100K-$1M = strong, >$1M =
  exceptional-for-stage) -- every specific dollar threshold is
  CALIBRATION REQUIRED, the concept (stage-relative absolute bands) is
  not.
CONFIDENCE DETERMINATION: HIGH if PRIMARY_SELF_REPORTED or better;
  MEDIUM if only a SECONDARY_ESTIMATE figure exists (e.g. a third-party
  revenue-estimate aggregator).
COVERAGE DETERMINATION: full weight counts whenever one real observation
  exists.
CONFLICT HANDLING: two disclosed figures for the same metric_type/date
  that disagree -> UNAVAILABLE_CONFLICTING_EVIDENCE (Part 6).
EXPLANATION OUTPUT: cites the specific observation, its date, its
  stage-relative band, rule ID, score.
BOUNDARY CASES: a company disclosing GMV but not revenue (marketplace
  model) -- GMV is accepted as its OWN metric_type with its own,
  separately-calibrated stage bands (never coerced to a revenue-shaped
  threshold, per Part 5).
CALIBRATION REQUIRED: every stage-relative dollar/count threshold, for
  every metric_type, at every stage -- this is one of the largest
  single calibration surfaces in the entire rulebook and is flagged as
  such in the companion calibration plan.
KNOWN LIMITATIONS: a company at massive real scale that discloses
  nothing publicly (common for some private companies) still resolves
  to UNAVAILABLE here -- this is correct per the methodology's own
  definition (SPS measures demonstrated evidence, not true underlying
  scale), but should be stated plainly to any reader comparing two
  companies with different disclosure norms.
```

### Worked example 4 — Execution / Strategic Execution (moved from C to B)

```
DIMENSION NAME: Strategic Execution
PURPOSE: Assess whether the company's strategic choices (market entry
  sequencing, competitive positioning, capital allocation) are
  coherent and evidenced, not merely stated.
WHY IT MATTERS: A company can execute operationally well while pursuing
  an incoherent strategy (unfocused segments, no response to
  competition, capital misallocated relative to stated milestones) --
  this is a real, distinct failure mode from weak GTM/product execution.
STAGE APPLICABILITY: what counts as a "coherent strategy" scales with
  stage -- a Pre-Seed company needs a focused wedge; a Growth-stage
  company needs a defensible category strategy.
EVIDENCE INPUTS: a new, narrowly-scoped set of four boolean-with-
  evidence fields, extracted the same way any other Category B
  taxonomy is (not a free strategic-quality judgment):
    wedge_named: bool + cited evidence (a specific initial customer
      segment/use-case named, not "we serve businesses")
    expansion_logic_stated: bool + cited evidence (a stated sequence
      from the initial wedge to a broader market)
    competitive_response_named: bool + cited evidence (a specific
      stated reaction to a NAMED competitor, not generic "we compete on
      quality")
    capital_allocation_stated: bool + cited evidence (a stated,
      specific link between funds raised and named milestones)
MINIMUM SCORABLE EVIDENCE: at least one of the four fields populated
  with cited evidence.
AVAILABILITY CONDITIONS: UNAVAILABLE_NO_EVIDENCE if zero fields
  populated.
POSITIVE SIGNALS: 3-4 fields populated with specific, cited evidence.
NEGATIVE SIGNALS: a field populated but the cited evidence is
  self-contradictory (e.g. a stated wedge directly contradicted by a
  stated expansion claim, or a disclosed strategic reversal with no
  stated reason).
CONTROLLED CLASSIFICATIONS: {NO_SIGNAL, SINGLE_SIGNAL, MULTIPLE_SIGNALS,
  COMPREHENSIVE, CONTRADICTED} -- five labels derived directly from a
  count of the four boolean fields plus the negative-signal check, not
  a holistic "is this a good strategy" judgment.
DETERMINISTIC SCORE MAPPING: SINGLE_SIGNAL -> band[5,6]; MULTIPLE_
  SIGNALS (2-3 fields) -> band[7,8]; COMPREHENSIVE (4 fields) ->
  band[9,10]; CONTRADICTED -> band[0,4]; all bands CALIBRATION REQUIRED.
CONFIDENCE DETERMINATION: standard provenance-grade-based rule (Part 6),
  no dimension-specific variation needed.
COVERAGE DETERMINATION: full weight whenever not NO_SIGNAL.
CONFLICT HANDLING: standard (Part 6).
EXPLANATION OUTPUT: lists which of the four fields were populated, their
  cited evidence, the resulting label, rule ID, score.
BOUNDARY CASES: a company with a genuinely simple, obviously-correct
  strategy that a source describes in one sentence (e.g. "we are the
  only company doing X for Y") -- may legitimately populate only
  wedge_named and still represent excellent strategy. CALIBRATION
  REQUIRED: whether SINGLE_SIGNAL's score band is too punishing for this
  legitimate case, vs. correctly distinguishing it from a company with
  comprehensively-evidenced strategy.
CALIBRATION REQUIRED: all four score bands; the single-signal boundary
  case above.
KNOWN LIMITATIONS: this decomposition necessarily loses some of the
  holistic "does this all hang together as a coherent narrative" signal
  a skilled human diligence reviewer would apply -- accepted as the
  honest cost of eliminating free-form LLM numeric judgment entirely
  (Part 34's decision), not hidden. If, after implementation, this
  decomposition is found to systematically mis-rank companies a human
  reviewer would clearly distinguish, that is grounds to revisit this
  decision in a future phase, not evidence to silently patch it now.
```

The remaining ~22 dimensions (full list, Part 36) follow this identical
18-field shape; Parts 9-14 below give each pillar's dimension set in
compact table form (purpose / evidence / classification / stage note /
calibration flag) rather than four more full 18-field write-ups each,
to keep this document's total length tractable — the four worked
examples above demonstrate the format is applicable to every dimension
type this methodology contains (a Public-evidence dimension, a
founder/team dimension, a redesigned quantitative Traction dimension,
and a decomposed former-qualitative dimension).

---

## Part 8 — Score Granularity

**Recommendation: (C) discrete bands mapped to canonical values, with
(D) as a narrow exception for genuinely continuous quantitative
dimensions.**

Reasoning: a Category B dimension's classification label (e.g.
`DIRECT_EXPERIENCE`) should map to one fixed canonical value (e.g. 7.5),
not a range the evaluator then has to further guess within — a decimal
like "7.3" implies a precision (why not 7.4?) the underlying evidence
cannot support once the evidence itself is a discrete label. **Every
Category B dimension therefore outputs one of a small number of fixed
canonical scores** (e.g. `{null, 5.5, 7.5, 9.5}` for a four-label
taxonomy — not even a symmetric `NONE=2/LOW=4/MEDIUM=6/HIGH=8` ladder
adopted merely because it looks tidy; each dimension's specific fixed
values are set per its own rulebook, per Part 19).

The narrow exception: Category A dimensions with genuinely continuous
underlying math (e.g. a computed burn/revenue ratio, a computed
year-over-year growth percentage) may output a continuous value **within
a band determined by which threshold range the raw number falls into**
— e.g. a growth rate of 340% YoY at Series A might map deterministically
to a formula-computed score of 8.7 rather than a flattened 8.5 fixed
value, because the underlying quantity genuinely is continuous and a
formula (not a judgment) produced it. This is (D), reserved for
dimensions where continuous precision reflects real continuous evidence,
never for taxonomy-classification dimensions where it would fabricate
false precision.

---

## Part 9 — Market Rulebook (compact)

| Dimension | Evidence inputs | Classification labels | Negative evidence | Stage note | Calibration flags |
|---|---|---|---|---|---|
| Market Size | MarketSizeObservation, ProductCapability (segment breadth) | NO_SIGNAL / NAMED_SEGMENT / NAMED_SEGMENT_WITH_ESTIMATE / VERIFIED_LARGE | n/a (size itself isn't negative-evidence-shaped) | Bar for "large enough" scales down at earlier stages (a focused niche is fine at Pre-Seed) | All score bands; whether TAM-estimate-absence should ever be treated as a mild negative for later-stage companies expected to have one |
| Market Growth | MarketGrowthObservation, disclosed company-growth-as-proxy | NO_SIGNAL / COMPANY_PROXY_ONLY / NAMED_CATEGORY_GROWTH / VERIFIED_STRONG_GROWTH | Explicit disclosed category contraction | Category-level growth matters more at Growth stage than Pre-Seed | All bands; how much to discount company-growth-as-market-growth-proxy |
| Market Timing | regulatory/catalyst/technology-inflection signals (three boolean fields) | NO_SIGNAL / SINGLE_CATALYST / MULTIPLE_CATALYSTS | Explicit disclosed adverse regulatory action | Same taxonomy at every stage; the boolean fields don't need stage variation, only the score bands might | All bands; hardest Market dimension to fully validate — flagged for extra Part-30 stress testing |
| Competitive Intensity | CompetitiveEvidenceObservation | See worked example 1, Part 7 | Disclosed lost deal/price pressure attributed to competition | Bar for "differentiated" rises with stage | All bands; the no-direct-competition boundary case |
| Customer Demand | disclosed customer/revenue-data presence, lifecycle-applicability facts (reuses existing `sie_v2_anchors.py` machinery) | Existing NOT_APPLICABLE / EXPECTED states, extended with a small taxonomy for the EXPECTED case | Explicit disclosed demand failure (e.g. discontinued pilot) | Already stage-aware via the existing lifecycle rule | Only the new EXPECTED-case taxonomy bands |

**Explicit rule for this pillar, directly answering Part 9's own
instruction:** no Market dimension may reach a positive classification
from a generic statement like "large and growing market" alone — every
positive label requires at minimum a named segment, a named competitor,
or a named catalyst; unnamed, unsourced characterizations are treated
identically to no evidence at all.

---

## Part 10 — Team Rulebook (compact)

| Dimension | Evidence inputs | Classification labels | Negative evidence | Stage note | Calibration flags |
|---|---|---|---|---|---|
| Founder-Market Fit | See worked example 2, Part 7 | NO_RELEVANT_EXPERIENCE / ADJACENT / DIRECT / DIRECT_WITH_OUTCOME | Attributed-shutdown FounderOutcomeObservation | Weighted heaviest in overall Team interpretation at Pre-Seed/Seed | All bands; the analogous-market boundary case |
| Technical Capability | ProductCapabilityObservation (shipped complexity), FounderExperienceObservation (technical) | NO_SIGNAL / BASIC_SHIPPED / COMPLEX_SHIPPED_OR_NAMED_TECHNICAL_FOUNDER / COMPLEX_SHIPPED_AND_NAMED_TECHNICAL_FOUNDER | Disclosed reliability failure | Complexity bar for "strong" rises with stage/product type | All bands; what counts as "complex" per product category |
| Business Capability | RevenueObservation (as a repeatability signal), CommercialContractObservation | NO_SIGNAL / SINGLE_SIGNAL / REPEATABILITY_EVIDENCED | Disclosed abandoned GTM motion | Bar rises with stage | All bands |
| Leadership | named-hire count, FounderExperienceObservation (leadership roles) | NO_SIGNAL / FOUNDER_CLARITY_ONLY / NAMED_HIRES / NAMED_EXECUTIVE_TEAM | Explicit disclosed founder conflict/departure | Pre-Seed bar = founder clarity; Growth bar = named execs | All bands; distinguishing "no named hires" (neutral, common pre-revenue) from a genuine gap |
| Execution Track Record (Team) | dated milestone claims, distinct from the Execution pillar's own dimensions (Part 18 double-counting rule) | NO_SIGNAL / SINGLE_MILESTONE / MULTIPLE_DATED_MILESTONES | Disclosed repeated missed milestones | What counts as "a milestone" scales with stage | All bands |

---

## Part 11 — Product Rulebook (compact)

| Dimension | Evidence inputs | Classification labels | Negative evidence | Stage note | Calibration flags |
|---|---|---|---|---|---|
| Customer Value | CustomerEvidenceObservation (named outcome, quantified outcome) | NO_SIGNAL / NAMED_UNQUANTIFIED / NAMED_QUANTIFIED | Disclosed customer complaint pattern | Bar for "quantified" rises with stage | All bands |
| Differentiation | ProductCapabilityObservation, CompetitiveEvidenceObservation | NO_SIGNAL / STATED_UNCOMPARED / NAMED_COMPARISON | Disclosed feature parity admission | Same at every stage | All bands |
| **Product Accessibility** (REDESIGNED from Usability — see Part 35) | self_serve_signup: bool, published_pricing: bool, integration_marketplace_presence: bool, published_api_docs: bool | NO_SIGNAL / SINGLE_SIGNAL / MULTIPLE_SIGNALS | n/a | Self-serve expectations differ by stage/business model (enterprise-only motions legitimately lack this) | All bands; whether enterprise-motion companies should be exempted from this dimension entirely rather than scored NO_SIGNAL by default |
| Defensibility | claimed network-effects/proprietary-data/switching-cost, each requiring cited evidence | NO_SIGNAL / CLAIMED_UNEVIDENCED / EVIDENCED | n/a | Same at every stage | All bands; how strictly to require evidence vs. accepting a well-reasoned claim |
| Adoption Potential | named expansion path, cross-sell evidence | NO_SIGNAL / NAMED_PATH / EVIDENCED_EXPANSION | n/a | Bar rises with stage | All bands |

**Directly answering Part 11's challenge on Usability:** the original
dimension is not simply removed — it is redesigned into "Product
Accessibility," a genuinely publicly-observable proxy set (self-serve
signup, published pricing, integration/marketplace presence, published
docs), explicitly distinct from true UX/onboarding-friction measurement
(activation rate, time-to-value), which remains primarily
founder/analytics-assessable and is not represented as a public-evidence
dimension at all under V3. This directly prevents polished marketing
copy from ever being treated as usability evidence — the four fields
are all binary, checkable facts (does a signup flow exist without a
sales call, is pricing published), not narrative quality judgments.

---

## Part 12 — Execution Rulebook (compact)

| Dimension | Evidence inputs | Classification labels | Negative evidence | Stage note | Calibration flags |
|---|---|---|---|---|---|
| Go-to-Market Execution | named channel, repeatability evidence, disclosed efficiency metric | NO_SIGNAL / SINGLE_SIGNAL / REPEATABILITY_EVIDENCED / EFFICIENCY_DISCLOSED | Disclosed high CAC / long unproductive sales cycle | Bar rises sharply with stage (founder-led vs. scaled motion) | All bands |
| Product Execution | shipped evidence, named integration, disclosed reliability metric | NO_SIGNAL / SHIPPED / SHIPPED_WITH_INTEGRATION_OR_RELIABILITY | Disclosed reliability failure/quality issue | Bar rises with stage | All bands |
| **Operating Discipline** (SPLIT from Operational Execution — qualitative half; see Part 35) | named process, disclosed hiring plan, disclosed milestone cadence | NO_SIGNAL / SINGLE_SIGNAL / MULTIPLE_SIGNALS | Disclosed process breakdown | Pre-Seed: informal is fine (NO_SIGNAL here is not penalized in the pillar aggregation, see Part 23); Growth: expected | All bands; ensuring this doesn't silently re-absorb the quantitative burn/margin claims that belong in Financial Health now (Part 18 enforcement point) |
| Strategic Execution | See worked example 4, Part 7 | NO_SIGNAL / SINGLE_SIGNAL / MULTIPLE_SIGNALS / COMPREHENSIVE / CONTRADICTED | Contradicted field | Same taxonomy at every stage | All bands; single-signal boundary case |

**Directly answering Part 12's challenge:** company existence and
generic milestone mentions ("we're growing fast") populate zero typed
fields under this design and correctly resolve to NO_SIGNAL —
Category B's requirement that every positive field carry cited,
specific evidence (a named channel, a named integration, a dated
milestone) is what prevents this pillar from repeating V2.1's mid-band-
floor problem (Phase 10.8A's central finding), independent of and in
addition to the removed free-form scoring itself.

---

## Part 13 — Traction Rulebook

| New dimension | What it measures | Supporting evidence | Does NOT establish | Category | Stage-relative interpretation | Negative evidence | Unavailable conditions |
|---|---|---|---|---|---|---|---|
| Current Scale | Absolute level of activity at a point in time | One dated RevenueObservation or CustomerCountObservation | Growth, durability, profitability | A | Stage-relative absolute bands (Part 15) | None native (see Growth Trajectory) | Zero qualifying observations |
| Growth Trajectory | Change in scale over time | Two same-metric_type observations at different dates | Absolute scale, profitability | A | Stage-relative rate expectations | Disclosed decline (same metric, same type, later date lower) — direct negative evidence, mapped to a low band, not merely "no growth" | Fewer than two comparable dated points |
| Customer Adoption | Breadth/composition of who has adopted | CustomerCountObservation (any type), named customer examples | Retention, revenue quality | B | Named enterprise logos matter more at later stages; raw count matters more at Pre-Seed/Seed | Disclosed customer loss pattern | Zero qualifying observations |
| Retention / Engagement | Whether adopters keep using/paying | RetentionObservation (A, when NRR/GRR/churn disclosed) or qualitative usage-frequency signals (B, otherwise) | Initial adoption, growth | A/B hybrid | Retention bar is largely stage-invariant (churn is bad at any stage) but the EXPECTATION that it's been measured yet rises with stage | Disclosed high churn / failed retention | Zero qualifying observations |
| Commercial Validation | Whether real buyers have committed | CommercialContractObservation (contract, renewal), named enterprise logos | Profitability, revenue scale | B | Contract SIZE expectations rise with stage; a single pilot is meaningful at Pre-Seed, unremarkable at Growth | Disclosed lost/non-renewed contract | Zero qualifying observations |

**Directly implementing the phase's own worked examples:** "$20M ARR
proves scale" now populates Current Scale fully and Growth Trajectory
not at all (correctly — a single figure cannot prove a trend). "10,000
customers proves adoption" populates Customer Adoption without touching
Retention/Engagement. "50 signed enterprise contracts proves commercial
validation" populates Commercial Validation without implying anything
about profitability (Financial Health's separate concern).

---

## Part 14 — Financial Health Rulebook

| Dimension | Publicly assessable? | Evidence inputs | Category | Score mechanism | Calibration status |
|---|---|---|---|---|---|
| Revenue Quality | Sometimes public | RetentionObservation, CommercialContractObservation, disclosed customer-concentration signal | B | Taxonomy: recurring-revenue claimed / contract-length disclosed / concentration-risk disclosed (negative field) | Score bands CALIBRATION REQUIRED |
| Unit Economics | Primarily private/founder-provided | CAC/LTV-shaped observations (new typed pair, not designed in full here) | A (unchanged from V2.1's Deterministic mechanism) | Pure computation once both real inputs exist; fail-closed otherwise | Unchanged — already the one dimension V2.1 got structurally right |
| **Capital Efficiency** (MERGED: Burn Efficiency + Runway + Operational Execution's quantitative half — see Part 35) | Primarily private/founder-provided | CashObservation, BurnObservation, RevenueObservation | A | burn÷revenue or cash÷burn, computed ONLY from real disclosed pairs; explicit disclosed runway *statement* (e.g. "18 months of runway") accepted as a DIRECT observation in its own right, not requiring the underlying cash/burn split to exist separately | Which specific ratio thresholds map to which bands — CALIBRATION REQUIRED; the MERGE itself (concept) is JUSTIFIED NOW per the double-counting audit (Part 18) |

**Should Financial Health frequently have low public coverage under
V3? Yes, explicitly by design** — restated from 10.8D and reaffirmed
after this phase's deeper redesign: two of the pillar's three surviving
dimensions are primarily private/founder-provided, and this pillar
carries the smallest pillar weight (10%) precisely because of that
structural reality, not despite it.

**Is SPS still publishable with Financial Health mostly Unavailable?
Yes** — Financial Health is not one of the (revised, Part 1) "at least 2
of {Market, Team, Product}" required pillars.

---

## Part 15 — Stage Tables (architecture, not final thresholds)

One stage table per dimension-family, structured as:

```
StageTable[dimension]:
  IDEA:      { ordinary: ..., strong: ..., exceptional: ... }
  PRE_SEED:  { ... }
  SEED:      { ... }
  SERIES_A:  { ... }
  SERIES_B_PLUS: { ... }
  GROWTH:    { ... }
```

Not every dimension needs six distinct rows — several (e.g.
Competitive Intensity's classification logic) are stage-**bar**-
sensitive (the same taxonomy label maps to a stronger relative meaning
at a later stage) rather than stage-**taxonomy**-sensitive (different
fields entirely at different stages). The distinction matters for
implementation cost: taxonomy-sensitive dimensions (none identified in
this pass — every taxonomy designed above works unchanged across
stages) are cheaper than bar-sensitive ones (most dimensions), which in
turn are cheaper than the genuinely quantitative stage-relative bands
Current Scale and Growth Trajectory require (Part 13), where every
single dollar/percentage threshold, at every stage, is its own
calibration surface.

**Every specific numeric threshold in every stage table is
CALIBRATION REQUIRED without exception.** No false precision is
asserted anywhere in this document — Part 30's stress tests exercise the
*shape* of stage-relative behavior (an exceptional Pre-Seed profile
scoring well, a weak Growth profile scoring poorly) without asserting
specific numbers.

---

## Part 16 — Controlled Qualitative Taxonomy Design Pattern

Generalizing from the four worked examples (Part 7), every Category B
taxonomy in V3 follows this exact output contract:

```
{
  "classification": <one label from the dimension's fixed enum>,
  "supporting_evidence_ids": [<CanonicalObservation ids>],
  "negative_evidence_ids": [<CanonicalObservation ids, if any>],
  "reason": "<one sentence, for the explanation trace, never consumed
              by scoring logic itself>"
}
```

**Design rules, applied uniformly:**
- Every label requires at least one `supporting_evidence_ids` entry
  except the "no signal" label, which requires an empty list (a
  taxonomy call with a positive label and zero cited evidence is a
  contract violation, rejected at validation, treated as
  UNAVAILABLE — never silently accepted).
- Ambiguous evidence (could plausibly support two labels) defaults to
  the MORE CONSERVATIVE label — the taxonomy never resolves ambiguity
  upward.
- Conflicting evidence (`negative_evidence_ids` populated alongside a
  positive `classification`) always routes to the dimension's own
  CONTRADICTED/NEGATIVE_SIGNAL_PRESENT label, never left to average out.
- **Model discretion is minimized structurally, not just by
  instruction**: the enum of valid `classification` values is enforced
  by the same typed-parsing validation as `CanonicalObservation` itself
  — an out-of-enum label is a parse failure, re-prompted once (mirroring
  V2.1's existing scoped-correction retry pattern), then falls to
  UNAVAILABLE rather than being coerced into the nearest valid label by
  guesswork.

---

## Part 17 — Negative Evidence Taxonomy

| Signal | Establishing evidence | Affects | Stage-sensitive? | Severity needed? |
|---|---|---|---|---|
| revenue_decline | Two RevenueObservations, same metric_type, later date lower | Traction (Growth Trajectory) | No — decline is decline at any stage | Yes — magnitude affects band (CALIBRATION REQUIRED) |
| customer_decline | Two CustomerCountObservations, same type, later date lower | Traction (Customer Adoption) | No | Yes |
| high_churn | RetentionObservation below a stage-calibrated floor | Traction (Retention/Engagement) | Yes — floor differs by business model, not stage per se (CALIBRATION REQUIRED) | Yes |
| founder_departure / leadership_instability | FounderOutcomeObservation or a disclosed departure event | Team (Leadership) | No | Yes — a departure with a stated amicable reason vs. an undisclosed abrupt exit differ (CALIBRATION REQUIRED) |
| product_shutdown | Disclosed discontinuation of a product line | Product (Adoption Potential), Execution (Product Execution) | No | No — binary |
| regulatory_constraint | Disclosed enforcement action or explicit regulatory bar | Market (Market Timing) | No | Yes |
| customer_concentration | Disclosed dependency on a small number of accounts for majority revenue | Financial Health (Revenue Quality) | Yes — concentration is more expected/tolerable pre-Series-A | Yes |
| failed_commercial_expansion | Disclosed withdrawal from a stated market/segment | Execution (Strategic Execution), Traction (Commercial Validation) | No | No |
| market_contraction | MarketGrowthObservation showing category decline from a named source | Market (Market Growth) | No | Yes |
| severe_cash_constraint | CashObservation/BurnObservation implying near-term insolvency | Financial Health (Capital Efficiency) | No — this is the specific case Part 1 flagged as wrongly excluded from justifying <40 under 10.8D's rejected gate | Yes |

**Double-counting prevention (cross-referencing Part 18):** each row
above lists exactly which dimension(s) the signal affects; a signal must
never be wired to populate two dimensions' negative-evidence fields from
the same single underlying fact unless each dimension's rule is asking
a genuinely distinct question of it (e.g. `severe_cash_constraint`
affects only Capital Efficiency, not also Traction, even though the
underlying `BurnObservation` might be cited in both dimensions'
explanation traces for context).

**Unknown must never populate these fields — enforced structurally, not
by convention:** every row's "establishing evidence" column names a
specific, typed, ACCEPTED observation or comparison of two observations
— there is no code path where an absence of information (rather than a
presence of a specific negative fact) can satisfy any row above.

---

## Part 18 — Double-Counting Audit

| Shared fact | Dimensions that may cite it | Distinguishing question each asks | Safeguard |
|---|---|---|---|
| Revenue | Traction/Current Scale, Traction/Growth Trajectory, Financial Health/Revenue Quality, Financial Health/Capital Efficiency, Team/Business Capability | "How big" / "is it growing" / "is it durable/recurring" / "is it efficient relative to burn" / "is there a repeatable motion" | Each evaluator's rule is written against a distinct field-combination (e.g. Capital Efficiency requires Revenue AND Burn together; Current Scale requires Revenue alone) — a rule that would fire identically off Revenue's mere presence regardless of which dimension is asking is disallowed by design review, not just convention |
| Founder history | Team/Founder-Market Fit, Team/Execution Track Record (historical, cross-venture), Execution/* (current-company-only, explicitly excluded from citing prior-venture facts) | "Domain insight" / "has this person, historically, hit milestones" / (Execution pillar dimensions never cite founder-history facts at all) | Execution pillar evaluators' evidence inputs are explicitly scoped to CURRENT-company observations only — a `FounderExperienceObservation` about a PRIOR company is structurally not a valid input type for any Execution-pillar evaluator |
| Funding | Financial Health/Capital Efficiency (as the cash-inflow side of a runway calculation only) | Never Traction, never "market perception" | `FundingObservation` has no code path into any Traction or Market evaluator, full stop — Part 5's normalization rules make this a type-system guarantee, not a review checklist item |
| Named competitors | Market/Competitive Intensity, Product/Differentiation | "Can the company win" / "is the product distinct" | Distinct evidence fields even when citing the same `CompetitiveEvidenceObservation` — Competitive Intensity asks about the competitive landscape's structure, Differentiation asks about the product's own distinctiveness within it |

**General rule, stated once and applied throughout this document:**
shared evidence across dimensions is permitted only when each
consuming dimension's deterministic rule is answering a genuinely
distinct, named question of that evidence. A rule that would trigger
identically regardless of which dimension is asking is a double-
counting violation and must be merged into one dimension or have one
instance's use of that evidence removed — this is the standard applied
throughout Parts 9-14 above, not a separate afterthought.

---

## Part 19 — Score Mapping Philosophy

Every classification→score mapping in this document follows one
principle, stated once here rather than repeated in every dimension's
rulebook: **a stronger classification must map above every weaker
classification's band, with no overlap, and the existence of that
ordering is justified by the taxonomy's own construction (more/better-
evidenced fields = stronger label, by design) — but the exact numeric
value of each band is explicitly NOT claimed to be known yet.**

This is why every worked rulebook above writes bands as `band[7,8]
(CALIBRATION REQUIRED)` rather than a specific value — the **provisional
structure** (ordinal ranking of labels, non-overlapping bands, negative
labels below positive labels) is fixed by this document; the **final
threshold** (is `DIRECT_EXPERIENCE` exactly 7.5, or 7.0, or 8.0) is
explicitly deferred to the calibration plan. A tidy symmetric ladder
(NONE=2/LOW=4/MEDIUM=6/HIGH=8/EXCEPTIONAL=10) is explicitly rejected as
a default — nothing in this document assumes evenly-spaced bands are
correct, only that ordering must be monotonic and non-overlapping.

---

## Part 20 — Coverage (Redesigned)

**Challenging 10.8D's 35%/40% directly (see Part 1): the numbers are
rejected as arbitrary; the underlying architecture (pillar-weight-based
coverage) is kept, refined as follows.**

**Answering this Part's own questions directly:**
- *Does one scorable dimension equal another for coverage purposes?*
  No — coverage is **weighted by each dimension's configured weight**
  within its pillar (unchanged mechanism from V2.1's
  `calculate_evidence_coverage`), not a flat per-dimension count. A
  25%-weighted dimension resolving contributes more coverage than a
  15%-weighted one.
- *Do 100 weak secondary sources increase coverage?* **No.** Coverage
  is computed per-dimension as a binary (scorable or not, per Part 7's
  "coverage determination" fields), not per-observation — once a
  dimension clears its minimum-evidence bar, additional redundant
  observations of the same fact do not add further coverage. This is
  the direct, structural answer to evidence-abundance bias leaking into
  Coverage: a famous company with fifty articles repeating the same
  fact gets the same coverage credit for that one dimension as a
  company with one clean source stating it once.
- *Should redundant evidence increase coverage?* No, per above — but
  redundant evidence from independent, high-provenance sources **does**
  increase Confidence (Part 21), which is the correct axis for "we are
  more sure of this," not Coverage, which answers "how much of the
  methodology could be evaluated at all."

**Coverage = weighted-dimension-coverage, computed identically at
dimension/pillar/overall levels** — the same architecture V2.1 already
uses, with the fix being entirely in what counts as "scorable" (Part 7's
mechanical, typed-evidence-count gates) rather than a free judgment
call, and the explicit non-redundancy rule above formalizing something
V2.1 left implicit.

---

## Part 21 — Confidence (Redesigned)

**Factors, and how they aggregate — deterministic where possible, per
this Part's own instruction:**

- **Per observation:** `extraction_confidence` (LOW/MEDIUM/HIGH, set at
  extraction time based on source clarity) × provenance grade (Part 6)
  → a deterministic per-observation confidence tier, not a count of
  evidence bullets.
- **Per dimension:** the LOWEST confidence tier among the observations
  actually cited in that dimension's classification (a chain-is-as-
  strong-as-its-weakest-link rule, not an average) — chosen because
  averaging could let one strong source mask several weak ones
  supporting the same conclusion, re-introducing exactly the "more
  sources = more confidence regardless of quality" bias Part 20 already
  rejected for Coverage.
- **Per pillar:** weighted average of scored dimensions' confidence
  tiers, using the same dimension weights as the score aggregation
  itself (structural consistency with how Strength and Coverage both
  already weight by configured dimension weight).
- **Overall:** weighted average across scored pillars, same weights as
  SPS aggregation.

**Deterministic given the same accepted evidence? Yes** — every step
above is a lookup/aggregation over already-typed, already-graded fields,
with no free LLM judgment anywhere in the confidence computation itself
(the only LLM involvement anywhere upstream is `extraction_confidence`,
set once at extraction time and then treated as a fixed input, not
re-judged during aggregation).

---

## Part 22 — Publishability Gates (Redesigned)

Replacing 10.8D's four-gate design (Part 1's critique) with a
two-gate design:

1. **Structural minimum:** ≥2 scorable dimensions per published pillar
   AND ≥4 of 6 pillars individually publishable AND at least 2 of
   {Market, Team, Product} among those publishable pillars (revised
   from "Market AND Team," Part 1).
2. **Overall coverage floor:** a single coverage percentage,
   **CALIBRATION REQUIRED** for its exact value (10.8D's 35% is
   explicitly not adopted), whose only fixed property for now is that
   it must be set high enough to block the exact "SPS 94 / Coverage 12%"
   case Part 22's own prompt worries about, and validated against that
   specific synthetic case (Part 30, Test 15: "nearly no evidence")
   before being finalized.

**Confidence is explicitly removed as a separate hard gate** (Part 1) —
a Low-confidence result that clears both gates above is **published**,
with Confidence displayed prominently at Low, consistent with 10.8D's
own "report honestly, don't distort" philosophy for confidence
elsewhere.

**Does this create false withholding / compression / stage / sector /
famous-company bias?** Structural minimums (gate 1) risk **stage bias**
if applied uniformly — a genuinely early Idea-stage company may
legitimately have fewer than 4 publishable pillars through no fault of
evidence quality, simply because fewer pillars are even *applicable*
yet (Financial Health, Traction). **Mitigation, new in this pass:**
`UNAVAILABLE_NOT_APPLICABLE_FOR_STAGE` pillars (not merely thin-evidence
ones) are excluded from the "of 6" denominator entirely, not counted
against the company — an Idea-stage company might only have 4
*applicable* pillars in the first place, and clearing "4 of 4 applicable"
is a fair bar in a way "4 of 6 including two structurally inapplicable
ones" would not be. **CALIBRATION REQUIRED** on exactly which pillars
are ever legitimately "not applicable" at Idea/Pre-Seed vs. merely
"usually thin" (a meaningful distinction this document does not fully
resolve).

---

## Part 23 — Pillar Aggregation (Confirmed/Refined)

- Unavailable dimensions renormalize (unchanged, justified).
- Dimension weights remain fixed per pillar (unchanged — no evidence
  found anywhere in four phases implicating dimension-level weights
  specifically, as distinct from the pillar-level weights Part 24
  separately confirms).
- **Pillar coverage does NOT mathematically affect Strength** — kept as
  a strictly separate, parallel output (Pillar Completeness, 10.8D's
  term, retained), never multiplied into the score. This is a direct,
  deliberate rejection of any "coverage-discounted strength" formula —
  Non-Negotiable Principle 6 (adding evidence must not automatically
  raise or lower SPS through a coverage side-channel) is best protected
  by keeping the two mathematically independent, not by finding a clever
  discount formula.
- **Confidence does NOT mathematically affect Strength either** —
  consistent with Part 12's earlier reversal of V2.1's confidence caps;
  Confidence is reported, never multiplied in.
- **Minimum evidence for a pillar to publish:** ≥2 scorable dimensions
  (Part 22), independent of the coverage-percentage question, which
  operates at the overall-SPS level (Part 24), not re-litigated per
  pillar.

---

## Part 24 — Overall SPS Aggregation (Confirmed/Refined)

Pillar weights **unchanged**: Market 20% / Team 20% / Product 20% /
Execution 15% / Traction 15% / Financial Health 10%. No phase to date
has produced evidence implicating them, and this phase's own
non-negotiable rule (every change must be justified, not merely
"different") gives no basis to touch them now.

- **Unavailable pillars:** renormalize over publishable pillars
  (Part 22's gates already determine which pillars qualify).
- **When SPS is withheld:** Part 22's two gates, both must pass.
- **Provisional SPS:** **rejected as a concept.** A "provisional" number
  invites exactly the same "SPS 94 / low confidence" misreading a fully
  withheld state avoids — if the gates don't pass, no SPS is shown, only
  the honest per-pillar Strength/Completeness data that does exist
  (10.8D's own Part 15 recommendation, reaffirmed here after
  re-examination).
- **Critical pillars:** at least 2 of {Market, Team, Product} (Part 22,
  revised from 10.8D's Market+Team-specifically rule).

---

## Part 25 — High-Score Gates: Necessary, Redundant, or Harmful?

**Conclusion: 10.8D's explicit multi-pillar 80+/85+/90+/95+ gates are
REDUNDANT and carry real risk of creating a new artificial ceiling —
REMOVED.**

Reasoning, directly engaging this Part's challenge: once every
dimension's positive classifications require specific, named, cited
evidence (Parts 9-14) and the 9-10 band specifically requires the
strongest classification label (itself gated on the most specific
evidence, e.g. `DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME`, `COMPREHENSIVE`),
a company cannot reach a high weighted-average SPS without **already**
having genuine strength spread across multiple pillars — that is simply
what a weighted average of six independently-gated numbers requires
mathematically. Adding a SEPARATE explicit rule ("no pillar below 7.0
for 90+") on top of that solves a problem the per-dimension design
already solves, while introducing a real failure mode: a company that
is genuinely exceptional in five pillars but has one honestly-thin
(not negative, just `UNAVAILABLE` or renormalized-away) pillar could be
blocked from 90+ by a rule checking "no pillar below 7.0" when that
pillar isn't even contributing a low number — it's simply not present.
**The one thing 10.8D's high-score gates were actually protecting
against (a single-outlier-pillar-driven high score with weak overall
coverage) is already fully handled by Part 22's coverage/structural
gates** — a genuinely single-pillar-driven high number would necessarily
come with low coverage and would already fail publishability. No
additional score-level gate is needed once the publishability gate and
the per-dimension evidence bar are both doing their jobs.

---

## Part 26 — Low-Score Behavior: Confirmed Natural

**Conclusion: 10.8D's explicit "<40 requires negative evidence in
specific named pillars" gate is REMOVED (Part 1); no replacement gate
is added.**

Per Part 17's negative-evidence taxonomy, any dimension's negative
signal maps directly to a low band (0-4) for that dimension, and the
normal weighted-average pillar/SPS aggregation (unchanged mechanism,
Part 23-24) naturally produces a low overall SPS when enough weighted
dimension-weight is occupied by low-banded scores — **no artificial
"number of negative flags" threshold is needed or added.** This
directly satisfies Part 26's own test: deterministic per-dimension
scoring, once evidence is genuinely weak or negative, produces low SPS
through ordinary arithmetic, the same way it produces high SPS through
ordinary arithmetic when evidence is genuinely strong (Part 25) — the
methodology does not need bespoke gates at either extreme once the
per-dimension design itself is sound.

---

## Part 32 — Explanation Trace Architecture

Confirmed and generalized from 10.8D's single worked example — every
dimension's trace is a mechanical concatenation of:

```
DIMENSION: <name>
ACCEPTED EVIDENCE: <list of cited CanonicalObservation excerpts + sources>
CLASSIFICATION: <the taxonomy label assigned, or "N/A -- quantitative">
RULE: <versioned rule ID, e.g. TEAM.FOUNDER_MARKET_FIT.DIRECT_WITH_OUTCOME.V1>
SCORE: <the resulting number>
CONFIDENCE: <Low/Medium/High, per Part 21>
WHY: <a template sentence generated by filling the rule's own
       human-readable description with the specific cited evidence --
       never a second free-form LLM call>
```

**No second LLM call is required anywhere in this trace** — every field
is either a direct copy of already-typed data or a template string keyed
to the specific `rule_triggered` ID, which is itself a fixed, versioned
string defined once per rule (Part 33), not generated per-analysis.

---

## Part 33 — Rule Versioning

```
SPS_V3                                    -- top-level methodology version
  TEAM.FOUNDER_MARKET_FIT.V1               -- one dimension's rule version
    .NO_RELEVANT_EXPERIENCE                -- (implicit -- maps to UNAVAILABLE,
                                               not itself versioned separately)
    .ADJACENT_EXPERIENCE.BAND_V1            -- one classification's score-band
                                               version, independently bumpable
    .DIRECT_EXPERIENCE.BAND_V1
    .DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME.BAND_V1
  TRACTION.CURRENT_SCALE.SEED.V1            -- stage-specific threshold version
  TRACTION.CURRENT_SCALE.SERIES_A.V1
  ...
```

**Tracking rule changes:** every dimension's taxonomy-to-band mapping
and every stage table entry is independently versioned (`.V1`, `.V2`,
...) — calibrating one dimension's thresholds (Part 27's plan) does not
require bumping `SPS_V3`'s own top-level version unless the change is
methodologically material (a new dimension, a changed taxonomy, a
changed aggregation rule) — mirroring the exact discipline already
established between `METHODOLOGY_VERSION` and finer-grained versions
like `ANCHOR_REGISTRY_VERSION` in the current codebase (Phase 10.8B's
own versioning practice, reused here, not invented new).

**Reproducibility guarantee:** a stored analysis records every rule ID
actually triggered, at its specific version, alongside
`methodology_version` — re-running the identical frozen canonical
evidence through a LATER rule version is expected to produce a
different score and is not a reproducibility violation; re-running it
through the SAME rule versions must produce the identical score, and
this is fully testable as a deterministic unit test per rule (Part 16's
architecture, extended).

---

## Part 34 — Category C Final Decision

**Strategic Execution: MOVE TO B.** See worked example 4, Part 7, for
the full decomposition (four boolean-with-evidence fields: wedge_named,
expansion_logic_stated, competitive_response_named,
capital_allocation_stated). On rechallenge, 10.8D's stated reason for
keeping this dimension qualitative ("resists decomposition into
independent facts without losing holistic reasoning") did not survive
actually attempting the decomposition — the four fields above capture
the concrete, checkable substance of "is this a coherent strategy"
without requiring a holistic judgment call, at the honest cost (stated
in the worked example's Known Limitations) of losing some genuinely
holistic narrative-coherence signal a human reviewer might apply. This
cost is accepted as the price of eliminating free-form LLM numeric
scoring entirely, consistent with Part 34's own instruction to attempt
elimination first and only retain C with a compelling documented reason
— no dimension in the final V3 set retains a compelling enough reason.

**Result: zero Category C dimensions remain in V3.** Direct LLM
numerical scoring is eliminated for all 26 final dimensions (Part 36).

---

## Part 35 — Category D Final Decisions

| Dimension | Decision | Reasoning |
|---|---|---|
| Usability | **REDESIGN** → renamed "Product Accessibility" (Part 11) | Original concept (onboarding/activation friction) is genuinely unassessable from public sources — confirmed by the codebase's own pre-existing `AMBIGUOUS_UNAVAILABLE_DIMENSIONS` flag. Redesigned around genuinely public-observable proxies rather than removed outright, preserving the pillar's dimension count. |
| Operational Execution | **SPLIT** | Quantitative sub-claims (the exact shape that produced fabrication in Phase 10.8B's audit) move entirely to Financial Health's Capital Efficiency evaluator (Deterministic, fail-closed). Qualitative sub-claims (hiring discipline, process, cadence) survive in Execution, renamed "Operating Discipline" (Category B). |
| Burn Efficiency / Runway | **MERGE** into "Capital Efficiency" (Financial Health) | Both dimensions required the same underlying cash/burn facts and had overlapping evidence needs — Phase 10.8B's full-cohort audit found fabrication concentrated exactly here (18/25 companies). Merging into one Deterministic evaluator, fed only by real typed `CashObservation`/`BurnObservation`/`RevenueObservation` instances, removes the free-LLM-narration shape that invited fabrication, and directly resolves the Part-18 double-counting risk between what were previously two separately-scored but evidentially-overlapping dimensions. |

None of the three Category D dimensions are left as vague placeholders
— each has a specific, actionable resolution.

---

## Part 36 — V3 Canonical Dimension Matrix (Final)

| Pillar | Dimension | Pillar weight | Dimension weight (provisional — CALIBRATION REQUIRED for final values) | Category | Public/Private assessability | Stage applicability | Min. evidence | Score mechanism |
|---|---|---|---|---|---|---|---|---|
| Market | Market Size | 20% | 0.25* | B | Public | All stages, bar varies | 1 taxonomy field | Classification → band |
| Market | Market Growth | 20% | 0.20* | B | Public | All stages | 1 field | Classification → band |
| Market | Market Timing | 20% | 0.20* | B | Public | All stages | 1 field | Classification → band |
| Market | Competitive Intensity | 20% | 0.15* | B | Public | Bar rises with stage | 1 field | Classification → band |
| Market | Customer Demand | 20% | 0.20* | B | Inferred/Public mix | Lifecycle-gated | Existing mechanism | Classification → band |
| Team | Founder-Market Fit | 20% | 0.25* | B | Public | Heaviest at Pre-Seed/Seed | 1 typed observation | Classification → band |
| Team | Technical Capability | 20% | 0.20* | B | Inferred | Bar rises with stage | 1 field | Classification → band |
| Team | Business Capability | 20% | 0.20* | B | Inferred | Bar rises with stage | 1 field | Classification → band |
| Team | Leadership | 20% | 0.20* | B | Inferred | Stage-conditioned bar | 1 field | Classification → band |
| Team | Execution Track Record (Team) | 20% | 0.15* | B | Inferred | Stage-conditioned | 1 field | Classification → band |
| Product | Customer Value | 20% | 0.25* | B | Inferred | Bar rises with stage | 1 field | Classification → band |
| Product | Differentiation | 20% | 0.20* | B | Public | All stages | 1 field | Classification → band |
| Product | Product Accessibility (redesigned) | 20% | 0.15* | B | Public | Business-model-dependent | 1 field | Classification → band |
| Product | Defensibility | 20% | 0.20* | B | Inferred | All stages | 1 field | Classification → band |
| Product | Adoption Potential | 20% | 0.20* | B | Inferred | Bar rises with stage | 1 field | Classification → band |
| Execution | Go-to-Market Execution | 15% | 0.33* | B | Inferred | Bar rises sharply with stage | 1 field | Classification → band |
| Execution | Product Execution | 15% | 0.33* | B | Inferred | Bar rises with stage | 1 field | Classification → band |
| Execution | Operating Discipline (split) | 15% | 0.17* | B | Inferred, informal OK pre-stage | Pre-Seed lenient, Growth expected | 1 field | Classification → band |
| Execution | Strategic Execution (moved from C) | 15% | 0.17* | B | Inferred | All stages | 1 field | Classification → band |
| Traction | Current Scale (redesigned) | 15% | 0.20* | A | Public | Stage-relative bands | 1 dated observation | Deterministic threshold |
| Traction | Growth Trajectory (redesigned) | 15% | 0.25* | A | Public | Stage-relative | 2 dated observations | Deterministic formula |
| Traction | Customer Adoption (redesigned) | 15% | 0.20* | B | Public | Stage-relative | 1 field | Classification → band |
| Traction | Retention/Engagement (redesigned) | 15% | 0.20* | A/B hybrid | Public/Inferred | Largely stage-invariant | 1 observation or field | Deterministic or classification |
| Traction | Commercial Validation (redesigned) | 15% | 0.15* | B | Public | Contract-size bar rises with stage | 1 field | Classification → band |
| Financial Health | Revenue Quality | 10% | 0.35* | B | Sometimes public | All stages | 1 field | Classification → band |
| Financial Health | Unit Economics | 10% | 0.30* | A (unchanged) | Primarily private | All stages | 2 real inputs | Deterministic formula |
| Financial Health | Capital Efficiency (merged) | 10% | 0.35* | A | Primarily private | Later-stage bar rises | 2 real inputs or 1 direct statement | Deterministic formula |

*Dimension weights marked with an asterisk are placeholders preserving
relative proportions from V2.1 where a direct analog exists and
splitting evenly where dimensions were split/merged — **all dimension-
level weights are CALIBRATION REQUIRED**, distinct from the
pillar-level weights (Part 24), which are confirmed unchanged.

**Total: 26 dimensions** (down from 28): Market 5 (unchanged), Team 5
(unchanged), Product 5 (unchanged count, 1 redesigned), Execution 4
(unchanged count, 1 split + 1 moved from C — net effect is Operational
Execution's qualitative half becomes Operating Discipline, its
quantitative half leaves the pillar entirely), Traction 5 (unchanged
count, full redesign), Financial Health 3 (down from 4 — Burn Efficiency
and Runway merged into one).

---

## Part 37 — Migration Consequences

| Change type | Dimensions |
|---|---|
| Unchanged (name and concept) | Market Size, Market Growth, Market Timing, Competitive Intensity, Customer Demand, Founder-Market Fit, Technical Capability, Business Capability, Leadership, Customer Value, Differentiation, Defensibility, Adoption Potential, Go-to-Market Execution, Product Execution, Unit Economics (16 of 26) |
| Renamed + redesigned | Usability → Product Accessibility; Execution Track Record (Team, unchanged name, clarified scope per Part 18) |
| Redesigned (same name, new evidence model) | Customer Growth → Current Scale, Revenue Growth → Growth Trajectory, Retention → Retention/Engagement, Growth Velocity → (absorbed into Growth Trajectory), Engagement → (absorbed into Customer Adoption / Retention-Engagement) — Traction's full 5-dimension redesign |
| Split | Operational Execution → Operating Discipline (Execution) + folded into Capital Efficiency (Financial Health) |
| Merged | Burn Efficiency + Runway → Capital Efficiency |
| Moved (Category C → B) | Strategic Execution |
| Removed | None outright — every V2.1 dimension maps to a successor, even where heavily redesigned |
| New | Product Accessibility (successor to Usability, materially different evidence model), Customer Adoption / Commercial Validation (successor concepts to old Traction dimensions, not 1:1 renames) |

**Impact by component (design only, no implementation performed):**

- **`SIEMethodologyAnalysis`, `SIEContext`:** unchanged outer shape,
  confirmed reusable (10.8D's assessment stands).
- **`PillarAnalysis`, `Subscore` → `DimensionResult`:** unchanged from
  10.8D's assessment — this remains the single largest breaking model
  change, now additionally touching Traction's full dimension-name
  change (any code reading `Subscore.name == "Revenue Growth"` etc. by
  string must be updated, not just the score-producing logic).
- **Historical JSONB:** additive-only, confirmed (10.8D's assessment
  stands) — old dimension names remain frozen inside old stored
  analyses' JSONB exactly as recorded; nothing is migrated.
- **API:** response models must add the renamed/restructured Traction
  and Financial Health dimension names — any frontend code keying off
  specific dimension name strings (confirmed not present in `dashboard/`
  as of this phase, per Phase 10.8B's own zero-dashboard-diff
  verification) would need updating if it existed.
- **Rankings, Startup Profile, Compare, Investor Workspace, SPS
  History, Founder Workspace:** unaffected at the aggregate-SPS/pillar-
  score level (10.8D's assessment stands); any UI specifically labeling
  "Burn Efficiency" or "Usability" by name would need updating to the
  new dimension names — flagged as a real but bounded, enumerable
  UI-copy update, not an architectural risk.

---

## Part 38 — Implementation Readiness Review

| Readiness criterion | Status |
|---|---|
| Canonical dimensions defined | **Yes** — 26, Part 36 |
| Evidence types defined | **Yes**, at the pattern level (Part 4) — the full field-by-field spec for every one of the ~15+ typed observation classes is not exhaustively written here (four are fully specified, the rest follow the demonstrated pattern) |
| Classifications defined | **Yes**, at the pattern level — 4 dimensions fully specified (Part 7), 22 specified at the summary-table level (Parts 9-14) |
| Deterministic mapping architecture defined | **Yes** (Part 19) — architecture yes, specific numeric bands explicitly no (CALIBRATION REQUIRED throughout) |
| Unknown semantics defined | **Yes**, unchanged from 10.8D, reaffirmed |
| Aggregation architecture defined | **Yes** (Parts 23-24), revised from 10.8D |
| Confidence architecture defined | **Yes** (Part 21), revised from 10.8D |
| Coverage architecture defined | **Yes** (Part 20), revised from 10.8D |
| Calibration-required items explicitly identified | **Yes** — every numeric threshold in this document is explicitly flagged, none hidden |
| No unresolved direct LLM numerical scoring | **Yes** — Category C eliminated (Part 34) |
| No known structural evidence ceilings created accidentally | **Not fully verifiable without implementation** — Traction/Financial-Health redesigns are believed to relieve the V2.1 ceiling (Part 13-14 reasoning) but this is an untested hypothesis, not a proven result (10.8D's own Part 30 flagged this same honest uncertainty) |

**Overall: NOT READY for engine implementation.** Every architectural
question this phase set out to answer has an answer; every numeric
threshold remains explicitly unresolved (CALIBRATION REQUIRED), and per
this phase's own non-negotiable rule, pretending otherwise would be
exactly the "hardcoded vibes" failure mode this phase exists to prevent.
The companion calibration plan (`SPS_V3_CALIBRATION_PLAN.md`) is the
necessary next step before engineering begins, not implementation
itself.

---

*End of rulebook. See `SPS_V3_CALIBRATION_PLAN.md` for calibration
philosophy, dataset design, outcome-data policy, and the 15 synthetic
rule-stress-tests.*
