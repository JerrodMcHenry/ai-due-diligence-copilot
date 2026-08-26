"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";

import { getFundraisingReadiness } from "@/lib/api";

import type { FundraisingReadiness } from "@/types";

type LoadState = "loading" | "ready" | "error";

type FundraisingReadinessCardProps = {
  startupId: number;
};

const BAND_CLASSES: Record<string, string> = {
  Early: "border border-border text-text-secondary",
  Developing: "bg-warning/10 text-warning",
  "Getting Ready": "bg-primary/10 text-primary",
  "Raise Ready": "bg-success/10 text-success",
};

// Phase 8 -- Fundraising Readiness V1. Deliberately compact -- this is a
// teaser/summary that links to the dedicated /fundraising page (Part
// 11's own preference), not a second copy of the full assessment. Keeps
// Founder Workspace from becoming an endless vertical wall while still
// making the capability discoverable from the operating cockpit.
export default function FundraisingReadinessCard({ startupId }: FundraisingReadinessCardProps) {
  const { getToken } = useAuth();

  const [readiness, setReadiness] = useState<FundraisingReadiness | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let isMounted = true;

    async function loadReadiness() {
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

        const data = await getFundraisingReadiness(startupId, token);

        if (isMounted) {
          setReadiness(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load Fundraising Readiness summary:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    loadReadiness();

    return () => {
      isMounted = false;
    };
  }, [startupId, getToken]);

  const href = `/founder/startups/${startupId}/fundraising`;

  if (loadState === "loading") {
    return <div className="h-24 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (loadState === "error" || !readiness) {
    // Fails quiet, same precedent as other secondary Founder Workspace
    // controls -- the page's primary purpose isn't affected either way.
    return null;
  }

  return (
    <Link href={href} className="group block">
      <BaseCard className="flex flex-wrap items-center justify-between gap-4 p-5 transition-colors group-hover:border-primary">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Fundraising Readiness
          </p>
          {readiness.has_canonical_analysis ? (
            readiness.readiness_score !== null ? (
              <p className="mt-1 flex items-center gap-2">
                <span className="text-2xl font-bold text-text-primary">
                  {readiness.readiness_score.toFixed(0)}
                </span>
                <span
                  className={[
                    "rounded-full px-2.5 py-0.5 text-xs font-semibold",
                    BAND_CLASSES[readiness.readiness_band ?? ""] ?? "border border-border text-text-secondary",
                  ].join(" ")}
                >
                  {readiness.readiness_band}
                </span>
              </p>
            ) : (
              <p className="mt-1 text-sm text-text-muted">Not enough data to assess yet.</p>
            )
          ) : (
            <p className="mt-1 text-sm text-text-muted">Needs a startup analysis first.</p>
          )}
          {readiness.gaps.length > 0 ? (
            <p className="mt-1 text-xs text-text-muted">
              {readiness.gaps.length} gap{readiness.gaps.length === 1 ? "" : "s"} identified
            </p>
          ) : null}
        </div>

        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
          View assessment
          <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">→</span>
        </span>
      </BaseCard>
    </Link>
  );
}
