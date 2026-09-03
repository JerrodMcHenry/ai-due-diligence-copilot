"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import CategoryChangesList from "./CategoryChangesList";
import { explainCategoryChanges, type CategoryChange } from "./categoryChangeExplain";
import { extractCaptureSignals, type ProposedSignal } from "@/lib/captureSignals";
import { captureVentureObservation, updateVenture } from "@/lib/api";

import type { MissionType, VentureAssumptions, VentureMission, VentureResponse, VPSResult } from "@/types";

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
  // Phase 26 -- Retention Loop Closure, Part 3/6 (Class B, ACTION-RELEVANT
  // outcomes). The EXACT SAME setPendingMission() channel IdeaLabNextStep,
  // NextMoves, and WeeklyReview already call -- this is not a second
  // action-creation pathway, just a fourth caller of the one that already
  // exists. Optional: a caller that doesn't wire this simply never sees
  // the "Make this an action" affordance (no crash, no silent failure).
  onStartMission?: (title: string, suggestion: { relatedCategory: string; missionType: MissionType }) => void;
  // Phase 26, Part 7: the founder's current top priority, exactly as
  // resolveIdeaLabNextStep() already resolves it for IdeaLabNextStep
  // directly above this component -- passed down as plain text so a
  // saved capture can always show "your current focus" without the
  // founder scrolling back up. No second resolver, no new logic.
  currentPriorityText?: string | null;
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
    // Phase 26, Part 5: delta can now be negative (a countable churn
    // signal) as well as positive (a new customer) -- same mechanic
    // either direction. Never let a real founder count go below zero.
    const current = assumptions.validation.paying_customers ?? 0;
    return { ...assumptions, validation: { ...assumptions.validation, paying_customers: Math.max(0, current + delta) } };
  }
  if (fieldPath === "validation.retention_pct") {
    // Retention is a replacement, not a delta -- an observed rate, same
    // reasoning as price_point below.
    return { ...assumptions, validation: { ...assumptions.validation, retention_pct: delta } };
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
  if (fieldPath === "validation.retention_pct") return "Retention";
  if (fieldPath === "economics.price_point") return "Price point";
  return "";
}

function currentFieldValue(assumptions: VentureAssumptions, fieldPath: ProposedSignal["fieldPath"]): number | null {
  if (fieldPath === "validation.customer_interviews") return assumptions.validation.customer_interviews;
  if (fieldPath === "validation.paying_customers") return assumptions.validation.paying_customers;
  if (fieldPath === "validation.retention_pct") return assumptions.validation.retention_pct;
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
  onStartMission,
  currentPriorityText,
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
  // Phase 29B, Part 6 -- a real, live-reproduced bug: the signal preview
  // below (line ~417) read `currentAssumptions` live, so once
  // handleUpdateModel() succeeded and the parent's assumptions prop
  // advanced (e.g. interviews 18 -> 21), this same card kept re-rendering
  // the SAME fixed delta against the NEW baseline (showing "21 -> 24"),
  // right next to "What changed," which correctly showed the update had
  // ALREADY happened -- a founder had no way to tell whether "21 -> 24"
  // was a still-pending offer or stale leftover math. Frozen once, at the
  // moment signals are computed, so the preview always reflects what was
  // true when the founder was actually deciding whether to apply it --
  // handleUpdateModel() itself is untouched and still reads live
  // currentAssumptions at click time, so correctness of the actual PUT
  // is unaffected.
  const [baselineAssumptions, setBaselineAssumptions] = useState<VentureAssumptions | null>(null);

  const [isUpdatingModel, setIsUpdatingModel] = useState(false);
  const [modelUpdateError, setModelUpdateError] = useState<string | null>(null);
  const [modelChangeResult, setModelChangeResult] = useState<{ beforeVps: number | null; afterVps: number | null } | null>(null);
  const [modelChangeCategories, setModelChangeCategories] = useState<CategoryChange[] | null>(null);

  // Phase 26, Part 3/6 (Class B, ACTION-RELEVANT). Local-only: which
  // action-relevant informational signal(s) the founder has already
  // turned into an action THIS capture, so the button becomes a
  // confirmation rather than staying clickable indefinitely. Captures
  // produce dynamic, one-off titles, not the fixed vps_guidance
  // milestone strings missionedMilestones tracks -- so this can't reuse
  // that array and needs its own small local set instead.
  const [actionsRequested, setActionsRequested] = useState<Set<string>>(new Set());

  const previewSignals = text.trim() ? extractCaptureSignals(text) : [];

  function reset() {
    setStep("collapsed");
    setText("");
    setCategory(null);
    setError(null);
    setSavedMission(null);
    setSignals([]);
    setBaselineAssumptions(null);
    setCheckedSignalIds(new Set());
    setModelChangeResult(null);
    setModelChangeCategories(null);
    setModelUpdateError(null);
    setActionsRequested(new Set());
  }

  function handleMakeAction(signal: ProposedSignal) {
    if (!onStartMission || !signal.suggestedActionTitle) return;
    // Phase 26, Part 5: churn/complaint-style observations map to
    // "customer_discovery" (investigating why a customer left or is
    // frustrated is itself a discovery task); an experiment result maps
    // to "product". Both are real, existing MissionType values already
    // used elsewhere in this codebase (missionSuggestions.ts) -- no new
    // category invented here.
    const missionType: MissionType = signal.label.includes("Experiment") ? "product" : "customer_discovery";
    const relatedCategory = signal.label.includes("Experiment") ? "problem_solution" : "validation";
    onStartMission(signal.suggestedActionTitle, { relatedCategory, missionType });
    setActionsRequested((prev) => new Set(prev).add(signal.id));
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
      setBaselineAssumptions(currentAssumptions);
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
        <p className="mt-1 text-xs text-text-muted">Category is optional -- just for your own organization.</p>

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
  //
  // Phase 26 -- Retention Loop Closure, Part 3/4/6. Every successfully
  // saved capture ends in an honest outcome class, restated in one plain
  // "WHAT THIS MEANS" line so the founder always knows what SIE did with
  // the information -- never silence, never invented confidence:
  //   A. MODEL-RELEVANT   -- >=1 field-mapped signal exists (unchanged
  //      from Phase 23's own "Update my model" pathway).
  //   B. ACTION-RELEVANT  -- no field-mapped signal, but >=1 informational
  //      signal is marked actionRelevant (captureSignals.ts's own
  //      classification -- see that module's docstring). This is the
  //      Phase 25 dead-end's fix: "Customer cancelled..." now ends here,
  //      not in silence.
  //   C. LEARNING-ONLY     -- zero signals, or only non-actionable
  //      informational signals (a shipped milestone, a mentioned
  //      competitor, etc.). Still a fully valid, honest outcome.
  // These are outcome CLASSES, not mutually exclusive UI states -- a
  // note can legitimately carry both a field-mapped AND an
  // action-relevant informational signal (Part 3's own "one or more"),
  // in which case both CTAs render, still capped at two (Part 6: "avoid
  // CTA explosion").
  const fieldMappedSignals = signals.filter((s) => s.fieldPath);
  const informationalSignals = signals.filter((s) => !s.fieldPath);
  const actionRelevantSignals = informationalSignals.filter((s) => s.actionRelevant);
  const hasSelectedFieldSignals = fieldMappedSignals.some((s) => checkedSignalIds.has(s.id));
  const pendingActionSignals = actionRelevantSignals.filter((s) => !actionsRequested.has(s.id));

  const whatThisMeans = modelChangeResult
    ? null // superseded by the explicit "What changed" block below once applied
    : fieldMappedSignals.length > 0
      ? "We found information that could update your venture model."
      : actionRelevantSignals.length > 0
        ? "This doesn't change your model yet, but it may be worth investigating."
        : "Saved. There isn't enough here to change your model yet.";

  return (
    <BaseCard className="border-success/30 bg-success-soft/40 p-5">
      <p className="text-sm font-semibold text-text-primary">Saved to your venture history.</p>

      <div className="mt-3 rounded-lg border border-border bg-surface p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">You recorded</p>
        <p className="mt-1 text-sm leading-6 text-text-primary">&ldquo;{savedMission?.learning_summary}&rdquo;</p>
      </div>

      {signals.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">SIE found these possible signals</p>

          {fieldMappedSignals.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {fieldMappedSignals.map((signal) => {
                const current = currentFieldValue(baselineAssumptions ?? currentAssumptions, signal.fieldPath);
                const isPrice = signal.fieldPath === "economics.price_point";
                const isPercent = signal.fieldPath === "validation.retention_pct";
                // interviews/paying_customers propose a +/-delta; price and
                // retention propose a direct replacement (an observed
                // value, not an increment).
                const isDelta = signal.fieldPath === "validation.customer_interviews" || signal.fieldPath === "validation.paying_customers";
                const proposedTotal =
                  isDelta && signal.proposedValue !== undefined
                    ? Math.max(0, (current ?? 0) + signal.proposedValue) // never display a negative count -- mirrors applyProposedValue()'s own clamp
                    : signal.proposedValue;
                const formatValue = (value: number | null) =>
                  value === null ? "Unknown" : isPrice ? `$${value.toLocaleString()}/month` : isPercent ? `${value}%` : value.toLocaleString();

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
      ) : null}

      {/* Phase 26, Part 4/6: one honest, restrained "what this means"
          line -- never overstated confidence, never silence. This is the
          single sentence that replaces Phase 23's old "no structured
          signals found" text for the zero-signal case, and is now shown
          for every outcome class, not just that one. */}
      {whatThisMeans ? <p className="mt-3 text-sm text-text-secondary">{whatThisMeans}</p> : null}

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

      {/* Phase 26, Part 3/6 (Class B, ACTION-RELEVANT). Reuses the exact
          same setPendingMission()/founder-confirmed action-creation
          pathway every other "Make this an action" affordance in this
          codebase already uses -- never a capture-specific task system.
          Rendered independently of the model-update CTA above (both can
          appear together, still capped at two -- Part 6's own "avoid CTA
          explosion" instruction). */}
      {onStartMission && pendingActionSignals.length > 0 ? (
        <div className="mt-4">
          {pendingActionSignals.map((signal) => (
            <div key={signal.id} className={pendingActionSignals.indexOf(signal) > 0 ? "mt-2" : undefined}>
              <Button type="button" variant="secondary" size="sm" onClick={() => handleMakeAction(signal)}>
                Make this an action: {signal.suggestedActionTitle}
              </Button>
            </div>
          ))}
        </div>
      ) : null}
      {actionsRequested.size > 0 ? (
        <p className="mt-2 text-xs text-success">Added to your actions ✓</p>
      ) : null}

      {/* Phase 26, Part 7: the founder's orientation is never lost after
          a capture -- shown regardless of outcome class, and unchanged
          unless the founder explicitly updated the model above (in which
          case IdeaLabNextStep above this component already reflects
          whatever the resolver now says; this line simply keeps that
          fact visible without the founder scrolling back up). */}
      {currentPriorityText ? (
        <p className="mt-4 text-xs text-text-muted">
          <span className="font-medium text-text-secondary">Your current focus:</span> {currentPriorityText}
        </p>
      ) : null}

      <div className="mt-4 border-t border-border pt-3">
        <Button type="button" variant="subtle" size="sm" onClick={reset}>
          Record something else
        </Button>
      </div>
    </BaseCard>
  );
}
