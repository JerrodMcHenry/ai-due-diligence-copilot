"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import Breadcrumbs from "@/components/layout/Breadcrumbs";
import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import Disclosure from "@/components/ui/Disclosure";
import VentureUnderstandingPanel from "@/components/idea-lab/VentureUnderstandingPanel";
import ScenarioComparison from "@/components/idea-lab/ScenarioComparison";
import VentureJourney, { manualStepIndex } from "@/components/idea-lab/VentureJourney";
import VentureOverview from "@/components/idea-lab/VentureOverview";
import ShareVentureSnapshot from "@/components/idea-lab/ShareVentureSnapshot";
import WhatIfPanel from "@/components/idea-lab/WhatIfPanel";
import MissionsSection from "@/components/idea-lab/MissionsSection";
import CaptureWhatHappened from "@/components/idea-lab/CaptureWhatHappened";
import VentureProgress from "@/components/idea-lab/VentureProgress";
import WeeklyReview from "@/components/idea-lab/WeeklyReview";
import Tabs, { TabPanel } from "@/components/ui/Tabs";
import FundraisingSimulator from "@/components/fundraising/FundraisingSimulator";
import ConceptDisclosure from "@/components/learn/ConceptDisclosure";
import PitchDeckCoachTeaser from "@/components/founder/PitchDeckCoachTeaser";
import NextMoves from "@/components/idea-lab/NextMoves";
import PrimaryCommandCard from "@/components/idea-lab/PrimaryCommandCard";
import CurrentQuestionCard from "@/components/idea-lab/CurrentQuestionCard";
import {
  useVentureGraduation,
  VentureGraduationAction,
  VentureGraduationBanner,
} from "@/components/idea-lab/VentureGraduation";
import { stillFiguringOutFromCategories } from "@/components/idea-lab/ventureOverviewHelpers";
import { suggestionForMilestone } from "@/components/idea-lab/missionSuggestions";
import {
  NumberField,
  SelectField,
  TextField,
  ToggleField,
} from "@/components/idea-lab/AssumptionFields";
import { resolveIdeaLabNextStep } from "@/lib/journey/resolveIdeaLabNextStep";
import { resolveVentureState } from "@/lib/journey/inferVentureStage";
import { stashVentureDescriptionForAnalyze } from "@/lib/ventureToStartupHandoff";
import { consumePitchDeckMission } from "@/lib/pitchDeckMissionHandoff";

import {
  compareVentureScenarios,
  deleteVenture,
  getVenture,
  getVentureHistory,
  updateVenture,
} from "@/lib/api";
import { emptyAssumptions, VENTURE_STAGES } from "@/types";

import type {
  MissionType,
  ScenarioCompareResponse,
  VentureAssumptions,
  VentureHistoryResponse,
  VentureResponse,
} from "@/types";

type LoadState = "loading" | "ready" | "error" | "not-found";

type VentureWorkspaceProps = {
  ventureId: number;
};

function assumptionsEqual(a: VentureAssumptions, b: VentureAssumptions): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

// Phase 13 -- Founder Home / Venture Command Center, Part 5/7. Mirrors
// app/idea-lab/IdeaLabDashboard.tsx's own formatUpdatedAt() exactly (same
// format string) for consistency between the venture list and this page
// -- not extracted to a shared util, since it's one small, single-purpose
// helper used in exactly two places, matching this file's own existing
// "small local helper" convention (see openDisclosureAndScrollIntoView
// below).
function formatUpdatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// Phase 33 -- Idea Workspace Information Architecture & Founder Operating
// Loop, Part 2. The five local-navigation destinations, and the ONLY
// place their ids/labels/order are defined -- both the <Tabs> control and
// the query-param guard below read from this single source. Adding a
// sixth destination without demonstrated necessity is explicitly
// forbidden by the approved architecture; if that ever needs revisiting,
// it happens here and nowhere else.
type TabId = "overview" | "model" | "what-if" | "fundraising" | "history";

const LOCAL_NAV_TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "model", label: "Model" },
  { id: "what-if", label: "What-If" },
  { id: "fundraising", label: "Fundraising" },
  { id: "history", label: "History" },
];

// Mirrors CompareView.tsx's own parseStartupIds() discipline: an
// unrecognized or missing `?tab=` value is never an error state -- it
// silently, gracefully resolves to Overview, the mandated default for
// every fresh navigation (including a bare `/idea-lab/[id]` with no query
// string at all).
function isTabId(value: string | null): value is TabId {
  return LOCAL_NAV_TABS.some((candidate) => candidate.id === value);
}

// Phase 33, Part 9. "Where things stand" is now concise STATUS only --
// current state (the same VentureJourney pill+sentence this page has
// always used for that) and the venture's biggest unknown(s), derived
// from the exact same stillFiguringOutFromCategories() helper
// VentureOverview's own "What we still need to figure out" list already
// uses. What used to live here (current action, most recent learning,
// latest model update) each now has a single, better home: current
// action is PrimaryCommandCard's own Case B; recent learning and model-
// update history live in the History tab's existing WeeklyReview /
// VentureProgress components. Nothing here is new data -- it's the same
// two facts, reused, with everything else removed per the directive's
// explicit list of what this card must NOT repeat.
function WhereThingsStand({
  stage,
  assumptions,
  stillFiguringOut,
}: {
  stage: string | null;
  assumptions: VentureAssumptions;
  stillFiguringOut: string[];
}) {
  return (
    <BaseCard variant="raised" className="p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Where things stand</p>

      <div className="mt-2">
        <VentureJourney stage={stage} assumptions={assumptions} />
      </div>

      {stillFiguringOut.length > 0 ? (
        <div className="mt-4 border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Biggest unknown{stillFiguringOut.length > 1 ? "s" : ""}
          </p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {stillFiguringOut.map((item) => (
              <li key={item} className="rounded-full bg-warning-soft px-3 py-1 text-sm font-semibold text-warning">
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </BaseCard>
  );
}

export default function VentureWorkspace({ ventureId }: VentureWorkspaceProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { getToken } = useAuth();

  // Phase 33, Part 1/2/3. The local nav's ONLY state is the URL itself --
  // no sessionStorage/localStorage persistence (explicitly forbidden: a
  // fresh navigation must always land on Overview), survives a refresh
  // (it's just the query string), and both browser back/forward and a
  // deep link (e.g. a saved `?tab=model` bookmark) work for free, because
  // `tab` is derived fresh from useSearchParams() on every render rather
  // than mirrored into local component state. setTab uses router.push
  // (not replace) specifically so switching tabs adds a history entry --
  // the directive requires back/forward to move between tabs.
  const rawTab = searchParams.get("tab");
  const tab: TabId = isTabId(rawTab) ? rawTab : "overview";

  function setTab(next: TabId) {
    const destination = next === "overview" ? pathname : `${pathname}?tab=${next}`;
    router.push(destination, { scroll: false });
  }

  const [venture, setVenture] = useState<VentureResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  const [name, setName] = useState("");
  const [description, setDescription] = useState<string | null>(null);
  const [industry, setIndustry] = useState<string | null>(null);
  const [businessModel, setBusinessModel] = useState<string | null>(null);
  const [targetCustomer, setTargetCustomer] = useState<string | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  const [draft, setDraft] = useState<VentureAssumptions>(emptyAssumptions());

  const [scenario, setScenario] = useState<ScenarioCompareResponse | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Phase 10.7 -- Founder Missions V1. `pendingMission` is the ONLY
  // channel between NextMoves and MissionsSection: NextMoves reports
  // which milestone text the founder chose ("Make this a mission"),
  // MissionsSection performs the one API call that creates it, then
  // clears this back to null. `missionedMilestones` is the reverse
  // direction -- which vps_guidance-sourced mission titles already exist,
  // so NextMoves can show "Added ✓" instead of offering a duplicate.
  //
  // Phase 11 -- Pitch Deck Coach V2, Part 13: `description`, `source`,
  // and `resourceRef` are additive, optional fields on the SAME
  // pendingMission channel -- a deck-review-originated mission carries
  // its own description/provenance/playbook slug, where a NextMoves
  // suggestion leaves them undefined (MissionsSection defaults
  // source to "vps_guidance" and resource_ref to null when absent, see
  // its own pendingMission-consumption effect).
  const [pendingMission, setPendingMission] = useState<
    {
      title: string;
      relatedCategory: string;
      missionType: MissionType;
      description?: string | null;
      source?: "vps_guidance" | "pitch_deck_coach";
      resourceRef?: string | null;
    } | null
  >(null);
  const [missionedMilestones, setMissionedMilestones] = useState<string[]>([]);
  // Phase 26 -- Retention Loop Closure, Part 9/11, superseded this phase.
  // `primaryMissionTitle` is fed by MissionsSection's own
  // onPrimaryMissionChanged callback (same lift-a-derived-value pattern
  // as missionedMilestones above) and is now the single source of truth
  // PrimaryCommandCard uses to decide Case A vs. Case B -- see that
  // component's own docstring for why it's deliberately never re-derived
  // from resolveIdeaLabNextStep() itself.
  const [primaryMissionTitle, setPrimaryMissionTitle] = useState<string | null>(null);

  // Phase 26, Part 13/15. A minimal, isolated rename affordance -- reuses
  // the SAME PUT /ventures/{id} pathway every other save on this page
  // already uses, but always sends venture.assumptions/description/
  // industry/business_model/target_customer/stage exactly as last saved
  // (never the possibly-edited `draft`/`industry`/`businessModel`/`stage`
  // component state), so a rename can never accidentally persist an
  // unrelated unsaved edit sitting in "Edit the full model." Because only
  // `name` differs from `venture`'s own last-saved snapshot, the backend's
  // existing assumptions-only diff (app/api.py::update_venture) writes no
  // venture_model_updates row and computes the identical VPS -- the
  // firewall Part 15 requires, satisfied by the existing endpoint's own
  // logic, not new code.
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [isSavingRename, setIsSavingRename] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);

  // Phase 33, Part 16. Share moved from a bottom-of-page disclosure to a
  // restrained header-level action -- same ShareVentureSnapshot component,
  // same behavior, only the toggle affordance and its position changed.
  const [isShareOpen, setIsShareOpen] = useState(false);

  // Founder Progress / Venture History V1. One dedicated GET, loaded once
  // alongside the venture itself and refreshed only after an action that
  // could actually change it (a mission-list change, or a saved model
  // update) -- never on every render, never N+1 (Section 17).
  const [history, setHistory] = useState<VentureHistoryResponse | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  // Phase 29B Closure, Part 2. See MissionsSection's own
  // missionsRefreshSignal comment for the full root cause: a capture
  // saved via CaptureWhatHappened creates a completed-status mission row
  // MissionsSection has no trigger to know about, so its own "N actions
  // completed" count went stale relative to VentureProgress's (sourced
  // from history). Bumped from the exact same onHistoryChanged callback
  // CaptureWhatHappened already calls after every save below -- no new
  // fetch, no new endpoint, just reusing the existing "something in
  // history-relevant state changed" signal to also tell MissionsSection
  // to reload.
  const [missionsRefreshSignal, setMissionsRefreshSignal] = useState(0);

  // Phase 33, Part 13 (implementation detail). Case A's "Edit your model"
  // action needs to land on the now-unmounted-until-selected Model tab's
  // "Edit the full model" disclosure -- a plain onClick can't do both
  // "switch tabs" and "open+scroll to a not-yet-rendered element" in one
  // synchronous step. This flag sequences the two: setTab("model") first,
  // then an effect (once the Model TabPanel has actually mounted) performs
  // the same openDisclosureAndScrollIntoView() this page has always used
  // for that exact purpose.
  const [pendingModelFocus, setPendingModelFocus] = useState(false);

  const refreshHistory = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    try {
      const data = await getVentureHistory(ventureId, token);
      setHistory(data);
    } catch (error) {
      console.error("Failed to load venture history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [ventureId, getToken]);

  // Phase 11, Part 13: a deck-review "Make this a mission" click stashes
  // one fix (lib/pitchDeckMissionHandoff.ts) and navigates here -- this
  // consumes it ONCE, the same read-and-clear contract every other
  // same-tab handoff in this codebase already uses (see
  // lib/ventureToStartupHandoff.ts). Deliberately still routes through
  // the SAME pendingMission state MissionsSection already renders a
  // confirmation step for -- nothing is created without the founder
  // seeing it first.
  useEffect(() => {
    // Deferred to a microtask -- same "avoid synchronous setState inside
    // an effect body" discipline MissionsSection.tsx's own loadMissions()
    // effect already applies (see that file's matching comment).
    Promise.resolve().then(() => {
      const handoff = consumePitchDeckMission();
      if (handoff) {
        setPendingMission({
          title: handoff.title,
          description: handoff.description,
          relatedCategory: handoff.relatedCategory ?? "other",
          missionType: handoff.missionType,
          source: "pitch_deck_coach",
          resourceRef: handoff.resourceRef,
        });
      }
    });
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadVenture() {
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

        const data = await getVenture(ventureId, token);

        if (isMounted) {
          setVenture(data);
          setName(data.name);
          setDescription(data.description);
          setIndustry(data.industry);
          setBusinessModel(data.business_model);
          setTargetCustomer(data.target_customer);
          setStage(data.stage);
          setDraft(data.assumptions);
          setLoadState("ready");
          refreshHistory();
        }
      } catch (error) {
        console.error("Failed to load venture:", error);

        if (isMounted) {
          setLoadState(
            error instanceof Error && /\(404\)/.test(error.message) ? "not-found" : "error"
          );
        }
      }
    }

    loadVenture();

    return () => {
      isMounted = false;
    };
  }, [ventureId, getToken, refreshHistory]);

  // Phase 33, Part 13 (implementation detail, continued). Runs only once
  // both conditions are true -- the Model tab is actually active (so its
  // TabPanel, and therefore the disclosure inside it, exists in the DOM)
  // and a focus is still pending. requestAnimationFrame gives React one
  // paint to mount the panel before the DOM lookup runs.
  useEffect(() => {
    if (tab !== "model" || !pendingModelFocus) {
      return;
    }

    const frame = requestAnimationFrame(() => {
      openDisclosureAndScrollIntoView("edit-the-full-model");
      setPendingModelFocus(false);
    });

    return () => cancelAnimationFrame(frame);
  }, [tab, pendingModelFocus]);

  function goToEditModel() {
    setPendingModelFocus(true);
    setTab("model");
  }

  // Phase 33, Part 9 (Section 8's "Log what happened" affordance). Capture
  // stays on Overview -- this never switches tabs, it only scrolls an
  // already-mounted section into view, exactly the same
  // scrollIntoView-based mechanism openDisclosureAndScrollIntoView already
  // uses elsewhere on this page.
  function scrollToCapture() {
    document.getElementById("capture-what-happened")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function buildRequestBody(assumptions: VentureAssumptions) {
    return { name: name.trim() || "Untitled venture", description, industry, business_model: businessModel, target_customer: targetCustomer, stage, assumptions };
  }

  async function handlePreview() {
    if (!venture) return;

    setIsPreviewing(true);
    setActionError(null);

    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }

      const result = await compareVentureScenarios(venture.assumptions, draft, token);
      setScenario(result);
    } catch (error) {
      console.error("Failed to preview scenario:", error);
      setActionError("Couldn't calculate that scenario. Try again.");
    } finally {
      setIsPreviewing(false);
    }
  }

  // Phase 10.6, Part 7: a "What if?" preset runs through this SAME
  // preview mechanism -- it only supplies a different `modifiedAssumptions`
  // value (whatIfScenarios.ts's own patch of the saved venture, not the
  // manually-edited `draft`). `draft` is updated to match so that if the
  // founder chooses "Apply & Save" afterward, the existing handleSave()
  // (unchanged) persists exactly the scenario they just previewed --
  // there is no separate apply path for a What If result.
  async function handleRunScenario(modifiedAssumptions: VentureAssumptions) {
    if (!venture) return;

    setIsPreviewing(true);
    setActionError(null);
    setDraft(modifiedAssumptions);

    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }

      const result = await compareVentureScenarios(venture.assumptions, modifiedAssumptions, token);
      setScenario(result);
    } catch (error) {
      console.error("Failed to run what-if scenario:", error);
      setActionError("Couldn't calculate that scenario. Try again.");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function handleSave() {
    setIsSaving(true);
    setActionError(null);

    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }

      const updated = await updateVenture(ventureId, buildRequestBody(draft), token);
      setVenture(updated);
      setDraft(updated.assumptions);
      setScenario(null);
      refreshHistory();
    } catch (error) {
      console.error("Failed to save venture:", error);
      setActionError("Your changes could not be saved. Try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    setActionError(null);

    try {
      const token = await getToken();
      if (!token) {
        setActionError("Your session expired. Sign in again.");
        return;
      }

      await deleteVenture(ventureId, token);
      router.push("/idea-lab");
    } catch (error) {
      console.error("Failed to delete venture:", error);
      setActionError("This venture could not be deleted. Try again.");
      setIsDeleting(false);
    }
  }

  async function handleRenameVenture() {
    if (!venture) return;
    const trimmed = renameValue.trim();
    if (!trimmed) {
      setRenameError("Give it a name, or Cancel.");
      return;
    }

    setIsSavingRename(true);
    setRenameError(null);

    try {
      const token = await getToken();
      if (!token) {
        setRenameError("Your session expired. Sign in again.");
        return;
      }

      // Deliberately built from `venture`'s own last-saved fields, NOT
      // from `draft`/`industry`/`businessModel`/`stage` component state
      // -- see this state's own comment above for why that isolation is
      // the actual safety guarantee here.
      const updated = await updateVenture(
        ventureId,
        {
          name: trimmed,
          description: venture.description,
          industry: venture.industry,
          business_model: venture.business_model,
          target_customer: venture.target_customer,
          stage: venture.stage,
          assumptions: venture.assumptions,
        },
        token
      );

      setVenture(updated);
      setName(updated.name);
      setIsRenaming(false);
    } catch (error) {
      console.error("Failed to rename venture:", error);
      setRenameError("Couldn't rename that. Try again.");
    } finally {
      setIsSavingRename(false);
    }
  }

  // Phase 31 -- Venture -> Startup Graduation V1. Called unconditionally
  // (React hook rules -- this sits above every early return below), one
  // fetch for the whole page (Section 17's "no N+1" discipline) rather
  // than one per placement. `venture?.assumptions` falls back to
  // emptyAssumptions() while still loading -- harmless, since
  // isEligibleForGraduationSuggestion() on all-null validation fields is
  // simply `false`, and the real assumptions replace it the instant
  // loadVenture() resolves.
  const graduation = useVentureGraduation(ventureId, {
    name: venture?.name ?? "",
    description,
    industry,
    business_model: businessModel,
    target_customer: targetCustomer,
    stage,
    assumptions: venture?.assumptions ?? emptyAssumptions(),
  });

  if (loadState === "loading") {
    return (
      <div className="space-y-6">
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />
      </div>
    );
  }

  if (loadState === "not-found") {
    return (
      <BaseCard className="p-10 text-center">
        <h1 className="text-xl font-bold text-text-primary">Idea not found</h1>
        <p className="mt-3 text-text-secondary">
          This idea doesn&rsquo;t exist, or doesn&rsquo;t belong to you.
        </p>
        <Link href="/idea-lab" className="mt-6 inline-flex text-sm font-semibold text-primary hover:text-primary-hover">
          Back to My Ideas →
        </Link>
      </BaseCard>
    );
  }

  if (loadState === "error" || !venture) {
    return (
      <div className="rounded-xl border border-danger/20 bg-danger-soft p-6">
        <h2 className="font-semibold text-danger">Unable to load this venture</h2>
        <p className="mt-2 text-sm text-danger/80">Try refreshing the page.</p>
      </div>
    );
  }

  const hasUnsavedChanges = !assumptionsEqual(draft, venture.assumptions);

  // Phase 31C-A -- Global Founder UX Acceptance, Part 3: the SAME
  // resolver PrimaryCommandCard (below) already calls internally, reused
  // here only to find out WHICH milestone (if any) it's about to show as
  // the one dominant recommendation -- so NextMoves can skip that exact
  // entry instead of repeating it. No new recommendation logic.
  const primaryNextStep = venture.model_result ? resolveIdeaLabNextStep(venture.model_result) : null;
  const primaryMilestoneText = primaryNextStep?.kind === "work_on_milestone" ? primaryNextStep.milestoneText : undefined;

  // Phase 33, Part 6 (header). A short, restrained textual echo of
  // current state -- reuses the exact same manualStepIndex() +
  // resolveVentureState() pair VentureJourney itself calls, so the header
  // never disagrees with the fuller state description on Overview's own
  // Where Things Stand card.
  //
  // Phase 34A, Part 2: no VPS segment here anymore -- Idea Lab no longer
  // presents a numeric score anywhere, including this compact readout.
  const ventureState = resolveVentureState(manualStepIndex(stage), venture.assumptions);
  const compactStatusParts = [ventureState.label];
  const updatedLabel = formatUpdatedAt(venture.updated_at);
  if (updatedLabel) {
    compactStatusParts.push(`Updated ${updatedLabel}`);
  }
  const compactStatus = compactStatusParts.join(" · ");

  return (
    <>
      {/* Phase 32, Part 7: the directive's own worked example verbatim
          ("Build / My Ideas / ClaimPilot") -- this page sits two levels
          below the primary nav's own "Build" destination, deep enough
          that the nav's active-state highlighting alone doesn't answer
          "where am I?" the moment a founder has more than one idea. */}
      <Breadcrumbs
        items={[
          { label: "Build", href: "/idea-lab" },
          { label: "My Ideas", href: "/idea-lab" },
          { label: venture.name },
        ]}
      />
      <PageHeader
        title={venture.name}
        subtitle={description?.trim() || "Idea"}
        action={
          <div className="flex items-center gap-2">
            <Button type="button" variant="subtle" onClick={() => setIsShareOpen((open) => !open)}>
              {isShareOpen ? "Hide share" : "Share"}
            </Button>
            <Button
              type="button"
              variant="subtle"
              onClick={() => {
                setRenameValue(venture.name);
                setRenameError(null);
                setIsRenaming(true);
              }}
            >
              Rename
            </Button>
            <Button
              type="button"
              variant="subtle"
              disabled={isDeleting}
              onClick={handleDelete}
              className="hover:text-danger"
            >
              {isDeleting ? "Deleting..." : "Delete venture"}
            </Button>
          </div>
        }
      />

      {/* Phase 33, Part 6, updated by Phase 34A: the compact state/updated
          readout, sitting just under the page title -- one plain line, not
          a card, no score of any kind. Visible regardless of which
          local-nav tab is active, since it's page-level identity, not
          Overview-specific content. */}
      <p className="-mt-4 mb-8 text-sm text-text-secondary">{compactStatus}</p>

      {/* Phase 26, Part 13/15: identity metadata only -- renaming never
          touches assumptions, never touches VPS, never writes model-
          change history, never creates an action, never touches SPS.
          See handleRenameVenture()'s own comment for exactly how that's
          guaranteed. */}
      {isRenaming ? (
        <BaseCard className="-mt-4 mb-8 p-4">
          <label htmlFor="venture-rename" className="block text-xs font-semibold uppercase tracking-wide text-text-muted">
            Venture name
          </label>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <input
              id="venture-rename"
              type="text"
              value={renameValue}
              onChange={(event) => setRenameValue(event.target.value)}
              maxLength={200}
              className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            />
            <Button type="button" size="sm" disabled={isSavingRename} loading={isSavingRename} onClick={handleRenameVenture}>
              {isSavingRename ? "Saving..." : "Save name"}
            </Button>
            <Button type="button" variant="subtle" size="sm" disabled={isSavingRename} onClick={() => setIsRenaming(false)}>
              Cancel
            </Button>
          </div>
          {renameError ? <p className="mt-2 text-xs text-danger">{renameError}</p> : null}
        </BaseCard>
      ) : null}

      {/* Phase 33, Part 16: the Share panel a header click reveals --
          same ShareVentureSnapshot component and behavior Phase 27 built,
          only its entry point moved. Sits above the local nav since
          sharing isn't specific to any one of the five tabs. */}
      {isShareOpen ? (
        <BaseCard className="-mt-4 mb-8 p-5">
          {venture.model_result ? (
            <ShareVentureSnapshot ventureId={ventureId} />
          ) : (
            <p className="text-sm text-text-secondary">Model a few assumptions before sharing your venture.</p>
          )}
        </BaseCard>
      ) : null}

      {/* Phase 33, Part 2/14: the local nav itself -- five destinations,
          always all five, query-param driven. Wrapped in overflow-x-auto
          per the 390px requirement (horizontal scroll, never a "More"
          menu, never hiding Fundraising/History). */}
      <div className="overflow-x-auto pb-2">
        <Tabs tabs={LOCAL_NAV_TABS} activeId={tab} onChange={(id) => setTab(id as TabId)} />
      </div>

      <div className="mt-6">
        {actionError ? (
          <div className="mb-6 rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {actionError}
          </div>
        ) : null}

        <TabPanel id="overview" activeId={tab}>
          <div className="space-y-8">
            <WhereThingsStand
              stage={stage}
              assumptions={venture.assumptions}
              stillFiguringOut={venture.model_result ? stillFiguringOutFromCategories(venture.model_result.categories) : []}
            />

            {/* Phase 31 -- Venture -> Startup Graduation V1, Part 10: a
                persistent, honest "operating startup" banner once
                graduated -- never buried, never hidden behind a
                secondary tab. Renders nothing until graduated. */}
            <VentureGraduationBanner state={graduation} />

            {/* Phase 33, Part 7 (CRITICAL): the single dynamically-
                state-driven primary command card -- Case A ("What should
                I do next?") when no active action exists, Case B ("Your
                current focus") when one does. Never both; see this
                component's own docstring for the exact mechanism that
                guarantees that. */}
            {venture.model_result ? (
              <PrimaryCommandCard
                modelResult={venture.model_result}
                primaryMissionTitle={primaryMissionTitle}
                missionedMilestones={missionedMilestones}
                onStartMission={(milestoneText, suggestion) =>
                  setPendingMission({
                    title: milestoneText,
                    relatedCategory: suggestion.relatedCategory,
                    missionType: suggestion.missionType,
                  })
                }
                onAnalyzeStartup={() => {
                  if (description) {
                    stashVentureDescriptionForAnalyze(description);
                  }
                  router.push("/analyze");
                }}
                onEditModel={goToEditModel}
                onLogWhatHappened={scrollToCapture}
              />
            ) : null}

            {/* Phase 31C -- Founder Experience Simplification, Part 4:
                "what happens afterward" -- the one thing the workspace
                never actually said out loud. Pure copy, no new
                mechanism -- describes exactly what Capture/Missions/the
                model-update path already do. */}
            {venture.model_result ? (
              <p className="text-center text-base leading-7 text-text-secondary">
                Do this → record what happened → SIE updates its understanding → you get your next guidance.
              </p>
            ) : null}

            {/* Phase 23 -- Universal Founder Capture V1, moved this
                phase from mid-page to directly reachable from the
                primary command card's own "Log what happened" action
                (Section 8) -- same component, same firewall, same
                onVentureUpdated/refreshHistory wiring, just given an id
                so scrollToCapture() above has something to scroll to. */}
            <div id="capture-what-happened">
              <CaptureWhatHappened
                ventureId={ventureId}
                currentAssumptions={venture.assumptions}
                currentModelResult={venture.model_result}
                ventureRequestBase={{
                  name: name.trim() || "Untitled venture",
                  description,
                  industry,
                  business_model: businessModel,
                  target_customer: targetCustomer,
                  stage,
                }}
                onVentureUpdated={(updated) => {
                  setVenture(updated);
                  setDraft(updated.assumptions);
                  setScenario(null);
                  refreshHistory();
                }}
                onHistoryChanged={() => {
                  refreshHistory();
                  // Phase 29B Closure, Part 2 -- see missionsRefreshSignal's
                  // own comment above. Fires for both a new capture
                  // (handleSave) and a model update tied to one
                  // (handleUpdateModel) -- either way, MissionsSection's
                  // own missions list may now be stale.
                  setMissionsRefreshSignal((n) => n + 1);
                }}
                onStartMission={(title, suggestion) =>
                  setPendingMission({
                    title,
                    relatedCategory: suggestion.relatedCategory,
                    missionType: suggestion.missionType,
                  })
                }
                // Phase 33 live acceptance test, Part 7/8 fix: this used
                // to always re-derive the raw resolveIdeaLabNextStep()
                // recommendation directly, independent of whether the
                // founder had already started a DIFFERENT milestone as a
                // real action. That surfaced as a live, observed
                // contradiction -- PrimaryCommandCard's own "YOUR CURRENT
                // FOCUS" naming one milestone while this panel's "Your
                // current focus:" line named a different, stale one right
                // next to it. Using the exact same primaryMissionTitle ??
                // primaryMilestoneText value NextMoves' dedup already uses
                // makes every "current focus" statement on the page agree,
                // by construction, with the one PrimaryCommandCard shows.
                currentPriorityText={primaryMissionTitle ?? primaryMilestoneText ?? null}
              />
            </div>

            {/* Phase 33, Part 8: "Your Active Work" -- the founder's own
                action-management surface (start/complete/dismiss/reflect
                on real venture_missions rows). Unchanged component and
                data; only the framing heading is new, making explicit
                that this is where active work is TRACKED, not a second
                place claiming to tell the founder what to do next -- that
                claim belongs to PrimaryCommandCard alone. */}
            <div className="space-y-3">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Your active work</h2>
              <div id="your-missions">
                <MissionsSection
                  ventureId={ventureId}
                  currentAssumptions={venture.assumptions}
                  currentModelResult={venture.model_result}
                  missionsRefreshSignal={missionsRefreshSignal}
                  ventureRequestBase={{
                    name: name.trim() || "Untitled venture",
                    description,
                    industry,
                    business_model: businessModel,
                    target_customer: targetCustomer,
                    stage,
                  }}
                  pendingMission={pendingMission}
                  onPendingMissionConsumed={() => setPendingMission(null)}
                  onMissionTitlesChanged={(titles) => {
                    setMissionedMilestones(titles);
                    // Founder Progress / Venture History V1: fires after
                    // every mission-list mutation (create, status change,
                    // learning recorded) -- MissionsSection's own
                    // loadMissions() already reloads for exactly those
                    // cases, so this reuses that same signal rather than
                    // adding new props/wiring.
                    refreshHistory();
                  }}
                  onPrimaryMissionChanged={setPrimaryMissionTitle}
                  onVentureUpdated={(updated) => {
                    setVenture(updated);
                    setDraft(updated.assumptions);
                    setScenario(null);
                    refreshHistory();
                  }}
                />
              </div>
            </div>

            {venture.model_result ? (
              <NextMoves
                milestones={venture.model_result.next_milestones}
                skipMilestoneText={primaryMissionTitle ?? primaryMilestoneText}
                missionedMilestones={missionedMilestones}
                onMakeMission={(milestoneText) => {
                  const suggestion = suggestionForMilestone(milestoneText);
                  setPendingMission({
                    title: milestoneText,
                    relatedCategory: suggestion.relatedCategory,
                    missionType: suggestion.missionType,
                  });
                }}
              />
            ) : null}

            {/* Phase 31 -- Venture -> Startup Graduation V1, Part 3/10:
                ONE contextual placement -- prominent when the existing
                eligibility check says real evidence has been reported,
                a quiet manual link otherwise. Renders nothing once
                already graduated (VentureGraduationBanner above covers
                that state). */}
            <VentureGraduationAction state={graduation} prominent={graduation.eligible} />

            {/* Phase 34D -- SIE Build Intelligence Loop V1. Deliberately
                additive and self-contained -- proves the
                question -> test -> result -> evidence -> interpretation ->
                recommendation -> decision -> outcome loop end to end
                without touching anything else on this tab. Does not
                replace PrimaryCommandCard, NextMoves, or Your Active
                Work above -- see this phase's own explicit "do not
                redesign Idea Lab" instruction. */}
            <CurrentQuestionCard ventureId={ventureId} ventureName={venture.name} />
          </div>
        </TabPanel>

        {/* Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and
            Decision Support, Part 4. Required flow, in order: WHAT SIE
            BELIEVES + WHAT'S UNKNOWN (VentureOverview -- both already live
            inside that one component), the six-category understanding
            breakdown (VentureUnderstandingPanel -- what we know / believe
            / don't know yet per category, no score), then EDIT ASSUMPTIONS
            (the full editor below). VPSResultPanel is no longer rendered
            here -- see this phase's final report for what was retained
            internally and why. A prominent "Edit venture model" action
            sits at the very top of this tab (Section 4's own explicit
            requirement) so the editor is never buried below a long read;
            it reuses the exact same open-and-scroll helper the old
            "Edit your model" Case A action already used, just fired
            without needing a tab switch first since we're already here. */}
        <TabPanel id="model" activeId={tab}>
          <div className="space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-text-primary">Your venture model</h2>
              <Button
                type="button"
                variant="secondary"
                onClick={() => openDisclosureAndScrollIntoView("edit-the-full-model")}
              >
                Edit venture model
              </Button>
            </div>

            <VentureOverview
              idea={description}
              whoItsFor={targetCustomer}
              howItMakesMoney={businessModel}
              stillFiguringOut={
                venture.model_result ? stillFiguringOutFromCategories(venture.model_result.categories) : []
              }
            />

            {venture.model_result ? <VentureUnderstandingPanel result={venture.model_result} /> : null}

            <Disclosure id="edit-the-full-model" summary="Edit the full model" defaultOpen={false}>
              <section>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-xl font-semibold text-text-primary">What you believe</h2>

                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={isPreviewing || !hasUnsavedChanges}
                      onClick={handlePreview}
                    >
                      {isPreviewing ? "Calculating..." : "Recalculate (preview)"}
                    </Button>

                    <Button
                      type="button"
                      disabled={isSaving || !hasUnsavedChanges}
                      loading={isSaving}
                      onClick={handleSave}
                    >
                      {isSaving ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                </div>

                <p className="mt-1 text-sm text-text-secondary">
                  Everything below except &ldquo;What you&rsquo;ve learned&rdquo; is a modeled assumption, not
                  observed evidence.
                </p>

                <div className="mt-4 space-y-3">
                  <VentureBasicsAccordion
                    targetCustomer={targetCustomer}
                    // Build V3, Part 3 investigation finding:
                    // `target_customer` is stored BOTH as its own
                    // top-level column AND inside `assumptions`
                    // (compute_vps() reads `assumptions.target_customer`
                    // directly -- see vps_scoring.py's own
                    // `_score_problem_solution`). Editing only the
                    // top-level piece here silently dropped a founder's
                    // edit from the actual scored/saved model -- both
                    // must update together.
                    onTargetCustomer={(value) => {
                      setTargetCustomer(value);
                      setDraft((prev) => ({ ...prev, target_customer: value }));
                    }}
                    industry={industry}
                    onIndustry={setIndustry}
                    businessModel={businessModel}
                    onBusinessModel={setBusinessModel}
                    stage={stage}
                    onStage={setStage}
                  />

                  <AssumptionAccordion title="Market">
                    <SelectField
                      id="market-size"
                      label="Estimated market size"
                      value={draft.market.estimated_market_size}
                      options={["Small", "Medium", "Large", "Very Large"]}
                      onChange={(value) => setDraft((prev) => ({ ...prev, market: { ...prev.market, estimated_market_size: value } }))}
                    />
                    <SelectField
                      id="market-competition"
                      label="Competition intensity"
                      value={draft.market.competition_intensity}
                      options={["Low", "Medium", "High"]}
                      onChange={(value) => setDraft((prev) => ({ ...prev, market: { ...prev.market, competition_intensity: value } }))}
                    />
                    <TextField
                      id="market-description"
                      label="Market description"
                      value={draft.market.market_description}
                      onChange={(value) => setDraft((prev) => ({ ...prev, market: { ...prev.market, market_description: value } }))}
                      multiline
                    />
                  </AssumptionAccordion>

                  <AssumptionAccordion title="Problem & Solution">
                    <TextField
                      id="problem-statement"
                      label="Problem statement"
                      value={draft.problem_solution.problem_statement}
                      onChange={(value) => setDraft((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, problem_statement: value } }))}
                      multiline
                    />
                    <TextField
                      id="solution-description"
                      label="Solution description"
                      value={draft.problem_solution.solution_description}
                      onChange={(value) => setDraft((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, solution_description: value } }))}
                      multiline
                    />
                    <TextField
                      id="differentiation"
                      label="Differentiation"
                      value={draft.problem_solution.differentiation}
                      onChange={(value) => setDraft((prev) => ({ ...prev, problem_solution: { ...prev.problem_solution, differentiation: value } }))}
                      multiline
                    />
                  </AssumptionAccordion>

                  <AssumptionAccordion title="Founder / Team">
                    <NumberField
                      id="founder-count"
                      label="Founder count"
                      value={draft.founder.founder_count}
                      onChange={(value) => setDraft((prev) => ({ ...prev, founder: { ...prev.founder, founder_count: value } }))}
                    />
                    <NumberField
                      id="founder-experience"
                      label="Relevant domain experience (years)"
                      value={draft.founder.relevant_domain_experience_years}
                      step={0.5}
                      onChange={(value) => setDraft((prev) => ({ ...prev, founder: { ...prev.founder, relevant_domain_experience_years: value } }))}
                    />
                    <ToggleField
                      id="founder-technical"
                      label="Technical cofounder?"
                      value={draft.founder.has_technical_cofounder}
                      onChange={(value) => setDraft((prev) => ({ ...prev, founder: { ...prev.founder, has_technical_cofounder: value } }))}
                    />
                    <ToggleField
                      id="founder-business"
                      label="Business cofounder?"
                      value={draft.founder.has_business_cofounder}
                      onChange={(value) => setDraft((prev) => ({ ...prev, founder: { ...prev.founder, has_business_cofounder: value } }))}
                    />
                  </AssumptionAccordion>

                  <AssumptionAccordion title="Go-to-Market">
                    <TextField
                      id="gtm-strategy"
                      label="Primary acquisition strategy"
                      value={draft.gtm.primary_acquisition_strategy}
                      onChange={(value) => setDraft((prev) => ({ ...prev, gtm: { ...prev.gtm, primary_acquisition_strategy: value } }))}
                      multiline
                    />
                    <div>
                      <NumberField
                        id="gtm-cac"
                        label="Expected CAC ($)"
                        value={draft.gtm.expected_cac}
                        onChange={(value) => setDraft((prev) => ({ ...prev, gtm: { ...prev.gtm, expected_cac: value } }))}
                      />
                      <ConceptDisclosure conceptKey="cac" value={draft.gtm.expected_cac} />
                    </div>
                  </AssumptionAccordion>

                  <AssumptionAccordion title="Economics">
                    <TextField
                      id="econ-pricing"
                      label="Pricing model"
                      value={draft.economics.pricing_model}
                      onChange={(value) => setDraft((prev) => ({ ...prev, economics: { ...prev.economics, pricing_model: value } }))}
                    />
                    <NumberField
                      id="econ-price"
                      label="Price point ($)"
                      value={draft.economics.price_point}
                      onChange={(value) => setDraft((prev) => ({ ...prev, economics: { ...prev.economics, price_point: value } }))}
                    />
                    <div>
                      <NumberField
                        id="econ-margin"
                        label="Expected gross margin (%)"
                        value={draft.economics.expected_gross_margin_pct}
                        onChange={(value) => setDraft((prev) => ({ ...prev, economics: { ...prev.economics, expected_gross_margin_pct: value } }))}
                      />
                      <ConceptDisclosure conceptKey="gross_margin" value={draft.economics.expected_gross_margin_pct} />
                    </div>
                  </AssumptionAccordion>

                  <AssumptionAccordion title="What you've learned (founder-reported observations)">
                    <NumberField
                      id="val-interviews"
                      label="Customer interviews conducted"
                      value={draft.validation.customer_interviews}
                      onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, customer_interviews: value } }))}
                    />
                    <NumberField
                      id="val-waitlist"
                      label="Waitlist signups"
                      value={draft.validation.waitlist_signups}
                      onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, waitlist_signups: value } }))}
                    />
                    <NumberField
                      id="val-paying"
                      label="Paying customers"
                      value={draft.validation.paying_customers}
                      onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, paying_customers: value } }))}
                    />
                    <NumberField
                      id="val-revenue"
                      label="Monthly revenue ($)"
                      value={draft.validation.monthly_revenue}
                      onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, monthly_revenue: value } }))}
                    />
                    <NumberField
                      id="val-prior-revenue"
                      label="Monthly revenue ~12 months ago ($)"
                      value={draft.validation.prior_monthly_revenue}
                      onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, prior_monthly_revenue: value } }))}
                    />
                    <div>
                      <NumberField
                        id="val-retention"
                        label="Retention (%)"
                        value={draft.validation.retention_pct}
                        onChange={(value) => setDraft((prev) => ({ ...prev, validation: { ...prev.validation, retention_pct: value } }))}
                      />
                      <ConceptDisclosure conceptKey="retention" value={draft.validation.retention_pct} />
                    </div>
                  </AssumptionAccordion>

                  <AssumptionAccordion title="Capital">
                    <NumberField
                      id="capital-starting"
                      label="Starting capital ($)"
                      value={draft.capital.starting_capital}
                      onChange={(value) => setDraft((prev) => ({ ...prev, capital: { ...prev.capital, starting_capital: value } }))}
                    />
                    <div>
                      <NumberField
                        id="capital-burn"
                        label="Monthly burn ($)"
                        value={draft.capital.monthly_burn}
                        onChange={(value) => setDraft((prev) => ({ ...prev, capital: { ...prev.capital, monthly_burn: value } }))}
                      />
                      <ConceptDisclosure conceptKey="burn" value={draft.capital.monthly_burn} />
                    </div>
                  </AssumptionAccordion>
                </div>
              </section>
            </Disclosure>
          </div>
        </TabPanel>

        {/* Phase 33, Part 12 (What-If). Reuses the exact same What If /
            ScenarioComparison flow that used to live inside Explore's own
            internal [ Venture ] [ Fundraising ] sub-tabs -- now a
            top-level destination in its own right, with no math change.
            "Discard" on ScenarioComparison is the existing, obvious path
            back to baseline (clears the preview; nothing was ever
            applied). */}
        <TabPanel id="what-if" activeId={tab}>
          <div className="space-y-3">
            <WhatIfPanel
              currentAssumptions={venture.assumptions}
              onRunScenario={handleRunScenario}
              isRunning={isPreviewing}
            />

            {scenario ? (
              <ScenarioComparison
                scenario={scenario}
                currentAssumptions={venture.assumptions}
                scenarioAssumptions={draft}
                onApply={handleSave}
                onDiscard={() => setScenario(null)}
                isApplying={isSaving}
              />
            ) : null}
          </div>
        </TabPanel>

        {/* Phase 33, Part 13 (Fundraising). Reuses the complete,
            unmodified FundraisingSimulator tree -- no math change.
            PitchDeckCoachTeaser sits above it as the contextual doorway
            the directive asks for (pitch quality matters most exactly
            when a founder is thinking about raising). */}
        <TabPanel id="fundraising" activeId={tab}>
          <div className="space-y-3">
            {venture.model_result ? <PitchDeckCoachTeaser /> : null}
            {/* Phase 21B live walkthrough finding: `name` here is the
                VENTURE's own title state (e.g. "ApexGrid"), not a
                founder's personal name -- this app has no founder-name
                field anywhere. Nothing honest to pass, so the default
                ("You") is used. */}
            <FundraisingSimulator founderName="" />
          </div>
        </TabPanel>

        {/* Phase 33, Part 14 (History). WeeklyReview ("This Week") and
            VentureProgress ("Overall Progress" plus its own built-in
            "Venture history" full-timeline disclosure) stacked together
            -- both components, and the venture-history timeline that
            already lived inside VentureProgress, are entirely unchanged.
            Read-only: no Capture, no active-work management here. */}
        <TabPanel id="history" activeId={tab}>
          <div className="space-y-6">
            <WeeklyReview
              history={history}
              isLoadingHistory={isLoadingHistory}
              modelResult={venture.model_result}
              missionedMilestones={missionedMilestones}
              onStartMission={(milestoneText, suggestion) =>
                setPendingMission({
                  title: milestoneText,
                  relatedCategory: suggestion.relatedCategory,
                  missionType: suggestion.missionType,
                })
              }
            />

            <VentureProgress history={history} isLoading={isLoadingHistory} />
          </div>
        </TabPanel>
      </div>
    </>
  );
}

// Phase 10.11, Part 2: fixes the one friction point Phase 10.10's own
// report flagged -- clicking "Edit your model" scrolled to the "Edit the
// full model" <details>, but a native <details> doesn't auto-expand on
// anchor navigation, leaving it collapsed right where the founder was
// just sent. A small local DOM helper, not a global state system: opens
// the element and scrolls to it in one click, then moves focus onto its
// own <summary> so a keyboard user lands somewhere meaningful (not
// yanked away with no context) and screen readers announce the now-
// expanded region.
function openDisclosureAndScrollIntoView(id: string) {
  const element = document.getElementById(id);

  if (!(element instanceof HTMLDetailsElement)) {
    return;
  }

  element.open = true;
  element.scrollIntoView({ behavior: "smooth", block: "start" });

  const summary = element.querySelector("summary");
  if (summary instanceof HTMLElement) {
    summary.focus();
  }
}

function AssumptionAccordion({
  title,
  defaultOpen,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  return (
    <details open={defaultOpen} className="group rounded-2xl border border-border bg-surface open:pb-2">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-base font-semibold text-text-primary marker:content-none">
        {title}
        <span aria-hidden="true" className="text-text-muted transition-transform group-open:rotate-180">▾</span>
      </summary>
      <div className="grid gap-4 px-5 pb-4 sm:grid-cols-2">{children}</div>
    </details>
  );
}

function VentureBasicsAccordion({
  targetCustomer,
  onTargetCustomer,
  industry,
  onIndustry,
  businessModel,
  onBusinessModel,
  stage,
  onStage,
}: {
  targetCustomer: string | null;
  onTargetCustomer: (value: string | null) => void;
  industry: string | null;
  onIndustry: (value: string | null) => void;
  businessModel: string | null;
  onBusinessModel: (value: string | null) => void;
  stage: string | null;
  onStage: (value: string | null) => void;
}) {
  return (
    <AssumptionAccordion title="Venture Basics">
      <TextField id="basics-customer" label="Target customer" value={targetCustomer} onChange={onTargetCustomer} />
      <TextField id="basics-industry" label="Industry" value={industry} onChange={onIndustry} />
      <TextField id="basics-model" label="Business model" value={businessModel} onChange={onBusinessModel} />
      <SelectField id="basics-stage" label="Current status" value={stage} options={[...VENTURE_STAGES]} onChange={onStage} />
    </AssumptionAccordion>
  );
}
