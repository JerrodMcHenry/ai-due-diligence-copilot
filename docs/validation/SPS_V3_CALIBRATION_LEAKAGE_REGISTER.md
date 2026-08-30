# SPS V3 Calibration Leakage Register

Phase 10.8H. A permanent record of every real company exposed during
SPS methodology development to date, across every phase from before
this V3 workstream began through Phase 10.8G. **Every company listed
here is permanently excluded from the future blind-validation cohort
(Group C).** This register is additive-only going forward — any company
touched in a future phase must be appended here, never removed.

## Why this register exists

Phase 10.8's own validation depended on a cohort no prior phase had
inspected. That guarantee has now been used up for 36 real companies
across the phases below. Before any V3 blind validation is possible,
this document exists so no future phase can accidentally reuse a name
that methodology development has already seen — seeing a company's
real evidence, even once, while building or testing the scoring rules
is enough to compromise it as a blind-validation subject, regardless of
whether a numeric score was ever recorded or acted on.

## Register

### Pre-existing canonical database (exposed before the 10.8 workstream began)

These companies were already present in the product's canonical
`startups`/`analyses` tables (confirmed via `get_rankings()` during
Phase 10.8's own baseline query) — analyzed under a pre-V2.1
methodology version, before any part of this validation/redesign
workstream started, but still real, already-scored exposure.

| Company | Context of exposure |
|---|---|
| Ramp Business Corporation | Pre-existing canonical analysis |
| Vanta, Inc. | Pre-existing canonical analysis |
| Brex, Inc. | Pre-existing canonical analysis |
| X (formerly Twitter) | Pre-existing canonical analysis |
| Airtable | Pre-existing canonical analysis |
| Retool | Pre-existing canonical analysis |
| LiveCheck Inc. | Pre-existing canonical analysis |
| Linear | Pre-existing canonical analysis |

### Phase 10.8 — 25-company frozen blind-validation cohort

All 30 were selected; 25 completed the pipeline, 5 failed at website
extraction (still exposed as named targets and rejected candidates —
registered regardless of pipeline outcome, per this document's own
standard: a company is "exposed" once it is named and targeted, not
only once it is successfully scored).

**Completed (25):**

| Group | Company |
|---|---|
| A | Notion Labs |
| A | Figma |
| A | Databricks |
| A | Deel |
| A | Rippling |
| A | Faire |
| A | Klaviyo |
| A | Abnormal Security |
| B | Plaid |
| B | Better.com |
| B | Loom |
| B | Away |
| B | Clubhouse |
| B | Bumble Inc. |
| B | Peloton Interactive |
| C | Rivet |
| C | Openroll |
| C | Fixpoint |
| C | Dome |
| C | LunaBill |
| C | Relaw |
| C | Sourcebot |
| C | Bear AI |
| C | Bravi |
| C | Denki |

**Failed at website extraction, still registered as exposed (5):**

| Group | Company | Reason |
|---|---|---|
| A | Toast, Inc. | HTTP 403 (both URL variants attempted) |
| A | Chime | HTTP 403 |
| B | Bolt | HTTP 429 |
| B | Gopuff | HTTP 403 |
| B | WeWork | HTTP 403 |

### Phase 10.8B — high-strength sanity check

| Company | Outcome |
|---|---|
| Stripe | Completed (SPS 76.4 under V2.1) |
| SpaceX | Completed (SPS 62.7 under V2.1) |
| Canva | Failed at website extraction (HTTP 403, confirmed reproducible) — still registered |

### Total unique real companies registered: 36

(8 pre-existing + 25 from the Phase 10.8 cohort + 5 Phase-10.8-attempted-but-failed
+ 3 from the high-strength sanity check, with zero overlap between
groups — confirmed by direct comparison.)

## May any of these be used for calibration (not blind validation)?

**None are pre-designated for calibration use in this phase.** Per
Part 18's own framing, an already-exposed company "may be used for
calibration only if explicitly designated" — no such designation is
made here. All 36 are earmarked for **exclusion from the calibration
dataset as well as blind validation**, for a specific reason beyond
simple leakage: many of these companies' real V2.1 scores and pillar-
level behavior are already extensively documented in
`docs/validation/SPS_REAL_COMPANY_VALIDATION_REPORT.md`,
`SPS_DISCRIMINATION_AUDIT.md`, and `SPS_V2_1_HIGH_STRENGTH_SANITY_CHECK.md`.
Using any of them for V3 calibration would create a second, more subtle
leakage risk: a parameter could be tuned (even unintentionally) to
"fix" a specific, already-known, already-published V2.1 behavior for
that specific company, which is a narrower version of the exact
company-specific-tuning prohibition this entire engagement has enforced
since Phase 10.8. **Recommendation: treat all 36 as permanently reserved
— neither calibration nor blind validation — unless a future phase
makes an explicit, reasoned case for calibration-only reuse of a
specific one.**

## Companies contaminated for blind validation specifically

All 36 listed above, without exception. This is the authoritative
answer to "which companies can never be Group C" for every future
phase.
