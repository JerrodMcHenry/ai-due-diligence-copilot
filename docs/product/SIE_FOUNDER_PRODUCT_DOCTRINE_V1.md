# SIE Founder Product Doctrine V1

**Status:** Implemented (Phase 34F — Founder Product Doctrine + Acceptance Corrections). This document is
the canonical statement of the product rule every future phase must follow; it does not change SPS
methodology, does not change Fundraising math, and does not migrate the Venture/Startup data model (that
migration is scoped separately — see `docs/product/VENTURE_STARTUP_ARCHITECTURE_AUDIT_V1.md`).

## 1. The governing rule

> **STAGE CHANGES GUIDANCE. EVIDENCE CHANGES CONFIDENCE. VERIFICATION CHANGES TRUST. NONE OF THEM DETERMINE
> FEATURE ACCESS.**

Concretely:

- A **Venture** is the founder's company/workspace from initial idea onward. It does not need to
  "graduate" before the founder can use Build, quantitative modeling, Fundraising, Analyze/SPS, pitch-deck
  tools, or any future founder tool.
- **Stage** (idea/validating/building/operating — §2) changes what SIE *recommends*, never what a founder
  is *allowed to do*.
- **Evidence** (Phase 34D's confirmed evidence, interpretations, decisions, outcomes) changes how much
  *confidence* SIE — or a reader of a Startup Profile — should place in a given assumption. It is not a
  permission system.
- **Verification** (a claim's provenance — founder-said vs. founder-observed vs. externally verified)
  changes *trust*, never access. An unverified assumption is still usable everywhere; it is simply labeled
  honestly as unverified.
- **SPS and evidence confidence/provenance are conceptually separate** (§4). SPS is an assessment of the
  venture as currently described. Evidence confidence describes how strongly that description is supported.
  A hypothetical, idea-stage, founder-reported, or fully operating company may all legitimately receive an
  SPS; what differs is how much confidence should be placed in it, never whether it is computed at all.
- An assumption is never presented as verified fact merely because it was entered into a model. See §3's
  terminology fix for how this shows up in copy.

## 2. Lifecycle language

**Before:** a single ambiguous word ("Idea") as both a founder-set dropdown value and (separately) a
computed venture-state pill, with a genuine live regression case (a $840K-ARR venture reading as "stuck at
Idea" — Phase 33's own finding) and no vocabulary for a launched/operating company at all.

**After:** the computed venture-state pill (`VentureJourney.tsx`, `lib/journey/inferVentureStage.ts`) now
has four explicit, current-maturity labels:

| id | label | meaning |
|---|---|---|
| `idea` | **Idea Stage** | Defining the problem, customer, solution, and the assumptions that matter most. |
| `validating` | **Validation Stage** | Testing whether the important assumptions are true against real-world evidence. |
| `building` | **Building Stage** | Executing against increasingly validated assumptions and tracking real progress. |
| `operating` | **Operating Stage** *(new this phase)* | Running as a real, launched company — the same tools remain available as the venture evolves. |

`operating` is reachable only via the founder's own explicit "Launched" manual stage selection — never
auto-inferred from evidence alone, however extreme (this mirrors the existing, unchanged rule that
evidence alone never implied "fundraise" either). Every rendering of this state keeps the existing,
unchanged qualifier immediately beside it: *"This describes where things stand right now, not a level
you've unlocked — it can move forward or backward as new evidence comes in."* This sentence, and the "no
staircase" design (one state, shown at a time, never a numbered progression with earlier steps "filled
in") were already correct from Phase 33's own Founder Experience Model correction; this phase only added
the fourth stage and the "Stage" suffix, and re-audited that no other founder-facing lifecycle copy implies
permanent, permission-based, or gamified progression. None found beyond what §2 already fixed.

## 3. "Model" language — removed where it named SIE's internal representation

Legitimate financial-modeling verb usage ("Model a SAFE," `FundraisingSimulator`'s own "What are you
thinking about? / Model your very first outside investment") is untouched — that is exactly the kind of
defensible modeling SIE should keep doing.

What changed is language that named SIE's own internal data structure rather than something meaningful to
a founder:

| Before | After |
|---|---|
| "Model a new venture" (page title) | "Start a new idea" |
| "Review Your Venture Model" (page title) | "Review what SIE understood" |
| "Build My Venture Model" (button) | "See What SIE Understands" |
| "Review and edit the full model" (disclosure) | "See the full details" |
| "Edit venture details" (Phase 34E's own already-improved name, further reframed — see §4) | "Help SIE understand your venture" / "Add venture context →" |
| "Modeled assumption" (provenance badge) | "SIE assumption" |
| "Your venture model was updated this week" / "Applying will update your venture model and history" / "update your venture model with what you actually observed" / "We found information that could update your venture model" | "your venture details" / "what SIE knows about your venture" (each reworded in place, same meaning) |

Every provenance distinction these labels carried (founder's own words vs. SIE's inferred guess vs. not yet
provided) is completely unchanged — only the noun naming the guess changed, from "model" to "assumption."

## 4. Adding venture context is now outcome-driven

The Overview section that lets a founder add/correct venture details is reframed around the founder's own
benefit, not profile completeness:

> **Help SIE understand your venture**
> Add details about your customers, business model, market, traction, and finances so SIE can give you
> more relevant guidance and analysis.
>
> **Add venture context →**

The explanation is always visible (even before the section is expanded) so a founder knows *why* before
deciding whether to open it. This is the same editor, byte-for-byte, that Phase 34E already moved off the
Model tab — only the surrounding pitch changed.

## 5. "Create a Startup Profile" removed from the primary journey

The quiet, unexplained `"Create a Startup Profile from this venture →"` link (shown to every venture not
yet eligible for the graduation suggestion) explained none of: what a Startup Profile is, what creating one
does, why a founder should want one, or why a Venture needs to become one. It is removed from Overview.

The fully-explained graduation card (shown only once real evidence makes graduation eligible — "Ready to
make this a startup?", with what/why spelled out: a private Founder Workspace, a public Startup Profile,
the idea and its history staying exactly as they are) is **unchanged** and still the only way to graduate
from Overview. No graduation/startup infrastructure was removed — see the architecture audit
(`VENTURE_STARTUP_ARCHITECTURE_AUDIT_V1.md`) for the full accounting, including the one real gap this
introduces (no remaining UI path to graduate a venture *before* it meets the evidence bar).

The four concepts this section asked to keep distinct — (1) the founder's venture workspace, (2) venture
stage, (3) a public/shareable startup profile, (4) verification/provenance — are addressed together in the
architecture audit, since they are fundamentally a Venture/Startup data-model question, not a copy fix.

## 6. "Other things you're tracking" simplified

Retitled to a single lightweight action, **"Working on something else? Add it →"**, with no separate intro
paragraph and no "tracking" language naming the internal mission architecture. It remains collapsed by
default and still opens onto the same, unmodified capture/actions/alternatives components (Phase 10/23/33) —
founder autonomy to pursue something other than SIE's recommendation is fully preserved, just via a smaller,
plainer entry point, exactly matching the acceptance standard's "primary experience stays focused on the
single highest-value question."

## 7. Recommendation prerequisite logic

**The bug:** for a venture with no described target customer, SIE's own `vps_guidance.py` milestone
ranking still put *"Interview 20+ target customers to validate the problem is real."* first — the same
milestone offered to every fresh, no-traction venture regardless of whether SIE knows who that customer is.
Live-confirmed: a venture describing only *"I want to create a product that streamlines macroeconomic
data. A Macrobond but cooler."* got exactly this recommendation while simultaneously showing "Who it's for:
Not described yet."

**The fix (`app/ai/build_recommendation.py::_fallback_recommendation`):** one narrow, named prerequisite
check — when the chosen milestone names "target customer(s)" and the venture's own `target_customer` field
is empty, substitute a customer-identification question first:

> **What matters now:** Figure out exactly who you're building [venture] for.
> **Why it matters:** You haven't identified a specific customer yet. Before testing demand, narrow down
> who experiences this problem most acutely.
> **Try this:** Choose the first customer group you want to investigate — for example a specific job
> title, industry, or use case that experiences this problem most acutely.

Once a target customer is described, the original milestone becomes reachable again automatically (this is
a fallback override, not a suppression) — verified by a new backend test
(`test_recommendation_respects_customer_prerequisite`) that exercises exactly this before/after transition.

`vps_guidance.py`'s own `next_milestones()` ranking (which also feeds `NextMoves` and `WeeklyReview`) was
deliberately **not** touched — the fix is scoped to the one place the acceptance test is about (the
"What matters now" hero), per the directive's own "minimum coherent correction, document remaining gaps."

**Remaining gaps identified but NOT corrected this phase** (same class of prerequisite dependency, same
narrow-check pattern would apply if/when addressed):

- Pricing recommendations before problem/customer clarity is confirmed.
- Acquisition-strategy recommendations before a customer segment is defined.
- Retention recommendations before any real usage/customer evidence exists.
- Scaling/growth recommendations before repeatable demand is demonstrated.
- Fundraising-adjacent recommendations issued without relevant capital/runway context.
- Monetization-assumption recommendations before customer/value clarity exists.

None of these were observed to actually fire incorrectly in this phase's testing (only the customer-
interview case was reproduced live) — they are documented as structurally-similar risk, not confirmed bugs,
and a genuine rule engine was deliberately not built to pre-empt them.

## 8. Feature-access gate audit (Section 12)

A repository-wide search for logic where graduation status, verification status, venture stage, Startup
status, evidence quantity, or "maturity" prevents access to founder functionality found **no artificial
maturity gates** in the current implementation:

- **Fundraising** (`FundraisingSimulator` and everything under the Fundraising tab) makes **zero backend
  calls** — it is pure client-side arithmetic. There is structurally nothing to gate.
- **`POST /analyze`** (Analyze/SPS) requires only `RequireAuth` (a valid signed-in user) — no stage,
  graduation, or verification check of any kind.
- Every backend use of "graduated"/"graduation" is about the graduation *feature itself* (recording status,
  preventing a venture from graduating twice, the honest-banner state) — none of it blocks an unrelated
  feature.
- The only frontend use of `graduation.eligible` outside `VentureGraduation.tsx` itself is the one CTA this
  phase's §5 already addressed — nothing else reads it.
- `app/ai/confidence.py::calculate_confidence()` — a function that computes exactly the "evidence
  confidence" label (High/Medium/Low) the doctrine's SPS-vs-confidence contract describes — exists but has
  **zero call sites anywhere in the backend**. It is orphaned, not wired into SPS or any live surface. This
  means the conceptual separation the doctrine asks for is already structurally anticipated in the
  codebase, but no live surface currently *displays* an evidence-confidence label alongside SPS. Wiring it
  up would be a new-feature phase, not a correction — not done here.

**Legitimate gates found** (kept, as instructed): every `_require_owned_venture`/`_require_owned_startup`-
style ownership check; `RequireAuth` on every mutating endpoint; the pitch-deck-review/founder-workspace
membership checks; idempotency-key deduplication; the append-only supersession checks from Phase
34D/34D-A. All of these are authentication/authorization/ownership/data-integrity concerns, never maturity
policy.

**The one genuine current dependency worth naming honestly:** the Founder Workspace (`/founder/*`) and its
own tools (fundraising-gap tracking, etc.) do require a real `Startup` row + membership to exist, because
that is literally what those pages operate on today. This is not an "artificial" business rule in the sense
Section 12 means (nobody wrote `if not graduated: raise 403`) — it is a real, current data-model dependency,
and it is exactly what the architecture audit (§9 below) evaluates for whether it should still be a
*separate* founder product surface at all.

## 9. Acceptance test result

A brand-new venture created with only the exact text *"I want to create a product that streamlines
macroeconomic data. A Macrobond but cooler."* was walked through live (see the final report for the full
transcript). All ten acceptance criteria passed: venture stage, what SIE knows/doesn't know, why the
missing context matters, the corrected next question (customer identification, not premature interviews),
a concrete action, how to record what happened, the ability to reject SIE's recommendation, and that
Fundraising is available regardless of stage were all reachable without encountering "Model," "Startup
Profile," "Other things we're tracking," "Graduation," or "Verification required" anywhere in the flow.
