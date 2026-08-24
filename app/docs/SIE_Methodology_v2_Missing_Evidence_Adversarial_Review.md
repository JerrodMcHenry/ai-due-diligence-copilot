# SIE Methodology v2 — Missing Evidence, Confidence & Aggregation: Adversarial Review

**Status: design document only.** No code changed, no methodology documents modified, no
calibration run, nothing committed. This is a standalone adversarial review of
`SIE_Methodology_v2_Scoring_Semantics.md`'s missing-evidence, confidence, and aggregation design —
it does not edit that document. Where this review overturns something in it, that document remains
as originally written until an explicit future edit is authorized; treat this file as superseding
guidance on the specific point identified, not as a silent correction.

**Headline finding: Part 4 of the Scoring Semantics document — the "expected-but-missing
dimension contributes a below-average default" mechanism — does not survive this review. It is
REJECTED as a general quality-score mechanism.** Under adversarial testing it cannot reliably tell
"an elite company that quietly didn't disclose a number" from "a weak company hiding a bad number,"
because both produce the *identical observable signal* (silence). Applying a below-average default
broadly converts "we don't know" into "we think it's weak" — exactly the collapse the task
forbids. The reasoning is below, followed by a replacement design.

---

## The eight stress cases

For each: underlying quality (ground truth, unknowable to SIE in most rows — stated only so the
reader can see where the design succeeds or fails), observable evidence, evidence coverage,
disclosure behavior, confidence, diligence risk, and recommended score treatment.

**1. Elite Series A, excellent retention, but private.**
- Underlying quality: excellent (e.g., true NRR ~140%).
- Observable evidence: none disclosed.
- Coverage: 0% for this dimension.
- Disclosure behavior: non-disclosure for reasons unrelated to weakness — retention data is
  competitively sensitive and withheld by strong and weak companies alike; many excellent
  pre-IPO companies simply don't publicize churn/NRR.
- Confidence: cannot be High (no evidence exists to be confident *about*) — must be Unavailable,
  not "confidently low."
- Diligence risk: low to the company's actual health; genuinely worth a human follow-up regardless.
- Score treatment: **must not receive a below-average default.** This is the direct counterexample
  that breaks the Part 4 mechanism — a below-average default here silently mislabels a strong
  company as weak.

**2. Weak Series A, hiding terrible retention.**
- Underlying quality: poor (e.g., true NRR ~85%, high churn).
- Observable evidence: none disclosed.
- Coverage: 0%.
- Disclosure behavior: non-disclosure — **observationally identical to Case 1.** This is the crux
  of the whole review: from evidence alone, Cases 1 and 2 cannot be told apart. Silence carries no
  information about which one is happening.
- Confidence: same as Case 1 — Unavailable, not "confidently low."
- Diligence risk: high, and correctly so — this is the case a human should chase.
- Score treatment: **identical to Case 1 at the score level**, because SIE has no way to know which
  case it's looking at. The only place these two cases can legitimately diverge is diligence-flag
  framing and (if it exists) a separate disclosure-risk signal (see Cases 7–8) — never the quality
  number.

**3. Public company, complete metrics.**
- Underlying quality: whatever it actually is (say, average — NRR ~105%).
- Observable evidence: full (SEC filings, earnings calls).
- Coverage: high/complete.
- Disclosure behavior: full disclosure, largely mandatory for public companies.
- Confidence: High — direct, verifiable, recent.
- Diligence risk: low — fully knowable.
- Score treatment: computed directly from actual evidence, no defaults needed. This is the
  **positive control** — it confirms the architecture works fine when evidence genuinely exists;
  the entire missing-evidence design problem is specific to the private/early-stage majority of
  this system's actual target population, not a universal complication.

**4. Private company, almost no disclosed metrics anywhere.**
- Underlying quality: genuinely unknowable from what's available — could be a hidden gem or a
  hidden disaster.
- Observable evidence: minimal, across nearly every pillar, not just one dimension.
- Coverage: very low, system-wide.
- Disclosure behavior: uniformly thin (very early, or unusually guarded).
- Confidence: Low/Unavailable across most dimensions.
- Diligence risk: high, and diffuse — SIE cannot meaningfully differentiate this company from
  either extreme.
- Score treatment: this is the strongest real-world argument for **not computing a confident point
  SPS at all** — see Part 5's minimum-evidence-threshold question, revisited below.

**5. Pre-Seed startup where Retention genuinely should not exist yet.**
- Underlying quality: not-yet-applicable for this dimension — there is no cohort old enough for
  "retention" to be a coherent concept.
- Observable evidence: none, correctly.
- Coverage: N/A (the dimension doesn't apply).
- Disclosure behavior: N/A — nothing is being withheld, there is nothing to withhold.
- Confidence: N/A (no score exists to have confidence in).
- Diligence risk: **none**, for this dimension specifically.
- Score treatment: this is the prior document's "Case 4 / Not-Yet-Applicable" and it was already
  correct — exclude cleanly, zero penalty, zero flag. **The one case in this review that survives
  unchanged.**

**6. Conflicting sources.**
- Underlying quality: unresolved pending verification (e.g., one source implies NRR ~90%, another
  implies ~130%, or one is a stale press mention and another a recent interview).
- Observable evidence: exists, but contradictory.
- Coverage: nominally present, low-value due to conflict.
- Disclosure behavior: N/A — this is a **data-quality problem, not a disclosure-choice problem**,
  and should be treated as conceptually distinct from every other case in this list.
- Confidence: must be capped Low (already correctly gated in the Scoring Semantics document's
  Part 8: "no unresolved conflict" is a stated High-confidence requirement).
- Diligence risk: high and specific — "verify which claim is accurate," not "verify the metric
  from scratch."
- Score treatment: **refinement to the prior document** — its Part 2 "Case 2, mixed evidence" was
  conflating two different things: *mixed* (multiple simultaneously-true facts pointing different
  directions — real, should be scored and flagged) and *conflicting* (sources disagree about a
  single underlying fact — only one can be true). For conflicting evidence, do **not** average the
  two disagreeing numbers into a fabricated hybrid neither source supports; instead score from the
  more credible/recent source with an explicit confidence cap and a "sources conflict, verify" flag,
  or mark Unavailable if no source is clearly more credible.

**7. SIE's own research failed to find evidence that does exist publicly.**
- Underlying quality: unknown to SIE, though genuinely discoverable in principle (e.g., a Tavily
  query that should have surfaced a press article with the metric, but didn't).
- Observable evidence to SIE: none — but this is a **system-reliability failure, not a
  company-side disclosure choice.** The company did disclose; SIE simply didn't find it.
- Coverage: appears low to SIE, but true population coverage (what's actually out there) is higher.
- Disclosure behavior: irrelevant — misattributing this to the company would be a real error.
- Confidence: Low, but for a different reason than Cases 1/2/4 (search completeness, not evidence
  scarcity).
- Diligence risk: **should not be framed as a company-diligence flag at all.** Flagging "Retention
  not found" in a way a reader interprets as "this company is hiding something" would be a genuine,
  previously-unaddressed error mode — it casts suspicion on the company for a SIE-side failure.
- Score treatment: excluded, same as any Unavailable case — but the flag language must be a
  distinct category: **"research completeness note" (system-facing: re-run/verify manually) vs.
  "diligence flag" (company-facing: ask them directly).** This is a refinement not present in the
  prior document.

**8. Management explicitly refuses to provide a metric investors would normally expect.**
- Underlying quality: still unknown — a refusal doesn't reveal the number.
- Observable evidence: none for the metric itself, **but the refusal is itself a new, real,
  observed fact** — categorically different from mere silence. This is the one case among the
  eight where something beyond "absence" is actually known.
- Coverage: 0% for the metric; but a genuinely new data point exists about *disclosure behavior*.
- Disclosure behavior: **explicit, observed evasion** — not inferred from silence, actually
  witnessed (typically only available via `founder`/`investor`/`data_room` evidence sources, not
  the default `public` analysis type).
- Confidence: still Unavailable for the metric itself.
- Diligence risk: elevated, and legitimately so — evasiveness upon being directly asked carries
  some real, general predictive signal in investing practice, independent of what the true number
  turns out to be.
- Score treatment: **still exclude the metric from the quality score** — refusal doesn't tell us
  the number, only that someone didn't want to share it. But this is the one case that may
  legitimately populate a genuinely separate **disclosure-risk** signal (Part-6-of-the-final-ask
  below) — never folded into SPS or the metric's own score, per the same non-collapse principle
  applied one level further.

---

## Does the below-average default ("Case 6" in the prior document) survive?

**No.** Cases 1 and 2 are proof by direct construction: they are observationally identical to SIE
(zero evidence, non-disclosure, no distinguishing signal), yet applying a below-average default to
"expected but missing" dimensions would score them identically *and wrongly low* for Case 1. The
prior document's Part 3 stage-conditional matrix classified Series-A Retention as "Expected" —
meaning, under the Part 4 mechanism as written, an elite, quietly-private company would have been
penalized in its quality score for a disclosure pattern shared by strong and weak companies alike.
This was not a hypothetical edge case; it is the *typical* shape of a real private-company analysis.

The deeper problem: **from public-only evidence, "expected but missing" is not information about
company quality at all** — it is, at best, weak information about disclosure *norms*, which apply
roughly equally regardless of underlying quality. Treating it as a quality signal was a category
error, not a tuning problem — no choice of the (deliberately unspecified) penalty-floor constant
would have fixed this, because the defect is structural, not calibration-dependent.

**But the concern the mechanism was trying to address — a company must not benefit from hiding
weak evidence — has not disappeared, and rejecting the mechanism does not resolve it on its own.**
See the architecture comparison below.

---

## Architecture comparison: A through F

**A. Penalize expected-but-missing evidence in the quality score.** *(The rejected mechanism.)*
Directly fails Cases 1/2 as shown above. **Reject.**

**B. Exclude missing evidence from quality but reduce confidence.**
Correctly keeps the quality score unbiased for Cases 1, 2, 4, 5, 7 (Confidence drops to
Unavailable/Low uniformly, score stays clean). But it has its own real gap: it does not
differentiate Case 1 (quiet-but-fine, lower diligence urgency) from Case 2 (hiding-and-bad, higher
diligence urgency) **at all** — both render identically (Unavailable, Low confidence), leaving a
reader equally uninformed about which deserves more urgent follow-up, even though *some*
differentiation is possible in principle (stage/dimension expectations from Part 3, plus any
Case-8-style behavioral signal) without ever needing to guess the true number.

**C. Exclude missing evidence from quality but apply a separate completeness/disclosure penalty to
SPS.**
This relocates rather than resolves the Case-1/2 problem: if a "disclosure penalty" reduces the
*displayed* SPS number, then quiet-but-strong companies (Case 1) get a lower headline number than
equally strong companies that happen to disclose everything (Case 3) — the exact "unknown
collapses into weak" failure, just moved from the dimension level to the aggregate level. **Reject
as literally specified.** The underlying impulse — surface a distinct disclosure-risk signal — is
right; it must live *outside* the SPS number entirely, never as a point deduction from it.

**D. Produce an evidence-bounded SPS plus a separate confidence/completeness grade.**
Close to correct: SPS reflects only what's actually knowable, decoupled entirely from a clearly
labeled confidence/coverage/diligence-flag block. This satisfies the non-collapse requirement as
long as the accompanying block is never folded back into the number. Cleanly resolves Cases 1, 2
(differently, via flag framing, not score), 3, 5, 6, 7, 8.

**E. Produce an SPS range/interval when important evidence is missing.**
More visually honest for Case 4 (near-total evidence absence) than a lone point number, but has two
real costs: (1) computing a genuine range requires pessimistic/optimistic bound constants per
missing dimension — this reintroduces the exact invented-constant problem the task explicitly
forbids, now doubled instead of singular; (2) a range is materially harder to use for the
dashboard's stated purpose (rankings/search/sortable per-startup breakdowns per `CLAUDE.md`) — a
range doesn't sort as cleanly as a scalar, and forcing sortability onto a range (e.g., sort by
midpoint) quietly throws away the honesty the range was meant to add.

**F. Recommended synthesis — D as the default, selective suppression instead of a general range.**
Use **D** (point SPS + separate confidence/coverage/diligence-flag block) as the standard
representation. **Do not** adopt a general-purpose numeric range as the primary mechanism — it
trades one fake-precision risk for two. For the genuine extreme case (Case 4: evidence coverage
below a meaningful floor), **suppress the SPS entirely** rather than compute either a misleading
point number or a fabricated range — show only the pillars/dimensions that do have real data plus
an explicit "insufficient evidence for an overall score" message (operationalizing the prior
document's Part 5 minimum-evidence-threshold idea, now sharpened: suppression, not degradation, is
the honest response to near-total evidence absence). A narrower interval *might* be a defensible
future refinement for the "meaningful-but-incomplete" middle ground between "fully evidenced" and
"suppress," but designing that well is nontrivial and is explicitly **not** resolved here — flagged
as open, not glossed over.

---

## Does D actually solve the "must not benefit from hiding" requirement?

**Partially, and this needs to be stated honestly rather than declared solved.**

At the **score-integrity level**, yes: under D, a company that hides weak Retention no longer gets
an artificially deflated *or* artificially inflated number — its Retention score is simply
Unavailable, exactly like an elite quiet company's would be. Neither company's *quality score* is
distorted by the absence.

At the **bare-number-comparison level**, only partially. Recall the original renormalization
example: an honest company disclosing weak Retention=3 landed at pillar score 6.0; the identical
company hiding it landed at 7.0 under plain renormalization. Under D, the hiding company's pillar
score is still computed by excluding the missing dimension from the weighted average (there is no
longer a below-average default to pull it down) — **so the bare number is still 7.0, higher than
the honest company's 6.0.** What D changes is that the 7.0 now travels with `Confidence: Low`,
lower `Evidence Coverage`, and an explicit diligence flag, while the honest 6.0 travels with higher
confidence, higher coverage, and no flag. **A reader who sees the full output would not treat the
hiding company as strictly better** — a 7.0 with a red flag and low confidence is not obviously
more attractive than a fully-transparent 6.0 to a sophisticated investor.

**But this only holds if SPS is never consumed as a bare number in isolation** — and the dashboard's
own stated purpose (`CLAUDE.md`: "rankings, search, and per-startup score breakdowns") includes a
rankings view, which is exactly the kind of consumption where confidence/coverage might not be
weighted into the sort order. **This is a genuinely open, unresolved question this document cannot
close alone**, because it depends on a downstream product decision (does ranking sort by raw SPS,
or by a confidence/coverage-aware measure) that sits outside pure methodology design. Flagging it
explicitly rather than asserting the exploit is fully closed.

---

## Final recommendation

**1. Quality-score semantics.** Unchanged from the Scoring Semantics document's Part 1: an
evidence-bounded estimate of quality, never discounted for the *possibility* that more evidence
exists elsewhere. This review adds one sharpening: it must also never be discounted for the
*probability* that absence reflects weakness, because that probability is not estimable from
silence alone (Cases 1/2).

**2. Missing-evidence semantics.** The seven-case table from the prior document mostly stands, with
two refinements from this review: (a) split "mixed" (Case 2 there) from "conflicting" (a new,
distinct case — sources disagree about one fact, don't average them); (b) **the "expected but
missing" case must never move the quality score** — it may only affect confidence, coverage,
diligence-flag severity, and (in the narrow Case-8 sub-scenario) a separate disclosure-risk signal.

**3. Confidence semantics.** Unchanged from Part 8 of the prior document (rule-gated
High/Medium/Low, not a numeric formula) — that design survives this review intact.

**4. Coverage semantics.** Unchanged: fraction of a dimension's defined evidence surface actually
found, independent of favorability. This review adds: coverage failures must be attributable —
distinguish "the company didn't disclose it" from "SIE's search missed it" (Case 7) wherever
possible, since conflating them misdirects diligence attention toward the company for a system
failure.

**5. Disclosure-risk semantics — new concept, not previously named.** A genuinely distinct fifth
axis, separate from score, confidence, coverage, and completeness: a behavioral signal about
*how* a company or its management responds to being asked for information, populated **only** when
a real, observed refusal or evasion exists (Case 8) — never inferred from ordinary silence (Cases
1/2, which must remain evidentially neutral). Reported as its own labeled item, never folded into
SPS, confidence, or the metric's own score.

**6. Pillar aggregation.** Revise the prior document's Part 4 recommendation: drop the case-6
below-average default entirely. Use the stage-aware expected-dimension denominator only for the
legitimate exclusions (Not-Yet-Applicable, Not-Applicable-Business-Model, Private-Not-Disclosed) —
all of which exclude cleanly, without penalty. "Expected but missing, unexplained" is *not* treated
as a fourth, penalized category — collapse it into the same clean-exclusion treatment as
Private-Not-Disclosed, since this review shows they cannot be reliably told apart from evidence
alone. The only thing that differs between them is diligence-flag *framing* (routine
"request-directly" language vs. an "atypical absence, verify" elevated flag), never the arithmetic.

**7. Overall SPS aggregation.** Same correction, one level up: no pillar-level below-average
default for an entirely-missing pillar. Exclude cleanly; let confidence/coverage/flags carry the
signal.

**8. Whether SPS should ever be suppressed.** Yes — recommend outright suppression (not a
degraded number, not a fabricated range) below a coverage floor, per Case 4. The exact floor is a
product decision needing real data, not derived here.

**9. Whether an SPS range is useful.** Not as the primary mechanism — rejected as introducing a
second fake-precision problem in place of the first, and as materially complicating the dashboard's
sortable-ranking use case. Point SPS + confidence/coverage block (item 15's format) is the primary
representation; suppression handles the extreme case a range would otherwise be reached for.

**10. Exact conditions under which missing information MAY affect the quality score.** Almost
never. The one legitimate path: a genuinely new, directly-observed fact beyond mere absence (Case
8's explicit refusal) may inform a *separate* disclosure-risk signal — but even then, it must not
touch the quality score of the metric in question, which remains Unavailable regardless.

**11. Exact conditions under which missing information MUST NOT affect the quality score.**
Everything else — the dominant category: genuine stage-inapplicability (Case 5), privacy/disclosure
norms indistinguishable between strong and weak companies (Cases 1/2 — the central finding of this
review), and SIE's own research failures (Case 7). In all of these, touching the quality score
manufactures the forbidden "unknown → weak" collapse.

**12. What should happen when expected private evidence is unavailable** (Case 5-style, e.g. Unit
Economics at Series A). Exclude from the quality score; confidence Unavailable for that dimension;
standard (not elevated) diligence-flag language ("recommend requesting in data room"); no score or
SPS impact.

**13. What should happen when management explicitly refuses expected evidence** (Case 8). Exclude
from the quality score (the number is still unknown); elevate diligence-flag severity
("explicitly declined — atypical, warrants scrutiny"); optionally populate the separate
disclosure-risk signal; never let this touch SPS directly.

**14. What should happen when SIE's research fails** (Case 7). Exclude from the quality score;
confidence Low, attributed explicitly to search completeness, not company behavior; use a distinct
flag category ("research completeness note," system-facing) rather than a company-facing diligence
flag, to avoid misattributing a SIE-side gap to company evasiveness.

**15. Whether the below-average-default proposal should be KEEP / REVISE / REJECT.**
**REJECT**, as a general mechanism — confirmed by direct construction (Cases 1/2). The underlying
concern it was meant to address (a company must not benefit from hiding weak evidence) is only
*partially* resolved by its replacement (architecture D): resolved at the score-integrity level,
only conditionally resolved at the bare-number-comparison level, pending an open, unresolved
product-layer question — whether the dashboard's ranking/sort consumption of SPS is
confidence/coverage-aware or treats SPS as a bare sortable number. This document cannot close that
question alone.

---

## Recommended default representation

```
SPS: 78                          (evidence-bounded — reflects only what was found)
Confidence: Medium
Evidence Coverage: 64%
Diligence Flags:
  - Retention: not found in public sources at a stage where it's typically available
    — recommend requesting directly
  - Runway: not disclosed — private-tier data, expected absence at this evidence type
Disclosure Risk: none flagged
```

And for the near-total-evidence-absence case (Case 4):

```
SPS: not displayed — insufficient evidence (coverage 18%, below minimum display threshold)
Available signal: Market pillar only — Team, Product, Execution, Traction, Financial Health
insufficient evidence
Diligence Flags: [full list of gaps]
```

This is, with the two refinements noted above (split conflicting-vs-mixed; add the disclosure-risk
axis and the research-failure-vs-diligence-flag distinction), the representation this review
recommends locking in.

---

## SEMANTICS READY FOR BENCHMARKING: **NO**

What remains unresolved, specifically:

1. **The bare-number ranking question (§ "Does D actually solve...").** Whether the dashboard's
   rankings/search consumption of SPS needs to be confidence/coverage-aware, or whether raw SPS is
   an acceptable sort key given that the full profile page shows the accompanying signals. This is
   a product decision outside pure methodology and materially affects whether the "must not benefit
   from hiding" requirement is actually satisfied in the tool users actually interact with, not just
   in the underlying number.
2. **The minimum-evidence suppression threshold** (item 8/9) — the exact coverage floor below which
   SPS is suppressed is explicitly undetermined here, and needs real data (or at minimum a
   deliberate product decision) rather than an invented constant.
3. **The disclosure-risk signal's design** is new in this review (§5) and has not been stress-tested
   itself — e.g., how it should behave when Case 8 co-occurs with genuinely strong evidence
   elsewhere, or whether it should ever escalate to affecting confidence (this review says no, but
   that call deserves its own dedicated pass before being locked in).
4. **The conflicting-vs-mixed evidence split** (§ Case 6) is a new refinement to the prior
   document's Part 2 that has not yet been reconciled back into that document's seven-case table —
   it currently only exists in this review.
5. **Whether a narrower interval (not a full range) is worth designing for the
   meaningful-but-incomplete middle ground** between full evidence and near-total absence — explicitly
   left open, not designed, in this review.

None of these are reasons to distrust the *directional* conclusions above (reject the below-average
default; adopt architecture D; suppress rather than degrade at the extreme) — but a benchmark
portfolio built before resolving items 1–2 in particular risks calibrating against a scoring
behavior that a subsequent product decision could still materially change.
