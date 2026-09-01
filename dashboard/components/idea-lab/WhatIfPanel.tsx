import Button from "@/components/ui/Button";

import { getWhatIfScenarios } from "./whatIfScenarios";

import type { VentureAssumptions } from "@/types";

// Phase 10.6 -- Idea Lab V2, Part 7. Elevates the existing scenario
// simulator into a first-class "What if?" experience -- one tap runs a
// real preview through the SAME compareVentureScenarios()/scenario-
// compare mechanism the manual assumption editor already used; this
// panel only supplies WHICH fields to change, never a different
// calculation path.
//
// Founder Loop V2, Section 6: scenarios are now generated from the
// venture's own current assumptions (getWhatIfScenarios(), replacing a
// fixed five-preset list) and each is visibly tagged Upside/Downside --
// see whatIfScenarios.ts's own docstring for why.
type WhatIfPanelProps = {
  currentAssumptions: VentureAssumptions;
  onRunScenario: (modifiedAssumptions: VentureAssumptions) => void;
  isRunning: boolean;
};

export default function WhatIfPanel({ currentAssumptions, onRunScenario, isRunning }: WhatIfPanelProps) {
  const scenarios = getWhatIfScenarios(currentAssumptions);

  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">What if?</h3>
      <p className="mt-1 text-xs text-text-muted">
        Try a real scenario, based on where your venture stands today — nothing is saved until you choose to
        apply it.
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        {scenarios.map((scenario) => (
          <Button
            key={scenario.id}
            type="button"
            variant="secondary"
            size="sm"
            disabled={isRunning}
            // scenario.apply is typed against whatIfScenarios.ts's own
            // minimal structural subset (so that module stays free of
            // "@/..." alias imports -- see its own docstring), but at
            // runtime it always receives and, via a top-level object
            // spread, fully preserves this real VentureAssumptions
            // object -- every scenario patches exactly one or two
            // nested fields and spreads everything else through
            // unchanged. The cast reflects that real, documented
            // runtime contract, not an unchecked escape hatch.
            onClick={() => onRunScenario(scenario.apply(currentAssumptions) as VentureAssumptions)}
            className="inline-flex items-center gap-1.5"
          >
            <span
              className={[
                "rounded-full px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
                scenario.direction === "upside"
                  ? "bg-success-soft text-success"
                  : "bg-danger-soft text-danger",
              ].join(" ")}
            >
              {scenario.direction === "upside" ? "Upside" : "Risk"}
            </span>
            {scenario.question}
          </Button>
        ))}
      </div>
    </div>
  );
}
