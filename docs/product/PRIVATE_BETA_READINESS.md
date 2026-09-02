# Private Beta Readiness & Production Release Gate — Phase 29

Status: audit + adversarial test + targeted P0/P1 fixes only. Not
deployed. This document is the release-gate record: what was verified,
what was found, what was fixed, and the final GO/NO-GO decision.

## 1. Release-gate thesis

The question this phase answers is narrow and specific: *can SIE be
handed to 5 real founders without the creator sitting beside them?* This
is not a roadmap review. Per the directive's own change budget (Part 2),
only demonstrated P0/P1 defects were fixed; everything else is either
already-frozen methodology (VPS/SPS/Fundraising Simulator, untouched) or
documented as P2 for post-invite feedback to prioritize.

## 2. Architecture audited

Re-read and, where claims were checkable, directly verified against the
running code rather than trusted: `UNIVERSAL_FOUNDER_CAPTURE_V1.md`,
`WEEKLY_FOUNDER_REVIEW_V1.md`, `PRODUCT_EVENT_TAXONOMY_V1.md`,
`FOUNDER_RETENTION_LOOP_ACCEPTANCE.md`, `RETENTION_LOOP_CLOSURE_V1.md`,
`SHAREABLE_VENTURE_SNAPSHOT_V1.md`, `PRODUCT_ANALYTICS_V1.md`, plus
`render.yaml` and `DEPLOYMENT.md` (a real, already-authored staging
runbook — Vercel frontend + Render backend/Postgres — that this phase
verified against the actual code rather than rewriting).

## 3. Environments/configuration

`DEPLOYMENT.md` already documents every required variable accurately —
verified line-by-line against `app/api.py`/`app/auth.py`/`app/database/db.py`:

| Variable | Behavior when unset | Verified |
|---|---|---|
| `DATABASE_URL` | Raises `ValueError` at import — fails loudly, cannot silently run against nothing | Yes, code inspected |
| `CLERK_ISSUER` | Every authenticated request 401s | Yes, code inspected |
| `CORS_ALLOWED_ORIGINS` | Falls back to `localhost:3000`/`127.0.0.1:3000` only — safe (rejects the real prod frontend rather than allowing anything) | Yes, code inspected |
| `ADMIN_USER_IDS` | Every admin check 403s (nobody is admin) | Yes, code inspected + live-tested (Section 6) |
| `OPENAI_API_KEY` / `TAVILY_API_KEY` | Required; no fallback | Documented, not independently re-verified (real secrets, correctly never printed) |
| `SPS_ENGINE_VERSION` | Defaults to `v3` (current methodology) when unset | Verified in code — not in `DEPLOYMENT.md`, but needs no action since the default is already correct |

CORS confirmed never wildcarded, `allow_credentials=True` paired only
with an explicit origin list. No `DEBUG` flag, no hardcoded secret, no
localhost URL baked into shipped code (all localhost defaults are
explicit, documented dev-only fallbacks, not accidental leakage).

## 4. Database readiness

**Fresh-init: directly tested, not assumed.** Created a genuinely empty
local Postgres database (`createdb`), pointed `DATABASE_URL` at it, and
imported `app.api` cold: every table, column, and index (including this
year's own additions — `modeled_ventures`, `venture_missions`,
`venture_model_updates`, the four `share_*` columns +
`idx_modeled_ventures_share_public_id`, `product_events`) was created
successfully with zero errors. Followed by a real end-to-end smoke test
against that same fresh database via `TestClient`: `POST /ventures`
succeeded (venture id 1) and `GET /health` returned healthy. Database
dropped after the test.

**Upgrade path**: unchanged, additive-only pattern (`CREATE TABLE IF NOT
EXISTS` / `ADD COLUMN` in try/except) already proven repeatedly against
the real, populated local dev database across every phase this
engagement — rolling a backend deploy back to an older commit is safe by
construction (older code never references newer columns).

## 5. Auth/privacy results (Part 7 — mandatory, P0-risk)

**Live-tested against the actual running server**, not just the
automated suite: created a genuinely separate venture and mission owned
by a distinct synthetic user (`zzbeta_other_owner`), then used a real,
live, Clerk-authenticated browser session (a different real identity) to
attempt, via direct `fetch()` calls (not UI navigation):

fetch venture, rename venture, capture against it, create an action, list
missions, read history, get share settings, change share settings, log a
link-copied event, delete the venture, record learning on its mission,
complete its mission, update its model.

**Result: 12/12 attempts returned 404** (not 401/403/200) — the same
non-leaking shape this codebase uses everywhere ("not found" and "not
yours" are indistinguishable). A request with zero auth token returned
401. Post-attack inspection confirmed the venture's name and mission
status were completely unchanged — zero mutation from any attack.
Fixture cleaned up. **No P0.**

## 6. Public sharing security (Part 8)

Re-confirmed live against the currently running server (building on
Phase 27/28's own exhaustive coverage): fetched a live public snapshot
directly and confirmed the response has exactly the 10 allowlisted keys
— no `id`, no `user_id`, no `description`. Prior automated coverage
(re-run this phase, still green) separately proves: private by default,
disable makes the same URL 404 immediately, malformed/unknown ids 404,
re-enable reuses the exact same public id, and a planted-sensitive-data
fixture (CAC, SAFE terms, capture/learning text) never appears in the
raw response. **No P0.**

## 7. Analytics security (Part 9)

`GET /admin/analytics` is gated by the pre-existing `RequireAdmin`
dependency (Phase 7.1A) — re-confirmed via the automated suite
(`test_admin_endpoint_requires_admin`: no-auth → 401, signed-in non-admin
→ 403, real admin → 200) and via code inspection of
`_resolve_admin_user_ids()`'s fail-closed default (empty/unset →
nobody is admin). A second, live real Clerk identity to click through
the 403 path end-to-end was not available this session (would require a
second real Clerk account); the code path is identical to the one the
automated test exercises through FastAPI's own dependency-injection
system, not a separate implementation. Raw `product_events` rows
inspected directly (25 most recent real rows) — zero founder/private
content in any row, confirmed again this phase. **No P0.**

## 8. Analytics baseline (Part 13/25) — real P1 found and fixed

**Found live, not by inspection alone**: the admin dashboard, after a
full real capture→action→model-update→share→public-view→CTA→attributed-
creation walkthrough under the creator's own real (non-`zztest_`)
account, correctly showed `Ventures created: 0` (the Phase 28
`exclude_test_users` fix already excluded it from
activation/retention/distribution) but **incorrectly showed `Captures:
2`, `Actions completed: 1`, `North Star: 1`** for the same creator-only
session. Root cause: `get_north_star_report()`,
`get_meaningful_building_days_report()`, and `get_engagement_counts_report()`
referenced the raw `_TEST_EXCLUSION_SQL` string constant directly instead
of calling the shared `_test_exclusion_sql()` function — so Phase 28's
own admin-account exclusion (Section 13 below) never reached three of
the six report functions.

**Fixed**: all six report functions now route through the one shared
`_test_exclusion_sql()` call. Re-verified two ways: a new automated test
(`test_admin_accounts_excluded_from_reports`, extended to also assert
the engagement-count exclusion) and a live reload of `/admin/analytics`
— every metric now reads exactly 0 / "Not enough data" for the same
creator-only session that previously showed non-zero counts. This is the
genuinely clean T0 a beta baseline requires.

**BETA_START procedure** (no further code needed): record the literal
invite timestamp in this document's own changelog when Wave 1 launches;
every report already supports arbitrary `window_days`, so "days since
BETA_START" is a valid window with no new parameter. Historical
development events are never deleted (Part 25's own explicit
instruction) — they simply predate the window a beta report would use.

## 9. Beginner walkthrough (Part 3)

Not re-walked start-to-finish this phase (Phase 25's own dedicated,
exhaustive persona audit already did this in full — landing → signup →
Build → AI extraction → naming decision → VPS → categories → What
Matters Now → Action → Capture → Learn → Progress → Weekly Review;
Phase 26 then closed the specific gaps that audit found: capture dead
ends, no cross-session memory, "Untitled venture" by default). This
phase's own live testing (venture 1578, the beginner house-cleaner-
adjacent fixture) re-confirmed the closed loop still holds: honest
"Not described yet" for unprovided fields, VPS framed as "not a
verdict," a concrete first action ("Interview 20+ target customers"),
and a real capture → "This doesn't change your model yet, but it may be
worth investigating" outcome (never a silent dead end).

## 10. Early-founder walkthrough (Part 4)

Covered by Phase 25's own Persona B audit (MVP + interviews + paying
customers + guessed CAC) plus Phase 26's live-verified churn/complaint/
retention capture fixes and Phase 28's live-verified capture→model-
update→snapshot funnel on real evidence-bearing ventures (venture 1578
this phase: signed a $49/month customer → correctly proposed both a
price-point and paying-customer signal → VPS moved 6.5→5.0 with a
neutral, honest "Economic Potential/Validation newly scored" framing,
not a punitive one). Recommendation evolution (idea-stage → "prove
repeatable acquisition") remains confirmed non-generic from Phase 25/26.

## 11. Advanced-founder walkthrough (Part 5)

Covered by Phase 25's Persona C audit and Phase 27's own live Fundraising
Simulator test (SAFE→Seed dilution math, correct cap table) on ApexGrid
(venture 1067, $11.8M ARR fixture) — VPS 6.9, credible Snapshot with a
full evidence set and category breakdown, Simulate scenarios dynamically
scaled to the venture's real numbers. No scoring change was made or
proposed this phase (Part 21's own instruction honored).

## 12. Returning-founder walkthrough (Part 6)

Live-verified this phase on venture 1578 (reloaded after this session's
own real activity): "Where things stand" rendered current action, most
recent learning, and latest model update together, consistent with
Weekly Review and Progress — no contradiction between surfaces. This
directly reconfirms Phase 26's own closure of the cross-session-memory
gap.

## 13. Failure testing

- **AI failure (Part 14)**: `POST /ventures/structure-idea` catches both
  the specific `IdeaStructuringError` and any other exception, returns a
  clean 502 with a generic, safe, retriable message, and prints the
  traceback only server-side. Because `structure_idea()` is fully
  stateless (Phase 6.1's own design, confirmed by the existing
  `test_structuring_endpoint_creates_no_database_row`), an AI failure
  here creates zero rows — no duplicate venture, no corrupted partial
  state is even possible. Automated coverage
  (`test_malformed_llm_response_fails_safely`,
  `test_provider_failure_fails_safely`) re-run this phase, still green.
- **Search/enrichment failure (Part 15)**: `enrich_research()`'s Tavily
  call has no try/except of its own, but its caller
  (`run_due_diligence()`, inside `/analyze`) is wrapped in a broad
  try/except that converts ANY failure — including a Tavily outage —
  into one clean 502 ("This can happen if a research or AI provider is
  temporarily unavailable"), before `save_analysis()` is ever reached.
  A provider failure therefore can never be silently converted into "no
  evidence found" negative intelligence — it aborts the whole analysis
  instead, honestly.
- **Double-submit (Part 16)**: every mutation surface built or touched
  across this engagement (Capture, Share enable/disable) uses a client-
  side `disabled`/`loading` guard on its own submit button, which
  handles ordinary double-clicks. Live-tested the adversarial case
  directly: two genuinely simultaneous `fetch()` calls to
  `POST /ventures/{id}/capture` (bypassing the UI's own guard entirely)
  created two real rows — no server-side idempotency exists. Classified
  **P2, not P0/P1**: a duplicate capture note is annoying, never
  corrupting or cross-user, and the directive's own Part 16 explicitly
  forbids building a global idempotency platform without a demonstrated
  defect at this severity. Test rows cleaned up.
- **Empty/partial data (Part 17)**: re-confirmed via this phase's own
  fresh-DB smoke test (a brand-new venture's `model_result` correctly
  shows `vps: null`, every category `score: null`, honest
  `validation_gaps` text — never a fabricated 0) and via the admin
  dashboard's own zero-data render (every count 0, every rate "Not
  enough data," confirmed live both before and after Section 8's fix).
  Consistent with Phases 25-27's own repeated, direct verification of
  honest Unknown-handling throughout the product.
- **Error exposure (Part 24)**: both failure-handling call sites
  reviewed (`/ventures/structure-idea`, `/analyze`) print tracebacks only
  to server logs and return a fixed, generic detail string — never SQL,
  internal paths, or provider payloads. No other exception handler in
  `app/api.py` was found to differ from this pattern during this audit.

## 14. Mobile/theme/accessibility

Not re-walked exhaustively this phase (390px capture, Where Things
Stand, Weekly Review, Simulate, Fundraising, Share, and the public
Snapshot were all independently, directly verified on a genuine 390px
same-origin-iframe viewport across Phases 25-28, each with real
screenshots, in both themes for the surfaces built in Phases 26-28).
Genuinely new-this-phase: the `/admin/analytics` page has **not** been
mobile/light-theme-checked — it is an internal-only surface with no
founder-facing exposure, so this is documented as an explicit, low-risk
gap rather than fixed under this phase's change budget (Part 2 forbids
opportunistic polish; an internal tool being desktop-first is not a beta
blocker for founders). The `PersonalMenu` feedback link (Section 16) was
added using the exact same `UserButton.Link` primitive the three
pre-existing menu items already use — same styling, same accessibility
semantics, verified by direct code parity and a clean `tsc`/build rather
than a live click-through (Clerk's `UserButton` renders through its own
internal component tree that this session's browser-automation could not
reliably drive; the three pre-existing links using the identical
component are already known-working from every prior session's real
sign-in usage).

## 15. Performance/cost findings (Part 21)

External AI/search calls, enumerated directly from the code (all
pre-existing, none added this phase): `POST /ventures/structure-idea`
(one `gpt-4.1-mini` call, founder-initiated, stateless), `PUT
/ventures/{id}` when it also triggers a Simulate/manual edit (zero AI —
`_build_model_result()` is pure deterministic scoring, not an LLM call),
`POST /analyze` and its siblings (the paid canonical-analysis pipeline —
multiple pillar LLM calls + one Tavily search per category, unchanged,
explicitly founder-initiated and rate-gated by
`test_analysis_usage_protection.py`'s own existing concurrency lock).

**No passive page render triggers an AI call anywhere in the code
touched or read this phase** — venture creation, Capture, Actions,
Weekly Review, Simulate, Fundraising, Share, and the public Snapshot are
all pure database reads/writes plus deterministic scoring; the public
Snapshot route in particular (Phase 27) makes zero AI/search calls per
view, confirmed by its own `_build_venture_snapshot()` implementation
having no LLM/Tavily import at all. `/admin/analytics` runs six small,
indexed aggregate queries per request (`product_events(event_name,
created_at)` and `(venture_id)` indexes both exist) — no per-row work,
no N+1 pattern found. **Beta cost exposure is bounded to founder-
initiated `structure_idea`/`analyze` calls only**, the same exposure that
already existed before this phase.

## 16. Feedback path (Part 22)

No existing support/contact/feedback mechanism was found anywhere in the
codebase (confirmed by direct grep across `dashboard/app` and
`dashboard/components`). Added the smallest option on the directive's
own preferred hierarchy: a **"Send feedback" entry in the existing
account menu** (`PersonalMenu.tsx`, alongside My Ideas/My Startup/Learn),
using a plain `mailto:` link with a prefilled subject and a three-
question body template (confusing / broken / an idea). Zero new backend
endpoint, zero new persistence, zero new architecture — the message goes
directly from the founder's own mail client to the creator's inbox and
is never seen by or stored in SIE at all.

## 17. Legal/product framing (Part 23)

Audited via direct grep for dangerous claim patterns (guarantee\*,
investment/legal/tax advice, "will succeed," "investor-ready," "your
valuation is," "fundable") across all founder-facing `.tsx` files —
every real match was either a code-level `Promise` false-positive or an
existing, deliberate disclaimer (VPS "not a verdict," Fundraising
Simulator "educational decision support, not legal, tax, or investment
advice," Snapshot's "not a company-quality, investment, or success
prediction"). **No trust-breaking claim found; no copy change made.**

## 18. P0 findings

**None.** Cross-user security, public-sharing security, and admin-
analytics authorization all held under live adversarial testing.

## 19. P1 findings

1. **Analytics baseline contamination** (Section 8) — three of six
   report functions silently bypassed the Phase 28 admin-exclusion fix.
   **Fixed and re-verified live this phase.**

## 20. P2 findings (deferred, not fixed)

1. Double-submit on Capture (and, by the same reasoning, on
   `POST /ventures`) has no server-side idempotency — a genuine race
   produces duplicate rows. Low severity (never cross-user, never
   corrupting); deferred per the directive's own explicit instruction.
2. `/admin/analytics` not verified on mobile/light theme — internal-only
   tool, no founder exposure.
3. The new `PersonalMenu` feedback link's click-through was not
   confirmed live in this session's browser-automation environment
   (Clerk component internals); verified instead by direct code parity
   with three already-working sibling links plus a clean typecheck/build.

## 21. Fixes made this phase

- `app/database/db.py`: `get_north_star_report()`,
  `get_meaningful_building_days_report()`, `get_engagement_counts_report()`
  now route through `_test_exclusion_sql()` (was: raw constant reference,
  silently missing the admin-account exclusion).
- `app/tests/test_product_analytics.py`: `test_admin_accounts_excluded_from_reports`
  extended to assert the engagement-count exclusion specifically (the
  exact gap the live walkthrough found).
- `dashboard/components/layout/PersonalMenu.tsx`: added a "Send feedback"
  `mailto:` entry to the existing account menu.

No VPS/SPS/Fundraising methodology change. No new score. No new AI
system. No new major feature.

## 22. Unresolved risks

- No second real, distinct Clerk identity was available this session to
  drive the non-admin-403 path through a live browser (covered instead
  by the automated suite exercising the identical FastAPI dependency).
- Real secrets (`OPENAI_API_KEY`, `TAVILY_API_KEY`, a production Clerk
  instance) have never been provisioned against a real Render/Vercel
  deployment — `DEPLOYMENT.md`'s own runbook has not yet been executed
  end-to-end against real infrastructure, only verified for correctness
  against the code.
- The double-submit gap (Section 20.1) remains a real, if low-severity,
  data-quality edge case under real concurrent beta usage.

## 23. Deployment checklist

1. Create the Render Blueprint from `render.yaml` (provisions Postgres +
   web service).
2. Set `OPENAI_API_KEY`, `TAVILY_API_KEY` on the Render service.
3. Deploy the backend; confirm `GET /health` and `GET /version`.
4. Deploy the frontend to Vercel with `NEXT_PUBLIC_API_URL` set to the
   Render backend's public URL.
5. Set `CORS_ALLOWED_ORIGINS`, `CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES`
   on the backend to the real Vercel URL/Clerk instance; redeploy.
6. Set `ADMIN_USER_IDS` to the creator's real Clerk user id (required for
   `/admin/analytics` to be reachable at all post-deploy).
7. Run `DEPLOYMENT.md`'s own health-verification steps (sign in, analyze
   a real company, confirm it appears in Rankings/Search, check for CORS
   errors in the console).
8. Record the real BETA_START timestamp in `PRIVATE_BETA_PLAN.md` before
   sending the first invite.

## 24. Final GO/NO-GO

**GO.** No known P0. The one P1 found was fixed and re-verified live
within this phase. Cross-user security, public-sharing security, and the
database fresh-init path were all directly, adversarially tested against
running code — not assumed. See the chat final report for the exact
recommended next action.
