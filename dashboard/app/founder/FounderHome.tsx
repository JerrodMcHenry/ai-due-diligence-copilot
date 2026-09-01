"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";

import { getMyStartups } from "@/lib/api";

import type { MyStartupMembership } from "@/types";

type LoadState = "loading" | "ready" | "error";

// Phase 7.2 -- Founder Workspace V1. Source of truth is exclusively
// GET /me/startups (Phase 7.1C), which itself derives every row
// exclusively from startup_memberships -- never a pending claim, a
// saved startup, or a modeled venture. This page never invents a
// membership: zero rows here always means zero rows in the backend
// response, full stop.
export default function FounderHome() {
  const { getToken } = useAuth();

  const [memberships, setMemberships] = useState<MyStartupMembership[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let isMounted = true;

    async function loadMemberships() {
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

        const data = await getMyStartups(token);

        if (isMounted) {
          setMemberships(data);
          setLoadState("ready");
        }
      } catch (error) {
        console.error("Failed to load founder memberships:", error);

        if (isMounted) {
          setLoadState("error");
        }
      }
    }

    loadMemberships();

    return () => {
      isMounted = false;
    };
  }, [getToken]);

  return (
    <div className="space-y-8">
      {/* Phase 10.10, Part 11: title now matches PersonalMenu's own "My
          Startup" label exactly (previously the nav said "My Startup" but
          this page's own H1 said "Founder Workspace" -- the underlying
          route, backend concept, and every internal reference are
          unchanged, presentation only). */}
      <PageHeader
        title="My Startup"
        subtitle="Your private command center for the startups you've been verified as a member of."
      />

      {loadState === "loading" ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
          <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
        </div>
      ) : loadState === "error" ? (
        <BaseCard className="border-danger/30 bg-danger-soft p-6">
          <h2 className="text-base font-semibold text-danger">
            Unable to load your startups
          </h2>
          <p className="mt-2 text-sm text-danger">
            Try refreshing the page.
          </p>
        </BaseCard>
      ) : memberships.length === 0 ? (
        <EmptyState />
      ) : (
        <MembershipGrid memberships={memberships} />
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <BaseCard className="p-10 text-center">
      <h2 className="text-xl font-bold text-text-primary">
        No startups yet
      </h2>

      <p className="mx-auto mt-3 max-w-md text-sm text-text-secondary">
        Founder Workspace unlocks once you&rsquo;re a verified member of a
        startup on SIE. If your company hasn&rsquo;t been analyzed yet,
        start there and claim it from its new Startup Profile.
      </p>

      {/* Phase 15 -- Founder Beta Surface Audit, Part 15/24: swapped
          which action is primary here. "Analyze a startup" always works
          (it evaluates whatever the founder describes, independent of
          how many other companies exist on SIE) and is now the prominent
          button; "Discover Startups" (a search over the currently
          near-empty canonical population -- Part 8/16) is de-emphasized
          but still present and fully functional, not removed. */}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/analyze"
          className="rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
        >
          Analyze a startup
        </Link>

        <Link
          href="/search"
          className="rounded-lg border border-border px-4 py-2.5 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
        >
          Discover Startups
        </Link>
      </div>
    </BaseCard>
  );
}

function MembershipGrid({
  memberships,
}: {
  memberships: MyStartupMembership[];
}) {
  const isSingle = memberships.length === 1;

  return (
    <div>
      <p className="mb-4 text-sm text-text-secondary">
        {isSingle
          ? "You have one verified startup."
          : `You have ${memberships.length} verified startups. Choose one to enter its workspace.`}
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {memberships.map((membership) => (
          <Link
            key={membership.startup_id}
            href={`/founder/startups/${membership.startup_id}`}
            className="group block"
          >
            <BaseCard className="flex h-full flex-col justify-between gap-4 p-6 transition-colors group-hover:border-primary">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                  Startup member
                </p>
                <h3 className="mt-1 text-lg font-bold text-text-primary">
                  {membership.canonical_name}
                </h3>
              </div>

              <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                Enter Workspace
                <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">
                  →
                </span>
              </span>
            </BaseCard>
          </Link>
        ))}
      </div>
    </div>
  );
}
