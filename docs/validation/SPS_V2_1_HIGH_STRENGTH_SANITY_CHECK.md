# V2.1 High-Strength Sanity Check

Read-only diagnostic, run after Phase 10.8B, before Phase 10.8C. No
methodology/scoring/anchor/confidence-cap/research/evidence/weight code
was modified to produce this document. See
`app/calibration/discrimination_audit_2026_08/HIGH_STRENGTH_SANITY_EXANTE.md`
for the ex-ante record (written before any company was run) and
`high_strength_sanity_check.py` for the instrumented (observe-only)
runner.

## Companies and outcome

| Company | Status | SPS | Stage |
|---|---|---|---|
| Stripe | Completed | **76.4** | Growth |
| Canva | Failed (website_extraction, HTTP 403, reproduced on retry) | -- | -- |
| SpaceX | Completed | **62.7** | Growth |

Canva's website blocks the scraper -- confirmed reproducible on a second
attempt, the same bot-protection pattern documented for Toast/Chime/
Bolt/Gopuff/WeWork in Phase 10.8. Not worked around further, not
substituted with another company (the user specified these three by
name).

## Stripe -- full detail

Overall: 8.5(Market)×.20 + 7.7(Team)×.20 + 8.4(Product)×.20 +
6.5(Execution)×.15 + 7.0(Traction)×.15 + 6.9(Financial Health)×.10 =
7.635 → **76.4**.

| Pillar | Score | Confidence | Coverage |
|---|---|---|---|
| Market | 8.5 | Medium | 80% |
| Team | 7.7 | Medium | 100% |
| Product | 8.4 | Medium | 100% |
| Execution | 6.5 | Medium | 100% |
| Traction | 7.0 | **Low** | **15%** |
| Financial Health | 6.9 | **Low** | 45% |

Dimension detail (score / status / confidence):

- Market: Size 8.0/Inferred/**High**, Growth **9.0**/Inferred/**High**,
  Timing **9.0**/Inferred/**High**, Competitive Intensity
  8.0/Inferred/High, Customer Demand Unavailable.
- Team: Founder-Market Fit 7.0/Inferred/Medium, Technical Capability
  **9.0**/Inferred/**High**, Business Capability 7.0/Inferred/Medium,
  Leadership 7.0/Inferred/Medium, Execution Track Record
  **9.0**/Inferred/**High**.
- Product: Customer Value **9.0**/Inferred/**High**, Differentiation
  8.0/Inferred/High, Usability 8.0/Inferred/High, Defensibility
  8.0/Inferred/High, Adoption Potential **9.0**/Inferred/**High**.
- Execution: GTM 7.0/Inferred/Medium, Product Execution
  7.0/Inferred/Medium, **Operational Execution 5.0/Observed/Low**,
  Strategic Execution 7.0/Inferred/Medium.
- Traction: Customer Growth/Revenue Growth/Retention/Growth Velocity all
  Unavailable (Deterministic, no dated two-point series in the website
  text); Engagement 7.0/Inferred/Medium.
- Financial Health: Revenue Quality 8.0/Inferred/Medium, Unit Economics
  Unavailable (Deterministic), **Burn Efficiency 6.0/Observed/Low**,
  Runway Unavailable.

**Confidence-cap activations: none.** No subscore was reduced by
`apply_confidence_score_cap` -- every score shown above is exactly what
Stage 2 (and, for Operational Execution/Burn Efficiency, the provenance
guard) produced.

**Provenance-guard rejections: 2 dimensions, live confirmation of the
V2.1 fix working on brand-new data.**

- *Operational Execution*: 4 evidence bullets dropped, all citing
  invented figures -- "$5M ARR with 40% gross margin," "$3M cash /
  $250K monthly burn / 12 months runway," "$10M funding round," "30%
  QoQ customer growth." None of these numbers appear anywhere in
  Stripe's actual research brief, and none are remotely consistent with
  the real company (Stripe's real scale is many billions in revenue,
  not $5M). After stripping, only enough genuine signal remained to
  support 5.0/Observed/Low, not the 7-8 the fabricated numbers would
  have otherwise supported.
- *Burn Efficiency*: 5 evidence bullets + 1 signal dropped, the same
  fabricated-figure pattern ("$5M ARR with 200 customers," "$3M cash /
  12-month runway," "$10M Series A," "70% gross margin," "~5% monthly
  burn vs. ARR"). Final score after correction: 6.0/Observed/Low.

## SpaceX -- full detail

Overall: 6.0(Market)×.20 + 6.0(Team)×.20 + 6.6(Product)×.20 +
7.0(Execution)×.15 + 6.0(Traction)×.15 + 6.0(Financial Health)×.10 =
6.27 → **62.7**.

| Pillar | Score | Confidence | Coverage |
|---|---|---|---|
| Market | 6.0 | **Low** | **20%** |
| Team | 6.0 | Medium | 75% |
| Product | 6.6 | Medium | 65% |
| Execution | 7.0 | Medium | 100% |
| Traction | 6.0 | **Low** | **15%** |
| Financial Health | 6.0 | Medium | 45% |

**Confidence-cap activations: none. Provenance-guard rejections: none**
(no fabricated numbers were introduced for SpaceX at all -- the model
correctly used SpaceX's real, disclosed $13.3B/$4.5B 2025 revenue/
earnings estimates from the brief without inventing anything extra).

**The research brief for SpaceX was excellent** -- confirmed by direct
inspection of `analysis_context.research_brief_snapshot`. It explicitly
named: Elon Musk's founding background (PayPal, Tesla, Neuralink, The
Boring Company, X/Twitter); named competitors (Blue Origin, Boeing/
Lockheed Martin/ULA, OneWeb, Telesat, Kuiper); a $350-425B valuation
trajectory; ~$13.3B expected 2025 revenue and ~$4.5B earnings; named
investors (Google, Fidelity, Sequoia, a16z, Founders Fund); and
SpaceX's stated differentiators (reusable-rocket cost advantage,
vertical integration). The four targeted Tavily searches added in
Phase 10.8B worked exactly as intended here.

**Yet 7 of SpaceX's 24 non-Deterministic dimensions were marked
Unavailable despite this evidence being present and specific**:

| Dimension | Pillar | Rationale excerpt |
|---|---|---|
| Founder-Market Fit | Team | "no public evidence demonstrating the founding team's unusually strong insight or experience **in the market**" |
| Market Size | Market | "No direct facts or multiple independent credible signals explicitly quantify... Reasonable assumptions exist but do not meet the evidence threshold." |
| Market Growth | Market | "no direct or multiple independent credible signals confirm rapid underlying market growth" |
| Market Timing | Market | "lacks any direct or indirect public evidence regarding customer readiness..." |
| Competitive Intensity | Market | "lacks relevant qualitative or quantitative evidence... Without details on differentiation... or market positioning" |
| Differentiation | Product | "no verifiable public evidence indicating meaningful differentiation" |
| Usability | Product | "No direct or inferred evidence about ease of adoption..." |

This is a genuine, newly-surfaced defect, distinct from the one Phase
10.8B fixed. Phase 10.8B's Part 4 fix targeted an **input-sourcing**
problem (the research never looked in the right place). Here, the
research unambiguously *did* look in the right place and found strong
material -- Musk's serial-founder history, named competitors, a
valuation/revenue trajectory, and a stated cost-advantage thesis are all
sitting in the brief. The evidence-extraction stage's Stage-1 judgment
is nonetheless applying a bar closer to "Observed" (explicit,
third-party-verified, quantified) than the dimension's own written
"Inferred" rule requires ("Exact quantitative metrics are not required
when credible qualitative signals are sufficient... Do not mark this
dimension Unavailable merely because quantitative metrics are absent").
Competitive Intensity's own rationale even cites "no public data on
competitors" as a reason -- directly contradicted by the same brief's
own Section 6, which names four specific competitors.

## Answers to the twelve questions

1. **Did any company naturally exceed 80 SPS?** No (Stripe 76.4, SpaceX
   62.7; Canva unobtainable).
2. **Did any naturally exceed 85?** No.
3. **What specifically prevented each from scoring higher?** Stripe: the
   Traction/Financial-Health structural coverage ceiling (unchanged by
   design, Part 5) plus genuinely thin real evidence remaining in
   Execution/Financial-Health *after* the provenance guard correctly
   removed fabricated substitutes. SpaceX: the same structural ceiling,
   **plus** the newly-found Stage-1 over-strict Unavailable
   classification affecting 7 dimensions across Market/Product/Team
   despite strong retrieved evidence.
4. **Were lower scores caused by genuine weaknesses?** No -- nothing in
   either brief shows a real business weakness in either company.
5. **Caused by unavailable/private information?** Partially, and
   legitimately so, for Traction/Unit-Economics/Runway in both
   companies -- this is the fail-closed contract working as designed
   for data neither company discloses publicly.
6. **Did research fail to retrieve publicly available evidence?** No for
   either company in the aggregate -- Stripe's and SpaceX's briefs are
   both substantive; SpaceX's is specifically confirmed excellent by
   direct inspection.
7. **Did confidence caps materially suppress scores?** No -- zero
   activations for either company. The confidence-cap mechanism was not
   the limiting factor here at all.
8. **Were 9-10 anchors actually earned anywhere?** Yes -- six times for
   Stripe (Market Growth, Market Timing, Technical Capability, Execution
   Track Record, Customer Value, Adoption Potential, all 9.0/High
   confidence). Zero times for SpaceX (max dimension score 8.0).
9. **If not [10.0 specifically], why not?** No dimension in this n=2
   sample reached exactly 10.0. Too small a sample to conclude whether
   10.0 is reachable at all; it simply was not observed here.
10. **Are 9-10 anchors practically attainable from public evidence?**
    Partially confirmed yes for 9.0 specifically (Stripe, six times,
    across three different pillars). Inconclusive for 10.0.
11. **Are Traction/Financial-Health ceilings materially suppressing
    otherwise-exceptional companies?** Yes, clearly -- both Stripe and
    SpaceX hit exactly the same 15%/45% coverage figures documented for
    all 25 real companies in Phase 10.8 and all 6 Phase 10.8A/B
    diagnostic companies. This ceiling is company-invariant, not
    evidence-quality-dependent, and continues to cap roughly 30% of
    total pillar weight for every real company tested so far regardless
    of real quality.
12. **Is SPS measuring startup quality, evidence availability, or a
    mixture?** A mixture -- more clearly demonstrated here than in any
    prior phase. Stripe and SpaceX are both exceptional real businesses;
    neither approached 80. The two companies also diverge in *why*:
    Stripe's ceiling is almost entirely the (by-design, unchanged)
    structural coverage ceiling plus honest post-fabrication-removal
    thinness; SpaceX's ceiling additionally includes a real,
    newly-discovered evidence-classification defect unrelated to data
    availability.

## Per-pillar cause classification (every pillar below 8.0)

| Company | Pillar | Score | Primary cause |
|---|---|---|---|
| Stripe | Team | 7.7 | MIXED PERFORMANCE (2 dims at 9.0/High, 3 at 7.0/Medium -- no single dominant cause) |
| Stripe | Execution | 6.5 | PRIVATE INFORMATION (Operational Execution's real efficiency data is undisclosed; provenance guard correctly removed fabricated substitutes, leaving honest thinness) |
| Stripe | Traction | 7.0 | AGGREGATION EFFECT / ANCHOR DESIGN (structural 15% Deterministic-coverage ceiling, unchanged by design) |
| Stripe | Financial Health | 6.9 | PRIVATE INFORMATION (Unit Economics/Runway genuinely undisclosed) + provenance-guard correction on Burn Efficiency |
| SpaceX | Market | 6.0 | **ANCHOR DESIGN** (Stage-1 evidence-classification bar stricter than the dimension's own written Inferred rule; strong retrieved evidence was available and discarded) |
| SpaceX | Team | 6.0 | MIXED -- Founder-Market Fit is ANCHOR DESIGN (same defect as Market); the other four dimensions' flat 6.0 is genuine INSUFFICIENT PUBLIC EVIDENCE (SpaceX discloses little granular internal team/hiring detail) |
| SpaceX | Product | 6.6 | ANCHOR DESIGN (Differentiation/Usability discarded despite explicit differentiation language in the brief) |
| SpaceX | Traction | 6.0 | AGGREGATION EFFECT / ANCHOR DESIGN (same structural ceiling as Stripe) |
| SpaceX | Financial Health | 6.0 | PRIVATE INFORMATION (Unit Economics/Runway undisclosed; no fabrication this time -- the real $13.3B/$4.5B figures were used correctly) |

(SpaceX's Execution, 7.0, is the one SpaceX pillar that used its
available evidence in a way that looks accurate and unremarkable --
MIXED PERFORMANCE, not flagged as a defect.)

## Conclusion

**UPPER SPS RANGE STILL APPEARS STRUCTURALLY SUPPRESSED — INVESTIGATE
BEFORE BLIND VALIDATION**

Exact evidence for this conclusion:

1. Neither of the two obtainable, deliberately-selected, maximally-
   favorable real companies came within 4 points of 80, let alone 85+.
2. The 9-10 band is demonstrably not decorative in the abstract (Stripe
   reached 9.0 six times) -- but no *company* got close to a high
   *overall* SPS, because the Traction/Financial-Health structural
   coverage ceiling (confirmed, by design, unchanged this phase) caps
   30% of total pillar weight at a Low-confidence, thin-evidence result
   for every real company tested to date, including these two.
3. This run additionally surfaced a **new, real, previously
   undocumented defect** -- SpaceX's Market, Product, and Founder-
   Market-Fit dimensions were marked Unavailable despite specific,
   correctly-retrieved, substantial evidence sitting in its own research
   brief, using an evidentiary bar stricter than the dimension's own
   written rule. This is not the same mechanism Phase 10.8B's research-
   sourcing fix addressed (that fix assumed the research would be
   insufficient; here the research was sufficient and the classification
   step still discarded it), and it was not fixed in this read-only
   phase per its own explicit instruction.

Per the phase's own instruction, nothing was changed because a score
"looked wrong." Stripe's 76.4 and SpaceX's 62.7 are both preserved and
reported exactly as produced. But the presence of an un-investigated,
newly-discovered classification defect, on top of the already-known and
deliberately-unaddressed structural ceiling, means a blind validation
run right now would still be measuring at least two suppression
mechanisms this diagnostic surfaced, not yet just the underlying
methodology. The responsible choice is to investigate the SpaceX-type
defect first.
