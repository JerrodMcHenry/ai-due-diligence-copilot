# SIE Historical Intelligence Retrieval V1

Phase 39A. **Pure design/audit phase — nothing in this document has been implemented.** No table, no column,
no migration, no endpoint, no frontend change, no AI call. This document answers one question: when SIE is
helping a founder make a decision today, what from this company's own history is genuinely relevant enough
to surface — and what is the smallest, most defensible architecture that could ever show it?

## 1. Product thesis

Generic AI can already say "hiring often costs more than expected." It cannot say "six months ago you
modeled this exact hire, expected $18,750/month, actual expenses later exceeded that, and you attributed
part of the difference to contractor overruns" — because that requires this company's own persisted history,
which no generic model has access to. That is the entire value proposition of this phase: identify the
narrow set of historical facts a generic AI structurally cannot know, and surface only those, only when they
materially improve a current decision — never as an automatic recommendation, never as a score, never as an
invented lesson.

## 2. Systems audited

### Build

- **`venture_missions`** — an ACTIVITY, never evidence (confirmed directly from its own model docstring).
  Carries `mission_type` (`Literal`, ~20 values: `pricing`, `pricing_test`, `willingness_to_pay_test`,
  `customer_discovery`, `paid_pilot`, etc.) — a real, already-populated decision-type taxonomy. `status`
  (`active`/`completed`/`dismissed`) and free-text `learning_summary`.
- **`venture_evidence`** — `evidence_type` (`founder_claim`/`reported_preference`/`observed_behavior`/
  `commitment`/`transaction`/`longitudinal_outcome`/`external_source`), `relationship`
  (`supports`/`contradicts`/`mixed`/`neutral`), `related_mission_id`, `related_decision_id`,
  `superseded_by_id`. No product/segment/company-stage field of any kind.
- **`venture_decisions`** — `sie_recommendation`, `sie_reasoning`, `founder_choice`, `founder_rationale`,
  `evidence_ids[]`, `related_mission_id` (optional), `supersedes_decision_id`. **No `decision_type` field at
  all** — the only way to infer a decision's "type" is through its optional `related_mission_id`'s own
  `mission_type`.
- **Recommendation engine** (`app/ai/build_recommendation.py`) — `_FUNNEL_ORDER = ["problem_evidence",
  "commitment_evidence", "transaction_evidence", "retention"]`, `_determine_focus_stage()` computes a
  `stage_mix` (`supports`/`contradicts`/`mixed`) per funnel stage from CURRENT evidence only.
- **The current/historical distinction already exists, built and shipped (Phase 34G-A):** `superseded_by_id
  IS NULL` is the filter the recommendation engine's own stage_mix computation already uses for "current
  decision-dominant evidence" (confirmed directly in `resolve_venture_evidence_for_owner()`'s own docstring:
  "Distinguishes EXISTS from CURRENTLY DECISION-DOMINANT"). A superseded row is never edited or deleted —
  `list_venture_evidence_for_owner()` returns it unfiltered, forever. **This is precisely the CURRENT vs.
  HISTORICAL distinction §10 of this phase's directive asks for — it does not need to be invented, only
  reused.**
- **Outcome** = a `venture_evidence` row with `evidence_type='longitudinal_outcome'` and `related_decision_id`
  set — confirmed to require an explicit, manual founder action; there is no automatic mechanism that
  guarantees every decision eventually gets an outcome recorded.
- **`learning_summary`** (on `venture_missions`, update-in-place) — a free-text field with no structured
  content; not itself retrievable as a discrete fact, only as prose.

### Finance

Already exhaustively audited across Phases 38D-A/B/C this session. Confirmed again for this phase: the
chain `scenario/plan → commitment → frozen expected_monthly → actual (via comparison, computed) →
founder_explanation` is real, fully persisted (except the actual/variance, deliberately never persisted —
38D-B), and is the **strongest historical chain in the entire codebase** — see §12.

### Analyze

- **`app/models/scoring.py`/`app/models/sps_v3.py`** — `PillarScoreBreakdown` (`confidence`,
  `evidence_coverage`, subscores), `StartupIntelligenceScore`. Confirmed by direct grep: **neither file
  contains any reference to `venture_id`/`modeled_venture` at all.** Analyze operates entirely on the
  separate `analyses`/`startups` domain.
- **The only structural bridge** between the Build/Finance/Decision domain (keyed by `modeled_ventures.id`)
  and the Analyze/SPS domain (keyed by `startups.id`) is `venture_graduations` — a `UNIQUE venture_id ↔
  startup_id` row, created only when a founder explicitly graduates a venture. **Most ventures never have
  one.** Confirms, by direct audit rather than assumption, the directive's own default: SPS is evaluation
  context, structurally isolated from the Build/Finance history this phase is designed to retrieve.

### Command Center

- `CurrentQuestion` (`app/models/venture_missions.py`) carries `mission_id`, `question_text`,
  `why_it_matters` — no explicit decision-type field of its own, but `mission_id` joins to
  `venture_missions.mission_type`, so a structural decision-type signal IS available for the Build side of
  Command Center's own current-question surface.
- `CommandCenter.tsx`/`CurrentQuestionCard.tsx`/`commandCenterCrossSystem.ts` (38B/38C) already establish the
  precedent this phase reuses throughout: pure, deterministic, client-side derivation functions; a hard cap
  (38C capped at 2 simultaneous cross-system connections); an explicit "Why SIE is showing this ▾"
  traceability disclosure; silence as the default render.
- **Command Center currently carries no Finance-side "what is the founder currently modeling" signal at
  all** — that signal exists only inside `FinanceOverview.tsx`'s own hire/plan-creation and preview flows,
  which Command Center never reads from. This matters directly for §15/§20 below.

## 3. Historical intelligence — definition

A historical fact qualifies as "historical intelligence" only when **all** of the following hold:

1. It concerns the SAME structural kind of decision the founder is making right now (not merely a similar
   word, topic, or vague timeframe).
2. It has already produced at least one comparable, persisted OUTCOME fact — not just a plan or intention.
3. It can be stated without inventing a causal claim beyond what was actually persisted.
4. Silence is preferred over a weak, semantically-similar-but-structurally-unconnected match.

Old financial snapshots on their own, old SPS values, unrelated evidence, and "you previously had low
runway" do not qualify — none of them are anchored to the SAME decision the founder is making now, and none
of them, alone, produce more insight than "the past exists."

## 4. History informs, does not control

Load-bearing product rule, restated so it cannot casually collapse in a later phase:

**RELEVANT HISTORY ≠ CURRENT RECOMMENDATION.**

The retrieval surface may state only what was expected, what happened, and what the founder said explained
it — three independently persisted facts, presented as facts. It must never conclude "therefore you
should/shouldn't do this again." That conclusion would require CURRENT-STATE reasoning (today's cash
position, today's priorities, today's market) that a historical fact alone cannot supply, and building it
would silently reintroduce exactly the kind of manufactured-relevance/causal-overreach this whole document
exists to prevent. The architecture enforces this by construction: retrieval's own output is a struct of
`{expected, actual, explanation}` — there is no field for "recommendation," so a future engineer would have
to add a NEW, clearly-separate field to reintroduce this, not overload an existing one.

## 5. Relevance model

**A. Entity/object match** — the strongest, most defensible signal available today. Finance's
`plan_snapshot[].kind` (`hire`/`revenue_target`/`expense_change`) is an exact, already-populated, machine
verifiable discriminator. Build's `mission_type` is the closest equivalent on that side, though weaker (see
§11).

**B. Decision-type match** — for Finance, subsumed by A (the `kind` field IS the decision type). For Build,
requires joining through `related_mission_id` to `mission_type`; a decision or evidence row with no
`related_mission_id` has no decision-type signal at all.

**C. Financial exposure match** — audited and rejected as a V1 criterion. No existing rule in this codebase
defines a "materially similar" dollar threshold (mirrors the exact finding Phase 38B made about runway
thresholds: none exists, none should be invented). Financial exposure is visible IN the surfaced fact itself
(the expected/actual dollar figures) but is not used to GATE eligibility.

**D. Build-stage/learning-question match** — `_FUNNEL_ORDER`'s four stages are a real, usable signal for any
future Build-history retrieval (matching current funnel stage to a prior mission/evidence row's own stage).
Not exercised by the recommended 39B scope (Finance-only), but available for a future Build-history phase.

**E. Temporal relevance** — **deliberately NOT modeled as decay in V1.** The directive's own instruction
("do NOT automatically assume old = irrelevant") is reinforced by a real audit finding: `modeled_ventures`
stores exactly one CURRENT, mutable `stage` value — there is no per-event historical snapshot of what stage
the company was in when a given commitment/evidence row was created. SIE cannot honestly compute "was the
company meaningfully different back then" at all today. Rather than fake a proxy (e.g., silence anything
older than N months, which the directive explicitly forbids as an assumption), V1 shows the most recent
qualifying match regardless of age and says nothing about temporal distance. This is a documented limitation
(§21), not a silent gap.

**F. Product/segment context** — audited: no structured field exists anywhere (`venture_evidence`,
`venture_decisions`, `venture_financial_commitments`) for product version, customer segment, or business
model. SIE cannot distinguish "this hire was for the old product" from "this hire is for the current one."
Documented as a real limitation (§21) rather than pretended away — retrieval must never claim segment/product
continuity it cannot verify.

**G. Outcome quality hierarchy** — real and justified, but expressed as **eligibility tiers**, not a score
(see §6):
- Tier 1 (strongest): commitment → actual (observed) → founder explanation.
- Tier 2: commitment → actual (observed), no explanation.
- Tier 3 (not eligible, §7): commitment with no observed actual yet.
- Not eligible at all: a plan/scenario with no commitment ever made.

## 6. Is a relevance score needed?

**No — not for the recommended 39B scope.** Evaluated three approaches:

**Option A — deterministic eligibility rules + ordered precedence.** Explainability: total (every inclusion/
exclusion traces to a named boolean/enum check). False-positive risk: very low (exact type match only).
False-negative risk: real but deliberately accepted (silence over guessing). Deterministic testing: trivial
— pure functions, exhaustively unit-testable exactly like 38D-B's own comparison function. Cost/latency:
negligible (one extra SQL read of already-existing rows). Future scalability: straightforward to widen one
`kind`/one domain at a time without restructuring.

**Option B — an internal (never founder-facing) relevance score.** Only useful once MULTIPLE, structurally
different candidate types (e.g., a Finance match AND a Build match) could both be eligible simultaneously and
need blending into one ranked list. Audited honestly: if the score's own inputs are just the same
boolean/enum eligibility facts Option A already uses, "Option B" is really "Option A plus an explicit
precedence rule" — not a materially different risk profile, just an ordering refinement. A genuine numeric
score (weighted, tunable) is not justified until a second retrievable domain actually exists and proves hard
to order with a simple rule table. **Deferred, not adopted, for 39B.**

**Option C — deterministic candidate generation, then AI ranks/selects/phrases the result.** Rejected for
39B: the candidate pool this phase's own recommended scope ever produces is 0 or 1 items — there is nothing
for a ranking step to rank. Introducing an LLM call here would add cost, latency, and non-deterministic
testability for zero benefit, directly contradicting this entire session's own established Finance-domain
discipline (no AI, pure functions, exhaustive tests). Named as a legitimate FUTURE option only once retrieval
spans enough simultaneous domains that deterministic ordering genuinely breaks down.

**If a score is ever introduced, it must remain purely internal — never rendered as a number, never phrased
as "relevance: 82" or equivalent, in any founder-facing surface.**

## 7. Silence rule

Silence (render nothing) when any of the following hold:

- No prior commitment shares the current decision's own structural kind (Cases A, X).
- The only prior match is a plan/hire that was never committed (Case C) — a plan alone is hypothetical, per
  38D-A's own "no automatic commitment" doctrine; it is not historical fact.
- A matching prior commitment exists but has zero observed actuals yet (`comparison_status ===
  "awaiting_actuals"`, Case D) — there is no outcome yet, only an unresolved current bet; that belongs to the
  venture's own live "Committed" panel (present tense), not a historical-intelligence surface (past tense).
- More than one equally-eligible strong candidate exists — never dump all of them (Cases M, N); reduce
  deterministically to the single most recent (`ORDER BY committed_at DESC`), a field that already exists,
  never an invented tie-break.
- The current decision's own type cannot be identified structurally (no `mission_type`, no plan `kind`) —
  silence rather than a semantic guess (Case X).
- The only available history is Analyze/SPS data (Case Q) — no structural link connects it to a specific
  decision (§2, §14).
- A structurally relevant prior evidence row is presently a live, still-blocking contradiction (Case R) — the
  existing `BlockingEvidenceItem` UI already surfaces this fact prominently; historical retrieval must not
  compete with or duplicate that existing, higher-priority surface. Silence from history's own side; defer
  entirely to the existing mechanism.
- Relating the current decision to a candidate would require guessing a segment/product/stage relationship
  SIE does not structurally know (§5F) — never guess.

Silence is a first-class, expected, majority-case output — not a fallback or an error state.

## 8. Provenance

Every surfaced clause maps to exactly one named, persisted field — mirrors Command Center's own established
"Why SIE is showing this ▾" pattern (38B/38C):

| Surfaced clause | Source |
|---|---|
| "Your previous engineering hire was modeled at $18,750/month." | `venture_financial_commitments.plan_snapshot[]` (the matched item's own frozen input values) |
| "Actual expenses later exceeded the committed expectation." | The historical commitment's own comparison result (`build_commitment_comparison()`, computed fresh, never stored) |
| "You attributed part of the difference to contractor overruns." | `venture_financial_commitments.founder_explanation` |

These three clauses are never collapsed into a single sentence like "your previous hire failed because
contractor costs were too high" — that would silently convert `FACT + FACT + FOUNDER INTERPRETATION` into an
`SIE CAUSAL CLAIM`, which nothing in the persisted data justifies. Each clause is rendered as its own
sentence, sourced from its own field, exactly as the table above shows.

## 9. Founder attribution

Preserved by construction, not by convention: retrieval's own output struct has three separate slots —
`expected`, `actual`, `explanation` — mirroring `FinancialCommitmentResponse`'s own three separate fields
(`expected_monthly`, the comparison's derived actual, `founder_explanation`) exactly. There is no "what SIE
learned" slot anywhere in the design. If a future phase wants to add SIE's own derived conclusion, it would
require adding a distinctly-labeled fourth field with its own explicit provenance (`sie_calculated` or
`sie_inferred`) — never overloading or paraphrasing the founder's own slot. No inferred founder belief is
ever created; the explanation slot is rendered VERBATIM or not at all (Case V).

## 10. Contradictions — current-dominant vs. historically-relevant

No new mechanism needed — Phase 34G-A's own `superseded_by_id` distinction already IS this distinction (§2):

- **CURRENT DECISION-DOMINANT EVIDENCE** = `superseded_by_id IS NULL`, the exact filter the recommendation
  engine's own `stage_mix` computation already uses.
- **HISTORICALLY RELEVANT EVIDENCE** = any row, superseded or not, read via the existing unfiltered
  `list_venture_evidence_for_owner()`.

Retrieval must never resurrect a superseded row as though it were current truth — when a matched historical
row has `superseded_by_id IS NOT NULL`, it must be labeled explicitly ("this was later superseded/resolved")
rather than presented bare (Cases J, S). Superseded evidence is never hidden or deleted merely because it was
superseded — it remains available to historical retrieval, correctly framed as history, forever.

## 11. Build history

The chain "we tested X, observed Y, chose Z, and outcome Q followed" is **structurally supported end-to-end**
via existing FKs (`mission → evidence.related_mission_id → decision.related_mission_id → outcome
evidence.related_decision_id`), all already populated by the normal Build flow with zero inference from
timestamps or text similarity required. The one real gap: **the final "outcome" link is optional and
manual** — nothing guarantees a founder ever records a `longitudinal_outcome` row for a given decision. A
Build-history retrieval phase can therefore honestly reconstruct the full chain only for decisions where an
outcome was actually recorded — a real, but not blocking-for-this-phase, limitation (39B does not touch
Build history at all; see §22).

## 12. Finance history

The strongest chain in the codebase, and the basis for the recommended 39B scope:

`venture_hire_plans`/`venture_financial_plans` (mutable, live) → `venture_financial_scenarios` (hypothetical,
never historical) → `venture_financial_commitments` (frozen `plan_snapshot` + `expected_monthly`, append-only,
38D-A) → comparison (`build_commitment_comparison()`, computed fresh, 38D-B) → `founder_explanation` (mutable,
founder-authored, 38D-C).

**Decision types identifiable structurally today:** hiring (`kind: "hire"`), revenue target (`kind:
"revenue_target"`), expense change (`kind: "expense_change"`) — directly from `plan_snapshot[].kind`, and
combinations (a single commitment's `plan_snapshot` may contain more than one kind at once, from a bundled
scenario commitment).

**A genuine, previously-undocumented limitation surfaced by this audit:** `expected_monthly` is a BLENDED
MONTHLY AGGREGATE across every item in a commitment's own `plan_snapshot` — `project_monthly_cash_flow()`
produces one `revenue_cents`/`expenses_cents`/`ending_cash_cents` figure per month across ALL active plan
items combined, never itemized per source id. For a commitment that bundled a hire together with a revenue
target or expense change, the aggregate expected-vs-actual figures cannot be honestly attributed to the hire
alone. **Consequence for retrieval:** the ITEMIZED `plan_snapshot` entry (role, salary, burden) is always
safe to quote regardless of bundling, but the AGGREGATE expected/actual/variance figures are only safely
attributable to the matched decision type when the historical commitment's `plan_snapshot` contains exactly
one item. 39B should require (or strongly prefer) single-item historical commitments for the full
three-slot claim, and fall back to itemized-input-only framing ("You previously modeled hiring a Product
Designer at $10,020/month" with no expected-vs-actual claim) when the best match is bundled. This is a
structural, not cosmetic, finding — documented as BLOCKING for the multi-item case (§21).

## 13. Decision history

`venture_decisions.related_decision_id` on a commitment (introduced 38D-A) is **optional** — most
commitments will never have one, and nothing in this phase should assume otherwise (per the directive's own
explicit instruction). When present, it enables one additional, clearly-labeled slot: SIE's original
recommendation and the founder's actual choice, read verbatim, never collapsed into "the founder followed/
ignored SIE" (Case T; §14 of the 38D architecture doc already established this exact non-collapsing rule).
`venture_decisions` itself has no `decision_type` field — its own type, if needed, could only ever come from
its OPTIONAL `related_mission_id`'s `mission_type`, meaning a decision with neither a related mission nor a
related commitment has no discoverable type at all. This narrows, rather than broadens, what decision-history
retrieval can safely claim — confirmed by audit, not assumed.

## 14. Analyze/SPS boundary

Confirmed by direct audit (§2): SPS/pillar scoring has no structural connection to `modeled_ventures` at all
except the optional, one-directional `venture_graduations` link. There is no mechanism by which "your SPS
used to be 61, now it's 68" could be tied to a SPECIFIC decision the founder is making — the score isn't
computed FROM the venture's own Build/Finance history in the first place; it's computed from a separately
submitted `analyses` row. **Default assumption confirmed correct: SPS is evaluation context, not historical
learning.** No compelling decision-linked use case survived this audit. Retrieval built on this document
must not use SPS/pillar values as a relevance signal.

## 15. Current-decision identification

Audited signal availability:

- **`CurrentQuestionCard`/Command Center** — knows `mission_id` → `mission_type` (Build decision-type signal
  only). Carries no Finance-modeling signal at all.
- **`venture_decisions`** — knows `founder_choice`/`related_mission_id` only at the moment a decision is
  actually recorded (i.e., after the fact, not while the founder is still modeling).
- **Finance plan/hire/scenario/commitment creation flows** (`FinanceOverview.tsx`) — the ONLY place a
  Finance-typed "the founder is right now considering a hire" signal exists, and only transiently, at the
  moment of creating or previewing a hire/revenue/expense plan.

**Recommendation: trigger contextually at the specific Finance modeling surface (Option B/"by a specific
decision surface" from the directive's own list), never globally on Overview or inside Command Center.**
Global/Overview placement was explicitly evaluated and rejected: Command Center has no Finance-modeling
signal to key off today (would require new wiring this phase does not propose), and dumping historical
intelligence onto Overview regardless of what the founder is currently doing is exactly the
"generic AI insights wall" anti-pattern §16 of the directive warns against.

## 16. UX model (design only)

```
Relevant history

Last time you modeled an engineering hire:
- Expected added cost: $10,020/month
- Actual expenses later exceeded the committed plan
- You attributed part of the difference to contractor overruns

Why is SIE showing this ▾
```

Compact, single card, appears only at the moment of modeling the same kind of decision. No timeline, no
company-memory feed, no "AI insights" wall, no historical dashboard, no lessons score — all explicitly
rejected, matching the directive's own list.

## 17. Traceability

The "Why is SIE showing this ▾" disclosure (identical pattern to Command Center's own 38B/38C precedent)
reveals the structural relationship, never hidden AI reasoning:

```
Current action:      Modeling a planned employee hire
Historical match:    Previous committed employee hire
Sources:              Committed plan #35
                       Actual snapshot — [the aligned month's own as_of_date]
                       Founder explanation — recorded [explanation_recorded_at]
```

## 18. Generic AI test

Applied throughout this document. High-value (passes): "six months ago you modeled this exact type of
decision, expected X, actual Y occurred, and you recorded Z as the reason" — no generic model can know this
without the founder manually reconstructing their own company's history. Low-value (rejected): any generic
statement a founder could get from ChatGPT with one prompt ("hiring can cost more than expected," "watch your
burn rate"). Every proposed behavior in §16/§22 passes this test — each one requires this specific company's
own persisted `plan_snapshot`/comparison/`founder_explanation`.

## 19. Test scenarios

| Case | Result |
|---|---|
| A. First-ever hire, no history | Silence |
| B. Second hire, prior committed hire + actuals + explanation | Full 3-slot candidate |
| C. Second hire, prior plan only, never committed | Silence — a plan is hypothetical, not historical fact |
| D. Prior commitment, no actuals yet | Silence — nothing observed yet; belongs to the live "Committed" panel, not history |
| E. Prior commitment + actuals, no explanation | Show Expected + Actual only; omit the explanation slot entirely, never fabricate one |
| F. Prior commitment + actuals + explanation | Strongest case — full 3-slot candidate |
| G. Current revenue target, prior revenue-target commitment | Eligible — same structural `kind` |
| H. Current hire, prior revenue-target history only | Silence — no structural relationship between the two kinds |
| I. Prior Build pricing test + evidence, current pricing decision | Eligible candidate IF structurally linked via `mission_type`; structurally weaker than Finance (§11) — out of 39B's own scope regardless |
| J. Prior pricing evidence was superseded | Shown as historically relevant, explicitly labeled "later superseded" — never as current truth |
| K. Company stage differs significantly from the historical event | Cannot be safely evaluated at all today — no per-event historical stage snapshot exists (§5E/§21); documented limitation, not silently ignored |
| L. Founder explanation vs. what variance alone might tempt SIE to infer | The founder's own text is the only explanation ever shown, verbatim; SIE never generates or substitutes its own inference |
| M. Multiple relevant historical events | Cap at 1, most recent by `committed_at` |
| N. Ten vaguely related events | Never dumped — same cap, same "most recent, exact type match" rule filters to 1 |
| O. No strong match | Silence |
| P. `related_decision_id` present on the matched commitment | Defensible extra value: an additional slot showing SIE's original recommendation vs. the founder's actual choice, verbatim, only when this optional FK is populated |
| Q. History contains only SPS changes | Silence — no structural link (§14) |
| R. History contains a still-live, decision-dominant contradiction | Silence from history's side — defer entirely to the existing `BlockingEvidenceItem` UI, never duplicate it |
| S. History contains a superseded contradiction | Same as J — historically relevant, current-truth framing prohibited |
| T. Founder disagreed with SIE historically, proceeded anyway | Both `sie_recommendation` and `founder_choice` shown as two separate, verbatim facts — never collapsed into "followed/ignored" |
| U. Result was BETTER than expected | Same eligibility rule regardless of favorable/unfavorable outcome — retrieval must never filter to failures only |
| V. Founder explanation missing | Never invented — omit the slot (same as Case E) |
| W. Actual fields partially unknown | NULL≠0 preserved exactly as 38D-B's own comparison already guarantees; an unknown specific metric is never fabricated as zero, and is omitted from that slot rather than guessed |
| X. Current decision type cannot be identified | Silence rather than a semantic guess |

## 20. Architecture options

**Option A — deterministic eligibility rules + ordered precedence, no persistence, no AI.**
Candidate generation: exact match on `plan_snapshot[].kind` within `list_venture_financial_commitments_for_owner()`,
excluding the commitment currently being modeled (if any), ordered `committed_at DESC`, capped to 1, filtered
to `comparison_status != "awaiting_actuals"` via the existing `build_commitment_comparison()`. Relevance
method: structural equality only. Schema changes: **none**. AI involvement: **none**. Explainability: total.
Latency: negligible (reuses two already-existing, already-tested functions). Testing difficulty: low — pure
function, exhaustively unit-testable. False-positive risk: very low. Future extensibility: straightforward,
one domain/one `kind` at a time.

**Option B — Option A plus an internal (never founder-facing) cross-domain relevance score.** Only
meaningfully different once a second retrievable domain (e.g., Build) exists simultaneously with Finance and
needs blending into one ranked list. Schema changes: none required. AI involvement: none. Explainability:
depends entirely on keeping the score's inputs to the same already-audited boolean/enum facts — otherwise
risks becoming an unexplainable black box. Recommended only as a LATER evolution of Option A, not adopted now.

**Option C — deterministic candidate generation, then an AI ranking/selection/phrasing pass.** Candidate
generation: same as A. AI involvement: **yes**, one call per retrieval. Explainability: degraded (a
constrained ranking step still introduces "why this one" opacity). Latency: materially higher. Testing
difficulty: high — reintroduces exactly the non-deterministic-testing problem this entire Finance workstream
has deliberately avoided since Phase 35B. False-positive risk: low if the upstream pool is already narrow,
but adds a new failure surface. Future extensibility: valuable only once the candidate pool is large/
cross-domain enough that deterministic rules genuinely break down — not the case for the proposed 39B slice
(0 or 1 candidates).

**Recommended: Option A.** Smallest architecture that produces defensible value, and the only one requiring
zero new machinery, zero AI, and zero schema change.

## 21. Schema gap analysis

| Gap | Classification |
|---|---|
| No `decision_type` field on `venture_decisions` (must infer via optional `related_mission_id`) | IMPORTANT BUT NOT BLOCKING — Finance's own `plan_snapshot.kind` already covers the recommended 39B scope without needing this |
| No per-event historical company-stage/segment/product-version snapshot (only a current, mutable `stage`) | IMPORTANT BUT NOT BLOCKING for hiring-cost relevance (judged low stage-sensitivity); FUTURE ENHANCEMENT for any broader retrieval |
| `related_decision_id` coverage on commitments is sparse/optional | NON-BLOCKING — 39B does not depend on it; a bonus 4th slot when present |
| No generic Finance ↔ Build relationship beyond the narrow, optional `related_decision_id` path | IMPORTANT BUT NOT BLOCKING for a Finance-only 39B; BLOCKING for any cross-domain retrieval phase |
| Build outcome recording (`longitudinal_outcome` evidence) is optional/manual, not guaranteed | BLOCKING for any Build-history retrieval slice; not relevant to the recommended Finance-only 39B |
| `expected_monthly` is a blended aggregate across a commitment's whole `plan_snapshot`, never itemized per source id | BLOCKING for confidently attributing aggregate expected/actual figures to one item within a MULTI-item (bundled) commitment; NOT blocking when the matched commitment has exactly one `plan_snapshot` item |
| Analyze/SPS structurally isolated from `modeled_ventures` except one optional `venture_graduations` link | BLOCKING for any SPS-based retrieval (confirms it should not be attempted) |
| No stored signal for WHY a founder is modeling a given plan (cash concern vs. growth bet, etc.) | FUTURE ENHANCEMENT — not needed for 39B's literal expected/actual/explanation projection |

39A does not fix any of these. They are named so a future phase inherits an audited map, not a fresh
investigation.

## 22. Minimum implementable slice (39B)

**Recommended scope:** when a founder is modeling or previewing a NEW hire (the existing
`POST /ventures/{id}/hire-plans` / `POST /ventures/{id}/hire-plans/preview` flow in `FinanceOverview.tsx`),
retrieve the single most recent PRIOR committed hire for the same venture — a commitment whose
`plan_snapshot` contains a `kind: "hire"` item, preferring (or requiring, per §12's own finding) a
single-item commitment for the full three-slot claim — with `comparison_status != "awaiting_actuals"`, and
render its Expected/Actual/(Explanation if present) as a compact "Relevant history" card with a "Why is SIE
showing this ▾" disclosure, exactly per §16/§17 above.

This is attractive, and confirmed by audit (not assumed): both sides are already fully structured
(`plan_snapshot[].kind`, `expected_monthly`, `build_commitment_comparison()`, `founder_explanation` all
already exist and are already tested), requires zero schema change, zero AI, and reuses two already-shipped
functions verbatim. It does NOT require solving Build-history's optional-outcome gap, Decision-history's
sparse-FK gap, or the multi-item aggregation problem (39B simply prefers/requires single-item matches, per
§12). Exact UI placement within the hire-modeling flow is an implementation decision left to 39B itself.

## 24. Phase 39B implementation (as built)

Implements exactly the recommended §22 slice. No table, no column, no migration, no AI call, no score. The
Non-Goals list (39B's own §22) was followed in full: no universal engine, no Build/pricing/revenue-target
retrieval in the UI, no Command Center change.

### Eligibility rule (exact)

A `venture_financial_commitments` row is eligible only when ALL hold: owned by the requesting user/venture
(existing `_require_owned_venture` pattern); `plan_snapshot` contains **exactly one** item; that item's
`kind == "hire"` and `employment_type == "employee"` (contractors excluded — §3, no equivalence assumed);
`build_commitment_comparison()`'s own `comparison_status != "awaiting_actuals"`; and at least one comparison
month has BOTH a matched actual snapshot AND a known (non-null) `expenses.actual` value specifically — a
month with a snapshot but an unrecorded expense figure is treated as not-yet-observed for this purpose
(Case Y), never as a fabricated zero.

### Selection rule (exact)

Candidates are sorted `(committed_at DESC, id DESC)` inside the pure function itself — never trusting the
caller's own query order — and the FIRST eligible one wins. No score, no AI, no semantic similarity, no
random selection. Verified directly: two eligible commitments return only the newer one (Case J); recency
wins even when an OLDER eligible commitment has a founder explanation and the newer one doesn't (Case K —
never biased toward richer history); of ten commitments only three eligible, the newest ELIGIBLE one wins,
skipping seven structurally ineligible ones (Case W); when the literally-newest commitment is ineligible
(bundled), the next-newest ELIGIBLE one is selected instead (Case X).

### Historical source / expected source / actual source / explanation source

Exactly as designed in §12 above, unchanged: `list_venture_financial_commitments_for_owner()` (existing,
38D-A) for candidates; the matched commitment's own frozen `expected_monthly` (never regenerated) for
expected values; `build_commitment_comparison()` (existing, 38D-B) for the actual/variance; the matched
commitment's own `founder_explanation` (existing, 38D-C) for the explanation, rendered verbatim or omitted.

### Observed month rule (a real refinement found during live testing)

`observed_month` is the MATCHED SNAPSHOT's own `actual_as_of_date` — never `month["date"]` (the expected
month's own calendar marker). This was NOT the original implementation: the first version used
`month["date"]`, and live testing on venture 8212 surfaced a genuine mismatch — a commitment whose source
snapshot was dated the 20th produced an expected-month marker of "Oct 20," while the real matching actual
snapshot was dated the 15th. Displaying "Oct 20" as the observed month would have silently misattributed the
actual data to a date it wasn't recorded on. Fixed before this phase's own final report, with a dedicated
regression test (`test_observed_month_uses_the_actual_snapshots_own_date_not_the_projection_marker`) proving
the distinction directly.

### Metrics shown / causal claims made

Role, committed salary, burden, modeled monthly employment cost (all frozen, itemized, from `plan_snapshot`)
plus expected/actual/variance for TOTAL monthly expenses (from the matched comparison month) — never a
hire-specific actual cost, because none exists (§7 of the directive, confirmed by 39A's own audit finding:
`expected_monthly` has no per-item breakdown). Copy is exactly "the plan expected total monthly expenses of
$X; the observed month recorded $Y" / "observed total monthly expenses were $Z above/below/matched the
committed expectation" — never "the hire cost $Z more." **Zero causal claims are made anywhere in this
phase's own code or copy.**

### Founder attribution / traceability

"You said: '<verbatim text>'" when `founder_explanation` is present; the block is entirely absent (not "no
explanation available") when it is null. A "Why is SIE showing this? ▾" disclosure states the structural
reason in plain language plus the committed/observed months — no internal ids surfaced to the founder.

### Silence behavior

`RelevantHireHistoryCard` renders nothing while loading and nothing when the backend returns `null` — no
"no history found" message anywhere, matching §13's "silence is a successful result" instruction exactly.

### API added

One endpoint: `GET /ventures/{venture_id}/financial-commitments/relevant-hire-history`, `response_model=
RelevantHireHistoryResponse | None`, following the exact existing "`null` body = no result, never an error"
convention `GET /me/startup-claims/{startup_id}` already established. **Route-ordering bug found and fixed
during test-writing:** this endpoint was initially declared AFTER the existing
`GET /ventures/{venture_id}/financial-commitments/{commitment_id}` route — FastAPI/Starlette matches routes
in declaration order, so the literal path segment `relevant-hire-history` was being swallowed by the earlier
`{commitment_id}: int` route and rejected with a 422 int-parsing error before ever reaching the new handler.
Fixed by moving the new route's declaration above the `{commitment_id}` route, with a comment explaining why
the ordering is load-bearing. Caught immediately by the very first API-level test run.

### Pure retrieval logic

`app/ai/hiring_history.py::find_relevant_hire_history()` — takes the venture's full commitment list, an
injected `build_comparison` callable (never imports `build_commitment_comparison`/the database directly), and
an optional `exclude_commitment_id`. Zero UI copy inside the module (copy lives entirely in
`FinanceOverview.tsx`'s own `RelevantHireHistoryCard`). Zero AI.

### Tests

New file `app/tests/test_hiring_history.py`: 29/29 passing — 23 direct pure-function unit tests (Cases A,
C-P, W-Z plus the exclude/order-independence/observed-month-source tests) and 6 API-level integration tests
(auth, null-body-not-error, a real end-to-end candidate with correct provenance, ownership, no-recompute,
and full source-mutation safety). Full regression re-run: `test_commitment_explanation` (12/12),
`test_commitment_comparison` (23/23), `test_venture_financial_commitments` (21/21),
`test_venture_scenarios`, `test_venture_financials`, `test_venture_hire_plans`, `test_build_intelligence_loop`,
`test_venture_graduation`, `test_idea_lab`, `test_founder_workspace` — all passing, zero regression. Frontend:
`tsc --noEmit`, `eslint`, `next build`, and the full `npm test` suite (19 files) all clean.

### Live walkthrough

On venture 8212: created a fresh, single-item employee-hire commitment (a standalone commit, distinct from
the venture's existing bundled commitment #35, which correctly remained ineligible throughout per Case I),
added a matching later actual snapshot, and recorded a founder explanation on it. Opened the real "Model a
change → Hire someone" flow, entered a DIFFERENT role ("Product Designer") to model a new hire, and confirmed
live that the "Relevant history" card appeared showing the PRIOR hire ("Backend Engineer") with hand-verified
exact figures (expected $33,038, actual $38,000, difference +$4,963 — all confirmed against the frozen data
by manual arithmetic) and the founder's own explanation verbatim. Expanded "Why is SIE showing this? ▾" and
confirmed the plain-language structural reason. Edited the historical hire's LIVE salary from $180,000 to
$900,000 directly against the running backend and confirmed via the API that the card's own frozen salary,
modeled cost, and expected-expense figures were completely unaffected. Confirmed silence on a venture with
zero commitments (venture 893) — a normal 200 response with a `null` body, not an error. Switched the
CURRENT modeling form to "Contractor" and confirmed the "Relevant history" card correctly disappeared (Case
U) while the current-decision preview content remained. Afterward, removed all walkthrough-only fixtures
(the new commitment, the new hire, both new snapshots) to restore venture 8212 to Phase 38C's own standing
Command Center demo state, reconfirmed live with no regression (stale-snapshot and revenue-divergence
statements both still render correctly).

### Known limitations

- Multi-item (bundled) commitments are never eligible, even when one of their items is a clean, isolated
  employee hire — a deliberate, documented tradeoff (39A §12), not a bug.
- V1 covers employee hires only; contractors, revenue targets, and expense changes are all explicitly out of
  scope for this phase's UI, per the directive's own non-goals.
- The card only ever shows total-expense variance, never a hire-specific cost variance — because no
  hire-specific actual-cost data exists anywhere in this codebase (confirmed by audit, not assumed).
