"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";
import { SPSRing } from "@/components/sps";
import SPSHistory from "@/components/startup/SPSHistory";
import IntelligencePillars from "@/components/startup/IntelligencePillars";
import { PILLARS } from "@/components/startup/pillarMeta";
import {
  formatAnalysisDate,
  getMethodologyVersion,
  getOverallConfidence,
} from "@/components/startup/StartupHeroV2";

import { getFounderStartupWorkspace } from "@/lib/api";

import type { PillarKey } from "@/components/startup/pillarMeta";
import type {
  FounderStartupWorkspace,
  PillarAnalysis,
  SIEMethodologyAnalysis,
  SPSHistoryPoint,
} from "@/types";

type LoadState = "loading" | "ready" | "not-found" | "error";

type FounderStartupWorkspaceViewProps = {
  startupId: number;
};

type ScoredPillar = {
  key: PillarKey;
  label: string;
  analysis: PillarAnalysis;
};

// Phase 7.2 -- Founder Workspace V1. This is the founder's own private
// view of intelligence that already exists publicly -- the difference is
// framing (improvement-oriented, "where do I stand / what's next") and
// authorization (GET /founder/startups/{id} requires a live
// startup_memberships row via RequireStartupMember; the public Startup
// Profile requires nothing). No intelligence is recomputed, re-scored,
// or duplicated here -- every field below comes straight from the same
// SIEMethodologyAnalysis the public profile renders.
export default function FounderStartupWorkspaceView({
  startupId,
}: FounderStartupWorkspaceViewProps) {
  const { getToken } = useAuth();

  const [workspace, setWorkspace] = useState<FounderStartupWorkspace | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let isMounted = true;

    async function loadWorkspace() {
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
        console.error("Failed to load Founder Workspace:", error);

        if (isMounted) {
          // A 404 here means "doesn't exist, or you don't have access" --
          // the backend deliberately never distinguishes the two (see
          // RequireStartupMember's own docstring), so neither does this
          // message.
          setLoadState(
            error instanceof Error && /\(404\)/.test(error.message) ? "not-found" : "error"
          );
        }
      }
    }

    loadWorkspace();

    return () => {
      isMounted = false;
    };
  }, [startupId, getToken]);

  if (loadState === "loading") {
    return (
      <div className="space-y-6">
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-56 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />
      </div>
    );
  }

  if (loadState === "not-found") {
    return (
      <BaseCard className="p-10 text-center">
        <h1 className="text-xl font-bold text-text-primary">
          Workspace not available
        </h1>
        <p className="mt-3 text-text-secondary">
          This startup workspace doesn&rsquo;t exist, or you don&rsquo;t
          have access to it.
        </p>
        <Link
          href="/founder"
          className="mt-6 inline-flex text-sm font-semibold text-primary hover:text-primary-hover"
        >
          ← Back to Founder Workspace
        </Link>
      </BaseCard>
    );
  }

  if (loadState === "error" || !workspace) {
    return (
      <div className="rounded-xl border border-danger/20 bg-danger-soft p-6">
        <h2 className="font-semibold text-danger">
          Unable to load this workspace
        </h2>
        <p className="mt-2 text-sm text-danger/80">Try refreshing the page.</p>
      </div>
    );
  }

  const { startup_id, canonical_name, created_at, methodology, sps_history } = workspace;
  const publicProfileHref = `/startup/${encodeURIComponent(canonical_name)}`;
  // Phase 7.2.1 -- Deterministic Founder Re-analysis: startup_id in the
  // query string is what makes AnalyzeStartupForm verify membership and
  // guarantee this exact canonical startup as the write target -- see
  // that component's own FounderTargetState comment. Never the company
  // name: a name-based link could never guarantee re-attachment to this
  // same startup, which was the whole problem this phase fixes.
  const reanalyzeHref = `/analyze?startup_id=${startup_id}`;

  return (
    <div className="space-y-8">
      <PageHeader
        title={canonical_name}
        subtitle="Founder Workspace — private to verified members. Public intelligence for this startup is unaffected by anything shown here."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={publicProfileHref}
              className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
            >
              View Public Profile
            </Link>
            <Link
              href={reanalyzeHref}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              Re-analyze
            </Link>
          </div>
        }
      />

      {!methodology ? (
        <NotYetAnalyzed canonicalName={canonical_name} reanalyzeHref={reanalyzeHref} />
      ) : (
        <>
          <OverviewSection
            methodology={methodology}
            createdAt={created_at}
            spsHistory={sps_history}
          />

          <PrioritiesSection methodology={methodology} />

          <SPSHistory history={sps_history} />

          <IntelligencePillars methodology={methodology} />
        </>
      )}
    </div>
  );
}

function NotYetAnalyzed({
  canonicalName,
  reanalyzeHref,
}: {
  canonicalName: string;
  reanalyzeHref: string;
}) {
  return (
    <BaseCard className="p-10 text-center">
      <h2 className="text-xl font-bold text-text-primary">
        No intelligence yet
      </h2>

      <p className="mx-auto mt-3 max-w-md text-sm text-text-secondary">
        {canonicalName} doesn&rsquo;t have a completed Startup Intelligence
        analysis yet. Run one to see your SPS, pillar scores, and
        recommendations here.
      </p>

      <Link
        href={reanalyzeHref}
        className="mt-6 inline-flex rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
      >
        Analyze this startup
      </Link>
    </BaseCard>
  );
}

function OverviewSection({
  methodology,
  createdAt,
  spsHistory,
}: {
  methodology: SIEMethodologyAnalysis;
  createdAt: string | null;
  spsHistory: SPSHistoryPoint[];
}) {
  const confidence = getOverallConfidence(methodology);
  const methodologyVersion = getMethodologyVersion(methodology.analysis_context);
  const analysisDate = createdAt ? formatAnalysisDate(createdAt) : null;

  // "How has SPS changed" -- change since the immediately preceding
  // analysis, same underlying sps_history data SPSHistory below charts
  // in full. Omitted (not zeroed) when fewer than two points exist yet.
  const trend =
    spsHistory.length >= 2
      ? spsHistory[spsHistory.length - 1].startup_intelligence_score -
        spsHistory[spsHistory.length - 2].startup_intelligence_score
      : undefined;

  const metaParts = [
    methodologyVersion ? `Methodology ${methodologyVersion}` : null,
    analysisDate ? `Analyzed ${analysisDate}` : null,
  ].filter((part): part is string => Boolean(part));

  return (
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
          <h2 className="text-lg font-semibold text-text-primary">
            Current Standing
          </h2>

          {metaParts.length > 0 ? (
            <p className="mt-1 text-sm text-text-muted">
              {metaParts.join(" · ")}
            </p>
          ) : null}

          {methodology.executive_coaching_summary ? (
            <p className="mt-4 max-w-prose text-sm leading-6 text-text-secondary">
              {methodology.executive_coaching_summary}
            </p>
          ) : null}
        </div>
      </div>
    </BaseCard>
  );
}

function getScoredPillars(methodology: SIEMethodologyAnalysis): ScoredPillar[] {
  const scored: ScoredPillar[] = [];

  for (const pillar of PILLARS) {
    const analysis = methodology[pillar.key];

    // Unavailable pillars (score === null) are excluded from ranking
    // entirely -- never treated as a 0, never ranked as "weakest".
    if (analysis.score !== null) {
      scored.push({ key: pillar.key, label: pillar.label, analysis });
    }
  }

  return scored;
}

// "What's working" / "Needs attention" / "Top priorities" -- all derived
// purely by sorting the same six real pillar scores/strengths/weaknesses/
// recommendations the public profile already has; nothing here is
// recomputed or re-scored. Deliberately does NOT surface
// methodology.next_actions -- that field is a fixed, hardcoded list
// (see app/workflows/sie_assembler.py) identical on every analysis
// regardless of company, so treating it as a personalized recommendation
// here would be misleading; each pillar's own recommendations list is
// genuine, evidence-derived, per-company output.
function PrioritiesSection({ methodology }: { methodology: SIEMethodologyAnalysis }) {
  const scored = getScoredPillars(methodology);

  if (scored.length === 0) {
    return (
      <BaseCard className="p-6">
        <p className="text-sm text-text-muted">
          Not enough evidence yet to identify strengths or priorities.
        </p>
      </BaseCard>
    );
  }

  const sortedByScoreDesc = [...scored].sort(
    (a, b) => (b.analysis.score as number) - (a.analysis.score as number)
  );

  const strongest = sortedByScoreDesc.slice(0, 2);
  const strongestKeys = new Set(strongest.map((p) => p.key));
  const weakest = [...sortedByScoreDesc]
    .reverse()
    .filter((p) => !strongestKeys.has(p.key))
    .slice(0, 2);

  const recommendations = Array.from(
    new Set(weakest.flatMap((p) => p.analysis.recommendations).filter(Boolean))
  ).slice(0, 5);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <BaseCard className="p-6">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
          What&rsquo;s Working
        </h2>

        <div className="mt-4 space-y-4">
          {strongest.map((pillar) => (
            <PillarHighlight
              key={pillar.key}
              pillar={pillar}
              items={pillar.analysis.strengths}
              emptyLabel="No specific strengths noted yet."
              dotClassName="bg-success"
              scoreClassName="text-success"
            />
          ))}
        </div>
      </BaseCard>

      <BaseCard className="p-6">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
          Needs Attention
        </h2>

        <div className="mt-4 space-y-4">
          {weakest.map((pillar) => (
            <PillarHighlight
              key={pillar.key}
              pillar={pillar}
              items={pillar.analysis.weaknesses}
              emptyLabel="No specific weaknesses noted yet."
              dotClassName="bg-danger"
              scoreClassName="text-danger"
            />
          ))}
        </div>
      </BaseCard>

      {recommendations.length > 0 ? (
        <BaseCard className="p-6 lg:col-span-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Top Priorities
          </h2>

          <ul className="mt-4 space-y-1.5">
            {recommendations.map((recommendation, index) => (
              <li
                key={index}
                className="flex items-start gap-2.5 rounded-lg bg-primary/5 px-3.5 py-2.5 text-sm text-text-primary"
              >
                <span aria-hidden="true" className="mt-0.5 shrink-0 text-primary">
                  →
                </span>
                <span className="max-w-prose leading-6">{recommendation}</span>
              </li>
            ))}
          </ul>
        </BaseCard>
      ) : null}
    </div>
  );
}

function PillarHighlight({
  pillar,
  items,
  emptyLabel,
  dotClassName,
  scoreClassName,
}: {
  pillar: ScoredPillar;
  items: string[];
  emptyLabel: string;
  dotClassName: string;
  scoreClassName: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-text-primary">{pillar.label}</p>
        <span className={["text-sm font-bold", scoreClassName].join(" ")}>
          {(pillar.analysis.score as number).toFixed(1)} / 10
        </span>
      </div>

      <ul className="mt-1.5 space-y-1">
        {items.length > 0 ? (
          items.slice(0, 2).map((item, index) => (
            <li key={index} className="flex gap-2 text-sm text-text-secondary">
              <span
                aria-hidden="true"
                className={["mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", dotClassName].join(" ")}
              />
              <span>{item}</span>
            </li>
          ))
        ) : (
          <li className="text-sm text-text-muted">{emptyLabel}</li>
        )}
      </ul>
    </div>
  );
}
