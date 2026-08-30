# SPS Discrimination Audit

Phase 10.8A. This is a read-only diagnostic audit over the frozen Phase
10.8 validation evidence (`app/calibration/validation_2026_08/`,
`docs/validation/SPS_REAL_COMPANY_VALIDATION_REPORT.md`). **No
production scoring, methodology, weights, anchors, prompts, VPS,
Fundraising Readiness, Rankings, Discovery, or homepage behavior was
modified to produce this report.** No company was re-run through the
pipeline; every number below comes from the already-frozen
`raw_results/*.json` and `raw_results_summary.json` files, cross-
referenced against the exact live code that produced them
(`app/ai/scoring_methodology.py`, `app/ai/analyze_pillar.py`,
`app/ai/evidence_extraction.py`, `app/ai/pillar_scoring.py`,
`app/ai/scoring.py`).

## 1. Executive Summary

The compression found in Phase 10.8 is not one diffuse phenomenon — it
has at least four distinct, independently identifiable mechanisms, three
of which are provable as **exact structural constants** rather than
statistical tendencies:

1. **Three of six pillars show an *identical*, decimal-exact evidence-
   coverage percentage across the entire 25-company real cohort** —
   Traction = 15.0% for 25/25 companies, Financial Health = 45.0% for
   25/25 companies, Execution = **100.0%** for 25/25 companies, Team =
   75.0% for 22/25 (100.0% for the other 3) (confirmed by the read-only
   script in Section 15, run against the frozen results). This is not
   noise: it is the direct, deterministic consequence of specific named
   scoring dimensions being unreachable (Traction, Financial Health) or
   always reachable (Execution) from website-based input for every
   company, regardless of real quality. This alone accounts for most of
   Traction's and Financial Health's compression, a large share of
   Team's, and it rules out "missing evidence" as the explanation for
   Execution's compression specifically — Execution's evidence coverage
   is complete for every company, so its 0.31 stdev is a pure scoring-
   floor effect (Section 12), not a coverage effect.
2. **A written scoring-stage rule instructs the model not to lower a
   score for sparse evidence** ("do not lower a score merely because
   little evidence was given"), combined with permissive "5-6"/"7-8"
   band language across almost every Inferred dimension. This creates a
   mid-band floor that is explicit in the prompt, not merely emergent.
3. **"Public" dimensions — which their own evidence rule says "must not
   be marked Unavailable" — are being marked Unavailable anyway**,
   for the single highest-weighted dimension in two different pillars
   (Team's Founder-Market Fit, weight 0.25; Financial Health's Runway,
   weight 0.30), for extremely well-documented real companies (Rippling,
   Databricks). This is a rule violation, not a calibration choice.
4. **Fabricated, specific-sounding quantitative "Private" evidence**
   (a dollar-exact cash balance, monthly burn, and ARR) appears in the
   Financial Health "Burn Efficiency" dimension for 3 of the 6
   diagnostic companies, in direct contradiction to each company's own
   upstream research brief, which explicitly listed financial metrics as
   "Important Unknowns." This is evidence hallucination, not anchor
   compression, and is the single most severe individual finding in
   this audit.

Group A does score highest on average (Phase 10.8's finding), but the
mechanism is not "the methodology correctly rewards strength" so much as
"the methodology structurally cannot see most of what would differentiate
strength from weakness, and fills the gap with permissive, occasionally
fabricated, defaults."

## 2. Current SPS Definition

**What SPS currently measures, stated from the code alone:** SPS is a
renormalized weighted average, across six pillars, of whatever fraction
of each pillar's named scoring dimensions the pipeline was able to
extract *some* qualifying public/inferred/private signal for from a
company's own website plus one Tavily research pass — where dimensions
lacking a two-point dated structured metric are silently dropped from
the average rather than scored low, and where a dimension without
strong evidence defaults toward the methodology's mid-band language
rather than toward uncertainty-adjusted caution.

**Candidate intended definition (user-supplied):** "Startup Power Score
measures the strength of a startup as a business and investment
opportunity relative to what should reasonably be demonstrated at its
current stage."

**Where the implementation diverges:**

- The candidate definition implies stage-relative *discrimination* —
  a mediocre later-stage company should score lower than an exceptional
  seed company, stage-adjusted. The implementation does have per-
  dimension `stage_guidance` text pursuing this, but Section 13 (Stage-
  Awareness) below shows the practical effect is closer to stage-
  *insensitivity* than stage-fairness, because the same forces that
  compress scores compress them almost identically at every stage.
- The candidate definition implies "what should reasonably be
  demonstrated" is being checked against real, verified evidence. In
  practice, three pillars' realized evidence coverage is capped at
  identical, structural values (15%, 45%, 75-100%) that have nothing to
  do with any individual company's actual quality — Rippling (a $16B+
  company) and Dome (a pre-seed company) both hit exactly 15.0% Traction
  coverage, for the same underlying code reason.
- The candidate definition implies "strength... as a business" is
  actually observed. Section 5 documents that at least one strength
  claim (Plaid's and Rippling's "$5M cash balance, $400K monthly burn"
  Burn Efficiency evidence) was not observed at all — it does not appear
  anywhere in either company's research brief and is not true of the
  real companies at their real scale.

## 3. Diagnostic Companies

| Company | Group | SPS | Stage (extracted) |
|---|---|---|---|
| Rippling | A | 76.0 | Growth |
| Databricks | A | 67.7 | Growth |
| Plaid | B | 68.2 | Growth |
| Clubhouse | B | 64.9 | Growth |
| Relaw | C | 72.5 | Seed |
| Dome | C | 63.0 | Growth (mis-extracted — see Section 13) |

## 4. Score Trace Architecture

The live pipeline (`app/ai/analyze_pillar.py`) is a two-stage
Evidence/Scoring separation, not a single model call:

```
company_text (website + Tavily research brief)
    |
    v
Stage 1 -- EVIDENCE EXTRACTION (app/ai/evidence_extraction.py)
    per dimension: evidence_status (Observed/Inferred/Unavailable),
    confidence, quoted evidence, signals, missing_information,
    rationale. NEVER produces a score. Governed by
    EVIDENCE_REQUIREMENT_RULES[Public|Inferred|Private].
    |
    v
Deterministic dimensions (Customer Growth, Revenue Growth, Retention,
Growth Velocity, Unit Economics) additionally try to extract
"structured_facts" (a dated two-point series) in this same stage.
    |
    v
Stage 2 -- SCORING (app/ai/pillar_scoring.py)
    receives ONLY the normalized evidence from stage 1 (never the raw
    text again) + the dimension's rubric (question, stage_guidance,
    score_9_10..score_0_2 bands, benchmark_examples). Assigns 0-10.
    Explicit rule: "do not lower a score merely because little evidence
    was given."
    |
    v
Deterministic override (app/ai/analyze_pillar.py::apply_deterministic_overrides)
    for the 5 Deterministic-named dimensions: the Stage-2 LLM score is
    UNCONDITIONALLY DISCARDED and replaced by a pure-Python anchor
    calculation from structured_facts (app/ai/sie_v2_anchors.py) --
    or score=None if structured_facts was never extracted in Stage 1.
    |
    v
finalize_pillar_score() (app/ai/scoring.py)
    weighted average of scorable (non-null, non-Unavailable) subscores,
    renormalized over only those subscores' weights -- unscored
    dimensions are dropped from the denominator, not zeroed.
    |
    v
Pillar score (0-10), pillar confidence (High/Med/Low, informational
only), pillar evidence_coverage % (informational only)
    |
    v
calculate_base_score() (app/ai/investment_score.py)
    weighted average across the 6 pillars using PILLAR_WEIGHTS
    (market .20 / team .20 / product .20 / execution .15 / traction .15
    / financial_health .10), renormalized over pillars that produced a
    score. get_adjustments() always returns []. Result x10 = SPS (0-100).
```

The two facts that matter most for everything below: (1) a dimension
that produces **no** usable evidence is dropped from the weighted
average rather than penalized, and (2) confidence and evidence_coverage
are computed and displayed but never multiply into the score at any
step.

## 5. Databricks vs. Relaw

| Pillar | Databricks (real: $100B+ AI infra leader) | Relaw (real: pre-seed YC F25 legal-tech) |
|---|---|---|
| Market | 7.1 (coverage 45%; Market Growth, Timing, Competitive Intensity all **Unavailable**) | 7.9 (coverage 100%; every dimension scored) |
| Team | 6.7 (coverage 75%; Founder-Market Fit **Unavailable**) | 6.3 (coverage 75%; Founder-Market Fit **Unavailable**; Business Capability scored 5.0/Low confidence) |
| Product | 6.0 | 6.6 |
| Execution | 6.8 | **7.5** |
| Traction | 7.0 (coverage 15%) | 8.0 (coverage 15%) |
| Financial Health | 7.4 | 7.6 |
| **SPS** | **67.7** | **72.5** |

**Why Relaw wins.** Not because Relaw has stronger real-world evidence —
it has *less*, being a company weeks old. It wins because (a) Relaw's
website apparently gave Stage 1 enough surface-level signal to avoid the
"Unavailable" outcome on dimensions Databricks lost (Market Growth,
Timing, Competitive Intensity), pulling Relaw's Market coverage to 100%
vs Databricks' 45%; (b) Relaw's Operational Execution and Burn Efficiency
both landed at 8.0/"Observed"/"High confidence" on the strength of
specific numbers ("$5M ARR from 150 customers... 20% QoQ... LTV:CAC
10:1... $10M funding") that read as fabricated (Section 6) — numbers no
real pre-seed YC company discloses on a marketing site, and that a
company of Databricks' real scale would report in the hundreds of
millions, not $5M. Databricks, more honestly, was left with vaguer,
lower "Inferred"-status language in the same dimension and scored lower
as a direct result of being *more accurately* uncertain.

**Would a reasonable investor consider these equivalent on Execution?**
No. A reasonable investor evaluating "is this company executing well"
would not rate a company with zero delivery history ahead of one of the
best-documented, highest-performing infrastructure companies of the last
decade. The anchor's "5-6"/"7-8" language ("some GTM traction... strong
GTM execution with credible repeatability") is satisfiable by narrative
alone for both, and the fabricated Burn Efficiency evidence tips the
tie toward Relaw specifically.

## 6. Rippling vs. Dome

| Pillar | Rippling (real: Growth-stage HR/payroll platform) | Dome (real: pre-seed YC F25, stage mis-extracted as "Growth") |
|---|---|---|
| Market | **8.8** (coverage 80%) | 5.9 (coverage 35%; Size/Growth/Timing **Unavailable**) |
| Team | 7.0 (coverage 75%; Founder-Market Fit **Unavailable**) | 6.5 (coverage 100%; Founder-Market Fit **scored** 7.0 — Dome is one of only 3/25 companies where this dimension survived) |
| Product | 7.0 | 6.5 |
| Execution | 7.2 | 6.8 |
| Traction | 8.0 (coverage 15%) | 6.0 (coverage 15%) |
| Financial Health | 7.6 | 6.0 |
| **SPS** | **76.0** | **63.0** |

This is the pair where the methodology's directional signal is
*strongest* among the six diagnostics — Rippling beats Dome on every
single pillar, and the 13-point SPS gap is the largest in the entire
25-company cohort. But the gap is still built almost entirely from
Market (+2.9) and Traction (+2.0), both driven by evidence-coverage
differences (80% vs 35%; both at the structurally-fixed 15%, so the
Traction gap here is pure score-band variance within the one dimension
that ever scores, Engagement) rather than differences legible as
"execution" or "team" — Execution and Team differ by well under a point
each, despite Rippling being a mature, revenue-scaled operating company
and Dome being a pre-seed prediction-market startup. Dome's Founder-
Market Fit accidentally scoring (CEO's prior Alchemy/blockchain role
was surfaced) while Rippling's did not (Parker Conrad's well-documented
prior Zenefits history was not surfaced) is a second-order but real
contributor to why the Team gap is smaller than a reasonable investor
would expect.

## 7. Plaid vs. Relaw

| Pillar | Plaid (real: ~$13B fintech infra unicorn, Growth) | Relaw (real: pre-seed YC F25, Seed) |
|---|---|---|
| Market | 7.0 (coverage 20%; only Market Size + Customer Demand scored) | 7.9 (coverage 100%) |
| Team | 6.0 (coverage 75%) | 6.3 (coverage 75%) |
| Product | 5.7 | 6.6 |
| Execution | 7.2 | 7.5 |
| Traction | 8.0 (coverage 15%) | 8.0 (coverage 15%) |
| Financial Health | 8.0 | 7.6 |
| **SPS** | **68.2** | **72.5** |

Relaw outscores Plaid on every pillar except Financial Health. Plaid's
own Financial Health "Burn Efficiency" dimension is the fabrication case
detailed in Section 6 below — a real fintech infrastructure company
processing payments for roughly half of U.S. banked adults, scored on
an invented "$5M cash balance, $400K monthly burn, $1.2M ARR" narrative
that appears nowhere in its own Tavily research brief (which explicitly
lists "financial performance metrics such as revenue, profitability,
and funding amounts" under "Important Unknowns"). Plaid's Market
coverage (20%) is also unusually low for a company this well-documented
— Market Growth, Market Timing, and Competitive Intensity were all
marked Unavailable despite Plaid's competitive landscape (Akoya, Yodlee)
being explicitly named in its own research brief. **This pair is the
clearest case in the diagnostic set of the methodology being unable to
distinguish "we found less to say" from "there is less good to say."**

## 8. Clubhouse vs. Dome

| Pillar | Clubhouse (real: post-peak, Growth) | Dome (real: pre-seed, mis-extracted as Growth) |
|---|---|---|
| Market | 7.0 (coverage 20%) | 5.9 (coverage 35%) |
| Team | 6.0 (coverage 75%) | 6.5 (coverage 100%) |
| Product | 6.7 | 6.5 |
| Execution | 7.0 | 6.8 |
| Traction | 6.0 (coverage 15%) | 6.0 (coverage 15%) |
| Financial Health | 6.0 | 6.0 |
| **SPS** | **64.9** | **63.0** |

The two lowest-scoring companies in the diagnostic set land within 1.9
points of each other for structurally different reasons: Clubhouse's
real-world decline from its 2021 peak (current-state, as designed) vs.
Dome's genuine pre-seed thinness. **Is this defensible?** Partially. It
is defensible in the sense that neither company currently has strong
public evidence of a thriving, scaling business — that much the
methodology gets right, and it is a case where the low end of the range
is at least occupied by two companies a reasonable investor would also
rate cautiously. It is not fully defensible in the sense that these are
different *kinds* of caution (proven decline vs. absence of data) that
a real investor would weigh very differently, and the methodology has no
mechanism to distinguish them — both simply fall through to the same
mid-5s/6s band language.

## 9. Anchor Utilization

Across the 6 diagnostic companies' Team and Execution subscores (36
data points: 6 companies x [4 scored Team dims + 4 Execution dims]):

| Range | Count | % |
|---|---|---|
| 0-2 | 0 | 0% |
| 3-4 | 0 | 0% |
| 5-6 | 15 | 42% |
| 7-8 | 21 | 58% |
| 9-10 | 0 | 0% |

**Unique values observed:** {5.0, 6.0, 7.0, 8.0} only — every single
Team/Execution subscore across all 6 diagnostic companies is an exact
integer from this 4-value set. Not one non-integer, not one value below
5 or above 8, appears anywhere in Team or Execution for any of the 6
companies, including the strongest (Rippling) and weakest (Dome, on
Team's Execution Track Record = 5.0, the only sub-6 value in the set).

**Pillar-level, across the full 25-company cohort** (from Phase 10.8's
`analysis_output.json`): Team min=6.0/max=7.3, Execution min=6.2/max=8.0
— i.e. after weighted-averaging, real pillar scores for 25 genuinely
different companies never left a roughly 2-point-wide corridor centered
on 7, out of a nominal 0-10 scale.

**What would 2, 4, 8, 10 actually require, per the rubric text itself?**

- **Score 8-10 (any Inferred dimension):** requires language like
  "Exceptional... with proof of complex product execution," "efficient
  CAC," "82% gross margin," or a named prior exit — specific, often
  numeric claims that even Rippling and Databricks' own research briefs
  did not supply for most dimensions (evidenced by their frequent
  "Inferred"/Medium-confidence status even at 8.0 — the model is
  reaching 8.0 on inference plus favorable narrative, not hitting the
  literal 9-10 bar's specificity).
- **Score 5-6:** requires almost nothing — "some," "moderate," "adequate,"
  "reasonable... but important unknowns remain" is true of nearly every
  real company's public presence, including the most successful ones,
  because *no* company's own marketing site fully discloses CAC, margins,
  or unit economics.
- **Score 0-4:** per the explicit scoring-stage rule ("do not lower a
  score merely because little evidence was given... only assign a low
  score when the given evidence affirmatively shows weak performance"),
  this band is reachable only when a company's own public materials
  affirmatively admit weakness — something no company's own website ever
  does. This band is not merely rarely reached in this data; the
  scoring rule makes it very difficult to reach at all from
  website-sourced input, for any company, regardless of real quality.

**Conclusion: yes, 8-10 requires evidence specificity most real
companies' public/website presence does not supply, and 5-6 is reached
by default.** Both halves of the hypothesis in Part 6 below are
confirmed.

## 10. Inference Audit

Every "Inferred" dimension (13 of 28 dimensions across the six pillars,
including 3 of Execution's 4 and 4 of Team's 5) is governed by this
evidence rule (`app/ai/evidence_extraction.py`,
`EVIDENCE_REQUIREMENT_RULES["Inferred"]`):

> "Use evidence_status 'Inferred' when at least two credible and
> independent signals support a reasonable conclusion... Do not mark
> this dimension Unavailable merely because quantitative metrics are
> absent -- qualitative signals are enough if at least two exist."

And every dimension's score (Inferred or Public) is governed by this
scoring rule (`app/ai/pillar_scoring.py`, `build_scoring_prompt`):

> "Only assign a low score when the given evidence affirmatively shows
> weak performance -- do not lower a score merely because little
> evidence was given; that was already decided in the evidence-status
> step, which you are not repeating."

**What separates plausible capability from demonstrated capability?**
In the prompt text: nothing explicit. "Inferred" evidence_status is
allowed to earn the same score range as "Observed" evidence_status —
there is no anchor-band language anywhere in `scoring_methodology.py`
that says "Inferred evidence should be scored more conservatively than
Observed evidence at the same apparent strength." Confidence (Low/
Medium) is the only place the "this was inferred, not demonstrated"
signal is recorded — and confidence never touches the score
(`calculate_pillar_confidence` is entirely separate from
`calculate_weighted_score`, confirmed in Section 4 and Phase 10.8's own
Part 15 finding).

**Can missing evidence accidentally become a neutral/mid score instead
of genuine uncertainty?** Yes, and this is not incidental — it is what
the rule quoted above is written to produce. "Genuine uncertainty" would
mean either (a) a lower score reflecting the risk of not knowing, or
(b) Unavailable/no score. The current design deliberately avoids (a) by
instruction, and avoids (b) by the "at least two credible signals" bar
for Inferred status being low enough that a polished company website
(which almost always offers at least two qualitative signals — a
mission statement plus a product description, say) clears it easily.

**Hypothesis: "Current inferred dimensions create a floor around the
middle of the scoring range."** **CONFIRMED**, from two independent
lines of evidence, not merely inferred from the prompt text: (1) the
explicit scoring rule quoted above, which is a written floor-creating
instruction, not just a permissive band; (2) the anchor-utilization data
in Section 9 — 100% of the 36 Team/Execution subscores examined across
6 real, very different companies landed in {5,6,7,8}, with 0% below 5
and 0% above 8.

**What prevents a polished website from receiving strong marks?**
Under the current rules, very little. "Do not infer performance from
brand reputation alone" is the one explicit guardrail in the Inferred
rule block, but there is no equivalent guardrail against inferring
performance from *narrative quality* (a well-written product page, a
confident mission statement) — the fabrication cases in Sections 5-7
show the model going further, inventing specific numbers where the
narrative was compelling enough to seem like it should be backed by
data.

## 11. Team Audit

Data point requiring explanation: Group C mean Team = 6.51 vs. Group A
mean Team = 6.38 (Phase 10.8, Section "Pillar Discrimination").

**Root mechanism identified: Founder-Market Fit (weight 0.25, the
single highest-weighted Team dimension) is marked Unavailable in 22 of
25 companies (88%) across the full validation cohort** — evidenced by
Team's evidence_coverage being exactly 75.0% (i.e. 1.00 - 0.25) for 22
of 25 companies, and exactly 100.0% for the other 3. In the 6-company
diagnostic set, this affected Rippling, Databricks, Plaid, Clubhouse,
and Relaw — every company except Dome. The rationale text is
essentially identical across all five: "no verifiable public evidence
was found demonstrating the founding team's unusually strong insight or
experience in the market." For Rippling (co-founded by Parker Conrad, a
well-known repeat founder whose prior company, Zenefits, is extensively
publicly documented) and Databricks (co-founded by the creators of
Apache Spark, whose academic/technical origin story is one of the most
publicly written-about founding stories in enterprise software), this
rationale is not a defensible "genuinely no evidence exists" conclusion
— it reads as a failure of the evidence-extraction stage to surface
easily available public information, or a failure of the research brief
(Tavily) feeding it, not a real absence of evidence in the world.

**Direct consequence for the Group A vs. Group C question:** because
this is the ONE Team dimension explicitly and only about founder
background/domain pedigree (the dimension most likely to differentiate
a repeat unicorn founder from a first-time pre-seed founder), and it is
disabled for nearly every company regardless of group, Team's remaining
signal comes overwhelmingly from Technical/Business/Leadership/
Execution-Track-Record Capability — all four "Inferred," all four
governed by the same mid-band-floor mechanism from Section 10. Dome
(the one diagnostic company where Founder-Market Fit *did* score, at
7.0) is also the one company pulling Group C's Team mean up in this
small sample — an artifact of which companies happened to survive
evidence extraction, not evidence that YC F25 teams are stronger.

**Answering the phase's A-F options directly:**

- (A) "Team methodology genuinely considers early YC teams
  equivalent/superior" — **not supported.** No dimension's rubric text
  privileges early teams; the effect is incidental.
- (B) "Public-data availability distorts results" — **primary driver**,
  specifically for Founder-Market Fit's near-universal Unavailable rate.
- (C) "Anchors are too broad" — **contributing factor** (Section 10's
  5-6 band language applies here too).
- (D) "Inference substitutes for evidence" — **contributing factor**,
  same mechanism as Section 10, applied to the four Inferred Team
  dimensions.
- (E) "Stage-aware expectations intentionally create this result" —
  **not supported** as the primary driver; stage_guidance text exists
  but the Founder-Market Fit failure is a Public-dimension extraction
  problem, not a stage-conditioned scoring choice.
- (F) is effectively B+C+D combined, which is the actual explanation.

## 12. Execution Audit

Execution's cohort-wide stdev was 0.31 — the lowest of any pillar.
Direct causes, ranked by how much of the effect each plausibly explains:

1. **Three of Execution's four dimensions are "Inferred"** (Go-to-Market,
   Product, Strategic Execution — weight 0.75 combined) and are governed
   by the exact same mid-band-floor mechanism documented in Section 10.
   The fourth, Operational Execution, is nominally "Private" but its
   evidence rule explicitly allows "publicly observable financial
   evidence" as a substitute and explicitly says "do not penalize the
   company because private information is unavailable" — so in practice
   it behaves like an Inferred dimension too, and (Sections 5-7) is
   where the fabricated-evidence cases concentrate.
2. **No dimension-specific mechanism distinguishes demonstrated
   execution from plausible execution.** "Strong GTM execution with
   credible repeatability" (7-8 band) does not require the specific,
   hard-to-satisfy metrics that would separate a company with an actual
   repeatable sales motion from one merely narrating "our GTM strategy
   focuses on...".
3. **Whether mature operating capability can reach 8-10:** rarely, in
   this data — cohort-wide Execution max was 8.0 (not one of 25 real
   companies, including several public/late-stage ones, reached 9+ on
   Execution). The 9-10 band's specificity requirement (Section 9) is
   the binding constraint at the top.
4. **Whether an early startup with no execution history can still reach
   6-7:** yes, directly demonstrated — Relaw (pre-seed, weeks-old
   Execution history) scored 7.5, the highest Execution score of any of
   the 6 diagnostic companies, higher than Rippling (7.2, a real,
   revenue-scaled company).
5. **Whether weak execution is sufficiently penalized:** not clearly
   observable in this data, because no diagnostic company's own public
   materials affirmatively claimed weak execution — which the scoring
   rule (Section 10) makes a near-precondition for a low score. This
   audit cannot confirm the penalty side works, because no case in the
   sample tested it.

**Concrete explanation for the 0.31 stdev:** three of four dimensions
share the mid-band-floor mechanism, the fourth nominally requires
Private evidence but is explicitly told not to penalize its absence,
and the two ends of the scale are both effectively gated (the low end by
the "don't lower for sparse evidence" rule, the high end by an unusually
specific 9-10 bar) — leaving a de facto 2-point corridor (6-8) as the
only practically reachable range for the overwhelming majority of real
companies regardless of actual execution quality. Critically, this
cannot be blamed on missing evidence: Section 15's read-only check
confirms Execution's evidence_coverage is **exactly 100.0% for all
25/25 real companies** — every Execution dimension scores for every
company, every time. Execution is therefore the cleanest single proof
in this audit that the mid-band-floor mechanism (Section 10), not
evidence sparsity, is sufficient on its own to produce severe
compression.

## 13. Stage-Awareness Audit

`stage_guidance` text exists per-dimension and is genuinely stage-
conditioned in its wording (e.g. Execution Track Record: "Pre-seed:
execution can be prototype, discovery, and speed of learning... Series
B+: expect consistent scaling performance"). The scoring-stage prompt
(`build_scoring_prompt`) does pass the extracted stage and instructs the
model to "Apply each dimension's Stage Guidance accordingly."

**But the practical effect, measured against Phase 10.8's own stage-
fairness table, is closer to stage-blindness than stage-fairness**:
Seed-stage mean SPS (69.2) and Growth-stage mean SPS (69.3) differ by
0.1 points across the full 25-company cohort. Two readings, both
consistent with the data:

- **GOOD STAGE FAIRNESS** would predict: SPS varies by real quality,
  with early-stage companies neither systematically penalized nor
  systematically inflated — an exceptional seed company can beat a
  mediocre later-stage one. This audit did NOT find evidence of the
  reverse (no systematic penalty against early companies was observed).
- **STAGE BLINDNESS** would predict: the bar is so forgiving at every
  stage that maturity/evidence barely moves the score at all — this
  audit's mechanism findings (Sections 9-12) directly support this
  reading. The same mid-band-floor and structurally-fixed-coverage
  mechanisms apply almost identically whether the company is Rippling
  or Dome; stage_guidance text exists but the actual score-producing
  rules (the 5-6 band's permissiveness, the "don't lower for sparse
  evidence" instruction, and the Deterministic-dimension coverage
  ceilings) are not meaningfully stage-differentiated in their
  practical effect.

**This audit's conclusion: current behavior is closer to STAGE
BLINDNESS than either GOOD STAGE FAIRNESS or STAGE PENALTY.** It is not
a stage penalty (early companies are not structurally capped low) — but
it is also not fairness in the sense of genuine stage-relative
discrimination, because almost nothing differentiates strongly by
anything, stage included.

**Known stage-extraction errors (documented, not fixed in this phase,
per Phase 10.8's own report):** Dome (real pre-seed YC F25 company)
extracted as stage "Growth"; LunaBill and Bravi (also YC F25) extracted
as "Series A." These were not investigated further here beyond
confirming they still stand unfixed in the frozen data.

## 14. Score-Scale Reachability (0-100)

**Realized pillar-score range across all 25 real companies (Phase
10.8's per-pillar min/max):**

| Pillar | Min | Max | Realized range | % of theoretical 0-10 range used |
|---|---|---|---|---|
| Market | 5.9 | 8.8 | 2.9 | 29% |
| Team | 6.0 | 7.3 | 1.3 | 13% |
| Product | 5.7 | 7.7 | 2.0 | 20% |
| Execution | 6.2 | 8.0 | 1.8 | 18% |
| Traction | 6.0 | 8.0 | 2.0 | 20% |
| Financial Health | 6.0 | 8.4 | 2.4 | 24% |

Not one pillar, for any of 25 real companies spanning pre-seed to
public/multi-billion-dollar, ever scored below 5.7 or above 8.8.

**Is SPS <40 practically reachable?** Only if nearly every pillar
simultaneously landed in the 0-4 per-pillar range. Section 10 established
that reaching 0-4 on any Inferred/Public dimension requires the
company's own public materials to *affirmatively* admit weak
performance — something no company's own marketing site or the
research brief a Tavily search produces is likely to contain. Under
current behavior, this is very unlikely to occur for almost any
website-sourced company, good or bad. Practically unreachable, not by
design intent but by the scoring rule's effect.

**Is 40-59 practically reachable?** More plausible than <40, but still
would require most pillars to land at or below the very bottom of the
5-6 band (5.0-5.5) simultaneously — none of the 25 real companies in
this cohort came close (overall SPS floor was 63.0).

**Is 80-89 practically reachable?** Would require most pillars near 8.5+
simultaneously. The single highest pillar score observed anywhere in
this cohort was Rippling's Market at 8.8 — and that was one pillar out
of six for the single highest-scoring company in the entire 25-company
run. No company's *overall* SPS exceeded 76.0.

**Is 90+ practically reachable?** Would require near-unanimous 9-10 band
language, which Section 9 shows requires evidence specificity
(quantitative CAC, margins, named exits) essentially absent from public/
website-sourced input for every company tested, including the most
prominent ones.

**Conclusion: the 0-100 range is not currently a genuine measurement
range for website/public-research-sourced companies — it is
substantially decorative.** The practically reachable band, under
current anchor language and evidence rules, is roughly 55-90 in theory
and 63-76 in this cohort's actual practice; both tails require
combinations of evidence that essentially never occur from this input
type.

## 15. Root Causes

| # | Finding | Classification | Pillar/Subscore | Companies affected | Code path | Severity | Diagnosis confidence | Overfitting risk if "fixed" from this data alone |
|---|---|---|---|---|---|---|---|---|
| 1 | Traction: 4 of 5 dimensions (85% of internal weight) are Deterministic and require a dated two-point structured series; coverage is *exactly* 15.0% for 25/25 real companies | EVIDENCE REQUIREMENT ISSUE / IMPLEMENTATION | Traction (Customer Growth, Revenue Growth, Retention, Growth Velocity) | 25/25 | `app/ai/analyze_pillar.py::apply_deterministic_overrides`, `app/ai/sie_v2_anchors.py` | **High** | **High** (exact structural constant, not inferred) | Low — this is a reproducible code fact, not a sample-specific pattern |
| 2 | Financial Health: Runway (Public, weight 0.30) and Unit Economics (Private/Deterministic, weight 0.25) unavailable in effectively 100% of cases; coverage exactly 45.0% for 25/25 companies | EVIDENCE REQUIREMENT ISSUE / CONTEXT EXTRACTION | Financial Health (Runway, Unit Economics) | 25/25 | `evidence_extraction.py`, `apply_deterministic_overrides` | **High** | **High** | Low |
| 3 | Fabricated specific quantitative "Private" evidence (exact-sounding cash/burn/ARR figures) in Burn Efficiency, contradicting each company's own research brief | IMPLEMENTATION BUG (evidence hallucination) | Financial Health / Burn Efficiency | 3/6 diagnostic (Rippling, Plaid, Relaw); not yet checked across full 25 | `app/ai/evidence_extraction.py` (Private rule), `pillar_scoring.py` | **High** | **High** for the 3 confirmed cases (verified against each company's own stored research_brief_snapshot) | Low for these 3 specific cases; **NEEDS MORE DATA** to know true prevalence across all 25 |
| 4 | "Public" dimensions marked Unavailable in violation of their own stated rule ("Public dimensions must not be marked Unavailable") | IMPLEMENTATION BUG / CONTEXT EXTRACTION | Team (Founder-Market Fit, 22/25 = 88%); Market (Market Growth/Timing/Competitive Intensity, seen in Databricks, Dome) | 22/25 for Team; at least 2/6 diagnostic for Market | `evidence_extraction.py` | **High** | **High** for Team (quantified); **Medium** for Market (only spot-checked on 2 companies) | Low for Team; needs broader check for Market |
| 5 | Explicit scoring-stage instruction not to lower a score for sparse evidence, plus permissive 5-6/7-8 band language — proven unconfounded by evidence coverage for Execution specifically (coverage is 100.0% for 25/25 companies, yet stdev is only 0.31) | SCORING ANCHOR ISSUE / INFERENCE ISSUE | All Inferred dimensions, most visibly Execution (3/4 dims, 100% coverage) and Team (4/5 dims) | 25/25 (structural, confirmed via anchor-utilization data on 6/25 plus full-cohort coverage check) | `pillar_scoring.py::build_scoring_prompt`, `scoring_methodology.py` band text | **High** | **High** | Medium — re-anchoring language risks overfitting to this cohort's specific phrasing if not validated on a second cohort |
| 6 | Confidence/evidence_coverage never discount the score itself | AGGREGATION ISSUE / CONFIDENCE-EVIDENCE ISSUE | All pillars (most visible: Traction at 15% coverage/Low confidence still fully weighted) | 25/25 | `app/ai/scoring.py::calculate_weighted_score`, `investment_score.py::calculate_base_score` | **Medium** | **High** (architecturally confirmed, restated from Phase 10.8) | Medium — any fix here is a scoring-formula change with wide blast radius |
| 7 | 9-10 band language requires evidence specificity (named metrics, named exits) rarely available from website/public-research input | SCORING ANCHOR ISSUE | All pillars' top band | 25/25 (no pillar exceeded 8.8 anywhere in the cohort) | `scoring_methodology.py` `score_9_10` text | **Medium** | **High** | Medium |
| 8 | Company-stage mis-extraction for at least 3 real pre-seed companies (Dome, LunaBill, Bravi) | CONTEXT EXTRACTION ISSUE | Upstream of all pillars for the affected companies | 3/25 | (not isolated in this audit; documented in Phase 10.8) | **Medium** | **High** | Low (factual correctness issue) |

## 16. Priority Findings

- **P0 — Fabricated quantitative evidence in Financial Health (Finding
  3).** This is a credibility/trust issue independent of scoring
  calibration: the product currently can present invented numbers as
  "Observed," "High confidence" evidence. This should be scoped and
  fixed before any anchor-recalibration work, and its prevalence across
  the full 25-company cohort (not just the 6 diagnostics) should be
  checked first.
- **P0 — Deterministic Traction/Financial-Health dimensions structurally
  unreachable from website input (Findings 1, 2).** These are exact,
  reproducible, code-level facts, not statistical impressions — the
  lowest-overfitting-risk findings in this entire audit precisely
  because they don't depend on this specific 25-company sample at all.
- **P0 — "Public" dimension marked Unavailable in violation of its own
  rule, at the highest-weight position in two pillars (Finding 4).**
  Especially damaging for Founder-Market Fit, arguably the single
  dimension most capable of differentiating founder quality across
  stages — its near-total (88%) unavailability actively removes the
  signal most likely to validate the product's own "strength relative
  to stage" definition.
- **P0 — Mid-band floor from explicit scoring instruction + permissive
  band language, for Execution specifically (Finding 5).** Elevated to
  P0 rather than P1 because Execution's 100.0%-for-25/25 evidence
  coverage rules out the "it's just missing evidence" explanation
  entirely — this is the cleanest, least-ambiguous proof in the audit
  that the scoring rule/anchor language alone is sufficient to produce
  severe compression, independent of any evidence-availability
  confound. Team and other Inferred dimensions (Finding 7) remain P1:
  real and well-evidenced, but with more evidence-availability confound
  than Execution, so higher overfitting risk to fix from this single
  cohort alone — recommend a second validation cohort before touching
  that language.
- **P1 — Confidence/evidence never discounting SPS (Finding 6).**
  Architecturally significant but the widest-blast-radius change of
  the set; needs its own dedicated design phase, not a quick patch.
  Restated from Phase 10.8, not new to this audit.
- **P2 — Stage-guidance text exists but doesn't visibly change outcomes
  (Section 13).** Worth investigating further with a stage-focused
  cohort (e.g. multiple companies at the identical real stage with
  visibly different real quality) before concluding this needs a
  structural fix.
- **NO CHANGE — PILLAR_WEIGHTS (market/team/product/execution/traction/
  financial_health at .20/.20/.20/.15/.15/.10).** Nothing in this audit
  points at the pillar-level weighting scheme itself as a driver of
  compression; the compression originates inside pillars, not from how
  pillars are combined.

## 17. What Should NOT Change

- **`PILLAR_WEIGHTS`** — no evidence in this audit implicates the
  pillar-level weighting; changing it would not address any root cause
  found here.
- **The Deterministic/fail-closed contract itself** (Part 8 of the v2
  spec: a Deterministic dimension's score must be Python-computed or
  absent, never an LLM guess) — this is a sound integrity guarantee. The
  problem is that its structured-facts precondition is rarely met from
  website input, not that the fail-closed behavior is wrong. Removing
  fail-closed behavior would trade a coverage problem for a correctness
  problem, which is worse.
- **The general Public/Inferred/Private evidence-requirement framework**
  — the three-tier design itself is reasonable; Finding 4 is a case of
  the *implementation* not honoring the framework's own stated rule, not
  evidence the framework's concept is wrong.
- **Stage_guidance text as a concept** — worth investigating why it
  isn't visibly moving outcomes (Section 13), but there's no evidence
  here that removing or simplifying it would help; it may simply need a
  stronger enforcement mechanism than free-text guidance in a single
  scoring prompt.

## 18. Questions Phase 10.8B Must Answer

1. Does the Burn Efficiency fabrication pattern (Finding 3) recur across
   the full 25-company cohort, or was it concentrated in the 3
   diagnostic cases found here? This needs a targeted check before any
   fix is scoped.
2. Is the "Public dimensions must not be marked Unavailable" rule
   violation (Finding 4) a prompt-following failure specific to Founder-
   Market Fit and a few Market dimensions, or does it recur across all
   12 Public-tagged dimensions system-wide?
3. Would tightening the "do not lower a score merely because little
   evidence was given" rule (Finding 5) reintroduce the exact
   evidence-availability bias this rule was presumably written to guard
   against (i.e. penalizing early/thin companies for genuinely having
   less public presence)? This is the central tension Phase 10.8B needs
   to resolve, not assume away in either direction.
4. Is there a design that makes Deterministic dimensions (Traction,
   Financial Health) reachable from richer input sources (e.g. a
   founder-submitted data room or pitch deck) while correctly staying
   Unavailable for website-only input — i.e. is 15%/45% coverage
   specifically a website-input-source problem rather than a permanent
   architectural ceiling?
5. Should evidence_coverage or confidence begin to influence SPS itself,
   and if so, how — a discount, a separate displayed "evidence
   strength" score, or something else? Finding 6 restates that this is
   currently a pure design choice, not a bug; Phase 10.8B needs to
   decide, not this audit.
6. What is the actual cost/benefit of a second, independent validation
   cohort before implementing any anchor-language change, given every
   Priority-1 and Priority-2 finding above carries a real overfitting
   risk if tuned to this specific 25-company sample alone?

---

_Regression/firewall verification and the phase's required final report
are provided in the chat response accompanying this document, not
duplicated here._
