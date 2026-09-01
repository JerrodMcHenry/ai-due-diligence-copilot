import BaseCard from "@/components/ui/BaseCard";
import Disclosure from "@/components/ui/Disclosure";

import { formatHistoryDateGroupLabel, groupHistoryEventsByDate, formatVpsDelta } from "@/lib/journey/formatVentureHistory";

import type { VentureHistoryCategoryChange, VentureHistoryEvent, VentureHistoryResponse } from "@/types";

// Founder Progress / Venture History V1, Section 6. Smallest coherent
// option chosen after investigating the existing codebase: reuses the
// SAME <Disclosure> pattern VentureWorkspace.tsx already uses for "Edit
// the full model" / "Preview your venture card" (option D, "another
// existing pattern already present") rather than a new tab, sub-page, or
// nav item. A compact, always-visible summary (Section 8) sits above the
// disclosure so a returning founder's three questions -- "what changed,"
// "stronger or weaker," "why" -- are answerable without expanding
// anything; the full chronological timeline is one click away, never
// competing with the primary Venture -> What Matters Now -> Current
// Action -> Next Moves hierarchy above it on the page.
type VentureProgressProps = {
  history: VentureHistoryResponse | null;
  isLoading: boolean;
};

export default function VentureProgress({ history, isLoading }: VentureProgressProps) {
  if (isLoading || !history) {
    return <div className="h-24 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  // A brand-new venture has exactly one event (venture_created) --
  // Section 12's honest empty state, never a manufactured history.
  if (history.events.length <= 1) {
    return (
      <BaseCard className="p-6 text-center">
        <h3 className="text-sm font-semibold text-text-primary">Your venture journey starts here</h3>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-text-secondary">
          As you test assumptions, complete founder actions, record what you learn, and update your venture
          model, SIE will build a history of how your startup evolves.
        </p>
      </BaseCard>
    );
  }

  const now = new Date();
  const groups = groupHistoryEventsByDate(history.events, now);

  return (
    <div className="space-y-3">
      <BaseCard className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Your progress</p>
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
          <SummaryStat
            label="Current VPS"
            value={history.current_vps !== null ? history.current_vps.toFixed(1) : "—"}
          />
          <SummaryStat label="Started" value={formatHistoryDateGroupLabel(history.started_at, now)} />
          <SummaryStat label="Actions completed" value={String(history.actions_completed)} />
          <SummaryStat label="Model updates" value={String(history.model_updates_count)} />
        </div>

        {history.strongest_improvement ? (
          <div className="mt-4 border-t border-border pt-3">
            <p className="text-xs font-semibold text-text-muted">Strongest improvement</p>
            <p className="mt-1 text-sm font-medium text-text-primary">
              {history.strongest_improvement.label}{" "}
              <span className="text-success">
                {formatVpsDelta(history.strongest_improvement.before, history.strongest_improvement.after)}
              </span>
            </p>
          </div>
        ) : null}
      </BaseCard>

      <Disclosure summary="Venture history">
        <ol className="space-y-5">
          {groups.map((group) => (
            <li key={group.label}>
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{group.label}</p>
              <ul className="mt-2 space-y-3 border-l-2 border-border pl-4">
                {group.events.map((event, index) => (
                  <li key={`${group.label}-${index}`}>
                    <HistoryEventCard event={event} />
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </Disclosure>
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-0.5 text-lg font-bold text-text-primary">{value}</p>
    </div>
  );
}

function CategoryChangesList({ changes }: { changes: VentureHistoryCategoryChange[] }) {
  if (changes.length === 0) return null;
  return (
    <ul className="mt-2 space-y-1">
      {changes.map((change) => {
        const isImprovement = change.before !== null && change.after !== null && change.after > change.before;
        const isDecline = change.before !== null && change.after !== null && change.after < change.before;
        return (
          <li key={change.key} className="flex items-center justify-between gap-3 text-xs">
            <span className="text-text-secondary">{change.label}</span>
            <span
              className={
                isImprovement ? "font-semibold text-success" : isDecline ? "font-semibold text-danger" : "font-semibold text-text-primary"
              }
            >
              {formatVpsDelta(change.before, change.after)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

// Founder Loop V2, Section 14/15's "no score chasing, no lost-XP
// framing" applied here directly: a model_updated event is always
// introduced the same way regardless of direction -- "Your model changed
// based on new evidence" -- VPS/category deltas are shown as plain facts
// (color only distinguishes up/down, never "good"/"bad" language), and a
// decline is never called "lost progress."
function HistoryEventCard({ event }: { event: VentureHistoryEvent }) {
  if (event.event_type === "venture_created") {
    return (
      <div>
        <p className="text-sm font-semibold text-text-primary">Venture created</p>
        {event.after_vps !== null ? (
          <p className="mt-0.5 text-xs text-text-muted">Initial VPS: {event.after_vps.toFixed(1)}</p>
        ) : null}
      </div>
    );
  }

  if (event.event_type === "action_added") {
    return (
      <div>
        <p className="text-sm font-semibold text-text-primary">Action added</p>
        <p className="mt-0.5 text-sm text-text-secondary">{event.title}</p>
      </div>
    );
  }

  if (event.event_type === "action_completed") {
    return (
      <div>
        <p className="text-sm font-semibold text-text-primary">Action completed</p>
        <p className="mt-0.5 text-sm text-text-secondary">{event.title}</p>
      </div>
    );
  }

  if (event.event_type === "learning_recorded") {
    return (
      <div>
        <p className="text-sm font-semibold text-text-primary">Learning recorded</p>
        {event.description ? (
          <p className="mt-1 text-sm italic leading-6 text-text-secondary">&ldquo;{event.description}&rdquo;</p>
        ) : null}
        {event.mission_title ? <p className="mt-1 text-xs text-text-muted">From &ldquo;{event.mission_title}&rdquo;</p> : null}
      </div>
    );
  }

  // model_updated
  const vpsChanged = event.before_vps !== null && event.after_vps !== null && Math.abs(event.after_vps - event.before_vps) >= 0.05;
  const vpsRose = vpsChanged && event.after_vps! > event.before_vps!;
  const vpsFell = vpsChanged && event.after_vps! < event.before_vps!;

  return (
    <div>
      <p className="text-sm font-semibold text-text-primary">Model updated</p>
      <p className="mt-1 text-sm text-text-secondary">Your model changed based on new evidence.</p>

      <div className="mt-2 flex items-center gap-2 text-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">VPS</span>
        <span
          className={vpsRose ? "font-semibold text-success" : vpsFell ? "font-semibold text-danger" : "font-semibold text-text-primary"}
        >
          {formatVpsDelta(event.before_vps, event.after_vps)}
        </span>
      </div>

      <CategoryChangesList changes={event.category_changes} />

      {event.description ? (
        <p className="mt-2 text-xs text-text-muted">
          Reason: <span className="italic">&ldquo;{event.description}&rdquo;</span>
        </p>
      ) : null}
    </div>
  );
}
