"""
Phase 10.11.1 -- SPS Real-Company Validation. This is the exact same 30
companies frozen in docs/validation/SPS_REAL_COMPANY_VALIDATION_COHORT.md
before any of them were run through SIE, encoded here only so the runner
script can iterate them programmatically. This file must never be edited
after the cohort was frozen (see the manifest's own freeze timestamp) --
if it disagrees with the markdown manifest, the markdown manifest is the
source of truth.

expected_group is a validation hypothesis label used ONLY for our own
post-hoc analysis. It is never passed into run_due_diligence() or any
part of the SIE pipeline -- the engine receives nothing but each
company's real website URL, identical to any real user's own submission.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CohortCompany:
    name: str
    website: str
    expected_group: str  # "A" | "B" | "C" -- validation hypothesis only
    stage_hypothesis: str


COHORT: list[CohortCompany] = [
    # --- Group A: strong / highly evidenced (hypothesis) ---
    CohortCompany("Notion Labs", "https://www.notion.com", "A", "Growth (late private)"),
    CohortCompany("Figma", "https://www.figma.com", "A", "Growth (pre-IPO)"),
    CohortCompany("Databricks", "https://www.databricks.com", "A", "Growth (late private)"),
    CohortCompany("Deel", "https://www.deel.com", "A", "Growth (late private)"),
    CohortCompany("Rippling", "https://www.rippling.com", "A", "Growth (late private)"),
    # Corrected from https://pos.toasttab.com (a product subdomain that
    # returned HTTP 403 to the scraper) to the actual canonical root
    # domain -- corrected BEFORE any score existed for this company, so
    # this is an input-URL fix, not a results-based substitution. See
    # SPS_REAL_COMPANY_VALIDATION_REPORT.md's Input Procedure notes.
    CohortCompany("Toast, Inc.", "https://www.toasttab.com", "A", "Public (Growth)"),
    CohortCompany("Faire", "https://www.faire.com", "A", "Growth (late private)"),
    CohortCompany("Klaviyo", "https://www.klaviyo.com", "A", "Public (Growth)"),
    CohortCompany("Chime", "https://www.chime.com", "A", "Public/late-stage (Growth)"),
    CohortCompany("Abnormal Security", "https://abnormalsecurity.com", "A", "Growth (Series D+, late private)"),

    # --- Group B: developing / mixed (hypothesis) ---
    CohortCompany("Plaid", "https://plaid.com", "B", "Growth (late private)"),
    CohortCompany("Better.com", "https://better.com", "B", "Public (via SPAC)"),
    CohortCompany("Bolt", "https://www.bolt.com", "B", "Growth (late private)"),
    CohortCompany("Gopuff", "https://www.gopuff.com", "B", "Growth (late private)"),
    CohortCompany("Loom", "https://www.loom.com", "B", "Acquired (by Atlassian, 2023)"),
    CohortCompany("WeWork", "https://www.wework.com", "B", "Post-restructuring (private)"),
    CohortCompany("Away", "https://www.awaytravel.com", "B", "Growth (private)"),
    CohortCompany("Clubhouse", "https://www.joinclubhouse.com", "B", "Growth (private)"),
    CohortCompany("Bumble Inc.", "https://bumble.com", "B", "Public"),
    CohortCompany("Peloton Interactive", "https://www.onepeloton.com", "B", "Public"),

    # --- Group C: early / weak / poorly evidenced (hypothesis) ---
    # All ten are real, currently-listed Y Combinator Fall 2025 batch
    # companies (Part 5: real companies only, never fabricated).
    CohortCompany("Rivet", "https://rivet.design", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Openroll", "https://www.openroll.com", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Fixpoint", "https://www.fixpoint.co", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Dome", "https://www.domeapi.io", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("LunaBill", "https://www.lunabill.com", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Relaw", "https://www.relaw.ai", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Sourcebot", "https://www.sourcebot.dev", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Bear AI", "https://www.usebear.ai", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Bravi", "https://www.bravi.app", "C", "Pre-Seed/Seed (YC F25)"),
    CohortCompany("Denki", "https://www.denki.ai", "C", "Pre-Seed/Seed (YC F25)"),
]

assert len(COHORT) == 30
assert sum(1 for c in COHORT if c.expected_group == "A") == 10
assert sum(1 for c in COHORT if c.expected_group == "B") == 10
assert sum(1 for c in COHORT if c.expected_group == "C") == 10
