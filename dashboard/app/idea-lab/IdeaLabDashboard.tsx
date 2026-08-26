"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";

import { listVentures } from "@/lib/api";

import type { VentureSummary } from "@/types";

function formatVps(value: number | null): string {
  return value === null ? "Not yet modeled" : value.toFixed(1);
}

function getVpsClasses(value: number | null): string {
  if (value === null) {
    return "bg-surface-muted text-text-muted";
  }
  if (value >= 7) {
    return "bg-success-soft text-success";
  }
  if (value >= 5) {
    return "bg-primary-soft text-primary";
  }
  return "bg-warning-soft text-warning";
}

function formatUpdatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

type LoadState = "loading" | "ready" | "error";

// This page lives behind app/idea-lab/page.tsx's server-side
// auth.protect() -- the isLoaded/isSignedIn checks below are a defensive
// guard for the brief hydration window, same pattern as
// SavedStartupsView.tsx.
export default function IdeaLabDashboard() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [ventures, setVentures] = useState<VentureSummary[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let isMounted = true;

    async function loadVentures() {
      if (!isLoaded || !isSignedIn) {
        return;
      }

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

        const data = await listVentures(token);

        if (isMounted) {
          setVentures(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load ventures:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    loadVentures();

    return () => {
      isMounted = false;
    };
  }, [isLoaded, isSignedIn, getToken]);

  return (
    <>
      <PageHeader
        title="Idea Lab"
        subtitle="Model a startup idea, see its Venture Potential Score, and explore what would make it stronger — before you build anything."
        action={
          <Link
            href="/idea-lab/new"
            className="rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            Model a new venture
          </Link>
        }
      />

      {loadState === "loading" ? (
        <div className="h-64 animate-pulse rounded-2xl border border-border bg-surface" />
      ) : loadState === "error" ? (
        <div className="rounded-xl border border-danger/20 bg-danger-soft p-6">
          <h2 className="font-semibold text-danger">Unable to load your ventures</h2>
          <p className="mt-2 text-sm text-danger/80">
            Something went wrong. Try refreshing the page.
          </p>
        </div>
      ) : ventures.length === 0 ? (
        <BaseCard className="p-10 text-center">
          <p className="text-lg font-semibold text-text-primary">
            You haven&rsquo;t modeled a venture yet.
          </p>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-text-secondary">
            Idea Lab lets you model a startup idea — even a pure idea with
            no customers yet — and see a Venture Potential Score built from
            your own stated assumptions.
          </p>

          <Link
            href="/idea-lab/new"
            className="mt-6 inline-flex rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            Model your first startup idea
          </Link>
        </BaseCard>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {ventures.map((venture) => (
            <Link key={venture.id} href={`/idea-lab/${venture.id}`}>
              <BaseCard className="flex h-full flex-col gap-3 p-5 transition-colors hover:border-primary/40">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="min-w-0 truncate text-base font-semibold text-text-primary">
                    {venture.name}
                  </h3>

                  <span
                    className={[
                      "shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold",
                      getVpsClasses(venture.vps),
                    ].join(" ")}
                  >
                    {venture.vps === null ? "—" : `VPS ${venture.vps.toFixed(1)}`}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
                  {venture.stage ? (
                    <span className="rounded-full border border-border px-2 py-0.5">{venture.stage}</span>
                  ) : null}
                  <span>Updated {formatUpdatedAt(venture.updated_at)}</span>
                </div>

                <p className="mt-auto text-xs text-text-muted">
                  {formatVps(venture.vps)} — MODELED, not observed evidence
                </p>
              </BaseCard>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
