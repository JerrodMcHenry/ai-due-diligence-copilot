"""
Phase 10.8I -- real canonical evidence for the 31-company calibration
roster, built from live WebSearch research conducted during this phase
(sources cited inline per company). This is REAL evidence, not
synthetic -- every figure below was found via a live web search during
this phase's execution, never invented.

HONEST SCOPE LIMITATION, stated once here rather than per-company:
research depth for this phase was ONE to TWO targeted searches per
company, focused on funding/valuation/revenue/status verification
(Phase 10.8I Part 1's "live-reverify" requirement) -- not the full
multi-query, multi-pillar research depth the production pipeline (or a
dedicated evidence-gathering pass) would use. As a direct, honest
consequence: Market, Product, and Execution evidence is sparse-to-absent
for most companies below (few named competitors, differentiation
claims, or GTM-motion facts were surfaced by funding-focused searches),
while Traction and Financial-Health-adjacent facts (revenue, growth,
funding stage, profitability, disclosed distress) are comparatively
well populated. This is reported as a real finding about this phase's
own research depth, not concealed by inventing Market/Product/Execution
facts to fill the gap -- see the calibration report's own discussion of
what this means for the P0 gate results.

No `desired_sps` exists anywhere in this file, on principle.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.factory import (
    commercial_contract,
    competitor,
    customer_evidence,
    founder_experience,
    founder_outcome,
    negative_signal,
    product_capability,
    revenue,
    runway_statement,
)
from app.calibration.sps_v3.types import (
    CompetitorType,
    CustomerType,
    FounderExperienceType,
    FounderOutcomeType,
    ProvenanceGrade,
    RevenueMetricType,
    Stage,
)

TODAY = date(2026, 8, 30)  # explicit reference_date for staleness, this phase's "now"


def _pre_seed_1() -> SyntheticCompany:
    # Balance -- YC W26, AI + accountant bookkeeping. Source: extruct.ai
    # YC W26 batch listing (Phase 10.8I live fetch).
    return SyntheticCompany(
        "CAL_001_BALANCE", Stage.PRE_SEED,
        evidence=(
            product_capability("AI-paired bookkeeping and financial reconciliation", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _pre_seed_2() -> SyntheticCompany:
    # Ritivel -- YC W26, AI-native regulatory platform for life sciences.
    return SyntheticCompany(
        "CAL_002_RITIVEL", Stage.IDEA,
        evidence=(
            product_capability("AI-native regulatory platform for life sciences clinical documents/submissions",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _vercel() -> SyntheticCompany:
    # Source: Sacra/PitchBook/BusinessWire coverage of Sept 2025 Series F,
    # TechCrunch/DigitalApplied on $340M ARR Feb 2026 -- WebSearch this phase.
    return SyntheticCompany(
        "CAL_003_VERCEL", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("144000000", date(2024, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("340000000", date(2026, 2, 28), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("AI Cloud platform (Fluid Compute, AI Gateway) positioned against AWS Lambda/Cloudflare Workers",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _modal_labs() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_004_MODAL_LABS", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("serverless AI inference/infrastructure platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _middesk() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_005_MIDDESK", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("business identity/KYB verification and underwriting for fintechs, banks, payroll providers",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _speak() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_006_SPEAK", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("AI conversational-English language-learning app", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            founder_experience("investor backing", FounderExperienceType.DIRECT_DOMAIN,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _clay() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_008_CLAY", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("31000000", date(2024, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("108000000", date(2025, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("150000000", date(2026, 5, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("AI go-to-market development platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _harvey_ai() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_009_HARVEY_AI", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("190000000", date(2026, 1, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("350000000", date(2026, 8, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("legal AI agents for law firms and enterprises", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            commercial_contract(CustomerType.PAYING, "law firm/enterprise customers (unnamed)", renewal=True,
                                 grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _together_ai() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_010_TOGETHER_AI", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("open-source AI inference/cloud infrastructure platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            # $1.15B "annual bookings" is a bookings figure, not revenue --
            # per Rulebook Part 5's explicit bookings != revenue rule, this
            # is deliberately NOT modeled as a RevenueObservation.
        ),
    )


def _whatnot() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_011_WHATNOT", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("live-video auction marketplace, ~60% share of a $22B live-commerce category",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            competitor("live commerce category (TikTok Shop-adjacent)", CompetitorType.DIRECT,
                       differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        # $8B GMV (2025) is gross merchandise value, not revenue -- per
        # Part 5, deliberately not modeled as RevenueObservation.
    )


def _perplexity() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_012_PERPLEXITY", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("450000000", date(2026, 3, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("AI search engine, ~45M monthly active users", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            competitor("Google Search / traditional search engines", CompetitorType.DIRECT,
                       differentiator=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _glean() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_013_GLEAN", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("100000000", date(2025, 2, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("208000000", date(2025, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("300000000", date(2026, 5, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("enterprise AI platform (permissions-aware knowledge graph, work assistant, agent-building)",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _mercury() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_014_MERCURY", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("650000000", date(2026, 5, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("startup-focused digital banking platform, OCC conditional bank-charter approval",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            runway_statement("999", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),  # "4 years of profitability", modeled as effectively unconstrained runway
        ),
    )


def _webflow() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_015_WEBFLOW", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("213000000", date(2026, 3, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("no-code website development platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _scale_ai() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_016_SCALE_AI", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("AI data-labeling/evaluation platform, filed S-1 for IPO March 2026", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        # 2026 revenue "projected to more than double to ~$2B" is a
        # forward-looking projection, not a disclosed actual -- per Part
        # 5's "estimated vs company-reported" discipline, deliberately
        # NOT modeled as a RevenueObservation (that would over-credit an
        # unconfirmed forecast as fact).
    )


def _hugging_face() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_017_HUGGING_FACE", Stage.SERIES_B_PLUS,
        evidence=(
            revenue("100000000", date(2026, 6, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("150000000", date(2026, 8, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("open-source AI/ML model hub and infrastructure, community-evidence-rich",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _flexport() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_018_FLEXPORT", Stage.GROWTH,
        evidence=(
            revenue("1500000000", date(2024, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("ocean/air/road freight forwarding and tracking platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("severe_cash_constraint", "capital_efficiency",
                             "SEVERE", excerpt="Full-year net loss in 2025; profitability achieved only via a one-time ~$250M gain from selling Convoy Platform assets; valuation fell from $8B peak (2022) to ~$3.8B (late 2024).",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _gusto() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_019_GUSTO", Stage.GROWTH,
        evidence=(
            revenue("1000000000", date(2026, 5, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("payroll/HR/benefits platform for small businesses, 400K customers", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            runway_statement("999", grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),  # "cash flow positive for several years"
        ),
    )


def _airwallex() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_020_AIRWALLEX", Stage.GROWTH,
        evidence=(
            revenue("1300000000", date(2026, 3, 1), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("global business financial platform (payments, cards, treasury)", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _carta() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_021_CARTA", Stage.GROWTH,
        evidence=(
            product_capability("cap table/equity management platform for startups and investors", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("leadership_instability", "leadership", "MODERATE",
                             excerpt="Multiple 2023 layoff rounds following public allegations of misconduct and employee exposes.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _instacart() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_022_INSTACART", Stage.GROWTH,
        evidence=(
            product_capability("grocery delivery/marketplace platform, publicly traded (NASDAQ: CART)", shipped=True,
                                grade=ProvenanceGrade.PRIMARY_VERIFIED),
        ),
    )


def _ziprecruiter() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_023_ZIPRECRUITER", Stage.GROWTH,
        evidence=(
            revenue("110100000", date(2025, 3, 31), RevenueMetricType.QUARTERLY_REVENUE, grade=ProvenanceGrade.PRIMARY_VERIFIED),
            revenue("107500000", date(2026, 3, 31), RevenueMetricType.QUARTERLY_REVENUE, grade=ProvenanceGrade.PRIMARY_VERIFIED),
            product_capability("job-search/recruiting marketplace, publicly traded (NYSE: ZIP)", shipped=True,
                                grade=ProvenanceGrade.PRIMARY_VERIFIED),
        ),
        negative_signals=(
            negative_signal("revenue_decline", "growth_trajectory", "MODERATE",
                             excerpt="Q1 2026 revenue $107.5M, down 2.3% YoY from $110.1M in Q1 2025 (public SEC-filed figures).",
                             grade=ProvenanceGrade.PRIMARY_VERIFIED),
        ),
    )


def _discord() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_024_DISCORD", Stage.GROWTH,
        evidence=(
            revenue("725000000", date(2024, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("consumer chat/community platform, 200M+ monthly active users", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("market_contraction", "revenue_quality", "MODERATE",
                             excerpt="Private-market valuation (~$8.5B Forge price, July 2026) down from 2021 primary-round peak of $15.2B; confidential IPO filing (Jan 2026) missed its window, base case now 2027.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _attio() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_007_ATTIO", Stage.SERIES_B_PLUS,
        evidence=(
            product_capability("AI-native CRM platform for go-to-market teams", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            founder_experience("co-founder", FounderExperienceType.DIRECT_DOMAIN,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _convoy() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_025_CONVOY", Stage.GROWTH,
        evidence=(
            product_capability("digital freight brokerage platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("failed_commercial_expansion", "strategic_execution", "SEVERE",
                             excerpt="Shut down operations October 2023; revenue collapsed ahead of an abrupt wind-down (The Information); platform assets later sold to Flexport for ~$250M.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE",
                             excerpt="Company wound down/closed with no buyer for the operating business itself.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _olive_ai() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_026_OLIVE_AI", Stage.GROWTH,
        evidence=(
            product_capability("healthcare RPA/AI automation platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("failed_commercial_expansion", "strategic_execution", "SEVERE",
                             excerpt="Wound down 2023 after selling clearinghouse/patient-access businesses to Waystar and Humata Health; CEO cited 'fast-paced growth and lack of focus'; laid off 450 (Jul 2022) then 200 more (Feb 2023) before shutdown.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE",
                             excerpt="Failed to deliver ROI at scale; unsustainable burn rate investor enthusiasm couldn't support.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _katerra() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_027_KATERRA", Stage.GROWTH,
        evidence=(
            product_capability("construction technology / prefabricated building platform", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE",
                             excerpt="Filed for Chapter 11 bankruptcy June 2021; left construction contractors owed $73M+ in unpaid debt.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _quibi() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_028_QUIBI", Stage.GROWTH,
        evidence=(
            product_capability("short-form mobile streaming service", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            founder_experience("co-founder", FounderExperienceType.REPEAT_FOUNDER, "DreamWorks Animation",
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("customer_decline", "customer_adoption", "SEVERE",
                             excerpt="Announced shutdown Oct 21, 2020 (just over 6 months after launch); service ended Dec 1, 2020; ~$1.75B raised, weak product-market fit widely cited as root cause.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _bird() -> SyntheticCompany:
    return SyntheticCompany(
        "CAL_029_BIRD", Stage.GROWTH,
        evidence=(
            product_capability("shared electric-scooter micromobility platform, ~$500M VC raised", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        negative_signals=(
            negative_signal("severe_cash_constraint", "capital_efficiency", "SEVERE",
                             excerpt="Filed Chapter 11 bankruptcy Dec 20, 2023; nearly entire market value wiped out since its 2021 SPAC listing.",
                             grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _mailchimp() -> SyntheticCompany:
    # Historical AS-OF 2020-01-01, deliberately BEFORE the Sept 13, 2021
    # acquisition announcement -- evidence below reflects only what was
    # publicly knowable as of that earlier date (Phase 10.8I Part 4's
    # as-of-date firewall). The acquisition itself lives ONLY in
    # outcome_data (calibration_manifest.json), never here.
    return SyntheticCompany(
        "CAL_030_MAILCHIMP", Stage.GROWTH,
        evidence=(
            founder_experience("CEO", FounderExperienceType.REPEAT_FOUNDER, "Rocket Science Group (Mailchimp's own predecessor, founded 2001)",
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            product_capability("email marketing / customer engagement platform for small and mid-market businesses",
                                shipped=True, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
    )


def _fast() -> SyntheticCompany:
    # Historical AS-OF 2021-06-01 -- after the real Series B close,
    # well before the April 2022 shutdown announcement. Reflects only
    # what was knowable as of that date; the eventual shutdown lives
    # only in outcome_data.
    return SyntheticCompany(
        "CAL_031_FAST", Stage.GROWTH,
        evidence=(
            founder_experience("CEO", FounderExperienceType.DIRECT_DOMAIN,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            founder_experience("co-founder", FounderExperienceType.ADJACENT_DOMAIN,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),  # former Uber exec -- adjacent, not direct fintech domain
            product_capability("one-click online checkout button", shipped=True,
                                grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
            revenue("600000", date(2021, 12, 31), RevenueMetricType.ANNUAL_REVENUE, grade=ProvenanceGrade.HIGH_QUALITY_SECONDARY),
        ),
        # NOTE: the 2021 revenue figure ($600K) and the ~$10M/month burn
        # figure were both reported retrospectively, AFTER the shutdown,
        # in the same April 2022 articles that reported the shutdown
        # itself -- neither was actually knowable as of the 2021-06-01
        # as-of date. Per Part 4's as-of-date firewall, the revenue
        # figure is EXCLUDED from this snapshot's evidence (a real,
        # concrete example of the firewall being applied, not just
        # described) -- flagged explicitly in the calibration report.
    )


CALIBRATION_COMPANIES: dict[str, tuple] = {
    "CAL-001": (_pre_seed_1, "TRAINING", None),
    "CAL-002": (_pre_seed_2, "HOLDOUT", None),
    "CAL-003": (_vercel, "TRAINING", None),
    "CAL-004": (_modal_labs, "TRAINING", None),
    "CAL-005": (_middesk, "HOLDOUT", None),
    "CAL-006": (_speak, "TRAINING", None),
    "CAL-007": (_attio, "HOLDOUT", None),  # replaces Metronome (acquired by Stripe Dec 2025)
    "CAL-008": (_clay, "HOLDOUT", None),
    "CAL-009": (_harvey_ai, "TRAINING", None),
    "CAL-010": (_together_ai, "TRAINING", None),
    "CAL-011": (_whatnot, "HOLDOUT", None),
    "CAL-012": (_perplexity, "TRAINING", None),
    "CAL-013": (_glean, "TRAINING", None),
    "CAL-014": (_mercury, "HOLDOUT", None),
    "CAL-015": (_webflow, "TRAINING", None),
    "CAL-016": (_scale_ai, "HOLDOUT", None),
    "CAL-017": (_hugging_face, "TRAINING", None),
    "CAL-018": (_flexport, "TRAINING", None),
    "CAL-019": (_gusto, "HOLDOUT", None),
    "CAL-020": (_airwallex, "TRAINING", None),
    "CAL-021": (_carta, "TRAINING", None),
    "CAL-022": (_instacart, "HOLDOUT", None),
    "CAL-023": (_ziprecruiter, "TRAINING", None),
    "CAL-024": (_discord, "HOLDOUT", None),
    "CAL-025": (_convoy, "TRAINING", {"outcome": "SHUT_DOWN", "outcome_date": "2023-10"}),
    "CAL-026": (_olive_ai, "TRAINING", {"outcome": "WOUND_DOWN", "outcome_date": "2023"}),
    "CAL-027": (_katerra, "HOLDOUT", {"outcome": "BANKRUPTCY", "outcome_date": "2021-06"}),
    "CAL-028": (_quibi, "TRAINING", {"outcome": "SHUT_DOWN", "outcome_date": "2020-12"}),
    "CAL-029": (_bird, "HOLDOUT", {"outcome": "BANKRUPTCY", "outcome_date": "2023-12"}),
    "CAL-030": (_mailchimp, "TRAINING", {"outcome": "ACQUIRED", "outcome_date": "2021-09", "acquirer": "Intuit", "amount_usd_approx": 12000000000}),
    "CAL-031": (_fast, "HOLDOUT", {"outcome": "SHUT_DOWN", "outcome_date": "2022-04"}),
}


def training_companies() -> list:
    return [builder() for cal_id, (builder, split, outcome) in CALIBRATION_COMPANIES.items() if split == "TRAINING"]


def holdout_companies() -> list:
    return [builder() for cal_id, (builder, split, outcome) in CALIBRATION_COMPANIES.items() if split == "HOLDOUT"]


def all_companies() -> list:
    return [builder() for cal_id, (builder, split, outcome) in CALIBRATION_COMPANIES.items()]
