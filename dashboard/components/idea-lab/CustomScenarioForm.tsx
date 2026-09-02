"use client";

import { useState } from "react";

import Button from "@/components/ui/Button";
import { NumberField } from "./AssumptionFields";
import { hasCommercialScale } from "@/lib/simulate/hasCommercialScale";

import type { VentureAssumptions } from "@/types";

// Simulate V1, Part 7: "If existing architecture makes this reasonably
// simple, allow 'Create custom scenario'... Use the existing
// structured-control patterns from Build V3." It does: this form reuses
// AssumptionFields.tsx's own NumberField unchanged (the same component
// Edit Model and the creation-review screen already use -- Unknown stays
// a blank/placeholder, never a fabricated 0, by construction) and calls
// the SAME onRunScenario prop the preset chips already call. No new
// preview mechanism, no new API surface -- this is a second way to
// PRODUCE a modifiedAssumptions object, not a second way to preview one.
//
// Deliberately scoped to Part 6's own five V1 concepts (price, paying
// customers, CAC, gross margin, retention) -- not a generic multi-field
// editor. Retention is shown only where the venture already has a
// meaningful retention concept (Part 6E), reusing the exact same
// commercial-scale threshold the preset scenarios use.
type CustomScenarioFormProps = {
  currentAssumptions: VentureAssumptions;
  onRunScenario: (modifiedAssumptions: VentureAssumptions) => void;
  isRunning: boolean;
};

export default function CustomScenarioForm({ currentAssumptions, onRunScenario, isRunning }: CustomScenarioFormProps) {
  const [price, setPrice] = useState<number | null>(currentAssumptions.economics.price_point);
  const [customers, setCustomers] = useState<number | null>(currentAssumptions.validation.paying_customers);
  const [cac, setCac] = useState<number | null>(currentAssumptions.gtm.expected_cac);
  const [margin, setMargin] = useState<number | null>(currentAssumptions.economics.expected_gross_margin_pct);
  const [retention, setRetention] = useState<number | null>(currentAssumptions.validation.retention_pct);

  const showRetention = hasCommercialScale(
    currentAssumptions.validation.paying_customers,
    currentAssumptions.validation.monthly_revenue
  );

  function handlePreview() {
    onRunScenario({
      ...currentAssumptions,
      economics: { ...currentAssumptions.economics, price_point: price, expected_gross_margin_pct: margin },
      validation: { ...currentAssumptions.validation, paying_customers: customers, retention_pct: retention },
      gtm: { ...currentAssumptions.gtm, expected_cac: cac },
    });
  }

  return (
    <details className="group mt-3 rounded-lg border border-border">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-3 text-xs font-semibold text-text-primary marker:content-none">
        Create custom scenario
        <span aria-hidden="true" className="text-text-muted transition-transform group-open:rotate-180">▾</span>
      </summary>

      <div className="space-y-3 border-t border-border px-4 py-4">
        <p className="text-xs text-text-muted">
          Change more than one assumption at once, then preview the combined effect. Leave a field as-is to keep it
          unchanged.
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          <NumberField id="sim-price" label="Price ($)" value={price} onChange={setPrice} />
          <NumberField id="sim-customers" label="Paying customers" value={customers} onChange={setCustomers} />
          <NumberField id="sim-cac" label="Customer acquisition cost ($)" value={cac} onChange={setCac} />
          <NumberField id="sim-margin" label="Gross margin (%)" value={margin} onChange={setMargin} />
          {showRetention ? (
            <NumberField id="sim-retention" label="Retention (%)" value={retention} onChange={setRetention} />
          ) : null}
        </div>

        <Button type="button" size="sm" disabled={isRunning} onClick={handlePreview}>
          {isRunning ? "Calculating..." : "Preview this scenario"}
        </Button>
      </div>
    </details>
  );
}
