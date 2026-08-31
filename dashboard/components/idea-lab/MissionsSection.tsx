"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import Disclosure from "@/components/ui/Disclosure";
import Skeleton from "@/components/ui/Skeleton";

import CategoryChangesList from "./CategoryChangesList";
import { explainCategoryChanges } from "./categoryChangeExplain";
import PlaybookLink from "@/components/playbooks/PlaybookLink";
import { getPlaybookForMission } from "@/lib/playbooks/resourceMap";
import { getPlaybookBySlug } from "@/content/playbooks";

import {
  createVentureMission,
  listVentureMissions,
  recordVentureMissionLearning,
  updateVenture,
  updateVentureMissionStatus,
} from "@/lib/api";

import type {
  MissionType,
  ValidationObservations,
  VentureAssumptions,
  VentureMission,
  VentureResponse,
  VPSResult,
} from "@/types";

// Phase 10.7 -- Founder Missions V1.
//
// THE VALIDATION FIREWALL, restated at the one place it matters most in
// the UI: every call in this file that touches `venture_missions`
// (create/status/learning) uses lib/api/ventureMissions.ts exclusively.
// The ONLY call anywhere below that can change a score is
// handleUpdateModel()'s explicit updateVenture() call -- the exact same
// PUT /ventures/{id} the manual assumption editor and Apply&Save already
// use, gated behind a founder typing/confirming numbers themselves. There
// is no code path from a mission's status or its learning_summary into
// VentureAssumptions.
const WHY_IT_MATTERS: Record<string, string> = {
  validation: "You currently have very little real customer evidence.",
  problem_solution: "A clear point of difference makes your idea easier to explain and defend.",
  founder_readiness: "Investors and cofounders look for relevant experience and complementary skills.",
  gtm_feasibility: "Without a clear way to reach customers, even a great product can struggle to grow.",
  economic_potential: "Understanding your margins early avoids building something that can't sustain itself.",
  market_potential: "Knowing your competitive landscape helps you position realistically.",
};

const CATEGORY_OPTIONS = [
  { value: "", label: "No specific category" },
  { value: "validation", label: "Validation" },
  { value: "problem_solution", label: "Problem & Solution" },
  { value: "founder_readiness", label: "Founder Readiness" },
  { value: "gtm_feasibility", label: "GTM Feasibility" },
  { value: "economic_potential", label: "Economic Potential" },
  { value: "market_potential", label: "Market Potential" },
];

type PendingMission = {
  title: string;
  relatedCategory: string;
  missionType: MissionType;
  // Phase 11 -- Pitch Deck Coach V2, Part 13: optional, additive.
  // Undefined for a NextMoves/vps_guidance suggestion (the original
  // Phase 10.7 shape); populated for a deck-review-originated mission
  // (source defaults to "vps_guidance" below when absent, preserving
  // the exact pre-Phase-11 behavior for every existing caller).
  description?: string | null;
  source?: "vps_guidance" | "pitch_deck_coach";
  resourceRef?: string | null;
};

type MissionsSectionProps = {
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
  pendingMission: PendingMission | null;
  onPendingMissionConsumed: () => void;
  onVentureUpdated: (updated: VentureResponse) => void;
  onMissionTitlesChanged?: (vpsGuidanceTitles: string[]) => void;
};

type LoadState = "loading" | "ready" | "error";

export default function MissionsSection({
  ventureId,
  currentAssumptions,
  currentModelResult,
  ventureRequestBase,
  pendingMission,
  onPendingMissionConsumed,
  onVentureUpdated,
  onMissionTitlesChanged,
}: MissionsSectionProps) {
  const { getToken } = useAuth();

  const [missions, setMissions] = useState<VentureMission[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [actionError, setActionError] = useState<string | null>(null);

  const [expandedMissionId, setExpandedMissionId] = useState<number | null>(null);
  const [reflectingMissionId, setReflectingMissionId] = useState<number | null>(null);
  const [reflectionText, setReflectionText] = useState("");
  const [isSavingReflection, setIsSavingReflection] = useState(false);
  const [reflectionSavedFor, setReflectionSavedFor] = useState<number | null>(null);

  const [showModelUpdateFor, setShowModelUpdateFor] = useState<number | null>(null);
  const [validationDraft, setValidationDraft] = useState<ValidationObservations>(currentAssumptions.validation);
  const [isUpdatingModel, setIsUpdatingModel] = useState(false);
  const [modelChangeResult, setModelChangeResult] = useState<{
    beforeVps: number | null;
    afterVps: number | null;
  } | null>(null);
  const [modelChangeCategories, setModelChangeCategories] = useState<
    ReturnType<typeof explainCategoryChanges>
  >([]);

  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customTitle, setCustomTitle] = useState("");
  const [customCategory, setCustomCategory] = useState("");
  const [isCreatingCustom, setIsCreatingCustom] = useState(false);

  const [isBusy, setIsBusy] = useState(false);

  async function loadMissions() {
    setLoadState("loading");
    try {
      const token = await getToken();
      if (!token) {
        setLoadState("error");
        return;
      }
      const data = await listVentureMissions(ventureId, token);
      setMissions(data);
      setLoadState("ready");
    } catch (error) {
      console.error("Failed to load missions:", error);
      setLoadState("error");
    }
  }

  // Promise.resolve().then() is a genuine microtask boundary, not
  // decoration -- react-hooks/set-state-in-effect flags loadMissions()'s
  // own synchronous setLoadState("loading") call (its first line, before
  // any await) as directly reachable from this effect body. Deferring the
  // call itself to a microtask satisfies the rule the same honest way
  // Phase 10.5's homepage-idea-handoff effect does (see
  // app/idea-lab/new/NewVentureForm.tsx's own comment on this exact
  // pattern) -- loadMissions is also called directly from several event
  // handlers below, where no such boundary is needed or applied.
  useEffect(() => {
    Promise.resolve().then(() => {
      loadMissions();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ventureId]);

  useEffect(() => {
    onMissionTitlesChanged?.(missions.filter((m) => m.source === "vps_guidance").map((m) => m.title));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [missions]);

  // Phase 10.7, Part 5: a NextMoves suggestion becomes a mission only when
  // the founder explicitly chooses "Make this a mission" -- never
  // automatically. This effect just performs the one API call that
  // choice triggers.
  useEffect(() => {
    if (!pendingMission) {
      return;
    }

    let cancelled = false;

    async function createFromSuggestion() {
      setActionError(null);
      try {
        const token = await getToken();
        if (!token) {
          setActionError("Your session expired. Sign in again.");
          return;
        }
        await createVentureMission(
          ventureId,
          {
            title: pendingMission!.title,
            description: pendingMission!.description ?? null,
            mission_type: pendingMission!.missionType,
            related_category: pendingMission!.relatedCategory || null,
            source: pendingMission!.source ?? "vps_guidance",
            resource_ref: pendingMission!.resourceRef ?? null,
          },
          token
        );
        if (!cancelled) {
          await loadMissions();
        }
      } catch (error) {
        console.error("Failed to create mission from suggestion:", error);
        if (!cancelled) {
          setActionError("Couldn't create that mission. Try again.");
        }
      } finally {
        if (!cancelled) {
          onPendingMissionConsumed();
        }
      }
    }

    createFromSuggestion();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingMission]);

  const activeMissions = missions.filter((m) => m.status === "active");
  const completedCount = missions.filter((m) => m.status === "completed").length;
  const primaryMission = activeMissions[0] ?? null;
  const otherActiveMissions = activeMissions.slice(1);

  async function handleStatusChange(missionId: number, status: "completed" | "dismissed") {
    setIsBusy(true);
    setActionError(null);
    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }
      await updateVentureMissionStatus(ventureId, missionId, status, token);
      await loadMissions();
      if (reflectingMissionId === missionId) setReflectingMissionId(null);
      if (expandedMissionId === missionId) setExpandedMissionId(null);
    } catch (error) {
      console.error("Failed to update mission status:", error);
      setActionError("Couldn't update that mission. Try again.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveReflection(missionId: number) {
    const trimmed = reflectionText.trim();
    if (!trimmed) return;

    setIsSavingReflection(true);
    setActionError(null);
    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }
      await recordVentureMissionLearning(ventureId, missionId, trimmed, token);
      await loadMissions();
      setReflectionSavedFor(missionId);
      setReflectionText("");
    } catch (error) {
      console.error("Failed to record reflection:", error);
      setActionError("Couldn't save that reflection. Try again.");
    } finally {
      setIsSavingReflection(false);
    }
  }

  // Part 12: the ONLY function in this file that can change VPS. It calls
  // the pre-existing PUT /ventures/{id} path -- the same one the manual
  // assumption editor and Apply&Save already use -- with the founder's
  // own confirmed validation values merged in. Nothing here reads
  // reflection text; validationDraft only ever changes when the founder
  // types into the NumberFields themselves.
  async function handleUpdateModel() {
    setIsUpdatingModel(true);
    setActionError(null);
    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }

      const beforeVps = currentModelResult?.vps ?? null;
      const beforeCategories = currentModelResult?.categories ?? [];

      const updated = await updateVenture(
        ventureId,
        {
          ...ventureRequestBase,
          assumptions: { ...currentAssumptions, validation: validationDraft },
        },
        token
      );

      setModelChangeResult({ beforeVps, afterVps: updated.model_result?.vps ?? null });
      setModelChangeCategories(explainCategoryChanges(beforeCategories, updated.model_result?.categories ?? []));
      onVentureUpdated(updated);
    } catch (error) {
      console.error("Failed to update model:", error);
      setActionError("Your model could not be updated. Try again.");
    } finally {
      setIsUpdatingModel(false);
    }
  }

  async function handleCreateCustomMission() {
    const trimmed = customTitle.trim();
    if (!trimmed) return;

    setIsCreatingCustom(true);
    setActionError(null);
    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }
      await createVentureMission(
        ventureId,
        { title: trimmed, related_category: customCategory || null, source: "founder_created" },
        token
      );
      await loadMissions();
      setCustomTitle("");
      setCustomCategory("");
      setShowCustomForm(false);
    } catch (error) {
      console.error("Failed to create custom mission:", error);
      setActionError("Couldn't create that mission. Try again.");
    } finally {
      setIsCreatingCustom(false);
    }
  }

  if (loadState === "loading") {
    return <Skeleton className="h-40 w-full" />;
  }

  if (loadState === "error") {
    return (
      <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
        Unable to load your missions. Try refreshing the page.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">Your Missions</h2>
          {/* Phase 10.10, Part 5: makes the Next Moves -> Missions
              relationship explicit in copy, not just in adjacent layout --
              a mission is how a move above actually gets done. */}
          <p className="mt-0.5 text-xs text-text-muted">
            How you actually work through your next moves, one at a time.
          </p>
        </div>
        <p className="text-xs text-text-muted">
          {completedCount} mission{completedCount === 1 ? "" : "s"} completed · {activeMissions.length} active
        </p>
      </div>

      {actionError ? (
        <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
          {actionError}
        </div>
      ) : null}

      {primaryMission ? (
        <BaseCard variant="raised" className="space-y-4 p-6">
          {expandedMissionId !== primaryMission.id ? (
            <>
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Your next mission</p>
              <p className="text-lg font-bold text-text-primary">{primaryMission.title}</p>
              {primaryMission.description ? (
                <p className="text-sm leading-6 text-text-secondary">{primaryMission.description}</p>
              ) : null}
              <Button type="button" onClick={() => setExpandedMissionId(primaryMission.id)}>
                Start Mission
              </Button>
            </>
          ) : (
            <>
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Current mission</p>
              <p className="text-lg font-bold text-text-primary">{primaryMission.title}</p>

              {primaryMission.related_category && WHY_IT_MATTERS[primaryMission.related_category] ? (
                <div>
                  <p className="text-xs font-semibold text-text-muted">Why this matters</p>
                  <p className="mt-1 text-sm text-text-secondary">
                    {WHY_IT_MATTERS[primaryMission.related_category]}
                  </p>
                </div>
              ) : null}

              {/* Phase 10.9 -- Founder Playbooks V1, Part 5A: purely
                  additive -- the mission is fully usable (Start/Complete/
                  Dismiss/Reflect) whether or not a playbook link renders.
                  Phase 11, Part 14: a mission with its own resource_ref
                  (currently only ever set by a "Make this a mission" click
                  from a deck review -- see MakeMissionButton.tsx) already
                  names the exact right playbook; the missionType/
                  relatedCategory-derived lookup is the fallback for every
                  mission that doesn't carry one. */}
              {(() => {
                const playbook = primaryMission.resource_ref
                  ? getPlaybookBySlug(primaryMission.resource_ref)
                  : getPlaybookForMission({
                      missionType: primaryMission.mission_type,
                      relatedCategory: primaryMission.related_category,
                    });
                return playbook ? <PlaybookLink slug={playbook.slug} label={`Learn: ${playbook.title} →`} /> : null;
              })()}

              {primaryMission.learning_summary ? (
                <div className="rounded-lg bg-surface-subtle p-3">
                  <p className="text-xs font-semibold text-text-muted">What you learned</p>
                  <p className="mt-1 text-sm text-text-secondary">{primaryMission.learning_summary}</p>
                </div>
              ) : null}

              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  disabled={isBusy}
                  onClick={() =>
                    setReflectingMissionId(reflectingMissionId === primaryMission.id ? null : primaryMission.id)
                  }
                >
                  Record What I Learned
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={isBusy}
                  onClick={() => handleStatusChange(primaryMission.id, "completed")}
                >
                  Mark Complete
                </Button>
                <Button
                  type="button"
                  variant="subtle"
                  disabled={isBusy}
                  onClick={() => handleStatusChange(primaryMission.id, "dismissed")}
                >
                  Dismiss
                </Button>
              </div>

              {reflectingMissionId === primaryMission.id ? (
                <div className="space-y-3 rounded-xl border border-border p-4">
                  <p className="text-sm font-semibold text-text-primary">What did you learn?</p>
                  <p className="text-xs text-text-muted">
                    &ldquo;What happened when you tried this?&rdquo; A failed experiment is still useful
                    learning.
                  </p>

                  <textarea
                    value={reflectionText}
                    onChange={(event) => setReflectionText(event.target.value)}
                    placeholder='e.g. "I interviewed 10 people and 2 said they would pay." or "Nobody responded."'
                    rows={3}
                    className="w-full resize-y rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-primary focus:ring-2 focus:ring-primary/20"
                  />

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setReflectionText("I learned something useful.")}
                    >
                      I learned something useful
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setReflectionText("No useful signal yet.")}
                    >
                      No useful signal yet
                    </Button>
                  </div>

                  <Button
                    type="button"
                    disabled={isSavingReflection || !reflectionText.trim()}
                    loading={isSavingReflection}
                    onClick={() => handleSaveReflection(primaryMission.id)}
                  >
                    Save Reflection
                  </Button>

                  {reflectionSavedFor === primaryMission.id ? (
                    <div className="rounded-lg bg-info-soft px-3 py-2 text-xs text-info">
                      <p className="font-semibold">That&rsquo;s useful signal.</p>
                      <p className="mt-0.5">
                        Learning what does or doesn&rsquo;t work can save months of building the wrong thing.
                      </p>
                    </div>
                  ) : null}

                  {primaryMission.related_category === "validation" ? (
                    <div className="border-t border-border pt-3">
                      {showModelUpdateFor !== primaryMission.id ? (
                        <Button
                          type="button"
                          variant="subtle"
                          size="sm"
                          onClick={() => {
                            setValidationDraft(currentAssumptions.validation);
                            setModelChangeResult(null);
                            setShowModelUpdateFor(primaryMission.id);
                          }}
                        >
                          Update my model →
                        </Button>
                      ) : (
                        <ValidationUpdateForm
                          draft={validationDraft}
                          onChange={setValidationDraft}
                          onCancel={() => setShowModelUpdateFor(null)}
                          onUpdate={handleUpdateModel}
                          isUpdating={isUpdatingModel}
                          result={modelChangeResult}
                          categoryChanges={modelChangeCategories}
                        />
                      )}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </>
          )}
        </BaseCard>
      ) : (
        <BaseCard variant="subtle" className="p-6 text-center">
          <p className="text-sm font-semibold text-text-primary">No active missions yet.</p>
          <p className="mt-1 text-xs text-text-secondary">
            Turn one of your next moves above into a mission, or add your own below.
          </p>
        </BaseCard>
      )}

      {otherActiveMissions.length > 0 ? (
        <Disclosure summary={`${otherActiveMissions.length} more saved mission${otherActiveMissions.length === 1 ? "" : "s"}`}>
          <ul className="space-y-2">
            {otherActiveMissions.map((mission) => (
              <li key={mission.id} className="flex items-center justify-between gap-3 text-sm">
                <span className="text-text-secondary">{mission.title}</span>
                <Button type="button" variant="subtle" size="sm" onClick={() => setExpandedMissionId(mission.id)}>
                  Focus on this
                </Button>
              </li>
            ))}
          </ul>
        </Disclosure>
      ) : null}

      <Disclosure summary="Create your own mission">
        {!showCustomForm ? (
          <Button type="button" variant="secondary" size="sm" onClick={() => setShowCustomForm(true)}>
            + New mission
          </Button>
        ) : (
          <div className="space-y-3">
            <div>
              <label htmlFor="custom-mission-title" className="mb-1.5 block text-xs font-medium text-text-muted">
                Title
              </label>
              <input
                id="custom-mission-title"
                type="text"
                value={customTitle}
                onChange={(event) => setCustomTitle(event.target.value)}
                placeholder="e.g. Ask my professor for feedback"
                className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <label htmlFor="custom-mission-category" className="mb-1.5 block text-xs font-medium text-text-muted">
                Related category (optional)
              </label>
              <select
                id="custom-mission-category"
                value={customCategory}
                onChange={(event) => setCustomCategory(event.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
              >
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                disabled={isCreatingCustom || !customTitle.trim()}
                loading={isCreatingCustom}
                onClick={handleCreateCustomMission}
              >
                Add Mission
              </Button>
              <Button type="button" variant="subtle" onClick={() => setShowCustomForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}
      </Disclosure>
    </div>
  );
}

function ValidationUpdateForm({
  draft,
  onChange,
  onCancel,
  onUpdate,
  isUpdating,
  result,
  categoryChanges,
}: {
  draft: ValidationObservations;
  onChange: (value: ValidationObservations) => void;
  onCancel: () => void;
  onUpdate: () => void;
  isUpdating: boolean;
  result: { beforeVps: number | null; afterVps: number | null } | null;
  categoryChanges: ReturnType<typeof explainCategoryChanges>;
}) {
  if (result) {
    return (
      <div className="space-y-3">
        <p className="text-sm font-semibold text-text-primary">Your model changed</p>
        <p className="text-sm text-text-secondary">
          Modeled VPS:{" "}
          <span className="font-semibold text-text-primary">
            {result.beforeVps !== null ? result.beforeVps.toFixed(1) : "—"} →{" "}
            {result.afterVps !== null ? result.afterVps.toFixed(1) : "—"}
          </span>
        </p>
        <p className="text-xs text-text-muted">
          Your model changed because you updated your own founder-reported observations — not because you
          completed a mission.
        </p>
        <CategoryChangesList changes={categoryChanges} heading="Why" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-text-secondary">
        Would you like to update your venture model with what you actually observed?
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <NumberInput
          id="validation-interviews"
          label="Customer interviews"
          value={draft.customer_interviews}
          onChange={(value) => onChange({ ...draft, customer_interviews: value })}
        />
        <NumberInput
          id="validation-paying"
          label="Paying customers"
          value={draft.paying_customers}
          onChange={(value) => onChange({ ...draft, paying_customers: value })}
        />
        <NumberInput
          id="validation-waitlist"
          label="Waitlist / preorders"
          value={draft.waitlist_signups}
          onChange={(value) => onChange({ ...draft, waitlist_signups: value })}
        />
        <NumberInput
          id="validation-revenue"
          label="Monthly revenue ($)"
          value={draft.monthly_revenue}
          onChange={(value) => onChange({ ...draft, monthly_revenue: value })}
        />
      </div>

      <div className="flex gap-2">
        <Button type="button" disabled={isUpdating} loading={isUpdating} onClick={onUpdate}>
          Update Model
        </Button>
        <Button type="button" variant="subtle" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function NumberInput({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-xs font-medium text-text-muted">
        {label}
      </label>
      <input
        id={id}
        type="number"
        inputMode="decimal"
        min={0}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}
        placeholder="Unknown"
        className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-primary focus:ring-2 focus:ring-primary/20"
      />
    </div>
  );
}
