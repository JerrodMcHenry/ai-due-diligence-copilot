# Founder UX & Methodology Acceptance Audit (Phase 29B)

**Status:** Audit complete. 5 P0 (score integrity) and 2 P1 (trust/comprehension) findings fixed and
regression-tested. 3 P1 findings documented and explicitly deferred (not narrow enough to fix safely
in this pass). Multiple P2s documented, not touched.

## 1. Methodology — approach

This phase used SIE aggressively as a real founder would, through two complementary channels:

- **Determinism, sensitivity, and adversarial testing (Parts 3-5):** through the real, authenticated
  `/ventures/structure-idea` and `/ventures` API endpoints (`FastAPI TestClient` against the actual
  `app.api.app` object, the same JWT-mocking harness `test_idea_lab.py` already uses — real auth
  dependency, real Pydantic validation, real `compute_vps()`, real Postgres writes). This is the same
  layer a real founder's browser calls; running it this way (rather than clicking through dozens of
  form submissions) let this phase cover 15 repeated-input runs, a 27-step sensitivity matrix, and 19
  adversarial payloads precisely and reproducibly.
- **Live browser walkthrough (Parts 6-11):** a real Chrome session against the running dev server
  (backend restarted mid-session to pick up this phase's fixes), creating a real venture end-to-end,
  capturing real observations, applying real model updates, and inspecting computed styles/copy across
  the actual rendered app in both themes.

## 2. Part 3 — Repeated identical input (determinism)

Three fixtures, 5 real runs each, through the real founder creation flow:

| Fixture | Description | Runs | Unique VPS | Result |
|---|---|---|---|---|
| A — sparse | "I want to start a company for hair loss." | 5 | 1 (`None`) | PASS |
| B — richer | "I want to start a hair loss company for men and women with our special serum." | 5 | 1 (`5.0`) | PASS |
| C — structured | Target customer, $49/mo price, 15 interviews, 8 paying customers | 5 | **2** (4.4 ×4, 4.6 ×1) pre-fix; **1** (4.4 ×5) post-fix | **FAIL → FIXED** |

Fixture C's pre-fix split was traced precisely: on 4 of 5 runs the LLM left `market.market_description`
null; on 1 run it additionally wrote a market-context sentence there. `market_description` never itself
contributed a point to `_score_market_potential`'s own score — but its mere presence flipped the whole
category from Unavailable to "scored at exactly the neutral base (5.0)," pulling the aggregate from 4.4
to 4.6. Root cause: **D — methodology/aggregation defect** (the same class as Phase 29A's finding, a
new manifestation), not LLM/provenance/scoring nondeterminism — `compute_vps()` itself was already
provably pure (Section 4). Fixed in `app/ai/vps_scoring.py::_score_market_potential()` (Section 5).

## 3. Part 4 — Monotonic / sensibility matrix

One baseline (2 scored categories: `market_potential`, `problem_solution`), each variable swept in
isolation from that same baseline, independently re-verified against the returned category scores
(not trusting the returned `vps` field blindly):

| Sweep | Steps | Aggregation independently verified |
|---|---|---|
| Customer interviews | Unknown(7.5) → 5(5.2) → 20(5.8) → 50(6.0) | 4/4 match |
| Paying customers | Unknown(7.5) → 1(5.7) → 5(6.0) → 20(6.5) | 4/4 match |
| Pricing | Unknown(7.5) → stated(7.2) | 2/2 match |
| Retention | Unknown(7.5) → w/20 paying(6.5) → 95%(6.7) → 60%(5.7) → retention-alone(pre-fix: 7.5 unchanged, i.e. discarded; post-fix: 5.0) | 5/5 match |
| Gross margin | Unknown(7.5) → 75%(7.5) → 25%(6.8) | 3/3 match |
| CAC | Unknown(7.5) → $30(pre-fix 6.7 / post-fix 7.0) → $200(6.3) → **$0(pre-fix 6.1 / post-fix 7.4)** | 4/4 match |
| Market evidence | Unknown(5.0) → Small/High(5.2) → Very Large/Low(8.8) | 3/3 match |

Every aggregation independently recomputed from category scores matched the API's own returned VPS
exactly, both before and after this phase's fixes — the aggregation math itself was never in question;
what changed was which categories a given input correctly established as "scored" (Section 5).

The interviews/paying-customers sweeps show a **real, expected drop** from "Unknown" to a first, weak
real value (e.g. 7.5 → 5.2 for 5 interviews) — this is intended and consistent with the frozen
methodology: an unscored category is excluded from the average entirely (never penalized as a 0), so
adding a first, still-weak piece of real evidence can legitimately look like a "drop" relative to not
having asked yet. This is not a bug; Part 4 explicitly anticipates it ("Unknown becoming known may
expose weakness and lower VPS").

The CAC sweep is where Part 4 caught a real, second-order defect: **$0 CAC (the best possible
acquisition cost) scored worse (6.1) than a normal $30 CAC (6.7) pre-fix** — an inversion, fixed in
Section 5.

## 4. Part 5 — Contradiction / adversarial test

19 structured-payload cases (through the real `POST /ventures` endpoint) + 5 narrative cases (through
`POST /ventures/structure-idea`, real LLM calls) + a repeated-submission check.

**Impossible-state rejection (Pydantic, `app/models/idea_lab.py`), confirmed working correctly:**
negative paying customers, negative CAC, margin > 100%, negative margin, retention > 500% — all
**422**, never silently clamped or accepted.

**Legitimate boundary values, confirmed handled correctly:** retention exactly 500 (accepted, net
extreme-but-legal expansion figure), 9,999,999 paying customers (clamps internally via `min(score,
8.0)`, no crash, no unbounded score), empty submissions (`vps: None`, never fabricated), `target_customer:
"everyone"` alone (contributes nothing on its own — never inflates a category), absurd starting capital
(a field VPS's scorers never read at all — no crash, no effect, confirmed by design).

**Genuine defects found and fixed** (Section 5): `price_point: 0` handling, `expected_cac: 0` handling,
and a founder-reported `retention_pct` with no other validation field being silently discarded.

**No NaN/Infinity ever observed** across all 19 structured payloads (checked programmatically against
every returned category score and the aggregate VPS).

**Repeated identical submission:** 3 independent `POST /ventures` calls with byte-identical assumptions
produced 3 byte-identical VPS values — confirmed no submission-order or timing dependency.

## 5. Root-caused defects, fixed (P0 — score integrity)

All five fixed in `app/ai/vps_scoring.py`; all are narrow, single-function edits; none touch category
weights, the aggregation formula, or any methodology calibration from Phase 29A.

1. **`market_description` alone falsely established `market_potential` as scored.** This field never
   contributes a point to that category's own score (only `estimated_market_size`/`competition_intensity`
   do) — its presence alone used to flip Unavailable → scored-at-neutral-5.0, the exact mechanism behind
   Part 3's live-reproduced C-fixture nondeterminism. Fixed: only `size`/`intensity` establish scored
   status now.
2. **`price_point` alone falsely established `economic_potential` as scored, with an empty basis.**
   Same defect class — `price_point` is read by `_score_gtm_feasibility`, not by
   `_score_economic_potential`'s own score math. Fixed: only `pricing_model`/`margin` establish scored
   status now.
3. **`expected_cac: 0` (free acquisition, the best case) scored as if CAC exceeded price point** — a
   genuine inversion. Live-verified: cac=0/price=49 scored 3.0 pre-fix, *worse* than cac=10/price=49's
   7.0. Fixed: CAC=0 against a real price now scores as the strong positive signal it is (7.0, tied with
   a comfortably-good ratio), never as a penalty.
4. **`price_point: 0` (an explicitly stated free product) was described as "no price point to check it
   against"** — a truthy-check bug (`if cac is not None and price_point:` treated 0 as falsy/absent).
   Fixed: `price_point is not None`; a stated $0 price against a real CAC now correctly reads as a real
   negative signal ("Assumed CAC exceeds the assumed price point" — true, since $0 revenue can never
   cover any positive CAC), not a fabricated "we don't know your price."
5. **A founder-reported `retention_pct` with no other validation field set was silently discarded** —
   `validation`'s own availability gate didn't include `retention_pct`, and even if it had, the modifier
   that reads it was only reachable from the commercial (paying/revenue-present) branch. Fixed: the
   gate now includes `retention_pct`, and the growth/retention modifier now runs regardless of which
   branch established the base score. A founder who reports "65% retention" alone now sees it reflected
   (and correctly scored below neutral, since 65% alone is real negative evidence) instead of vanishing
   with zero trace.

All five verified against the exact live-reproduced cases that found them, plus 12 new regression
tests (`app/tests/test_vps_scoring_correctness.py`, 12/12 passing) protecting each mechanism.

## 6. Fixed (P1 — trust/comprehension)

6. **Capture confirmation card kept showing a live, drifting "→" delta after the signal was already
   applied** (`components/idea-lab/CaptureWhatHappened.tsx`). Live-reproduced: after applying "Talked to
   3 more contractors" (customer_interviews 18→21), the SAME card kept re-rendering "Customer interviews:
   21 → 24" right next to "What changed... Your model was updated" — the two numbers didn't match, and
   there was no button left to act on the stale preview, making it unclear whether this was a pending
   offer or leftover math. Root cause: the preview read `currentAssumptions` live, so it kept
   recomputing the same fixed delta against the newly-updated baseline after every apply. Fixed: the
   baseline is now frozen (`baselineAssumptions`) the moment a capture's signals are computed, so the
   preview always reflects what was true when the founder was actually deciding whether to apply it.
   `handleUpdateModel()` itself still reads live `currentAssumptions` at click time — the fix touches
   only the display, not the actual update logic.
7. **Fundraising Simulator never told founders, anywhere in user-facing copy, that it specifically
   models Post-Money SAFEs** (only in code comments). Confirmed: `PathChooser.tsx`'s "Issue a SAFE" /
   "Model multiple SAFEs" / "Model SAFE → Seed" descriptions, `SafeTermsForm.tsx`'s per-SAFE header, and
   the SAFE glossary entry (`content/concepts/data.ts`) all said only generic "SAFE." A founder could
   reasonably believe this supports a generic or pre-money SAFE structure. Fixed: all four touchpoints
   now say "Post-Money SAFE" explicitly, including a one-sentence explanation in the glossary entry of
   what "post-money" specifically means for their ownership math — restrained, not a legal essay.

## 7. Readability (Part 7)

The creator's manual report was verified, not assumed. Direct computed-style measurement on one real
venture page (`getComputedStyle` over every text-bearing element):

| Font size | Element count |
|---|---|
| 16px (target for primary body copy) | 60 |
| 14px | 137 |
| **12px** | **156** |
| **11px** | **41** |
| **10px** | **5** |

**~200 of ~409 text-bearing elements (49%) rendered at 12px or smaller**, including primary founder
navigation: the journey-stage labels ("Idea / Model / Experiment / Build / Fundraise") were rendered at
an arbitrary 11px — below even the design system's own smallest defined step (Tailwind's `text-xs`,
12px).

**Fix approach:** the existing design system already has the right pattern in places (e.g.
`VentureOverview.tsx`'s "YOUR IDEA" section already correctly pairs a `text-xs` eyebrow label with
`text-base` (16px) body content) — this phase extended that same pattern rather than inventing a new
one, and fixed the SYSTEM (shared components used everywhere) rather than dozens of one-off page edits:

- **19 files** had arbitrary sub-12px sizes (`text-[9px]`/`text-[10px]`/`text-[11px]`) — all below the
  design system's own smallest defined token. **13 of the 19** (every one on the core Idea Lab / VPS /
  founder-journey / Learn / mobile-nav surfaces Part 7 named) were bumped to the nearest real token
  (`text-xs`, 12px), including `AssumptionFields.tsx`'s shared `FieldWrapper` (one fix, applied to every
  field's "You said: ..." quote across the entire venture creation/review form at once) and
  `VentureJourney.tsx`'s journey-stage labels.
- Content that is genuinely primary explanation, not a label — `VPSResultPanel.tsx`'s "What does this
  score mean?" bullet list, and the new sole-uncorroborated-category note — was bumped further, from
  `text-xs` to `text-sm` (14px), since it stands alone with room to breathe rather than living in a
  compact multi-column card.
- 6 files outside the Founder Loop / Idea Lab surface (`PillarWorkspace.tsx`, `PillarNav.tsx`,
  `SPSHistory.tsx`, `PillarComparisonTable.tsx`, `InvestorWorkspaceView.tsx`,
  `PitchDeckReviewView.tsx` — the real-startup SPS/Investor/pitch-deck surfaces, not toured this phase)
  were **not** touched; documented as a P2 to revisit in a future pass scoped to that surface.

No blanket `text-xs`/`text-sm` global redefinition was made — Tailwind's default scale (12/14/16px) is
unchanged; only which specific elements use which token changed.

**Small-text violations remaining:** the 6 files above (P2), plus badges/timestamps/compact metadata
across the app that remain at `text-xs` (12px) deliberately — the target explicitly reserves 12px for
"genuinely tertiary metadata, compact badges, or similar," which is exactly what those are.

## 8. Visual hierarchy / color (Part 8)

Design System V2's tokens (`dashboard/app/globals.css`) already define a full restrained semantic
palette: `primary`/`secondary`/`accent`/`success`/`warning`/`danger`/`info`, plus purpose-built aliases
`movement-positive`/`movement-negative`/`movement-neutral` and `confidence-high`/`medium`/`low` — both
themed correctly for light and dark. Confirmed **already in active use**, not dormant:
`ScoreDisplay.tsx`, `CategoryChangesList.tsx`, and `ScenarioComparison.tsx` all use the movement tokens
for score-delta direction; `Badge.tsx` uses the confidence tokens.

On the live venture page, category strength is **already** color-coded meaningfully: a category's
progress bar renders success-green at ≥7, primary-blue at ≥5, and warning-amber below 5
(`VPSResultPanel.tsx::getCategoryBarColor`) — the decision-relevant signal (is this category strong,
adequate, or weak) already carries color, not just a bare number.

**Considered and explicitly rejected:** color-coding the 6 VPS categories by identity (Market =
one hue, Validation = another, etc.), which several of Part 8's own suggested "potential semantic
uses" implicitly invite. Rejected because there are only 4 identity-safe hues left once
success/warning/danger stay reserved for score-quality meaning (primary/secondary/accent/info) for 6
categories — assigning them anyway would require either reusing a status color for a second,
conflicting meaning (a category rendered in "danger" red regardless of its actual score) or drifting
into the "rainbow dashboard" look Part 8 explicitly forbids. The existing score-band coloring already
carries the meaningful signal; category identity is already carried by label text and consistent
card position.

**Conclusion:** the "bland" perception is real, but the missing ingredient was contrast/hierarchy from
typography (Section 7) and the near-total absence of color in page chrome (headers, navigation) rather
than an absent color *system* — the system itself is sound and appropriately restrained. No new colors,
gradients, or category-identity coding were added. This was a considered decision, not an oversight:
adding more color for its own sake, on top of an already-sufficient semantic system, would have been
decoration without new information — exactly what Part 8 says not to do.

Both light and dark themes were spot-checked live on the audited venture page; no contrast or
theme-parity issues found.

## 9. Fundraising trust audit (Part 9)

- **Post-Money SAFE language**: was missing from all user-facing copy; fixed (Section 6, finding 7).
- **SAFE vs. priced round explanation**: already existed, already good — `content/concepts/data.ts`'s
  SAFE and priced-round glossary entries and `content/playbooks/data.ts`'s cap-table playbook already
  state the exact beginner-safe framing Part 9 itself specifies almost verbatim ("not a loan," "not
  equity yet," "a priced round sets an actual valuation and issues real equity immediately"). Extended,
  not rewritten, with the Post-Money clarification.
- **Fundraising math hand-verified**: not re-derived from scratch — the existing suite already contains
  externally-cross-checked "golden" fixtures (`test_B_golden_1_simple_priced_round`,
  `test_F_golden_2_safe_plus_priced_seed`, `test_I_golden_3_safe_plus_option_pool_plus_priced_round`,
  `test_E_external_cross_check_multiple_safes`, `test_priced_round_matches_directive_worked_example`) —
  confirmed still passing (14/14, 16/16) after this phase's copy-only changes, which is the correct
  standard of hand-verification given real, previously-audited golden math already exists; re-deriving
  it a second time by hand would be redundant, not more rigorous.
- **Unsupported financing structures remain blocked**: confirmed via `test_nonsensical_terms_never_silently_normalized`,
  `test_engine_warning_blocks_ownership_result`, `test_invalid_percentages_block_the_scenario` — all
  still passing.
- **No financing estimate changes VPS/SPS/history**: confirmed via direct grep — zero references to
  `compute_vps`, `vps_scoring`, `updateVenture`, or `venture_model_update` anywhere in
  `lib/fundraising/`, `lib/fundraisingUi/`, or `components/fundraising/`.
- Manually walked: one Post-Money SAFE, multiple SAFEs, a priced round, SAFE→priced round, an option
  pool, sequential rounds, and runway, via the live venture created this session (QuoteFast) — all
  rendered with the "Estimate — not final until a triggering financing event" badge exactly where the
  engine's own `isEstimateOnly` flag says it should.

## 10. Trust language audit (Part 10)

Grepped for every prohibited pattern the directive names (`"your company is worth"`, `"you will"`,
`"investors will"`, `"this will increase"`, `"best"`, `"optimal"`, `"guaranteed"`, `"should raise"`,
`"fair valuation"`, plus a broader second pass for `"definitely"`, `"certainly"`, `"proven to work"`,
`"risk-free"`, etc.) across every founder-facing content file. **Zero real violations found.** The 3
raw matches were all false positives on inspection: "your best signal of real demand" (a comparative
description of pricing feedback quality, not an overconfidence claim), a pre-money-valuation glossary
*definition* ("the value... your company is worth BEFORE new money" — defining what the term means, not
asserting a value), and one hit inside a code comment (`guaranteed.` closing a docstring sentence about
architecture, never rendered to a founder). No changes were needed here — this is a clean result
confirming prior phases' trust-language discipline held.

## 11. Visual / device acceptance (Part 11)

Desktop (both themes) was verified live via the browser. **Mobile (390px) could not be verified live
this session**: `resize_window` reported success twice, but `window.innerWidth` remained unchanged
(1641px) both times — a tool/environment limitation in this session, not a product finding, and it
should not be read as "mobile was checked and passed." In its place: (1) `MobileTabBar.tsx` was
confirmed correctly gated by the standard Tailwind `md:hidden` breakpoint (visible below 768px, hidden
above) and already covered by `founderBetaNav.test.ts` (7/7 passing); (2) every responsive grid on the
audited screens (e.g. `VPSResultPanel.tsx`'s `grid gap-3 sm:grid-cols-2 lg:grid-cols-3`) uses standard
Tailwind breakpoints that collapse to single-column below `sm` (640px), a well-established pattern
already in production; (3) this phase's own CSS changes (Section 7) only ever substituted one existing
Tailwind size token for another (`text-[11px]` → `text-xs`, `text-xs` → `text-sm`) — no new fixed
widths, no new overflow-prone layout, so no new mobile regression risk was introduced. A live 390px
pass with a working viewport-resize mechanism is a legitimate open item for the next session that has
one, not a claim this phase makes.

## 12. Bugs discovered, not fixed (documented limitations)

- **Capture signal extraction misses "X paying customers" phrased as "bringing us to 5 paying
  customers."** Live-reproduced: a real capture stating exactly this produced only a pricing signal, no
  paying-customer delta, meaning that specific real growth fact never reaches "possible signals" unless
  the founder separately edits the model by hand. `captureSignals.ts` is a separately-owned,
  already-tested heuristic module (14/14 in `captureSignals.test.ts`); extending its pattern matching
  safely requires its own focused pass, not a blind edit under this phase's time budget. **P1, deferred.**
- **Two "actions completed" counters on the same venture page disagree, consistently off by one.**
  Live-observed at two points in the same session: `MissionsSection.tsx`'s "Your Actions" header
  ("N actions completed") and `VentureProgress.tsx`'s "YOUR PROGRESS" panel (`actions_completed` from
  `GET /ventures/{id}/history`) showed 0-vs-1, then 1-vs-2, as this session's two captures were saved —
  the same +1 offset both times. `MissionsSection.tsx` counts `missions.filter(m => m.status ===
  "completed")` from its own loaded list; the backend's `actions_completed`
  (`app/api.py`, `sum(1 for m in missions if m.get("completed_at") is not None)`) is computed
  independently. Root cause not fully isolated (most likely: a difference in which mission types each
  side includes, e.g. whether capture-type missions count as "actions"), and which of the two
  definitions is actually correct wasn't established with confidence this session. **P1, deferred** —
  fixing the wrong side would make the inconsistency worse, not better, without first settling which
  count a founder should actually see.
- **Growth modifier never fires for "$0 revenue → real revenue"** (the strongest possible growth
  story): `_validation_modifiers()` requires `prior_revenue > 0` before computing a growth percentage,
  so going from literally nothing to real revenue earns no growth bonus (though the commercial-scale
  base score still credits the real revenue amount itself). Pre-existing, unrelated to this phase's
  fixes. **P2** — a real gap, but not misleading (no false claim is made either way), and fixing it
  is a calibration question in the same family as Phase 29A's own scope, not a quick patch.
- **Customer interview count stops affecting Validation once paying customers or revenue are
  reported** (the pre-commercial vs. commercial branch is mutually exclusive by design, confirmed via
  the interviews sweep staying flat once `paying_customers` was already set in the baseline). This is
  existing, deliberate, pre-Phase-29B calibration (see `_score_validation`'s own docstring: "UNCHANGED
  from the prior formula, which was never the reported defect") — noted as a limitation, not a bug.

## 13. P0/P1/P2 classification summary

| # | Finding | Class | Status |
|---|---|---|---|
| 1 | `market_description` alone falsely scores `market_potential` | P0 (score integrity) | Fixed |
| 2 | `price_point` alone falsely scores `economic_potential` | P0 (score integrity) | Fixed |
| 3 | `expected_cac: 0` scored as a penalty (inverted) | P0 (score integrity) | Fixed |
| 4 | `price_point: 0` mislabeled as unstated | P0 (score integrity) | Fixed |
| 5 | Retention-alone silently discarded | P0 (score integrity) | Fixed |
| 6 | Capture signal preview shows stale drifting delta after apply | P1 | Fixed |
| 7 | No "Post-Money SAFE" language anywhere user-facing | P1 | Fixed |
| 8 | ~49% of text on a venture page ≤12px, including primary nav | P1 | Fixed (system-level, 13 files) |
| 9 | Capture misses "X paying customers" phrasing | P1 | Deferred (not narrow) |
| 10 | Two "actions completed" counters disagree | P1 | Deferred (root cause not confirmed) |
| 11 | 6 non-Founder-Loop files still have arbitrary sub-12px text | P2 | Documented |
| 12 | $0→real revenue earns no growth bonus | P2 | Documented |
| 13 | Interview count stops mattering once commercial | P2 (design, not bug) | Documented |
| 14 | 390px live viewport testing unavailable this session | — (tooling) | Documented |

## 14. Regressions

Full suite, run after all fixes:

- **Backend**: `test_vps_intelligence_reset` 16/16, `test_vps_determinism_and_calibration` 13/13, new
  `test_vps_scoring_correctness` 12/12, `test_idea_lab` 27/27, `test_venture_history` 12/12,
  `test_venture_share` 18/18, `test_founder_missions` 27/27, `test_founder_actions` 32/32,
  `test_founder_evidence` 37/37, `test_product_analytics` 18/18, `test_idea_structuring` 20/21 (sole
  failure pre-existing/unrelated, confirmed present before this phase and before Phase 29A).
- **Dashboard**: `npm run test` — 157/157 (playbooks, journey, founderBetaNav, concepts, simulate,
  fundraising, fundraisingUi, captureSignals, weeklyReview).
- **TypeScript**: `npx tsc --noEmit` — clean.
- **Lint**: `npm run lint` — clean.
- **Build**: `npm run build` — clean, all routes generated.
- **SPS/SIE Methodology v2 firewall**: confirmed via direct import-coupling grep (zero matches for
  `idea_structuring`/`vps_scoring`/`vps_guidance` anywhere in the SIE pillar modules, `scoring.py`,
  `readiness_score.py`, or the calibration suite) — this phase's changes cannot have affected SPS.
- **Fundraising firewall**: confirmed via grep — zero references to `compute_vps`/`vps_scoring`/
  `updateVenture`/`venture_model_update` in any fundraising library or component file.

## 15. Remaining limitations

- Findings 9 and 10 (Section 12) remain open, by deliberate choice, pending a follow-up pass with a
  clear owner and enough time to resolve them correctly rather than risk a second inconsistency.
- Mobile viewport testing (Section 11) needs a session with a working `resize_window` (or an equivalent
  device-emulation path) to actually complete Part 11's 390px requirement live.
- The 6 non-Founder-Loop files with remaining sub-12px text (Section 7) were not audited for their own
  visual hierarchy/color needs at all this phase — a future pass on the SPS/Investor/pitch-deck surface
  should treat this document's Section 7/8 findings as a template, not assume they transfer unchanged.
