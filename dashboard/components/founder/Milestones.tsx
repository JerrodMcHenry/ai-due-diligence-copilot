"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import { PILLARS } from "@/components/startup/pillarMeta";

import {
  createStartupMilestone,
  getStartupMilestones,
  updateMilestoneStatus,
} from "@/lib/api";

import type { PillarKey } from "@/components/startup/pillarMeta";
import type { MilestoneStatus, StartupMilestone } from "@/types";

type LoadState = "loading" | "ready" | "error";

type MilestonesProps = {
  startupId: number;
};

const PILLAR_LABELS: Record<PillarKey, string> = Object.fromEntries(
  PILLARS.map((pillar) => [pillar.key, pillar.label])
) as Record<PillarKey, string>;

const STATUS_LABELS: Record<MilestoneStatus, string> = {
  planned: "Planned",
  in_progress: "In Progress",
  achieved: "Achieved",
  cancelled: "Cancelled",
};

const STATUS_BADGE_CLASSES: Record<MilestoneStatus, string> = {
  planned: "border border-border text-text-secondary",
  in_progress: "bg-warning/10 text-warning",
  achieved: "bg-success/10 text-success",
  cancelled: "border border-border text-text-muted",
};

function formatTargetDate(iso: string): string {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// Phase 7.4 -- Founder Evidence + Milestones V1. Persistent, shared-
// per-startup workflow state, same Part 11 decision Phase 7.3 made for
// founder_actions: every verified member sees and can act on the exact
// same milestone list. Marking a milestone "achieved" is a plain status
// transition on a startup_milestones row -- it never computes, sends, or
// implies a score (app/database/db.py's own Phase 7.4 section is the
// authoritative "never touches scoring" boundary).
export default function Milestones({ startupId }: MilestonesProps) {
  const { getToken } = useAuth();

  const [milestones, setMilestones] = useState<StartupMilestone[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [pendingIds, setPendingIds] = useState<Set<number>>(new Set());
  const [rowError, setRowError] = useState<string | null>(null);

  const [isCreating, setIsCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [pillar, setPillar] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadMilestones() {
      if (isMounted) {
        setLoadState("loading");
      }

      try {
        const token = await getToken();

        if (!token) {
          if (isMounted) {
            setLoadState("error");
          }
          return;
        }

        const data = await getStartupMilestones(startupId, token);

        if (isMounted) {
          setMilestones(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load milestones:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    loadMilestones();

    return () => {
      isMounted = false;
    };
  }, [startupId, getToken]);

  function upsertMilestone(updated: StartupMilestone) {
    setMilestones((previous) => {
      const exists = previous.some((m) => m.id === updated.id);
      return exists
        ? previous.map((m) => (m.id === updated.id ? updated : m))
        : [...previous, updated];
    });
  }

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setFormError("Enter the milestone you're aiming for.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const token = await getToken();

      if (!token) {
        setFormError("Your session expired. Sign in again.");
        return;
      }

      const created = await createStartupMilestone(
        startupId,
        { title: trimmedTitle, related_pillar: pillar || null, target_date: targetDate || null },
        token
      );
      upsertMilestone(created);
      setTitle("");
      setPillar("");
      setTargetDate("");
      setIsCreating(false);
    } catch (error) {
      console.error("Failed to create milestone:", error);
      setFormError("Couldn't create that milestone. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleStatusChange(milestoneId: number, status: MilestoneStatus) {
    setPendingIds((previous) => new Set(previous).add(milestoneId));
    setRowError(null);

    try {
      const token = await getToken();

      if (!token) {
        setRowError("Your session expired. Sign in again.");
        return;
      }

      const updated = await updateMilestoneStatus(startupId, milestoneId, { status }, token);
      upsertMilestone(updated);
    } catch (error) {
      console.error("Failed to update milestone:", error);
      setRowError("Couldn't update that milestone. Try again.");
    } finally {
      setPendingIds((previous) => {
        const next = new Set(previous);
        next.delete(milestoneId);
        return next;
      });
    }
  }

  if (loadState === "loading") {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (loadState === "error") {
    return (
      <BaseCard className="border-danger/20 bg-danger-soft p-6">
        <h2 className="text-sm font-semibold text-danger">Unable to load Milestones</h2>
        <p className="mt-1 text-sm text-danger/80">Try refreshing the page.</p>
      </BaseCard>
    );
  }

  const visibleMilestones = milestones.filter((m) => m.status !== "cancelled");

  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">Milestones</h2>
      <p className="mt-1 text-sm text-text-muted">
        {visibleMilestones.length > 0
          ? "The meaningful targets this startup is working toward."
          : "Set your first meaningful company milestone."}
      </p>

      {rowError ? <p className="mt-2 text-xs text-danger">{rowError}</p> : null}

      <BaseCard className="mt-4 p-4">
        {visibleMilestones.length === 0 ? (
          <p className="text-sm text-text-muted">No milestones yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {visibleMilestones.map((milestone) => (
              <MilestoneRow
                key={milestone.id}
                milestone={milestone}
                isPending={pendingIds.has(milestone.id)}
                onStatusChange={handleStatusChange}
              />
            ))}
          </ul>
        )}
      </BaseCard>

      <div className="mt-4">
        {isCreating ? (
          <BaseCard className="p-5">
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label htmlFor="milestone-title" className="mb-1.5 block text-sm font-medium text-text-primary">
                  What are you aiming for?
                </label>
                <input
                  id="milestone-title"
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="e.g. Reach $50K MRR"
                  disabled={isSubmitting}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label htmlFor="milestone-pillar" className="mb-1.5 block text-sm font-medium text-text-primary">
                    Related pillar <span className="font-normal text-text-muted">(optional)</span>
                  </label>
                  <select
                    id="milestone-pillar"
                    value={pillar}
                    onChange={(event) => setPillar(event.target.value)}
                    disabled={isSubmitting}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
                  >
                    <option value="">No specific pillar</option>
                    {PILLARS.map((p) => (
                      <option key={p.key} value={p.key}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="milestone-target-date" className="mb-1.5 block text-sm font-medium text-text-primary">
                    Target date <span className="font-normal text-text-muted">(optional)</span>
                  </label>
                  <input
                    id="milestone-target-date"
                    type="date"
                    value={targetDate}
                    onChange={(event) => setTargetDate(event.target.value)}
                    disabled={isSubmitting}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
                  />
                </div>
              </div>

              {formError ? <p className="text-xs text-danger">{formError}</p> : null}

              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Adding…" : "Add milestone"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false);
                    setFormError(null);
                  }}
                  disabled={isSubmitting}
                  className="rounded-lg px-3 py-2 text-sm font-semibold text-text-muted transition-colors hover:text-text-secondary disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Cancel
                </button>
              </div>
            </form>
          </BaseCard>
        ) : (
          <button
            type="button"
            onClick={() => setIsCreating(true)}
            className="rounded-lg border border-dashed border-border px-4 py-2.5 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
          >
            + Add milestone
          </button>
        )}
      </div>
    </section>
  );
}

function MilestoneRow({
  milestone,
  isPending,
  onStatusChange,
}: {
  milestone: StartupMilestone;
  isPending: boolean;
  onStatusChange: (milestoneId: number, status: MilestoneStatus) => void;
}) {
  const pillarLabel = milestone.related_pillar
    ? PILLAR_LABELS[milestone.related_pillar as PillarKey]
    : null;

  return (
    <li className={["flex flex-wrap items-center justify-between gap-3 py-3", milestone.status === "achieved" ? "opacity-90" : ""].join(" ")}>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          {milestone.status === "achieved" ? (
            <span aria-hidden="true" className="text-success">✓</span>
          ) : null}
          <p className="truncate text-sm font-medium text-text-primary">{milestone.title}</p>
        </div>

        <div className="mt-1 flex flex-wrap items-center gap-1.5">
          <span
            className={["rounded-full px-2 py-0.5 text-xs font-medium", STATUS_BADGE_CLASSES[milestone.status]].join(" ")}
          >
            {STATUS_LABELS[milestone.status]}
          </span>
          {pillarLabel ? (
            <span className="rounded-full border border-border px-2 py-0.5 text-xs font-medium text-text-muted">
              {pillarLabel}
            </span>
          ) : null}
          {milestone.target_date ? (
            <span className="text-xs text-text-muted">Target: {formatTargetDate(milestone.target_date)}</span>
          ) : null}
        </div>
      </div>

      <div className="flex shrink-0 flex-wrap gap-2">
        {milestone.status === "planned" ? (
          <>
            <MilestoneButton label="Start" primary disabled={isPending} onClick={() => onStatusChange(milestone.id, "in_progress")} />
            <MilestoneButton label="Cancel" disabled={isPending} onClick={() => onStatusChange(milestone.id, "cancelled")} />
          </>
        ) : null}

        {milestone.status === "in_progress" ? (
          <>
            <MilestoneButton label="Mark Achieved" primary disabled={isPending} onClick={() => onStatusChange(milestone.id, "achieved")} />
            <MilestoneButton label="Cancel" disabled={isPending} onClick={() => onStatusChange(milestone.id, "cancelled")} />
          </>
        ) : null}

        {milestone.status === "achieved" ? (
          <MilestoneButton label="Reopen" disabled={isPending} onClick={() => onStatusChange(milestone.id, "planned")} />
        ) : null}
      </div>
    </li>
  );
}

function MilestoneButton({
  label,
  onClick,
  disabled,
  primary,
}: {
  label: string;
  onClick: () => void;
  disabled: boolean;
  primary?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={[
        "rounded-md px-2.5 py-1 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        primary ? "bg-primary text-white hover:bg-primary-hover" : "border border-border text-text-muted hover:text-text-secondary",
      ].join(" ")}
    >
      {label}
    </button>
  );
}
