import BaseCard from "@/components/ui/BaseCard";
import Badge from "@/components/ui/Badge";
import Disclosure from "@/components/ui/Disclosure";
import PlaybookLink from "@/components/playbooks/PlaybookLink";

import OwnershipBar from "./OwnershipBar";
import FundraisingDisclaimer from "./FundraisingDisclaimer";

import type { ScenarioResult } from "@/lib/fundraisingUi/types";

type FundraisingResultProps = {
  result: ScenarioResult;
};

// Phase 21B, Part 9/11/12/13/14/18/26/27/32. Consequence-first: the
// headline "what this means for you" comes before any spreadsheet, the
// detailed cap table and calculation trace are secondary (collapsed)
// information, and an untrustworthy engine result is BLOCKED outright
// (Part 9) rather than shown with a caveat. Neutral framing throughout --
// no "good deal"/"bad deal" language, no score (Part 21/26).
export default function FundraisingResult({ result }: FundraisingResultProps) {
  if (result.kind === "invalid") {
    return (
      <BaseCard className="border-danger/20 bg-danger-soft p-5">
        <p className="text-sm font-semibold text-danger">This scenario can&rsquo;t be modeled yet</p>
        <p className="mt-1 text-sm text-danger/90">{result.message}</p>
      </BaseCard>
    );
  }

  if (result.kind === "blocked") {
    return (
      <BaseCard className="border-warning/30 bg-warning-soft p-5">
        <p className="text-sm font-semibold text-text-primary">{result.reason}</p>
        <ul className="mt-3 space-y-2">
          {result.warnings.map((w, i) => (
            <li key={i} className="text-sm leading-6 text-text-secondary">
              {w}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-text-muted">
          Try adjusting the round&rsquo;s valuation, or the SAFE&rsquo;s cap, and simulate again.
        </p>
      </BaseCard>
    );
  }

  const founder = result.founderDilution;

  return (
    <div className="space-y-5">
      {result.isEstimateOnly ? (
        <Badge tone="info">Estimate -- not final until a triggering financing event</Badge>
      ) : null}

      <BaseCard className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What this means for you</p>

        {founder ? (
          <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="text-sm text-text-secondary">Founder ownership</span>
            {/* Visual-acceptance-pass finding: kept as one inline-flex unit
                (not individually wrappable spans) so a narrow (~390px)
                viewport wraps between the label and this pair, never
                between the arrow and its value -- the old layout let
                "70.00% ->" end one line with "63.00%" stranded alone on
                the next. */}
            <span className="inline-flex items-baseline gap-2 whitespace-nowrap">
              <span className="text-2xl font-bold text-text-primary">
                {result.startingOwnership.find((r) => r.role === "founder")?.beforePercent ?? "—"}
              </span>
              <span aria-hidden="true" className="text-text-muted">→</span>
              <span className="text-2xl font-bold text-text-primary">
                {result.finalOwnership.find((r) => r.role === "founder")?.afterPercent ?? "—"}
              </span>
            </span>
          </div>
        ) : null}

        <dl className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-text-muted">Capital raised</dt>
            <dd className="text-base font-semibold text-text-primary">{result.capitalRaisedLabel}</dd>
          </div>
          {founder ? (
            <div>
              <dt className="text-xs text-text-muted">Founder dilution</dt>
              <dd className="text-base font-semibold text-text-primary">
                {founder.percentDilution} <span className="text-xs font-normal text-text-muted">({founder.pointChange} points)</span>
              </dd>
            </div>
          ) : null}
          {result.runway ? (
            <div>
              <dt className="text-xs text-text-muted">Modeled runway</dt>
              <dd className="text-base font-semibold text-text-primary">{result.runway.postFinancingLabel}</dd>
            </div>
          ) : null}
        </dl>
      </BaseCard>

      <BaseCard className="p-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <OwnershipBar title="Before" rows={result.startingOwnership} percentField="beforePercent" />
          <OwnershipBar title="After" rows={result.finalOwnership} percentField="afterPercent" />
        </div>
      </BaseCard>

      {result.runway ? (
        <BaseCard className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Modeled runway</p>
          <div className="mt-2 flex flex-wrap items-baseline gap-3">
            <span className="text-sm text-text-secondary">Current</span>
            <span className="text-lg font-semibold text-text-primary">{result.runway.currentLabel}</span>
            <span aria-hidden="true" className="text-text-muted">→</span>
            <span className="text-sm text-text-secondary">After this financing</span>
            <span className="text-lg font-semibold text-text-primary">{result.runway.postFinancingLabel}</span>
          </div>
          <p className="mt-2 text-sm text-text-muted">{result.runway.note}</p>
        </BaseCard>
      ) : null}

      <Disclosure summary="Detailed cap table">
        <div className="overflow-x-auto">
          {/* Visual-acceptance-pass finding: min-w-[360px] forced
              horizontal scrolling on a ~390px card (padding leaves
              ~317px), clipping the "Ownership" header down to "OWNER"
              with no visible scroll affordance. No forced minimum --
              columns shrink to fit naturally; overflow-x-auto above
              remains as a safety net for pathologically long names. */}
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="py-1.5 pr-3 font-semibold">Stakeholder</th>
                <th className="py-1.5 pr-3 font-semibold">Shares</th>
                <th className="py-1.5 font-semibold">Ownership</th>
              </tr>
            </thead>
            <tbody>
              {result.detailedCapTable.map((row) => (
                <tr key={row.name} className="border-t border-border">
                  <td className="max-w-[140px] break-words py-2 pr-3 text-text-primary">{row.name}</td>
                  <td className="py-2 pr-3 text-text-secondary">{row.shares}</td>
                  <td className="py-2 font-semibold text-text-primary">{row.ownership}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Disclosure>

      <Disclosure summary="How was this calculated?">
        <ol className="space-y-3">
          {result.trace.map((step, i) => (
            <li key={i} className="text-sm leading-6">
              <span className="font-semibold text-text-primary">{step.label}.</span>{" "}
              <span className="text-text-secondary">{step.detail}</span>
            </li>
          ))}
        </ol>
      </Disclosure>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <FundraisingDisclaimer />
        <PlaybookLink slug="cap-table" label="Learn how startup fundraising works →" />
      </div>
    </div>
  );
}
