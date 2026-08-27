import type { VentureAssumptions } from "@/types";

// Phase 10.6 -- Idea Lab V2, Part 7. Five preset "What if?" scenarios --
// each patches EXACTLY the one or two VentureAssumptions fields its
// question names, nothing else, and nothing outside the fields
// vps_scoring.py's category scorers actually read (see that module's own
// docstring: "every category function reads ONLY its own namespaced
// slice"). No scenario here is invented or approximated; each maps
// honestly onto a real, existing field. Applying a preset never mutates
// the venture itself -- it only produces the MODIFIED assumptions object
// the caller passes into the existing, unchanged
// compareVentureScenarios()/POST /ventures/scenario-compare preview path
// (Part 7: "Preview = temporary. Apply & Save = persistent. Discard = no
// mutation" -- entirely pre-existing, untouched by this phase).
export type WhatIfScenario = {
  id: string;
  question: string;
  apply: (assumptions: VentureAssumptions) => VentureAssumptions;
};

export const WHAT_IF_SCENARIOS: WhatIfScenario[] = [
  {
    id: "interview-20",
    question: "What if I interview 20 customers?",
    apply: (a) => ({
      ...a,
      validation: { ...a.validation, customer_interviews: 20 },
    }),
  },
  {
    id: "5-paying",
    question: "What if 5 customers agree to pay?",
    apply: (a) => ({
      ...a,
      validation: { ...a.validation, paying_customers: 5 },
    }),
  },
  {
    id: "price-29",
    question: "What if I charge $29/month?",
    apply: (a) => ({
      ...a,
      economics: { ...a.economics, price_point: 29 },
    }),
  },
  {
    id: "cac-50",
    question: "What if customer acquisition costs $50?",
    apply: (a) => ({
      ...a,
      gtm: { ...a.gtm, expected_cac: 50 },
    }),
  },
  {
    id: "find-cofounder",
    question: "What if I find a cofounder?",
    // Fills whichever complementary cofounder slot isn't already set --
    // a solo technical founder is offered a business cofounder and vice
    // versa, so the preset always represents a genuinely NEW addition to
    // the founding team rather than silently no-op'ing.
    apply: (a) => {
      if (!a.founder.has_technical_cofounder) {
        return { ...a, founder: { ...a.founder, has_technical_cofounder: true } };
      }
      return { ...a, founder: { ...a.founder, has_business_cofounder: true } };
    },
  },
];
