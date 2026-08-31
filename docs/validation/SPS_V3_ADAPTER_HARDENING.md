# SPS V3 — Final Adapter Hardening

Builds directly on `docs/validation/SPS_V3_REAL_WORLD_ACCEPTANCE.md`'s own verdict
(Decision B: accept the SPS V3 methodology, harden the evidence/adapter layer). This
phase modifies **only** `app/ai/sps_v3_adapter.py` (and its test file). The
deterministic engine (`app/ai/sps_v3_engine/`), the frozen calibration harness
(`app/calibration/sps_v3/`), and every V2.1/VPS/Readiness scoring file are
untouched — verified below via `git diff`, not asserted.

This document does not edit or overwrite `SPS_V3_REAL_WORLD_ACCEPTANCE.md`, its
ex-ante companion, or `docs/validation/sps_v3_real_world_acceptance_raw/`. All three
remain exactly as that phase left them.

## 1. Interrupted-session recovery

The prior session was interrupted mid-implementation (machine sleep) immediately
after the adapter rewrite landed and one regression test had been run and found to
need updating for new, intentional behavior. Recovery steps taken this session,
before any further edits:

- `git status --short` / `git diff --stat` — confirmed exactly one file
  (`app/ai/sps_v3_adapter.py`) was modified, nothing else in the tree.
- Full fresh read of `app/ai/sps_v3_adapter.py` (1003 lines at that point) —
  confirmed the file parses (`ast.parse`, `py_compile`), and a duplicate-definition
  scan (`grep -n "^def \|^class "` + `sort | uniq -c`) found **zero duplicate
  function/class names** — no interleaved old/new code, no unreachable branches, no
  duplicate `return` statements.
- Re-read `app/ai/sps_v3_engine/types.py`, `evaluators.py`, `signals.py`,
  `evidence_bundle.py`, `registry.py`, `factory.py`, and `app/ai/pillar_shared.py` in
  full to reconstruct the exact production data flow before touching anything
  further, per the directive's "do not infer architecture from memory" instruction.

**Conclusion: the interrupted rewrite landed cleanly.** No malformed, duplicated, or
partially-applied code was found. The only follow-on work needed was (a) finishing
the interrupted regression test split and (b) the two genuine defects found and
fixed during this session's own verification pass (Section 4).

## 2. What was implemented (recap)

Three fixes, all confined to `app/ai/sps_v3_adapter.py`:

1. **Capability classification leakage** — `_SYSTEM_MESSAGE` now states explicit
   positive/negative criteria for what counts as a shipped capability, plus a
   deterministic secondary safety net, `_is_financial_operational_boilerplate()`,
   built from generic term **families** (`_FINANCIAL_OPERATIONAL_TERMS` /
   `_PRODUCT_TECHNICAL_TERMS` / `_PRODUCT_TECHNICAL_STEMS`) — never the literal
   sentences the acceptance test found for any specific company. A capability quote
   is rejected only when it contains financial/operational language **and** no
   product/technical language at all.
2. **Negative evidence** — a new `negative_signals` extraction category
   (`_NegativeSignalClaim`) reuses the existing, frozen `NegativeSignalObservation`
   contract exactly. `affected_dimension` is validated against the real dimension
   vocabulary for that claim's own pillar, read-only from the frozen engine's
   `DIMENSION_PILLARS` table (`_DIMENSIONS_BY_PILLAR_KEY`) — an invalid or
   cross-pillar dimension is dropped, never guessed.
3. **Safe grounding recovery** — two-tier: (a) deterministic, zero-LLM-call anchor
   recovery (`_recover_quote_by_anchor`) using a claim's own proper-noun field; (b) a
   single bounded correction-retry LLM call (`_attempt_correction_retry`), batched
   across every still-unresolved claim, capped at `_MAX_CORRECTION_RETRY_ITEMS = 40`,
   narrowly scoped to "return the exact quote or null." Every recovered observation
   is marked `extraction_confidence=LOW`, `source_reference=
   "recovered_by_grounding_repair"`.

## 3. Two defects found and fixed during this session's own verification

Neither was present in the interrupted patch as landed-cleanly code; both were found
by actually exercising the hardened adapter (unit tests + a live 7-company rerun),
consistent with "read/verify before declaring done."

### 3a. Negative signals were never reaching the engine

`compute_sps_v3_assessment()` built `EvidenceBundle(..., evidence=observations)`,
putting **every** observation — including `NegativeSignalObservation` — into the
bundle's `evidence` field. But every one of the 27 deterministic evaluators reads
negative evidence from `company.negative_signals`, a **separate** field
(`app/ai/sps_v3_engine/evaluators.py`, every `eval_*` function). A
`NegativeSignalObservation` placed in `.evidence` is invisible to every evaluator —
Fix #2 would have extracted negative evidence correctly and then silently dropped it
before scoring, in every single case. Found by
`test_negative_signal_reaches_engine_and_lowers_relevant_strength` failing on first
run. **Fixed** by splitting `classify_evidence_for_v3`'s flat output in
`compute_sps_v3_assessment()`:

```python
positive_observations = tuple(o for o in observations if not isinstance(o, NegativeSignalObservation))
negative_observations = tuple(o for o in observations if isinstance(o, NegativeSignalObservation))
bundle = EvidenceBundle(..., evidence=positive_observations, negative_signals=negative_observations)
```

Covered by `test_compute_sps_v3_assessment_routes_negative_signals_correctly`
(exercises the actual production entry point, not just the lower-level API).

### 3b. `"engine"` matched inside `"engineering"`

The Fix #1 safety net's term-matching used substring matching for any term longer
than 4 characters. `"engine"` (6 chars) is a legitimate technical term
(recommendation engine, fraud-detection engine) — but as a plain substring it also
matches inside the unrelated word `"engineering"`. A live 7-company rerun caught
this directly: Lovable's genuinely-boilerplate claim *"Hiring plan disclosed to
double engineering and sales teams over next 12 months"* was classified as a
capability, and the safety net failed to reject it, solely because "engineering"
contains "engine." **Fixed** by requiring a full word boundary (`\bengine\b`) for
every standalone single-word term, while keeping a small, explicit set of
intentional prefix **stems** (`deploy`, `integrat`, `automat` — meant to match
`deployed/deployment`, `integration/integrated`, `automated/automation`) as
start-boundary-only. Regression test:
`test_capability_filter_term_matching_does_not_collide_on_substrings`. Re-running
Lovable after the fix confirmed the claim is now correctly rejected (Section 8).

Both fixes are additive, minimal, and confined to `app/ai/sps_v3_adapter.py`. No
engine/methodology file was touched to fix either.

## 4. Test results

| Suite | Count | Result |
|---|---|---|
| `app/tests/test_sps_v3_adapter.py` (adapter, offline/mocked) | 22 | **22/22 pass** |
| `app/calibration/sps_v3/tests/` (frozen deterministic engine) | 76 | **76/76 pass** |
| `test_provenance`, `test_evidence_validator`, `test_evidence_scoring_pipeline`, `test_scoring_weights`, `test_methodology_v2_1`, `test_sie_v2_methodology`, `test_sie_v2_evidence_semantics`, `test_sie_v2_deterministic_integration`, `test_sie_v2_anchors`, `test_scoped_correction`, `test_fundraising_readiness` | 172 | **172/172 pass** |
| `test_security_hardening`, `test_backend_authentication`, `test_public_evidence_consistency`, `test_founder_evidence`, `test_pitch_deck_coach`, `test_founder_missions` | 138 | **138/138 pass** |
| **Total** | **408** | **408/408 pass** |

No test was modified to accommodate broken behavior. The one pre-existing test that
needed updating (`test_missing_verbatim_quote_drops_only_that_claim`) was updated
because its old assertion described behavior Fix #3 *deliberately* changed
(missing-quote claims are no longer unconditionally dropped) — the update **splits**
that single case into two explicit, still-strict tests
(`test_missing_quote_recoverable_via_anchor_is_deterministically_recovered` /
`test_missing_quote_with_no_safe_anchor_is_not_accepted_by_tier_one`), plus the
original test itself is kept, now exercising a genuinely-unrecoverable claim.

New tests added this phase (19, on top of the original 6 adapter tests): capability
boilerplate rejection/acceptance (2) + pipeline-level dimension-availability
confirmation (1) + the term-collision regression (1); negative-signal grounded
acceptance/rejection/dimension-validation/engine-routing (5); grounding-recovery
tier-1/tier-2 exact-quote/paraphrase/fabrication/malformed-response/call-failure/
bounded-retry (7); the two split missing-quote cases (2); the interrupted-session's
original test, adjusted (1).

`app/calibration/run_calibration.py` (the live-API 31-company suite) was not run —
it takes multiple minutes per company and is explicitly documented as "not a unit
test suite" (`app/calibration/README.md`); the frozen-engine `pytest` suite (76
tests, 0.5s, fully offline) is the correct regression check for the deterministic
methodology, and passed cleanly.

## 5. Methodology freeze verification

```
git diff --stat -- app/ai/sps_v3_engine/ app/calibration/sps_v3/ app/ai/scoring.py \
  app/ai/scoring_methodology.py app/ai/analyze_pillar.py app/ai/pillar_scoring.py \
  app/ai/evidence_provenance.py app/ai/readiness_score.py app/ai/investment_score.py \
  app/ai/scorecard.py
```

**Empty output.** Confirmed independently by `git status --short`, which shows only
`app/ai/sps_v3_adapter.py` and `app/tests/test_sps_v3_adapter.py` modified in the
whole repository. Pillar weights, dimension weights, score bands, publishability
thresholds, Coverage math, Confidence math, Strength math, aggregation, evaluators,
Unknown semantics, deduplication, conflict resolution, and freshness rules are all
byte-identical to what the Real-World Acceptance Test ran against — confirmed
functionally, not just by diff, by the 76/76 frozen-engine test pass.

(One incidental non-adapter file, a disposable PDF test fixture regenerated by an
unrelated test suite with a fresh timestamp, was found modified as a side effect of
running the test suites above. It was reverted via `git checkout` — it was never an
intended change and carries no content of interest.)

## 6. Seven-company before/after rerun

Reused the **exact frozen V2.1 pillar evidence** cached by the Real-World Acceptance
Test for all seven companies (no new research, no new companies, no target scores) —
only the V3 classification/adapter step was re-run, now through the hardened
`app/ai/sps_v3_adapter.py`. Full before/after JSON preserved at
`/private/tmp/.../scratchpad/rerun_hardened_out/` (session-scoped scratch — the
tables below are the durable record).

| Company | Before | After | tech_capability | product_execution |
|---|---|---|---|---|
| A. Palantir | 4 obs, all `ProductCapabilityObservation` (boilerplate) | **0 obs**, 0 negative | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** |
| B. Anduril | 0 obs | **6 obs** (4 FounderExperience, 2 CustomerEvidence), 0 negative | unavailable → unavailable | unavailable → unavailable |
| C. Checkr | 0 obs | **7 obs** (5 competitors + 2 customer, **all 7 recovered** via Fix #3), 0 negative | unavailable → unavailable | unavailable → unavailable |
| D. Zapier | 2 obs, both `ProductCapabilityObservation` (boilerplate) | **0 obs**, 0 negative | unavailable → unavailable | unavailable → unavailable |
| E. Zume | 0 obs | **2 obs** (customer evidence, recovered), **0 negative** | unavailable → unavailable | unavailable → unavailable |
| F. Lovable | 9 obs (5 capability [boilerplate], 4 customer) | **3 obs** (customer only; the 5 boilerplate capability claims, incl. the "engineering" one — Section 3b — all correctly rejected) | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** |
| G. Circlemind | 6 obs, all `ProductCapabilityObservation` (boilerplate) | **0 obs**, 0 negative | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** | SCORABLE → **UNAVAILABLE_NO_EVIDENCE** |

Per the directive's own acceptance framing, **success here is not higher SPS,
higher coverage, or more SUFFICIENT companies** — several companies show *lower*
coverage after hardening (Palantir 9.0%→0.0%, Lovable 20.5%→9.0%, Circlemind
11.5%→0.0%). In every one of those cases the "before" coverage was propped up
entirely by misclassified financial/operational boilerplate; the "after" number is
the honest one. Success is measured against the four criteria the directive states
explicitly:

- **Fewer legitimate facts unnecessarily lost** — Checkr: 0 → 7 (all 5 real named
  competitors + 2 real customer-demand facts recovered). Anduril: 0 → 6 real,
  correctly-classified founder/traction facts. Zume: 0 → 2 real customer facts.
- **No irrelevant capability signals** — 0 boilerplate capability claims survive
  anywhere in the 7-company set after hardening (down from 4+2+5+6 = 17 across
  Palantir/Zapier/Lovable/Circlemind before).
- **Real adverse evidence can reach V3** — structurally proven (Section 4a fix +
  `test_negative_signal_reaches_engine_and_lowers_relevant_strength` +
  `test_compute_sps_v3_assessment_routes_negative_signals_correctly`); see Section 8
  for why none of the 7 companies' frozen input actually exercises this live.
- **Unsupported evidence remains rejected** — confirmed both live (every recovered
  claim above is a real, verbatim substring of the source text; nothing fabricated
  survived) and by the 4 dedicated correction-retry rejection tests (paraphrase,
  fabricated number, unsupported fact, malformed response).

## 7. Palantir / Anduril / Lovable / Circlemind — capability-leak fix verification

All four companies were named in the acceptance report as exhibiting the same
generic-financial-boilerplate-as-capability misclassification. After hardening:

- **Palantir**: 4/4 boilerplate claims ("sufficient runway and cash balance,"
  "positive customer growth and retention," "healthy margins," "successful funding
  rounds"-shaped text) rejected. 0 false capability signals remain.
- **Lovable**: 5/5 boilerplate claims (hiring plan, operating cadence, cash
  runway/funding, hiring+cadence, gross margins) rejected — including the one that
  initially slipped through via the "engine"/"engineering" collision, now fixed
  (Section 3b) and re-verified.
- **Circlemind**: 6/6 boilerplate claims ("customer acquisition numbers and revenue
  growth," "raised multiple funding rounds," "hiring sequences") rejected.
- **Anduril**: this run's live extraction did not attempt any capability
  classification for Anduril at all (0 `ProductCapabilityObservation` either way) —
  a clean run rather than a rejection to demonstrate, but consistent with (not
  contradicting) the fix; the founder-experience content it did extract is real and
  unrelated to the capability question.

**No universal false negative was introduced**: `test_capability_filter_accepts_
legitimate_shipped_capability_and_release` and
`test_boilerplate_does_not_create_technical_capability_or_product_execution_but_
legit_does` both confirm a real shipped-capability/product-release claim still
survives and still makes `product_execution` `SCORABLE`.

## 8. Anduril / Checkr — recovery detail

**Checkr** (the cleanest, most reproducible result this phase): re-run 4 times
independently (1 in the main 7-company sweep + 3 further diagnostic attempts), the
adapter recovered **all 5 real named competitors** (HireRight, Sterling, First
Advantage, Accurate Background, GoodHire) and 2 real customer-demand facts in
**every** attempt (4/4), all marked `recovered_by_grounding_repair`. Each competitor
anchor (`named_competitor`) is a literal, distinct proper noun present in the single
grounding sentence *"Checkr competes with established players including HireRight,
Sterling, First Advantage, Accurate Background, and GoodHire"* — textbook Fix #3
tier-1 deterministic anchor recovery. The two customer-demand facts (no
`named_customer` anchor available) were recovered via tier-2 correction retry. **0
of the 5 previously-lost competitors are still lost.**

**Anduril**: this run's baseline snapshot already showed 0 observations (matching
the acceptance report's own disclosed run-to-run variance for this exact
deep-dump), so a strict recovered/still-lost mapping against *this specific*
baseline file isn't meaningful. Mapped instead against the acceptance report's
named 6-claim narrative:

| Founder claim | Outcome | Why |
|---|---|---|
| Palmer Luckey (co-founder) | RECOVERED | Folded into a single grounded "Founded in 2017 by..." entry |
| Brian Schimpf, ex-Palantir | RECOVERED | Directly grounded this run (model supplied a valid quote) |
| Matt Grimm, ex-Palantir | RECOVERED | Directly grounded this run |
| Matt Grimm, ex-Booz Allen Hamilton | **STILL LOST** | The model did not emit a second, separate claim for Grimm's Booz Allen Hamilton background this run at all — an upstream extraction-completeness gap (Category A, acquisition/classification variance), not a grounding-firewall rejection; nothing to recover because nothing was proposed |
| Trae Stephens, ex-Founders Fund | RECOVERED | Directly grounded this run (classified `ADJACENT_DOMAIN` rather than `REPEAT_FOUNDER` — a classification nuance, not a loss) |

Zero boilerplate capability leakage in this run's Anduril output either (0
`ProductCapabilityObservation`, positive or rejected).

## 9. Zume — negative evidence check

Directly inspected Zume's **frozen, unmodified V2.1 `Observed`-status evidence**
(the same input this and the original acceptance run both used) subscore-by-subscore.
Every `Observed` item is positive-framed: market-size/growth figures, "Zume served
major corporate clients such as PepsiCo and Unilever," "18 months of cash runway,"
"phased hiring plan indicates disciplined resource allocation," "customer growth
from 100 to 300." **None of it mentions layoffs, the PFAS packaging-compliance
failure, or the June 2023 shutdown** — the real, well-documented adverse history a
person researching Zume today would find.

The hardened adapter correctly produced **0 `NegativeSignalObservation`** for Zume.
This is the structurally correct outcome, not a defect: Fix #2's grounding firewall
requires a real adverse sentence to exist in the given source text, and none does —
the gap is upstream, in V2.1's own evidence-acquisition/status-classification layer
(never marking Zume's real negative coverage as `Observed`), exactly as the original
acceptance report identified in Section 13. Per the directive's explicit
instruction, **no negative evidence was manufactured from hindsight** — a company
known to have failed is not treated any differently from what its actual, frozen,
`Observed` input text supports. Fix #2's engine-reaching, Strength-lowering
mechanism itself is proven correct and live via `test_negative_signal_grounded_
adverse_fact_becomes_observation`, `test_negative_signal_reaches_engine_and_lowers_
relevant_strength`, and `test_compute_sps_v3_assessment_routes_negative_signals_
correctly` (Section 4a) — it simply has nothing to act on for Zume's specific
frozen input.

## 10. Retry mechanism — bounds, cost, and failure behavior

- **Trigger**: only claims that (a) fail the primary firewall check and (b) have no
  usable deterministic anchor (tier 1) are batched into the correction retry.
- **Bound**: exactly one additional LLM call per `classify_evidence_for_v3`
  invocation, regardless of how many claims are pending — proven by
  `test_correction_retry_is_bounded_to_a_single_non_recursive_call` (5 unresolved
  items, still exactly 2 total calls) and `test_missing_quote_recoverable_via_
  anchor_is_deterministically_recovered` (tier-1 success alone: exactly 1 call, the
  retry never fires when unneeded).
- **Cap**: `_MAX_CORRECTION_RETRY_ITEMS = 40` — anything beyond the cap is dropped,
  never silently trusted.
- **Non-recursion**: whatever the one retry call returns is final; a claim still
  ungrounded afterward is dropped, never retried again.
- **Scope**: narrowly "return the exact quote or null" — no score field, no
  reclassification, confirmed never to accept a paraphrase, a fabricated number, or
  an unsupported fact (`test_correction_retry_accepts_exact_quote_rejects_
  paraphrase_fabrication_and_unsupported`).
- **Failure behavior**: a malformed (non-JSON, non-array) response degrades to zero
  recovered claims (`test_correction_retry_malformed_response_fails_closed`); a
  raised exception (simulated API outage) degrades the same way **without losing
  claims that were already grounded elsewhere in the same analysis**
  (`test_correction_retry_call_failure_fails_closed_without_losing_other_claims`).
- **Expected additional call count in production**: 0 or 1 per analysis — 1 only
  when at least one claim survives classification with no usable quote and no
  deterministic anchor. Observed live in this phase's rerun: Checkr and Zume each
  triggered exactly one retry call and recovered real, grounded facts from it; most
  other runs (Palantir, Zapier, Circlemind, most of Lovable/Anduril) needed zero
  retries.

## 11. Remaining limitations (honest, not overclaimed)

- **"Missing information" / "uncertainty" are not negative signals" is enforced
  structurally (the shared grounding firewall — a negative claim with no real
  supporting text is dropped, for whatever reason it lacks support), but is **not**
  separately, semantically distinguished from a fabricated claim at the code level —
  there is no deterministic way to tell "the model correctly declined to invent a
  negative signal for missing data" from "the model tried to and got caught by the
  firewall" from the outside. Both degrade to the same safe outcome (nothing
  extracted), which is what matters, but the *reason* is not separately observable.
  This mirrors exactly how positive-evidence grounding already worked before this
  phase.
- **Financial Health remains entirely out of adapter scope** (unchanged from Phase
  10.9) — this phase did not extend coverage to `revenue_quality`,
  `unit_economics`, or `capital_efficiency`.
- **The four Category-A quantitative dimensions remain unclassified** by this
  adapter (`current_scale`, `growth_trajectory`, `retention_engagement`,
  `capital_efficiency`) — unchanged scope boundary from Phase 10.9, not touched
  this phase.
- **Extraction completeness still varies run-to-run** (Anduril's still-lost
  Booz Allen Hamilton claim, Section 8) — this is upstream LLM extraction
  variance, already disclosed in the acceptance report, and out of this phase's
  authorized scope (methodology/prompt-determinism is not something an adapter
  hardening pass can fully eliminate without a different model or a
  multi-sample consensus mechanism, neither of which was authorized here).
- **No real company in this 7-company set exercises the negative-evidence path
  live**, because none of their frozen `Observed` V2.1 input happens to contain
  grounded adverse text. The mechanism is proven correct by direct engine-level
  tests (Section 4a) and by live extraction on synthetic-but-realistic text in this
  phase's own test suite, not by a live 7-company negative-signal example.

## 12. Final decision

**A. ADAPTER HARDENED — SPS V3 PIPELINE READY.**

All three defects the Real-World Acceptance Test found are fixed and verified: the
capability-leakage false positives are eliminated (0 surviving across all 7
companies, with a real generalization test proving legitimate capabilities still
pass); the negative-evidence path exists, is wired correctly into the deterministic
engine (a genuine integration bug found and fixed during this phase's own
verification), and is proven to lower Strength on grounded input; and grounding
recovery is demonstrably working live (Checkr: 5/5 previously-lost real competitors
recovered, reproducibly). The deterministic engine and methodology are unmodified
and independently confirmed unchanged (76/76 frozen tests, empty `git diff` on every
methodology file). 408/408 tests pass across the full relevant regression surface.
Remaining limitations (Section 11) are scope boundaries already known from Phase
10.9, not new defects, and none of them block the pipeline from being frozen at its
current, honest scope.

**Recommendation: freeze the SPS V3 pipeline at this state and return to the
Founder Product roadmap.** Do not begin another SPS phase.

---

INTERRUPTED WORKING TREE RECOVERED: YES
PARTIAL/MALFORMED CODE FOUND: NO

FROZEN COMPANIES RERUN: 7

CAPABILITY LEAK FIXED: YES
FINANCIAL BOILERPLATE CAN BECOME TECHNICAL CAPABILITY: NO
FINANCIAL BOILERPLATE CAN BECOME PRODUCT EXECUTION: NO
LEGITIMATE CAPABILITY EVIDENCE STILL PASSES: YES

NEGATIVE SIGNAL PRODUCTION PATH EXISTS: YES
MISSING EVIDENCE BECOMES NEGATIVE: NO
NEGATIVE EVIDENCE REACHES ENGINE: YES
NEGATIVE EVIDENCE LOWERS RELEVANT STRENGTH: YES

SAFE QUOTE RECOVERY IMPLEMENTED: YES
UNSUPPORTED CLAIMS STILL FAIL CLOSED: YES
FABRICATED NUMERIC CLAIMS ACCEPTED: NO

UNKNOWN FIREWALL PASSES: YES
DUPLICATE/FAME PROTECTION PASSES: YES
DETERMINISTIC SCORING PASSES: YES

SPS WEIGHTS CHANGED: NO
SPS BANDS CHANGED: NO
SPS THRESHOLDS CHANGED: NO
SPS METHODOLOGY CHANGED: NO
VPS CHANGED: NO

ADAPTER HARDENING PASS: YES
FINAL DECISION: A

SPS PIPELINE READY TO FREEZE: YES
READY TO RETURN TO FOUNDER PRODUCT ROADMAP: YES

STOP.
