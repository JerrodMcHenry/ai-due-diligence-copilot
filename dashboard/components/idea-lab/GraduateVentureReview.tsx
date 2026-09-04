"use client";

import { useMemo, useState } from "react";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import { buildGraduationSummaryText, type GraduationSourceVenture } from "@/lib/ventureToStartupHandoff";
import type { MyStartupMembership } from "@/types";

// Phase 31 -- Venture -> Startup Graduation V1, Part 4/5/15. The explicit
// review-before-create step every graduation goes through -- nothing is
// created by opening this panel, only by pressing its own submit button.
// Deliberately an inline expansion (this codebase has no modal component
// anywhere -- see CaptureWhatHappened/the rename affordance in
// VentureWorkspace.tsx for the same established pattern), not a route
// change or a dialog.
//
// Copy audit (Part 15): never "you're ready," "graduated," or
// "congratulations" -- this screen's own language is "create," "connect,"
// and "linked," and the founder chooses the company name themselves
// rather than having one assigned.
type GraduateVentureReviewProps = {
  venture: GraduationSourceVenture;
  existingStartups: MyStartupMembership[];
  isSubmitting: boolean;
  error: string | null;
  onCancel: () => void;
  onSubmit: (args: {
    companyName: string;
    connectExistingStartupId: number | null;
    fieldsTransferredCount: number;
  }) => void;
};

export default function GraduateVentureReview({
  venture,
  existingStartups,
  isSubmitting,
  error,
  onCancel,
  onSubmit,
}: GraduateVentureReviewProps) {
  const [mode, setMode] = useState<"create" | "connect">("create");
  const [companyName, setCompanyName] = useState(venture.name);
  const [connectId, setConnectId] = useState<number | null>(
    existingStartups.length > 0 ? existingStartups[0].startup_id : null
  );

  const summary = useMemo(() => buildGraduationSummaryText(venture), [venture]);

  function handleSubmit() {
    if (mode === "connect") {
      onSubmit({ companyName: "", connectExistingStartupId: connectId, fieldsTransferredCount: 0 });
      return;
    }

    onSubmit({
      companyName: companyName.trim() || venture.name,
      connectExistingStartupId: null,
      fieldsTransferredCount: summary.fieldsIncluded,
    });
  }

  const canSubmit = mode === "create" ? companyName.trim().length > 0 : connectId !== null;

  return (
    <BaseCard variant="raised" className="p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Create Startup Profile</p>
      <p className="mt-1.5 text-sm leading-6 text-text-secondary">
        This creates a real Startup entry linked to this venture, so you can track it going forward. Nothing is
        analyzed yet — you&rsquo;ll review and submit what to analyze next, exactly like any other startup on SIE.
      </p>

      {existingStartups.length > 0 ? (
        <div className="mt-4 flex gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "create"} onChange={() => setMode("create")} />
            Create a new Startup Profile
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "connect"} onChange={() => setMode("connect")} />
            Connect a startup I already have
          </label>
        </div>
      ) : null}

      {mode === "create" ? (
        <div className="mt-4">
          <label htmlFor="graduate-company-name" className="block text-xs font-semibold uppercase tracking-wide text-text-muted">
            Company name
          </label>
          <input
            id="graduate-company-name"
            type="text"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            maxLength={200}
            className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          />

          {summary.text ? (
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                What carries over as a starting point
              </p>
              <p className="mt-1 text-xs text-text-muted">
                You&rsquo;ll be able to edit or remove any of this before it&rsquo;s submitted for analysis.
              </p>
              <pre className="mt-2 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-surface p-3 text-xs leading-5 text-text-secondary">
                {summary.text}
              </pre>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="mt-4">
          <label htmlFor="graduate-connect-select" className="block text-xs font-semibold uppercase tracking-wide text-text-muted">
            Which startup?
          </label>
          <select
            id="graduate-connect-select"
            value={connectId ?? ""}
            onChange={(event) => setConnectId(Number(event.target.value))}
            className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
          >
            {existingStartups.map((startup) => (
              <option key={startup.startup_id} value={startup.startup_id}>
                {startup.canonical_name}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-text-muted">
            Links this venture to a startup you already have access to. Its own intelligence is unaffected.
          </p>
        </div>
      )}

      {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Button type="button" disabled={isSubmitting || !canSubmit} loading={isSubmitting} onClick={handleSubmit}>
          {isSubmitting ? "Creating..." : mode === "create" ? "Create Startup Profile" : "Connect Startup"}
        </Button>
        <Button type="button" variant="subtle" disabled={isSubmitting} onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </BaseCard>
  );
}
