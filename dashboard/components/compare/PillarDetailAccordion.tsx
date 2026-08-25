import { PILLARS } from "@/components/startup/pillarMeta";

import { gridColsClass } from "./gridCols";

import type { ComparisonStartup } from "@/types";

type PillarDetailAccordionProps = {
  startups: ComparisonStartup[];
};

// Part 11/12: progressive disclosure via native <details>/<summary> --
// collapsed by default (28 dimensions across up to 4 companies is never
// shown all at once), fully keyboard-operable and screen-reader
// announced with no custom ARIA needed. One panel per pillar; each
// panel's own contents (strengths/weaknesses, then dimensions) reuse the
// SAME structured lists the Startup Profile already renders -- nothing
// here is re-summarized by an LLM.
export default function PillarDetailAccordion({
  startups,
}: PillarDetailAccordionProps) {
  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">
        Detailed Intelligence
      </h2>

      <div className="mt-4 space-y-3">
        {PILLARS.map((pillar) => (
          <details
            key={pillar.key}
            className="group rounded-2xl border border-border bg-surface open:pb-2"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-semibold text-text-primary marker:content-none">
              {pillar.label}

              <span
                aria-hidden="true"
                className="text-text-muted transition-transform group-open:rotate-180"
              >
                ▾
              </span>
            </summary>

            <div className="space-y-6 px-5 pb-4">
              <StrengthsWeaknesses pillarKey={pillar.key} startups={startups} />
              <DimensionRows pillarKey={pillar.key} startups={startups} />
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

function StrengthsWeaknesses({
  pillarKey,
  startups,
}: {
  pillarKey: (typeof PILLARS)[number]["key"];
  startups: ComparisonStartup[];
}) {
  return (
    <div className={`grid gap-4 ${gridColsClass(startups.length)}`}>
      {startups.map((startup) => {
        const pillarData = startup[pillarKey];

        return (
          <div key={startup.startup_id} className="min-w-0">
            <p className="truncate text-xs font-semibold text-text-muted">
              {startup.company_name}
            </p>

            {pillarData.strengths.length === 0 &&
            pillarData.weaknesses.length === 0 ? (
              <p className="mt-2 text-xs text-text-muted">
                No structured strengths/weaknesses recorded.
              </p>
            ) : (
              <>
                {pillarData.strengths.length > 0 ? (
                  <ul className="mt-2 space-y-1 text-xs text-text-secondary">
                    {pillarData.strengths.map((strength, index) => (
                      <li key={index} className="flex gap-1.5">
                        <span aria-hidden="true" className="text-success">
                          +
                        </span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                ) : null}

                {pillarData.weaknesses.length > 0 ? (
                  <ul className="mt-2 space-y-1 text-xs text-text-secondary">
                    {pillarData.weaknesses.map((weakness, index) => (
                      <li key={index} className="flex gap-1.5">
                        <span aria-hidden="true" className="text-danger">
                          −
                        </span>
                        <span>{weakness}</span>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function DimensionRows({
  pillarKey,
  startups,
}: {
  pillarKey: (typeof PILLARS)[number]["key"];
  startups: ComparisonStartup[];
}) {
  // Union of dimension names across all selected startups, in first-seen
  // order -- every startup within one pillar is scored against the same
  // rubric (scoring_methodology.py), so in practice these names already
  // match across companies; the union just protects against one startup
  // having a dimension genuinely Unavailable and therefore absent from
  // its own subscores list.
  const dimensionNames: string[] = [];
  for (const startup of startups) {
    for (const subscore of startup[pillarKey].subscores) {
      if (!dimensionNames.includes(subscore.name)) {
        dimensionNames.push(subscore.name);
      }
    }
  }

  if (dimensionNames.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-border pt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        Dimensions
      </p>

      <div className="mt-3 space-y-4">
        {dimensionNames.map((dimensionName) => (
          <div key={dimensionName}>
            <p className="text-xs font-medium text-text-secondary">
              {dimensionName}
            </p>

            <dl className={`mt-1.5 grid gap-2 ${gridColsClass(startups.length)}`}>
              {startups.map((startup) => {
                const subscore = startup[pillarKey].subscores.find(
                  (entry) => entry.name === dimensionName
                );

                return (
                  <div key={startup.startup_id} className="flex items-center justify-between gap-2 text-xs">
                    <dt className="truncate text-text-muted">
                      {startup.company_name}
                    </dt>

                    <dd className="shrink-0 font-semibold text-text-primary">
                      {subscore && subscore.score !== null
                        ? subscore.score.toFixed(1)
                        : subscore
                          ? "Unavailable"
                          : "—"}
                    </dd>
                  </div>
                );
              })}
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
