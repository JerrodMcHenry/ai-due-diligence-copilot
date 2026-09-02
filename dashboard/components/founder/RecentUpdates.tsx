"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import { PILLARS } from "@/components/startup/pillarMeta";

import { createFounderUpdate, editFounderUpdate, getFounderUpdates } from "@/lib/api";
import { extractCaptureSignals } from "@/lib/captureSignals";

import type { PillarKey } from "@/components/startup/pillarMeta";
import type {
  FounderUpdate,
  FounderUpdateRequestFields,
  FounderUpdateType,
} from "@/types";

type LoadState = "loading" | "ready" | "error";

type RecentUpdatesProps = {
  startupId: number;
};

const PILLAR_LABELS: Record<PillarKey, string> = Object.fromEntries(
  PILLARS.map((pillar) => [pillar.key, pillar.label])
) as Record<PillarKey, string>;

const UPDATE_TYPE_LABELS: Record<FounderUpdateType, string> = {
  customer: "Customer",
  revenue: "Revenue",
  product: "Product",
  team: "Team",
  fundraising: "Fundraising",
  partnership: "Partnership",
  validation: "Validation",
  operations: "Operations",
  other: "Other",
};

const UPDATE_TYPES = Object.keys(UPDATE_TYPE_LABELS) as FounderUpdateType[];

function todayDateInputValue(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatUpdateDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

// Phase 7.4 -- Founder Evidence + Milestones V1. Every row here is
// FOUNDER-REPORTED -- "Founder reported" is shown on every single item,
// deliberately, so this can never be mistaken for independently
// verified canonical evidence (see app/models/founder_update.py's own
// docstring). Recording an update never touches SPS or methodology --
// this is the private foundation for a later unified Startup Timeline
// (Part 10), not that timeline itself.
export default function RecentUpdates({ startupId }: RecentUpdatesProps) {
  const { getToken } = useAuth();

  const [updates, setUpdates] = useState<FounderUpdate[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadUpdates() {
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

        const data = await getFounderUpdates(startupId, token);

        if (isMounted) {
          setUpdates(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load Recent Updates:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    loadUpdates();

    return () => {
      isMounted = false;
    };
  }, [startupId, getToken]);

  function upsertUpdate(updated: FounderUpdate) {
    setUpdates((previous) => {
      const exists = previous.some((u) => u.id === updated.id);
      const next = exists
        ? previous.map((u) => (u.id === updated.id ? updated : u))
        : [updated, ...previous];
      // Keep newest-first by occurred_at, matching the backend's own
      // ordering, since an edit can change occurred_at.
      return [...next].sort(
        (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime()
      );
    });
  }

  async function handleCreate(fields: FounderUpdateRequestFields) {
    const token = await getToken();
    if (!token) {
      setRowError("Your session expired. Sign in again.");
      return false;
    }

    try {
      const created = await createFounderUpdate(startupId, fields, token);
      upsertUpdate(created);
      setIsAdding(false);
      return true;
    } catch (error) {
      console.error("Failed to record update:", error);
      setRowError("Couldn't record that update. Try again.");
      return false;
    }
  }

  async function handleEdit(updateId: number, fields: FounderUpdateRequestFields) {
    const token = await getToken();
    if (!token) {
      setRowError("Your session expired. Sign in again.");
      return false;
    }

    try {
      const updated = await editFounderUpdate(startupId, updateId, fields, token);
      upsertUpdate(updated);
      setEditingId(null);
      return true;
    } catch (error) {
      console.error("Failed to edit update:", error);
      setRowError("Couldn't save that edit. Try again.");
      return false;
    }
  }

  if (loadState === "loading") {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (loadState === "error") {
    return (
      <BaseCard className="border-danger/20 bg-danger-soft p-6">
        <h2 className="text-sm font-semibold text-danger">Unable to load Recent Updates</h2>
        <p className="mt-1 text-sm text-danger/80">Try refreshing the page.</p>
      </BaseCard>
    );
  }

  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">Recent Updates</h2>
      <p className="mt-1 text-sm text-text-muted">
        {updates.length > 0
          ? "Founder-reported progress, newest first."
          : "Record meaningful progress as your startup evolves."}
      </p>

      {rowError ? <p className="mt-2 text-xs text-danger">{rowError}</p> : null}

      {updates.length > 0 ? (
        <BaseCard className="mt-4 divide-y divide-border p-0">
          {updates.map((update) =>
            editingId === update.id ? (
              <div key={update.id} className="p-5">
                <UpdateForm
                  initial={update}
                  onCancel={() => setEditingId(null)}
                  onSubmit={(fields) => handleEdit(update.id, fields)}
                  submitLabel="Save"
                />
              </div>
            ) : (
              <div key={update.id} className="flex items-start justify-between gap-3 px-5 py-4">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-text-muted">{formatUpdateDate(update.occurred_at)}</p>
                  <p className="mt-0.5 text-sm font-medium text-text-primary">{update.title}</p>
                  <p className="mt-1 text-xs text-text-muted">
                    {UPDATE_TYPE_LABELS[update.update_type]}
                    {update.related_pillar ? ` · ${PILLAR_LABELS[update.related_pillar as PillarKey]}` : ""}
                    {" · "}
                    <span className="font-medium text-text-secondary">Founder reported</span>
                  </p>
                  {update.metric_name && update.metric_value !== null ? (
                    <p className="mt-1 text-xs text-text-muted">
                      {update.metric_name}: {update.metric_value.toLocaleString()} {update.metric_unit ?? ""}
                    </p>
                  ) : null}
                  {update.description ? (
                    <p className="mt-1.5 max-w-prose text-sm text-text-secondary">{update.description}</p>
                  ) : null}
                </div>

                <button
                  type="button"
                  onClick={() => setEditingId(update.id)}
                  className="shrink-0 text-xs font-semibold text-text-muted hover:text-primary"
                >
                  Edit
                </button>
              </div>
            )
          )}
        </BaseCard>
      ) : null}

      <div className="mt-4">
        {isAdding ? (
          <BaseCard className="p-5">
            <UpdateForm onCancel={() => setIsAdding(false)} onSubmit={handleCreate} submitLabel="Record update" />
          </BaseCard>
        ) : (
          <button
            type="button"
            onClick={() => setIsAdding(true)}
            className="rounded-lg border border-dashed border-border px-4 py-2.5 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
          >
            + Add Update
          </button>
        )}
      </div>
    </section>
  );
}

// Shared by "Add Update" and inline "Edit" -- same fields either way
// (Part 13: edit is a full-field correction, not a partial patch).
// Deliberately fast by default: title + type + date are the only
// required fields, description and the optional metric are both tucked
// behind their own small disclosures so recording a plain update stays
// a ~15-30 second action.
function UpdateForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel,
}: {
  initial?: FounderUpdate;
  onSubmit: (fields: FounderUpdateRequestFields) => Promise<boolean>;
  onCancel: () => void;
  submitLabel: string;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [updateType, setUpdateType] = useState<FounderUpdateType>(initial?.update_type ?? "other");
  const [pillar, setPillar] = useState(initial?.related_pillar ?? "");
  const [occurredAt, setOccurredAt] = useState(
    initial ? initial.occurred_at.slice(0, 10) : todayDateInputValue()
  );
  const [description, setDescription] = useState(initial?.description ?? "");
  const [showMetric, setShowMetric] = useState(Boolean(initial?.metric_name));
  const [metricName, setMetricName] = useState(initial?.metric_name ?? "");
  const [metricValue, setMetricValue] = useState(
    initial?.metric_value !== undefined && initial?.metric_value !== null
      ? String(initial.metric_value)
      : ""
  );
  const [metricUnit, setMetricUnit] = useState(initial?.metric_unit ?? "");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setError("What happened?");
      return;
    }

    const hasMetric = showMetric && metricName.trim() && metricValue.trim();
    const parsedMetricValue = hasMetric ? Number(metricValue) : null;

    if (showMetric && metricName.trim() && metricValue.trim() && Number.isNaN(parsedMetricValue)) {
      setError("The number for your metric isn't valid.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const ok = await onSubmit({
      title: trimmedTitle,
      update_type: updateType,
      related_pillar: pillar || null,
      occurred_at: new Date(`${occurredAt}T00:00:00`).toISOString(),
      description: description.trim() || null,
      metric_name: hasMetric ? metricName.trim() : null,
      metric_value: hasMetric ? parsedMetricValue : null,
      metric_unit: hasMetric ? metricUnit.trim() || null : null,
    });

    setIsSubmitting(false);

    if (!ok) {
      setError("Couldn't save. Try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label htmlFor="update-title" className="mb-1.5 block text-sm font-medium text-text-primary">
          What happened?
        </label>
        <input
          id="update-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. Signed 5 new customers"
          disabled={isSubmitting}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
        />
        {/* Phase 23 -- Universal Founder Capture V1, Part 14: the SAME
            deterministic, zero-AI signal detector the Idea Lab capture
            surface uses (lib/captureSignals.ts) -- shown here purely as
            an informational preview, never auto-filling a field. This
            never becomes SPS evidence and never changes update_type or
            the metric fields on its own; the founder still types
            everything themselves. Keeps this track's own "What
            happened?" moment honestly on par with the venture track's,
            without touching founder_update's evidence semantics. */}
        {title.trim() ? (
          (() => {
            const signals = extractCaptureSignals(title);
            return signals.length > 0 ? (
              <p className="mt-1.5 text-xs text-text-muted">
                SIE noticed: {signals.map((s) => s.label).join(", ")}
              </p>
            ) : null;
          })()
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <label htmlFor="update-type" className="mb-1.5 block text-sm font-medium text-text-primary">
            Type
          </label>
          <select
            id="update-type"
            value={updateType}
            onChange={(event) => setUpdateType(event.target.value as FounderUpdateType)}
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          >
            {UPDATE_TYPES.map((type) => (
              <option key={type} value={type}>
                {UPDATE_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="update-pillar" className="mb-1.5 block text-sm font-medium text-text-primary">
            Pillar <span className="font-normal text-text-muted">(optional)</span>
          </label>
          <select
            id="update-pillar"
            value={pillar}
            onChange={(event) => setPillar(event.target.value)}
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          >
            <option value="">None</option>
            {PILLARS.map((p) => (
              <option key={p.key} value={p.key}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="update-occurred-at" className="mb-1.5 block text-sm font-medium text-text-primary">
            When?
          </label>
          <input
            id="update-occurred-at"
            type="date"
            value={occurredAt}
            onChange={(event) => setOccurredAt(event.target.value)}
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          />
        </div>
      </div>

      {showMetric ? (
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            type="text"
            value={metricName}
            onChange={(event) => setMetricName(event.target.value)}
            placeholder="Metric (e.g. MRR)"
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          />
          <input
            type="text"
            inputMode="decimal"
            value={metricValue}
            onChange={(event) => setMetricValue(event.target.value)}
            placeholder="Value (e.g. 25000)"
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          />
          <input
            type="text"
            value={metricUnit}
            onChange={(event) => setMetricUnit(event.target.value)}
            placeholder="Unit (e.g. USD)"
            disabled={isSubmitting}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          />
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowMetric(true)}
          className="text-xs font-semibold text-primary hover:text-primary-hover"
        >
          + Add a number (optional)
        </button>
      )}

      <details className="text-sm">
        <summary className="cursor-pointer text-xs font-semibold text-text-muted hover:text-text-secondary">
          Add more detail (optional)
        </summary>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={2}
          placeholder="Any additional context worth recording."
          disabled={isSubmitting}
          className="mt-2 w-full resize-y rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
        />
      </details>

      <p className="text-xs leading-5 text-text-muted">
        This is recorded as founder-reported progress, not independently verified
        evidence. It never changes your SPS.
      </p>

      {error ? <p className="text-xs text-danger">{error}</p> : null}

      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Saving…" : submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="rounded-lg px-3 py-2 text-sm font-semibold text-text-muted transition-colors hover:text-text-secondary disabled:cursor-not-allowed disabled:opacity-60"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
