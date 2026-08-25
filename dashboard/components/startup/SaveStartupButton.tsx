"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import { getSavedStartupStatus, saveStartup, unsaveStartup } from "@/lib/api";

type SaveStartupButtonProps = {
  startupId: number;
};

// Saved Startups (Watchlist Phase 1). Behavior, per the product spec:
//
// SIGNED OUT: the rest of the Startup Profile is fully public (no auth
// gate on this page) -- this control alone leads a signed-out visitor
// through authentication if they try to use it, via a plain Link to
// /sign-in (same established pattern as Sidebar.tsx's own signed-out
// state -- no Clerk-hosted modal, nothing else on the page changes).
//
// SIGNED IN: checks real saved status on mount (GET /me/saved-startups/
// {id}) rather than assuming -- never guesses "not saved" as a starting
// state. Save/unsave are real network calls; the button only flips to
// its new state after the backend confirms success. A failure reverts to
// the last CONFIRMED state and shows a short inline message -- this never
// optimistically shows "Saved" (or "not saved") for a request that
// actually failed.
type Status =
  | "checking"
  | "signed-out"
  | "saved"
  | "unsaved"
  | "saving"
  | "removing"
  | "error";

export default function SaveStartupButton({
  startupId,
}: SaveStartupButtonProps) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [status, setStatus] = useState<Status>("checking");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    // Every setState call below lives inside this locally-defined async
    // function, invoked once by the effect -- never as a bare statement
    // directly in the effect body (react-hooks/set-state-in-effect).
    async function resolveStatus() {
      if (!isLoaded) {
        return;
      }

      if (!isSignedIn) {
        if (isMounted) {
          setStatus("signed-out");
        }
        return;
      }

      if (isMounted) {
        setStatus("checking");
        setErrorMessage(null);
      }

      try {
        const token = await getToken();

        if (!token) {
          if (isMounted) {
            setStatus("signed-out");
          }
          return;
        }

        const result = await getSavedStartupStatus(startupId, token);

        if (isMounted) {
          setStatus(result.saved ? "saved" : "unsaved");
        }
      } catch {
        if (isMounted) {
          // Unknown state is treated as "unsaved" so the control is still
          // usable -- a real Save attempt will surface its own error if
          // something is still wrong, rather than leaving the control
          // stuck permanently.
          setStatus("unsaved");
        }
      }
    }

    resolveStatus();

    return () => {
      isMounted = false;
    };
  }, [isLoaded, isSignedIn, startupId, getToken]);

  async function handleSave() {
    setStatus("saving");
    setErrorMessage(null);

    try {
      const token = await getToken();

      if (!token) {
        setStatus("signed-out");
        return;
      }

      const result = await saveStartup(startupId, token);
      setStatus(result.saved ? "saved" : "unsaved");
    } catch {
      setStatus("unsaved");
      setErrorMessage("Couldn't save this startup. Try again.");
    }
  }

  async function handleUnsave() {
    setStatus("removing");
    setErrorMessage(null);

    try {
      const token = await getToken();

      if (!token) {
        setStatus("signed-out");
        return;
      }

      const result = await unsaveStartup(startupId, token);
      setStatus(result.saved ? "saved" : "unsaved");
    } catch {
      setStatus("saved");
      setErrorMessage("Couldn't remove this startup. Try again.");
    }
  }

  if (status === "checking") {
    return (
      <div className="h-9 w-32 animate-pulse rounded-full bg-surface-muted" />
    );
  }

  if (status === "signed-out") {
    return (
      <Link
        href="/sign-in"
        className="inline-flex h-9 items-center rounded-full border border-border px-4 text-sm font-semibold text-text-secondary transition-colors hover:border-primary hover:text-primary"
      >
        Save Startup
      </Link>
    );
  }

  const isSaved = status === "saved" || status === "removing";
  const isWorking = status === "saving" || status === "removing";

  return (
    <div className="flex flex-col items-end gap-1.5">
      <button
        type="button"
        disabled={isWorking}
        onClick={isSaved ? handleUnsave : handleSave}
        aria-pressed={isSaved}
        className={[
          "inline-flex h-9 items-center gap-1.5 rounded-full px-4 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-70",
          isSaved
            ? "bg-success-soft text-success hover:bg-danger-soft hover:text-danger"
            : "border border-primary/30 text-primary hover:bg-primary-soft",
        ].join(" ")}
      >
        {status === "saving"
          ? "Saving..."
          : status === "removing"
            ? "Removing..."
            : isSaved
              ? "★ Saved"
              : "☆ Save Startup"}
      </button>

      {errorMessage ? (
        <p className="text-xs text-danger">{errorMessage}</p>
      ) : null}
    </div>
  );
}
