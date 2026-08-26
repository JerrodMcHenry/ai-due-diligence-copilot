"use client";

import { useState } from "react";

import BaseCard from "@/components/ui/BaseCard";
import ProvenanceBadge from "@/components/idea-lab/ProvenanceBadge";
import {
  NumberField,
  SelectField,
  TextField,
  ToggleField,
} from "@/components/idea-lab/AssumptionFields";

import { draftToAssumptions, VENTURE_STAGES } from "@/types";
import type { VentureAssumptions, VentureDraft } from "@/types";

type VentureBasics = {
  name: string;
  industry: string | null;
  businessModel: string | null;
  targetCustomer: string | null;
  stage: string | null;
};

export type ConfirmedVenture = {
  basics: VentureBasics;
  assumptions: VentureAssumptions;
};

type VentureDraftReviewProps = {
  draft: VentureDraft;
  originalDescription: string;
  onBack: () => void;
  onConfirm: (confirmed: ConfirmedVenture) => void;
  isSubmitting: boolean;
};

// Phase 6.1, Part 5/6: the founder never lands on a saved venture
// straight out of the AI structuring call -- this screen is the explicit
// review/edit/confirm step. Nothing here is submitted anywhere until
// "Create Venture" is clicked; going Back changes nothing that was
// already typed into the description.
export default function VentureDraftReview({
  draft,
  originalDescription,
  onBack,
  onConfirm,
  isSubmitting,
}: VentureDraftReviewProps) {
  const [name, setName] = useState(draft.name.value ?? originalDescription.slice(0, 120));
  const [industry, setIndustry] = useState(draft.industry.value);
  const [businessModel, setBusinessModel] = useState(draft.business_model.value);
  const [targetCustomer, setTargetCustomer] = useState(draft.target_customer.value);
  const [stage, setStage] = useState(draft.stage.value ?? VENTURE_STAGES[0]);
  const [assumptions, setAssumptions] = useState<VentureAssumptions>(() =>
    draftToAssumptions(draft)
  );

  function handleConfirm() {
    onConfirm({
      basics: {
        name: name.trim() || "Untitled venture",
        industry,
        businessModel,
        targetCustomer,
        stage,
      },
      assumptions,
    });
  }

  return (
    <div className="space-y-6">
      <BaseCard className="p-5">
        <p className="text-sm text-text-secondary">
          Here&rsquo;s what SIE understood from your description. Anything
          labeled <span className="font-semibold text-warning">Modeled
          assumption</span> is a guess for you to correct — nothing here is
          saved until you confirm below.
        </p>
        <button
          type="button"
          onClick={onBack}
          className="mt-3 text-xs font-semibold text-primary hover:text-primary-hover"
        >
          ← Back to my description
        </button>
      </BaseCard>

      <div className="space-y-3">
        <ReviewAccordion title="Venture Basics" defaultOpen>
          <TextField
            id="review-name"
            label="Venture name"
            value={name}
            onChange={(value) => setName(value ?? "")}
          />
          <TextField
            id="review-industry"
            label="Industry"
            value={industry}
            onChange={setIndustry}
            badge={<ProvenanceBadge provenance={draft.industry.provenance} />}
          />
          <TextField
            id="review-customer"
            label="Target customer"
            value={targetCustomer}
            onChange={setTargetCustomer}
            badge={<ProvenanceBadge provenance={draft.target_customer.provenance} />}
          />
          <TextField
            id="review-business-model"
            label="Business model"
            value={businessModel}
            onChange={setBusinessModel}
            badge={<ProvenanceBadge provenance={draft.business_model.provenance} />}
          />
          <SelectField
            id="review-stage"
            label="Current status"
            value={stage}
            options={[...VENTURE_STAGES]}
            onChange={(value) => setStage(value ?? VENTURE_STAGES[0])}
            badge={<ProvenanceBadge provenance={draft.stage.provenance} />}
          />
        </ReviewAccordion>

        <ReviewAccordion title="Market" defaultOpen>
          <SelectField
            id="review-market-size"
            label="Estimated market size"
            value={assumptions.market.estimated_market_size}
            options={["Small", "Medium", "Large", "Very Large"]}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, market: { ...prev.market, estimated_market_size: value } }))}
            badge={<ProvenanceBadge provenance={draft.market.estimated_market_size.provenance} />}
          />
          <SelectField
            id="review-competition"
            label="Competition intensity"
            value={assumptions.market.competition_intensity}
            options={["Low", "Medium", "High"]}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, market: { ...prev.market, competition_intensity: value } }))}
            badge={<ProvenanceBadge provenance={draft.market.competition_intensity.provenance} />}
          />
          <TextField
            id="review-market-description"
            label="Market description"
            value={assumptions.market.market_description}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, market: { ...prev.market, market_description: value } }))}
            badge={<ProvenanceBadge provenance={draft.market.market_description.provenance} />}
            multiline
          />
        </ReviewAccordion>

        <ReviewAccordion title="Problem & Solution" defaultOpen>
          <TextField
            id="review-problem"
            label="Problem statement"
            value={assumptions.problem_solution.problem_statement}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, problem_statement: value } }))}
            badge={<ProvenanceBadge provenance={draft.problem_solution.problem_statement.provenance} />}
            multiline
          />
          <TextField
            id="review-solution"
            label="Solution description"
            value={assumptions.problem_solution.solution_description}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, solution_description: value } }))}
            badge={<ProvenanceBadge provenance={draft.problem_solution.solution_description.provenance} />}
            multiline
          />
          <TextField
            id="review-differentiation"
            label="Differentiation"
            value={assumptions.problem_solution.differentiation}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, differentiation: value } }))}
            badge={<ProvenanceBadge provenance={draft.problem_solution.differentiation.provenance} />}
            multiline
          />
        </ReviewAccordion>

        <ReviewAccordion title="Founder / Team">
          <NumberField
            id="review-founder-count"
            label="Founder count"
            value={assumptions.founder.founder_count}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, founder: { ...prev.founder, founder_count: value } }))}
            badge={<ProvenanceBadge provenance={draft.founder.founder_count.provenance} />}
          />
          <NumberField
            id="review-founder-experience"
            label="Relevant domain experience (years)"
            step={0.5}
            value={assumptions.founder.relevant_domain_experience_years}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, founder: { ...prev.founder, relevant_domain_experience_years: value } }))}
            badge={<ProvenanceBadge provenance={draft.founder.relevant_domain_experience_years.provenance} />}
          />
          <ToggleField
            id="review-technical-cofounder"
            label="Technical cofounder?"
            value={assumptions.founder.has_technical_cofounder}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, founder: { ...prev.founder, has_technical_cofounder: value } }))}
            badge={<ProvenanceBadge provenance={draft.founder.has_technical_cofounder.provenance} />}
          />
          <ToggleField
            id="review-business-cofounder"
            label="Business cofounder?"
            value={assumptions.founder.has_business_cofounder}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, founder: { ...prev.founder, has_business_cofounder: value } }))}
            badge={<ProvenanceBadge provenance={draft.founder.has_business_cofounder.provenance} />}
          />
        </ReviewAccordion>

        <ReviewAccordion title="Go-to-Market">
          <TextField
            id="review-gtm-strategy"
            label="Primary acquisition strategy"
            value={assumptions.gtm.primary_acquisition_strategy}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, gtm: { ...prev.gtm, primary_acquisition_strategy: value } }))}
            badge={<ProvenanceBadge provenance={draft.gtm.primary_acquisition_strategy.provenance} />}
            multiline
          />
          <NumberField
            id="review-gtm-cac"
            label="Expected CAC ($)"
            value={assumptions.gtm.expected_cac}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, gtm: { ...prev.gtm, expected_cac: value } }))}
            badge={<ProvenanceBadge provenance={draft.gtm.expected_cac.provenance} />}
          />
        </ReviewAccordion>

        <ReviewAccordion title="Economics">
          <TextField
            id="review-pricing-model"
            label="Pricing model"
            value={assumptions.economics.pricing_model}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, economics: { ...prev.economics, pricing_model: value } }))}
            badge={<ProvenanceBadge provenance={draft.economics.pricing_model.provenance} />}
          />
          <NumberField
            id="review-price-point"
            label="Price point ($)"
            value={assumptions.economics.price_point}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, economics: { ...prev.economics, price_point: value } }))}
            badge={<ProvenanceBadge provenance={draft.economics.price_point.provenance} />}
          />
          <NumberField
            id="review-margin"
            label="Expected gross margin (%)"
            value={assumptions.economics.expected_gross_margin_pct}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, economics: { ...prev.economics, expected_gross_margin_pct: value } }))}
            badge={<ProvenanceBadge provenance={draft.economics.expected_gross_margin_pct.provenance} />}
          />
        </ReviewAccordion>

        <ReviewAccordion title="Validation (founder-reported observations)" defaultOpen>
          <p className="sm:col-span-2 text-xs text-text-muted">
            SIE never invents these — they&rsquo;re only filled in when you
            explicitly said so, or when you fill them in yourself below.
          </p>
          <NumberField
            id="review-interviews"
            label="Customer interviews conducted"
            value={assumptions.validation.customer_interviews}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, validation: { ...prev.validation, customer_interviews: value } }))}
            badge={<ProvenanceBadge provenance={draft.validation.customer_interviews.provenance} />}
          />
          <NumberField
            id="review-waitlist"
            label="Waitlist signups"
            value={assumptions.validation.waitlist_signups}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, validation: { ...prev.validation, waitlist_signups: value } }))}
            badge={<ProvenanceBadge provenance={draft.validation.waitlist_signups.provenance} />}
          />
          <NumberField
            id="review-paying"
            label="Paying customers"
            value={assumptions.validation.paying_customers}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, validation: { ...prev.validation, paying_customers: value } }))}
            badge={<ProvenanceBadge provenance={draft.validation.paying_customers.provenance} />}
          />
          <NumberField
            id="review-revenue"
            label="Monthly revenue ($)"
            value={assumptions.validation.monthly_revenue}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, validation: { ...prev.validation, monthly_revenue: value } }))}
            badge={<ProvenanceBadge provenance={draft.validation.monthly_revenue.provenance} />}
          />
        </ReviewAccordion>

        <ReviewAccordion title="Capital">
          <NumberField
            id="review-starting-capital"
            label="Starting capital ($)"
            value={assumptions.capital.starting_capital}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, capital: { ...prev.capital, starting_capital: value } }))}
            badge={<ProvenanceBadge provenance={draft.capital.starting_capital.provenance} />}
          />
          <NumberField
            id="review-burn"
            label="Monthly burn ($)"
            value={assumptions.capital.monthly_burn}
            onChange={(value) => setAssumptions((prev) => ({ ...prev, capital: { ...prev.capital, monthly_burn: value } }))}
            badge={<ProvenanceBadge provenance={draft.capital.monthly_burn.provenance} />}
          />
        </ReviewAccordion>
      </div>

      <div className="flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-border px-4 py-2.5 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
        >
          Back
        </button>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleConfirm}
          className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Creating..." : "Create Venture"}
        </button>
      </div>
    </div>
  );
}

function ReviewAccordion({
  title,
  defaultOpen,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  return (
    <details open={defaultOpen} className="group rounded-2xl border border-border bg-surface open:pb-2">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-semibold text-text-primary marker:content-none">
        {title}
        <span aria-hidden="true" className="text-text-muted transition-transform group-open:rotate-180">▾</span>
      </summary>
      <div className="grid gap-4 px-5 pb-4 sm:grid-cols-2">{children}</div>
    </details>
  );
}
