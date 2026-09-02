import BaseCard from "@/components/ui/BaseCard";
import FundraisingDisclaimer from "./FundraisingDisclaimer";

import type { ScenarioResult } from "@/lib/fundraisingUi/types";

type FundraisingScenarioCompareProps = {
  labelA: string;
  labelB: string;
  resultA: ScenarioResult;
  resultB: ScenarioResult;
};

function summaryRow(label: string, a: string, b: string) {
  return (
    <tr className="border-t border-border">
      <td className="py-2 pr-3 text-xs font-medium text-text-muted">{label}</td>
      <td className="max-w-[120px] break-words py-2 pr-3 text-sm font-semibold text-text-primary">{a}</td>
      <td className="max-w-[120px] break-words py-2 text-sm font-semibold text-text-primary">{b}</td>
    </tr>
  );
}

function extractSummary(result: ScenarioResult) {
  if (result.kind !== "success") {
    return { capital: "—", founder: "—", runway: "—" };
  }
  const founder = result.finalOwnership.find((r) => r.role === "founder");
  return {
    capital: result.capitalRaisedLabel,
    founder: founder ? `${founder.afterPercent}${result.founderDilution ? ` (${result.founderDilution.percentDilution} dilution)` : ""}` : "—",
    runway: result.runway?.postFinancingLabel ?? "Not modeled",
  };
}

// Phase 21B, Part 19/20/21. Compares two scenarios side by side --
// deliberately restrained: capital / ownership / dilution / runway only,
// never a score, never a "Scenario B is better" verdict (Part 21/26: "no
// recommendation, no score -- say 'here's what changes'"). Stacks
// vertically on mobile via a horizontally-scrollable table rather than a
// cramped side-by-side layout (Part 20/38).
export default function FundraisingScenarioCompare({ labelA, labelB, resultA, resultB }: FundraisingScenarioCompareProps) {
  const a = extractSummary(resultA);
  const b = extractSummary(resultB);

  return (
    <div className="space-y-5">
      <BaseCard className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Here&rsquo;s what changes</p>
        <div className="mt-3 overflow-x-auto">
          {/* Visual-acceptance-pass finding: min-w-[420px] forced
              horizontal scrolling on a ~390px card, clipping the
              Scenario B column almost entirely out of view with no
              visible scroll affordance. No forced minimum -- columns
              shrink and value cells wrap naturally instead. */}
          <table className="w-full text-left">
            <thead>
              <tr>
                <th className="py-1.5 pr-3 text-xs font-semibold uppercase tracking-wide text-text-muted"> </th>
                <th className="py-1.5 pr-3 text-sm font-bold text-text-primary">{labelA}</th>
                <th className="py-1.5 text-sm font-bold text-text-primary">{labelB}</th>
              </tr>
            </thead>
            <tbody>
              {summaryRow("Capital raised", a.capital, b.capital)}
              {summaryRow("Founder ownership after", a.founder, b.founder)}
              {summaryRow("Modeled runway", a.runway, b.runway)}
            </tbody>
          </table>
        </div>
      </BaseCard>

      <div className="grid gap-5 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-semibold text-text-primary">{labelA}</p>
          <ScenarioMini result={resultA} />
        </div>
        <div>
          <p className="mb-2 text-sm font-semibold text-text-primary">{labelB}</p>
          <ScenarioMini result={resultB} />
        </div>
      </div>

      <FundraisingDisclaimer />
    </div>
  );
}

function ScenarioMini({ result }: { result: ScenarioResult }) {
  if (result.kind === "invalid") {
    return <BaseCard className="border-danger/20 bg-danger-soft p-4 text-sm text-danger">{result.message}</BaseCard>;
  }
  if (result.kind === "blocked") {
    return <BaseCard className="border-warning/30 bg-warning-soft p-4 text-sm text-text-primary">{result.reason}</BaseCard>;
  }
  return (
    <BaseCard className="p-4">
      <ul className="space-y-1.5">
        {result.finalOwnership.map((row) => (
          <li key={row.id} className="flex items-center justify-between text-sm">
            <span className="text-text-secondary">{row.name}</span>
            <span className="font-semibold text-text-primary">{row.afterPercent}</span>
          </li>
        ))}
      </ul>
    </BaseCard>
  );
}
