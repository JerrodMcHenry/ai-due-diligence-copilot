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
import VentureJourney, { manualStepIndex } from "@/components/idea-lab/VentureJourney";
import ShareVentureSnapshot from "@/components/idea-lab/ShareVentureSnapshot";
import MissionsSection from "@/components/idea-lab/MissionsSection";
import CaptureWhatHappened from "@/components/idea-lab/CaptureWhatHappened";
import VentureProgress from "@/components/idea-lab/VentureProgress";
import WeeklyReview from "@/components/idea-lab/WeeklyReview";
import Tabs, { TabPanel } from "@/components/ui/Tabs";
import FundraisingSimulator from "@/components/fundraising/FundraisingSimulator";
import ConceptDisclosure from "@/components/learn/ConceptDisclosure";
import PitchDeckCoachTeaser from "@/components/founder/PitchDeckCoachTeaser";
import NextMoves from "@/components/idea-lab/NextMoves";
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

import { deleteVenture, getVenture, getVentureHistory, updateVenture } from "@/lib/api";
import { emptyAssumptions, VENTURE_STAGES } from "@/types";

import type {
  CompanyIntelligenceSummary,
  MissionType,
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

// Phase 34E -- Founder Experience Simplification V1. Three local-
// navigation destinations, down from five -- Model and What-If are
// removed as primary destinations (see this phase's own final report and
// docs/product/SIE_BUILD_FOUNDER_EXPERIENCE_V1.md for the full audit and
// reasoning). This remains the ONLY place the destinations are defined --
// both the <Tabs> control and the query-param guard below read from this
// single source.
//
// "Validate" (this phase's own initial hypothesis for a fourth
// destination) was deliberately NOT added: everything it would have
// held -- the current question, the recommended test, recording a
// result -- is now Overview's own hero (CurrentQuestionCard), and a
// separate tab repeating that would be exactly the visual duplication
// Section 23 forbids, not a genuinely different founder job.
type TabId = "overview" | "fundraising" | "history";

const LOCAL_NAV_TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
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

// Phase 34E -- Founder Experience Simplification V1, Section 9's
// "VENTURE IDENTITY" step: what is this, who's it for, how might it make
// money, current stage, and the venture's biggest unknown(s) -- ONE card,
// where Phase 33 had this split across two (this page's own
// "Where things stand" card here on Overview, and a near-identical "Your
// idea / Who it's for / How it might make money / What we still need to
// figure out" card -- VentureOverview.tsx -- on the now-removed Model
// tab). Same two underlying facts (VentureJourney's stage state,
// stillFiguringOutFromCategories()'s unknowns list) as before, rendered
// exactly once each -- Section 23's own "if two sections answer the same
// founder question, merge or remove one." "Your idea" itself is NOT
// repeated here -- PageHeader's subtitle, immediately above this card,
// already shows the venture's own description.
function VentureIdentity({
  stage,
  assumptions,
  whoItsFor,
  howItMakesMoney,
  stillFiguringOut,
  onEditDetails,
}: {
  stage: string | null;
  assumptions: VentureAssumptions;
  whoItsFor: string | null;
  howItMakesMoney: string | null;
  stillFiguringOut: string[];
  onEditDetails: () => void;
}) {
  return (
    <BaseCard className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <VentureJourney stage={stage} assumptions={assumptions} />
        {/* Phase 34F, Section 4: outcome-driven, not a profile-maintenance
            chore -- matches the CTA wording on the section this opens. */}
        <Button type="button" variant="subtle" size="sm" onClick={onEditDetails}>
          Add venture context →
        </Button>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Who it&rsquo;s for</p>
          <p className="mt-1 text-base leading-6 text-text-primary">
            {whoItsFor?.trim() || <span className="text-text-muted">Not described yet.</span>}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">How it might make money</p>
          <p className="mt-1 text-base leading-6 text-text-primary">
            {howItMakesMoney?.trim() || <span className="text-text-muted">Not described yet.</span>}
          </p>
        </div>
      </div>

      {stillFiguringOut.length > 0 ? (
        <div className="mt-5 border-t border-border pt-4">
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

// Phase 34E, Section 12, superseded by Phase 34G -- SIE Intelligence
// Advantage V1, §10-13: "what SIE currently understands" is now driven
// by accumulated EVIDENCE (venture_evidence, missions, decisions --
// exactly the state actually driving CurrentQuestionCard's own
// recommendation) rather than VPS category `basis` sentences, which
// answer a different question (what's been MODELED, not what's been
// OBSERVED). The old VPS-category view is not gone -- it is still fully
// intact and one click away via "See the full breakdown by category"
// -- it is just no longer the DEFAULT content, since Section 10's own
// instruction is that this section "should summarize the state that is
// actually driving SIE's recommendation."
//
// Three state-dependent sub-sections (WHAT SIE KNOWS / STILL FIGURING
// OUT / WHAT CHANGED RECENTLY), each rendered only when non-empty --
// §18's own explicit "do not overwhelm a brand-new venture with empty
// intelligence sections" applies per-section, not just to the whole
// card. A single "See full history →" link replaces Phase 34E's own
// separate "Most recent: ..." one-liner (Section 23's anti-duplication
// rule: once "what changed" says something specific and evidence-
// grounded, repeating a second, vaguer "most recent" line right below
// it would be exactly the kind of duplication that rule forbids).
function CompanyIntelligenceState({
  modelResult,
  companyIntelligence,
  hasHistory,
  onSeeHistory,
}: {
  modelResult: NonNullable<VentureResponse["model_result"]> | null;
  companyIntelligence: CompanyIntelligenceSummary | null;
  hasHistory: boolean;
  onSeeHistory: () => void;
}) {
  const knows = companyIntelligence?.what_sie_knows ?? [];
  const stillFiguringOut = companyIntelligence?.still_figuring_out ?? [];
  const whatChanged = companyIntelligence?.what_changed ?? [];
  const hasAnyIntelligence = knows.length > 0 || stillFiguringOut.length > 0 || whatChanged.length > 0;

  // Nothing to show yet at all (brand-new venture, no evidence, no
  // model) -- Overview's hero above already covers this state.
  if (!hasAnyIntelligence && !modelResult) {
    return null;
  }

  return (
    <BaseCard className="space-y-5 p-6">
      {knows.length > 0 ? (
        <div>
          <h2 className="text-lg font-semibold text-text-primary">What SIE knows</h2>
          <ul className="mt-2 space-y-1.5">
            {knows.map((fact) => (
              <li key={fact} className="flex gap-2 text-base leading-7 text-text-secondary">
                <span aria-hidden="true" className="text-text-muted">•</span>
                {fact}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {stillFiguringOut.length > 0 ? (
        <div className={knows.length > 0 ? "border-t border-border pt-4" : undefined}>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Still figuring out</p>
          <ul className="mt-2 space-y-1.5">
            {stillFiguringOut.map((item) => (
              <li key={item} className="flex gap-2 text-base leading-7 text-text-secondary">
                <span aria-hidden="true" className="text-text-muted">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {whatChanged.length > 0 ? (
        <div className={knows.length > 0 || stillFiguringOut.length > 0 ? "border-t border-border pt-4" : undefined}>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What changed recently</p>
          <ul className="mt-2 space-y-1.5">
            {whatChanged.map((item) => (
              <li key={item} className="flex gap-2 text-base leading-7 text-text-secondary">
                <span aria-hidden="true" className="text-text-muted">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!hasAnyIntelligence ? (
        <p className="text-base leading-7 text-text-secondary">
          Nothing has been tested yet -- once you record a result, SIE will start building a real
          understanding of your venture here.
        </p>
      ) : null}

      {hasHistory ? (
        <button type="button" onClick={onSeeHistory} className="text-sm font-semibold text-primary hover:text-primary-hover">
          See full history →
        </button>
      ) : null}

      {modelResult ? (
        <Disclosure summary="See the full breakdown by category" defaultOpen={false}>
          <div className="pt-2">
            <VentureUnderstandingPanel result={modelResult} />
          </div>
        </Disclosure>
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

  // Phase 34G -- SIE Intelligence Advantage V1. Lifted from
  // CurrentQuestionCard's own already-fetched recommendation response
  // (see that component's own onCompanyIntelligence prop) so
  // CompanyIntelligenceState below can render it without a second fetch.
  const [companyIntelligence, setCompanyIntelligence] = useState<CompanyIntelligenceSummary | null>(null);

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

  // Phase 34E -- Founder Experience Simplification V1: editing venture
  // details is now a contextual disclosure directly on Overview (Section
  // 6), not a separate Model tab -- so this no longer needs to switch
  // tabs before it can scroll/expand the disclosure; both happen in the
  // same synchronous click, since the disclosure is already mounted.
  function goToEditDetails() {
    openDisclosureAndScrollIntoView("edit-the-full-model");
  }

  function buildRequestBody(assumptions: VentureAssumptions) {
    return { name: name.trim() || "Untitled venture", description, industry, business_model: businessModel, target_customer: targetCustomer, stage, assumptions };
  }

  // Phase 34E: the separate "Recalculate (preview)" / What-If-only
  // preview step is gone along with the What-If tab it rendered into
  // (Section 8) -- editing venture details now just saves directly, one
  // fewer step for a job that was never actually a "what if," just a
  // correction.
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

  // Phase 34E: the deterministic vps_guidance milestone resolver, still
  // used for two narrow, still-legitimate jobs -- (1) recognizing
  // "ready_for_real_startup" for the small Analyze bridge card below
  // (Section 9's "specialized tools/secondary actions"), and (2) letting
  // NextMoves skip whichever milestone is already this venture's single
  // active question, so its "other things to consider" list never repeats
  // the SIE loop's own current question. It's no longer used to render a
  // primary "what should I do next" card -- that job belongs to
  // CurrentQuestionCard alone now (see Section 23's own anti-duplication
  // rule, and this phase's final report for the removed PrimaryCommandCard).
  const primaryNextStep = venture.model_result ? resolveIdeaLabNextStep(venture.model_result) : null;
  const primaryMilestoneText = primaryNextStep?.kind === "work_on_milestone" ? primaryNextStep.milestoneText : undefined;
  const readyToAnalyze = primaryNextStep?.kind === "ready_for_real_startup";

  // Phase 33, Part 6 (header). A short, restrained textual echo of
  // current state -- reuses the exact same manualStepIndex() +
  // resolveVentureState() pair VentureJourney itself calls, so the header
  // never disagrees with the fuller state description on the Venture
  // Identity card below.
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

      {/* Phase 34E -- Founder Experience Simplification V1: three
          destinations, wrapped in overflow-x-auto per the 390px
          requirement (horizontal scroll, never a "More" menu, never
          hiding Fundraising/History). */}
      <div className="overflow-x-auto pb-2">
        <Tabs tabs={LOCAL_NAV_TABS} activeId={tab} onChange={(id) => setTab(id as TabId)} />
      </div>

      <div className="mt-6">
        {actionError ? (
          <div className="mb-6 rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {actionError}
          </div>
        ) : null}

        {/* Phase 34E -- Founder Experience Simplification V1. Overview is
            now the home: one clear hierarchy, not a stack of surfaces each
            claiming to be "what to do" -- Venture Identity (what is this,
            who's it for, biggest unknowns) -> the intelligence loop hero
            (what matters now, why, what to do -- CurrentQuestionCard,
            unchanged from Phase 34D/34D-A) -> what SIE understands ->
            recent activity -> graduation/analyze bridges -> secondary,
            de-emphasized "other things you're tracking" -> the venture
            details editor, contextual and collapsed by default. See
            docs/product/SIE_BUILD_FOUNDER_EXPERIENCE_V1.md for the full
            audit and the reasoning behind every removal/move below. */}
        <TabPanel id="overview" activeId={tab}>
          <div className="space-y-8">
            <VentureIdentity
              stage={stage}
              assumptions={venture.assumptions}
              whoItsFor={targetCustomer}
              howItMakesMoney={businessModel}
              stillFiguringOut={venture.model_result ? stillFiguringOutFromCategories(venture.model_result.categories) : []}
              onEditDetails={goToEditDetails}
            />

            {/* Phase 31 -- Venture -> Startup Graduation V1, Part 10: a
                persistent, honest "operating startup" banner once
                graduated -- never buried, never hidden behind a
                secondary tab. Renders nothing until graduated. */}
            <VentureGraduationBanner state={graduation} />

            {/* Phase 34D/34D-A -- SIE Build Intelligence Loop, now
                Overview's own hero (Phase 34E, Sections 9-10): "what
                matters now / why / what to do," progressively revealing
                the test/result/evidence/interpretation/recommendation/
                decision/outcome states as they become real. This is the
                ONE place the workspace answers "what should I do?" --
                the older, separate "What should I do next?" card
                (PrimaryCommandCard) and its duplicate "What to consider
                next" list are retired from this page for exactly that
                reason (Section 23: two sections answering the same
                question). Nothing about CurrentQuestionCard's own logic
                changed. */}
            <CurrentQuestionCard ventureId={ventureId} ventureName={venture.name} onCompanyIntelligence={setCompanyIntelligence} />

            {/* Phase 34E, Section 9's "specialized tools/secondary
                actions": the one thing PrimaryCommandCard did that
                CurrentQuestionCard doesn't -- recognizing a modeled
                venture is ready for a real, evidence-based Startup
                Profile, and explaining that boundary honestly. */}
            {readyToAnalyze ? (
              <BaseCard className="p-6">
                <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Your model looks solid</p>
                <h2 className="mt-1 text-lg font-semibold text-text-primary">Ready to turn this into a real startup?</h2>
                <p className="mt-2 text-base leading-7 text-text-secondary">
                  This modeled idea shows what COULD work, based on your own assumptions. A real Startup Profile
                  shows what evidence supports TODAY, built the same way for every company on SIE. Analyzing brings
                  over your own description as a starting point -- it never creates anything or invents evidence on
                  your behalf.
                </p>
                <Button
                  type="button"
                  className="mt-4"
                  onClick={() => {
                    if (description) {
                      stashVentureDescriptionForAnalyze(description);
                    }
                    router.push("/analyze");
                  }}
                >
                  Analyze My Startup
                </Button>
              </BaseCard>
            ) : null}

            <CompanyIntelligenceState
              modelResult={venture.model_result}
              companyIntelligence={companyIntelligence}
              hasHistory={!isLoadingHistory && Boolean(history) && history!.events.length > 1}
              onSeeHistory={() => setTab("history")}
            />

            {/* Phase 31 -- Venture -> Startup Graduation V1, Part 3/10,
                corrected by Phase 34F, Section 5: the unprominent "Create
                a Startup Profile from this venture →" quiet link never
                explained what a Startup Profile is, what creating one
                does, or why a venture needs to become one -- exactly the
                gap the acceptance test named. It's removed from the
                primary journey; only the fully-explained, self-contained
                card (real evidence reported -> "Ready to make this a
                startup?", with what/why spelled out) still shows, and
                only once genuinely eligible. `VentureGraduationAction`'s
                own non-prominent branch/component is untouched --
                nothing about graduation itself was removed, only this
                one under-explained entry point to it. Renders nothing
                once already graduated (VentureGraduationBanner above
                covers that state) or not yet eligible. */}
            {graduation.eligible ? <VentureGraduationAction state={graduation} prominent /> : null}

            {/* Phase 34E, Section 11, corrected by Phase 34F, Section 6:
                "Other things you're tracking" was still too large and
                too permanently present for what the acceptance standard
                asks -- a founder must be free to work on something other
                than SIE's recommendation, but the primary experience
                should stay focused on the single highest-value question
                above. The trigger itself is now the entire pitch
                ("Working on something else? Add it →") -- no separate
                intro paragraph, no "tracking" language exposing the
                internal mission architecture. Nothing about the three
                components' own logic/data changed -- venture_missions,
                the capture/model-update firewall, and the milestone
                suggestions are all exactly as Phase 10/23/33 built them;
                only this entry point got smaller and plainer. */}
            <Disclosure summary="Working on something else? Add it →" defaultOpen={false}>
              <div className="space-y-8 pt-2">

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
                    currentPriorityText={primaryMissionTitle ?? primaryMilestoneText ?? null}
                  />
                </div>

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
                      refreshHistory();
                    }}
                    onPrimaryMissionChanged={setPrimaryMissionTitle}
                    onVentureUpdated={(updated) => {
                      setVenture(updated);
                      setDraft(updated.assumptions);
                      refreshHistory();
                    }}
                  />
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
              </div>
            </Disclosure>

            {/* Phase 34E, Section 6: the old Model tab's editor, retired
                as a primary destination and moved here as a contextual,
                collapsed-by-default entry point, opened either by this
                disclosure directly or by the Venture Identity card's own
                button above (goToEditDetails()). The editor itself
                (every field, every accordion) is byte-for-byte the same
                as before; only its address on the page changed. The
                separate "Recalculate (preview)" step is gone (Section
                8) -- Save now applies directly.
                Phase 34F, Section 4: reframed around the founder benefit
                -- not "maintain a complete profile," but "SIE gives
                better guidance the more it understands." The heading and
                explanation are always visible (even collapsed) so a
                founder knows WHY before deciding whether to expand it;
                only the CTA itself is the disclosure's clickable
                trigger. */}
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Help SIE understand your venture</h2>
              <p className="mt-1 text-sm leading-6 text-text-secondary">
                Add details about your customers, business model, market, traction, and finances so SIE can
                give you more relevant guidance and analysis.
              </p>
            </div>

            <Disclosure id="edit-the-full-model" summary="Add venture context →" defaultOpen={false}>
              <section>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-xl font-semibold text-text-primary">What you believe</h2>
                  <Button type="button" disabled={isSaving || !hasUnsavedChanges} loading={isSaving} onClick={handleSave}>
                    {isSaving ? "Saving..." : "Save Changes"}
                  </Button>
                </div>

                <p className="mt-1 text-sm text-text-secondary">
                  Everything below except &ldquo;What you&rsquo;ve learned&rdquo; is an assumption, not
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
