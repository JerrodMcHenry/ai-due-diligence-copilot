# SPS V3 Real-World Acceptance Test

A read-only test. No production code, methodology, weights, thresholds,
evidence rules, or prompts were modified in this pass. Nothing was
committed, deployed, or written to the production database — every run
below called `run_due_diligence()` directly, in-process, with
`SPS_ENGINE_VERSION=v3`, bypassing persistence entirely. Full raw outputs
are preserved locally (untracked) under
`docs/validation/sps_v3_real_world_acceptance_raw/`.

See `docs/validation/SPS_V3_REAL_WORLD_ACCEPTANCE_EX_ANTE.md` for the
frozen, pre-results company selection record.

## 1. Ex-ante company set

| # | Category | Company | Stage |
|---|---|---|---|
| A | Elite / evidence-rich tech | Palantir Technologies | Late/public |
| B | Elite / evidence-rich, different model | Anduril Industries | Growth/late, private |
| C | Strong, less famous | Checkr | Growth |
| D | Ordinary / mixed | Zapier | Growth |
| E | Distressed / failed | Zume | Defunct (shut down June 2023) |
| F | Early-stage | Lovable | Early/Series A-ish |
| G | Sparse public evidence | Circlemind | Seed ($2M, June 2025) |

## 2. Why each was selected

See the ex-ante document for the full rationale; in short, all seven were
chosen to be real, verifiable, and outside both the Phase 10.8F
forbidden-fragments list and the Phase 10.8H/I 31-company calibration
roster — i.e., none were used to design or tune SPS V3.

## 3-7. Assessment state / SPS / Coverage / Confidence / Pillar results

| Company | State | SPS | Coverage | Confidence | Publishable pillars |
|---|---|---|---|---|---|
| A Palantir | INSUFFICIENT | null | 9.0% | Medium | none (Team 20%, Execution 33% -- both below the 40% pillar floor) |
| B Anduril | INSUFFICIENT | null | 0.0% | Low | none |
| C Checkr | INSUFFICIENT | null | 0.0% | Low | none |
| D Zapier | INSUFFICIENT | null | 0.0% | Low | none |
| E Zume | INSUFFICIENT | null | 0.0% | Low | none |
| F Lovable | LIMITED | null | 20.5% | Medium | Execution (50% coverage, Strength 8.14) |
| G Circlemind | LIMITED | null | 11.5% | Medium | Execution (50% coverage, Strength 6.82) |

Zero of the seven reached SUFFICIENT. This is consistent with, and
explained by, the findings in Sections 8-10 below — it is a production
**adapter** coverage limitation, not a defect in the deterministic
scoring engine, and Part 21's own acceptance criteria explicitly say
this alone is not a failure signal.

## 8. Evidence correctness findings

Classified per company using the taxonomy: ACQUISITION FAILURE /
GROUNDING FAILURE / CLASSIFICATION FAILURE / DUPLICATION FAILURE / NO
MATERIAL EVIDENCE PROBLEM.

**A. Palantir -- CLASSIFICATION FAILURE (confirmed, concrete).** V2.1's
own research genuinely acquired rich, specific, real evidence (121% YoY
commercial revenue growth, 1,479 customers, named competitors
Databricks/Splunk/Tableau, named products Gotham/Foundry) -- but nearly
all of it was marked `Inferred`, not `Observed`, by V2.1's own
evidence-status classifier (a V2.1 behavior, out of scope to change
here). Only two V2.1 subscores were `Observed` company-wide
(`Operational Execution`, `Burn Efficiency`), and both are generic
boilerplate ("The company has disclosed cash balance and runway
information indicating sufficient capital...") rather than
company-specific facts. The V3 classification step then cast this
generic financial boilerplate as `ProductCapabilityObservation` with
`shipped: true` and labels like *"Sufficient runway and cash balance,"
"Positive customer growth and retention," "Healthy margins," "Successful
funding rounds"* -- none of which describe an actual shipped product
capability. This fed **Team's `technical_capability`** and
**Execution's `product_execution`**, producing COMPREHENSIVE/9.5
Strength on both from evidence that has nothing to do with either
concept. Confirmed reproducible: the same misclassification pattern
recurred independently for Lovable and Circlemind (Section 12).

**B. Anduril -- GROUNDING FAILURE (confirmed, concrete) + the same
CLASSIFICATION FAILURE pattern, on the same run.** A raw-response
capture showed the classifier correctly identified all five founders by
name and correctly extracted their real backgrounds (Palmer Luckey;
Brian Schimpf, ex-Palantir; Matt Grimm, ex-Palantir/Booz Allen Hamilton;
Trae Stephens, ex-Founders Fund, repeat founder) -- genuinely strong,
specific, real `founder_market_fit`-relevant material -- but **every one
of the six founder-experience claims omitted `verbatim_quote`**, so the
grounding firewall correctly rejected all six. Separately, the same
generic-financial-boilerplate-to-`ProductCapabilityObservation(shipped=
true)` leak seen in Palantir appeared again in Anduril's `execution`
extraction ("cash runway," "gross margins," "customer growth," "funding
round" all labeled as shipped capabilities). The deep-dump run (used for
the scored-results table above) happened to produce zero surviving
observations entirely -- a second, independent classification call on
the identical source text, showing real run-to-run classification
variance (expected and disclosed; see Section 22).

**C. Checkr -- GROUNDING FAILURE (confirmed, concrete).** V2.1 acquired
a genuinely strong, specific, correctly-classified-by-V2.1-itself
`Observed` fact: five real named competitors (HireRight, Sterling, First
Advantage, Accurate Background, GoodHire) plus real market-size/CAGR
figures. The raw V3 classification response correctly identified all
five competitors by name -- but the response was **malformed relative to
the schema**: `differentiator_named` was returned as a single top-level
list under `market` rather than a per-competitor boolean, and **no
competitor entry included `verbatim_quote`**. All five were dropped by
the firewall. Zero observations survived.

**D. Zapier -- NO MATERIAL EVIDENCE PROBLEM (of the kind this test can
attribute to V3).** Only one `Observed`-status V2.1 subscore existed for
the whole company (`Operational Execution`: a hiring-plan sentence), and
it sits in a Category-A/uncovered dimension for this v1 adapter. Zero
V3 observations is the mechanically correct outcome given that input --
not a V3 defect, but a direct consequence of V2.1's own evidence-status
classification being very conservative for this company on this run.

**E. Zume -- ACQUISITION-ADJACENT, and separately a real STRUCTURAL GAP
(Section 13).** V2.1 acquired only generic `Observed` boilerplate
(market-size figures for the packaging-industry pivot, a generic burn/
runway sentence) -- none of Zume's real, well-documented negative
history (repeated layoffs, the PFAS packaging-compliance failure, the
June 2023 shutdown) survived as `Observed`-status V2.1 evidence in this
run. Separately, and more importantly: **the production V3 adapter
(`app/ai/sps_v3_adapter.py`) contains no code path that constructs a
`NegativeSignalObservation` at all** -- confirmed by direct source
inspection (zero references to `NegativeSignalObservation` anywhere in
the file). Even if V2.1 had marked negative material `Observed`, the
current adapter has no mechanism to carry it into the deterministic
engine. See Section 13.

**F. Lovable -- CLASSIFICATION FAILURE (same pattern as A) alongside
genuinely correct extraction.** `customer_demand`/`customer_value` were
populated correctly and specifically (2.3M users, 180K paying
subscribers, a $1.8B->$6.6B->$13.3B valuation progression, all with real
verbatim quotes) -- a clean, correct extraction. But `technical_capability`
and `product_execution` again absorbed generic financial/operational
boilerplate ("Healthy cash runway and recent funding," "High gross
margins," "Operating cadence includes monthly financial reviews") as
shipped product capabilities -- the same misclassification as Palantir
and Anduril, on a third, independent company.

**G. Circlemind -- Same CLASSIFICATION FAILURE pattern (third
independent confirmation) plus correct dedup.** `technical_capability`
and `product_execution` again absorbed generic "customer acquisition
numbers and revenue growth," "raised multiple funding rounds," "hiring
sequences" as shipped capabilities. Signal deduplication is visibly
working correctly here, though: the classification_reason field reports
*"3 unique substantive signal(s) (deduplicated from 6 raw
observation(s))"* -- six near-duplicate observations correctly collapsed
to three distinct signals before scoring, per Phase 10.8G's design.

## 9. Grounding findings

The firewall itself (`_quote_is_grounded()`, a normalized substring
check against the actual source page/pillar text) behaved **correctly**
every time it was exercised: it never accepted a claim whose quote could
not be found, and it correctly rejected every claim missing a quote
(Anduril's six founder-experience claims, Checkr's five competitors).
The problem observed in this test is entirely upstream: the
classification LLM does not reliably populate `verbatim_quote` on every
claim, so a **conservative, correctly-behaving firewall** ends up
rejecting a high proportion of genuinely well-evidenced, correctly-named
facts. This is Part 18 Category **B (Evidence Grounding)** — valid
evidence rejected — located in the adapter/prompt layer, not a defect in
the firewall's own logic.

## 10. Classification findings

Confirmed, concrete, reproducible across three independent companies
(A, B, F, and again G): generic financial/operational boilerplate
("cash runway," "gross margins," "funding round," "customer growth,"
"revenue and hiring plans") is being classified as
`ProductCapabilityObservation` with `shipped: true`, which then feeds
**Team's `technical_capability`** and **Execution's `product_execution`**
-- two dimensions about engineering/product delivery that this evidence
says nothing about. This is Part 18 Category **C (Evidence
Classification)**: correct, real evidence, mapped to the wrong canonical
signal/dimension. It is the single most consequential and most
reproducible defect found in this test. It lives entirely in
`app/ai/sps_v3_adapter.py`'s classification schema/prompt (Phase 10.9,
production integration) -- not in `app/ai/sps_v3_engine/` (Phase 10.8,
the deterministic scoring methodology).

No instance was found of evidence being duplicated to inflate a score
(the opposite was observed and confirmed working -- see Section 12) and
no instance was found of unrelated-pillar leakage beyond the
`ProductCapabilityObservation` pattern above.

## 11. Unknown-firewall findings

Directly verified on live data. Example (Palantir, Team pillar): 5
dimensions exist (`founder_market_fit` 0.25, `technical_capability` 0.20,
`business_capability` 0.20, `leadership` 0.20,
`execution_track_record_team` 0.15). Only `technical_capability` was
scorable. Pillar Strength = 9.50 -- computed **only** from
`technical_capability`'s own score, renormalized over its own weight
(the 4 unavailable dimensions contribute literally nothing to that
number, positive or negative). Pillar Coverage = 20.0% = 0.20 / 1.00
(technical_capability's original weight over the pillar's full original
weight) -- exactly reflecting that 80% of the pillar's configured weight
is Unknown. No dimension anywhere in any of the 7 runs was observed
converted to 0, 5, "neutral," an average, or a negative value for being
unavailable -- every unavailable dimension's `score` field is `null`,
full stop, in every JSON output inspected.

## 12. Negative-evidence findings

**No company in this 7-company set produced a `NegativeSignalObservation`
via the live production path**, including E (Zume), the company
selected specifically to exercise this. Two separate, distinct reasons,
both documented:

1. For this run, V2.1 itself did not mark Zume's real negative history
   (layoffs, PFAS compliance failure, shutdown) as `Observed` -- an
   acquisition/upstream-classification limitation for this specific run,
   not something this test can attribute to V3.
2. **Structurally, independent of any run's specific results**: the
   production adapter's extraction schema (`_PillarExtraction` in
   `app/ai/sps_v3_adapter.py`) has no `negative_signal` field and
   `classify_evidence_for_v3()` never constructs a
   `NegativeSignalObservation` under any circumstance. This means the
   negative-evidence-lowers-Strength rule -- verified correct in the
   deterministic engine by unit test and in the Phase 10.8J/10.9
   synthetic and real-company sanity work (Convoy, Olive AI, both
   showing Strength correctly pulled down by hand-constructed negative
   signals) -- currently **cannot be exercised via any real, live
   analysis** through today's production adapter. Per Part 21's own
   explicit instruction ("a failed company isn't low enough when
   negative evidence wasn't acquired" is *not* a failure condition), this
   is recorded as an **evidence acquisition/classification limitation**,
   not a scoring defect -- but it is a real, structural gap in the
   adapter worth prioritizing, since it means the negative-evidence path
   is currently dead code in production regardless of what a company's
   real history contains.

## 13. Fame / evidence-abundance findings

The strongest available evidence against fame bias came from Circlemind
(G, the deliberately obscure, sparse-evidence company): its
`technical_capability` classification_reason explicitly reports
signal-count deduplication in action -- *"3 unique substantive signal(s)
(deduplicated from 6 raw observation(s))"* -- meaning six observed
statements collapsed to three distinct signals before scoring, exactly
per Phase 10.8G's anti-fame-bias design. No company's Strength appeared
to rise merely because more sources repeated an identical fact; where
multiple observations existed, they were consistently deduplicated by
`(metric_type/type, entity/subject, period/classification)` identity
before the classification band was chosen, not by raw count.

The clearer fame-bias-*adjacent* finding is the one in Section 10:
Palantir, Anduril, and Lovable (three of the most evidence-rich
companies in the set) are exactly the three where the
financial-boilerplate-into-`ProductCapabilityObservation` misclassification
recurred -- plausibly *because* evidence-rich companies have more
`Observed`-status financial/operational text overall for the classifier
to (mis)use, not because their Strength is being inflated by volume once
inside the engine. This is worth naming precisely: more evidence volume
increased the *opportunity* for a classification error, but the
deterministic engine's own dedup/scoring math never rewarded volume with
a higher band once evidence entered it correctly.

## 14. Coverage findings

Manually re-derived and confirmed exactly correct for three companies:

- Lovable: 20\*0.20 + 20\*0.20 + 25\*0.20 + 50\*0.15 + 0\*0.15 + 0\*0.10
  = 20.5 -- matches the reported 20.5% exactly.
- Circlemind: 0\*0.20 + 20\*0.20 + 0\*0.20 + 50\*0.15 + 0\*0.15 + 0\*0.10
  = 11.5 -- matches exactly.
- Palantir: 0\*0.20 + 20\*0.20 + 0\*0.20 + 33\*0.15 + 0\*0.15 + 0\*0.10
  = 8.95, rounds to 9.0 -- matches exactly.

No artificial ceiling or floor was observed. No case was found of
Coverage rising from duplicate or irrelevant evidence -- Coverage is
strictly a function of which dimensions are `SCORABLE` (a binary,
per-dimension fact), never of how many observations support a scorable
dimension.

## 15. Confidence findings

Confidence tracked provenance grade and (where applicable) corroboration
-- never company fame or Strength magnitude. Concretely: Palantir and
Anduril, two of the most famous companies in the set, show `Low`/`Medium`
overall Confidence, identical in kind to Circlemind's (the deliberately
obscure company) `Medium`. No company's Confidence moved in lockstep
with a higher or lower Strength value -- e.g. Lovable's `Execution`
pillar carries `Medium` confidence at Strength 8.14, the same confidence
level Circlemind's `Execution` carries at Strength 6.82. Confidence
never behaved as a proxy for company quality or probability of success
anywhere in this data.

## 16. Stage-fairness findings

Stage (`map_stage()`) is correctly derived per company (Series-A-ish for
Lovable, Seed for Circlemind, Growth/Late for the others via the free-text
mapper) but had **no observable effect** on any of these seven results,
because none of them populated the four Category-A stage-relative
dimensions (`current_scale`, `growth_trajectory`, `retention_engagement`,
`capital_efficiency`) at all -- the v1 adapter does not extract the
structured numeric observations those dimensions require (a known,
already-documented Phase 10.9 scope limitation, not new). This means
stage-relative behavior could not be *positively* exercised in this
test, but it also means no early-stage company was penalized by a
stage-relative rule that didn't fire -- Circlemind's low Coverage comes
entirely from missing dimensions being excluded, never from a
stage-mismatch producing a negative or default score.

## 17. High-strength-company findings

**Genuinely exceptional, correctly-classified signals were shown capable
of receiving COMPREHENSIVE/9.5 Strength** -- confirmed for Lovable's
`customer_demand`/`customer_value` (2.3M users, 180K paying subscribers,
a real quantified valuation progression, four unique signals, all
correctly grounded). This is a clean, positive confirmation that the
deterministic engine does not mechanically suppress strong evidence into
mediocrity when the evidence is correctly classified. The *negative*
counterpart is the finding in Sections 8/10: Palantir's 9.5s on
`technical_capability`/`product_execution` are exceptional Strength
values attached to the *wrong* evidence, not evidence that was correctly
classified and then suppressed. No case was found anywhere in this test
of correctly-classified, genuinely exceptional evidence being
mechanically capped at a mediocre score -- so no
"POTENTIAL STRUCTURAL SCORING DEFECT" per Part 12's specific definition
is being flagged. The defect that *was* found is upstream of the
scoring rule, not in it.

## 18. Ordinary-company findings

Zapier (D), the deliberate "ordinary/mixed" pick, produced a single
`Observed` V2.1 fact company-wide, entirely outside this adapter's
covered-dimension scope, and therefore correctly produced zero V3
observations and an honest INSUFFICIENT/0% result. The system did not
force Zapier toward a high, low, or "average" outcome by reputation --
it simply, correctly reported that it had almost nothing in-scope to
evaluate. This is the right behavior under the "unknown is safe, not
punished" design, even though it means this test's "ordinary company"
case yielded the least analytically rich data of the seven.

## 19. Distressed-company findings

Covered in full in Section 12. The one thing to add here: no evidence
was found of hindsight leakage -- since no negative material about
Zume's later failure reached the classifier at all (for either of the
two independent reasons documented in Section 12), there was no
opportunity for it to leak backward into an earlier "as-of" evidence
set in this particular run. This test did not exercise an explicit
as-of-date freeze (Zume's input text was a plain company description,
not a dated historical snapshot the way the Phase 10.8I calibration set
used explicit `_REFERENCE_DATE_OVERRIDES`) -- worth naming as something
this specific test could not exercise, distinct from a defect.

## 20. Early-stage-company findings

Covered in Section 16. Circlemind was not penalized for being early --
its one publishable pillar (Execution, Strength 6.82) came from real,
if boilerplate-tinged, evidence, and every other pillar is honestly
`Unknown` rather than defaulted low. No stage-relative rule mechanically
fired against it because none of the stage-relative dimensions received
any evidence at all in this run (Section 16) -- an absence of positive
proof, not a proof of unfairness, and consistent with "missing
mature-company evidence primarily affects Coverage" holding true here.

## 21. Trace-reconstruction results

Manually reconstructed and independently verified, evidence -> signal ->
rule -> score, for:

- **Strong company (Palantir), `technical_capability`**: 4 raw
  `ProductCapabilityObservation`s (misclassified boilerplate, Section
  10) -> `build_canonical_signals` dedup to 4 unique signals (each
  distinct capability_label) -> `_generic_b_classification`: 4 signals
  >= 4 -> `COMPREHENSIVE` band -> `band.comprehensive` = 9.5. **Rule
  executed exactly as written** given its input.
- **Strong company (Lovable), `customer_demand`**: 4
  `CustomerEvidenceObservation`s (2.3M users / 180K subscribers /
  valuation progression, correctly classified) -> deduplicated to 4
  unique signals -> `COMPREHENSIVE` -> 9.5. **Rule executed exactly as
  written**, on correctly-classified input this time.
- **Ordinary/sparse company (Circlemind), `operating_discipline`**: 2
  raw observations -> deduplicated to 1 unique signal -> `SINGLE_SIGNAL`
  band -> `band.single_signal` = 5.5. **Rule executed exactly as
  written.**
- **Distressed company (Zume)**: no dimension anywhere reached
  `SCORABLE` -- there is no trace to reconstruct. Recorded honestly as
  "no trace available" rather than fabricated.

Across every dimension actually inspected, the deterministic
aggregation math (`_generic_b_classification` / `_build_b_result`)
executed **exactly** as documented -- zero instances of a
`RULE EXECUTION DEFECT`. Every anomaly found in this test was upstream,
in what evidence reached the rule, never in the rule itself.

## 22. Repeatability results

Ran for 2 companies, isolating deterministic scoring from acquisition
variance exactly as Part 17 specifies: `classify_evidence_for_v3()` was
called once per company to freeze a real observations tuple, then
`evaluate_all_dimensions()` + `evaluate_sps()` + `classify_ux_state()`
were run twice against that identical frozen input.

- **Palantir**: 4 observations frozen; two scoring runs -> **IDENTICAL**
  (SPS, Coverage, Confidence, publishable, every pillar and dimension
  score byte-for-byte equal).
- **Lovable**: 6 observations frozen; two scoring runs -> **IDENTICAL**.

Separately and expectedly, **classification itself is not perfectly
repeatable** run-to-run (Anduril's two independent classification calls
produced 0 and then a handful of observations; Lovable's two independent
runs produced 9 and then 6). This is acquisition/classification-layer
LLM variance, explicitly out of scope for the deterministic-scoring
repeatability test per Part 17's own instruction ("do NOT require
evidence acquisition itself to be identical").

## 23. Acquisition-vs-scoring defect table

| Company | Issue | Category (Part 18) | Layer |
|---|---|---|---|
| A Palantir | Financial boilerplate misclassified as shipped product capability, feeding `technical_capability`/`product_execution` | C. Evidence Classification | Adapter (`sps_v3_adapter.py`) |
| B Anduril | 6/6 real founder-experience claims dropped for missing `verbatim_quote`; same misclassification pattern as A | B. Evidence Grounding + C. Evidence Classification | Adapter |
| C Checkr | 5/5 real named competitors dropped -- malformed response shape + missing `verbatim_quote` | B. Evidence Grounding | Adapter |
| D Zapier | No in-scope `Observed` evidence existed | Not a V3 issue -- upstream V2.1 conservatism | Out of this test's scope |
| E Zume | No `NegativeSignalObservation` code path exists in the adapter at all | C. Evidence Classification (structural omission) | Adapter |
| F Lovable | Same misclassification as A, alongside a clean, correct `customer_demand`/`customer_value` extraction | C. Evidence Classification | Adapter |
| G Circlemind | Same misclassification as A/F; dedup confirmed working correctly | C. Evidence Classification | Adapter |

**No entry in this table is category D (Deterministic Scoring), E
(Coverage/Confidence math), or F (Presentation).** Every real defect
found in this test is category B or C, and every one lives in the
Phase 10.9 production adapter, not the Phase 10.8 deterministic
scoring engine.

## 24. Product-usefulness result per company

| Company | Rating | Why |
|---|---|---|
| A Palantir | PARTIALLY USEFUL | Correctly shows what's Unknown; the two populated pillars carry a real but misleading signal (see Section 10) that a founder/investor reading it could misinterpret as "strong technical execution" when it's actually financial-health boilerplate. |
| B Anduril | NOT USEFUL (this run) | INSUFFICIENT with 0% coverage teaches nothing beyond "not enough evidence," despite real, extractable evidence existing (Section 8). |
| C Checkr | NOT USEFUL (this run) | Same as B -- real, well-documented competitive evidence existed and was entirely lost to grounding rejection. |
| D Zapier | PARTIALLY USEFUL | Honestly communicates "not enough evidence," which is itself informative and non-misleading, if thin. |
| E Zume | NOT USEFUL (this run) | Gives no signal at all about the company's real, well-documented distress -- correctly abstains rather than fabricating, but teaches nothing. |
| F Lovable | USEFUL | Correctly surfaces real, specific, well-grounded traction (users, paying subscribers, valuation trajectory) and honestly marks Traction/Financial Health Unknown; the Execution pillar's misclassification (Section 10) is a real flaw but sits alongside genuinely correct signal. |
| G Circlemind | PARTIALLY USEFUL | Team strength (founder signal) is real; Execution strength repeats the Section 10 misclassification; correctly honest about five of six pillars being Unknown for a seed-stage company. |

## 25. Structural defects found

**None in the deterministic scoring engine** (`app/ai/sps_v3_engine/` --
types, signals, freshness, evaluators, aggregation). Every rule
inspected in Section 21 executed exactly as written. Unknown never
affected Strength (Section 11). Duplicate evidence never inflated a
score (Sections 10/13). Coverage math was exact in every case checked
(Section 14). Confidence never behaved as Strength or as probability of
success (Section 15). Deterministic scoring was perfectly repeatable
given frozen evidence (Section 22).

**Real, concrete, reproducible defects found in the production
INTEGRATION ADAPTER** (`app/ai/sps_v3_adapter.py`, Phase 10.9 -- not the
Phase 10.8 methodology this test is deciding whether to freeze):
1. Financial/operational boilerplate is misclassified as a shipped
   product capability, feeding two unrelated dimensions (confirmed on 3
   of 7 companies independently).
2. The classification LLM frequently omits `verbatim_quote`, causing a
   correctly-strict firewall to reject a high proportion of genuinely
   well-evidenced facts (confirmed on 2 of 7 companies, likely broader).
3. No code path exists anywhere in the adapter to construct a
   `NegativeSignalObservation` -- the negative-evidence rule is
   unreachable via any real, live analysis today, regardless of what a
   company's actual history contains.

## 26. Non-structural limitations found

Classification-call variance run-to-run (Section 22) -- expected LLM
behavior, not a defect, and explicitly not what determinism is being
tested for. This v1 adapter's 9/27-dimension coverage and its exclusion
of the four Category-A quantitative dimensions (already documented in
Phase 10.9) directly explains why zero of seven companies reached
SUFFICIENT -- this is a known, already-disclosed limitation, not a new
finding.

## 27. Whether any methodology change is actually justified

**No.** Every defect found in this test is upstream of the methodology
(Phase 10.8's deterministic engine): in the Phase 10.9 production
adapter's evidence-classification prompt/schema, and in V2.1's own
Observed/Inferred evidence-status classification (frozen, explicitly out
of scope). No finding in this test implicates a weight, a score band, a
threshold, an evidence-acceptance rule, or an aggregation formula. Per
this test's own Part 19 instruction, nothing was tuned, and nothing
should be -- the fix for every defect found here is a scoped adapter
change (a stricter capability-extraction prompt; a negative-signal
extraction category; possibly a correction-pass retry for missing
quotes, mirroring V2.1's own established pattern), not a methodology
phase.

## 28. Final decision

**B. ACCEPT SPS V3, BUT PRIORITIZE EVIDENCE ACQUISITION/CLASSIFICATION
IMPROVEMENTS LATER.**

The deterministic scoring engine (Phase 10.8) shows no structural
defect across every test this phase's directive specified: the unknown
firewall holds, negative evidence (where it reaches the engine) has
already been shown to work correctly (Phase 10.9's own sanity set), no
duplication inflation was found, Coverage math is exact, Confidence
stays separate from Strength, and scoring is perfectly repeatable given
frozen evidence. That is the thing this test was asked to accept, and it
passes. The real, concrete, reproducible problems found in this test
(Section 25) all sit in the Phase 10.9 production adapter -- a
narrower, already-partially-documented integration layer, not the
methodology.

## 29. Exact next action

Do not open another SPS methodology phase. The next SPS-adjacent action,
whenever the team chooses to prioritize it (explicitly NOT triggered
automatically by this report, per this phase's own instruction), is a
narrowly-scoped **adapter hardening pass** covering exactly the three
items in Section 25's second list -- not a redesign, not new
dimensions, not new weights. Otherwise: return to the founder product
roadmap now, as instructed.

---

```
REAL COMPANIES TESTED: 7

EVIDENCE GROUNDED: YES (the firewall itself never accepted an
  unverifiable claim; see Section 9 for the upstream limitation this
  causes)
UNKNOWN FIREWALL PASSES: YES
NEGATIVE EVIDENCE BEHAVES CORRECTLY: YES where it reaches the engine
  (prior Phase 10.9 sanity set); UNTESTABLE via this live run because no
  company in this set produced a NegativeSignalObservation (Section 12)
DUPLICATE/FAME BIAS DETECTED: NO

DETERMINISTIC RULE EXECUTION CORRECT: YES
COVERAGE MATH CORRECT: YES
CONFIDENCE SEPARATE FROM STRENGTH: YES
STAGE FAIRNESS ACCEPTABLE: YES (not adversely exercised; no penalty
  observed)
TRACE RECONSTRUCTION PASSES: YES
REPEATABILITY PASSES: YES

SYSTEMIC STRUCTURAL SCORING DEFECT FOUND: NO
EVIDENCE ACQUISITION LIMITATIONS FOUND: YES

SPS V3 REAL-WORLD ACCEPTANCE: PASS

FINAL DECISION:
B

METHODOLOGY CHANGE JUSTIFIED: NO
SAFE TO FREEZE SPS METHODOLOGY: YES
READY TO RETURN TO FOUNDER PRODUCT ROADMAP: YES
```

STOP.

No production code was modified. Nothing was tuned. Nothing was
committed. Nothing was deployed. No further SPS methodology phase is
being proposed or started.
