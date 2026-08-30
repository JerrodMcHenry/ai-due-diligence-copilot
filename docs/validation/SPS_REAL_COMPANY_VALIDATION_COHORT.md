# SPS Real-Company Validation Cohort (FROZEN)

Phase 10.11.1. This manifest is written and frozen **before** any company in
it is run through SIE. Nothing below was chosen or adjusted based on an SPS
result — see `SPS_REAL_COMPANY_VALIDATION_REPORT.md` for what happened after
running the cohort.

**Frozen:** 2026-08-28, before any pipeline run for these 30 companies.

**Rule:** `expected_group` is an ordinal, qualitative hypothesis about how
much strong, credible, publicly-demonstrable evidence exists for a company
*right now* — never a predicted numeric SPS, and never told to the engine.
The engine receives only a website URL, exactly like any real user's
submission.

**Current-state, not point-in-time (Part 18):** every hypothesis below
reflects the company's understood status as of this freeze date, including,
for a few companies, publicly known history of difficulty or decline. SIE
itself will independently research and analyze whatever it finds — nothing
here is fed to the model.

---

## Group A — Strong / Highly Evidenced (hypothesis)

Companies where independent public record (funding history, enterprise
customer references, disclosed financials where public, executive/founder
track record, category leadership) suggests substantial, credible evidence
across several dimensions at once.

| # | Company | Website | Stage hypothesis | Rationale |
|---|---------|---------|-------------------|-----------|
| 1 | Notion Labs | notion.com | Growth (late private) | Long-established, broad B2C+B2B adoption, well-documented enterprise expansion, multiple large funding rounds, high public brand recognition. |
| 2 | Figma | figma.com | Growth (pre-IPO) | Category-defining design/dev collaboration product, extensively documented enterprise adoption, a well-publicized (blocked) acquisition attempt that itself evidences durable strategic value, now pursuing its own IPO. |
| 3 | Databricks | databricks.com | Growth (late private) | Enterprise data/AI infrastructure with large, well-documented funding rounds, named Fortune-500-scale customers, and a mature multi-year product/engineering track record. |
| 4 | Deel | deel.com | Growth (late private) | Global payroll/HR infrastructure with rapid, well-covered revenue growth claims, large funding rounds, and broad publicized customer base across many countries. |
| 5 | Rippling | rippling.com | Growth (late private) | HR/IT/Finance SaaS suite with substantial funding, well-documented enterprise customer growth, and an experienced, previously-successful founding team. |
| 6 | Toast, Inc. | toasttab.com | Public (Growth) | Publicly traded (NYSE: TOST) restaurant technology company — real disclosed revenue and financials via SEC filings, a materially different and stronger evidence class than any private company here. |
| 7 | Faire | faire.com | Growth (late private) | B2B wholesale marketplace connecting independent retailers and brands, well-documented GMV growth claims, large funding rounds, broad press coverage of marketplace scale. |
| 8 | Klaviyo | klaviyo.com | Public (Growth) | Publicly traded (NYSE: KVYU) marketing-automation SaaS company — real disclosed revenue/financials via SEC filings. |
| 9 | Chime | chime.com | Public/late-stage (Growth) | Large-scale consumer neobank with a well-documented multi-million-user base, extensive funding history, and substantial public financial/press coverage. |
| 10 | Abnormal Security (Abnormal AI) | abnormalsecurity.com | Growth (Series D+, late private) | AI-native email/cloud security company with a large, well-covered Series D round, named enterprise customers, and strong analyst/press coverage; confirmed still independently operating (not acquired) as of this freeze. |

## Group B — Developing / Mixed (hypothesis)

Real companies with substantial, credible public evidence on *some*
dimensions, but with important, well-documented uncertainty, weakness,
decline, or unresolved controversy on others — not simply "less famous,"
but companies whose own public record is genuinely mixed.

| # | Company | Website | Stage hypothesis | Rationale |
|---|---------|---------|-------------------|-----------|
| 1 | Plaid | plaid.com | Growth (late private) | Real, substantial fintech infrastructure business and funding history, but a well-publicized failed acquisition by Visa (blocked on antitrust grounds) and widely-discussed growth/valuation-reset narrative since create genuine uncertainty. |
| 2 | Better.com | better.com | Public (via SPAC) | Real mortgage-fintech product and public listing, but extensively, publicly documented mass layoffs, a widely-covered CEO controversy, and a sharply declined valuation since IPO. |
| 3 | Bolt (bolt.com) | bolt.com | Growth (late private) | Real checkout/fintech product and funding history, but well-publicized leadership turmoil, disputed growth-metric claims, and public credibility questions from investors/press. |
| 4 | Gopuff | gopuff.com | Growth (late private) | Real, large-scale instant-delivery operation and funding history, but extensively documented layoffs, warehouse closures, and a well-covered slowdown/pivot narrative. |
| 5 | Loom | loom.com | Acquired (by Atlassian, 2023) | Real product adoption and prior funding history, but now operating inside a larger acquirer — its evidence trail as an independent "startup" is real but has a genuine, unusual discontinuity. |
| 6 | WeWork | wework.com | Post-restructuring (private) | Extremely well-documented company: real historical scale and real estate footprint, but a Chapter 11 bankruptcy (2023) and 2024 emergence under new ownership/leadership create legitimate, current uncertainty about durability. |
| 7 | Away (travel) | awaytravel.com | Growth (private) | Real, funded D2C consumer brand with real early traction, but a well-publicized 2019 workplace-culture controversy and a much lower public profile/growth narrative since. |
| 8 | Clubhouse | joinclubhouse.com | Growth (private) | Real, heavily funded product with a well-documented explosive 2020-21 rise, but an equally well-documented, substantial decline in usage/relevance since, alongside real continued operation and pivots. |
| 9 | Bumble Inc. | bumble.com | Public | Publicly traded (NASDAQ: BMBL) — real disclosed revenue and a large real user base, but well-documented stock decline, leadership changes, and competitive-pressure narratives from press/analysts. |
| 10 | Peloton Interactive | onepeloton.com | Public | Publicly traded (NASDAQ: PTON) — real historical scale and disclosed financials, but an extensively documented post-pandemic demand collapse, restructuring, and leadership churn. |

## Group C — Early / Weak / Poorly Evidenced (hypothesis)

Real, currently-operating companies whose public evidence is genuinely
thin — not fabricated, not deliberately under-described, and not selected
because they are obscure for its own sake, but because very little
independent public record yet exists for them. All ten are real,
currently-listed Y Combinator Fall 2025 batch companies (sourced from
Y Combinator's own public batch directory), i.e. genuinely early
(effectively pre-seed/seed) companies that only recently became public at
all.

| # | Company | Website | Stage hypothesis | Rationale |
|---|---------|---------|-------------------|-----------|
| 1 | Rivet | rivet.design | Pre-Seed/Seed (YC F25) | Newly launched dev-tools product; minimal independent press, no disclosed funding amount found, no third-party customer evidence beyond the company's own claims. |
| 2 | Openroll | openroll.com | Pre-Seed/Seed (YC F25) | Newly launched HR/compensation-benchmarking SaaS; same YC-batch-stage profile — essentially no independent public evidence yet beyond the company's own site and YC's own listing. |
| 3 | Fixpoint | fixpoint.co | Pre-Seed/Seed (YC F25) | Newly launched B2B hiring/staffing product; minimal public footprint beyond YC's own batch announcement. |
| 4 | Dome | domeapi.io | Pre-Seed/Seed (YC F25) | Newly launched developer-facing data API (prediction-market data); a narrow, technical product with essentially no public evidence beyond the company's own site. |
| 5 | LunaBill | lunabill.com | Pre-Seed/Seed (YC F25) | Newly launched AI voice-agent product for medical billing calls; healthcare-adjacent claims with no independent verification found. |
| 6 | Relaw | relaw.ai | Pre-Seed/Seed (YC F25) | Newly launched legal-tech SaaS; essentially no public evidence beyond the company's own site and its YC listing. |
| 7 | Sourcebot | sourcebot.dev | Pre-Seed/Seed (YC F25) | Newly launched self-hosted code-search/understanding tool aimed at developers; open-source-adjacent but minimal independent public evidence of adoption. |
| 8 | Bear AI | usebear.ai | Pre-Seed/Seed (YC F25) | Newly launched brand-visibility-monitoring tool for AI search platforms; a very new category with no independent evidence beyond the company's own claims. |
| 9 | Bravi | bravi.app | Pre-Seed/Seed (YC F25) | Newly launched AI receptionist/customer-engagement product; no independent public evidence beyond the company's own site. |
| 10 | Denki | denki.ai | Pre-Seed/Seed (YC F25) | Newly launched AI audit-automation tool; a narrow niche product with no independent public evidence beyond the company's own site. |

---

## Explicit non-goals recorded at freeze time

- No company above was chosen, swapped, or excluded based on any SIE
  output — this manifest was finalized before any of the 30 companies were
  analyzed.
- No numeric SPS was predicted for any company, individually or in
  aggregate, by group.
- `expected_group` will never be passed to `run_due_diligence()` or any
  part of the SIE pipeline. The engine receives only each company's real
  website URL.
- Group C is composed of real, currently-listed, real-website companies —
  no fictional companies, no deliberately impoverished descriptions of
  otherwise-strong companies.
- Where a company's public history includes real controversy, decline, or
  restructuring (Group B, several entries), that history is part of what
  makes public evidence about it genuinely real and mixed — it is not
  included to manufacture a "bad" example.
