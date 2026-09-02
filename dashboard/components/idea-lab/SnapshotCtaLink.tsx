"use client";

import Link from "next/link";

import { logSnapshotCtaClicked } from "@/lib/api";

// Phase 28 -- Product Analytics & Growth Measurement V1, Part 3/4/17. A
// tiny client component ONLY because the public /v/[publicId] page is a
// server component and can't attach an onClick itself. Fires
// snapshot_cta_clicked best-effort, fire-and-forget -- never blocks or
// delays the actual navigation, and a logging failure here must never
// prevent the recipient from reaching /idea-lab/new. The href itself
// carries the SAME opaque public_id the recipient is already looking at
// (Part 17: "do not build cross-site tracking, do not fingerprint" --
// forwarding an id the visitor already has is not new information).
export default function SnapshotCtaLink({ publicId }: { publicId: string }) {
  function handleClick() {
    logSnapshotCtaClicked(publicId).catch((error) => {
      console.error("Failed to log snapshot CTA click:", error);
    });
  }

  return (
    <Link
      href={`/idea-lab/new?ref=snapshot&share=${encodeURIComponent(publicId)}`}
      onClick={handleClick}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-text-primary transition-colors hover:border-primary"
    >
      Model your own venture →
    </Link>
  );
}
