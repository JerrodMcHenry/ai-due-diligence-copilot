"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import { SPSRing } from "@/components/sps";
import SPSHistory from "@/components/startup/SPSHistory";
import IntelligencePillars from "@/components/startup/IntelligencePillars";
import FundraisingReadinessCard from "@/components/founder/FundraisingReadinessCard";
import PitchDeckCoachTeaser from "@/components/founder/PitchDeckCoachTeaser";
import { getOverallConfidence } from "@/components/startup/StartupHeroV2";

import { getFounderStartupWorkspace } from "@/lib/api";

import type { FounderStartupWorkspace } from "@/types";

type LoadState = "loading" | "ready" | "error";

type VentureAnalyzeSectionProps = {
  startupId: number;
};

// Phase 37C -- Legacy Founder Workspace Capability Triage + Unified
// Workspace Integration. The smallest useful "how does SIE evaluate this
// company" surface for a venture already linked to a startup identity
// (the caller checks graduation status before rendering this at all --
// see VentureWorkspace.tsx's own "analyze" tab). Reads the exact same
// GET /founder/startups/{id} the legacy Founder Workspace itself reads --
// no new endpoint, no new score, no recomputation, same ownership check
// (RequireStartupMember) server-side.
//
// Deliberately NOT a second Founder Workspace: no Action Plan, no
// Milestones, no Recent Updates here. Per this phase's own audit, those
// are workflow-tracking capabilities that Build's own evidence-first loop
// (venture_missions / Current Question / decisions) already covers for a
// linked company -- rendering them a second time here would be exactly
// the kind of duplication this phase exists to remove. This section only
// ever reads existing canonical intelligence; it never writes.
export default function VentureAnalyzeSection({ startupId }: VentureAnalyzeSectionProps) {
  const { getToken } = useAuth();

  const [workspace, setWorkspace] = useState<FounderStartupWorkspace | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let isMounted = true;

    async function load() {
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

        const data = await getFounderStartupWorkspace(startupId, token);

        if (isMounted) {
          setWorkspace(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load company analysis:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [startupId, getToken]);

  if (loadState === "loading") {
    return (
      <div className="space-y-6">
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-64 animate-pulse rounded-2xl border border-border bg-surface" />
      </div>
    );
  }

  if (loadState === "error" || !workspace) {
    return (
      <div className="rounded-xl border border-danger/20 bg-danger-soft p-6">
        <h2 className="font-semibold text-danger">Unable to load company analysis</h2>
        <p className="mt-2 text-sm text-danger/80">Try refreshing the page.</p>
      </div>
    );
  }

  const { canonical_name, methodology, sps_history } = workspace;
  const publicProfileHref = `/startup/${encodeURIComponent(canonical_name)}`;
  // Same deterministic re-analysis path the legacy Founder Workspace uses
  // (startup_id in the query string, never the company name) -- see that
  // component's own comment for why this is the only safe way to
  // guarantee re-attachment to this exact canonical startup.
  const reanalyzeHref = `/analyze?startup_id=${startupId}`;

  // Section 7's own required honest empty state: a newly graduated
  // company has a startup identity but no canonical analysis yet. Never
  // shown as zeros, never a fabricated pillar breakdown.
  if (!methodology) {
    return (
      <BaseCard className="p-8 text-center">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
          Company Analysis
        </p>
        <h2 className="mt-1 text-lg font-semibold text-text-primary">
          No SIE company analysis has been run yet
        </h2>
        <p className="mx-auto mt-3 max-w-md text-base leading-7 text-text-secondary">
          {canonical_name}{" "}
          has a startup profile, but SIE hasn&rsquo;t evaluated it yet.
          Analyzing looks at the evidence available today — it never changes how you build{" "}
          {canonical_name} here.
        </p>
        <Link
          href={reanalyzeHref}
          className="mt-5 inline-flex rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
        >
          Analyze this company
        </Link>
      </BaseCard>
    );
  }

  const confidence = getOverallConfidence(methodology);

  const trend =
    sps_history.length >= 2
      ? sps_history[sps_history.length - 1].startup_intelligence_score -
        sps_history[sps_history.length - 2].startup_intelligence_score
      : undefined;

  // Section 8: never amplify low-coverage false precision. Reuses the
  // exact same structural_coverage semantics StartupHeroV2 already
  // surfaces on the public profile -- no new confidence formula.
  const structuralCoverage = methodology.structural_coverage;
  const showPartialCoverageWarning = Boolean(structuralCoverage?.partial_structural_coverage);

  return (
    <div className="space-y-8">
      <BaseCard className="p-8">
        <div className="grid gap-8 lg:grid-cols-[240px_1fr] lg:items-center">
          <div className="flex justify-center">
            <SPSRing
              score={methodology.startup_intelligence_score}
              confidence={confidence}
              trend={trend}
              size="lg"
            />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              Company Analysis
            </p>
            <h2 className="mt-1 text-lg font-semibold text-text-primary">
              How SIE evaluates {canonical_name}
            </h2>
            <p className="mt-2 max-w-prose text-base leading-7 text-text-secondary">
              Based on the evidence SIE has for {canonical_name}{" "}
              today — separate from how you&rsquo;re building it here.
            </p>

            {showPartialCoverageWarning ? (
              <p className="mt-3 rounded-lg bg-warning/10 px-3 py-2 text-sm text-warning">
                Partial structural coverage
                {structuralCoverage?.pillars_unavailable_entirely &&
                structuralCoverage.pillars_unavailable_entirely.length > 0
                  ? `: no scoreable evidence was found for ${structuralCoverage.pillars_unavailable_entirely.join(", ")}. `
                  : ". "}
                This score reflects only the evidence currently available, not full coverage of
                every pillar.
              </p>
            ) : null}
          </div>
        </div>
      </BaseCard>

      <div className="grid gap-4 sm:grid-cols-2">
        <FundraisingReadinessCard startupId={startupId} />
        <PitchDeckCoachTeaser />
      </div>

      <IntelligencePillars methodology={methodology} />

      <SPSHistory history={sps_history} />

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border p-4">
        <Link
          href={publicProfileHref}
          className="text-sm font-semibold text-primary hover:text-primary-hover"
        >
          View public profile →
        </Link>
        <Link
          href={reanalyzeHref}
          className="text-sm font-semibold text-primary hover:text-primary-hover"
        >
          Re-analyze →
        </Link>
      </div>
    </div>
  );
}
