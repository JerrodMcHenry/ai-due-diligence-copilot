// Learn V1 -- Contextual Founder Education, Part 26/2's investigation.
//
// WHAT ALREADY FUNCTIONED AS "LEARN" BEFORE THIS PHASE:
//   - Founder Playbooks (content/playbooks/) -- full "HOW DO I DO THIS?"
//     guides, already reused everywhere via lib/playbooks/resourceMap.ts.
//   - VPSResultPanel's own "What does this score mean?" disclosure and
//     Build V3's per-field source-quote hints (components/idea-lab/
//     AssumptionFields.tsx's `hint` prop) -- both real, but neither
//     explains WHAT a concept like GTM Feasibility or CAC actually is.
//   - "Learn" in the account menu already points at /playbooks (Part 13
//     -- confirmed still correct, see the final report; not touched).
// THE GAP: no layer answers "what is this term/category, and why does it
// matter" in plain language, in context, before a founder reaches for a
// full Playbook. That gap is this file's entire scope.
//
// Two exported registries, kept deliberately separate (see types.ts):
//
// VPS_CATEGORY_CONCEPTS -- one entry per real VPS category key
// (app/ai/vps_scoring.py::VPS_CATEGORIES). Framed as a question per
// category, per Part 5's own worked example. Never restates or implies
// the internal weighting/formula (Part 5: "Do not expose internal
// scoring formulas. Do not teach founders how to game VPS.").
//
// METRIC_CONCEPTS -- ONLY concepts actually surfaced by a real field
// label or What If scenario today (Part 7: "Select concepts actually
// surfaced in the current product," "Do NOT blindly implement all of
// these"). Audited directly against:
//   - VentureAssumptions field labels (AssumptionFields.tsx call sites
//     in VentureDraftReview.tsx / VentureWorkspace.tsx)
//   - whatIfScenarios.ts's own scenario questions
// Confirmed jargon actually shown to a founder: CAC ("Expected CAC
// ($)"), gross margin ("Expected gross margin (%)"), retention
// ("Retention (%)", plus "churn" appearing literally in a What If
// question), and monthly burn ("Monthly burn ($)"). Everything else in
// Part 7's candidate list (LTV, MRR, ARR, ACV, market size, willingness
// to pay, ICP, PMF) is either never shown as UI text (MRR/ARR/ACV are
// only ever unit-converted server-side, never displayed as acronyms --
// the app already follows Part 8's "plain language first" instinct by
// simply not using them) or already in plain, self-explanatory language
// (paying customers, price point, market size dropdown) -- adding a
// concept card for a term that isn't actually jargon would be exactly
// the "educational clutter everywhere" Part 4 warns against. "Runway" is
// closely related to burn but is never itself a field, label, or
// computed value anywhere in the product -- explained briefly inside the
// burn concept's own whyItMatters instead of getting its own unused
// entry. "Market size" and "customer validation" are deliberately NOT
// separate metric concepts either -- they're exactly what the
// market_potential / validation VPS_CATEGORY_CONCEPTS entries below
// already cover; a second, overlapping concept card would be redundant.
//
// Part 16 (fundraising foundation): MetricConcept/VpsCategoryConcept are
// already fully generic -- a future SAFE/valuation/dilution concept
// needs no shape change, just a new data entry. None are added here.
import type { MetricConcept, VpsCategoryConcept } from "./types.ts";

export const VPS_CATEGORY_CONCEPTS: Record<string, VpsCategoryConcept> = {
  market_potential: {
    key: "market_potential",
    question: "How big is the opportunity, and how much room is there to grow?",
    whyItMatters:
      "Even a great product has a ceiling if the market it sells into is small, shrinking, or dominated by a few strong competitors. This looks at how much real room there is to build a large business here.",
  },
  problem_solution: {
    key: "problem_solution",
    question: "Is this solving a real problem, in a way that's genuinely different from what already exists?",
    whyItMatters:
      "A product nobody urgently needs is hard to sell no matter how well it's built. This looks at how clearly the problem is defined and how convincingly the solution addresses it.",
  },
  founder_readiness: {
    key: "founder_readiness",
    question: "Does this founding team have what it takes to execute on this specific idea?",
    whyItMatters:
      "Investors and early customers are betting on the team as much as the idea itself -- relevant experience and complementary skills make execution meaningfully more likely to succeed.",
  },
  gtm_feasibility: {
    key: "gtm_feasibility",
    // Part 5's own exact worked example -- kept verbatim.
    question: "Can this venture consistently reach and acquire customers?",
    whyItMatters: "A strong product can still fail if customers are too expensive or too difficult to acquire.",
  },
  economic_potential: {
    key: "economic_potential",
    question: "If this works, does the underlying business make financial sense?",
    whyItMatters:
      "A business can have happy customers and still lose money on every sale. This looks at whether the pricing and cost structure could realistically support a healthy company.",
  },
  validation: {
    key: "validation",
    question: "How much of this is backed by real evidence, rather than a guess?",
    whyItMatters:
      "Ideas are cheap to have and expensive to be wrong about. Real conversations, signups, and paying customers are what separate a plausible story from actual proof.",
  },
};

export const METRIC_CONCEPTS: Record<string, MetricConcept> = {
  cac: {
    key: "cac",
    name: "Customer acquisition cost (CAC)",
    whatIsThis:
      "Customer acquisition cost is roughly how much you spend, on average, to gain one new paying customer -- marketing, ads, sales time, tools, anything that goes into winning that customer.",
    whyItMatters:
      // Part 3's own worked example, kept close to verbatim.
      "If it costs more to acquire a customer than that customer is worth to you over time, growing faster can make the business worse, not better. There's no universal 'good' number here -- it depends entirely on your price and how long customers stick around.",
    playbookSlug: "go-to-market",
    personalize: (value) =>
      value === null
        ? "Your model doesn't have a customer acquisition cost yet. That's normal early on -- as you start spending on marketing or sales, track what you spend and how many customers each channel actually produces."
        : `Your current model assumes it costs about $${value.toLocaleString()} to acquire one customer.`,
  },
  gross_margin: {
    key: "gross_margin",
    name: "Gross margin",
    whatIsThis:
      "Gross margin is the percentage of revenue left over after covering the direct cost of delivering your product -- for software that's often hosting and support; for a physical product it's the cost of goods.",
    whyItMatters:
      "It's a rough ceiling on how much you have left to spend on growth, salaries, and everything else and still make money. A thin margin means you need a lot of volume just to break even.",
    playbookSlug: "pricing",
    personalize: (value) =>
      value === null
        ? "Your model doesn't have a gross margin estimate yet. Even a rough guess is useful here -- it doesn't need to be exact this early."
        : `Your current model uses an estimated gross margin of ${value}%.`,
  },
  retention: {
    key: "retention",
    name: "Retention",
    whatIsThis:
      "Retention is how much of your revenue or customer base sticks around over time instead of leaving. Measured the other way around -- the share you lose -- it's usually called churn. Net revenue retention specifically tracks how existing customers' spending changes after upgrades, downgrades, and cancellations.",
    whyItMatters:
      "Winning a customer only to lose them a month later is expensive and makes growth much harder. Strong retention means the customers you already have keep paying, so growth compounds instead of constantly replacing what leaked out.",
    playbookSlug: "early-traction",
    personalize: (value) =>
      value === null
        ? "Your model doesn't have a retention figure yet. That's expected before you have paying customers to measure -- once you do, tracking who stays and who leaves each month is one of the most useful things you can watch."
        : `Your current model assumes about ${value}% retention.`,
  },
  burn: {
    key: "burn",
    name: "Monthly burn",
    whatIsThis:
      "Monthly burn is how much cash your company spends each month beyond what it brings in -- essentially, how fast your bank balance is shrinking.",
    whyItMatters:
      "Combined with how much cash you have, burn tells you your runway -- roughly how many months you can keep operating before you run out of money. Watching it early avoids being surprised later.",
    // Deliberately no playbookSlug -- no existing Playbook is genuinely
    // about burn/runway management (Cap Table & Dilution is about
    // ownership and raise terms, a different topic); forcing that link
    // would be exactly the "weak match just to have a link" Part 3
    // warns against.
    personalize: (value) =>
      value === null
        ? "Your model doesn't have a monthly burn figure yet. That's expected before you're actively spending -- once you are, this is worth tracking closely alongside how much cash you have on hand."
        : `Your current model assumes you're spending about $${value.toLocaleString()} more than you bring in each month.`,
  },
};

// Phase 21B -- Fundraising Simulator V1, Part 15. Extends the SAME
// METRIC_CONCEPTS registry (no new registry/shape needed -- the comment
// at the top of this file already anticipated this addition) with the
// fundraising terms Fundraising Simulator surfaces via ConceptDisclosure.
// Beginner-first, never legal advice, never a duplicate of the "Cap Table
// & Dilution" / "Fundraising" Playbooks' own step-by-step HOW content --
// these are the WHAT/WHY layer only (see this file's own docstring on the
// Learn vs. Playbook split).
const FUNDRAISING_CONCEPTS: Record<string, MetricConcept> = {
  safe: {
    key: "safe",
    name: "SAFE (Simple Agreement for Future Equity)",
    whatIsThis:
      "A SAFE is a common early-stage investment document where an investor gives you money now in exchange for equity later -- usually when you raise a priced round in the future. It is not a loan (no interest, no repayment obligation) and it is not equity yet.",
    whyItMatters:
      "SAFEs let founders raise money quickly without agreeing on a company valuation up front. But the terms you agree to now -- especially the valuation cap -- determine how much ownership that money converts into later, so it's worth understanding before you sign one.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a SAFE amount yet. Once you enter one, you can see roughly what it would be worth if it converted today."
        : `This scenario models a SAFE investment of about $${value.toLocaleString()}.`,
  },
  valuation_cap: {
    key: "valuation_cap",
    name: "Valuation cap",
    whatIsThis:
      "The maximum company valuation used to determine how a cap SAFE converts into equity in a future financing.",
    whyItMatters:
      "A lower cap can result in the SAFE investor receiving more ownership when the SAFE converts. The cap doesn't set your company's actual value -- it only sets a ceiling for this specific conversion calculation.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a valuation cap set yet."
        : `This scenario uses a valuation cap of about $${value.toLocaleString()}.`,
  },
  pre_money_valuation: {
    key: "pre_money_valuation",
    name: "Pre-money valuation",
    whatIsThis: "The value investors and founders agree your company is worth BEFORE new investment money is added.",
    whyItMatters:
      "Pre-money valuation is the starting point for figuring out how much of the company a new investor's money buys -- a higher pre-money valuation means the same investment buys a smaller percentage.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a pre-money valuation set yet."
        : `This scenario uses a pre-money valuation of about $${value.toLocaleString()}.`,
  },
  post_money_valuation: {
    key: "post_money_valuation",
    name: "Post-money valuation",
    whatIsThis: "Pre-money valuation plus the new money raised -- your company's value immediately AFTER the investment closes.",
    whyItMatters:
      "An investor's resulting ownership percentage is roughly their investment divided by the post-money valuation -- this is the number that actually determines how much of the company changed hands.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a post-money valuation yet."
        : `In this scenario, the post-money valuation works out to about $${value.toLocaleString()}.`,
  },
  dilution: {
    key: "dilution",
    name: "Dilution",
    whatIsThis:
      "Dilution is what happens to your ownership percentage when new shares are issued -- your number of shares doesn't change, but the total number of shares does, so your slice of the pie gets smaller. A drop from 25% to 20% is 5 percentage points, but it's 20% dilution (you lost a fifth of what you had) -- these two ways of describing the same change are not interchangeable.",
    whyItMatters:
      "Every SAFE, option pool, or priced round dilutes existing shareholders to some degree. Dilution itself isn't inherently bad -- it's usually the cost of raising money to grow -- but it's worth seeing plainly rather than being surprised by it later.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a dilution figure yet."
        : `In this scenario, this represents about ${value} percentage point${value === 1 ? "" : "s"} of change to that stakeholder's ownership.`,
  },
  priced_round: {
    key: "priced_round",
    name: "Priced round",
    whatIsThis:
      "Unlike a SAFE, a priced round sets an actual company valuation and issues real equity to investors immediately, rather than a promise of future equity.",
    whyItMatters:
      "A priced round is usually the point where any outstanding SAFEs convert into real shares, alongside the new investor's own shares -- it's often the first time a company's cap table becomes fully concrete.",
    playbookSlug: "fundraising",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a priced round modeled yet."
        : `This scenario models new shares being priced at about $${value} per share.`,
  },
  option_pool: {
    key: "option_pool",
    name: "Option pool",
    whatIsThis: "A block of shares set aside -- usually before a raise -- to grant to future employees as equity compensation.",
    whyItMatters:
      "Creating or increasing an option pool dilutes existing shareholders just like issuing shares to an investor does. When a pool is expanded as part of a priced round, that dilution is typically borne by existing shareholders (like founders), not by the incoming investor.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't include an option pool change."
        : `This scenario adds an option pool increase of about ${value}% of the company's current shares.`,
  },
  fully_diluted_ownership: {
    key: "fully_diluted_ownership",
    name: "Fully diluted ownership",
    whatIsThis:
      "Your ownership percentage counting every share that could exist -- issued shares, outstanding options, and any unissued option pool -- not just the shares that have been formally issued today.",
    whyItMatters:
      "Fully diluted ownership is the honest number: it's what your stake actually looks like once every already-promised share is accounted for, which is why it's the standard way cap tables are measured.",
    playbookSlug: "cap-table",
    personalize: (value) =>
      value === null
        ? "This scenario doesn't have a fully diluted share count yet."
        : `This scenario's fully diluted cap table totals about ${value.toLocaleString()} shares.`,
  },
  pro_rata_rights: {
    key: "pro_rata_rights",
    name: "Pro-rata rights",
    whatIsThis:
      "A pro-rata right lets an existing investor invest additional money in a future round to maintain their current ownership percentage, rather than being diluted like other existing shareholders.",
    whyItMatters:
      "Pro-rata rights are common in SAFEs and priced rounds, and can meaningfully affect how much room is left for new investors in a future round. Fundraising Simulator V1 does not calculate pro-rata scenarios -- this is background context only.",
    playbookSlug: "fundraising",
    personalize: (value) =>
      value === null
        ? "Pro-rata rights aren't modeled in this scenario."
        : `A pro-rata right of about ${value}% is referenced in this scenario's terms.`,
  },
};

Object.assign(METRIC_CONCEPTS, FUNDRAISING_CONCEPTS);

// What If scenario id (whatIfScenarios.ts) -> the metric concept it's
// really about, Part 15's own instruction: "if a scenario uses a concept
// like CAC/gross margin/pricing/churn, the founder should be able to
// understand the concept." Only the scenario ids that genuinely turn on
// one of the four METRIC_CONCEPTS above are listed; every other scenario
// (interviews, paying customers, revenue, price point, competition,
// cofounder) is already plain language and gets no entry.
export const WHAT_IF_SCENARIO_CONCEPTS: Record<string, string> = {
  "cac-50": "cac",
  "cac-rises": "cac",
  "margin-improves": "gross_margin",
  "margin-falls": "gross_margin",
  "retention-improves": "retention",
  "retention-falls": "retention",
  churn: "retention",
};
