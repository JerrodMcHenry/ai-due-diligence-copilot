"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import VentureSnapshotCard from "./VentureSnapshotCard";

import { getVentureShare, getVentureSharePreview, logSnapshotLinkCopied, updateVentureShare } from "@/lib/api";
import type { VentureShareSettings, VentureSnapshotResponse } from "@/types";

// Phase 27 -- Shareable Venture Snapshot V1, Part 5/13/16/17. Supersedes
// Phase 10.6's old "Preview your venture card" disclosure (VentureCard.tsx,
// removed this phase -- see the final report's "Venture Card final role"
// section) -- this is now the one, real Share control panel: preview,
// toggles, enable, copy link, disable. The preview always renders via
// VentureSnapshotCard fed by GET /ventures/{id}/share/preview, which
// server-side reuses the EXACT SAME DTO builder the public route does
// (app/api.py::_build_venture_snapshot) -- there is no separate preview
// rendering path here to accidentally drift from what a recipient sees.
//
// THE FIREWALL, restated for the frontend layer: nothing in this
// component ever calls updateVenture(), captureVentureObservation(), or
// any mission-creation function -- every state change here goes through
// updateVentureShare() alone, which only ever touches the four share_*
// columns (Part 23).
export default function ShareVentureSnapshot({ ventureId }: { ventureId: number }) {
  const { getToken } = useAuth();

  const [settings, setSettings] = useState<VentureShareSettings | null>(null);
  const [preview, setPreview] = useState<VentureSnapshotResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied">("idle");

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("Your session expired. Sign in again.");
        return;
      }
      const [settingsResult, previewResult] = await Promise.all([
        getVentureShare(ventureId, token),
        getVentureSharePreview(ventureId, token),
      ]);
      setSettings(settingsResult);
      setPreview(previewResult);
    } catch (err) {
      console.error("Failed to load share settings:", err);
      setError("Couldn't load sharing settings. Try again.");
    } finally {
      setIsLoading(false);
    }
  }, [ventureId, getToken]);

  useEffect(() => {
    // Promise.resolve().then() is a genuine microtask boundary, not
    // decoration -- react-hooks/set-state-in-effect flags load()'s own
    // synchronous setIsLoading(true) call (its first line) as directly
    // reachable from this effect body. Same pattern MissionsSection.tsx's
    // own loadMissions() effect and NewVentureForm.tsx's homepage-idea
    // handoff effect already use.
    Promise.resolve().then(() => {
      load();
    });
  }, [load]);

  async function applyChange(next: { enabled: boolean; show_vps: boolean; show_validation: boolean }) {
    setIsBusy(true);
    setError(null);
    setCopyStatus("idle");
    try {
      const token = await getToken();
      if (!token) {
        setError("Your session expired. Sign in again.");
        return;
      }
      const updated = await updateVentureShare(ventureId, next, token);
      setSettings(updated);
      // Re-fetch the preview so it reflects the toggles that actually
      // took effect -- never assume the request body equals the saved
      // state.
      const previewResult = await getVentureSharePreview(ventureId, token);
      setPreview(previewResult);
    } catch (err) {
      console.error("Failed to update share settings:", err);
      setError("Couldn't update sharing. Try again.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCopyLink() {
    if (!settings?.public_id) return;
    const url = `${window.location.origin}/v/${settings.public_id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopyStatus("copied");
      setTimeout(() => setCopyStatus("idle"), 2000);
      // Phase 28, Part 3/4: fires only after the copy genuinely
      // succeeded -- never on the button render, never on a failed
      // clipboard write. Best-effort: a logging failure here must never
      // surface to the founder as a copy failure (the copy itself
      // already succeeded by this point).
      try {
        const token = await getToken();
        if (token) await logSnapshotLinkCopied(ventureId, token);
      } catch (logErr) {
        console.error("Failed to log link-copied event:", logErr);
      }
    } catch (err) {
      console.error("Failed to copy link:", err);
      setError("Couldn't copy the link. Select and copy it manually.");
    }
  }

  if (isLoading) {
    return <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (!settings || !preview) {
    return error ? <p className="text-sm text-danger">{error}</p> : null;
  }

  const publicUrl = settings.public_id ? `${typeof window !== "undefined" ? window.location.origin : ""}/v/${settings.public_id}` : null;

  return (
    <div className="space-y-4">
      <BaseCard className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-text-primary">
              {settings.enabled ? "Sharing is on" : "Sharing is off"}
            </p>
            <p className="mt-0.5 text-xs text-text-secondary">
              {settings.enabled
                ? "Anyone with the link below can view this snapshot. Nothing else about your venture is public."
                : "Private until you turn this on. Preview below shows exactly what a recipient would see."}
            </p>
          </div>
          <Button
            type="button"
            variant={settings.enabled ? "secondary" : "primary"}
            disabled={isBusy}
            loading={isBusy}
            onClick={() =>
              applyChange({
                enabled: !settings.enabled,
                show_vps: settings.show_vps,
                show_validation: settings.show_validation,
              })
            }
          >
            {settings.enabled ? "Disable sharing" : "Enable sharing"}
          </Button>
        </div>

        {settings.enabled && publicUrl ? (
          <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-border bg-background px-3 py-2">
            <span className="min-w-0 flex-1 truncate text-xs text-text-secondary">{publicUrl}</span>
            <Button type="button" variant="subtle" size="sm" onClick={handleCopyLink}>
              {copyStatus === "copied" ? "Copied ✓" : "Copy link"}
            </Button>
          </div>
        ) : null}

        <div className="mt-4 space-y-2 border-t border-border pt-3">
          <label className="flex items-center gap-2.5 text-sm text-text-primary">
            <input
              type="checkbox"
              checked={settings.show_vps}
              disabled={isBusy}
              onChange={(event) =>
                applyChange({ enabled: settings.enabled, show_vps: event.target.checked, show_validation: settings.show_validation })
              }
              className="size-4 accent-primary"
            />
            Show Venture Potential Score
          </label>
          <label className="flex items-center gap-2.5 text-sm text-text-primary">
            <input
              type="checkbox"
              checked={settings.show_validation}
              disabled={isBusy}
              onChange={(event) =>
                applyChange({ enabled: settings.enabled, show_vps: settings.show_vps, show_validation: event.target.checked })
              }
              className="size-4 accent-primary"
            />
            Show evidence (customer conversations, paying customers, pricing, revenue)
          </label>
        </div>

        {error ? <p className="mt-2 text-xs text-danger">{error}</p> : null}
      </BaseCard>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
          {settings.enabled ? "What recipients see" : "Preview — not shared yet"}
        </p>
        <VentureSnapshotCard snapshot={preview} />
      </div>
    </div>
  );
}
