import Button from "@/components/ui/Button";
import ConceptDisclosure from "@/components/learn/ConceptDisclosure";
import { getMetricConceptForWhatIfScenario } from "@/content/concepts";

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

  // Learn V1, Part 15: "if a scenario uses a concept like CAC/gross
  // margin/pricing/churn, the founder should be able to understand the
  // concept... do not turn What If into a lesson page." ONE small,
  // collapsed-by-default section below the chips -- not a trigger per
  // chip, which would be exactly the clutter Part 19 warns against --
  // covering only the concepts the CURRENTLY offered scenarios actually
  // reference, deduplicated. Never mutates a scenario or changes what
  // clicking a chip does.
  const referencedConceptKeys = Array.from(
    new Set(
      scenarios
        .map((scenario) => getMetricConceptForWhatIfScenario(scenario.id)?.key)
        .filter((key): key is string => Boolean(key))
    )
  );

  const conceptValueByKey: Record<string, number | null> = {
    cac: currentAssumptions.gtm.expected_cac,
    gross_margin: currentAssumptions.economics.expected_gross_margin_pct,
    retention: currentAssumptions.validation.retention_pct,
  };

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

      {referencedConceptKeys.length > 0 ? (
        <div className="mt-3 space-y-1.5 border-t border-border pt-3">
          <p className="text-[11px] font-semibold text-text-muted">New to these terms?</p>
          {referencedConceptKeys.map((key) => (
            <ConceptDisclosure key={key} conceptKey={key} value={conceptValueByKey[key] ?? null} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
