"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import { cancelMyStartupClaim, getMyStartupClaimStatus } from "@/lib/api";
import ClaimStartupForm from "./ClaimStartupForm";

import type { StartupClaimStatus, StartupClaimSubmissionResponse } from "@/types";

type ClaimStartupButtonProps = {
  startupId: number;
};

// Phase 7.1B. Behavior, per the product spec:
//
// SIGNED OUT: the rest of the Startup Profile is fully public (no auth
// gate on this page) -- this control alone leads a signed-out visitor
// through sign-in, same established pattern as SaveStartupButton.
//
// SIGNED IN: checks real claim status on mount (GET /me/startup-claims/
// {id}) rather than assuming -- this single endpoint already resolves to
// the caller's own MOST RECENT claim (see its own docstring in
// app/database/db.py), so "approved", "pending", "rejected", and "no
// claim at all" are all derived from one real, fresh read -- never
// guessed or remembered from a previous session.
//
// Every state transition below waits for the backend to confirm before
// changing what's shown -- this never optimistically shows "pending" or
// "cancelled" for a request that actually failed.
type Phase =
  | "checking"
  | "signed-out"
  | "claimable"
  | "form-open"
  | "pending"
  | "cancelling"
  | "rejected"
  | "member"
  | "error";

export default function ClaimStartupButton({ startupId }: ClaimStartupButtonProps) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [phase, setPhase] = useState<Phase>("checking");
  const [claim, setClaim] = useState<StartupClaimStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    // Every setState call below lives inside this locally-defined async
    // function, invoked once by the effect -- never as a bare statement
    // directly in the effect body (react-hooks/set-state-in-effect),
    // same pattern as SaveStartupButton's own status-check effect.
    async function resolveStatus() {
      if (!isLoaded) {
        return;
      }

      if (!isSignedIn) {
        if (isMounted) {
          setPhase("signed-out");
        }
        return;
      }

      if (isMounted) {
        setPhase("checking");
      }

      try {
        const token = await getToken();

        if (!token) {
          if (isMounted) {
            setPhase("signed-out");
          }
          return;
        }

        const status = await getMyStartupClaimStatus(startupId, token);

        if (!isMounted) {
          return;
        }

        if (status === null) {
          setClaim(null);
          setPhase("claimable");
          return;
        }

        setClaim(status);

        if (status.status === "approved") {
          // The backend only ever reports "approved" here because a real
          // startup_memberships row exists for this user/startup (see
          // approve_startup_claim()'s own invariant) -- this label is
          // never shown speculatively.
          setPhase("member");
        } else if (status.status === "pending") {
          setPhase("pending");
        } else if (status.status === "rejected") {
          setPhase("rejected");
        } else {
          // cancelled -- claimable again, same as never having claimed.
          setPhase("claimable");
        }
      } catch {
        if (isMounted) {
          setPhase("error");
        }
      }
    }

    resolveStatus();

    return () => {
      isMounted = false;
    };
  }, [isLoaded, isSignedIn, startupId, getToken]);

  function handleSubmitted(result: StartupClaimSubmissionResponse) {
    setClaim({
      claim_id: result.id,
      status: result.status,
      submitted_at: new Date().toISOString(),
      reviewed_at: null,
      rejection_reason: null,
    });
    setActionError(null);
    setPhase("pending");
  }

  async function handleCancel() {
    if (!claim) {
      return;
    }

    setPhase("cancelling");
    setActionError(null);

    try {
      const token = await getToken();

      if (!token) {
        setActionError("Your session expired. Sign in again.");
        setPhase("pending");
        return;
      }

      await cancelMyStartupClaim(claim.claim_id, token);
      setClaim(null);
      setPhase("claimable");
    } catch {
      setActionError("Couldn't cancel this claim. Try again.");
      setPhase("pending");
    }
  }

  if (phase === "checking") {
    return <div className="h-9 w-36 animate-pulse rounded-full bg-surface-muted" />;
  }

  if (phase === "signed-out") {
    return (
      <Link
        href="/sign-in"
        className="inline-flex h-9 items-center rounded-full border border-border px-4 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
      >
        Claim Startup
      </Link>
    );
  }

  if (phase === "error") {
    // Fails quiet, same as SaveStartupButton's own status-check failure
    // path -- a secondary control silently absent is better than an
    // alarming error banner on a page whose primary purpose (viewing
    // intelligence) is unaffected either way.
    return null;
  }

  if (phase === "member") {
    return (
      <span className="inline-flex h-9 items-center gap-1.5 rounded-full bg-success-soft px-4 text-sm font-semibold text-success">
        ✓ Verified member
      </span>
    );
  }

  if (phase === "pending") {
    return (
      <div className="flex flex-col items-end gap-1.5">
        <span className="inline-flex h-9 items-center gap-2 rounded-full bg-warning-soft px-4 text-sm font-semibold text-warning">
          Claim pending review
        </span>

        <button
          type="button"
          onClick={handleCancel}
          className="text-xs font-medium text-text-muted hover:text-danger"
        >
          Cancel claim
        </button>

        {actionError ? <p className="text-xs text-danger">{actionError}</p> : null}
      </div>
    );
  }

  if (phase === "cancelling") {
    return (
      <span className="inline-flex h-9 items-center gap-2 rounded-full bg-surface-muted px-4 text-sm font-semibold text-text-muted">
        Cancelling...
      </span>
    );
  }

  if (phase === "rejected") {
    return (
      <div className="flex max-w-xs flex-col items-end gap-1.5 text-right">
        <span className="inline-flex h-9 items-center rounded-full bg-surface-muted px-4 text-sm font-semibold text-text-secondary">
          Claim not approved
        </span>

        {claim?.rejection_reason ? (
          <p className="text-xs text-text-muted">{claim.rejection_reason}</p>
        ) : null}

        <button
          type="button"
          onClick={() => setPhase("form-open")}
          className="text-xs font-semibold text-primary hover:text-primary-hover"
        >
          Submit a new claim
        </button>
      </div>
    );
  }

  if (phase === "form-open") {
    return (
      <div className="w-full max-w-sm">
        <ClaimStartupForm
          startupId={startupId}
          onSubmitted={handleSubmitted}
          onDismiss={() =>
            setPhase(claim?.status === "rejected" ? "rejected" : "claimable")
          }
        />
      </div>
    );
  }

  // claimable
  return (
    <button
      type="button"
      onClick={() => setPhase("form-open")}
      className="inline-flex h-9 items-center rounded-full border border-primary/30 px-4 text-sm font-semibold text-primary transition-colors hover:bg-primary-soft"
    >
      Claim Startup
    </button>
  );
}
