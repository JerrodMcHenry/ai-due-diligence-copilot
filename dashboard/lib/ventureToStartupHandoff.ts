import type { VentureAssumptions } from "@/types";

// Phase 10.10 -- Founder Journey Integration, Part 8. The idea -> real
// startup bridge, using the EXACT SAME mechanism lib/homepageIdeaHandoff.ts
// already established for "a visitor types text in one place, it should
// be waiting for them in a different EXISTING form" -- a same-tab
// sessionStorage stash, read-and-cleared once. Nothing is created here:
// no venture-to-startup conversion, no canonical startup, no evidence.
// This only carries the founder's OWN already-written venture description
// into /analyze's existing "Additional Company Information" field as a
// convenience starting point they can edit or delete -- the same honest
// "founder's own words, offered back to them" contract
// homepageIdeaHandoff.ts already uses, applied one step later in the
// journey.
const VENTURE_TO_STARTUP_STORAGE_KEY = "sie:venture-description-handoff";

export function stashVentureDescriptionForAnalyze(description: string): void {
  try {
    sessionStorage.setItem(VENTURE_TO_STARTUP_STORAGE_KEY, description);
  } catch {
    // Private browsing / storage disabled: the description just won't be
    // pre-filled on /analyze. Not worth blocking navigation over.
  }
}

export function consumeVentureDescriptionForAnalyze(): string | null {
  try {
    const value = sessionStorage.getItem(VENTURE_TO_STARTUP_STORAGE_KEY);

    if (value) {
      sessionStorage.removeItem(VENTURE_TO_STARTUP_STORAGE_KEY);
    }

    return value;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Phase 31 -- Venture -> Startup Graduation V1, Part 5/6. The Data
// Transfer Contract, implemented as plain, reviewable TEXT rather than a
// second database write path -- see this phase's own design record in
// docs/product/VENTURE_TO_STARTUP_GRADUATION_V1.md for the full reasoning.
// startups itself has no content columns to receive VentureAssumptions
// directly (canonical_name/normalized_name/created_at only); the only
// safe, non-fabricating way for a venture's own context to reach a real
// Startup is through this EXACT SAME stash-then-founder-reviews-then-
// submits-to-/analyze mechanism the description-only handoff above
// already established, just carrying a fuller, explicitly labeled
// summary. POST /analyze's own canonical pipeline still independently
// re-derives every piece of evidence from scratch -- this text is a
// convenience starting point the founder can edit or delete, never
// evidence in itself.
//
// Field classification (reusing VPS's OWN existing structural provenance
// distinction -- validation = founder-REPORTED OBSERVATION, everything
// else = MODELED ASSUMPTION -- rather than inventing a second one):
//
//   SAFE, unlabeled: description, target_customer, problem_solution.*,
//     validation.* (these are founder-reported observations by the
//     codebase's own architecture, not projections).
//   REVIEW, explicitly marked "modeled assumption, not yet verified":
//     market.*, founder.*, gtm.*, economics.*, business_model, industry,
//     stage.
//   NEVER included: VPS score/categories/guidance (would look like
//     pre-existing SPS intelligence), capital.* (speculative, no SPS
//     landing concept), and every internal operating-history record
//     (missions, captures, model-update history).
export type GraduationSourceVenture = {
  name: string;
  description: string | null;
  industry: string | null;
  business_model: string | null;
  target_customer: string | null;
  stage: string | null;
  assumptions: VentureAssumptions;
};

function pushIfPresent(lines: string[], label: string, value: string | number | null | undefined, suffix = ""): boolean {
  if (value === null || value === undefined || value === "") {
    return false;
  }
  lines.push(`${label}: ${value}${suffix}`);
  return true;
}

/**
 * Builds the reviewable pre-fill text AND reports how many real (non-
 * empty) fields it included -- the latter feeds `fields_transferred_count`
 * on POST /ventures/{id}/graduate purely for analytics (Part 14), never
 * persisted as venture/startup content.
 */
export function buildGraduationSummaryText(
  venture: GraduationSourceVenture
): { text: string; fieldsIncluded: number } {
  const { assumptions } = venture;
  let fieldsIncluded = 0;
  const count = (added: boolean) => {
    if (added) fieldsIncluded += 1;
  };

  const safeLines: string[] = [];
  count(pushIfPresent(safeLines, "Target customer", venture.target_customer));
  count(pushIfPresent(safeLines, "Problem", assumptions.problem_solution.problem_statement));
  count(pushIfPresent(safeLines, "Solution", assumptions.problem_solution.solution_description));
  count(pushIfPresent(safeLines, "Differentiation", assumptions.problem_solution.differentiation));

  const validationLines: string[] = [];
  count(pushIfPresent(validationLines, "Customer interviews conducted", assumptions.validation.customer_interviews));
  count(pushIfPresent(validationLines, "Waitlist signups", assumptions.validation.waitlist_signups));
  count(pushIfPresent(validationLines, "Paying customers", assumptions.validation.paying_customers));
  count(pushIfPresent(validationLines, "Monthly revenue", assumptions.validation.monthly_revenue, " USD"));
  count(pushIfPresent(validationLines, "Monthly revenue ~12 months ago", assumptions.validation.prior_monthly_revenue, " USD"));
  count(pushIfPresent(validationLines, "Retention", assumptions.validation.retention_pct, "%"));

  const reviewLines: string[] = [];
  count(pushIfPresent(reviewLines, "Industry", venture.industry));
  count(pushIfPresent(reviewLines, "Business model", venture.business_model));
  count(pushIfPresent(reviewLines, "Stage", venture.stage));
  count(pushIfPresent(reviewLines, "Estimated market size", assumptions.market.estimated_market_size));
  count(pushIfPresent(reviewLines, "Competition intensity", assumptions.market.competition_intensity));
  count(pushIfPresent(reviewLines, "Market description", assumptions.market.market_description));
  count(pushIfPresent(reviewLines, "Founder count", assumptions.founder.founder_count));
  count(pushIfPresent(reviewLines, "Relevant domain experience", assumptions.founder.relevant_domain_experience_years, " years"));
  count(pushIfPresent(reviewLines, "Primary acquisition strategy", assumptions.gtm.primary_acquisition_strategy));
  count(pushIfPresent(reviewLines, "Expected CAC", assumptions.gtm.expected_cac, " USD"));
  count(pushIfPresent(reviewLines, "Pricing model", assumptions.economics.pricing_model));
  count(pushIfPresent(reviewLines, "Price point", assumptions.economics.price_point, " USD"));
  count(pushIfPresent(reviewLines, "Expected gross margin", assumptions.economics.expected_gross_margin_pct, "%"));

  const sections: string[] = [];

  if (venture.description) {
    sections.push(venture.description.trim());
    fieldsIncluded += 1;
  }

  if (safeLines.length > 0) {
    sections.push(safeLines.join("\n"));
  }

  if (validationLines.length > 0) {
    sections.push(`What we've observed so far:\n${validationLines.join("\n")}`);
  }

  if (reviewLines.length > 0) {
    sections.push(
      `Modeled assumptions from Idea Lab (not yet verified -- edit or remove anything below):\n${reviewLines.join("\n")}`
    );
  }

  return { text: sections.join("\n\n"), fieldsIncluded };
}

// Same read-and-cleared-once sessionStorage contract as
// stash/consumeVentureDescriptionForAnalyze above -- deliberately the
// SAME storage key, since this is a richer version of the exact same
// pre-fill, never a second, competing stash a caller could get out of
// sync with.
export function stashGraduationSummaryForAnalyze(venture: GraduationSourceVenture): number {
  const { text, fieldsIncluded } = buildGraduationSummaryText(venture);
  stashVentureDescriptionForAnalyze(text);
  return fieldsIncluded;
}
