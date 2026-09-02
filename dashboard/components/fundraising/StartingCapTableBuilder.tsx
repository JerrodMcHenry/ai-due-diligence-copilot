"use client";

import { useState } from "react";

import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { validateOwnershipPercentages, oneClickSoleFounder } from "@/lib/fundraisingUi/startingCapTable";
import { STAKEHOLDER_ROLE_LABELS } from "@/lib/fundraisingUi/types";

import type { StakeholderRole, UiStakeholder } from "@/lib/fundraisingUi/types";

const ROLE_OPTIONS: StakeholderRole[] = ["founder", "cofounder", "employee_pool", "existing_investor", "other"];

let nextId = 1;
function freshId(): string {
  nextId += 1;
  return `stakeholder-${nextId}`;
}

type StartingCapTableBuilderProps = {
  founderName: string;
  initial: UiStakeholder[] | null;
  onConfirm: (stakeholders: UiStakeholder[]) => void;
};

// Phase 21B, Part 5/6/7. Ephemeral, simulation-only ownership builder --
// nothing here is persisted to the canonical venture model. Part 6: never
// silently assume 100% -- "You -- 100%" is offered as an explicit
// one-click choice the founder must actually select, not a pre-filled
// default.
export default function StartingCapTableBuilder({ founderName, initial, onConfirm }: StartingCapTableBuilderProps) {
  const [stakeholders, setStakeholders] = useState<UiStakeholder[] | null>(initial);

  if (stakeholders === null) {
    return (
      <div>
        <h3 className="text-base font-semibold text-text-primary">Who owns the company today?</h3>
        <p className="mt-1 text-sm text-text-secondary">
          This is just for this simulation -- it won&rsquo;t change your saved venture.
        </p>

        <div className="mt-4 flex flex-wrap gap-2.5">
          <button
            type="button"
            onClick={() => setStakeholders(oneClickSoleFounder(founderName))}
            className="rounded-2xl border border-border bg-surface p-4 text-left transition-colors hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="block text-sm font-semibold text-text-primary">You -- 100%</span>
            <span className="mt-1 block text-xs text-text-muted">You&rsquo;re the sole owner today.</span>
          </button>
          <button
            type="button"
            onClick={() =>
              setStakeholders([
                { id: freshId(), name: founderName || "You", role: "founder", percent: 50 },
                { id: freshId(), name: "Cofounder", role: "cofounder", percent: 50 },
              ])
            }
            className="rounded-2xl border border-border bg-surface p-4 text-left transition-colors hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="block text-sm font-semibold text-text-primary">You and a cofounder</span>
            <span className="mt-1 block text-xs text-text-muted">Split ownership between two founders.</span>
          </button>
          <button
            type="button"
            onClick={() => setStakeholders([{ id: freshId(), name: founderName || "You", role: "founder", percent: 100 }])}
            className="rounded-2xl border border-border bg-surface p-4 text-left text-sm font-semibold text-primary hover:text-primary-hover"
          >
            Set up ownership myself →
          </button>
        </div>
      </div>
    );
  }

  const error = validateOwnershipPercentages(stakeholders);

  function updateRow(id: string, patch: Partial<UiStakeholder>) {
    setStakeholders((prev) => (prev ? prev.map((s) => (s.id === id ? { ...s, ...patch } : s)) : prev));
  }

  function removeRow(id: string) {
    setStakeholders((prev) => (prev ? prev.filter((s) => s.id !== id) : prev));
  }

  function addRow() {
    setStakeholders((prev) => [...(prev ?? []), { id: freshId(), name: "", role: "other", percent: 0 }]);
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-text-primary">Who owns the company today?</h3>
      <p className="mt-1 text-sm text-text-secondary">
        This is just for this simulation -- it won&rsquo;t change your saved venture.
      </p>

      <div className="mt-4 space-y-3">
        {stakeholders.map((s) => (
          <div key={s.id} className="flex flex-wrap items-end gap-2 rounded-xl border border-border p-3 sm:flex-nowrap">
            <div className="min-w-0 flex-1">
              <Input
                id={`name-${s.id}`}
                label="Name"
                value={s.name}
                onChange={(e) => updateRow(s.id, { name: e.target.value })}
                placeholder={STAKEHOLDER_ROLE_LABELS[s.role]}
              />
            </div>
            <div className="w-full sm:w-44">
              <label htmlFor={`role-${s.id}`} className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
                Type
              </label>
              <select
                id={`role-${s.id}`}
                value={s.role}
                onChange={(e) => updateRow(s.id, { role: e.target.value as StakeholderRole })}
                className="mt-2 h-[46px] w-full rounded-xl border border-border bg-surface px-3 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              >
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>
                    {STAKEHOLDER_ROLE_LABELS[role]}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-full sm:w-32">
              <Input
                id={`percent-${s.id}`}
                label="Ownership %"
                type="number"
                inputMode="decimal"
                min={0}
                max={100}
                step={0.01}
                value={Number.isFinite(s.percent) ? s.percent : ""}
                onChange={(e) => updateRow(s.id, { percent: e.target.value === "" ? 0 : Number(e.target.value) })}
              />
            </div>
            {stakeholders.length > 1 ? (
              <Button type="button" variant="subtle" size="sm" onClick={() => removeRow(s.id)} className="hover:text-danger">
                Remove
              </Button>
            ) : null}
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <Button type="button" variant="secondary" size="sm" onClick={addRow}>
          + Add stakeholder
        </Button>
        <p className={["text-sm font-semibold", error ? "text-danger" : "text-success"].join(" ")}>
          {error ? error : "Adds up to 100% ✓"}
        </p>
      </div>

      <Button type="button" className="mt-4" disabled={Boolean(error)} onClick={() => onConfirm(stakeholders)}>
        Continue
      </Button>
    </div>
  );
}
