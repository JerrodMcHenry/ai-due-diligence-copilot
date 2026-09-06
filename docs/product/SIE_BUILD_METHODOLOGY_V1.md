# SIE Build Methodology V1

**Status:** Methodology/architecture specification only. No code changed in this phase (34B). Grounded in a
full repository audit (§23) rather than aspiration — every "what exists today" claim below cites the real
file/table/function it describes.

**Explicitly out of scope for this document and this phase:** implementation, UI redesign, new database
tables, new scores, SPS/Analyze changes, deployment. This document is the contract a future engineering
phase (34C+) builds against.

**Relationship to Phase 34A:** 34A removed VPS from the founder-facing Idea Lab experience and replaced
the Model tab with a knowledge-state view (`VentureUnderstandingPanel`, `WHAT WE KNOW` / `WHAT WE BELIEVE`
/ `WHAT WE DON'T KNOW YET`) and rebuilt What-If around qualitative consequences
(`lib/simulate/scenarioInsights.ts`). This document generalizes and formalizes the direction 34A already
started; 34A's own retained-VPS-internals decisions are treated as settled fact here, not re-litigated.

---

## 0. How to read this document

Every section distinguishes two kinds of statement:

- **CURRENT SYSTEM FACT** — true today, verified against the actual code/schema during this phase's audit.
- **RECOMMENDED FUTURE ARCHITECTURE** — proposed, not yet built.

Where a section is pure recommendation with no current-system anchor, it says so explicitly rather than
implying something exists that doesn't.

---

## 1. Product mission and core loop

**RECOMMENDED (product direction, locked per the directive):**

> SIE Build helps founders identify the most important uncertainty facing their venture, test it with
> credible evidence, understand what they learned, and make the next decision.

Core loop:

```
HYPOTHESIS → UNKNOWN → TEST → EVIDENCE → INTERPRETATION → DECISION → OUTCOME
→ UPDATED UNDERSTANDING → NEXT HIGHEST-VALUE UNKNOWN → REPEAT
```

The founder never needs to see this vocabulary. The founder-facing questions are exactly six, and every
canonical object below exists to answer one of them:

| Founder-facing question | Answered by |
|---|---|
| "What should I figure out next?" | UNKNOWN (ranked) |
| "Why does it matter?" | UNKNOWN's decision-relevance rationale |
| "How should I test it?" | TEST (recommended) |
| "What happened?" | EVIDENCE (captured) |
| "What did we learn?" | INTERPRETATION |
| "What should I do now?" | DECISION (SIE recommends, founder decides) |

**CURRENT SYSTEM FACT:** a version of this loop already exists end to end, just without persisted
intermediate objects. `resolveIdeaLabNextStep.ts` + `vps_guidance.py::_next_milestones()` answer "what
next" (crudely — see §8-9); `MissionsSection.tsx`/`CaptureWhatHappened.tsx` let a founder act and record
what happened; `venture_model_updates` stores a before/after diff. What's missing is not the loop shape —
it's that every step's *reasoning* is recomputed fresh from the current assumption snapshot rather than
accumulated as history a founder can review. §23 maps this precisely.

---

## 2. Canonical objects

Format per object: meaning, non-meaning, required/optional fields, relationships, lifecycle, provenance,
persistence, current-system mapping, genuine gap.

### 2.1 VENTURE

**Means:** the founder's current understanding of what they are trying to build — a live, editable model,
not a verdict.
**Does not mean:** a scored evaluation; a real company's public profile (that is Startup/Analyze, §17).

**Required:** `name`, a current assumptions snapshot.
**Optional:** `description`, `industry`, `business_model`, `target_customer`, `stage`.

**Relationships:** has many Hypotheses, Tests, Evidence records, Decisions; has exactly one current
assumptions snapshot (the "belief state now"); has zero or one Graduation record (§16).

**Lifecycle:** non-linear — see §16.

**Provenance:** founder-owned; SIE proposes structure via AI extraction (§2 note on `idea_structuring.py`)
but the founder confirms before anything is created.

**Persistence:** CURRENT SYSTEM FACT — `modeled_ventures` table (`app/database/db.py:2946`), one row per
venture, `assumptions JSONB` and `model_result JSONB` columns. `assumptions` is the live "belief state"; it
is overwritten on every save (no per-field version history at the row level — history lives separately in
`venture_model_updates`, §2.5).

**Gap:** none structural. The Venture object itself needs no new table. What it currently lacks is a
*decomposition* of its flat assumption fields into discrete, individually-tracked Hypotheses (§2.2).

### 2.2 HYPOTHESIS

**Means:** a specific, falsifiable proposition the founder currently believes, not yet sufficiently
established by evidence. "Specific" is load-bearing — see §5's bad/good example.
**Does not mean:** a VPS category; a vague topic ("market demand"); a fact already proven by transaction
evidence (once well-supported, it graduates toward "known," not "hypothesis" — but see §5 on why binary
validated/invalidated framing is still wrong).

**Required:** `venture_id`, `statement` (natural language, specific), `family` (one of the families in §5),
`status` (§5's lifecycle states), `created_by` (`founder` | `sie_suggested`), `created_at`.
**Optional:** `depends_on_hypothesis_id` (sequencing), `related_category` (bridge to the existing six VPS
categories for migration/backward-compat only — see §23), `founder_note` (disagreement/context, §15).

**Relationships:** many-to-many with Evidence (one interview can speak to several hypotheses; one
hypothesis needs several pieces of evidence); zero-or-one `depends_on_hypothesis_id`; one-to-many with
Test (a test targets one or more hypotheses); zero-or-many Decisions reference it as context.

**Lifecycle:** `OPEN` → `TESTING` (a Test is in flight) → `SUPPORTED` / `CONTRADICTED` / `MIXED` /
`STILL_INSUFFICIENT` (§5, §7 — never a binary validated/invalidated) → `RETIRED` (superseded by a pivot or
judged no longer decision-relevant).

**Provenance:** founder-authored explicitly, or SIE-suggested by decomposing the venture's free-text
description/assumptions into testable statements — the same kind of extraction `idea_structuring.py`
already performs for flat fields, generalized to propositions.

**Persistence:** RECOMMENDED, genuinely new — no table exists today.

**Current-system mapping:** `VentureAssumptions`' flat fields (`problem_solution.problem_statement`,
`target_customer`, `gtm.primary_acquisition_strategy`, etc. — `dashboard/types/ideaLab.ts`) are each a
crude, single-valued, un-versioned approximation of a hypothesis: one text field standing in for "what we
currently believe about X," with no separate confidence/evidence-linkage state and no history beyond
whatever `venture_model_updates` happens to capture as a before/after diff. `next_milestones`
(`app/ai/vps_guidance.py::_next_milestones()`) are effectively hypothesis-testing prompts already, just
generated fresh each time from the assumptions blob rather than attached to a persisted Hypothesis object
a founder can watch evolve over months.

### 2.3 UNKNOWN

**Means:** an unresolved question whose answer could materially change what the founder should do next.
**Does not mean:** every fact SIE happens not to have — see §8's explicit anti-checklist rule.

**Required:** a decision-relevance rationale ("why does answering this change anything"); a link to the
Hypothesis (or Hypothesis family, pre-decomposition) it would help resolve.
**Optional:** an estimated cost-of-being-wrong note; a `depends_on_unknown_id`.

**Relationships:** resolves (fully or partially) as Evidence accumulates against its linked Hypothesis. An
Unknown is not itself persisted as a separate row from its Hypothesis in the recommended architecture — it
is the *unresolved state* of a Hypothesis, computed, not stored twice (see §23: avoid a second parallel
object that can drift from the Hypothesis it describes).

**Lifecycle:** exists exactly as long as its Hypothesis is `OPEN`/`TESTING`/`STILL_INSUFFICIENT`;
disappears (nothing further to compute) once `SUPPORTED`, `CONTRADICTED`, `MIXED`-and-accepted, or
`RETIRED`.

**Provenance:** derived, not separately authored.

**Persistence:** no new table — a computed view over Hypotheses + Evidence.

**Current-system mapping:** `next_milestones` and `validation_gaps` (`vps_guidance.py`) are today's working,
if rigid, Unknown-prioritization mechanism. `next_milestones` is a fixed-priority-tier candidate list
(`_next_milestones()`'s own `candidates: list[tuple[int, str]]`); `validation_gaps` is a finer-grained
version scoped to the Validation category alone. Both are ADAPT candidates (§23), not new infrastructure —
the ranking logic in §9 below is an evolution of `_next_milestones()`'s own tiering, not a replacement of
its spirit.

### 2.4 TEST

**Means:** a deliberate action designed to reduce a specific Unknown / gather evidence for a Hypothesis.
**Does not mean:** passive waiting; a vanity activity done for its own sake (§10, §20).

**Required:** `venture_id`, `title`, `test_type` (§10's taxonomy), `target_hypothesis_id(s)`, `status`
(`active` | `completed` | `dismissed`), `source` (`sie_recommended` | `founder_created`).
**Optional:** `description`, `resource_ref` (playbook link), `related_category` (legacy bridge).

**Relationships:** targets one or more Hypotheses; produces zero or more Evidence records on completion;
a Decision may follow.

**Lifecycle:** `active` → `completed` (produces Evidence + prompts Interpretation) or `dismissed` (a
founder authority event, §15 — preserved, never silently deleted).

**Provenance:** `sie_recommended` (from the Unknown-prioritization logic, §9) or `founder_created` (custom).

**Persistence:** CURRENT SYSTEM FACT, substantially — `venture_missions` table
(`app/database/db.py:3290`). Columns already present: `title`, `description`, `mission_type` (a *test-type*
enum: `customer_discovery, validation, pricing, gtm, product, founder, economics, other` — a real, if
coarse, subset of §10's taxonomy), `related_category`, `source` (`vps_guidance` | `founder_created` —
maps directly to `sie_recommended`/`founder_created`), `status`, `learning_summary`, `resource_ref`.

**Gap:** `related_category` references a VPS category key, not a Hypothesis id (Hypothesis doesn't exist
yet). `mission_type`'s enum needs widening to the fuller taxonomy in §10 (an additive `ALTER TABLE ...
CHECK` change, not a new subsystem). Everything else is a rename/relabel exercise, not new infrastructure.

### 2.5 EVIDENCE

**Means:** an observation relevant to one or more Hypotheses, tagged with its own evidence type (§6),
never collapsed into a score.
**Does not mean:** a fact automatically true just because a founder typed it; see §22 (founder
exaggeration).

**Required:** `venture_id`, `raw_text` (verbatim, never rewritten), `evidence_type` (§6), `provenance`
(§14), `recorded_at`.
**Optional:** `hypothesis_id(s)` (many-to-many — may be unlinked at capture time and linked later, or never
linked if genuinely unstructured), `structured_observation` (e.g. a count, a percentage, a dollar figure —
what `captureSignals.ts` already extracts), `sample_size`, `segment`, `relationship_to_hypothesis`
(`supports` | `contradicts` | `mixed` | `neutral` — per hypothesis link, since the same evidence can
support one hypothesis and be irrelevant to another), `source` (`founder_reported` today; `external_source`
is a future, out-of-scope-for-V1 type per the directive's own "for future use" framing), `limitations` note.

**Relationships:** many-to-many with Hypothesis; zero-or-one originating Test; feeds Interpretation.

**Lifecycle:** immutable once recorded (a founder can add a *correction* as a new Evidence row referencing
the old one, §15 — never silently overwritten) — mirrors `venture_missions`' own append-only discipline.

**Provenance:** see §14; the dominant case is `founder_reported` (a founder's own free text) reclassified
by `evidence_type`.

**Persistence:** RECOMMENDED, genuinely new — this is the single largest gap this audit found (§23,
§9 "MISSING INFRASTRUCTURE"). Today's architecture computes evidence-shaped structure and *throws it
away*: `dashboard/lib/captureSignals.ts::extractCaptureSignals()` already produces exactly the right shape
— `ProposedSignal { label, sourceQuote, fieldPath?, proposedValue?, polarity, actionRelevant? }` — for
every capture, but nothing persists it. Only the resulting `venture_missions.learning_summary` (raw free
text) and, if the founder applies a field-mapped signal, the resulting `VentureAssumptions` value survive.
The classification (evidence type, polarity, which hypothesis it speaks to) is recomputed or lost on every
page load. **This is the one place where "genuinely missing" is not a euphemism for "needs a bigger
version of something that exists" — it needs a new table**, described in §6/§23.

### 2.6 INTERPRETATION

**Means:** what the available evidence reasonably implies for a Hypothesis, stated in prose, including
ambiguity and contradiction (§7, §11).
**Does not mean:** a score, a percentage, a "validated" stamp.

**Required:** `hypothesis_id`, `summary` (prose — what strengthened, what's still unresolved, what
contradicts), `generated_at`, `triggering_evidence_id(s)`.
**Optional:** `newly_created_unknowns` (a pointer to Unknowns this interpretation surfaced).

**Relationships:** produced whenever new Evidence attaches to a Hypothesis; read by the founder before a
Decision.

**Lifecycle:** one Interpretation per meaningful evidence-arrival event, not continuously recomputed
silently — a founder should be able to see "this is what we thought before, this is what changed."

**Provenance:** `sie_derived` — deterministic template logic first (per §11), an LLM synthesis step only
where template logic cannot honestly cover ambiguity/contradiction narration (see §1 AI-role framing
carried over from 34A: "explain consequences," "surface contradictions" are sanctioned AI uses).

**Persistence:** RECOMMENDED, new — no table exists.

**Current-system mapping:** the closest working prototype of this exact concept is Phase 34A's own
`lib/simulate/scenarioInsights.ts::buildScenarioInsights()` — it already produces "strengthened,"
"weakened," "still unknown," and "new questions" sections from before/after category data, entirely
template-driven, zero score. That function is scoped to a *hypothetical* What-If scenario; §11 recommends
generalizing its shape to *real* evidence-arrival events. `vps_guidance.py`'s `_strengths()`/`_risks()`
are a weaker, threshold-based ancestor of the same idea and are being hidden from the UI (34A) precisely
because they collapse into evaluative "strength/weak point" language rather than genuine interpretation.

### 2.7 DECISION

**Means:** a choice the founder makes after considering available evidence. SIE recommends; the founder
decides — these are two separate, separately-preserved facts (§12, §15).
**Does not mean:** an automatic system action; SIE never acts as the founder's proxy.

**Required:** `venture_id`, `context` (which Hypothesis/Unknown), `sie_recommendation`, `sie_reasoning`,
`founder_choice` (from §12's closed list), `decided_at`.
**Optional:** `founder_rationale` (free text, if the founder disagreed or wants to record why), pointer to
`evidence_considered`.

**Relationships:** references the Hypothesis/Unknown it resolves; may reference a completed Test; produces
zero-or-one Outcome later.

**Lifecycle:** immutable once recorded; a later reversal (§15) is a *new* Decision row referencing the
prior one, never an edit.

**Provenance:** `sie_recommendation`/`sie_reasoning` are `sie_derived`; `founder_choice`/
`founder_rationale` are `founder_said`.

**Persistence:** RECOMMENDED, new for the general case — but a working, narrower precedent already exists
and should be the template: `GraduateVentureRequest` (`app/models/venture_graduation.py`) already carries
exactly this shape for one specific decision ("graduate to a real startup"): a `trigger`
(`suggested`/`manual` — i.e., was this SIE-prompted or founder-initiated) alongside the founder's actual
choice. §23 recommends generalizing this one-decision-type pattern into the generic Decision object rather
than inventing an unrelated shape.

### 2.8 OUTCOME

**Means:** what happened after a Test or Decision, observed later — the longitudinal half of the loop
(§13's pilot-renewal worked example).
**Does not mean:** the immediate Evidence from a test's own completion (that's Evidence, §2.5) — Outcome is
specifically *downstream*, checked-in-on-later information.

**Required:** `decision_id` or `test_id` it follows from, `observed_at`, `description`.
**Optional:** structured fields (mirrors Evidence's `structured_observation` shape) when the outcome itself
is measurable (e.g. "1 of 2 pilots renewed").

**Relationships:** may itself become new Evidence for the same or a related Hypothesis (§13's own point:
"SIE should eventually be able to reason over this chain").

**Lifecycle:** created once, at the moment of observation; there can be more than one Outcome over time for
the same Decision (60-day check-in, 6-month check-in).

**Provenance:** `founder_reported` (the founder says what happened) unless a future integration makes it
`external_source`-observable (out of scope for V1).

**Persistence:** RECOMMENDED, new — **this is the second largest gap** (§23). Nothing in the current
system prompts or records a later check-in on a completed mission or a past decision. `WeeklyReview`
surfaces *recent* history; it never specifically asks "you decided to run paid pilots six weeks ago — what
happened?" This absence is exactly what would make the product feel like "a form, once" rather than
compounding memory (§19's stress-test).

---

## 3. Hypothesis methodology (§5 of the directive)

A hypothesis must be specific enough that a real test could support or contradict it. The directive's own
example is the bar:

- BAD: "Market demand"
- GOOD: "Controllers at companies with 50–500 employees experience enough pain from manual
  accounts-receivable collections that they would consider adopting dedicated software."

**Hypothesis families** (used to organize decomposition, never mechanically forced): problem, customer,
solution, behavior/adoption, willingness to pay, acquisition, economics, retention, differentiation,
market, founder/team, operational/scaling. A pre-revenue idea-stage venture will typically only have live
hypotheses in 3-5 of these at once — forcing all twelve is exactly the "giant checklist" anti-pattern §8
forbids.

**When SIE creates/suggests a hypothesis:** at venture creation, by decomposing the free-text description
the same way `idea_structuring.py` already decomposes it into flat fields — except into propositions
instead of (or in addition to) single-value fields; and reactively, whenever new Evidence surfaces a
question the founder hasn't stated as a hypothesis (e.g. two interviewees mention a workflow constraint
the founder never named — SIE proposes it as a new hypothesis for confirmation, never silently assumes
it).

**Refinement:** a founder or SIE can narrow an over-broad hypothesis ("customers want this" →
"controllers at 50-500-employee companies want this") without losing history — refinement creates a new
hypothesis version that supersedes the old one; evidence already linked to the old one is not orphaned
(both stay linked; the interpretation layer notes the narrowing).

**Dependency:** one hypothesis can require another to be at least partially resolved first (e.g.
willingness-to-pay is only a meaningful question once the problem hypothesis has some support) — surfaced
via `depends_on_hypothesis_id` and used by the ranking logic (§4) to sequence recommendations, mirroring
`_next_milestones()`'s own existing priority-tiering (e.g. its GTM-feasibility candidate is explicitly
gated on `has_traction`).

**Contradictory evidence's effect on a hypothesis:** never collapses to invalidated — moves the hypothesis
to `MIXED` or `CONTRADICTED` with the contradiction preserved and narrated (§7), never silently averaged
away.

**Sufficiency:** a hypothesis becomes `SUPPORTED` when evidence of a strong-enough type (§6) exists with no
material unresolved contradiction — never a fixed count/threshold (no "3 pieces of evidence = validated");
the bar is qualitative and evidence-type-aware (a single Transaction outweighs ten Reported Preferences).

**Remaining unresolved:** perfectly normal, default state (`OPEN`/`STILL_INSUFFICIENT`) — never treated as
a defect to fix before the founder can proceed with other work.

**Revision:** editing a hypothesis's statement materially (not just narrowing) creates a new hypothesis and
retires the old one, with an explicit link — never an in-place rewrite that would make old evidence
attributions misleading.

**Retirement:** founder-initiated (a pivot) or SIE-suggested when a hypothesis is structurally no longer
decision-relevant (e.g. the venture pivoted target customers entirely) — always requires founder
confirmation (§15), never silent.

**Founder disagreement:** a `founder_note` field on the Hypothesis preserves the founder's own reasoning
for disagreeing with SIE's classification or interpretation — the disagreement is recorded, not resolved
by overwriting one party's view (§15's general rule).

---

## 4. Evidence methodology and taxonomy (§6 of the directive)

**Recommended canonical taxonomy** (seven types, ordered by ascending strength of what they establish —
strength is *contextual to the hypothesis*, not absolute):

1. **FOUNDER CLAIM** — an unverified belief the founder states about the market/customers, not something
   they observed directly ("I think customers will pay $500/month"). Weakest evidence type; useful mainly
   as the seed a Hypothesis is built from, not as support for it.
2. **REPORTED PREFERENCE** — a third party's stated intention/opinion, collected by the founder ("eight
   prospects said they'd probably pay"). Real signal, but intention-to-behavior gap is well-known and must
   be named in Interpretation (§7's worked example is exactly this).
3. **OBSERVED BEHAVIOR** — something a third party actually *did*, short of a commitment ("four prospects
   completed the prototype workflow").
4. **COMMITMENT** — a real but non-monetary or conditional commitment ("two signed LOIs / agreed to
   pilots").
5. **TRANSACTION** — money has actually changed hands, or an active paid agreement exists ("three
   customers paid $500"). Maps directly onto the existing `paying_customers`/`monthly_revenue` fields'
   strict definitions in `idea_structuring.py`'s own prompt rules (§14).
6. **LONGITUDINAL OUTCOME** — a Transaction or Commitment's status observed again later ("three customers
   remained active and paying six months later"). This is specifically an Outcome (§2.8) that becomes new
   Evidence.
7. **EXTERNAL EVIDENCE** — market/competitive/industry information from a traceable external source. Not
   collectable in V1 (no external data integration exists) — reserved for future use per the directive's
   own framing; the taxonomy has a slot for it now so it isn't a breaking addition later.

**CURRENT SYSTEM FACT grounding this taxonomy:** `idea_structuring.py`'s validation-field rules already
draw exactly the REPORTED PREFERENCE vs. TRANSACTION line by hand, in prose, for one specific case: "Someone
who 'said they would pay'... is NOT a paying customer — that is expressed willingness, a weaker and
different signal." This taxonomy generalizes a distinction the system already enforces narrowly into a
first-class, reusable classification.

**Preserved fields per Evidence record:** source, provenance (§14), date, related hypothesis/hypotheses,
sample size, segment/context, the quantitative observation (if any), the qualitative observation (verbatim
text), supports/contradicts/mixed/neutral (per hypothesis), founder-confirmed vs. SIE-inferred, recency
(computed from date, not stored separately), limitations. This is the `Evidence` shape from §2.5 — see
there for the exact required/optional split.

**No Evidence Score.** Nothing here reduces to a number. Evidence *type* plus its per-hypothesis
relationship (supports/contradicts/mixed) is the entire representation; ranking/prioritization logic (§9)
reasons over these categorically, not by summing weights into a hidden scalar.

**How SIE reasons differently by evidence type:** a REPORTED PREFERENCE can raise a hypothesis to `MIXED`
or lightly toward `STILL_INSUFFICIENT`-with-some-support, never to `SUPPORTED` on its own; a TRANSACTION
can move a willingness-to-pay hypothesis to `SUPPORTED` even in small numbers, because it is the strongest
type available for that family. This is a qualitative reasoning rule set (documented per-family in a
future implementation phase), not a weighted formula — consistent with §2's "measure what can legitimately
be measured, represent uncertainty explicitly elsewhere" rule.

---

## 5. Contradictory evidence (§7 of the directive)

Contradiction is first-class, never hidden to produce a clean conclusion. The directive's own worked
example is the canonical test case for a future implementation:

> 8/10 controllers say AR collections is painful, but 1/10 would change their existing workflow.
> Correct: "The problem appears meaningful, but adoption/willingness-to-change evidence remains weak."
> Wrong: "Validated."

This is two *different* hypotheses (a PROBLEM hypothesis and a BEHAVIOR/ADOPTION hypothesis) receiving
evidence from the same interviews — the methodology must attach each of the ten data points to the
correct hypothesis rather than averaging them into one "validation" verdict. This is precisely why
Evidence-to-Hypothesis is many-to-many (§2.5/§2.2), not one-to-one.

**Representation rules:**
- **Supporting evidence** — recorded per hypothesis, never aggregated across hypotheses.
- **Contradictory evidence** — recorded explicitly, surfaces in Interpretation as a named tension, not
  averaged into a midpoint.
- **Mixed evidence** — a hypothesis can legitimately sit at `MIXED` indefinitely; this is not a bug state.
- **Insufficient evidence** — the default, honest state; never punished (carried over from `vps_guidance.py`'s
  own "expected at the idea stage, not a failure" framing in `_validation_gaps()`, which this generalizes).
- **Segment-specific disagreement** — evidence tagged with a `segment` (§2.5) that disagrees across
  segments is surfaced as "this holds for segment A but not segment B," never silently pooled.
- **Stale evidence** — computed from evidence `date` vs. venture pace, surfaced as a caveat in
  Interpretation ("this was true five months ago; consider re-testing"), never silently trusted forever or
  silently discarded.
- **Evidence answering a different hypothesis than the founder thinks** — a real, named failure mode a
  future extraction/tagging step must guard against (e.g. a founder logs "talked to 5 customers about
  pricing" tagged against the PROBLEM hypothesis by mistake); the founder-correction mechanism (§15) is the
  safety valve — SIE proposes a hypothesis link, founder confirms or corrects it.

---

## 6. Unknown / uncertainty methodology (§8 of the directive)

An Unknown is decision-relevant when answering it would change what the founder does next — not merely
because SIE lacks the fact. Concretely, an Unknown qualifies when at least one of these is true:

- A live Hypothesis it resolves is on the path to a near-term Decision.
- Multiple plausible Decisions currently depend on which way it resolves.
- It gates another Unknown (dependency, §3).
- It is the single largest source of "cost of being wrong" (§4) among currently-open questions.

**Anti-pattern, explicitly forbidden:** enumerating every unset field on `VentureAssumptions` as an
"unknown" and presenting it as a checklist. `stillFiguringOutFromCategories()`
(`dashboard/components/idea-lab/ventureOverviewHelpers.ts`) is the CURRENT SYSTEM's closest analog and is
already disciplined about this — it lists categories with *no score at all* (nothing to reason from yet),
not every individual missing field within an already-scored category. The recommended architecture
preserves that discipline: Unknowns are ranked and trimmed (§4), never dumped in full.

---

## 7. Next-best-question / recommendation methodology (§9 of the directive)

**RECOMMENDED ranking criteria** (qualitative, not a hidden formula the founder never sees a number from):

1. **Decision relevance** — would answering this materially change what the founder should do?
2. **Uncertainty** — how unresolved is it right now (`OPEN` vs. `MIXED` vs. `STILL_INSUFFICIENT`)?
3. **Cost of being wrong** — how costly is it to keep building on a false assumption here (e.g.
   willingness-to-pay is usually higher cost-of-being-wrong than a differentiation phrasing)?
4. **Evidence gap** — what evidence already exists bearing on it (an Unknown with zero evidence outranks
   one with some-but-mixed evidence at the same relevance level)?
5. **Testability** — can a reasonable Test actually move it (an Unknown with no feasible near-term test is
   deprioritized, not hidden)?
6. **Sequencing/dependency** — does another Unknown need answering first (§3)?
7. **Stage/context** — what's appropriate given the venture's actual state (directly inherited from
   `_next_milestones()`'s own `has_traction`/`has_commercial_scale` gating, which already does real,
   working stage-awareness — e.g. it suppresses "interview 20 customers" outright once a venture has
   genuine commercial scale).

**No visible formula.** These criteria combine into a ranking; the founder never sees a weighted score.
**RECOMMENDED, documented separately per the directive's own instruction:** an internal deterministic
prioritization mechanism (a fixed rule/tier system, exactly like `_next_milestones()`'s own
`candidates: list[tuple[int, str]]` priority-tier approach, just generalized to operate over persisted
Hypotheses/Unknowns instead of being recomputed fresh from assumptions each time) is the right
implementation shape *if and when* an internal ranking is needed — extending a pattern that already works,
not inventing scoring theater.

**Founder-facing output shape** (locked, matches the directive exactly):

```
MOST IMPORTANT QUESTION
WHY IT MATTERS
RECOMMENDED TEST
WHY THIS TEST
WHAT RESULT WOULD BE INFORMATIVE
WHAT THIS TEST WILL NOT PROVE
```

**CURRENT SYSTEM FACT:** `missionSuggestions.ts`'s `why` field already answers "why it matters" for the
current fixed set of nine milestone templates (a real, if static, precedent for this exact output field).
"What result would be informative" and "what this test will not prove" do not exist today anywhere in the
founder-facing copy — genuinely new fields to add per recommendation.

---

## 8. Test methodology (§10 of the directive)

**Recommended test taxonomy:** customer interview, problem interview, prototype/usability test,
landing-page test, willingness-to-pay test, paid pilot, pre-sale, outbound test, pricing test, channel
test, retention/usage observation, competitive research, unit-economics investigation, founder/team
action, custom. Not rigid Lean Startup bureaucracy — a test is recommended because it fits the specific
Unknown, never because "the methodology says do interviews first."

**CURRENT SYSTEM FACT:** `venture_missions.mission_type` already encodes a coarser six-plus-other version
of this (`customer_discovery, validation, pricing, gtm, product, founder, economics, other`). Widening this
CHECK constraint is the concrete, additive schema change §23 recommends — not a new table.

**Every recommended test answers, per the directive's own required shape:**

```
WHAT ARE WE TRYING TO LEARN?
WHY DOES IT MATTER?
WHAT SHOULD THE FOUNDER DO?
WHO / WHAT SHOULD BE TESTED?
WHAT SHOULD BE RECORDED?
WHAT RESULT WOULD CHANGE OUR UNDERSTANDING?
WHAT WOULD THIS TEST NOT ESTABLISH?
```

The last two fields ("what result would change our understanding" / "what this would not establish") are
new — they are the test-methodology mirror of §7's recommendation-output fields, and both are the direct
methodological fix for the directive's own §22 "over-testing" failure mode: naming in advance what a test
*cannot* prove keeps a founder from mistaking one successful interview round for full validation.

---

## 9. Interpretation methodology (§11 of the directive)

After evidence is recorded, SIE states plainly what changed — evidence restated as observation, then a
clearly separate inference, never blended into one confident sentence. Worked example (directive's own):

> Evidence: "We interviewed 10 controllers. Seven spend more than five hours per week manually following
> up on overdue invoices."
> Interpretation: "Early interview evidence supports the hypothesis that manual collections creates
> meaningful workflow pain among the interviewed controllers." — **and, in the same breath:** "This does
> not establish willingness to pay, adoption, retention, or whether the same problem is present in other
> customer segments."

**Rules an Interpretation must follow:**
- Never overclaim — every interpretive sentence traces to a named piece of evidence.
- Evidence (fact) and inference (what it implies) are visually/structurally distinct, never merged.
- Explicitly name: what strengthened, what weakened, what remains unresolved, what new questions this
  evidence created (mirrors `scenarioInsights.ts`'s own four-bucket shape, §2.6), and any contradiction.
- **Declining information value:** if a second test of the *same* already-well-supported hypothesis
  produces the same class of evidence with no new information (e.g. an 11th confirmatory interview after
  ten already agreed), Interpretation says so plainly ("this confirms what you already knew; consider
  moving to the next unknown instead") — the direct methodological answer to §22's "over-testing /
  endless validation" failure mode.

**CURRENT SYSTEM FACT / working prototype:** `scenarioInsights.ts::buildScenarioInsights()` (34A) already
implements this exact shape — strengthened / weakened / still-unknown / new-questions — for a *hypothetical*
scenario. §23 recommends generalizing it to run on *real* evidence-arrival events instead of (or in
addition to) What-If previews.

---

## 10. Decision methodology (§12 of the directive)

Learning is not the product outcome; a better decision is. **SIE recommends. The founder decides.** These
are two permanently separate, separately-preserved facts — never merged into one record that looks like
"the system decided."

**Recommended closed decision vocabulary** (extensible, not exhaustive): continue testing, proceed, revise
hypothesis, change customer, change problem, change solution, change pricing/business model, build
prototype, begin selling, run paid pilot, focus on retention, focus on acquisition, pause, graduate to
operating startup (§16), consider fundraising (§16 — explicitly non-terminal).

**Preserved per Decision (§2.7's required fields, restated for emphasis):** SIE's recommendation, SIE's
reasoning, the founder's actual choice, the founder's rationale if given, the date, the evidence
considered, and — later — the Outcome. **SIE must never appear to have acted as the founder.** Concretely:
no code path may change `venture_missions.status`, `VentureAssumptions`, or create a Decision's
`founder_choice` value without an explicit founder action — mirrors the existing, load-bearing "VPS
FIREWALL" discipline already enforced in `MissionsSection.tsx`/`CaptureWhatHappened.tsx` ("the ONLY call
in this file that can change a score is `handleUpdateModel()`'s explicit `updateVenture()` call") —
generalized from "only an explicit founder action changes the model" to "only an explicit founder action
records a Decision."

**CURRENT SYSTEM FACT / precedent:** `GraduateVentureRequest.trigger` (`suggested` | `manual`) is a real,
narrow, working instance of exactly this pattern for one decision type. §23 recommends generalizing this
shape rather than inventing a new one.

---

## 11. Outcome methodology (§13 of the directive)

Four distinct concepts, deliberately kept separate (directive's own worked example, reproduced as the
canonical test case):

```
TEST:      Offer paid pilot to 5 prospects.
RESULT:    2 accept.
EVIDENCE:  2/5 qualified prospects made a real purchase commitment.   (a COMMITMENT-type Evidence, §4)
DECISION:  Proceed with paid pilots before full product build.
OUTCOME (60 days later): 2 pilots active, 1 renewed, 1 churned.       (a LONGITUDINAL OUTCOME, §4,
                                                                        which itself becomes new Evidence)
```

**Why the separation matters:** "Result" and "Evidence" look identical in casual conversation but are not
— the Result is the raw event; Evidence is the *classified* observation extracted from it (its
evidence-type, which hypothesis it bears on, supports/contradicts). Collapsing them loses exactly the
distinction §6/§7 depend on. Outcome is deliberately never conflated with the Test's own immediate Result —
Outcome is what a *check-in later* reveals, and is the mechanism that lets SIE "reason over this chain"
longitudinally, which is the paid-value thesis's central claim (§13/§19).

---

## 12. Provenance model (§14 of the directive)

**Recommended canonical vocabulary** (six values):

| Value | Means |
|---|---|
| `FOUNDER_SAID` | The founder directly stated this. |
| `FOUNDER_OBSERVED` | The founder reports something they witnessed in the real world (an interview outcome, a signed pilot). |
| `SIE_INFERRED` | SIE proposed a reasonable, labeled guess the founder has not confirmed. |
| `SIE_CALCULATED` | A deterministic arithmetic derivation from other known values (e.g. MRR from price × customers). |
| `EXTERNAL_SOURCE` | A traceable third-party source (reserved for future use, §4). |
| `STILL_UNKNOWN` | Nothing is known; never silently defaulted to a guess. |

**CURRENT SYSTEM FACT — this is not a green-field recommendation, it is a generalization of a real,
working mechanism.** `DraftProvenance` (`dashboard/types/ideaLab.ts`) already implements three of these
six values almost verbatim: `"user_provided"` (≈ `FOUNDER_SAID`), `"ai_inferred"` (≈ `SIE_INFERRED`),
`"unknown"` (≈ `STILL_UNKNOWN`) — enforced server-side by `idea_structuring.py::_sanitize_field()`, which
independently verifies every `"user_provided"` claim's `source_quote` against the founder's actual
submitted text (`_quote_is_verifiable()`) rather than trusting the LLM's own self-report. `FOUNDER_OBSERVED`
is currently *implicit*, not a per-field tag: the entire `validation` assumption group is structurally
defined as founder-reported observation by `vps_scoring.py`'s own module docstring
("everything under `assumptions["validation"]` is a founder-REPORTED OBSERVATION... every other top-level
group is a MODELED ASSUMPTION by construction") and is enforced the same fail-closed way
(`_sanitize_field(..., allow_inferred=False)` for the whole group). `SIE_CALCULATED` already exists in one
narrow, sanctioned form: `_revenue_value_is_verifiable()`'s ARR÷12 conversion, and
`lib/simulate/directConsequences.ts`'s MRR/ARR arithmetic (34A). `EXTERNAL_SOURCE` does not exist anywhere
in Build today — reserved, per the directive, for later.

**"Why does SIE believe this?"** — for every important conclusion, the architecture must make this
answerable by construction, not by a founder digging through history. This is already true for the
provenance the system tracks today (a `DraftField`'s `source_quote` answers it directly); the recommended
Evidence/Hypothesis/Interpretation objects (§2) extend the same discipline to the new object types —
every Interpretation cites its `triggering_evidence_id(s)`, every Decision cites `evidence_considered`.

**No confidence theater.** If a confidence-like signal is ever retained anywhere (none is recommended in
this document), it must be accompanied by an explicit, honest statement of what it means and why it's
defensible — the same bar `sole_uncorroborated_category` already meets today (a real, narrow, *explained*
flag on `compute_vps()`'s output, not a bare percentage) — but note VPS itself is being hidden from the
founder-facing UI (34A) precisely because a single blended number failed this bar in practice. The lesson
generalizes: a flag that explains a specific mechanism is fine; a number that implies more precision than
the inputs support is not.

---

## 13. Founder authority (§15 of the directive)

SIE is a copilot. Founder authority is explicit and total. Required behavior:

| Founder action | Required system behavior |
|---|---|
| Rejects SIE's recommended test | Test marked `dismissed` (mirrors `venture_missions.status` today), preserved, never deleted. |
| Chooses a different test | The founder's own test is created (`founder_created`, exactly as `venture_missions.source` already distinguishes today); SIE's original recommendation stays visible in history, not overwritten. |
| Disagrees with an interpretation | `founder_note` recorded on the Hypothesis/Interpretation (§2.2/§2.6); SIE's original interpretation is preserved alongside it, not replaced. |
| Corrects extracted evidence | A correction is a **new** Evidence-adjacent record referencing the original — never an in-place edit that erases what SIE originally extracted (mirrors the append-only discipline `venture_model_updates` already has for assumption changes). |
| Proceeds despite uncertainty | Allowed unconditionally — the Decision is recorded with the Hypothesis still `OPEN`/`STILL_INSUFFICIENT`; SIE never blocks a founder's own choice. |
| Revises the venture model | Existing `updateVenture()` path, unchanged — but now additionally may prompt "does this change any open Hypothesis?" |
| Reverses a prior decision | A new Decision row referencing the old one as superseded — the old Decision is never deleted or edited. |

**General rule, stated once because it governs all seven rows above:** SIE preserves history rather than
silently rewriting it. This is not a new principle for this codebase — it is the same discipline already
enforced by `venture_model_updates` (before/after snapshots, never in-place mutation) and by
`venture_missions.status` (a dismissed mission is a fact, not a deletion). §2's new objects (Hypothesis,
Evidence, Decision) simply need the same discipline applied to concepts that don't have a persisted home
yet.

---

## 14. Build lifecycle (§16 of the directive)

**Broad, non-linear states:** `IDEA → VALIDATING → BUILDING → OPERATING`. Fundraising is explicitly **not**
a terminal stage — a venture can raise money at any state or never raise at all (unchanged from 34A's own
Fundraising-tab framing: "You don't need to raise money to build a successful company").

**CURRENT SYSTEM FACT:** this is already the architecture. `VENTURE_STAGES` (`dashboard/types/ideaLab.ts`:
`["Idea", "Researching", "Validating", "Building", "Launched"]`) is the founder's own manually-set field;
`resolveVentureState()` (`dashboard/lib/journey/inferVentureStage.ts`) independently *infers* a
`{id: "idea"|"validating"|"building", label, description}` state from real assumption/validation data,
reconciled with (never overriding) the founder's manual stage. Both already explicitly reject a "staircase"
framing — `VentureJourney.tsx`'s own docstring documents replacing a literal numbered stepper with a
plain-language, non-committal state description for exactly this reason. No change needed here; this
document adopts the existing model as canonical.

**Graduation:** remains founder-initiated (§2's `GraduateVentureRequest`), never automatic, never
VPS/score-gated (VPS is gone from Build entirely; graduation eligibility was already computed from real
`paying_customers`/`monthly_revenue` fields via `isEligibleForGraduationSuggestion()`, never VPS, even
before 34A — see `resolveGraduationEligibility.ts`'s own docstring: "no VPS score, no new score of any
kind"). **Audit finding: no serious incompatibility exists between the existing graduation architecture
and this methodology.** The existing `venture_graduations` table, self-approval membership mechanism, and
eligibility check are preserved unchanged. The one addition worth making later (not now): a graduated
venture's accumulated Hypotheses/Evidence/Decisions should be visible in the resulting Founder Workspace as
provenance for the Startup's own SPS evidence base — see §15 for how this connects without merging the two
systems.

---

## 15. Build vs. Analyze (§17 of the directive)

Protected, unmerged distinction:

| | BUILD | ANALYZE |
|---|---|---|
| Subject | A founder's own venture, pre-evidence or early-evidence | A real, operating startup |
| Method | Hypotheses, Tests, Evidence, Decisions, Interpretation (this document) | SIE Methodology v2, six pillars, SPS |
| Score | None (removed, 34A; none recommended here) | SPS, calibrated, frozen this phase |
| AI role | Structure free text, suggest hypotheses/tests, interpret evidence, explain consequences | Evidence-graded pillar analysis, calibration-tested scoring |

**How they may eventually connect, without collapsing:** a graduated venture's Build history (Hypotheses
resolved, Evidence recorded, Decisions made) is legitimate **provenance context** for the resulting Startup
Profile — e.g. "this founder validated willingness-to-pay via 3 paying pilots before building" is a real,
citable fact a Founder Workspace could surface *alongside* the Startup's own independently-computed SPS,
the same way `GraduateVentureRequest.fields_transferred_count` already tracks how much Build context
carried over today. **Build evidence must never become an input to SPS's own scoring formula** — SPS stays
computed the way `app/docs/SIE_Methodology_v2_Specification.md` already defines it, from the Startup's own
evidence corpus (public information, pitch decks, company data), not from the founder's private Build
history. This is the same firewall discipline as the VPS/SPS separation `vps_scoring.py`'s own module
docstring already states ("VPS is architecturally separate from SIE Methodology v2 / SPS... It must never
be labeled, stored, or treated as SPS") — generalized to the newer Build objects.

---

## 16. Simulation rule (§18 of the directive)

**Strict rule:** SIE may simulate a consequence only when it is defensibly, deterministically calculable
from explicit assumptions the founder controls. SIE must never simulate a causal claim about startup
success where no defensible model exists.

**Defensible (already built, unchanged):**
- SAFE dilution / priced-round ownership — `app/ai/fundraising_engine.py` family (Phase 21A/21B), untouched
  this phase, deterministic cap-table math from explicit terms.
- Runway/burn — `directConsequences.ts`-style arithmetic (price × customers → MRR/ARR is the existing,
  narrowly-scoped example; runway = capital ÷ burn is the same shape, already computable from
  `capital.starting_capital`/`capital.monthly_burn`, though not currently surfaced as its own Direct
  Consequence — a plausible, low-risk future addition following the exact pattern `directConsequences.ts`
  already established, not a new mechanism).
- Basic unit economics (CAC vs. price ratio) — already computed, deterministically, inside
  `vps_scoring.py::_score_gtm_feasibility()`'s own ratio logic (currently feeding a hidden category score;
  the arithmetic itself — price ÷ CAC — is legitimately reusable as a Direct Consequence independent of
  whether it also feeds a score).
- Possibly hiring/runway scenarios — same category as burn/runway above, not yet built, would follow the
  same rule if built.

**Never defensible, explicitly forbidden as simulation output:**
- "Find a cofounder → startup becomes stronger."
- "Competition increases → viability falls."
- "Get five customers → venture potential rises X%."

These are exactly the causal-success claims a single VPS number implicitly made, and exactly the class of
statement the directive's own §1 origin story (adding 5 paying customers *decreased* VPS) demonstrated is
untrustworthy. 34A's `buildScenarioInsights()` already enforces this rule in practice — it reports
*direct*, arithmetic consequences and *qualitative* evidence-shift language, never a probability or
composite score of venture success.

**What-If's status, per explicit instruction:** generic What-If/scenario preview
(`components/idea-lab/WhatIfPanel.tsx`, `ScenarioComparison.tsx`) is expected to be removed from primary
Build navigation in a *later* phase, once the Hypothesis/Evidence loop is real (a founder should test
things in the real world and record what happened, not primarily preview hypothetical assumption changes).
**Not removed in this phase or the next — this document does not authorize that removal; it is scheduled,
not scoped, here.**

---

## 17. Paid-value / retention thesis (§19 of the directive)

**Required loop:** open SIE → see what matters now → do real-world work → return with results → SIE
remembers and interprets them → receive better next guidance → decide → repeat.

**Stress test — does the current + recommended architecture actually deliver this, or could it collapse
into "ChatGPT with forms"?**

*Where it already holds up:* `venture_missions` + `venture_model_updates` already give SIE genuine memory
a blank chat session cannot have — a specific, timestamped, queryable record of what a specific venture
tried and what changed. `WeeklyReview`/`VentureProgress` already surface *some* of this back to the founder
on return. This is real, structured memory, not marketing language.

*Where it would still collapse without the objects in §2:* the memory that exists today is shaped like a
changelog (state before → state after), not like a research notebook (what did we believe, what did we
test, what did we learn, why). A founder returning after two months sees *that* their assumptions changed,
but not *why* in a form richer than a fixed-template `_next_milestones()` sentence recomputed fresh from
the current snapshot — the reasoning behind a past recommendation is not preserved once superseded. **This
is precisely the gap Hypothesis + Evidence + Interpretation + Decision close**: without them, a founder's
tenth week with SIE reasons about the venture from the same recomputed-fresh state a first-time user would
see, plus a changelog — genuinely more useful than a blank chatbot, but not yet "SIE remembers *why*."
With them, SIE can answer "what did we try for this exact question before, and what happened" — a real
compounding-value claim a generic chat session structurally cannot make regardless of how good its prompt
is, because it has no durable, queryable object model at all.

**Verdict:** the paid-value thesis is achievable with the existing architecture as a foundation, but is
**not yet fully true** until Hypothesis/Evidence/Interpretation/Decision/Outcome exist as persisted,
linked objects (§23's "missing infrastructure"). Today's system is a good append-only changelog; it is not
yet a research notebook.

---

## 18. North star and product success (§20 of the directive)

**Product north star:** *meaningful founder decisions supported by evidence* — specifically, the count of
Decisions (§2.7) recorded with `evidence_considered` non-empty, over time, per active venture. Not
engagement, not time-in-app, not forms completed.

**Supporting operational metrics (instrumentable today or with the recommended schema, never invented
speculatively):**
- Hypotheses reaching `SUPPORTED`/`CONTRADICTED`/`MIXED` (a resolved state) per venture per month —
  instrumentable once Hypothesis exists; a rough proxy exists today via `venture_model_updates_count`
  (`VentureHistoryResponse.model_updates_count`, already computed).
- Tests completed with a recorded Outcome (not just a completed status) — the Outcome-linkage rate is the
  direct measure of whether the "return with results" half of the loop (§17) is actually happening, not
  just the "do the test" half.
- Weekly-active-ventures-with-a-recorded-Decision — a stricter, more honest version of a generic
  weekly-active-user metric, already partially instrumentable via the existing product-analytics event
  taxonomy (`docs/product/PRODUCT_EVENT_TAXONOMY_V1.md`) once Decision events are added to it.
- Return-visit interpretation reads — a founder opening an Interpretation SIE generated from evidence they
  submitted previously (directly measures whether "SIE remembers and interprets" is landing, per §17).

**Explicitly rejected as metrics:** number of clicks, raw time in app, forms completed, tests created
merely for activity (a Test created and immediately dismissed with no Evidence is not a success event, and
must not be counted as one).

---

## 19. LedgerFlow methodology walkthrough (§21 of the directive)

Applying this methodology on paper to the actual LedgerFlow test venture (id 3378, created during Phase
34A), starting from its real initial state: an AI accounts-receivable automation platform, target
"businesses / finance teams," no pricing/revenue/interviews/acquisition-strategy/retention/market-size
stated (per the directive's own reset assumption for this walkthrough, even though the live venture in the
repo does have an AI-inferred price point and target customer — the walkthrough below starts from the
directive's leaner baseline to show the methodology at its earliest, hardest point).

### Iteration 1 — bare idea

**What do we believe?** One FOUNDER CLAIM-level hypothesis exists implicitly in the description: *"Finance
teams at businesses experience meaningful pain from manually managing overdue invoices."* (PROBLEM family.)
No CUSTOMER hypothesis is specific enough yet — "businesses / finance teams" fails the §3 specificity bar.

**Highest-value unknown:** *Who, specifically, experiences this problem badly enough to act on it?* — this
gates every other hypothesis (willingness-to-pay, acquisition, economics all depend on knowing the
customer first, per §3's dependency rule) and currently has zero evidence.

**Recommended test:** Problem/customer interview — 15-20 conversations with finance-team members across a
couple of company-size bands, to both sharpen the customer hypothesis and start gathering PROBLEM evidence
simultaneously.

**Why:** Cheapest, fastest way to convert a FOUNDER CLAIM into either REPORTED PREFERENCE/OBSERVED BEHAVIOR
evidence, and to make the CUSTOMER hypothesis specific enough to test further (mirrors the existing,
unchanged `next_milestones` behavior: "Interview 20+ target customers to validate the problem is real" is
already the system's real first recommendation for a bare idea).

### Iteration 2 — 12 customer interviews conducted

**What changes:** New Evidence records, type mostly REPORTED PREFERENCE (a few OBSERVED BEHAVIOR if any
interviewee described a specific past workaround they built). Say 9/12 describe real, frequent
(multiple-hours-per-week) manual follow-up pain, concentrated among finance teams at companies with 50-500
employees managing SaaS/professional-services billing.

**Interpretation:** "Interview evidence supports the PROBLEM hypothesis, specifically for finance teams at
mid-market B2B service companies — narrower than the original 'businesses' framing." The CUSTOMER
hypothesis is refined (§3) to that segment, evidence is linked to the refined version. **What this does
NOT establish:** willingness to pay, adoption behavior, or whether the problem holds outside this segment
(directly mirrors the directive's own §11 worked example).

**New highest-value unknown:** *Would they actually adopt something new, or is this a "painful but
tolerated" problem?* (BEHAVIOR/ADOPTION family — genuinely different from the PROBLEM hypothesis just
supported, and not yet tested at all.)

**Recommended test:** Prototype/usability test or a landing-page test targeting the same segment,
specifically probing willingness to change existing workflow — not more problem interviews (§9's "declining
information value" rule: the problem hypothesis already has real support; more of the same evidence type
would not move it further).

### Iteration 3 — prototype/usability tests run

Say 4 of 6 invited prospects complete a guided prototype workflow; 2 explicitly say they'd need it to
integrate with their specific ERP before switching.

**Evidence:** OBSERVED BEHAVIOR (completed workflow) for 4; a new, specific integration constraint
(informational, not yet quantified) surfaces from 2.

**Interpretation:** "Adoption/behavior evidence is now moderately positive within the tested segment — most
completed the workflow unprompted. A new, previously unknown constraint (ERP integration) has emerged as a
potential adoption blocker for at least some of this segment." A **new hypothesis** is created (SIE-proposed,
per §3's "reactively" trigger): *"ERP integration compatibility is a prerequisite for adoption for a
meaningful subset of this segment."*

**Next unknown:** *Will anyone actually pay, and how much?* (WILLINGNESS-TO-PAY family — the highest-value
remaining unknown now that problem and basic adoption both have real support.)

**Recommended test:** Willingness-to-pay test / pre-sale — offer a paid pilot at a stated price to the same
qualified prospects.

### Iteration 4 — first paid pilot

2 of 5 qualified prospects accept a paid pilot at $1,500/month.

**Result → Evidence:** COMMITMENT-type evidence ("2/5 qualified prospects made a real purchase commitment
at $1,500/month") — not yet TRANSACTION until money actually moves, and not yet LONGITUDINAL OUTCOME.

**Direct modeled consequence (§16 simulation rule, legitimately calculable):** if both pilots convert to
paying, that's a modeled $3,000/month, $36,000/year — computed the same way `directConsequences.ts`
already computes MRR/ARR from price × customers, applied to this specific evidence rather than a
hypothetical.

**Interpretation:** "Willingness-to-pay hypothesis now has real, if early, COMMITMENT-level support at the
stated price point within the tested segment. This does not yet establish retention, whether this price
holds at a larger sample, or whether acquisition is repeatable beyond founder-led outreach to warm
prospects." (Directly mirrors the existing app-wide discipline of never letting early commercial evidence
imply more than it does — the same discipline `vps_guidance.py::_has_meaningful_commercial_scale()`
already enforces by *suppressing*, not just deprioritizing, "is the problem real" once real commercial
signal exists.)

**Decision:** SIE recommends "proceed with paid pilots before full build"; founder's actual choice and
rationale are recorded regardless of which way they go (§12) — say the founder agrees.

**Next unknown:** *Can acquisition work beyond the founder's own warm network?* (ACQUISITION family — now
the clear highest-value question, since problem/adoption/early-willingness-to-pay all have some support
and the venture has never tested a repeatable channel.)

### Iteration 5 — multiple paying customers

60 days later: both pilots convert to TRANSACTION (paying), plus 3 more customers acquired via a tested
outbound channel; 1 of the original 2 pilots churns after 45 days citing the same ERP-integration
constraint identified in Iteration 3.

**Outcome (§13):** the 60-day check-in on the Iteration-4 Decision — 4 active paying customers, 1 churned,
with a stated reason. This churn is itself new EVIDENCE, and it *specifically confirms* the ERP-integration
hypothesis from Iteration 3 rather than being a generic negative signal — the methodology's job here is
linking this churn to the *correct* existing hypothesis, not creating an undifferentiated "bad news" entry.

**Interpretation:** "Willingness-to-pay now has TRANSACTION-level support (4 paying customers) — the
strongest evidence type for this family. The outbound channel shows early, real repeatability (3 of 4 new
customers via one tested channel) — a genuine, if small-sample, signal on the previously-open ACQUISITION
hypothesis. The ERP-integration hypothesis gains its first piece of real supporting evidence (a churn
directly attributed to it) — worth testing directly rather than waiting for further incidental confirmation."

**Demonstrated point:** recommendations evolved at every iteration strictly because the evidence evolved —
Iteration 1's "talk to customers" became Iteration 5's "test the ERP-integration hypothesis directly and
watch retention on the surviving 3 customers," never because of a score crossing a threshold. **No score
appeared anywhere in this walkthrough.**

---

## 20. Failure modes / adversarial cases (§22 of the directive)

| Case | Required safe behavior |
|---|---|
| Founder lies/exaggerates | System cannot detect a lie; it can and must preserve the *type* of evidence honestly (a FOUNDER CLAIM stays a FOUNDER CLAIM, never silently upgraded to TRANSACTION because the founder typed a big number — same discipline `idea_structuring.py` already enforces for validation fields: only a verified, quoted claim can become `user_provided`). |
| Tiny samples | Evidence retains `sample_size`; Interpretation must name the sample size in its own language ("among 3 interviewees") rather than implying broader support — never suppressed, never inflated. |
| Biased interview sample | `segment`/context field lets Interpretation flag "all interviewees came from the founder's own network" as a stated limitation, not silently generalized. |
| Contradictory evidence | §5 — first-class, never averaged away. |
| Vanity metrics | A metric not tied to a Hypothesis (e.g. raw signups with no linked willingness-to-pay or retention hypothesis) is recorded as Evidence but Interpretation must explicitly say what it does *not* establish (§9/§11's "what this will not prove" discipline applied after the fact). |
| Stale evidence | §5 — surfaced as a caveat, recency computed from date. |
| Founder ignores recommendations | Fully allowed (§13/§15) — the Test/Decision the founder actually took is recorded as-is; SIE's original recommendation is preserved for later comparison, never deleted. |
| Founder pivots completely | New Hypotheses created for the new direction; old ones move to `RETIRED` (§3), never deleted — the venture's full history remains legible as "here's what we tried before this pivot." |
| Multiple customer segments behave differently | `segment` field on Evidence + segment-specific disagreement handling (§5). |
| Revenue exists but retention is poor | Two different hypothesis families (WILLINGNESS-TO-PAY vs. RETENTION) — a strong TRANSACTION signal on one does not imply anything about the other; Interpretation must keep them separate, exactly as Iteration 5 above does with churn. |
| Users love product but buyer won't pay | Distinguishes BEHAVIOR/ADOPTION (the end-user) from WILLINGNESS-TO-PAY (the economic buyer) as separate hypotheses/families when they're different people — a real, common B2B failure mode the family taxonomy (§3) is deliberately granular enough to represent. |
| Strong demand but terrible economics | ECONOMICS family hypothesis is independently tracked from PROBLEM/CUSTOMER — a strongly `SUPPORTED` problem hypothesis never implies anything about an untested or `CONTRADICTED` economics hypothesis. |
| Founder has real traction before ever using SIE | At venture creation, SIE should classify existing stated facts directly into the strongest applicable evidence type immediately (a founder who states "$50K MRR, 40 customers" on day one gets TRANSACTION-level evidence from the start, not a fabricated "early-stage" framing) — mirrors `_has_meaningful_commercial_scale()`'s existing behavior of fully suppressing early-stage-only recommendations once real scale is stated. |
| Company already operating when entered | Same as above — the Build lifecycle (§14) already supports entering directly at `OPERATING`; nothing forces a founder through earlier states. |
| AI extracts evidence incorrectly | Founder-correction mechanism (§15) is the safety valve; every AI-derived (`SIE_INFERRED`) classification must be presented as correctable, never as settled fact, mirroring `idea_structuring.py`'s existing "ai_inferred... never as fact" framing. |
| AI recommendation is bad | The founder can dismiss/override unconditionally (§13); a bad recommendation is a preserved, visible data point, not hidden — this also means bad recommendations are eventually auditable across many ventures, a real quality-improvement mechanism the current fixed-template system doesn't get for free. |
| Insufficient data | Default, honest state (§7's `STILL_INSUFFICIENT`) — never blocks the founder from proceeding (§13). |
| Over-testing / endless validation | §9/§11's "declining information value" rule — Interpretation explicitly says when a hypothesis is already as supported as this evidence type can make it. |
| Premature fundraising | Fundraising is explicitly non-terminal and never gated behind a score (§14, §16 of the earlier directive/34A); SIE may recommend "consider fundraising" as one Decision option among many, never as an implied milestone every venture should reach. |

---

## 21. Repository gap analysis (§23 of the directive)

| Subsystem | Classification | Why |
|---|---|---|
| Venture model (`modeled_ventures`, `VentureResponse`) | **KEEP** | Correct container for current belief state; no structural defect found. |
| Venture assumptions (`VentureAssumptions`, flat typed fields) | **ADAPT** | Becomes the seed for Hypothesis decomposition (§2.2); the fields themselves stay — they're still the right home for "current stated value," Hypotheses add the testable-proposition layer on top. |
| Six-category Idea Lab model (`vps_scoring.py::VPS_CATEGORIES`) | **ADAPT** | Category structure and `basis` text generation are reusable inputs to Hypothesis families (§3) and `VentureUnderstandingPanel` (34A) already reorganized them around knowledge states, not scores — keep that framing, map categories onto hypothesis families loosely, don't force a rigid 1:1. |
| Retained VPS backend internals (`compute_vps`, `vps`, `path_to_stronger`, `sole_uncorroborated_category`) | **HIDE** (unchanged from 34A) | Already not founder-facing; no reason to expose, no reason to delete given coupling risk documented in 34A's own report. |
| `validation_gaps` | **ADAPT** | Direct precedent/input for Unknown generation (§2.3) scoped to the Validation category; generalize the pattern to other hypothesis families rather than rebuilding. |
| `next_milestones` / `_next_milestones()` | **ADAPT** | Direct precedent for Unknown ranking (§2.3/§7); its priority-tier mechanism is the right shape for the internal deterministic ranking recommended in §7, generalized to operate over persisted Hypotheses. |
| Recommendation resolver (`resolveIdeaLabNextStep.ts`, `PrimaryCommandCard.tsx`) | **ADAPT** | Its Case A/B (no-active-action vs. active-action) UI logic is exactly right and should be preserved; its *input* changes from "raw next_milestones + mission title" to "ranked Unknown + linked Test," per §7/§9. |
| Missions/actions (`venture_missions`) | **ADAPT** | Becomes the Test object (§2.4) with a widened `mission_type` taxonomy and a new `target_hypothesis_id` column — additive schema change, not a new table. |
| `CaptureWhatHappened` + `captureSignals.ts` | **ADAPT** | The single most valuable existing asset for this methodology — its `ProposedSignal` shape already *is* a structured-evidence draft; it needs a persistence target (the new Evidence table, §2.5) instead of discarding its output after each capture. |
| `WeeklyReview` | **ADAPT** | Its "what you did / what you learned / what changed" shape is the right retrieval surface for Outcome check-in prompts (§2.8) once Outcome exists; logic mostly reusable. |
| `VentureProgress` / `VentureHistory` | **ADAPT** | `venture_model_updates`' before/after-snapshot discipline is the right append-only pattern to extend to Decision/Outcome records; the existing event-type union (`action_added`, `learning_recorded`, `action_completed`, `model_updated`) needs two new event types (`decision_recorded`, `outcome_recorded`), not a new history mechanism. |
| What-If / scenario architecture (`WhatIfPanel.tsx`, `ScenarioComparison.tsx`, `scenarioInsights.ts`) | **DEFER** | Not removed now (explicit instruction, §18/§16 above); scheduled for removal from primary Build navigation once the real evidence loop exists. `scenarioInsights.ts`'s *shape* (strengthened/weakened/unknown/new-questions) is ADAPTed into Interpretation (§2.6) even as the What-If UI itself is deferred for later removal. |
| Fundraising (`FundraisingSimulator` family) | **KEEP** | Deterministic, explicit-assumption simulation exactly matching §16's simulation rule; no changes needed. |
| Graduation (`venture_graduations`, `VentureGraduation.tsx`) | **KEEP** | No incompatibility found (§14); `GraduateVentureRequest.trigger` is the direct template for the generalized Decision object (§2.7/§10). |
| Venture → Startup handoff (`ventureToStartupHandoff.ts`) | **KEEP** | Session-storage description handoff is fine as-is; future connection point documented in §15 without merging. |
| Learn/playbooks (`resourceMap.ts`, `missionSuggestions.ts`) | **ADAPT** | `missionSuggestions.ts`'s per-milestone `why` field is a real, working precedent for §7's "why it matters" output; extend its keying from exact-milestone-string match to hypothesis-family + test-type once those exist, rather than growing the fixed string table indefinitely. |
| Public venture snapshot / sharing (`ShareVentureSnapshot.tsx`, `VentureSnapshotCard.tsx`) | **KEEP** | Already VPS-free (34A); its "Evidence so far" / "Proving next" sections are already evidence-forward in spirit and compatible with this methodology without further change. |
| AI extraction (`idea_structuring.py`) | **ADAPT** | Its provenance-verification pattern (§12) is the template for Hypothesis-suggestion extraction; the same `_quote_is_verifiable()`-style fail-closed discipline should gate any future SIE-suggested Hypothesis or Evidence classification. |
| AI analysis calls used in Build generally | **KEEP the discipline, ADAPT the scope** | No new AI *system* is being created by this document; future Interpretation generation (§9) should follow the exact same "deterministic template first, LLM only where templates can't honestly cover nuance" discipline `vps_guidance.py` already established for `next_milestones`/`validation_gaps`. |

**What already exists:** a working, if fresh-computed-every-time, version of nearly the entire loop —
extraction with real provenance discipline, a real (if coarse) test taxonomy, real append-only history,
real founder-authority preservation, real evidence-classification logic (just not persisted), a real
non-linear lifecycle, real deterministic simulation boundaries.

**What can be repurposed:** almost everything in the ADAPT column above — this methodology is
substantially an act of *naming and connecting* things that already exist (Hypothesis ≈ decomposed
assumptions + missing persistence; Test ≈ `venture_missions` + widened taxonomy; Unknown ≈
`next_milestones`/`validation_gaps` generalized; Decision ≈ `GraduateVentureRequest.trigger` generalized).

**What is genuinely missing:** a persisted **Evidence** table (§2.5 — the single biggest gap: the
classification logic already exists in `captureSignals.ts` and is discarded today), a persisted
**Hypothesis** table (§2.2), a persisted **Decision** table generalized beyond graduation (§2.7), a
persisted **Interpretation** record (§2.6 — `scenarioInsights.ts` is a strong prototype of its *shape* but
nothing like it runs against real evidence today), and an **Outcome**/check-in mechanism (§2.8 — currently
entirely absent; no part of the system prompts or records a later follow-up on a past Test or Decision).

**What should not be built:** a new score of any kind (locked, §2/§18); a rigid, mandatory hypothesis
checklist forcing every family for every venture (§3, §6); a visible numeric prioritization formula (§7); a
second, parallel "unknowns" table that could drift from Hypothesis state (§2.3); a wholesale rewrite of
Missions/History/Graduation/Fundraising, all of which are sound (§21 KEEP/ADAPT rows above).

---

## 22. Implementation plan (§24 of the directive)

The directive's own suggested phase labels are adopted as-is — the audit did not surface a better ordering.

- **34C — architecture mapping / contracts.** Turn §2's object definitions into actual Pydantic
  models/TypeScript types and draft (not yet applied) migration SQL for the new tables identified in §21
  ("genuinely missing"): `hypotheses`, `evidence`, `decisions`, `interpretations`, `outcomes`. Define the
  exact additive columns on `venture_missions` (`target_hypothesis_id`, widened `mission_type` CHECK).
  Still no running code changes to founder-facing behavior.
- **34D — smallest end-to-end intelligence loop.** Wire exactly one full loop, real, for one venture at a
  time: capture an observation → persist it as Evidence (finally not discarding `captureSignals.ts`'s
  output) → link it to a Hypothesis (SIE-proposed, founder-confirmed) → generate one Interpretation
  (reusing `scenarioInsights.ts`'s shape against real evidence) → surface one ranked Unknown using the
  existing `_next_milestones()`-style tiering generalized over persisted Hypotheses. No UI redesign — bolt
  this onto the existing Overview/Model tabs first.
- **34E — simplified founder UX.** Once the loop is real, redesign the founder-facing surfaces around the
  six questions in §1's table, and only then reconsider removing What-If from primary navigation (§16).
- **34F — longitudinal learning/history.** Build the Outcome/check-in mechanism (§2.8) — the piece with
  literally zero current-system precedent — and extend `WeeklyReview`/`VentureProgress` to surface it.
- **Later** — external evidence sources, richer deterministic simulation tools (runway/hiring scenarios per
  §16), any accelerator/investor-facing intelligence built on top of a now-real evidence history.

**Governing rule, restated because it is the single most important sequencing constraint:** prove one
complete intelligence loop (34D) before any large UI rebuild (34E). Building the full six-question UX
around a loop that doesn't yet persist Evidence/Hypothesis/Interpretation would recreate exactly the
"ChatGPT with forms" risk identified in §17.

---

## 23. Summary of what this document does and does not authorize

This document defines methodology and contracts only. It does not create database tables, does not change
any founder-facing UI, does not modify VPS internals (already frozen/hidden per 34A), does not modify SPS
or Analyze, and does not introduce any new score. It is the input to Phase 34C, not itself an
implementation.
