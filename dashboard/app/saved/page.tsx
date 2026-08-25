import { auth } from "@clerk/nextjs/server";

import SavedStartupsView from "./SavedStartupsView";

// Saved Startups (Watchlist Phase 1): same page-level protection pattern
// as app/analyze/page.tsx -- auth.protect() is the real, resource-based
// check (server-side, redirects a signed-out visitor to /sign-in itself);
// proxy.ts's route-matcher redirect (already lists "/saved(.*)", added in
// Phase 1 in anticipation of this page) is a UX-only optimistic layer on
// top of it, not a substitute. This protects the FRONTEND route only --
// GET /me/saved-startups on the backend enforces its own auth
// independently (see app/auth.py's RequireAuth), so a signed-out visitor
// can't reach this page, and a direct API call without a token still
// can't reach the data either way.
export default async function SavedStartupsPage() {
  await auth.protect();

  return <SavedStartupsView />;
}
