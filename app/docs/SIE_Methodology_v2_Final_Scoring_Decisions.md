# SIE Methodology v2 — Final Scoring Decisions (Frozen Semantics)

**Status: decision document only.** No code changed, no existing methodology document modified,
no calibration run, nothing committed. This closes the five blockers identified in
`SIE_Methodology_v2_Missing_Evidence_Adversarial_Review.md` with single, final design decisions —
it is not another open-ended audit.

**Core principle, restated as the test every decision below must pass:** SPS represents
evidence-supported quality. Missing information is never converted into negative quality evidence
merely because it is missing. Confidence, coverage, diligence risk, and disclosure behavior are
five genuinely separate concepts and none of them may silently become another.

---

## Part 1 — Ranking semantics

**Company A:** SPS 82, Confidence Low, Coverage poor. **Company B:** SPS 78, Confidence High,
Coverage strong. **Company C:** SPS 85, Confidence Medium, Coverage moderate.

- **A (rank purely by SPS):** rejected — would rank A above B despite B resting on far stronger
  evidence, and low-evidence estimates are inherently higher-variance, so pure-SPS ranking
  systematically over-represents thin-evidence companies at both extremes of any ranked list.
- **B (mathematically confidence-adjust SPS)** and **C (mathematically penalize SPS for
  coverage):** both rejected outright — an arithmetic penalty for uncertainty is a relabeled
  version of the already-rejected "expected-but-missing lowers the score" mechanism, and the task
  explicitly forbids inventing one.
- **D (rank by SPS, expose confidence/coverage prominently):** necessary but not sufficient alone
  — decoration next to an unchanged sort order still shows A above B to anyone scanning the list
  top to bottom.
- **E (minimum-evidence eligibility gate):** necessary, but answers *who may be ranked at all*, not
  *how they're ordered once eligible* — A and C could both clear a gate yet still differ enough in
  reliability to make a shared raw-SPS sort misleading.
- **F (separate rankings into evidence tiers):** the mechanism that actually changes the ordering
  users see, and does it without arithmetic: within a tier of comparable evidence quality, a raw
  SPS comparison is legitimate (like-for-like), so "quality ≠ certainty" is preserved by
  **segmentation, not subtraction.**

**Recommended production design (single, final): eligibility-gated, evidence-tiered ranking, with
full confidence/coverage/eligibility metadata always displayed.**
1. Apply the eligibility gate (Part 2) — below it, a company is not shown in comparative rankings
   at all.
2. Among eligible companies, assign an evidence tier from confidence/coverage (e.g.,
   "Well-Evidenced" vs. "Limited-Evidence but Eligible" — tier count and boundaries are a
   calibration output, not decided here).
3. **Sort by SPS only within a tier**, never across tiers.
4. Confidence, coverage, and eligibility status are always shown next to rank position — never
   optional, never buried on a secondary page.

Applied to the example: A (Low confidence, poor coverage) very likely fails eligibility or lands in
the lowest tier — it would not appear ranked above B in the primary view even though 82 > 78. C's
placement depends on where the (not-yet-numerically-set) tier boundary falls — that boundary is a
calibration output, not a blocker to adopting this design now.

---

## Part 2 — Ranking eligibility

**Confirmed: SPS may exist with incomplete evidence; public/comparative rankings require a
separate, stricter minimum-evidence eligibility gate.** A profile page makes a claim about one
company; a ranking makes a claim about *relative order* across companies whose evidence bases may
differ wildly — that comparative claim needs a higher evidentiary floor than a single number does.

**Eligibility, defined conceptually (no numeric thresholds):**
- **Minimum scoreable-pillar representation** — a meaningful fraction of the six pillars must have
  at least one scored dimension; a company built almost entirely from one pillar shouldn't be
  compared against companies scored across all six.
- **Minimum coverage, measured against the stage-appropriate denominator, not the fixed
  30-dimension universe** — coverage must be computed against *what should be knowable at this
  company's stage* (per the stage-conditional matrix). Measuring against the full fixed universe
  would structurally fail every Pre-Seed company for a reason that has nothing to do with genuine
  evidence thinness — this is a load-bearing design constraint, not a detail.
- **Load-bearing pillars** — some pillars (candidates: Market, Team, given their foundational
  weight in the methodology) may need to have *some* representation for eligibility, as a
  condition distinct from the general pillar-count rule. Exact pillar list is a calibration/domain
  call, not fixed here.
- **Stage-aware expectations** — the eligibility bar itself scales with what's expected at the
  company's stage, exactly mirroring the coverage-denominator point above; a Pre-Seed and a Series
  B company should not face the identical bar.
- **Source quality / excessive inferred evidence** — eligibility should also weigh *how* the
  coverage was achieved: a profile built entirely from Inferred/proxy evidence with no direct facts
  is a different eligibility case than the same raw coverage % built on direct, corroborated
  evidence — high coverage should not be achievable purely through inference chains.

**What the benchmark/calibration process must determine numerically** (explicitly deferred, not a
blocker): the minimum pillar-representation fraction; the minimum stage-adjusted coverage %; the
list of load-bearing pillars, if any; the maximum acceptable share of purely-inferred evidence; and
the tier boundaries used in Part 1's ranking design.

---

## Part 3 — SPS suppression

- **A — enough evidence for a useful estimate:** display normally (point SPS + full
  confidence/coverage/flag block).
- **B — enough evidence for a low-confidence estimate:** **display it, clearly labeled** — a
  labeled, low-confidence, low-coverage number is still more useful to a reader than nothing, as
  long as *some* real evidence exists to ground it. Suppression is reserved for C, not extended to
  B.
- **C — insufficient evidence for any defensible scalar:** **suppress the SPS entirely.** Refined
  response, correcting the earlier example's inconsistency (showing a per-SPS confidence value when
  there is no SPS for it to describe):

```
SPS: Not enough evidence for an overall score
Evidence Coverage: 18%
Available signal: [per-pillar partial scores/confidence where any exist]
Diligence Flags: [full list of gaps]
```

No SPS-level confidence field in case C — confidence describes a score, and there isn't one.
Pillar-level partial data is still shown where it exists; the page is never blank, and no top-line
number is fabricated. The exact coverage floor separating B from C is a calibration output, not
decided here — per the task's own instruction, this does not block readiness.

---

## Part 4 — Disclosure risk (narrow design)

Classifying the seven listed behaviors:

| Behavior | Disclosure risk? | Actual routing |
|---|---|---|
| Evidence simply not public | **No** | Ordinary Unavailable (Private-Not-Disclosed or Not-Yet-Applicable) |
| SIE research failed | **No** | System-side "research completeness" note — never attributed to the company |
| Management has not been asked | **No** | No behavior has occurred yet to observe — Unavailable, no flag at all |
| Management says metric is unavailable/not tracked | **No, mild context only** | A low-severity note distinguishing "stated as untracked" from true silence — not a risk flag |
| **Management explicitly refuses an expected metric** | **Yes — the only true case** | Elevated diligence flag; the sole trigger for the disclosure-risk signal |
| Management provides contradictory numbers | **No — misfiled if treated as disclosure risk** | This is Conflicting Evidence (Part 5), a data-reliability issue, not a concealment-behavior issue |
| Management provides unverifiable claims | **No — misfiled if treated as disclosure risk** | Weak/unverifiable voluntary disclosure — routed to standard weak-evidence handling (Unavailable/low confidence) plus a mild "unverifiable, request support" note; they engaged, they just didn't provide evidence |

**Disclosure risk is designed narrowly on purpose: it is triggered by exactly one thing —
observed, explicit refusal of an expected, specifically-requested metric. Never by silence, never
by a system-side gap, never by a hedge, never by unverifiable marketing language.** This is the
direct enforcement of "only observable behavior may affect disclosure risk; silence alone must not
imply concealment."

**Final recommendation on effect:** disclosure risk **never affects SPS or Confidence** (both would
reopen the collapse this entire design chain exists to prevent). It **remains a distinct, separately
labeled diligence signal**, and it **may affect ranking tier/eligibility** — a company that
explicitly stonewalls an expected metric can be capped below the top ranking tier or carry an
explicit ranking-page caveat, independent of its SPS. This is the one legitimate, narrow channel
through which a behavioral signal reaches the comparative-ranking layer without ever touching the
quality number.

---

## Part 5 — Mixed vs. conflicting evidence

**Mixed:** multiple credible facts, all simultaneously *true*, pointing different directions about
quality (e.g., very high growth + weak retention — both real, at once).
- **Score:** a real, synthesized number reflecting the net read of the tension — never a mechanical
  average of "what each fact alone would imply."
- **Confidence:** can be Medium-to-High — the evidence is clear on both sides, just not univocal;
  "mixed but clear" is not automatically "uncertain."
- **Coverage:** unaffected — coverage measures whether evidence was found, not whether it agrees.
- **Diligence flags:** always generated, naming the specific tension explicitly (e.g., "high growth
  co-occurring with weak retention — verify durability").

**Conflicting:** sources disagree about the *same* underlying fact — only one can be true (e.g.,
company states $5M ARR; a credible filing states $3M ARR for the same period).
- **Score:** never average the disagreeing figures — that fabricates a hybrid neither source
  supports. If one source is clearly more credible/authoritative, score from that source with a
  note that a conflicting lower-credibility claim exists. If credibility is genuinely ambiguous
  between the sources, treat the fact as unresolved and the dimension as approaching Unavailable
  rather than force a number.
- **Confidence:** capped Low regardless of path — the existence of a serious, unresolved
  disagreement is itself informative of uncertainty.
- **Coverage:** the fact was technically found (arguably twice) — coverage stays counted; the
  unreliability is confidence's job, not coverage's.
- **Diligence flags:** always generated, and phrased as a *verification* flag ("sources disagree,
  reconcile before relying on either figure") — a different action, and a different flag category,
  than a Mixed-evidence tension flag.

---

## Part 6 — SPS intervals

Evaluated against interpretability, fake precision, ranking compatibility, user understanding,
statistical defensibility, and implementation complexity: a range (e.g., "72–84") is intuitively
graspable at a glance, but generating *defensible* bounds requires either a real population-level
prior model (which needs calibration data this system doesn't have yet — the same "v3, not now"
Bayesian path flagged in the earlier documents) or an invented heuristic (e.g., "±X points per
missing dimension") — which is exactly the fake-precision problem restated with two numbers instead
of one. Ranges also sort poorly (breaking the ranking design in Part 1, which already solves the
"how much to trust this" problem via tiering, making a range redundant for that purpose) and can
paradoxically communicate *false* precision about their own edges even while trying to communicate
imprecision about the center.

Per the task's own tiebreak instruction — reject ranges absent a strong, defensible
bound-generation methodology — and no such methodology currently exists:

**SPS RANGE: REJECT.** Point SPS + Confidence + Coverage + tiered ranking (Parts 1–3) already
carries the epistemic content a range would add, without inventing bounds. Reopen only if a real
population-prior model is built later — a distinct, data-dependent decision, not a blocker today.

---

## Part 7 — Canonical Startup Profile header

```
Startup Power Score: 78
Confidence: Medium
Evidence Coverage: 64%
Ranking Eligibility: Eligible / Limited / Not Eligible
Diligence Flags: 3
```

- **Startup Power Score (78):** the evidence-bounded estimate of this company's investment-relevant
  quality, computed only from what was actually found — never discounted for what wasn't.
- **Confidence (Medium):** how much to trust that this specific number reflects a well-supported
  read of the evidence, independent of whether the company itself is good or bad.
- **Evidence Coverage (64%):** how much of the methodology's defined, stage-appropriate evidence
  surface was actually found, independent of whether it was favorable.
- **Ranking Eligibility (Eligible/Limited/Not Eligible):** whether this company's evidence base is
  complete and reliable enough to be meaningfully compared against others in a ranked list.
- **Diligence Flags (3):** the count of specific, human-actionable follow-up items — missing
  expected data, mixed signals, conflicting sources, or refusals — worth chasing before relying on
  this analysis.

**Confidence stays categorical (Low/Medium/High)** — final, not reopened. A numeric confidence
score would claim a precision the underlying judgment (a rule-gated ordinal assessment, not a
measurement) cannot support.

**Coverage is both numeric and categorical.** Unlike confidence, coverage has a real countable
numerator/denominator (evidence-priority items found, over what's expected at this stage) — showing
the exact percentage is not fake precision, it's an honest count. A derived categorical band (e.g.,
"64% — Moderate") should sit alongside it for at-a-glance scanning, computed *from* the percentage,
never invented independently of it.

---

## Part 8 — Gaming stress test

1. **Hides weak retention.** Retention → Unavailable, no score penalty (per the earlier REJECT of
   the below-average-default mechanism) — but coverage drops, Traction-pillar confidence can't
   reach High, and the company likely lands in a lower ranking tier. The bare SPS number may still
   be numerically higher than an honest peer's, but it will not be ranked *alongside or above* that
   peer in the primary comparative view — tiering, not score math, closes the gap the earlier
   review left open. **No unjustified score advantage; ranking advantage is structurally blocked.**
2. **Discloses strong retention.** Real high score, high confidence, full coverage credit, likely a
   higher evidence tier. Correctly rewarded on every axis. **No issue.**
3. **Discloses weak retention.** Real low score (honest), but decent-to-high confidence (direct,
   clear evidence) and — critically — *better* coverage/tier standing than scenario 1's company,
   since disclosure itself improves coverage regardless of favorability. **Honesty never costs
   coverage or eligibility, only ever costs the score to the extent the truth is genuinely bad — the
   correct trade-off.**
4. **Little public information, not evasive.** Low coverage, low confidence, likely
   Limited/Not-Eligible tier, possibly suppressed (Part 3) — but no disclosure-risk flag (silence
   never implies concealment) and no score penalty beyond the natural consequence of fewer
   dimensions being scoreable. **Correctly treated as "unknown," not "bad."**
5. **Famous company, enormous public coverage.** Naturally high coverage/confidence/tier — but
   coverage measures whether evidence was *found*, not whether it's *favorable*; a famous company
   whose abundant coverage reveals genuine weaknesses still scores those weaknesses honestly. **The
   advantage fame confers is trustworthiness of the conclusion, not favorability of it — the correct
   kind of advantage, not a gaming vulnerability.**
6. **Early-stage, legitimately little evidence.** Coverage measured against the stage-appropriate
   denominator (Part 2) means this company isn't penalized for lacking dimensions that were never
   expected yet. **Confirms Part 2's design choice is load-bearing, not decorative.**
7. **Floods the web with low-quality PR.** A genuine, previously-unflagged vulnerability: naive
   coverage measurement (raw source count or mention frequency) could be inflated by volume without
   substance. **Closing this now:** coverage must count *substantive, credible* findings against
   each `evidence_priority` item, not raw source volume — and the confidence model's existing
   source-quality/credibility gate must discount PR-only, uncorroborated content, keeping such a
   profile's confidence low and its ranking tier no better than a genuinely thin one, regardless of
   apparent coverage.
8. **Explicitly refuses diligence information.** Score/confidence for the refused metric untouched
   (still Unavailable — refusal doesn't reveal the number), disclosure-risk flag fires, ranking
   tier/eligibility may be capped. **Working exactly as designed — the one case where a
   behavior-triggered consequence at the ranking layer is intentional.**

**Verdict: no scenario produces an unjustified score advantage.** The one real structural gap
carried over from the adversarial review (a hiding company's bare SPS number can still exceed an
honest peer's) is resolved at the correct layer — ranking/comparison via tiering and eligibility,
not the score itself — consistent with the whole design chain's finding that fixing this in the
score always reintroduces the "unknown → weak" collapse. One new vulnerability (PR-volume gaming
coverage) is identified and closed via a substance/credibility requirement on what counts as
coverage.

---

## Part 9 — Frozen canonical specification

| Concept | Definition | Affects | Does NOT affect | Affects SPS? | Affects ranking eligibility? |
|---|---|---|---|---|---|
| **QUALITY SCORE (SPS)** | Evidence-bounded estimate of quality, computed only from evidence found, at face value | The content/favorability of found evidence | Absence of evidence for any reason, confidence, coverage, tier | — | No |
| **CONFIDENCE** | How much to trust a produced score | Coverage adequacy, direct-vs-inferred mix, source agreement, recency, stage-appropriateness, source credibility | Favorability of evidence, disclosure risk, stage per se (only whether evidence meets *that* stage's bar) | No | Yes, indirectly (feeds tier) |
| **EVIDENCE COVERAGE** | Fraction of the stage-appropriate, substantive evidence surface actually found | Substantive findings relative to what's expected at this stage | Favorability, reliability (that's confidence's job), disclosure behavior | No | Yes, directly |
| **RANKING ELIGIBILITY** | Whether the evidence base is complete/reliable enough for meaningful comparison | Coverage, pillar representation, evidence-quality mix, explicit disclosure-risk refusal | The SPS number itself | No | — |
| **DILIGENCE FLAGS** | Human-actionable follow-up items | Mixed evidence, conflicting evidence, expected-but-missing gaps, refusals, unverifiable claims | Nothing — purely additive/descriptive | No | Only the refusal sub-type, indirectly |
| **DISCLOSURE RISK** | Narrow signal: management explicitly refused an expected metric | Only observed refusal | Silence, absence, thinness, research failure, hedged answers, unverifiable claims | No | Yes — may cap tier |
| **UNAVAILABLE** | Binary state: no evidence exists to anchor any score, with sub-types differing only in flag framing | Literal absence of evidence | Nothing scores it | No direct contribution; excluded from the weighted average | Yes, cumulatively (via coverage) |
| **MIXED EVIDENCE** | Multiple credible, simultaneously-true facts implying different things | Genuine, non-contradictory tension | Source disagreement on one fact (that's Conflicting) | Yes — a real synthesized number | No direct effect (flag only) |
| **CONFLICTING EVIDENCE** | Sources disagree about the same fact | Genuine source disagreement | Multiple different facts merely pointing different ways (that's Mixed) | Indirectly — score from the more credible source, or Unavailable if ambiguous; never averaged | No direct effect beyond confidence/flag consequences |

---

## Part 10 — Benchmark readiness

1. Ranking semantics: **RESOLVED**
2. Suppression semantics: **RESOLVED**
3. Disclosure risk: **RESOLVED**
4. Mixed vs. conflicting evidence: **RESOLVED**
5. SPS ranges: **RESOLVED**

No genuine conceptual contradiction remains. Every open item still on the table (tier boundaries,
coverage floors, eligibility fractions, load-bearing pillar list, minimum-inferred-evidence cap) is
a numeric threshold — exactly the category the benchmark portfolio exists to determine, not a
blocker to building it.

## SEMANTICS READY FOR BENCHMARKING: **YES**

**Exact next step:** construct the 20-company historical-snapshot benchmark portfolio as already
designed in `SIE_Methodology_v2_Audit.md` (Part 7) — gather and write the historical-snapshot input
data for those companies (or a refined equivalent list), score them under the v2 rules frozen across
this document and its predecessors, and use the results to determine the numeric constants
repeatedly deferred here: the eligibility coverage/pillar-representation thresholds, the ranking-tier
boundaries, the SPS-suppression coverage floor, the maximum-inferred-evidence cap, and the
load-bearing pillar list. This is the next task to scope, not to start here.
