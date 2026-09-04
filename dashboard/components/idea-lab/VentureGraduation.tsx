"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import GraduateVentureReview from "@/components/idea-lab/GraduateVentureReview";
import { isEligibleForGraduationSuggestion } from "@/lib/journey/resolveGraduationEligibility";
import { stashGraduationSummaryForAnalyze, type GraduationSourceVenture } from "@/lib/ventureToStartupHandoff";
import {
  getMyStartups,
  getVentureGraduationStatus,
  graduateVenture,
  logGraduationPromptShown,
  logGraduationStarted,
  logStartupOpenedFromVenture,
} from "@/lib/api";
import type { MyStartupMembership, VentureGraduationStatus } from "@/types";

// Phase 31 -- Venture -> Startup Graduation V1, Part 3/10/15.
//
// One hook (fetched ONCE per page load, never per placement -- Section
// 17's own "no N+1" discipline) plus two small presentational pieces the
// caller (VentureWorkspace.tsx) places at three different positions per
// Part 10's own layout requirement:
//
//   VentureGraduationBanner  -- already graduated: a small, persistent,
//     honest "operating startup" banner near "Where things stand". Never
//     hidden, never buried.
//   VentureGraduationAction  -- not yet graduated: either the moderately
//     prominent suggestion (real evidence reported -- Part 2/3's
//     deterministic, no-AI, no-VPS eligibility check) placed after the
//     primary next-step card, OR the quiet manual-only link placed
//     inside Explore -- same component, same review flow, the caller
//     just decides WHERE to mount it based on `state.eligible`.
//
// Nothing here mutates the venture, computes a score, or calls an LLM.
export type VentureGraduationState = {
  status: VentureGraduationStatus | null;
  eligible: boolean;
  isReviewOpen: boolean;
  isSubmitting: boolean;
  error: string | null;
  existingStartups: MyStartupMembership[];
  venture: GraduationSourceVenture;
  openReview: () => void;
  closeReview: () => void;
  submit: (args: {
    companyName: string;
    connectExistingStartupId: number | null;
    fieldsTransferredCount: number;
  }) => void;
  openStartup: () => void;
};

export function useVentureGraduation(
  ventureId: number,
  venture: GraduationSourceVenture
): VentureGraduationState {
  const router = useRouter();
  const { getToken } = useAuth();

  const [status, setStatus] = useState<VentureGraduationStatus | null>(null);
  const [existingStartups, setExistingStartups] = useState<MyStartupMembership[]>([]);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eligible = isEligibleForGraduationSuggestion(venture.assumptions.validation);
  const promptLoggedRef = useRef(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      const token = await getToken();
      if (!token) return;

      try {
        const result = await getVentureGraduationStatus(ventureId, token);
        if (isMounted) setStatus(result);
      } catch (loadError) {
        console.error("Failed to load graduation status:", loadError);
      }
    }

    load();
    return () => {
      isMounted = false;
    };
  }, [ventureId, getToken]);

  // Part 14: fires once per mount, only for the eligible+not-yet-
  // graduated combination actually rendered as the prominent suggestion
  // -- never for the quiet manual link, never repeated on re-render.
  useEffect(() => {
    if (!eligible || !status || status.graduated || promptLoggedRef.current) {
      return;
    }
    promptLoggedRef.current = true;

    getToken().then((token) => {
      if (token) logGraduationPromptShown(ventureId, token);
    });
  }, [eligible, status, ventureId, getToken]);

  function openReview() {
    setError(null);
    setIsReviewOpen(true);

    getToken().then(async (token) => {
      if (!token) return;
      logGraduationStarted(ventureId, token);
      try {
        const startups = await getMyStartups(token);
        setExistingStartups(startups);
      } catch (loadError) {
        console.error("Failed to load existing startups:", loadError);
      }
    });
  }

  function closeReview() {
    setIsReviewOpen(false);
  }

  async function submit(args: {
    companyName: string;
    connectExistingStartupId: number | null;
    fieldsTransferredCount: number;
  }) {
    setIsSubmitting(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("Your session expired. Sign in again.");
        return;
      }

      const result = await graduateVenture(
        ventureId,
        {
          company_name: args.companyName,
          trigger: eligible ? "suggested" : "manual",
          connect_existing_startup_id: args.connectExistingStartupId,
          fields_transferred_count: args.fieldsTransferredCount,
        },
        token
      );

      if (args.connectExistingStartupId === null) {
        stashGraduationSummaryForAnalyze(venture);
      }

      router.push(`/analyze?startup_id=${result.startup_id}`);
    } catch (submitError) {
      console.error("Failed to graduate venture:", submitError);
      setError("This startup could not be created. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function openStartup() {
    if (!status?.startup_id) return;
    const token = await getToken();
    if (token) logStartupOpenedFromVenture(ventureId, token);
    router.push(`/founder/startups/${status.startup_id}`);
  }

  return {
    status,
    eligible,
    isReviewOpen,
    isSubmitting,
    error,
    existingStartups,
    venture,
    openReview,
    closeReview,
    submit,
    openStartup,
  };
}

export function VentureGraduationBanner({ state }: { state: VentureGraduationState }) {
  if (!state.status?.graduated) {
    return null;
  }

  return (
    <BaseCard variant="subtle" className="flex flex-wrap items-center justify-between gap-3 p-4">
      <p className="text-sm text-text-secondary">
        Operating startup: <span className="font-semibold text-text-primary">{state.status.startup_name}</span> was
        created from this venture.
      </p>
      <Button type="button" variant="secondary" size="sm" onClick={state.openStartup}>
        Open Startup Profile →
      </Button>
    </BaseCard>
  );
}

export function VentureGraduationAction({
  state,
  prominent,
}: {
  state: VentureGraduationState;
  prominent: boolean;
}) {
  if (!state.status || state.status.graduated) {
    return null;
  }

  if (state.isReviewOpen) {
    return (
      <GraduateVentureReview
        venture={state.venture}
        existingStartups={state.existingStartups}
        isSubmitting={state.isSubmitting}
        error={state.error}
        onCancel={state.closeReview}
        onSubmit={state.submit}
      />
    );
  }

  if (!prominent) {
    return (
      <button
        type="button"
        onClick={state.openReview}
        className="text-left text-sm font-semibold text-primary hover:text-primary-hover"
      >
        Create a Startup Profile from this venture →
      </button>
    );
  }

  return (
    <BaseCard variant="raised" className="p-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Real evidence, not just a model</p>
      <p className="mt-1.5 text-lg font-bold text-text-primary">Create a Startup Profile</p>
      <p className="mt-1.5 text-sm leading-6 text-text-secondary">
        You&rsquo;ve reported real customers or revenue. A Startup Profile tracks this venture with SIE&rsquo;s
        canonical intelligence going forward — your venture and its history stay exactly as they are.
      </p>
      <div className="mt-4">
        <Button type="button" onClick={state.openReview}>
          Create Startup Profile
        </Button>
      </div>
    </BaseCard>
  );
}
