"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Disclosure from "@/components/ui/Disclosure";
import CurrentQuestionCard from "@/components/idea-lab/CurrentQuestionCard";
import VentureUnderstandingPanel from "@/components/idea-lab/VentureUnderstandingPanel";

import { getVentureFinancials } from "@/lib/api";
import { formatWholeDollars, formatMonthYear } from "@/lib/finance/money";
import { isFinancialConstraintActive } from "@/lib/build/commandCenterPriority";

import type { CompanyIntelligenceSummary, DerivedFinancialMetrics, FinancialSnapshot, VPSResult } from "@/types";

type Props = {
  ventureId: number;
  ventureName: string;
  modelResult: VPSResult | null;
  hasHistory: boolean;
  onSeeHistory: () => void;
};

type FinanceLoadState = "loading" | "ready" | "error";

// Phase 38B -- Founder Command Center V1
// (docs/product/SIE_FOUNDER_COMMAND_CENTER_V1.md is the governing spec).
//
// Replaces the old three-piece Overview stack (CurrentQuestionCard +
// a private CompanyIntelligenceState function + implicit "nothing about
// Finance" silence) with one coherent "What matters now" surface that
// can ALSO consider Finance -- but only for the one objective, already-
// existing, zero-invented-threshold condition the repository actually
// supports: DerivedFinancialMetrics.status === "out_of_cash" (cash at or
// below zero while burn is positive -- app/ai/financial_engine.py's own
// compute_derived_metrics(), unchanged, unduplicated). Section 22 of the
// 38B directive is explicit: if no defensible rule already exists, do
// not invent one. "burning" with any amount of runway_months, however
// small, is NOT treated as urgent here -- that would require choosing a
// cutoff (e.g. "3 months") the product has never established, which is
// exactly the fabricated-authority failure mode 38A/38B both forbid.
// Runway-based escalation is explicitly deferred to a future phase that
// establishes a real methodology for it first.
//
// No new backend endpoint: this component reads the SAME two existing,
// already-tested endpoints Overview and Finance already independently
// expose (GET /ventures/{id}/recommendation via CurrentQuestionCard's
// own unchanged fetch, GET /ventures/{id}/financials via the same
// getVentureFinancials() FundraisingSimulator.tsx already calls) and
// combines them with a small, pure, client-side comparison -- zero
// duplicated calculation, zero new AI, zero new score.
export default function CommandCenter({ ventureId, ventureName, modelResult, hasHistory, onSeeHistory }: Props) {
  const { getToken } = useAuth();

  const [financeState, setFinanceState] = useState<FinanceLoadState>("loading");
  const [derived, setDerived] = useState<DerivedFinancialMetrics | null>(null);
  const [snapshot, setSnapshot] = useState<FinancialSnapshot | null>(null);
  const [companyIntelligence, setCompanyIntelligence] = useState<CompanyIntelligenceSummary | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadFinance() {
      if (isMounted) setFinanceState("loading");
      try {
        const token = await getToken();
        if (!token) {
          if (isMounted) setFinanceState("error");
          return;
        }
        const data = await getVentureFinancials(ventureId, token);
        if (isMounted) {
          setDerived(data.derived);
          setSnapshot(data.latest_snapshot);
          setFinanceState("ready");
        }
      } catch (error) {
        console.error("Command Center: failed to load Finance state:", error);
        // Finance is a SILENT, optional input here (§12 of the 38B
        // directive: "do not show Finance simply because Finance
        // exists") -- a failed fetch degrades to "Finance contributes
        // nothing," never a visible error banner competing with Build's
        // own primary recommendation.
        if (isMounted) setFinanceState("error");
      }
    }

    loadFinance();
    return () => {
      isMounted = false;
    };
  }, [ventureId, getToken]);

  // The one, real, existing, zero-invented-threshold financial override
  // condition -- see lib/build/commandCenterPriority.ts's own module
  // comment for the full "why only this condition" reasoning.
  const financialConstraint =
    financeState === "ready" && isFinancialConstraintActive(derived) && derived
      ? { derived, snapshot }
      : null;

  const knows = companyIntelligence?.what_sie_knows ?? [];
  const stillFiguringOut = companyIntelligence?.still_figuring_out ?? [];
  const whatChanged = companyIntelligence?.what_changed ?? [];
  const hasAnyBuildContext = knows.length > 0 || stillFiguringOut.length > 0 || whatChanged.length > 0;

  return (
    <div className="space-y-6">
      {financialConstraint ? (
        <FinancialPriorityCard ventureId={ventureId} ventureName={ventureName} constraint={financialConstraint} />
      ) : null}

      <CurrentQuestionCard
        ventureId={ventureId}
        ventureName={ventureName}
        onCompanyIntelligence={setCompanyIntelligence}
        heading={financialConstraint ? null : "What matters now"}
      />

      {/* Phase 38B, Section 16: this is the SAME content the old
          CompanyIntelligenceState private function rendered (Phase 34G
          §10-13's own "what SIE knows / still figuring out / what
          changed" summary) -- moved here as Command Center's own
          "Current context" section, not duplicated or reinterpreted.
          Absent entirely (not "nothing to show yet") when Build has
          nothing recorded and no model exists -- the fresh-venture
          case CurrentQuestionCard's own hero already covers on its own. */}
      {hasAnyBuildContext || modelResult ? (
        <BaseCard className="space-y-5 p-6">
          <h2 className="text-lg font-semibold text-text-primary">Current context</h2>

          {knows.length > 0 ? (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What SIE knows</p>
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
              <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Still unclear</p>
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

          {hasHistory ? (
            <button
              type="button"
              onClick={onSeeHistory}
              className="text-sm font-semibold text-primary hover:text-primary-hover"
            >
              See full history →
            </button>
          ) : null}

          {/* Phase 34E's own preserved capability, carried over unchanged
              from the old CompanyIntelligenceState: the MODELED (not
              observed) VPS-category breakdown remains one click away,
              never the default content -- this answers "what was
              modeled," a different question from "current context"
              above, which answers "what's been observed." */}
          {modelResult ? (
            <Disclosure summary="See the full breakdown by category" defaultOpen={false}>
              <div className="pt-2">
                <VentureUnderstandingPanel result={modelResult} />
              </div>
            </Disclosure>
          ) : null}
        </BaseCard>
      ) : null}
    </div>
  );
}

// --- Financial priority (only ever rendered for status === "out_of_cash") --

function FinancialPriorityCard({
  ventureId,
  ventureName,
  constraint,
}: {
  ventureId: number;
  ventureName: string;
  constraint: { derived: DerivedFinancialMetrics; snapshot: FinancialSnapshot | null };
}) {
  const { derived, snapshot } = constraint;
  const [showTrace, setShowTrace] = useState(false);

  const cashLabel = snapshot?.cash_balance_cents != null ? formatWholeDollars(snapshot.cash_balance_cents) : "unknown";
  const burnLabel = derived.net_burn_cents != null ? formatWholeDollars(derived.net_burn_cents) : "unknown";
  const snapshotDateLabel = snapshot?.as_of_date ? formatMonthYear(snapshot.as_of_date) : null;

  return (
    <BaseCard variant="raised" className="space-y-4 border-danger/30 bg-danger-soft/40 p-6 sm:p-7">
      <p className="text-xs font-semibold uppercase tracking-wide text-danger">What matters now</p>
      <h2 className="text-xl font-bold text-text-primary">Your cash trajectory needs attention</h2>

      <p className="text-base leading-7 text-text-secondary">
        {snapshotDateLabel ? `Based on your ${snapshotDateLabel} financial snapshot, c` : "C"}urrent cash is{" "}
        {cashLabel} and monthly net burn is {burnLabel}. At {ventureName}&rsquo;s current numbers, cash is
        already at or below zero — this comes before anything else you&rsquo;re working on right now.
      </p>

      <Link
        href={`/idea-lab/${ventureId}?tab=finance`}
        className="inline-flex h-10 items-center rounded-lg bg-primary px-4 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
      >
        Review your cash plan →
      </Link>

      <div>
        <button
          type="button"
          onClick={() => setShowTrace((v) => !v)}
          className="text-sm font-semibold text-primary hover:text-primary-hover"
        >
          Why SIE is focusing here {showTrace ? "▴" : "▾"}
        </button>
        {showTrace ? (
          <ul className="mt-2 space-y-1 text-sm text-text-secondary">
            <li>• Cash: {cashLabel}</li>
            <li>• Monthly net burn: {burnLabel}</li>
            {snapshotDateLabel ? <li>• Snapshot date: {snapshotDateLabel}</li> : null}
            <li>• Status: cash is at or below zero while spending exceeds revenue</li>
          </ul>
        ) : null}
      </div>
    </BaseCard>
  );
}
