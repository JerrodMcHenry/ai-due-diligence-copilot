// Phase 10.6 -- Idea Lab V2, Part 7. "What if?" scenarios -- each patches
// EXACTLY the one or two VentureAssumptions fields its question names,
// nothing else, and nothing outside the fields vps_scoring.py's category
// scorers actually read (see that module's own docstring: "every
// category function reads ONLY its own namespaced slice"). No scenario
// here is invented or approximated; each maps honestly onto a real,
// existing field. Applying a preset never mutates the venture itself --
// it only produces the MODIFIED assumptions object the caller passes
// into the existing, unchanged compareVentureScenarios()/POST
// /ventures/scenario-compare preview path (Part 7: "Preview = temporary.
// Apply & Save = persistent. Discard = no mutation" -- entirely
// pre-existing, untouched by this phase).
//
// Founder Loop V2, Section 6: rewritten from a FIXED list of five presets
// (which produced nonsense like "What if I interview 20 customers?" for
// a venture that already reported 85) into a function of the venture's
// OWN current assumptions. Every scenario is generated only when it's
// still a meaningful question given what's already modeled/reported, and
// every incremental scenario moves RELATIVE to the current value -- never
// a fixed absolute that could silently present as "progress" a number
// smaller than what's already there. Deliberately stays within fields
// vps_scoring.py's scorers actually read (capital.* isn't scored by any
// category -- see that module's own `_CATEGORY_SCORERS` -- so no
// scenario here touches it; a burn/runway "what if" would preview zero
// VPS change, which would look broken even though it's honest).
// A structural subset of VentureAssumptions -- only the fields this
// module actually reads/writes. Deliberately not imported from "@/types"
// (zero "@/..." alias imports here, same discipline as
// lib/journey/inferVentureStage.ts and this repo's other pure logic
// modules), so this stays trivially runnable by plain `node`. `apply` is
// generic so calling it with a real VentureAssumptions object returns a
// real VentureAssumptions back -- nothing here narrows the caller's type.
type MinimalAssumptions = {
  market: { competition_intensity: string | null };
  founder: { has_technical_cofounder: boolean | null; has_business_cofounder: boolean | null };
  gtm: { expected_cac: number | null };
  economics: { price_point: number | null; expected_gross_margin_pct: number | null };
  validation: {
    customer_interviews: number | null;
    paying_customers: number | null;
    monthly_revenue: number | null;
    retention_pct: number | null;
  };
};

export type WhatIfScenario = {
  id: string;
  question: string;
  // Section 6's explicit requirement: distinguish an upside scenario
  // (stronger than today) from a downside/risk one (weaker than today,
  // deliberately, to stress-test the model) -- never presented the same
  // way in the UI.
  direction: "upside" | "downside";
  // Typed against the minimal shape only -- at runtime this always
  // receives (and, via object spread, fully preserves) the caller's real
  // full VentureAssumptions object; see WhatIfPanel.tsx's own call site
  // for how the result is merged back onto the original so no field is
  // ever statically dropped.
  apply: (assumptions: MinimalAssumptions) => MinimalAssumptions;
};

function roundTo(value: number, step: number): number {
  return Math.round(value / step) * step;
}

export function getWhatIfScenarios(current: MinimalAssumptions): WhatIfScenario[] {
  const scenarios: WhatIfScenario[] = [];

  const interviews = current.validation.customer_interviews;
  const paying = current.validation.paying_customers;
  const revenue = current.validation.monthly_revenue;
  const priceSet = current.economics.price_point !== null;
  const cacSet = current.gtm.expected_cac !== null;
  const margin = current.economics.expected_gross_margin_pct;
  const intensity = current.market.competition_intensity;
  const hasTechnicalCofounder = current.founder.has_technical_cofounder;
  const hasBusinessCofounder = current.founder.has_business_cofounder;
  // SIE Intelligence Reset: matches vps_guidance.py's own
  // _has_meaningful_commercial_scale() threshold exactly -- a company at
  // real commercial scale should never be offered "what if I interview
  // 20 customers", the confirmed regression case (a company with 186
  // paying customers and $11.8M ARR was offered this exact scenario).
  // "Is the problem real" is no longer a meaningful open question at
  // this scale; it isn't lower-priority, it's inapplicable.
  const hasCommercialScale = (paying !== null && paying >= 10) || (revenue !== null && revenue >= 10_000);

  // --- Validation upside: always relative to what's already reported ---

  if (!hasCommercialScale && (interviews === null || interviews < 20)) {
    scenarios.push({
      id: "interview-20",
      question: "What if I interview 20 customers?",
      direction: "upside",
      apply: (a) => ({ ...a, validation: { ...a.validation, customer_interviews: 20 } }),
    });
  } else if (!hasCommercialScale && interviews !== null) {
    const target = interviews + 15;
    scenarios.push({
      id: "interview-more",
      question: `What if I interview ${target} customers?`,
      direction: "upside",
      apply: (a) => ({ ...a, validation: { ...a.validation, customer_interviews: target } }),
    });
  }

  if (paying === null || paying === 0) {
    scenarios.push({
      id: "5-paying",
      question: "What if 5 customers agree to pay?",
      direction: "upside",
      apply: (a) => ({ ...a, validation: { ...a.validation, paying_customers: 5 } }),
    });
  } else {
    const target = paying + Math.max(5, Math.round(paying * 0.3));
    scenarios.push({
      id: "more-paying",
      question: `What if you have ${target} paying customers?`,
      direction: "upside",
      apply: (a) => ({ ...a, validation: { ...a.validation, paying_customers: target } }),
    });

    // Downside: only offered once there's a real number of paying
    // customers to meaningfully stress -- an explicit risk scenario
    // (Section 6's "never lower an already-strong value unless
    // explicitly modeling downside"), never silently presented as
    // progress.
    if (paying >= 2) {
      const lost = Math.max(1, Math.round(paying * 0.2));
      scenarios.push({
        id: "churn",
        question: `What if ${lost} paying customer${lost === 1 ? "" : "s"} churn${lost === 1 ? "s" : ""}?`,
        direction: "downside",
        apply: (a) => ({ ...a, validation: { ...a.validation, paying_customers: Math.max(0, paying - lost) } }),
      });
    }
  }

  if (revenue !== null && revenue > 0) {
    const target = roundTo(revenue * 1.5, 100);
    scenarios.push({
      id: "revenue-grows",
      question: `What if monthly revenue reaches $${target.toLocaleString()}?`,
      direction: "upside",
      apply: (a) => ({ ...a, validation: { ...a.validation, monthly_revenue: target } }),
    });
  }

  // --- Retention: only a meaningful question once there's a commercial
  // base to retain -- SIE Intelligence Reset's new retention_pct field ---

  const retention = current.validation.retention_pct;
  if (hasCommercialScale) {
    if (retention === null || retention < 110) {
      const target = retention === null ? 105 : Math.min(140, retention + 15);
      scenarios.push({
        id: "retention-improves",
        question: `What if retention reaches ${target}%?`,
        direction: "upside",
        apply: (a) => ({ ...a, validation: { ...a.validation, retention_pct: target } }),
      });
    }
    if (retention === null || retention >= 80) {
      const target = retention === null ? 65 : Math.max(30, retention - 25);
      scenarios.push({
        id: "retention-falls",
        question: `What if retention falls to ${target}%?`,
        direction: "downside",
        apply: (a) => ({ ...a, validation: { ...a.validation, retention_pct: target } }),
      });
    }
  }

  // --- Pricing / GTM ---

  if (!priceSet) {
    scenarios.push({
      id: "price-29",
      question: "What if I charge $29/month?",
      direction: "upside",
      apply: (a) => ({ ...a, economics: { ...a.economics, price_point: 29 } }),
    });
  }

  if (!cacSet) {
    scenarios.push({
      id: "cac-50",
      question: "What if customer acquisition costs $50?",
      direction: "downside",
      apply: (a) => ({ ...a, gtm: { ...a.gtm, expected_cac: 50 } }),
    });
  } else {
    const currentCac = current.gtm.expected_cac as number;
    const worse = roundTo(currentCac * 1.5, 5);
    scenarios.push({
      id: "cac-rises",
      question: `What if acquisition cost rises to $${worse}?`,
      direction: "downside",
      apply: (a) => ({ ...a, gtm: { ...a.gtm, expected_cac: worse } }),
    });
  }

  // --- Economics: margin, only a meaningful question in each direction
  // when there's an existing value to move ---

  if (margin !== null && margin < 70) {
    const better = Math.min(85, margin + 15);
    scenarios.push({
      id: "margin-improves",
      question: `What if gross margin improves to ${better}%?`,
      direction: "upside",
      apply: (a) => ({ ...a, economics: { ...a.economics, expected_gross_margin_pct: better } }),
    });
  }
  if (margin !== null && margin >= 40) {
    const worse = Math.max(10, margin - 20);
    scenarios.push({
      id: "margin-falls",
      question: `What if gross margin falls to ${worse}%?`,
      direction: "downside",
      apply: (a) => ({ ...a, economics: { ...a.economics, expected_gross_margin_pct: worse } }),
    });
  }

  // --- Market: competition intensity, only meaningful in the direction
  // that's still open ---

  if (intensity !== "High") {
    scenarios.push({
      id: "competition-intensifies",
      question: "What if competition in your market intensifies?",
      direction: "downside",
      apply: (a) => ({ ...a, market: { ...a.market, competition_intensity: "High" } }),
    });
  }
  if (intensity === "High" || intensity === "Medium") {
    scenarios.push({
      id: "competition-eases",
      question: "What if you find a less crowded niche?",
      direction: "upside",
      apply: (a) => ({ ...a, market: { ...a.market, competition_intensity: "Low" } }),
    });
  }

  // --- Team ---

  if (!hasTechnicalCofounder || !hasBusinessCofounder) {
    scenarios.push({
      id: "find-cofounder",
      question: "What if I find a cofounder?",
      direction: "upside",
      // Fills whichever complementary cofounder slot isn't already set --
      // a solo technical founder is offered a business cofounder and vice
      // versa, so the preset always represents a genuinely NEW addition
      // to the founding team rather than silently no-op'ing.
      apply: (a) => {
        if (!a.founder.has_technical_cofounder) {
          return { ...a, founder: { ...a.founder, has_technical_cofounder: true } };
        }
        return { ...a, founder: { ...a.founder, has_business_cofounder: true } };
      },
    });
  }

  return scenarios;
}
