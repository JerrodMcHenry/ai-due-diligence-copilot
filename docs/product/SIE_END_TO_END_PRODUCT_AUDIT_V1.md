# SIE End-to-End Product Audit V1

**Phase 36 — End-to-End Founder Journey + Product Coherence Audit**

This is an audit document, not an implementation spec. It records what the live product actually does today,
tested through a real founder journey on a fresh venture (RelayOps), cross-referenced against the codebase
where the UI alone couldn't answer a question. Every claim below is either (a) something observed live in
the browser during this phase, or (b) something confirmed by reading the actual source (marked as such). No
finding here is inferred from documentation or prior phase reports without being re-verified live or in code
this phase.

---

## 1. Governing product thesis — tested, not assumed

The hypothesis under test: *SIE is a persistent decision system for building a company* — one that helps a
founder Understand, Decide, Test, Learn, Plan, Model, Remember, and Adapt, with value that compounds the more
it's used.

**Verdict: the thesis is real and substantially delivered inside Build, and real but siloed inside Finance
and Fundraising. It is NOT yet delivered as one coherent whole**, because the systems that deliver each verb
don't share a timeline, a vocabulary, or — in one major case (My Startups vs. Build) — even an epistemology.

The single clearest piece of live evidence *for* the thesis: after recording one deliberately mixed piece of
evidence on a fresh venture, SIE's next recommended question changed from a generic "interview customers" to
a specific "why do some of RelayOps's target customers experience this problem and others don't?" — a
question a founder could only be asked *because* the contradiction was persisted and reasoned about. ChatGPT,
re-opened cold, cannot ask that question; it would need the founder to restate everything, including the
contradiction, from scratch.

The single clearest piece of live evidence *against* full coherence: the same company, once "graduated," is
managed in a workspace (My Startups) that shows a numeric Startup Power Score, pillar subscores, and
confidence weightings — the exact apparatus Build deliberately avoids. A founder does not experience one
product that grew up; they experience a handoff into a different product with a different worldview.

---

## 2. Current product map

```
                         ┌─────────────────────────────────────────────┐
                         │                 Home (/)                    │
                         │  hero: "idea → startup", 6-category grid    │
                         └───────────────┬─────────────┬───────────────┘
                                          │             │
                    ┌─────────────────────┘             └─────────────────┐
                    ▼                                                     ▼
   ┌────────────────────────────────┐                    ┌──────────────────────────────┐
   │  BUILD (/idea-lab)              │                    │  ANALYZE (/analyze)           │
   │  "My Ideas" → a Venture         │                    │  Pitch deck coach             │
   │  Overview / Finance /           │  ── graduate ──▶   │  or full Startup Profile      │
   │  Fundraising / History          │   (paying cust.    │  (SPS, six pillars, evidence, │
   │  - evidence + decision loop     │    or revenue)      │   confidence, recommendations)│
   │  - Finance: snapshots, hiring,  │                    └───────────────┬───────────────┘
   │    plans, scenarios             │                                    │
   │  - Fundraising: SAFE/priced     │                                    │ same canonical
   │    round simulator              │                                    │ Startup + Analysis
   └───────────────┬─────────────────┘                                    │ objects
                    │ venture_graduations                                 ▼
                    ▼                                     ┌──────────────────────────────┐
   ┌────────────────────────────────┐   startup_membership │  Public Startup Profile        │
   │  MY STARTUPS (/founder)         │◀──────────────────── │  (/startup/[id])               │
   │  Founder Workspace              │                      │  trust badge, SPS, Compare      │
   │  - SPS + pillars (from Analyze) │                      └──────────────────────────────┘
   │  - Fundraising Readiness (LLM)  │
   │  - Action Plan (separate from   │
   │    Build's "Your Actions")      │
   │  - Recent Updates (separate     │
   │    from Build's evidence loop)  │
   └──────────────────────────────────┘

   LEARN (/playbooks) — a standalone content library, also linked contextually
   from Build's "What to consider next" recommendations ("Learn how: ... →").
```

---

## 3. Founder journey — live walkthrough (RelayOps)

A fresh venture was created through the live product (not an existing test fixture) to exercise the full
journey. RelayOps: a B2B SaaS dispatch workspace for regional HVAC/plumbing/electrical field-service
companies, $1,500/mo per operating location, idea-stage, no product, no customers, several industry contacts
— per the phase's own suggested test case.

### 3.1 Home page (Section 4)

Tested at 100% zoom. Could not safely test a genuinely logged-out session without risking the loss of the
long-running authenticated session this audit depends on — noted honestly rather than fabricated. The home
page itself shows **zero personalization for a signed-in user** (same "Free to start. No credit card."
first-time-visitor copy regardless of auth state) — itself a finding: a returning founder with real ventures
gets the same cold-open pitch as a first-time visitor.

Within 10 seconds a first-time founder can answer "what can I do here" (three clearly-labeled entry cards:
*I have an idea* / *I'm building a startup* / *I want SIE to evaluate a company*) but **cannot** easily answer
"why isn't this just ChatGPT" — nothing on the home page mentions persistence, memory, evidence, or
decisions; the pitch is entirely "model your idea before you build it."

**Legacy-language finding (high confidence):** the hero's supporting section — *"Every idea gets modeled
across six categories"* (Market Potential, Problem & Solution, Founder Readiness, Reaching Customers,
Economic Potential, Validation) — is deliberately kept consistent with Build's own internal six-category
evidence taxonomy (confirmed in code: `VisualPayoff.tsx`'s own comment says *"VPSResultPanel screen will
recognize these exact six categories"*). The categories themselves are alive and legitimately used
(qualitatively, never as a number, in Build's `VentureUnderstandingPanel`). **The wording is the problem, not
the categories**: "modeled across six categories" reads exactly like a scoring pitch, at the moment a founder
is deciding whether SIE is a grading tool — the one thing the current product direction says it should not
lead with.

### 3.2 Navigation (Section 5)

`Build / Analyze / My Startups / Learn`. Tested each:

| Label | Expected before clicking | What you actually get | Clear? |
|---|---|---|---|
| Build | Work on a company/idea | "My Ideas" — a list of ventures, all labeled "Idea" or a stage | Mostly — see 3.3 |
| Analyze | Evaluate *a* company (any company) | Two-choice screen: pitch deck coaching or full Startup Profile | Yes |
| My Startups | Companies I operate | A second, separate workspace for graduated companies, with a *different* intelligence system than Build | No — see 3.7 |
| Learn | Supporting knowledge | A playbook library, also linked contextually from Build | Yes |

The `Build` vs `My Startups` split is the one genuine ambiguity: a first-time user has no way to know, from
the nav alone, that these are two different systems with two different views of "company intelligence," not
two views of the same thing at different maturity levels.

### 3.3 Build entry (Section 6)

Page title is **"My Ideas"** even though the nav tab is labeled **"Build"** — a small but real mismatch.
"Idea" is used as both the *object type* (a card's implicit type) and a *lifecycle stage* label ("Idea Stage")
shown on the venture's own overview — two different jobs for one word. **User feedback already on record says
"idea" was too vague**; live testing didn't reveal an obviously better single noun that fits the *object*
(the persistent Build workspace for a company you're pursuing, at any stage from idea through revenue)
without confusing it with the "Startup" that exists after graduation. See §9 vocabulary recommendation.

The empty/populated list itself carries live, direct evidence of a real bug (next section).

### 3.4 Venture creation (Section 7) — bug reproduced live

Created RelayOps through the real "Start a new idea" flow: free-text description → AI-structured review →
confirm. The AI correctly extracted "RelayOps" as the suggested venture name.

**Reproduced, live, the exact previously-reported bug**: clearing the "What's your venture called?" field
before clicking "Create Venture" left the **Create Venture button fully enabled** (not disabled), and
clicking it **silently created a venture named "Untitled venture"** — no warning, no confirmation, no
required-field indication. The resulting `/idea-lab` list already had **6 of 12 existing ventures sitting
permanently as "Untitled venture"** before this test began — direct evidence this is not a hypothetical edge
case but a recurring, live failure mode. Fixed for this walkthrough via the existing Rename feature (a
UI action, not a code change, per this phase's audit-only scope) so the walkthrough could continue. **This is
the single most concrete, unambiguous defect found in this entire audit** and belongs at P0.

Every other field in venture creation was optional, well-explained, and low-friction. Time to a created,
correctly-populated venture (once the name bug is worked around): under two minutes including one real LLM
call.

### 3.5 First landing / Overview (Section 8)

Genuinely strong. Without documentation, the Overview answered all six of the directive's questions:

- **Where am I** — breadcrumb, venture name, "Idea Stage" label with an honest caveat ("not a level you've
  unlocked — it can move forward or backward as new evidence comes in").
- **What does SIE know / not know** — "Who it's for" / "How it might make money" plainly stated; "Biggest
  unknowns" as plain tags (Market demand, Founder fit, Acquisition strategy, Real-world validation).
- **What should I do next, and why** — "What matters now" names one question ("Interview 20+ target
  customers to validate the problem is real"), explains *why* it's the priority ("answering it will shape
  everything else you test next"), and gives one concrete action.
- **What happens if I do it** — an explicit, honest line: *"Nothing has been tested yet — once you record a
  result, SIE will start building a real understanding of your venture here."* This is the compounding-value
  thesis stated directly, in plain language, to the founder.

No internal architecture leaked into this surface — no "hypothesis," "evidence type," or "confidence
interval." The word "modeled" appears a few times ("not enough modeled yet to say anything here") — mild,
tolerable, not confusing.

### 3.6 "Edit venture details" (now "Add venture context") (Section 9) — orphaned fields found, code-confirmed

Renamed since the concern was last raised; the surface is now titled **"What you believe"** with an
explicit, well-worded caveat: *"Everything below except 'What you've learned' is an assumption, not observed
evidence."* Organized into Venture Basics / Market / Problem & Solution / Founder & Team / Go-to-Market /
Economics / What you've learned / Capital. Several fields (CAC, gross margin, retention, monthly burn) have
excellent, plain-language "What's this?" explainers that teach the concept even when the field is empty.

**Decisive, code-verified finding**: traced the entire consumption chain for the **Capital** section
(`starting_capital`, `monthly_burn`) end to end:

- `starting_capital` is read by **zero** functions anywhere in the backend — not `compute_vps()`, not
  `generate_guidance()`, not anything. It is stored and never used for anything.
- `monthly_burn` is read by exactly one function, `vps_guidance.py::_key_assumptions()`, which builds a
  sentence ("Assumption: monthly burn is $X") that is a prop of `VPSResultPanel.tsx` — a component confirmed,
  by its own successor's code comment (*"Support, Part 3/4. Replaces VPSResultPanel..."*) and by an
  exhaustive search for live importers, **to no longer be mounted anywhere in the current app.**

So: this whole section's *raison d'être* (feeding VPS guidance text) is gone, and its one specific field with
a real reader (`monthly_burn`) feeds a UI surface that no longer exists. Meanwhile Finance now does this job
for real, with real numbers, elsewhere in the same venture workspace. **Flag for reframing, not deletion**:
these fields still serve a legitimate, different purpose — letting a founder sketch a rough financial
assumption *before* they have real Finance data — but the current copy and placement don't say that, and
nothing currently nudges a founder with real Finance data to stop maintaining this parallel, disconnected
guess.

The same investigation shows the broader `generate_guidance()` output (strengths, risks, key assumptions,
milestones, "path to stronger") is **entirely dead** from a founder's perspective — computed on every venture
create/update, still returned by the API, never rendered by anything live. See §8 (dead-concept audit).

### 3.7 Build Intelligence Loop (Section 10) — the strongest part of the product

Ran a real loop: started the recommended test, recorded deliberately mixed evidence (4/5 positive on
frequency of pain, 3/5 relying on texts alongside existing tools, 2/5 wanting a prototype, **1/5 explicitly
negative** — a larger operator saying their existing platform is adequate).

The classification step surfaced **one** structured signal ("5 customer conversations") and required an
explicit relationship choice — *Supports it / Mixed — some of both / Contradicts it / Doesn't tell us yet* —
before it would save. Selected the honest answer, "Mixed."

**What SIE did with it, verified live:**

- Never averaged the signal into a false "validated." Explicit output: *"Early preference-based evidence...
  is mixed."*
- Named exactly what the evidence does **not** prove (willingness to pay, retention, repeatable acquisition,
  broader-segment validity, unit economics) — genuine epistemic honesty, not hedging for its own sake.
- **The next recommended question changed, meaningfully, because of the contradiction**: not a generic
  "test more," but *"Why do some of RelayOps's target customers experience this problem and others don't?"*
  — a question that could only be asked because the specific tension was persisted and reasoned about.
  ChatGPT, asked cold, cannot produce this question without the founder re-explaining the entire prior
  conversation, including the exact 4-vs-1 split.
- Surfaced the resolution mechanism ("if one of these no longer reflects the current situation... mark it
  resolved") without forcing resolution — exactly the "discoverable, not immediate" standard asked for.

**One real limitation, worth naming honestly**: the four distinct sub-signals in the recorded note (frequency
pain, tool-stacking behavior, prototype interest, one contradicting objection) were classified as a **single**
aggregate item ("5 customer conversations"), not decomposed. This is the safer failure mode (no false
precision, matching the "never invent what wasn't given" doctrine seen throughout Finance too) but it does
mean a founder who wants to know *which part* of what they said supports vs. contradicts can't currently see
that distinction inside SIE — only in their own original note.

### 3.8 Decision + History (Sections 13–14)

Chose "Continue as recommended." The recommendation and the decision are shown in visually distinct places
(a forward-looking "Try this" card vs. a retrospective "What happened afterward: you decided..." line) —
though when a founder simply accepts the default, both currently show the *identical sentence*, which reads
as slightly redundant rather than clearly differentiated in that specific case.

History (`?tab=history`) genuinely tells a story, not just a timestamped log: *"WHAT YOU LEARNED"* (the raw
quote, preserved verbatim), *"WHAT STILL NEEDS PROVING,"* and an expandable full event trail that shows, in
order: *Decision recorded — SIE recommended: X / You decided: X → Learning recorded: "..." → Action added →
Venture created.* A founder returning months later could genuinely answer "why did we decide this" from this
trail alone. One inconsistency observed: the collapsed "WHAT STILL NEEDS PROVING" summary line still showed
the *original* question after a new one had already been decided — likely a stale-summary vs. live-detail
mismatch, not chased further given time constraints, but worth a follow-up look.

### 3.9 Finance (Section 15) — verified exact

Entered the exact figures specified: Cash $300,000; MRR $0; Payroll $10,000, Contractors $8,000, Software
$2,000, Marketing $2,000, Rent $0, Professional services $2,000, Other $1,000.

**Verified exactly correct, live**: Monthly spend $25,000. Net burn $25,000/mo. Runway **12 months** exactly.
Cash Outlook table: $275,000 in October 2026, decrementing by exactly $25,000/month, reaching $0 in September
2027 — arithmetically perfect.

Finance felt like the same company workspace structurally (same header, breadcrumb, tabs) but **carries zero
narrative connection to what Build already knows about this company** — nothing on the Finance page
references the customer-validation work just completed in Build, and nothing in Build's recommendation
engine is aware RelayOps now has 12 months of runway. This is the coherence gap the phase asked to be
*identified, not solved*.

### 3.10 Hiring (Section 16) — verified exact

Modeled a Founding Engineer, $180,000 salary, 25% burden, starting 2 months out. **Verified exactly
correct**: $225,000/year fully loaded ($180,000 × 1.25), $18,750/mo. Current runway correctly read 12 months;
"without this hire" and "with this hire" depletion dates were both shown, clearly distinguishing current vs.
planned. The product genuinely does more than calculate here — the same page's persistent context (this
company's actual cash, actual revenue, other already-planned changes) is what makes the number *actionable*
rather than a bare arithmetic fact; a spreadsheet doing the same multiplication would tell you the cost
without ever connecting it to *this company's* specific runway trajectory or its other pending decisions.

### 3.11 Operating changes + Plan comparison (Section 17)

Modeled contractor spending −$5,000/month and a revenue change to $15,000/month beginning 6 months out. Both
previews used explicitly hypothetical language ("Assumption: revenue becomes $15,000/month beginning March
2027. If this holds, this is the modeled result — not a prediction.") and never touched the actual snapshot.
With three active plans (the hire + both changes), the **"You have multiple planned changes / Compare
plans"** contextual prompt (shipped in Phase 35D-B) appeared correctly beneath Planned Changes — not before,
not with only one plan. Created a combined plan; its assumption list read as clean, descriptive sentences
("Founding Engineer starts November 2026 ($18,750/mo)," "Contractors spending decreases $5,000/month starting
October 2026," "Revenue becomes $15,000/month starting March 2027") with **no arbitrary-nickname collisions**
— the 35D-A/B fix holds up under a fresh, independent test.

### 3.12 Fundraising (Section 18) — verified exact, both instruments

Finance pre-fill confirmed exact: Cash On Hand and Monthly Burn fields arrived pre-populated at **$300,000**
and **$25,000** — read directly from the same Finance data just entered, labeled "Loaded from your Finance
tab — editable here, won't change Finance."

**SAFE ($1,000,000 / $8,000,000 post-money cap) — verified exact**: 12.50% dilution (1,000,000 / 8,000,000),
founder ownership 100.00% → 87.50%, modeled runway 12.0 → **52.0 months** (($300,000 + $1,000,000) / $25,000
= 52 exactly).

**Priced round ($7,000,000 pre-money / $1,500,000 new investment) — verified exact**: 17.65% dilution
(1,500,000 / 8,500,000 post), founder ownership 100.00% → 82.35%, modeled runway 12.0 → **72.0 months**
(($300,000 + $1,500,000) / $25,000 = 72 exactly).

A founder can answer cash, ownership, dilution, and runway consequences for both instruments, side by side
with a real cap table, entirely without a spreadsheet. What's visibly missing, honestly: **any guidance on
how much to raise**, and no connection back to the operating plans just modeled in Finance (a raise sized to
cover a specific hiring plan's cash need, for instance).

### 3.13 Finance → Fundraising coherence (Section 19)

Confirmed precisely the distinction the phase asked to be documented: **the product answers "what happens if
I raise this" fully and accurately, but not "how much should I raise."** A real Capital Planning workflow —
operating plan → capital need → financing structure → dilution → resulting runway — is not built, and
building it now would be premature: it would need to sit on top of the Finance↔Fundraising connection (§3.9,
§19) that doesn't exist yet. The math and UI foundation for both halves already exist and are both verified
correct; the missing piece is entirely the *bridge*, not new math in either system.

### 3.14 Venture → Startup graduation (Section 20)

RelayOps, being genuinely early (no revenue, no paying customers), correctly shows **no graduation
prompt at all** — confirmed in code: eligibility is `hasPayingCustomers || hasRevenue` from the venture's own
reported validation data, a real evidence threshold, not a time-based or engagement-based gate. This is a
good design choice against "artificial gating" pressure.

**Found, in code, a second and separately-triggered "become more real" pathway on the same Overview page**:
alongside `graduation.eligible` (→ "Ready to make this a startup?" → creates a Startup Profile/membership),
there is an independent `readyToAnalyze` condition (driven by the server's own recommendation engine,
`primaryNextStep.kind === "ready_for_real_startup"`) that surfaces a *different* card — *"Ready to turn this
into a real startup?"* → **"Analyze My Startup"** → routes to `/analyze`, which does not graduate anything,
create a membership, or claim ownership; it just runs the evidence-based Analyze pipeline on the venture's
own description. Two different signals, two different pieces of copy, two different destinations, both
about "becoming real," on the same page. A prior phase (34F, per its own code comments) already fixed one
half of this confusion (an under-explained quiet link); this second, structurally distinct pathway was not
part of that fix and remains a live source of the exact ambiguity Section 20 asked to test for.

### 3.15 My Startups / Founder Workspace (Section 21) — the sharpest finding in this audit

Entered an existing graduated company's Founder Workspace (Retool). This is **not** a more-mature version of
Build's own workspace — it is a structurally different product:

- **A numeric score is front and center**: "71.1 Startup Power Score / B− / Strong / Medium confidence" —
  exactly the presentation Build deliberately avoids everywhere else in the current product.
- **A full pillar/subscore breakdown** (Market, Team, Product, Execution, Traction, Financial Health, each
  with a weight, a confidence level, and an "Inferred/Unavailable" status) — the entire Analyze apparatus,
  reused wholesale as the founder's own primary intelligence surface.
- **"Fundraising Readiness: 50, Developing, 2 gaps identified"** — a *third*, separate scoring concept,
  distinct from both SPS and Finance/Fundraising's own deterministic math.
- **"Action Plan"** (own table, `founder_actions`) — functionally the same job as Build's "Your Actions"
  (`venture_missions`), but a **separate, non-overlapping system**, scoped to `startup_id` instead of
  `venture_id`.
- **"Recent Updates"** (own table, `founder_updates`) — functionally the same job as Build's evidence-capture
  loop (`venture_evidence`), again a **separate system**.
- **"✓ Verified — SIE has confirmed your relationship to this company"** shown prominently inside a page the
  UI itself labels *"private to you and your team"* — trust language surfacing where the founder is the only
  audience and already knows who they are.

**Answer to the directive's own A/B/C question: (C) — Build and My Startups are duplicative and should
eventually converge.** They are not complementary (A) — a founder does not get something in My Startups that
extends what Build already does; they get a *replacement* worldview. They are more than "overlapping but
clarifiable" (B) — the duplication is structural (two action tables, two evidence tables, two entirely
different intelligence presentations for the same real company), not just a labeling problem. A graduated
company's memory is now **split across two systems with no shared timeline**: Build's own History for that
venture freezes at the moment of graduation, while a new, separate history starts accumulating in My
Startups. Answering "what's the full story of this company" requires checking both.

### 3.16 Trust / Verification (Section 22)

"Verified" and "Founder-managed" are real, meaningful distinctions **for a public viewer or investor**
deciding whether to trust a claim of ownership. Live-observed inside the founder's own private workspace,
this same trust language adds a badge with no clear audience — the founder isn't being asked to trust
themselves. The underlying trust architecture (claims, memberships, verification) is sound and should not be
removed; the issue is *placement*, not the concept — it's being shown on a screen where it primarily serves
as reassurance rather than as the access-relevant signal it is on a public profile.

### 3.17 Analyze / SPS (Section 23)

Ran a real, live analysis on RelayOps (the actual pipeline, not a cached example) using the venture's own
description plus its recorded customer-conversation evidence as "additional company information."

**A serious, live, code-confirmed finding**: the resulting public profile displayed, simultaneously:

- A top banner: *"Not enough evidence yet — we don't have enough public evidence yet to evaluate this
  company's fundamentals. Coverage 5%."*
- Directly below it, a full six-pillar score breakdown with specific numbers (Market 6.0/10, Team 6.5/10,
  Product 4.9/10, Execution 7.2/10, Traction 6.0/10, Financial Health 6.6/10) and subscores with explicit
  percentage weights.
- A separate section, **"V2.1 SCORE (LEGACY): 61.2"**, with its own copy: *"This tracks the earlier V2.1
  methodology's score history, separate from the Startup Power Score assessment above."*

Traced this in code: the "(legacy)" label is a **deliberate, already-documented mitigation** from a prior
phase (comment: *"Phase 10.9 verification fix... showing a bare 'Current SPS' here reads as a second,
competing number right next to (or directly contradicting) the V3 assessment above it"*) — a past team
already recognized exactly this risk and added an honest label rather than leaving it silent. **The label is
honest; the net effect is still confusing.** A founder or investor scanning this page sees "not enough
evidence" and two different specific-looking numeric scores (a pillar breakdown and a "61.2 legacy" score) in
the same view. This is precise-looking output for a company that, by the page's own top-line admission,
doesn't have enough evidence to be meaningfully scored — a direct, live example of SPS "looking falsely
precise," which Section 23 explicitly asked to test for.

**Who is this for?** The page itself is built for an investor/public-viewer decision ("should I trust this
company"), not a founder decision — confirmed by its own framing (evidence, confidence, recommendations
phrased as gaps to close for external credibility) and by the fact that a founder's *actual* decision support
(the evidence loop, the recommendation engine) lives entirely in Build, not here.

### 3.18 Build vs. Analyze (Section 24)

The mental model the phase proposes — *Build: help me operate and learn about MY company over time. Analyze:
help me evaluate A company from available evidence* — **is well-communicated within Build and within Analyze
each on their own**, but the boundary blurs exactly at the two seams already found: (a) the `readyToAnalyze`
card inside Build that routes into Analyze without explaining that this leaves Build's own worldview behind,
and (b) My Startups, which is nominally "my own companies" (Build's job) but is actually powered entirely by
Analyze's intelligence. A founder who has never graduated a venture will find the Build/Analyze boundary
clear. A founder who *has* graduated one will find it much less clear, because their own company now lives
inside what is functionally the Analyze system.

### 3.19 Learn (Section 25)

Not merely a content library. Confirmed live, twice: (1) as a standalone destination (`/playbooks`, a clean,
stage-organized library — Start/Model/Build/Pitch/Fundraise — each article a short, plain-language read), and
(2) as a **contextual link directly inside a Build recommendation** ("Secure a first paying customer..." →
"Learn how: Pricing & Willingness-to-Pay →"). The second pattern is exactly the "strongest version of Learn"
the directive describes and already exists in the live product — it's a genuine asset, not a gap. Nothing
found suggests Learn content is personalized or persisted per founder; it functions as a shared reference
library, appropriately.

---

## 4. Cross-system memory map

| System | What it actually persists (confirmed via `app/database/db.py` table list) | Scope |
|---|---|---|
| **Build** | `modeled_ventures` (details/assumptions), `venture_missions` (questions/tests/actions — "Your Actions"), `venture_model_updates`, `venture_decisions`, `venture_evidence`, `venture_financial_snapshots`, `venture_hire_plans`, `venture_financial_plans`, `venture_financial_scenarios`, `venture_graduations` | `venture_id` |
| **Finance** (subset of Build) | `venture_financial_snapshots`, `venture_hire_plans`, `venture_financial_plans`, `venture_financial_scenarios` | `venture_id` |
| **Fundraising** | **Nothing persists.** Confirmed unchanged from earlier phases: the entire SAFE/priced-round simulator is ephemeral client-side state; only the Finance pre-fill (a read) crosses the boundary. | none (ephemeral) |
| **Startup / Founder Workspace** | `startups`, `startup_memberships`, `startup_claims`, `founder_actions`, `founder_updates`, `startup_milestones`, `saved_startups` | `startup_id` |
| **Analyze** | `analyses` (canonical analysis rows), `score_history`, `analysis_runs` | `startup_id` (shared with Startup) |
| **Learn** | Nothing personalized or persisted — a static content set. | none |

**Duplicated state, confirmed in code:**
- `venture_missions` (Build's action loop) vs. `founder_actions` (My Startups' "Action Plan") — two
  independent systems tracking the same underlying concept ("things the founder should do next") for what
  may be the same real company before and after graduation.
- `venture_evidence` (Build's "What happened?" capture) vs. `founder_updates` (My Startups' "Recent
  Updates") — two independent "record what happened" systems.

**Disconnected state:** Finance's real, deterministic financial picture (cash, burn, runway) has no path
into Build's recommendation engine or into My Startups' Fundraising Readiness assessment — three systems
that could each be more useful with the others' data, sharing none of it today.

**Ephemeral state that should eventually persist, if Capital Planning is ever built:** nothing about a
modeled SAFE or priced round is remembered — a founder who models three financing scenarios today has no way
to compare them next week without re-entering everything.

**Hypothetical data that must never contaminate factual data:** verified, live, in both directions this
phase — no Fundraising input ever reached canonical Finance (confirmed via network inspection showing only
`GET` calls), and no Finance scenario/plan value ever appeared in a canonical snapshot. This boundary is
solid and should be preserved exactly as-is in any future Capital Planning work.

---

## 5. Product object / vocabulary audit

| Noun | Founder needs to know it? | Product or implementation language? | Genuinely distinct object? | Recommendation |
|---|---|---|---|---|
| Idea | Yes | Product (but overloaded — object type *and* lifecycle stage) | Yes, as an object; ambiguous as a stage label | Keep as the Build object type; consider a different stage label than "Idea Stage" to stop double-duty |
| Venture | Rarely surfaced directly to founders (mostly internal/URL) | Mostly implementation | Same object as "Idea" | Keep internal; founders never need this word |
| Startup | Yes | Product | Yes — a real, distinct post-graduation object with membership/trust semantics | Keep, but see Founder Workspace convergence below |
| Startup Profile | Yes (shown at the graduation moment) | Product, but under-explained at the point of creation historically | Yes | Keep name; keep improving the explanation (already partly fixed in Phase 34F) |
| Founder Workspace | Yes (page header) | Product | Structurally, yes — but see §3.15: should not remain this different from Build | Reconsider scope, not name, first |
| Company | Used loosely/interchangeably in copy | Product | No — not a distinct object, an informal synonym for Venture/Startup | Fine as prose; don't formalize as a fourth noun |
| Analysis | Yes | Product | Yes | Keep |
| Scenario | Internal/DB only; founder sees "Compare plans," "plan," never "scenario" (per 35D-A/B) | Implementation | Yes, as a DB concept | Correctly hidden already — keep it that way |
| Plan | Yes (financial plans, hire plans) | Product | Yes | Keep |
| Test | Yes, informally ("Try this," "Start this test") | Product | Yes | Keep as used — never over-formalized into "hypothesis" |
| Evidence | Occasionally leaks in copy ("Early preference-based evidence...") | Borderline | Yes | Mostly fine; watch for drift toward more clinical phrasing |
| Decision | Shown as "you decided," never the bare word "Decision" as a UI label | Product | Yes | Keep |
| Outcome | Not used as a UI noun; folded into "What happened" | N/A | Yes, in the data model | Correctly hidden |
| Action | Yes — but means two different systems (`venture_missions` vs `founder_actions`) | Product | Ambiguous — same word, two objects | Needs the convergence recommended in §3.15, not a rename |

**Recommended founder-facing vocabulary (no renames performed this phase):** Build / Venture-stage company
(displayed simply as "Idea" for the pre-revenue stage it already uses) → Startup (post-graduation) →
Analysis / Startup Profile (Analyze's own output, for any company) → Plan / Compare plans (Finance) →
Financing (Fundraising's own instruments) → Action, Evidence, Decision (Build's own loop, kept exactly as
worded live today). The one real gap is not a missing word — it's that **"Action"** and **"what happened"**
each already have the right founder-facing words, but two different underlying systems answer to them.

---

## 6. Top-nav verdict

`Build / Analyze / My Startups / Learn` is **still the strongest available four-item structure** given what
exists today — each item names something a founder can act on, and none is redundant *in isolation*. The
problem this audit found is not that the nav needs different labels or a different count of items; it's that
**My Startups currently points at a different product than Build does**, so the nav's implicit promise
("Build now, graduate into My Startups") is only half true. Fixing that is a scope/architecture question
(§3.15), not a navigation-relabeling question — redesigning the nav now, before that convergence question is
answered, would be solving the wrong layer.

---

## 7. ChatGPT head-to-head

| Task | Verdict | Why |
|---|---|---|
| What should I validate next? | **SIE wins** | Recommendation is derived from this company's own persisted evidence and contradictions, not a fresh guess each time. |
| What have I learned about customers? | **SIE wins** | Raw quotes + classified relationship (supports/mixed/contradicts) persist verbatim; ChatGPT has no memory across sessions without the founder re-pasting everything. |
| Why did I make this decision? | **SIE wins** | History shows "SIE recommended X / you decided X," dated, next to the evidence that prompted it. |
| What contradictions exist in my evidence? | **SIE wins** | Explicit "Mixed" classification and a discoverable resolution mechanism; ChatGPT would average or ignore unless explicitly reminded of every prior data point. |
| What is my runway? | **SIE wins narrowly** | The calculation itself (cash/burn) is commodity arithmetic ChatGPT does instantly — but SIE already has the real numbers on file, deterministically, with NULL-vs-zero handled correctly; ChatGPT needs the founder to supply and re-supply every input. |
| What happens if I hire someone? | **SIE wins narrowly** | Same reasoning — the math is trivial, the value is that it's computed against *this company's actual, current, remembered* cash position without re-entering anything. |
| What happens if revenue drops? | **Equivalent for the math; SIE wins for context** | ChatGPT can do the arithmetic if given the numbers; only SIE already has them and shows the result next to the company's other planned changes. |
| Compare two operating plans | **SIE wins** | Deterministic, reproducible, side-by-side, tied to the same persisted actual baseline; a ChatGPT comparison is only as consistent as the prompt re-supplies every assumption identically each time. |
| What happens if I raise a SAFE? | **SIE wins** | Correct, auditable dilution/cap-table math with a real "before/after" table; ChatGPT can approximate SAFE math but has no persistent cap table to update. |
| What happened to ownership? | **SIE wins** | Same reasoning — a real, inspectable cap table, not a re-derived estimate. |
| How has the company changed over 3 months? | **SIE wins, if History is used consistently** | Only SIE has an actual persisted timeline; this is entirely unavailable to a fresh ChatGPT session by construction. |
| What should I focus on next given everything SIE knows? | **SIE wins — this is the core differentiator** | This is precisely the "remember everything and use it consistently" capability generic AI cannot replicate without the founder doing all the remembering themselves. |

**Where generic AI still wins outright:** open-ended brainstorming, general startup education (though Learn
already covers much of this), and any question that benefits from broad external knowledge SIE's own
evidence base doesn't contain (e.g., "what do investors in my specific sector typically look for" as a
general knowledge question, versus SIE's own evidence-grounded, company-specific version of that question).

**Generic-AI replacement risk, by capability:**
- **HIGH**: bare calculators used in isolation (burn/runway math *by itself*, with no persisted context) —
  this is the one place the phase's own example ("calculate cash/burn") is right to worry, and it's exactly
  why Finance's value is the *persistence and reuse* of the numbers, not the arithmetic.
- **MEDIUM**: pitch deck coaching, general "give me startup advice" style prompts, generic Learn-equivalent
  content (a founder could get comparable generic advice from ChatGPT, though not the contextual, evidence-
  linked version Build already delivers).
- **LOW**: everything that depends on remembering and reasoning over *this specific company's* accumulated
  evidence, contradictions, decisions, and financial state consistently over time — the entire Build
  Intelligence Loop, History, and any cross-referencing of Finance + Fundraising + evidence together (the
  last of which doesn't fully exist yet, but is exactly where the defensible value would compound if built).

---

## 8. Dead / legacy product concept audit

| Concept | Where found | Classification | Reasoning |
|---|---|---|---|
| `VPSResultPanel.tsx` (score ring, strengths/risks, "Path to Stronger") | Confirmed zero live importers; explicitly superseded per its successor's own code comment | **REMOVE LATER** | Fully dead; not urgent, but real maintenance debt — the component, its Learn explainer (`VpsCategoryExplainer.tsx`), and related dead links should eventually be deleted together |
| `generate_guidance()` output (`app/ai/vps_guidance.py`) — strengths, risks, key_assumptions, milestones | Still computed and returned by the API on every venture create/update; zero live renderer | **REMOVE LATER** | Backend computation with no consumer; safe to remove once confirmed nothing else depends on the API response shape |
| `WhatIfPanel.tsx`, `ScenarioComparison.tsx` | Zero live importers anywhere in the app; explicitly noted in `VentureWorkspace.tsx`'s own comment as already removed from navigation | **REMOVE NOW** candidate | Lowest possible risk — already fully disconnected, and the codebase's own comments confirm the removal was intentional; only the file deletion itself remains |
| `whatIfScenarios.ts` underlying utilities (`assumptionDiff.ts`, `hasCommercialScale.ts` consumers) | Some functions still imported by live code | **KEEP INTERNAL** | Do not delete the whole file — only the dead panel components above |
| Six-category taxonomy (Market Potential, Problem & Solution, Founder Readiness, Reaching Customers, Economic Potential, Validation) | Home page + Build's `VentureUnderstandingPanel` | **KEEP USER-FACING**, reword the home page only | The categories are alive, useful, and non-numeric; only the home page's "modeled across six categories" framing oversells them as a scoring pitch |
| `V2.1 SCORE (LEGACY)` on public Startup Profiles | `SPSHistory.tsx`, confirmed via a live analysis run on RelayOps | **RENAME/CONSOLIDATE** (already partially mitigated) | Honestly labeled already; still produces a confusing side-by-side with "not enough evidence" banners and a full pillar breakdown — worth a follow-up on when/whether to suppress it entirely for low-coverage companies |
| "Fundraising Readiness" (LLM-judged gap score in My Startups) | Live on Retool's Founder Workspace | **KEEP USER-FACING, but clarify boundary** | A real, distinct, already-known-disconnected system from Finance/Fundraising's deterministic math (confirmed in an earlier phase's own audit); the risk is a founder assuming it's related to Finance's real burn/runway numbers when it isn't |
| Idea Lab / "Venture Simulator" naming in code comments | Throughout `app/api.py`, `vps_scoring.py` | **KEEP INTERNAL** | Never founder-facing; harmless as internal naming |
| "Model" tab / old What-If tab (removed) | Referenced only in `VentureWorkspace.tsx`'s own historical comments | **KEEP INTERNAL** (comment already documents the removal) | No action needed — this is the codebase correctly remembering its own history |

---

## 9. Top product problems (unranked list, prioritized in §10)

1. Venture creation allows a venture to be created with no name, silently, with the create button never
   disabled — reproduced live, and evidenced by 6 of 12 pre-existing ventures already sitting as "Untitled
   venture."
2. Build and My Startups are two different products wearing one navigation label each ("Build" and "My
   Startups") that implies continuity where none currently exists.
3. Two independent, non-overlapping systems each track "things to do" (`venture_missions` /
   `founder_actions`) and "what happened" (`venture_evidence` / `founder_updates`) for what can be the same
   real company before and after graduation.
4. The home page's "modeled across six categories" framing reads as a scoring pitch, contradicting the
   product's own current direction away from founder-facing scores in Build.
5. SPS can present a confident-looking, precise numeric breakdown (pillar scores, a "V2.1 legacy" score) on
   the same page that says "not enough evidence yet" — a live, reproduced instance of false precision.
6. Two separately-triggered "become more real" pathways exist on the same Build Overview page (graduation vs.
   "Analyze My Startup"), with similar copy and different consequences.
7. Finance, Fundraising, and Build's own recommendation engine share no data — each is individually excellent
   and mutually blind to the others.
8. The Capital assumption fields in "Add venture context" are provably orphaned (confirmed, code-traced) —
   founders can spend effort on a field that drives nothing.
9. Trust/verification language ("✓ Verified") appears inside a page explicitly labeled private to the
   founder, where it has no clear access-relevant purpose.
10. "Action" means two different objects depending on which workspace a founder is in.

---

## 10. Recommended simplifications (non-exhaustive, feeding §11 priorities)

- Require a non-empty, non-placeholder venture name before enabling "Create Venture" (client-side is
  sufficient; this is validation, not new capability).
- Reword the home page's six-category framing away from "modeled across six categories" toward the same
  "what we believe / what we don't know yet" language already used live inside Build.
- Decide, deliberately, whether My Startups should (a) be rebuilt to use Build's own evidence/decision loop
  post-graduation instead of Analyze's scoring apparatus, or (b) keep its current investor-facing character
  but be relabeled/re-explained so a founder doesn't expect Build-style continuity. Either is defensible;
  leaving it ambiguous is not.
- Merge or bridge `venture_missions`/`founder_actions` and `venture_evidence`/`founder_updates` so a
  graduated company's history doesn't split into two untraceable halves.
- Give Finance's real numbers *some* path into Build's recommendation text and/or My Startups' Fundraising
  Readiness assessment (read-only, one direction, no math changes) before considering Capital Planning.
- Consolidate the two "become more real" pathways on Build's Overview into one, clearly explained choice.
- Remove `WhatIfPanel.tsx`/`ScenarioComparison.tsx` and the dead `vps_guidance.py` output path as a small,
  low-risk cleanup pass, separate from any of the above.

---

## 11. Recommended product architecture (direction, not a spec)

The cleanest framing this audit could construct: **one company, one continuous timeline, three lenses on it.**

- **Build** owns the timeline: evidence, decisions, outcomes, financial state, financing models — for a
  company at any stage, idea through revenue through fundraising. Nothing about "graduating" should reset or
  fork this timeline.
- **Analyze** owns *evaluation from available evidence* — for any company, including one the founder is
  building, on demand, never automatically replacing Build's own evidence loop.
- **My Startups**, if it continues to exist as a distinct surface at all, should be a *view* into the same
  Build timeline for companies that have crossed the graduation threshold, with the addition of
  trust/membership/public-profile management — not a second, parallel intelligence system.

This is a direction to evaluate, not a phase to begin. See §39/next phase.

---

## 12. Explicit non-goals of this document

This document does not decide whether to build Capital Planning, does not redesign SPS, does not propose a
new evidence taxonomy, does not merge Build and My Startups, does not rename any object in the product, and
does not commit to any specific engineering plan. It records what was found, live, this phase, and prioritizes
it. Implementation is explicitly out of scope per this phase's own directive.
