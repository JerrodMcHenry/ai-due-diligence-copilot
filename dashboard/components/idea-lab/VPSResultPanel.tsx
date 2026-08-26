import BaseCard from "@/components/ui/BaseCard";

import type { VPSResult } from "@/types";

function getVpsClasses(value: number | null): string {
  if (value === null) {
    return "text-text-muted";
  }
  if (value >= 7) {
    return "text-success";
  }
  if (value >= 5) {
    return "text-primary";
  }
  return "text-warning";
}

function getCategoryBarColor(score: number | null): string {
  if (score === null) {
    return "bg-surface-muted";
  }
  if (score >= 7) {
    return "bg-success";
  }
  if (score >= 5) {
    return "bg-primary";
  }
  return "bg-warning";
}

type VPSResultPanelProps = {
  result: VPSResult;
  title?: string;
};

// Part 8/14: VPS is never presented without its MODELED label directly
// beside it, and the category/guidance sections below make clear WHAT
// drove the number and WHERE evidence is missing -- never just a grade.
export default function VPSResultPanel({ result, title = "Venture Potential Score" }: VPSResultPanelProps) {
  if (result.vps === null) {
    return (
      <BaseCard className="p-6 text-center">
        <p className="text-sm font-semibold text-text-primary">
          Not enough assumptions yet to model a score.
        </p>
        <p className="mt-2 text-xs text-text-muted">
          Add a few assumptions below — even a market size guess or a
          problem statement — to see an initial Venture Potential Score.
        </p>
      </BaseCard>
    );
  }

  return (
    <div className="space-y-6">
      <BaseCard className="p-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</p>
        <p className={`mt-1 text-5xl font-bold ${getVpsClasses(result.vps)}`}>
          {result.vps.toFixed(1)}
        </p>
        <p className="mt-2 inline-block rounded-full bg-surface-muted px-3 py-1 text-xs font-semibold text-text-muted">
          {result.label}
        </p>
        <p className="mt-2 text-xs text-text-muted">
          Based on your current assumptions — not observed evidence, and not comparable to a real company&rsquo;s SPS.
        </p>
      </BaseCard>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {result.categories.map((category) => (
          <BaseCard key={category.key} className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-secondary">{category.label}</p>
              <p className="text-sm font-semibold text-text-primary">
                {category.score !== null ? category.score.toFixed(1) : "—"}
              </p>
            </div>

            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-muted">
              {category.score !== null ? (
                <div
                  className={`h-full rounded-full ${getCategoryBarColor(category.score)}`}
                  style={{ width: `${Math.max(0, Math.min(100, (category.score / 10) * 100))}%` }}
                />
              ) : null}
            </div>

            {category.score === null ? (
              <p className="mt-1.5 text-[11px] text-text-muted">Not enough assumptions yet</p>
            ) : null}
          </BaseCard>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <GuidanceList title="Strengths" items={result.strengths} icon="▲" iconClass="text-success" />
        <GuidanceList title="Risks" items={result.risks} icon="▼" iconClass="text-danger" />
        <GuidanceList title="Key Assumptions" items={result.key_assumptions} icon="•" iconClass="text-primary" />
        <GuidanceList title="Validation Gaps" items={result.validation_gaps} icon="!" iconClass="text-warning" />
      </div>

      {result.next_milestones.length > 0 ? (
        <BaseCard className="p-5">
          <h3 className="text-sm font-semibold text-text-primary">Next Milestones</h3>
          <p className="mt-1 text-xs text-text-muted">
            Ways to strengthen the modeled venture and reduce uncertainty — not guarantees of success.
          </p>
          <ul className="mt-3 space-y-1.5 text-sm text-text-secondary">
            {result.next_milestones.map((milestone, index) => (
              <li key={index} className="flex gap-2">
                <span aria-hidden="true" className="text-primary">→</span>
                <span>{milestone}</span>
              </li>
            ))}
          </ul>
        </BaseCard>
      ) : null}
    </div>
  );
}

function GuidanceList({
  title,
  items,
  icon,
  iconClass,
}: {
  title: string;
  items: string[];
  icon: string;
  iconClass: string;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <BaseCard className="p-4">
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      <ul className="mt-2 space-y-1.5 text-sm text-text-secondary">
        {items.map((item, index) => (
          <li key={index} className="flex gap-2">
            <span aria-hidden="true" className={iconClass}>{icon}</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </BaseCard>
  );
}
