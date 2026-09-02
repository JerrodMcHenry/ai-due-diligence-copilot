# Private Beta Plan — SIE

Status: plan only. No invites sent. Pairs with
`docs/product/PRIVATE_BETA_READINESS.md` (the release-gate audit this
plan assumes passed).

## Wave 0 — creator/admin final smoke test

Before any invite: the creator signs in as themselves, walks
`DEPLOYMENT.md`'s own health-verification steps against the real deployed
staging URL (not localhost), and performs one real end-to-end pass:
create a venture → Capture → an Action → an explicit model update →
enable a Snapshot → open it logged out → click its CTA → confirm the
attributed venture creation. Record the exact **BETA_START** timestamp
here once this pass is clean:

> BETA_START: _(fill in immediately before Wave 1's first invite)_

Every `/admin/analytics` report from this point forward should be read
with `window_days` scoped to "days since BETA_START," not a longer
window that would blend in this Wave-0 smoke-test traffic (which is real,
non-`zztest_`, non-admin activity by design — Wave 0 IS the creator using
their own real account one last time before opening it up, so its
`venture_id`s are worth noting here to manually exclude from Wave 1's
earliest reads if precision matters before a code-level BETA_START filter
is worth building).

## Wave 1 — 5 founders

Invite exactly 5. Target mix (adjust the exact count, not the shape, to
whoever is actually available and willing):

- 2 idea-stage / first-time founders — people who may not have
  previously believed startup/VC participation was accessible to them.
  Not exclusively experienced SaaS operators.
- 2 MVP/pre-revenue founders.
- 1 founder with real customers/revenue.

Observe for **several days** (not a single session). Fix only:

- P0 (any found).
- P1 (any found).
- A friction point that repeats across **more than one** of the 5
  founders independently — a single founder's one-off confusion is a
  data point for the interview, not yet a pattern to build around.

Do not act on Wave 1 feedback by starting a new feature. Every fix in
this window should be traceable to a concrete P0/P1 or a repeated
friction pattern, matching Phase 29's own change-budget discipline.

## Wave 2 — expand to 10–20 total

Once Wave 1's P0/P1s (if any) are resolved, expand to 10–20 total
founders, same mix ratio as Wave 1 (idea-stage : MVP/pre-revenue :
revenue-stage), run until **at least one complete W1 retention window has
fully elapsed** for the earliest-activated cohort (14+ days from their
own activation, per `PRODUCT_ANALYTICS_V1.md`'s own W1 definition) before
drawing any conclusion.

## Interview guide

Ask every founder, in their own words, not leading toward SIE's existing
roadmap:

1. What did you come to SIE hoping to accomplish?
2. When did SIE first become useful?
3. What confused you?
4. What felt unnecessary?
5. What decision did SIE help you make?
6. What did you leave SIE to use another tool for?
7. What made you return?
8. What would make you return more often?
9. Did you share your Venture Snapshot? Why or why not?
10. If SIE disappeared tomorrow, what would you miss?
11. Would you recommend it to another founder? Why?
12. What would you expect to pay for something like this, if anything?

## Success criteria — hypotheses, not benchmarks

No invented industry benchmark is used here (e.g. "40% W1 means PMF" is
not a claim this plan makes — there isn't yet evidence to support any
specific number). These are internal decision thresholds, read alongside
the interviews, never analytics alone:

**GREEN** — strong activation, repeated meaningful building across
multiple sessions per founder, founders voluntarily return without a
prompt, and the interviews surface concrete decisions SIE actually
changed. → Continue expanding; distribution investment (Phase 27's own
Snapshot thesis) is earning its keep.

**YELLOW** — activation happens (founders get through onboarding and
understand the product), but repeat behavior is weak or inconsistent —
some founders return, some don't, without a clear pattern the interviews
explain. → Stay in Wave 1/2 longer; prioritize whichever specific
friction the interviews name most often before expanding further.

**RED** — founders understand what SIE is and can operate it
independently, but don't return, because the interviews reveal it simply
isn't useful enough yet for real, ongoing company-building decisions. →
Stop expanding; this is a product-value problem, not an onboarding or
distribution problem, and needs to be solved before more founders are
invited.

Read analytics (`/admin/analytics`, scoped to BETA_START) and interviews
together — a strong activation rate with weak interview sentiment, or
vice versa, is itself a finding, not a tie-breaker to resolve by picking
one source over the other.
