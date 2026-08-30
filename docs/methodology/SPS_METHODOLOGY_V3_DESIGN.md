# SPS Methodology V3 Design

Phase 10.8D. **This is a design document. Nothing in this phase changed
production code, V2.1, prompts, anchors, the database schema, the
frontend, or any historical score.** No company was re-run. No new
cohort was selected or run. This document is the sole deliverable.

> **Superseded in part by Phase 10.8E.** `docs/methodology/
> SPS_V3_RULEBOOK.md` and `SPS_V3_CALIBRATION_PLAN.md` re-examined this
> document's proposals and revised several: the 35%/40% coverage
> thresholds and the Market+Team-specific publishability gate are
> replaced; the confidence-not-Low publishability gate is reversed; the
> explicit high/low-score gates (Parts "High Score Semantics"/"Low Score
> Semantics" below) are removed as redundant; Strategic Execution moves
> from Category C to Category B (Category C is now empty); and Usability/
> Operational Execution/Burn Efficiency/Runway receive concrete
> REDESIGN/SPLIT/MERGE resolutions instead of open placeholders. This
> document's architecture, three-axis design, and canonical-evidence
> concept stand as the foundation 10.8E builds on and are not superseded.

---

## Executive Summary

Four validation/audit phases (10.8, 10.8A, 10.8B, and a fresh
high-strength sanity check) converged on the same underlying finding
from different angles: **V2/V2.1's numbers are produced by asking an
LLM to directly choose a 0-10 dimension score from narrative evidence,
and every defect found so far — mid-band clustering, evidence
fabrication, Public dimensions wrongly marked Unavailable even with
strong retrieved evidence (SpaceX), structural Traction/Financial-Health
coverage ceilings — is a direct or indirect consequence of that one
architectural choice.** V2.1's fixes (a stricter scoring rule, a
provenance guard, confidence caps, rewritten anchor text) measurably
helped but are all *mitigations layered on top of* an LLM that still
makes the final numeric call. The SpaceX defect discovered after V2.1
shipped — strong, correctly-retrieved evidence discarded by an
evidence-classification judgment stricter than its own written rule —
is proof that prompt-level mitigation has a ceiling.

V3's proposed fix is structural, not another mitigation: **move the
LLM's role from "producer of the score" to "producer of structured,
falsifiable observations," and give deterministic, versioned code sole
ownership of what those observations are worth.** This document defines
what SPS should mean, designs a three-axis output (Power / Coverage /
Confidence), classifies every one of the current 28 dimensions against
how deterministic each one can honestly become, and designs the
canonical evidence layer, aggregation rules, publishability gates,
explainability trace, and calibration/validation plan that architecture
requires. It also honestly identifies where full determinism is not
achievable (Strategic Execution, most clearly) and recommends against
pretending otherwise.

**Recommendation, stated up front and justified in Part 37: Option C
(eliminate direct LLM numerical scoring) as the target architecture,
implemented pragmatically — the large majority of dimensions redesigned
as Category B (LLM performs controlled classification, code owns the
score), a small, explicitly bounded set kept as disciplined Category C
(constrained qualitative judgment with a fixed label set, never a free
0-10 number), and zero dimensions left as pure free-form LLM scoring.**
This is a V3.0, not a V2.2 — the meaning and derivation of SPS changes
materially enough that calling it a point release would misrepresent it
to anyone reading a stored `methodology_version`.

---

## Current Architectural Problem

Restated precisely, because "the scores are compressed" undersells it:

1. **The LLM is asked, in one prompt call per dimension, to both decide
   what a number means and pick the number.** `pillar_scoring.py`'s
   rubric gives the model band *descriptions* (score_9_10 through
   score_0_2 as English sentences), not a decision procedure — the
   model free-associates from evidence to a number. Two runs of the
   same evidence through the same prompt are not guaranteed to produce
   the same score (temperature is 0, which helps, but wording
   sensitivity and provider-specific behavior remain).
2. **"Evidence sufficiency" is judged by the same free-form mechanism**,
   which is how a dimension explicitly marked "Public dimensions must
   not be marked Unavailable" can still end up Unavailable for SpaceX
   with excellent evidence sitting right there in the prompt — the rule
   is prose, competing with other prose, not a mechanical gate.
3. **Fabrication is a predictable consequence, not a random bug.** When
   a "Private" dimension's rubric implicitly expects a number (burn,
   margin) and none exists, an LLM optimizing for "sound rigorous" will
   sometimes invent a plausible one. V2.1's provenance guard catches
   this after the fact; it does not prevent the underlying incentive.
4. **Structural coverage ceilings (Traction 15%, Financial Health 45%,
   both exact constants across every company tested) are a symptom of
   forcing every kind of evidence through the same Deterministic
   two-point-series requirement**, regardless of whether that's the
   right way to prove the underlying concept (see Traction Redesign,
   Part 16).
5. **The result mixes three different questions into one number**:
   how strong is this company, how much could we find out about it, and
   how sure are we. V2.1 computes coverage and confidence but never lets
   either affect the presented number except through a coarse cap.

---

## Definition of SPS

**What SPS measures:** the strength of a startup as a business,
demonstrated by evidence SIE could responsibly evaluate, judged relative
to what a company at its stage should reasonably be able to show.

**What SPS does not measure:**
- A probability of success, exit, or survival.
- Absolute company value, valuation, or size.
- How much information exists about the company (that is Evidence
  Coverage).
- How sure SIE is of its own assessment (that is Assessment Confidence).
- Founder likability, pitch quality, or narrative polish.

**What a higher SPS means:** SIE found specific, credible, stage-relevant
evidence that this company is executing well across most of what a
reasonable investor would check.

**What a lower SPS means:** either SIE found specific evidence of
weakness, or SIE found a company whose demonstrated evidence, relative
to its stage, is thin or ordinary. **These two causes must be
distinguishable in the surrounding coverage/confidence output — SPS
alone is a single number and cannot carry that distinction on its own,
which is exactly why the three-axis architecture (Part 2) exists.**

### Band semantics (stage-relative, not absolute)

| Band | Behavioral meaning |
|---|---|
| 90-100 | Exceptional, specifically-evidenced strength across nearly every pillar, clearly exceeding stage norms, with no material demonstrated weakness anywhere. Rare by construction (Part 21), not by a quota. |
| 80-89 | Strong, specifically-evidenced performance across most pillars for this stage; at most minor, non-structural gaps. |
| 70-79 | Solid, credible evidence of real execution, but with at least one pillar showing only ordinary (not distinguishing) performance, or one real, bounded weakness. |
| 60-69 | Plausible, generally positive picture, but evidence is thin, generic, or covers few pillars with real specificity — not yet demonstrating differentiated strength. |
| 40-59 | Evidence shows a mix of real strengths and real, demonstrated weaknesses, or shows a company meaningfully behind stage-relative expectations in more than one important pillar. |
| 20-39 | Multiple pillars show demonstrated, specific weakness (not merely thin evidence) — declining metrics, disclosed operational failure, or clearly sub-stage performance in dimensions that were actually assessed. |
| 0-19 | Pervasive, specific, disclosed evidence of failure or collapse across most assessed pillars (e.g. disclosed shutdown-adjacent signals, severe disclosed decline, fundamental team/product dysfunction) — not merely "we don't know much." |

**Is 100 theoretically achievable?** Yes, in principle, but only as an
asymptote no real company should be expected to hit — it requires every
pillar to independently reach the 9-10 band with High confidence and
complete coverage, which the design deliberately keeps hard (Part 21).

**What must an 80+ startup demonstrate?** Specific, checkable evidence
of strong stage-relative performance in at least four of six pillars,
with no pillar showing demonstrated (not merely thin) weakness, and
Evidence Coverage/Confidence high enough that the score is not resting
on guesswork (exact publishability gate in Part 15).

**What must a 90+ startup demonstrate?** The above, plus: at least two
pillars in the 9-10 band with High confidence, and no pillar below 7.

**What evidence would justify <50, <40, <20?** Progressively more
specific, affirmative (not merely absent) evidence of weakness — see
Negative Evidence (Part 19) — spread across a larger fraction of the
pillars that were actually assessed. Thin evidence alone, however
sparse, should never by itself justify these bands (Non-Negotiable
Principle 1); only demonstrated weakness should.

---

## SPS Non-Goals

Restated as a checklist so future work can be checked against it
directly:
- Not a leaderboard-optimization target. Not a proxy for fundability.
- Not a replacement for human diligence.
- Not comparable across methodology versions without an explicit
  version label (Part 32).
- Not intended to be reproducible across different evidence — only
  across identical evidence (Non-Negotiable Principle 5).
- Not designed to guarantee a particular distribution shape. A
  methodology that happens to produce a narrow real-world distribution
  because most real companies genuinely cluster is not automatically
  broken; a methodology that produces a narrow distribution because it
  structurally can't discriminate is (this is the actual finding from
  Phase 10.8/10.8A, and V3 targets the latter without chasing the
  former).

---

## Design Principles

The user's ten Non-Negotiable Principles are adopted verbatim as V3's
constitution and are cross-referenced throughout this document rather
than restated in full here. Two operational corollaries worth making
explicit:

- **Corollary to Principle 4 ("hard-code the methodology, not the
  company"):** every deterministic rule in V3 must be expressible and
  reviewable without reference to any specific company name. A rule
  that can only be justified by "this makes Company X score correctly"
  is disqualified by construction, regardless of whether Company X is
  Stripe or an obscure pre-seed company.
- **Corollary to Principle 6 ("adding evidence must not automatically
  increase SPS"):** this rules out any aggregation scheme where adding
  a scorable dimension can only pull a pillar average toward the
  *existing* mean in a way that mechanically favors whichever direction
  the new evidence points, without possibility of it constituting
  negative evidence. Simple renormalized weighted averaging already
  satisfies this (a newly-scored dimension can be lower than the
  existing average, pulling the pillar down); V3 must not regress this
  property while fixing everything else.

---

## Three-Axis Architecture

### A. Startup Power Score (SPS)

A 0-100 number expressing demonstrated startup strength, computed
**only from dimensions that were responsibly scorable** — unavailable
dimensions are excluded from the computation entirely (renormalized),
never treated as zero, average, or any other implicit value.

### B. Evidence Coverage

A 0-100% figure: the fraction of the methodology's total configured
weight that was backed by scorable evidence (Observed or Inferred/
sufficiently-classified, not Unavailable), computed identically at the
dimension, pillar, and overall level. This already exists in V2.1
(`evidence_coverage`) — V3 keeps the concept and makes it load-bearing
for publishability (Part 15) rather than purely informational.

### C. Assessment Confidence

A categorical (Low/Medium/High, unchanged granularity from V2.1) or
optionally continuous measure of how reliable the *evidence backing the
scored dimensions* is — independent of how much evidence exists
(Coverage) and independent of what the evidence says (Power). A company
can have 100% coverage built entirely on Low-confidence Inferred
signals (high coverage, low confidence) or 40% coverage built entirely
on hard Observed disclosures (low coverage, high confidence) — these
are different, both legitimate, and must never collapse into one
number.

**Explicit non-meaning, stated because it is the single most important
sentence in this document:** "Startup Power Score: 87, Evidence
Coverage: 68%, Assessment Confidence: Medium" does **not** mean "87%
probability of success" or "we are 68% sure." Power, Coverage, and
Confidence answer three different questions and none of them is a
probability of anything.

**Should all three exist in V3? Yes.** Coverage and Confidence already
exist in V2.1 as computed-but-cosmetic fields; V3's contribution is
making them structurally necessary (Coverage gates publishability,
Confidence gates which anchor bands a dimension can reach — see Part
12) rather than optional, plus surfacing all three to the product
(Part 31) instead of collapsing them into SPS alone the way the
homepage currently would if it showed SPS in isolation.

---

## Current LLM Dependency (Audit)

Tracing `app/ai/analyze_pillar.py`'s pipeline exactly as it exists today:

| Step | Code path | Classification |
|---|---|---|
| What evidence exists per dimension (Observed/Inferred/Unavailable) | `evidence_extraction.py::extract_pillar_evidence` | **LLM GENERATED** (free-form judgment against prose rules) |
| Structured facts for Deterministic dimensions (two-point series) | same file, `structured_facts` extraction | **LLM CLASSIFICATION → DETERMINISTIC** (LLM extracts typed values; `sie_v2_anchors.py` computes the score in pure Python) |
| Numeric fabrication check | `evidence_provenance.py::apply_provenance_guard` | **DETERMINISTIC** (pure Python, added in V2.1) |
| Dimension score (non-Deterministic dimensions — 23 of 28) | `pillar_scoring.py::score_pillar_evidence` | **LLM GENERATED** (free 0-10 number from prose rubric) |
| Confidence-score cap | `scoring.py::apply_confidence_score_cap` | **DETERMINISTIC** (added in V2.1) |
| Pillar score | `scoring.py::calculate_weighted_score` | **DETERMINISTIC** (weighted average of whatever the LLM produced above) |
| Pillar confidence / evidence coverage | `scoring.py::calculate_pillar_confidence` / `calculate_evidence_coverage` | **DETERMINISTIC** |
| Overall SPS | `investment_score.py::calculate_base_score` | **DETERMINISTIC** (weighted average of pillar scores) |

**How much of final SPS depends on LLM numerical judgment today:**
23 of 28 dimensions (82% of the methodology's dimension count, and a
similar fraction of total weight) have their actual number chosen
directly by an LLM in one free-form call. The 5 Deterministic dimensions
(all in Traction, plus Unit Economics in Financial Health) already
prove the "LLM classifies, code scores" pattern works end-to-end in
this codebase — V3 generalizes it to the other 23.

---

## Recommended V3 Pipeline

```
RAW SOURCES (website, Tavily research)
    |
    v
RESEARCH / RETRIEVAL   -- unchanged in kind from V2.1's four-query
    |                     research_enrichment.py; may itself improve
    |                     independently of V3 (Part 27: model-agnostic)
    v
LLM EVIDENCE EXTRACTION  -- extracts CANONICAL STRUCTURED EVIDENCE
    |                        (Part 6), never a score, never free prose
    |                        alone -- typed fields with value/unit/date/
    |                        source/directly-stated-vs-derived
    v
PROVENANCE VERIFICATION  -- generalizes V2.1's numeric-only guard to
    |                        every typed claim: is this traceable to
    |                        the supplied source text?
    v
CANONICAL STRUCTURED EVIDENCE  -- versioned, immutable per analysis,
    |                              the single frozen input to scoring
    v
DETERMINISTIC DIMENSION EVALUATORS  -- versioned Python rules (Parts
    |                                   8-11) map accepted evidence to
    |                                   score/null + availability_status
    |                                   + confidence + rule_triggered
    v
DETERMINISTIC PILLAR AGGREGATION  -- Part 13
    |
    v
DETERMINISTIC SPS  -- Part 14
    |
    +---> EVIDENCE COVERAGE
    +---> ASSESSMENT CONFIDENCE
    +---> EXPLANATION TRACE (Part 25)
```

**Should this become the V3 architecture? Yes**, with one explicit
carve-out: a small number of dimensions (Part 5's Category C, expected
to be 1-3 of 28) retain a constrained qualitative-judgment step between
"canonical evidence" and "deterministic evaluator" — the LLM there
outputs one label from a small, versioned, fixed set (never a number),
and a deterministic table maps that label to a score. This is
architecturally still "the LLM does not choose the number," just with
an extra classification hop for the handful of dimensions where reducing
judgment to boolean/count facts alone would discard real signal.

---

## Canonical Evidence Architecture

One `CanonicalObservation` shape, reused across all pillars, is
proposed rather than a bespoke schema per pillar (reduces engineering
surface area and gives one place to enforce provenance rules):

```
CanonicalObservation:
  dimension: str
  field: str                      # e.g. "revenue", "founder_prior_exit"
  value: number | string | bool | null
  unit: str | null                # "$", "%", "customers", etc.
  as_of_date: date | null
  prior_value: number | null      # for growth-shaped fields only
  prior_as_of_date: date | null
  directly_stated: bool           # vs. derived/computed
  derivation: str | null          # required if directly_stated is False
  source_excerpt: str             # the literal supporting text
  source_reference: str | null    # URL/title if available
  provenance_status: ACCEPTED | REJECTED_UNTRACEABLE | REJECTED_CONTRADICTED
  extraction_confidence: LOW | MEDIUM | HIGH   # the LLM's own stated
                                                 # confidence in having
                                                 # read the source
                                                 # correctly -- distinct
                                                 # from Assessment
                                                 # Confidence, which is
                                                 # about the METHODOLOGY's
                                                 # confidence in the
                                                 # resulting score
```

Per-pillar field catalogs (illustrative, not exhaustive — the user's
own Part 6 examples are adopted as the starting catalog for Traction,
Team, Market, Product, Execution, Financial Health and are not repeated
verbatim here to avoid duplicating this document's own source prompt).
Key design decisions:

- **No field is required for every company.** A `CanonicalObservation`
  simply does not exist for a field nothing was found for — there is no
  placeholder, no null-with-a-reason at this layer (that classification
  happens one layer up, Part 7).
- **`directly_stated: false` requires `derivation`** — this is how "a
  computed 5:1 ratio from two supported numbers" (flagged as an
  intentional V2.1 test-suite limitation, `test_methodology_v2_1.py`)
  becomes properly representable in V3: the ratio is accepted as a
  derived observation with its two supporting `directly_stated: true`
  inputs cited in `derivation`, rather than being rejected outright the
  way V2.1's token-level guard does today.
- **Multiple observations of the same field over time are allowed and
  expected** (e.g. two `revenue` observations at different
  `as_of_date`s) — this is what lets a Deterministic evaluator compute
  genuine growth without the "structured_facts" special-casing V2.1
  needs today.

---

## Dimension Classification Matrix

All 28 current dimensions, classified. "Proposed scoring mechanism"
sketches the deterministic rule shape at a level sufficient to scope
engineering work — full threshold values are explicitly NOT chosen here
(Part 35: calibration is a separate, later phase).

| Pillar | Dimension | Current req. | Category | Proposed mechanism | Stage-awareness | Availability rule | Major risk |
|---|---|---|---|---|---|---|---|
| Market | Market Size | Public | B | Taxonomy: segment_breadth, cited_estimate_present, buyer_budget_signal → banded table | Same taxonomy, stage changes which bands are "strong" | Unavailable only if zero taxonomy fields populated | Taxonomy could still be gamed by generic claims; needs explicit "named/specific" requirement per field |
| Market | Market Growth | Public | B | Taxonomy: cited_growth_signal, category_momentum_signal, disclosed_company_growth-as-proxy | Same | Unavailable if no fields populated | Company-specific growth used as sole market-growth proxy overstates confidence |
| Market | Market Timing | Public | B (harder) | Taxonomy: regulatory_tailwind, technology_inflection_named, catalyst_named | Same | Unavailable if no fields | Hardest Market dimension to reduce cleanly; risk of taxonomy collapsing to a relabeled free score |
| Market | Competitive Intensity | Public | B | Taxonomy: named_competitor_count, incumbent_dominance_signal, differentiation_vs_competitor_named | Same | Unavailable only if truly zero competitive context found | **This is the exact SpaceX-defect dimension** — redesign directly targets it |
| Market | Customer Demand | Inferred | B (mostly done) | Extend existing lifecycle-override machinery (`sie_v2_anchors.py`) to full taxonomy | Stage-conditioned applicability already exists | Existing `NOT_APPLICABLE` state preserved | Low risk — closest dimension to V3-ready today |
| Team | Founder-Market Fit | Public | B | Taxonomy: domain_experience{NONE/ADJACENT/DIRECT}, repeat_founder, prior_exit, named_customer_insight | Pre-seed weights this taxonomy heaviest | Unavailable only if literally no founder background found at all | **The exact SpaceX-defect dimension** — redesign directly targets it |
| Team | Technical Capability | Inferred | B | Taxonomy: shipped_complexity{NONE/BASIC/MODERATE/COMPLEX}, technical_founder, named_prior_technical_success | Complexity bar rises with stage | Unavailable if no technical signal at all | Complexity classification itself still somewhat judgment-based |
| Team | Business Capability | Inferred | B | Taxonomy: disclosed_revenue_metric, repeatable_motion_evidence, prior_scaling_experience | Stage changes which fields matter | Unavailable if none populated | — |
| Team | Leadership | Inferred | B | Taxonomy: named_hire_count, prior_leadership_role, disclosed_dysfunction (negative-evidence field) | Stage changes bar (pre-seed: founder clarity; growth: named execs) | Unavailable if none populated | Must not conflate "no named hires" with "founder dysfunction" |
| Team | Execution Track Record | Inferred | B | Taxonomy: named_milestone_count, milestone_dated_and_specific | Stage changes what counts as a milestone | Unavailable if none | — |
| Product | Customer Value | Inferred | B | Taxonomy: named_customer_outcome, quantified_outcome, testimonial_specificity | Stage changes evidentiary bar | Unavailable if none | Risk of testimonial marketing copy being over-credited |
| Product | Differentiation | Public | B | Taxonomy: named_differentiator, comparison_to_named_competitor | Same | **This is the second SpaceX-defect dimension** | Redesign directly targets it |
| Product | Usability | Public | **D** | Public sources structurally rarely disclose activation/onboarding data (already flagged internally as `AMBIGUOUS_UNAVAILABLE_DIMENSIONS` in `evidence_extraction.py`) | N/A until redesigned | Redesign should likely move this toward a Private/founder-submitted evidence requirement, or replace with a public-observable proxy (self-serve signup presence, named integration count) | Current dimension may be structurally unassessable from public info; keeping it as-is guarantees chronic near-100% Unavailable |
| Product | Defensibility | Inferred | B | Taxonomy: network_effects_claimed_with_evidence, proprietary_data_claimed_with_evidence, switching_cost_evidence | Same | Unavailable if none | Easy to over-credit unverified claims of moats |
| Product | Adoption Potential | Inferred | B | Taxonomy: named_expansion_path, cross_sell_evidence | Same | Unavailable if none | Overlaps conceptually with Market Size; needs a clear boundary rule |
| Execution | Go-to-Market Execution | Inferred | B | Taxonomy: named_channel, repeatability_evidence, disclosed_efficiency_metric (→A-like once present) | Stage changes bar sharply (founder-led vs. scaled motion) | Unavailable if none | — |
| Execution | Product Execution | Inferred | B | Taxonomy: shipped_evidence, named_integration, disclosed_reliability_metric | Same | Unavailable if none | — |
| Execution | Operational Execution | Private | **D** | Split: quantitative sub-claims (burn/margin/runway-adjacent) move to Deterministic (A) fail-closed; qualitative sub-claims (hiring discipline, process) become B | Same | Deterministic half Unavailable without real disclosed figures; qualitative half Unavailable if no signal | **This is where V2.1's fabrication concentrated** — redesign is the direct fix, not another provenance patch |
| Execution | Strategic Execution | Inferred | **C** (reluctantly) | Constrained label set (e.g. WEDGE_EVIDENCED / WEDGE_PLAUSIBLE_UNEVIDENCED / WEDGE_ABSENT_OR_CONTRADICTED) mapped deterministically; never a free number | Same | Unavailable if no strategy narrative at all | Hardest dimension in the entire methodology to fully decompose without losing real signal |
| Traction | Customer Growth | Public/Det. | A | Keep Deterministic; reframe as part of a redesigned Traction family (Part 16) | Stage changes what "meaningful growth" means | Fail-closed, unchanged | None new |
| Traction | Revenue Growth | Public/Det. | A | Same | Same | Same | None new |
| Traction | Retention | Public/Det. | A | Same | Same | Same | None new |
| Traction | Engagement | Inferred | B | Taxonomy: disclosed_active_user_metric, usage_frequency_signal | Same | Unavailable if none | — |
| Traction | Growth Velocity | Public/Det. | A | Same | Same | Same | None new |
| Financial Health | Revenue Quality | Inferred | B | Taxonomy: recurring_revenue_claimed, contract_length_disclosed, concentration_risk_disclosed (negative-evidence field) | Same | Unavailable if none | — |
| Financial Health | Unit Economics | Private/Det. | A | Keep Deterministic, unchanged | Same | Fail-closed, unchanged | None new |
| Financial Health | Burn Efficiency | Private | **D** | Redesign as Deterministic-only (burn ÷ revenue or burn ÷ run-rate, only when both are real disclosed CanonicalObservations); remove free LLM narration entirely | Later-stage bar for "efficient" rises | Unavailable without both real figures | **The single dimension responsible for the most fabrication cases found in Phase 10.8B's full-cohort audit (18/25)** |
| Financial Health | Runway | Public | **D** | Redesign as Deterministic-first: disclosed runway statement, or cash ÷ burn when both are real CanonicalObservations; remove implicit free-LLM narration | Same | Unavailable without a real disclosed statement or both real inputs | Currently the single most Unavailable dimension in the entire methodology (100% across all 25 real companies audited) |
| Financial Health | (none removed) | | | | | | |

**Count: 5 unchanged Category A (all already-Deterministic Traction/
Unit-Economics dimensions), 19 proposed Category B, 1 proposed Category
C, 3 proposed Category D (Usability, Operational Execution, Burn
Efficiency/Runway treated as one redesign family).** Zero dimensions
remain free-form-LLM-numeric (Category "current default") under this
proposal.

---

## Dimension Scoring Contract

```
DimensionResult:
  dimension: str
  methodology_version: str
  score: float | null              # null unless sufficient evidence
  availability_status: SCORABLE | UNAVAILABLE_NO_EVIDENCE |
                        UNAVAILABLE_INSUFFICIENT |
                        UNAVAILABLE_NOT_APPLICABLE_FOR_STAGE
  confidence: LOW | MEDIUM | HIGH
  evidence: list[CanonicalObservation]   # only ACCEPTED provenance
  coverage_weight: float            # this dimension's contribution to
                                     # pillar coverage if scorable
  rule_triggered: str               # which versioned rule produced the
                                     # score, for the explanation trace
  rationale: str                    # human-readable, generated from the
                                     # rule + evidence, not free LLM prose
  weight: float                     # from config, unchanged pattern
```

**Minimum evidence requirements**, by category:
- **Category A (fully deterministic):** requires the exact structured
  facts its rule needs (e.g. two dated revenue points) — unchanged from
  V2.1's existing Deterministic contract, which already works correctly
  and is not being loosened (Non-Negotiable Principle 4's spirit:
  hard-code the methodology, don't invent data to fill gaps).
- **Category B:** requires at least one populated, provenance-ACCEPTED
  taxonomy field relevant to that dimension. Zero populated fields ->
  `UNAVAILABLE_NO_EVIDENCE`.
- **Category C:** requires the constrained label to be assigned with at
  least one cited `CanonicalObservation` supporting it — a label with no
  supporting evidence is not accepted, full stop.

Quantitative claims (revenue, growth, margin) always require a
quantitative `CanonicalObservation`; qualitative characteristics
(founder domain experience, strategic coherence) never require one —
this directly implements the user's Part 8 instruction and closes the
exact gap that let "credible qualitative signals" rules coexist with
implicit pressure to produce a number (Section 3 above).

---

## Unknown/Unavailable Semantics

Six internally distinct states, collapsed to at most three user-facing
states in the product (Part 31):

| Internal state | Meaning | Collapses to (user-facing) |
|---|---|---|
| Unavailable — No Evidence | Nothing relevant was found or extracted | "Not enough public information yet" |
| Unavailable — Insufficient | Something was found but does not meet the minimum evidence bar (e.g. one taxonomy signal when two are required) | "Not enough public information yet" |
| Unavailable — Private Information | The concept is well-defined and important but the required data is inherently non-public (e.g. real burn rate) | "This typically requires founder-provided data" |
| Unavailable — Not Applicable for Stage | The dimension's own lifecycle rule (already exists for Customer Demand) determined the question no longer applies | Dimension omitted from display entirely |
| Unavailable — Research Retrieval Failure | The retrieval step itself failed (e.g. website blocked) before extraction ever ran | "We couldn't access this company's public information" (distinct from the other four — an infrastructure failure, not an evidentiary one) |
| Unavailable — Conflicting Evidence | Two ACCEPTED observations for the same field materially disagree and neither can be preferred | "Evidence conflicts — under review" (new state; V2.1 has no equivalent) |

**Non-negotiable, restated as an implementation contract:** none of the
six states may ever silently become a numeric score of 0, an average
(5.0-ish), 50% coverage, or a "failure" verdict. Each state is either
(a) excluded from the pillar's weighted average and coverage
denominator identically (states 1-4), (b) surfaced as a distinct,
separately-reported infrastructure failure that blocks the whole
analysis rather than one dimension (state 5), or (c) surfaced but
excluded pending resolution (state 6, new).

**Effect on scoring/coverage/confidence:** identical to V2.1's existing
pattern for states 1-4 (excluded from `calculate_weighted_score`'s
denominator, excluded from the coverage numerator, contributes zero to
weighted confidence) — V3 is not changing this mechanism, only making
the reasons for landing in it far more precise and far less prone to
the SpaceX-style misclassification, because a Category B/C dimension's
availability decision is "did the taxonomy get at least one field
populated with ACCEPTED provenance," a mechanical check, not "does this
feel like enough evidence," a free judgment call.

---

## Deterministic Scoring Architecture

**Is the invariant "frozen canonical evidence + frozen methodology
version = identical scores" achievable? Yes, for Category A and B
dimensions (24 of 28) — this follows directly from them being pure
functions of typed, already-accepted `CanonicalObservation` data plus
versioned Python lookup tables, with no model call anywhere in that
path.** It is **not fully achievable** for the reluctant Category C
dimension (Strategic Execution, or however many the eventual design
settles on): a constrained-label LLM classification step still sits
between evidence and score there, and while the label→score mapping is
deterministic, the label assignment itself is a model call and carries
the same (much smaller, because far more constrained) reproducibility
risk V2.1 has everywhere today. This should be reported honestly rather
than claimed as solved: **V3 achieves the reproducibility invariant for
~85-90% of the methodology's weight and meaningfully narrows, but does
not fully close, the remaining gap.**

Model-provider independence (Part 27) follows directly for the same 24
Category A/B dimensions: if two different LLM providers extract the
same `CanonicalObservation`s from the same source text, scoring is
byte-identical regardless of provider, because scoring never touches
the LLM again after extraction/classification. For Category C, provider
independence is not guaranteed (different providers may assign different
labels from the same evidence) — this is the honest cost of keeping any
Category C dimension at all, and is one more reason to keep that
category as small as this document proposes (1 dimension, not several).

---

## Qualitative Classification Architecture (Category B mechanism)

For every Category B dimension, the LLM's actual output changes from
"a rationale and a 0-10 number" to a fixed-shape object of independently
verifiable fields, e.g. (Founder-Market Fit):

```
{
  "domain_experience": "DIRECT",       // NONE | ADJACENT | DIRECT
  "domain_experience_evidence": "Co-founder was VP Engineering at
    [named prior company] in the same industry for 4 years.",
  "repeat_founder": true,
  "repeat_founder_evidence": "Previously founded and sold [named company].",
  "prior_exit": true,
  "named_customer_insight": false,
  "named_customer_insight_evidence": null
}
```

A versioned Python table then maps combinations of these fields to a
score and confidence — e.g. `DIRECT + repeat_founder + prior_exit` maps
to a fixed high band; `NONE` across every field maps to
`UNAVAILABLE_NO_EVIDENCE` rather than a guessed low number. **Every
field requires a cited `domain_experience_evidence`-shaped string when
true/non-NONE** — an unsupported `true` is rejected by the same
provenance-verification step every other canonical observation goes
through (Part 24), closing the fabrication vector at its source rather
than after the fact.

**Does ANY current dimension truly require direct LLM numerical
scoring?** No — this document does not identify one. The 5 already-
Deterministic dimensions prove the pattern works; the 19 proposed
Category B redesigns above show a taxonomy decomposition exists for
every non-Deterministic dimension except Strategic Execution, where a
decomposition was attempted and judged too lossy (Part 5's entry) —
even there, the proposal is a constrained *label*, not a free number.

---

## Confidence

**Reviewing V2.1's caps (Low→6.0, Medium→8.5, High→10.0):
recommendation is Option (E) — a confidence-adjusted view exists
separately, alongside removing the caps' role in the primary Power
score.**

Reasoning: the caps do mix quality with certainty, exactly as Part 12
asks to check — a genuinely exceptional, specifically-evidenced
dimension that happens to be graded "Medium" confidence (V2.1's
threshold is fairly strict: ≥80% coverage AND ≥40% Observed-weight for
High) is *capped below 9* regardless of how strong its actual content
is. Under V3's Category B/C architecture this problem shrinks (a
taxonomy-backed field with cited evidence is a stronger confidence
signal than V2.1's coarser Observed/Inferred/Unavailable), but the
mixing objection stands on principle. V3's answer:

- **Power Score is computed from the dimension score alone**, no cap.
- **Confidence is reported alongside, at the same granularity as
  today**, computed from the same evidence structure (coverage +
  proportion of Observed-tier/high-extraction-confidence fields).
- **Publishability (Part 15), not the score itself, is where confidence
  becomes load-bearing** — a low-confidence 90 is not hidden by lowering
  it to a fake 60; it is either published honestly as "90, Low
  confidence" (letting the reader weigh both numbers, which is what the
  three-axis architecture is *for*) or, if confidence is catastrophically
  low, the whole SPS is withheld (Part 15) rather than silently
  distorted.

This is a considered reversal of V2.1's approach, not a rubber stamp:
V2.1's caps were a reasonable, fast, deterministic mitigation given the
architecture at the time (an LLM-chosen number that needed *some*
downstream check), and they measurably worked (zero cap activations for
Stripe/SpaceX in practice meant they weren't even the binding constraint
in the one live test available). Under V3's architecture, the far more
precise, field-level confidence signal available makes a blunt score
cap both less necessary and more distorting than reporting the two axes
honestly side by side.

---

## Pillar Aggregation

**Renormalization when dimensions are unavailable: yes, kept** (this is
already V2.1/V2.0 behavior and nothing here found reason to change it)
— but three new, explicit gates are added to prevent one strong
dimension from producing a misleadingly strong pillar:

- **Minimum scorable dimensions per pillar:** at least 2 of the
  pillar's dimensions must be scorable, or the pillar itself becomes
  `UNAVAILABLE` (no score), not a one-dimension average standing in for
  the whole pillar.
- **Minimum pillar coverage:** at least 40% of the pillar's configured
  weight must be scorable (same threshold V2.1 already uses as its
  Medium-confidence coverage floor, reused here for consistency) — below
  that, the pillar score is still computed (for internal/debug use) but
  is marked `below_publication_threshold` and excluded from SPS (falls
  through to the SPS-level renormalization in Part 14, not a fabricated
  substitute value).
- **Pillar Completeness, reported separately from Pillar Strength:**
  Strength = the pillar's score (0-10, only from scorable dimensions).
  Completeness = coverage %. A pillar can be "Strength 9.2, Completeness
  40%" — genuinely strong on what could be checked, genuinely thin
  overall — and the product must show both, never collapse them (Part
  31).

---

## SPS Aggregation

Pillar weights are the frozen V2.1 baseline (Market 20/Team 20/Product
20/Execution 15/Traction 15/Financial Health 10) — **unchanged here**,
per explicit instruction and because no phase to date has found evidence
implicating the weights themselves.

**Unavailable-pillar behavior:** renormalization over scorable pillars
(unchanged mechanism from V2.1), gated by two new, explicit
requirements before SPS is computed at all:

- **Minimum scorable pillars:** at least 4 of 6 pillars must be
  individually publishable (per Part 13's gate) for an overall SPS to
  be computed at all.
- **Minimum critical-pillar representation:** Market and Team — the two
  highest-weighted pillars and, per Phase 10.8A/10.8B's own findings,
  the two most reliably assessable from public information — must both
  be individually publishable. A company with strong Product/Execution/
  Traction but no assessable Market or Team evidence does not get an
  SPS; the missing pillars are too structurally important to paper over
  with renormalization alone.

Worked example from Part 14's own prompt: Financial Health mostly
private, but Market/Team/Product/Execution/Traction well-supported ->
**SPS is still published**, computed over the 5 available pillars,
renormalized, with Financial Health shown as "Unavailable — Private
Information" rather than silently dropped from view.

---

## Publishability Rules

To prevent "SPS 94, Coverage 12%": SPS is published only when **all**
of the following hold simultaneously —

1. Minimum scorable pillars (≥4 of 6, Part 14).
2. Market and Team both individually publishable (Part 14).
3. **Overall Evidence Coverage ≥ 35%** of total methodology weight
   across all pillars combined (a floor below Traction's own known-
   structural 15% + Financial Health's 45%-ish ceiling combined average,
   chosen so that a company hitting only the two known-structural
   ceilings and nothing else in Market/Team/Product/Execution still
   fails this gate rather than squeaking through on structural coverage
   alone — exact value is a placeholder for Part 35 calibration, not a
   final number).
4. **Overall Assessment Confidence is not "Low."**

If any gate fails: the product shows **"Not enough evidence for a
Startup Power Score yet"**, plus whatever partial pillar-level
Strength/Completeness data *does* exist (never nothing — partial,
labeled information is more useful and more honest than an artificial
full blackout). This directly answers Part 15's own worked concern:
Gate 3 alone would already block a 94/12% case; Gates 1-2 add structural
protection against a single freak strong pillar carrying the whole
score.

---

## Traction Redesign

Current Traction (Customer Growth, Revenue Growth, Retention, Growth
Velocity — all Deterministic, requiring a dated two-point series;
Engagement, the sole non-Deterministic dimension) produces the exact
15.0% coverage constant for 25 of 25 real companies audited (Phase
10.8B) **because every real value that mattered was scale, not growth,
and V2.1 has no dimension that credits scale on its own.** V3 separates
the concepts explicitly, per the user's own Part 16 framing:

| New dimension | What it proves | What it does NOT prove | Category |
|---|---|---|---|
| Current Scale | The company has reached a real, disclosed absolute level (revenue, GMV, ARR, users) at a point in time | Growth, trajectory, or durability | **A** — deterministic once ONE real dated observation exists (no second point required) |
| Growth Trajectory | The scale is increasing/decreasing over time | Current absolute scale, or that growth is profitable | **A** — unchanged from today's Customer/Revenue Growth mechanism, genuinely requires two dated points, stays fail-closed |
| Customer Adoption Breadth | How many/what kind of customers have adopted the product | Retention or revenue quality | **B** — taxonomy (named customer count, named customer types, enterprise-vs-SMB mix) |
| Retention / Engagement | Customers who adopted keep using/paying | Initial adoption or growth | **A** where NRR/GRR/churn is disclosed (unchanged Deterministic mechanism); **B** otherwise (qualitative engagement signals) |
| Commercial Validation | Real buyers have committed (contracts, renewals, enterprise logos) | Profitability or even revenue scale | **B** — taxonomy (named contract, named enterprise logo, renewal evidence) |

This directly fixes the structural-ceiling finding: "$20M ARR proves
scale" (Current Scale, A, scorable from one disclosed figure) is no
longer forced through the same gate as "prove this grew" (Growth
Trajectory, A, correctly still fail-closed without two points) — a
company that discloses scale but not history now gets honest partial
credit instead of zero coverage on 85% of the pillar's weight. Fail-
closed behavior for claims requiring missing data is explicitly
preserved for Growth Trajectory and the Deterministic half of
Retention, per the user's own instruction not to weaken it.

---

## Financial Health Redesign

**Which dimensions are realistically publicly assessable:** Revenue
Quality (qualitative signals about recurring/contract revenue are often
discussed publicly even without hard numbers) and, when a company
discloses top-line figures at all, a Current-Scale-style financial
observation. **Which are primarily founder/data-room assessable:** Unit
Economics, Burn Efficiency, and Runway — the three dimensions that,
combined, account for 80% of the pillar's configured weight and 100%
of Phase 10.8B's confirmed fabrication cases.

**Should Financial Health frequently have low public coverage? Yes —
this should be treated as an expected, honest, structural property of
the pillar for public-information-only analyses, not a defect to
engineer away.** The redesign (Part 5: Burn Efficiency and Runway both
become Deterministic-only, fail-closed) makes this explicit rather than
papering over it with LLM narration.

**Is SPS still publishable when Financial Health has low coverage?
Yes** — per the SPS Aggregation gate (Part 14), Financial Health is not
one of the two pillars (Market, Team) required for publishability, and
its 10% weight is the smallest of the six, by design, precisely because
it is the pillar most structurally dependent on private disclosure.

**How could private founder evidence later increase coverage without
automatically increasing score (design only, no ingestion built here):**
a future founder-submitted data room would produce new
`CanonicalObservation`s (real cash balance, real burn, real margin) that
flow through the identical Deterministic evaluators already designed
for public evidence — the evaluator does not know or care whether an
observation came from a public website or a founder upload, only whether
it is ACCEPTED and dated. A founder disclosing genuinely poor unit
economics would *lower* Financial Health, exactly as Part 23 requires;
disclosing strong ones would raise it; disclosing nothing new leaves
coverage and score both unchanged.

---

## Stage Fairness

Six stages (Idea, Pre-Seed, Seed, Series A, Series B+, Growth), each
with its own version of "what counts as strong evidence" per dimension
— generalizing the `stage_guidance` text V2.1 already writes into
`scoring_methodology.py`, but moving the *enforcement* into the
taxonomy-to-score mapping table itself (Category B/C dimensions) rather
than leaving it as prose the model may or may not apply consistently
(the mechanism V2.1 already relies on and that this document's own
audits show is inconsistently effective).

Concretely: the same Founder-Market-Fit taxonomy field combination
(`domain_experience: DIRECT, repeat_founder: false`) maps to a *higher*
score band at Pre-Seed (where domain experience alone is one of the only
signals available) than at Series B+ (where the same combination, with
no additional leadership/hiring/traction corroboration, would be a
below-average signal for that stage). This is a per-stage lookup table,
not a per-stage prompt instruction — the mechanism this document argues
is more reliable than V2.1's prose-based stage_guidance.

**Guarantee check:** an exceptional early startup can score highly
because its taxonomy fields can independently hit the top Pre-Seed band
without needing any Series-B-shaped evidence (repeatable GTM, named
executives) it has no way of having yet. A weak mature startup can score
poorly because the same taxonomy fields, evaluated against the Growth-
stage table, will not clear that stage's higher bar merely by existing
longer.

---

## Negative Evidence

`CanonicalObservation` and the Category B/C taxonomies both explicitly
carry **negative-evidence fields**, not just presence/absence of
positive signals — e.g. Leadership's `disclosed_dysfunction`, Revenue
Quality's `concentration_risk_disclosed`, and a new cross-cutting
`decline_signal` field usable by any dimension (declining customers,
declining revenue, high churn, failed retention, founder turnover,
regulatory problems, product stagnation, failed commercial execution,
severe burn, market contraction — the user's own Part 19 list, adopted
directly).

**Mechanism:** a populated negative-evidence field maps, via the same
versioned lookup table, to a **low** band (0-2 or 3-4, per Part 19's
requirement) — structurally identical in kind to how a positive field
maps to a high band, not a separate penalty subtracted afterward. This
keeps the "identical evidence -> identical score" invariant intact:
negative evidence is symmetric evidence, not an exception bolted onto
the aggregation formula.

**The critical distinguishing rule, made mechanical rather than
aspirational:** `UNAVAILABLE_NO_EVIDENCE` (no field populated at all)
and a populated `decline_signal` field are different `availability_status`
values from the start — there is no code path where "we found nothing"
and "we found evidence of decline" can be confused, because they are
different branches of the same evaluator function, not different
interpretations of the same free-form LLM number the way V2.1's 0-2
band ("no clear connection," "little or no execution evidence") is
worded ambiguously close to "nothing was found" today.

---

## Evidence-Abundance Bias

**The risk, confirmed empirically, not hypothetically:** Phase 10.8A's
famous-company/public-data-bias analysis and this phase's SpaceX finding
both show that how much has been publicly written about a company
still shapes outcomes independent of real quality — a famous company
gets more taxonomy fields populated simply by being famous, which raises
both Power (more scorable dimensions) and Coverage together, in a way
that can look like "this is a great company" when it may partly be "this
company has been in the news a lot."

**The inverse risk:** an obscure but genuinely excellent early-stage
company can score only "mediocre" (not low — V2.1/V3 both correctly
avoid punishing sparse evidence with a low score) purely for lack of
public visibility, landing in an uninformative middle band that looks
identical to genuine averageness.

**Safeguards designed here:**
- **Coverage is always reported alongside Power** (Part 2) specifically
  so "we don't know enough" (low coverage, whatever Power number
  resulted) is visually and structurally distinguishable from "we know
  this company is average" (high coverage, mid Power) — this is the
  single most direct mitigation, and it is a reporting/architecture
  fix, not a scoring-formula fix, because the underlying asymmetry in
  what's publicly known about companies is a fact about the world, not
  a bug to compute away.
- **Stage-relative taxonomy tables (Part 18)** mean an obscure Pre-Seed
  company is judged against Pre-Seed evidence expectations, not against
  how much a Series B company would typically have generated in press
  coverage — reducing (not eliminating) the gap between "famous" and
  "young."
- **Publishability gates (Part 15)** ensure a company whose only
  advantage is abundant-but-shallow public evidence (high coverage, low
  confidence because none of it is Observed-tier) cannot reach a
  headline SPS without the accompanying Confidence label making that
  shallowness visible.
- **What the system must NOT do:** artificially cap or boost scores
  based on how famous a company is, or apply a "familiarity discount" —
  this would violate Non-Negotiable Principle 4 outright (hard-coding a
  company-fame heuristic is exactly the kind of company-specific rule
  that principle forbids) and was explicitly rejected as an option.

---

## High Score Semantics

**80+** requires: ≥4 of 6 pillars individually publishable and scoring
≥7.0, no pillar showing a populated negative-evidence field, overall
Confidence ≥ Medium, overall Coverage ≥ 50%.

**85+** requires the above, plus: ≥3 pillars scoring ≥8.0.

**90+** requires: ≥2 pillars in the 9-10 band with High confidence, no
pillar below 7.0, overall Coverage ≥ 60%, zero negative-evidence fields
anywhere.

**95+** requires: ≥3 pillars in the 9-10 band with High confidence, no
pillar below 7.5, overall Coverage ≥ 70%.

These are explicitly placeholder thresholds for Part 35's later
calibration pass, not final numbers — what's fixed here is the *shape*
of the gate (multiple independently-strong pillars + coverage +
confidence + absence of negative evidence, never a single strong pillar
alone), designed specifically so it cannot be satisfied by the kind of
single-dimension-driven inflation Phase 10.8A found in V2 (one company
whose entire compression profile was masked by a single outlier-high
pillar).

---

## Low Score Semantics

**<60** requires at least one pillar showing either a populated
negative-evidence field or a below-stage-expectation score on a
dimension with real (not sparse) evidence.

**<50** requires at least two pillars meeting the above.

**<40** requires at least one populated negative-evidence field
specifically in Market, Team, or Execution (the three pillars most
directly tied to viability) — chosen because Financial Health/Traction
negative signals alone (e.g. honestly-disclosed thin scale at Pre-Seed)
should not, by themselves, crater a score for a company that is
otherwise genuinely early and otherwise strong; the user's own Non-
Negotiable Principle 9 ("low scores should also be actually achievable
when evidence demonstrates weakness") is explicitly not "low scores
should be easy to produce," and this asymmetric gate keeps the two from
being confused.

**<20** requires negative-evidence fields present in a majority of
scorable pillars, or one pillar's negative evidence explicitly
indicating collapse-adjacent facts (disclosed shutdown signals, severe
disclosed decline, disclosed fundamental team dysfunction).

**Explicit guardrail, restated:** sparse evidence, at any coverage
level, never on its own satisfies any of the above — every low-score
gate requires a populated negative-evidence field or a specific
below-stage-expectation scored dimension, never merely
`UNAVAILABLE_NO_EVIDENCE`.

---

## Founder-Provided Evidence (Design Only)

Future data-room/pitch-deck/metrics ingestion produces the exact same
`CanonicalObservation` shape as public research, tagged with a
`source_type: FOUNDER_PROVIDED` field, and flows through the identical
provenance/evaluator pipeline. This means the Part 23 behavior falls out
of the architecture rather than needing bespoke logic: churn data
submitted by a founder either populates Retention's Deterministic
evaluator with real numbers (raising or lowering the score depending on
what the numbers say) or, if internally contradictory or clearly
implausible, gets rejected at the provenance step exactly like any other
observation (Part 24) — "founder-provided" is a provenance tag, not a
trust override.

---

## Hallucination Containment

```
SOURCE
  |
  v
EXTRACTED CLAIM (LLM, typed CanonicalObservation, not free text)
  |
  v
PROVENANCE CHECK (deterministic: does this literal claim trace to the
  |                source text? -- generalizes V2.1's evidence_provenance.py
  |                from "numbers only" to every typed field)
  v
ACCEPT / REJECT
  |
  v
CANONICAL EVIDENCE (only ACCEPTED observations ever reach this layer)
  |
  v
DETERMINISTIC SCORING (Category A/B) or CONSTRAINED CLASSIFICATION
  then DETERMINISTIC MAPPING (Category C)
```

**How this improves on V2.1's shape** ("LLM invents evidence -> LLM
interprets its own evidence -> LLM chooses score"): V2.1 already added
the provenance check (Part 3, Phase 10.8B) but only for numeric tokens,
and only after the same free-form scoring stage had already been
exposed to whatever unfiltered evidence Stage 1 produced — the
provenance guard runs on the OUTPUT of extraction, filtering what the
Subscore ends up displaying, but Stage 2's free-form score was computed
in the same pipeline pass as the fabricated evidence in V2.1's original
design intent (the fix works because the guard was inserted before
scoring, not because scoring itself changed). V3 makes this the
*primary* architecture rather than a bolted-on filter: every claim, not
just numeric ones, is provenance-checked before it becomes a
`CanonicalObservation` at all, and scoring never has the option to
"interpret" a claim's meaning the way a free 0-10 judgment does — it can
only apply a versioned table to already-accepted, already-typed facts.
The LLM's opportunity to hallucinate is confined to the extraction step,
where it is checkable against source text; its opportunity to
launder a hallucination into a specific number by narrating around it is
removed entirely for 24 of 28 dimensions.

---

## Explainability

Every scored dimension produces a trace of exactly this shape (worked
example, Customer Adoption Breadth, illustrative numbers):

```
Dimension: Customer Adoption Breadth
Evidence:
  - "4,200 customers as of March 2026" (directly_stated, source: company
     press release, provenance: ACCEPTED)
  - "600 enterprise customers" (directly_stated, source: same, ACCEPTED)
  - named customer examples: [Acme Corp, Globex] (ACCEPTED)
Classification: named_customer_count=4200, enterprise_subset=600,
  named_reference_customers=2
Rule triggered: "STRONG_ADOPTION_v3.0.0: enterprise_subset > 500 AND
  named_reference_customers >= 2 for stage=Growth"
Confidence: High (all fields directly_stated, all ACCEPTED)
Score: 8.0
```

This is a mechanical concatenation of already-existing structured data
(evidence + classification + the specific rule name/version + its
inputs), not a second LLM call asked to "explain the score" after the
fact — which matters because an after-the-fact LLM explanation could
itself hallucinate a plausible-sounding but incorrect justification.
**An investor or founder reading this can verify every line against the
cited source themselves**, which is the actual bar "defensible" should
be held to, not merely "reads plausibly."

---

## Reproducibility

Invariants, and their achievability under this design:

| Invariant | Achievable? |
|---|---|
| Same canonical evidence + same methodology version → same score | **Yes**, for Category A/B (24/28 dimensions); **mostly** for the 1 Category C dimension (label assignment still model-dependent) |
| Same methodology version + same evidence → same score | Same as above |
| Evidence changes → score may change | Yes, by construction (this is desired, not merely tolerated) |
| Methodology changes → new version required | Yes, enforced by process (Part 33), same discipline V2.1 already followed for its own version bumps |
| Different LLM provider, identical extracted canonical evidence → identical SPS | **Yes** for Category A/B; **not guaranteed** for Category C |

---

## Model Independence

**Should V3 allow swapping OpenAI/Anthropic/Gemini/open-source models
without changing scoring methodology? Yes, and the proposed
architecture achieves this for the large majority of the methodology
directly** — because research, extraction, and (for Category B)
controlled classification are the only steps touching a model at all,
and the contract each must satisfy (produce a `CanonicalObservation` or
a taxonomy object matching a fixed schema) is provider-agnostic by
construction. This is a meaningful strategic asset independent of SPS
quality: it de-risks provider pricing/availability/deprecation changes
for the whole product, not just for scoring.

**Strategic value:** high. The current architecture ties SIE's core
intelligence to one model family's judgment quality and prompt-following
behavior (the SpaceX defect is, in effect, a `gpt-4.1-mini`-specific
failure mode observed on this exact prompt wording — a provider change
today could shift, not necessarily fix, that exact defect without
anyone knowing why). V3 converts "does the LLM interpret evidence the
way we want" from an ongoing, provider-coupled risk into a one-time,
narrowly-scoped extraction-quality question, testable in isolation
(Part 36's cross-model test).

---

## SIE IP Implications

Under V3, the proprietary asset shifts from "prompt engineering that
happens to produce good judgment" (hard to defend, easy to approximate,
and — per this document's own findings — not even reliably correct
today) to a durable, inspectable, versioned asset stack:

- The evidence ontology and canonical schema (Part 6).
- The dimension taxonomy definitions and their stage-conditioned scoring
  tables (Parts 5, 11, 18).
- The deterministic evaluators and aggregation methodology (Parts 9,
  13, 14).
- The confidence and coverage methodology (Parts 2, 12).
- The calibration dataset and validation corpus, once built (Parts 35,
  36).
- The methodology versioning and explanation-engine design itself
  (Parts 25, 32, 33).

This is a stronger, more defensible position than the current
architecture, where a meaningful fraction of "what SIE actually knows"
lives inside prose the model may or may not follow consistently, is not
independently reviewable without re-running expensive LLM calls, and (as
this document's own Section 3 argues) has already been shown not to be
fully reliable.

---

## Synthetic Stress Tests

Conceptual walkthroughs only — no code run, no real company involved.

| Case | Pillar strength pattern | Coverage | Confidence | SPS or verdict |
|---|---|---|---|---|
| A. Exceptional / high coverage | All 6 pillars 8-10, several negative-evidence-free | High (>70%) | High | Published, likely 85-95 |
| B. Exceptional / medium coverage | Market/Team/Product strong, Execution/Traction/Financial thinner | Medium (45-60%) | Medium | Published (gates met), likely 70-82 with visible "Medium confidence" label — this is the realistic Stripe-shaped case |
| C. Exceptional / insufficient coverage | Market/Team strong, everything else Unavailable | Low (<35%) | Low | **Not published** — fails the overall-coverage gate (Part 15) even though what little exists is strong; product shows partial pillar data only |
| D. Average / high coverage | All 6 pillars land in the 5-6 "credible but ordinary" band, high coverage | High | High | Published, ~55-65 — a legitimate, confidently-average result |
| E. Weak / high coverage | Multiple pillars show populated negative-evidence fields, high coverage | High | High | Published, <40 — confidently weak, correctly distinguishable from Case F |
| F. Weak / low coverage | Sparse evidence, no negative-evidence fields found (not because none exist, but because little was found at all) | Low | Low | **Not published**, or published with heavy Low-coverage/Low-confidence labeling — must NOT resolve to the same low number as Case E, since the underlying finding ("we don't know" vs. "we know it's bad") is different |
| G. Exceptional Pre-Seed | Stage-relative taxonomy tables (Part 18) let Team/Market/Product hit top Pre-Seed bands on qualitative signals alone; Traction/Financial-Health honestly thin (expected at this stage) | Medium overall (Pre-Seed-appropriate pillars strong, others structurally thin) | Medium-High | Published, potentially 75-85 — this is the case V2/V2.1 structurally could not produce (Relaw's real V2 result, 72.5, was an *unearned* version of this; V3's version would need genuine taxonomy-field support, not narrative alone) |
| H. Weak Growth-stage | Team/Execution/Traction show populated negative-evidence or below-stage-expectation scores despite the company's maturity | High (mature companies are well-documented) | High | Published, <40 — a mature company does not get credit merely for being large or old |
| I. Strong, Financial Health Unavailable | Market/Team/Product/Execution/Traction all strong; Financial Health entirely Private-Information-Unavailable | Overall coverage still likely >50% since only the smallest-weight pillar is missing | Medium-High | Published (Part 14's worked example) — Financial Health shown as "Unavailable — Private Information," not silently dropped |
| J. Abundant evidence, substantial negative evidence | High coverage across all pillars, but several carry populated negative-evidence fields (declining metrics, disclosed churn, disclosed team turnover) | High | High | Published, likely 20-45 depending on how many pillars are affected — this is the case that most directly tests Non-Negotiable Principle 3 and the architecture handles it correctly by construction, since negative evidence maps to low bands exactly like positive evidence maps to high ones |

These ten cases were used to pressure-test the design in Parts 13-22
above (e.g., Case C directly motivated the overall-coverage
publishability gate; Case F vs. E directly motivated keeping "no
evidence" and "negative evidence" as structurally distinct code paths
rather than two interpretations of one score).

---

## Existing-Company Thought Experiment

**No V3 scores are invented below.** Reasoning only, about which
specific V2/V2.1 distortions would plausibly disappear and which
uncertainties would remain, company by company:

- **Stripe:** The Operational Execution / Burn Efficiency fabrication
  (confirmed live in the high-strength sanity check) disappears
  structurally — both dimensions become Deterministic-only under V3's
  Financial Health redesign, so instead of an LLM inventing "$5M
  cash/$400K burn" and a provenance guard catching it after the fact,
  the dimension is honestly `UNAVAILABLE_PRIVATE_INFORMATION` from the
  start. Founder-Market Fit would plausibly resolve to a populated,
  confident taxonomy (Patrick and John Collison's prior history is
  extensively documented) rather than needing to survive V2.1's
  free-form "does this feel like enough" judgment. **Remaining
  uncertainty:** whether the underlying research step surfaces that
  founder history at all is a retrieval question V3's scoring redesign
  does not itself solve.
- **SpaceX:** The exact discovered defect (Market Size/Growth/Timing,
  Competitive Intensity, Differentiation, Founder-Market Fit marked
  Unavailable despite strong retrieved evidence) is the case this
  document's redesign most directly targets — turning "does this feel
  like enough evidence" into "is at least one taxonomy field populated
  with cited evidence" is a mechanical check that Musk's PayPal/Tesla
  history, named competitors (Blue Origin, ULA), and stated cost-
  advantage thesis would very plausibly satisfy. Financial Health and
  Traction's structural ceiling would likely persist in modified form —
  Current Scale (the new Traction dimension) could credit SpaceX's
  disclosed $13.3B revenue estimate where V2.1's Deterministic-only
  Traction gave zero credit for it. **Remaining uncertainty:** whether
  the taxonomy tables, once actually built and calibrated, are generous
  enough to credit Musk's cross-industry (not aerospace-specific) prior
  history as "domain experience" — this is exactly the kind of
  calibration judgment Part 35 defers, not resolves, here.
- **Databricks:** Similar to Stripe/SpaceX — the well-documented Apache
  Spark/UC Berkeley AMPLab founding story is a strong candidate for
  resolving Founder-Market Fit's taxonomy where V2/V2.1 marked it
  Unavailable for this exact company (Phase 10.8A's own diagnostic
  finding).
- **Rippling:** Parker Conrad's Zenefits history is likewise a strong
  taxonomy-field candidate; V2/V2.1 marked Founder-Market Fit
  Unavailable here too. The V2.1 diagnostic replay already showed
  Rippling's Team score reaching 8.0 once the research fix alone
  surfaced more; V3's redesign targets the remaining classification-
  strictness half of that same problem.
- **Plaid:** The fabricated "$5M cash balance, $400K monthly burn"
  Burn-Efficiency case (this document's own motivating example,
  Phase 10.8B Section 3) disappears structurally under the same
  Financial Health redesign as Stripe — honestly Unavailable rather
  than invented.
- **Relaw / Dome:** Both real pre-seed YC companies whose V2 scores
  (72.5 and 63.0 respectively) partly rode the mid-band-floor mechanism
  Phase 10.8A diagnosed and V2.1 partially addressed (Relaw dropped to
  64.2 under V2.1's diagnostic replay). Under V3, an "exceptional
  Pre-Seed" result (Synthetic Case G) is achievable, but only from
  genuine, cited, stage-appropriate taxonomy evidence — generic
  narrative that previously satisfied a free-form "5-6, some relevant
  experience" band would instead need to populate a specific field with
  specific cited support to move any dimension's score up at all.
  **Remaining uncertainty:** whether either company's real public
  presence contains enough specific, citable fact (as opposed to
  narrative) to populate those fields is exactly what a real V3 run,
  not this thought experiment, would need to determine.

---

## Product Presentation

```
STARTUP POWER SCORE
87 · Strong

EVIDENCE COVERAGE
68%

ASSESSMENT CONFIDENCE
Medium

"SIE found strong, specific evidence across Market, Team, and Product.
Financial Health could not be assessed from public information — this
is common and does not count against the company."
```

Design principles for the founder-facing surface (explicitly honoring
"do not turn the UI into a methodology dashboard"):

- **One headline number, two supporting labels, one sentence of plain-
  language explanation** — the internal six-pillar/28-dimension/
  taxonomy-field machinery stays available one click deeper (an
  "Intelligence Pillars" drill-down, consistent with the existing
  dashboard pattern from Phase 10.7-10.10) but is never the first thing
  a founder sees.
- **Missing information is framed as normal, not as a penalty** — "this
  is common and does not count against the company" directly operationalizes
  Non-Negotiable Principle 2 in the actual copy, not just in the math.
- **Negative evidence, when present, is named specifically** rather than
  folded into a vague low number — "SIE found evidence of declining
  retention" is more useful and more honest to a founder than a bare 34.
- **Investor-facing surfaces** (Investor Workspace, Compare) can show
  more of the three-axis detail side-by-side across companies, since
  that audience already expects and benefits from the extra rigor —
  this is a presentation-layer decision, not a scoring one, and is
  explicitly out of this design phase's implementation scope.

---

## Historical Comparability

- **Every stored analysis already carries `methodology_version`,
  `anchor_registry_version`, `scoring_version`, and `prompt_version`**
  (confirmed architecture, unchanged since before V2.1). V3 continues
  this pattern with its own version identifiers — no new plumbing
  required, only new version strings.
- **No historical V2/V2.1 analysis is ever rewritten, migrated, or
  reinterpreted under V3's semantics.** A V2.1 SPS of 76.4 remains,
  permanently, a V2.1 SPS of 76.4, displayed with its own version label
  if ever shown next to a V3 result.
- **Trend/SPS History implications:** any company with both a V2.1 and
  a later V3 analysis on file will show a visible score discontinuity
  at the version boundary that is NOT a signal of the company changing —
  the SPS History UI must annotate a methodology-version change
  explicitly (a vertical marker/label on the trend line) rather than
  plotting V2.1 and V3 scores on one continuous, implicitly-comparable
  line.
- **Rankings/Investor Workspace change-detection implications:** any
  ranking or "score changed since last analysis" feature must exclude,
  or separately flag, comparisons that cross a methodology-version
  boundary — comparing a V2.1 score to a V3 score is comparing two
  different instruments, not tracking real change.

---

## Versioning

**Recommendation: V3.0, not V2.2.** The meaning of "score" changes
materially (LLM no longer chooses the number for 24 of 28 dimensions),
new fields become load-bearing (Coverage/Confidence move from cosmetic
to structurally necessary), Traction and Financial Health's dimension
sets are redesigned rather than merely re-anchored, and publishability
itself becomes a gate that can withhold SPS entirely — none of this is
a point release by any reasonable definition, and calling it V2.2 to
minimize the apparent size of the change would itself violate the
project's own standing preference for honest versioning (already
demonstrated in how `METHODOLOGY_VERSION` was bumped, not silently
reused, for V2.1 itself).

---

## Migration Impact (Design Only)

| Component | Reuse / Replace / Risk |
|---|---|
| `SIEMethodologyAnalysis`, `SIEContext` | **Reuse** the outer shape (six pillars + context + analysis_context); add new top-level `evidence_coverage_overall`/`assessment_confidence_overall`/`publishable: bool` fields |
| `PillarAnalysis`, `PillarScoreBreakdown` | **Reuse** structurally; extend `PillarScoreBreakdown` with `completeness` (distinct from `evidence_coverage`, per Part 13) and `published: bool` |
| `Subscore` | **Replace** with the richer `DimensionResult` contract (Part 8) — this is the most invasive single model change, since every pillar wrapper and every downstream consumer of `Subscore.score`/`.evidence`/`.confidence` touches it |
| `scoring.py` (`calculate_weighted_score`, `calculate_pillar_confidence`, `calculate_evidence_coverage`, `apply_confidence_score_cap`) | **Replace** the cap function per Part 12's decision; **extend** the weighted-average/coverage functions to the new gating rules (Parts 13-15); core weighted-average math itself is **reused** unchanged |
| `scoring_methodology.py` | **Replace** dimension definitions with taxonomy/rule-table definitions per pillar; `PILLAR_WEIGHTS` **reused** unchanged |
| `pillar_scoring.py` | **Replace** — its entire purpose (turn evidence into a free 0-10 number via prompt) is what V3 eliminates for 24/28 dimensions; a much smaller module remains for Category C's constrained-label mapping |
| `evidence_extraction.py` | **Substantially replace** the per-dimension prose evidence-status prompt with per-dimension taxonomy-extraction prompts; **reuse** the existing per-dimension scoped-correction retry pattern, which generalizes cleanly to "one taxonomy field failed provenance, re-extract only that field" |
| `research_enrichment.py` | **Reuse** the V2.1 four-query architecture as-is; independent of V3's scoring changes (Part 27's model-independence argument applies equally here) |
| `evidence_provenance.py` | **Extend**, not replace — generalize from "numeric tokens only" to "every typed `CanonicalObservation` field," same core traceability check |
| `investment_score.py` | **Reuse** `calculate_base_score`'s weighted-average shape; **extend** with the new SPS-level publishability gates (Part 14) |
| API responses (`app/api.py`) | **Extend** response models with `evidence_coverage_overall`/`assessment_confidence_overall`/`publishable`/explanation-trace fields; existing SPS/pillar-score fields **reused** for backward compatibility with anything not yet updated to read the new fields |
| Database JSONB (`analyses.methodology`) | **Additive only** — the JSONB column already stores the full serialized analysis; new fields land inside it without a schema migration (confirmed pattern: this repo already adds fields via additive `add_*_columns()` functions per `CLAUDE.md`, never destructive migrations) |
| Startup Profile, Rankings, Discovery, Compare | **Reuse** as consumers of `startup_intelligence_score`/pillar scores; **extend** to show Coverage/Confidence and the "not enough evidence" state (Part 31) — genuinely new UI work, but additive, not a rewrite of existing display logic |
| Founder Workspace, Investor Workspace, SPS History | **Extend** with version-boundary annotations (Part 32); **reuse** existing trend/comparison scaffolding |
| Fundraising Readiness | **Reuse unchanged** — confirmed architecturally separate from SPS/pillar scoring throughout Phases 10.8-10.8B (zero shared code path), and nothing in this design touches it |
| Homepage examples | **Not touched by this design phase**; any homepage SPS-range preview remains blocked on Phase 10.8C's still-pending blind validation, unaffected by whether that validation eventually runs against V2.1 or V3 |

**Compatibility risk, stated plainly:** `Subscore` → `DimensionResult`
is a breaking model change touching every one of the six pillar wrapper
modules (`market_analysis.py`, `founder_analysis.py`, etc.) and every
downstream reader. This is the single largest engineering cost in the
migration and should be sequenced first, behind a compatibility shim if
incremental rollout is desired (see below).

**Preferred migration sequence (incremental, not a rewrite):**
1. Introduce `CanonicalObservation` and the provenance-verification
   generalization (Part 24) as a new layer, initially feeding the
   *existing* V2.1 scoring unchanged (a pure plumbing change, fully
   testable in isolation, zero behavior change).
2. Migrate Traction and Financial Health first (Parts 16-17) — they are
   the most self-contained redesigns, have the clearest existing
   structural-ceiling evidence justifying the change, and already share
   the Deterministic pattern with the least new machinery to build.
3. Migrate the remaining four pillars' Category B dimensions one pillar
   at a time, each independently testable against frozen historical
   evidence (the same "replay Phase 10.8's cohort through the new code,
   compare" diagnostic pattern already established and reusable here).
4. Introduce the Category C constrained-classification mechanism last,
   scoped to Strategic Execution only, once the rest of the pipeline is
   stable.
5. Only then introduce the SPS-level publishability gates and the
   three-axis product surface (Part 31) — these depend on every pillar
   already reporting Coverage/Confidence in the new shape.

---

## Calibration Strategy (Design Only — Not Performed Here)

Every numeric threshold in this document (Parts 15, 21, 22) is
explicitly a placeholder. Calibration, when it happens, should draw on:

1. **Synthetic boundary cases** (Part 29's ten cases, extended) —
   cheap, fast, no LLM cost, establishes the *shape* of each gate before
   any real data is involved.
2. **The existing historical/frozen corpus** (Phase 10.8's 25-company
   cohort, Phase 10.8A/B's 6 diagnostic companies, this phase's Stripe/
   SpaceX pair) — replayed through V3 purely as **diagnostic**
   regression data, never as blind validation (they have all already
   shaped design decisions).
3. **Stage-specific cohorts** — enough real companies per stage
   (Pre-Seed through Growth) to calibrate each stage's taxonomy table
   independently, since a single blended threshold risks re-introducing
   stage-blindness.
4. **A genuinely new, independently-selected blind cohort** (Phase
   10.8C, still pending, now against whichever version actually ships).
5. **Known-outcome cohorts where ethically/practically available**
   (e.g. companies with public post-hoc outcomes — shutdowns,
   acquisitions, IPOs) — used cautiously and only for qualitative
   sanity-checking, never to reverse-engineer thresholds toward a
   "correct" answer, since SPS is explicitly not a probability of
   outcome (Non-Negotiable Principle 7).
6. **Expert review** of a sample of explanation traces (Part 25) by
   someone with real diligence experience, checking not "does the
   number look right" but "is the *reasoning* something I'd accept."
7. **Distribution and sensitivity analysis** on whatever cohort results
   from steps 2-4 — but explicitly **not** threshold-shopping until a
   prettier bell curve appears, which the user's own instruction (Part
   35) and this document's repeated emphasis both rule out.

---

## Validation Plan (Design Only — Not Performed Here)

Sequenced, each gating the next:

1. Deterministic unit tests (evaluators, aggregation, gates — pure
   Python, no LLM, extending `test_methodology_v2_1.py`'s existing
   pattern).
2. Rule-boundary tests (exact threshold edges for every gate in Parts
   13-15, 21-22).
3. Synthetic full-scale tests (Part 29's ten cases, executed as code,
   not just reasoned through).
4. High-strength sanity cases (repeat this phase's Stripe/SpaceX/Canva
   protocol against V3).
5. Low-strength sanity cases (the inverse of #4 — deliberately weak,
   real, obscure companies).
6. Sparse-evidence cases (companies with almost nothing public) — must
   confirm they land in "not enough evidence" or a mid-band-with-
   low-coverage-label, never a confidently low score.
7. Stage-fairness cases (matched pairs at different stages with
   comparable real quality).
8. Evidence-abundance-bias cases (a deliberately obscure company vs. a
   deliberately famous one, matched as closely as possible on
   underlying real quality — acknowledging this matching is itself
   hard and approximate).
9. Fabrication/provenance audit, generalized from Phase 10.8B's
   numeric-only audit to every typed field.
10. A fresh, genuinely blind, independently-selected real-company
    cohort (Phase 10.8C, deferred).
11. Score-distribution analysis (descriptive only, not a target).
12. Score-distance/discrimination analysis (pairwise dominance, rank
    correlation — same methods Phase 10.8 already established).
13. Repeatability test (same evidence, same version, run twice,
    confirm identical output for Category A/B; measure and report
    Category C's residual variance honestly).
14. Cross-model evidence-extraction test (same source text, two
    different LLM providers, confirm identical `CanonicalObservation`s
    or characterize the gap if not identical) — this is the direct test
    of the model-independence claim in Part 27.
15. External expert/product review of the explanation traces and the
    overall three-axis presentation.

---

## Architecture Recommendation

| Criterion | A: Keep LLM numeric scoring | B: Hybrid (some deterministic, some LLM numeric) | C: Eliminate direct LLM numeric scoring | D: Alternative |
|---|---|---|---|---|
| Truthfulness | Poor — proven capable of fabrication | Better, uneven | Best achievable | — |
| Reproducibility | Poor | Uneven, dimension-dependent | Strong (24/28 dimensions) | — |
| Explainability | Weak (post-hoc rationale text) | Uneven | Strong (mechanical trace) | — |
| Hallucination risk | High (confirmed, 72% of a real cohort) | Reduced but present wherever LLM-numeric remains | Lowest achievable, not zero (extraction can still misread a source) | — |
| Model independence | None | Partial | Strong for 24/28 dimensions | — |
| Stage fairness | Prose-dependent, shown inconsistent | Improved, still uneven | Enforceable via lookup tables | — |
| Calibration ability | Very hard (opaque prompt tuning) | Moderate | Direct (versioned tables are literally the calibration surface) | — |
| Engineering complexity | Lowest today | Moderate | **Highest** — this is Option C's real cost | — |
| Maintainability | Poor (prompt drift, provider drift) | Moderate | Good once built, but taxonomy tables for 28 dimensions × 6 stages is real, ongoing maintenance surface | — |
| Investor credibility | Weak given confirmed fabrication | Improved | Strongest | — |
| Founder usability | Unaffected either way (presentation layer is separable) | Unaffected | Unaffected | — |
| Defensibility as IP | Weak (lives in prompts) | Moderate | Strong (Part 28) | — |

**Recommendation: Option C, with the explicit, bounded exception
already built into this document (a single reluctant Category C
dimension, Strategic Execution, using constrained-label classification
rather than free numeric scoring).** This is not "Option C because the
brief discussed it heavily" — it is Option C because every defect found
across four separate investigation phases traces to the same root
cause, and Option B (the natural-seeming compromise) does not remove
that root cause, only shrinks its blast radius, for whichever
dimensions happen to stay LLM-numeric. **Challenging it directly, as
instructed:** Option C's honest cost is engineering effort (Category B
taxonomy design and calibration for ~19 dimensions × up to 6 stages is
a large, multi-phase undertaking, not a prompt edit) and a real,
acknowledged loss of nuance for at least one dimension (Strategic
Execution) that resists full decomposition — a pure-Option-C purist
would force that dimension into a taxonomy too, and this document
explicitly declines to do that because the resulting taxonomy would
either be so coarse it loses real signal or so granular it just
re-implements a free-form score with extra steps. Option C is
recommended as the target *architecture*, not as a claim that 100% of
scoring can or should be mechanical.

---

## Open Questions

1. Is one reluctant Category C dimension (Strategic Execution) the right
   number, or would honest decomposition attempts on Market Timing,
   Customer Value, or others reveal they also resist full taxonomy
   reduction once actually attempted (as opposed to sketched here)?
2. What is the right minimum-evidence bar per taxonomy field —
   this document proposes "at least one cited field" for Category B
   availability, mirroring V2.1's "at least two credible signals" for
   Inferred status loosely, but the two are not identical and the right
   number needs Part 35's calibration, not a guess here.
3. How should `UNAVAILABLE_CONFLICTING_EVIDENCE` (new in this design)
   actually resolve in the product — always block scoring, or allow a
   confidence-discounted score through with a visible conflict flag?
4. Should Category C's constrained-label step itself require multi-
   provider agreement (an ensemble/consensus check) to partially recover
   the reproducibility invariant it otherwise lacks — this would add
   real cost and latency and is not designed here.
5. Where exactly should the "founder-provided evidence" ingestion UI
   sit in the product, and how should conflicting founder-vs-public
   observations for the same field be resolved (Part 23 designs the
   scoring consequence, not the ingestion/conflict-resolution UX)?
6. Is 35% overall coverage (Part 15) the right publishability floor, or
   should it be pillar-composition-aware (e.g. a different floor
   depending on which pillars make up that 35%) — flagged as a
   placeholder, not resolved.
7. Does the Traction/Financial-Health redesign (Parts 16-17) fully
   relieve the structural ceiling, or merely shift it — this document's
   own thought experiment (Part 30) explicitly flags this as unresolved
   pending an actual run.

---

*End of design document. No implementation follows from this file
alone — see the Final Report's verdict block for the explicit
next-step recommendation.*
