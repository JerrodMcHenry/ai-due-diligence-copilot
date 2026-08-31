"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import Button from "@/components/ui/Button";
import { listVentures } from "@/lib/api";
import { missionTypeForDeckCategory } from "@/lib/pitchDeckMissionMap";
import { getPlaybookForDeckSection } from "@/lib/playbooks/resourceMap";
import { stashPitchDeckMission } from "@/lib/pitchDeckMissionHandoff";

import type { PriorityFix, VentureSummary } from "@/types";

// Phase 11 -- Pitch Deck Coach V2, Part 13. A pitch deck review has no
// venture (it's a user-owned coaching artifact, see
// app/database/db.py's own pitch_deck_reviews comment) -- so unlike
// Idea Lab's own "Make this a mission" button (NextMoves.tsx, already on
// a specific venture's own page), this one first has to find out WHICH
// venture the founder means. Never auto-creates anything: this only ever
// stashes the fix and navigates to a venture page, where the founder
// sees the SAME pending-mission confirmation step
// (MissionsSection.tsx's pendingMission effect) Idea Lab's own button
// already uses before anything is actually posted.
type LoadState = "idle" | "loading" | "ready" | "error";

export default function MakeMissionButton({ fix }: { fix: PriorityFix }) {
  const router = useRouter();
  const { getToken } = useAuth();

  const [state, setState] = useState<LoadState>("idle");
  const [ventures, setVentures] = useState<VentureSummary[]>([]);
  const [selectedVentureId, setSelectedVentureId] = useState<number | null>(null);

  function buildHandoff() {
    const playbook = getPlaybookForDeckSection(fix.related_category);
    return {
      title: fix.title,
      description: `${fix.issue}\n\nWhy it matters: ${fix.why_it_matters}\n\nTry this: ${fix.try_this}`,
      missionType: missionTypeForDeckCategory(fix.related_category),
      relatedCategory: fix.related_category,
      resourceRef: playbook?.slug ?? null,
    };
  }

  function goToVenture(ventureId: number) {
    stashPitchDeckMission(buildHandoff());
    router.push(`/idea-lab/${ventureId}#your-missions`);
  }

  async function handleClick() {
    if (state === "loading") {
      return;
    }

    setState("loading");
    try {
      const token = await getToken();
      if (!token) {
        setState("error");
        return;
      }
      const list = await listVentures(token);
      setVentures(list);

      if (list.length === 1) {
        goToVenture(list[0].id);
        return;
      }

      setState("ready");
    } catch (error) {
      console.error("Failed to load ventures for mission handoff:", error);
      setState("error");
    }
  }

  if (state === "ready" && ventures.length > 1) {
    return (
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label htmlFor={`mission-venture-${fix.title}`} className="text-xs font-medium text-text-secondary">
          Add to which venture?
        </label>
        <select
          id={`mission-venture-${fix.title}`}
          value={selectedVentureId ?? ""}
          onChange={(event) => setSelectedVentureId(Number(event.target.value) || null)}
          className="min-h-9 rounded-lg border border-border bg-surface px-2 text-sm text-text-primary"
        >
          <option value="" disabled>
            Choose a venture&hellip;
          </option>
          {ventures.map((venture) => (
            <option key={venture.id} value={venture.id}>
              {venture.name}
            </option>
          ))}
        </select>
        <Button
          type="button"
          variant="subtle"
          size="sm"
          disabled={!selectedVentureId}
          onClick={() => selectedVentureId && goToVenture(selectedVentureId)}
        >
          Continue →
        </Button>
      </div>
    );
  }

  if (state === "ready" && ventures.length === 0) {
    return (
      <p className="mt-3 text-xs text-text-muted">
        You don&rsquo;t have a venture in Idea Lab yet.{" "}
        <Link href="/idea-lab/new" className="font-semibold text-primary hover:text-primary-hover">
          Start one
        </Link>{" "}
        to turn this into a mission.
      </p>
    );
  }

  if (state === "error") {
    return <p className="mt-3 text-xs text-danger">Couldn&rsquo;t load your ventures. Try again.</p>;
  }

  return (
    <Button type="button" variant="subtle" size="sm" className="-ml-3.5 mt-3" onClick={handleClick} disabled={state === "loading"}>
      {state === "loading" ? "Loading your ventures…" : "Make this a mission →"}
    </Button>
  );
}
