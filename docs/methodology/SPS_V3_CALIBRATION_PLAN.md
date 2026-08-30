# SPS V3 Calibration Plan

Phase 10.8E companion document. **Design only — no calibration is
performed here, no company is run, no threshold is finalized.** This
document defines what calibration means for V3, what data should
inform it, how to test the rulebook (`SPS_V3_RULEBOOK.md`) against
adversarial synthetic cases before any real evidence is involved, and
what a healthy score distribution should look like — without ever
targeting a distribution shape directly.

---

## Part 27 — Calibration Philosophy

**Calibration is NOT:** running real companies and adjusting thresholds
until a specific company reaches a specific expected number ("Stripe
should be 90, adjust until Stripe is 90"). This is explicitly the
failure mode Phase 10.8's own directive warned against from the start,
and it remains prohibited for V3.

**Calibration SHOULD determine:**
- Whether each stage table's thresholds (Rulebook Part 15) represent
  *meaningfully different* startup performance, not arbitrary cut
  points — e.g. is the gap between `SEED.ordinary` and `SEED.strong`
  for Current Scale large enough that a real reviewer would call the
  two profiles genuinely different companies, or is it noise-sized?
- Whether each taxonomy's classification→band mapping (Rulebook Part 19)
  produces *useful discrimination* — do `ADJACENT_EXPERIENCE` and
  `DIRECT_EXPERIENCE` companies, in a real sample, actually look
  different in ways beyond the taxonomy label itself?
- Whether the 0-100 scale is *usable* — not whether it produces a
  specific distribution, but whether both tails are reachable in
  principle and, once real data exists, whether they are reached by
  at least some real companies with genuinely extreme evidence.
- Whether evidence rules are *fair* — do the same taxonomy fields
  produce comparable outcomes for comparable real companies regardless
  of stage, sector, or public visibility (the evidence-abundance-bias
  question, tested explicitly in Part 30 below)?
- Whether adjacent score bands (Rulebook's band semantics, inherited
  from 10.8D Part "Definition of SPS") correspond to *materially
  different startup profiles* a human reviewer would also distinguish.

**Acceptable calibration inputs**, ranked by how much they can be
trusted without introducing the exact bias this whole project fights:

1. Synthetic boundary fixtures (Part 30) — zero real-world bias risk,
   used first, always.
2. Rule-internal consistency checks (does a `MULTIPLE_SIGNALS`
   classification always score above `SINGLE_SIGNAL` across every
   dimension using that pattern) — mechanical, cheap, no bias risk.
3. The existing historical/frozen corpus (Phase 10.8's 25 companies,
   Phase 10.8B's 6 diagnostics, this phase's Stripe/SpaceX pair) —
   used only as **regression/sanity data**, never as the basis for
   picking a threshold, because every one of these companies has
   already shaped design decisions and using them to also set numbers
   would be circular.
4. A genuinely new, independently-selected blind cohort (Phase 10.8C,
   still pending) — the first data actually eligible to inform real
   threshold values, precisely because it was not used to build the
   rules being tested.
5. Stage-specific and sector-specific sub-cohorts of #4, once #4 exists
   in enough volume.
6. Cautious, qualitative use of known outcomes (Part 29) — sanity-
   checking only, never threshold-fitting.
7. Expert review of explanation traces (Rulebook Part 32) — checking
   reasoning quality, not number-matching.
8. Distribution and sensitivity analysis on whatever real results
   accumulate from #4-5 — descriptive, and explicitly barred from
   becoming threshold-shopping for a prettier curve (Part 31 below).

---

## Part 28 — Calibration Dataset Design

**Categories, and the specific bias each must guard against:**

| Category | Purpose | Bias risk to actively guard against |
|---|---|---|
| Synthetic boundary fixtures | Test rule *shape* before any real data | None inherent — but a fixture designer's own assumptions about what "strong" looks like can smuggle in the same biases as real data; fixtures should be reviewed by more than one person/pass |
| Expert-labeled cases | Ground-truth check on whether taxonomy labels match human judgment | Expert's own sector/stage familiarity biases — use multiple experts across different backgrounds, never one reviewer's opinion as ground truth |
| Historical startup snapshots (point-in-time, not current-state) | Tests whether the methodology would have judged a company reasonably at the time, without hindsight | **Hindsight leakage** — a snapshot must be genuinely reconstructed from what was publicly known AT THAT TIME, not filtered through what is now known about the outcome; this is materially harder than it sounds and should not be attempted casually |
| Failed startups | Tests whether genuine negative evidence produces low scores | **Survivorship-adjacent bias in reverse** — failed companies are often over-represented in post-mortem content (a failed company that wrote a public "lessons learned" post has MORE public evidence about its failure than an equally-failed company that quietly shut down, which would bias the sample toward companies that failed loudly) |
| Successful startups | Tests whether genuine strength produces high scores | **Survivorship bias** (the classic form) and evidence-abundance bias compound here — successful companies are also the most publicly documented; the dataset must include successful-but-quiet companies, not just famous ones, or this category alone will re-teach the exact bias V3 exists to remove |
| Stage-specific cohorts | Calibrates each stage table independently | Must have enough companies per stage to avoid one company's idiosyncrasies defining an entire stage's thresholds |
| Sector-specific cohorts | Tests whether taxonomy fields generalize across business models (SaaS vs. marketplace vs. hardware vs. deep-tech) | A taxonomy field designed with SaaS in mind (e.g. "recurring revenue claimed") may not transfer cleanly to hardware or deep-tech — sector cohorts specifically stress-test this |
| Private founder-provided cases | Tests the Financial Health/Traction dimensions once real private data exists (design only per Phase 10.8D Part 23 — no ingestion built yet) | Founder-provided data is self-reported by definition — provenance grading (Rulebook Part 6) must not simply trust it more because it's more detailed |
| Public-company-like mature cases | Tests the Growth/Series B+ stage tables where public disclosure is richest | Risk of over-fitting stage tables to public-company disclosure norms that don't reflect genuinely private late-stage companies |

**Explicit anti-bias construction rules for the eventual dataset:**
- No category above may be built by searching for companies that
  produce a *desired* score outcome — every company must be selected
  on criteria independent of what it would score (company size, sector,
  founding year, public-visibility tier), mirroring exactly the
  ex-ante-selection discipline already established in Phase 10.8's own
  cohort-freezing protocol.
- Obscure-but-strong and famous-but-mediocre pairs (Part 30, Tests 1-2)
  should be deliberately over-represented relative to their real-world
  frequency, specifically because they are the cases most likely to
  expose evidence-abundance bias, and a randomly-sampled cohort would
  under-test exactly this failure mode.
- **This dataset is not built in this phase.** This section is a
  specification for what Phase 10.8C (or a dedicated calibration phase)
  should assemble, not a deliverable of 10.8E.

---

## Part 29 — Outcome Data

**Should actual startup outcomes (fundraising, revenue growth,
survival, exit, IPO, shutdown) calibrate SPS? Cautiously, and only for
validation, never for threshold-fitting.**

The critical distinction, restated because it is easy to blur in
practice: SPS is defined (10.8D, reaffirmed) as *demonstrated strength
relative to stage*, not a probability of any outcome. Outcome data can
legitimately answer "does the methodology's notion of 'strong evidence'
correlate at all with real-world trajectories" as a sanity check — if
companies the methodology confidently scores as showing severe,
specific negative evidence (Rulebook Part 17) turn out to overwhelmingly
survive and thrive, that is a signal something in the negative-evidence
taxonomy is miscalibrated or measuring the wrong thing. But outcome data
must **never** be used to reverse-engineer score thresholds toward
"whatever number best predicts success," because:

1. That would silently convert SPS into a success-probability model,
   directly violating Non-Negotiable Principle 7 (Phase 10.8D) without
   ever formally deciding to.
2. Outcomes are confounded by countless factors SIE cannot and should
   not try to observe (market timing luck, macro conditions, individual
   investor decisions) — fitting to them would launder those confounds
   into the methodology as if they were evidence-based.
3. Outcome data is itself subject to survivorship and reporting bias
   (Part 28) at least as severe as the evidence-abundance bias this
   whole redesign targets.

**Appropriate use, concretely:** a large-sample, retrospective,
correlational check — "among companies SIE would score 80+, what
fraction later raised a subsequent round / grew revenue / are still
operating, compared to companies scored 40-59" — reported as a
descriptive validity check in a future calibration report, explicitly
labeled as correlational and non-causal, and never fed back into any
threshold as an optimization target.

---

## Part 30 — Synthetic Rule Stress Tests

Fifteen adversarial cases, reasoned through against the Rulebook's
architecture. **No thresholds are asserted as final** — each case shows
whether the *shape* of the design produces a sensible outcome, flagging
any case where it does not (used to revise the Rulebook, not papered
over).

**1. Famous company / abundant evidence / mediocre actual signals.**
Many `HIGH_QUALITY_SECONDARY`/`PRIMARY_SELF_REPORTED` observations
exist, but few populate any dimension's *positive* classification
fields (lots of press coverage about the company being well-known, not
about specific named facts the taxonomies require). **Expected
behavior:** high Coverage/Confidence (lots of sourced, clear
observations), but only ORDINARY-band classifications across most
dimensions → a mid-range SPS, correctly NOT inflated by fame alone,
because Part 20's coverage design explicitly does not reward redundant
low-signal evidence. **Risk if this fails:** if fame alone somehow
still inflates the score, the evidence-abundance-bias fix has not
worked and every taxonomy needs re-review for implicit "more sources ⇒
stronger label" logic.

**2. Obscure company / sparse evidence / genuinely strong signals.**
Few sources exist, but the ones that do contain specific, named,
high-provenance facts (a named enterprise contract, a named prior-exit
founder). **Expected behavior:** lower Coverage (fewer dimensions
resolve at all) but the dimensions that DO resolve hit STRONG/
EXCEPTIONAL bands with HIGH confidence — SPS may be withheld entirely
if the structural gates (Rulebook Part 22) aren't met, or published at
a genuinely high per-pillar Strength with visibly lower overall
Coverage. **This is the single most important case for proving the
three-axis architecture earns its complexity** — a good design shows
"Strength: high, Coverage: low" as a legible, distinct signal, not a
muddled middling number.

**3. Pre-Seed company / no revenue / exceptional validation.**
Zero `RevenueObservation`s exist (Current Scale/Growth Trajectory
correctly `UNAVAILABLE`), but strong `CommercialContractObservation`s
(named signed pilots), `FounderExperienceObservation`s
(`DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME`), and Product/Market signals
exist. **Expected behavior:** Traction pillar renormalizes over
Customer Adoption/Commercial Validation alone (Current Scale/Growth
Trajectory excluded, not zeroed), Team/Product/Market score well,
Financial Health legitimately near-empty (small pillar weight limits
its drag) → a genuinely high SPS is reachable. **This is the case
Relaw's real V2 score (72.5) was an *unearned* version of** — the test
here is whether V3 reaches a comparably high number only when the
underlying facts are this specific, not from generic narrative.

**4. Growth-stage company / large revenue / declining sharply.**
Strong `Current Scale` (large absolute revenue) but `Growth Trajectory`
shows two dated points with a clear decline. **Expected behavior:**
Current Scale scores well; Growth Trajectory hits its negative-evidence
band (Rulebook Part 13); the pillar-level renormalization does NOT let
Current Scale's strength offset Growth Trajectory's negative signal
into a bland average — negative evidence must visibly drag the pillar
down, not merely dilute one component's positive contribution. **Risk
if this fails:** if a large absolute number can fully mask a disclosed
decline, Non-Negotiable Principle 3 (negative evidence must be able to
produce low scores) is violated.

**5. Huge market / terrible product.** Strong Market pillar
classifications, Product pillar populated entirely with negative
signals (disclosed quality issues, feature-parity admissions).
**Expected behavior:** the two pillars move independently — Market
scores high, Product scores low — and the 20%/20% weighting means
neither pillar alone determines SPS; a genuinely bad product with a
big market lands in a moderate-to-low overall range, not masked by
market size. **This directly tests that pillars are NOT allowed to
cross-subsidize each other's weaknesses**, which the architecture
should guarantee simply by keeping pillar scoring independent
(no design changes needed if true; a real risk to check once
implemented).

**6. Elite team / no traction.** Team scores very high
(`DIRECT_EXPERIENCE_WITH_PRIOR_OUTCOME`, named executive hires), all
five Traction dimensions genuinely `UNAVAILABLE_NO_EVIDENCE` (not
negative — literally nothing to observe yet, plausible for a very early
company). **Expected behavior:** Traction pillar itself may fail its
own ≥2-scorable-dimensions gate (Rulebook Part 23) and become
`UNAVAILABLE`, renormalizing out of SPS entirely — SPS computed over
the remaining 5 pillars, correctly not penalized by Traction's absence
(Non-Negotiable Principle 2), and correctly not artificially inflated
by Team's strength alone either, since Market/Product/Execution/
Financial-Health are independently assessed.

**7. Mediocre team / exceptional traction.** The inverse of #6 — real,
strong, specific `Current Scale`/`Growth Trajectory`/`Commercial
Validation` evidence, but Team dimensions resolve to `ADJACENT`/
`ORDINARY` labels only (no named prior outcomes, no named technical
background). **Expected behavior:** Traction scores high, Team scores
moderate, both real and both count — this is a legitimate, common real
profile (strong business, unremarkable-on-paper founders) the
methodology should represent honestly rather than forcing agreement
between pillars.

**8. High funding / weak unit economics.** Strong `FundingObservation`s
exist; real, disclosed `CAC`/`LTV`/margin figures show poor economics.
**Expected behavior:** Funding contributes nothing to Financial Health
directly (Rulebook Part 5's explicit "never treat funding as financial
health automatically" type-system rule) — Unit Economics/Capital
Efficiency score based on the real disclosed ratios alone, correctly
producing a LOW Financial Health score despite abundant funding. **This
is a direct, load-bearing test of Part 5's normalization rules actually
holding** — if funding leaks into Financial Health's score anywhere,
the type-system guarantee has failed in practice, not just in design.

**9. Profitable company / slow growth.** Strong Capital Efficiency
(real, disclosed low burn/high margin), Growth Trajectory shows
positive but modest growth (not negative, not exceptional).
**Expected behavior:** Financial Health scores well, Traction's Growth
Trajectory lands in an ORDINARY (not STRONG, not negative) band — a
legitimate, non-extreme result for a legitimately non-extreme profile,
demonstrating the mid-bands are actually reachable and meaningful, not
merely a dumping ground (the core critique of V2's compression).

**10. High growth / catastrophic burn.** Strong Growth Trajectory,
Capital Efficiency shows a severe-cash-constraint negative signal
(Rulebook Part 17). **Expected behavior:** Traction scores well,
Financial Health hits its low band — again, pillars must not average
each other into a falsely moderate combined signal; the point of
keeping pillars independent is exactly to preserve this kind of
internally-contradictory-but-real profile.

**11. Great product / tiny market.** Strong Product pillar, Market
Size genuinely and specifically classified as small (not merely
`NO_SIGNAL` — an actual `NAMED_SEGMENT` with a small stated size).
**Expected behavior:** Market's own taxonomy must be capable of scoring
LOW from genuine evidence of a small market, not merely `UNAVAILABLE`
from absence of size data — this tests whether Market Size's taxonomy
(Rulebook Part 9) has a real low-end, not just a NO_SIGNAL/ordinary/
strong ladder with no room for "we know this market is genuinely
small." **Flagged as a real gap to close during implementation** if the
current Market Size taxonomy (Part 9's compact table) doesn't yet have
an explicit small-market classification distinct from NO_SIGNAL.

**12. Conflicting evidence.** Two `PRIMARY_SELF_REPORTED` sources
disagree on a specific revenue figure. **Expected behavior:**
`UNAVAILABLE_CONFLICTING_EVIDENCE` (Rulebook Part 6), excluded from
scoring, surfaced distinctly in the product rather than either number
being silently chosen or averaged.

**13. Stale evidence.** All available observations are dated several
years old, no recent evidence exists. **Expected behavior:** not
explicitly designed in the Rulebook as written — **flagged as an open
gap.** `as_of_date` is captured on every observation type (Part 4), but
no dimension's rulebook currently specifies a recency requirement or
staleness penalty. **CALIBRATION REQUIRED** determination needed:
should stale evidence reduce confidence (treated as a weaker source),
become `UNAVAILABLE` past some age threshold, or remain valid
indefinitely for facts that don't meaningfully change (e.g. a founder's
prior-company history doesn't go stale the way a revenue figure does)?
This is a genuine open question this stress test surfaced, not a solved
case — added to Part 40's remaining-open-questions list.

**14. Founder self-report conflicting with external evidence.** A
`PRIMARY_SELF_REPORTED` founder claim disagrees with a
`HIGH_QUALITY_SECONDARY` independent source. **Expected behavior**:
per Rulebook Part 6's provenance-grade conflict rule, the higher grade
(here, the independent secondary source, if it is genuinely
higher-quality than self-report) is used — but this requires an explicit
ranking between `PRIMARY_SELF_REPORTED` and `HIGH_QUALITY_SECONDARY`
that Part 6's list order does not fully settle (self-reported is listed
above secondary estimate but the relative rank against *high-quality*
secondary is ambiguous). **Flagged as an open gap** — Part 6 needs a
tie-breaking rule for this specific pair, not yet fully specified.

**15. Nearly no evidence.** A company with almost nothing publicly
findable — one or two vague, generic observations across all six
pillars. **Expected behavior:** this is the exact case the
publishability gates (Rulebook Part 22) exist for — the structural
minimum (≥2 scorable dimensions per pillar, ≥4/6 pillars publishable,
≥2 of {Market,Team,Product}) should fail immediately, and the overall-
coverage floor (still CALIBRATION REQUIRED for its exact value, Part 22)
should be validated specifically against a case shaped like this one
before that threshold is finalized — this is the concrete test case
Part 22 itself names as the validation target for that still-undecided
number.

**Summary of gaps this stress-testing surfaced** (not fixed here, fed
into Part 40): no explicit recency/staleness rule (Test 13); an
underspecified provenance tie-break between self-reported and
high-quality-secondary sources (Test 14); Market Size's taxonomy may
need an explicit small-market classification, not just NO_SIGNAL vs.
ordinary/strong (Test 11).

---

## Part 31 — Score Distribution Principles

**Explicitly not a target distribution.** No specific percentage of
companies is required to land in any band. Instead, a healthy V3
result set should exhibit these *properties*, checked descriptively
once real data exists:

- **Full scale mechanically reachable:** at least some real companies
  in a sufficiently large, diverse sample should reach both the 90+ and
  <20 bands, given sufficiently extreme genuine evidence — absence of
  ANY company ever reaching either tail across a large, diverse sample
  would itself be evidence of a structural ceiling/floor problem
  (exactly the finding that motivated this entire redesign), independent
  of what the "right" percentage is.
- **Strong and weak cases distinguishable:** two companies a human
  reviewer would clearly rank differently should not, absent a
  Category-A/B design flaw, land within a point or two of each other —
  measurable via the same pairwise-dominance/rank-correlation methods
  Phase 10.8's own validation already established (`app/calibration/
  validation_2026_08/analyze_results.py`'s `pairwise_dominance` and
  `spearman_rank_correlation` functions are directly reusable for a
  future V3 cohort, not reinvented).
- **No automatic mid-band clustering:** the specific, diagnosable
  failure mode this entire multi-phase investigation exists to fix —
  checked via per-dimension and per-pillar standard-deviation/range
  diagnostics, exactly as Phase 10.8A's audit already demonstrated
  (e.g. the finding that Execution's V2.1 stdev was 0.31 with 100%
  evidence coverage, proving the compression was a scoring-design
  problem, not an evidence problem — the same diagnostic technique
  applies unchanged to a future V3 cohort).
- **Sparse evidence produces withholding, not artificial averaging:**
  checked by confirming the rate at which the publishability gates
  (Rulebook Part 22) trigger correlates with genuinely low-evidence
  real companies, not with any particular sector/stage disproportionately.
- **Extreme scores require extreme evidence:** checked qualitatively by
  sampling every company that reaches 90+ or falls below 20 in a future
  cohort and manually confirming each one's explanation trace
  (Rulebook Part 32) actually shows the kind of specific, named,
  high-provenance evidence the design intends — not merely confirming
  the number, confirming the *reasoning* is defensible, which is the
  same "explainability" bar this entire redesign was built around.

**Explicit prohibition, restated once more because it is the single
easiest principle to violate under schedule pressure:** if a future
real cohort's distribution looks "wrong" in some way, the correct
response is to re-examine the specific rules that produced it (does a
taxonomy field's inclusion criteria need adjustment, does a stage
threshold need recalibration against more data) — never to adjust a
threshold merely to move the aggregate shape closer to some assumed
"healthy-looking" curve.

---

*End of calibration plan. Together with `SPS_V3_RULEBOOK.md`, this
completes Phase 10.8E's design deliverables. No calibration, no
implementation, and no real-company run has been performed by either
document.*
