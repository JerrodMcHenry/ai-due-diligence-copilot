"use client";

import { useState } from "react";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import PathChooser from "./PathChooser";
import StartingCapTableBuilder from "./StartingCapTableBuilder";
import SafeTermsForm, { newSafeTerm } from "./SafeTermsForm";
import PricedRoundTermsForm, { emptyPricedRoundTerm } from "./PricedRoundTermsForm";
import RunwayTermsForm from "./RunwayTermsForm";
import FundraisingResult from "./FundraisingResult";
import FundraisingScenarioCompare from "./FundraisingScenarioCompare";
import FundraisingDisclaimer from "./FundraisingDisclaimer";

import { runScenario } from "@/lib/fundraisingUi/runScenario";
import { chainOwnershipFromResult } from "@/lib/fundraisingUi/chainScenario";
import type { FundraisingPath, RunwayTerms, ScenarioInput, ScenarioResult, UiPricedRoundTerm, UiSafeTerm, UiStakeholder } from "@/lib/fundraisingUi/types";

type ScenarioDraft = {
  path: FundraisingPath;
  safes: UiSafeTerm[];
  round: UiPricedRoundTerm;
  poolPercent: number;
};

type Step = "chooser" | "ownership" | "terms" | "result";

function freshDraft(path: FundraisingPath, safeCount: 1 | 2): ScenarioDraft {
  return {
    path,
    safes: path === "priced_round" ? [] : Array.from({ length: safeCount }, (_, i) => newSafeTerm(safeCount > 1 ? `SAFE ${i + 1}` : "SAFE Investor")),
    round: emptyPricedRoundTerm(path === "safe" ? "" : "Seed"),
    poolPercent: 0,
  };
}

function pathLabel(path: FundraisingPath): string {
  if (path === "safe") return "SAFE";
  if (path === "priced_round") return "Priced round";
  return "SAFE → Priced round";
}

function buildInput(ownership: UiStakeholder[], draft: ScenarioDraft, runway: RunwayTerms): ScenarioInput {
  return {
    startingStakeholders: ownership,
    path: draft.path,
    safes: draft.safes,
    pricedRound: draft.path === "safe" ? null : draft.round,
    optionPoolIncreasePercentOfCurrent: draft.poolPercent,
    runway,
  };
}

// Phase 21B, Part 1/2/25. Fundraising Simulator V1 -- lives inside the
// Simulate surface's [ Venture ] [ Fundraising ] tabs (see
// VentureWorkspace.tsx's own Founder Tools section). Entirely ephemeral
// (Part 23): every piece of state here is local component state, nothing
// is read from or written to the canonical venture model, no history
// event is created, VPS/SPS are never touched. `founderName` is the only
// real venture data this component reads, purely as a display default for
// the "You -- 100%" starting-ownership shortcut.
type FundraisingSimulatorProps = {
  founderName: string;
};

export default function FundraisingSimulator({ founderName }: FundraisingSimulatorProps) {
  const [ownership, setOwnership] = useState<UiStakeholder[] | null>(null);
  const [step, setStep] = useState<Step>("chooser");
  const [compareMode, setCompareMode] = useState(false);

  const [draftA, setDraftA] = useState<ScenarioDraft | null>(null);
  const [draftB, setDraftB] = useState<ScenarioDraft | null>(null);
  const [runway, setRunway] = useState<RunwayTerms>({ cashOnHandDollars: null, monthlyBurnDollars: null });

  const [resultA, setResultA] = useState<ScenarioResult | null>(null);
  const [resultB, setResultB] = useState<ScenarioResult | null>(null);

  function resetToChooser() {
    setStep("chooser");
    setCompareMode(false);
    setDraftA(null);
    setDraftB(null);
    setResultA(null);
    setResultB(null);
  }

  function choosePath(path: FundraisingPath, safeCount: 1 | 2) {
    setDraftA(freshDraft(path, safeCount));
    setDraftB(compareMode ? freshDraft(path, safeCount) : null);
    setStep(ownership ? "terms" : "ownership");
  }

  function startCompare() {
    setCompareMode(true);
    setStep("chooser");
  }

  function confirmOwnership(stakeholders: UiStakeholder[]) {
    setOwnership(stakeholders);
    setStep("terms");
  }

  function simulate() {
    if (!ownership || !draftA) return;
    const result = runScenario(buildInput(ownership, draftA, runway));
    setResultA(result);
    if (compareMode && draftB) {
      setResultB(runScenario(buildInput(ownership, draftB, runway)));
    }
    setStep("result");
  }

  function modelAnotherRound() {
    if (resultA?.kind !== "success") return;
    const chained = chainOwnershipFromResult(resultA);
    setOwnership(chained);
    setDraftA(freshDraft("priced_round", 1));
    setDraftB(null);
    setCompareMode(false);
    setResultA(null);
    setResultB(null);
    setStep("terms");
  }

  const canChainAnotherRound = resultA?.kind === "success" && !resultA.isEstimateOnly && !compareMode;

  return (
    <div className="space-y-5">
      {step === "chooser" ? (
        <BaseCard className="p-5">
          {compareMode ? (
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-primary">
              Comparing two options -- pick the instrument both will use
            </p>
          ) : null}
          <PathChooser onChoose={choosePath} onCompare={startCompare} />
        </BaseCard>
      ) : null}

      {step === "ownership" ? (
        <BaseCard className="p-5">
          <StartingCapTableBuilder founderName={founderName} initial={ownership} onConfirm={confirmOwnership} />
        </BaseCard>
      ) : null}

      {step === "terms" && ownership && draftA ? (
        <div className="space-y-5">
          <button
            type="button"
            onClick={() => setStep("ownership")}
            className="text-xs font-semibold text-primary hover:text-primary-hover"
          >
            ← Edit starting ownership
          </button>

          {compareMode && draftB ? (
            <div className="grid gap-5 lg:grid-cols-2">
              <ScenarioTermsPanel label="Scenario A" draft={draftA} onChange={setDraftA} />
              <ScenarioTermsPanel label="Scenario B" draft={draftB} onChange={setDraftB} />
            </div>
          ) : (
            <BaseCard className="p-5">
              <p className="mb-3 text-sm font-semibold text-text-primary">{pathLabel(draftA.path)} terms</p>
              <ScenarioTermsFields draft={draftA} onChange={setDraftA} />
            </BaseCard>
          )}

          <BaseCard className="p-5">
            <RunwayTermsForm runway={runway} onChange={setRunway} />
          </BaseCard>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" onClick={simulate}>
              {compareMode ? "Compare" : "Simulate"}
            </Button>
            <Button type="button" variant="subtle" onClick={resetToChooser}>
              Start over
            </Button>
          </div>
        </div>
      ) : null}

      {step === "result" && resultA ? (
        <div className="space-y-4">
          {compareMode && resultB ? (
            <FundraisingScenarioCompare labelA="Scenario A" labelB="Scenario B" resultA={resultA} resultB={resultB} />
          ) : (
            <FundraisingResult result={resultA} />
          )}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" variant="secondary" size="sm" onClick={resetToChooser}>
              Try another scenario
            </Button>
            {canChainAnotherRound ? (
              <Button type="button" variant="secondary" size="sm" onClick={modelAnotherRound}>
                Model another round on top of this
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {step === "chooser" && ownership === null ? <FundraisingDisclaimer /> : null}
    </div>
  );
}

function ScenarioTermsPanel({ label, draft, onChange }: { label: string; draft: ScenarioDraft; onChange: (d: ScenarioDraft) => void }) {
  return (
    <BaseCard className="p-5">
      <p className="mb-3 text-sm font-semibold text-text-primary">
        {label} -- {pathLabel(draft.path)}
      </p>
      <ScenarioTermsFields draft={draft} onChange={onChange} />
    </BaseCard>
  );
}

function ScenarioTermsFields({ draft, onChange }: { draft: ScenarioDraft; onChange: (d: ScenarioDraft) => void }) {
  return (
    <div className="space-y-4">
      {draft.path !== "priced_round" ? <SafeTermsForm safes={draft.safes} onChange={(safes) => onChange({ ...draft, safes })} /> : null}
      {draft.path !== "safe" ? (
        <PricedRoundTermsForm
          round={draft.round}
          onChange={(round) => onChange({ ...draft, round })}
          optionPoolIncreasePercent={draft.poolPercent}
          onOptionPoolIncreasePercentChange={(poolPercent) => onChange({ ...draft, poolPercent })}
        />
      ) : null}
    </div>
  );
}
