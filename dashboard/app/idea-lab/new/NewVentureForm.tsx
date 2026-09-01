"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";

import { createVenture, structureIdea } from "@/lib/api";
import { consumeHomepageIdea } from "@/lib/homepageIdeaHandoff";
import VentureDraftReview, { type ConfirmedVenture } from "./VentureDraftReview";

import type { VentureDraft } from "@/types";

const IDEA_PLACEHOLDER = `Be as informal as you like -- write it the way you'd explain it to a friend.

e.g. "I want to build an AI bookkeeping product for independent construction contractors. It would connect to their bank accounts and invoices and automatically categorize expenses and prepare books for their accountant."`;

type Phase = "describe" | "structuring" | "review";

// Phase 6.1, Part 5: the low-friction first step is just a description --
// SIE proposes a structured draft, the founder reviews/edits it (see
// VentureDraftReview), and ONLY an explicit "Create Venture" click ever
// calls POST /ventures (see handleConfirmVenture below). Nothing is
// persisted between those two points.
//
// isCreating is deliberately a separate flag from `phase`, not a fourth
// phase value -- the review screen must stay ON SCREEN (showing
// "Creating...") while the request is in flight, not be swapped out for
// a different screen the instant creation starts.
export default function NewVentureForm() {
  const router = useRouter();
  const { getToken } = useAuth();

  const [phase, setPhase] = useState<Phase>("describe");
  const [description, setDescription] = useState("");
  const [draft, setDraft] = useState<VentureDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Phase 10.5 -- Consumer Home V2: pre-fills the description a visitor
  // already typed on the homepage's hero idea input, if they arrived via
  // that flow (see lib/homepageIdeaHandoff.ts for the full handoff
  // contract). A plain client-only effect, not a query param, so there's
  // nothing to parse/validate here beyond "was something stashed" --
  // every other code path in this file (structuring, review, create) is
  // completely unaware this happened and behaves exactly as it did
  // before this phase.
  //
  // The Promise.resolve().then() is a genuine microtask boundary, not
  // decoration -- react-hooks/set-state-in-effect flags a setState call
  // that's synchronously reachable from the effect body (it could have
  // run during render instead); deferring it to a microtask is the same
  // shape every other effect in this codebase that legitimately sets
  // state already uses (they clear it via a real `await`, e.g.
  // AnalyzeStartupForm's verifyFounderTarget()) -- this has no real async
  // work, so it earns that boundary the honest way: this update must
  // land strictly after the initial client render commits, since
  // sessionStorage doesn't exist during SSR and description must start
  // as "" there for hydration to match.
  useEffect(() => {
    Promise.resolve().then(() => {
      const stashedIdea = consumeHomepageIdea();

      if (stashedIdea) {
        setDescription(stashedIdea);
      }
    });
  }, []);

  async function handleBuildModel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedDescription = description.trim();

    if (!trimmedDescription) {
      setError("Describe your idea in a sentence or two to get started.");
      return;
    }

    setPhase("structuring");
    setError(null);

    try {
      const token = await getToken();

      if (!token) {
        setError("Your session expired. Please sign in again.");
        setPhase("describe");
        return;
      }

      const response = await structureIdea(trimmedDescription, token);
      setDraft(response.draft);
      setPhase("review");
    } catch (structureError) {
      console.error("Failed to structure idea:", structureError);
      setError("We couldn't structure that idea right now. Please try again.");
      setPhase("describe");
    }
  }

  async function handleConfirmVenture(confirmed: ConfirmedVenture) {
    setIsCreating(true);
    setError(null);

    try {
      const token = await getToken();

      if (!token) {
        setError("Your session expired. Please sign in again.");
        return;
      }

      const venture = await createVenture(
        {
          name: confirmed.basics.name,
          description: description.trim(),
          industry: confirmed.basics.industry,
          business_model: confirmed.basics.businessModel,
          target_customer: confirmed.basics.targetCustomer,
          stage: confirmed.basics.stage,
          assumptions: confirmed.assumptions,
        },
        token
      );

      router.push(`/idea-lab/${venture.id}`);
    } catch (createError) {
      console.error("Failed to create venture:", createError);
      setError("Your venture could not be created. Please try again.");
    } finally {
      setIsCreating(false);
    }
  }

  if (phase === "review" && draft) {
    return (
      <>
        <PageHeader
          title="Review Your Venture Model"
          subtitle="Confirm or adjust what SIE understood before creating your venture."
        />

        {error ? (
          <div className="mb-5 rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {error}
          </div>
        ) : null}

        <VentureDraftReview
          draft={draft}
          originalDescription={description}
          onBack={() => setPhase("describe")}
          onConfirm={handleConfirmVenture}
          isSubmitting={isCreating}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Model a new venture"
        subtitle="Describe your idea in your own words — SIE will propose a structured starting point for you to review."
      />

      <form onSubmit={handleBuildModel} className="max-w-2xl space-y-5">
        <div>
          <label htmlFor="idea-description" className="mb-1.5 block text-sm font-medium text-text-primary">
            Describe your startup idea
          </label>

          <textarea
            id="idea-description"
            rows={8}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder={IDEA_PLACEHOLDER}
            // SIE Intelligence Reset -- root cause #1 of the ApexGrid
            // regression case: a real, evidence-rich company's
            // description (traction metrics, retention, GTM channel
            // mix, founder backgrounds, etc.) routinely exceeds 4000
            // characters. At 4000 the browser silently discarded
            // everything past that point -- confirmed live: ApexGrid's
            // stored description cut off mid-sentence, and every fact
            // that would have come after was never even sent to
            // extraction. 8000 is still well below /analyze's own
            // 50,000-character ceiling (a different, much more
            // thorough evidence pipeline) -- this is a short pitch,
            // not a full document, but it must fit a real company's
            // real evidence.
            maxLength={8000}
            disabled={phase === "structuring"}
            className="w-full resize-y rounded-lg border border-border bg-surface px-4 py-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 disabled:opacity-60"
          />
        </div>

        {error ? (
          <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={phase === "structuring"}
          className="min-h-11 rounded-lg bg-primary px-6 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {phase === "structuring" ? "Thinking..." : "Build My Venture Model"}
        </button>

        <p className="text-xs text-text-muted">
          SIE will propose a starting model based on what you write — you&rsquo;ll
          review and can edit everything before anything is created.
        </p>
      </form>
    </>
  );
}
