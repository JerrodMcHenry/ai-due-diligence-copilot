# SIE Product End-State & Network Architecture (Phase 30)

**Status:** Strategy and architecture specification only. No code, database, VPS, SPS, or scoring
changes were made in this phase. Every claim below about the current product is grounded in the live
repository as of this audit (file paths and row counts cited); every claim about the future is
explicitly marked as a recommendation, not a decision already made.

---

## Part 1 — Audit of the Product That Actually Exists

Ground truth first. Live database row counts at the time of this audit:

| Table | Rows | What it tells us |
|---|---|---|
| `startups` | 23 | Real companies with at least one canonical analysis |
| `analyses` | 86 | Re-analysis is common (~3.7 analyses/startup) — the SPS track is used longitudinally |
| `modeled_ventures` | 53 | Idea Lab has more usage than the real-startup track — low friction works |
| `saved_startups` (the *only* watchlist table, used by both "Saved Startups" and "Investor Workspace") | 3 | Watchlist/investor behavior is not happening in practice yet |
| `startup_claims` | 5 | A handful of founders have claimed their own analyzed company |

### A. Idea / Venture Track
**Purpose:** let anyone turn a raw idea into a structured, evidence-tagged model and operate it.
**Canonical entity:** `modeled_ventures` (`app/database/db.py::create_modeled_ventures_table`).
**Persistence:** `modeled_ventures`, `venture_missions` (Actions + Capture, unified), `venture_model_updates`
(history), `product_events` (analytics).
**Scoring:** VPS (`app/ai/vps_scoring.py`) — deterministic, 6 categories, no LLM, no persistence of its
own (recomputed and stored as `model_result` JSON on the venture row itself).
**Evidence:** founder-typed assumptions + explicitly-flagged validation observations (interviews,
waitlist, paying customers, revenue) — provenance-tagged at structuring time
(`app/ai/idea_structuring.py`).
**Founder-facing value:** immediate structure, a venture-state description (Idea/Validating/Building,
Phase 29 correction), a single deterministic next-action, What-If simulation, a Fundraising Simulator,
Weekly Review, a shareable public Snapshot.
**Investor-facing value:** none directly — a shared Snapshot is the only investor-visible artifact, and
it is founder-initiated, opt-in, and privacy-firewalled (Phase 27).
**Connects to the rest of SIE:** **no** — see the graduation finding below.
**Duplication/overlap:** this track has its *own* complete operating-loop primitive set (Actions,
Capture, History, Weekly Review) that is structurally unrelated to the real-startup track's equivalent
primitives (see Part 6).
**Dead-end behavior:** none currently known (Phases 26/29A/29B/29C closed the ones that were found).

### B. Real Startup / Founder Track
**Purpose:** let a founder who has *already been analyzed* (via Analyze) manage the company on an
ongoing basis.
**Canonical entity:** `startups` + `startup_memberships` (who owns/manages which startup) +
`startup_claims` (the request-to-claim workflow).
**Persistence:** `founder_actions`, `founder_updates`, `startup_milestones` — three separate tables,
**not** `venture_missions`/`venture_model_updates`. This is a second, independent operating-loop
implementation, not a shared one.
**Scoring:** SPS (`app/ai/scoring.py` + Methodology v2) — LLM-scored, six pillars, confidence/evidence
tagged, calibrated (`app/calibration/`).
**Evidence:** whatever the original Analyze submission contained, plus anything a founder later adds via
`founder_updates`.
**Founder-facing value:** SPS trend, an action plan, milestones, and — critically — **Fundraising
Readiness** (see below), a fully-built system this phase's audit found already answers most of what
Phase 30 was asked to design.
**Investor-facing value:** the canonical SPS breakdown other users can see via Search/Rankings/Compare
if the startup surfaces there.
**Connects to the rest of SIE:** shares presentation primitives with the venture track (`NextStepCard`
is reused, confirmed in `FounderStartupWorkspaceView.tsx`) but **not** any data model.
**Duplication/overlap:** this is the load-bearing finding of this whole audit — **there are two parallel,
independently-built operating-loop stacks in this codebase, not one, and not zero.** See Part 6.
**Dead-end behavior:** no Weekly-Review-equivalent cadence exists on this track at all (confirmed: zero
matches for "Weekly Review" anywhere under the founder/startup surface). A founder here gets a
one-time action plan and milestones, never a recurring "what changed" digest.

### C. Analyze / Due Diligence
**Purpose:** the entry point that produces a canonical `StartupIntelligenceScore` from pasted
text/PDF/URL.
**Canonical entity:** `analyses` (each row a point-in-time SPS run), joined to `startups` by
`company_name`/`startup_id`.
**Scoring:** SPS, the system's most mature and calibrated asset (`app/calibration/expected_scores.py`).
**Evidence:** whatever research enrichment (Tavily) plus submitted text can support; every dimension is
Public/Inferred/Private-tagged (`app/ai/scoring_methodology.py`).
**Founder-facing value:** the one-time (or repeatable) evaluation; also the entry point into the Founder
Track via `startup_claims`.
**Investor-facing value:** the canonical intelligence artifact everything else (Rankings, Compare,
Watchlist, Fundraising Readiness) is built on top of.
**Duplication:** none — this is the one clearly singular, non-duplicated system in the product.

### D. Investor Workspace
**Purpose:** as-built, this is **"my watchlist with trajectory," not an investor identity or
discovery product.**
**Canonical entity:** `saved_startups` (bare `user_id, startup_id` relationship table — no notes, no
thesis tags, no role field) joined out to the two most recent canonical analyses per startup.
**Persistence:** none beyond the relationship row; every view (`assess_investor_workspace`) is
recomputed fresh.
**Scoring:** reuses SPS; adds pillar-level "what changed" deltas and staleness flags, which is a genuine,
useful, and currently-unique-in-this-audit feature — nothing else in the product computes "what changed
since I last looked."
**Founder-facing value:** **zero** — a founder cannot see that they are being watched, by whom, or how
many times. This is a structural privacy choice (Phase 15/29 privacy discipline), not an oversight, but
it also means there is no feedback loop back to the founder today.
**Investor-facing value:** real, if the watcher already knows which startups to watch.
**Connects to the rest of SIE:** joins to canonical `analyses`, otherwise isolated.
**Critical finding:** **there is no investor identity anywhere in this system.** `users` is
`(id, email, created_at)` — no role field exists. "Investor Workspace" is a URL any authenticated user
can visit; it is not gated by, or aware of, any investor status. Any product decision that assumes
"investors" as a distinct actor type is designing ahead of the data model.
**Dead-end behavior:** the workspace's own value depends entirely on Search/Rankings surfacing startups
worth watching, and those are the surfaces Phase 15 already found and de-emphasized as not-yet-credible
(see Part E). 3 total watchlist rows in the live database confirms this is not happening in practice.

### E. Public Discovery (Search / Rankings / Compare)
**Purpose:** browse and compare analyzed startups.
**Status, per Phase 15's own investigation (still true today — 23 startups total):** the dataset is
real but small. This is not a fabricated concern; it is measured. Discovery is functional but not yet
"a marketplace" by any reasonable definition — 23 companies is a demo dataset's scale, not a network's.
**Founder-facing value:** limited until a founder's own company is one of the 23 with credible data.
**Investor-facing value:** limited by the same dataset size.
**Duplication:** Rankings/Search/Compare/Discovery are genuinely three different UIs over the same
underlying `analyses` data — not duplicated logic, but a fragmented surface a user must already know to
visit three separate places to fully use.

### F. Learn / Playbooks
**Purpose:** contextual and now globally-navigable founder education (Phase 29C promoted it to the
primary `Build | Analyze | Learn` switcher).
**Canonical entity:** none — pure static content (`dashboard/content/playbooks/`), no persistence, no
scoring, deliberately.
**Founder-facing value:** real and already well-integrated (contextual "Learn how →" links from VPS
categories, missions, fundraising terms).
**Investor-facing value:** none, and none is proposed.
**Connects to the rest of SIE:** yes, extensively, by design — this is the one area of the product with
no duplication risk because it deliberately holds no state.

### G. Simulation (What-If / Model)
**Purpose:** ephemeral, non-persisting exploration of assumption changes.
**Canonical entity:** none — stateless (`POST /ventures/scenario-compare`), applies only via the
founder's own explicit Save.
**Duplication:** none. Correctly scoped to the venture track only; no real-startup equivalent exists,
which is arguably a gap (a real startup founder cannot "what-if" their own SPS-scored assumptions), not
a duplication.

### H. Fundraising
**Two systems exist here, doing genuinely different things, and this is the single most important
finding for Parts 3-5 of this phase:**

1. **Fundraising Simulator** (venture track) — pure math (SAFE/priced-round/dilution), zero AI, zero
   persistence beyond the founder's own explicit apply. Lives in `lib/fundraising/`.
2. **Fundraising Readiness** (real-startup track, `app/ai/fundraising_readiness.py`) — **this already
   is almost exactly what Phase 30 asked this audit to determine whether to build.** It is: fully
   deterministic (no LLM), stage-weighted (6 profiles from Idea through Growth), driven by evidence
   *confidence and coverage* rather than raw pillar score (its own docstring: "a startup can have high
   SPS with a great-looking but thinly-evidenced story (low readiness), or a modest SPS with a
   well-documented, defensible one (higher readiness than SPS alone would suggest)"), produces a 0-100
   `readiness_score` **and** a 4-band status (Early / Developing / Getting Ready / Raise Ready), a
   per-pillar breakdown, gaps with "why it matters" + a recommended next step wired directly into
   `founder_actions` (`source='fundraising_gap'`), investor-likely-questions, and a checklist. Zero new
   persistence — recomputed fresh from the startup's existing canonical analysis every time.

   **Its own module docstring already documents rejecting the alternative this phase might otherwise
   propose:** an earlier, ungrounded LLM-based "readiness_score" (`app/ai/readiness_score.py`) was found
   to be "effectively SPS restated in different words" and was superseded by this deterministic
   approach — the dashboard doesn't even render the old field anymore.

   **The gap:** this excellent system is (a) scoped only to the real-startup/SPS track, with zero
   connection to modeled ventures, and (b) framed narrowly as "Fundraising Readiness" rather than the
   broader, destination-independent "Investor Ready" status Phase 30's thesis describes. Both are fixable
   without a rebuild — see Part 18.

### I. Sharing / Distribution
**Purpose:** let a founder show their venture to someone outside SIE.
**Canonical entity:** `VentureSnapshotResponse` — an explicit, allowlisted public DTO (Phase 27),
never a serialized-then-hidden internal model.
**Founder-facing value:** real, and Phase 27's own adversarial privacy testing gives it real trust
grounding.
**Investor-facing value:** real but entirely founder-initiated and one-directional — a snapshot viewer
cannot watch, follow, or be identified back to the founder in any way today.
**Duplication:** none. This is the one piece of "founder → outside world" infrastructure that already
exists and already works; Part 6/7's designs should reuse it, not replace it.

### J. Analytics
**Purpose:** first-party product measurement (Phase 28).
**Canonical entity:** `product_events`.
**Value:** this is a genuine, already-built operational asset for measuring whether any Phase 30
recommendation actually changes behavior — not a gap, a strength to build on.

---

## Part 2 — Stress-Testing the Core Product Thesis

**Proposed thesis:** *"SIE is a startup intelligence platform that helps founders build evidence-backed
companies, become investor-ready, and continuously improve — while giving investors a structured way to
discover and evaluate startups based on real progress over time."*

**1. Is this supported by the architecture we have?**
**Half of it, solidly. Half of it, not yet.** The founder-facing half (build, evidence, continuous
improvement) is real and mature — VPS, the Idea Lab operating loop, SPS, Fundraising Readiness, Weekly
Review, Capture, and the Phase 29 non-linear founder-experience correction are all genuinely built and
tested. The investor-facing half ("discover and evaluate... based on real progress over time") is
**mostly aspirational today**: there is no investor identity, the discovery dataset is 23 companies, and
watchlist usage is 3 rows total. The trajectory/delta-tracking *logic* Investor Workspace already
computes is real and good — but it currently has almost nothing to watch and nobody watching it.

**2. Differentiation from adjacent categories?**
- **ChatGPT:** SIE's structured, provenance-tagged, deterministic-where-possible methodology (VPS/SPS
  never fabricate a score, always distinguish Unknown from assumed) is a real differentiator against a
  free-text chat interface with no persistent structured model. This holds.
- **Startup coaching tools / accelerator software:** these are advice-and-community products; SIE has no
  human-in-the-loop coaching or cohort structure. Differentiated by being self-serve and always-on, not
  by being better coaching.
- **Pitch-deck tools:** SIE has one (Pitch Deck Coach) but it is a feature, not the product; genuinely
  differentiated by living inside a broader evidence model rather than being a standalone deck grader.
- **Fundraising CRMs (Visible.vc):** Visible is investor-update/portfolio-monitoring-first, with 7,000+
  founders and 950+ funds already using it for exactly the "turn progress into investor communication"
  job. **This is the closest existing competitor to SIE's own Part 8 "Investor Updates" retention
  pillar** — SIE does not yet do this at all, and Visible does it well today. Real, not fooling
  ourselves.
- **Founder communities:** not a real competitor; different job entirely.
- **Investor databases (PitchBook, Harmonic.ai):** Harmonic.ai indexes 6M+ companies from public signals
  (hiring, web traffic, patents) to surface *undiscovered* deal flow — a fundamentally different data
  source than SIE's (founder-self-reported, structured, longitudinal). SIE's data is deeper per-company
  but exists for zero companies an investor hasn't already found through Harmonic-style tools first, at
  today's scale.
- **Cap-table products (Carta, Pulley):** genuinely adjacent, not competitive — SIE's Fundraising
  Simulator explicitly models *before* a real instrument exists; Carta/Pulley manage the real thing
  after. No overlap worth worrying about; a plausible future integration point, not a threat.
- **Due-diligence software (Harmonic Scout, UnicornScreener.vc, Dealroom):** these are investor-side AI
  agents that evaluate companies *investors already found*. SIE's SPS methodology is a genuine, real
  differentiator here (documented, calibrated, evidence/confidence-tagged, reproducible — Phase 29A's
  entire determinism-fix effort exists because this matters), but SIE has no comparable investor-facing
  distribution today.

**3. What is SIE's true moat if this succeeds?**
Separating what exists from what would have to be earned:

**CURRENT DIFFERENTIATION (real today):**
- A single coherent methodology spanning idea → validated venture → real startup → fundraising
  scenario, with deterministic, provenance-aware scoring throughout (VPS, SPS, Fundraising Readiness) —
  no other product in the research above spans this range in one system.
- Genuine reproducibility/trust engineering (Phase 29A's whole determinism-fix effort is evidence this is
  taken seriously, not asserted).
- An operating-loop UX (Capture → Model Update → Weekly Review) with no direct competitor doing exactly
  this for idea-stage founders.

**POTENTIAL COMPOUNDING MOAT (does not exist yet, would have to be earned):**
- Accumulated longitudinal founder + venture history *across many founders* — today this is 53
  ventures and 23 startups, not yet a dataset with statistical weight.
- Network effects between founders and investors — **do not exist today** (Part 12 makes this
  explicit; 3 watchlist rows is not a network).
- Proprietary benchmarks — cannot exist responsibly yet; the SaaS-benchmark research above (Aleph,
  342-peer comparisons) shows what a credible benchmarking product needs in sample size, and SIE is
  two orders of magnitude short.

**Conclusion:** the thesis is directionally right but currently describes an aspiration for the
investor half, not a built reality. The document below treats "current differentiation" and "future
moat" as separate categories throughout, per this section's own finding.

---

## Part 3 — Defining the Founder Destination

**Recommendation: yes, Investor Readiness (reframed, see below) should be the primary named
destination** — but as a *status describing durable company quality*, not a fundraising trigger.

**Working definition:** *"If this company were put in front of a serious investor today, where would it
withstand scrutiny, and where would diligence expose a gap?"* — deliberately independent of whether the
founder is actually raising. A profitable, non-fundraising company can and should still be able to see
"you would withstand scrutiny on economics but not on team depth," because that is genuinely useful
operating information regardless of capital plans.

**The smallest coherent framework, built from what already exists (Fundraising Readiness's own six
pillars), not a new list:** Market, Team, Product, Execution, Traction, Financial Health — the exact
same six SPS/Methodology-v2 pillars, re-weighted by the same stage-aware logic
`fundraising_readiness.py` already implements, with the same evidence-confidence-driven "defensibility"
logic. **Do not invent a second, longer list** (company/story clarity, cap table awareness, data-room
readiness, etc. as named in the directive's own brainstorm) — those are better expressed as gap items
*within* the existing six pillars (e.g., "cap table awareness" is a Financial Health gap; "data room
readiness" is an Execution/Financial Health gap) than as new top-level dimensions. Adding dimensions
multiplies both LLM prompt surface and founder cognitive load for marginal gain; the existing six already
cover the space.

---

## Part 4 — Score vs. Status vs. Checklist

Evaluated against the four options, informed by what already ships in `fundraising_readiness.py`:

| | Comprehension | False precision risk | Overlaps VPS | Overlaps SPS | Gaming risk | Trust | Explainability | Build cost |
|---|---|---|---|---|---|---|---|---|
| A. 0-100 score | Medium | **High** — a third number next to VPS/SPS invites "why is this different" confusion | Low | **High** — readers will assume it's a re-scoring of SPS | Medium | Low (a third number erodes, not builds, trust) | Medium | Already built |
| B. Status bands only | High | Low | Low | Low | Low | High | High | Trivial (already partially built) |
| C. Dimension checklist only | High | None | Low | Low | Low | High | Medium (loses the "how close" signal) | Low |
| **D. Hybrid: bands (primary) + checklist (detail) + score kept internal, never surfaced as a headline number** | **High** | **Low** | Low | Low | Low | **High** | **High** | **Already built** |

**Recommendation: Option D**, which is functionally what `fundraising_readiness.py` already computes —
the fix is not architectural but *presentational*: keep computing `readiness_score` internally (it
already drives the band and the pillar weighting cleanly), but **never headline it as a bare number the
way VPS and SPS are headlined.** Surface the band ("Getting Ready") as the primary signal, the gaps/
checklist as the actionable detail, and treat the numeric score as an internal aggregation detail a
founder can optionally expand into (mirroring how VPS's own `sole_uncorroborated_category` transparency
note works — explain, don't just display a number). **Default preference of "no new numeric score" is
satisfied**: this reuses the existing score, it does not create a fourth one.

---

## Part 5 — VPS, SPS, and Readiness Roles

**VPS answers:** *"Based on what I've told the model, how strong does my modeled venture look across the
things that make an idea work?"* — pre-evidence-heavy, founder-self-reported, explicitly uncalibrated,
scoped to `modeled_ventures` only.

**SPS answers:** *"Based on real evidence I can find or you've given me, how strong is this actual
company, right now, across six calibrated pillars?"* — evidence-graded (Public/Inferred/Private),
calibrated against real benchmark companies, scoped to `startups`/`analyses` only.

**Investor Readiness answers:** *"Given what SPS already found, how defensible is that finding under
outside scrutiny, and what would an investor's diligence process specifically challenge?"* — it does not
re-evaluate the company; it re-evaluates the *evidence behind* the company's existing SPS, stage-weighted.
This is already orthogonal by construction (`fundraising_readiness.py`'s own docstring states this
exactly) — Part 5's "must be orthogonal enough to justify existence" bar is already met by the existing
implementation, not something this phase needs to newly design.

**Should VPS stay venture-specific and SPS stay startup-specific?** Yes, unconditionally. They already
encode fundamentally different epistemics (modeled assumption vs. observed evidence) and merging them
would violate the "real evidence and modeled assumptions must remain distinct" invariant this codebase
has enforced since Phase 29A. **Investor Readiness, however, should NOT remain SPS-exclusive forever** —
see Part 6.

---

## Part 6 — Venture → Startup Graduation

**Current state, confirmed by direct inspection:** `modeled_ventures` and `startups` share **zero**
database relationship. The only bridge is `dashboard/lib/ventureToStartupHandoff.ts`, which stashes the
venture's raw free-text `description` in `sessionStorage` and pre-fills it into `/analyze` — explicitly,
by that file's own comment, **never** carrying VPS, assumptions, or validation evidence forward. A
founder who has been diligently using Capture/Weekly Review/Actions on their venture for months starts
completely from scratch, evidence-wise, the moment they analyze it as a real startup.

**Should graduation exist? Yes** — this is the single most concrete, low-risk, high-value gap this audit
found. **What it must NOT be** (per the directive's own explicit constraints, which this audit agrees
with): not VPS-triggered, not automatic, not a silent migration.

**Recommended trigger model:** founder-initiated only, offered (never forced) when *any* of these
signals are present — real paying customers reported, real revenue reported, or the founder has run
Analyze on their own venture's description at least once. These are **suggestions for when to surface
the option**, never a gate — a founder can graduate a bare idea if they choose, or never graduate a
venture with $50K MRR if they don't want to.

**What the founder sees:** an explicit, reversible-feeling ("this doesn't delete your venture") prompt:
*"Your venture QuoteFast now has real customers. Want to see it evaluated as a real startup?"* → routes
into Analyze with the venture's description **and now, additionally, its structured assumptions**
pre-filled as the "Additional Company Information" the founder can edit before submitting — a strict
superset of today's text-only handoff, still requiring the founder's own submission, never an automatic
write to `startups`.

**What carries forward:** the founder's own words (as today) plus a structured summary of
`VentureAssumptions` rendered as readable text (not raw JSON) — SPS still independently re-derives its
own scores from scratch, exactly as it does for any other Analyze submission, preserving the "each
system computes its own evidence" firewall.

**What remains venture history:** everything — `modeled_ventures`, `venture_missions`,
`venture_model_updates` are never deleted or migrated. The venture becomes historical record of "how we
got here," not a competing live system.

**How duplicate records are avoided:** a new, optional `graduated_to_startup_id` column on
`modeled_ventures` (nullable, set once, founder-visible), populated only after the founder completes a
real Analyze submission and confirms the link — never inferred from company-name matching (name
collisions are a known real-world risk this design must not create false-positive links from).

**Does Venture Snapshot become Startup Profile?** No — keep them structurally distinct.
`VentureSnapshotResponse` is explicitly, by Phase 27's own design, an allowlisted DTO that **cannot**
represent history, real evidence, or SPS. A graduated startup's public profile (if one is ever built)
would need a *different*, SPS-shaped DTO with its own privacy review — reusing the Snapshot renderer for
a fundamentally different evidence class would reintroduce the exact "serialize-then-hide" risk Phase 27
was built to avoid.

---

## Part 7 — Investor Readiness Experience (Spec Only)

**Where it belongs:** primarily on the real-startup/Founder Workspace track (where it already lives),
extended to appear on a graduated venture's workspace once graduation (Part 6) has happened. It should
**not** appear on an ungraduated modeled venture — Investor Readiness presupposes SPS-grade evidence,
which a modeled venture by definition does not have.

**How frequently it changes:** exactly as often as the underlying SPS re-analysis happens — it is a
derived view, not an independently-updating live score, matching its existing zero-persistence design.

**What data feeds it:** the startup's current canonical `SIEMethodologyAnalysis` (pillar scores,
confidence, evidence coverage) plus its stage — all of which already exists; no new data collection.

**How it connects to Actions:** already connected — gaps write into `founder_actions` with
`source='fundraising_gap'`. This wiring should be renamed/reframed (not rebuilt) to `source='readiness_gap'`
if Readiness is decoupled from "fundraising" specifically, so an action created from a readiness gap
doesn't read as "you must be about to raise."

**How it connects to Weekly Review:** **this is a genuine gap to close**, not something already wired —
the real-startup track has no Weekly Review at all (Part 1.B). A startup-track digest ("what changed in
your Readiness band this week") is the single most direct way to give this track the same operating
cadence the venture track already has.

**How it connects to Learn:** each gap's "recommended next step" should link to the existing Playbooks
library exactly the way VPS's `Learn how →` links already do — no new content system.

**How it connects to fundraising tools:** Readiness is upstream of the Fundraising Simulator
conceptually ("are you ready" vs. "what would this specific term sheet mean") — they should link to each
other, never merge into one screen.

**Before or after graduation:** strictly after — see Part 6.

---

## Part 8 — Post-Readiness Founder Retention

Ranked by founder value × frequency × willingness to pay × how much existing architecture already
supports it:

| Rank | Pillar | Founder value | Frequency | Willingness to pay | Build cost from here | Depends on network scale |
|---|---|---|---|---|---|---|
| **1** | **Operating Intelligence** ("what matters most right now") | High | Daily/weekly | High | **Already built** (NextStepCard, resolveIdeaLabNextStep, Fundraising Readiness gaps) | No |
| **2** | **Progress Intelligence** ("how has the company changed") | High | Weekly | High | **Mostly built** on venture track (Weekly Review, Venture History); needs the same on the startup track (Part 7) | No |
| **3** | **Living Startup Profile** ("maintain a credible representation") | Medium-High | As-needed | Medium | **Mostly built** (Venture Snapshot exists; a startup-grade equivalent is the main gap) | No |
| 4 | Investor Readiness | High but episodic | Monthly-ish | Medium | **Already built** | No |
| 5 | Fundraising Intelligence | High but episodic | Only while raising | High (during raise) | **Already built** (Simulator) | No |
| 6 | Investor Updates | Medium | Monthly | Medium | Not built; closest competitor (Visible.vc) already does this well | No |
| 7 | Benchmarking | Medium | Occasional | Low today, higher later | Not built; **explicitly blocked by dataset size** (23 startups; the SaaS-benchmark research above uses 342+ peers for credibility) | **Yes — hard blocker today** |
| 8 | Investor Visibility | Low today | N/A | Low today | Not built; **blocked by both dataset size and the missing investor-identity system** | **Yes — hard blocker today** |
| 9 | Data Room / Diligence Readiness | Medium | Rare (pre-raise) | Medium-High during raise | Not built; natural extension of Readiness gaps | No |
| 10 | Advisor / Board Reporting | Low-Medium | Monthly/quarterly | Low | Not built; closest to Investor Updates, likely the same feature | No |

**#1, #2, #3 are the retention core**, and the honest finding is that **#1 is fully built, #2 is half-built
(venture track yes, startup track no), and #3 is half-built (venture Snapshot yes, startup-grade profile
no)**. The two "network-dependent" pillars (Benchmarking, Investor Visibility) are correctly the
lowest-ranked — not because they're low-value in theory, but because this audit found the data doesn't
exist yet to make them honest.

---

## Part 9 — Investor Discovery Loop (Spec Only)

Audited: Search/Rankings/Compare/Investor Workspace/Watchlists/public Snapshot — see Part 1.D/E for the
concrete state (no investor identity, 23-company dataset, 3 watchlist rows total).

**Smallest legitimate loop, given what's real today:**

Founder builds → founder opts a *graduated startup* (never an ungraduated venture) into "discoverable" →
the startup can appear in Search/Rankings exactly as it does today (no change needed there) → any
signed-in user can save it to their watchlist (as today) → the founder sees **only an aggregate,
anonymized signal** ("3 people are watching this startup"), never who.

**Explicit constraints this design honors:**
- **Opt-in requirement:** discoverability must be a startup-level, founder-controlled setting, off by
  default — the same "private until shared" discipline Venture Snapshot already established.
- **Privacy model:** watcher identity stays private from the founder (matches Investor Workspace's
  existing design intent); only aggregate counts, if anything, are ever shown.
- **Minimum profile quality:** only startups with a canonical, current-methodology analysis should be
  discoverable — never an unanalyzed or stale one (matches `get_rankings()`'s existing "methodology
  version" filtering discipline).
- **Investor identity visibility:** **do not build "investor identity" as a concept yet** — there is no
  role system to back it, and fabricating one (e.g., a self-declared "I am an investor" checkbox with no
  verification) would create exactly the "fabricated views/watchlists" credibility risk the directive
  explicitly forbids.
- **Anti-spam:** because there is no investor verification, any future "investor may contact founder"
  feature must be explicitly out of scope until an identity/verification system exists — this phase
  recommends **not building direct contact at all** yet.

**What this phase explicitly does NOT recommend:** any claim of "investor discovery" as a marketed
capability at current dataset size and identity-system maturity. The honest current capability is
"opt-in visibility to other signed-in users," which is real but should not be oversold.

---

## Part 10 — Why Founders Keep Their Data Current: The Flywheel Map

Testing: *"The more accurately founders maintain SIE, the better their operating guidance becomes AND
the stronger their investor-facing intelligence profile becomes."*

| Link | Status |
|---|---|
| Capture → Structured Evidence | **Exists** (venture track: `captureSignals.ts` deterministic extraction) |
| Structured Evidence → Model | **Exists** (explicit "Update my model" step, Phase 26 firewall) |
| Model → History | **Exists** (`venture_model_updates`) |
| History → Weekly Review | **Exists** (venture track only) |
| Weekly Review → Readiness | **Does not exist** — Weekly Review is venture-scoped, Readiness is
startup-scoped; no bridge |
| Readiness → Startup Profile | **Partially exists** — Readiness reads the startup's canonical analysis,
but there is no "Startup Profile" artifact today distinct from the raw analysis record itself |
| Startup Profile → Investor Intelligence | **Does not exist** — Investor Workspace reads canonical
analyses directly, not through any profile layer |

**Honest conclusion:** roughly half this flywheel is real (the venture-side operating loop is genuinely
excellent), and it breaks exactly at the venture→startup seam identified in Part 6. **Closing the
graduation gap is therefore not just a UX nicety — it is the single missing link that would make this
entire flywheel real end-to-end**, which is the strongest argument in this whole document for Part 18's
recommendation.

---

## Part 11 — Investor Value Proposition

**Why would an investor use SIE instead of Crunchbase/PitchBook/LinkedIn/decks/spreadsheets/ChatGPT?**

Ranked by value × uniqueness × data dependency × cost:

1. **Trajectory / "what changed since I last looked"** (Investor Workspace's existing pillar-delta
   logic) — genuinely differentiated; none of Crunchbase/PitchBook/decks compute this today, because none
   of them have a founder actively maintaining structured evidence over time. **Already built.** This is
   SIE's strongest honest investor-side claim.
2. **Structured, evidence/confidence-graded profiles** (SPS itself) — differentiated from static decks
   and from PitchBook's firmographic data, but Harmonic.ai and similar AI-native tools are converging on
   similar structured evaluation from a different data source (public signals vs. founder-self-reported).
   Real but contested ground, not a clean win.
3. **Diligence/gap surfacing** (Investor Readiness, reframed for investor consumption as "here's what
   this founder's own diligence-prep tool already found") — a genuinely novel angle: not "here's a score
   an outside AI gave," but "here's what the founder's own operating tool has been telling them to fix."
   Nobody found in this phase's research does this.
4. Discovery/filtering — **not currently competitive** at 23 companies; Harmonic.ai's 6M+ company index
   makes this a losing comparison until dataset scale changes fundamentally.
5. Investment memo generation, thesis matching — **do not build**; these require both dataset scale and
   investor behavior data SIE does not have, and building them now would be designing for a network that
   doesn't exist (this phase's own Part 12 finding).

**Strongest honest investor thesis today:** *not* "we have more startups than Crunchbase" (false) but
*"the startups on SIE are the only ones anywhere with a continuously-maintained, structured, evidence-
graded operating history, because their founders are using SIE to run the company, not just to raise
money."* This is a real, defensible, currently-small-but-true claim.

---

## Part 12 — The Network Flywheel: Arrow-by-Arrow Stress Test

| Arrow | Status |
|---|---|
| Founder uses SIE → creates structured startup intelligence | **EXISTS** |
| → company profile improves | **PARTIALLY EXISTS** (SPS improves with re-analysis; no persistent "profile" artifact separate from raw analyses) |
| → investor discovery improves | **DOES NOT EXIST** (23-company dataset, no investor-facing search relevance tuning) |
| → investors use SIE | **DOES NOT EXIST** (no investor identity, 3 lifetime watchlist rows) |
| → investor activity increases founder value | **DOES NOT EXIST** (founders cannot see investor activity at all, by design) |
| → founders update more often | **DOES NOT EXIST** (nothing today incentivizes updates via investor feedback, since none is visible) |
| → longitudinal intelligence improves | **PARTIALLY EXISTS** (re-analysis happens — 86 analyses / 23 startups — but not demonstrably *because* of investor activity) |
| → investor value improves | **DOES NOT EXIST** (circular on the above) |
| → more investors join | **DOES NOT EXIST** |
| → founder discovery value increases | **DOES NOT EXIST** |

**Verdict: this is not a network effect today. It is, at best, two separate one-sided tools (a founder
operating system and a personal watchlist) that happen to share a database.** Calling this a flywheel
in its current state would be fooling ourselves — exactly the failure mode Part 12 warns against. The
honest, buildable near-term goal is closing the *first two* arrows (profile improves → discovery
improves), which are tractable with graduation (Part 6) and better profile richness, without needing to
solve investor identity or network liquidity yet.

---

## Part 13 — Business Model Architecture

Not inventing pricing (no evidence exists for what the market will pay); determining what belongs where.

**Should never be paywalled:** creating a venture, basic VPS, Capture, core Learn content, the
Fundraising Simulator's basic math, Analyze itself (it is the top-of-funnel and the thing every other
system depends on having real data to work with).

**What creates real paid value once built:** Weekly Review depth/history retention length, Investor
Readiness detail (gaps + checklist + investor-question prep), the graduation flow's richer handoff,
advanced What-If/multi-scenario comparison, longer venture/startup history retention.

**What requires network density first (do not price until it exists):** any Investor Visibility tier,
any Benchmarking tier, any Investor-side "Discovery" tier — pricing these today would be charging for a
capability this audit found does not yet function.

**Organization tier (accelerator/university/incubator):** the most plausible *near-term* revenue path
that does NOT depend on investor-network density — a cohort of founders using the existing venture-track
operating loop, sold to the accelerator, is buildable entirely on top of what already exists (multi-
founder aggregate reporting is the only new piece, and it is a reporting view over existing data, not a
new capability).

---

## Part 14 — Cancellation Test

**IDEA-STAGE:** loses the entire structured model, VPS, Capture history, and Learn contextualization —
**high loss**, this stage is well-served.

**VALIDATING:** loses What-If, Weekly Review cadence, and the deterministic next-step guidance — **high
loss**, well-served.

**BUILDING:** loses Actions/Capture/History plus, if graduated, SPS and its trend — **high loss**,
well-served, assuming graduation (Part 6) exists; without it, a Building-stage founder who never
graduates loses relatively little once they've internalized their model (**this is a real, current
retention hole** — see below).

**EARLY TRACTION:** loses Fundraising Readiness gaps and the action-plan wiring — **moderate-high loss**
on the real-startup track; **weak** on the venture track, since nothing currently tells a traction-stage
modeled venture "you should be looking at Readiness/graduation" (a missed prompt, not a missing
capability).

**INVESTOR READY:** loses the Readiness status/checklist and its Action wiring — **moderate loss** today;
this is where retention starts thinning, because nothing yet gives an Investor-Ready founder a reason to
check in *daily* rather than *once, to confirm the status*.

**FUNDRAISING:** loses the Fundraising Simulator — **high loss** while actively raising, but this is
inherently episodic (Part 8's own finding), so the loss is real but time-boxed.

**POST-RAISE / GROWING:** loses… very little today. **This is the biggest retention hole in the whole
product.** There is no benchmarking, no investor-update generation, no board-reporting artifact, no data-
room maintenance — every retention pillar ranked #1-3 in Part 8 is venture-track-only machinery a
post-raise company has already outgrown, and the startup-track equivalent (Part 7's Weekly-Review gap)
doesn't exist yet.

**Biggest retention hole, stated plainly:** the product currently retains an idea-stage founder better
than it retains a funded one — backwards from where the highest willingness-to-pay founder segment sits.

---

## Part 15 — Competitive Research

*(Search dates: this audit, current as of the live web in September 2026; sources cited inline.)*

- **[Visible.vc](https://visible.vc/)** — 7,000+ founders, 950+ VC funds. Investor updates, portfolio
  monitoring, AI-generated update narratives from real metrics. **Closest competitor to SIE's own
  unbuilt "Investor Updates" retention pillar (Part 8, #6).** Visible does this well today; SIE does not
  do it at all.
- **[Harmonic.ai](https://harmonic.ai/)** — 6M+ companies indexed from public signals (hiring, traffic,
  patents), used by a16z, Floodgate, Accel. **Closest competitor to the investor-discovery half of SIE's
  thesis**, and structurally incomparable at SIE's current 23-company scale — this is the clearest
  incumbent-advantage finding in this research: public-signal-based discovery at scale is a genuinely
  hard, capital-intensive problem SIE should not attempt to compete on directly.
- **[Pulley](https://pulley.com/) / [Carta](https://carta.com/)** — cap table and SAFE modeling, the
  default stack pre-incorporation through Series B (Pulley) and post-institutional-round (Carta).
  Adjacent, not competitive; SIE's Fundraising Simulator explicitly models the pre-instrument scenario
  these tools manage after the fact.
- **[Aleph](https://www.getaleph.com/)** — SaaS/AI benchmarking across 342+ peer companies. **Direct
  evidence for why SIE's own Benchmarking pillar (Part 8, #7) is correctly ranked low today** — credible
  benchmarking needs hundreds of peers; SIE has 23 companies total.
- **[Harmonic Scout / UnicornScreener.vc / Dealroom](https://harmonic.ai/blog/pitchbook-competitors-and-alternatives-a-guide-for-2026)**
  — AI due-diligence agents evaluating companies investors already sourced elsewhere. SIE's calibrated,
  reproducible SPS methodology (the subject of this codebase's own extensive Phase 29A determinism work)
  is a genuine differentiator in rigor, but these tools have investor distribution SIE does not.
- **["Founder operating system"](https://www.thevccorner.com/p/founder-operating-system-startup-resources)
  category** — currently fragmented: Notion template bundles, YC Startup School content, and point tools
  (cap table, CRM, benchmarking) rather than one coherent structured product. **No single incumbent
  currently owns the exact idea→investor-ready→fundraising continuum SIE's thesis describes** — this is
  the strongest "where is SIE genuinely differentiated" finding.

**Answers:**
1. **Closest to the end-state vision:** no single product; Visible.vc (founder↔investor communication)
   and Harmonic.ai (investor-side discovery) together cover more of the *investor* half than any one
   competitor, while nobody covers the *founder-operating* half as coherently as SIE already does.
2. **What they do better:** Visible has real investor-update distribution and 950+ funds already
   trusting it; Harmonic has discovery scale SIE cannot approach without years of dataset growth.
3. **What they don't do:** neither connects idea-stage modeling through to fundraising scenario math
   through to investor-facing trajectory in one coherent, evidence-graded system.
4. **Where SIE is genuinely differentiated:** the founder-side operating loop plus its calibrated,
   reproducible scoring methodology — real, built, tested.
5. **Where we'd be fooling ourselves:** claiming investor discovery or benchmarking value at current
   scale, or assuming network effects exist because two user types can both sign in.
6. **Obvious incumbent advantage that makes part of this strategy unattractive:** Harmonic.ai's
   public-signal-based discovery scale is a real, capital-intensive moat SIE should not try to out-build
   directly — SIE's investor-side wedge should be trajectory/depth on companies whose founders already
   chose SIE, not breadth of the whole market.

---

## Part 16 — Product Architecture (End-State Map)

```
                                   SIE
                                    |
                --------------------------------------------
                |                                            |
             FOUNDERS                                     INVESTORS
                |                                            |
        Build Venture (VPS)                          [Identity: NOT YET BUILT]
                |                                            |
        Validate (Capture/Evidence)                   Discover (Search/Rankings —
                |                                       real but small: 23 startups)
        Build (Actions/History/                             |
          Weekly Review)                               Watch (Investor Workspace —
                |                                       real, currently near-unused:
        [GRADUATION — founder-initiated,                 3 rows)
         explicit, non-VPS-gated]                            |
                |                                       Compare / Evaluate (SPS,
      Real Startup (SPS)                                real, calibrated)
                |                                            |
        Investor Readiness                                   |
        (reuses Fundraising Readiness,              Trajectory Intelligence
         reframed as status not score)               (pillar deltas — real,
                |                                     genuinely differentiated)
        Startup Profile / Weekly                             |
        Review-equivalent [GAP TO CLOSE]                     |
                |                                             |
        Ongoing Growth ---------- Startup Intelligence -------
                |                  (shared canonical read,
        Capture / History /        never a shared write path)
        Intelligence (venture-
        track only today;
        needs startup-track
        equivalent)
```

**Canonical entities and boundaries** (no backend redesign proposed — this restates existing boundaries
plus the one new field Part 6 recommends):

- `modeled_ventures` — founder hypothesis space. VPS-scored. Never becomes a `startups` row by mutation;
  at most gains a `graduated_to_startup_id` pointer.
- `startups`/`analyses` — evidence-graded canonical record. SPS-scored. The only entity Investor
  Readiness, Rankings, Search, Compare, and Investor Workspace read from.
- `founder_actions`/`founder_updates`/`startup_milestones` — real-startup operating primitives. Should
  gain a Weekly-Review-equivalent digest (new, small, reusing existing history data — not a new
  scoring system).
- `saved_startups` — the one relationship table serving both "my saved list" and "Investor Workspace";
  should remain one table (no need to fork it by role) until/unless a real investor-identity system is
  designed, which this phase explicitly does not recommend building yet.

---

## Part 17 — Roadmap

**NOW** (closes real, measured gaps; no new identity/network infrastructure required):
- Venture → Startup graduation (Part 6) — closes the single biggest architectural gap this audit found.
- Reframe Fundraising Readiness's presentation as "Investor Ready" status (band-first, score internal,
  Part 4/7) — a presentation and labeling change over an already-correct engine.
- Weekly-Review-equivalent digest for the real-startup track (Part 7/8/14) — closes the "post-raise
  retention hole," the single sharpest finding in Part 14.

**NEXT** (builds on NOW, still no new identity system required):
- Investor Updates generation from existing history data (closest validated competitor: Visible.vc) —
  turns already-collected progress data into founder-facing, investor-sendable output.
- Opt-in discoverability flag on graduated startups + aggregate (never identified) watcher counts (Part
  9) — the smallest legitimate step toward the discovery loop, deliberately short of any investor-
  identity claim.
- Organization/cohort reporting tier (Part 13) — a revenue path that requires zero network effects.

**LATER** (requires either dataset scale or an identity system this phase found does not exist):
- Real investor identity/verification system.
- Benchmarking (blocked until dataset materially exceeds today's 23 startups — Aleph's 342-peer
  standard is the credibility bar).
- Data room / diligence-readiness artifact generation.

**DO NOT BUILD YET:**
- A fourth numeric score of any kind.
- Investor discovery marketed as a capability (dataset and identity system both too immature).
- Direct investor-founder contact/messaging (no verification system to prevent spam/impersonation).
- Investment memo generation or thesis-matching (requires both scale and investor behavioral data SIE
  does not have).
- A second Fundraising-Readiness-style engine for the venture track — extend graduation instead of
  building a parallel system.

---

## Part 18 — The One Next Implementation

**Recommendation: Venture → Startup Graduation (Part 6).**

**Why this beats every other candidate right now:**

1. **It is the only recommendation that fixes something broken today, not something merely missing.**
   The flywheel audit (Part 10) found the entire founder data flywheel is real and connected on both
   sides of one specific seam — and completely severed at that seam. Every other candidate (Investor
   Readiness V1, benchmarking, discovery) either already exists in usable form (Fundraising Readiness) or
   is correctly blocked by a prerequisite this phase found is missing (identity, dataset scale).
2. **It requires no new scoring, no new AI system, and no new identity infrastructure** — exactly the
   guardrails this phase itself was run under, satisfied by construction rather than by restraint.
3. **It is what makes Investor Readiness reachable by the *other* half of SIE's own user base.**
   Presentation-reframing Fundraising Readiness (the "NOW" item this phase also recommends) is nearly
   free engineering effort, but has zero founder impact until modeled ventures have a path to become the
   real startups that engine already serves.
4. **It directly targets the sharpest, most concrete finding in this entire audit** (Part 14): SIE
   currently retains idea-stage founders better than funded ones. Graduation is the mechanism by which a
   Building-stage founder's accumulated venture history becomes visible to, and connects with, the
   systems (SPS, Fundraising Readiness, eventual Investor Workspace visibility) that matter most exactly
   when their willingness to pay is highest.
5. **It is low-risk by the codebase's own established discipline** — the recommended design (Part 6)
   adds one nullable column and one founder-initiated flow; it does not touch VPS, SPS, or any existing
   firewall this multi-phase engagement has spent significant effort building and protecting.

---

## Summary of What This Phase Did Not Do

No code, database schema, VPS, SPS, or scoring changes were made. No new score, AI agent, or database
architecture was created. This document is a strategic and architectural specification only.
