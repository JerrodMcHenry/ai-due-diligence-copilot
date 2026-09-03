"use client";

import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import ConceptDisclosure from "@/components/learn/ConceptDisclosure";

import type { UiSafeTerm } from "@/lib/fundraisingUi/types";

let nextId = 1;
function freshId(): string {
  nextId += 1;
  return `safe-${nextId}`;
}

export function newSafeTerm(holderName: string): UiSafeTerm {
  return { id: freshId(), holderName, investmentDollars: 0, valuationCapDollars: 0 };
}

type SafeTermsFormProps = {
  safes: UiSafeTerm[];
  onChange: (safes: UiSafeTerm[]) => void;
};

// Phase 21B, Part 4/7. Experienced founders can enter terms directly --
// no separate "advanced mode," just the same form used from either entry
// path (Part 4: "The beginner and experienced path should converge on the
// SAME engine"). Only the validated V1 representation is exposed: an
// investment amount and a valuation cap (Part 7/9) -- no discount field,
// no MFN field (Part 8: unsupported structures are never collected).
export default function SafeTermsForm({ safes, onChange }: SafeTermsFormProps) {
  function update(id: string, patch: Partial<UiSafeTerm>) {
    onChange(safes.map((s) => (s.id === id ? { ...s, ...patch } : s)));
  }

  function remove(id: string) {
    onChange(safes.filter((s) => s.id !== id));
  }

  function add() {
    onChange([...safes, newSafeTerm(`SAFE ${safes.length + 1}`)]);
  }

  return (
    <div className="space-y-4">
      {safes.map((safe, i) => (
        <div key={safe.id} className="rounded-2xl border border-border p-4">
          <div className="flex items-center justify-between gap-2">
            {/* Phase 29B, Part 9: the engine only ever models a Post-Money
                SAFE (lib/fundraising/safe.ts) -- named explicitly right
                where the founder enters terms, not just in a glossary
                entry they may never open. */}
            <p className="text-sm font-semibold text-text-primary">Post-Money SAFE {i + 1}</p>
            {safes.length > 1 ? (
              <Button type="button" variant="subtle" size="sm" onClick={() => remove(safe.id)} className="hover:text-danger">
                Remove
              </Button>
            ) : null}
          </div>

          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <Input
              id={`safe-name-${safe.id}`}
              label="Investor name"
              value={safe.holderName}
              onChange={(e) => update(safe.id, { holderName: e.target.value })}
              placeholder="e.g. Angel Investor"
            />
            <Input
              id={`safe-amount-${safe.id}`}
              label="Investment ($)"
              type="number"
              inputMode="decimal"
              min={0}
              value={safe.investmentDollars || ""}
              onChange={(e) => update(safe.id, { investmentDollars: Number(e.target.value) || 0 })}
              placeholder="500,000"
            />
            <div>
              <Input
                id={`safe-cap-${safe.id}`}
                label="Valuation cap ($)"
                type="number"
                inputMode="decimal"
                min={0}
                value={safe.valuationCapDollars || ""}
                onChange={(e) => update(safe.id, { valuationCapDollars: Number(e.target.value) || 0 })}
                placeholder="5,000,000"
              />
              {i === 0 ? <ConceptDisclosure conceptKey="valuation_cap" value={safe.valuationCapDollars || null} /> : null}
            </div>
          </div>
        </div>
      ))}

      {safes.length === 0 ? <p className="text-sm text-text-muted">No SAFE added yet.</p> : null}

      <Button type="button" variant="secondary" size="sm" onClick={add}>
        + Add another SAFE
      </Button>

      {safes.length === 1 ? <ConceptDisclosure conceptKey="safe" value={null} /> : null}
    </div>
  );
}
