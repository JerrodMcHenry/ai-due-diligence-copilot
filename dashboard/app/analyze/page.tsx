import { auth } from "@clerk/nextjs/server";

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
// FastAPI backend is not yet auth-enforced (Phase 2) -- a signed-out
// visitor can't reach this page, but a direct API call to the backend
// still can. Do not read this page-level gate as backend security.
export default async function AnalyzeStartupPage() {
  await auth.protect();

  return <AnalyzeStartupForm />;
}
