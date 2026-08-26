import { auth } from "@clerk/nextjs/server";

import FounderHome from "./FounderHome";

// Phase 7.2 -- Founder Workspace V1. Same page-level protection pattern
// as app/saved/page.tsx and app/idea-lab/page.tsx: auth.protect() is the
// real, resource-based, server-side check that redirects a signed-out
// visitor to /sign-in itself. This protects the FRONTEND route only --
// every backend call FounderHome makes (GET /me/startups, and later
// GET /founder/startups/{id}) enforces its own auth/membership
// independently (app/auth.py's RequireAuth/RequireStartupMember), so a
// signed-out visitor or a direct API call without a token still can't
// reach the data either way.
export default async function FounderPage() {
  await auth.protect();

  return <FounderHome />;
}
