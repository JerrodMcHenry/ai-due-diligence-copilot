from dataclasses import dataclass
from typing import Literal


EvidenceRequirement = Literal[
    "Public",
    "Inferred",
    "Private",
]


@dataclass(frozen=True)
class ScoringDimension:
    name: str
    weight: float

    question: str
    description: str
    stage_guidance: str

    score_9_10: str
    score_7_8: str
    score_5_6: str
    score_3_4: str
    score_0_2: str

    strong_signals: list[str]
    weak_signals: list[str]

    evidence_priority: list[str]
    common_mistakes: list[str]
    benchmark_examples: list[str]
    diligence_questions: list[str]

    evidence_requirement: EvidenceRequirement


SCORING_METHODOLOGY = {
    "Market": [
        ScoringDimension(
            name="Market Size",
            weight=0.25,
            evidence_requirement="Public",
            question="How large is the realistic addressable market if this company executes successfully?",
            description=(
                "Evaluate venture-scale market potential. Do not punish missing TAM alone. "
                "Infer market size from customer segment, buyer budget, geography, use-case breadth, and expansion paths. "
                "A narrow initial wedge can still score highly if there is credible expansion into a large category."
            ),
            stage_guidance=(
                "Pre-seed: market can be inferred from problem severity and ICP. "
                "Seed: expect early evidence that the ICP is meaningful. "
                "Series A: expect a credible path to a large market and expansion beyond the initial wedge. "
                "Series B+: expect proof the category can support large-scale outcomes."
            ),
            score_9_10="Massive global market with multiple expansion paths and realistic multi-billion-dollar outcome potential.",
            score_7_8="Large attractive market with meaningful expansion potential and a credible venture-scale path.",
            score_5_6="Moderate market or large market with unclear path to capture meaningful share.",
            score_3_4="Limited market, narrow buyer segment, or constrained growth ceiling.",
            score_0_2="Tiny niche with little evidence of venture-scale upside.",
            strong_signals=[
                "Large enterprise or SMB budget category",
                "Global or multi-region opportunity",
                "Multiple customer segments",
                "Expansion into adjacent workflows or verticals",
                "Large recurring spend category",
                "Clear path from wedge to broader platform",
            ],
            weak_signals=[
                "Tiny niche",
                "Local-only market",
                "Single narrow buyer segment",
                "Limited expansion potential",
                "Shrinking customer base",
                "No credible path to venture-scale outcome",
            ],
                        evidence_priority=[
                "Customer segment size",
                "Buyer budget category",
                "Expansion paths",
                "Comparable public/private market categories",
                "TAM/SAM/SOM only when credible",
            ],
            common_mistakes=[
                "Do not assign a low score only because TAM is missing.",
                "Do not assume a narrow initial wedge means a small market.",
                "Do not treat vague billion-dollar market claims as proof.",
            ],
            benchmark_examples=[
                "Large enterprise software categories can support venture-scale outcomes even without explicit TAM.",
                "A narrow wedge can still score highly if expansion into adjacent workflows is credible.",
            ],
            diligence_questions=[
                "What is the realistic TAM, SAM, and SOM?",
                "Which customer segments expand the market beyond the initial wedge?",
                "Can this become a platform or does it remain a point solution?",
                "What budget category does this product pull from?",
            ],
        ),
        ScoringDimension(
            name="Market Growth",
            weight=0.20,
            evidence_requirement="Public",
            question="Is the underlying market growing rapidly?",
            description=(
                "Evaluate category growth, not just company growth. Company growth can support the assessment, "
                "but the score should reflect broader market expansion, budget growth, buyer urgency, and secular tailwinds."
            ),
            stage_guidance=(
                "Pre-seed: look for credible emerging tailwinds. "
                "Seed: expect early buyer urgency. "
                "Series A: expect clear evidence the category is expanding. "
                "Series B+: expect durable multi-year market growth."
            ),
            score_9_10="Rapidly expanding market with strong secular tailwinds, increasing budgets, and accelerating adoption.",
            score_7_8="Healthy growing market with clear demand drivers and durable category expansion.",
            score_5_6="Stable or moderately growing market with some demand tailwinds.",
            score_3_4="Slow-growth market with weak or uncertain expansion signals.",
            score_0_2="Declining market or shrinking category.",
            strong_signals=[
                "AI adoption",
                "Digital transformation",
                "Regulatory tailwinds",
                "Increasing customer budgets",
                "Growing buyer urgency",
                "Labor shortage or automation pressure",
                "Rapid category funding or adoption",
            ],
            weak_signals=[
                "Shrinking budgets",
                "Declining demand",
                "Stagnant category",
                "No clear growth driver",
                "Customer budget pressure",
            ],
                        evidence_priority=[
                "Category growth data",
                "Budget expansion",
                "Buyer urgency",
                "Company growth as supporting evidence",
                "Market reports as lower-confidence supporting evidence",
            ],
            common_mistakes=[
                "Do not confuse company revenue growth with market growth.",
                "Do not overrate a market only because it is associated with AI.",
                "Do not rely on hype without buyer-budget evidence.",
            ],
            benchmark_examples=[
                "AI adoption is a positive signal only when tied to real buyer urgency or budget shifts.",
                "A market with increasing budget allocation and urgent pain should usually score above average.",
            ],
            diligence_questions=[
                "What external forces are driving market growth?",
                "Are customer budgets increasing or shifting toward this category?",
                "Is growth durable or hype-driven?",
                "How fast are comparable categories growing?",
            ],
        ),
        ScoringDimension(
            name="Market Timing",
            weight=0.20,
            evidence_requirement="Public",
            question="Is now the right time for this solution?",
            description=(
                "Evaluate whether customer readiness, technology maturity, regulation, budgets, and workflow urgency support adoption now. "
                "Great timing means the market is being pulled open by a real change, not just a founder narrative."
            ),
            stage_guidance=(
                "Pre-seed: timing may be thesis-driven but must be plausible. "
                "Seed: expect early customer urgency. "
                "Series A: expect adoption momentum and repeatability. "
                "Series B+: timing should already be validated by scale."
            ),
            score_9_10="Excellent timing with urgent demand, technology readiness, budget availability, and clear market pull.",
            score_7_8="Good timing supported by adoption trends and customer demand.",
            score_5_6="Acceptable timing, but adoption may require education or market development.",
            score_3_4="Timing appears premature, late, or misaligned with buyer readiness.",
            score_0_2="Poor timing with little evidence customers are ready to adopt.",
            strong_signals=[
                "Customer urgency",
                "Technology inflection point",
                "Regulatory change",
                "Budget availability",
                "Pain point becoming acute",
                "Recent platform shift",
                "Manual process becoming untenable",
            ],
            weak_signals=[
                "Low buyer urgency",
                "Customers not ready",
                "Premature market",
                "Late commodity market",
                "Heavy customer education required",
            ],
                        evidence_priority=[
                "Buyer urgency",
                "Technology readiness",
                "Regulatory or platform shifts",
                "Budget availability",
                "Evidence of adoption momentum",
            ],
            common_mistakes=[
                "Do not treat founder 'why now' narrative as proof by itself.",
                "Do not ignore strong customer adoption when exact timing data is missing.",
                "Do not confuse future possibility with current readiness.",
            ],
            benchmark_examples=[
                "Clear customer urgency plus accelerating adoption usually supports a 7-8+ timing score.",
                "A new technology inflection point only matters if customers are ready to adopt.",
            ],
            diligence_questions=[
                "Why now?",
                "What changed that makes adoption possible today?",
                "Are buyers actively searching for a solution?",
                "What would have prevented this company from working five years ago?",
            ],
        ),
        ScoringDimension(
            name="Competitive Intensity",
            weight=0.15,
            evidence_requirement="Public",
            question="Can the company realistically win despite competition?",
            description=(
                "Do not penalize a startup simply because competitors exist. Attractive markets usually have competitors. "
                "Evaluate whether the company has a credible wedge, differentiation, distribution advantage, switching costs, or right to win."
            ),
            stage_guidance=(
                "Pre-seed: expect a credible wedge or unique insight. "
                "Seed: expect early differentiation. "
                "Series A: expect evidence the wedge is working. "
                "Series B+: expect durable competitive position or category leadership path."
            ),
            score_9_10="Clear wedge, durable differentiation, and credible path to category leadership despite competition.",
            score_7_8="Differentiated with manageable competition and credible right to win.",
            score_5_6="Some differentiation, but durability or positioning remains unclear.",
            score_3_4="Crowded market with limited differentiation or weak positioning.",
            score_0_2="Commodity product with no credible differentiation or path to win.",
            strong_signals=[
                "Clear wedge",
                "Switching costs",
                "Workflow lock-in",
                "Distribution advantage",
                "Unique founder insight",
                "Superior customer outcomes",
                "Proprietary data or integrations",
            ],
            weak_signals=[
                "Commodity offering",
                "No wedge",
                "Feature parity",
                "Powerful incumbents with no clear opening",
                "Undifferentiated positioning",
            ],
                        evidence_priority=[
                "Customer win/loss evidence",
                "Switching costs",
                "Differentiation customers recognize",
                "Distribution advantage",
                "Incumbent vulnerability",
            ],
            common_mistakes=[
                "Do not penalize a startup simply because competitors exist.",
                "Do not assume incumbents automatically win.",
                "Do not reward differentiation that customers do not care about.",
            ],
            benchmark_examples=[
                "A crowded market can still score well if the company has a clear wedge and strong customer pull.",
                "Deep workflow lock-in and switching costs can offset competitive intensity.",
            ],
            diligence_questions=[
                "Why will this company win?",
                "What prevents incumbents from copying it?",
                "What is the wedge into the market?",
                "Which competitor does the customer replace or avoid?",
            ],
        ),
        ScoringDimension(
            name="Customer Demand",
            weight=0.20,
            evidence_requirement="Inferred",
            question="How convincing is the evidence that customers genuinely want this product?",
            description=(
                "Evaluate actual customer pull using adoption, revenue, retention, expansion, usage, urgency, and customer outcomes. "
                "Do not require every metric to be present. Strong commercial signals can prove demand even when some market research is missing."
            ),
            stage_guidance=(
                "Pre-seed: demand can be credible discovery, LOIs, pilots, or design partners. "
                "Seed: expect pilots, early users, or early paying customers. "
                "Series A: expect repeatable demand, retention, expansion, and customer proof. "
                "Series B+: expect scalable demand across segments or geographies."
            ),
            score_9_10="Exceptional demand shown by rapid adoption, strong retention, expansion, and clear customer pull.",
            score_7_8="Strong demand with paying customers, meaningful validation, and credible repeatability.",
            score_5_6="Some validation, but demand is still emerging or inconsistent.",
            score_3_4="Limited validation, weak urgency, or unclear buyer pull.",
            score_0_2="Little or no evidence customers want the product.",
            strong_signals=[
                "Paying customers",
                "Revenue growth",
                "High retention",
                "Expansion revenue",
                "Customer case studies",
                "Strong usage",
                "Enterprise adoption",
                "Low churn",
                "Urgent buyer pain",
            ],
            weak_signals=[
                "No customers",
                "No validation",
                "Weak retention",
                "Low usage",
                "Unclear buyer pain",
                "No willingness to pay",
            ],
                        evidence_priority=[
                "Paying customers",
                "Revenue growth",
                "Retention and expansion",
                "Usage depth",
                "Customer references and case studies",
            ],
            common_mistakes=[
                "Do not require every demand metric to be present.",
                "Do not underrate demand when revenue, retention, and expansion are strong.",
                "Do not treat unpaid interest as equal to paying customers.",
            ],
            benchmark_examples=[
                "185 paying customers and 132% NRR is strong demand evidence for Series A SaaS.",
                "High retention and expansion can be stronger demand proof than survey data.",
            ],
            diligence_questions=[
                "Are customers pulling the product or being pushed?",
                "What retention and expansion signals exist?",
                "How urgent is the customer pain?",
                "What evidence shows willingness to pay?",
            ],
        ),
    ],

    "Team": [
        ScoringDimension(
            name="Founder-Market Fit",
            weight=0.25,
            evidence_requirement="Public",
            question="Does the founding team have unusually strong insight or experience in the market?",
            description=(
                "Evaluate founder connection to the customer, problem, and industry. "
                "Founder-market fit is not just resume prestige; it is evidence the team understands the problem better than others."
            ),
            stage_guidance=(
                "Pre-seed: one of the most important signals. "
                "Seed: expect customer insight to translate into product and early GTM. "
                "Series A+: expect founder-market fit to show up in traction, hiring, and strategic clarity."
            ),
            score_9_10="Exceptional founder-market fit with direct domain expertise, deep customer insight, and relevant prior success.",
            score_7_8="Strong founder-market fit with relevant experience and credible customer understanding.",
            score_5_6="Some relevant experience but not clearly advantaged.",
            score_3_4="Limited relevant experience or shallow market understanding.",
            score_0_2="No clear connection between the team and the problem.",
            strong_signals=[
                "Former buyer or operator in the target market",
                "Direct industry expertise",
                "Repeat founder",
                "Prior successful exit",
                "Deep customer knowledge",
                "Unique insight from lived experience",
                "Credibility with target buyers",
            ],
            weak_signals=[
                "No domain expertise",
                "Generic founder background",
                "Weak customer insight",
                "No evidence of problem understanding",
                "Founder narrative disconnected from market",
            ],
                        evidence_priority=[
                "Direct experience as buyer/operator",
                "Prior founder success",
                "Customer insight",
                "Domain credibility",
                "Ability to recruit customers or talent from the market",
            ],
            common_mistakes=[
                "Do not confuse elite logos with founder-market fit unless the experience is relevant.",
                "Do not overrate generic startup experience.",
                "Do not ignore lived experience or direct customer insight.",
            ],
            benchmark_examples=[
                "A former buyer/operator in the exact target market is a strong founder-market fit signal.",
                "A repeat founder with a relevant prior exit can justify an 8-9 score when paired with domain expertise.",
            ],
            diligence_questions=[
                "Why is this the right team to solve this problem?",
                "What customer insight does the team have that others lack?",
                "Have they built, sold, or operated in this market before?",
                "Do customers view the founders as credible?",
            ],
        ),
        ScoringDimension(
            name="Technical Capability",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Can the team build, maintain, and scale the product?",
            description=(
                "Evaluate technical capability relative to product complexity. "
                "A simple product requires less technical depth; AI, infrastructure, regulated workflows, and deep integrations require much more."
            ),
            stage_guidance=(
                "Pre-seed: technical founder or credible builder matters. "
                "Seed: expect MVP/product execution. "
                "Series A: expect scalable engineering capability and product reliability. "
                "Series B+: expect mature technical organization."
            ),
            score_9_10="Exceptional technical capability with proof of complex product execution and scalable architecture.",
            score_7_8="Strong technical capability with credible ability to build and scale.",
            score_5_6="Adequate capability with some scaling, reliability, or complexity risk.",
            score_3_4="Weak technical depth relative to product requirements.",
            score_0_2="No credible ability to build or maintain the product.",
            strong_signals=[
                "Technical founder",
                "Complex product already built",
                "Deep integrations",
                "AI or infrastructure expertise",
                "Relevant engineering leadership",
                "High reliability requirements handled",
                "Security or compliance capability",
            ],
            weak_signals=[
                "No technical founder",
                "Outsourced core product",
                "Unproven technical claims",
                "Poor product reliability",
                "No ability to support product complexity",
            ],
                        evidence_priority=[
                "Shipped product complexity",
                "Technical founder or engineering leadership",
                "Reliability and scalability evidence",
                "Security/compliance needs handled",
                "Deep integrations or infrastructure complexity",
            ],
            common_mistakes=[
                "Do not overrate technical capability based only on AI claims.",
                "Do not underrate simple products that do not require complex engineering.",
                "Do not ignore product reliability and integration depth.",
            ],
            benchmark_examples=[
                "Deep integrations with major enterprise systems are strong technical execution evidence.",
                "A technical leader from a relevant platform company is a strong but not sufficient signal.",
            ],
            diligence_questions=[
                "Who owns technical architecture?",
                "Can the product scale with customers and usage?",
                "What is proprietary in the technology?",
                "Where are the biggest technical risks?",
            ],
        ),
        ScoringDimension(
            name="Business Capability",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Can the team sell, operate, and build a durable company?",
            description=(
                "Evaluate commercial, operational, and company-building capability. "
                "Strong business capability shows up in GTM learning, revenue execution, pricing, unit economics, and operating discipline."
            ),
            stage_guidance=(
                "Pre-seed: expect commercial instincts and customer discovery. "
                "Seed: expect early GTM learning and willingness to iterate. "
                "Series A: expect repeatable business execution. "
                "Series B+: expect scalable business operations."
            ),
            score_9_10="Exceptional commercial execution, operating discipline, and company-building ability.",
            score_7_8="Strong business capability with credible GTM and operating execution.",
            score_5_6="Some business capability, but important gaps remain.",
            score_3_4="Limited business execution or weak commercial discipline.",
            score_0_2="No evidence of commercial or operational capability.",
            strong_signals=[
                "Revenue growth",
                "Repeatable sales motion",
                "Strong unit economics",
                "Enterprise customer acquisition",
                "Prior scaling experience",
                "Clear pricing strategy",
                "Capital efficiency",
            ],
            weak_signals=[
                "No GTM clarity",
                "Weak sales capability",
                "Poor unit economics",
                "No operating discipline",
                "Unclear pricing",
                "Founder unable to explain buyer motion",
            ],
                        evidence_priority=[
                "Revenue growth",
                "Sales repeatability",
                "Unit economics",
                "Pricing discipline",
                "Operating discipline",
            ],
            common_mistakes=[
                "Do not score business capability based only on founder charisma.",
                "Do not ignore strong unit economics.",
                "Do not confuse early founder-led sales with repeatable GTM.",
            ],
            benchmark_examples=[
                "9-month CAC payback and 5x+ LTV:CAC are strong business capability signals for SaaS.",
                "Repeatable sales into a clear ICP usually supports a 7-8+ score.",
            ],
            diligence_questions=[
                "Who owns sales and GTM?",
                "Is the sales motion repeatable?",
                "Can the team operate efficiently as it scales?",
                "Does pricing reflect value delivered?",
            ],
        ),
        ScoringDimension(
            name="Leadership",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Can the team lead, hire, and scale the organization?",
            description=(
                "Evaluate leadership maturity, hiring ability, decision quality, and ability to attract talent. "
                "Do not over-penalize missing org charts at early stages; focus on evidence of leadership capacity."
            ),
            stage_guidance=(
                "Pre-seed: founder leadership and clarity matter. "
                "Seed: expect ability to attract early hires. "
                "Series A: expect leadership depth and hiring plan. "
                "Series B+: expect executive team and scalable org design."
            ),
            score_9_10="Exceptional leadership with proven organization-building and talent attraction ability.",
            score_7_8="Strong leadership indicators with credible ability to scale.",
            score_5_6="Moderate leadership evidence with some unknowns.",
            score_3_4="Limited leadership evidence or meaningful leadership gaps.",
            score_0_2="No evidence of leadership capacity or signs of founder dysfunction.",
            strong_signals=[
                "Prior leadership roles",
                "Hiring success",
                "Strong executive team",
                "Company-building experience",
                "Clear decision-making",
                "Ability to attract senior talent",
                "Founder credibility",
            ],
            weak_signals=[
                "Founder conflict",
                "Weak hiring ability",
                "No leadership detail at later stage",
                "Poor communication",
                "Lack of ownership",
                "No operating cadence",
            ],
                        evidence_priority=[
                "Prior leadership roles",
                "Hiring success",
                "Team quality",
                "Decision quality",
                "Ability to attract investors, customers, and talent",
            ],
            common_mistakes=[
                "Do not over-penalize missing org charts at early stages.",
                "Do not assume leadership quality from titles alone.",
                "Do not ignore signs of founder dysfunction.",
            ],
            benchmark_examples=[
                "At Series A, strong founders plus evidence of early hiring can support a 7-8 score.",
                "A broader executive team matters more at Series B+ than pre-seed.",
            ],
            diligence_questions=[
                "Can the founders hire A-players?",
                "What leadership gaps exist?",
                "Can the founders scale with the company?",
                "Who owns product, GTM, engineering, and finance?",
            ],
        ),
        ScoringDimension(
            name="Execution Track Record",
            weight=0.15,
            evidence_requirement="Inferred",
            question="Has the team demonstrated the ability to execute against meaningful milestones?",
            description=(
                "Evaluate demonstrated progress, not promises. Execution track record includes product shipped, customers won, revenue grown, retention maintained, and milestones achieved."
            ),
            stage_guidance=(
                "Pre-seed: execution can be prototype, discovery, and speed of learning. "
                "Seed: expect early product and traction milestones. "
                "Series A: expect measurable growth and repeatability. "
                "Series B+: expect consistent scaling performance."
            ),
            score_9_10="Exceptional execution history with rapid progress and repeated milestone achievement.",
            score_7_8="Strong execution with clear evidence of progress.",
            score_5_6="Some execution evidence but incomplete or uneven track record.",
            score_3_4="Weak or inconsistent execution.",
            score_0_2="Little or no execution evidence.",
            strong_signals=[
                "Rapid revenue growth",
                "Product shipped",
                "Customer adoption",
                "Fundraising progress",
                "Previous exit",
                "Milestones hit",
                "Fast iteration",
            ],
            weak_signals=[
                "Slow progress",
                "Missed milestones",
                "No product shipped",
                "No customer traction",
                "Repeated pivots without learning",
                "Unclear progress",
            ],
                        evidence_priority=[
                "Milestones achieved",
                "Revenue growth",
                "Product shipped",
                "Customer adoption",
                "Retention and expansion",
            ],
            common_mistakes=[
                "Do not score promises as execution.",
                "Do not punish a young company for lacking long history if velocity is strong.",
                "Do not ignore repeated missed milestones.",
            ],
            benchmark_examples=[
                "3.5x MRR growth in 12 months is strong execution evidence for Series A SaaS.",
                "Product shipped plus paying customers is stronger than roadmap claims.",
            ],
            diligence_questions=[
                "What milestones has the team hit?",
                "How fast did they execute?",
                "What slipped and why?",
                "What did the team learn from customers?",
            ],
        ),
    ],

    "Product": [
        ScoringDimension(
            name="Customer Value",
            weight=0.25,
            evidence_requirement="Inferred",
            question="Does the product solve an important customer problem with measurable value?",
            description=(
                "Evaluate pain severity, ROI, workflow importance, and customer outcomes. "
                "High retention and expansion are strong evidence of customer value, especially in B2B SaaS."
            ),
            stage_guidance=(
                "Pre-seed: value can be qualitative from discovery. "
                "Seed: expect early user or customer proof. "
                "Series A: expect measurable customer outcomes and retention. "
                "Series B+: expect proven ROI across many customers."
            ),
            score_9_10="Exceptional customer value with urgent pain, measurable ROI, and strong customer outcomes.",
            score_7_8="Strong customer value with meaningful impact and credible proof.",
            score_5_6="Moderate value but not clearly mission-critical or not well-proven.",
            score_3_4="Weak value proposition or unclear customer benefit.",
            score_0_2="No clear customer value.",
            strong_signals=[
                "Measurable ROI",
                "High retention",
                "Expansion revenue",
                "Urgent workflow pain",
                "Mission-critical use case",
                "Strong customer outcomes",
                "Low churn",
            ],
            weak_signals=[
                "Nice-to-have product",
                "Weak ROI",
                "Unclear pain",
                "Low usage",
                "No customer outcomes",
                "Low willingness to pay",
            ],
                        evidence_priority=[
                "Measured ROI",
                "Retention and expansion",
                "Customer outcome data",
                "Mission-critical workflow evidence",
                "Willingness to pay",
            ],
            common_mistakes=[
                "Do not require perfect usage analytics when retention and ROI are strong.",
                "Do not confuse feature novelty with customer value.",
                "Do not overrate nice-to-have products with weak retention.",
            ],
            benchmark_examples=[
                "132% NRR and low churn are strong customer value signals in B2B SaaS.",
                "45-60% manual work reduction is meaningful ROI if credible and repeatable.",
            ],
            diligence_questions=[
                "What ROI does the product deliver?",
                "Is the product mission-critical?",
                "What happens if customers stop using it?",
                "Which workflow does it replace or improve?",
            ],
        ),
        ScoringDimension(
            name="Differentiation",
            weight=0.20,
            evidence_requirement="Public",
            question="Is the product meaningfully different from alternatives?",
            description=(
                "Evaluate whether the product has a clear wedge, superior customer outcome, unique workflow, or insight that competitors lack. "
                "Do not confuse differentiation with feature count."
            ),
            stage_guidance=(
                "Pre-seed: expect thesis-level differentiation. "
                "Seed: expect early proof customers care about the difference. "
                "Series A: expect differentiation recognized by customers. "
                "Series B+: expect differentiation that supports durable market position."
            ),
            score_9_10="Highly differentiated with a clear durable wedge and superior customer outcomes.",
            score_7_8="Meaningfully differentiated with strong positioning.",
            score_5_6="Some differentiation, but risk of imitation or commoditization remains.",
            score_3_4="Limited differentiation or unclear wedge.",
            score_0_2="Undifferentiated commodity product.",
            strong_signals=[
                "Unique workflow",
                "Better customer outcomes",
                "AI advantage",
                "Deep domain insight",
                "Clear wedge",
                "Proprietary data",
                "Distinct buyer insight",
            ],
            weak_signals=[
                "Feature parity",
                "No clear wedge",
                "Commodity positioning",
                "Similar competitors",
                "No customer-recognized advantage",
            ],
                        evidence_priority=[
                "Customer-recognized advantage",
                "Win/loss evidence",
                "Unique workflow or data",
                "Integration depth",
                "Superior outcomes",
            ],
            common_mistakes=[
                "Do not confuse having AI with differentiation.",
                "Do not reward feature count if customers do not care.",
                "Do not underrate workflow-specific differentiation.",
            ],
            benchmark_examples=[
                "Deep ERP integrations can support differentiation, but proprietary data or unique workflow advantage strengthens the score.",
                "If incumbents can easily copy the product and customers do not perceive a difference, score should stay near 5-6 or lower.",
            ],
            diligence_questions=[
                "Why is this product better?",
                "What do customers choose it over?",
                "Can competitors copy it easily?",
                "What is the product wedge?",
            ],
        ),
        ScoringDimension(
            name="Usability",
            weight=0.15,
            evidence_requirement="Public",
            question="Can customers adopt and use the product with low friction?",
            description=(
                "Evaluate onboarding, workflow fit, implementation burden, UX, and ease of adoption. "
                "For enterprise products, some implementation complexity is acceptable if value and retention are strong."
            ),
            stage_guidance=(
                "Pre-seed: usability can be early and prototype-based. "
                "Seed: expect usable MVP and early feedback. "
                "Series A: expect repeatable onboarding and adoption. "
                "Series B+: expect scalable implementation and customer success processes."
            ),
            score_9_10="Very easy adoption with excellent workflow fit, low friction, and strong user satisfaction.",
            score_7_8="Good usability and adoption experience.",
            score_5_6="Usable, but with onboarding, implementation, or workflow friction.",
            score_3_4="Difficult adoption or high customer friction.",
            score_0_2="Hard to use or unlikely to be adopted.",
            strong_signals=[
                "Easy onboarding",
                "Workflow integration",
                "Low implementation burden",
                "Strong user feedback",
                "Fast time to value",
                "High activation",
            ],
            weak_signals=[
                "Complex setup",
                "Long implementation",
                "Poor UX",
                "High training burden",
                "Slow time to value",
                "Low activation",
            ],
                        evidence_priority=[
                "Time to value",
                "Activation",
                "Implementation time",
                "User satisfaction",
                "Customer success burden",
            ],
            common_mistakes=[
                "Do not assume enterprise implementation complexity means poor usability.",
                "Do not overrate usability without user or onboarding evidence.",
                "Do not ignore retention as a usability proxy.",
            ],
            benchmark_examples=[
                "Fast time-to-value and low onboarding friction support 8+ usability.",
                "Enterprise products can still score well with implementation if ROI and retention are strong.",
            ],
            diligence_questions=[
                "How long does implementation take?",
                "Who uses the product daily?",
                "What causes adoption friction?",
                "How fast do customers reach value?",
            ],
        ),
        ScoringDimension(
            name="Defensibility",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Can the product become difficult to copy or replace?",
            description=(
                "Evaluate moats beyond patents: switching costs, data, workflow lock-in, integrations, network effects, ecosystem position, regulatory complexity, and distribution. "
                "Retention and deep integrations can be strong defensibility signals."
            ),
            stage_guidance=(
                "Pre-seed: defensibility may be thesis-based. "
                "Seed: expect emerging wedge. "
                "Series A: expect evidence of lock-in, data, integrations, or superior distribution. "
                "Series B+: expect durable moat strengthening with scale."
            ),
            score_9_10="Very strong defensibility through multiple durable moats that improve with scale.",
            score_7_8="Strong defensibility through integrations, data, lock-in, distribution, or ecosystem position.",
            score_5_6="Some defensibility, but not yet durable or proven.",
            score_3_4="Limited defensibility and easy to copy.",
            score_0_2="No defensibility.",
            strong_signals=[
                "Switching costs",
                "Deep integrations",
                "Proprietary data",
                "Network effects",
                "Workflow lock-in",
                "Regulatory complexity",
                "Distribution advantage",
                "Ecosystem partnerships",
            ],
            weak_signals=[
                "Easy to copy",
                "No switching costs",
                "No proprietary advantage",
                "No ecosystem position",
                "Low retention",
                "No compounding advantage",
            ],
                        evidence_priority=[
                "Switching costs",
                "Proprietary data",
                "Deep integrations",
                "Workflow lock-in",
                "Network effects",
                "Distribution advantage",
            ],
            common_mistakes=[
                "Do not assume patents are required.",
                "Do not confuse early differentiation with durable defensibility.",
                "Do not ignore retention and integrations as moat signals.",
            ],
            benchmark_examples=[
                "Deep integrations plus high retention can justify strong defensibility in enterprise SaaS.",
                "Patents are not required; workflow lock-in, data, and distribution can be stronger moats.",
            ],
            diligence_questions=[
                "What is the moat?",
                "What gets stronger with scale?",
                "Why won't incumbents copy it?",
                "How costly is it for customers to switch?",
            ],
        ),
        ScoringDimension(
            name="Adoption Potential",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Can adoption scale meaningfully across customers, teams, or markets?",
            description=(
                "Evaluate whether the product can spread across users, teams, accounts, geographies, or adjacent use cases. "
                "Expansion revenue, low churn, and enterprise adoption are strong adoption-potential signals."
            ),
            stage_guidance=(
                "Pre-seed: assess likely adoption path. "
                "Seed: expect early adoption or pilots. "
                "Series A: expect repeatable adoption and expansion potential. "
                "Series B+: expect scalable adoption motion."
            ),
            score_9_10="Exceptional adoption potential with strong pull, low friction, and multiple expansion paths.",
            score_7_8="Strong adoption potential with credible scaling motion.",
            score_5_6="Moderate adoption potential with some friction or narrowness.",
            score_3_4="Limited adoption potential due to friction or narrow use case.",
            score_0_2="Very low adoption potential.",
            strong_signals=[
                "Repeatable sales motion",
                "Low churn",
                "Expansion revenue",
                "Enterprise adoption",
                "Multi-seat usage",
                "Multi-team usage",
                "Strong customer references",
            ],
            weak_signals=[
                "Long sales cycle with weak conversion",
                "Low usage",
                "Narrow use case",
                "Difficult onboarding",
                "No expansion path",
                "Low willingness to adopt",
            ],
                        evidence_priority=[
                "Expansion revenue",
                "Low churn",
                "Sales repeatability",
                "Multi-seat or multi-team usage",
                "Customer references",
            ],
            common_mistakes=[
                "Do not confuse current adoption with future adoption potential.",
                "Do not ignore expansion paths inside existing accounts.",
                "Do not overrate adoption if onboarding is very heavy and ROI is unclear.",
            ],
            benchmark_examples=[
                "Enterprise customers plus high NRR suggests strong adoption potential.",
                "A product that expands from one team into many workflows can score 8+.",
            ],
            diligence_questions=[
                "Can this expand inside accounts?",
                "What limits adoption?",
                "Is the sales or adoption motion repeatable?",
                "What is the natural expansion path?",
            ],
        ),
    ],

    "Execution": [
        ScoringDimension(
            name="Go-to-Market Execution",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is the company effectively acquiring customers through a repeatable motion?",
            description=(
                "Evaluate ICP clarity, pipeline, sales motion, acquisition efficiency, sales cycle, and repeatability. "
                "Strong retention and efficient CAC can support GTM execution even if every pipeline metric is not present."
            ),
            stage_guidance=(
                "Pre-seed: GTM may be founder-led discovery. "
                "Seed: expect GTM learning and early repeatability. "
                "Series A: expect a repeatable motion and sales efficiency signals. "
                "Series B+: expect scalable GTM engine."
            ),
            score_9_10="Exceptional GTM with rapid acquisition, efficient CAC, clear ICP, and repeatable scalable motion.",
            score_7_8="Strong GTM execution with credible repeatability.",
            score_5_6="Some GTM traction, but repeatability or efficiency remains unclear.",
            score_3_4="Weak GTM execution or unclear sales motion.",
            score_0_2="No evidence of customer acquisition ability.",
            strong_signals=[
                "Repeatable sales motion",
                "Clear ICP",
                "Efficient CAC",
                "Strong pipeline",
                "Enterprise customers",
                "Shortening sales cycle",
                "High conversion",
            ],
            weak_signals=[
                "No GTM clarity",
                "Weak pipeline",
                "High CAC",
                "Unclear buyer",
                "Founder-only selling with no repeatability",
                "Long sales cycle with low conversion",
            ],
                        evidence_priority=[
                "Repeatable sales motion",
                "CAC payback",
                "Pipeline quality",
                "Sales cycle and conversion",
                "ICP clarity",
            ],
            common_mistakes=[
                "Do not overrate one-off founder-led sales.",
                "Do not ignore efficient CAC payback.",
                "Do not require every funnel metric if growth and sales efficiency are strong.",
            ],
            benchmark_examples=[
                "CAC payback under 12 months is excellent for SaaS.",
                "Clear ICP plus repeatable outbound and strong retention supports 8+ GTM execution.",
            ],
            diligence_questions=[
                "Is GTM repeatable?",
                "What is CAC by channel?",
                "How strong is the pipeline?",
                "What is the sales cycle and conversion rate?",
            ],
        ),
        ScoringDimension(
            name="Product Execution",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is the team executing well on product development and delivery?",
            description=(
                "Evaluate product maturity, roadmap delivery, reliability, integrations, iteration speed, and customer outcomes. "
                "Customer value and retention are strong signals that product execution is working."
            ),
            stage_guidance=(
                "Pre-seed: expect prototype or MVP progress. "
                "Seed: expect usable product and iteration. "
                "Series A: expect mature product serving real customers. "
                "Series B+: expect scalable product organization and reliability."
            ),
            score_9_10="Exceptional product execution with mature product, fast iteration, reliability, and strong customer outcomes.",
            score_7_8="Strong product execution with credible maturity and delivery.",
            score_5_6="Moderate product execution with remaining gaps.",
            score_3_4="Weak product execution or slow delivery.",
            score_0_2="No credible product execution.",
            strong_signals=[
                "Product shipped",
                "Deep integrations",
                "High reliability",
                "Strong customer outcomes",
                "Fast iteration",
                "Roadmap milestones hit",
                "Strong retention",
            ],
            weak_signals=[
                "Immature product",
                "Quality issues",
                "Unclear roadmap",
                "Slow development",
                "Poor reliability",
                "Weak customer outcomes",
            ],
                        evidence_priority=[
                "Product shipped",
                "Customer outcomes",
                "Reliability",
                "Integration depth",
                "Roadmap velocity",
            ],
            common_mistakes=[
                "Do not judge product execution only by roadmap documentation.",
                "Do not ignore customer outcomes and retention.",
                "Do not overrate unshipped product vision.",
            ],
            benchmark_examples=[
                "Deep integrations with strong customer outcomes support strong product execution.",
                "A mature product serving enterprise customers typically should not score below 7 without quality issues.",
            ],
            diligence_questions=[
                "What has shipped?",
                "What is roadmap velocity?",
                "How reliable is the product?",
                "What product milestones are next?",
            ],
        ),
        ScoringDimension(
            name="Operational Execution",
            weight=0.20,
            evidence_requirement="Private",
            question="Can the company operate efficiently as it scales?",
            description=(
                "Evaluate burn discipline, margins, runway, hiring, processes, and operating cadence. "
                "Do not over-penalize missing process details if financial and growth metrics show strong operating discipline."
            ),
            stage_guidance=(
                "Pre-seed: lightweight operations are acceptable. "
                "Seed: expect basic discipline. "
                "Series A: expect scalable operating cadence and hiring plan. "
                "Series B+: expect mature operations."
            ),
            score_9_10="Exceptional operating discipline with efficient growth, strong margins, and scalable processes.",
            score_7_8="Strong operational execution with healthy discipline and scaling potential.",
            score_5_6="Adequate operations with some scaling risk.",
            score_3_4="Weak operations, inefficient scaling, or poor discipline.",
            score_0_2="Poor operating discipline that threatens the company.",
            strong_signals=[
                "Efficient burn",
                "Healthy margins",
                "Strong runway",
                "Hiring plan",
                "Operational processes",
                "Revenue growth relative to spend",
                "Clear ownership",
            ],
            weak_signals=[
                "High burn",
                "No operating discipline",
                "Weak hiring plan",
                "Process gaps",
                "Growth inefficient relative to spend",
                "Short runway",
            ],
                        evidence_priority=[
                "Burn efficiency",
                "Gross margin",
                "Runway",
                "Hiring discipline",
                "Revenue growth relative to spend",
            ],
            common_mistakes=[
                "Do not over-penalize missing operating-process detail if financial metrics are strong.",
                "Do not ignore burn relative to revenue.",
                "Do not reward low burn if it reflects underinvestment and slow growth.",
            ],
            benchmark_examples=[
                "82% gross margin and 25 months runway are strong operating signals.",
                "Burn below or near MRR with strong growth suggests good operational discipline.",
            ],
            diligence_questions=[
                "Can operations scale?",
                "Is burn disciplined?",
                "What team or process gaps exist?",
                "How does spend map to milestones?",
            ],
        ),
        ScoringDimension(
            name="Strategic Execution",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is the company making strategically sound decisions?",
            description=(
                "Evaluate positioning, focus, sequencing, wedge strategy, partnerships, and competitive response. "
                "A strong strategy should explain why this company can win from its current position."
            ),
            stage_guidance=(
                "Pre-seed: expect focused wedge and clear thesis. "
                "Seed: expect clear ICP and learning loop. "
                "Series A: expect coherent expansion strategy. "
                "Series B+: expect durable category and competitive strategy."
            ),
            score_9_10="Exceptional strategic clarity with strong wedge, sequencing, and path to category leadership.",
            score_7_8="Strong strategy with credible path to scale.",
            score_5_6="Reasonable strategy but important unknowns remain.",
            score_3_4="Weak strategy, unclear positioning, or poor sequencing.",
            score_0_2="No credible strategy.",
            strong_signals=[
                "Clear wedge",
                "Strong positioning",
                "Logical expansion",
                "Strategic partnerships",
                "Competitive response",
                "Focused ICP",
                "Clear use of capital",
            ],
            weak_signals=[
                "Unclear strategy",
                "Weak positioning",
                "No expansion logic",
                "Reactive decisions",
                "Too many customer segments too early",
                "No competitive response",
            ],
                        evidence_priority=[
                "Clear wedge",
                "ICP focus",
                "Expansion sequence",
                "Competitive response",
                "Use of capital",
            ],
            common_mistakes=[
                "Do not reward vague strategy language.",
                "Do not confuse broad ambition with strategic clarity.",
                "Do not ignore lack of focus across too many segments.",
            ],
            benchmark_examples=[
                "A focused wedge into a large category with logical expansion supports a 7-8+ score.",
                "Clear use of funds tied to growth milestones improves strategic execution.",
            ],
            diligence_questions=[
                "What is the wedge?",
                "What is the sequencing from wedge to platform?",
                "How does strategy respond to competition?",
                "What strategic choices has the company rejected?",
            ],
        ),
        ScoringDimension(
            name="Execution Velocity",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is the company moving fast enough relative to its stage?",
            description=(
                "Evaluate speed of revenue growth, customer acquisition, product delivery, hiring, and milestone achievement. "
                "Velocity should be judged relative to stage and business model."
            ),
            stage_guidance=(
                "Pre-seed: velocity is learning and building. "
                "Seed: velocity is PMF progress and early traction. "
                "Series A: velocity is repeatable growth and scaling. "
                "Series B+: velocity is efficient expansion."
            ),
            score_9_10="Exceptional velocity with rapid growth, fast learning, and repeated milestone achievement.",
            score_7_8="Strong velocity for the company’s stage.",
            score_5_6="Moderate velocity with some progress but not exceptional.",
            score_3_4="Slow progress relative to stage.",
            score_0_2="Stalled execution.",
            strong_signals=[
                "Rapid MRR growth",
                "Fast customer acquisition",
                "Product velocity",
                "Hiring momentum",
                "Milestones hit",
                "Fast sales learning",
                "Strong expansion",
            ],
            weak_signals=[
                "Flat growth",
                "Slow product progress",
                "Missed milestones",
                "Stalled GTM",
                "Slow learning",
                "Low urgency",
            ],
                        evidence_priority=[
                "Revenue growth rate",
                "Customer growth",
                "Product milestones",
                "Hiring momentum",
                "Learning velocity",
            ],
            common_mistakes=[
                "Do not require all velocity metrics if revenue and customer growth are strong.",
                "Do not mistake activity for progress.",
                "Do not ignore stagnation after fundraising.",
            ],
            benchmark_examples=[
                "3.5x MRR growth in 12 months is strong Series A velocity.",
                "Fast customer acquisition plus strong retention is more meaningful than feature release count alone.",
            ],
            diligence_questions=[
                "How fast is revenue growing?",
                "What milestones were hit?",
                "Where is execution slow?",
                "What is the next major milestone?",
            ],
        ),
    ],

    "Traction": [
        ScoringDimension(
            name="Customer Growth",
            weight=0.20,
            evidence_requirement="Public",
            question="Is the customer base growing meaningfully for the company's stage?",
            description=(
                "Evaluate customer acquisition relative to stage, segment, ACV, and business model. "
                "Enterprise companies may have fewer customers but higher quality accounts."
            ),
            stage_guidance=(
                "Pre-seed: customers are not required, but strong discovery helps. "
                "Seed: expect pilots, design partners, or early customers. "
                "Series A: expect meaningful customer base growth. "
                "Series B+: expect scalable customer acquisition."
            ),
            score_9_10="Exceptional customer growth with clear market pull and high-quality customer acquisition.",
            score_7_8="Strong customer growth for the stage and business model.",
            score_5_6="Moderate customer growth or promising but incomplete acquisition evidence.",
            score_3_4="Weak customer growth or unclear acquisition motion.",
            score_0_2="Little or no customer growth.",
            strong_signals=[
                "Growing customer count",
                "Enterprise adoption",
                "Repeatable acquisition",
                "Strong pipeline",
                "High-quality customers",
                "Logo growth",
                "Expansion into target ICP",
            ],
            weak_signals=[
                "No customers",
                "Flat customer count",
                "Weak acquisition",
                "Unclear pipeline",
                "Poor customer quality",
                "No repeatability",
            ],
                        evidence_priority=[
                "Customer count growth",
                "Enterprise account growth",
                "Pipeline conversion",
                "Customer quality",
                "Repeatability",
            ],
            common_mistakes=[
                "Do not compare enterprise customer count directly to PLG user count.",
                "Do not ignore customer quality and ACV.",
                "Do not overrate pilot counts without conversion.",
            ],
            benchmark_examples=[
                "42 enterprise accounts can be very strong for Series A B2B SaaS.",
                "Customer count should be judged relative to ACV and sales motion.",
            ],
            diligence_questions=[
                "How fast is customer count growing?",
                "What is customer quality?",
                "Is acquisition repeatable?",
                "How does customer growth compare to similar companies at this stage?",
            ],
        ),
        ScoringDimension(
            name="Revenue Growth",
            weight=0.20,
            evidence_requirement="Public",
            question="Is revenue growing strongly relative to stage and business model?",
            description=(
                "Evaluate revenue growth rate, new logo growth, expansion revenue, ACV, and revenue durability. "
                "Expansion-driven growth and high NRR are especially strong signals in SaaS."
            ),
            stage_guidance=(
                "Pre-seed: revenue is optional. "
                "Seed: early revenue is a strong signal. "
                "Series A: expect repeatable revenue growth. "
                "Series B+: expect scalable and efficient growth."
            ),
            score_9_10="Exceptional revenue growth for the stage, supported by durable customers and/or expansion.",
            score_7_8="Strong revenue growth with credible repeatability.",
            score_5_6="Moderate revenue growth or promising but inconsistent monetization.",
            score_3_4="Weak revenue growth or unclear monetization.",
            score_0_2="No revenue, declining revenue, or no willingness to pay.",
            strong_signals=[
                "Rapid MRR or ARR growth",
                "ARR expansion",
                "Strong ACV",
                "Expansion revenue",
                "High NRR",
                "Repeatable sales motion",
                "Pricing power",
            ],
            weak_signals=[
                "No revenue",
                "Flat revenue",
                "Declining revenue",
                "Weak monetization",
                "Low ACV with high CAC",
                "No expansion revenue",
            ],
                        evidence_priority=[
                "MRR/ARR growth",
                "YoY or trailing growth",
                "Expansion revenue",
                "ACV",
                "New-logo growth",
            ],
            common_mistakes=[
                "Do not ignore expansion-led growth.",
                "Do not compare low-ACV PLG growth directly to enterprise SaaS growth.",
                "Do not overrate growth if churn or CAC is poor.",
            ],
            benchmark_examples=[
                "3.5x MRR growth in 12 months is exceptional for many Series A SaaS companies.",
                "High NRR makes revenue growth more durable.",
            ],
            diligence_questions=[
                "What is YoY or trailing 12-month revenue growth?",
                "Is growth from new logos or expansion?",
                "Is revenue durable and recurring?",
                "What is ACV and sales cycle?",
            ],
        ),
        ScoringDimension(
            name="Retention",
            weight=0.20,
            evidence_requirement="Public",
            question="Are customers staying, renewing, and expanding?",
            description=(
                "Evaluate churn, NRR, GRR, renewals, expansion, and customer stickiness. "
                "For B2B SaaS, retention can be stronger evidence of product-market fit than surface-level usage metrics."
            ),
            stage_guidance=(
                "Pre-seed: retention may be unavailable. "
                "Seed: early retention and repeat usage matter. "
                "Series A: retention is critical. "
                "Series B+: retention must support efficient scaling."
            ),
            score_9_10="Exceptional retention and expansion with very low churn and strong customer stickiness.",
            score_7_8="Strong retention and positive expansion signals.",
            score_5_6="Moderate retention with some churn or insufficient history.",
            score_3_4="Weak retention or concerning churn.",
            score_0_2="Severe churn or no evidence customers stay.",
            strong_signals=[
                "High NRR",
                "High GRR",
                "Low churn",
                "Renewals",
                "Expansion revenue",
                "Multi-year contracts",
                "High switching costs",
            ],
            weak_signals=[
                "High churn",
                "Weak retention",
                "No renewals",
                "Low expansion",
                "Short-lived usage",
                "Customers fail to activate",
            ],
                        evidence_priority=[
                "NRR",
                "GRR",
                "Logo churn",
                "Renewals",
                "Expansion revenue",
            ],
            common_mistakes=[
                "Do not treat missing DAU as weak retention.",
                "Do not underrate retention when NRR and churn are strong.",
                "Do not ignore cohort maturity.",
            ],
            benchmark_examples=[
                "NRR above 130% is excellent for Series A SaaS.",
                "GRR above 90% is strong for many B2B SaaS businesses.",
                "Monthly logo churn below 1.5% is strong if sustained.",
            ],
            diligence_questions=[
                "What is NRR?",
                "What is GRR?",
                "Why do customers churn?",
                "How much growth comes from expansion?",
            ],
        ),
        ScoringDimension(
            name="Engagement",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Are customers actively using the product in a way that indicates durable value?",
            description=(
                "Evaluate usage frequency, workflow depth, automation volume, active users, and outcome evidence. "
                "For enterprise SaaS, retention, expansion, and workflow embedding can substitute for consumer-style DAU/MAU metrics."
            ),
            stage_guidance=(
                "Pre-seed: qualitative engagement may count. "
                "Seed: expect usage signals from early users. "
                "Series A: expect measurable engagement or strong proxy metrics such as retention and workflow depth. "
                "Series B+: expect robust usage analytics."
            ),
            score_9_10="Exceptional usage depth, workflow embedding, and outcome evidence.",
            score_7_8="Strong engagement supported by usage data, retention, expansion, or workflow depth.",
            score_5_6="Some engagement evidence but incomplete metrics.",
            score_3_4="Weak usage or shallow engagement.",
            score_0_2="Little or no engagement evidence.",
            strong_signals=[
                "High usage frequency",
                "Workflow volume",
                "Active users",
                "Deep workflow adoption",
                "Customer outcome data",
                "High retention",
                "Expansion revenue",
                "Embedded integrations",
            ],
            weak_signals=[
                "No usage metrics",
                "Low activity",
                "Shallow usage",
                "Weak stickiness",
                "Low retention",
                "No workflow dependency",
            ],
                        evidence_priority=[
                "Workflow usage depth",
                "Usage frequency",
                "Automation volume",
                "Retention and expansion as proxies",
                "Customer outcome data",
            ],
            common_mistakes=[
                "Do not require consumer-style DAU/MAU for enterprise SaaS.",
                "Do not ignore retention and expansion as engagement proxies.",
                "Do not overrate shallow login activity without workflow value.",
            ],
            benchmark_examples=[
                "High NRR plus deep workflow integrations can justify a strong engagement score even without DAU.",
                "Workflow volume and automation frequency are better engagement metrics than page views for B2B tools.",
            ],
            diligence_questions=[
                "How often is the product used?",
                "How deep is workflow adoption?",
                "What usage predicts retention?",
                "What workflow volume runs through the product?",
            ],
        ),
        ScoringDimension(
            name="Commercial Validation",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is there convincing commercial proof that the business works?",
            description=(
                "Evaluate paying customers, renewals, expansion, pricing power, unit economics, case studies, and referenceability. "
                "Commercial validation should be judged relative to stage and sales motion."
            ),
            stage_guidance=(
                "Pre-seed: commercial validation may be LOIs, paid pilots, or design partners. "
                "Seed: expect early paid proof. "
                "Series A: expect strong commercial evidence and repeatability. "
                "Series B+: expect scalable commercial engine."
            ),
            score_9_10="Exceptional commercial validation with strong revenue, retention, economics, references, and repeatability.",
            score_7_8="Strong commercial validation with paying customers and credible proof.",
            score_5_6="Some commercial proof but still early or incomplete.",
            score_3_4="Limited commercial validation.",
            score_0_2="No commercial validation.",
            strong_signals=[
                "Paying customers",
                "Strong ACV",
                "Good unit economics",
                "Case studies",
                "Expansion revenue",
                "Renewals",
                "Reference customers",
                "Repeatable sales",
            ],
            weak_signals=[
                "No paying customers",
                "No renewals",
                "Weak pricing",
                "No customer proof",
                "Pilot-only traction",
                "No referenceability",
            ],
                        evidence_priority=[
                "Paying customers",
                "Renewals",
                "Expansion",
                "Reference customers",
                "Unit economics",
            ],
            common_mistakes=[
                "Do not treat unpaid pilots as equal to paid customers.",
                "Do not ignore case studies and references when paired with revenue.",
                "Do not overrate revenue that is non-recurring or unsustainable.",
            ],
            benchmark_examples=[
                "185 paying customers, strong ACV, and 5x+ LTV:CAC are strong Series A commercial validation.",
                "Referenceable enterprise customers materially strengthen commercial validation.",
            ],
            diligence_questions=[
                "Are customers paying real money?",
                "Is pricing sustainable?",
                "Do customers renew and expand?",
                "Can customers serve as references?",
            ],
        ),
    ],

    "Financial Health": [
        ScoringDimension(
            name="Revenue Quality",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is revenue durable, recurring, and high quality?",
            description=(
                "Evaluate recurring revenue, retention, predictability, concentration, customer quality, and contract durability. "
                "High NRR and low churn are strong indicators of high-quality SaaS revenue."
            ),
            stage_guidance=(
                "Pre-seed: revenue optional. "
                "Seed: revenue quality may be early. "
                "Series A: revenue quality matters heavily. "
                "Series B+: revenue quality must support scaling and valuation."
            ),
            score_9_10="Exceptional recurring revenue quality with strong retention, predictability, and customer quality.",
            score_7_8="Strong revenue quality with good recurring characteristics.",
            score_5_6="Moderate revenue quality with some risks or insufficient history.",
            score_3_4="Weak or low-quality revenue.",
            score_0_2="No meaningful revenue or poor-quality revenue.",
            strong_signals=[
                "Recurring revenue",
                "High NRR",
                "High GRR",
                "Low churn",
                "Enterprise customers",
                "Predictable contracts",
                "Expansion revenue",
            ],
            weak_signals=[
                "One-time revenue",
                "High churn",
                "Customer concentration risk",
                "Unclear contracts",
                "Low renewal rates",
                "Unpredictable revenue",
            ],
                        evidence_priority=[
                "Recurring revenue",
                "NRR",
                "GRR",
                "Customer concentration",
                "Contract predictability",
            ],
            common_mistakes=[
                "Do not treat all revenue equally.",
                "Do not ignore churn or concentration.",
                "Do not overrate one-time services revenue.",
            ],
            benchmark_examples=[
                "132% NRR is excellent revenue quality for SaaS.",
                "94% GRR is strong if measured over a meaningful customer cohort.",
            ],
            diligence_questions=[
                "Is revenue recurring?",
                "How concentrated is revenue?",
                "What is renewal quality?",
                "How predictable is expansion?",
            ],
        ),
        ScoringDimension(
            name="Unit Economics",
            weight=0.20,
            evidence_requirement="Public",
            question="Are the economics of acquiring and serving customers attractive?",
            description=(
                "Evaluate gross margin, CAC payback, LTV:CAC, pricing power, sales efficiency, and expansion. "
                "Strong unit economics can materially increase investment attractiveness."
            ),
            stage_guidance=(
                "Pre-seed: unit economics may be unknown. "
                "Seed: expect directional signals. "
                "Series A: expect credible unit economics. "
                "Series B+: expect proven economics at scale."
            ),
            score_9_10="Exceptional unit economics with high margin, fast payback, strong LTV:CAC, and efficient expansion.",
            score_7_8="Strong unit economics with attractive margin and acquisition efficiency.",
            score_5_6="Acceptable economics with uncertainty or incomplete proof.",
            score_3_4="Weak unit economics or concerning acquisition costs.",
            score_0_2="Unsustainable unit economics.",
            strong_signals=[
                "High gross margin",
                "Fast CAC payback",
                "Strong LTV:CAC",
                "Efficient sales motion",
                "Expansion revenue",
                "Pricing power",
                "Low servicing cost",
            ],
            weak_signals=[
                "Low margin",
                "Long CAC payback",
                "Poor LTV:CAC",
                "Unclear pricing",
                "High servicing cost",
                "Growth dependent on unsustainable spend",
            ],
                        evidence_priority=[
                "Gross margin",
                "CAC payback",
                "LTV:CAC",
                "Sales efficiency",
                "Expansion economics",
            ],
            common_mistakes=[
                "Do not score missing unit economics as poor performance by default at pre-seed.",
                "Do not ignore CAC payback and gross margin when provided.",
                "Do not overrate LTV:CAC if churn assumptions are weak.",
            ],
            benchmark_examples=[
                "Gross margin above 80% is excellent for SaaS.",
                "CAC payback under 12 months is excellent.",
                "LTV:CAC above 3x is generally strong; 5x+ is very strong if assumptions are sound.",
            ],
            diligence_questions=[
                "What is CAC payback?",
                "What is LTV:CAC?",
                "Do economics hold as sales scales?",
                "What happens to margins as the company grows?",
            ],
        ),
        ScoringDimension(
            name="Burn Efficiency",
            weight=0.20,
            evidence_requirement="Private",
            question="Is the company using capital efficiently?",
            description=(
                "Evaluate burn relative to revenue, growth, stage, and milestones. "
                "High burn is acceptable only if it creates strong growth, learning, or durable advantage."
            ),
            stage_guidance=(
                "Pre-seed: burn should be controlled and learning-focused. "
                "Seed: spend should create PMF evidence. "
                "Series A: burn should map to repeatable growth. "
                "Series B+: burn efficiency should support scalable expansion."
            ),
            score_9_10="Exceptional capital efficiency with strong growth relative to spend.",
            score_7_8="Good burn efficiency with disciplined spend and clear growth output.",
            score_5_6="Moderate burn efficiency with some uncertainty.",
            score_3_4="Concerning burn efficiency or weak growth relative to spend.",
            score_0_2="Severe burn problem threatening company viability.",
            strong_signals=[
                "Revenue exceeds burn",
                "Efficient growth",
                "Disciplined spend",
                "Strong margin",
                "Clear use of capital",
                "Low burn multiple",
                "Milestones tied to spend",
            ],
            weak_signals=[
                "High burn",
                "Weak growth relative to spend",
                "No spend discipline",
                "Unclear capital plan",
                "Runway pressure",
                "Hiring ahead of proof",
            ],
                        evidence_priority=[
                "Burn multiple",
                "Revenue relative to burn",
                "Growth per dollar spent",
                "Gross margin",
                "Runway impact",
            ],
            common_mistakes=[
                "Do not reward under-spending if growth is too slow.",
                "Do not punish burn if it is efficiently producing growth.",
                "Do not ignore burn relative to MRR/ARR.",
            ],
            benchmark_examples=[
                "MRR above monthly burn with strong growth is a positive efficiency signal.",
                "A low burn multiple is more important at later stages than pre-seed.",
            ],
            diligence_questions=[
                "What is burn multiple?",
                "How does spend map to growth?",
                "Can burn be reduced if needed?",
                "What milestones does current burn unlock?",
            ],
        ),
        ScoringDimension(
            name="Runway",
            weight=0.20,
            evidence_requirement="Public",
            question="Does the company have enough cash runway to reach the next major milestone?",
            description=(
                "Evaluate cash runway relative to fundraising needs, growth plan, market conditions, and stage. "
                "Runway should be judged by whether it gets the company to a stronger financing or strategic position."
            ),
            stage_guidance=(
                "Pre-seed/Seed: runway should support the next proof milestone. "
                "Series A: runway should support scaling and next raise. "
                "Series B+: runway should support efficient growth and strategic flexibility."
            ),
            score_9_10="Excellent runway with strong flexibility and enough time to reach meaningful milestones.",
            score_7_8="Healthy runway with manageable financing risk.",
            score_5_6="Adequate runway, but fundraising timing matters.",
            score_3_4="Short runway or material fundraising pressure.",
            score_0_2="Critical runway risk.",
            strong_signals=[
                "18+ months runway",
                "Strong cash position",
                "Controlled burn",
                "Clear fundraising plan",
                "Milestone-based capital plan",
                "Ability to reduce burn",
            ],
            weak_signals=[
                "Short runway",
                "High burn",
                "Unclear financing",
                "Immediate cash risk",
                "No milestone plan",
                "Dependence on difficult fundraise",
            ],
                        evidence_priority=[
                "Months of runway",
                "Cash on hand",
                "Burn rate",
                "Milestone plan",
                "Fundraising environment",
            ],
            common_mistakes=[
                "Do not score runway without considering burn flexibility.",
                "Do not ignore whether runway reaches the next fundable milestone.",
                "Do not treat cash balance alone as runway.",
            ],
            benchmark_examples=[
                "18+ months runway is generally healthy.",
                "24+ months runway is strong if spend is disciplined.",
                "Less than 6 months runway is usually a major risk unless financing is imminent.",
            ],
            diligence_questions=[
                "How many months of runway remain?",
                "What milestone will current cash reach?",
                "When is the next raise needed?",
                "Can burn be flexed if fundraising conditions worsen?",
            ],
        ),
        ScoringDimension(
            name="Fundraising Readiness",
            weight=0.20,
            evidence_requirement="Inferred",
            question="Is the company well positioned to raise capital for the next milestone?",
            description=(
                "Evaluate whether team, market, traction, metrics, narrative, and use of funds support the next financing. "
                "Fundraising readiness is not just whether the company needs money; it is whether investors have a compelling reason to invest now."
            ),
            stage_guidance=(
                "Pre-seed: team, market, and insight matter most. "
                "Seed: early proof and founder-market fit matter. "
                "Series A: metrics, repeatability, and market narrative matter. "
                "Series B+: scale, efficiency, and category leadership matter."
            ),
            score_9_10="Exceptional fundraising profile likely to attract strong investor interest and competitive terms.",
            score_7_8="Strong fundraising readiness with credible metrics and narrative.",
            score_5_6="Some readiness but important gaps remain.",
            score_3_4="Weak fundraising profile with serious investor objections.",
            score_0_2="Not ready for institutional capital.",
            strong_signals=[
                "Strong growth",
                "Strong retention",
                "Experienced founders",
                "Healthy unit economics",
                "Large market",
                "Clear use of funds",
                "Strong investor narrative",
                "Reference customers",
            ],
            weak_signals=[
                "Weak metrics",
                "Unclear market",
                "Poor economics",
                "No investor narrative",
                "Short runway",
                "Weak team",
                "No milestone clarity",
            ],
                        evidence_priority=[
                "Growth",
                "Retention",
                "Team quality",
                "Market size",
                "Use of funds",
                "Investor narrative",
            ],
            common_mistakes=[
                "Do not equate needing money with being fundable.",
                "Do not ignore investor objections.",
                "Do not overrate a raise plan without metrics or milestones.",
            ],
            benchmark_examples=[
                "Strong growth, 130%+ NRR, strong unit economics, and relevant founders make a compelling Series A profile.",
                "A clear use of funds tied to enterprise sales or product expansion improves fundraising readiness.",
            ],
            diligence_questions=[
                "Why fund this company now?",
                "What milestones will capital unlock?",
                "What investor objections remain?",
                "What round size and use of funds are justified?",
            ],
        ),
    ],
}
