import { auth } from "@clerk/nextjs/server";

import FounderStartupWorkspaceView from "./FounderStartupWorkspaceView";

type Props = {
  params: Promise<{ startupId: string }>;
};

// Phase 7.2 -- Founder Workspace V1. Same server-wrapper auth pattern as
// app/idea-lab/[id]/page.tsx: auth.protect() is the real, resource-based,
// server-side gate. The REAL authorization for this specific startup is
// enforced independently on the backend by RequireStartupMember (see
// app/auth.py) when FounderStartupWorkspaceView calls
// GET /founder/startups/{startupId} -- this page-level check alone
// cannot and does not decide who may see which startup's data.
export default async function FounderStartupPage({ params }: Props) {
  await auth.protect();

  const { startupId } = await params;

  return <FounderStartupWorkspaceView startupId={Number(startupId)} />;
}
