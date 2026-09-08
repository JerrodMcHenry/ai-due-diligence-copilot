"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";

import { listVentures } from "@/lib/api";

import type { VentureSummary } from "@/types";

// Phase 37E -- Company Lifecycle + Public Identity Convergence, Section 4.
// This list only ever has the venture's raw, founder-set `stage` string
// (VentureSummary has no `assumptions` -- fetching that per card would be
// the N+1 this lightweight list deliberately avoids elsewhere), so it
// cannot run the full evidence-aware resolveVentureState() the venture's
// own detail page uses (VentureWorkspace.tsx) -- a venture whose real
// evidence has outpaced its manually-set stage may still show the
// earlier label here until that page's own resolver corrects it. What
// this table DOES fix: a bare "Idea" pill read, out of context, as this
// venture's TYPE or LEGITIMACY rather than its current stage -- exactly
// the ambiguity this phase's own audit named. Every value gets the same
// "Stage" framing the detail page already uses (VENTURE_STATES in
// lib/journey/inferVentureStage.ts), so "Idea" never appears bare.
const STAGE_CARD_LABELS: Record<string, string> = {
  Idea: "Idea Stage",
  Researching: "Researching Stage",
  Validating: "Validation Stage",
  Building: "Building Stage",
  Launched: "Operating Stage",
};

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
      {/* Phase 32 -- Product Information Architecture + Seamless User
          Journey, Part 3: "Idea Lab" removed as a user-facing label --
          a founder shouldn't need to know what an "Idea Lab" is to use
          it. CTA "Start a New Idea," plain founder language, replacing
          the internal "venture" term -- left unchanged by 37E below,
          since a new entry usually does start as just an idea. Route
          (/idea-lab, /idea-lab/new) and every backend/type name are
          unchanged -- see this phase's own terminology map for the full
          list of what did and didn't rename.
          Phase 37E -- Company Lifecycle + Public Identity Convergence,
          Section 10: title changed from "My Ideas" to "My Companies."
          This list holds every venture regardless of stage -- including
          ones with real paying customers and six figures of ARR (see
          lib/journey/inferVentureStage.ts's own "Operating Stage"
          bucket) -- so a bare "Ideas" label was exactly the same
          ambiguity Section 4 already fixed on each card's own stage
          badge, one level up. "Build" (the top-level nav item pointing
          here) is intentionally left as-is; this only renames the
          in-page title/breadcrumb one level below it. */}
      <PageHeader
        title="My Companies"
        subtitle="Start with just an idea. SIE helps you model it, test your assumptions, and see what would make it stronger — before you build anything."
        action={
          <Link
            href="/idea-lab/new"
            className="rounded-xl bg-primary px-5 py-2.5 text-base font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            Start a New Idea
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
            You haven&rsquo;t started an idea yet.
          </p>

          <p className="mx-auto mt-2 max-w-md text-base leading-7 text-text-secondary">
            Model a startup idea — even a pure idea with no customers yet — and see what you&rsquo;d need to
            prove for it to work, organized around your own stated assumptions.
          </p>

          <Link
            href="/idea-lab/new"
            className="mt-6 inline-flex rounded-xl bg-primary px-5 py-2.5 text-base font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            Model your first startup idea
          </Link>
        </BaseCard>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {ventures.map((venture) => (
            // Phase 31C-C -- Global Visual Scale + Readability Correction,
            // Part 4: the directive's own worked example -- the venture
            // TITLE must clearly dominate its metadata at a glance.
            // Title bumped text-base->text-lg (18px, "card heading"
            // range); stage/date row at text-sm (14px, the "metadata"
            // floor, not the 12px "exceptional only" one); more card
            // padding/gap for breathing room.
            //
            // Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence
            // and Decision Support, Part 2: the VPS badge and the
            // "X.X — MODELED, not observed evidence" line are both gone --
            // `stage` (already a real, founder-set field, unchanged) is
            // now the card's only status signal.
            <Link key={venture.id} href={`/idea-lab/${venture.id}`}>
              <BaseCard className="flex h-full flex-col gap-3.5 p-6 transition-colors hover:border-primary/40">
                <h3 className="min-w-0 truncate text-lg font-semibold text-text-primary">
                  {venture.name}
                </h3>

                {/* Phase 34E -- Founder Experience Simplification V1: "what
                    should I continue?" per card, not model-centric
                    metadata -- the venture's current active question
                    (Phase 34D), when one exists. Two lines, never more,
                    so the card stays a card, not a second Overview. */}
                {venture.current_question ? (
                  <p className="line-clamp-2 text-sm leading-6 text-text-secondary">{venture.current_question}</p>
                ) : null}

                <div className="mt-auto flex flex-wrap items-center gap-2 text-sm text-text-secondary">
                  {venture.stage ? (
                    <span className="rounded-full border border-border px-2 py-0.5">
                      {STAGE_CARD_LABELS[venture.stage] ?? venture.stage}
                    </span>
                  ) : null}
                  <span>Updated {formatUpdatedAt(venture.updated_at)}</span>
                </div>
              </BaseCard>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
