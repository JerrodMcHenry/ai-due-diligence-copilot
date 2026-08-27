import { auth } from "@clerk/nextjs/server";

import InvestorWorkspaceView from "./InvestorWorkspaceView";

// Phase 9 -- Investor Workspace V1. Same page-level protection pattern as
// app/saved/page.tsx and app/founder/page.tsx: auth.protect() is the
// real, resource-based, server-side check that redirects a signed-out
// visitor to /sign-in itself. This protects the FRONTEND route only --
// GET /investor/workspace enforces its own auth independently
// (app/auth.py's RequireAuth), so a signed-out visitor or a direct API
// call without a token still can't reach the data either way.
export default async function InvestorWorkspacePage() {
  await auth.protect();

  return <InvestorWorkspaceView />;
}
