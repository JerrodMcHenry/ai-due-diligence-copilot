import Button from "@/components/ui/Button";

import { WHAT_IF_SCENARIOS } from "./whatIfScenarios";

import type { VentureAssumptions } from "@/types";

// Phase 10.6 -- Idea Lab V2, Part 7. Elevates the existing scenario
// simulator into a first-class "What if?" experience -- one tap runs a
// real preview through the SAME compareVentureScenarios()/scenario-
// compare mechanism the manual assumption editor already used; this
// panel only supplies WHICH fields to change, never a different
// calculation path.
type WhatIfPanelProps = {
  currentAssumptions: VentureAssumptions;
  onRunScenario: (modifiedAssumptions: VentureAssumptions) => void;
  isRunning: boolean;
};

export default function WhatIfPanel({ currentAssumptions, onRunScenario, isRunning }: WhatIfPanelProps) {
  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">What if?</h3>
      <p className="mt-1 text-xs text-text-muted">
        Try a real scenario — nothing is saved until you choose to apply it.
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        {WHAT_IF_SCENARIOS.map((scenario) => (
          <Button
            key={scenario.id}
            type="button"
            variant="secondary"
            size="sm"
            disabled={isRunning}
            onClick={() => onRunScenario(scenario.apply(currentAssumptions))}
          >
            {scenario.question}
          </Button>
        ))}
      </div>
    </div>
  );
}
