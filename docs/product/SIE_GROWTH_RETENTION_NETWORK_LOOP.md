# SIE Growth, Retention & Network Loop — Phase 22 Audit

Status: **strategy/specification only.** No code, database, or scoring changes
were made to produce this document. Every claim below is grounded in the
repository as it exists today (backend `app/`, frontend `dashboard/`) —
where a claim depends on the code's own stated intent rather than something
independently re-derived, the source file is named so it can be re-checked.

---

## 1. Executive thesis

SIE has built two genuinely strong pillars — a rigorous, versioned scoring
**methodology** (SIE/SPS on the evidence-graded side, VPS on the modeled
side) and a growing set of **decision-support tools** on top of it (Simulate,
Fundraising Simulator, Learn, Playbooks) — sitting on top of a **founder
progress loop that has almost no reason to pull a founder back on its own**.
Every return trip today is founder-initiated: nothing in the product emails,
notifies, or otherwise reaches out, and the two places a founder can record
"something happened" (`venture_missions` learning capture on the modeled
side, `founder_update` on the real-startup side) are either gated behind
completing a pre-existing task or buried as an optional, undiscovered
feature. The venture/startup **evidence trail already accumulates** in a
form rich enough to build a genuine weekly review almost entirely from data
that exists today — that is the single most under-exploited asset in the
repository.

The thesis for this phase: **do not build new AI, new scores, or network
features yet.** The retention loop has to be proven with the cheapest
possible version of itself, built almost entirely out of existing data and
existing UI patterns, before any of Parts 9–13's network/sharing/investor
ambitions can mean anything — those all depend on founders already having a
reason to come back repeatedly, which is not yet true.

---

## 2. Current founder-loop map

SIE is architecturally **two parallel tracks**, not one, and this
fragmentation is itself a major finding of this audit.

### Track A — Idea Lab / modeled venture (`dashboard/app/idea-lab/`)

No claim/verification gate; open to any signed-in user. A venture is a
`VentureAssumptions` object scored deterministically into a **VPS** (Venture
Potential Score, `app/ai/vps_scoring.py`).

| Capability | Route/component | Persists | Reason to return |
|---|---|---|---|
| Build/model | `VentureWorkspace.tsx`, `AssumptionFields.tsx` | `VentureAssumptions` | Only when the founder decides to edit |
| Understand | `VPSResultPanel`, `ConceptDisclosure` | — | Passive, read-only |
| Decide | `NextMoves`, `resolveIdeaLabNextStep` (`lib/journey/`) | — | One deterministic "what's next" surfaced every visit |
| Act | `MissionsSection` (`venture_missions` table) | mission row (todo-like: active/completed/dismissed) | Yes — an open mission is a reason to come back |
| Record | learning capture, **only at mission completion** (`venture_missions.learning_summary`) | verbatim founder text | No freestanding capture exists |
| Update | "Edit the full model" accordion, manual | `VentureAssumptions` | Founder-initiated only |
| Progress | `VentureProgress` + `VentureHistoryResponse` (`app/models/idea_lab.py`) | derived from persisted events | Read-only digest, no push |
| Simulate | `WhatIfPanel` / `ScenarioComparison` (Simulate V1) | nothing (preview only, explicit Apply) | Exploratory, not sticky |
| Fundraise | `FundraisingSimulator` (Phase 21A/21B) | **nothing at all** — fully ephemeral by design | Exploratory, not sticky |
| Learn | `ConceptDisclosure`, Playbooks | — | Passive |

### Track B — Founder Workspace / real startup (`dashboard/app/founder/`)

Gated behind a verified `startup_membership` row (`FounderHome.tsx`:
"never invents a membership: zero rows here always means zero rows in the
backend response"). A startup's canonical intelligence comes from the full
evidence-based analysis pipeline (`app/workflows/due_diligence_workflow.py`)
into an **SPS** (Startup [Power/Potential] Score) with per-pillar
Public/Inferred/Private evidence tagging.

| Capability | Route/component | Persists | Reason to return |
|---|---|---|---|
| Understand | SPS Ring + trend, `SPSHistory`, `IntelligencePillars`, public `/startup/[name]` | — | Passive |
| Decide | `ActionPlan` (`founder_action`: todo/in_progress/completed/dismissed; sources `sie_recommendation`/`founder_created`/`fundraising_gap`) | shared per-startup row | Yes, and shared across cofounders |
| Record (structured, freestanding) | `RecentUpdates` (`founder_update`: title/type/optional pillar/optional metric/description, explicitly "**never changes your SPS**") | founder_update row | Only if the founder discovers and opts into it — no prompt, no forcing function |
| Record (workflow) | `Milestones` (`startup_milestone`: planned/in_progress/achieved/cancelled) | shared per-startup row | Same as above |
| Update score | **"Re-analyze"** — reruns the entire AI evidence pipeline against fresh pasted/uploaded evidence | new canonical analysis + `sps_history` point | Heavyweight, deliberate, infrequent by construction |
| Fundraising readiness | `FundraisingReadinessCard` (Phase 8: deterministic defensibility score from existing SPS confidence/coverage) | — | Passive |
| Progress | **no unified timeline exists.** `RecentUpdates`'s own docstring states it is "the private foundation for a later unified Startup Timeline… not that timeline itself." | — | Nothing to review yet |

### The exact loop today, founder-created-venture edition

1. Founder creates a venture → VPS computed instantly (deterministic, free).
2. `NextMoves`/`IdeaLabNextStep` surfaces one concrete milestone.
3. Founder clicks "Start this action" → a `venture_missions` row is created.
4. Founder does the real-world work (customer interviews, a sale, etc.) — **entirely outside SIE.**
5. Founder must **remember** to come back and mark the mission complete.
6. Completing a mission **requires** a learning_summary — the one place capture is forced, and it works well because it's forced.
7. Optionally, the founder walks through "Update my model," VPS recalculates, `VentureHistory` logs `model_updated`.
8. `VentureProgress` shows the delta — but only if the founder navigates there.
9. Days later: **nothing brings the founder back.** No email, no notification, no cron job exists anywhere in the codebase (verified: no SMTP/SendGrid/cron/Celery/APScheduler reference anywhere in `app/`).

### Retention weaknesses, named plainly

- **Zero push mechanism anywhere in the product.** Every single return visit today is 100% founder-initiated. This is the single largest structural gap identified in this audit.
- Capture is **forced-but-narrow** on the venture track (only at mission completion — a founder can't casually log "a customer just churned" without an open mission to attach it to) and **optional-but-broad** on the startup track (`RecentUpdates` accepts anything, but nothing prompts its use and it's positioned near the bottom of the page).
- Recording an update or a milestone **never** feeds back into the score on either track (correctly, by design — see Section 6) — but there is also no visible, immediate "here's what this might mean" response, so the capture act feels like writing into a void.
- Seeing a real SPS move requires the full, heavyweight Re-analyze pipeline. There is no lightweight "did today's inputs move the needle" loop on the startup track the way the venture track has (instant deterministic VPS).
- The two tracks do not share a schema, a capture mechanism, or a progress-history concept. A founder who "graduates" from Idea Lab to a real analyzed startup via "Analyze My Startup" carries over **only their free-text description** (`lib/ventureToStartupHandoff.ts`, verified: "a modeled venture's assumptions… are never transferred here, and never will be by this mechanism"). Every mission, learning entry, and history event from the venture track is left behind.

---

## 3. Five recurring founder jobs — assessment

**A. DECIDE — "What should I work on next?" → STRONG (venture track) / PARTIAL (startup track)**
Venture track: `resolveIdeaLabNextStep` + `NextMoves` is a genuinely good, deterministic, always-current "what next" surfaced on every visit, with an explicit reason ("why") attached. Startup track: `ActionPlan` has SIE-recommended actions plus a separate fundraising-gap source, but there is no single headline "do this next" the way the venture track has — three action sources coexist without a stated priority order.

**B. CAPTURE — "Something happened." → PARTIAL**
The shape is right (`RecentUpdates`'s title/type/optional-metric/optional-description form is close to ideal — fast by default, 15–30 seconds per the component's own comment) but it exists on only one track, isn't prompted, and there is no free-text→structured-interpretation assist (the directive's own worked example — "talked to six restaurant owners…" → structured signals — has no analogue anywhere in the repo today).

**C. UNDERSTAND — "What does this mean for my venture?" → WEAK**
This is the most important gap. `founder_update.metric_name/metric_value/metric_unit` are free-text fields with **no connection to any scoring input** — recording "MRR: $25,000" produces a display row and nothing else. The only way a founder-reported fact becomes a scored fact is to manually retype/re-paste it into the Re-analyze flow's evidence text, which does not read `founder_update` rows at all. The record-something / understand-what-it-means loop is **structurally disconnected** today.

**D. DECIDE AGAIN — "Given what I learned, what should I do now?" → WEAK, downstream of C**
Because C doesn't close the loop, D can't either: nothing today re-surfaces "you just told us X, here's an updated next step" in direct response to a capture event.

**E. REVIEW — "Am I actually making progress?" → STRONG (venture) / MISSING (startup)**
`VentureHistoryResponse` already carries almost everything a review needs: typed events (`venture_created`/`action_added`/`learning_recorded`/`action_completed`/`model_updated`), before/after VPS, per-category deltas, and a compact summary (current VPS, actions completed, model-update count, strongest improvement). This is genuinely close to review-ready. The startup track has no equivalent — `SPSHistory` is a chart of score points across analyses, not a "what happened between then and now" narrative, and the unified timeline is explicitly not built yet.

---

## 4. Activation

**Rejected candidates** (events, not value, per the directive's own
instruction): account created, venture created, page viewed, VPS
calculated — all of these already happen today with no guarantee the
founder understood or believed anything.

**Strongest candidate:** *the founder sees a specific, credible weakness or
strength on their own venture/startup, and receives one concrete next
action they believe is worth doing* — i.e., reaching a populated
`NextStepCard` (the exact shared pattern both `IdeaLabNextStep` and
`FounderStartupWorkspaceView`'s `NotYetAnalyzed` state already use) with a
real "why," not a placeholder.

- **Activation event:** first render of a populated Next-Step recommendation tied to the founder's own real inputs (not a generic empty-state prompt).
- **Supporting events:** at least one modeled/scored pillar with a non-null score; the founder reads or expands at least one "why" explanation (`ConceptDisclosure`/pillar highlight).
- **Time-to-value target:** venture track can hit this in well under a minute (VPS is deterministic, instant). Startup track is materially slower — the analysis pipeline makes real external calls (Tavily research, OpenAI scoring across six pillars) and realistically takes tens of seconds to low minutes.
- **Major activation friction, startup track specifically:** the Founder *Workspace* (actions, updates, milestones — the actually retentive part) is gated behind claim **verification**, which is a separate, asynchronous step from the public analysis itself. This creates **two distinct activation moments** — "I saw my score" (public profile, fast) and "I can act on it" (verified workspace, slower, possibly never reached) — and only the second one is where any of Section 3's recurring jobs actually live.
- **What could be removed/shortened:** nothing about the scoring pipeline should be shortcut (accuracy is the product), but the gap between "I got a score" and "I have a workspace to act in" is the highest-leverage friction to look at — not by weakening verification, but by making sure the value proposition of *finishing* verification is obvious before a founder abandons the flow.

---

## 5. Weekly retention loop

The directive's proposed shape (Monday: what matters now → midweek: capture
→ midweek: decision support → end of week: what changed) maps almost
exactly onto primitives that **already exist**, just not assembled into a
cadence:

| Day | Job | Existing primitive |
|---|---|---|
| Start of week | What matters now | `NextMoves`/`IdeaLabNextStep` (venture), `ActionPlan` (startup) — both already exist, already deterministic |
| Midweek | Capture | `RecentUpdates` schema (startup) / mission-completion learning (venture) — exists, but not prompted or unified |
| Midweek | Decide | `WhatIfPanel`, `FundraisingSimulator`, Learn/Playbooks — all exist |
| End of week | What changed | `VentureHistory`'s compact summary + `categoryChangeExplain.ts`'s deterministic "why it changed" text — exists on the venture track only |

**Verdict: this cadence is appropriate and should not be replaced with
something invented from scratch** — the honest gap is not "design a new
loop," it's "assemble and surface the loop that's already implicit in the
data, and make it available on both tracks." No streaks, XP, or arbitrary
notifications are needed to make this loop legitimate; each step already
solves a real, named founder job (Section 3).

2–4 sessions/week is realistic **only if** capture (midweek) stops being
optional-and-buried and the end-of-week review becomes a real artifact
instead of something a founder has to know to seek out.

---

## 6. Evidence-capture assessment

`founder_update` (`RecentUpdates.tsx` + `app/models/founder_update.py`) is
the closest thing SIE has to the directive's "universal lightweight capture
mechanism," and it is already well-designed for its scope: fast (title +
type + date required, everything else optional and tucked behind a
disclosure), explicitly and honestly labeled ("Founder reported… never
changes your SPS"). What's missing is not the mechanism, it's **reach**
(startup track only), **prominence** (bottom of a long page, opt-in), and
**interpretation** (no structured extraction from free text).

The directive's explicit guardrail — *founder evidence and canonical
venture assumptions must remain distinct; AI extraction should propose,
never auto-mutate* — is already the codebase's own established discipline,
independently arrived at in multiple places:

- `venture_missions.py`'s own docstring: "nothing here is inferred or fabricated… cannot carry a validation number into VentureAssumptions."
- `founder_update`'s UI copy: "This is recorded as founder-reported progress, not independently verified evidence. It never changes your SPS."
- Simulate V1's own preview → explicit-Apply pattern (`ScenarioComparison`'s `onApply`/`onDiscard`, nothing commits without a click).

**This means the infrastructure precedent for a future "AI proposes, founder
confirms" extraction flow already exists and is proven in production** (the
scenario-preview pattern). A future capture-interpretation feature should
reuse that exact shape: free-text in → a proposed structured interpretation
shown as a diff/preview → founder explicitly applies or discards, never a
silent mutation.

---

## 7. Weekly-review assessment

Separating what's honestly available today:

- **FACT** (already persisted, zero computation): `actions_completed`, `model_updates_count`, event timestamps, raw event counts — all directly in `VentureHistoryResponse` today.
- **DERIVED FACT** (already computed deterministically, zero AI): `before_vps`/`after_vps` deltas, per-category `before`/`after` in `VentureHistoryCategoryChange`, `strongest_improvement`.
- **DETERMINISTIC INTERPRETATION** (already exists as rule-based text, zero AI): `categoryChangeExplain.ts`'s "why it changed" framing, already reused across `ScenarioComparison` and `MissionsSection`.
- **AI-GENERATED INTERPRETATION** (does not exist in this shape today): a narrative "biggest unresolved question" / "recommended focus" synthesis. The closest existing analogues are `executive_coaching_summary` (AI-written, startup track) and `vps_guidance`-driven next steps (deterministic, venture track) — neither is a weekly-cadence synthesis today.

**Honest conclusion:** a first, real weekly review for the **venture
track** could be built almost entirely from FACT + DERIVED FACT +
DETERMINISTIC INTERPRETATION that already exists — no new AI call
required for a v1. The **startup track** cannot support this yet because
its unified timeline was never built (explicitly deferred per
`RecentUpdates`'s own comment) — that is real, if modest, backend work, not
a UI assembly task.

---

## 8. Compounding-value thesis

**What already compounds today:** the venture's `VentureHistory` (a growing,
faithful record), the startup's `sps_history` (score + evidence trail across
re-analyses), completed-mission/action counts, and milestones. These are
real, and they are the strongest existing argument for why SIE gets more
valuable the longer someone uses it.

**What does not yet compound, and should be named honestly:**

- **Fundraising scenarios are deliberately non-persisted** (Phase 21A/21B design decision, correct for that phase's scope) — so "financing history" is not part of the growing record today, on purpose. If compounding value becomes a stated goal, this specific non-persistence decision deserves a fresh look in a later phase — not reversed casually, since ephemerality was chosen for good reasons (no premature system-of-record for real equity).
- **The venture-track and startup-track records don't merge.** "Graduating" a venture into a real analyzed startup carries over only free text; the accumulated venture history stops mattering the moment a founder's real company exists on SIE.
- There is no single **Venture Profile** object today that already spans assumptions + actions + evidence + learning + model changes + metrics + milestones + simulations + financing + history in one place — the pieces exist, scattered across two tracks and several tables, not unified.

The switching cost SIE could legitimately earn is real (an accumulated,
methodology-consistent evidence trail is genuinely hard to reconstruct
elsewhere) — but it requires closing the venture/startup fragmentation
before it can be honestly claimed.

---

## 9. Shareability thesis

| Artifact | Exists today? | Why share | Who | What must stay private | What makes it non-spammy |
|---|---|---|---|---|---|
| Public Startup Profile (`/startup/[name]`) | **Yes, already public and shareable** | Social proof for hiring/fundraising/customers | Anyone | `founder_update`/milestones (already never shown here) | Evidence-graded, not self-scored |
| Venture Card | **Built, explicitly unwired** (`VentureCard.tsx`: "NOT wired to any sharing, export, or public route") | Lightweight "here's what I'm building" | Peers, potential cofounders | Raw assumptions detail | Card already carries a mandatory MODELED/ASSUMPTION-BASED disclaimer |
| Founder Progress summary | Does not exist as a standalone artifact | Accountability, momentum signal | Mentors, cofounders, self | Financials, private evidence | Would need to be fact-forward, not score-forward |
| Fundraising scenario | Exists, but **must stay private** — modeling a specific SAFE negotiation is sensitive | N/A — do not build sharing for this | N/A | Everything | N/A |
| Milestone card | Does not exist as a distinct object | Momentum | Public/social | — | Needs to be a real, earned milestone, not a manufactured one |

The public Startup Profile is the one artifact already proven to work as a
shareable output; the Venture Card is the cheapest next candidate (the
component already exists, just needs an export/share surface and a privacy
decision this phase deliberately does not make).

---

## 10. Founder-identity thesis

Signals that already exist in some persisted form, scattered per-entity
rather than aggregated: ventures created, actions/missions completed (both
tracks, different tables), milestones achieved, self-reported customer
interview counts (`VentureAssumptions.validation.customer_interviews` —
modeled, not independently verified), startups analyzed/claimed
(`startup_membership`).

Nothing today aggregates these **across ventures and across time** into a
single founder-level object, and nothing should turn this into a score —
the directive is explicit, and the codebase's own existing discipline
(Section 6: self-reported vs. verified is never blurred; "Unknown" is never
treated as zero or as failure — see `content/concepts/data.ts`'s own
anti-fabrication tests) is exactly the design posture a future
demonstrated-execution profile would need: distinguish **self-reported**
signals from **SIE-observed** signals, always, and never collapse either
into a single number.

This is directly on-mission (people without traditional pedigree
demonstrating they can build) but is a genuinely new cross-entity data
layer — nothing to reuse structurally beyond the anti-fabrication
discipline itself.

---

## 11. Collaboration thesis

**Already exists and is underused:** `startup_membership` already makes
`founder_action`, `startup_milestone`, and `founder_update` **shared, not
per-user** — "every verified member sees and can act on the exact same
milestone list" (`Milestones.tsx`'s own comment). This is a real, working
lightweight cofounder-collaboration primitive that isn't marketed or built
on as such today.

**Does not exist:** any read-only or limited-role tier (mentor, advisor,
professor, accelerator operator). Today it's binary — verified member or
no access at all (`RequireStartupMember`, confirmed via
`FounderStartupWorkspaceView`'s 404-style "doesn't exist, or you don't have
access" framing that deliberately never distinguishes the two cases).
Idea Lab ventures have **no membership concept at all** — they are
single-owner only.

A future mentor/advisor visibility tier is plausible and on-thesis (SIE
becoming the shared record in a founder/mentor conversation), but requires
a genuinely new permission model — correctly out of scope this phase.

---

## 12. Investor/network thesis

The **Investor Workspace already does a version of this today** — a
watchlist of saved startups with pillar-score deltas over time and a
"needs attention" flag, explicitly with **no new score**
(`app/ai/investor_workspace.py`'s own stated design). This is close to
exactly the kind of differentiated-not-duplicative signal Part 12 asks
about: trajectory over time under a consistent methodology, not a static
profile.

What's missing before this becomes a real network asset:

- It's **watch-based** (investor opts in to follow a startup), not activity-triggered — a watching investor's presence today produces no visible signal back to the founder, so the loop-back arrow in Section 13's flywheel is genuinely unbuilt.
- It only exists for the **startup track** — Idea Lab ventures have (correctly) no investor-facing surface, since they're pre-evidence.
- Differentiation from Crunchbase/PitchBook/Carta is real **only if** founders are actually returning and generating fresh evidence — a trajectory built on stale, rarely-updated analyses is not differentiated from a static database. This makes founder retention (Sections 2–5) the true precondition for any investor-network value, not a parallel track that can be built independently.

---

## 13. Flywheel stress test

> Founder gets value → founder repeatedly uses SIE → venture record becomes
> richer → SIE becomes harder to replace → progress becomes shareable →
> other founders discover SIE → ecosystem participation grows →
> investor/mentor/accelerator value emerges → their participation creates
> more founder value → more founders join

Stress-tested link by link:

1. **Founder gets value** — real, but only partially (Section 3: C/D are weak).
2. **Founder repeatedly uses SIE** — **not yet true.** Section 2's core finding: zero push mechanism, capture is either forced-and-narrow or optional-and-buried. This is the first structurally broken link.
3. **Venture record becomes richer** — true on the venture track, absent on the startup track (no unified timeline), and doesn't survive the venture→startup transition (Section 8).
4. **SIE becomes harder to replace** — only as strong as link 3, so currently weak/partial.
5. **Progress becomes shareable** — mostly unbuilt; only the public Startup Profile is real (Section 9).
6. **Other founders discover SIE** — no mechanism exists for this at all beyond organic/public-profile discovery; entirely unbuilt.
7. **Ecosystem participation grows** — depends on 5 and 6, both weak/unbuilt.
8. **Investor/mentor/accelerator value emerges** — a real seed exists (Investor Workspace), but it's watch-based and startup-track-only (Section 12).
9. **Their participation creates more founder value** — **no loop-back mechanism exists at all** — a watching investor is invisible to the founder today.
10. **More founders join** — depends on everything above.

**Honest verdict: only link 1 is meaningfully built today, and even it is
partial. Links 2, 5, 6, 9, and 10 are effectively unbuilt.** The flywheel is
not a small set of easy wires away from turning — it depends entirely on
proving link 2 first, which is exactly why this phase's roadmap (Section 18)
concentrates entirely on retention and none on network features.

---

## 14. Product metrics / north-star definition

**Meaningful session** — a session containing at least one of: a
mission/action created or completed, a learning/update recorded, a model
update, a milestone status change, a re-analysis run, or genuine engagement
with a decision-support tool with an outcome (a saved/applied scenario, not
merely opening a panel). Explicitly **not** meaningful: sign-in alone, a
VPS/SPS render from a cached read, a page view with no interaction.

Proposed scoreboard (definitions, not yet instrumented — see Section 18):

- **Activation Rate** — % of new ventures/claimed startups reaching a populated Next-Step recommendation (Section 4) within their first session.
- **First-Week Meaningful Sessions** — count of meaningful sessions (as defined above) in the 7 days after activation.
- **Action Start Rate** — % of ventures/startups with ≥1 mission/action created.
- **Action Completion Rate** — completed / started.
- **Evidence/Learning Capture Rate** — % of active weeks with ≥1 `learning_recorded` or `founder_update` event.
- **Model Update Rate** — `model_updated` events / active ventures / week.
- **W1 / W4 Retention** — % of activated founders with ≥1 meaningful session in week 1 / week 4 after activation.
- **Simulation Usage** — Simulate/Fundraising sessions with a concrete input change or applied/compared scenario. **Currently unmeasurable**: `FundraisingSimulator` persists nothing at all by design (Phase 21A/21B), so this metric has zero data source today without new, lightweight, content-free event logging (log that a simulation ran, never log its financial content).
- **Weekly Review Usage** — does not exist yet; would be defined once Section 7's review artifact exists.
- **Share Rate** — does not exist yet; would be defined once Section 9's artifacts exist.

**North star: Weekly Active Building Ventures.** A venture (or claimed
startup) counts for a given week **only if** its founder performed ≥1 of:
mission/action created, mission/action completed, learning/update recorded,
model updated, milestone status changed, re-analysis run. It explicitly
**does not** count: a page view, a passive VPS/SPS display, a sign-in with
no action, or (deliberately, for now) an unsaved Simulate/Fundraising
exploration — those are valuable but not yet "building" in a way the
product can currently observe as committed activity. This keeps the
north star honest against the biggest risk named throughout this audit:
mistaking browsing for building.

---

## 15. Business-model implications

| Payer | Value received today | WTP mechanism | Conflicts with founder accessibility? | Free-usage strategic value |
|---|---|---|---|---|
| Aspiring founder | Idea Lab modeling, Learn | Low — top-of-funnel | High if charged now | High — primary distribution surface |
| Active founder | VPS/SPS, actions, Simulate | Moderate, **only once weekly utility is real** | Charging before retention is proven taxes the exact usage needed to prove the thesis | High — this is the core loop |
| Funded startup | Deeper actions, fundraising tools | Higher — cofounder seats, investor-update generation | Low, if scoped to genuinely new value | Moderate |
| Accelerator | Cohort licensing, mentor visibility | Real, but mentor tier (Section 11) is unbuilt | Low | High — distribution channel |
| University/MBA | Course integration | Similar to accelerator | Low | High — distribution channel |
| VC/investor | Investor Workspace trajectory intelligence | **Already has a real product hook today** | **None** — a separate, orthogonal audience whose payment doesn't gate founder usage | N/A (they are the payer, not the free tier) |

**Most plausible initial payer: the investor side**, via the existing
Investor Workspace, precisely because it's a two-sided-marketplace structure
where the paying side is separate from the side whose free usage the
product still needs to grow. This is explicitly **conditional on Section 2's
retention gap closing first** — an investor will not pay to watch founders
who show up once and never return.

---

## 16. Kill list

**Freeze (complete enough for now — do not invest further without new
evidence of demand):**
- Fundraising Simulator V1's math/engine and instrument breadth (Phase 21A) — rigorously validated; further instrument types (discount SAFEs, notes, etc.) should wait for real founder demand, not be built speculatively.
- Learn/Playbooks content depth — sufficient; more content has lower marginal value than fixing the retention loop.

**Challenge (no evidence in this audit that these move activation,
retention, compounding value, decision quality, distribution, network
effects, or monetization):**
- Compare Startups — niche, public, no connection to the core founder-building loop.
- Discovery/Rankings/Search — these serve browsing/investor use cases, not the founder loop this phase targets; the homepage already de-emphasized the equivalent "Explore Startups" surface for a thin-dataset reason that still holds (`components/home/ExplorePreview.tsx`'s own removal note).

**Do not build right now, full stop (explicitly out of scope per this
phase's own instructions and per the flywheel stress test):**
- Any gamification (streaks, XP, badges, arbitrary notifications, fake urgency).
- A founder score or company score beyond existing VPS/SPS.
- Persistent cap-table/system-of-record equity tracking.
- Notification/email infrastructure **as a goal in itself** — build the weekly-review *content* first (Section 18 P0); only add a delivery mechanism once that content is proven worth returning for. Building delivery before content risks training founders to ignore SIE's notifications the first time they're empty or generic.
- A third parallel action/evidence system. Any new capture work should target **unifying** `venture_missions` and `founder_action`/`founder_update`/`startup_milestone`, never adding a third shape.

---

## 17. Competitive/category positioning

Based on the product's actual architecture, SIE should explicitly not try
to become:

- **A generic AI chatbot.** The differentiation is a fixed, versioned, evidence-graded methodology (SIE/SPS/VPS scoring rules, Public/Inferred/Private evidence tagging) — not a free-form conversational agent. Nothing in the roadmap should trade that methodology consistency for open-ended chat.
- **A startup course/LMS.** Learn/Playbooks are deliberately minimal and contextual (`content/concepts/data.ts`'s own docstring: concepts are added only where actually surfaced by real UI, never as a curriculum); nothing should gate a founder's progress behind lessons.
- **A cap-table administration product.** Phase 21A/21B explicitly and repeatedly refused to become a system of record for real equity — Fundraising Simulator stays a decision-support simulator, on purpose.
- **A startup database (Crunchbase/PitchBook-style).** Discovery/Rankings/Compare are real but secondary; the product's center of gravity is the founder's own building process, not a browsable index of other companies.
- **Project-management software.** `ActionPlan`/Missions are methodology-linked, not a generic kanban/todo system — this should stay true even as capture and review are unified.

**The category SIE is actually building:** a **venture intelligence
operating layer** — a single, evidence-and-methodology-grounded system that
turns a founder's ongoing real-world activity into a continuously updated,
structured understanding of their venture's fundability, with lightweight
decision-support tools (Simulate, Fundraise) built directly on that same
evidence base. The defensibility is methodology consistency plus an
accumulated, founder-specific evidence trail — not a generic LLM wrapper,
and not a static document/database product.

---

## 18. Prioritized implementation roadmap

**P0 — required to prove retention**

1. **Unify and elevate evidence capture across both tracks.**
   - Problem: capture is forced-but-narrow (venture) or optional-and-buried (startup); Section 3's Job B/C is the weakest link in the whole loop.
   - Hypothesis: a prominent, always-available "what happened?" affordance, present on both tracks, increases weekly capture rate more than any other single change.
   - Expected behavior change: `learning_recorded`/`founder_update`-equivalent events per active venture/week increases.
   - Metric affected: Evidence/Learning Capture Rate (Section 14).
   - Complexity: low-moderate — reuse `RecentUpdates`'s proven schema/UX, extend the *pattern* to Idea Lab (does not require merging the underlying tables in this step).
   - Reuse: `founder_update`'s form design almost unchanged; `venture_missions.learning_summary`'s honest "founder-reported, never scores" framing.
   - Deliberately NOT building: AI-assisted extraction from free text (Section 6) — sequence structured manual capture first; free-text interpretation is a distinct, higher-risk follow-on.

2. **Build the Weekly Review artifact, venture track first.**
   - Problem: Section 7 found this is buildable almost entirely from data that already exists.
   - Hypothesis: a real "here's what changed and what's next" digest, even pull-based (no email yet), increases founders' willingness to return on a repeatable cadence.
   - Expected behavior change: increase in W1/W4 retention and in sessions where a founder reviews history rather than only edits it.
   - Metric affected: Weekly Review Usage, W1/W4 Retention.
   - Complexity: low — `VentureHistoryResponse` and `categoryChangeExplain.ts` already supply FACT/DERIVED FACT/DETERMINISTIC INTERPRETATION; no new AI call required for v1.
   - Reuse: `VentureProgress`, `VentureHistory`, `categoryChangeExplain.ts` almost entirely as-is.
   - Deliberately NOT building: the AI-generated "biggest unresolved question" narrative layer (Section 7) — ship the deterministic version first and prove it's used before adding an AI layer on top.

3. **Instrument the metrics defined in Section 14.**
   - Problem: none of the funnel/retention metrics above can currently be measured — there is no session/event logging layer at all.
   - Hypothesis: without this, no retention hypothesis in this document is falsifiable.
   - Expected behavior change: none directly — this is measurement infrastructure, not a founder-facing change.
   - Metric affected: all of Section 14.
   - Complexity: low-moderate — lightweight event logging only (event type + timestamp + venture/startup id), explicitly never logging simulation *content* (financial figures stay ephemeral per Phase 21A/21B's own design).
   - Reuse: none directly; this is new, minimal infrastructure.
   - Deliberately NOT building: a full analytics platform, session replay, or anything beyond the specific events named in Section 14.

**P1 — strongly improves compounding value/distribution**

4. **Wire the existing Venture Card into a real, private-by-default shareable artifact.**
   - Problem: the component already exists and is explicitly unwired (Section 9).
   - Hypothesis: a low-effort, low-risk shareable artifact tests whether founders want to share progress at all before investing further in Section 9's other candidates.
   - Metric affected: Share Rate (new).
   - Complexity: low — component exists; needs an export/share surface and an explicit privacy decision (deliberately deferred by the component's own comment, and still deliberately deferred here beyond "make the decision").
   - Deliberately NOT building: sharing for fundraising scenarios or founder-identity artifacts (Sections 9, 10) — both need dedicated privacy design this phase does not do.

5. **Give the startup track a real unified timeline, matching what the venture track already has.**
   - Problem: Section 7/8's core startup-track gap; without it, P0-2 can never extend to real analyzed startups.
   - Hypothesis: closing this gap is required before compounding value (Section 8) or a startup-track weekly review can be honestly claimed.
   - Metric affected: Evidence/Learning Capture Rate and Weekly Review Usage, startup track.
   - Complexity: moderate — real backend work (a `founder_update`/`founder_action`/`startup_milestone`-spanning event log), not a UI assembly task like P0-2 was.
   - Reuse: `VentureHistoryEvent`'s shape as a design template.
   - Deliberately NOT building: merging the venture-track and startup-track schemas into one table in this step — parallel-but-consistent shapes first, true unification later if warranted.

**P2 — later network expansion (do not start before P0 shows results)**

- Investor-facing trajectory intelligence beyond today's Watchlist (Section 12) — only once founder retention is proven; an investor won't pay to watch inactive founders.
- A read-only mentor/advisor/accelerator visibility tier (Section 11) — needs a genuinely new permission model.
- A cross-venture, cross-time founder-identity view (Section 10) — needs a new aggregation layer, and must resist ever becoming a score.

**DO NOT BUILD** (repeated from Section 16 for completeness): gamification
in any form; a founder/company score beyond VPS/SPS; persistent cap-table
system-of-record features; notification/email delivery infrastructure
before P0's content is proven; a third parallel action/evidence system.

---

## 19. What we build next

P0 items 1–3, in the order listed: unify/elevate evidence capture across
both tracks → build the venture-track Weekly Review from existing data →
instrument the metrics needed to know whether either of the first two
actually worked. Nothing else should start before these three are shipped
and measured.

## 20. What we do NOT build next

Anything in Section 16's kill list; any P1/P2 item before P0 shows real
retention movement; any AI-assisted free-text evidence extraction before
the manual, structured version (P0-1) is proven used; any notification/email
delivery mechanism before the Weekly Review (P0-2) has content worth
delivering; any network/investor/collaboration feature (Sections 11–13)
before founders are demonstrably returning on their own.
