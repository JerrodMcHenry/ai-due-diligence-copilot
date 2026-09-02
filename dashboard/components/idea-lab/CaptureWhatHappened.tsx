"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import CategoryChangesList from "./CategoryChangesList";
import { explainCategoryChanges, type CategoryChange } from "./categoryChangeExplain";
import { extractCaptureSignals, type ProposedSignal } from "@/lib/captureSignals";
import { captureVentureObservation, updateVenture } from "@/lib/api";

import type { VentureAssumptions, VentureMission, VentureResponse, VPSResult } from "@/types";

// Phase 23 -- Universal Founder Capture V1.
//
// THE VPS FIREWALL, restated exactly as MissionsSection.tsx's own does:
// the ONLY call in this file that can change a score is
// handleUpdateModel()'s explicit updateVenture() call -- the exact same
// PUT /ventures/{id} the manual assumption editor, Apply&Save, and
// MissionsSection's own "Update my model" already use. Saving an
// observation (handleSave, POST /ventures/{id}/capture) can NEVER reach
// that call on its own; it is a fully separate, later, founder-initiated
// action (Part 7).
//
// Placement (Part 2): rendered directly in VentureWorkspace, near the top
// -- a founder should never need to open Progress or "Edit the full
// model" merely to record something that happened.
const CATEGORY_OPTIONS: { value: string; label: string }[] = [
  { value: "customer_conversation", label: "Customer conversation" },
  { value: "customer_revenue", label: "Customer / revenue" },
  { value: "product", label: "Product" },
  { value: "experiment", label: "Experiment" },
  { value: "fundraising", label: "Fundraising" },
  { value: "market_competitor", label: "Market / competitor" },
  { value: "team", label: "Team" },
  { value: "other", label: "Other" },
];

type Step = "collapsed" | "writing" | "saved";

type CaptureWhatHappenedProps = {
  ventureId: number;
  currentAssumptions: VentureAssumptions;
  currentModelResult: VPSResult | null;
  ventureRequestBase: {
    name: string;
    description: string | null;
    industry: string | null;
    business_model: string | null;
    target_customer: string | null;
    stage: string | null;
  };
  onVentureUpdated: (updated: VentureResponse) => void;
  // Founder Progress / Venture History V1's own refresh signal --
  // MissionsSection fires this after every mission-list mutation; a
  // capture is exactly that (a new completed venture_missions row), so
  // it reuses the identical signal rather than adding a second one.
  onHistoryChanged?: () => void;
};

function applyProposedValue(
  assumptions: VentureAssumptions,
  fieldPath: ProposedSignal["fieldPath"],
  delta: number
): VentureAssumptions {
  if (fieldPath === "validation.customer_interviews") {
    const current = assumptions.validation.customer_interviews ?? 0;
    return { ...assumptions, validation: { ...assumptions.validation, customer_interviews: current + delta } };
  }
  if (fieldPath === "validation.paying_customers") {
    const current = assumptions.validation.paying_customers ?? 0;
    return { ...assumptions, validation: { ...assumptions.validation, paying_customers: current + delta } };
  }
  if (fieldPath === "economics.price_point") {
    // Price is a replacement, not a delta -- a founder learning "$500/mo"
    // is a direct observed value, not an increment to an existing price.
    return { ...assumptions, economics: { ...assumptions.economics, price_point: delta } };
  }
  return assumptions;
}

function fieldPathLabel(fieldPath: ProposedSignal["fieldPath"]): string {
  if (fieldPath === "validation.customer_interviews") return "Customer interviews";
  if (fieldPath === "validation.paying_customers") return "Paying customers";
  if (fieldPath === "economics.price_point") return "Price point";
  return "";
}

function currentFieldValue(assumptions: VentureAssumptions, fieldPath: ProposedSignal["fieldPath"]): number | null {
  if (fieldPath === "validation.customer_interviews") return assumptions.validation.customer_interviews;
  if (fieldPath === "validation.paying_customers") return assumptions.validation.paying_customers;
  if (fieldPath === "economics.price_point") return assumptions.economics.price_point;
  return null;
}

export default function CaptureWhatHappened({
  ventureId,
  currentAssumptions,
  currentModelResult,
  ventureRequestBase,
  onVentureUpdated,
  onHistoryChanged,
}: CaptureWhatHappenedProps) {
  const { getToken } = useAuth();

  const [step, setStep] = useState<Step>("collapsed");
  const [text, setText] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [savedMission, setSavedMission] = useState<VentureMission | null>(null);
  const [signals, setSignals] = useState<ProposedSignal[]>([]);
  const [checkedSignalIds, setCheckedSignalIds] = useState<Set<string>>(new Set());

  const [isUpdatingModel, setIsUpdatingModel] = useState(false);
  const [modelUpdateError, setModelUpdateError] = useState<string | null>(null);
  const [modelChangeResult, setModelChangeResult] = useState<{ beforeVps: number | null; afterVps: number | null } | null>(null);
  const [modelChangeCategories, setModelChangeCategories] = useState<CategoryChange[] | null>(null);

  const previewSignals = text.trim() ? extractCaptureSignals(text) : [];

  function reset() {
    setStep("collapsed");
    setText("");
    setCategory(null);
    setError(null);
    setSavedMission(null);
    setSignals([]);
    setCheckedSignalIds(new Set());
    setModelChangeResult(null);
    setModelChangeCategories(null);
    setModelUpdateError(null);
  }

  async function handleSave() {
    const trimmed = text.trim();
    if (!trimmed) {
      setError("What happened?");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("Your session expired. Sign in again.");
        return;
      }

      const mission = await captureVentureObservation(ventureId, trimmed, category, token);
      const found = extractCaptureSignals(trimmed);

      setSavedMission(mission);
      setSignals(found);
      // Field-mapped signals default to checked (the founder can still
      // uncheck any of them before choosing "Update my model" -- Part 6's
      // confirm/correct/remove requirement); informational-only signals
      // have no checkbox at all, so they're irrelevant to this set.
      setCheckedSignalIds(new Set(found.filter((s) => s.fieldPath).map((s) => s.id)));
      setStep("saved");
      onHistoryChanged?.();
    } catch (err) {
      console.error("Failed to save observation:", err);
      setError("Couldn't save that. Try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleUpdateModel() {
    if (!savedMission) return;

    setIsUpdatingModel(true);
    setModelUpdateError(null);

    try {
      const token = await getToken();
      if (!token) {
        setModelUpdateError("Your session expired. Sign in again.");
        return;
      }

      let nextAssumptions = currentAssumptions;
      for (const signal of signals) {
        if (!signal.fieldPath || !checkedSignalIds.has(signal.id)) continue;
        if (signal.proposedValue === undefined) continue;
        nextAssumptions = applyProposedValue(nextAssumptions, signal.fieldPath, signal.proposedValue);
      }

      const beforeVps = currentModelResult?.vps ?? null;
      const beforeCategories = currentModelResult?.categories ?? [];

      const updated = await updateVenture(
        ventureId,
        {
          ...ventureRequestBase,
          assumptions: nextAssumptions,
          // Founder Progress / Venture History V1, Part 10's own linking
          // mechanism -- the exact same field MissionsSection's
          // handleUpdateModel() already sets, here pointed at the
          // capture's own mission id so the resulting model_updated
          // history event links back to this observation.
          related_mission_id: savedMission.id,
        },
        token
      );

      setModelChangeResult({ beforeVps, afterVps: updated.model_result?.vps ?? null });
      setModelChangeCategories(explainCategoryChanges(beforeCategories, updated.model_result?.categories ?? []));
      onVentureUpdated(updated);
      onHistoryChanged?.();
    } catch (err) {
      console.error("Failed to update model:", err);
      setModelUpdateError("Your model could not be updated. Try again.");
    } finally {
      setIsUpdatingModel(false);
    }
  }

  function toggleSignal(id: string) {
    setCheckedSignalIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (step === "collapsed") {
    return (
      <BaseCard className="p-5">
        <button
          type="button"
          onClick={() => setStep("writing")}
          className="flex w-full items-center justify-between gap-3 text-left"
        >
          <div>
            <h2 className="text-base font-semibold text-text-primary">What happened?</h2>
            <p className="mt-1 text-sm text-text-secondary">
              Capture a customer conversation, sale, experiment, product milestone, investor conversation, or
              anything else you learned while building.
            </p>
          </div>
          <span aria-hidden="true" className="shrink-0 text-2xl font-semibold text-primary">
            +
          </span>
        </button>
      </BaseCard>
    );
  }

  if (step === "writing") {
    const fieldMappedPreview = previewSignals.filter((s) => s.fieldPath);
    return (
      <BaseCard className="p-5">
        <h2 className="text-base font-semibold text-text-primary">What happened?</h2>
        <p className="mt-1 text-xs text-text-muted">
          Write it in your own words. This is saved exactly as you write it -- nothing here changes your Venture
          Potential Score.
        </p>

        <textarea
          id="capture-text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={5}
          placeholder="e.g. Talked to six restaurant owners. Four said inventory waste is a serious problem, but only one would pay $500/month."
          className="mt-3 w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
        />

        <div className="mt-3 flex flex-wrap gap-1.5">
          {CATEGORY_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setCategory((prev) => (prev === option.value ? null : option.value))}
              className={[
                "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                category === option.value
                  ? "border-primary bg-primary-soft text-primary"
                  : "border-border text-text-secondary hover:border-primary/40",
              ].join(" ")}
            >
              {option.label}
            </button>
          ))}
        </div>
        <p className="mt-1 text-[11px] text-text-muted">Category is optional -- just for your own organization.</p>

        {fieldMappedPreview.length > 0 ? (
          <p className="mt-3 text-xs text-text-secondary">
            SIE may find {fieldMappedPreview.length} possible signal{fieldMappedPreview.length === 1 ? "" : "s"} in
            this -- you&rsquo;ll see them after saving, and nothing changes your model unless you choose to update
            it.
          </p>
        ) : null}

        {error ? <p className="mt-2 text-xs text-danger">{error}</p> : null}

        <div className="mt-4 flex items-center gap-2">
          <Button type="button" disabled={isSaving} loading={isSaving} onClick={handleSave}>
            {isSaving ? "Saving..." : "Save to venture history"}
          </Button>
          <Button type="button" variant="subtle" disabled={isSaving} onClick={reset}>
            Cancel
          </Button>
        </div>
      </BaseCard>
    );
  }

  // step === "saved"
  const fieldMappedSignals = signals.filter((s) => s.fieldPath);
  const informationalSignals = signals.filter((s) => !s.fieldPath);
  const hasSelectedFieldSignals = fieldMappedSignals.some((s) => checkedSignalIds.has(s.id));

  return (
    <BaseCard className="border-success/30 bg-success-soft/40 p-5">
      <p className="text-sm font-semibold text-text-primary">Saved to your venture history.</p>

      <div className="mt-3 rounded-lg border border-border bg-surface p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">You recorded</p>
        <p className="mt-1 text-sm leading-6 text-text-primary">&ldquo;{savedMission?.learning_summary}&rdquo;</p>
      </div>

      {signals.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">SIE found these possible signals</p>

          {fieldMappedSignals.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {fieldMappedSignals.map((signal) => {
                const current = currentFieldValue(currentAssumptions, signal.fieldPath);
                const isPrice = signal.fieldPath === "economics.price_point";
                const isDelta = signal.fieldPath !== "economics.price_point"; // interviews/paying_customers propose a +delta, price proposes a replacement
                const proposedTotal = isDelta && signal.proposedValue !== undefined ? (current ?? 0) + signal.proposedValue : signal.proposedValue;
                const formatValue = (value: number | null) =>
                  value === null ? "Unknown" : isPrice ? `$${value.toLocaleString()}/month` : value.toLocaleString();

                return (
                  <li key={signal.id} className="flex items-start gap-2.5 rounded-lg border border-border bg-surface p-3">
                    <input
                      id={`signal-${signal.id}`}
                      type="checkbox"
                      checked={checkedSignalIds.has(signal.id)}
                      onChange={() => toggleSignal(signal.id)}
                      className="mt-0.5 size-4 shrink-0 accent-primary"
                    />
                    <label htmlFor={`signal-${signal.id}`} className="min-w-0 cursor-pointer">
                      <span className="block text-sm font-medium text-text-primary">{signal.label}</span>
                      <span className="mt-0.5 block text-xs text-text-muted">from: &ldquo;{signal.sourceQuote}&rdquo;</span>
                      <span className="mt-1 flex items-baseline gap-1.5 text-xs">
                        <span className="font-medium text-text-secondary">{fieldPathLabel(signal.fieldPath)}:</span>
                        <span className="text-text-muted">{formatValue(current)}</span>
                        <span aria-hidden="true" className="text-text-muted">→</span>
                        <span className="font-semibold text-primary">{formatValue(proposedTotal ?? null)}</span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          ) : null}

          {informationalSignals.length > 0 ? (
            <ul className="mt-2 space-y-1.5">
              {informationalSignals.map((signal) => (
                <li key={signal.id} className="flex items-start gap-2 text-sm text-text-secondary">
                  <span aria-hidden="true" className="mt-1.5 size-1.5 shrink-0 rounded-full bg-text-muted" />
                  <span>
                    {signal.label} <span className="text-xs text-text-muted">(&ldquo;{signal.sourceQuote}&rdquo;)</span>
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : (
        <p className="mt-3 text-xs text-text-muted">
          No structured signals found in this note -- that&rsquo;s fine. It&rsquo;s still saved.
        </p>
      )}

      {modelChangeResult ? (
        <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What changed</p>
          <p className="mt-1.5 flex items-baseline gap-2 text-sm">
            <span className="text-text-secondary">Venture Potential Score</span>
            <span className="font-semibold text-text-primary">
              {modelChangeResult.beforeVps !== null ? modelChangeResult.beforeVps.toFixed(1) : "—"}
            </span>
            <span aria-hidden="true" className="text-text-muted">→</span>
            <span className="font-semibold text-text-primary">
              {modelChangeResult.afterVps !== null ? modelChangeResult.afterVps.toFixed(1) : "—"}
            </span>
          </p>
          {modelChangeResult.beforeVps !== null &&
          modelChangeResult.afterVps !== null &&
          Math.abs(modelChangeResult.afterVps - modelChangeResult.beforeVps) < 0.05 ? (
            <p className="mt-1 text-xs text-text-muted">
              Your model was updated. Venture Potential Score did not materially change.
            </p>
          ) : null}
          {modelChangeCategories && modelChangeCategories.length > 0 ? (
            <div className="mt-3">
              <CategoryChangesList changes={modelChangeCategories} />
            </div>
          ) : null}
        </div>
      ) : hasSelectedFieldSignals ? (
        <div className="mt-4">
          {modelUpdateError ? <p className="mb-2 text-xs text-danger">{modelUpdateError}</p> : null}
          <Button type="button" variant="secondary" size="sm" disabled={isUpdatingModel} loading={isUpdatingModel} onClick={handleUpdateModel}>
            {isUpdatingModel ? "Updating..." : "Update my model with these signals"}
          </Button>
          <p className="mt-1.5 text-xs text-text-muted">
            Only the signals checked above are applied. You can also save this and update your model later, or
            never -- that&rsquo;s a fine choice too.
          </p>
        </div>
      ) : null}

      <div className="mt-4 border-t border-border pt-3">
        <Button type="button" variant="subtle" size="sm" onClick={reset}>
          Record something else
        </Button>
      </div>
    </BaseCard>
  );
}
