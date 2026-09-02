# Product Event Taxonomy V1

Status: **specification only — no analytics provider chosen, no event
logging code written.** This document exists because Phase 22 identified
instrumentation as necessary to test the retention thesis, and Phase 24's
own instruction was explicit: if no analytics infrastructure exists and
building one would create meaningful architecture/dependency work,
document the minimal taxonomy instead of building it. That is exactly the
situation here — re-confirmed directly this phase (`lib/api/analytics.ts`
is platform-wide aggregate analytics — rankings, top-startups — a
different concern; there is no per-founder behavioral event mechanism
anywhere in `app/` or `dashboard/`).

Choosing a provider (a first-party table, a third-party product-analytics
tool, etc.) is a separate decision, out of scope here.

## How to read this table

- **Event name** — the identifier a future logger would use.
- **Trigger** — the exact UI/API moment that fires it.
- **Qualifying behavior** — whether this event should count toward
  "Weekly Active Building Venture" (Phase 22's north star). Only real
  founder-initiated building activity qualifies; passive engagement never
  does.
- **Properties required** — the minimum fields needed, never simulation
  or capture *content* (matching the precedent already established for
  the Fundraising Simulator and Universal Capture: log that something
  happened, never the sensitive founder text/numbers themselves).
- **Metric supported** — which Phase 22 metric this event feeds.

## Venture-track events (Idea Lab)

| Event name | Trigger | Qualifying? | Properties | Metric supported |
|---|---|---|---|---|
| `mission_created` | `POST /ventures/{id}/missions` succeeds | **Yes** | venture_id, mission_source | Action Start Rate |
| `mission_completed` | `PATCH /ventures/{id}/missions/{id}/status` → completed succeeds | **Yes** | venture_id, mission_id | Action Completion Rate, North Star |
| `capture_started` | Capture textarea receives focus / "What happened?" card expanded | No (intent, not completion) | venture_id | Funnel diagnostic only |
| `observation_saved` | `POST /ventures/{id}/capture` succeeds | **Yes** | venture_id, category (nullable) | Evidence/Learning Capture Rate, North Star |
| `structured_interpretation_reviewed` | A proposed signal checkbox is toggled | No (review, not commitment) | venture_id, signal_count | Funnel diagnostic only |
| `model_update_initiated` | "Update my model" clicked (before the API call resolves) | No (intent) | venture_id | Funnel diagnostic only |
| `model_update_applied` | `PUT /ventures/{id}` succeeds AND assumptions actually changed | **Yes** | venture_id, vps_delta_bucket (e.g. "increased"/"decreased"/"unchanged" — never the raw score) | Model Update Rate, North Star |
| `weekly_review_viewed` | `WeeklyReview` component renders with `hasActivityInWindow` or `isBrandNew` resolved (i.e. real data shown) | No | venture_id, review_state | Weekly Review Usage |
| `weekly_review_record_capture_clicked` | The review's own quiet-week "record what happened" pointer is clicked | No (intent) | venture_id | Funnel diagnostic only |
| `weekly_review_action_started` | The review's "Make this an action" button is clicked | **Yes**, once the resulting `mission_created` fires | venture_id | Weekly Review Usage, North Star (via mission_created) |
| `simulation_previewed` | A What-If scenario or Fundraising Simulator scenario is run (preview only, no apply) | No | venture_id | Simulation Usage |
| `simulation_applied` | Scenario "Apply" clicked (`PUT /ventures/{id}` from that flow) | **Yes** | venture_id | Model Update Rate, North Star |
| `learn_disclosure_opened` | A `ConceptDisclosure` is expanded | No | concept_key | Engagement diagnostic only |
| `playbook_viewed` | A Playbook page is opened | No | playbook_slug | Distribution diagnostic only |

## Real-startup track events (Founder Workspace)

| Event name | Trigger | Qualifying? | Properties | Metric supported |
|---|---|---|---|---|
| `founder_action_created` | `POST /startups/{id}/actions` succeeds | **Yes** | startup_id, source | Action Start Rate |
| `founder_action_completed` | Action status → completed | **Yes** | startup_id, action_id | Action Completion Rate, North Star |
| `founder_update_saved` | `POST /startups/{id}/updates` succeeds | **Yes** | startup_id, update_type | Evidence/Learning Capture Rate, North Star |
| `milestone_status_changed` | A `startup_milestones` row's status changes | **Yes**, only when moving to `achieved` | startup_id, milestone_id | North Star |
| `reanalysis_started` | "Re-analyze" clicked | No (intent) | startup_id | Funnel diagnostic only |
| `reanalysis_completed` | A new canonical analysis is saved | **Yes** | startup_id | North Star (a legitimate, deliberate re-analysis is real building activity) |

## Explicitly non-qualifying, regardless of track

Matching Phase 22's own north-star definition precisely — engagement is
never counted as building:

- `login` / session start
- any page view
- a passive VPS/SPS render (opening a page that already had a score)
- `weekly_review_viewed` on its own, with no accompanying qualifying event
- `learn_disclosure_opened`
- `playbook_viewed`
- `simulation_previewed` (an unapplied preview — Fundraising Simulator and
  Simulate V1 scenarios are explicitly ephemeral by design; running one is
  exploration, not commitment)

## North-star calculation (once instrumented)

**Weekly Active Building Venture** = a venture/startup with ≥1 qualifying
event (marked **Yes** above) in the trailing 7 days. This mirrors
`buildWeeklyReview.ts`'s own `hasActivityInWindow` boolean almost exactly
— the review's own display logic and the eventual north-star metric are
intended to agree, by design, so "does this founder see an active-week
review" and "does this venture count toward the north star" never
diverge.
