"use client";

import Input from "@/components/ui/Input";
import Disclosure from "@/components/ui/Disclosure";
import ConceptDisclosure from "@/components/learn/ConceptDisclosure";

import type { UiPricedRoundTerm } from "@/lib/fundraisingUi/types";

export function emptyPricedRoundTerm(name: string): UiPricedRoundTerm {
  return { name, preMoneyDollars: 0, newMoneyDollars: 0, newInvestorName: "" };
}

type PricedRoundTermsFormProps = {
  round: UiPricedRoundTerm;
  onChange: (round: UiPricedRoundTerm) => void;
  optionPoolIncreasePercent: number;
  onOptionPoolIncreasePercentChange: (percent: number) => void;
};

// Phase 21B, Part 4/7/10. Direct-entry terms for a priced round. The
// option-pool field is deliberately tucked into an "Advanced" disclosure,
// collapsed by default (Part 10: "defer option-pool editing from the
// primary flow... where inputs are explicit") -- and is labeled precisely
// as a percentage of CURRENT shares, never implying the unsupported
// target-post-money-% form (see lib/fundraisingUi/types.ts's own comment).
export default function PricedRoundTermsForm({
  round,
  onChange,
  optionPoolIncreasePercent,
  onOptionPoolIncreasePercentChange,
}: PricedRoundTermsFormProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          id="round-name"
          label="Round name"
          value={round.name}
          onChange={(e) => onChange({ ...round, name: e.target.value })}
          placeholder="Seed"
        />
        <Input
          id="round-investor"
          label="Lead investor name"
          value={round.newInvestorName}
          onChange={(e) => onChange({ ...round, newInvestorName: e.target.value })}
          placeholder="e.g. Seed Fund"
        />
        <div>
          <Input
            id="round-premoney"
            label="Pre-money valuation ($)"
            type="number"
            inputMode="decimal"
            min={0}
            value={round.preMoneyDollars || ""}
            onChange={(e) => onChange({ ...round, preMoneyDollars: Number(e.target.value) || 0 })}
            placeholder="8,000,000"
          />
          <ConceptDisclosure conceptKey="pre_money_valuation" value={round.preMoneyDollars || null} />
        </div>
        <Input
          id="round-newmoney"
          label="New investment ($)"
          type="number"
          inputMode="decimal"
          min={0}
          value={round.newMoneyDollars || ""}
          onChange={(e) => onChange({ ...round, newMoneyDollars: Number(e.target.value) || 0 })}
          placeholder="2,000,000"
        />
      </div>

      <ConceptDisclosure conceptKey="priced_round" value={null} />

      <Disclosure summary="Advanced: option pool" defaultOpen={false}>
        <p className="text-xs leading-5 text-text-muted">
          Add a new option pool as part of this round, sized as a percentage of your company&rsquo;s CURRENT shares
          (before this round) -- not a target percentage of the company after the round, which Fundraising Simulator
          V1 does not calculate.
        </p>
        <div className="mt-3 max-w-xs">
          <Input
            id="pool-increase"
            label="New option pool (% of current shares)"
            type="number"
            inputMode="decimal"
            min={0}
            max={100}
            step={0.5}
            value={optionPoolIncreasePercent || ""}
            onChange={(e) => onOptionPoolIncreasePercentChange(Number(e.target.value) || 0)}
            placeholder="0"
          />
        </div>
        <ConceptDisclosure conceptKey="option_pool" value={optionPoolIncreasePercent || null} />
      </Disclosure>
    </div>
  );
}
