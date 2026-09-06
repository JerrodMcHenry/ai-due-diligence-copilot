import { Suspense } from "react";

import { auth } from "@clerk/nextjs/server";

import Skeleton from "@/components/ui/Skeleton";
import VentureWorkspace from "./VentureWorkspace";

type Props = {
  params: Promise<{ id: string }>;
};

// Phase 33 -- Idea Workspace Information Architecture & Founder Operating
// Loop, Part 3. VentureWorkspace now reads its own local-navigation tab
// (?tab=model|what-if|fundraising|history, omitted = Overview) via
// useSearchParams() -- the same Client Component hook app/analyze/page.tsx
// and app/search/page.tsx already wrap in a Suspense boundary for their
// own query-param usage, and the same reason applies here: Next.js
// requires it. No other behavior of this page changed -- auth.protect()
// still runs first, ventureId is still resolved from the path the same
// way.
export default async function VenturePage({ params }: Props) {
  await auth.protect();

  const { id } = await params;
  const ventureId = Number(id);

  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-2xl" />}>
      <VentureWorkspace ventureId={ventureId} />
    </Suspense>
  );
}
