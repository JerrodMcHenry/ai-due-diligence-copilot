import { Suspense } from "react";

import { auth } from "@clerk/nextjs/server";

import Skeleton from "@/components/ui/Skeleton";
import AnalyzeStartupForm from "./AnalyzeStartupForm";

// SIE Authentication Phase 1: page-level protection, independent of
// proxy.ts. auth() is server-side only (Server Components, Route
// Handlers, Server Actions) and requires clerkMiddleware() to be
// configured in proxy.ts -- auth.protect() redirects a signed-out
// visitor to /sign-in itself for a normal page request, so no manual
// redirect() call is needed here. This is the real check; proxy.ts's
// route-matcher redirect is a UX-only optimistic layer on top of it, not
// a substitute for it (see proxy.ts's own comment).
//
// IMPORTANT: this protects the FRONTEND route only. POST /analyze on the
// FastAPI backend enforces its own auth independently (RequireAuth, and
// -- for a founder-targeted request -- membership too; see app/auth.py).
//
// Phase 7.2.1 -- Deterministic Founder Re-analysis: AnalyzeStartupForm
// now reads an optional ?startup_id= query param via useSearchParams(),
// which Next.js requires be wrapped in a Suspense boundary (same
// pattern app/search/page.tsx already established for DiscoveryView's
// own useSearchParams() usage) -- normal analysis (no query param) is
// otherwise completely unaffected by this wrapper.
export default async function AnalyzeStartupPage() {
  await auth.protect();

  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-2xl" />}>
      <AnalyzeStartupForm />
    </Suspense>
  );
}
