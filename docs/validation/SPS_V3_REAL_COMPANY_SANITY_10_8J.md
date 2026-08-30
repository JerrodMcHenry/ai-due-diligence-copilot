# SPS V3 Real-Company Sanity Set (Phase 10.8J, Parts 21-22)

10 companies selected from the existing 31-company `calibration_evidence.py`
dataset (Phase 10.8I). **No new companies, no new research** -- every
figure below comes from re-running the already-built, unmodified
`run_calibration.py` after this phase's gate simplification. Selection
spans strong / ordinary / weak-distressed / sparse-evidence /
evidence-richer / different stages, per the directive. This is
deliberately NOT a "does this famous company score high enough" exercise
-- the 9 questions below never ask that.

The 9 questions, per company:
1. Does SPS publish now (SUFFICIENT), or what UX state does it land in?
2. What is Coverage?
3. What is Confidence?
4. Which pillars are scoreable (individually publishable)?
5. Which pillars are unknown/insufficient?
6. Is the result explainable (can it be traced to specific evidence)?
7. Is the company rewarded for missing information anywhere?
8. Is the company punished for missing information anywhere (beyond the
   expected Coverage reduction)?
9. Does negative evidence, where present, appropriately lower Strength?

---

### CAL-003 -- Vercel (Series B+, strong/evidence-rich profile)
1. LIMITED (SPS withheld, Team pillar individually publishable).
2. Coverage 13.0%.
3. Confidence HIGH (on the Team pillar).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes -- Team's score traces to specific founder-history evidence
   (`cited_evidence_ids`), not a generic default.
7. No -- Team's HIGH confidence reflects genuinely strong, corroborated
   founder evidence in the sourced dataset, not an absence of
   contradicting information.
8. No beyond the expected Coverage hit -- the other 5 pillars show
   `strength=None`, never a penalized low number.
9. N/A -- no negative evidence in this company's evidence set.

### CAL-021 -- Carta (Growth, mixed/documented struggles)
1. LIMITED.
2. Coverage 13.0%.
3. Confidence HIGH (Team).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes.
7. No.
8. No beyond expected Coverage reduction -- notably, Carta's
   well-documented 2023 governance/trust issues live in `Execution`-
   or `Team`-adjacent territory in the real world, but that evidence
   wasn't part of the 10.8I sourced set for this company, so it
   correctly does not appear here. This is a dataset-completeness
   observation, not a scoring defect: the architecture only ever
   penalizes based on evidence actually supplied to it.
9. N/A for this company's dataset (no `NegativeSignalObservation`s
   were sourced for Carta in 10.8I).

### CAL-025 -- Convoy (Growth, failed/shut down 2023)
1. LIMITED.
2. Coverage 15.0%.
3. Confidence HIGH (Execution).
4. Execution.
5. Market, Team, Product, Traction, Financial Health.
6. Yes -- Execution's 4.31/10 strength traces to the specific
   `failed_commercial_expansion` (SEVERE) and `severe_cash_constraint`
   (SEVERE) negative observations sourced for this company.
7. No.
8. No beyond expected Coverage reduction.
9. **Yes, directly demonstrable** -- Execution scores 4.31/10, well
   below `band.multiple_signals`' neutral-positive midpoint (7.5) and
   below `band.single_signal` (5.5), reflecting the SEVERE negative
   evidence pulling the weighted average down. This is the clearest
   real-world confirmation in the sanity set that negative evidence
   moves Strength in the correct direction, not just in synthetic tests.

### CAL-026 -- Olive AI (healthcare AI, failed/wound down 2023)
1. LIMITED.
2. Coverage 15.0%.
3. Confidence HIGH (Execution).
4. Execution.
5. Market, Team, Product, Traction, Financial Health.
6. Yes, same structure as Convoy.
7. No.
8. No beyond expected Coverage reduction.
9. Yes -- same 4.31/10 Execution strength pattern as Convoy (both
   companies carry the identical `failed_commercial_expansion` +
   `severe_cash_constraint` SEVERE pair in the sourced 10.8I evidence),
   confirming the negative-evidence-lowers-Strength behavior is
   consistent across companies with comparable failure evidence, not a
   one-off.

### CAL-030 -- Mailchimp (historical snapshot, as-of 2020-01-01, capital-efficient)
1. LIMITED.
2. Coverage 14.0%.
3. Confidence HIGH (Team).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes.
7. No.
8. No beyond expected Coverage reduction -- notably, Mailchimp's famous
   bootstrapped/capital-efficient profile (the reason it was selected
   for the calibration roster at all) does NOT show up as a Financial
   Health strength here, because Financial Health is Unknown for this
   company at this Coverage level -- correctly withheld rather than
   inferred from reputation.
9. N/A (no negative evidence in this company's sourced set).

### CAL-031 -- Fast (historical, as-of 2021-06-01, failed/shut down 2022)
1. LIMITED.
2. Coverage 18.0% (highest of the historical-snapshot companies in this set).
3. Confidence HIGH (Team).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes.
7. No.
8. No beyond expected Coverage reduction. Notably, Fast's real 2021
   revenue (~$600K) and burn (~$10M/month) figures were **deliberately
   excluded** from its evidence set during 10.8I because they were only
   reported retrospectively in April 2022 shutdown-coverage articles --
   unknowable as of the 2021-06-01 as-of date. This means Fast is NOT
   punished here for its famously bad unit economics, because that
   specific information would have been hindsight leakage. This is
   correct behavior for an as-of-date-honest system, even though it
   means this particular sanity check can't demonstrate Fast's negative
   evidence being caught (Financial Health is Unknown, not scored-low).
9. N/A for the reason above -- the negative financial evidence exists
   in the real world but was correctly excluded from this as-of-dated
   evidence set; see Convoy/Olive AI above for the negative-evidence
   confirmation instead.

### CAL-001 -- Balance (Pre-Seed, YC W26, sparse evidence by design)
1. INSUFFICIENT (no pillar individually publishable).
2. Coverage 9.0% (lowest in the sanity set, as expected for pre-seed).
3. N/A -- no pillar reaches a confidence-bearing publishable state.
4. None.
5. Market, Team, Product, Execution, Traction, Financial Health (all six).
6. Yes, trivially -- the explanation is "not enough evidence yet,"
   which is itself an honest, traceable statement (zero dimensions
   scorable), not a silent failure.
7. No.
8. No -- INSUFFICIENT is the correct, undramatic outcome for a
   pre-seed company with minimal public footprint; nothing here reads
   as a penalty beyond the accurate Coverage number.
9. N/A (no negative evidence).

### CAL-012 -- Perplexity AI (Series C/D, strong, highest Coverage in the 31-company set)
1. LIMITED.
2. Coverage 20.0% (highest of any of the 31 companies at 10.8I's
   research depth -- included specifically to test the top of the
   achievable range).
3. Confidence HIGH (Team).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes.
7. No -- even at the dataset's highest Coverage, only Team clears the
   40% pillar floor, which is an honest reflection of 10.8I's shallow
   per-company research rather than a scoring bias toward well-known
   companies (Perplexity is not treated more favorably than Convoy or
   Balance beyond what its actual sourced evidence supports).
8. No beyond expected Coverage reduction.
9. N/A (no negative evidence sourced for this company).

### CAL-018 -- Flexport (Growth, distressed/mixed profile)
1. INSUFFICIENT.
2. Coverage 12.4%.
3. N/A.
4. None.
5. All six.
6. Yes, same as Balance -- honest "not enough evidence."
7. No.
8. No.
9. N/A for this specific company's sourced set at 10.8I's depth (no
   `NegativeSignalObservation`s were included for Flexport, despite its
   real-world distressed reputation) -- again a dataset-completeness
   note, not a scoring defect: the system only reflects evidence it was
   actually given.

### CAL-023 -- ZipRecruiter (Growth/Public, profitable but slower growth)
1. LIMITED.
2. Coverage 16.7%.
3. Confidence HIGH (Team).
4. Team.
5. Market, Product, Execution, Traction, Financial Health.
6. Yes.
7. No.
8. No beyond expected Coverage reduction.
9. N/A (no negative evidence in this company's sourced set).

---

## Cross-company observations

- **9/10 land in LIMITED, 1/10 (Balance) in... ** -- correction, actual
  tally: 8 LIMITED (Vercel, Carta, Convoy, Olive AI, Mailchimp, Fast,
  Perplexity, ZipRecruiter), 2 INSUFFICIENT (Balance, Flexport), 0
  SUFFICIENT. Consistent with the full 31-company tally (19 LIMITED / 12
  INSUFFICIENT / 0 SUFFICIENT) -- this 10-company subset is not an
  outlier sample.
- **Team is overwhelmingly the pillar that clears the individual-pillar
  bar** (7 of the 8 LIMITED companies) -- reflecting that founder/team
  background is the most consistently well-documented dimension type in
  public sources at 10.8I's research depth, not a scoring bias toward
  Team specifically (Team's pillar weight was not changed this phase).
  Execution is the only other pillar that clears the bar in this
  subset, and only for the two companies with SEVERE negative evidence
  (Convoy, Olive AI) -- because negative evidence is still evidence:
  a documented failure produces a scoreable (and correctly low)
  Execution dimension, whereas an undocumented-but-fine execution
  history produces nothing scoreable at all.
- **No company in this set is rewarded for missing information.** Every
  unknown pillar shows `strength=None`, never a neutral-default number.
- **No company is punished beyond the expected Coverage reduction.**
  The only borderline case worth flagging honestly (Carta, Flexport) is
  that some companies' real-world negative reputations are NOT reflected
  here because that evidence wasn't part of 10.8I's sourced set -- this
  is a dataset-depth limitation, not a methodology defect: the
  architecture never fabricates negative evidence it wasn't given, which
  is correct, but it also means "no negative evidence found" and
  "negative evidence exists but wasn't sourced" currently look identical
  to the score. This is worth naming as a known limitation of the
  *research depth*, not the *scoring logic*, and is explicitly the kind
  of gap a future, larger research pipeline (out of scope this phase)
  would need to close -- not a reason to change any formula here.
- **Negative evidence, where present in the sourced data, works
  correctly**: both Convoy and Olive AI's Execution pillars score
  4.31/10 -- meaningfully below the neutral-positive band midpoints,
  directly attributable to their SEVERE negative observations.
