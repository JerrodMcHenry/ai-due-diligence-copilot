import Link from "next/link";
import type { Metadata } from "next";

import BaseCard from "@/components/ui/BaseCard";
import VentureSnapshotCard from "@/components/idea-lab/VentureSnapshotCard";

import { getPublicVentureSnapshot } from "@/lib/api";
import type { VentureSnapshotResponse } from "@/types";

// Phase 27 -- Shareable Venture Snapshot V1, Part 7. THE public route --
// deliberately no `await auth.protect()` call anywhere in this file
// (unlike /idea-lab/[id]/page.tsx), matching this repo's own existing
// public-page precedent (/search, /rankings, /startup/[id] are all
// equally unauthenticated server components; see those pages' own
// absence of auth.protect()). A person needs the link -- there is no
// listing, search, or directory of public snapshots anywhere in this
// app (Part 24's own "do not build public venture browsing").
type Props = {
  params: Promise<{ publicId: string }>;
};

function isNotFoundError(error: unknown): boolean {
  return error instanceof Error && /\(404\)/.test(error.message);
}

async function loadSnapshot(publicId: string): Promise<VentureSnapshotResponse | null> {
  try {
    return await getPublicVentureSnapshot(publicId);
  } catch (error) {
    if (isNotFoundError(error)) {
      return null;
    }
    throw error;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { publicId } = await params;
  const snapshot = await loadSnapshot(publicId);

  if (!snapshot) {
    return { title: "Venture snapshot" };
  }

  return {
    title: snapshot.name,
    description: snapshot.problem_statement ?? "A venture modeled with the Startup Intelligence Engine.",
  };
}

export default async function VentureSnapshotPage({ params }: Props) {
  const { publicId } = await params;
  const snapshot = await loadSnapshot(publicId);

  if (!snapshot) {
    return (
      <BaseCard className="mx-auto max-w-md p-10 text-center">
        <h1 className="text-xl font-bold text-text-primary">This snapshot isn&rsquo;t available</h1>
        <p className="mt-3 text-sm text-text-secondary">
          This link may be disabled, or it may never have existed. If you have the right link, check with whoever
          shared it with you.
        </p>
        <Link href="/idea-lab/new" className="mt-6 inline-flex text-sm font-semibold text-primary hover:text-primary-hover">
          Model your own venture →
        </Link>
      </BaseCard>
    );
  }

  return (
    <div className="space-y-6">
      <VentureSnapshotCard snapshot={snapshot} />

      <div className="mx-auto max-w-xl text-center">
        <Link
          href="/idea-lab/new"
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-text-primary transition-colors hover:border-primary"
        >
          Model your own venture →
        </Link>
      </div>
    </div>
  );
}
