"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import Disclosure from "@/components/ui/Disclosure";
import VPSResultPanel from "@/components/idea-lab/VPSResultPanel";
import ScenarioComparison from "@/components/idea-lab/ScenarioComparison";
import VentureJourney from "@/components/idea-lab/VentureJourney";
import VentureOverview from "@/components/idea-lab/VentureOverview";
import VentureCard from "@/components/idea-lab/VentureCard";
import WhatIfPanel from "@/components/idea-lab/WhatIfPanel";
import MissionsSection from "@/components/idea-lab/MissionsSection";
import NextMoves from "@/components/idea-lab/NextMoves";
import { stillFiguringOutFromCategories } from "@/components/idea-lab/ventureOverviewHelpers";
import { suggestionForMilestone } from "@/components/idea-lab/missionSuggestions";
import {
  NumberField,
  SelectField,
  TextField,
  ToggleField,
} from "@/components/idea-lab/AssumptionFields";
import NextStepCard from "@/components/journey/NextStepCard";
import { resolveIdeaLabNextStep } from "@/lib/journey/resolveIdeaLabNextStep";
import { getPlaybookForMission } from "@/lib/playbooks/resourceMap";
import { stashVentureDescriptionForAnalyze } from "@/lib/ventureToStartupHandoff";

import {
  compareVentureScenarios,
  deleteVenture,
  getVenture,
  updateVenture,
} from "@/lib/api";
import { emptyAssumptions, VENTURE_STAGES } from "@/types";

import type {
  MissionType,
  ScenarioCompareResponse,
  VentureAssumptions,
  VentureResponse,
  VPSResult,
} from "@/types";

type LoadState = "loading" | "ready" | "error" | "not-found";

type VentureWorkspaceProps = {
  ventureId: number;
};

function assumptionsEqual(a: VentureAssumptions, b: VentureAssumptions): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export default function VentureWorkspace({ ventureId }: VentureWorkspaceProps) {
  const router = useRouter();
  const { getToken } = useAuth();

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
  const [pendingMission, setPendingMission] = useState<
    { title: string; relatedCategory: string; missionType: MissionType } | null
  >(null);
  const [missionedMilestones, setMissionedMilestones] = useState<string[]>([]);

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
  }, [ventureId, getToken]);

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
        <h1 className="text-xl font-bold text-text-primary">Venture not found</h1>
        <p className="mt-3 text-text-secondary">
          This venture doesn&rsquo;t exist, or doesn&rsquo;t belong to you.
        </p>
        <Link href="/idea-lab" className="mt-6 inline-flex text-sm font-semibold text-primary hover:text-primary-hover">
          Back to Idea Lab →
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

  return (
    <>
      <PageHeader
        title={venture.name}
        subtitle="Modeled venture — Idea Lab"
        action={
          <Button
            type="button"
            variant="subtle"
            disabled={isDeleting}
            onClick={handleDelete}
            className="hover:text-danger"
          >
            {isDeleting ? "Deleting..." : "Delete venture"}
          </Button>
        }
      />

      <div className="space-y-8">
        <BaseCard className="p-5">
          <VentureJourney stage={stage} />
        </BaseCard>

        <VentureOverview
          idea={description}
          whoItsFor={targetCustomer}
          howItMakesMoney={businessModel}
          stillFiguringOut={
            venture.model_result ? stillFiguringOutFromCategories(venture.model_result.categories) : []
          }
        />

        {venture.model_result ? <VPSResultPanel result={venture.model_result} /> : null}

        {actionError ? (
          <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {actionError}
          </div>
        ) : null}

        {/* Phase 10.10, Part 5/6: ONE headline "what should I do next?"
            card, deterministically derived from the exact same
            next_milestones/vps data NextMoves already renders below it
            (see resolveIdeaLabNextStep's own docstring -- no new logic,
            no score, no LLM). NextMoves keeps showing the fuller top-3
            list underneath as supporting detail; this is the hierarchy
            Part 5 asks for, not a duplicate competing CTA -- "Start this
            mission" here calls the exact same setPendingMission()
            mechanism NextMoves' own "Make this a mission" button does. */}
        {venture.model_result ? <IdeaLabNextStep
          modelResult={venture.model_result}
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
        /> : null}

        {venture.model_result ? (
          <NextMoves
            milestones={venture.model_result.next_milestones}
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

        <div id="your-missions">
        <MissionsSection
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
          pendingMission={pendingMission}
          onPendingMissionConsumed={() => setPendingMission(null)}
          onMissionTitlesChanged={setMissionedMilestones}
          onVentureUpdated={(updated) => {
            setVenture(updated);
            setDraft(updated.assumptions);
            setScenario(null);
          }}
        />
        </div>

        <BaseCard className="p-5">
          <WhatIfPanel
            currentAssumptions={venture.assumptions}
            onRunScenario={handleRunScenario}
            isRunning={isPreviewing}
          />
        </BaseCard>

        {scenario ? (
          <ScenarioComparison
            scenario={scenario}
            onApply={handleSave}
            onDiscard={() => setScenario(null)}
            isApplying={isSaving}
          />
        ) : null}

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

          <p className="mt-1 text-xs text-text-muted">
            Everything below except &ldquo;What you&rsquo;ve learned&rdquo; is a modeled assumption, not
            observed evidence.
          </p>

          <div className="mt-4 space-y-3">
            <VentureBasicsAccordion
              targetCustomer={targetCustomer}
              onTargetCustomer={setTargetCustomer}
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
              <NumberField
                id="gtm-cac"
                label="Expected CAC ($)"
                value={draft.gtm.expected_cac}
                onChange={(value) => setDraft((prev) => ({ ...prev, gtm: { ...prev.gtm, expected_cac: value } }))}
              />
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
              <NumberField
                id="econ-margin"
                label="Expected gross margin (%)"
                value={draft.economics.expected_gross_margin_pct}
                onChange={(value) => setDraft((prev) => ({ ...prev, economics: { ...prev.economics, expected_gross_margin_pct: value } }))}
              />
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
            </AssumptionAccordion>

            <AssumptionAccordion title="Capital">
              <NumberField
                id="capital-starting"
                label="Starting capital ($)"
                value={draft.capital.starting_capital}
                onChange={(value) => setDraft((prev) => ({ ...prev, capital: { ...prev.capital, starting_capital: value } }))}
              />
              <NumberField
                id="capital-burn"
                label="Monthly burn ($)"
                value={draft.capital.monthly_burn}
                onChange={(value) => setDraft((prev) => ({ ...prev, capital: { ...prev.capital, monthly_burn: value } }))}
              />
            </AssumptionAccordion>
          </div>
        </section>
        </Disclosure>

        {/* Phase 10.6, Part 11: visual architecture for a future
            shareable venture card -- see VentureCard.tsx's own comment.
            Collapsed by default so it doesn't compete with the primary
            workspace; nothing here is wired to sharing yet. */}
        <Disclosure summary="Preview your venture card" defaultOpen={false}>
          {venture.model_result ? (
            <VentureCard
              name={venture.name}
              oneLineConcept={description}
              vps={venture.model_result.vps}
              categories={venture.model_result.categories}
            />
          ) : (
            <p className="text-sm text-text-muted">
              Model a few assumptions to see a preview of your venture card.
            </p>
          )}
        </Disclosure>
      </div>
    </>
  );
}

// Phase 10.10 -- Founder Journey Integration, Part 5/6. Turns
// resolveIdeaLabNextStep()'s pure, deterministic result into real
// NextStepCard props -- the only place that happens, since building the
// actual actions needs callbacks (setPendingMission, router navigation)
// the resolver itself deliberately has no access to.
function IdeaLabNextStep({
  modelResult,
  missionedMilestones,
  onStartMission,
  onAnalyzeStartup,
}: {
  modelResult: VPSResult;
  missionedMilestones: string[];
  onStartMission: (milestoneText: string, suggestion: { relatedCategory: string; missionType: MissionType }) => void;
  onAnalyzeStartup: () => void;
}) {
  const nextStep = resolveIdeaLabNextStep(modelResult);

  if (nextStep.kind === "add_assumptions") {
    return (
      <NextStepCard
        title="Add a few assumptions to see your first model"
        why="Even a rough guess at your market or problem statement is enough to get started."
        primaryAction={{ label: "Edit your model", href: "#edit-the-full-model" }}
      />
    );
  }

  if (nextStep.kind === "work_on_milestone") {
    const suggestion = suggestionForMilestone(nextStep.milestoneText);
    const alreadyMissioned = missionedMilestones.includes(nextStep.milestoneText);
    const playbook = getPlaybookForMission({
      missionType: suggestion.missionType,
      relatedCategory: suggestion.relatedCategory,
    });

    return (
      <NextStepCard
        title={nextStep.milestoneText}
        why="This reduces one of your venture's biggest unknowns right now."
        primaryAction={
          alreadyMissioned
            ? { label: "Go to your missions", href: "#your-missions" }
            : { label: "Start this mission", onClick: () => onStartMission(nextStep.milestoneText, suggestion) }
        }
        learnPlaybookSlug={playbook?.slug}
      />
    );
  }

  // "ready_for_real_startup" -- Part 8's idea -> real startup bridge.
  // Deliberately explains the boundary rather than implying anything
  // transfers automatically: analyzing does not create a startup by
  // itself, and nothing here invents evidence -- POST /analyze still runs
  // its own independent research/evidence pipeline exactly as it does for
  // any other visitor.
  return (
    <NextStepCard
      eyebrow="Your model looks solid"
      title="Ready to turn this into a real startup?"
      why="This modeled idea shows what COULD work, based on your own assumptions. A real Startup Profile shows what evidence supports TODAY, built the same way for every company on SIE. Analyzing brings over your own description as a starting point -- it never creates anything or invents evidence on your behalf."
      primaryAction={{ label: "Analyze My Startup", onClick: onAnalyzeStartup }}
    />
  );
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
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-semibold text-text-primary marker:content-none">
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
