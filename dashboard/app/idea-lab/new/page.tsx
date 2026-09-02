import { Suspense } from "react";

import { auth } from "@clerk/nextjs/server";

import Skeleton from "@/components/ui/Skeleton";
import NewVentureForm from "./NewVentureForm";

// Phase 28 -- Product Analytics & Growth Measurement V1, Part 17:
// NewVentureForm now reads optional ?ref=/?share= query params via
// useSearchParams() (a shareable snapshot's own CTA link), which Next.js
// requires be wrapped in a Suspense boundary -- same pattern
// app/analyze/page.tsx already established for its own ?startup_id=
// usage. Normal creation (no query params) is otherwise unaffected.
export default async function NewVenturePage() {
  await auth.protect();

  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-2xl" />}>
      <NewVentureForm />
    </Suspense>
  );
}
