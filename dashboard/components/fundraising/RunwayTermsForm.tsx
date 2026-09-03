"use client";

import Input from "@/components/ui/Input";
import Disclosure from "@/components/ui/Disclosure";

import type { RunwayTerms } from "@/lib/fundraisingUi/types";

type RunwayTermsFormProps = {
  runway: RunwayTerms;
  onChange: (runway: RunwayTerms) => void;
};

// Phase 21B, Part 17. Optional -- collapsed by default so it never
// competes with the required SAFE/round terms above it. Cash and burn
// are collected only for THIS scenario (never read from or written to the
// canonical venture model, matching the rest of the simulator's firewall).
export default function RunwayTermsForm({ runway, onChange }: RunwayTermsFormProps) {
  return (
    <Disclosure summary="Optional: see modeled runway" defaultOpen={false}>
      <p className="text-sm leading-6 text-text-muted">
        Add your current cash on hand and monthly burn to see how this financing would change your modeled runway.
        Assumes burn stays constant -- this is not a forecast.
      </p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Input
          id="runway-cash"
          label="Cash on hand ($)"
          type="number"
          inputMode="decimal"
          min={0}
          value={runway.cashOnHandDollars ?? ""}
          onChange={(e) => onChange({ ...runway, cashOnHandDollars: e.target.value === "" ? null : Number(e.target.value) })}
          placeholder="Unknown"
        />
        <Input
          id="runway-burn"
          label="Monthly burn ($)"
          type="number"
          inputMode="decimal"
          min={0}
          value={runway.monthlyBurnDollars ?? ""}
          onChange={(e) => onChange({ ...runway, monthlyBurnDollars: e.target.value === "" ? null : Number(e.target.value) })}
          placeholder="Unknown"
        />
      </div>
    </Disclosure>
  );
}
