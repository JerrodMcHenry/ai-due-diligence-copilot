# SPS V3 Real-World Acceptance Test — Ex-Ante Company Selection

Frozen before any V3 run against these companies in this phase. No desired
SPS, pillar score, or assessment state is recorded anywhere in this
document — only category, stage, and selection rationale, per the test's
own explicit requirement.

Selection deliberately avoided every company name already exposed during
SPS V3's design/calibration work (the Phase 10.8F `_FORBIDDEN_NAME_FRAGMENTS`
list — Stripe, SpaceX, Databricks, Rippling, Plaid, Relaw, Dome, Notion,
Figma, Deel, Toast, Faire, Klaviyo, Chime, Abnormal, Bumble, Peloton,
Clubhouse, WeWork, Loom, Better.com, Bolt, Gopuff, Away, Rivet, Openroll,
Fixpoint, Lunabill, Sourcebot, Bear AI, Bravi, Denki, Canva, Ramp,
Vanta, Brex, Airtable, Retool, Livecheck, Linear — plus the Phase 10.8H/I
31-company real-calibration roster: Balance, Ritivel, Vercel, Modal Labs,
Middesk, Speak, Attio, Clay, Harvey AI, Together AI, Whatnot, Perplexity,
Glean, Mercury, Webflow, Scale AI, Hugging Face, Flexport, Gusto,
Airwallex, Carta, Instacart, ZipRecruiter, Discord, Convoy, Olive AI,
Katerra, Quibi, Bird, Mailchimp, Fast) wherever a comparably-fitting
alternative existed.

| # | Category | Company | Stage (believed) | Why selected |
|---|----------|---------|-------------------|--------------|
| A | Elite / evidence-rich technology company | **Palantir Technologies** | Late-stage / public (IPO 2020) | Extremely high public evidence volume, distinct enterprise data-platform business model (government + commercial), never used in any prior SPS V3 design/calibration pass. |
| B | Elite / evidence-rich, different business model | **Anduril Industries** | Growth/late-stage, private | Defense hardware + software, government-contract revenue model -- structurally unlike A's enterprise-software model. Heavily covered in tech/defense press. Not previously used. |
| C | Strong but less globally famous | **Checkr** | Growth-stage, private | Background-check infrastructure SaaS -- a real, substantial company with real public evidence, but materially less globally famous than A/B. Not previously used. |
| D | Ordinary / mixed startup | **Zapier** | Growth-stage, private, profitable | Workflow-automation SaaS with a steady, non-hype-driven public narrative (bootstrapped-to-profitable, not a headline-grabbing growth story) -- a genuine "ordinary/mixed" test case. Not previously used. |
| E | Distressed or failed startup with documented negative evidence | **Zume (Zume Inc., formerly Zume Pizza)** | Defunct (shut down June 2023); was growth-stage | Raised $445M (incl. ~$375M from SoftBank), pivoted from pizza robotics to sustainable packaging, and shut down in June 2023 amid well-documented negative coverage (repeated layoffs, PFAS packaging-compliance failure). Confirmed real via live web search this phase. Not previously used. |
| F | Early-stage startup | **Lovable** (formerly GPT Engineer) | Early/Series A-ish | Real, recent (2024-2025) AI app-builder breakout -- genuinely early-stage by evidence depth even though public attention has grown quickly. Not previously used. |
| G | Sparse-public-evidence startup | **Circlemind** | Seed-stage ($2M seed, June 2025) | Small AI-memory-infrastructure startup surfaced via live web search this phase specifically for low public evidence volume; a CB Insights financial-data page is essentially its only substantial public footprint found. Not previously used. |

## Explicit non-recording

No target SPS, pillar Strength, Coverage, Confidence, or assessment state
is recorded for any company above. This table will not be edited after
V3 results are observed -- any correction found necessary after running
will be recorded in the final acceptance report instead, with an
explicit note of what changed and why, never a silent edit to this file.

## Execution method (recorded ex-ante, for transparency)

`app.workflows.due_diligence_workflow.run_due_diligence()` will be called
directly, in-process, with `SPS_ENGINE_VERSION=v3` set, for each company's
name/description as the input text. This is the exact same production V3
code path `POST /analyze` uses (`run_due_diligence()` →
`sps_v3_enabled()` → `compute_sps_v3_assessment()`), invoked directly in
Python specifically so this test does not write to the production
database (per this phase's "prefer isolated/local execution" instruction)
and does not run through the auth/usage-cap/persistence layers, which are
irrelevant to what this test measures. Raw results are saved as JSON per
company for inspection and for the trace-reconstruction/repeatability
sections of the final report.
